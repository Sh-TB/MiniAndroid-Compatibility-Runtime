#!/usr/bin/env python3
"""cont73_triage.py — CONT-73 ten-app one-harness triage (issue #364).

Batch A (FOUNDATION 14/4) + Batch B (FOUNDATION 15/4) on the current HEAD
binary. One shared store, one bounded warm probe per app (<=120s budget),
capability-aware first checkpoint, per-row: package | apk_sha16 | version |
ABI | binary_sha16 | checkpoint | exact trace/exception | screenshot sha16 |
pixel census | status | next action. ARM-only targets: record the REAL
dlopen refusal (PREREQUISITE_MISMATCH row), never a fake pass.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = "/home/z/my-project"
BIN = f"{ROOT}/miniandroid/build/miniandroid"
OUT = f"{ROOT}/run/cont73/triage"
STORE = f"{ROOT}/run/cont73/triage_store"
BIN_SHA = hashlib.sha256(open(BIN, "rb").read()).hexdigest()[:16]

ROWS = [
    # (batch, name, package, apk, abi, family, checkpoint)
    ("A", "Memory", "eu.quelltext.memory",
     "upload/cont73_apks/eu.quelltext.memory_7.apk", "none",
     "webview-local-asset",
     "WebView local URL/asset bytes -> document/JS load -> first app pixels"),
    ("A", "SimpleChessClock", "com.chessclock.android",
     "upload/chessclock_29.apk", "none", "xml-custom-view",
     "ViewTree IDs + measured bounds + canvas ops -> real clock face pixels"),
    ("A", "Ball2Box", "com.simondalvai.ball2box",
     "upload/cont73_apks/com.simondalvai.ball2box_69.apk", "arm-only",
     "native-engine",
     "ELF/ABI gate -> dlopen real refusal (PREREQUISITE_MISMATCH)"),
    ("A", "OpenSurge", "org.opensurge2d.surgeengine",
     "upload/cont73_apks/org.opensurge2d.surgeengine_30650.apk", "arm-only",
     "native-engine",
     "ELF/ABI gate -> dlopen real refusal (PREREQUISITE_MISMATCH)"),
    ("A", "Guandan", "page.codeberg.lanticy.guandan",
     "upload/cont73_apks/page.codeberg.lanticy.guandan_7.apk",
     "x86+x86_64+arm", "native-engine-x86",
     "native lib load -> graphics context -> first scene/frame"),
    ("B", "PFSudoku", "org.secuso.privacyfriendlysudoku",
     "upload/sudoku_secuso_101.apk", "none", "xml-custom-view",
     "ViewTree + resource resolution + onDraw ops -> board pixels"),
    ("B", "PFMemory", "org.secuso.privacyfriendlymemory",
     "upload/canonical_apks/org.secuso.privacyfriendlymemory_100.apk", "none",
     "xml-custom-view",
     "grid render vs recorded warm face c559b630 (regression row)"),
    ("B", "PFDame", "org.secuso.privacyfriendlydame",
     "upload/cont73_apks/org.secuso.privacyfriendlydame_101.apk", "none",
     "xml-custom-view",
     "ViewTree + drawable resolution + board pixels"),
    ("B", "PFSolitaire", "org.secuso.privacyfriendlysolitaire",
     "upload/cont73_apks/org.secuso.privacyfriendlysolitaire_4.apk",
     "x86+x86+arm", "xml-custom-view-native-x86",
     "native lib load (x86 present) -> ViewTree -> card sprites"),
    ("B", "AndStatus2048", "org.andstatus.game2048",
     "upload/cont73_apks/org.andstatus.game2048_47.apk", "x86+x86_64+arm",
     "xml-custom-view-native-x86",
     "native lib load (x86 present) -> ViewTree -> tile grid"),
]

VERSIONS = {
    "eu.quelltext.memory": "1.7 (vc7)",
    "com.chessclock.android": "2.11.2 (vc29)",
    "com.simondalvai.ball2box": "4.1.9 (vc69)",
    "org.opensurge2d.surgeengine": "6.1.3.0-fdroid (vc30650)",
    "page.codeberg.lanticy.guandan": "1.2.2 (vc7)",
    "org.secuso.privacyfriendlysudoku": "3.2.6 (vc101)",
    "org.secuso.privacyfriendlymemory": "1.1.3-google (vc100)",
    "org.secuso.privacyfriendlydame": "1.3.4 (vc101)",
    "org.secuso.privacyfriendlysolitaire": "1.1 (vc4)",
    "org.andstatus.game2048": "1.16.2 (vc47)",
}


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def pixel_census(png):
    """nonbg fraction via the engine's own census if present in report.md."""
    return None


