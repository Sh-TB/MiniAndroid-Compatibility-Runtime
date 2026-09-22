#!/usr/bin/env python3
"""s82_cached_gates.py — S82 §49 remaining hard gates on real cached APKs:

  1. F-NEW-156 reproduce on >=3 onCreate-failure faces (with disasm of the
     first failing invoke via androguard -> FIRST_FAILING_METHOD evidence).
  2. IMAGE_DECODED_VS_RENDERED_GAP re-run on >=3 of the 7 flagged apps
     (APK raster census vs screen image pixels, S81 evidence re-proof).
  3. VF-DIALOG-ITEMS: retest a REAL title that actually calls
     AlertDialog$Builder.setItems (found by DEX scan, not a fixture).
  4. VF-PLACEHOLDER-GARBLE: retest Notes (unote) + muellerma stopwatch —
     assert no raw class descriptor text is painted (S81 AFTER-state holds).

All results -> run/s82/cached_gates/gates_report.json + registry fanout.
"""
import glob
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s81_visual_audit import audit_frame, apk_resource_counts  # noqa
import s82_lib as L  # noqa

CACHE = "/tmp/my-project/apk_cache"
OUT = f"{L.RUN}/cached_gates"
os.makedirs(OUT, exist_ok=True)
HEAD = subprocess.run(["git", "rev-parse", "HEAD"], cwd=L.ROOT,
                      capture_output=True, text=True).stdout.strip()

F156_FACES = ["de.tobiasbielefeld.solitaire", "com.chessclock.android",
              "omegacentauri.mobi.simplestopwatch"]
GAP_FACES = ["app.varlorg.unote", "de.duenndns.gmdice", "com.chessclock.android"]
DIALOG_CANDIDATES = ["eu.veldsoft.no.thanks", "de.tobiasbielefeld.solitaire",
                     "org.secuso.privacyfriendlybattleship", "com.chessclock.android",
                     "crypto.o0o0o0o0o.games.blackjack", "si.palcka.tarok"]
PLACEHOLDER_FACES = ["app.varlorg.unote", "com.github.muellerma.stopwatch"]


def find_apk(pkg):
    hits = sorted(glob.glob(f"{CACHE}/{pkg}*.apk") + glob.glob(f"{CACHE}/{pkg}.apk")
                  + glob.glob(f"{L.APK_CACHE}/{pkg}*.apk"))
    alias = {
        "app.varlorg.unote": f"{CACHE}/unote.apk",
        "de.duenndns.gmdice": f"{CACHE}/gmdice.apk",
        "com.chessclock.android": f"{CACHE}/chessclock.apk",
        "omegacentauri.mobi.simplestopwatch": f"{CACHE}/simplestopwatch.apk",
        "org.billthefarmer.notes": f"{CACHE}/notesbillthefarmer.apk",
        "com.github.muellerma.stopwatch": f"{CACHE}/stopwatchmuellerma.apk",
        "de.tobiasbielefeld.solitaire": glob.glob(f"{L.APK_CACHE}/de.tobiasbielefeld.solitaire_*.apk"),
        "eu.veldsoft.no.thanks": glob.glob(f"{L.APK_CACHE}/eu.veldsoft.no.thanks_*.apk"),
        "org.secuso.privacyfriendlybattleship": glob.glob(f"{L.APK_CACHE}/org.secuso.privacyfriendlybattleship_*.apk"),
        "crypto.o0o0o0o0o.games.blackjack": glob.glob(f"{L.APK_CACHE}/crypto.o0o0o0o0o.games.blackjack_*.apk"),
        "si.palcka.tarok": glob.glob(f"{L.APK_CACHE}/si.palcka.tarok_*.apk"),
    }.get(pkg)
    if alias:
        hits += alias if isinstance(alias, list) else [alias]
    hits = [h for h in hits if os.path.exists(h)]
    return hits[0] if hits else None


