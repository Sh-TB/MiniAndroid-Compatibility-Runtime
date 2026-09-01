# MASTER_CURRENT_GAP_MATRIX — UNIFIED_011.2

Identity rule (§7): findings are identified by **subject + source location**, NOT by RESULT numbers.
Every row: verified at FINAL HEAD `8e1d633` by fresh execution or fresh source inspection.
Repro command unless stated: `python3 scripts/u011_test_matrix.py --binary build/miniandroid --apk-dir <cache>`.

## A. DEX interpreter

| Finding | Source/Provenance | HEAD state | Reproduced | Real APK impact | Already fixed | Needs fix | Test | Status |
|---|---|---|---|---|---|---|---|---|
| filled-new-array 35c arg_count read from opcode nibble `(pc>>4)&0xF` (const 2); G register never read | EXP-093 handler, dalvik_engine.cpp:5504 (pre-fix) | **FIXED** (2f05134): A=(>>12), G=(>>8), C..F=cu2 | YES — fixture: old 4/5 FAIL | Telegram varargs (Object… args), any D8 varargs APK | — | — | unified0112_filled_new_array_test 5/5 PASS | FIXED+REGRESSION_TESTED |
| aget confirmed-OOB warn-and-continue (no AIOOBE) → dooz LM1/i;.f livelock (78 s, 1.2 M instr) | run/u011/matrix_postfix/dooz | **FIXED** (2f05134): confirmed OOB (arr_len>0) throws ArrayIndexOutOfBoundsException via SYNTH-EXC; arr_len==0 (unknown) keeps legacy path | YES — dooz 78 s → 0.8 s | dooz/Compose progression; any loop over arrays | — | — | matrix dooz row + [SYNTH-EXC] log | FIXED+REGRESSION_TESTED |
| Typed catch handlers decoded but not type-matched (catch-all only) | dalvik_engine.cpp THROW + find_catch_handler_for_pc (pre-existing) | present | by source inspection | apps relying on typed catch at throw site | no | yes (low risk, medium value) | — | BLOCKED (deferred: needs class-hierarchy instanceof; behavior-preserving refactor landed first) |
| THROW with no handler = skip-and-continue (not frame unwind) | EXP-071 compatibility approximation, dalvik_engine.cpp:5885 | present | by source inspection | error paths continue past throw | no | yes (now cheap: raise_synthetic_exception already unwinds) | — | DEFERRED (documented; next candidate) |
| APUT auto-grows `__array_length__` past end (no OOB) | ARRAY_PUT_CASE dalvik_engine.cpp | present | by source inspection | array semantics drift | no | yes, but regression risk | — | DEFERRED (documented with risk note) |
| long arithmetic / wide / cmp-long / rsub / shifts / neg-not / switch / lit8 | EXP-052/054/055/058/060 reports + code at HEAD | present | partially (fixtures from prior campaigns) | Telegram timestamps (long) run 3/3 deterministic | — | — | prior campaign fixtures | INTEGRATED |
| repeat-call state leakage | EXP-088 multidex_inject / EXP-043 | addressed via EXP-088 injection idempotence | no | — | yes | — | — | INTEGRATED |

## B. Resources / layout

| Finding | Source/Provenance | HEAD state | Reproduced | Real APK impact | Already fixed | Needs fix | Test | Status |
|---|---|---|---|---|---|---|---|---|
| `src_drawable_path` (AXML) vs `image_drawable_path` (runtime) render mismatch | layout_inflater.cpp:661 vs execution_engine.cpp:1382 (pre-fix) | **FIXED** (73e1946): render consumes src_drawable_path fallback | YES — ssw icons | simplestopwatch (3 icons), any XML-src ImageView | — | — | experiments/exp_graphics_image_e2e | FIXED+REGRESSION_TESTED |
| `resource_drawable_paths_` never populated (dead resolution chain) | dalvik_engine.cpp:4303/10770 readers; zero writers (pre-fix) | **FIXED** (73e1946): populate_resource_drawable_paths, density-ranked | YES | runtime setImageResource chain | — | — | [IMG-RES-RENDER] log + ssw run | FIXED |
| @string resolution / ARSC / res_config | 009 pipeline, UNIFIED_007 | present | YES (gmdice strings, ssw layout) | corpus-wide | — | — | matrix rows | INTEGRATED |
| density-qualified resources (drawable-*dpi) | populate rank order xxxhdpi>…>mipmap | **NEW** (73e1946) | YES (ssw picked hdpi icons) | all APKs | — | — | ssw after-frame | INTEGRATED |
| obfuscated res names (unote/headingcalc) | status_011_1.json blockers | present | not reproduced this run | those APKs fall to default screen | no | yes | — | DEFERRED (ARSC obfuscation — next campaign) |
| weight/measure WRAP/MATCH_PARENT | measure_layout in layout_inflater + view_renderer | present | ssw frame matches real app incl. icons | ssw | — | — | ssw BASELINE_MATCH 2a12587a | INTEGRATED |
| XML `android:onClick` captured but never dispatched | layout_inflater.cpp:658; zero consumers (pre-fix) | **FIXED** (8e1d633): dispatched on Activity via try_recursive_invoke | YES — ssw 4 handlers, 2 state changes | ssw, many F-Droid apps | — | — | click_test_report.json | FIXED |
| ComposeView inflates 0 children (Compose runtime) | dooz run log (post-2f05134): node=47 ComposeView 1080x1920, children=0 | present | YES | dooz, any Compose app | no | yes | — | BLOCKED (Compose architecture gap — known) |

