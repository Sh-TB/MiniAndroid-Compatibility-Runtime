#!/usr/bin/env python3
"""cont76_fence_mg150.py — MG-150 dedicated transform hit-test fence runner
(issue #364 MG-150). Locks the CURRENT MiniAndroid hit-test semantics and
records the AOSP-delta rows as the named frontier:

  GREEN (current law, locked):
    - translation get/set properties hold values (readbacks 300/200);
    - tap inside LAYOUT bounds reaches the button (canonical pipeline).
  NAMED FRONTIER (documented deviation, measured — NOT a silent gap):
    - tap inside TRANSLATED-visual bounds only does NOT reach the button
      (AOSP View.java inverse-maps the point through the render transform;
      the engine's hit walk consumes layout bounds only — F-NEW-359 records
      the transform family as the frontier).

Exit 0 = fence GREEN (both current-law rows PASS and the deviation row is
stable evidence, not a crash).
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

    check("tap-A-layout-bounds-hit", "[MG150-CLICK] count=1" in a,
          "tap (150,150) inside layout bounds -> PerformClick fired")

    a_clicks = len(re.findall(r"\[MG150-CLICK\]", a))
    b_clicks = len(re.findall(r"\[MG150-CLICK\]", b))
    check("tap-B-translated-bounds-deviation-recorded",
          a_clicks == 1 and b_clicks == 0,
          "tap (450,350) inside translated bounds only -> NO target "
          "(current semantics locked; AOSP would map through the transform "
          "— the delta is the NAMED FRONTIER, x/y-translation consumption "
          "by hit-test + render is one coherent law)")

    n_pass = sum(1 for c in CHECKS if c["ok"])
    verdict = "FENCE GREEN" if n_pass == len(CHECKS) else "FENCE RED"
    result = {"fence": "MG-150 transform hit-test",
              "probe": "com.probe.mg150",
              "apk_sha16": "131ffbad6940c40e",
              "checks": CHECKS, "pass": n_pass, "total": len(CHECKS),
              "verdict": verdict,
              "frontier": "translation/rotation consumption by hit-test "
                          "+ render (one coherent AOSP law) — named, not "
                          "implemented this wave"}
    os.makedirs(f"{ROOT}/evidence/cont76", exist_ok=True)
    with open(f"{ROOT}/evidence/cont76/mg150_fence.json", "w") as f:
        json.dump(result, f, indent=1)
    print(f"{verdict}: {n_pass}/{len(CHECKS)}")
    return 0 if n_pass == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
