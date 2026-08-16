#!/usr/bin/env python3
"""
EXP-042 PHASE 5 — Telegram DEX JNI Native-Method Inventory

Walks every DEX file inside the production Telegram APK
(/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/download/
exp038_telegram/Telegram.apk), parses the Dalvik DEX binary format directly
(no external deps), finds every Java method that has the ACC_NATIVE bit
(0x100) set, and writes:

  * miniandroid/docs/exp042/JNI_INVENTORY.md    (markdown table)
  * miniandroid/docs/exp042/JNI_INVENTORY.json   (machine-readable)

The DEX layout reference used here is the canonical Android source header
dalvik/libdex/DexFile.h:

  DexHeader            112 bytes  at offset 0
  string_ids[]         4 bytes each  (string_data_off: u32)
  type_ids[]           4 bytes each  (descriptor_idx: u32 -> string_ids)
  proto_ids[]         12 bytes each  (shorty_idx, return_type_idx,
                                       parameters_off)
  field_ids[]          8 bytes each  (class_idx u16, type_idx u16,
                                       name_idx u32)
  method_ids[]         8 bytes each  (class_idx u16, proto_idx u16,
                                       name_idx u32)
  class_defs[]        32 bytes each  (class_idx, access_flags,
                                       superclass_idx, interfaces_off,
                                       source_file_idx, annotations_off,
                                       class_data_off, static_values_off)

A method is native iff (access_flags & 0x100) != 0. Other access flags
used for context: PUBLIC=0x1, PRIVATE=0x2, PROTECTED=0x4, STATIC=0x8,
FINAL=0x10, SYNCHRONIZED=0x20, ABSTRACT=0x400.
"""

from __future__ import annotations

import json
import os
import struct
import sys
import zipfile
from collections import defaultdict
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

APK_PATH = (
    "/home/z/my-project/MiniAndroid-Compatibility-Runtime/"
    "miniandroid/download/exp038_telegram/Telegram.apk"
)
DOCS_DIR = (
    "/home/z/my-project/MiniAndroid-Compatibility-Runtime/"
    "miniandroid/docs/exp042"
)
MD_PATH = os.path.join(DOCS_DIR, "JNI_INVENTORY.md")
JSON_PATH = os.path.join(DOCS_DIR, "JNI_INVENTORY.json")

DEX_FILES = [
    "classes.dex",
    "classes2.dex",
    "classes3.dex",
    "classes4.dex",
    "classes5.dex",
]

# Access-flag bit (see com.android.dx.rop.code.AccessFlags)
ACC_PUBLIC       = 0x1
ACC_PRIVATE      = 0x2
ACC_PROTECTED    = 0x4
ACC_STATIC       = 0x8
ACC_FINAL        = 0x10
ACC_SYNCHRONIZED = 0x20
ACC_NATIVE       = 0x100
ACC_ABSTRACT     = 0x400

# DEX binary structures (all little-endian).
HEADER_FMT  = "<8sI20s" + "I" * 20   # 8+4+20+80 = 112 bytes
HEADER_SIZE  = struct.calcsize(HEADER_FMT)
assert HEADER_SIZE == 112, "DexHeader must be 112 bytes"

STRING_ID_FMT = "<I"             # 4 bytes  (string_data_off)
TYPE_ID_FMT   = "<I"             # 4 bytes  (descriptor_idx -> string_ids)
PROTO_ID_FMT  = "<III"           # 12 bytes (shorty_idx, return_type_idx, parameters_off)
METHOD_ID_FMT = "<HHI"           # 8 bytes  (class_idx u16, proto_idx u16, name_idx u32)
CLASS_DEF_FMT = "<IIIIIIII"      # 32 bytes (see module docstring)

NO_INDEX = 0xFFFFFFFF

# ---------------------------------------------------------------------------
# Low-level binary helpers
# ---------------------------------------------------------------------------

def read_uleb128(data: bytes, offset: int) -> Tuple[int, int]:
    """Read an unsigned LEB128 integer; return (value, new_offset)."""
    result = 0
    shift = 0
    while True:
        if offset >= len(data):
            break
        b = data[offset]
        offset += 1
        result |= (b & 0x7F) << shift
        if (b & 0x80) == 0:
            break
        shift += 7
    return result, offset


