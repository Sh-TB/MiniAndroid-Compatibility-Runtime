# CONT-48 — Dooz past the white screen: the F084 budget judgment + the res/font law

**Continuation**: Issue #375 umbrella. The user's standing directive: get
Dooz and the calculator past the white screen; keep going with a high
number of concurrent tasks until a complete result; answer the cross-app
impact question by measurement. CONT-47 took BMI to REAL_APP_CONTENT; this
wave closed the Dooz half.

## Phase 0 — reconciliation (all measured)

| Row | STATUS | RESULT | EVIDENCE |
|-----|--------|--------|----------|
| Remote HEAD | TESTED | origin/main == local HEAD == b0b903be (CONT-47 closeout); working tree only tmp/flappycow submodule noise | git fetch + rev-parse |
| Binary identity | TESTED | miniandroid/build/miniandroid == 387390a00f2de498 (the recorded CONT-47 post-fix SHA) — no rebuild needed at phase 0 | sha256sum |
| Registry | TESTED | root_registry.json = 624 roots, last F-NEW-313 | python census |
| APK pins | TESTED | dooz v23 299eab21ac8b3c61 exact (the rest re-pinned during regression) | sha256sum |
| Dooz baseline face | TESTED | 31ddd4d5b8e6d18e ×3 byte-identical, rc=1, PARTIAL SUCCESS, verdict=DEFAULT_BACKGROUND_ONLY, first_missing_stage=APP_DRAW_OPS | run/cont48/baseline/r1..r3 |

## Phase 1 — the F084 judgment (CONT-42 standing question: budget vs real defect)

| Row | STATUS | RESULT | EVIDENCE |
|-----|--------|--------|----------|
| 15 s budget | TESTED | 4.7M instrs, white anchor 31ddd4d5 ×3; all 170 F084 rows are "Wall-clock budget reached (15000 ms)" tails — no [HALT-LOOP], no [R361-DEEP-REFUSE] | run/cont48/baseline/r1/run.log |
| 60 s budget | TESTED | SAME white face 31ddd4d5, 76 F084 tails — boot composition still incomplete | run/cont48/budget_t60 |
| **120 s budget** | TESTED | **36.2M instrs, composition COMPLETES: "Execution completed successfully"; real Scaffold renders — screenshot 6841d52a20e6597e ×3 byte-identical, 11.3% non-background** | run/cont48/budget_t120, dooz120_r1..r3 |
| S51-era face | TESTED | superseded: 0 [HALT-LOOP], 0 [R361-DEEP-REFUSE] at every budget | all run/cont48 logs |
| Verdict | CLASSIFIED | **F-NEW-314: budget class, not a correctness defect.** The 15 s canonical anchor stays the honest corpus face; the 120 s face is the measured envelope. Throughput engineering is the follow-up (not a dispatch/lifecycle change) | registry |

## Phase 2 — the 120 s face decoded (op-trace + DEX-wide static scan)

| Row | STATUS | RESULT | EVIDENCE |
|-----|--------|--------|----------|
| Face inventory | TESTED | top app bar (168 px) + bottom action bar (1710→1920) with real Material geometry: IconButton 105×105 r52.5 (=40dp×2.625), icon slots 63×63 (=24dp×2.625); pill/circle buttons drawn | run/cont48/optrace/optrace.tsv |
| Empty paths | TESTED | **1721/1721 PATH ops have ZERO contours**; colors 0x4d000000/0xff000000 at icon origins, scale 2.625 — no vector icon pixel ever lands | optrace.tsv |
| buildPath absent | TESTED | Lbo;::T (compose PathNode→android Path builder: rewind/setFillType/moveTo/lineTo/close) has 2 static callers (Led0;::a pc=253, Lh41;::a pc=8) and ZERO runtime presence (no Lbo;/Led0;/Lh41; mention, no CLASS_INIT row) | scripts/cont48_dooz_draw_scan.py (13,908 methods scanned) |
| Black squares | TESTED | 4 solid-black 63×63 RECTs (one per icon slot): drawRect(0,0,24,24) under translate(849,53)+scale(2.625), recorded BEFORE the paired empty PATHs → **F-NEW-317 CLASSIFIED** | optrace.tsv seq 3/60/67 + repeats |
| drawBitmap chain | TESTED | RecordingCanvas drawBitmap(bitmap-unresolved) NO-OP + Bitmap.prepareToDraw/getWidth null-recv (caller=Lf22;.e) — a parallel Image(bitmap) path with no bitmap | budget_t120/run.log:4684-4859 |
| Text | TESTED | zero TEXT ops; FONT_SOURCE font_files=0 — while the APK ships res/UJ.ttf | budget_t120/run.log:12 |
| New diagnostics | TESTED | MINIANDROID_DRAW_CALLER_TRACE (env-gated, canvas_shadow drawRect/drawPath handlers, EXP-055 convention): drawRect caller=Ly3;.p pc=6 ×1098, drawPath caller=Ly3;.g pc=12 ×1747; screenshot SHA unchanged with trace on | run/cont48/callertrace, callertrace2 |

