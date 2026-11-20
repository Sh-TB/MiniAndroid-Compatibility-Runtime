#!/usr/bin/env python3
"""S18-2: row-level classification of every row still marked NO-CITE (131 rows —
the S17 commit's '120 remaining' double-counted 11 rows that were already
S16-marked before S17 upgraded them; honest unmarked count = 131, corrected in
this ledger pass; settled rows = 103/234 machine-marked).

Every row keeps its ID and all prior columns; source_check 'NO-CITE' becomes
'S18-CLASS 2026-11-20: <CATEGORY> — <note>' (provenance preserved in-row).

Categories (mission S18-2):
TESTABLE-NO-APK            deterministic repo/code census or hand-built-node law
TESTABLE-WITH-NEW-FIXTURE  synthetic fixture creatable locally (font/PNG/mini-DEX)
NEEDS-FONT-FIXTURE         app-specific font required
NEEDS-IMAGE-FIXTURE        app goldens / nine-patch / real image assets
NEEDS-EXTERNAL-ORACLE      Robolectric/AOSP/upstream diff needed
NEEDS-MISSING-APK          tied to the missing original APKs (#597/#618/#623)
NEEDS-MISSING-CODER-ARTIFACT
DUPLICATE                  claim explicitly subsumed by another row
ALREADY-RESOLVED           covered by existing tests/evidence (retracted or pinned)
UNVERIFIABLE               process suggestion / plan / perf-without-oracle / retracted / external-service state
"""
import csv, sys

FIND = "/home/z/my-project/miniandroid/evidence/audit/632_FINDINGS.csv"

