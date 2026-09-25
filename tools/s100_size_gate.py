#!/usr/bin/env python3
"""s100_size_gate.py — Binary Size Gate (S98-FUTURE §9/§10/§12, S100 §19).

Measures the canonical runtime binary with the strongest available
toolchain facilities (size(1), nm, strip+gzip) and reports:

    UNSTRIPPED_SIZE STRIPPED_SIZE COMPRESSED_SIZE
    TEXT RODATA DATA BSS
    SYMBOL_COUNT
    SIZE_DELTA_BYTES / SIZE_DELTA_PERCENT vs docs/SIZE_BASELINE.json

Gates (configurable, evidence-based — never arbitrary-blocking):
  * core growth > warn threshold  -> WARN
  * core growth > fail threshold  -> FAIL
  * DEPENDENCY_AMPLIFICATION      -> flags small-source/huge-binary growth
    (root-cause required; exact attribution only claimed with a linker map)

Usage:
    python3 tools/s100_size_gate.py                 # measure + gate
    python3 tools/s100_size_gate.py --update-baseline
"""
import argparse
import gzip
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(REPO, "miniandroid", "build", "miniandroid")
BASELINE = os.path.join(REPO, "docs", "SIZE_BASELINE.json")
OUT = os.path.join(REPO, "run", "s100", "size_gate.json")

RULES = {"core_growth_warn_bytes": 150000, "core_growth_fail_bytes": 500000,
         "amplification_ratio": 100}


def measure(binary):
    m = {}
    m["unstripped_bytes"] = os.path.getsize(binary)
    size_out = subprocess.run(["size", binary], capture_output=True, text=True)
    lines = size_out.stdout.strip().splitlines()
    if len(lines) >= 2:
        parts = lines[1].split()
        m["text"], m["data"], m["bss"] = int(parts[0]), int(parts[1]), int(parts[2])
        m["dec"] = int(parts[3])
    ro = subprocess.run(["readelf", "-S", "-W", binary], capture_output=True,
                        text=True).stdout
    for line in ro.splitlines():
        if ".rodata" in line and "PROGBITS" in line:
            m["rodata"] = int(line.split()[5], 16)  # readelf -W: Name Type Address Off SIZE ...
            break
    nm = subprocess.run(["nm", binary], capture_output=True, text=True).stdout
    m["symbol_count_nm"] = sum(1 for _ in nm.splitlines())
    with tempfile.NamedTemporaryFile(suffix=".strip", delete=False) as tf:
        tmp = tf.name
    subprocess.run(["cp", binary, tmp])
    subprocess.run(["strip", tmp])
    m["stripped_bytes"] = os.path.getsize(tmp)
    with open(tmp, "rb") as f:
        m["compressed_gzip_bytes"] = len(gzip.compress(f.read()))
    os.unlink(tmp)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--update-baseline", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(BIN):
        print(f"FAIL: binary missing: {BIN}")
        return 2
    m = measure(BIN)
    verdict = {"measured": m}
    status = "PASS"

    if os.path.exists(BASELINE):
        with open(BASELINE) as f:
            base = json.load(f)["measured"]
        d_stripped = m["stripped_bytes"] - base["stripped_bytes"]
        d_text = m["text"] - base["text"]
        pct = (d_stripped / base["stripped_bytes"] * 100.0) if base["stripped_bytes"] else 0.0
        verdict["delta"] = {
            "stripped_bytes": d_stripped, "text_bytes": d_text,
            "stripped_percent": round(pct, 3),
        }
        if d_stripped > RULES["core_growth_fail_bytes"]:
            status = "FAIL"
        elif d_stripped > RULES["core_growth_warn_bytes"]:
            status = "WARN"
        verdict["delta"]["flags"] = []
        if d_stripped > RULES["core_growth_warn_bytes"]:
            verdict["delta"]["flags"].append(
                "CORE_GROWTH_OVER_WARN — attribute per capability before close")
        if d_text > 0 and RULES["amplification_ratio"] * 1024 < d_text:
            verdict["delta"]["flags"].append(
                "DEPENDENCY_AMPLIFICATION_SUSPECT — root-cause the growth "
                "(small source addition -> disproportionate binary growth, S98 §12)")
    else:
        verdict["delta"] = {"note": "no baseline yet"}

    verdict["status"] = status
    verdict["rules"] = RULES
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(verdict, f, indent=2)

    if args.update_baseline:
        with open(BASELINE) as f:
            b = json.load(f)
        b["measured"] = m
        with open(BASELINE, "w") as f:
            json.dump(b, f, indent=2)
        print(f"BASELINE UPDATED: {BASELINE}")

    print(f"SIZE GATE: {status}")
    print(f"  unstripped {m['unstripped_bytes']}  stripped {m['stripped_bytes']}"
          f"  gzip {m['compressed_gzip_bytes']}")
    print(f"  text {m['text']}  rodata {m.get('rodata')}  data {m['data']}"
          f"  bss {m['bss']}  symbols {m['symbol_count_nm']}")
    if "stripped_bytes" in verdict.get("delta", {}):
        print(f"  delta stripped {verdict['delta']['stripped_bytes']:+d}"
              f" ({verdict['delta']['stripped_percent']:+.3f}%)"
              f"  text {verdict['delta']['text_bytes']:+d}")
        for fl in verdict["delta"].get("flags", []):
            print(f"  FLAG: {fl}")
    return 0 if status == "PASS" else (1 if status == "WARN" else 2)


if __name__ == "__main__":
    sys.exit(main())
