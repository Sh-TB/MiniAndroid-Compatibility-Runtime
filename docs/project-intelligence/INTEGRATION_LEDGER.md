# INTEGRATION_LEDGER.md — canonical record of every discovered implementation

Remote main: `4efb0f21c`. States: OBSERVED < ANALYZED < IMPLEMENTED < TESTED < RUNTIME-VERIFIED < MAIN-INTEGRATED < MAIN-VERIFIED; also PARTIALLY-VERIFIED, BLOCKED, REJECTED, SUPERSEDED. Corrections appended, never overwritten.


## L-001 audit/s236 — chess/opensudoku/provider law wave (#596 era)
**Status: IMPLEMENTED-ON-BRANCH / TESTED (branch gates 32/32) — NOT integrated; needs re-port**

- **Contributor:** audit wave coder (S236.1)
- **Commits:** 536cd5ace, a86442485, 307cf55ae, c45573c88, 0121eeb0f, 99fe3ac5d, 0f4e43b32 on `origin/audit/s236` (7 ahead/162 behind main)
- **Content:** F-NEW-656c UriMatcher '#'-gate fix; F-NEW-658c ContentValues copy-ctor flat-mirror completion; F-NEW-658 SQLiteDatabase.insert family (DatabaseShadow); F-NEW-659 framework 0x01 string-id table (24 rows); F-NEW-660 AbstractStringBuilder.indexOf; F596-P1 getXml leak-shape law (chess boot uncaughts 12->0); Instant.now/ofEpochMilli (opensudoku NPE); composed-CREATE dedupe (opensudoku table create); s236_port_laws_test 12 rows + evidence/
- **Integration blocker:** src fixes target PRE-SPLIT layout (dalvik_engine.cpp +354, dalvik_engine.h +7); main now builds the split TUs (DALVIK_SPLIT=1) — laws must be re-located to domain TUs / sqlite_shadow (which is NOT split and may apply nearly verbatim)
- **Next:** re-port cycle: sqlite_shadow.cpp +161 diff review vs main; monolith diffs mapped to split TUs; battery + chess/opensudoku runtime verification

## L-002 wave10/dalvik-accel — W19/W20 build engineering (PR #626, OPEN)
**Status: IMPLEMENTED / TESTED on branch; PR open targeting wave9/dev-so-clean (stale base) — NOT in main**

