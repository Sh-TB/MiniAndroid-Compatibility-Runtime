#!/usr/bin/env python3
"""FINAL CAMPAIGN item 22 wave A — post-fix gates.
Runs the golden set 3x each (byte-identical screenshot SHA law) with the
rebuilt binary and extracts the frame verdict. Goldens:
  dooz            d602648e8e401895 (item21 wave A honest verdict)
  simplestopwatch 10446aaf0cd642cc (real content pixels)
  headingcalc     823 colors / 466062 px (real content untouched)
  microtimer      frame determinism (XML custom-view attach-law risk case)
  whatsapp        NO_ROOT verdict preserved
"""
import hashlib, json, os, re, subprocess, sys
from pathlib import Path

ENG = "/home/z/my-project/miniandroid/build/miniandroid"
CACHE = "/tmp/my-project/apk_cache"
OUT = Path("/tmp/fc22")

GOLDENS = [
    ("dooz",      f"{CACHE}/dooz.apk", 1, "d602648e8e401895"),
    ("ssw",       f"{CACHE}/omegacentauri.mobi.simplestopwatch_26.apk", 1, "10446aaf0cd642cc"),
    ("headingcalc", f"{CACHE}/org.debian.eugen.headingcalculator_1.apk", 1, None),
    ("microtimer",  f"{CACHE}/dubrowgn.microtimer_8.apk", 2, None),
    ("whatsapp",    f"{CACHE}/WhatsApp_real.apk", 1, None),
]

def sha16(p):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
    except FileNotFoundError:
        return None

def run(tag, apk, frames):
    import shutil
    d = OUT / tag
    # FRESH data-root per run: apps persist state (simplestopwatch stores its
    # elapsed time via SharedPreferences — a reused data-root lawfully loads
    # the previous run's state and renders differently). The golden law is
    # defined on a CLEAN data root.
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(frames), "--frame-delay", "200",
           "--data-root", f"{d}/data", "-o", str(d), apk]
    log = f"{OUT}/{tag}.log"
    try:
        rc = subprocess.call(cmd, stdout=open(log, "w"),
                             stderr=subprocess.STDOUT, timeout=600)
    except subprocess.TimeoutExpired:
        rc = -99
    return rc, log

def main():
    results = {}
    for tag, apk, frames, golden in GOLDENS:
        shas = []
        for i in range(3):
            rc, log = run(f"{tag}_r{i}", apk, frames)
            s = sha16(f"{OUT}/{tag}_r{i}/screenshot.png")
            shas.append(s)
            # verdict line
            verdict = None
            try:
                txt = open(log, errors="ignore").read()
                m = re.findall(r"FRAME VERDICT[^\"]*?:\s*\"?([A-Z_]+)", txt)
                if m: verdict = m[-1]
                if verdict is None:
                    m2 = re.findall(r"capture_verdict=([A-Z_]+)", txt)
                    if m2: verdict = m2[-1]
            except FileNotFoundError:
                pass
            results[f"{tag}_{i}"] = {"rc": rc, "sha": s, "verdict": verdict}
        identical = len(set(shas)) == 1 and shas[0] is not None
        match = "" if golden is None else (" MATCH-GOLDEN" if golden in shas else f" (golden {golden} NOT in {shas})")
        print(f"[GATE] {tag:12s} x3 sha={shas[0] if identical else shas} "
              f"{'BYTE-IDENTICAL' if identical else 'DRIFT'}{match} verdict={results[f'{tag}_0']['verdict']}")
    Path(f"{OUT}/gate_results.json").write_text(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
