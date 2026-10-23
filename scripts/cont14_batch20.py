#!/usr/bin/env python3
"""CONT-13 — BATCH 3 of the 20-by-20 directive (user: "ادامه و پوشش ۲۰ قطار").

20 titles = the three largest REMAINING recurring families from the #387
121-title census (census_v2_after), re-run at the TRUE post-CONT-12 head
(856261cf, F-NEW-517 getConstructors landed):

  A. Object.getClass umbrella survivors (13): prism, wocheneinkauf, matewave,
     sparkledns, aurora, awagam, webstack, composeStopwatch, notepad, k9,
     audiobook, goodtime, netguard
  B. fossify content-provider IAE family F-NEW-515 (4): fossify math/notes/
     calendar/clock
  C. List.size-on-null family F-NEW-516 (3): dmfs tasks, surgeengine, bouncy

Fresh stores, bounded launch window (census harness law), honest final-uncaught
signature + verdict + png metrics. Output: evidence/cont13/batch20_census_v2.json
"""
import hashlib, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
OUT = Path(f"{ROOT}/run/cont14_batch20")
OUT.mkdir(parents=True, exist_ok=True)
EV = Path(f"{ROOT}/evidence/cont14")
EV.mkdir(parents=True, exist_ok=True)

BATCH = [
    # --- A. Object.getClass umbrella survivors (13) ---
    ("prism",           "upload/fdroid_batch/app.lonecloud.prism_10402.apk"),
    ("wocheneinkauf",   "upload/fdroid_batch/app.wocheneinkauf_199.apk"),
    ("matewave",        "upload/fdroid_batch/cc.skysparkle.matewave_2.apk"),
    ("sparkledns",      "upload/fdroid_batch/cc.skysparkle.sparkledns_10006.apk"),
    ("aurora",          "upload/fdroid_batch/com.aurora.store_76.apk"),
    ("awagam",          "upload/fdroid_batch/com.awagam.android_5.apk"),
    ("webstack",        "upload/fdroid_batch/com.chiranth7.webstack_6.apk"),
    ("compose_stopwatch","upload/cont54_refetch/com.justdeax.composeStopwatch_1009011.apk"),
    ("notepad",         "upload/fdroid_batch/com.nononsenseapps.notepad_72700.apk"),
    ("k9",              "upload/fdroid_batch/com.fsck.k9_39046.apk"),
    ("audiobook",       "upload/fdroid_batch/de.ph1b.audiobook_5410002.apk"),
    ("goodtime",        "upload/fdroid_batch/com.apps.adrcotfas.goodtime_364.apk"),
    ("netguard",        "upload/fdroid_batch/eu.faircode.netguard_2026080101.apk"),
    # --- B. fossify F-NEW-515 family (4) ---
    ("fossify_math",    "upload/fdroid_batch/org.fossify.math_10.apk"),
    ("fossify_notes",   "upload/fdroid_batch/org.fossify.notes_13.apk"),
    ("fossify_calendar","upload/fdroid_batch/org.fossify.calendar_23.apk"),
    ("fossify_clock",   "upload/fdroid_batch/org.fossify.clock_10.apk"),
    # --- C. List.size F-NEW-516 family (3) ---
    ("dmfs_tasks",      "upload/fdroid_batch/org.dmfs.tasks_82200.apk"),
    ("surgeengine",     "upload/cont73_apks/org.opensurge2d.surgeengine_30650.apk"),
    ("bouncy",          "upload/canonical_apks/com.dozingcatsoftware.bouncy_43.apk"),
]


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def png_metrics(p):
    from PIL import Image
    try:
        im = Image.open(p).convert("RGB")
        w, h = im.size
        px = list(im.resize((min(w, 270), min(h, 480))).getdata())
        total = len(px)
        colors = {}
        for q in px:
            colors[q] = colors.get(q, 0) + 1
        bg = max(colors.values()) if colors else total
        return {"w": w, "h": h, "distinct_colors": len(colors),
                "content_px": total - bg,
                "content_frac": round((total - bg) / total, 4)}
    except Exception as e:
        return {"error": str(e)}


def signature(logpath):
    txt = open(logpath, errors="replace").read() if os.path.exists(logpath) else ""
    sigs = []
    for s in re.findall(r"\[SYNTH-EXC\][^\n]*", txt)[-3:]:
        sigs.append(("SYNTH_EXC", s[:260]))
    props = re.findall(r"\[EXC-PROPAGATE\][^\n]*uncaught[^\n]*", txt)
    if props:
        sigs.append(("UNCAUGHT_SITE", props[-1][:260]))
    v = None
    for m in re.finditer(r"verdict=(\w+), first_missing_stage=(\w+)", txt):
        v = f"verdict={m.group(1)} first_missing={m.group(2)}"
    rms = []
    for m in re.finditer(r"\[REC-MISS\] (\S+) caller=(\S+)", txt):
        if m.group(1) not in rms:
            rms.append(m.group(1))
    if rms:
        sigs.append(("REC_MISS", ",".join(rms[:10])[:260]))
    return sigs, v, rms, txt


