#!/usr/bin/env python3
"""CONT-41 — batch-50 census at the post-R-NEW-550/551/552 binary.
Same binary as the CONT-36 final gate, so the 13 content rows MUST retain
byte-exact (regression gate) and the 37 blanks report their POST-FIX faces.
User: «گیت هاب به روز رسانی ادامه ادامه تا هدف نهایی» — continue to the final goal.
Pool(2), chunked foreground (--limit N [only=label,...]).
Output: evidence/cont41/batch50_census.json + run/cont41_batch50/r_<label>/."""
import hashlib, json, os, re, shutil, subprocess, sys, time
from multiprocessing import Pool
from pathlib import Path

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
OUT = Path(f"{ROOT}/run/cont42t6_batch50")
EV = Path(f"{ROOT}/evidence/cont42t6")
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
    ("balance",          "upload/fdroid_batch/com.ashkanrafiee.balance_29000.apk"),
    ("best_deskclock",   "upload/fdroid_batch/com.best.deskclock_2037.apk"),
    ("shizuwall",        "upload/fdroid_batch/com.arslan.shizuwall_51.apk"),
    ("aegis",            "upload/fdroid_batch/com.beemdevelopment.aegis_82.apk"),
    ("lumolight",        "upload/fdroid_batch/com.bitmavrick.lumolight_35.apk"),
    ("lrceditor",        "upload/fdroid_batch/com.cg.lrceditor_57.apk"),
    ("concealmobile",    "upload/fdroid_batch/com.concealnetwork.concealmobile_59.apk"),
    ("qssp",             "upload/fdroid_batch/com.curryplayer.quicksettingssoundprofile_11.apk"),
    ("librecontacts",    "upload/fdroid_batch/com.ashkanrafiee.librecontactsbackup_32.apk"),
    ("listai",           "upload/fdroid_batch/com.avstaim.listai_29.apk"),
]
BATCH = BATCH20 + NEW30
ORDER = {lbl: i for i, (lbl, _) in enumerate(BATCH)}

def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]

def png_metrics(p):
    try:
        from PIL import Image
        import collections
        im = Image.open(p).convert("RGB")
        cnt = collections.Counter(im.getdata())
        bg = cnt.most_common(1)[0][0]
        content = sum(n for c, n in cnt.items() if c != bg)
        return {"w": im.width, "h": im.height,
                "distinct_colors": len(cnt),
                "content_px": content,
                "content_frac": round(content / (im.width * im.height), 4)}
    except Exception:
        return None

def rec_pkg(apk_path):
    r = subprocess.run([f"{ROOT}/tools/aapt2/aapt2", "dump", "badging", str(apk_path)],
                       capture_output=True, text=True)
    m = re.search(r"package: name='([^']+)'", r.stdout or "")
    return m.group(1) if m else None

def signature(logpath):
    sig, rms, v = [], [], None
    try:
        txt = open(logpath, errors="replace").read()
    except Exception:
        return sig, rms, v, 0
    for m in re.finditer(r"\[SYNTH-EXC\] (\S+) unwound (\S+) pc=(0x[0-9a-f]+)", txt):
        sig.append((m.group(1), f"{m.group(2)} pc={m.group(3)}"))
    v = re.search(r"FINAL-STATUS: (\S+)", txt)
    v = v.group(1) if v else None
    for m in re.finditer(r"REC-MISS ([^ \n]+)", txt):
        rms.append(m.group(1))
    return sig, rms, v, txt.count("uncaught")

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
    rec = {"label": label, "apk": os.path.basename(rel), "apk_sha16": sha16(apk)}
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
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=420)
    except subprocess.TimeoutExpired:
        rec.update({"run_rc": "TIMEOUT", "wall_s": round(time.time() - t0, 1)})
        return rec
    rec["run_rc"] = r.returncode
    rec["wall_s"] = round(time.time() - t0, 1)
    sig, v, verdict, unc = signature(str(run / "run.log"))
    rec["sig"] = sig[0][1] if sig else None
    rec["verdict_line"] = verdict
    rec["rec_miss"] = ",".join(v)[:280] if v else None
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
        import os
    with Pool(int(os.environ.get("CENSUS_POOL", "2"))) as pool:
            for rec in pool.imap_unordered(run_one, todo):
                done[rec["label"]] = rec
                results = [done[k] for k in sorted(done, key=lambda x: ORDER.get(x, 99))]
                json.dump(results, open(EV / "batch50_census.json", "w"), indent=1)
                png = rec.get("png") or {}
                print(f"[{round(time.time()-t0,1):>6}s] {rec['label']:20s} "
                      f"install={rec.get('install')} rc={rec.get('run_rc')} "
                      f"px={png.get('content_px', '-'):>7} colors={png.get('distinct_colors', '-'):>5} "
                      f"sig={str(rec.get('sig'))[:60]}",
                      flush=True)
    total = len(done)
    ok = sum(1 for r in done.values() if (r.get("png") or {}).get("content_px", 0) >= 1000)
    print(f"\nPROGRESS: {total}/50 rows | CONTENT ROWS: {ok}")

if __name__ == "__main__":
    main()