def read_mutf8_string(data: bytes, offset: int) -> Tuple[str, int]:
    """Read a string_data_item (uleb128 utf16 length + MUTF-8 bytes + NUL).

    Returns (decoded_string, new_offset_just_past_NUL).
    For typical DEX descriptors / method names this is plain ASCII so a
    plain utf-8 decode with replacement is enough.
    """
    _utf16_len, offset = read_uleb128(data, offset)
    end = offset
    while end < len(data) and data[end] != 0:
        end += 1
    raw = data[offset:end]
    try:
        s = raw.decode("utf-8", errors="replace")
    except Exception:
        s = "<decode-error>"
    # Skip past the NUL terminator.
    return s, end + 1


# ---------------------------------------------------------------------------
# Per-DEX parsing
# ---------------------------------------------------------------------------

class DexFile:
    """Minimal lazy DEX reader. Holds the raw bytes and parses only the
    sections needed for the native-method scan."""

    def __init__(self, name: str, data: bytes):
        self.name = name
        self.data = data
        if len(data) < HEADER_SIZE:
            raise ValueError(f"{name}: truncated DEX (< {HEADER_SIZE} bytes)")
        h = struct.unpack(HEADER_FMT, data[:HEADER_SIZE])
        (
            self.magic,
            self.checksum,
            self.signature,
            self.file_size,
            self.header_size,
            self.endian_tag,
            self.link_size,
            self.link_off,
            self.map_off,
            self.string_ids_size,
            self.string_ids_off,
            self.type_ids_size,
            self.type_ids_off,
            self.proto_ids_size,
            self.proto_ids_off,
            self.field_ids_size,
            self.field_ids_off,
            self.method_ids_size,
            self.method_ids_off,
            self.class_defs_size,
            self.class_defs_off,
            self.data_size,
            self.data_off,
        ) = h
        # Pre-parse the lookup tables we need.
        self._strings = self._parse_string_ids()
        self._types = self._parse_type_ids()
        self._protos = self._parse_proto_ids()
        self._methods = self._parse_method_ids()

    # ----- section readers --------------------------------------------------

    def _parse_string_ids(self) -> List[str]:
        if self.string_ids_size == 0:
            return []
        # string_ids is an array of u32 string_data_off
        raw = self.data[
            self.string_ids_off:
            self.string_ids_off + self.string_ids_size * 4
        ]
        offs = struct.unpack(f"<{self.string_ids_size}I", raw)
        out: List[str] = []
        for off in offs:
            if off == 0 or off >= len(self.data):
                out.append("<bad-string-off>")
                continue
            s, _ = read_mutf8_string(self.data, off)
            out.append(s)
        return out

    def _parse_type_ids(self) -> List[str]:
        if self.type_ids_size == 0:
            return []
        raw = self.data[
            self.type_ids_off:
            self.type_ids_off + self.type_ids_size * 4
        ]
        desc_idxs = struct.unpack(f"<{self.type_ids_size}I", raw)
        return [
            self._strings[i] if 0 <= i < len(self._strings) else "<bad-type-idx>"
            for i in desc_idxs
        ]

    def _parse_proto_ids(self) -> List[Tuple[int, int, int]]:
        if self.proto_ids_size == 0:
            return []
        raw = self.data[
            self.proto_ids_off:
            self.proto_ids_off + self.proto_ids_size * 12
        ]
        flat = struct.unpack(f"<{self.proto_ids_size * 3}I", raw)
        return [
            (flat[i], flat[i + 1], flat[i + 2])
            for i in range(0, len(flat), 3)
        ]

    def _parse_method_ids(self) -> List[Tuple[int, int, int]]:
        if self.method_ids_size == 0:
            return []
        raw = self.data[
            self.method_ids_off:
            self.method_ids_off + self.method_ids_size * 8
        ]
        out: List[Tuple[int, int, int]] = []
        # method_id is (u16 class_idx, u16 proto_idx, u32 name_idx).
        # We unpack per-record to avoid the struct native-alignment padding
        # that <HHI would NOT introduce here but is clearer to read.
        for i in range(self.method_ids_size):
            chunk = raw[i * 8:(i + 1) * 8]
            class_idx, proto_idx, name_idx = struct.unpack(METHOD_ID_FMT, chunk)
            out.append((class_idx, proto_idx, name_idx))
        return out

    # ----- accessors --------------------------------------------------------

    def get_method_class(self, method_idx: int) -> str:
        if not (0 <= method_idx < len(self._methods)):
            return f"<bad-method-idx:{method_idx}>"
        class_idx = self._methods[method_idx][0]
        if 0 <= class_idx < len(self._types):
            return self._types[class_idx]
        return f"<bad-class-idx:{class_idx}>"

    def get_method_name(self, method_idx: int) -> str:
        if not (0 <= method_idx < len(self._methods)):
            return f"<bad-method-idx:{method_idx}>"
        name_idx = self._methods[method_idx][2]
        if 0 <= name_idx < len(self._strings):
            return self._strings[name_idx]
        return f"<bad-name-idx:{name_idx}>"

    def get_method_shorty(self, method_idx: int) -> str:
        if not (0 <= method_idx < len(self._methods)):
            return "<bad-method-idx>"
        proto_idx = self._methods[method_idx][1]
        if not (0 <= proto_idx < len(self._protos)):
            return "<bad-proto-idx>"
        shorty_idx = self._protos[proto_idx][0]
        if 0 <= shorty_idx < len(self._strings):
            return self._strings[shorty_idx]
        return "<bad-shorty-idx>"

    # ----- class iteration --------------------------------------------------

    def iter_classes(self):
        """Yield (class_descriptor, class_access_flags, class_data_off)
        for every class_def in this DEX."""
        if self.class_defs_size == 0:
            return
        for i in range(self.class_defs_size):
            base = self.class_defs_off + i * 32
            chunk = self.data[base:base + 32]
            if len(chunk) < 32:
                break
            (
                class_idx,
                access_flags,
                _superclass_idx,
                _interfaces_off,
                _source_file_idx,
                _annotations_off,
                class_data_off,
                _static_values_off,
            ) = struct.unpack(CLASS_DEF_FMT, chunk)
            descriptor = (
                self._types[class_idx]
                if 0 <= class_idx < len(self._types)
                else f"<bad-class-idx:{class_idx}>"
            )
            yield descriptor, access_flags, class_data_off

    def iter_native_methods(self):
        """Yield (class_descriptor, class_access_flags, method_name,
        method_shorty, method_idx) for every native method in this DEX."""
        for descriptor, class_access, class_data_off in self.iter_classes():
            if class_data_off == 0:
                continue
            yield from self._iter_native_methods_in_class(
                descriptor, class_access, class_data_off
            )

    def _iter_native_methods_in_class(self, descriptor, class_access,
                                      class_data_off):
        data = self.data
        off = class_data_off
        # class_data_item header
        static_fields_size, off   = read_uleb128(data, off)
        instance_fields_size, off = read_uleb128(data, off)
        direct_methods_size, off  = read_uleb128(data, off)
        virtual_methods_size, off = read_uleb128(data, off)

        # Skip static_fields[] and instance_fields[] — we don't need them.
        for _ in range(static_fields_size + instance_fields_size):
            _fidx, off = read_uleb128(data, off)
            _aflg, off = read_uleb128(data, off)

        # Walk direct_methods[] then virtual_methods[]. method_idx is
        # delta-encoded: prev_method_idx starts at 0 for each method list.
        for size_label, size in (
            ("direct",  direct_methods_size),
            ("virtual", virtual_methods_size),
        ):
            prev_idx = 0
            for _ in range(size):
                idx_diff, off = read_uleb128(data, off)
                access_flags, off = read_uleb128(data, off)
                _code_off, off = read_uleb128(data, off)
                method_idx = prev_idx + idx_diff
                prev_idx = method_idx
                if (access_flags & ACC_NATIVE) == 0:
                    continue
                yield (
                    descriptor,
                    class_access,
                    self.get_method_name(method_idx),
                    self.get_method_shorty(method_idx),
                    method_idx,
                    size_label,
                )


