# MASTER_PROJECT_KNOWLEDGE — canonical finding index

Purpose: a future coder must be able to find every important finding, its
evidence, current status, protecting test, and commit — WITHOUT rediscovering
old bugs. Maintained on `integration/master-reconciliation`.

Status vocabulary: VERIFIED / VERIFIED+FIXED / PARTIALLY VERIFIED / ALREADY
FIXED / NOT REPRODUCED / FALSE / UNKNOWN / ANALYSIS ONLY / NOT IMPLEMENTED.

| # | Finding | Subsystem | Evidence | Status | Protecting test / artifact | Commit |
|---|---------|-----------|----------|--------|---------------------------|--------|
| K-01 | Long arithmetic computed in low-32 union bits while tagging INT64 (2^32+1==1); System.currentTimeMillis destroyed | dalvik_engine ARITH_LONG / 2ADDR | before: 12/14 FAIL fixture | **VERIFIED+FIXED** 2026-09-02 | tests/semantic_long_cmp_conv_test.cpp (3 long-arith cases) | 6fda28d |
| K-02 | cmp-long returned 0 for ALL INT64 operands (int-only CMP_CASE) | dalvik_engine CMP | before-fixture FAIL ×3 | **VERIFIED+FIXED** 2026-09-02 | same fixture (cmp_long_64bit_*) | 6fda28d |
| K-03 | cmpl/cmpg had no NaN ordering; FLOAT64 read through float_val; INT64-tagged double consts read as garbage | dalvik_engine CMP_FLOATING | before-fixture FAIL ×2 | **VERIFIED+FIXED** 2026-09-02 | same fixture (cmpl/cmpg_double_nan, signed-zero) + bits_l2d helper | 6fda28d |
| K-04 | Conversions were type-tag-only (int-to-long(-5) garbage; float-to-int returned raw float BITS; int-to-byte/char/short never masked) | dalvik_engine CONV | before-fixture FAIL ×5 | **VERIFIED+FIXED** 2026-09-02 | same fixture (5 conversion cases) | 6fda28d |
| K-05 | 12x register nibbles: /2addr read vA=(>>8),vB=(>>4) → regB was opcode high nibble (constant 11); CONV dest/src swapped → result written to source slot | dalvik_engine 12x family | fixture add_long_2addr computed v0+reg11 | **VERIFIED+FIXED** 2026-09-02 | same fixture; NOTE: real-APK impact masked because d8 usually emits dest==src | 6fda28d |
| K-06 | Opcode table off-by-1 (ADD_INT=0x91…), lit8 corrections | dalvik_engine.h opcode table | inline comments (lines ~300/342) | **ALREADY FIXED** (pre-011.2) | real-APK journeys + fixtures | historical |
| K-07 | filled-new-array 35c: arg_count read wrong nibble, G register ignored | dalvik_engine FNA | 011.2 audit | **ALREADY FIXED** | tests/unified0112_filled_new_array_test.cpp 5/5 | historical (2f05134-era) |
| K-08 | return-wide missing from dispatcher (methods returning long/double halted) | dalvik_engine RETURN_WIDE | EXP-088 F5 | **ALREADY FIXED** | tests/exp088_f5_return_wide_test.cpp 5/5 | historical |
| K-09 | Typed catch handlers never matched; THROW skipped; cross-frame exceptions dropped | exception system | 011.3 campaign | **ALREADY FIXED** | tests/unified0113_typed_catch_test.cpp 8/8 | historical (0da839a) |
| K-10 | Handler/Looper FIFO semantics | runtime queues | EXP-088 phase F | **VERIFIED** | tests/exp088_phasef_handler_queue_semantics.cpp 23/23 | historical |
| K-11 | ARSC value-path: resource_drawable_paths_ had ZERO writers (dead chain since EXP-067) | resources/renderer | 011.2 IMAGE-RES-RENDER | **ALREADY FIXED** | simplestopwatch icons before/after d495e3cb→2a12587a | historical (73e1946) |
| K-12 | Dialog/Toast/ArrayAdapter object model missing (B1) | framework/dialog | campaign 013 | **ALREADY FIXED** (v0.11.4-fix-01 lineage) | DIALOG_SURFACE_REPORT_013.md; gmdice two-dialog chain | a5f7995 |
| K-13 | Hierarchy shadow dispatch (B4) + real-tree inflation (B5) | framework/resources | campaign 013 | **ALREADY FIXED** | REAL_APP_MATRIX_013.md | cb621fc |
| K-14 | ARSC file-backed value-path resolution | resources/arsc | campaign 013 FIX-013-04 | **ALREADY FIXED** | probe run 2026-09-02: 58 entries, 3/3 layouts | b9d93cc |
| K-15 | Real onDraw(Canvas) for custom views (libGDX ScoreView pixels) | renderer | campaign 013 FIX-013-05 | **ALREADY FIXED** | GLES_REPORT_013.md (bouncy replay) | cd0463f |
| K-16 | RESULT_016 ARSC @string/ chain: XML→AXML→ARSC→string→View property | resources | c013 probe + FIX-013-04 | **VERIFIED** | tests/c013_arsc_probe.cpp on real APK (2026-09-02) | b9d93cc |
| K-17 | RESULT_003 clock: System.currentTimeMillis/nanoTime implemented as REAL clock (EXP-043); deterministic replay does NOT currently require virtualization — virtual clock remains a design option, exp018 was experimental only | dalvik_engine API bridge | source lines ~11334-11360 | **VERIFIED** (implementation) / design note: determinism achieved via staged reruns + hash pinning, not virtual time | matrix determinism ×3 runs | historical |
| K-18 | packed-switch (0x2B) / sparse-switch (0x2C) defined but NOT dispatched | dalvik_engine | fixture 7/7 FAIL pre-fix (run/semantic_reconciliation2/) | **VERIFIED+FIXED** 2026-09-03 | tests/semantic_switch_parse_neg_test.cpp group S (7 cases) | 9d095f9 |
| K-19 | Integer.parseInt / Long.parseLong / Float.parseFloat / Double.parseDouble NOT in production dispatch (exp018 "NATIVE_CPP" was a plan, not code) | API bridge | fixture 5/5 FAIL pre-fix (VOID results) | **VERIFIED+FIXED** 2026-09-03 | same fixture group P (parse cases incl. parseLong 2^32) | 9d095f9 |
| K-20 | String.substring / String.concat NOT in production dispatch | API bridge | fixture 2/2 FAIL pre-fix (empty results) | **VERIFIED+FIXED** 2026-09-03 | same fixture group P (substring/concat) | 9d095f9 |
| K-21 | String bridge PRESENT for: StringBuilder toString/length/charAt/isEmpty, String.equals | dalvik_engine ~10220-10264 | source + real journeys | **VERIFIED** | Telegram/SimpleStopwatch journeys | historical |
| K-22 | monitor-enter/exit dispatched (no-op lock model) | dalvik_engine 6406/6411 | source 2026-09-02 | **VERIFIED** (minimal) | — | historical |
| K-23 | Canvas save/restore/translate/scale/rotate/skew/concat/clipRect/saveLayer/restoreToCount accepted by canvas shadow | framework/canvas_shadow.cpp 237-239 | source 2026-09-02 | **PARTIALLY VERIFIED** (dispatch present; full matrix-composition semantics not exhaustively proven) | canvas shadow tests | historical |
| K-24 | Compose (Dooz) blank frame boundary: ComposeView 0 children; composition hook not crossed | runtime/framework | COMPOSE_REPORT_013.md; dooz 31ddd4d5 unchanged | **UNKNOWN / BLOCKED** | matrix (deterministic blank) | — |
| K-25 | GLES render loop not connected; PortableGL glue adopted | src/gles | GLES_REPORT_013.md | **BLOCKED** (dispatch hook open) | golden cube 1,668 fps | historical |
| K-26 | Telegram golden APK SHA f5e11927 lost with 2026-09 cache wipe; current download = newer Telegram bytes (hash mismatch, also truncated 1.2MB bogus file) | external data | downloader output 2026-09-02 | **NOT REPRODUCED** (data lost — re-acquire APK) | pending | — |
| K-27 | f5da664 / v0.12.0 never existed in any recoverable artifact (remote = bbe0ce3 only; campaign-012-baseline = ea81e00) | provenance | ls-remote + local DAG 2026-09-02 | **UNKNOWN → documented** | GIT_PROVENANCE_RESOLUTION.md | 894eae2 |
| K-28 | Campaign-014 code commits lost with workspace; surviving triage artifacts archived | campaign 014 | CAMPAIGN_014_STATUS_PARTIAL.md | **PARTIAL / documented** | docs/campaign014_evidence/ (16 apps) | 894eae2 |
| K-29 | div/rem-long by zero returns 0 (Android: ArithmeticException) | dalvik_engine | fixture group D: caught/uncaught cases 0/5 pre-fix | **VERIFIED+FIXED** 2026-09-03 (all integer forms incl. previously-UNGUARDED div-int/2addr UB) | same fixture group D (5 cases, typed catch + unwind) | 9d095f9 |
| K-30 | 353-commit full history re-unified from GitHub master (was shallow at a9434de) | repository | fsck clean, merge-base bbe0ce3 | **VERIFIED** 2026-09-02 | git log/rev-parse | this branch |
| K-31 | lit8 opcode table SHIFTED against AOSP (real add-int/lit8 0xDB dispatched as AND; mul-int/lit8 0xDD as XOR; 0xDE..0xE5 unimplemented; rsub semantics wrong) — same bug class as K-06, missed in that fix | dalvik_engine.h opcode table | corpus scan scan_lit8_opcodes.py (0xDB ×2361, 0xE0 ×3399, 0xDD ×3532, 0xE4 ×5789); goldens unchanged pre/post → golden-critical paths unaffected | **VERIFIED+FIXED** 2026-09-03 (AOSP-correct table + missing dispatch: div/rem/shl/shr/ushr lit8, shl/shr/ushr lit16, rsub = lit−vB) | goldens byte-identical pre/post + lit8 fixture cases | 9d095f9 |
| K-32 | unary neg/not family (0x7B..0x80: neg/not-int, neg/not-long, neg-float, neg-double) absent from table AND dispatch — NOT_DONE #4 predicted an int32-alias bug; truth: no implementation at all | dalvik_engine | fixture group N: 7/7 FAIL pre-fix (all → 0 via unimplemented path) | **VERIFIED+FIXED** 2026-09-03 (12x dest=HIGH nibble; unsigned-domain negation → INT_MIN wraps per JLS) | same fixture group N | 9d095f9 |
| K-33 | dooz (Compose) runtime 0.9 s → 69.9 s (Pass-2) after FIX-04/02 (deterministic SAME final blank-frame SHA 31ddd4d5): Compose bytecode previously halted early on unimplemented lit8/switch opcodes and now executes ~70× more instructions before reaching the composition boundary | real app behavior | matrix runs 2026-09-03 pre/post | **DOCUMENTED** (not a regression — same result, more real work executed) | matrix_summary.json | 9d095f9 |

