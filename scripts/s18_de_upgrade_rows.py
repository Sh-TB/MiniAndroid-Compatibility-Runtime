#!/usr/bin/env python3
"""S18 D/E law families — upgrade the 5 law-verified rows in 632_FINDINGS.csv
(D4/D5/D6/E6/E7) and print the honest settled arithmetic.

Arithmetic (matches the S18-corrected convention — no double-counting):
  * D4/D5/D6 already carried S16-CHECK marks (inside the 103 machine-checked
    rows) -> their verdicts upgrade IN PLACE (PARTIAL -> LAW-PINNED); the
    settled count does NOT grow for them again.
  * E6/E7 were S18-CLASS rows (inside the classified 131-queue) -> law
    verification settles them: classified-remaining 120 -> 118, settled
    114 -> 116.
"""
import csv
import sys

CSV_PATH = "/home/z/my-project/miniandroid/evidence/audit/632_FINDINGS.csv"

UPGRADES = {
    "D4": (" + S18-DE-LAW 2026-11-21: LAW-PINNED (was S16 PARTIAL) — STRING "
           "start/end decode drops the 0x00800000 relative flag "
           "(gravity_bits, layout_inflater.cpp:105-107) so the RTL flip law "
           "(:5022-5028) never fires for XML-declared start; INT "
           "0x00800003 DOES flip under RTL (laws D3/D4 in "
           "tests/s18_gravity_direction_laws_test.cpp, mutation-validated)"),
    "D5": (" + S18-DE-LAW 2026-11-21: LAW-PINNED (was S16 PARTIAL claim) — "
           "FILL_VERTICAL/FILL_HORIZONTAL decode to 0x70/0x7 but NO stretch "
           "branch exists on either cross axis (:4853-4883/:5006-5034): "
           "child keeps its own size, top/left-aligned (laws D1/D2; AOSP "
           "expects the child to stretch to the container)"),
    "D6": (" + S18-DE-LAW 2026-11-21: LAW-PINNED (was S18-CLASS census) — "
           "DISPLAY_CLIP_VERTICAL|HORIZONTAL (0x11000000) placement-identical "
           "to a no-gravity control child (law D5)"),
    "E6": (" + S18-DE-LAW 2026-11-21: LAW-PINNED (was S18-CLASS census) — no "
           "baseline branch in the horizontal cross-axis law: 30px/60px "
           "children both top-aligned at 0 (law E1 in "
           "tests/s18_linear_extras_laws_test.cpp; AOSP baselineAligned "
           "default would offset the 30px child)"),
    "E7": (" + S18-DE-LAW 2026-11-21: LAW-PINNED (was S18-CLASS census) — "
           "showDividers matches no decode case: silent vanish (inflate "
           "warnings EMPTY, S17 A1 law) and placement identical to the "
           "no-divider control on both axes (laws E2/E3; AOSP inserts "
           "divider drawable sizes)"),
}

def main() -> int:
    with open(CSV_PATH, newline="") as f:
        rows = list(csv.DictReader(f))
    n0 = len(rows)
    hit = 0
    for r in rows:
        oid = r["original_id"]
        if oid in UPGRADES:
            if "S18-DE-LAW" in r["source_check"]:
                continue  # idempotent re-run
            r["source_check"] += UPGRADES[oid]
            hit += 1
    assert hit in (0, len(UPGRADES)), f"partial upgrade state: {hit}"

    with open(CSV_PATH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()),
                           lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    # honest arithmetic — OFFICIAL ledger convention (S18-corrected):
    # the classified queue held 131 NO-CITE rows; S18 settled 11 of them
    # (S18-LAW marks, committed), this session settles 2 more (E6/E7) and
    # upgrades 3 already-marked rows IN PLACE (D4/D5/D6 carried S16-CHECK
    # PARTIAL marks inside the 103 machine-checked rows — no recount).
    def has(r, *tags):
        return any(t in r["source_check"] for t in tags)
    de_law = sum(1 for r in rows if has(r, "S18-DE-LAW"))
    s18_law = sum(1 for r in rows if has(r, "S18-LAW") and not has(r, "S18-DE-LAW"))
    de_from_class = sum(1 for r in rows
                        if has(r, "S18-DE-LAW") and has(r, "S18-CLASS"))
    de_upgraded_in_place = sum(1 for r in rows
                               if has(r, "S18-DE-LAW")
                               and not has(r, "S18-CLASS"))
    classified_remaining = 131 - s18_law - de_from_class
    print(f"rows total: {n0} (expected 234)")
    print(f"S18-DE-LAW rows: {de_law} total = {de_from_class} newly settled "
          f"(D5/D6/E6/E7 — carried S18-CLASS stamps) + "
          f"{de_upgraded_in_place} upgraded in place (D4 — carried an "
          f"S16-CHECK mark inside the 103 machine-checked rows)")
    print(f"prior S18-LAW settled rows (unchanged): {s18_law}")
    print(f"classified queue: 131 - {s18_law} - {de_from_class} = "
          f"{classified_remaining} remaining (S18 recorded 120)")
    print(f"settled: 234 - {classified_remaining} = {234 - classified_remaining}"
          f" (S18 recorded 114)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
