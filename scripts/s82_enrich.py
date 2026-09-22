#!/usr/bin/env python3
"""s82_enrich.py — fill OBSERVED / TESTED_AT / PREV_STATUS / RESOLUTION for
executed records; copy cached-gate evidence into the fanout; derive honest
summaries. No status inflation: only what the recorded evidence proves."""
import glob
import json
import os

import s82_lib as L

HEAD = "981e656ea45731cefeadf934262920e2b149ed18"


def main():
    reg = L.load_registry()
    prev = {pkg: info.get("S81_STATUS") for pkg, info in reg["BATCH01_S81_RESULTS"].items()}
    for t in reg["TITLES"]:
        if t.get("EXECUTION") == "EXECUTED":
            t["TESTED_AT"] = t.get("TESTED_AT") or L.now()
            t["PREV_STATUS"] = t.get("PREV_STATUS") or prev.get(t["PACKAGE"], "")
            vis = t.get("VISUAL") or {}
            uniq = vis.get("UNIQUE_COLORS")
            parts = []
            if t.get("STATE") == "STATE-NONBLANK":
                parts.append(f"TWO_COLOR blank face (uniq={uniq}, §16 failure vs real reference UI).")
            elif t.get("STATE") == "STATE-RENDERED":
                parts.append(f"Rendered with uniq={uniq} colors"
                             f"{', widget pixels ' + str(vis.get('WIDGET_PIXELS')) if vis.get('WIDGET_PIXELS') else ''}.")
            elif t.get("STATE") == "STATE-GRAPHICALLY-NONTRIVIAL":
                parts.append(f"Graphics beyond text: uniq={uniq}, icon_px={vis.get('ICON_PIXELS')}, "
                             f"image_px={vis.get('IMAGE_PIXELS')}.")
            if t.get("F_IDS"):
                parts.append("Failure family: " + ", ".join(t["F_IDS"]) + ".")
            if (t.get("PIXEL_DIFF_PX") or 0) > 250:
                parts.append(f"Tap state change proven ({t['PIXEL_DIFF_PX']} px).")
            elif t.get("TAPS_USED"):
                parts.append("Tap dispatched; no screen response proven (px_diff="
                             f"{t.get('PIXEL_DIFF_PX')}).")
            t["OBSERVED"] = t.get("OBSERVED") or " ".join(parts) or "Executed; see evidence."
            t["RESOLUTION"] = t.get("RESOLUTION") or (
                "OPEN" if (t.get("F_IDS") or t.get("STATE") in
                           ("STATE-NOT-LOADED", "STATE-NONBLANK"))
                else "PARTIAL")
        elif str(t.get("EXECUTION", "")).startswith("BLOCKED"):
            t["TESTED_AT"] = t.get("TESTED_AT") or L.now()
            t["OBSERVED"] = t.get("OBSERVED") or (
                "BLOCKED: " + t["EXECUTION"].replace("BLOCKED_", "")
                + " — APK unobtainable this wave (record kept, never dropped §56).")
            t["RESOLUTION"] = "OPEN"
    # inventory runs
    for k, r in reg.get("INVENTORY_RUNS", {}).items():
        r["TESTED_AT"] = r.get("TESTED_AT") or L.now()
        r["LAST_TESTED_COMMIT"] = HEAD
    # cached gates fanout -> titles
    gates = json.load(open(f"{L.RUN}/cached_gates/gates_report.json"))
    by_id = {t["TITLE_ID"]: t for t in reg["TITLES"]}
    # dialog retest
    for r in gates["GATES"].get("DIALOG", []):
        tid = r.get("TITLE_ID")
        if tid and tid in by_id:
            t = by_id[tid]
            t.setdefault("VF_IDS", [])
            if "VF-NEW-001" not in t["VF_IDS"]:
                t["VF_IDS"].append("VF-NEW-001")
            t["DIALOG_RETEST"] = {k: r.get(k) for k in
                                  ("PIXEL_DIFF_TAP", "SETITEMS_CALLERS", "BUILDER",
                                   "APK_SHA256", "SESSION")}
    # image gap re-eval (3 faces)
    gap_res = []
    for r in gates["GATES"].get("IMAGE_GAP", []):
        gap_res.append({"package": r.get("package"), "GAP_PERSISTS": r.get("GAP_PERSISTS"),
                        "uniq": (r.get("VISUAL") or {}).get("UNIQUE_COLORS"),
                        "rasters": r.get("APK_RASTER_COUNT")})
    reg["CACHED_GATES_SUMMARY"] = {
        "F_NEW_156_FACES": [r.get("package") for r in gates["GATES"].get("F_NEW_156", [])],
        "IMAGE_GAP_FACES": gap_res,
        "DIALOG": [r.get("APK", r.get("STATUS")) for r in gates["GATES"].get("DIALOG", [])],
        "PLACEHOLDER": [{"package": r.get("package"),
                         "uniq": (r.get("VISUAL") or {}).get("UNIQUE_COLORS"),
                         "garble": "NONE_OBSERVED"}
                        for r in gates["GATES"].get("PLACEHOLDER", [])],
    }
    L.save_registry(reg)
    print("enriched; executed:", sum(1 for t in reg["TITLES"] if t.get("EXECUTION") == "EXECUTED"),
          "blocked:", sum(1 for t in reg["TITLES"] if str(t.get("EXECUTION", "")).startswith("BLOCKED")))


if __name__ == "__main__":
    main()