## Phase 3 — F-NEW-315: the res/font law (fix)

| Row | STATUS | RESULT | EVIDENCE |
|-----|--------|--------|----------|
| Root | TESTED | FIX-4 app-font law scanned ONLY assets/; AOSP "Fonts in XML" (API 26+) ships app fonts as file-backed res/font entries that aapt2 renames arbitrarily (res/UJ.ttf) | src/runtime/execution_engine.cpp |
| Fix | TESTED | same extension-only scan now covers res/ — no package/name special-casing, bold detection unchanged, negative space provably unchanged | the FIX-4 block diff |
| Positive | TESTED | Dooz: FONT_SOURCE font_files=1 registered=1 first=res/UJ.ttf | run/cont48/f315_dooz |
| Negative | TESTED | every other corpus member still font_files=0 registered=0 | run/cont48/reg_* rows |
| Honest bound | TESTED | dooz RENDERED face unchanged (6841d52a ×3) — its compose text chain stops before drawText; the registration law is a correctness fix, not a face fix | dooz120_r1..r3 |

## Phase 4 — regression (binary c0f31ade222bdf9a)

| Row | STATUS | RESULT | EVIDENCE |
|-----|--------|--------|----------|
| Canonical gate | TESTED | **33/33 MATCH, ZERO DRIFT** — dooz 31ddd4d5 ×3 (the 15 s anchor held through the wave), micro da73010a, unote 4f1a9e4e, gmdice f3b483fe, opencalc a976d2f9, tttdeluxe af609429, flappycow 13cf4746, g2048 59ca1526, tanana 5f7e0114, csw 3442d9a9, simplecalc e847ca03 | run/cont48/regression_full.log |
| CONT-47 support group | TESTED | **BMI b52252c2de19b03a MATCH (REAL_APP_CONTENT held)**, sol ba50a4d2 ×2 variants, notes eb5ebd55 MATCH, alex c8d69f81 MATCH | run/cont48/reg_* |
| Probe battery | TESTED | == records exactly: fcol 140/0, f259 49/0, f259g 84/7, f266 42/0, f268 96/0, fnew253 147/0, fnew286 10/0, fnew289 28/0, ckey 105/0, cpipe 119/0, fnew302 48/24, fnew252 56/0, fnew290..297 PASS, fnew298 19/0 KEEP=5 corner=PASS, **fnew260 13/0, fnew262 19/0** | regression_full.log + probe_fnew260/262 |
| Skill self-test | TESTED | 13/13 PASS rc=0 | run/cont48/skill.log |
| Dooz 120 s determinism | TESTED | 6841d52a20e6597e ×3 byte-identical on the new binary | run/cont48/dooz120_r1..r3 |

## Cross-app impact (standing CONT-42 directive, measured on THIS wave)

One binary (c0f31ade) carries two env-gated diagnostics (zero-behavior,
screenshot SHA verified unchanged) and one res/font law whose negative space
is the whole corpus minus Dooz: **every other member byte-identical** (33/33
gate + BMI/sol/notes/alex), Dooz improved in the measured envelope (white →
real layout at 120 s) and in the font-registration truth (0 → 1 faces). The
fix helps exactly the apps that ship res/font families and drifts nothing.

## Honest bounds

1. Dooz at 15 s (the canonical corpus budget) is still the white anchor
   31ddd4d5 — the composition needs ~36M interpreter instructions. The 120 s
   face is the measured envelope, not a corpus-budget change; throughput
   engineering (interpreter speed) is the honest follow-up, registered as
   F-NEW-314's follow-up.
2. The 120 s face is REAL_LAYOUT_CONTENT: real bars/buttons/geometry, but
   the four icon slots are black squares (F-NEW-317) with empty vector paths
   (F-NEW-316), and no text is drawn yet (compose text chain stops before
   drawText; res font now registered but unused by that broken chain).
3. ctx.caller is one frame deep — both F-NEW-316/317 pin the compose
   AndroidCanvas forwarding arms (Ly3;.g/.p) but not their DEX callers; the
   next decode needs a stack-PC-style diagnostic (THROWABLE-STACK-PC
   precedent) before any dispatch change.
4. The drawBitmap(bitmap-unresolved) Image path (caller Lf22;.e) is decoded
   but unclassified this wave — recorded in the op trace evidence.
