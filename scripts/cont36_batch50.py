#!/usr/bin/env python3
"""CONT-36 — batch-50 RE-CENSUS at the post-F-NEW-525/526/527/528/529 binary (user: «ادامه حل مشکل برنامه و بازی ۵۰ توسط ابزار ها»).
20 known titles (retention = regression gate vs cont33) + 30 NEW fdroid titles.
Pool of 2 workers (2 CPU / 3GB RAM). Chunked foreground: --limit N runs the
first N not-done titles then exits (background dies at tool-call boundary).
Output: evidence/cont36/batch50_census.json"""
import hashlib, json, os, re, shutil, subprocess, sys, time
from multiprocessing import Pool
from pathlib import Path

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
OUT = Path(f"{ROOT}/run/cont36_batch50")
EV = Path(f"{ROOT}/evidence/cont36")
OUT.mkdir(parents=True, exist_ok=True)
EV.mkdir(parents=True, exist_ok=True)

BATCH20 = [
    ("prism",            "upload/fdroid_batch/app.lonecloud.prism_10402.apk"),
    ("wocheneinkauf",    "upload/fdroid_batch/app.wocheneinkauf_199.apk"),
    ("matewave",         "upload/fdroid_batch/cc.skysparkle.matewave_2.apk"),
    ("sparkledns",       "upload/fdroid_batch/cc.skysparkle.sparkledns_10006.apk"),
    ("aurora",           "upload/fdroid_batch/com.aurora.store_76.apk"),
    ("awagam",           "upload/fdroid_batch/com.awagam.android_5.apk"),
    ("webstack",         "upload/fdroid_batch/com.chiranth7.webstack_6.apk"),
    ("compose_stopwatch","upload/cont54_refetch/com.justdeax.composeStopwatch_1009011.apk"),
    ("notepad",          "upload/fdroid_batch/com.nononsenseapps.notepad_72700.apk"),
    ("k9",               "upload/fdroid_batch/com.fsck.k9_39046.apk"),
    ("audiobook",        "upload/fdroid_batch/de.ph1b.audiobook_5410002.apk"),
    ("goodtime",         "upload/fdroid_batch/com.apps.adrcotfas.goodtime_364.apk"),
    ("netguard",         "upload/fdroid_batch/eu.faircode.netguard_2026080101.apk"),
    ("fossify_math",     "upload/fdroid_batch/org.fossify.math_10.apk"),
    ("fossify_notes",    "upload/fdroid_batch/org.fossify.notes_13.apk"),
    ("fossify_calendar", "upload/fdroid_batch/org.fossify.calendar_23.apk"),
    ("fossify_clock",    "upload/fdroid_batch/org.fossify.clock_10.apk"),
    ("dmfs_tasks",       "upload/fdroid_batch/org.dmfs.tasks_82200.apk"),
    ("surgeengine",      "upload/cont73_apks/org.opensurge2d.surgeengine_30650.apk"),
    ("bouncy",           "upload/canonical_apks/com.dozingcatsoftware.bouncy_43.apk"),
]
NEW30 = [
    ("uturn",            "upload/fdroid_batch/ac.stresa.uturn_22.apk"),
    ("chompass",         "upload/fdroid_batch/app.chompass_92.apk"),
    ("floatdeck",        "upload/fdroid_batch/app.floatdeck_8.apk"),
    ("peri",             "upload/fdroid_batch/app.simple.peri_983.apk"),
    ("sopadeletras",     "upload/fdroid_batch/app.sopadeletras_24.apk"),
    ("starlingmap",      "upload/fdroid_batch/app.starlingmap_2100.apk"),
    ("subster",          "upload/fdroid_batch/app.subster_201.apk"),
    ("voyager",          "upload/fdroid_batch/app.vger.voyager_988.apk"),
    ("how2vote",         "upload/fdroid_batch/au.how2vote.app_109001000.apk"),
    ("leradar",          "upload/fdroid_batch/ca.leradar.app_3.apk"),
    ("aat",              "upload/fdroid_batch/ch.bailu.aat_45.apk"),
    ("sunpiano",         "upload/fdroid_batch/code.alimiracle.sunpiano_2.apk"),
    ("batterymonitor",   "upload/fdroid_batch/codes.swistak.batterymonitor_1007003.apk"),
    ("firewall",         "upload/fdroid_batch/com.acutis.firewall_10006.apk"),
    ("ricochlime",       "upload/fdroid_batch/com.adilhanney.ricochlime_1140003.apk"),
    ("aeropayout",       "upload/fdroid_batch/com.aeropayout.game_12.apk"),
    ("amaze",            "upload/fdroid_batch/com.amaze.filemanager_126.apk"),
    ("fitbuddy",         "upload/fdroid_batch/com.anant.fitbuddy_82.apk"),
    ("gecko",            "upload/fdroid_batch/com.anant.gecko_3.apk"),
    ("airlyrics",        "upload/fdroid_batch/com.andsi.airlyrics_17.apk"),
    ("shizuwall",        "upload/fdroid_batch/com.arslan.shizuwall_51.apk"),
    ("balance",          "upload/fdroid_batch/com.ashkanrafiee.balance_29000.apk"),
    ("librecontacts",    "upload/fdroid_batch/com.ashkanrafiee.librecontactsbackup_32.apk"),
    ("listai",           "upload/fdroid_batch/com.avstaim.listai_29.apk"),
    ("aegis",            "upload/fdroid_batch/com.beemdevelopment.aegis_82.apk"),
    ("best_deskclock",   "upload/fdroid_batch/com.best.deskclock_2037.apk"),
    ("lumolight",        "upload/fdroid_batch/com.bitmavrick.lumolight_35.apk"),
    ("lrceditor",        "upload/fdroid_batch/com.cg.lrceditor_57.apk"),
    ("concealmobile",    "upload/fdroid_batch/com.concealnetwork.concealmobile_59.apk"),
    ("qssp",             "upload/fdroid_batch/com.curryplayer.quicksettingssoundprofile_11.apk"),
]
BATCH = BATCH20 + NEW30
ORDER = {lbl: i for i, (lbl, _) in enumerate(BATCH)}

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
        sigs.append(("SYNTH_EXC", s[:280]))
    props = re.findall(r"\[EXC-PROPAGATE\][^\n]*uncaught[^\n]*", txt)
    if props:
        sigs.append(("UNCAUGHT_SITE", props[-1][:280]))
    v = None
    for m in re.finditer(r"verdict=(\w+), first_missing_stage=(\w+)", txt):
        v = f"verdict={m.group(1)} first_missing={m.group(2)}"
    rms = []
    for m in re.finditer(r"\[REC-MISS\] (\S+) caller=(\S+)", txt):
        if m.group(1) not in rms:
            rms.append(m.group(1))
    if rms:
        sigs.append(("REC_MISS", ",".join(rms[:10])[:280]))
    uncaught = len(re.findall(r"EXC-UNCAUGHT-TOP", txt))
    return sigs, v, rms, uncaught

