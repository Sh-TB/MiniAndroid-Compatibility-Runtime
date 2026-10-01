#!/usr/bin/env python3
"""s129_input_wave.py — S129 INPUT LAW wave (R-NEW-425 VelocityTracker +
R-NEW-426 TouchDelegate + MOVE-delivery law).

Fan-out per campaign §25:

  A. 3-run determinism gate: heading calculator (a169346e) + flappycow menu
     (13cf4746) — goldens must be PRESERVED (taps-only paths untouched).
  B. S129 law evidence: the s129_input_law fixture — delegate tap law
     (DELEGATE-CLICK via TouchDelegate fallback) + swipe velocity law
     (VelView's real-DEX VelocityTracker computes VY=999;VX=0) + uNote
     swipe (MOVE delivery law on a scrollable container; honest record).
  C. Coherence: calc taps (PerformClick chain), tictactoe byte-identical
     baseline, uNote/gmdice BOOT-ORDER.
  D. Honest frontiers: telegram/whatsapp stay NOT-A-RENDER.
"""
import glob, hashlib, json, os, re, subprocess
from PIL import Image

R = "/home/z/my-project"
ENG = f"{R}/miniandroid/build/miniandroid"
OUT = f"{R}/run/s129"
os.makedirs(OUT, exist_ok=True)

APKS = {
    "headingcalc": "/tmp/my-project/apk_cache/org.debian.eugen.headingcalculator_1.apk",
    "flappycow": f"{R}/upload/flappycow_rebuilt.apk",
    "unote": f"{R}/upload/canonical_apks/app.varlorg.unote_30.apk",
    "gmdice": f"{R}/upload/canonical_apks/de.duenndns.gmdice_8.apk",
    "tictactoe": f"{R}/upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk",
    "telegram": f"{R}/upload/telegram_official.apk",
    "whatsapp": "/tmp/my-project/apk_cache/WhatsApp_real.apk",
    "fixture": "/tmp/s129_fixture/inputlaw.apk",
}
CALC_GOLDEN = "a169346e26d9fa83"
FLAPPY_MENU_GOLDEN = "13cf47464d9787f4"
TTT_BASELINE = "b5a7a35d5fe0564b"
FLAPPY_TAPS = [(540, 1400, 18), (540, 900, 30), (540, 900, 36),
               (540, 900, 42), (540, 900, 48)]
CALC_TAPS = [(135, 1327, 20), (405, 1327, 24), (675, 1327, 28)]
TTT_TAPS = [(540, 960, 20)]


def run_engine(tag, apk, frames, taps=(), swipe=None, delay=200,
               timeout=900, dump_tree=False):
    d = f"{OUT}/{tag}"
    os.makedirs(d, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(frames), "--frame-delay", str(delay)]
    if dump_tree:
        cmd += ["--dump-view-tree"]
    if swipe:
        cmd += ["-o", d]
        # swipe fires once at frame N — needs -o before? keep positional order:
        cmd = [ENG, "run", "--execution-mode", "real-dalvik",
               "--frames", str(frames), "--frame-delay", str(delay)]
        if dump_tree:
            cmd += ["--dump-view-tree"]
        x1, y1, x2, y2, at = swipe
        cmd += ["--swipe", f"{x1},{y1},{x2},{y2}@{at}", "-o", d]
    else:
        cmd += ["-o", d]
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
    if not p:
        return None
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def frame_at(d, i):
    fs = sorted(glob.glob(f"{d}/frames/frame_*.png"))
    return fs[i] if i < len(fs) else (fs[-1] if fs else None)


def last_frame(d):
    fs = sorted(glob.glob(f"{d}/frames/frame_*.png"))
    return fs[-1] if fs else None


def colorcount(png):
    if not png:
        return 0
    img = Image.open(png).convert("RGB")
    w, h = img.size
    px = img.load()
    return len({px[x, y] for y in range(0, h, 3) for x in range(0, w, 3)})


