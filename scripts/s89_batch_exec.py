#!/usr/bin/env python3
"""s89_batch_exec.py — S89 §5 batch execution: run a bounded set of scanned
corpus titles through the engine (obs pass), classify with the S85 visual
gate, group first-divergences, emit run/s89/batch/EXEC_RESULTS.json.

Batching law (§18): after each batch, divergence families are grouped and
counted — a family with >=3 members becomes the next root-cause attack.
"""
import glob
import hashlib
import json
import os
import subprocess
import sys

sys.path.insert(0, "/home/z/my-project/scripts")
from s81_visual_audit import audit_frame

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
OUT = f"{ROOT}/run/s89/batch"
APKS = f"{OUT}/apks"
MIRROR = "https://ftp.lysator.liu.se/pub/fdroid/repo/"
os.makedirs(APKS, exist_ok=True)

def uniq_colors(png):
    try:
        m = audit_frame(png)
        return m.get("UNIQUE_COLORS", -1)
    except Exception:
        return -1

def engine_run(apk, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", "6", "--frame-delay", "250",
           "--max-seconds", "150", "-o", out_dir, apk]
    log = out_dir + ".log"
    with open(log, "w") as lf:
        try:
            rc = subprocess.call(cmd, stdout=lf, stderr=lf,
                                 timeout=200)
        except subprocess.TimeoutExpired:
            rc = -1
    errors = 0
    first_div = ""
    for line in open(log, encoding="utf-8", errors="replace"):
        if "[SYNTH-EXC]" in line:
            errors += 1
            if not first_div:
                # signature: exception type + method + pc
                seg = line.split("SYNTH-EXC")[-1]
                first_div = seg.strip()[:140]
    frames = sorted(glob.glob(f"{out_dir}/frames/frame_*.png"))
    uniques = [uniq_colors(f) for f in frames[-3:]]
    return {"rc": rc, "exceptions": errors, "first_divergence": first_div,
            "frames": len(frames), "uniq_tail": uniques, "log": log}

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    profiles = json.load(open(f"{ROOT}/run/s88/corpus/profiles.json"))
    results = json.load(open(f"{OUT}/EXEC_RESULTS.json")) if \
        os.path.exists(f"{OUT}/EXEC_RESULTS.json") else {}
    # order: smallest first, games and apps interleaved; skip already run
    cands = [(p, pr) for p, pr in profiles.items()
             if pr.get("sha256") and p not in results]
    cands.sort(key=lambda x: x[1].get("size", 9e9))
    done = 0
    for pkg, prof in cands:
        if done >= n:
            break
        url = prof.get("url", "")
        name = url.rsplit("/", 1)[-1] if url else f"{pkg}_{prof.get('vc')}.apk"
        dst = f"{APKS}/{pkg}.apk"
        rc = subprocess.run(["curl", "-s", "-L", "-m", "75", "-A",
                             "MiniAndroid-S89/1.0", "-o", dst,
                             MIRROR + name]).returncode
        if rc != 0 or not os.path.exists(dst) or \
                os.path.getsize(dst) < 10000:
            if os.path.exists(dst):
                os.remove(dst)
            results[pkg] = {"state": "DOWNLOAD_BLOCKED"}
            print(f"  {pkg}: blocked", flush=True)
        else:
            r = engine_run(dst, f"{OUT}/{pkg}")
            r["sha256"] = hashlib.sha256(
                open(dst, "rb").read()).hexdigest()[:16]
            r["kind"] = prof.get("kind", "app")
            r["libs"] = prof.get("libs", {})
            results[pkg] = r
            tail = max(r["uniq_tail"]) if r["uniq_tail"] else -1
            state = ("NONTRIVIAL_RENDER" if tail > 40 else
                     "PARTIAL_RENDER" if tail > 2 else
                     "LOAD_FAILED" if r["rc"] != 0 else "SHELL_RENDER")
            print(f"  {pkg}: rc={r['rc']} frames={r['frames']} "
                  f"uniq={tail} {state} exc={r['exceptions']}", flush=True)
            os.remove(dst)
        done += 1
        json.dump(results, open(f"{OUT}/EXEC_RESULTS.json", "w"), indent=1)

    # divergence family grouping
    from collections import Counter
    fams = Counter()
    for pkg, r in results.items():
        d = r.get("first_divergence", "")
        if d:
            fams[d[:90]] += 1
    print("=== TOP DIVERGENCE FAMILIES (this batch) ===", flush=True)
    for k, v in fams.most_common(10):
        print(f"  {v:3d}  {k}", flush=True)

if __name__ == "__main__":
    main()
