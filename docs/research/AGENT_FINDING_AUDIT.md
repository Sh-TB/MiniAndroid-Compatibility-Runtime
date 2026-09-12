# AGENT_FINDING_AUDIT (campaign §4 — master status table)

Directive: *Never mark something VERIFIED solely because an Agent said it
was fixed.* Every row below carries the INDEPENDENT current-HEAD evidence
probe used this campaign (2026-09-05, base commit 0edb52b + campaign
commits de5f370…). Statuses: VERIFIED / PARTIALLY VERIFIED / IMPLEMENTED
BUT NOT VERIFIED / KNOWN FAILURE / NOT REPRODUCED / BLOCKED / OBSOLETE.

## DEX / semantic battery (re-run on current HEAD, all green)

| Finding | Independent probe on current HEAD | Result | Status |
|---|---|---|---|
| RESULT_001 — long arithmetic 64-bit | `semantic_long_cmp_conv_test.cpp` (2^32+1 etc.) | 14/14 | VERIFIED |
| RESULT_009 — cmp-long / cmpl / cmpg NaN | same probe | 14/14 | VERIFIED |
| RESULT_010 — CONV_CASE conversions | same probe (int-to-byte/char/short sign-extend) | 14/14 | VERIFIED |
| invoke argument issues (35c/range receiver alignment, float raw bits) | `semantic_pass3_bridge_test.cpp` | 55/55 | VERIFIED |
| const-wide / const-wide/32 decoding | long-cmp-conv probe (CONST_WIDE cases) + return-wide F5 fix | green | VERIFIED |
| lit8 semantics | pass3-bridge + switch-parse-neg probes | 55/55 + 25/25 | VERIFIED |
| packed-switch / sparse-switch | `semantic_switch_parse_neg_test.cpp` | 25/25 | VERIFIED |
| filled-new-array(/range) | `unified0112_filled_new_array_test.cpp` | 5/5 | VERIFIED |
| typed-catch / exceptions | `unified0113_typed_catch_test.cpp` | 8/8 | VERIFIED |
| aput bounds | `unified014_aput_bounds_test.cpp` | 6/6 | VERIFIED |
| fill-array | `unified014_fill_array_test.cpp` | 5/5 | VERIFIED |
| return-wide | F5 fix + long-cmp-conv probe | green | VERIFIED |
| if-*z zero-law (INT64/FLOAT/BOOLEAN) | EXP-093 law; char-probe P6/P7 exercises if-eq family after CHAR retyping | green | VERIFIED |
| boxing / unboxing (Integer.valueOf …) | campaign Task-7 (a7d1a500-era) + chessclock format path; char-probe valueOf(char) | green | VERIFIED |
| String.format engine (%02d …) | Task-7 chessclock "0:%02d"→"0:00" | green | VERIFIED |
| enum ordinal/name (framework enums) | Cycle-E validator (Paint$Style / Path$FillType pixel-discriminated) | ALL PASS | VERIFIED |

## RESULT_012 / RESULT_013 — agent-claim reconciliation on current HEAD

| Finding | Old note (AGENT_DISCOVERIES) | Current-HEAD independent check | Status |
|---|---|---|---|
| RESULT_012 — parseInt/parseLong/parseFloat/parseDouble | "report-only claim, not wired" | production dispatch EXISTS (`dalvik_engine.cpp:13763+`); pass3-bridge PS group covers MAX/MIN/NFE | VERIFIED (claim OBSOLETE — implemented since) |
| RESULT_013 — String.substring/concat bridges | "no dispatch exists" | dispatch EXISTS (`dalvik_engine.cpp:13889/13915`); pass3-bridge covers SIOOBE + unicode | VERIFIED (claim OBSOLETE — implemented since) |

## Runtime / UI / app-level findings

| Finding | Independent evidence this campaign | Status |
|---|---|---|
| RESULT_016 — ARSC @string resolution | Task-7 chessclock [ARSC-VALUES] strings=38 colors=8; baseline matrix green | VERIFIED |
| Cycle E — Canvas Path (cubic/rMoveTo/rLineTo/offset/oval/arc/winding/even-odd/stroke) | `validate_cycle_e.sh` ALL PASS; frame SHA 64c8398e… reproduced EXACTLY across sandbox resets | VERIFIED |
| Font discovery (assets/fonts list_entries dead path) | Task-7 fix; tictactoe(emmanuelmess) font_files=1 registered=1 | VERIFIED (fixture-level) |
| Programmatic LayoutParams (weight) — NEW | tictactoe_golden: `LinearLayout.LayoutParams(0,h,1f)` rows/cells pixel-verified | VERIFIED (new commit de5f370) |
| Synthetic accessor throttle corruption — NEW | tictactoe_golden pre-fix: "null WINS" after 11 calls; post-fix: full game | VERIFIED (fixed, commit de5f370) |
| Signature-aware primitive typing (char/bool/byte/short) — NEW | char_probe 8/8 post-fix; pre-fix rendered "88"/"0"/"1" | VERIFIED (fixed, commit de5f370) |
| res/font chain (Typeface from res/font) | documented boundary since Task-7; no fixture yet | KNOWN FAILURE (open) |
| Typeface.create / family+style selection | partial paths only; Fixture D/E of §7 not built | PARTIALLY VERIFIED |
| stopwatch (muellerma) PARTIAL exit=1 | same exit + same frame SHA eb16ab5c… before/after campaign commits — pre-existing AppCompat startup chain limitation, 23k px render | KNOWN FAILURE (pre-existing, not a regression) |
| tictactoe (emmanuelmess, libGDX) blank | libGDX `com.badlogic.gdx` GL pipeline — runtime has no EGL/GLSurfaceView path; blank frame recorded honestly | KNOWN FAILURE (GL boundary, documented) |
| dooz partial AndroidX render (#F0F0F0 + few grays) | reproduced twice on current HEAD | KNOWN FAILURE (Compose/AndroidX depth, open) |
| Telegram official APK acquisition | download serves 1.2 MB stub vs pinned 82 MB hash — fetch tool rejects | BLOCKED (artifact) |
| RESULT_003 — virtual clock for determinism | determinism achieved by staged re-runs + SHA pinning (tictactoe_golden replay byte-identical); virtual clock still not needed | PARTIALLY VERIFIED (unchanged) |
| RESULT_014 — Canvas matrix composition | canvas_shadow accepts ops; Cycle-E pixel-proves geometry subset; exhaustive composition still unproven | PARTIALLY VERIFIED |

## Regression anchors (cross-sandbox, cross-history)

| Anchor | SHA | Evidence |
|---|---|---|
| simplestopwatch golden | `97933dbcb993ba09…` | BASELINE_MATCH on rebuilt sandbox (u011 matrix) |
| Cycle E path fixture frame | `64c8398ee8706188…` | byte-identical across sandbox reset + engine changes |
| tictactoe_golden frames (10) | `0d339d847f91…` run A/B | byte-identical replay (validator) |
| semantic battery | 14+55+25+5+8+6+5 = 118/118 | green after every engine change |
