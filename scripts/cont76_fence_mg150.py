#!/usr/bin/env python3
"""cont76_fence_mg150.py — MG-150 dedicated transform hit-test fence runner
(issue #364 MG-150).

CONT-99 T2 UPDATE (F-NEW-408): the previously NAMED FRONTIER — the hit walk
consuming raw layout bounds and ignoring translation — has been CONSUMED.
AOSP View.java inverse-maps the DOWN point through the child's transform
matrix, so a view translated by (300,200) answers taps at its VISUAL rect
(400..600, 300..400) and NOT at its stale laid-out rect (100..300,
100..200). This fence now locks the AOSP law:

  GREEN (AOSP law, locked since F-NEW-408):
    - translation get/set properties hold values (readbacks 300/200);
    - tap at the STALE layout position (150,150) does NOT fire — the view
      is visually elsewhere (the old fence called this row the current law:
      it was the pre-fix hit-test blindness, now fixed);
    - tap inside the TRANSLATED visual bounds (450,350) FIRES
      (transformed hit-test == F-NEW-408; the fence recorded the old
      no-target row as the named frontier — consumed).

Remaining frontier (unchanged): rotation-about-pivot and scaled-subtree
re-transform stay the F-NEW-359 draw/hit frontier.

Exit 0 = fence GREEN (all AOSP-law rows PASS).
"""
import json
import os
import re
import sys

ROOT = "/home/z/my-project"
A_LOG = f"{ROOT}/run/cont76/mg150_a.stderr"
B_LOG = f"{ROOT}/run/cont76/mg150_b.stderr"
CHECKS = []


def check(name, ok, detail):
    CHECKS.append({"name": name, "ok": bool(ok), "detail": detail})
    print(f"  {'PASS' if ok else 'FAIL'}  {name}: {detail}")


def main():
    a = open(A_LOG, errors="replace").read()
    b = open(B_LOG, errors="replace").read()

    check("geom-properties", ("[MG150-GEOM] layout=(100,100) size=(200,100)"
                              " tx=300.000000 ty=200.000000" in a)
          and ("tx=300.000000 ty=200.000000" in b),
          "set/get translationX/Y readbacks = 300/200 (both runs)")

    check("tap-A-stale-layout-position-silent", len(re.findall(
              r"\[MG150-CLICK\]", a)) == 0,
          "tap (150,150) at the stale layout position -> NO click "
          "(AOSP inverse-maps through the translation: the view is "
          "visually at (400..600, 300..400) — the old fence locked the "
          "pre-fix blindness here; F-NEW-408 fixed the frame)")

    a_clicks = len(re.findall(r"\[MG150-CLICK\]", a))
    b_clicks = len(re.findall(r"\[MG150-CLICK\]", b))
    check("tap-B-translated-visual-bounds-hit",
          a_clicks == 0 and b_clicks == 1,
          "tap (450,350) inside the TRANSLATED visual bounds -> click "
          "(F-NEW-408 consumed the named frontier: hit-test now maps the "
          "point through the view's transform — hit == raster)")

    n_pass = sum(1 for c in CHECKS if c["ok"])
    verdict = "FENCE GREEN" if n_pass == len(CHECKS) else "FENCE RED"
    result = {"fence": "MG-150 transform hit-test",
              "probe": "com.probe.mg150",
              "apk_sha16": "6b86899e89221897",
              "checks": CHECKS, "pass": n_pass, "total": len(CHECKS),
              "verdict": verdict,
              "frontier": "CONSUMED by F-NEW-408 (CONT-99 T2): translation "
                          "hit-test mapping now AOSP-law; remaining "
                          "frontier = rotation-about-pivot + scaled-subtree "
                          "re-transform (F-NEW-359 draw frontier)"}
    os.makedirs(f"{ROOT}/evidence/cont76", exist_ok=True)
    with open(f"{ROOT}/evidence/cont76/mg150_fence.json", "w") as f:
        json.dump(result, f, indent=1)
    print(f"{verdict}: {n_pass}/{len(CHECKS)}")
    return 0 if n_pass == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