- **Commits:** 15 ahead of main; head 671d2577a
- **Content:** dev-so dep-graph fix (.d files generated but never -include'd → stale relinks; -include moved below var defs); adapter_scrap_bin.h <cstdint>; verified independent-coder patch (#627: one unnecessary android_shadows.h include removed from dalvik_engine_tail.cpp, fan-out 18->17); dev PIC -O0 profile; PCH rejected with data (codegen-bound 79% wall); make -j2 rejected (9% slower, 2 cores); corrected W19 bottleneck theory (per-TU -O2 codegen floor, NOT header parse); dev targets apk-run/gate/cycle + w20_bench.sh 7-phase evidence
- **Integration blocker:** PR base is wave9/dev-so-clean (126 behind main) — retarget/cherry-pick to main required
- **Next:** cherry-pick the 3 source fixes (Makefile dev-so .d include, cstdint, engine_tail include) + record; the rest is evidence/process — reference, don't merge

## L-003 audit/m16-litehtml — OPTIONAL WebView render path (M-16, #596 §2.5)
**Status: IMPLEMENTED / TESTED on branch (probe binary) — NOT integrated; parity-optional, OFF-by-default**

- **Commits:** 3 ahead: 5755c22a5 (audit), 9ff960c43 (real prototype), 951ea2bfc (fixes)
- **Content:** vendored pinned litehtml ebb9d32b28cb under third_party/; litehtml_adapter.cpp behind MINIANDROID_USE_LITEHTML (OFF default, separate probe binary, production binary inputs byte-identical); relative @import resolution fixed per CSS spec
- **Disposition:** ZERO runtime risk (flag OFF, not linked into portable binary). Integration = adopt vendored dep + probe as opt-in; defer until WebView family work is prioritized

## L-004 #713 LAYOUT-GEOMETRY-002 — TableLayout column law fix
**Status: CLAIMED-IMPLEMENTED but commits NOT FOUND anywhere (976f97bc, ec7bf965, branch layout-geometry-001-fixes absent from remote and local) — LOST/NEVER-PUSHED**

- **Claim:** fix committed on branch layout-geometry-001-fixes; AOSP passes findLargestCells/shrinkable-row distribution described in the issue comment
- **Evidence:** issue #713 comment 2 (2026-11-27T19:17)
- **Next:** re-implement from the documented AOSP algorithm + issue description; or request the coder re-push. Do NOT mark integrated

## L-005 #714 LAYOUT-GEOMETRY-001 — MeasureSpec law mission
**Status: PARTIALLY-MAIN-INTEGRATED: f714_measurespec_law_test (9/9) IS in main's TEST_LAW; the later claimed commits (8426390c, F-NEW-714e) NOT FOUND — lost**

- **In main:** miniandroid/tests/f714_measurespec_law_test.cpp — verified running in the T281 gate
- **Lost:** 8426390c + F-NEW-714e (correction comment 2026-11-28T16:47)

## L-006 #627 S256 memory/exotic-define fixes
**Status: CLAIMED-LOCAL-ONLY (3f3df30b, c6a7291c NOT FOUND) — lost; one sub-patch (engine_tail include) separately verified+landed on wave10 (see L-002)**

- **Claim:** S256 exotic-define + SurfaceView frame-budget + uploaded-image-reference fixes, 4 local commits
- **Next:** request re-push or re-derive from the comment descriptions

## L-007 wave9/dev-so-integration (3 commits)
**Status: SUPERSEDED by main's W21-W23 build engineering (main carries the dev-so palette via merged PR #625 and subsequent direct waves)**

- **Commits:** 4f34a77f4, da5daa86d, eac17a660 (W7/W9 addenda, 106 behind main)

## L-008 T281 — KA-KYK-034/035 architecture forensic
**Status: MAIN-INTEGRATED (399fb2378, cff6846cf, 4efb0f21c) + MAIN-VERIFIED (gate green, 6-APK route evidence)**

- **Content:** domain chain proven LIVE production bridge; monolith mirror hazard named+banner-guarded; MINIANDROID_BRIDGE_ROUTE diagnostic landed; #707 correction comment 7241632176
- **Supersedes:** T280's 034 strong form + 035

## L-009 cont24/skeleton-light-experiment
**Status: OBSERVED — large divergent experiment (534 ahead/1270 behind); not assessed this session; treat as isolated until review**

- **Next:** catalog-only; do not merge without a dedicated review wave

## L-010 showcase-v1 branch + #715
**Status: OBSERVED — showcase gallery (6 commits, 1434 behind); gh-pages republished historically (ab33d08e6 per T279-CONT)**

- **Next:** showcase is presentation-only; low priority for mainline

## Corrections (appended, never overwritten)

### C1 — L-002 correction (2026-11-28, Main Coder session)
**L-002 → SUPERSEDED (fully).** All three claimed wave10 source fixes are ALREADY IN MAIN, verified by content:
- `adapter_scrap_bin.h:11` has `#include <cstdint> // W20: ... exposed by dev .d tracking fix` (the fix comment present);
- `dalvik_engine_tail.cpp` no longer includes `../framework/android_shadows.h` (removal present);
- Makefile `-include $(CORE_OBJECTS:.o=.d)` sits at line 759, BELOW the variable definitions (line 162) — the ordering bug is gone in main.
Conclusion: the wave10/W19-W20 source work reached main via direct wave commits; PR #626's remaining delta is evidence/process only. Recommendation: close PR #626 as SUPERSEDED with a pointer to the mainline waves (feedback comment to post).

### C2 — L-001 correction (2026-11-28, Main Coder session)
**L-001 → 95% MAIN-INTEGRATED (selective integration verified).** Content-level audit of main vs audit/s236:
- F596-P1 path-1 (getXml leak-shape + Instant) = main commit `0d9b537a9` ("selective integration", battery rows r11-r14 included) — MAIN-INTEGRATED;
- F-NEW-656c '#' gate = present in LIVE TU `dalvik_bridge_domain_android_core.cpp:322` — MAIN-INTEGRATED;
- F-NEW-658c copy-ctor mirror = present in `dalvik_bridge_domain_android_core.cpp:48` — MAIN-INTEGRATED;
- F-NEW-659 string-id table = present in LIVE TU `dalvik_opcodes_invoke.cpp:6785-6805` — MAIN-INTEGRATED;
- test battery `s236_port_laws_test.cpp` = present in main's tests/ — MAIN-INTEGRATED;
- **the ONLY missing piece: F596-P1 path-2 composed-CREATE dedupe law** (opensudoku CREATE-crash face) — NOT in main at session start.
Status change: INTEGRATION-IN-PROGRESS by the Main Coder this session: dedupe law applied to `sqlite_shadow.cpp` execSQL + battery row `r12_f596p2_composed_create_dedupe` (functional criterion: deduped table exists, INSERT answers rowId 1). Build+verify pending at correction time.
