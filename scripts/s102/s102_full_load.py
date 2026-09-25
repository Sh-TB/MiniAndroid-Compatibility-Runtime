#!/usr/bin/env python3
"""s102_full_load.py — S102 COMPOSE FAMILY ROOT-CAUSE SWEEP census runner.

Re-executes the S99/S101 full-load protocol (obs + click + visual audit +
state-change pixel measurement) against the CURRENT engine for the S102
wave. Resume-safe per-title (run/s102/full_load/<pkg>/report.json), so
foreground chunks make incremental progress across invocations.

Differences vs s101_rerun_full_load.py:
  * compose-first priority: titles with genuine androidx/compose or
    kotlinx/coroutines evidence in the S101 ledger run FIRST, so root-cause
    work starts while the rest of the census is still pending.
  * `--only pkg,pkg` subset mode for targeted re-runs after each fix.
  * census is written incrementally (run/s102/full_load_report.json) after
    every completed title.

Output: run/s102/full_load_report.json + run/s102/full_load/<pkg>/
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
OUT = f"{ROOT}/run/s102/full_load"
REPORT = f"{ROOT}/run/s102/full_load_report.json"
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
# S101-ledger genuine androidx/compose + kotlinx/coroutines evidence — run first
PRIORITY = [
    "com.vayunmathur.games.solitaire",   # real androidx/compose stack
    "com.helddertierwelt.mentalmath",    # kotlinx.coroutines FastServiceLoader + Hilt
]


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
            if not crash_family:
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
    rep_path = f"{base}/report.json"
    if os.path.exists(rep_path):
        return json.load(open(rep_path)), True
    if not os.path.exists(apk):
        rec = {"package": pkg, "apk": apk, "status": "APK-MISSING"}
    else:
        os.makedirs(base, exist_ok=True)
        obs = engine_run(apk, f"{base}/obs", click=False)
        clk = engine_run(apk, f"{base}/click", click=True)
        rec = {"package": pkg, "apk": apk, "apk_sha256": sha256(apk),
               "rc_obs": obs["rc"], "errors_obs": obs["errors"],
               "rc_click": clk["rc"], "errors_click": clk["errors"],
               "crash_family": obs["crash_family"] or clk["crash_family"],
               "frames_obs": len(obs["frames"])}
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
            if rec.get("final_frame_sha256") and \
               rec["click_final_frame_sha256"] != rec["final_frame_sha256"]:
                rec["state_change_px"] = pixel_change(obs["frames"][-1],
                                                      clk["frames"][-1])
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
    return rec, False


def load_all():
    recs = []
    if os.path.exists(REPORT):
        recs = json.load(open(REPORT))
    else:
        for p in glob.glob(f"{OUT}/*/report.json"):
            recs.append(json.load(open(p)))
    return recs


def write_report(recs):
    json.dump(recs, open(REPORT, "w"), indent=1)


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
    entries = [(p, a) for p, a in entries if p in PRIORITY or True]
    # priority ordering: PRIORITY first
    order = {p: i for i, p in enumerate(PRIORITY)}
    entries.sort(key=lambda e: order.get(e[0], 99))
    only = None
    workers = 4
    args = sys.argv[1:]
    if "--only" in args:
        only = set(args[args.index("--only") + 1].split(","))
        entries = [e for e in entries if e[0] in only]
    if "--workers" in args:
        workers = int(args[args.index("--workers") + 1])
    done = {r["package"] for r in load_all()}
    if only:
        done = done & only
    queue = [(p, a) for p, a in entries if p not in done]
    print(f"queue: {len(queue)} titles (done: {len(done)})", flush=True)
    recs = load_all()
    from collections import Counter
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for rec, cached in ex.map(run_title, queue):
            recs = [r for r in recs if r["package"] != rec["package"]] + [rec]
            write_report(recs)
            print(f"[{rec['status']:>19}] {rec['package']}"
                  + (" (cached)" if cached else ""), flush=True)
    census = Counter(r["status"] for r in recs)
    print("\nSTATUS CENSUS:", dict(census))


if __name__ == "__main__":
    main()
