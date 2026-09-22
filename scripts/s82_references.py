#!/usr/bin/env python3
"""s82_references.py — §10: official F-Droid reference screenshots with
provenance (URL + SHA256) for MAND + executed titles. Then §19/§30 structured
REFERENCE-vs-MINIANDROID comparison for executed titles (palette level).
Resumable; no fabricated references ever."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s82_lib as L  # noqa


def main():
    reg = L.load_registry()
    by_id = {t["TITLE_ID"]: t for t in reg["TITLES"]}
    targets = [t for t in reg["TITLES"]
               if t["TYPE"] == "mandatory" or t.get("EXECUTION") == "EXECUTED"]
    done = 0
    for t in targets:
        ref = t.get("REFERENCE") or {}
        if ref.get("STATUS") == "OK" and ref.get("SHA256"):
            done += 1
            continue
        url = t.get("REFERENCE_SCREENSHOT_URL", "")
        r = L.get_reference(t["PACKAGE"], mandatory_url=url)
        t["REFERENCE"] = r
        done += 1
        print(t["TITLE_ID"], t["PACKAGE"], "->", r["STATUS"], r["URL"][:70], flush=True)
        L.save_registry(reg)
    L.save_registry(reg)
    ok = sum(1 for t in targets if t["REFERENCE"].get("STATUS") == "OK")
    print(f"references OK {ok}/{len(targets)}")

    # §19/§30 structured comparisons for executed titles with both images
    n = 0
    for t in targets:
        if t.get("EXECUTION") != "EXECUTED" or t["TYPE"] == "mandatory":
            if not (t["TYPE"] == "mandatory" and t.get("EXECUTION") == "EXECUTED"):
                continue
        ref = t.get("REFERENCE") or {}
        shot = t.get("SCREENSHOT")
        if ref.get("STATUS") != "OK" or not shot:
            continue
        ref_png = ref["PATH"]
        ma_png = f"{L.RUN}/{t['TITLE_ID']}/run1/frames/frame_007.png"
        if not os.path.exists(ma_png):
            cands = sorted(__import__("glob").glob(f"{L.RUN}/{t['TITLE_ID']}/*/frames/frame_*.png"))
            if not cands:
                continue
            ma_png = cands[-1]
        cmp_ = L.compare_reference(ref_png, ma_png)
        t["COMPARISON"] = cmp_
        if cmp_.get("STATUS") == "VISUAL_FAIL":
            t["VISUAL_CORRELATION"] = "VISUAL_FAIL_PALETTE"
        elif cmp_.get("LEVEL", 0) >= 3:
            t["VISUAL_CORRELATION"] = "STRUCTURAL_CANDIDATE"
        elif cmp_.get("LEVEL", 0) >= 1:
            t["VISUAL_CORRELATION"] = "PARTIAL_PALETTE"
        n += 1
        print("cmp", t["TITLE_ID"], cmp_.get("STATUS"), "lvl", cmp_.get("LEVEL"), flush=True)
    L.save_registry(reg)
    print("comparisons:", n)


if __name__ == "__main__":
    main()
