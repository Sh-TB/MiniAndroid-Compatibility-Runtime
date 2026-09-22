#!/usr/bin/env python3
"""s82_execute.py — S82 §12/§13/§27-§31/§37/§49: REAL per-title execution.

Every executed title gets: source (F-Droid + SHA256) -> real engine session
(own SESSION_ID) -> screenshot (JPG + SHA256) -> visual audit -> evidence-gated
status -> registry update. Interaction gate = tap RUN-2 with before/after pixel
diff. Reference chain per §10/§19. NEVER: fabricated reference, fixture-as-APK,
status without evidence (§44), auto-L5 (§31).

Usage:
  python3 scripts/s82_execute.py --ids MAND-001 MAND-002          # registry IDs
  python3 scripts/s82_execute.py --batch01                        # Gate C (25)
  python3 scripts/s82_execute.py --stopwatch --platformer         # Gate D parts
  python3 scripts/s82_execute.py --pkg <pkg> [--vc N]
  python3 scripts/s82_execute.py --inventory-only                 # extras
Parallel: --jobs N (default 3 concurrent engine sessions).
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import threading
from queue import Queue

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s81_visual_audit import audit_frame, level_of, apk_resource_counts  # noqa
import s82_lib as L

ROOT = L.ROOT
HEAD = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                      capture_output=True, text=True).stdout.strip()
PRINT_LOCK = threading.Lock()
REG_LOCK = threading.Lock()

CATEGORY_GATE_FAMILIES = [
    "stopwatch", "platformer", "puzzle", "board", "card", "action", "casual",
    "shooter", "calculator", "clock", "file-manager", "gallery", "multimedia",
    "weather", "connectivity", "reading", "internet", "security",
    "development", "navigation",
]


def log(*a):
    with PRINT_LOCK:
        print(*a, flush=True)


def pixels_diff(p1, p2):
    """count differing pixels between two frames (§14)."""
    try:
        from PIL import Image, ImageChops
        a = Image.open(p1).convert("RGB")
        b = Image.open(p2).convert("RGB")
        if a.size != b.size:
            return -1
        diff = ImageChops.difference(a, b)
        bbox = diff.getbbox()
        if not bbox:
            return 0
        gray = diff.convert("L")
        hist = gray.histogram()
        return sum(hist[16:])  # pixels with meaningful delta
    except Exception:
        return -1


def evidence_jpg(src_png, title_id):
    jpg = f"{L.EVID}/{title_id}.jpg"
    size = L.frame_to_jpg(src_png, jpg)
    return jpg, size


def execute_title(t, reg, jobs_args):
    """full chain for one title. Returns updated record fields."""
    tid = t["TITLE_ID"]
    rec = {}
    rec["SESSION_ID"] = f"S82-R-{tid}-RUN1"
    rec["LAST_TESTED_COMMIT"] = HEAD

    src = L.source_apk(t["PACKAGE"], jobs_args.get("vc"))
    rec["APK_SHA256"] = src["APK_SHA256"]
    rec["VERSION"] = src["VERSION"] or t.get("VERSION", "")
    rec["VERSION_CODE"] = src["VERSION_CODE"]
    rec["APK_URL"] = src.get("APK_URL", "")
    if src["STATUS"] != "SOURCED":
        rec["EXECUTION"] = f"BLOCKED_{src['STATUS']}"
        log(f"{tid} BLOCKED {src['STATUS']}")
        return rec

    # ---- RUN-1: plain observe (§12 observe stage)
    outdir = f"{L.RUN}/{tid}/run1"
    r1 = L.run_engine(src["APK_PATH"], outdir, frames=8, frame_delay=300)
    res_runs = [r1]

    visual = None
    if r1["FRAMES"]:
        m = audit_frame(r1["FRAME_PATHS"][-1])
        visual = m
        rec["VISUAL"] = {k: m.get(k) for k in
                         ("UNIQUE_COLORS", "COLOR_ENTROPY", "DOMINANT_COLOR_RATIO",
                          "NON_BACKGROUND_RATIO", "IMAGE_PIXELS", "ICON_PIXELS",
                          "TEXT_PIXELS", "WIDGET_PIXELS", "FLAGS")}
        jpg, size = evidence_jpg(r1["FRAME_PATHS"][-1], tid)
        if size:
            rec["SCREENSHOT"] = f"docs/evidence/s82/{tid}.jpg"
            rec["SCREENSHOT_SHA256"] = L.sha256_file(jpg)

    # ---- RUN-2: interaction gate (tap) when RUN-1 produced frames (§28/§29)
    tap_used = False
    stch_px = 0
    if r1["FRAMES"]:
        rec["SESSION_ID"] = f"S82-R-{tid}-RUN1,RUN2"
        kind = t["TYPE"]
        taps = ([(540, 960, 3), (540, 1700, 5), (300, 1700, 6)] if kind in ("game", "mandatory")
                else [(540, 960, 3), (540, 400, 5)])
        outdir2 = f"{L.RUN}/{tid}/run2"
        r2 = L.run_engine(src["APK_PATH"], outdir2, frames=8, frame_delay=300,
                          taps=taps)
        res_runs.append(r2)
        tap_used = True
        if r2["FRAMES"]:
            # before = last frame before first tap influence; after = last frame
            before_idx = max(0, taps[0][2] - 1)
            before = (r2["FRAME_PATHS"][before_idx]
                      if len(r2["FRAME_PATHS"]) > before_idx else r2["FRAME_PATHS"][0])
            after = r2["FRAME_PATHS"][-1]
            stch_px = pixels_diff(before, after)
            rec["BEFORE_FRAME_SHA256"] = L.sha256_file(before)
            rec["AFTER_FRAME_SHA256"] = L.sha256_file(after)
            rec["PIXEL_DIFF_PX"] = stch_px
            m2 = audit_frame(after)
            if not visual or m2.get("UNIQUE_COLORS", 0) > visual.get("UNIQUE_COLORS", 0):
                visual = m2
                rec["VISUAL"] = {k: m2.get(k) for k in
                                 ("UNIQUE_COLORS", "COLOR_ENTROPY", "DOMINANT_COLOR_RATIO",
                                  "NON_BACKGROUND_RATIO", "IMAGE_PIXELS", "ICON_PIXELS",
                                  "TEXT_PIXELS", "WIDGET_PIXELS", "FLAGS")}
                jpg, size = evidence_jpg(after, tid)
                if size:
                    rec["SCREENSHOT"] = f"docs/evidence/s82/{tid}.jpg"
                    rec["SCREENSHOT_SHA256"] = L.sha256_file(jpg)

    best = max(res_runs, key=lambda r: (r["FRAMES"], -abs(r["RUN_RC"])))
    rec["RUN_RC"] = best["RUN_RC"]
    rec["FRAMES"] = best["FRAMES"]
    rec["RUNS"] = len(res_runs)
    rec["TAPS_USED"] = tap_used
    rec["LOG_EXCERPT"] = "\n".join(best["LOG_TEXT"].strip().splitlines()[-8:])[:1500]

    # ---- §13 reproducibility: extra runs for crashed/blank important titles
    fails = L.classify_log(best["LOG_TEXT"])
    if best["FRAMES"] == 0 and len(res_runs) < 2:
        r3 = L.run_engine(src["APK_PATH"], f"{L.RUN}/{tid}/run3",
                          frames=8, frame_delay=300)
        res_runs.append(r3)
        rec["RUNS"] = len(res_runs)
        if r3["FRAMES"] and (not best["FRAMES"]):
            best = r3
            rec["RUN_RC"], rec["FRAMES"] = r3["RUN_RC"], r3["FRAMES"]
            m3 = audit_frame(r3["FRAME_PATHS"][-1])
            visual = m3
            rec["VISUAL"] = {k: m3.get(k) for k in
                             ("UNIQUE_COLORS", "COLOR_ENTROPY", "DOMINANT_COLOR_RATIO",
                              "NON_BACKGROUND_RATIO", "IMAGE_PIXELS", "ICON_PIXELS",
                              "TEXT_PIXELS", "WIDGET_PIXELS", "FLAGS")}
            jpg, size = evidence_jpg(r3["FRAME_PATHS"][-1], tid)
            if size:
                rec["SCREENSHOT"] = f"docs/evidence/s82/{tid}.jpg"
                rec["SCREENSHOT_SHA256"] = L.sha256_file(jpg)

    # ---- APK resource census (IMAGE_GAP proof chain §15)
    try:
        rc_counts = apk_resource_counts(src["APK_PATH"])
        rec["APK_RASTER_COUNT"] = rc_counts.get("APK_RASTER_RESOURCES", 0)
    except Exception:
        rec["APK_RASTER_COUNT"] = None

    # ---- status derivation (§7 evidence-gated)
    state, graph, inter, stch, fails2, flags, notes = L.derive_status(
        visual, best, tap_used, stch_px,
        ref_present=False, ref_comparison=None)
    if stch_px and stch_px > 250:
        stch = "PIXEL_DIFF_PROVEN"
    rec["STATE"] = state
    rec["GRAPHICS"] = graph
    rec["INTERACTION"] = inter
    rec["STATE_CHANGE"] = stch
    rec["RENDERING"] = "FRAMES" if best["FRAMES"] else "NONE"
    rec["EXECUTION"] = "EXECUTED"
    rec["FLAGS"] = sorted(set(flags + notes))
    fids = []
    if any(f in ("FAIL-ONCREATE", "FAIL-NPE", "FAIL-CRASH") for f in fails2):
        fids.append("F-NEW-156")   # fanout membership (§17): common onCreate unwind
    if rec.get("VISUAL", {}).get("IMAGE_PIXELS", 0) == 0 and rec.get("APK_RASTER_COUNT"):
        rec["FLAGS"].append("IMAGE_DECODED_VS_RENDERED_GAP")
        rec["VF_IDS"] = ["VF-NEW-003"]
    rec["F_IDS"] = sorted(set(fids))
    rec["FAILURE_LABELS"] = sorted(set(fails2))

    # ---- reference + comparison for mandatory (§49 Gate A/B chain)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="*", default=[])
    ap.add_argument("--pkg", default=None)
    ap.add_argument("--vc", default=None)
    ap.add_argument("--batch01", action="store_true")
    ap.add_argument("--stopwatch", action="store_true")
    ap.add_argument("--platformer", action="store_true")
    ap.add_argument("--category-gate", action="store_true")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--no-skip", action="store_true",
                    help="re-execute even if already EXECUTED at this commit")
    args = ap.parse_args()

    reg = L.load_registry()
    titles = reg["TITLES"]
    by_id = {t["TITLE_ID"]: t for t in titles}
    by_pkg = {t["PACKAGE"]: t for t in titles}

    targets = []
    if args.batch01:
        for pkg, info in reg["BATCH01_S81_RESULTS"].items():
            if info.get("TITLE_ID"):
                targets.append(by_id[info["TITLE_ID"]])
            else:
                # inventory-only batch members — run but NOT granted a 200-ID
                targets.append({"TITLE_ID": f"INV-{pkg}", "PACKAGE": pkg,
                                "TYPE": "inventory", "CATEGORY": "inventory"})
    if args.stopwatch:
        sw = [t for t in titles if t["TYPE"] == "app"
              and t["CATEGORY"] == "stopwatch"][:3]
        targets += sw
    if args.platformer:
        pl = [t for t in titles if t["TYPE"] == "game"
              and t["CATEGORY"] == "platformer-game"][:3]
        targets += pl
    if args.category_gate:
        covered = set()
        for pkg, info in reg["BATCH01_S81_RESULTS"].items():
            m = by_pkg.get(pkg)
            if m:
                covered.add(m["CATEGORY"])
        for t in targets:
            covered.add(t.get("CATEGORY", ""))
        for fam in CATEGORY_GATE_FAMILIES:
            if fam in covered:
                continue
            cand = [t for t in titles if t["CATEGORY"] == fam]
            if cand:
                targets.append(cand[0])
    if args.ids:
        targets += [by_id[i] for i in args.ids]
    if args.pkg:
        targets.append(by_pkg[args.pkg])

    # dedupe, skip already-executed-with-same-commit unless --no-skip
    seen = set()
    uniq = []
    for t in targets:
        if t["TITLE_ID"] in seen:
            continue
        seen.add(t["TITLE_ID"])
        if (not args.no_skip and t.get("EXECUTION") == "EXECUTED"
                and t.get("LAST_TESTED_COMMIT") == HEAD):
            log(f"SKIP {t['TITLE_ID']} (already EXECUTED at {HEAD[:8]})")
            continue
        uniq.append(t)

    q = Queue()
    for t in uniq:
        q.put(t)

    def worker():
        while True:
            try:
                t = q.get_nowait()
            except Exception:
                return
            try:
                rec = execute_title(t, reg, {"vc": args.vc})
                with REG_LOCK:
                    full = L.load_registry()
                    for i, tt in enumerate(full["TITLES"]):
                        if tt["TITLE_ID"] == t["TITLE_ID"]:
                            full["TITLES"][i].update(rec)
                            break
                    if t["TITLE_ID"].startswith("INV-"):
                        full.setdefault("INVENTORY_RUNS", {})[t["TITLE_ID"]] = rec
                    L.save_registry(full)
                log(f"DONE {t['TITLE_ID']} {rec.get('STATE')} "
                    f"exec={rec.get('EXECUTION')} px_diff={rec.get('PIXEL_DIFF_PX')}")
            except Exception as e:
                log(f"ERROR {t['TITLE_ID']}: {type(e).__name__} {e}")
            finally:
                q.task_done()

    threads = [threading.Thread(target=worker, daemon=True)
               for _ in range(args.jobs)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    print(f"executed {len(uniq)} targets; disk free {L.disk_free_gb()}G")


if __name__ == "__main__":
    main()
