#!/usr/bin/env python3
"""s163_dooz_longshot.py — S163: dooz convergence attempt on merged main.

User directive: run dooz. State: 380s probe (S159) did not converge; RSS
growth decelerating (+1.87 -> +1.00 MB/s); all ready-made levers measured
and rejected (S158), overlay surgery rejected (S159). Two zero-build
questions remain before any structural work:

  PROBE  lean-mode A/B (2x60s, PERF-OPS): does dropping --trace change the
         work-done rate (sum of PERF-OPS calls) and RSS slope? If trace
         costs >10% throughput, the long shot runs lean.
  LONG   single 900s shot in the leanest measured-faster config (default
         protocol config if lean is inert). Convergence signal = verdict
         timeline leaving the spin state (any FRAME_ANALYSIS state change
         late in the run) + screenshot content; RSS end-slope recorded.

No build, no surgery — measurement + budget, per the reuse law.
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
import s154_awaitup_gate as g

g.OUT = BASE / "run_s163_dooz"
g.OUT.mkdir(parents=True, exist_ok=True)
EVID = BASE / "evidence/s163_runs"
EVID.mkdir(parents=True, exist_ok=True)

APK = BASE / "upload/canonical_apks/dooz_23_toplevel.apk"
PKG = "io.github.yamin8000.dooz"
STORE = g.OUT / "store_dooz/data"

OPS_RE = re.compile(r"op=(0x[0-9a-f]+)\s+calls=(\d+)\s+ticks=(\d+)")
RSS_RE = re.compile(r"RSS=(\d+(?:\.\d+)?)\s*MB")


def lean_run(tag, trace, seconds, perf_ops):
    rundir = g.OUT / tag
    console = g.OUT / f"{tag}_console.log"
    env = dict(os.environ)
    if perf_ops:
        env["MINIANDROID_PERF_PHASES"] = "1"
    cmd = [str(g.BIN), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(STORE), "-o", str(rundir),
           "--max-seconds", str(seconds), "--frames", "4",
           "--package", PKG]
    if trace:
        cmd.append("--trace")
    t0 = time.time()
    killed = False
    try:
        with open(console, "w") as cf:
            subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                           timeout=seconds + 90, env=env)
    except subprocess.TimeoutExpired:
        killed = True
    wall = round(time.time() - t0, 1)
    text = console.read_text(errors="replace")
    ops = OPS_RE.findall(text)
    total_calls = sum(int(c) for _, c, _ in ops)
    total_ticks = sum(int(t) for _, _, t in ops)
    rss = [float(x) for x in RSS_RE.findall(text)]
    return {
        "tag": tag, "trace": trace, "perf_ops": perf_ops,
        "wall_s": wall, "killed": killed,
        "ops_total_calls": total_calls, "ops_total_ticks": total_ticks,
        "tpc_avg": round(total_ticks / total_calls, 2) if total_calls else None,
        "rss_first": rss[0] if rss else None,
        "rss_last": rss[-1] if rss else None,
        "rss_grow_mb_s": (round((rss[-1] - rss[0]) / wall, 3)
                          if len(rss) >= 2 and wall > 0 else None),
        "verdict_timeline": re.findall(r"FRAME_ANALYSIS state=(\S+)", text),
        "uncaught": len(re.findall(r"UNCAUGHT", text)),
        "face": g.sha16(rundir / "screenshot.png")
        if (rundir / "screenshot.png").exists() else None,
    }


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    out = EVID / "S163_DOOZ_LONGSHOT.json"
    out_rows = {}
    if out.exists():          # merge across invocations (probe -> long)
        try:
            out_rows = json.load(open(out))
        except Exception:
            out_rows = {}

    g.install(APK, STORE)

    if mode in ("all", "probe"):
        print("== PROBE A: 60s trace-ON (protocol config) ==")
        a = lean_run("probe_trace_on", True, 60, True)
        print(json.dumps({k: v for k, v in a.items()}, indent=1))
        print("== PROBE B: 60s trace-OFF (lean) ==")
        b = lean_run("probe_trace_off", False, 60, True)
        print(json.dumps({k: v for k, v in b.items()}, indent=1))
        out_rows["probe_trace_on"] = a
        out_rows["probe_trace_off"] = b
        wc, nc = a["ops_total_calls"], b["ops_total_calls"]
        out_rows["_lean_gain"] = (round((nc - wc) / wc * 100, 1)
                                  if wc and nc else None)

    if mode in ("all", "long"):
        lean_gain = out_rows.get("_lean_gain")
        use_trace = not (lean_gain is not None and lean_gain > 10.0)
        # S163 chunk law: background processes do NOT survive between tool
        # calls in this sandbox (fresh shell per call — nohup'd pid died
        # silently within 2 min), and the Bash tool cap is 600s. The long
        # shot therefore runs FOREGROUND at 540s (engine self-exits at the
        # soft budget, 60s tool margin). 1.42x the S159 380s probe.
        sec = int(os.environ.get("S163_LONG_S", "540"))
        print(f"== LONG SHOT: {sec}s trace={use_trace} "
              f"(lean_gain={lean_gain}) ==")
        row = lean_run(f"longshot_{sec}s", use_trace, sec, False)
        print(json.dumps({k: v for k, v in row.items()
                          if k != "face"}, indent=1))
        out_rows[f"longshot_{sec}s"] = row
        out_rows["longshot_config"] = {"trace": use_trace,
                                       "max_seconds": sec}
        shot = g.OUT / f"longshot_{sec}s/screenshot.png"
        if shot.exists():
            import shutil
            shutil.copy(shot, EVID / "S163_dooz_longshot_screenshot.png")

    json.dump(out_rows, open(out, "w"), indent=1)
    print("evidence ->", out)


if __name__ == "__main__":
    main()
