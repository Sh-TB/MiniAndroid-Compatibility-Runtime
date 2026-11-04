#!/usr/bin/env python3
"""s159_perfops_ab.py — S159: mechanism check for the field-slot overlay.

The S159 dooz run showed face byte-identical and api_trace near-identical
(+24 bytes / same counts) with wall flat (+0.9%) — so whether the overlay
actually reduced FIELD-OP cost needs the phase-clock metric, not the wall.
Runs dooz E5 (fresh store each) with MINIANDROID_PERF_PHASES=1 on BOTH the
S157-B ref (908d5ba6) and the overlay binary (fde53d47), parses [PERF-OPS]
rows from stderr, and A/Bs ticks-per-call on the field op families.

Usage: python3 scripts/s159_perfops_ab.py ref|w3|collect
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

BASE = Path("/home/z/my-project")
OUT = BASE / "run_s159_fieldslot"
EVID = BASE / "evidence/s156_record_loop"

REF = BASE / "upload/_ma_local_backup/miniandroid_s157b_gated_908d5ba61aa62485.bin"
W3 = BASE / "upload/_ma_local_backup/miniandroid_fieldslot_303ad5b1_fde53d47bd5b3845.bin"
APK = BASE / "upload/canonical_apks/io.github.yamin8000.dooz_23.apk"


def run_perf(tag, bin_path, max_seconds=110):
    store = OUT / f"store_perf_{tag}/data"
    subprocess.run(["rm", "-rf", str(store)], check=False)
    r = subprocess.run([str(bin_path), "install", str(APK),
                        "--data-root", str(store)],
                       capture_output=True, timeout=300)
    assert r.returncode == 0, r.stderr[-300:]
    rundir = OUT / f"perf_{tag}"
    subprocess.run(["rm", "-rf", str(rundir)], check=False)
    env = dict(os.environ)
    env["MINIANDROID_PERF_PHASES"] = "1"
    env.pop("MINIANDROID_S155_APPLY", None)
    t0 = time.time()
    r = subprocess.run(
        [str(bin_path), "run", "--execution-mode", "real-dalvik",
         "--package", "io.github.yamin8000.dooz", "--data-root", str(store),
         "--trace", "--max-seconds", str(max_seconds), "--frames", "30",
         "-o", str(rundir)],
        env=env, capture_output=True, text=True, timeout=max_seconds + 90)
    wall = round(time.time() - t0, 1)
    err = OUT / f"perf_{tag}.stderr.log"
    err.write_text(r.stderr, errors="replace")
    ops = {}
    for m in re.finditer(
            r"op=(0x[0-9a-f]+)\s+calls=(\d+)\s+ticks=(\d+)", r.stderr):
        ops[m.group(1)] = {"calls": int(m.group(2)),
                           "tpc": round(int(m.group(3)) / int(m.group(2)), 1)}
    row = {"tag": tag, "wall_s": wall, "ops": ops,
           "binary": Path(bin_path).name}
    print(f"[{tag}] wall={wall}s ops_found={len(ops)}")
    for k, v in sorted(ops.items()):
        print(f"  {k}: calls={v['calls']:,} tpc={v['tpc']}")
    return row


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "collect"
    p = EVID / "S159_PERFOPS_AB.json"
    rows = json.loads(p.read_text()) if p.exists() else {}
    if mode == "ref":
        rows["ref"] = run_perf("ref", REF)
    elif mode == "w3":
        rows["w3"] = run_perf("w3", W3)
    json.dump(rows, open(p, "w"), indent=1)
    if mode == "collect" and "ref" in rows and "w3" in rows:
        print("\nA/B (tpc: ref -> w3, %):")
        for k in sorted(set(rows["ref"]["ops"]) & set(rows["w3"]["ops"])):
            a, b = rows["ref"]["ops"][k]["tpc"], rows["w3"]["ops"][k]["tpc"]
            d = (b - a) / a * 100 if a else 0
            ca, cb = rows["ref"]["ops"][k]["calls"], rows["w3"]["ops"][k]["calls"]
            print(f"  {k}: {a} -> {b} ({d:+.1f}%)  calls {ca:,} -> {cb:,}")


if __name__ == "__main__":
    main()
