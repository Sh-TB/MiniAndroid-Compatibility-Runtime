#!/usr/bin/env python3
"""ISSUE-612 WAVE-2 — dev.py: fast developer feedback driver (Phase 7).

Interface (proposed names from the issue, implemented on the existing
Makefile/tooling without CMake/Ninja prerequisites):

  python3 dev.py build module <name>      # -O0 objects of ONE src module
  python3 dev.py test module <name>       # component test for that module (if defined)
  python3 dev.py test component mutf8     # run the mutf8 L0 component test
  python3 dev.py test affected <file.cpp> # rebuild affected objects + run matching tests
  python3 dev.py run-apk <apk> [args...]  # build (prod profile if needed) + run real APK
  python3 dev.py test regression          # full core battery (production flags)
  python3 dev.py timings                  # acceptance-table helper (no-change + module)

Every command prints wall-clock duration; DEV=1 loops use -O0 -g0.
"""
import subprocess, sys, time, os, json

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

MAKE = ["make", "--no-print-directory"]

def run(cmd, quiet=False, timeout=900):
    t0 = time.monotonic()
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    dt = time.monotonic() - t0
    if not quiet:
        for line in (r.stdout or "").splitlines()[-6:]:
            print("  |", line)
        if r.returncode != 0:
            for line in (r.stderr or "").splitlines()[-8:]:
                print("  !", line)
    return r.returncode, dt

def module_objects(module):
    src = f"src/{module}"
    objs = []
    for f in sorted(os.listdir(src)):
        if f.endswith(".cpp"):
            objs.append(f"build/{module}/{f[:-4]}.o")
    return objs

# dev.py test component → Makefile target mapping (component-closure tests)
COMPONENT_TESTS = {"mutf8": "mutf8_component"}
# module → component test name
MODULE_TEST = {"dex": "mutf8_component"}

def cmd_build_module(module):
    print(f"[build module {module}] DEV=1 (-O0 -g0)")
    rc, dt = run(MAKE + [f"DEV=1", "module", f"MODULE={module}", "-j2"])
    print(f"  => rc={rc}  {dt:.2f}s")
    return rc

def cmd_test_component(name):
    tgt = COMPONENT_TESTS.get(name)
    if not tgt:
        print(f"no component test named {name!r}; known: {sorted(COMPONENT_TESTS)}")
        return 2
    print(f"[test component {name}] (minimal closure, DEV=1)")
    rc, dt = run(MAKE + ["DEV=1", tgt, "-j2"])
    print(f"  => rc={rc}  {dt:.2f}s")
    return rc

def cmd_test_module(module):
    name = MODULE_TEST.get(module)
    if not name:
        print(f"[test module {module}] no dedicated component test; building module instead")
        return cmd_build_module(module)
    return cmd_test_component(name)

def cmd_test_affected(changed):
    changed = changed.replace("src/", "", 1) if changed.startswith("src/") else changed
    module = changed.split("/")[0]
    print(f"[test affected {changed}] → module {module} (+ .d header reverse-deps)")
    rc, dt = run(MAKE + ["DEV=1", "module", f"MODULE={module}", "-j2"])
    print(f"  objects rebuilt in {dt:.2f}s (rc={rc})")
    name = MODULE_TEST.get(module)
    if name:
        rc2, dt2 = run(MAKE + ["DEV=1", COMPONENT_TESTS[name], "-j2"])
        print(f"  component test {name}: rc={rc2} {dt2:.2f}s")
        return rc2
    return rc

def cmd_run_apk(apk, *args):
    print("[run-apk] production profile build (required for L3 fidelity)")
    rc, dt = run(MAKE + ["all", "-j1"], quiet=True, timeout=2400)
    print(f"  build rc={rc} {dt:.1f}s")
    if rc:
        return rc
    t0 = time.monotonic()
    r = subprocess.run(["./build/miniandroid", "run", apk, "--max-seconds", "70",
                        "--frames", "3", "--frame-delay", "400", "--dump-view-tree",
                        *args], capture_output=True, text=True, timeout=600)
    dt = time.monotonic() - t0
    status = next((l for l in r.stdout.splitlines() if l.startswith("Status:")), "?")
    print(f"  {status}  {dt:.1f}s")
    return r.returncode

def cmd_test_regression():
    print("[test regression] production-profile core battery")
    rc, dt = run(MAKE + ["test-all", "-j1"], quiet=True, timeout=3600)
    print(f"  => rc={rc}  {dt:.1f}s")
    return rc

def cmd_timings():
    print("[timings] acceptance probes (median of 3 where cheap)")
    # F: no-change build
    ts = []
    for _ in range(3):
        rc, dt = run(MAKE + ["module", "MODULE=resources"], quiet=True)
        ts.append(dt)
    ts.sort()
    print(f"  no-change module build: median {ts[1]:.2f}s (target < 15s)")
    # mutf8 component test loop
    rc, dt = run(MAKE + ["DEV=1", "mutf8_component"], quiet=True)
    print(f"  mutf8 component test (warm): {dt:.2f}s (target < 5s)")

def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "build" and argv[2] == "module":
        return cmd_build_module(argv[3])
    if cmd == "test" and argv[2] == "component":
        return cmd_test_component(argv[3])
    if cmd == "test" and argv[2] == "module":
        return cmd_test_module(argv[3])
    if cmd == "test" and argv[2] == "affected":
        return cmd_test_affected(argv[3])
    if cmd == "test" and argv[2] == "regression":
        return cmd_test_regression()
    if cmd == "run-apk":
        return cmd_run_apk(argv[2], *argv[3:])
    if cmd == "timings":
        cmd_timings()
        return 0
    print(__doc__)
    return 2

if __name__ == "__main__":
    sys.exit(main(sys.argv))
