# CAMPAIGN_REAL_GRAPHICS_COMPATIBILITY_FINAL — UNIFIED_011.2

Executor-executed campaign per the FULL RECOVERY/VALIDATION/INTEGRATION directive.
No recommendation-only content: every claim below carries a reproduction command,
log path, or SHA captured during this campaign on the final HEAD.

```
CAMPAIGN:  UNIFIED_011.2 — full-repository recovery, validation, integration,
           real-app execution, graphics/image end-to-end, interaction
STATUS:    EXECUTED — 3 code commits + docs + handoff ZIP; full matrix green

BASE_HEAD:   340a9cf861948b2512a8d239808be519275e87a0 (tag v0.11.1-unified-011-1)
FINAL_HEAD:  8e1d633 (+ docs commit — resolve via git rev-parse HEAD)
BRANCH:      main (13+3 commits ahead of origin bbe0ce3; push = owner credentials)
FINAL_COMMIT: see git log -1
```

## HISTORICAL_RECOVERY
- campaigns recovered: UNIFIED_000…011.1 (12 archives SHA-recorded in recovery/FORENSICS_SUMMARY.json; import 3b862e5 = 152 files, +38,349 lines). **011.5 / 012 / NEXT do not exist anywhere in the repo or history** — verified.
- missing deliverables found: 9 cases (M1–M9 in RECOVERED_CAMPAIGN_STATUS.md §2) — incl. TBD placeholder shipped in status json, untracked START_HERE/recovery, dead resource_drawable_paths_ chain, android:onClick dead data, script naming mismatch (matrix vs downloader).
- claims rejected: EXP071_OPCODE_AUDIT "filled-new-array ✓ verified" (presence-only audit; semantics broken — see FIXES); "dooz blank is terminal" (engine now progresses past setContentView).
- prior fixes verified: telegram 3/3 determinism, libpng 12/12, gmdice 158,040 px, EXP-052 throw machinery, EXP-098 RLottie wiring — all reproduced or code-verified at HEAD.

## CURRENT_REAL_GAPS (top, evidence-ranked)
1. Compose runtime — dooz ComposeView created (1080×1920) but 0 children (L4 not reached for Compose apps).
2. Handler-mutation re-render — ssw onButtonStart executes real bytecode and mutates state, but frame 2 renders blank in the mutated region (visual correctness PARTIAL).
3. Bitmap heap model — setImageBitmap/decodeResource have no pixel source; images render only via resource-resolved paths (XML src + resid→APK chain).
4. WhatsApp 12-DEX entry chain — L1 reached (56K instructions); app-shell delegate → MainActivity creation unresolved.
5. Signal init window — lifecycle/coroutines bytecode executes but exceeds a 280 s probe (progress, not livelock).
6. Typed catch handlers not type-matched (catch-all only).
7. ARSC obfuscated res names (unote/headingcalc class of apps stay on default screen).
8. WebView — bgclock full-screen background renders, no content (WebView absent).
9. Entry-chain for 6 corpus APKs (chessclock/headingcalc/notes/simplekeyboard/openlauncher/microtimer) — default shared screen (23,472 px).

## FIXES_IMPLEMENTED (all committed, all regression-verified)
1. **filled-new-array 35c** (2f05134) — arg_count from bits 12–15, 5th register G from bits 8–11, C–F from cu2 nibbles. Fixture `tests/unified0112_filled_new_array_test.cpp`: FIXED 5/5 PASS; OLD code reproduced 4/5 FAIL (always 2-element arrays) — discrimination proof.
2. **SYNTH-EXC runtime exceptions** (2f05134) — try-table search extracted verbatim (`find_catch_handler_for_pc`); `raise_synthetic_exception()` (in-frame catch → pending_exception_+jump; else frame unwind). aget **confirmed OOB** now throws ArrayIndexOutOfBoundsException. dooz: 78.0 s livelock → 0.8 s clean exit; execution progresses past ComponentActivity.setContentView.
3. **IMAGE-RES-RENDER** (73e1946) — `populate_resource_drawable_paths()` (density-ranked xxxhdpi>…>mipmap) + render dispatch: image_drawable_path → resid-chain → src_drawable_path fallback, magic-detected PNG/JPEG/WebP decode. simplestopwatch: 3 blank buttons → **real lock/settings/menu icons** (before SHA `d495e3cb2ccf6c11`, after `2a12587a0acf196c`, determinism 3/3).
4. **CLICK-TEST + XML onClick dispatch** (8e1d633) — generic `--click-test` probe (frame-1 restore → real dispatch → re-render → pixel diff → click_frame_N.png + JSON report) and the previously-dead `android:onClick` path now dispatched on the host Activity. gmdice: roll click → 181,512 px second frame. ssw: onButtonStart/onButtonReset → 918,207 px each.

## REAL_APPS (stage model §12; never equating exit-0 or non-blank with success)

Telegram (v12.10.1, SHA-verified f5e11927…):
  highest_stage: L12 — deterministic golden + auth chain + touch audit lineage
  result: 3/3 runs SHA 088ea640587ec0d28fc7cd16b0097f2529ff7da2d594c3c2663c67531d770f6a BASELINE_MATCH (unchanged by all fixes — preserved)
  screenshot: run/u011/matrix_final/telegram_v12/screenshot.png

WhatsApp (latest prod universal, 143,571,570 B, sha256 88228eeaa121ab16…):
  highest_stage: L1 — APK parsed (12 DEX, 71,506 strings), 56,187 real instructions
  first_blocker: entry app-shell delegate chain across 12-DEX class index (L2→L3)
  result: exit 0 but renders the shared default screen (eb16ab5c) — honestly recorded as NOT WhatsApp UI
  screenshot: run/real_whatsapp/screenshot.png