# ---------------------------------------------------------------------------
# Library / priority guessing
# ---------------------------------------------------------------------------

def guess_library(class_desc: str) -> str:
    """Best-effort library attribution.

    Telegram bundles essentially all of its JNI glue into a single shared
    object, libtmessages.X.so (the X is the protobuf-schema version, 49 in
    the build under analysis). The class-name keyword tells us which
    *module* inside that .so the symbol lives in — useful context for
    later cross-checking against the ELF symbol table.
    """
    if "TgNet" in class_desc or "tgnet" in class_desc:
        return "libtmessages.49.so (tgnet module)"
    if "RLottie" in class_desc or "Lottie" in class_desc:
        return "libtmessages.49.so (rlottie module)"
    if "BotWebView" in class_desc or "WebView" in class_desc:
        return "libtmessages.49.so (botwebview module)"
    if "Secret" in class_desc:
        return "libtmessages.49.so (secret module)"
    if "Utilities" in class_desc:
        return "libtmessages.49.so (utilities module)"
    if "FileLog" in class_desc:
        return "libtmessages.49.so (filelog module)"
    if "NativeLoader" in class_desc:
        return "libtmessages.49.so (loader bootstrap)"
    if "MessagesController" in class_desc:
        return "libtmessages.49.so (controller module)"
    return "libtmessages.49.so"