def run_one(label, rel):
    apk = Path(ROOT) / rel
    store = OUT / f"store_{label}"
    run = OUT / f"r_{label}"
    for d in (store, run):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    rec = {"label": label, "apk": os.path.basename(rel), "apk_sha16": sha16(apk),
           "family_group": ("A-getClass" if label in (
               "prism", "wocheneinkauf", "matewave", "sparkledns", "aurora",
               "awagam", "webstack", "compose_stopwatch", "notepad", "k9",
               "audiobook", "goodtime", "netguard")
               else "B-fossify-515" if label.startswith("fossify_")
               else "C-listsize-516")}
    ip = subprocess.run([ENG, "install", str(apk), "--data-root", str(store)],
                        capture_output=True, text=True, timeout=300)
    if ip.returncode != 0:
        rec.update({"install": "FAIL", "sig": (ip.stderr or ip.stdout or "")[-300:]})
        return rec
    rec["install"] = "OK"
    cmd = [ENG, "run", "--package", rec_pkg(apk), "--data-root", str(store),
           "--dump-view-tree", "--max-seconds", "90", "--frames", "6", "-o", str(run)]
    t0 = time.time()
    with open(run / "run.log", "w") as lf:
        try:
            rc = subprocess.call(cmd, stdout=lf, stderr=subprocess.STDOUT, timeout=420)
        except subprocess.TimeoutExpired:
            rc = -99
            lf.write("\nTIMEOUT\n")
    rec["run_rc"] = rc
    rec["wall_s"] = round(time.time() - t0, 1)
    sigs, v, rms, log = signature(str(run / "run.log"))
    rec["verdict"] = v
    m = re.search(r"app_draw_ops[=:]?\s*(\d+)", log)
    rec["app_draw_ops"] = int(m.group(1)) if m else None
    fbn = re.search(r"\[EXP092-COPY\] fb has (\d+) non-white pixels", log)
    rec["fb_nonwhite"] = int(fbn.group(1)) if fbn else None
    ss = run / "screenshot.png"
    if ss.exists():
        rec["screenshot_sha16"] = sha16(ss)
        rec["png"] = png_metrics(ss)
    final_exc = None
    for kind, s in sigs:
        if kind == "SYNTH_EXC":
            final_exc = s
    if not final_exc:
        for kind, s in sigs:
            if kind == "UNCAUGHT_SITE":
                final_exc = s
                break
    rec["sig"] = final_exc or (v or "no-signal")[:200]
    rec["rec_miss"] = next((s for k, s in sigs if k == "REC_MISS"), None)
    rec["loading_screen"] = bool(
        (rec.get("app_draw_ops") or 0) > 0 or (rec.get("fb_nonwhite") or 0) > 2000
        or (rec.get("png", {}).get("content_px") or 0) > 2000)
    return rec


_PKG = None
def rec_pkg(apk):
    r = subprocess.run([f"{ROOT}/tools/aapt2/aapt2", "dump", "badging", str(apk)],
                       capture_output=True, text=True, timeout=60)
    m = re.search(r"^package: name='([^']+)'", r.stdout, re.M)
    return m.group(1) if m else None


def main():
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    results = []
    if (EV / "batch20_census_v2.json").exists():
        try:
            results = json.load(open(EV / "batch20_census_v2.json"))
        except Exception:
            results = []
    done = {r.get("label") for r in results}
    for label, rel in BATCH:
        if only and label not in only:
            continue
        if label in done:
            continue
        print(f"=== {label} ({rel})", flush=True)
        try:
            rec = run_one(label, rel)
        except Exception as e:
            rec = {"label": label, "apk": rel, "install": "HARNESS-ERROR",
                   "sig": str(e)[:200]}
        results.append(rec)
        json.dump(results, open(EV / "batch20_census_v2.json", "w"), indent=1)
        print(f"  -> {rec.get('verdict')} ops={rec.get('app_draw_ops')} "
              f"fb={rec.get('fb_nonwhite')} load={rec.get('loading_screen')} "
              f"sig={str(rec.get('sig'))[:110]}", flush=True)
    print(json.dumps({r["label"]: {"v": r.get("verdict"), "ops": r.get("app_draw_ops")}
                      for r in results}, indent=1))


if __name__ == "__main__":
    main()