Signal (8.24.2 official, sha256 bba7a207c73215d7… — manifest match):
  highest_stage: L2+ — Application/LifecycleCoroutineScope init bytecode executing
  first_blocker: stub-heavy init exceeds 280 s probe window (progressing, not livelocked)
  result: probe timeout, no frame yet
  screenshot: none

Game — gmdice (real dice game, SHA-verified):
  highest_stage: L12–L13 — first frame 158,040 px; real roll click; 181,512 px state change; second frame rendered (configure dialog view)
  interaction: CLICK-TEST report run/clicktest_gmdice/click_test_report.json (listener Lde/duenndns/gmdice/GameMasterDice;)
  screenshot_before: run/clicktest_gmdice/screenshot.png
  screenshot_after:  run/clicktest_gmdice/click_frame_0.png

simplestopwatch (real app, SHA-verified):
  highest_stage: L12 — icons render (IMAGE-RES-RENDER); XML onClick start/reset dispatch → 918,207 px state change each
  interaction: run/clicktest_ssw2/click_test_report.json (4 handlers; 2 changed; settings/menu dispatched, 0 px — dialog gap)
  screenshot_before: experiments/exp_graphics_image_e2e/ssw_frame_before_full.png
  screenshot_after:  experiments/exp_graphics_image_e2e/ssw_frame_after_full.png

Corpus (all SHA-verified): dooz L3→L4 (setContentView completes post-fix; ComposeView 0 children);
bgclock L6 (real dark window background, WebView gap); chessclock/headingcalc/notes/simplekeyboard/
openlauncher/microtimer L1–L2 default screen; tictactoe L2 blank (libGDX); stopwatch(muellerma) exit 1
(pre-existing truncated APK); tinymusicplayer registry SHA stale (F-Droid serves different build).

## GRAPHICS
- ImageView: XML-src chain FIXED end-to-end; runtime resid chain FIXED (populate + dispatch); FAB name-match deferred
- Bitmap: no heap model yet (honest gap); decoders deliver RGBA directly to canvas
- Canvas: draw_image/draw_rect/draw_text proven on real APKs; save/clip subset per STUB_DEBT
- PNG: libpng lineage intact; ssw icons decoded from real APK assets (hdpi bucket selected by density rank)
- WebP/JPEG: linked + now reachable via stage_render_frame magic dispatch (no real-asset trigger in this corpus run — code path present)
- Resource: ARSC/AXML/res_config verified via matrix rows; density preference implemented
- Layout: ssw geometry matches real app incl. icon-bearing buttons (BASELINE_MATCH)
- VisualOracle: before/after frames + SHA + pixel-diff + bbox recorded for every graphics change (§27/§30)

## HIGH_IMPACT_FINDINGS
1. EXP071 opcode audit's "✓ verified" was presence-only — real varargs semantics were broken until 2f05134.
2. resource_drawable_paths_ had ZERO writers since EXP-067 — the runtime image chain was dead code for two campaigns.
3. android:onClick was captured-but-never-dispatched — whole apps (ssw) were untouchable despite a working listener path.
4. The dooz "blank" was an exception-semantics gap, not a rendering gap.
5. Two official scripts disagree on APK cache filenames (matrix vs downloader) — reproducibility hazard (worked around, flagged).
6. telegram.org/dl/android now redirects to Play Store; `telegram.org/dl/android/apk` still serves the SHA-matching v12 binary.

## DEFERRED_FINDINGS
Typed-catch type matching · THROW-no-handler unwind (machinery now exists) · APUT bounds semantics ·
Bitmap heap model (prereq for setImageBitmap/decodeResource) · FAB class-name match ·
VectorDrawable/StateList/NinePatch · ARSC obfuscation · WebView · GLES (per §20 — unproven need).

## REGRESSION (after EVERY fix; §29 order respected)
- deterministic matrix: telegram_v12 3/3 `088ea640…` BASELINE_MATCH; gmdice 158,040/`472c1d3c`; ssw 916,815/`2a12587a` (new anchor, reason recorded); microtimer/unote 23,472; tictactoe/dooz as documented; stopwatch exit 1 pre-existing
- FNA semantic fixture 5/5; old-code discrimination proof 1/5
- no new nonzero exits introduced anywhere in the matrix

## HANDOFF_MD
RECOVERED_CAMPAIGN_STATUS.md · MASTER_CURRENT_GAP_MATRIX.md · this file ·
experiments/exp_graphics_image_e2e/README.md (+ 4 evidence PNGs) · updated worklog

## HANDOFF_ZIP
MiniAndroid_FULL_VALIDATION_HANDOFF_<FINAL_HEAD>.zip — see ZIP_SHA256 below
(final name/SHA recorded at packaging time in SHA256SUMS inside the ZIP)

## ZIP_SHA256
recorded in the final message and inside the ZIP (SHA256SUMS_UNIFIED_011_2.txt)

## SCREENSHOT_MANIFEST
- run/u011/matrix_final/*/screenshot.png (8 rows incl. telegram BASELINE_MATCH)
- run/clicktest_gmdice/{screenshot,click_frame_0}.png
- run/clicktest_ssw2/{screenshot,click_frame_0,click_frame_1}.png
- run/real_whatsapp/screenshot.png
- experiments/exp_graphics_image_e2e/ssw_{buttons,frame}_{before,after}*.png
- run/corpus_*/screenshot.png (7 remaining corpus rows)
