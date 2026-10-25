#!/usr/bin/env python3
"""CONT-32 — BATCH-20 census at the CONT-32 binary (CowStr lever + F-NEW-522).
Same 20-title set as cont13 (families A/B/C), fresh stores, 90s window.
Output: evidence/cont32/batch20_census.json"""
import hashlib, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
OUT = Path(f"{ROOT}/run/cont32_batch20")
OUT.mkdir(parents=True, exist_ok=True)
EV = Path(f"{ROOT}/evidence/cont32")
EV.mkdir(parents=True, exist_ok=True)

BATCH = [
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
    ("fossify_math",    "upload/fdroid_batch/org.fossify.math_10.apk"),
    ("fossify_notes",   "upload/fdroid_batch/org.fossify.notes_13.apk"),
    ("fossify_calendar","upload/fdroid_batch/org.fossify.calendar_23.apk"),
    ("fossify_clock",   "upload/fdroid_batch/org.fossify.clock_10.apk"),
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

def rec_pkg(apk_path):
    r = subprocess.run([f"{ROOT}/tools/aapt2/aapt2", "dump", "badging", str(apk_path)],
                       capture_output=True, text=True, timeout=60)
    m = re.search(r"^package: name='([^']+)'", r.stdout, re.M)
    return m.group(1) if m else None

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
    try:
        ip = subprocess.run([ENG, "install", str(apk), "--data-root", str(store)],
                            capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        rec.update({"install": "TIMEOUT"})
        return rec
    if ip.returncode != 0:
        rec.update({"install": "FAIL", "sig": (ip.stderr or ip.stdout or "")[-300:]})
        return rec
    rec["install"] = "OK"
    cmd = [ENG, "run", "--package", rec_pkg(apk), "--data-root", str(store),
           "--dump-view-tree", "--max-seconds", "90", "--frames", "6", "-o", str(run)]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=420)
    except subprocess.TimeoutExpired:
        rec.update({"run_rc": "TIMEOUT", "wall_s": round(time.time() - t0, 1)})
        return rec
    rec["run_rc"] = r.returncode
    rec["wall_s"] = round(time.time() - t0, 1)
    sig, v, rms, txt = signature(str(run / "run.log"))
    rec["sig"] = sig[0][1] if sig else None
    rec["verdict_line"] = v
    rec["rec_miss"] = ",".join(rms)[:260] if rms else None
    shot = run / "screenshot.png"
    if shot.exists():
        rec["screenshot_sha16"] = sha16(shot)
        rec["png"] = png_metrics(str(shot))
    # uncaught count
    rec["uncaught_n"] = len(re.findall(r"EXC-UNCAUGHT-TOP", txt)) or \
                        len(re.findall(r"uncaught", r.stdout or ""))
    return rec

def main():
    only = set(sys.argv[1:]) if len(sys.argv) > 1 else None
    results = []
    if (EV / "batch20_census.json").exists():
        try:
            results = json.load(open(EV / "batch20_census.json"))
        except Exception:
            results = []
    done = {r["label"]: r for r in results}
    for label, rel in BATCH:
        if only and label not in only:
            continue
        if label in done and done[label].get("png") and not only:
            continue
        t0 = time.time()
        rec = run_one(label, rel)
        done[label] = rec
        results = [done[k] for k in done]
        results = [r for r in results if r]
        # keep canonical order
        order = {lbl: i for i, (lbl, _) in enumerate(BATCH)}
        results.sort(key=lambda r: order.get(r["label"], 99))
        json.dump(results, open(EV / "batch20_census.json", "w"), indent=1)
        png = rec.get("png") or {}
        print(f"{label:20s} install={rec.get('install')} rc={rec.get('run_rc')} "
              f"px={png.get('content_px', '-'):>7} colors={png.get('distinct_colors', '-'):>5} "
              f"({round(time.time()-t0,1)}s)", flush=True)
    ok = sum(1 for r in results if (r.get("png") or {}).get("content_px", 0) >= 1000)
    print(f"\nCONTENT ROWS: {ok}/20")

if __name__ == "__main__":
    main()
