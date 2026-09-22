#!/usr/bin/env python3
"""s85_ab.py — S85 A/B re-runs after F-NEW-163 (Context-family getResources
hierarchy law) + re-download of 3 truncated APKs (pysolfc, pfmemory, pf2048).

A/B titles (F-NEW-163 fan-out): solitaire_cg, aurora.store, hecate, notepad.
Re-downloaded: pysolfc, privacyfriendlymemory, privacyfriendly2048.
Same protocol as s85_run_new.py. Updates run/s85/report.json in place.
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
OUT = f"{ROOT}/run/s85"
REPORT = f"{OUT}/report.json"

AB = ["net.sourceforge.solitaire_cg", "com.aurora.store", "dev.lexip.hecate",
      "com.nononsenseapps.notepad", "org.lufebe16.pysolfc",
      "org.secuso.privacyfriendlymemory", "org.secuso.privacyfriendly2048"]


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
    rec = dict(t)  # keep manifest fields
    rec.update({"rc_obs": None, "note": "A/B re-run after F-NEW-163 "
                + ("+ APK re-download" if pkg.endswith(("pysolfc", "memory", "2048")) else "")})
    if not os.path.exists(apk):
        rec["status"] = "APK-MISSING"
        return rec

    obs = engine_run(apk, f"{base}/obs", click=False)
    clk = engine_run(apk, f"{base}/click", click=True)
    rec["rc_obs"], rec["errors_obs"] = obs["rc"], obs["errors"]
    rec["rc_click"], rec["errors_click"] = clk["rc"], clk["errors"]
    rec["frames_obs"], rec["frames_click"] = len(obs["frames"]), len(clk["frames"])

    probed = changed = -1
    if clk["clickline"]:
        for tok in clk["clickline"].split():
            if tok.startswith("probed="):
                probed = int(tok.split("=")[1])
            if tok.startswith("state_changed="):
                changed = int(tok.split("=")[1])
    rec["click_probed"], rec["click_state_changed"] = probed, changed

    if obs["frames"]:
        m = audit_frame(obs["frames"][-1])
        lvl, name = level_of(m)
        m["LEVEL"], m["LEVEL_NAME"] = lvl, name
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
    vis = rec.get("visual", {})
    lvl = vis.get("LEVEL", 0)
    if rec["state_change_evidence"] and rec["frames_click"] > 0:
        rec["status"] = "VERIFIED-INTERACTIVE-CANDIDATE"
    elif lvl >= 2 and rec["frames_obs"] > 0:
        rec["status"] = "VERIFIED"
    elif rec["frames_obs"] > 0:
        rec["status"] = "OBSERVED"
    else:
        rec["status"] = "LOADED"
    # refresh apk sha for re-downloads
    rec["apk_sha256"] = sha256(apk)
    print(f"AB {pkg}: rc={rec['rc_obs']} lvl={lvl} frames={rec['frames_obs']} "
          f"-> {rec['status']}", flush=True)
    return rec


def main():
    manifest = json.load(open(f"{OUT}/manifest_new.json"))["titles"]
    todo = [t for t in manifest if t["package"] in AB]
    with ThreadPoolExecutor(max_workers=4) as ex:
        recs = list(ex.map(run_title, todo))
    report = json.load(open(REPORT))
    titles = [r for r in report["titles"] if r["package"] not in AB]
    titles += recs
    report["titles"] = titles
    report["count"] = len(titles)
    json.dump(report, open(REPORT, "w"), indent=1)
    print(f"report updated: {REPORT}")


if __name__ == "__main__":
    main()
