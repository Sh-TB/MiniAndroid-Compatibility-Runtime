#!/usr/bin/env python3
"""s85_run_new.py — S85 execution campaign for the NEW-50 titles.

Same evidence protocol as S84 (s84_run_new.py):
  PASS 1 (obs):   real-dalvik, 8 frames @300ms
  PASS 2 (click): + --click-test
Per title: rc, Errors, frames, S81 visual-audit level, click probed /
state_changed, frame SHAs. rc=0 alone is never success.

Chunked-foreground friendly: resume-safe (report.json grows), each
invocation stops after BUDGET seconds or when all titles are done.
"""
import glob
import hashlib
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s81_visual_audit import audit_frame, level_of, apk_resource_counts

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
OUT = f"{ROOT}/run/s85"
MANIFEST = f"{OUT}/manifest_new.json"
REPORT = f"{OUT}/report.json"
BUDGET = 420


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def engine_run(apk, out_dir, click=False, timeout=300):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", "8", "--frame-delay", "300", "--max-seconds", "240",
           "-o", out_dir, apk]
    if click:
        cmd.append("--click-test")
    log = out_dir + ("_click.log" if click else "_obs.log")
    with open(log, "w") as lf:
        try:
            rc = subprocess.call(cmd, stdout=lf, stderr=lf, timeout=timeout)
        except subprocess.TimeoutExpired:
            rc = -1
    errors, clickline = "?", ""
    for line in open(log, encoding="utf-8", errors="replace"):
        if line.startswith("Errors:"):
            errors = line.split(":", 1)[1].strip()
        if "[CLICK-TEST] done:" in line:
            clickline = line.strip()
    frames = sorted(glob.glob(f"{out_dir}/frames/frame_*.png"))
    return {"rc": rc, "errors": errors, "log": log, "frames": frames,
            "clickline": clickline}


def run_title(t):
    pkg = t["package"]
    apk = f"{OUT}/apks/{t['file']}"
    base = f"{OUT}/{pkg}"
    rec = {"package": pkg, "kind": t["kind"], "version": t["version"],
           "vc": t["vc"], "apk_sha256": t["sha256"], "source": t["source"],
           "upstream": t.get("upstream", "")}
    if not os.path.exists(apk):
        rec.update({"status": "APK-MISSING", "rc": -2})
        return rec

    obs = engine_run(apk, f"{base}/obs", click=False)
    clk = engine_run(apk, f"{base}/click", click=True)

    rec["rc_obs"] = obs["rc"]
    rec["errors_obs"] = obs["errors"]
    rec["rc_click"] = clk["rc"]
    rec["errors_click"] = clk["errors"]
    rec["frames_obs"] = len(obs["frames"])
    rec["frames_click"] = len(clk["frames"])

    probed = changed = -1
    if clk["clickline"]:
        for tok in clk["clickline"].split():
            if tok.startswith("probed="):
                probed = int(tok.split("=")[1])
            if tok.startswith("state_changed="):
                changed = int(tok.split("=")[1])
    rec["click_probed"] = probed
    rec["click_state_changed"] = changed

    if obs["frames"]:
        m = audit_frame(obs["frames"][-1])
        lvl, name = level_of(m)
        m["LEVEL"] = lvl
        m["LEVEL_NAME"] = name
        m.update(apk_resource_counts(apk))
        rec["visual"] = m
        rec["final_frame"] = obs["frames"][-1]
        rec["final_frame_sha256"] = sha256(obs["frames"][-1])
    if clk["frames"]:
        rec["click_final_frame"] = clk["frames"][-1]
        rec["click_final_frame_sha256"] = sha256(clk["frames"][-1])

    rec["state_change_evidence"] = bool(
        changed > 0 or
        (rec.get("final_frame_sha256") and rec.get("click_final_frame_sha256")
         and rec["final_frame_sha256"] != rec["click_final_frame_sha256"]))

    # honest status vocabulary (S84 law)
    vis = rec.get("visual", {})
    lvl = vis.get("LEVEL", 0)
    if rec["state_change_evidence"] and rec["frames_click"] > 0:
        rec["status"] = "VERIFIED-INTERACTIVE-CANDIDATE"
    elif lvl >= 2 and rec["frames_obs"] > 0:
        rec["status"] = "VERIFIED"
    elif lvl == 1:
        rec["status"] = "OBSERVED"
    else:
        rec["status"] = "OBSERVED" if rec["frames_obs"] > 0 else "LOADED"
    print(f"DONE {pkg} rc={rec['rc_obs']} lvl={lvl} frames={rec['frames_obs']} "
          f"state={rec['state_change_evidence']} -> {rec['status']}", flush=True)
    return rec


def main():
    manifest = json.load(open(MANIFEST))["titles"]
    done = set()
    if os.path.exists(REPORT):
        try:
            done = {r["package"] for r in json.load(open(REPORT))["titles"]}
        except Exception:
            pass
    todo = [t for t in manifest if t["package"] not in done]
    print(f"S85 run: {len(todo)} to go ({len(done)} already done)", flush=True)
    t0 = time.time()

    recs = []
    BATCH = 8  # 2x4 workers per batch; budget checked between batches
    for i in range(0, len(todo), BATCH):
        if time.time() - t0 > BUDGET and i > 0:
            print(f"TIME-BUDGET hit ({len(recs)} recorded this invocation)",
                  flush=True)
            break
        batch = todo[i:i + BATCH]
        with ThreadPoolExecutor(max_workers=4) as ex:
            for r in ex.map(run_title, batch):
                recs.append(r)

    # merge with existing report
    merged = []
    if os.path.exists(REPORT):
        try:
            merged = json.load(open(REPORT))["titles"]
        except Exception:
            merged = []
    merged += recs
    json.dump({"wave": "S85", "count": len(merged), "titles": merged},
              open(REPORT, "w"), indent=1)
    print(f"report: {REPORT} ({len(merged)} recorded)", flush=True)


if __name__ == "__main__":
    main()