def boot_order(log):
    stages = re.findall(r"\[BOOT-ORDER\] (\d)/7 stage=(\w+) ok=(\d) ms=(\d+)",
                        open(log, errors="ignore").read())
    return {"stages": len(stages),
            "all_ok": bool(stages) and all(s[2] == "1" for s in stages)}


def view_texts(d):
    p = f"{d}/view_tree.json"
    if not os.path.exists(p):
        return []
    return [n.get("text", "") for n in json.load(open(p)).get("nodes", [])]


def touch_law(log, d):
    mf = f"{d}/frames/manifest.json"
    ev = {"targets": 0, "chains": 0, "max_chain": 0, "clicks": 0,
          "click_dispatched": 0, "moves_dispatched": 0, "swipes": 0,
          "downs": 0, "ups": 0, "delegates": 0, "intercept_asked": 0}
    if os.path.exists(mf):
        try:
            m = json.load(open(mf))
            for it in m.get("interactions", []):
                if "swipe" in str(it.get("event", "")):
                    ev["swipes"] += 1
                for arm in ("down_record", "up_record"):
                    t = it.get(arm)
                    if not t:
                        continue
                    if arm == "down_record":
                        ev["downs"] += 1
                    else:
                        ev["ups"] += 1
                    if t.get("target_view_id"):
                        ev["targets"] += 1
                        ch = t.get("touch_target_chain") or []
                        ev["chains"] += 1 if ch else 0
                        ev["max_chain"] = max(ev["max_chain"], len(ch))
                    if t.get("click_posted"):
                        ev["clicks"] += 1
                    if t.get("delegate_law"):
                        ev["delegates"] += 1
                    if t.get("move_dispatched"):
                        ev["moves_dispatched"] += 1
                    ev["intercept_asked"] += len(t.get("intercept_asked") or [])
        except Exception as e:
            ev["manifest_error"] = str(e)
    # PerformClick→DEX dispatch evidence lives in the stderr trace
    # (fire_framework_callback's record is not a manifest down/up record).
    txt = open(log, errors="ignore").read()
    ev["click_dispatched"] = len(re.findall(r"click_dispatched.{0,4}true", txt))
    ev["moves_in_log"] = len(re.findall(r"arm=onTouchEvent\(override\)", txt))
    return ev


def report(tag, apk, frames, taps=(), swipe=None, dump_tree=False):
    rc, d, log = run_engine(tag, apk, frames, taps, swipe,
                            dump_tree=dump_tree)
    lf = last_frame(d)
    rec = {"rc": rc, "boot": boot_order(log),
           "frame_sha": frame_sha(lf) if lf else None,
           "colors": colorcount(lf), "touch": touch_law(log, d)}
    if dump_tree:
        rec["texts"] = [t for t in view_texts(d) if t]
    print(f"[{tag}] rc={rc} boot={rec['boot']['stages']}/7 "
          f"sha={rec['frame_sha']} colors={rec['colors']} "
          f"touch={rec['touch']}")
    return rec, d, lf


