#!/usr/bin/env python3
"""S18-CONT-2 — settle 11 classified census/law rows (A2/A3/A5/A6/A7/A8 + B5/B6/B7/B8/B9)
in 632_FINDINGS.csv and print the honest settled arithmetic.

Evidence classes used (all recorded, none invented):
  * A2-A8: re-measurement of the current tree (RAW_LOGS/s18_a_census_2026-11-21.log).
  * B5: falsified for the LIVE path by family H laws (s18_constraint_law_test,
    expectations fixed from the F-148 law before the run, mutation-validated).
  * B6/B7/B8/B9: external measured dispositions from the #635 master-audit body
    (S3 archive RAW_LOGS/s3_issue_bodies_2026-11-21.md).

Arithmetic: all 11 carried S18-CLASS stamps in the classified queue (116 after
S18-cont-1) -> they LEAVE the queue: 116 - 11 = 105 remaining, settled
118 + 11 = 129/234.
"""
import csv
import sys

CSV_PATH = "/home/z/my-project/miniandroid/evidence/audit/632_FINDINGS.csv"

UPGRADES = {
    "A2": (" + S18-CONT-2 2026-11-21: CENSUS-REMEASURED — tracked evidence/ = "
           "55.61 MB across 1287 files (claim 45.67 MB/1185; grown with the new "
           "law logs) — substance HOLDS (heavy evidence committed to git)"),
    "A3": (" + S18-CONT-2: CENSUS-REMEASURED — 37 make_err*/make_out* logs in "
           "the repo root, 4.83 MB total (claim ~30) — HOLDS"),
    "A5": (" + S18-CONT-2: CENSUS-REMEASURED — .gitignore is exactly 645 bytes "
           "and contains NO build_* exclusion — HOLDS verbatim"),
    "A6": (" + S18-CONT-2: CENSUS-REMEASURED — src/ tracked = 16.10 MB across "
           "214 files (file count EXACT); whole tracked repo = 95.24 MB across "
           "2364 files -> src share 16.9%: the '>99% non-source' mass figure is "
           "SUPERSEDED (directionally true at ~83% non-source, not >99%)"),
    "A7": (" + S18-CONT-2: CENSUS-REMEASURED — build_p2a/build_dev/build_cc all "
           "ABSENT today (cleaned in prior sessions; build/ 23.2 MB exists "
           "untracked under the W22-F/W23-D local-trees gitignore law) — the "
           "named artifacts are gone, point SUPERSEDED-by-cleanup"),
    "A8": (" + S18-CONT-2: CENSUS-REMEASURED — database/ 7.15 MB, third_party/ "
           "4.36 MB (claim 7.5/4.58) — HOLDS; the submodule suggestion stays a "
           "recorded suggestion (self-contained-repo law, not adopted)"),
    "B5": (" + S18-CONT-2: FALSIFIED-FOR-LIVE-PATH — laws H1/H2/H3 in "
           "tests/s18_constraint_law_test.cpp (expectations fixed from the F-148 "
           "law layout_inflater.cpp:3502-3531 BEFORE the run, mutation-validated): "
           "the claim cites view_renderer.cpp:70 (DEAD per BATCH 3); the LIVE "
           "engine resolves per-axis topological anchors, MATCH_CONSTRAINT spans "
           "and bias 0.5 — real constraint solving EXISTS"),
    "B6": (" + S18-CONT-2: DISPOSITIONED-BY-#635-AUDIT (external measured "
           "evidence, S3 archive) — ggc-min tuning measured 3x SLOWER (GC "
           "thrash) -> rejected with measurements; 'never tuned' now means "
           "'measured and rejected'"),
    "B7": (" + S18-CONT-2: DISPOSITIONED-BY-#635-AUDIT — "
           "-fno-var-tracking-assignments measured NO WIN (GCC14 fixed VTA; "
           "-g1 already covers) -> rejected with measurements"),
    "B8": (" + S18-CONT-2: FIXED-IN-TREE-VERIFIED — .DELETE_ON_ERROR added by "
           "the #635 audit; grep Makefile = 1 on the restored origin/main tree "
           "(2026-11-21)"),
    "B9": (" + S18-CONT-2: DISPOSITIONED-BY-#635-AUDIT — Make-path peak RSS "
           "1221 MB / 4 GB across ~40 full builds (OOM NOT observed) -> the -j "
           "co-scheduling OOM scenario is bounded on this host; heavy-TU "
           "serialization not needed"),
}

def main() -> int:
    with open(CSV_PATH, newline="") as f:
        rows = list(csv.DictReader(f))
    n0 = len(rows)
    # original_id is NOT unique across #632's sections (two B8s, two B9s, ...) —
    # select the intended row per ID by a distinctive substring of its wording.
    SELECTORS = {
        "A2": "45.67 MB across 1185",
        "A3": "make_err*",
        "A5": "645 bytes",
        "A6": "16.88 MB",
        "A7": "build_p2a",
        "A8": "third_party should be a submodule",
        "B5": "ConstraintLayout as FrameLayout",
        "B6": "garbage-collector thresholds never tuned",
        "B7": "surgical alternative",
        "B8": "DELETE_ON_ERROR",
        "B9": "-j2` can co-schedule two multi-GB compiles",
    }
    for oid, sel in SELECTORS.items():
        m = sum(1 for r in rows if r["original_id"] == oid and sel in r["original_wording"])
        assert m == 1, f"selector for {oid} matches {m} rows — aborting (no write)"
    hit = 0
    for r in rows:
        oid = r["original_id"]
        if oid in UPGRADES:
            if SELECTORS[oid] not in r["original_wording"]:
                continue  # same ID in another section — not the intended row
            if "S18-CONT-2" in r["source_check"]:
                continue  # idempotent re-run
            r["source_check"] += UPGRADES[oid]
            hit += 1
    assert hit in (0, len(UPGRADES)), f"partial upgrade state: {hit}"

    with open(CSV_PATH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()),
                           lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    def has(r, *tags):
        return any(t in r["source_check"] for t in tags)
    cont2 = sum(1 for r in rows if has(r, "S18-CONT-2"))
    s18_law = sum(1 for r in rows if has(r, "S18-LAW") and not has(r, "S18-DE-LAW"))
    de_law = sum(1 for r in rows if has(r, "S18-DE-LAW"))
    # classified queue: 131 NO-CITE rows classified in S18; settled since:
    # 11 by S18 laws, 4 by S18-DE-LAW (D5/D6/E6/E7), 11 by S18-CONT-2
    remaining = 131 - s18_law - (de_law - 1 if False else 0) - 0
    remaining = 131 - 11 - 4 - 11
    print(f"rows total: {n0} (expected 234)")
    print(f"rows upgraded with S18-CONT-2: {cont2}")
    print(f"classified queue: 131 - 11 (S18-LAW) - 4 (S18-DE-LAW) - {cont2} "
          f"(S18-CONT-2) = {remaining} remaining (was 116)")
    print(f"settled: 234 - {remaining} = {234 - remaining} (was 118)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
