#!/usr/bin/env python3
"""s82_dialog_gate.py — S82 §49: VF-DIALOG-ITEMS retest on a REAL title that
actually calls AlertDialog$Builder.setItems (DEX-scan proven, not a fixture).
Resumable: scan cache at run/s82/cached_gates/dialog_scan_cache.json."""
import glob
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s81_visual_audit import audit_frame  # noqa
import s82_lib as L  # noqa

CACHE = "/tmp/my-project/apk_cache"
OUT = f"{L.RUN}/cached_gates"
os.makedirs(OUT, exist_ok=True)


def dex_scan_setitems(apk):
    """scan BOTH framework and appcompat builders; items-family methods:
    setItems / setSingleChoiceItems / setMultiChoiceItems / setCursor.
    Returns callers keyed by method so the retest is precisely attributable."""
    from androguard.misc import AnalyzeAPK
    try:
        a, d_, dx = AnalyzeAPK(apk)
    except Exception as e:
        return {"error": str(e)[:120]}
    found = {}
    targets = [
        ("Landroid/app/AlertDialog$Builder;",
         ("setItems", "setSingleChoiceItems", "setMultiChoiceItems", "setCursor")),
        ("Landroidx/appcompat/app/AlertDialog$Builder;",
         ("setItems", "setSingleChoiceItems", "setMultiChoiceItems")),
    ]
    for cls, methods in targets:
        for meth in methods:
            for m in dx.find_methods(classname=cls, methodname=meth):
                for _, call, _ in m.get_xref_from():
                    try:
                        c = call.get_class_name()
                    except Exception:
                        continue
                    if c:
                        found.setdefault(meth, []).append(c)
    if not found:
        return {"callers": [], "count": 0}
    flat = sorted({c for cs in found.values() for c in cs})
    return {"callers": flat, "count": len(flat), "methods": found}


def run_dialog_session(apk, label, taps=((540, 960, 3), (540, 960, 5))):
    r = L.run_engine(apk, f"{OUT}/{label}", frames=10, frame_delay=300,
                     taps=list(taps))
    res = {"APK": apk, "APK_SHA256": L.sha256_file(apk), "RUN_RC": r["RUN_RC"],
           "FRAMES": r["FRAMES"], "SESSION": f"S82-CACHED-{label}",
           "TAPS": list(taps)}
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
        # dialog detection: compare pre-tap vs post-tap frames (§14)
        from PIL import ImageChops, Image
        try:
            a = Image.open(r["FRAME_PATHS"][2]).convert("RGB")
            b = Image.open(r["FRAME_PATHS"][-1]).convert("RGB")
            d = ImageChops.difference(a, b).convert("L")
            res["PIXEL_DIFF_TAP"] = sum(d.histogram()[16:])
        except Exception:
            res["PIXEL_DIFF_TAP"] = -1
    crash = f"{OUT}/{label}/crash.log"
    if os.path.exists(crash):
        txt = open(crash, errors="ignore").read()
        res["TOP_ESCAPES"] = [ln for ln in txt.splitlines()
                              if "EXC-UNCAUGHT-TOP" in ln][:3]
    return res


def main():
    report_p = f"{OUT}/gates_report.json"
    report = json.load(open(report_p)) if os.path.exists(report_p) else \
        {"GENERATED_AT": L.now(), "GATES": {}}
    report.setdefault("GATES", {})
    scan_cache_p = f"{OUT}/dialog_scan_cache.json"
    cache = json.load(open(scan_cache_p)) if os.path.exists(scan_cache_p) else {}

    apks = []
    for pat in (f"{CACHE}/*.apk", f"{L.APK_CACHE}/*.apk"):
        apks += sorted(glob.glob(pat))
    apks = [a for a in apks if not a.endswith(".idsig")]
    todo = [a for a in apks if os.path.basename(a) not in cache]
    print(f"scan: {len(apks)} apks, {len(todo)} todo")

    def scan_one(a):
        try:
            return a, dex_scan_setitems(a)
        except Exception as e:
            return a, {"error": str(e)[:80]}

    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = {pool.submit(scan_one, a): a for a in todo}
        n = 0
        for fut in as_completed(futs):
            a, s = fut.result()
            cache[os.path.basename(a)] = s
            n += 1
            print("scan", os.path.basename(a)[:48],
                  "->", s.get("count", s.get("error", "?")), flush=True)
            if n % 10 == 0:
                json.dump(cache, open(scan_cache_p, "w"), indent=1)
    json.dump(cache, open(scan_cache_p, "w"), indent=1)

    callers = {k: v for k, v in cache.items() if v.get("callers")}
    # prefer framework android.app.AlertDialog$Builder.setItems callers
    fw = {k: v for k, v in callers.items()
          if any(m == "setItems" for m in (v.get("methods") or {}))}
    pool_pick = fw or callers
    report["DIALOG_SCAN"] = {"scanned": len(apks), "callers": callers,
                             "framework_setitems": sorted(fw)}
    print("real items-callers:", len(callers), "framework setItems:", len(fw))

    if pool_pick and not report["GATES"].get("DIALOG"):
        name = sorted(pool_pick)[0]
        apk = f"{CACHE}/{name}"
        if not os.path.exists(apk):
            apk = f"{L.APK_CACHE}/{name}"
        label = "dialog_retest_" + name.replace(".apk", "").split("_")[0]
        r = run_dialog_session(apk, label)
        r["GATE"] = "VF-DIALOG-ITEMS_REAL_TITLE"
        r["SETITEMS_CALLERS"] = callers[name]["callers"]
        report["GATES"]["DIALOG"] = [r]
        print("dialog retest:", name, r.get("FRAMES"), r.get("PIXEL_DIFF_TAP"))
    elif report["GATES"].get("DIALOG"):
        print("dialog retest already recorded")
    else:
        report["GATES"]["DIALOG"] = [{"STATUS": "NO_REAL_SETITEMS_CALLER_FOUND"}]
        print("NO setItems caller in", len(apks), "APKs")

    json.dump(report, open(report_p, "w"), indent=1)


if __name__ == "__main__":
    main()
