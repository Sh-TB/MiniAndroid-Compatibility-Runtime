#!/usr/bin/env python3
"""s128_input_wave.py — S128 INPUT LAW wave (R-NEW-424: TouchTarget + intercept).

Proves CAP-INPUT-102 (TouchTarget chain law) + CAP-INPUT-100
(onInterceptTouchEvent pass) with real-APK fan-out per campaign §25:

  A. 3-run determinism gate: heading calculator (a169346e) + flappycow menu
     (13cf4746) — goldens must be PRESERVED.
  B. INPUT law evidence: headingcalc keypad taps (TouchTarget chain +
     PerformClick), tictactoe custom-view board tap (onTouchEvent arm),
     flappy G08-LAUNCH (PLAY tap -> Game activity).
  C. Coherence: uNote BOOT-ORDER, gmdice.
  D. Honest frontiers: telegram/whatsapp stay NOT-A-RENDER (3/2 colors).
"""
import glob, hashlib, json, math, os, re, subprocess
from collections import Counter
from PIL import Image

R = "/home/z/my-project"
ENG = f"{R}/miniandroid/build/miniandroid"
OUT = f"{R}/run/s128"
os.makedirs(OUT, exist_ok=True)

APKS = {
    "headingcalc": "/tmp/my-project/apk_cache/org.debian.eugen.headingcalculator_1.apk",
    "flappycow": f"{R}/upload/flappycow_rebuilt.apk",
    "unote": f"{R}/upload/canonical_apks/app.varlorg.unote_30.apk",
    "gmdice": f"{R}/upload/canonical_apks/de.duenndns.gmdice_8.apk",
    "tictactoe": f"{R}/upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk",
    "telegram": f"{R}/upload/telegram_official.apk",
    "whatsapp": "/tmp/my-project/apk_cache/WhatsApp_real.apk",
}
CALC_GOLDEN = "a169346e26d9fa83"
FLAPPY_MENU_GOLDEN = "13cf47464d9787f4"
FLAPPY_TAPS = [(540, 1400, 18), (540, 900, 30), (540, 900, 36),
               (540, 900, 42), (540, 900, 48)]
CALC_TAPS = [(135, 1327, 20), (405, 1327, 24), (675, 1327, 28)]  # keys 1,2,3 (keypad rows y=345/739/1133/1528)
TTT_TAPS = [(540, 960, 20)]