## C. Image pipeline (§13/§14)

| Finding | Source/Provenance | HEAD state | Reproduced | Real APK impact | Already fixed | Needs fix | Test | Status |
|---|---|---|---|---|---|---|---|---|
| Full chain: XML src → ARSC → path → libpng decode → draw_image → framebuffer → PNG | E2E experiment | **PASS end-to-end** (73e1946) | YES — ssw | ssw + all XML-src apps | — | — | experiments/exp_graphics_image_e2e | INTEGRATED |
| `Resources.getDrawable` returns stub string | dalvik_engine.cpp:10760 (EXP-067) | present | source inspection | minor (code path rarely hit) | no | optional | — | LOW_IMPACT |
| `BitmapFactory.decodeResource` not an API entry | source scan | absent as API; decoders exist | source inspection | runtime-bitmap apps | no | yes (needs Bitmap heap model) | — | DEFERRED (with Bitmap model) |
| `setImageBitmap/setImageDrawable/setImageURI` discard state ("we don't decode drawables yet") | android_shadows.cpp:1331 | present | source inspection | runtime-bitmap apps | no | yes (same Bitmap model prerequisite) | — | DEFERRED (honest: no pixel source to copy) |
| ImageView render check misses FAB (class-name string match) | execution_engine.cpp is_image_view | present | source inspection | FloatingActionButton apps | no | yes (trivial + risk-free later) | — | DEFERRED |
| VectorDrawable/StateList/NinePatch decode | ssw "IMG?" path when XML drawable | partial (placeholder) | by design of fix | some apps | no | yes | — | DEFERRED |
| PNG palette/transparency/16-bit/interlace | CAMPAIGN-010 libpng lineage | libpng-backed | prior 7,036-image differential | corpus | yes | — | exp088_a4_png_decoder_test 12/12 | INTEGRATED |
| WebP/JPEG decode | EXP-097 §5/§6 linked | linked (libwebp/libjpeg) + now reachable from stage_render_frame (73e1946) | code path exercised when real assets are WebP/JPEG | Telegram (WebP avatars) | — | — | ssw run (PNG branch); WebP/JPEG branch by magic detect | INTEGRATED |

## D. Graphics / input

| Finding | Source/Provenance | HEAD state | Reproduced | Real APK impact | Already fixed | Needs fix | Test | Status |
|---|---|---|---|---|---|---|---|---|
| Canvas save/restore/translate/clipRect/drawBitmap/drawText | software_renderer + api Canvas | present (subset) | ssw/ssw-icons, gmdice frames | corpus | — | — | matrix frames | INTEGRATED (subset documented in STUB_DEBT.md) |
| Touch → listener bytecode → state → SECOND frame | CLICK-TEST (8e1d633) | **NEW capability** | YES — gmdice 181,512 px, ssw 918,207 px ×2 | real games | — | — | run/clicktest_gmdice/click_test_report.json | INTEGRATED |
| Frame-2 visual correctness after handler mutation | ssw onButtonStart → UI blanks (mutated tree renders empty region) | partial | YES (recorded honestly) | interaction UX | no | yes | click_frame_0.png ssw2 | HIGH_IMPACT finding, DEFERRED (needs re-render bridge for handler-mutated views) |
| GLES backend | status_011_1.json | not built (bridge glue present) | not triggered by any corpus APK (§20 rule respected — no real-APK GLES requirement demonstrated) | — | — | — | — | BLOCKED per §20 (no proven need yet) |