# Classes whose native methods are on the critical startup path
# (LaunchActivity.onCreate -> postInitApplication).  Determined by reading
# docs/exp042/EXP042_TELEGRAM_COMPATIBILITY_MAP.md.
P0_CLASSES = (
    "ApplicationLoader",
    "LaunchActivity",
    "NativeLoader",
    "FileLog",
    "AndroidUtilities",
    "UserConfig",
    "SharedConfig",
    "NotificationCenter",
    "MessagesController",
    "MessagesStorage",
    "Theme",
)

# Classes that are exercised on the message send/receive path (after
# startup completes).  Includes TgNet ConnectionsManager, secret-chat
# crypto helpers, and file transfer workers.
P1_CLASSES = (
    "TgNet",
    "tgnet",
    "ConnectionsManager",
    "TLObject",
    "TLRPC",
    "RPCRequest",
    "SecretChat",
    "SecretStats",
    "Utilities",
    "FileLoader",
    "FileUploadOperation",
    "FileDownloadOperation",
    "SendMessagesHelper",
    "AudioRecoder",  # sic — typo in real Telegram source
    "AudioPlayer",
    "VideoPlayer",
    "GpuIntegration",
)


def guess_priority(class_desc: str) -> str:
    """Priority bucket — P0 (startup), P1 (msg send/recv), P2 (rare)."""
    for needle in P0_CLASSES:
        if needle in class_desc:
            return "P0"
    for needle in P1_CLASSES:
        if needle in class_desc:
            return "P1"
    return "P2"


# ---------------------------------------------------------------------------
# Top-level driver
# ---------------------------------------------------------------------------