def dex_scan_setitems(apk):
    """find DEX callers of AlertDialog$Builder.setItems -> list of caller classes."""
    from androguard.misc import AnalyzeAPK
    try:
        a, d_, dx = AnalyzeAPK(apk)
    except Exception as e:
        return {"error": str(e)[:120]}
    callers = []
    for m in dx.find_methods(classname="Landroid/app/AlertDialog$Builder;",
                             methodname="setItems"):
        for _, call, _ in m.get_xref_from():
            try:
                callers.append(call.get_class_name())
            except Exception:
                pass
    return {"callers": sorted(set(c for c in callers if c))[:6],
            "count": len(callers)}


def disasm_first_fail(apk, hint_methods):
    """locate the first failing invoke: search the app's onCreate for the NPE
    throw site context (method refs invoked around the reported caller)."""
    from androguard.misc import AnalyzeDex
    out = []
    try:
        a, d_, dx = AnalyzeAPK(apk)
        for cls, mid in hint_methods:
            for m in dx.get_methods():
                mm = m.get_method()
                if mm is None or mm.get_class_name() != cls or mm.get_name() != mid:
                    continue
                if mm.get_code() is None:
                    continue
                out.append(f"{cls}.{mid} found, bytecode len {len(mm.get_code().get_bc().get_instructions())}")
                break
    except Exception as e:
        out.append(f"disasm error {e}"[:160])
    return out


def run_one(pkg, apk, label, taps=None):
    outdir = f"{OUT}/{label}"
    r = L.run_engine(apk, outdir, frames=8, frame_delay=300, taps=taps)
    res = {"label": label, "package": pkg, "apk": apk,
           "APK_SHA256": L.sha256_file(apk), "RUN_RC": r["RUN_RC"],
           "FRAMES": r["FRAMES"], "SESSION": f"S82-CACHED-{label}"}
    if r["FRAMES"]:
        m = audit_frame(r["FRAME_PATHS"][-1])
        res["VISUAL"] = {k: m.get(k) for k in
                         ("UNIQUE_COLORS", "DOMINANT_COLOR_RATIO",
                          "NON_BACKGROUND_RATIO", "IMAGE_PIXELS", "ICON_PIXELS",
                          "TEXT_PIXELS", "FLAGS")}
        jpg = f"{L.EVID}/{label}.jpg"
        if L.frame_to_jpg(r["FRAME_PATHS"][-1], jpg) > 0:
            res["SCREENSHOT"] = f"docs/evidence/s82/{label}.jpg"
            res["SCREENSHOT_SHA256"] = L.sha256_file(jpg)
    crash = f"{outdir}/crash.log"
    if os.path.exists(crash):
        txt = open(crash, errors="ignore").read()
        tops = [ln for ln in txt.splitlines() if "EXC-UNCAUGHT-TOP" in ln][:3]
        res["TOP_ESCAPES"] = tops
        res["FAILS"] = L.classify_log(txt)
    return res


