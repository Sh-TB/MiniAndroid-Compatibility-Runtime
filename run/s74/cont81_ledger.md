# CONT-81 RESULT — CONT-78 corpus expansion delivered (31 rows, 73.3% app-content) + two shared-law fixes (F-NEW-382/382b) + the CONT-79/80 track verdicts

Start HEAD `a005f92a` → end HEAD `c3b759b6` · binary `fc12647ff1a7b13a` → `c2b649586357a84e` (deterministic rebuilds verified; final binary carries both fixes) · tree clean at each push · registry **687→689** (id-unique, canonical mirrored).

## 1. CONT-78 §1 — the executed corpus (≥25 NEW distinct APKs, ≥30 total)

Harness v2 (`scripts/cont81_corpus_runner.py`) closes **all seven** CONT-78-addendum gaps of `cont76_semantic_probe.py` (left untouched for history): versioned verdict vocabulary V2 (12 buckets) with legacy verdicts preserved per row; correlated-provenance law (REAL requires the ENGINE frame census from `trace_summary.json` via `MINIANDROID_BOOT_TRACE=1` — zero-drift verified on dooz `31ddd4d5`); install/harness/run-failure separation; rich evidence columns (versionName/Code, ABI inventory, exact commands+rc, full SHA-256, engine verdict + first_missing_stage + first_divergence, uncaught_n, per-app logs); interaction manifest (`--tap` + `--click-test`, per-app frames, before/after delta proof); ROOT from script location with fail-fast; honest denominators (distinct-SHA vs distinct-package, exclusions listed). **Selftests 14/14** (the addendum's 10 acceptance cases + harness-failure + sparse-content).

**Batch: 31 rows / 31 distinct APK SHAs / 31 distinct packages = 25 NEW APKs (never in CONT-73's ten-app triage nor CONT-76's five-app validation) + 6 controls. 30 executable.**

| verdict_v2 | n | % of executable | rows |
|---|---|---|---|
| REAL_APP_CONTENT | 17 | 56.7% | bouncy, flappycow, notes_secuso, tananaev-calc, simplecalc, bmi, snake(zhangman), snakeneon, tetris, snake_deluxe, g2048, tictactoedeluxe, minicraft, gmdice, unote, opencalc, chessclock, microtimer |
| INTERACTIVE_CONTENT_VERIFIED | 5 | 16.7% | OPMT (recorded tap), tetris, g2048, tictactoedeluxe, gmdice (`--click-test` canonical actuator; before≠after face + engine REAL after-state) |
| SPLASH_ONLY | 4 | 13.3% | muellerma.stopwatch (see §3), stack.tower3d (see §2), klondike (APP_DRAW_OPS), dooz (F-NEW-381 budget) |
| DEFAULT_BACKGROUND_ONLY | 3 | 10.0% | solitaire-bielefeld (APP_PIXELS), fishrings (APP_DRAW_OPS), tripeaks (APP_DRAW_OPS) |
| WHITE_BLANK | 1 | 3.3% | chess (APP_DRAW_OPS) |
| PREREQUISITE_MISMATCH | 1 | — | forkgram (arm64-only APK; honest pre-classification, not a renderer failure) |

**App-content coverage: 22/30 = 73.3% of executable.** Repeatability: **19/19** claimed successes re-run ×3, faces byte-identical (`evidence/cont81/repeatability.json`); every face with a recorded anchor matches it exactly (opencalc `f25b754c`, unote `90a67cc1`, microtimer `bbd350b6`, g2048 `f43face0`, flappycow `13cf4746`, simplecalc `2ac5d8d0`, tananaev `afe0bd8d`, ttt-deluxe `db1d633d`, gmdice `3891679d`).

Honest notes: g2048's interactive delta came from click-test — the SWIPE law is not in the tap vocabulary (named frontier). snakedeluxe: the recorded s83 steer plan did NOT reproduce a delta at `--frames 30` (before==after, honest null; stays REAL launch face). sparse-content law added after diagnosis: ballbreak (12,269 engine-owned px) / alexcalc (158,760 px, 2 colors — black-on-white calculator) are REAL; the downscaled PIL re-census is informational. telegram: REAL engine face + rc=1 + 13 uncaught (content-then-crash honesty, recorded).

## 2. CONT-78 §2 + CONT-79 P0-C — shared-law fix loop (2 roots ROOT-CAUSED-FIXED)

The NO_ROOT/WINDOW_ROOT "pair" (muellerma.stopwatch + stack.tower3d) was diagnosed at current HEAD:

- **muellerma.stopwatch — package artifact, honestly reclassified.** The uploaded APK (versionCode 6) declares **ZERO `<activity>` elements** (aapt2 xmltree: only StopwatchTile service + StopwatchService + provider + receiver) and its dex contains **NO Activity subclass**. An activity-less package cannot present window content on any Android runtime. NOT a MiniAndroid defect.
- **stack.tower3d — real libGDX native-bootstrap chain, two generic laws fixed:**
  - **F-NEW-382 (ROOT-CAUSED-FIXED P1)** — ART-identity System-property law gap. Decoded live from the APK's dex (`scripts/cont81_decode_loader.py`): libGDX's `SharedLibraryLoader.<clinit>` classifies the platform by `moe.platform.name` (iOS probe) then **`java.runtime.name.contains("Android Runtime")`**. The F-080 table answered a self-descriptive `java.vm.name` and had NO `java.runtime.name` → Os=desktop-Linux → desktop extract path (`Class.getResourceAsStream`) → `SharedLibraryLoadRuntimeException` before any view. Fix: the property table now carries the ART identity set (`java.vm.name="Dalvik"`, `java.specification.name="Dalvik Specification"`, `java.specification.vendor="The Android Open Source Project"`, `java.runtime.name="Android Runtime"`). Honest decode note: the dex contains **no "Dalvik" string at all** — the first `vm.name`-only fix attempt was insufficient and caught before any claim.
  - **F-NEW-382b (ROOT-CAUSED-FIXED P1)** — lazy G-4 `nativeLibraryDir` derivation. The extracted-lib identity existed only inside the `getApplicationInfo` seed; libGDX loads natives BEFORE any getApplicationInfo call → false "extracted a different primary ABI" refusal although `native_libs.json` recorded `primaryAbi=x86_64`. Fix: the loadLibrary branch derives the install's own law on demand (x86_64-first, `[G-4-LAZY]`). Post-fix: the loader classifies Android, takes the `System.loadLibrary` branch, and reaches the **REAL dlopen** of the extracted x86_64 `libgdx.so`.
  - **Remaining boundary, named not claimed:** the dlopen then fails on Android `DT_NEEDED` sonames (`libm.so/liblog.so/libc.so/libstdc++.so/libdl.so` — readelf recorded) vs host sonames/ld-scripts (this host's `libm.so` is a GNU ld script: "invalid ELF header"). That is the F-NEW-157/UPP-001 native-execution domain (ELF dependency-shim law). stack.tower3d's face honestly stays NO_ROOT — its first divergence moved from "platform misclassification" to the native-execution frontier.
- **Regression lock:** `fixtures/fnew382_props_probe` (apk `493d081ce592c8c6`, real toolchain) — `[F382-VM] Dalvik`, `[F382-SPEC] Dalvik Specification`, `[F382-RT] Android Runtime android-law=1`, `[F382-NEG] absent=null` (4/4).

## 3. CONT-79/80 track verdicts (evidence-backed, current HEAD)

| track | verdict | evidence |
|---|---|---|
| CONT-79 P0-A (F-NEW-277 Compose re-arm) | **CONFIRMED_ADVANCED** (re-arm + NavHost re-invoke + 926-op draw replay proven in CONT-77; the residual blocker is the budget wall) | dooz row: engine DEFAULT_BACKGROUND_ONLY/APP_DRAW_OPS with real NavHost materialization upstream; face `31ddd4d5` unchanged = zero drift |
| CONT-79 P0-B (F-NEW-381 throughput) | **BLOCKED_NEEDS_EVIDENCE** (representation change is its own wave; the measured law stands: ~10-12M ins vs ~310K ins/s, PERF-1/2 hoist = measured null) | CONT-77 PROGRESS linear scaling + 100x opencalc contrast; not re-measured this wave |
| CONT-79 P0-C (WINDOW_ROOT pair) | **RESOLVED honestly**: 1 package artifact (muellerma, no Activity) + 1 fixed libGDX bootstrap chain (F-NEW-382/382b) + residual native-execution boundary named | §2 above |
| CONT-79 P1-D (wrapper residuals) | **CONFIRMED_NOT_FIXED, scope refined**: the unwrap law itself is correct at HEAD; corpus evidence shows the residual rows are `arg_fields=(none)` draws (solitaire ×17, dooz ×1, telegram ×1) — null-vs-field-less needs the one-bit F-NEW-351 diagnostic upgrade (next wave); `addRoundRect(RectF-unresolved)` + `clipPath(path-unresolved)` single-site rows recorded | corpus stdout rows; 2 unrelated APKs carry drawBitmap noise |
| CONT-79 P1-E (AndStatus2048 NPE) | **decode-complete, NOT fixed** (fixture-first discipline; the NPE site Lt60;.getValue/Ll90;.u pc=160 stands from CONT-76's decode) | CONT-76 ledger; not re-run this wave |
| CONT-79 P1-F (interaction chain) | **5/6 verified** (OPMT, tetris, g2048, tictactoedeluxe, gmdice) + snakedeluxe honest null | §1 interactive rows |
| CONT-80 Track1 (R-NEW-001 MessageQueue) | **REJECTED as a current blocker**: across the 31-row corpus no app shows a queue-order hang — every non-real face is explained by another named root (budget/native/window-root/app-gap); the dedicated MQ invariant battery remains a tooling lead, not a proven defect | corpus rows + engine verdicts |
| CONT-80 Track2 (F-NEW-159 null receivers) | **REJECTED as a current blocker**: zero "invoked on null receiver" failures across 31 apps (alexcalc's LocaleList rows are informational; app is REAL_APP_CONTENT) | corpus stdout scan |
| CONT-80 Track3 (F-NEW-157 GLSurfaceView/EGL) | **CONFIRMED, boundary advanced + precisely named**: tower3d now classifies Android and reaches real dlopen; remaining = DT_NEEDED soname shim + EGL/surface contract | §2 + F-NEW-382b honest_note |
| CONT-80 Track4 (Arrays.toString) | **BLOCKED_NEEDS_EVIDENCE**: the Asteroids Revenge APK is not in the local corpus; 1 corpus app touches `Arrays.toString` with no failure row; the overload matrix fixture remains the acceptance gate | corpus scan |
| CONT-80 Track5 (R-NEW-068 drawables) | **REJECTED as a current blocker at launch-face level**: no layer-list/inset/rotate failure rows across 31 apps; the `adaptive-icon DECODE FAILED` icon row (4 apps, honest, non-blocking) is the recorded miss | corpus stdout scan |

## 4. Regression battery (final binary c2b649586357a84e)

wall **12/12** MATCH zero drift (dooz `31ddd4d5` ×3 + opencalc `f25b754c` ×3 + unote `90a67cc1` ×3 + microtimer `bbd350b6` ×3) · goldens **4/4** (2048/snakedeluxe/minicraft REAL + helloworld `83720c1028f832d0`) · negatives **19/19** · reinstall **8/8** · MG-310 **7/7** · MG-150 **3/3** · c72priv zero-BAD · F-NEW-376 fault-injection **70/70** · s82 validator **PASS** · f382 probe **4/4** · harness selftests **14/14**.

## 5. What did NOT run / could not be proven

- telegram/forkgram full UI (content-then-crash honesty recorded; forkgram arm64-only refusal is a prerequisite, not a face).
- The libGDX GL games do NOT render — the DT_NEEDED soname shim + EGL contract is the named frontier.
- F-NEW-381's register-file representation change was NOT attempted (its own wave; measured evidence stands).
- AndStatus2048 fixture, Arrays.toString overload fixture, MQ invariant battery, F-NEW-351 one-bit diagnostic — next-wave acceptance gates.
- sudoku/WhatsApp historical WINDOW_ROOT faces could not be re-run (APKs not in the local corpus snapshot); the historical distinction (window-content-chain vs loading) is preserved in the registry.