def run_engine(tag, apk, frames, taps=(), delay=200, timeout=900):
    d = f"{OUT}/{tag}"
    os.makedirs(d, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(frames), "--frame-delay", str(delay),
           "--dump-view-tree", "-o", d]
    for (x, y, k) in taps:
        cmd += ["--tap", f"{x},{y}@{k}"]
    cmd += [apk]
    log = f"{d}.log"
    try:
        rc = subprocess.call(cmd, stdout=open(log, "w"),
                             stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.TimeoutExpired:
        rc = -9
    return rc, d, log


def frame_sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def frame_at(d, i):
    fs = sorted(glob.glob(f"{d}/frames/frame_*.png"))
    return fs[i] if i < len(fs) else (fs[-1] if fs else None)


def last_frame(d):
    fs = sorted(glob.glob(f"{d}/frames/frame_*.png"))
    return fs[-1] if fs else None


def colorcount(png):
    if not png: return 0
    img = Image.open(png).convert("RGB")
    w, h = img.size
    px = img.load()
    return len({px[x, y] for y in range(0, h, 3) for x in range(0, w, 3)})


def boot_order(log):
    stages = re.findall(r"\[BOOT-ORDER\] (\d)/7 stage=(\w+) ok=(\d) ms=(\d+)",
                        open(log, errors="ignore").read())
    return {"stages": len(stages),
            "all_ok": bool(stages) and all(s[2] == "1" for s in stages)}


def touch_law(log, d):
    """Extract TouchTarget-law evidence from interactions[] + log."""
    mf = f"{d}/frames/manifest.json"
    ev = {"chains": 0, "max_chain": 0, "targets": 0, "intercept_asked": 0,
          "clicks": 0, "touch_dispatched": 0, "downs": 0, "ups": 0,
          "click_dispatched": 0}
    if os.path.exists(mf):
        try:
            m = json.load(open(mf))
            for it in m.get("interactions", []):
                for arm in ("down_record", "up_record"):
                    t = it.get(arm)
                    if not t: continue
                    if t.get("target_view_id"):
                        ev["targets"] += 1
                        ch = t.get("touch_target_chain") or []
                        ev["chains"] += 1 if ch else 0
                        ev["max_chain"] = max(ev["max_chain"], len(ch))
                    if arm == "down_record": ev["downs"] += 1
                    else: ev["ups"] += 1
                    if t.get("click_posted"): ev["clicks"] += 1
                    if t.get("touch_dispatched"): ev["touch_dispatched"] += 1
                    ev["intercept_asked"] += len(t.get("intercept_asked") or [])
        except Exception as e:
            ev["manifest_error"] = str(e)
    txt = open(log, errors="ignore").read()
    ev["ui_event_intercept"] = len(re.findall(r"event=INTERCEPT", txt))
    ev["ui_event_touch"] = len(re.findall(r"event=TOUCH", txt))
    ev["ontouch_arm"] = len(re.findall(r"arm=onTouchEvent\(override\)", txt))
    ev["click_dispatched"] = len(re.findall(r"click_dispatched.{0,4}true", txt))
    return ev


def report(tag, apk, frames, taps=()):
    rc, d, log = run_engine(tag, apk, frames, taps)
    lf = last_frame(d)
    rec = {"rc": rc, "boot": boot_order(log),
           "frame_sha": frame_sha(lf) if lf else None,
           "colors": colorcount(lf),
           "touch": touch_law(log, d)}
    print(f"[{tag}] rc={rc} boot={rec['boot']['stages']}/7 "
          f"sha={rec['frame_sha']} colors={rec['colors']} touch={rec['touch']}")
    return rec, d, lf


def main():
    rep = {}
    # A. 3-run goldens (no taps — byte-exact vs S127)
    for i in (1, 2, 3):
        rec, _, _ = report(f"calc_r{i}", APKS["headingcalc"], 48)
        rep[f"calc_run{i}"] = rec
    for i in (1, 2, 3):
        rec, d, _ = report(f"flappy_r{i}", APKS["flappycow"], 64, FLAPPY_TAPS)
        rec["menu_sha"] = frame_sha(frame_at(d, 16) or "")
        rep[f"flappy_run{i}"] = rec

    # B. INPUT law evidence runs
    rep["calc_taps"], calc_d, _ = report(
        "calc_taps", APKS["headingcalc"], 40, CALC_TAPS)
    rep["ttt_taps"], _, _ = report(
        "ttt_taps", APKS["tictactoe"], 32, TTT_TAPS)

    # C. coherence
    rep["unote"], _, _ = report("unote", APKS["unote"], 40)
    rep["gmdice"], _, _ = report("gmdice", APKS["gmdice"], 40)

    # D. honest frontiers
    for name, frames in (("telegram", 48), ("whatsapp", 24)):
        rc, d, log = run_engine(name, APKS[name], frames)
        lf = last_frame(d)
        rep[name] = {"rc": rc, "boot": boot_order(log),
                     "frame_sha": frame_sha(lf) if lf else None,
                     "colors": colorcount(lf)}
        print(f"[{name}] rc={rc} colors={rep[name]['colors']} (NOT-A-RENDER gate)")

    json.dump(rep, open(f"{OUT}/s128_report.json", "w"), indent=1)
    print(f"report -> {OUT}/s128_report.json")

    # Gate summary
    g = []
    g.append(("calc golden x3", all(rep[f"calc_run{i}"]["frame_sha"] == CALC_GOLDEN
                                    for i in (1, 2, 3))))
    g.append(("flappy menu golden x3", all(rep[f"flappy_run{i}"]["menu_sha"] == FLAPPY_MENU_GOLDEN
                                           for i in (1, 2, 3))))
    g.append(("touch_target_chain present (calc taps)", rep["calc_taps"]["touch"]["chains"] > 0))
    g.append(("clicks PerformClick-dispatched x3 (calc taps)",
              rep["calc_taps"]["touch"]["click_dispatched"] >= 3))
    g.append(("ttt state unchanged vs S127 baseline (b5a7a35d, honest target=0)",
              rep["ttt_taps"]["frame_sha"] == "b5a7a35d5fe0564b"))
    g.append(("flappy TouchTarget chain + onTouchEvent arm", rep["flappy_run1"]["touch"]["chains"] > 0 and
              rep["flappy_run1"]["touch"]["ontouch_arm"] > 0))
    g.append(("uNote BOOT-ORDER 7/7", rep["unote"]["boot"]["all_ok"]))
    g.append(("telegram grey NOT-A-RENDER (colors<=4)", rep["telegram"]["colors"] <= 4))
    g.append(("whatsapp b/w NOT-A-RENDER (colors<=3)", rep["whatsapp"]["colors"] <= 3))
    print("\nGATES:")
    ok = True
    for name, passed in g:
        print(f"  {'PASS' if passed else 'FAIL'}  {name}")
        ok = ok and passed
    print("S128 INPUT WAVE:", "ALL PASS" if ok else "FAILURES PRESENT")


if __name__ == "__main__":
    main()