## E. Real apps (§11/§12) — compatibility stages

| App | SHA (verified) | Highest stage | First blocker | Exit | Screenshot |
|---|---|---|---|---|---|
| Telegram v12 12.10.1 | f5e1192725772960… (registry match) | **L12** (auth chain + deterministic render + click audit; 3/3 `088ea640…`) | — (next: onNextPressed override dispatch per docs) | 0 | run/u011/matrix_final/telegram_v12/screenshot.png |
| WhatsApp (latest, 143,571,570 B) | 88228eeaa121ab16… | L1 (56,187 instr; 12 DEX parsed) | entry app-shell delegate creation in 12-DEX index (L2→L3) | 0 (default screen eb16ab5c — NOT WhatsApp UI) | run/real_whatsapp/screenshot.png |
| Signal 8.24.2 | bba7a207c73215d7… (official manifest match) | L2+ (androidx.lifecycle/coroutines init bytecode executing) | stub-heavy init path exceeds probe window (280 s, no livelock — progress ongoing) | timeout (probe) | — (no frame yet) |
| gmdice (real game) | 1621eda11b5dbc0c… | **L13 candidate**: L12 + click state change + second frame (181,512 px) | second-frame content = configure dialog (partial visuals) | 0 | run/clicktest_gmdice/click_frame_0.png |
| simplestopwatch | b3ec1a5ec24ce53b… | L12 (XML onClick dispatched; start/reset state change 918,207 px) | frame-2 visual correctness | 0 | run/clicktest_ssw2/click_frame_0.png |
| bgclock | 72c140b0083ef273… | L6 (real window background full-screen) | WebView (not implemented) | 0 | run/corpus_bgclockhansdezwart/screenshot.png |
| microtimer / unote / chessclock / headingcalc / notes / simplekeyboard / openlauncher | see APK_REGISTRY | L1–L2 (default shared screen eb16ab5c — entry view tree not built) | entry-chain/multi-dex or ARSC obfuscation | 0 | run/corpus_*/screenshot.png |
| dooz (Compose game) | d81292cd346dcb23… | L3→L4 (setContentView completes post-2f05134; ComposeView created 0 children) | Compose runtime | 0 | run/u011/matrix_final/dooz/screenshot.png |
| tictactoe (libGDX) | 760fe5acf7b39435… | L2 (blank pre-existing) | libGDX game framework | 0 | run/u011/matrix_final/tictactoe/screenshot.png |
| stopwatch (muellerma) | 3b6a10c8dc8ddc72… | L0/L1 (pre-existing truncated APK — exit 1) | truncated APK itself | 1 | — |
| tinymusicplayer | registry SHA stale (F-Droid serves b636acad…, registry wants d7bcb24d…) | L0 (registry staleness) | n/a (registry fix needed) | 1 | — |

## F. Classification roll-up

- FIXED (this campaign, evidence above): filled-new-array 35c, aget-OOB livelock (SYNTH-EXC), src/image drawable render mismatch, dead resource_drawable_paths_ chain, XML android:onClick dead data, status_011_1 TBD placeholder, untracked handoff files.
- INTEGRATED (verified working at HEAD): telegram deterministic render, libpng/WebP/JPEG codecs, RLottie wiring, ARSC/AXML/res_config, weight/measure for ssw/gmdice, click dispatch (both paths), corpus baseline rows.
- REGRESSION_TESTED: every fix re-ran the full matrix; telegram golden 3/3 unchanged; ssw anchor moved WITH reason + determinism 3/3.
- BLOCKED: Compose runtime (dooz children), typed-catch type matching, GLES (per §20 — no real-APK requirement demonstrated), WebView (bgclock content), Signal 280 s init window, WhatsApp 12-DEX entry chain.
- DEFERRED (with reasons): THROW-no-handler frame unwind (machinery now exists), APUT bounds semantics (regression risk), Bitmap heap model prerequisite for setImageBitmap/decodeResource, FAB name match, VectorDrawable family.
- NOT_REPRODUCED / LOW_IMPACT: Resources.getDrawable stub string (rarely hit), repeat-call leakage (prior fixtures cover).
- REJECTED: EXP071_OPCODE_AUDIT's "filled-new-array ✓ verified" (was presence-only; semantics were broken until 2f05134); "dooz blank is pre-existing and engine cannot progress" (engine now progresses past setContentView).
