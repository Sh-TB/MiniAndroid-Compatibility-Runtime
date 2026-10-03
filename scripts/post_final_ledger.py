#!/usr/bin/env python3
"""post_final_ledger.py — post the #371 FINAL CLOSEOUT ledger."""
import sys
sys.path.insert(0, '/home/z/my-project/scripts')
import gh371

BODY = """
# FINAL CLOSEOUT LEDGER — Issue #371

CURRENT HEAD at closeout: `5de3ab22` (binary sha16 `267bf47d5d901054`). BASE for A/B = recorded `6a6ef5b2a69f1f9d` — clean same-path rebuild reproduced it BYTE-IDENTICALLY (reproducibility proven, not assumed). Container was reset mid-closeout and repaired; every recorded gate re-executed at the final binary. All work in this Issue only — no new/parallel tracking issues. Classifier UNTOUCHED (21-P0-6 pixel ownership + correlated proof).

## §0 — BASELINE RECONCILIATION
STATUS: VERIFIED | RESULT: recorded closeout waves (S-2 b9f2c0d2, Suntimes 731bb538, GL/provenance/fanout 300f38a7) reconciled at current HEAD; BASE binary reproduced byte-identically; recorded next-divergence (Duration$Metric "Duplicate unit" IAE) re-classified as CAUGHT/NON-FATAL by direct runtime trace — the actual killers were the TimeAxis-unit and FileProvider chains | EVIDENCE: run/closeout/sun_ab/BASE_6a6ef5b2a69f1f9d/run1/run.log (ISE at line 1646, IAE at 2033); git log b9f2c0d2..bd9e9fbd | TESTS: sha equality, 3 arms ×3 runs

## §1 — RULE COMPLIANCE
STATUS: VERIFIED | RESULT: same-Issue protocol honored; status enums used; no package-name/APK-specific code (all 7 fixes are engine/framework laws with AOSP/ART/OpenJDK citations); no classifier or gate weakened — one mechanical battery repair (link lines missing build/jni/*.o after the S-2 wave added src/jni/) is completion, not weakening | EVIDENCE: commit diffs b9f2c0d2..5de3ab22; run/battery_371_final2.log (124/124) | TESTS: n/a

## §2 — S-2 NATIVE EXECUTION
STATUS: VERIFIED | RESULT: NATX probe 10/10 PASS ×3 byte-identical results (fib=610, checksum bit-exact, mixed I/F/D/J); gate A NAT-03/04 closed-frontier expectations GREEN with extraction-backed x86_64 libs rebuilt (gcc d5ec1f57fef3d271, zig aarch64 df30d6ec1aba3884); missing-symbol/missing-lib shapes remain honest ULE (N-08-NAT-01 PASS, NAT-05 PASS); repeat runs do not depend on stale host files (fresh stores) | EVIDENCE: run/closeout/natx_store/.../native_probe_results.jsonl ×3; probe_store gate_a_results.jsonl 95/0/2; prior-wave A/B BASE b2b8c18bb92dab6a NATX 0/null vs PATCH 934a58c0800e6b16 10/10 | TESTS: 10 ops ×3 runs + gate A 71 ops

## §3 — SUNTIMES/TIME4J INITIALIZATION (the recorded open frontier)
STATUS: VERIFIED at the runtime level | RESULT: time4j class-init chain now COMPLETES end-to-end — PlainDate/PlainTime/PlainTimestamp <clinit> (prior wave: EnumSet.range/allOf law), Moment <clinit> axis build (THIS WAVE: framework-enum values()/valueOf() law — TimeUnit.values() returned empty so the registerUnits loop registered 0 units and TimeAxis$Builder.build threw ISE "No time unit was registered."), Duration$Metric IAE confirmed caught. Second chain: FileProvider.parsePathStrategy IAE eliminated (meta-data law set below). BASE 3 APP-BOUNDARY process deaths → PATCH 0. App state: WelcomeActivity onCreate 736 instructions, ViewPager + indicator + Next/Back with real listeners (WelcomeActivity$2/$3), full lifecycle, canonical verdict REAL_APP_CONTENT (app_owned_pixels=61452, app_draw_ops=4), screenshot BYTE-IDENTICAL ×3 | NEXT FRONTIER NAMED: ViewPager page-fragment materialization (pager children empty, IGET-MISS ViewPager->mCurItem, setCurrentItem re-entry cycle-stub) — generic FragmentPagerAdapter container primitive, NOT a Suntimes-specific gap | EVIDENCE: run/closeout/sun_ab/{BASE_6a6ef5b2a69f1f9d,PATCH_1b744e2a213505ce}/run1..3 + ab_report.json; run/closeout/final_closeout_state.json | TESTS: 3 arms ×3 cold runs, installed identity, source hidden

## §4 — LIBGDX/GL BACKEND
STATUS: PARTIAL (boundary precisely named, no vague label) | RESULT: EGL JSR-239 facade law (prior wave) closes AndroidGraphics.checkGL20; the chain then reaches System.load(libgdx.so) and fails honestly — libgdx.so ships arm64-v8a+armeabi-v7a ONLY (no x86_64); the sole remaining dependency is ARM binary translation (S-2/UPP-001 boundary, BLOCKED-BY-IDENTITY). Deeper GL honesty note stands: PGL GLSL is recorded-not-executed | EVIDENCE: prior-wave traces in worklog 300f38a7; git show 300f38a7 | TESTS: tictactoedeluxe chain re-affirmed at current HEAD

## §5 — DEFERRED UI (TriPeaks family)
STATUS: VERIFIED (superseded by direct evidence) | RESULT: prior-wave "deferred-UI incl. TriPeaks" label SUPERSEDED — tripeaks/gmdice VERIFIED at the recorded BASE binary itself (no causal claim fabricated); suntimes welcome reached REAL_APP_CONTENT this wave; the remaining deferred-UI primitive is named (ViewPager page-fragment materialization) and recorded, not papered over | EVIDENCE: run/closeout/sun_ab; run/cont371/final_* | TESTS: ×3 byte-identical per target

## §6 — WHITE/BLACK/PARTIAL CLOSEOUT
STATUS: DONE | RESULT: classification table at final binary with STABLE classifier — VERIFIED_REAL_APP_CONTENT ×3: flappycow (13cf47464d9787f4 — recorded sha EXACT), notes_secuso (eb5ebd559cad1028 — recorded sha EXACT); REAL_APP_CONTENT ×3 byte-identical: tripeaks, gmdice, sudoku_secuso, fishrings (a341e3ad9092f640 — matches recorded), suntimes (a49f90d65a8fc5c8); determinism anchors ×3: opencalc/chess/dooz/microtimer/unote; pixel goldens 4/4: 2048/snakedeluxe/minicraft/helloworld; honest structural: stopwatch (manifest has NO <activity> — QuickSettings tile app, NO_ROOT is structural); BLOCKED-BY-IDENTITY: tictactoedeluxe (arm-only libgdx.so); render-FAIL inspection: blockblast completes honestly | EVIDENCE: run/closeout/final_closeout_state.json; run/cont371/final_miniandroid.json | TESTS: 3 cold runs per target, source APK hidden, installed-identity launch

## §7 — INSTALL/FILESYSTEM/PERSISTENCE FINAL PROOF
STATUS: VERIFIED | RESULT: persistence law set re-proven green at the final binary: loading probe restart-persistence ×2 hops + WAL/db persistence + file persistence ALL PASS; reinstall matrix 8/8; uninstall proof ALL PASS; prior-wave 32/32 physical-persistence proof (Telegram + opencalculator + chess + notes: real bytes on disk, File.length truthful, package containment, cross-package denial, SharedPreferences/SQLite/WAL, asset/resource + native-lib provenance from installed package) stands at HEAD | EVIDENCE: run/audit gate logs; scripts/closeout_persistence.py (prior wave); gate A 95/0/2 re-run in both stores | TESTS: 32/32 + gates above

## §8 — MEDIA/BITMAP/RESOURCE PROVENANCE
STATUS: VERIFIED | RESULT: flappycow MINIANDROID_GFX_PROVENANCE 12 bitmap events, all DECODED/DRAW_CALLED/REPLAYED, drawn bitmap dimensions EXACTLY match the installed APK's own drawable art (720x1280 splash, 320x160 play_button, 56x112 speaker, 250x250 about, 218x340 socket, 300x176 signinout) — and this wave's flappycow ×3 reproduces the recorded screenshot sha EXACTLY, proving the provenance chain still holds at the final binary | EVIDENCE: run/cont371/final_miniandroid.json; prior-wave provenance trace | TESTS: 3 cold runs sha-exact

## §9 — NEW-APP FAN-OUT
STATUS: VERIFIED | RESULT: ≥2 NEW games (tripeaks, gmdice) + ≥2 NEW apps (sudoku_secuso, stopwatch) + ≥1 random corpus pick (fishrings, seed 20261004), none among the main verification targets, selected BEFORE final verification; each install→launch→capture→classify; ×3 byte-identical where content is reachable | EVIDENCE: run/cont371/final_miniandroid.json | TESTS: ×3 per target

## §10 — A/B CAUSALITY
STATUS: VERIFIED | RESULT: (a) S-2: BASE NATX 0/null vs PATCH 10/10 — native execution created by the dlopen/JNI layer; (b) Suntimes: BASE 3 process deaths (TimeAxis ISE, PlatformTimezone NPE ×2, FileProvider IAE) vs PATCH 0 with the calculator chain surviving — same APK SHA bd0fbe51f684895d…, same store layout, same capture rules, evidence dirs isolated per binary (run/closeout/sun_ab/<binary-tag>/), nothing overwritten; (c) input law: tap target pager→button (F117-TAP target=2147, PerformClick dispatched=true) caused solely by the TouchDispatcher claim law | EVIDENCE: run/closeout/sun_ab/ab_report.json; prior-wave S-2 A/B | TESTS: 3 arms ×3 runs

## §11 — REGRESSION PROTECTION
STATUS: ALL GREEN at binary 267bf47d5d901054 | RESULT: determinism anchors 5/5 ×3 byte-identical (opencalc e364b001ee7abd66, chess b5a7a35d5fe0564b, dooz d602648e8e401895, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8); user goldens 4/4; loading probe ALL PASS; gate A synthetic probe 95 PASS/0 FAIL/2 INFO (reproduced in both probe stores); negative suite 17/17; reinstall matrix 8/8; uninstall proof ALL PASS; test battery 124/124 ALL PASS; multi-app installed-environment 5/5 (incl. render-FAIL blockblast); NATX 10/10 ×3; fan-out ×3 (above) | EVIDENCE: run/battery_371_final2.log; run/audit; run/closeout/* | TESTS: as listed

## ENVIRONMENT REPAIR (container reset, disclosed)
STATUS: DONE | RESULT: toolchain relayout (ecj/d8/aapt2/android-34), EXT-01/02 fixtures re-fetched SHA-exact (009b4671…/121d479c…), corpus re-fetch SHA-exact (blockblast 64589a3a7e5c0f73 matches recorded row), native probe libs rebuilt deterministic (-frandom-seed, -ffile-prefix-map), monospace font law environment restored (text2 X11 14/14), battery link lines completed with build/jni/*.o (S-2 aftermath — completion of the S-2 wave, not a gate change), Makefile resource_trace target linked with THUNK_OBJECT | EVIDENCE: run/battery_371_final2.log stage rows; scripts/build/build_fixture_apk.sh lib/ packaging | TESTS: battery 124/124 after repair

## HONEST REMAINING FRONTIERS (unchanged, not collapsed)
- ViewPager page-fragment materialization (generic FragmentPagerAdapter container primitive) — next actionable UI frontier, named with runtime evidence (IGET-MISS mCurItem, empty pager children, cycle-stub).
- ARM binary translation (UPP-001/S-2 boundary) — sole dependency for libGDX targets shipping arm-only .so (tictactoedeluxe) and Godot-class apps; BLOCKED-BY-IDENTITY.
- PGL GLSL recorded-not-executed honesty note stands.
- Safir/BLACK remain BLOCKED-BY-IDENTITY.
"""

urls = gh371.post_comment(371, BODY)
print("POSTED:", urls)
