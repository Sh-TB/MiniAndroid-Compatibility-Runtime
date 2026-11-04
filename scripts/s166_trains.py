#!/usr/bin/env python3
"""s166_trains.py — S166: the 20-train campaign round 2 (10 dooz + 10 Telegram).

User directive: «ادامه ۲۰ قطار» — continue, 20 trains; the standing theme
applies: apps must LOAD FASTER and run LIGHTER (faster load, lighter weight).

Method law (S165 precedent): every train = ONE change -> A/B measure ->
APPROVED/REJECTED -> ledger row. Metrics: dooz = settle wall (fresh store
per run, S156 VM-state law) + RSS growth + face byte-exact + PERF-OPS tpc;
Telegram = boot wall + RSS peak + app_owned_pixels identical (2161) +
uncaught==0 (seed+skip envs on both arms).

Phases (argv[1]):
  z1_ab        dooz Z1 alloc-log gate A/B (control insurance D3 vs build)
  z1_perf      dooz Z1 PERF-OPS pair (mechanism evidence)
  z2_env       dooz Z2 MALLOC_MMAP_THRESHOLD_ env A/B
  tg_boot      generic Telegram boot A/B runner (tag,bin,envs json argv)
  anchors      anchor family gate (microtimer pin + g2048 + opencalc)
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s165_trains as t  # ensure_store, RSSMonitor, sha16

EVID = BASE / "evidence/s166_trains"
EVID.mkdir(parents=True, exist_ok=True)
OUT = BASE / "run_s166_trains"
OUT.mkdir(parents=True, exist_ok=True)

BIN_D3 = BASE / ("upload/_ma_local_backup/"
                 "miniandroid_s165_d3ckpt2_770206f2d976d997.bin")
BIN_NEW = BASE / "miniandroid/build/miniandroid"

DOOZ_APK = t.DOOZ_APK
DOOZ_PKG = t.DOOZ_PKG
TG_APK = t.TG_APK
TG_PKG = t.TG_PKG

SEED_SKIP = {"MINIANDROID_APP_DATA_SEED": "1",
             "MINIANDROID_PROVIDER_SKIP":
                 "FirebaseInitProvider,MlKitInitProvider"}
CLEAN_ENVS = ("MINIANDROID_APP_DATA_SEED", "MINIANDROID_PROVIDER_SKIP",
              "MINIANDROID_DRAW_CHECKPOINT", "MINIANDROID_FB_HISTO",
              "MINIANDROID_ALLOC_LOG", "MINIANDROID_PERF_PHASES",
              "MINIANDROID_HALT_HISTO")
DOOZ_STANDING_FACE = "11a38a5aeeff45a6"


def save(name, row):
    out = EVID / name
    rows = {}
    if out.exists():
        try:
            rows = json.load(open(out))
        except Exception:
            rows = {}
    rows.update(row)
    json.dump(rows, open(out, "w"), indent=1, default=str)
    print("evidence ->", out)


def perfops_parse(text):
    ops = {}
    for m in re.finditer(
            r"op=(0x[0-9a-f]+)\s+calls=(\d+)\s+ticks=(\d+)", text):
        ops[m.group(1)] = {"calls": int(m.group(2)),
                           "tpc": round(int(m.group(3)) / int(m.group(2)), 1)}
    return ops


def dooz_run(tag, bin_path, envs=None, budget=240, perf=False,
             store_root=None):
    """One dooz settle-protocol run. FRESH store per run (S156 VM-state
    spin law). Returns settle wall / face / RSS band / uncaught."""
    for k in CLEAN_ENVS:
        os.environ.pop(k, None)
    env = dict(os.environ)
    if envs:
        env.update(envs)
    if perf:
        env["MINIANDROID_PERF_PHASES"] = "1"
    store = (store_root or OUT) / f"store_dz_{tag}"
    assert t.ensure_store(DOOZ_APK, store, bin_path, DOOZ_PKG), \
        f"dooz install failed for {tag}"
    rundir = OUT / tag
    console = OUT / f"{tag}_console.log"
    cmd = [str(bin_path), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(store), "-o", str(rundir),
           "--max-seconds", str(budget), "--frames", "4",
           "--trace", "--package", DOOZ_PKG]
    proc = subprocess.Popen(cmd, stdout=open(console, "w"),
                            stderr=subprocess.STDOUT, env=env)
    mon = t.RSSMonitor(proc.pid)
    mon.start()
    t0 = time.time()
    rc = proc.wait(timeout=budget + 120)
    wall = round(time.time() - t0, 1)
    mon.stop()
    text = console.read_text(errors="replace")
    shot = rundir / "screenshot.png"
    # RSS growth from the monitor samples (first->last positive sample,
    # skipping the teardown rss==0 rows per the S159 monitor law)
    ss = mon.samples
    grow = None
    if len(ss) >= 2:
        dt = ss[-1][0] - ss[0][0]
        grow = round((ss[-1][1] - ss[0][1]) / dt, 3) if dt > 0 else None
    row = {
        "tag": tag, "bin": t.sha16(bin_path), "env": envs or {},
        "wall_s": wall, "rc": rc, "settle": wall < budget - 5,
        "face": t.sha16(shot) if shot.exists() else None,
        "rss_peak_mb": round(mon.peak, 1), "rss_final_mb": round(mon.last, 1),
        "rss_grow_mb_s": grow,
        "uncaught": len(re.findall(r"UNCAUGHT", text)),
        "f298_rows": len(re.findall(r"\[F298", text)),
        "frames_rendered": re.findall(r"Frames Rendered: (\d+)", text)[-1:],
        "verdict": re.findall(r"FRAME_ANALYSIS state=(\S+)", text)[-1:] or None,
    }
    if perf:
        row["perfops"] = perfops_parse(text)
    return row


def tg_run(tag, bin_path, envs=None, max_seconds=90, store_name=None):
    """One Telegram boot run (seed+skip baseline envs by default).
    Returns wall / RSS peak / pixels / uncaught."""
    for k in CLEAN_ENVS:
        os.environ.pop(k, None)
    env = dict(os.environ)
    merged = dict(SEED_SKIP)
    if envs:
        merged.update(envs)
    env.update(merged)
    store = OUT / (store_name or "store_tg")
    assert t.ensure_store(TG_APK, store, bin_path, TG_PKG), \
        f"tg install failed for {tag}"
    rundir = OUT / tag
    console = OUT / f"{tag}_console.log"
    cmd = [str(bin_path), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(store), "-o", str(rundir),
           "--max-seconds", str(max_seconds), "--frames", "8",
           "--trace", "--package", TG_PKG]
    proc = subprocess.Popen(cmd, stdout=open(console, "w"),
                            stderr=subprocess.STDOUT, env=env)
    mon = t.RSSMonitor(proc.pid)
    mon.start()
    t0 = time.time()
    rc = proc.wait(timeout=max_seconds + 120)
    wall = round(time.time() - t0, 1)
    mon.stop()
    text = console.read_text(errors="replace")
    row = {
        "tag": tag, "bin": t.sha16(bin_path), "env": merged, "wall_s": wall,
        "rc": rc, "rss_peak_mb": round(mon.peak, 1),
        "rss_final_mb": round(mon.last, 1),
        "uncaught": len(re.findall(r"UNCAUGHT", text)),
        "uncaught_l9j": len(re.findall(r"UNCAUGHT[^\n]*l9/j", text)),
        "frames_rendered": re.findall(r"Frames Rendered: (\d+)", text)[-1:],
        "verdict": re.findall(r"FRAME_ANALYSIS state=(\S+)", text)[-1:] or None,
    }
    ts = rundir / "trace_summary.json"
    if ts.exists():
        try:
            s = json.load(open(ts))
            fa = s.get("frame_analysis") or {}
            row["app_draw_ops"] = fa.get("app_draw_ops")
            row["app_owned_pixels"] = fa.get("app_owned_pixels")
            row["final_state"] = (s.get("lifecycle") or {}).get("final_state")
        except Exception:
            pass
    at = rundir / "api_trace.json"
    if at.exists():
        try:
            row["api_calls"] = json.load(open(at)).get("total_calls")
        except Exception:
            pass
    return row


def pair_summary(ctl, fix):
    return {
        "wall": f"{ctl['wall_s']} -> {fix['wall_s']}",
        "wall_delta_pct": round(
            (fix["wall_s"] - ctl["wall_s"]) / ctl["wall_s"] * 100.0, 1),
        "rss_peak": f"{ctl['rss_peak_mb']} -> {fix['rss_peak_mb']}",
        "face_equal": ctl.get("face") == fix.get("face"),
        "pixels_equal": (ctl.get("app_owned_pixels")
                         == fix.get("app_owned_pixels")),
    }


if __name__ == "__main__":
    phase = sys.argv[1]
    if phase == "z1_ab":
        suf = sys.argv[2] if len(sys.argv) > 2 else ""
        ctl = dooz_run("z1_ctl" + suf, BIN_D3)
        print(json.dumps(ctl))
        save("S166_TRAINS_LEDGER.json", {"z1_ctl" + suf: ctl})
        fix = dooz_run("z1_fix" + suf, BIN_NEW)
        print(json.dumps(fix))
        save("S166_TRAINS_LEDGER.json",
             {"z1_fix" + suf: fix, "z1_summary" + suf: pair_summary(ctl, fix)})
    elif phase == "z1_perf":
        ctl = dooz_run("z1p_ctl", BIN_D3, perf=True)
        fix = dooz_run("z1p_fix", BIN_NEW, perf=True)
        save("S166_Z1_PERFOPS.json", {"ctl": ctl, "fix": fix})
        top = sorted(set(ctl["perfops"]) & set(fix["perfops"]),
                     key=lambda k: -ctl["perfops"][k]["calls"])[:8]
        for k in top:
            a, b = ctl["perfops"][k]["tpc"], fix["perfops"][k]["tpc"]
            print(f"  op {k}: calls {ctl['perfops'][k]['calls']:,} -> "
                  f"{fix['perfops'][k]['calls']:,}  tpc {a} -> {b} "
                  f"({(b - a) / a * 100:+.1f}%)")
    elif phase == "tg_boot":
        # argv[2]=tag argv[3]=bin(d3|new) argv[4]=json envs argv[5]=store
        tag, bname = sys.argv[2], sys.argv[3]
        envs = json.loads(sys.argv[4]) if len(sys.argv) > 4 and \
            sys.argv[4] != "-" else None
        store = sys.argv[5] if len(sys.argv) > 5 else None
        b = BIN_D3 if bname == "d3" else BIN_NEW
        row = tg_run(tag, b, envs, store_name=store)
        print(json.dumps(row))
        save("S166_TRAINS_LEDGER.json", {tag: row})

    elif phase == "dz_pair":
        # argv: tag ctl_bin fix_bin ctl_envs(-) fix_envs(-)  -> dooz A/B pair
        tag = sys.argv[2]
        cb, fb = Path(sys.argv[3]), Path(sys.argv[4])
        ce = json.loads(sys.argv[5]) if sys.argv[5] != "-" else None
        fe = json.loads(sys.argv[6]) if sys.argv[6] != "-" else None
        ctl = dooz_run(tag + "_ctl", cb, ce)
        print(json.dumps(ctl)); save("S166_TRAINS_LEDGER.json", {tag + "_ctl": ctl})
        fix = dooz_run(tag + "_fix", fb, fe)
        print(json.dumps(fix))
        save("S166_TRAINS_LEDGER.json",
             {tag + "_fix": fix, tag + "_summary": pair_summary(ctl, fix)})

    elif phase == "tg_pair":
        # argv: tag ctl_bin fix_bin ctl_envs(-) fix_envs(-)  -> Telegram A/B pair
        tag = sys.argv[2]
        cb, fb = Path(sys.argv[3]), Path(sys.argv[4])
        ce = json.loads(sys.argv[5]) if sys.argv[5] != "-" else None
        fe = json.loads(sys.argv[6]) if sys.argv[6] != "-" else None
        ctl = tg_run(tag + "_ctl", cb, ce)
        print(json.dumps(ctl)); save("S166_TRAINS_LEDGER.json", {tag + "_ctl": ctl})
        fix = tg_run(tag + "_fix", fb, fe)
        print(json.dumps(fix))
        save("S166_TRAINS_LEDGER.json",
             {tag + "_fix": fix, tag + "_summary": pair_summary(ctl, fix)})
