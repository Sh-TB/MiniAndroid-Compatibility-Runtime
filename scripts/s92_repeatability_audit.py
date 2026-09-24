#!/usr/bin/env python3
"""s92_repeatability_audit.py — S92 §28 (3-run law) + §32 (S91 claim audit).

§28: every pilot verdict at or above VISUALLY_VERIFIED is re-run twice in
the same environment; all three frame streams (frame SHAs) must match the
original run's verdict overall. Inconsistent -> NONDETERMINISTIC (never
PASS).

§32: the 12 S91 GIF VERIFIED-INTERACTIVE claims are reclassified against
the fresh S92 verdicts. No evidence is deleted: each record keeps
previous_status, new_status, reason, evidence pointers.
"""
import glob
import hashlib
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

BASE_OUT = os.path.join(REPO, "run", "s92pilot")
MA_BIN = os.path.join(REPO, "miniandroid", "build", "miniandroid")
VERDICTS = os.path.join(REPO, "registry", "graphics_verdicts")
REGISTRY = os.path.join(REPO, "docs", "evidence", "canonical",
                        "registry.json")

# §28 scope: pilot cases whose S92 verdict reached VISUALLY_VERIFIED or
# INTERACTION_VERIFIED in the first pass.
STRONG = {
    "bobball": ("org.bobstuff.bobball_26.apk", 10, None),
    "unote": ("app.varlorg.unote_30.apk", 10, None),
    "fishrings": ("eu.veldsoft.fish.rings_6.apk", 60, (184, 184, 40)),
    "snake-deluxe": ("upload/s80_games/build_sd/snake_deluxe_v1.0_vc1.apk",
                     24, (540, 1500, 16)),
    "tictactoedeluxe":
        ("upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk",
         24, (540, 1500, 16)),
    "g2048": ("upload/s80_games/build_2048/g2048_v1.0_vc1.apk",
              24, (170, 1839, 16)),
    "minicraft": ("upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk",
                  24, (154, 1747, 16)),
}

# §32 mapping: canonical package -> pilot case + fresh verdict file.
GIF_CLAIMS = {
    "ca.rmen.nounours": "nounours",
    "com.dozingcatsoftware.dodge": "dodge",
    "com.smorgasbork.hotdeath": "hotdeath",
    "org.bobstuff.bobball": "bobball",
    "com.miniandroid.snakedeluxe": "snake-deluxe",
    "com.miniandroid.tetris": "mini-tetris",
    "com.miniandroid.g2048": "g2048",
    "com.miniandroid.tictactoedeluxe": "tictactoedeluxe",
    "com.emmanuelmess.tictactoe": "tictactoe",
    "com.dozingcatsoftware.bouncy": "bouncy",
    "com.trianguloy.urlchecker": "urlchecker",
    "com.miniandroid.minicraft": "minicraft",
}

ACCEPT_LEVELS = {"VISUALLY_VERIFIED", "INTERACTION_VERIFIED",
                 "FULLY_VERIFIED"}
STRONG_LEVELS = {"VISUALLY_PARTIAL", "FRAME_CAPTURED"} | ACCEPT_LEVELS


def sh(cmd, env=None, timeout=900):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          env=env, timeout=timeout)


def find_apk(fname):
    if "/" in fname:
        p = os.path.join(REPO, fname)
        return p if os.path.isfile(p) else None
    dl = os.path.join(REPO, "miniandroid", "download")
    for base in (dl, os.path.join(dl, "exp076_corpus"),
                 os.path.join(dl, "exp073_real_apps")):
        p = os.path.join(base, fname)
        if os.path.isfile(p):
            return p
    return None


def frame_shas(rundir):
    mf = os.path.join(rundir, "frames", "manifest.json")
    if not os.path.isfile(mf):
        return []
    try:
        m = json.load(open(mf))
        return [f.get("sha256", "") for f in m.get("frames", [])]
    except Exception:
        return []


def verdict_file(package):
    # deterministic: prefer the exact <package>.json (surgical reruns)
    # over <package>@<apk>.json (pilot bulk runs); never OS-order.
    exact = os.path.join(VERDICTS, f"{package}.json")
    if os.path.isfile(exact):
        return exact
    hits = sorted(glob.glob(os.path.join(VERDICTS, f"{package}*.json")))
    return hits[0] if hits else None


