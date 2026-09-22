#!/usr/bin/env python3
"""s84_run_new.py — S84 NEW-50 execution campaign (user mandate §5-§6).

For each of the 50 fresh titles (run/s84/manifest_new.json):
  PASS 1 (obs):   --execution-mode real-dalvik --frames 8 --frame-delay 300
  PASS 2 (click): same + --click-test  (real clicks on clickable views)
Per title records: rc, engine Errors count, frames, visual audit metrics,
rendering LEVEL (L0..L5 ladder of s81_visual_audit), CLICK-TEST summary
(probed / state_changed / frames_saved), frame SHAs.

NOTES (§6 user law): rc=0 alone is NEVER success. Success vocabulary:
LOADED / LAUNCHED / UI_OBSERVED / RENDERED / INTERACTED / STATE_CHANGED /
SCREENSHOT_CAPTURED derived from evidence below.

Parallel: 4 workers. Output: run/s84/report.json (merged incrementally).
"""
import glob
import hashlib
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s81_visual_audit import audit_frame, level_of, apk_resource_counts

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
OUT = f"{ROOT}/run/s84"
MANIFEST = f"{OUT}/manifest_new.json"
REPORT = f"{OUT}/report.json"


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

    # interaction evidence from engine's own CLICK-TEST summary
    probed = changed = -1
    if clk["clickline"]:
        try:
            for tok in clk["clickline"].split():
                if tok.startswith("probed="):
                    probed = int(tok.split("=")[1])
                if tok.startswith("state_changed="):
                    changed = int(tok.split("=")[1])
        except Exception:
            pass
    rec["click_probed"] = probed
    rec["click_state_changed"] = changed

    # visual audit on last obs frame
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

    # state-change: engine reported >0 views changed OR click-run final frame
    # differs from obs final frame
    rec["state_change_evidence"] = bool(
        changed > 0 or
        (rec.get("final_frame_sha256") and rec.get("click_final_frame_sha256")
         and rec["final_frame_sha256"] != rec["click_final_frame_sha256"]))

    # status vocabulary (§6)
    launched = obs["rc"] == 0
    rendered = bool(obs["frames"]) and rec["visual"]["LEVEL"] >= 1
    rec["launched"] = launched
    rec["rendered"] = rendered
    rec["interacted"] = probed > 0
    rec["state_changed"] = rec["state_change_evidence"]
    if not launched:
        rec["status"] = "BLOCKED"
    elif rendered and rec["state_changed"]:
        rec["status"] = "INTERACTED"
    elif rendered:
        rec["status"] = "RENDERED"
    elif obs["frames"]:
        rec["status"] = "LOADED"
    else:
        rec["status"] = "BLOCKED"
    v = rec.get("visual", {})
    print(f"[{rec['status']:<11}] rc={obs['rc']:<3} L{v.get('LEVEL','-')} "
          f"{v.get('LEVEL_NAME','NO-FRAME'):<24} probe={probed:<3} chg={changed:<3} "
          f"{pkg[:40]}")
    return rec


def main():
    man = json.load(open(MANIFEST))
    titles = man["titles"]
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        for rec in ex.map(run_title, titles):
            results.append(rec)
            with open(REPORT, "w") as f:
                json.dump({"campaign": "S84 NEW-50", "results": results}, f, indent=1)
    n = len(results)
    ok = sum(1 for r in results if r.get("launched"))
    inter = sum(1 for r in results if r.get("state_changed"))
    print(f"\nreport: {REPORT}  launched {ok}/{n}  state_changed {inter}/{n}")


if __name__ == "__main__":
    main()