def run_one(job):
    label, rel = job
    t0 = time.time()
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
               else "C-listsize-516" if label in ("surgeengine", "bouncy", "dmfs_tasks")
               else "D-new")}
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
    sig, v, rms, unc = signature(str(run / "run.log"))
    rec["sig"] = sig[0][1] if sig else None
    rec["verdict_line"] = v
    rec["rec_miss"] = ",".join(rms)[:280] if rms else None
    rec["uncaught_n"] = unc
    shot = run / "screenshot.png"
    if shot.exists():
        rec["screenshot_sha16"] = sha16(shot)
        rec["png"] = png_metrics(str(shot))
    return rec

def load_results():
    f = EV / "batch50_census.json"
    if f.exists():
        try:
            return json.load(open(f))
        except Exception:
            pass
    return []

def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    only = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    results = load_results()
    done = {r["label"]: r for r in results}
    todo = [(lbl, rel) for lbl, rel in BATCH
            if lbl not in done and (only is None or lbl in only)][:limit]
    if not todo:
        print("nothing to do")
    else:
        t0 = time.time()
        with Pool(2) as pool:
            for rec in pool.imap_unordered(run_one, todo):
                done[rec["label"]] = rec
                results = [done[k] for k in sorted(done, key=lambda x: ORDER.get(x, 99))]
                json.dump(results, open(EV / "batch50_census.json", "w"), indent=1)
                png = rec.get("png") or {}
                print(f"[{round(time.time()-t0,1):>6}s] {rec['label']:20s} "
                      f"install={rec.get('install')} rc={rec.get('run_rc')} "
                      f"px={png.get('content_px', '-'):>7} colors={png.get('distinct_colors', '-'):>5} "
                      f"unc={rec.get('uncaught_n', '-')} wall={rec.get('wall_s', '-')}",
                      flush=True)
    total = len(done)
    ok = sum(1 for r in done.values() if (r.get("png") or {}).get("content_px", 0) >= 1000)
    print(f"\nPROGRESS: {total}/50 rows | CONTENT ROWS: {ok}")

if __name__ == "__main__":
    main()