| K-34 | InputStream.read()/available()/close() returned 0 (old shadow); only readLine bypassed | dalvik_engine | old comment + pass3 fixture | **VERIFIED+FIXED** 2026-09-03 | tests/semantic_pass3_bridge_test.cpp group ST (5/5 vs independent unzip oracle) | pass3 |
| K-35 | XmlPullParser absent (no event machine, no termination); android.util.Xml.newPullParser + StringReader.<init> absent | dalvik_engine bridge | pass3 audit: zero source hits pre-fix | **VERIFIED+FIXED** 2026-09-03 | pass3 group X 7/7 (event seq + typed XmlPullParserException after END_DOCUMENT) | pass3 |
| K-36 | AtomicReference absent (get/set/getAndSet/compareAndSet) | dalvik_engine bridge | pass3 audit: zero source hits pre-fix | **VERIFIED+FIXED** 2026-09-03 | pass3 group AR 7/7 incl. object-identity discriminator | pass3 |
| K-37 | lit8 table STILL +3-shifted after Pass-2 "K-31 fix" (self-consistent fixture could not catch it); INVENTED SHL/SHR/USHR_INT_LIT16 at 0xD8..0xDA collided with real add/rsub/mul-int/lit8; REM_DOUBLE_2ADDR=0xD0 collided with ADD_INT_LIT16 | dalvik_engine.h | PASS3_OPCODE_AUDIT.md (independent AOSP reference): 11 shifted names, 19 byte mismatches → 0 semantic shifts after fix | **VERIFIED+FIXED** 2026-09-03 | audit script + pass3 fixture (mul-int/lit8 accumulator case FAIL pre-fix) | pass3 |
| K-38 | lit16 (22s) register nibbles one-nibble-off (vA=(>>8), vB=(>>4)) — K-05 bug class again | dalvik_engine.cpp ARITH_LIT16_CASE | 7/-2 div-int/lit16 = 0 pre-fix | **VERIFIED+FIXED** 2026-09-03 | pass3 group DR | pass3 |
| K-39 | NEW_ARRAY stored `__new_array_length__` while aget/aput/read read `__array_length__` | dalvik_engine.cpp NEW_ARRAY | bulk read([B) saw length 0 | **VERIFIED+FIXED** 2026-09-03 | pass3 ST bulk-read case | pass3 |
| K-40 | aget-byte/char/short zeroed typed heap elements; typed registers (BYTE/CHAR/SHORT union members) invisible to int_val arithmetic | dalvik_engine.cpp ARRAY_GET_CASE | aget-byte[0] = 0 on array holding 'C' | **VERIFIED+FIXED** 2026-09-03 | st_bulk_read 16067 (16×1000+67) after typed-element normalization | pass3 |
| K-41 | parseInt("2147483648") wrapped to INT_MIN (acc == 2^31 accepted on positive side) | parse bridge | FIX-05 boundary bug | **VERIFIED+FIXED** 2026-09-03 | ps_parseInt_overflow_throws_nfe | pass3 |
| K-42 | parseDouble/parseFloat rejected Java words NaN/±Infinity; strtof would accept non-Java "nan"/"inf" | parse bridge | FIX-05 documented residual TODO | **VERIFIED+FIXED** 2026-09-03 | ps_parseDouble_nan_word / infinity | pass3 |
| K-43 | Open-source source & tool intelligence catalog: 66 curated entries across all 60 mission categories, priority-ranked, with TYPE/USE discipline and PHASE-9 self-review record | project knowledge | **HELPER_SOURCE_LIST.md** (repo root) | **REGISTERED** 2026-09-03 | n/a (knowledge artifact; oracle tooling listed is external) | game-changer |

## HELPER SOURCE INTELLIGENCE (K-43) — GAME CHANGER pass, 2026-09-03

`HELPER_SOURCE_LIST.md` (repo root) is the official permanent catalog of open-source
projects/libraries/tools/corpora that can make MiniAndroid better: AOSP art + frameworks/base
+ libcore/Harmony law sources, smali/dexlib2, Apktool, Androguard, aapt2, Skia, Robolectric
(architecturally our closest sibling), CTS fixture-mining, F-Droid version-pinned corpus,
libFuzzer/AFL++/ASan robustness lane, differential-oracle machines (Waydroid + Frida),
and the full 60-category coverage map with priorities (P0×13 / P1×23 / P2×26 / P3×4).
Every entry carries: license, language, why-it-matters to MiniAndroid, reuse/adaptation
verdict (USE DIRECTLY / PORT / BORROW DESIGN / USE AS ORACLE / USE FOR TESTING /
USE FOR RESEARCH), expected gain, difficulty, relevant modules, and known limitations.
Already-integrated dependencies are recorded in its §0 so nobody re-proposes them.
Provenance: created by the FINAL GAME CHANGER mission (PHASE 8), critically self-reviewed
in PHASE 9 (duplicates merged, low-value demoted, missing sources added), registered here,
in KNOWLEDGE_LEDGER.csv (LED-051) and KNOWLEDGE_RECONCILIATION.md (§11) per mission rule 19.

## Historical campaign knowledge (§10) — where to look

| Campaign | Knowledge | Location |
|---|---|---|
| UNIFIED_000–004 | workstream transfers, corpus, tool matrix | miniandroid/docs/knowledge/WS-C*.md, CODER*_KNOWLEDGE.md |
| UNIFIED_005 | audio/3D recovery, TASKS_UNIFIED_005 | miniandroid/docs/knowledge/campaign005/ |
| UNIFIED_006 | runtime push EXP-117..120 | miniandroid/docs/knowledge/campaign006/ |
| UNIFIED_007 | real resource pipeline (ARSC/AXML) | miniandroid/docs/115_CAMPAIGN_005_REPORT.md + build_unified_007 scripts |
| UNIFIED_008 | external-libs audit (used/rejected), GLES investigation | miniandroid/docs/knowledge/campaign008/ |
| UNIFIED_009 | APK demand matrix, config matching | miniandroid/docs/knowledge/campaign009/ |
| UNIFIED_010 | PNG pipeline (libpng default) | miniandroid/docs/knowledge/campaign010/ |
| UNIFIED_011–011.1 | recovery, matrix anchor | MASTER_PROJECT_STATE*.md, MASTER_RECONCILIATION_011_1.md |
| UNIFIED_011.3 | typed catch, goldens | RECOVERED_11_1_TO_HEAD_DELTA.md |
| UNIFIED_011.4 / GAP-RECONCILIATION | ARSC value path (FIX-013-04 tag v0.11.4-fix-01) | FIXES_013.md |
| CAMPAIGN_012 | never executed as a version — provenance UNKNOWN | BUG_RECONCILIATION_013.md, GIT_PROVENANCE_RESOLUTION.md |
| CAMPAIGN_013 | dialogs, hierarchy, onDraw, scoreboard | CAMPAIGN_013_WORKLOG.md, *_013.md suite |
| CAMPAIGN_014 | PARTIAL — evidence archive | docs/campaign014_evidence/ |

## Rules this document encodes (do not relearn the hard way)

1. **The DalvikValue union aliases int_val over the LOW 32 bits of long_val.**
   Any 64-bit op that reads int_val is a bug. Use long_val / bits_l2d.
2. **12x format is B|A|op** — dest is the HIGH nibble. Read it as (instr>>12) for A.
3. **const-wide family stores raw double bit patterns tagged INT64** — floating
   handlers must bits_l2d them.
4. **Every semantic fix needs a discriminating fixture** (FAIL before, PASS after).
5. **Goldens are law**: 2a12587a (simplestopwatch), 088ea640 (Telegram, pending APK
   re-acquisition). Never overwrite silently — document or revert.
6. **Agent claims are leads.** exp018's "NATIVE_CPP parse*" list stayed a plan for
   100+ commits — always check the production dispatch.
