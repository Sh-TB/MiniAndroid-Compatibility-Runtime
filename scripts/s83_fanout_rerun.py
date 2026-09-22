#!/usr/bin/env python3
"""S83-GFX-BASE §32 — F-NEW-159 fanout rerun.

One fix (LocaleInsetsShadow: LocaleList/Locale/WindowInsetsController
semantic shadows) → rerun the whole F-NEW-156 35-title onCreate-unwind
family at the current binary and measure the blast radius honestly:

  per title:
    run the cached APK with the S83 binary
    classify:
      SIG_159_PRESENT   — old F-NEW-159 signatures still in log (fix NOT effective)
      UNWIND_ONCREATE   — APP BOUNDARY unwind at onCreate still (other roots)
      ADVANCED          — old signature gone AND the app produced frames/pixels
                          OR reached deeper call sites (API_CALLS > 0)
    record first divergence evidence: the FIRST uncaught exception signature
    in the log (honest next-blocker naming, no status inflation).

Output: run/s83/fanout/FANOUT_S159.json + per-title engine.log.
"""
import json
import os
import re
import subprocess
import sys

ENG = "/home/z/my-project/miniandroid/build/miniandroid"
OUT = "/home/z/my-project/run/s83/fanout"
MAP = "/tmp/my-project/fanout_map.json"

SIG_159 = re.compile(r"toLanguageTags|setSystemBarsAppearance")
# S83 classification law: a signature only counts as PRESENT when it appears
# in an EXCEPTION context (THROWABLE-MSG / SYNTH-EXC / EXC-PROPAGATE /
# NullPointerException line). A [REC-MISS] dispatch line means the shadow
# HANDLED the call (execution continued) — that is the FIX working, not the
# failure recurring.
EXC_CTX = re.compile(r"THROWABLE-MSG|SYNTH-EXC|EXC-PROPAGATE|NullPointerException|FATAL")
UNWIND = re.compile(r"APP BOUNDARY unwind")
FIRST_EXC = re.compile(r"\[EXC-PROPAGATE\] (\S+) uncaught at caller (\S+)")

def main():
    found = json.load(open(MAP))["found"]
    os.makedirs(OUT, exist_ok=True)
    classify_only = "--classify-only" in sys.argv
    rows = []
    for tid, apk in found:
        rundir = os.path.join(OUT, tid)
        os.makedirs(rundir, exist_ok=True)
        log = os.path.join(rundir, "engine.log")
        rc = None
        if not classify_only or not os.path.exists(log):
            env = dict(os.environ)
            env["MINIANDROID_GFX_PROVENANCE"] = os.path.join(rundir, "provenance.json")
            cmd = [ENG, "run", "--execution-mode", "real-dalvik", "--frames", "4",
                   "--frame-delay", "300", "-o", rundir, apk]
            try:
                with open(log, "w") as lf:
                    rc = subprocess.call(cmd, stdout=lf, stderr=lf, timeout=180, env=env)
            except subprocess.TimeoutExpired:
                rc = -1
        txt = open(log, errors="ignore").read() if os.path.exists(log) else ""
        shot = os.path.join(rundir, "screenshot.png")
        shot_bytes = os.path.getsize(shot) if os.path.exists(shot) else 0
        nonwhite = 0
        try:
            from PIL import Image
            im = Image.open(shot).convert("RGBA")
            px = im.load()
            for y in range(0, im.size[1], 4):
                for x in range(0, im.size[0], 4):
                    if px[x, y][:3] != (255, 255, 255):
                        nonwhite += 1
        except Exception:
            pass
        # exception-context-only scan: a sig line is a real recurrence only
        # when its ±1-line window carries exception markers. A bare
        # [REC-MISS] dispatch line = the shadow HANDLED the call (the fix
        # working), never counted as recurrence.
        sig = False
        lines = txt.splitlines()
        for i, ln in enumerate(lines):
            if SIG_159.search(ln):
                window = "\n".join(lines[max(0, i - 1):i + 2])
                if EXC_CTX.search(window):
                    sig = True
                    break
        unwind = bool(UNWIND.search(txt))
        m = FIRST_EXC.search(txt)
        first_exc = f"{m.group(1)} at {m.group(2)}" if m else None
        api_calls = 0
        ma = re.search(r"API Calls: (\d+)", txt)
        if ma:
            api_calls = int(ma.group(1))
        cls = []
        if sig:
            cls.append("SIG_159_PRESENT")
        if unwind:
            cls.append("UNWIND_ONCREATE")
        if not sig and (api_calls > 0 or nonwhite > 0):
            cls.append("ADVANCED")
        rows.append({
            "title_id": tid, "rc": rc, "classes": cls,
            "sig_159_present": sig, "unwind_oncreate": unwind,
            "api_calls": api_calls, "nonwhite_quarter_sampled": nonwhite,
            "screenshot_bytes": shot_bytes,
            "first_uncaught_exception": first_exc,
        })
        print(f"{tid:9s} rc={rc} sig159={sig} unwind={unwind} "
              f"api={api_calls} nw={nonwhite} first_exc={first_exc}")
    json.dump(rows, open(os.path.join(OUT, "FANOUT_S159.json"), "w"), indent=1)
    n_sig = sum(1 for r in rows if r["sig_159_present"])
    n_adv = sum(1 for r in rows if "ADVANCED" in r["classes"])
    n_unwind = sum(1 for r in rows if r["unwind_oncreate"])
    print(f"\nSUMMARY: {len(rows)} titles | sig159 present: {n_sig} | "
          f"advanced past old blocker: {n_adv} | onCreate unwind remains: {n_unwind}")

if __name__ == "__main__":
    main()
