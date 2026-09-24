#!/usr/bin/env python3
"""s92_run_battery.py — S92 §25/§40 false-positive battery runner.

Builds the battery fixture APKs with the REAL aapt2 toolchain, runs each
through MiniAndroid with full evidence instrumentation (GfxProvenance +
ClickAudit + frames + view_tree), verifies each run with
tools/verify_graphics.py, and judges against fixtures/s92battery/ORACLE.json.

Exit code 0 only if the battery holds: ACCEPT cases accepted, REJECT cases
rejected. This is the gate that proves the verifier catches the exact
false-completion problem (S92 §25/§40) before it may be trusted on the
real corpus (§40: "If it cannot distinguish these, DO NOT deploy it").
"""
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tools", "verify"))

BASE = os.path.join(REPO, "fixtures", "s92battery")
OUT = os.path.join(REPO, "run", "s92battery")
VERDICTS = os.path.join(REPO, "run", "s92battery", "verdicts")
MA_BIN = os.path.join(REPO, "miniandroid", "build", "miniandroid")
BUILD_APK = os.path.join(REPO, "scripts", "build", "build_fixture_apk.sh")


def sh(cmd, **kw):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          **kw)


def build_apks(cases):
    apks = {}
    for case, meta in cases.items():
        src = os.path.join(BASE, case)
        out = os.path.join(BASE, f"{case}.apk")
        if os.path.isfile(out) and os.path.getmtime(out) > os.path.getmtime(src):
            apks[case] = out
            continue
        r = sh(f"bash {BUILD_APK} {src} {out}")
        if r.returncode != 0 or not os.path.isfile(out):
            print(f"BUILD FAIL {case}: {r.stdout[-400:]}\n{r.stderr[-400:]}")
            continue
        apks[case] = out
    return apks


def run_case(case, apk):
    rundir = os.path.join(OUT, case)
    os.makedirs(rundir, exist_ok=True)
    env = dict(os.environ)
    env["MINIANDROID_GFX_PROVENANCE"] = os.path.join(rundir,
                                                     "gfx_provenance.json")
    env["MINIANDROID_CLICK_AUDIT"] = os.path.join(rundir, "click_audit.jsonl")
    cmd = (f"{MA_BIN} run -o {rundir} --execution-mode real-dalvik "
           f"--frames 6 --width 1080 --height 1920 "
           f"--data-root {rundir}/data --apk {apk}")
    r = sh(cmd, env=env, timeout=180)
    return rundir, r.returncode, (r.stdout or "")[-2000:], (r.stderr or "")[-2000:]


def judge(case, meta, verdict):
    """Apply ORACLE.json to a verdict -> (ok, detail)."""
    req = meta["required_verdict"]
    overall = verdict.get("overall", "UNKNOWN")
    fails = set(verdict.get("failing_stages", []))
    if req == "ACCEPT":
        ok = overall in ("VISUALLY_VERIFIED", "INTERACTION_VERIFIED") or \
            (overall in ("VISUALLY_PARTIAL", "FRAME_CAPTURED") and not
             (fails & {"visual", "assets_resolved", "assets_decoded",
                       "assets_rendered"}))
        return ok, f"required ACCEPT, got {overall} fails={sorted(fails)}"
    if req == "REJECT":
        ok = overall in ("VISUALLY_PARTIAL", "FAILED") or bool(
            fails & {"visual", "input_target_visibility", "assets_rendered",
                     "frame_output", "geometry"})
        return ok, f"required REJECT, got {overall} fails={sorted(fails)}"
    if req == "REJECT_INTERACTION":
        bad = verdict.get("stages", {}).get("visual_change", {}).get("value")
        ok = overall not in ("INTERACTION_VERIFIED", "FULLY_VERIFIED")
        return ok, (f"must not reach interaction-verified: {overall}; "
                    f"visual_change={bad}")
    if req == "REJECT_VISUAL_CHANGE":
        vc = verdict.get("stages", {}).get("visual_change", {}).get("value")
        ok = overall not in ("INTERACTION_VERIFIED", "FULLY_VERIFIED") and \
            (vc in ("FAIL", "UNKNOWN", None) or
             overall in ("VISUALLY_PARTIAL", "FAILED"))
        return ok, f"visual_change must not PASS: {vc}, overall={overall}"
    if req == "REJECT_SHORT_WINDOW":
        scene = verdict.get("stages", {}).get("scene", {})
        ok = overall not in ("VISUALLY_VERIFIED", "INTERACTION_VERIFIED",
                             "FULLY_VERIFIED")
        return ok, (f"splash-only must not pass scene/full: overall="
                    f"{overall}, scene={scene.get('value')}")
    if req == "MEASURE":
        return True, f"measured: overall={overall} (density judged manually)"
    return False, f"unknown oracle {req}"


def main():
    oracle = json.load(open(os.path.join(BASE, "ORACLE.json")))
    cases = oracle["cases"]
    if not os.path.isfile(MA_BIN):
        print("runtime binary missing:", MA_BIN)
        return 3
    apks = build_apks(cases)
    results = {}
    battery_ok = True
    os.makedirs(VERDICTS, exist_ok=True)
    for case, meta in sorted(cases.items()):
        apk = apks.get(case)
        if not apk:
            results[case] = {"error": "apk build failed"}
            battery_ok = False
            continue
        rundir, rc, out, err = run_case(case, apk)
        vpath = os.path.join(VERDICTS, f"{meta['pkg']}.json")
        vr = subprocess.run(
            [sys.executable, os.path.join(REPO, "tools", "verify_graphics.py"),
             "verify-run", "--run-dir", rundir, "--apk", apk,
             "--package", meta["pkg"], "--out", vpath],
            capture_output=True, text=True)
        verdict = json.load(open(vpath)) if os.path.isfile(vpath) else \
            {"error": (vr.stderr or "no verdict")[-400:]}
        ok, detail = judge(case, meta, verdict)
        battery_ok = battery_ok and ok
        results[case] = {
            "oracle": meta["required_verdict"],
            "run_rc": rc,
            "verdict_overall": verdict.get("overall"),
            "failing_stages": verdict.get("failing_stages"),
            "battery": "PASS" if ok else "FAIL",
            "detail": detail,
        }
        print(f"{case:24s} {results[case]['battery']} "
              f"{results[case]['detail'][:110]}")
    summary = {
        "schema": "s92.battery_result.v1",
        "battery_ok": battery_ok,
        "cases": results,
    }
    with open(os.path.join(OUT, "BATTERY_RESULT.json"), "w") as f:
        json.dump(summary, f, indent=1, sort_keys=True)
    print("BATTERY:", "OK" if battery_ok else "BROKEN")
    return 0 if battery_ok else 1


if __name__ == "__main__":
    sys.exit(main())
