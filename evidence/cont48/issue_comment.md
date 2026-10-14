## CONT-48 execution-stage audit — Dooz past the white screen: the F084 budget judgment + the res/font law

Continued from remote HEAD `b0b903be` (CONT-47 closeout), per the "continue from the latest remote HEAD" directive. Every row is **STATUS — RESULT — EVIDENCE** with exact artifacts. Work binary `c0f31ade…` (= the CONT-47 recorded post-fix `387390a0…` + two env-gated zero-behavior draw-caller diagnostics + one res/font law). The Dooz half of the standing goal ("get Dooz and the calculator past the white screen") is now closed by measurement.

### Phase 0 — reconciliation (measured, not assumed)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | origin/main == local HEAD == `b0b903be` (CONT-47 closeout) | git fetch + rev-parse |
| TESTED | binary identity == recorded CONT-47 post-fix `387390a00f2de498` — no rebuild needed at phase 0 | sha256sum |
| TESTED | registry = 624 roots (last F-NEW-313); dooz v23 pin `299eab21ac8b3c61` exact | census + sha256sum |
| TESTED | baseline face reproduced: `31ddd4d5b8e6d18e` ×3 byte-identical, PARTIAL SUCCESS, verdict=DEFAULT_BACKGROUND_ONLY, first_missing_stage=APP_DRAW_OPS | run/cont48/baseline/r1..r3 |

### Phase 1 — the F084 judgment (the CONT-42 standing question: budget vs real defect)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | 15 s budget: 4.7M instrs, white anchor `31ddd4d5` ×3; **all 170 F084 rows are "Wall-clock budget reached (15000 ms)" tails — zero [HALT-LOOP], zero [R361-DEEP-REFUSE]** | run/cont48/baseline/r1/run.log |
| TESTED | 60 s budget: SAME white face `31ddd4d5`, 76 F084 tails — composition still incomplete | run/cont48/budget_t60 |
| TESTED | **120 s budget: 36.2M instrs, boot composition COMPLETES ("Execution completed successfully"); the real Scaffold renders — screenshot `6841d52a20e6597e` ×3 byte-identical, 11.3% non-background pixels** | run/cont48/budget_t120 + dooz120_r1..r3 |
| TESTED | the S51-era face (HALT-LOOP + DEEP-REFUSE) is superseded by later engine fixes: 0 occurrences at every budget | all run/cont48 logs |
| CLASSIFIED | **F-NEW-314: budget class, NOT a correctness defect.** The 15 s canonical anchor stays the honest corpus face; the 120 s face is the measured envelope; the follow-up is throughput engineering (interpreter speed), NOT a dispatch/lifecycle change | registry 624→628 |

### Phase 2 — the 120 s face decoded (op trace + DEX-wide static scan of 13,908 methods)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | real Material geometry: top app bar (168 px) + bottom action bar (1710→1920); IconButton 105×105 r52.5 (=40dp×2.625), icon slots 63×63 (=24dp×2.625); circle + pill buttons drawn | run/cont48/optrace/optrace.tsv |
| TESTED | **1721/1721 PATH ops have ZERO contours** (colors 0x4d000000/0xff000000 at icon origins, scale 2.625) — no vector icon pixel ever lands → **F-NEW-316 CLASSIFIED** | optrace.tsv |
| TESTED | compose buildPath (`Lbo;::T`, the PathNode→android Path builder: rewind/setFillType/moveTo/lineTo/close) has exactly 2 static callers (`Led0;::a` pc=253, `Lh41;::a` pc=8) and ZERO runtime presence (no class mentions, no CLASS_INIT rows in the whole 120 s log) | scripts/cont48_dooz_draw_scan.py |
| TESTED | 4 solid-black 63×63 RECTs (one per icon slot) = `drawRect(0,0,24,24)` under the icon canvas translate(849,53)+scale(2.625), recorded BEFORE the paired empty PATHs → **F-NEW-317 CLASSIFIED** | optrace.tsv seq 3/60/67 |
| TESTED | parallel Image(bitmap) chain dead-ends: RecordingCanvas drawBitmap(bitmap-unresolved) NO-OP + Bitmap.prepareToDraw/getWidth null-recv (caller `Lf22;.e`) | budget_t120/run.log:4684-4859 |
| TESTED | zero TEXT ops; FONT_SOURCE font_files=0 — while the APK ships `res/UJ.ttf` | budget_t120/run.log:12 |
| TESTED | new permanent env-gated `MINIANDROID_DRAW_CALLER_TRACE` diagnostic (canvas_shadow drawRect/drawPath handlers, EXP-055 convention; screenshot SHA verified unchanged with it on): drawRect caller=`Ly3;.p` pc=6 ×1098, drawPath caller=`Ly3;.g` pc=12 ×1747 — one frame deep; the next decode needs a stack-PC-style diagnostic | run/cont48/callertrace, callertrace2 |

