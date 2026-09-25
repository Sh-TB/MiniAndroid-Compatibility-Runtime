#!/usr/bin/env python3
"""s101_rerun_full_load.py — S101 RECALL SWEEP.

The S99 full-load report (run/s99/full_load_report.json) predates the S100
runtime fixes (dooz child-snapshot crash law, theme-gate hop bound 8->32,
Handler/Pattern/String null-laws, NET-001). Its PARTIAL/FAIL census is
therefore STALE. This runner re-executes the identical S99 protocol
(obs + click + visual audit + state-change measurement) against the
CURRENT engine, writing to run/s101/full_load_report.json, and emits a
before/after flip table (per-title S99 status -> S101 status).

Resume-safe per-title via run/s101/full_load/<pkg>/report.json.
Parallel across 4 workers (same as S99).
"""
import glob
import hashlib
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = "/home/z/my-project"
sys.path.insert(0, f"{ROOT}/scripts")
from s81_visual_audit import audit_frame, level_of  # noqa: E402

ENG = f"{ROOT}/miniandroid/build/miniandroid"
OUT = f"{ROOT}/run/s101/full_load"
REPORT = f"{ROOT}/run/s101/full_load_report.json"
S99_REPORT = f"{ROOT}/run/s99/full_load_report.json"
MANIFEST = f"{ROOT}/run/s99/apk_manifest.json"
INHOUSE = {
    "com.miniandroid.snakedeluxe": f"{ROOT}/upload/s83_games/build_sd/snake_deluxe_v1.0_vc1.apk",
    "com.miniandroid.g2048": f"{ROOT}/upload/s83_games/g2048_v1.0_vc1.apk",
    "com.miniandroid.tetris": f"{ROOT}/upload/s83_games/build_tetris/tetris_v1.0_vc1.apk",
    "com.miniandroid.tictactoedeluxe": f"{ROOT}/upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk",
    "com.miniandroid.minicraft": f"{ROOT}/upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk",
    "com.miniandroid.snakeneon": f"{ROOT}/upload/s98_games/build_snakeneon/snakeneon_v1.0_vc1.apk",
    "com.miniandroid.snake": f"{ROOT}/upload/s72_w4_apks/snake_v1.0_vc1.apk",
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def engine_run(apk, out_dir, click=False, frames="8", timeout=300):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", frames, "--frame-delay", "300", "--max-seconds", "240",
           "-o", out_dir, apk]
    if click:
        cmd.append("--click-test")
    log = out_dir + ("_click.log" if click else "_obs.log")
    with open(log, "w") as lf:
        try:
            rc = subprocess.call(cmd, stdout=lf, stderr=lf, timeout=timeout)
        except subprocess.TimeoutExpired:
            rc = -1
    errors, clickline, crash_family = "?", "", ""
    for line in open(log, encoding="utf-8", errors="replace"):
        if line.startswith("Errors:"):
            errors = line.split(":", 1)[1].strip()
        if "[CLICK-TEST] done:" in line:
            clickline = line.strip()
        if "Uncaught exception" in line or "CNFE" in line or "RuntimeException" in line \
           or "NullPointerException" in line or "fail-oncreate" in line:
            crash_family = line.strip()[:160]
    frames_p = sorted(glob.glob(f"{out_dir}/frames/frame_*.png"))
    return {"rc": rc, "errors": errors, "log": log, "frames": frames_p,
            "clickline": clickline, "crash_family": crash_family}


def pixel_change(a, b):
    """Exact full-res changed-pixel count between two PNGs (S91 law)."""
    from PIL import Image
    try:
        ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
        if ia.size != ib.size:
            return -1
        pa, pb = ia.tobytes(), ib.tobytes()
        return sum(1 for i in range(0, len(pa), 3)
                   if pa[i:i + 3] != pb[i:i + 3])
    except Exception:
        return -1


def run_title(entry):
    pkg, apk = entry
    base = f"{OUT}/{pkg}"
    rec = {"package": pkg, "apk": apk,
           "apk_sha256": sha256(apk) if os.path.exists(apk) else None}
    rep_path = f"{base}/report.json"
    if os.path.exists(rep_path):
        return json.load(open(rep_path))
    if not os.path.exists(apk):
        rec["status"] = "APK-MISSING"
        return rec
    os.makedirs(base, exist_ok=True)
    obs = engine_run(apk, f"{base}/obs", click=False)
    clk = engine_run(apk, f"{base}/click", click=True)
    rec["rc_obs"], rec["errors_obs"] = obs["rc"], obs["errors"]
    rec["rc_click"], rec["errors_click"] = clk["rc"], clk["errors"]
    rec["crash_family"] = obs["crash_family"] or clk["crash_family"]
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
        if rec.get("final_frame_sha256") and rec["click_final_frame_sha256"] != rec["final_frame_sha256"]:
            rec["state_change_px"] = pixel_change(obs["frames"][-1], clk["frames"][-1])
    rec["state_change_evidence"] = bool(
        changed > 0 or rec.get("state_change_px", 0) not in (None, -1, 0))
    lvl = rec.get("visual", {}).get("LEVEL", 0)
    if rec["state_change_evidence"]:
        rec["status"] = "INTERACTIVE-EVIDENCE"
    elif lvl >= 2 and rec["rc_obs"] == 0:
        rec["status"] = "RENDERED-L2+"
    elif lvl >= 1:
        rec["status"] = "PARTIAL"
    else:
        rec["status"] = "FAIL"
    json.dump(rec, open(rep_path, "w"), indent=1)
    return rec


def main():
    os.makedirs(OUT, exist_ok=True)
    entries = []
    man = json.load(open(MANIFEST))
    for r in man:
        if r.get("status") in ("SOURCED", "CACHED"):
            entries.append((r["package"], f"{ROOT}/run/s99/apks/{r['package']}.apk"))
    for pkg, apk in INHOUSE.items():
        if os.path.exists(apk):
            entries.append((pkg, apk))
    print(f"queue: {len(entries)} titles")
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        for rec in ex.map(run_title, entries):
            results.append(rec)
            print(f"[{rec['status']:>19}] {rec['package']}", flush=True)
    json.dump(results, open(REPORT, "w"), indent=1)
    from collections import Counter
    census = Counter(r["status"] for r in results)
    print("\nSTATUS CENSUS:", dict(census))

    # ---- before/after flip table vs S99 ----
    try:
        s99 = {r["package"]: r["status"] for r in json.load(open(S99_REPORT))}
        flips = []
        for r in results:
            old = s99.get(r["package"])
            if old and old != r["status"]:
                flips.append((old, r["status"], r["package"]))
        print(f"\nFLIPS vs S99: {len(flips)}")
        rank = {"FAIL": 0, "PARTIAL": 1, "RENDERED-L2+": 2, "INTERACTIVE-EVIDENCE": 3}
        for old, new, pkg in sorted(flips, key=lambda f: rank[f[1]] - rank[f[0]]):
            arrow = "UP" if rank[new] > rank[old] else "DOWN"
            print(f"  [{arrow}] {old:>19} -> {new:<19} {pkg}")
    except FileNotFoundError:
        print("S99 report missing; no flip table")


if __name__ == "__main__":
    main()