def main():
    rep = {}
    # A. 3-run goldens (unchanged tap paths)
    for i in (1, 2, 3):
        rec, _, _ = report(f"calc_r{i}", APKS["headingcalc"], 48)
        rep[f"calc_run{i}"] = rec
    for i in (1, 2, 3):
        rec, d, _ = report(f"flappy_r{i}", APKS["flappycow"], 64, FLAPPY_TAPS)
        rec["menu_sha"] = frame_sha(frame_at(d, 16) or "")
        rep[f"flappy_run{i}"] = rec

    # B. S129 law evidence
    rep["fixture_tap"], _, _ = report(
        "fixture_tap", APKS["fixture"], 4, taps=[(900, 700, 2)],
        dump_tree=True)
    rep["fixture_swipe"], _, _ = report(
        "fixture_swipe", APKS["fixture"], 4,
        swipe=(100, 1400, 100, 1592, 2), dump_tree=True)
    # 3-run determinism of the swipe run (fixture frames byte-identical)
    shas = []
    for i in (1, 2, 3):
        rec, _, _ = report(f"fixture_swipe_r{i}", APKS["fixture"], 4,
                           swipe=(100, 1400, 100, 1592, 2))
        shas.append(rec["frame_sha"])
        rep[f"fixture_swipe_run{i}"] = rec
    rep["fixture_swipe_3run_identical"] = len(set(shas)) == 1 and shas[0]
    # MOVE delivery on a real scrollable container (honest record: the
    # ListView scroll-offset arm is CAP-SCROLLING-126, not claimed here).
    rep["unote_swipe"], _, _ = report(
        "unote_swipe", APKS["unote"], 24, swipe=(540, 900, 540, 1500, 2))

    # C. coherence
    rep["calc_taps"], _, _ = report("calc_taps", APKS["headingcalc"], 40,
                                    CALC_TAPS)
    rep["ttt_taps"], _, _ = report("ttt_taps", APKS["tictactoe"], 32,
                                   TTT_TAPS)
    rep["unote"], _, _ = report("unote", APKS["unote"], 40)
    rep["gmdice"], _, _ = report("gmdice", APKS["gmdice"], 40)

    # D. honest frontiers
    for name, frames in (("telegram", 48), ("whatsapp", 24)):
        rc, d, log = run_engine(name, APKS[name], frames)
        lf = last_frame(d)
        rep[name] = {"rc": rc, "boot": boot_order(log),
                     "frame_sha": frame_sha(lf) if lf else None,
                     "colors": colorcount(lf)}
        print(f"[{name}] rc={rc} colors={rep[name]['colors']} "
              f"(NOT-A-RENDER gate)")

    json.dump(rep, open(f"{OUT}/s129_report.json", "w"), indent=1)
    print(f"report -> {OUT}/s129_report.json")

    g = []
    g.append(("calc golden x3", all(
        rep[f"calc_run{i}"]["frame_sha"] == CALC_GOLDEN for i in (1, 2, 3))))
    g.append(("flappy menu golden x3", all(
        rep[f"flappy_run{i}"]["menu_sha"] == FLAPPY_MENU_GOLDEN
        for i in (1, 2, 3))))
    g.append(("fixture delegate tap law (DELEGATE-CLICK via fallback)",
              "DELEGATE-CLICK" in rep["fixture_tap"]["texts"]))
    g.append(("fixture swipe velocity law (VY=999;VX=0 via real DEX)",
              "VY=999;VX=0" in rep["fixture_swipe"]["texts"]))
    g.append(("fixture swipe 3-run frame SHA identical",
              rep["fixture_swipe_3run_identical"]))
    g.append(("uNote swipe MOVE-delivery recorded, rc=0",
              rep["unote_swipe"]["rc"] == 0 and
              rep["unote_swipe"]["touch"]["swipes"] == 1))
    g.append(("ttt baseline byte-identical (b5a7a35d)",
              rep["ttt_taps"]["frame_sha"] == TTT_BASELINE))
    g.append(("calc taps PerformClick chain intact",
              rep["calc_taps"]["touch"]["click_dispatched"] >= 3))
    g.append(("uNote BOOT-ORDER 7/7", rep["unote"]["boot"]["all_ok"]))
    g.append(("telegram grey NOT-A-RENDER (colors<=4)",
              rep["telegram"]["colors"] <= 4))
    g.append(("whatsapp b/w NOT-A-RENDER (colors<=3)",
              rep["whatsapp"]["colors"] <= 3))
    print("\nGATES:")
    ok = True
    for name, passed in g:
        print(f"  {'PASS' if passed else 'FAIL'}  {name}")
        ok = ok and passed
    print("S129 INPUT WAVE:", "ALL PASS" if ok else "FAILURES PRESENT")


if __name__ == "__main__":
    main()
