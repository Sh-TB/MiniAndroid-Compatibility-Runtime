#!/usr/bin/env python3
"""W6 Phase 3 driver: bridge arm extraction loop.
Each iteration: regenerate the cut from git HEAD + STATE (hoist list),
build, parse 'not declared' errors -> append to STATE['hoist_ids'],
retry. Aborts honestly on non-hoistable errors."""
import json, os, re, subprocess, sys, time

os.chdir("/home/z/my-project/miniandroid")
EV = "evidence/wave6"
STATEF = f"{EV}/w6_bridge_cut_state.json"

for it in range(6):
    STATE = json.load(open(STATEF))
    r = subprocess.run([sys.executable, "-I",
                        "/home/z/my-project/scripts/w6_bridge_cut.py", "all"],
                       capture_output=True, text=True, timeout=560)
    print(f"--- iter {it}: transform rc={r.returncode}")
    for l in (r.stdout + r.stderr).splitlines()[-6:]:
        print("   ", l.strip()[:130])
    if r.returncode != 0:
        print("TRANSFORM FAILED - tree left pristine; abort honestly")
        break
    t0 = time.monotonic()
    mk = subprocess.run(["make", "-j1", "all"], capture_output=True,
                        text=True, timeout=560)
    print(f"--- iter {it}: build rc={mk.returncode} "
          f"wall={time.monotonic()-t0:.1f}s")
    if mk.returncode == 0:
        print("BUILD CLEAN")
        break
    errs = [l for l in mk.stderr.splitlines() if ": error:" in l]
    missing = sorted(set(re.findall(r"error: [‘'](\w+)[’'] was not declared",
                                    mk.stderr)))
    if missing:
        STATE.setdefault("hoist_ids", [])
        new = [m for m in missing if m not in STATE["hoist_ids"]]
        if new:
            STATE["hoist_ids"].extend(new)
            json.dump(STATE, open(STATEF, "w"), indent=1)
            print("--- hoisting:", new)
            continue
    for e in errs[:5]:
        print("  ", e.strip()[:140])
    print("NON-HOISTABLE ERROR — abort")
    break
