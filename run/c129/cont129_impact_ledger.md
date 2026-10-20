# CONT-129 Ledger — «چه تاثیری رو اون همه برنامه داشت و چقدر بهبود تو اجرا برنامه ها داشته» — impacts measured, all claims evidence-anchored

**Wave:** CONT-129 — the question was answered with a fresh full-corpus battery (22 real APKs), not with claims. Binary `25578933` (same as CONT-127 wall), HEAD base `ff162dc8`.

## ۱) امروز، روی ۲۲ برنامه واقعی کورپوس (batten تازه، همین باینری)

| metric | value |
|---|---|
| render a face | **21/22** (only whatsapp fails — corrupt 5,615-byte stub APK, honest ARTIFACT_DEFECTIVE) |
| exit rc=0 | **7** — unote, microtimer, gmdice, bouncy, opmt, chessclock, flappycow |
| zero exceptions of any kind | **11/22** |
| fully clean (rc=0 AND no-exc) | **6** |
| anchors byte-identical | **9/9** (dooz d602648e / klondike 31ddd4d5 / unote 90a67cc1 / chess a0319686 / telegram 20ac8cbbbb / tower3d 11a38a5a / opencalc d5f3c7b5 / microtimer bbd350b6 / sudoku be640e39) |

Honest adjudication: telegram at 25s gave face 31ddd4d5 (DIFF) — re-run at wall params (max-seconds 60) → `20ac8cbbbb692e63` **MATCH**. Zero drift stands; the DIFF was a harness-param artifact, reported as such.

## ۲) قبل ← بعد (سخت‌ترین شواهد)

- **tictactoe:** CONT-118 = corpus-first NATIVE **SIGSEGV** (rc=139, no screenshot) → TODAY rc=1, face `b5a7a35d` renders, runtime **survives** the poisoned dlopen loader (FIX-TTT) + F-NEW-470 clinit-attribution law (Gdx.app=OK, onResume real body). The only native crash in corpus history is now non-fatal.
- **dooz (تک‌تاک):** face `d602648e` frozen (place-then-reset poison + draw-op frontier remain), but the placement pass now **runs for the first time in lineage** (CONT-124, F-NEW-469 superinterface closure): store-check AIOOBE **27→0**, ASC-REJECT **9→0**, REAL packed position writes `2319282340800` (Ld61;.i0 updateSizeAndPosition).
- **telegram:** F-NEW-449 (MessageInfo two-count-sources) ROOT-CAUSED-FIXED → **16 PARTIAL telegram tasks unlocked**; anchor stable. Residual dlopen libjnigraphics.so (x86_64) = honest UPP-001 **APP-BOUNDARY**, architecture-level, not a runtime bug (1,175 deferred boundary logs recorded as-is).
- **forkgram:** arm64-v8a-only APK on x86_64 runtime — same honest UPP-001 boundary.
- **whatsapp:** non-ZIP stub artifact — honest classification unchanged.
- **Signal:** no APK in corpus — honest BLOCKED (no fabrication).

## ۳) اثر در مقیاس رجیستری (root-cause accounting)

- **786 roots** tracked; **312 ROOT-CAUSED-FIXED** (+50 VERIFIED-FIXED, +3 ALREADY_FIXED_AND_TESTED) → fixed-verified family ≈ **365**; terminal/closed (incl. 63 VERIFIED-CORRECT, 37+26 IMPLEMENTED(±TESTED), 48 STALE, 44 NOT-APPLICABLE, 35 SUPERSEDED, 15 CLASSIFIED …) vs open-ish ≈ **127** (112 PARTIAL + 9 UNPROVEN + 5 RC-PARTIAL + 1 BLOCKED).
- Cross-app fan-out (one fix → many apps): F-NEW-272 → **9 apps**; F-NEW-376 → 7; F-NEW-271 → 6; F-NEW-251/273/382 → 5 each; F-NEW-401..409 family → dooz/unote/opencalc/microtimer/notes.
- Every fix landed behind the zero-drift wall (9 anchors + selftest + negatives 19/19) — improvements are **stable, not flaky**.

## ۴) جمع‌بندی صادقانه

Baseline (s57, 2026-10-14) 5 anchors had faces `a976d2f9`(opencalc) `4f1a9e4e`(unote) `b5a7a35d`(chess) `da73010a`(microtimer) `d602648e`(dooz blank) — **4 of 5 anchor faces have since ADVANCED** (render content changed as fixes landed: opencalc `d5f3c7b5`, unote `90a67cc1`, chess `a0319686`, microtimer `bbd350b6`). Today: 21/22 apps render, 7 exit clean, 11 are exception-free, the corpus's only native crash is defused, and 312 root causes are fixed with byte-identical regression walls. What did NOT improve: UPP-001 dlopen architecture (telegram/forkgram), whatsapp's corrupt artifact, dooz's final draw-op frontier — all honestly OPEN with named levers.

Evidence: `run/c129/scorecard.json`, `run/c129/impact_mine.json`, `run/c129/battery.log`, 22 per-app logs + screenshots.