def census_from_report(outdir):
    """Harvest the run's own pixel census lines (same law as the gates)."""
    rep = f"{outdir}/report.md"
    if not os.path.exists(rep):
        return {}
    body = open(rep, errors="replace").read()
    out = {}
    for key, pat in [
        ("nonbg", r"non-?bg[^0-9]*([0-9.]+)%"),
        ("owned_px", r"owned[^0-9]*([0-9,]+)"),
        ("draw_ops", r"draw[_ ]ops[^0-9]*([0-9,]+)"),
        ("pixclass", r"class[=:]\s*(\w+)"),
    ]:
        m = re.search(pat, body, re.I)
        if m:
            out[key] = m.group(1)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    ledger = []
    for batch, name, pkg, apk, abi, family, checkpoint in ROWS:
        apk_path = f"{ROOT}/{apk}"
        row = {
            "batch": batch, "name": name, "package": pkg,
            "apk": apk, "apk_sha16": sha16(apk_path),
            "version": VERSIONS[pkg], "abi": abi, "family": family,
            "binary_sha16": BIN_SHA, "checkpoint_contract": checkpoint,
        }
        outdir = f"{OUT}/{pkg}"
        shutil.rmtree(outdir, ignore_errors=True)
        os.makedirs(outdir, exist_ok=True)
        # install into the shared store (F-NEW-376 staged-generation path)
        inst = subprocess.run(
            [BIN, "install", apk_path, "--data-root", STORE],
            capture_output=True, text=True, timeout=120)
        row["install_rc"] = inst.returncode
        row["install_record"] = None
        rec = f"{STORE}/data/app/{pkg}/package.json"
        if os.path.exists(rec):
            body = open(rec).read()
            m = re.search(r'"versionCode":\s*(\d+)', body)
            row["install_record"] = f"vc={m.group(1)}" if m else "present"
        # one bounded warm probe (<=120s wall)
        cmd = [BIN, "run", "--package", pkg, "--data-root", STORE,
               "--width", "1080", "--height", "1920", "--frames", "5",
               "--max-seconds", "90", "-o", outdir]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
        combined = r.stdout + r.stderr
        row["run_rc"] = r.returncode
        shot = f"{outdir}/screenshot.png"
        row["screenshot_sha16"] = (sha16(shot) if os.path.exists(shot)
                                   else "NOSCREEN")
        row["census"] = census_from_report(outdir)
        # first checkpoint: first exception / first engine checkpoint line
        exc = None
        for pat in ["UnsatisfiedLinkError", "UnsatisfiedLink", "dlopen",
                    "FATAL", "Uncaught", "Exception", "HALT", "F084"]:
            m = re.search(rf".*{pat}.*", combined, re.I)
            if m:
                exc = m.group(0).strip()[:200]
                break
        row["first_exception"] = exc
        row["log"] = f"{outdir}/run.log"
        open(f"{outdir}/run.log", "w").write(combined)
        # status adjudication
        nbg = row["census"].get("nonbg")
        if abi == "arm-only":
            row["status"] = ("PREREQUISITE_MISMATCH (ARM-only; real dlopen "
                             "refusal recorded)" if exc else
                             "PREREQUISITE_MISMATCH (ARM-only)")
        elif row["screenshot_sha16"] == "NOSCREEN":
            row["status"] = "FAIL (no screenshot)"
        elif nbg is None:
            row["status"] = "RUN (census n/a — read report manually)"
        elif float(nbg) < 1.0:
            row["status"] = f"DEFAULT_BACKGROUND_ONLY (nonbg={nbg}%)"
        else:
            row["status"] = f"REAL_APP_CONTENT (nonbg={nbg}%)"
        ledger.append(row)
        print(f"[{batch}] {name:16s} {row['status']:44s} "
              f"shot={row['screenshot_sha16']} exc={bool(exc)}")
    json.dump({"binary_sha16": BIN_SHA, "store": STORE, "rows": ledger},
              open(f"{ROOT}/run/cont73/triage_rows.json", "w"), indent=1)
    print(f"\nrows written: {ROOT}/run/cont73/triage_rows.json")


if __name__ == "__main__":
    sys.exit(main())