def scan_apk(apk_path: str) -> Dict:
    """Scan every DEX in the APK and return a structured inventory."""
    inventory: List[Dict] = []
    dex_stats: Dict[str, Dict] = {}
    total_classes_scanned = 0

    with zipfile.ZipFile(apk_path, "r") as z:
        available = set(z.namelist())
        for dex_name in DEX_FILES:
            if dex_name not in available:
                print(f"  [WARN] {dex_name} not in APK, skipping", file=sys.stderr)
                continue
            raw = z.read(dex_name)
            dex = DexFile(dex_name, raw)
            classes_in_dex = dex.class_defs_size
            total_classes_scanned += classes_in_dex
            native_count = 0
            classes_with_native = set()
            for (
                descriptor,
                class_access,
                method_name,
                shorty,
                method_idx,
                method_kind,
            ) in dex.iter_native_methods():
                native_count += 1
                classes_with_native.add(descriptor)
                inventory.append({
                    "class": descriptor,
                    "method": method_name,
                    "shorty": shorty,
                    "library": guess_library(descriptor),
                    "dex": dex_name,
                    "priority": guess_priority(descriptor),
                    "class_access_flags": class_access,
                    "method_idx": method_idx,
                    "method_kind": method_kind,
                })
            dex_stats[dex_name] = {
                "file_size_bytes": len(raw),
                "classes": classes_in_dex,
                "native_methods": native_count,
                "classes_with_native": len(classes_with_native),
                "strings": dex.string_ids_size,
                "types": dex.type_ids_size,
                "protos": dex.proto_ids_size,
                "methods": dex.method_ids_size,
                "fields": dex.field_ids_size,
            }
            print(
                f"  [OK] {dex_name}: {classes_in_dex} classes, "
                f"{native_count} native methods across "
                f"{len(classes_with_native)} classes",
                file=sys.stderr,
            )

    # Class-level aggregation
    by_class = defaultdict(list)
    for entry in inventory:
        by_class[entry["class"]].append(entry)
    class_summary = sorted(
        ((cls, len(items)) for cls, items in by_class.items()),
        key=lambda x: (-x[1], x[0]),
    )

    # Library and priority distribution
    lib_dist = defaultdict(int)
    pri_dist = defaultdict(int)
    for entry in inventory:
        lib_dist[entry["library"]] += 1
        pri_dist[entry["priority"]] += 1

    return {
        "apk": apk_path,
        "total_classes_scanned": total_classes_scanned,
        "total_native_methods": len(inventory),
        "total_classes_with_native_methods": len(by_class),
        "dex_stats": dex_stats,
        "class_summary": class_summary,
        "library_distribution": dict(sorted(lib_dist.items(),
                                            key=lambda x: -x[1])),
        "priority_distribution": dict(sorted(pri_dist.items())),
        "inventory": inventory,
    }


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def render_markdown(result: Dict) -> str:
    out: List[str] = []
    out.append("# EXP-042 Phase 5 — Telegram JNI Native-Method Inventory")
    out.append("")
    out.append(
        "Generated by `miniandroid/tools/exp042_jni_inventory.py`. Scans "
        "every DEX file inside the production Telegram APK and lists every "
        "Java method whose `access_flags` has the `ACC_NATIVE` (0x100) bit "
        "set."
    )
    out.append("")

    out.append("## 1. Summary")
    out.append("")
    out.append(f"- **APK**: `{result['apk']}`")
    out.append(f"- **DEX files scanned**: "
               f"{len(result['dex_stats'])} of 5 expected")
    out.append(f"- **Total classes scanned**: "
               f"{result['total_classes_scanned']:,}")
    out.append(f"- **Total native methods found**: "
               f"{result['total_native_methods']:,}")
    out.append(f"- **Total classes with native methods**: "
               f"{result['total_classes_with_native_methods']:,}")
    out.append("")

    out.append("## 2. Per-DEX Breakdown")
    out.append("")
    out.append("| DEX file | Size (B) | Classes | Strings | Types | Protos | "
               "Fields | Methods | Native methods | Classes w/ native |")
    out.append("|----------|---------:|--------:|--------:|------:|-------:|"
               "-------:|--------:|---------------:|-------------------:|")
    for dex_name, st in result["dex_stats"].items():
        out.append(
            f"| {dex_name} | {st['file_size_bytes']:,} | {st['classes']:,} | "
            f"{st['strings']:,} | {st['types']:,} | {st['protos']:,} | "
            f"{st['fields']:,} | {st['methods']:,} | {st['native_methods']} | "
            f"{st['classes_with_native']} |"
        )
    out.append("")

    out.append("## 3. Top Classes by Native-Method Count")
    out.append("")
    out.append("| Rank | Class | Native methods | Library (guess) | Priority |")
    out.append("|-----:|-------|---------------:|-----------------|:--------:|")
    for rank, (cls, n) in enumerate(result["class_summary"][:25], 1):
        lib = guess_library(cls)
        pri = guess_priority(cls)
        out.append(f"| {rank} | `{cls}` | {n} | {lib} | {pri} |")
    out.append("")

    out.append("## 4. Library-Attribution Distribution")
    out.append("")
    out.append("| Library (guess) | Native methods |")
    out.append("|-----------------|---------------:|")
    for lib, n in result["library_distribution"].items():
        out.append(f"| {lib} | {n} |")
    out.append("")

    out.append("## 5. Priority Distribution")
    out.append("")
    out.append(
        "- **P0** — class is on Telegram's startup path "
        "(`LaunchActivity.onCreate` / `ApplicationLoader.postInitApplication`)."
    )
    out.append(
        "- **P1** — class is used during message send/receive "
        "(TgNet, secret-chat crypto, file transfer workers)."
    )
    out.append("- **P2** — class is rarely used (Lottie, BotWebView, etc.).")
    out.append("")
    out.append("| Priority | Native methods |")
    out.append("|:--------:|---------------:|")
    for pri, n in result["priority_distribution"].items():
        out.append(f"| {pri} | {n} |")
    out.append("")

    out.append("## 6. Full Inventory")
    out.append("")
    out.append(
        "Sorted by (priority, class, method). All "
        f"{result['total_native_methods']} native methods are listed."
    )
    out.append("")
    out.append(
        "| Class | Method | Prototype (shorty) | Library (guess) | "
        "DEX file | Priority |"
    )
    out.append("|-------|--------|--------------------|------------------|"
               "----------|:--------:|")

    # Sort: P0 first, then P1, then P2; within priority by class then method.
    pri_order = {"P0": 0, "P1": 1, "P2": 2}
    sorted_inv = sorted(
        result["inventory"],
        key=lambda e: (pri_order.get(e["priority"], 9),
                       e["class"],
                       e["method"]),
    )
    for e in sorted_inv:
        # Escape pipe characters in any field (class descriptors won't
        # contain them, but method/shorty could theoretically).
        cls = e["class"].replace("|", "\\|")
        mtd = e["method"].replace("|", "\\|")
        sho = e["shorty"].replace("|", "\\|")
        out.append(
            f"| `{cls}` | `{mtd}` | `{sho}` | {e['library']} | "
            f"{e['dex']} | {e['priority']} |"
        )
    out.append("")

    out.append("## 7. Methodology")
    out.append("")
    out.append(
        "1. APK opened as ZIP, each `classesN.dex` read into memory."
    )
    out.append(
        "2. DEX header parsed at offset 0 (112 bytes, little-endian)."
    )
    out.append(
        "3. `string_ids[]`, `type_ids[]`, `proto_ids[]`, `method_ids[]` "
        "and `class_defs[]` sections loaded."
    )
    out.append(
        "4. For each `class_def_item`, `class_data_off` resolved and the "
        "ULEB128-encoded `class_data_item` parsed."
    )
    out.append(
        "5. Both `direct_methods[]` and `virtual_methods[]` lists walked. "
        "For each `encoded_method`, `access_flags & 0x100` decides if the "
        "method is native."
    )
    out.append(
        "6. Native methods are resolved back to (class, name, shorty) via "
        "`method_ids[]` -> `proto_ids[]` -> `string_ids[]`."
    )
    out.append(
        "7. Library attribution and priority bucket are heuristic, "
        "based on the declaring-class descriptor (see the python source for "
        "the exact keyword tables)."
    )
    out.append("")

    return "\n".join(out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    os.makedirs(DOCS_DIR, exist_ok=True)

    if not os.path.exists(APK_PATH):
        print(f"ERROR: APK not found at {APK_PATH}", file=sys.stderr)
        return 2

    print(f"Scanning {APK_PATH} ...", file=sys.stderr)
    result = scan_apk(APK_PATH)

    print(f"\nWriting {MD_PATH} ...", file=sys.stderr)
    md_text = render_markdown(result)
    with open(MD_PATH, "w", encoding="utf-8") as f:
        f.write(md_text)

    print(f"Writing {JSON_PATH} ...", file=sys.stderr)
    # class_summary is a list of [class, count] tuples; JSON-serialise as lists.
    json_payload = {
        "apk": result["apk"],
        "total_classes_scanned": result["total_classes_scanned"],
        "total_native_methods": result["total_native_methods"],
        "total_classes_with_native_methods":
            result["total_classes_with_native_methods"],
        "dex_stats": result["dex_stats"],
        "class_summary": [
            {"class": cls, "native_method_count": n}
            for cls, n in result["class_summary"]
        ],
        "library_distribution": result["library_distribution"],
        "priority_distribution": result["priority_distribution"],
        "inventory": result["inventory"],
    }
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(json_payload, f, indent=2, ensure_ascii=False)

    print("\n=== Done ===", file=sys.stderr)
    print(f"  Total native methods:     "
          f"{result['total_native_methods']}", file=sys.stderr)
    print(f"  Classes with native:      "
          f"{result['total_classes_with_native_methods']}", file=sys.stderr)
    print(f"  Top class:                "
          f"{result['class_summary'][0][0]} "
          f"({result['class_summary'][0][1]} methods)", file=sys.stderr)
    print(f"  Markdown written to:      {MD_PATH}", file=sys.stderr)
    print(f"  JSON written to:         {JSON_PATH}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
