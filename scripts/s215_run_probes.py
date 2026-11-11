#!/usr/bin/env python3
"""S215 A-R probe battery runner — build artifacts from s215_build_probes.sh,
run through the W12-integrated binary, parse |PASS|/|FAIL| rows."""
import hashlib, json, re, shutil, subprocess, sys
from pathlib import Path

BASE = Path("/home/z/my-project")
BIN = BASE / "miniandroid/build/miniandroid"
RUNS = BASE / "evidence/s215/runs"
RUNS.mkdir(parents=True, exist_ok=True)


def run_probe(apk, tag, frames=8, delay=250):
    store = RUNS / f"store_{tag}"
    shutil.rmtree(store, ignore_errors=True)
    store.mkdir(parents=True)
    subprocess.run([str(BIN), "install", str(apk), "--data-root", str(store)],
                   capture_output=True, timeout=300)
    apps = store / "data" / "app"
    dpkg = None
    if apps.exists():
        ds = [d.name for d in sorted(apps.iterdir())
              if d.is_dir() and not d.name.startswith(".")
              and not d.name.endswith(".staging")
              and (d / "base.apk").exists()]
        dpkg = ds[0] if ds else None
    rundir = RUNS / tag
    shutil.rmtree(rundir, ignore_errors=True)
    console = RUNS / f"{tag}.console.log"
    cmd = [str(BIN), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(store), "-o", str(rundir),
           "--package", dpkg, "--frames", str(frames),
           "--frame-delay", str(delay)]
    with open(console, "wb") as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT, cwd=str(BASE),
                       timeout=600)
    log = console.read_text(errors="ignore")
    rows = re.findall(r"(R\d+-\d+\|(?:PASS|FAIL)\|[^\n\"]*)", log)
    p = sum(1 for r in rows if "|PASS|" in r)
    f = sum(1 for r in rows if "|FAIL|" in r)
    shot = rundir / "screenshot.png"
    face = hashlib.sha256(shot.read_bytes()).hexdigest()[:16] if shot.exists() else None
    uncaught = len(re.findall(r"uncaught exception|FATAL", log))
    return {"rows": rows, "pass": p, "fail": f, "face": face, "uncaught": uncaught}


out = {}
for tag, apk, expect in [("ar_probe", "run/s215/ar_probe.apk", 15),
                         ("r1_probe", "run/s215/r1_probe.apk", 2)]:
    r = run_probe(str(BASE / apk), tag)
    out[tag] = r
    print(f"== {tag}: PASS {r['pass']}/{r['pass']+r['fail']} (expected {expect}) "
          f"uncaught={r['uncaught']} face={r['face']}")
    for row in r["rows"]:
        print("   ", row)

# second run for determinism (face x2)
r2 = run_probe(str(BASE / "run/s215/ar_probe.apk"), "ar_probe_x2")
out["ar_probe_rerun"] = {"pass": r2["pass"], "fail": r2["fail"], "face": r2["face"]}
print(f"ar rerun: face={r2['face']} identical={r2['face'] == out['ar_probe']['face']}")

(BASE / "evidence/s215/A_R_BATTERY_S215.json").write_text(json.dumps(out, indent=1))
print("saved evidence/s215/A_R_BATTERY_S215.json")