C = {
# ── repo-hygiene censuses (du/wc/grep — deterministic, no APK) ──────────────
"632-A2":  ("TESTABLE-NO-APK", "du census: evidence/ size+file count vs claim 45.67MB/1185"),
"632-A3":  ("TESTABLE-NO-APK", "ls census: make_*.txt logs in repo root vs claim ~30"),
"632-A5":  ("TESTABLE-NO-APK", "wc -c .gitignore + grep build_*/ exclusion vs claim 645B/no exclude"),
"632-A6":  ("TESTABLE-NO-APK", "du census: src/ mass vs repo total vs claim 16.88MB/>99%"),
"632-A7":  ("TESTABLE-NO-APK", "du census: build_p2a/build_dev sizes vs claim 34.71/32.87MB"),
"632-A8":  ("TESTABLE-NO-APK", "du census: database/ + third_party/ sizes vs claim 7.5/4.58MB"),
"632-B8":  ("TESTABLE-NO-APK", "grep census: app class names in framework src vs cited lines"),
"632-B9":  ("TESTABLE-NO-APK", "grep census: MINIANDROID_*_DIAG env vars count"),
"632-BP-6":("TESTABLE-NO-APK", "Makefile census: no GC threshold flags (GCcminsize etc.)"),
"632-BP-7":("TESTABLE-NO-APK", "Makefile census: -fno-var-tracking-assignments absent"),
"632-BP-8":("TESTABLE-NO-APK", "Makefile census: no .DELETE_ON_ERROR"),
"632-BP-9":("TESTABLE-NO-APK", "Makefile census: no -j serialization for heavy TUs"),
"632-NEW-10":("TESTABLE-NO-APK","CMake census: if(EXISTS) dead-target guards"),
"632-NEW-8":("TESTABLE-NO-APK","wc census: largest TU vs claim 5.15MB"),
"632-NEW-9":("TESTABLE-NO-APK","CMake census: duplicate add_executable(miniandroid_test)"),
"632-REUSE-TOTAL":("TESTABLE-NO-APK","du census: hand-written vs upstream-provided mass"),
# ── code-shape censuses (lint/structural facts) ─────────────────────────────
"632-C10":("TESTABLE-NO-APK","code census: entries container element type at cited site"),
"632-C7": ("TESTABLE-NO-APK","code census: stats_.laid_out++ inside measure_view"),
"632-C8": ("TESTABLE-NO-APK","code census: WRAP_CONTENT sentinels -2 and INT_MIN"),
"632-C9": ("TESTABLE-NO-APK","code census: magic-number inventory (-1/-2/INT_MIN/8/0x3FFFFFFF)"),
"632-E4": ("TESTABLE-NO-APK","code census: dead `unit` local at cited site"),
"632-E5": ("TESTABLE-NO-APK","code census: cursor_pre scaffolding at cited site"),
"632-E7": ("TESTABLE-NO-APK","census+law: showDividers/dividerPadding handler absence"),
"632-F3": ("TESTABLE-NO-APK","code census: identical ternary arms at cited site (+ spacing law in family)"),
"632-F6": ("TESTABLE-NO-APK","code census: declared-simplification comment at cited site"),
"632-H3": ("TESTABLE-NO-APK","code census: no GridLayout.Spec data model (s247 G2 pins the axis-count law instead)"),
"632-J10":("TESTABLE-NO-APK","census+law: adjustViewBounds handler absent (decode+measure pin)"),
"632-J11":("TESTABLE-NO-APK","census+law: tint/ColorFilter/setImageAlpha handler absence"),
"632-J6": ("TESTABLE-NO-APK","code census: bitmap_cache_ keyed by path, no eviction"),
"632-NEW-2":("TESTABLE-NO-APK","code census: tautological condition in weight path"),
"632-NEW-26":("TESTABLE-NO-APK","code census: phantom-NUL residual allocation in string pool sizing"),
"632-NEW-32":("TESTABLE-NO-APK","code census: density-scale logic duplicated measure vs draw"),
"632-NEW-39":("TESTABLE-NO-APK","census: LL attr family handlers absent"),
"632-NEW-41":("TESTABLE-NO-APK","census: ImageView attr family handlers absent"),
"632-NEW-42":("TESTABLE-NO-APK","census: CL attr family handlers absent"),
"632-NEW-43":("TESTABLE-NO-APK","census: fitsSystemWindows handler absent"),
"632-NEW-44":("TESTABLE-NO-APK","census: FL tint/foreground attr family absent"),
"632-NEW-45":("TESTABLE-NO-APK","census: AbsListView/GridView 10 attrs absent"),
"632-NEW-46":("TESTABLE-NO-APK","census: focus/a11y ~30 attrs absent"),
"632-NEW-47":("TESTABLE-NO-APK","census: ViewGroup animation/flags absent"),
"632-Q4": ("TESTABLE-NO-APK","code census: extract_entry_cached no LRU cap"),
"632-R3": ("TESTABLE-NO-APK","census: dead locals present; CI -Werror absent"),
"632-R4": ("TESTABLE-NO-APK","census: identical ternary (same site as F3)"),
"632-R5": ("TESTABLE-NO-APK","census: CI lint config absent"),
"632-P2": ("TESTABLE-NO-APK","code census: ungated std::cerr at cited site"),
"632-SWEEP-S2":("TESTABLE-NO-APK","census: attr-handler sweep count (S16 NEW-33 work covers the mechanism)"),
"632-O3": ("UNVERIFIABLE","retracted-by-author (RETR); per-pixel counter shape still grep-able, no live claim"),
# ── behavioral laws, hand-built nodes / direct API (no fixtures) ────────────
"632-B5": ("TESTABLE-NO-APK","law candidate: CL classification + measure path (s247 G6 already pins the real solver; pin classify+fallback)"),
"632-C6": ("TESTABLE-NO-APK","law candidate: renderer root padding -> root box"),
"632-C11":("TESTABLE-NO-APK","law candidate: measure hook counts re-measures (set_custom_view_measure_hook)"),
"632-D5": ("TESTABLE-NO-APK","law candidate: FILL_VERTICAL/HORIZONTAL gravity at the live engine — S18 family G"),
"632-D6": ("TESTABLE-NO-APK","law+census: DISPLAY_CLIP_* ignored — S18 family G"),
"632-E6": ("TESTABLE-NO-APK","law candidate: baselineAligned horizontal LL — font-metric dependent"),
"632-F4": ("TESTABLE-NO-APK","law candidate: grid child margins ignored — S18 family"),
"632-F5": ("TESTABLE-NO-APK","law candidate: stretchSpacing cols+1 uniform vs AOSP inner-gap law"),
"632-G5": ("TESTABLE-NO-APK","census+law: alignBaseline absent"),
"632-G6": ("TESTABLE-NO-APK","law candidate: cyclic relative refs terminate (depth cap; no AOSP-style explicit error)"),
"632-I4": ("TESTABLE-NO-APK","law candidate: fillViewport dropped — decode+measure pin"),
"632-J2": ("TESTABLE-NO-APK","law candidate: nearest-neighbour sampling observable via in-memory bitmap draw"),
"632-J4": ("TESTABLE-NO-APK","law candidate: path-density buckets incl -nodpi/-tvdpi (temp dirs, no APK)"),
"632-K5": ("TESTABLE-NO-APK","law candidate: pathData verbs via vector_inflater (hand-built strings)"),
"632-M3": ("TESTABLE-NO-APK","law candidate: rounding nonzero-floor law — direct res_id API — S18 family"),
"632-N3": ("TESTABLE-NO-APK","census+law: lineSpacing attrs dropped"),
"632-N4": ("TESTABLE-NO-APK","law candidate: ellipsize/maxLines behavior pins"),
"632-NEW-11":("TESTABLE-NO-APK","retracted, but the S18 gravity law settles the live-engine half (D5/D6 family)"),
"632-NEW-12":("TESTABLE-NO-APK","retracted; scaleType draw-path law (family with J2/NEW-14/NEW-17)"),
"632-NEW-14":("TESTABLE-NO-APK","law candidate: CENTER/CENTER_CROP rect math observable"),
"632-NEW-16":("TESTABLE-NO-APK","law candidate: measure-depth cap terminates deep chains"),
"632-NEW-17":("TESTABLE-NO-APK","law candidate: MATRIX scaleType ignores matrix"),
"632-NEW-28":("TESTABLE-NO-APK","law candidate: config->qualifier roundtrip via res_config"),
"632-NEW-30":("TESTABLE-NO-APK","law candidate: clipChildren no draw-stage enforcement — pixel law"),
"632-NEW-5": ("TESTABLE-NO-APK","law candidate: createScaledBitmap(filter=true) nearest-neighbour pixels"),
"632-NEW-40":("TESTABLE-NO-APK","law candidate: fillViewport dropped (family with I4)"),
"632-NEW-48":("TESTABLE-NO-APK","census+law: measureAllChildren/ignoreGravity/alignBaseline dropped"),
"632-O4": ("TESTABLE-NO-APK","law candidate: framebuffer init color = WHITE pixel observable"),
"632-O5": ("TESTABLE-NO-APK","law+census: get_pixels_mut bypasses blending"),
"632-O8": ("TESTABLE-NO-APK","census+law: elevation/Z ordering absent"),
"632-O9": ("TESTABLE-NO-APK","census+law: PorterDuff beyond SRC_OVER/CLEAR absent"),
"632-P6": ("TESTABLE-NO-APK","law candidate: invalidate() full-surface not dirty-rect"),
"632-P7": ("TESTABLE-NO-APK","law candidate: ViewStub.inflate / <merge> current path"),
"632-SQL-4":("TESTABLE-NO-APK","law candidate: BLOB cell via shadow exec (s248 harness)"),
"632-SQL-5":("TESTABLE-NO-APK","law candidate: CursorFactory accepted+ignored"),
"632-SQL-6":("TESTABLE-NO-APK","law candidate: WAL set, pool absent (PRAGMA introspection)"),
"632-SQL-7":("TESTABLE-NO-APK","census: sqlite3_busy_timeout absent"),
"632-SQL-8":("TESTABLE-NO-APK","census: insert not in implemented_methods()"),
# ── fixtures creatable locally ──────────────────────────────────────────────
"632-N2": ("TESTABLE-WITH-NEW-FIXTURE","font metrics law with a system TTF (Noto/Liberation present) — S18 family"),
"632-NEW-24":("TESTABLE-WITH-NEW-FIXTURE","metrics fallback law: real TTF vs missing font deterministic fallback"),
"632-P8": ("TESTABLE-WITH-NEW-FIXTURE","mini-DEX onMeasure fixture (gp_dex003-style harness)"),
# ── app-specific fixtures ───────────────────────────────────────────────────
"632-N8": ("NEEDS-IMAGE-FIXTURE","nine-patch Button insets + Material 88x48 dims need real .9.png/app assets"),
# ── external oracle needed ──────────────────────────────────────────────────
"632-M4": ("NEEDS-EXTERNAL-ORACLE","Configuration lifecycle propagation parity needs AOSP/Robolectric oracle"),
"632-N5": ("NEEDS-EXTERNAL-ORACLE","Minikin line-breaking parity (breakStrategy/hyphenationFrequency)"),
"632-NEW-23":("NEEDS-EXTERNAL-ORACLE","first-strong vs locale textDirection parity needs AOSP oracle"),
"632-P5": ("NEEDS-EXTERNAL-ORACLE","onAttachedToWindow/ViewTreeObserver/post ordering vs AOSP traversal"),
# ── duplicates (explicit cross-refs in the claim text) ──────────────────────
"632-Q1": ("DUPLICATE","claims 'see O2' verbatim"),
"632-Q2": ("DUPLICATE","claims 'see J12' verbatim"),
"632-Q3": ("DUPLICATE","claims 'see J6' verbatim"),
"632-Q5": ("DUPLICATE","claims 'see C11' verbatim"),
"632-Q6": ("DUPLICATE","claims 'see B3' verbatim"),
"632-Q7": ("DUPLICATE","claims 'see C7' verbatim"),
# ── already resolved by existing tests/evidence ─────────────────────────────
"632-E2": ("ALREADY-RESOLVED","retracted, and weightSum IS read in-tree (inflater.cpp:1672 handler; weight_sum_valid consumed :4930) — S18 weightSum law pins it"),
"632-E8": ("ALREADY-RESOLVED","retracted; S17 W1 laws pin the EXACTLY re-measure (inflater.cpp:4819-4826)"),
"632-H1": ("ALREADY-RESOLVED","retracted; s247 G1-G3 pins the real GridLayout engine (span-track cells, axis counts)"),
"632-NEW-3":("ALREADY-RESOLVED","S17 W1/W1.b laws pin milli-unit weight semantics (layout_weight=1000 == 1.0)"),
# ── unverifiable: plans, process, perf, external state ──────────────────────
"632-C5": ("UNVERIFIABLE","retracted-by-author (RETR); window_insets_shadow.cpp exists as partial counter-evidence, no live claim"),
"632-I3": ("UNVERIFIABLE","retracted-by-author (RETR)"),
"632-I5": ("UNVERIFIABLE","retracted-by-author (RETR)"),
"632-J3": ("UNVERIFIABLE","retracted-by-author (RETR)"),
"632-J5": ("UNVERIFIABLE","retracted-by-author (RETR)"),
"632-K3": ("UNVERIFIABLE","retracted-by-author (RETR)"),
"632-J12":("UNVERIFIABLE","perf claim without a benchmark oracle; code-shape censusable but the speedup is unfalsifiable here"),
"632-O10":("UNVERIFIABLE","perf claim (scanline span) without benchmark oracle"),
"632-O11":("UNVERIFIABLE","perf claim (bounds hoisting) without benchmark oracle"),
"632-NEW-6":("UNVERIFIABLE","external-service state (GitHub indexing), time-varying, cannot be verified from the tree"),
"632-NEW-13":("UNVERIFIABLE","process suggestion (use the census), not a verifiable behavior claim"),
"632-NEW-15":("UNVERIFIABLE","justification critique, process-level"),
"632-NEW-25":("UNVERIFIABLE","process suggestion (pin crash notes in CI)"),
"632-NEW-31":("UNVERIFIABLE","process suggestion (encode prior fix as test)"),
"632-R-1":("UNVERIFIABLE","port plan + effort estimate, not a behavior claim"),
"632-R-2":("UNVERIFIABLE","port plan (VelocityTracker + upstream test)"),
"632-R-3":("UNVERIFIABLE","port plan (SkPathParser extraction)"),
"632-R-4":("UNVERIFIABLE","port plan (Lexbor HTML/CSS)"),
"632-R-5":("UNVERIFIABLE","port plan (nativeExecuteForCursorWindow)"),
"632-R8": ("UNVERIFIABLE","process suggestion (fuzzing campaign), catalogue not a law"),
"632-S1": ("UNVERIFIABLE","sweep plan (batch 7); not a claim — status_note already says S2 executed"),
"632-S3": ("UNVERIFIABLE","sweep plan: aapt2 diff needs aapt2 + 20 APKs"),
"632-S4": ("NEEDS-EXTERNAL-ORACLE","sweep plan: Robolectric geometry diff IS the external oracle"),
"632-S5": ("UNVERIFIABLE","sweep plan: CI lint run"),
"632-S6": ("UNVERIFIABLE","sweep plan: cerr inventory"),
"632-S7": ("UNVERIFIABLE","sweep plan: duplicated-law grep"),
"632-S8": ("UNVERIFIABLE","sweep plan: fuzz catalogue"),
"632-S9": ("UNVERIFIABLE","sweep plan: drawable element sweep"),
}

rows = list(csv.DictReader(open(FIND, newline="", encoding="utf-8")))
changed = missed = 0
for r in rows:
    if r["source_check"].strip() == "NO-CITE":
        fid = r["finding_id"]
        if fid not in C:
            print(f"MISSING CLASSIFICATION: {fid}", file=sys.stderr); missed += 1; continue
        cat, note = C[fid]
        r["source_check"] = f"S18-CLASS 2026-11-20: {cat} — {note} (was NO-CITE)"
        changed += 1
if missed:
    sys.exit(f"{missed} rows unclassified — aborting, nothing written")
with open(FIND, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader(); w.writerows(rows)
from collections import Counter
hist = Counter(v.split(" — ")[0].replace("S18-CLASS 2026-11-20: ","") for v in (r["source_check"] for r in rows) if v.startswith("S18-CLASS"))
print(f"classified {changed} rows")
for k, v in hist.most_common(): print(f"  {k}: {v}")
print("total NO-CITE left:", sum(1 for r in rows if r["source_check"].strip()=="NO-CITE"))