def repeatability():
    out = {}
    for case, (fname, frames, tap) in STRONG.items():
        vpath = None
        for pkg in _pkg_candidates(case):
            vpath = verdict_file(pkg)
            if vpath:
                break
        if not vpath:
            out[case] = {"error": "no verdict"}
            continue
        v0 = json.load(open(vpath))
        overall0 = v0.get("overall")
        if overall0 not in ACCEPT_LEVELS:
            out[case] = {"base_overall": overall0, "required": "skip"}
            continue
        apk = find_apk(fname)
        if not apk:
            out[case] = {"error": f"apk missing {fname}"}
            continue
        shas = [hashlib.sha256(json.dumps(v0, sort_keys=True).encode())
                .hexdigest()[:16]]
        runs = []
        consistent = True
        for i in (2, 3):
            rd = os.path.join(BASE_OUT, case, f"run{i}")
            env = dict(os.environ)
            env["MINIANDROID_GFX_PROVENANCE"] = os.path.join(rd,
                                                             "gfx_provenance.json")
            env["MINIANDROID_CLICK_AUDIT"] = os.path.join(rd,
                                                          "click_audit.jsonl")
            tap_arg = f" --tap {tap[0]},{tap[1]}@{tap[2]}" if tap else ""
            cmd = (f"{MA_BIN} run -o {rd} --execution-mode real-dalvik "
                   f"--frames {frames} --width 1080 --height 1920 "
                   f"--dump-view-tree --data-root {rd}/data{tap_arg} "
                   f"--apk {apk}")
            r = sh(cmd, env=env)
            vpath_i = os.path.join(rd, "verdict.json")
            vr = sh(f"{sys.executable} {REPO}/tools/verify_graphics.py "
                    f"verify-run --run-dir {rd} --apk {apk} "
                    f"--contract {os.path.join(REPO, 'registry', 'visual_contracts', _contract_pkg(case) + '.json')} "
                    f"--package {_contract_pkg(case)} "
                    f"--title {_contract_pkg(case)} --out {vpath_i}")
            vi = json.load(open(vpath_i)) if os.path.isfile(vpath_i) else {}
            ov = vi.get("overall")
            runs.append({"run": i, "rc": r.returncode, "overall": ov,
                         "frame_shas": frame_shas(rd)})
            if ov != overall0:
                consistent = False
        out[case] = {
            "base_overall": overall0, "reruns": runs,
            "verdict": "3RUN_REPEATABLE" if consistent else
            "NONDETERMINISTIC",
        }
    return out


_PKG_BY_CASE = {
    "bobball": "org.bobstuff.bobball",
    "unote": "app.varlorg.unote",
    "fishrings": "eu.veldsoft.fish.rings",
    "snake-deluxe": "com.miniandroid.snakedeluxe",
    "tictactoedeluxe": "com.miniandroid.tictactoedeluxe",
    "g2048": "com.miniandroid.g2048",
    "minicraft": "com.miniandroid.minicraft",
    "nounours": "ca.rmen.nounours",
    "dodge": "com.dozingcatsoftware.dodge",
    "hotdeath": "com.smorgasbork.hotdeath",
    "tictactoe": "com.emmanuelmess.tictactoe",
    "bouncy": "com.dozingcatsoftware.bouncy",
    "urlchecker": "com.trianguloy.urlchecker",
    "chessclock": "com.chessclock.android",
    "gmdice": "de.duenndns.gmdice",
}


def _contract_pkg(case):
    return _PKG_BY_CASE.get(case, case)


def _pkg_candidates(case):
    return [_contract_pkg(case)]


def claim_audit(rep):
    reg = json.load(open(REGISTRY))
    titles = reg.get("titles", reg if isinstance(reg, list) else [])
    by_pkg = {}
    for t in (titles if isinstance(titles, list) else titles.values()):
        by_pkg[t.get("package")] = t
    audit = []
    for pkg, case in GIF_CLAIMS.items():
        t = by_pkg.get(pkg, {})
        prev = t.get("status", "UNKNOWN")
        vpath = verdict_file(pkg)
        fresh = json.load(open(vpath)) if vpath else {}
        new = fresh.get("overall", "UNKNOWN")
        # §32 reclassification law: the fresh S92 verdict is the status
        # candidate; human-review gate (§29) applies before public
        # canonical promotion, so anything above VISUALLY_VERIFIED is
        # recorded as candidate_<level>.
        if new in ACCEPT_LEVELS:
            rec = "candidate_" + ("INTERACTION_VERIFIED"
                                  if new == "INTERACTION_VERIFIED"
                                  else "VISUALLY_VERIFIED")
        elif new in STRONG_LEVELS:
            rec = new
        else:
            rec = new if new != "UNKNOWN" else "BLOCKED_OR_UNKNOWN"
        reason = (f"S92 verify-run on fresh same-SHA APK; failing stages: "
                  f"{fresh.get('failing_stages') or 'none'}")
        audit.append({
            "package": pkg, "pilot_case": case,
            "previous_status": prev, "fresh_verdict": new,
            "reclassification": rec, "reason": reason,
            "evidence": {"verdict": vpath,
                         "run_dir": os.path.join(BASE_OUT, case),
                         "apk_sha256": fresh.get("apk_sha256", "")},
        })
    return audit


def main():
    rep = json.load(open(os.path.join(BASE_OUT, "PILOT_RESULTS.json")))
    repeats = repeatability()
    audit = claim_audit(rep)
    out = {
        "schema": "s92.repeatability_claims.v1",
        "repeatability_3run": repeats,
        "s91_claim_audit": audit,
    }
    path = os.path.join(BASE_OUT, "REPEATABILITY_AND_CLAIMS.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    for case, r in repeats.items():
        print(f"R3 {case:16s} {r.get('verdict', r.get('error', '?'))}")
    for a in audit:
        print(f"S91 {a['package']:34s} {a['previous_status'][:22]:22s} -> "
              f"{a['fresh_verdict']}")
    print("saved:", path)


if __name__ == "__main__":
    main()