### Phase 3 — F-NEW-315: the res/font law (fix)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED (root) | AOSP "Fonts in XML" (API 26+) ships app fonts as file-backed res/font entries; aapt2 renames them arbitrarily (`res/UJ.ttf`); the FIX-4 app-font law scanned ONLY assets/ → any res/font family silently unregistered | src/runtime/execution_engine.cpp |
| TESTED (fix) | the same extension-only scan now covers res/ — no package/name special-casing, bold detection unchanged, the negative space (apps with no .ttf/.otf anywhere) provably unchanged | the FIX-4 block diff |
| TESTED (positive) | Dooz: `FONT_SOURCE font_files=1 registered=1 first=res/UJ.ttf` (was 0/0) | run/cont48/f315_dooz |
| TESTED (negative) | every other corpus member still `font_files=0 registered=0` | run/cont48/reg_* |
| TESTED (honest bound) | dooz RENDERED face unchanged (`6841d52a` ×3) — its compose text chain stops before drawText; the registration law is a correctness fix, not a face fix | dooz120_r1..r3 |

### Phase 4 — regression (binary `c0f31ade…`)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | canonical regression gate **33/33 MATCH, ZERO DRIFT** — dooz `31ddd4d5` ×3 (the 15 s anchor held through the wave), micro/unote/gmdice/opencalc/tttdeluxe/flappycow/g2048/tanana ×3 byte-identical + csw ×3 + simplecalc ×3 | run/cont48/regression_full.log |
| TESTED | **BMI `b52252c2` MATCH — CONT-47's REAL_APP_CONTENT held**; sol `ba50a4d2` MATCH; notes `eb5ebd55` MATCH; alex `c8d69f81` MATCH | run/cont48/reg_* |
| TESTED | probe battery == records exactly: fcol 140/0, f259 49/0, f259g 84/7, f266 42/0, f268 96/0, fnew253 147/0, fnew286 10/0, fnew289 28/0, ckey 105/0, cpipe 119/0, fnew302 48/24, fnew252 56/0, fnew290..297 PASS, fnew298 19/0 KEEP=5, **fnew260 13/0, fnew262 19/0** | regression_full.log + probe rows |
| TESTED | skill self-test 13/13 rc=0; dooz 120 s determinism `6841d52a` ×3 on the new binary | run/cont48/skill.log, dooz120_r1..r3 |

### Cross-app impact (the standing directive, measured on ONE binary)

The two diagnostics are env-gated and zero-behavior (screenshot SHA verified unchanged with them on). The res/font law's negative space is the whole corpus minus Dooz: **every other member byte-identical** (33/33 gate + BMI/sol/notes/alex); Dooz improved in the measured envelope (white → real layout at 120 s) and in font-registration truth (0 → 1 faces). The fix helps exactly the apps that ship res/font families and drifts nothing else.

### Honest bounds

1. Dooz at 15 s (the canonical corpus budget) is still the white anchor `31ddd4d5` — boot composition needs ~36M interpreter instructions. The 120 s face is the measured envelope, not a corpus-budget change; throughput engineering is the honest follow-up (F-NEW-314).
2. The 120 s face is REAL_LAYOUT_CONTENT: real bars/buttons/geometry, but the four icon slots are black squares (F-NEW-317) with empty vector paths (F-NEW-316), and no text is drawn yet (the compose text chain stops before drawText; the res font is now registered but unused by that broken chain).
3. `ctx.caller` is one frame deep — F-NEW-316/317 pin the compose AndroidCanvas forwarding arms (`Ly3;.g/.p`) but not their DEX callers; the next decode needs a stack-PC-style diagnostic (THROWABLE-STACK-PC precedent) before any dispatch change.
4. The drawBitmap(bitmap-unresolved) Image path (caller `Lf22;.e`) is decoded but unclassified this wave — recorded in the op-trace evidence.

Registry 624→628 (F-NEW-314 CLASSIFIED, F-NEW-315 ROOT-CAUSED-FIXED, F-NEW-316/317 CLASSIFIED). Evidence: `evidence/cont48/CONT48_RESULT.md`; scripts: `scripts/cont48_{dooz_draw_scan.py,registry.py}`; runs: `run/cont48/`.
