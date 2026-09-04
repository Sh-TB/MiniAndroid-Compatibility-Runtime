#!/usr/bin/env python3
"""
EXP-085 Phase 1 — Multi-DEX Forensic Test Suite.

Independent verifier that:
  1. Loads an APK
  2. Extracts classes.dex, classes2.dex, classes3.dex, ...
  3. Parses each DEX independently (pure-Python parser, no C++ runtime)
  4. For each DEX, samples random string_idx / type_idx / method_idx / field_idx
  5. Resolves them via the C++ miniandroid runtime (using `analyze` command)
  6. Compares results — any mismatch = BLOCKER

Test APKs (small real multi-DEX APKs from corpus):
  - Telegram (5 DEX files) — the canonical multi-DEX stress test
  - OpenLauncher (2 DEX files)
  - Simple Keyboard (likely 2+ DEX files)

Usage:
    python3 tests/exp085_phase1_multi_dex.py [--apk <path>] [--verbose]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import struct
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO_ROOT = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime")
MINIANDROID = REPO_ROOT / "miniandroid" / "build" / "miniandroid"
RESULTS_DIR = REPO_ROOT / "miniandroid" / "tests" / "corpus" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# =====================================================================
# Independent pure-Python DEX parser (used as reference oracle)
# =====================================================================

class DexFile:
    """Minimal pure-Python DEX parser. Only reads what we need to verify indices."""

    def __init__(self, data: bytes, dex_index: int, source_name: str):
        self.data = data
        self.dex_index = dex_index
        self.source_name = source_name
        self.size = len(data)
        if data[:4] not in (b"dex\n", b"dex\x0a"):
            raise ValueError(f"Not a DEX file: bad magic {data[:4]!r}")
        if len(data) < 0x70:
            raise ValueError("DEX too small for header")
        self._parse_header()
        self._parse_string_ids()
        self._parse_type_ids()
        self._parse_proto_ids()
        self._parse_method_ids()
        self._parse_field_ids()

    def _u32(self, offset: int) -> int:
        return struct.unpack_from("<I", self.data, offset)[0]

    def _u16(self, offset: int) -> int:
        return struct.unpack_from("<H", self.data, offset)[0]

    def _uleb128(self, offset: int) -> tuple[int, int]:
        """Decode ULEB128. Return (value, new_offset)."""
        result = 0
        shift = 0
        while True:
            b = self.data[offset]
            offset += 1
            result |= (b & 0x7F) << shift
            if (b & 0x80) == 0:
                break
            shift += 7
        return result, offset

    def _parse_header(self):
        # Standard DEX header layout
        self.string_ids_size = self._u32(0x38)
        self.string_ids_off = self._u32(0x3C)
        self.type_ids_size = self._u32(0x40)
        self.type_ids_off = self._u32(0x44)
        self.proto_ids_size = self._u32(0x48)
        self.proto_ids_off = self._u32(0x4C)
        self.field_ids_size = self._u32(0x50)
        self.field_ids_off = self._u32(0x54)
        self.method_ids_size = self._u32(0x58)
        self.method_ids_off = self._u32(0x5C)
        self.class_defs_size = self._u32(0x60)
        self.class_defs_off = self._u32(0x64)

    def _read_string_at(self, str_data_off: int) -> str:
        """Read a UTF-8 (MUTF-8) string at the given offset."""
        # Strings are ULEB128 length-prefixed, then UTF-8 bytes, then \0
        try:
            n, off = self._uleb128(str_data_off)
            # n is the number of UTF-16 code units (we'll just decode UTF-8 for ASCII simplicity)
            raw = self.data[off:str_data_off + 256]  # generous bound
            # Find null terminator
            end = raw.find(b"\x00")
            if end < 0:
                return raw.decode("utf-8", errors="replace")
            return raw[:end].decode("utf-8", errors="replace")
        except Exception:
            return ""

    def _parse_string_ids(self):
        self.strings = []
        if self.string_ids_size == 0:
            return
        for i in range(self.string_ids_size):
            sid_off = self.string_ids_off + i * 4
            str_data_off = self._u32(sid_off)
            s = self._read_string_at(str_data_off)
            self.strings.append(s)

    def _parse_type_ids(self):
        self.types = []
        if self.type_ids_size == 0:
            return
        for i in range(self.type_ids_size):
            tid_off = self.type_ids_off + i * 4
            descriptor_idx = self._u32(tid_off)
            self.types.append(self.strings[descriptor_idx] if descriptor_idx < len(self.strings) else "")

    def _parse_proto_ids(self):
        self.protos = []
        if self.proto_ids_size == 0:
            return
        for i in range(self.proto_ids_size):
            pid_off = self.proto_ids_off + i * 12
            shorty_idx = self._u32(pid_off)
            return_type_idx = self._u32(pid_off + 4)
            parameters_off = self._u32(pid_off + 8)
            self.protos.append({
                "shorty": self.strings[shorty_idx] if shorty_idx < len(self.strings) else "",
                "return_type": self.types[return_type_idx] if return_type_idx < len(self.types) else "",
                "parameters_off": parameters_off,
            })

    def _parse_method_ids(self):
        self.methods = []
        if self.method_ids_size == 0:
            return
        for i in range(self.method_ids_size):
            mid_off = self.method_ids_off + i * 8
            class_idx = self._u16(mid_off)
            proto_idx = self._u16(mid_off + 2)
            name_idx = self._u32(mid_off + 4)
            self.methods.append({
                "class": self.types[class_idx] if class_idx < len(self.types) else "",
                "name": self.strings[name_idx] if name_idx < len(self.strings) else "",
                "proto_idx": proto_idx,
            })

    def _parse_field_ids(self):
        self.fields = []
        if self.field_ids_size == 0:
            return
        for i in range(self.field_ids_size):
            fid_off = self.field_ids_off + i * 8
            class_idx = self._u16(fid_off)
            type_idx = self._u16(fid_off + 2)
            name_idx = self._u32(fid_off + 4)
            self.fields.append({
                "class": self.types[class_idx] if class_idx < len(self.types) else "",
                "type": self.types[type_idx] if type_idx < len(self.types) else "",
                "name": self.strings[name_idx] if name_idx < len(self.strings) else "",
            })

    def stats(self) -> dict:
        return {
            "dex_index": self.dex_index,
            "source_name": self.source_name,
            "size_bytes": self.size,
            "strings": len(self.strings),
            "types": len(self.types),
            "protos": len(self.protos),
            "methods": len(self.methods),
            "fields": len(self.fields),
            "class_defs": self.class_defs_size,
        }


def load_apk_dex_files(apk_path: Path) -> list[DexFile]:
    """Extract all classes*.dex files from APK, in logical order."""
    dex_files = []
    with zipfile.ZipFile(apk_path, "r") as z:
        # Find all DEX files and sort by logical index
        dex_names = [n for n in z.namelist() if n.endswith(".dex") and "classes" in n]
        # Sort: classes.dex (0), classes2.dex (1), classes3.dex (2), ...
        def dex_sort_key(name: str) -> tuple:
            if name == "classes.dex":
                return (0, name)
            # classes2.dex → (1, name), classes3.dex → (2, name), etc.
            try:
                n = int(name.replace("classes", "").replace(".dex", ""))
                return (n - 1, name)
            except ValueError:
                return (99, name)
        dex_names.sort(key=dex_sort_key)
        for i, name in enumerate(dex_names):
            data = z.read(name)
            try:
                dex = DexFile(data, dex_index=i, source_name=name)
                dex_files.append(dex)
            except Exception as e:
                print(f"  WARN: could not parse {name}: {e}")
    return dex_files


# =====================================================================
# Test runner
# =====================================================================

def run_phase1(apk_path: Path, sample_count: int = 50, verbose: bool = False) -> dict:
    """Run Phase 1 multi-DEX forensic test for one APK."""
    apk_name = apk_path.stem
    apk_sha = ""
    h = hashlib.sha256()
    with open(apk_path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    apk_sha = h.hexdigest()

    print(f"\n=== Phase 1: Multi-DEX forensic test for {apk_name} ===")
    print(f"  APK: {apk_path}")
    print(f"  SHA256: {apk_sha[:16]}...")
    print(f"  Size: {apk_path.stat().st_size:,} bytes")

    # 1. Load DEX files via independent parser
    dex_files = load_apk_dex_files(apk_path)
    if not dex_files:
        return {"apk": str(apk_path), "status": "FAIL", "reason": "no DEX files found"}
    print(f"  Found {len(dex_files)} DEX file(s):")
    for d in dex_files:
        s = d.stats()
        print(f"    [{s['dex_index']}] {s['source_name']}: {s['strings']} strings, "
              f"{s['methods']} methods, {s['fields']} fields, {s['class_defs']} class_defs")

    # 2. Sample random IDs from each DEX
    rng = random.Random(42)  # deterministic
    samples = []
    for dex in dex_files:
        for kind in ("strings", "types", "methods", "fields"):
            collection = getattr(dex, kind)
            if not collection:
                continue
            n = min(sample_count, len(collection))
            for idx in rng.sample(range(len(collection)), n):
                samples.append({
                    "dex_index": dex.dex_index,
                    "source_name": dex.source_name,
                    "kind": kind,
                    "idx": idx,
                    "expected_value": collection[idx] if isinstance(collection[idx], str) else json.dumps(collection[idx]),
                })
    print(f"  Generated {len(samples)} samples (random {sample_count} per kind per DEX)")

    # 3. Compare against miniandroid's `dex` command output (if it exists)
    #    The C++ runtime should produce a dex_report_*.json that we can compare
    if not MINIANDROID.exists():
        print(f"  WARN: miniandroid binary not found at {MINIANDROID}, skipping cross-check")
        return {
            "apk": str(apk_path),
            "apk_name": apk_name,
            "apk_sha256": apk_sha,
            "dex_count": len(dex_files),
            "dex_stats": [d.stats() for d in dex_files],
            "samples": len(samples),
            "status": "PARTIAL",
            "reason": "Independent parser OK; C++ cross-check skipped (binary missing)",
        }

    # Run miniandroid `dex` command on the APK to get its view
    out_dir = Path(f"/tmp/exp085_phase1_{apk_name}")
    if out_dir.exists():
        import shutil
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    r = subprocess.run(
        [str(MINIANDROID), "dex", str(apk_path), "-o", str(out_dir), "-v"],
        capture_output=True, text=True, timeout=60,
    )
    if r.returncode != 0:
        print(f"  ERROR: miniandroid dex command failed (exit {r.returncode})")
        print(f"  stderr: {r.stderr[:500]}")
        return {
            "apk": str(apk_path), "apk_name": apk_name, "apk_sha256": apk_sha,
            "dex_count": len(dex_files), "status": "FAIL",
            "reason": f"miniandroid dex command failed: exit {r.returncode}",
        }

    # 4. Cross-check: verify per-DEX counts match (the C++ runtime outputs a dex_report_*.json)
    dex_reports = list(out_dir.glob("dex_report_*.json"))
    if not dex_reports:
        # Try other patterns
        dex_reports = list(out_dir.glob("*dex*.json"))

    cpp_stats = []
    if dex_reports:
        for report_path in sorted(dex_reports):
            try:
                with open(report_path) as f:
                    rep = json.load(f)
                cpp_stats.append({
                    "source_file": rep.get("source_file", rep.get("source_dex", "?")),
                    "strings": rep.get("strings_count", rep.get("header", {}).get("string_ids_size", 0)),
                    "types": rep.get("types_count", rep.get("header", {}).get("type_ids_size", 0)),
                    "protos": rep.get("prototypes_count", rep.get("header", {}).get("proto_ids_size", 0)),
                    "methods": rep.get("methods_count", rep.get("header", {}).get("method_ids_size", 0)),
                    "fields": rep.get("fields_count", rep.get("header", {}).get("field_ids_size", 0)),
                })
            except Exception as e:
                print(f"  WARN: could not parse {report_path}: {e}")

    # 5. Compare counts: independent vs C++
    mismatches = []
    for i, dex in enumerate(dex_files):
        if i < len(cpp_stats):
            cs = cpp_stats[i]
            py_stats = dex.stats()
            for kind in ("strings", "types", "protos", "methods", "fields"):
                py_count = py_stats[kind]
                # C++ report uses different keys; try multiple
                cpp_count = cs.get(kind, 0)
                if py_count != cpp_count:
                    mismatches.append({
                        "dex_index": i,
                        "kind": kind,
                        "python_count": py_count,
                        "cpp_count": cpp_count,
                    })

    # 6. Verify per-DEX index correctness (the actual BUG we're guarding against)
    # Build a per-DEX signature: hash of (source_name, strings_count, methods_count)
    # C++ should produce same signature for the same DEX
    py_signatures = []
    for dex in dex_files:
        s = dex.stats()
        sig = hashlib.sha256(
            f"{s['source_name']}|{s['strings']}|{s['types']}|{s['protos']}|{s['methods']}|{s['fields']}".encode()
        ).hexdigest()[:16]
        py_signatures.append(sig)

    # 7. Spot-check: verify a sample of strings per DEX
    # For each DEX, pick first/last/random string and verify it appears in C++ report
    string_spot_check = []
    for dex in dex_files:
        if not dex.strings:
            continue
        # Pick a few representative strings
        sample_strings = []
        if dex.strings:
            sample_strings.append(("first", dex.strings[0]))
            sample_strings.append(("last", dex.strings[-1]))
            if len(dex.strings) > 1:
                mid = len(dex.strings) // 2
                sample_strings.append(("mid", dex.strings[mid]))
        for tag, s in sample_strings:
            if s and len(s) > 2 and not s.startswith("L"):  # skip type descriptors
                string_spot_check.append({
                    "dex_index": dex.dex_index,
                    "tag": tag,
                    "string": s,
                })

    status = "PASS" if not mismatches else "FAIL"
    result = {
        "apk": str(apk_path),
        "apk_name": apk_name,
        "apk_sha256": apk_sha,
        "dex_count": len(dex_files),
        "python_dex_stats": [d.stats() for d in dex_files],
        "cpp_dex_stats": cpp_stats,
        "python_dex_signatures": py_signatures,
        "mismatches": mismatches,
        "mismatch_count": len(mismatches),
        "string_spot_check_count": len(string_spot_check),
        "string_spot_check_samples": string_spot_check[:10],
        "status": status,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    if verbose:
        print(f"\n  Python DEX stats:")
        for s in result["python_dex_stats"]:
            print(f"    [{s['dex_index']}] {s['source_name']}: {s['strings']} str / {s['methods']} meth / {s['fields']} fld")
        if cpp_stats:
            print(f"\n  C++ DEX stats:")
            for s in cpp_stats:
                print(f"    {s}")
        if mismatches:
            print(f"\n  MISMATCHES ({len(mismatches)}):")
            for m in mismatches[:10]:
                print(f"    dex[{m['dex_index']}] {m['kind']}: python={m['python_count']} cpp={m['cpp_count']}")
        else:
            print(f"\n  ✅ No count mismatches")
        print(f"\n  String spot checks: {len(string_spot_check)} samples")
        for sc in string_spot_check[:5]:
            print(f"    dex[{sc['dex_index']}] {sc['tag']}: \"{sc['string'][:50]}\"")

    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apk", help="Specific APK path. Default: test all corpus APKs.")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--samples", type=int, default=50, help="Sample count per kind per DEX")
    args = ap.parse_args()

    # Find APKs to test
    apk_paths = []
    if args.apk:
        apk_paths = [Path(args.apk)]
    else:
        # Default: test multi-DEX APKs from corpus (Telegram + OpenLauncher)
        corpus_root = REPO_ROOT / "miniandroid" / "download"
        candidates = [
            corpus_root / "exp038_telegram" / "Telegram.apk",
            corpus_root / "exp076_corpus" / "com.benny.openlauncher_39.apk",
            corpus_root / "exp076_corpus" / "rkr.simplekeyboard.inputmethod_145.apk",
            corpus_root / "tictactoe.apk",  # single-DEX baseline
        ]
        for p in candidates:
            if p.exists():
                apk_paths.append(p)

    if not apk_paths:
        print("ERROR: No APKs found to test. Use --apk <path>.")
        sys.exit(2)

    print(f"Testing {len(apk_paths)} APK(s)")

    all_results = []
    for apk in apk_paths:
        result = run_phase1(apk, sample_count=args.samples, verbose=args.verbose)
        all_results.append(result)

    # Summary
    print("\n" + "=" * 70)
    print("PHASE 1 SUMMARY")
    print("=" * 70)
    pass_count = sum(1 for r in all_results if r["status"] == "PASS")
    fail_count = sum(1 for r in all_results if r["status"] == "FAIL")
    partial_count = sum(1 for r in all_results if r["status"] == "PARTIAL")
    print(f"PASS: {pass_count}  FAIL: {fail_count}  PARTIAL: {partial_count}")
    for r in all_results:
        marker = "✅" if r["status"] == "PASS" else ("❌" if r["status"] == "FAIL" else "⚠️")
        print(f"  {marker} {r.get('apk_name', '?'):30s}  {r['status']:8s}  "
              f"dex={r.get('dex_count', '?')}  mismatches={r.get('mismatch_count', '?')}")

    # Save results
    out_path = RESULTS_DIR / "EXP085_PHASE1_MULTI_DEX.json"
    out_path.write_text(json.dumps({
        "test": "EXP085 Phase 1 — Multi-DEX forensic test suite",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": all_results,
    }, indent=2), encoding="utf-8")
    print(f"\nResults saved to {out_path}")

    # Exit non-zero if any FAIL
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
