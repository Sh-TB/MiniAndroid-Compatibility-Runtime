#!/usr/bin/env python3
"""s85_rescue.py — S85: complete the incomplete titles (user mandate:
"complete the ones that remained incomplete").

Re-runs at CURRENT engine (S83 engine laws + F-NEW-160 fixed):
  * org.lufebe16.pysolfc   — BLOCKED pre-F-NEW-160 (CNFE Build bridge);
                             F-NEW-160 fixed -> expect unblock, fresh level.
  * one.scarecrow.games.OPMT      — PARTIAL (S62-S65 spotlight).
  * eu.veldsoft.tri.peaks         — PARTIAL.
  * org.billthefarmer.siggen      — PARTIAL; APK re-fetched from F-Droid.

Same evidence protocol as S84 NEW-50: obs + click passes, visual audit,
levels, frame SHAs. rc=0 alone is never success.
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
OUT = f"{ROOT}/run/s85_rescue"
os.makedirs(OUT, exist_ok=True)
UA = "Mozilla/5.0 (X11; Linux x86_64) MiniAndroid-S85-rescue/1.0"

TITLES = [
    ("org.lufebe16.pysolfc", f"{ROOT}/run/s84/apks/org.lufebe16.pysolfc.apk",
     "PySol FC", "game"),
    ("one.scarecrow.games.OPMT",
     f"{ROOT}/upload/canonical_apks/opmt_v0.1.2_vc1.apk",
     "OPMT (One More Time…)", "game"),
    ("eu.veldsoft.tri.peaks",
     f"{ROOT}/upload/canonical_apks/tripeaks_v1.2.1_vc4.apk",
     "TriPeaks", "game"),
    ("org.billthefarmer.siggen", f"{OUT}/org.billthefarmer.siggen.apk",
     "SigGen", "app"),
]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def fetch_siggen():
    dst = f"{OUT}/org.billthefarmer.siggen.apk"
    if os.path.exists(dst) and os.path.getsize(dst) > 100000:
        return dst
    r = subprocess.run(["curl", "-s", "-m", "15", "-A", UA,
                        "https://f-droid.org/api/v1/packages/org.billthefarmer.siggen"],
                       capture_output=True)
    try:
        vc = json.loads(r.stdout)["packages"][0]["versionCode"]
    except Exception:
        print("siggen: no API version; abort fetch")
        return None
    url = f"https://f-droid.org/repo/org.billthefarmer.siggen_{vc}.apk"
    if subprocess.call(["curl", "-sL", "-m", "120", "-A", UA, "-o", dst, url]) != 0 \
            or not os.path.exists(dst) or os.path.getsize(dst) < 100000:
        print("siggen: download failed")
        return None
    return dst


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


def run_title(entry):
    pkg, apk, title, kind = entry
    if not os.path.exists(apk):
        if pkg.endswith("siggen"):
            apk = fetch_siggen()
        if not apk or not os.path.exists(apk):
            return {"package": pkg, "title": title, "status": "APK-MISSING"}
    base = f"{OUT}/{pkg}"
    rec = {"package": pkg, "title": title, "kind": kind,
           "apk_sha256": sha256(apk), "prior_status": "BLOCKED" if "pysol" in pkg else "PARTIAL"}

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
    print(f"DONE {pkg} rc_obs={rec['rc_obs']} frames={rec['frames_obs']} "
          f"state_change={rec['state_change_evidence']}", flush=True)
    return rec


def main():
    with ThreadPoolExecutor(max_workers=4) as ex:
        recs = list(ex.map(run_title, TITLES))
    with open(f"{OUT}/report.json", "w") as f:
        json.dump({"wave": "S85-rescue", "count": len(recs), "titles": recs},
                  f, indent=1)
    print(f"report: {OUT}/report.json")


if __name__ == "__main__":
    main()
