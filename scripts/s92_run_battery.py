#!/usr/bin/env python3
"""s92_run_battery.py — S92 §25/§40 false-positive battery runner (v2).

Two-phase, REAL execution only:
  phase 1 REFERENCE:  long-window run (crosses splash timers) with
        --dump-view-tree -> build visual contract from the app's own
        declared scene (observed confidence; sources live in fixtures/)
  phase 2 TEST:       oracle-window run (+ --tap at the contract's
        interaction target for interactive cases) -> verify_graphics
        verify-run with the reference contract -> judge vs ORACLE.json

Exit 0 only if the battery holds: ACCEPT cases accepted, REJECT cases
rejected. This is the §40 gate: the verifier may not be deployed to the
real corpus until it distinguishes every case here.
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
VERDICTS = os.path.join(OUT, "verdicts")
MA_BIN = os.path.join(REPO, "miniandroid", "build", "miniandroid")


def sh(cmd, env=None, timeout=240):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          env=env, timeout=timeout)


def run_mini(rundir, apk, frames, tap=None, dump_vt=False):
    os.makedirs(rundir, exist_ok=True)
    env = dict(os.environ)
    env["MINIANDROID_GFX_PROVENANCE"] = os.path.join(rundir,
                                                     "gfx_provenance.json")
    env["MINIANDROID_CLICK_AUDIT"] = os.path.join(rundir, "click_audit.jsonl")
    cmd = (f"{MA_BIN} run -o {rundir} --execution-mode real-dalvik "
           f"--frames {frames} --width 1080 --height 1920 --dump-view-tree "
           f"--data-root {rundir}/data --apk {apk}")
    if tap:
        cmd += f" --tap {tap[0]},{tap[1]}@{tap[2]}"
    r = sh(cmd, env=env)
    return r.returncode


def build_contract(apk, pkg, title, ref_run):
    out = os.path.join(OUT, "contracts", f"{pkg}.json")
    r = sh(f"{sys.executable} {REPO}/tools/build_visual_contract.py "
           f"--apk {apk} --package {pkg} --title {title} "
           f"--run-dir {ref_run} --out {out}")
    if not os.path.isfile(out):
        print("contract build failed:", (r.stderr or "")[-300:])
    return out


def tap_from_contract(contract_path):
    c = json.load(open(contract_path)) if os.path.isfile(contract_path) \
        else {}
    for t in c.get("interaction_targets", []):
        b = t.get("bounds") or []
        if len(b) == 4 and b[2] > 4 and b[3] > 4:
            return (int(b[0] + b[2] / 2), int(b[1] + b[3] / 2), 8)
    return None


def judge(case, meta, verdict):
    req = meta["required_verdict"]
    overall = verdict.get("overall", "UNKNOWN")
    fails = set(verdict.get("failing_stages", []))
    if req == "ACCEPT":
        ok = overall in ("VISUALLY_VERIFIED", "INTERACTION_VERIFIED") or \
            (overall in ("VISUALLY_PARTIAL", "FRAME_CAPTURED") and not
             (fails & {"visual", "assets_resolved", "assets_decoded",
                       "assets_rendered", "geometry", "frame_output"}))
        return ok, f"required ACCEPT, got {overall} fails={sorted(fails)}"
    if req == "REJECT":
        ok = overall in ("VISUALLY_PARTIAL", "FAILED") or bool(
            fails & {"visual", "input_target_visibility", "assets_rendered",
                     "frame_output", "geometry", "visual_change"})
        return ok, f"required REJECT, got {overall} fails={sorted(fails)}"
    if req == "REJECT_INTERACTION":
        ok = overall not in ("INTERACTION_VERIFIED", "FULLY_VERIFIED")
        return ok, f"must not reach interaction-verified: overall={overall}"
    if req == "REJECT_VISUAL_CHANGE":
        vc = verdict.get("stages", {}).get("visual_change", {}).get("value")
        ok = overall not in ("INTERACTION_VERIFIED", "FULLY_VERIFIED")
        return ok, f"visual_change={vc}, overall={overall} (must not FULL)"
    if req == "REJECT_SHORT_WINDOW":
        scene = verdict.get("stages", {}).get("scene", {})
        geom = verdict.get("stages", {}).get("geometry", {})
        ok = overall not in ("VISUALLY_VERIFIED", "INTERACTION_VERIFIED",
                             "FULLY_VERIFIED")
        return ok, (f"splash-only: overall={overall}, scene="
                    f"{scene.get('value')}, geometry={geom.get('value')}")
    if req == "MEASURE":
        dens = [c.get("DENSITY_CHECK") for c in verdict.get("asset_chains", [])
                if c.get("DENSITY_CHECK")]
        return True, (f"measured overall={overall}, density_checks={dens}, "
                      f"fails={sorted(fails)}")
    return False, f"unknown oracle {req}"


def main():
    oracle = json.load(open(os.path.join(BASE, "ORACLE.json")))
    cases = oracle["cases"]
    if not os.path.isfile(MA_BIN):
        print("runtime binary missing:", MA_BIN)
        return 3
    results = {}
    battery_ok = True
    os.makedirs(VERDICTS, exist_ok=True)
    for case, meta in sorted(cases.items()):
        apk = os.path.join(BASE, f"{case}.apk")
        if not os.path.isfile(apk):
            results[case] = {"error": "apk missing"}
            battery_ok = False
            continue
        pkg = meta["pkg"]
        ref = os.path.join(OUT, case, "reference")
        test = os.path.join(OUT, case, "test")
        rc1 = run_mini(ref, apk, frames=30)
        cpath = build_contract(apk, pkg, pkg, ref)
        tap = tap_from_contract(cpath)
        frames = 6 if meta["required_verdict"] == "REJECT_SHORT_WINDOW" else 12
        rc2 = run_mini(test, apk, frames=frames, tap=tap)
        vpath = os.path.join(VERDICTS, f"{pkg}.json")
        vr = sh(f"{sys.executable} {REPO}/tools/verify_graphics.py "
                f"verify-run --run-dir {test} --apk {apk} "
                f"--contract {cpath} --package {pkg} --out {vpath}")
        verdict = json.load(open(vpath)) if os.path.isfile(vpath) else \
            {"error": (vr.stderr or "no verdict")[-300:]}
        ok, detail = judge(case, meta, verdict)
        battery_ok = battery_ok and ok
        results[case] = {
            "oracle": meta["required_verdict"],
            "ref_rc": rc1, "test_rc": rc2,
            "tap": list(tap) if tap else None,
            "verdict_overall": verdict.get("overall"),
            "failing_stages": verdict.get("failing_stages"),
            "battery": "PASS" if ok else "FAIL",
            "detail": detail,
        }
        print(f"{case:24s} {results[case]['battery']} "
              f"{results[case]['detail'][:120]}")

    # ---- §40 verifier self-test: doctored-evidence rejection battery -----
    st = sh(f"{sys.executable} {REPO}/tools/verify_graphics.py selftest "
            f"--run-dir {os.path.join(OUT, 'good', 'test')} "
            f"--apk {os.path.join(BASE, 'good.apk')} "
            f"--contract {os.path.join(OUT, 'contracts', 'org.miniandroid.s92.good.json')}")
    selftest = {}
    raw = (st.stdout or "").strip()
    try:
        # F-NEW-198-era selftest prints ONE pretty JSON doc on stdout —
        # parse the whole document (the old last-line-only parse broke on
        # multi-line output and stored a stdout tail as "error").
        selftest = json.loads(raw)
    except Exception:
        try:
            selftest = json.loads(raw.splitlines()[-1])
        except Exception:
            selftest = {"error": (st.stderr or raw or "")[-300:]}
    battery_ok = battery_ok and bool(selftest.get("BATTERY_OK"))

    summary = {
        "schema": "s92.battery_result.v2",
        "battery_ok": battery_ok,
        "cases": results,
        "selftest_doctored_evidence": selftest,
    }
    with open(os.path.join(OUT, "BATTERY_RESULT.json"), "w") as f:
        json.dump(summary, f, indent=1, sort_keys=True)
    print("SELFTEST:", json.dumps(selftest)[:200])
    print("BATTERY:", "OK" if battery_ok else "BROKEN")
    return 0 if battery_ok else 1


if __name__ == "__main__":
    sys.exit(main())
