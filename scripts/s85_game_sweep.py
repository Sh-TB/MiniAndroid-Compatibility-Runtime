#!/usr/bin/env python3
"""s85_game_sweep.py — S85 general review of all registered games
(user mandate: "بررسی کلی سایر بازی ها").

Re-probes every registered game with a cached APK at the CURRENT engine
(S83 laws + F-NEW-160 + F-NEW-163/163b): obs pass + click pass.
Goal: honest promotion candidates (L2+ renders, state-change evidence)
and blocker-family census. Resume-safe, chunked-foreground friendly.
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
OUT = f"{ROOT}/run/s85_sweep"
REPORT = f"{OUT}/report.json"
BUDGET = 420
os.makedirs(OUT, exist_ok=True)


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


def run_title(entry):
    pkg, apk, prior = entry
    base = f"{OUT}/{pkg}"
    rec = {"package": pkg, "apk": apk, "prior_status": prior}
    if not os.path.exists(apk):
        rec["status"] = "APK-MISSING"
        return rec
    obs = engine_run(apk, f"{base}/obs", click=False)
    clk = engine_run(apk, f"{base}/click", click=True)
    rec["rc_obs"], rec["errors_obs"] = obs["rc"], obs["errors"]
    rec["rc_click"], rec["errors_click"] = clk["rc"], clk["errors"]
    rec["frames_obs"] = len(obs["frames"])
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
    lvl = rec.get("visual", {}).get("LEVEL", 0)
    if rec["state_change_evidence"]:
        rec["status"] = "INTERACTIVE-EVIDENCE"
    elif lvl >= 2:
        rec["status"] = "RENDERED-L2+"
    elif rec["frames_obs"] > 0:
        rec["status"] = "OBSERVED"
    else:
        rec["status"] = "NO-FRAMES"
    print(f"SWEEP {pkg}: rc={rec['rc_obs']} L{lvl} state={rec['state_change_evidence']} -> {rec['status']}", flush=True)
    return rec


def main():
    reg = json.load(open(f"{ROOT}/docs/evidence/canonical/registry.json"))
    apkmap = json.load(open(f"{ROOT}/run/s85/game_apk_map.json"))
    # interactive in-house titles already proven: skip re-probe (GIF canonical exists)
    skip = {"com.miniandroid.snakedeluxe", "com.miniandroid.tetris",
            "com.miniandroid.tictactoedeluxe", "com.miniandroid.g2048",
            "com.smorgasbork.hotdeath", "org.bobstuff.bobball",
            "com.dozingcatsoftware.dodge", "ca.rmen.nounours",
            "com.emmanuelmess.tictactoe", "io.github.yamin8000.dooz"}
    todo = []
    for t in reg["titles"]:
        if t.get("type") != "game":
            continue
        pkg = t["package"]
        if pkg in skip or pkg not in apkmap:
            continue
        todo.append((pkg, apkmap[pkg], t["status"]))
    done = set()
    if os.path.exists(REPORT):
        try:
            done = {r["package"] for r in json.load(open(REPORT))["titles"]}
        except Exception:
            pass
    todo = [e for e in todo if e[0] not in done]
    print(f"S85 sweep: {len(todo)} games to go", flush=True)
    t0 = time.time()
    recs = []
    BATCH = 8
    for i in range(0, len(todo), BATCH):
        if time.time() - t0 > BUDGET and i > 0:
            print(f"TIME-BUDGET ({len(recs)} this invocation)", flush=True)
            break
        batch = todo[i:i + BATCH]
        with ThreadPoolExecutor(max_workers=4) as ex:
            for r in ex.map(run_title, batch):
                recs.append(r)
    merged = []
    if os.path.exists(REPORT):
        try:
            merged = json.load(open(REPORT))["titles"]
        except Exception:
            merged = []
    merged += recs
    json.dump({"wave": "S85-sweep", "count": len(merged), "titles": merged},
              open(REPORT, "w"), indent=1)
    print(f"report: {REPORT} ({len(merged)} recorded)", flush=True)


if __name__ == "__main__":
    main()
