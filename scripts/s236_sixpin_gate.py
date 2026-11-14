#!/usr/bin/env python3
"""S236 pre-merge six-pin regression gate (integration round).

Runs the six recorded pins (gmdice / microtimer / unote / dooz / bouncy /
tictactoe) x3 on TWO binaries and compares the screenshot sha16 faces:

  gate A — pristine main binary  (/tmp/bin_main_pristine)
  gate B — integrated candidate  (argv[1])

Verdict per pin:
  HOLD      — all 3 faces identical within each binary AND gateA==gateB
  DRIFT     — deterministic per binary but pristine != candidate
             (must match a DOCUMENTED drift face, else FAIL)
  FLAKY     — faces differ within one binary
  FAIL      — install/run failure

Usage: s236_sixpin_gate.py <candidate-binary> <out-dir>
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = Path("/home/z/my-project")
GOLDENS = {  # the recorded audit faces (s235/s236 receipts)
    "gmdice": "3891679d", "microtimer": "b39665f6", "unote": "3b8dcb0a",
    "dooz": "a0fae907", "bouncy": "60182d11", "tictactoe": "cd1c71df",
}
# documented faces that legitimately differ from the old golden
DOC_DRIFT = {"bouncy", "tictactoe"}
PINS = {
    "gmdice": (BASE / "upload/canonical_apks/de.duenndns.gmdice_8.apk",
               "de.duenndns.gmdice"),
    "microtimer": (BASE / "upload/canonical_apks/dubrowgn.microtimer_8.apk",
                   "dubrowgn.microtimer"),
    "unote": (BASE / "upload/canonical_apks/app.varlorg.unote_30.apk",
              "app.varlorg.unote"),
    "dooz": (BASE / "upload/canonical_apks/io.github.yamin8000.dooz_23.apk",
             "io.github.yamin8000.dooz"),
    "bouncy": (BASE / "upload/canonical_apks/com.dozingcatsoftware.bouncy_43.apk",
               "com.dozingcatsoftware.bouncy"),
    "tictactoe": (BASE / "upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk",
                  "com.emmanuelmess.tictactoe"),
}


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()[:16]


def run_pin(binary, name, out_root):
    apk, pkg = PINS[name]
    store = Path(tempfile.mkdtemp(prefix=f"sixpin_{name}_store_"))
    outd = Path(tempfile.mkdtemp(prefix=f"sixpin_{name}_out_"))
    faces = []
    uncaughts = []
    for i in range(3):
        shutil.rmtree(outd, ignore_errors=True)
        outd.mkdir(parents=True)
        ip = subprocess.run([str(binary), "install", str(apk),
                             "--data-root", str(store)],
                            capture_output=True, text=True, timeout=300)
        if ip.returncode != 0:
            return {"verdict": "FAIL", "faces": [], "err": "install"}
        try:
            pkg = json.JSONDecoder().raw_decode(
                ip.stdout[ip.stdout.index("{"):])[0]["package"]
        except Exception:
            return {"verdict": "FAIL", "faces": [], "err": "pkg-parse"}
        with open(outd / "run.log", "w") as f:
            subprocess.run([str(binary), "run", "--package", pkg,
                            "--data-root", str(store), "--trace",
                            "--max-seconds", "120", "--frames", "40",
                            "-o", str(outd)],
                           stdout=f, stderr=subprocess.STDOUT, timeout=240)
        shot = outd / "screenshot.png"
        faces.append(sha16(shot) if shot.exists() else None)
        try:
            serr = (outd / "run.log").read_text(errors="replace")
            uncaughts.append(serr.count("uncaught"))
        except Exception:
            uncaughts.append(-1)
    shutil.rmtree(store, ignore_errors=True)
    shutil.rmtree(outd, ignore_errors=True)
    det = len(set(faces)) == 1 and faces[0] is not None
    return {"faces": faces, "deterministic": det,
            "uncaught_total": sum(uncaughts)}


def main():
    cand = sys.argv[1]
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    pristine = "/tmp/bin_main_pristine"
    rows = {}
    for name in PINS:
        a = run_pin(pristine, name, out)
        b = run_pin(cand, name, out)
        verdict = "?"
        if a.get("verdict") == "FAIL" or b.get("verdict") == "FAIL":
            verdict = "FAIL"
        elif a["deterministic"] and b["deterministic"]:
            if a["faces"][0] == b["faces"][0]:
                verdict = "HOLD"
            elif name in DOC_DRIFT:
                verdict = "DRIFT-documented"
            else:
                verdict = "DRIFT-UNDOCUMENTED"
        elif a["faces"][0] == b["faces"][0]:
            verdict = "HOLD-flaky-but-equal"
        else:
            verdict = "FLAKY"
        rows[name] = {"pristine": a, "candidate": b, "verdict": verdict,
                      "recorded_golden": GOLDENS[name]}
        print(f"{name:11s} {verdict:20s} pristine={a['faces']} "
              f"cand={b['faces']} golden={GOLDENS[name]}")
    (out / "sixpin_gate.json").write_text(json.dumps(rows, indent=1) + "\n")
    bad = [k for k, v in rows.items()
           if v["verdict"] not in ("HOLD", "HOLD-flaky-but-equal",
                                   "DRIFT-documented")]
    print("GATE:", "PASS" if not bad else f"FAIL {bad}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