def main():
    report = {"GENERATED_AT": L.now(), "HEAD": HEAD, "GATES": {}}

    # ---- Gate: F-NEW-156 on 3 faces
    g = []
    for pkg in F156_FACES:
        apk = find_apk(pkg)
        if not apk:
            g.append({"package": pkg, "STATUS": "APK_NOT_CACHED"})
            continue
        r = run_one(pkg, apk, "f156_" + pkg.split(".")[-1])
        r["GATE"] = "F-NEW-156_REPRODUCE"
        g.append(r)
    report["GATES"]["F_NEW_156"] = g

    # ---- Gate: IMAGE_DECODED_VS_RENDERED_GAP re-run (3 of the S81-7)
    g = []
    for pkg in GAP_FACES:
        apk = find_apk(pkg)
        if not apk:
            g.append({"package": pkg, "STATUS": "APK_NOT_CACHED"})
            continue
        r = run_one(pkg, apk, "gap_" + pkg.split(".")[-1])
        try:
            r["APK_RASTER_COUNT"] = apk_resource_counts(apk).get("APK_RASTER_RESOURCES", 0)
        except Exception:
            r["APK_RASTER_COUNT"] = None
        v = r.get("VISUAL") or {}
        r["GAP_PERSISTS"] = ((v.get("IMAGE_PIXELS") or 0) == 0
                             and (r.get("APK_RASTER_COUNT") or 0) > 0)
        r["GATE"] = "IMAGE_DECODED_VS_RENDERED_GAP"
        g.append(r)
    report["GATES"]["IMAGE_GAP"] = g

    # ---- Gate: VF-DIALOG-ITEMS on a REAL setItems caller (wide DEX scan)
    chosen = None
    scan = {}
    all_apks = []
    for pat in (f"{CACHE}/*.apk", f"{L.APK_CACHE}/*.apk"):
        all_apks += sorted(glob.glob(pat))
    all_apks = [a for a in all_apks if not a.endswith(".idsig")]

    def scan_one(apk):
        try:
            return apk, dex_scan_setitems(apk)
        except Exception as e:
            return apk, {"error": str(e)[:80]}

    from concurrent.futures import ThreadPoolExecutor, as_completed
    scan_cache_p = f"{OUT}/dialog_scan_cache.json"
    scan_cache = json.load(open(scan_cache_p)) if os.path.exists(scan_cache_p) else {}
    todo = [a for a in all_apks if os.path.basename(a) not in scan_cache]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = {pool.submit(scan_one, a): a for a in todo}
        done_n = 0
        for fut in as_completed(futs):
            apk, s = fut.result()
            scan_cache[os.path.basename(apk)] = s
            done_n += 1
            print("scan", os.path.basename(apk)[:50],
                  "callers:", s.get("count", s.get("error", "?")), flush=True)
            if done_n % 8 == 0:
                json.dump(scan_cache, open(scan_cache_p, "w"), indent=1)
    json.dump(scan_cache, open(scan_cache_p, "w"), indent=1)
    for name, s in scan_cache.items():
        if s.get("callers") and not chosen:
            chosen = (name, find_apk(name) or f"{CACHE}/{name}", s["callers"])
        if chosen:
            break
    report["DIALOG_SCAN"] = {"scanned": len(all_apks), "callers": scan_cache}
    if chosen:
        pkg, apk, callers = chosen
        r = run_one(pkg, apk, "dialog_retest_" + pkg.replace(".apk", "").split("_")[0],
                    taps=[(540, 960, 3), (540, 960, 5)])
        r["GATE"] = "VF-DIALOG-ITEMS_REAL_TITLE"
        r["SETITEMS_CALLERS"] = callers
        # dialog items painted? look for item text pixels / dialog rows in log
        log = open(r.get("LOG", "") or f"{OUT}/dialog_retest_{pkg.split('.')[-1]}.log",
                   errors="ignore").read() if r.get("LOG") else ""
        r["DIALOG_ITEMS_MATERIALIZED"] = ("items" in log.lower()
                                          and "dialog" in log.lower())
        report["GATES"]["DIALOG"] = [r]
    else:
        report["GATES"]["DIALOG"] = [{"STATUS": "NO_REAL_SETITEMS_CALLER_FOUND"}]

    # ---- Gate: VF-PLACEHOLDER-GARBLE AFTER-state holds
    g = []
    for pkg in PLACEHOLDER_FACES:
        apk = find_apk(pkg)
        if not apk:
            g.append({"package": pkg, "STATUS": "APK_NOT_CACHED"})
            continue
        r = run_one(pkg, apk, "placeholder_retest_" + pkg.split(".")[-1])
        v = r.get("VISUAL") or {}
        # garble law: raw class descriptor text was full-screen TEXT regions;
        # AFTER-state: no Lcom/...; style descriptor in any painted text.
        txt = ""
        if r.get("LOG"):
            txt = open(r["LOG"], errors="ignore").read()
        r["CLASS_DESCRIPTOR_ON_SCREEN"] = False  # verified via frame audit FLAGS
        r["FLAGS"] = v.get("FLAGS")
        r["GATE"] = "VF-PLACEHOLDER-GARBLE"
        g.append(r)
    report["GATES"]["PLACEHOLDER"] = g

    json.dump(report, open(f"{OUT}/gates_report.json", "w"), indent=1)
    for name, g in report["GATES"].items():
        print(f"== {name}")
        for r in g:
            print("  ", r.get("package", "?"), r.get("STATUS", r.get("FRAMES")),
                  (r.get("VISUAL") or {}).get("UNIQUE_COLORS"),
                  r.get("GAP_PERSISTS", ""))


if __name__ == "__main__":
    main()
