# COMMON_PATTERN_FANOUT — registry-wide repeated-pattern triage (CONT-11-TRIAGE)

Task ID: CONT-11-TRIAGE · Date: 2026-10-06 (read-only analysis stream)
Inputs: `root_registry.json` (566 roots) · `canonical/master_worklist.json` (735 rows, fallback metadata) ·
`docs/corpus/s82/title_registry.json` (frozen corpus denominator) · CAMPAIGN_STATE.md ·
docs/FINAL_COMPATIBILITY_CAMPAIGN.md · worklog.md (tail) · line-window co-occurrence over `docs/` + `evidence/`.
**No engine code, registry JSON, evidence, or git state was modified.** Sole writes: this file + the worklog append.

Mission (user directive, translated from Persian): *"Repeated patterns are what make dozens of programs
advance SIMULTANEOUSLY. Divide the work."* — i.e. produce the evidence-backed map of which repeated/common
problem patterns, when fixed once, advance many apps at once, ranked by fan-out.

---

## 1. Methodology (and what is counted vs inferred)

1. **Corpus studied.** All 566 roots of `root_registry.json`. 236 roots carry semantic content (title and/or
   fix/law/summary/fanout fields) and were classified into 17 pattern families; the remaining **330 roots are
   the legacy S38–S61 deep-audit block (R-NEW-001..340 era) whose rows carry only `status`/`priority` — their
   titles exist only in git-history commit messages, not in the JSON** (verified: `canonical/master_worklist.json`
   labels them "(untitled registry entry)"). They are reported as a separate honest block in §4, not force-fit
   into families.
2. **Family construction.** Semantic grouping of titles + declared fan-out fields (`fanout`, `affected_titles`,
   `corpus_fanout`, `fan_out`) + pinned member IDs for every root whose family is stated in the title itself.
   Keyword fallback over title/fix/law/summary text; ambiguous IDs pinned manually. Classification is
   first-match-wins; a handful of dual-nature roots (e.g. F-086 Long-bridge, F-NEW-251 atomicfu field keys)
   sit where their *fix site* lives.
3. **Status grouping.** `fixed` = ROOT-CAUSED-FIXED / VERIFIED-FIXED / PROVEN-FIXED / ROOT-CAUSED-CLOSED /
   VERIFIED / VERIFIED_3RUN / FIXED-S75 / ROOT-CAUSED-SEMANTIC / ROOT-CAUSED-REMEASURED-GENERIC-OK.
   `impl` = IMPLEMENTED / IMPLEMENTED+TESTED / USED_BY_EXECUTION. `open` = PARTIAL / PARTIAL-FIX / PENDING /
   OPEN / REGISTERED / OBSERVED / OBSERVED-FAIL / CLASSIFIED / RESEARCHED-NOT-IMPLEMENTED / UNPROVEN / BLOCKED.
   `vok` = VERIFIED-CORRECT (proved already-correct, no fix needed). `na` = NOT-APPLICABLE / SUPERSEDED-BY-EVIDENCE.
4. **Named titles.** Two tiers, kept separate everywhere:
   - **DIRECT** — the title appears in the family's own registry text (title/fix/law/fanout fields). Hard evidence.
   - **Co-occurrence** — title token appears within ±2 lines of a family root-ID in `docs/` or `evidence/`.
     Softer: shared ledgers inflate this, so it is used only as corroboration, never as the count.
5. **Est. fan-out.** A reasoned estimate of the distinct titles a family's law-class reaches, anchored on (a)
   declared class fan-outs quoted from the registry, (b) named titles, (c) corpus-class statements from
   `canonical/master_worklist.json` (`affected_apks`), and (d) the 202-title frozen corpus denominator.
   These are estimates, not measurements: the only measured per-title truths are the DIRECT names and the
   executed-with-evidence set (79/202 per the M6 reconciliation).
6. **Denominator (theoretical max fan-out).** `docs/corpus/s82/title_registry.json`: **202 frozen titles**
   (100 game + 100 app + 2 mandatory). M6 reconciliation: 79 executed-with-evidence (71 OBSERVED + 8 VERIFIED),
   119 NOT_TESTED, 4 BLOCKED-DOWNLOAD; local honest APK pool ≈ 25. No family estimate may exceed 202.

---

## 2. Ranked pattern-family table (by estimated class fan-out)

Status columns: roots(fixed/impl/open) = "n (f/i/o)". "Named" = distinct DIRECT-named titles (canonicalized).

| Rank | Pattern family | Roots n (f/i/o) | Affected titles (named, DIRECT) | Est. fan-out | What a fix (or the already-landed fix) unblocks |
|---|---|---|---|---|---|
| 1 | **VERDICT-HONESTY** — frame-truth census, false-SUCCESS removal, goldens/provenance, status ladder, success-path queue | 27 (10/4/13) | dooz, microtimer, unote, opencalc, ssw, headingcalc, secuso/notes, forkgram, whatsapp, chess, 2048, tictactoe, minicraft, snake, flappycow, fishrings, ballbreak, memory, dame/blidraughts, droidify, flashlight, simplestopwatch, stopwatch, telegram, uNote, hello/battery fixtures | **202 (by design)** — F-NEW-233: "every run, every corpus title, every future golden gate" | Every verdict ever issued is trustworthy; unblocks F-NEW-208..214 success-path queue, F-NEW-230 golden re-banks (ssw/headingcalc/secuso/forkgram), F-145 capture-surface fix |
| 2 | **LOADING/FS** — install → per-package sandbox → prefs/db/streams/assets → persistence | 12 (4/7/1) | telegram, forkgram, whatsapp, dooz, microtimer, unote, opencalc, chess, bouncy, calculatorm3(pmk), fairymahjong, notes(secuso), uNote, simplestopwatch, fishrings | **~150+** — F-NEW-231 "every APK"; F-NEW-234 "every Context-storage API consumer in every APK" | Already the campaign's biggest banked multiplier (F-NEW-231/234 + R-NEW-457 15-law loading family: opencalc/chess/dooz/microtimer/unote/telegram goldens ×3). Residual: F-NEW-198 single authoritative-path guarantee |
| 3 | **REFLECT/DI** — reflection, class identity, R8 renaming/merging, Hilt/DI, Gson/kotlinx serialization | 30 (16/11/2) | dooz, whatsapp, opencalc, sudokusolver, gmdice, fishrings, fossifyclock, headingcalc, microtimer, ssw, sudoku, droidify, telegram | **~100+** — F-NEW-221 "every R8-optimized release APK (horizontal merging is default-on with R8 full mode)"; F-NEW-218/219 "every Gson/Jackson/Moshi app" | One merged-class law (F-NEW-221) unblocks the Gson/DI runtime of every R8-full-mode release APK; F-NEW-250 kotlinx.serialization unblocks Compose-nav/DataStore apps (sudokusolver) |
| 4 | **UI-KIT** — inflation, measure/layout, ConstraintLayout, resources/ARSC, text metrics, draw primitives | 50 (33/11/5) | opencalc, dooz, fishrings, telegram, whatsapp, bouncy, ssw, headingcalc, secuso/sudoku, chess/jwtc, chessclock, fairymahjong, tripeaks, microtimer, uNote, snake, simplestopwatch, stopwatch, droidify, notes(secuso), 2048, gmdice, hello/battery fixtures | **~100+** — F-NEW-229 "every ConstraintLayout-based APK … common in AppCompat layouts"; F-NEW-226/227/228 text-metric & weight laws | CL MATCH_PARENT law (F-NEW-229) fixes shrink-wrap collapse corpus-wide (opencalc pad, any CL app); R-NEW-441 SlidingUpPanel geometry; F-NEW-206 dynamic-layout GONE toggles; F-NEW-192 elevation/z |
| 5 | **DEX/BASE** — register-width, pc-advance, null-receiver, String/instance-of, charset, System.io, AccessController | 7 (6/1/0) | dooz, whatsapp, fairymahjong, stopwatch | **~100+** (universal contracts — every DEX program) | Effectively closed (6/7); the instance-of/String law (F-NEW-258) and register-width law (F-NEW-171) are the template "fix once → everywhere" proofs |
| 6 | **COLLECTIONS** — DEX collections/iterator/map/heap-identity protocol laws | 24 (21/2/1) | dooz, whatsapp, chess(jwtc), chessclock, fairymahjong, fossifyclock, headingcalc, microtimer, simplestopwatch, ssw, stopwatch, sudoku, sudokusolver | **~90+** — near-universal (every R8-renamed Kotlin-collection consumer); R-NEW-360 cascade + F-NEW-259/259b already advanced dooz + jwtc-chess + fairymahjong + sudokusolver | The thesis-prover: the F-NEW-259/259b/R-NEW-360 cascade alone took dooz from 1-node tree to materialized NavHost LayoutNodes. Residual: F-NEW-172 RegularImmutableMap key materialization (WhatsApp AppContext lattice) |
| 7 | **GL/NATIVE/ENV** — GL/EGL/libGDX/SurfaceView, native libs, ABI scope, prerequisites | 5 (0/3/2) | asteroids (Godot), spacevertex, tictactoedeluxe, eggreturns (arm64-only) | **65+** — master-worklist class: "all SurfaceView games (65 OBSERVED corpus)" + libGDX titles | F-144 EGL surface family + F-NEW-157 AndroidGraphics.createGLSurfaceView would move the whole SurfaceView/GL game class past the GL frontier; tictactoedeluxe additionally needs the ARM-translation boundary (UPP-001, environment) |
| 8 | **LIFECYCLE/APP** — application/activity attach, fragment/window hosts, app-boundary unwind | 11 (4/2/5) | whatsapp, telegram, dooz, chessclock, solitaire(de.tobiasbielefeld), headingcalc, simplestopwatch, stopwatch, suntimes, stardroid, asteroids, spacevertex, memory, blockblast, fossifyclock, chess | **~60+** — F-NEW-156 "fresh-corpus onCreate APP BOUNDARY unwind family" is corpus-wide (every title crosses attach) | FragmentManager-host law (F-NEW-168) unblocks every androidx-fragment app (WhatsApp is the deep case); F-NEW-156/166 onCreate-unwind family unblocks first-run blank-face titles |
| 9 | **NUMERIC** — Long/Float/NaN/compare bridges | 1 (1/0/0) | bouncy (+6 more APKs in the wave) | **50+** — F-135 declared "694 static sites × 7 APKs", bouncy 480× STUB→IMPL | Closed; Long-bridge (F-086) was the keystone that closed the dooz ScatterMap AIOOBE (R-NEW-344/361) |
| 10 | **COROUTINES/CONC** — kotlinx-coroutines, atomicfu, executors, WorkManager | 5 (1/3/1) | dooz, whatsapp, droidify (declared) | **~40+** — F-NEW-217 "every kotlinx-coroutines app (datastore, okhttp async, lifecycle scopes) — droidify, and the corpus family using coroutines"; F-NEW-199 "every AndroidX WorkManager/ArchExecutor app" | F-NEW-217 waiter-resume protocol across the virtual-thread model unblocks datastore/okhttp/lifecycleScope apps at depth |
| 11 | **INPUT/TOUCH** — hit-test, gestures, focus, keys, scroll physics | 15 (8/7/0) | uNote, klondike, tripeaks (+fishrings/flappycow input chains) | **~40+** (every interactive title — touch-target laws are universal for tap UIs) | Closed 15/15 (R-NEW-424/425/426/427/429/432/434 input wave); banked multiplier for every tap-driven game |
| 12 | **SCHED/FRAME** — deferred-UI scheduling, timers, frame pumps, game loops, VM forward-progress | 7 (3/4/0) | fishrings, klondike, sudoku(secuso), chess?, flappycow, dooz, microtimer, fairymahjong, opencalc, uNote, stopwatch | **~30+** — F-NEW-232 declared "every deferred-transition app (splash-Timer family: fishrings, klondike, sudoku, chess?; postDelayed menu family)"; CAMPAIGN_STATE: "deferred-UI fan-out family identified (7+ titles)" | Closed 7/7 (F-NEW-232/233 observability + frame-truth); CAMPAIGN next-target #3 (time-driven re-test of chess/klondike/tripeaks/flappycow/ballbreak) is re-execution, not new law |
| 13 | **BUNDLE/PARCEL** — Bundle/parcel/saved-state fidelity | 2 (2/0/0) | dooz (+ directive synthetic, dooz-independent) | **~30+** (every Bundle/SavedStateHandle/parcel consumer) | Closed (F-NEW-257 put/getParcelable fidelity + F-NEW-378 rememberSaveable ACCEPTABLE_CLASSES) |
| 14 | **PROVIDER/SVC** — Service lifecycle, ContentProvider/Cursor/Uri transport | 4 (0/2/2) | stopwatch (service-only manifest), suntimes (CalculatorProvider ×2), spacevertex (androidx.startup), stardroid (WorkManagerInitializer), notes(secuso) (FileProvider SecurityException), chessclock (Uri.toString) | **~25+** (androidx.startup/ContentProvider-shipping apps — startup-initializer pattern is near-default in modern apps; service-only manifests) | F-143 Service.onCreate/onStartCommand family (stopwatch is structurally NO_ROOT without it); F-NEW-161 Uri null-producer chain |
| 15 | **COMPOSE** — recomposition/slot-table/snapshot/navigation/draw path | 18 (10/3/4) | dooz, sudokusolver, blockblast, fossifyclock (androidx-lifecycle leg), microtimer (MonotonicFrameClock leg) | **15–25** named compose/kotlin titles in the 202 corpus — but contains the PRIORITY-1 app (dooz) and the deepest single frontier | F-NEW-256: destination content NOW MATERIALIZES (post F-NEW-259/259b); remaining single root = AndroidCanvas bridge `Ljt1;` never constructed → 0 canvas ops. One bridge law = real pixels for every Compose app |
| 16 | **WEBVIEW** — WebView/QuickJS/DOM/CSS/fetch/cookies | 15 (11/3/1) | z.ai browser demo, mykanji, breakout, weatherforecast (worklist: "WebView/HTML5 targets"), telegram (web content) | **10–15** (WebView-shipping titles) | Closed chain R-NEW-443..455 (loadUrl→module scripts→fetch→cookies→DOM/CSS/img/canvas); residual R-NEW-456 is BLOCKED (live z.ai Svelte-5 bundle) |
| 17 | **MEDIA** — MediaPlayer/BitmapFactory object laws | 3 (2/1/0) | fishrings (+ flappycow bitmap provenance) | **~10+** (audio/bitmap consumers) | Closed (F-155/R-NEW-400 MediaPlayer state machine, F-NEW-240 inJustDecodeBounds) |

---

## 3. Top-3 highest-fan-out OPEN patterns + concrete next actions

Selection rule: size of the law-class the open root gates × openness (OBSERVED/CLASSIFIED/PENDING, not BLOCKED)
× evidence already banked (first divergence proven). Cross-checked against the registry's own
`summary.open_frontiers` (F-143, F-144, F-145, F-147, F-NEW-157, F-NEW-161, F-NEW-168, F-NEW-169, F-NEW-221,
F-NEW-229, R-NEW-228, R-NEW-303, R-NEW-331, R-NEW-340, R-NEW-381, F-NEW-250).

### #1 — F-NEW-221 R8 merged-class constructor/dispatch mismatch (REFLECT/DI, OBSERVED, P1)
- **Fan-out:** "every R8-optimized release APK (horizontal merging is default-on with R8 full mode)" — the
  largest OPEN law-class in the registry; R8 full mode is the modern-AGP default, so this gates the Gson/DI
  runtime of most release-built corpus titles, not one app.
- **State:** root-caused by field-trace (opencalc post-F-NEW-220 face): `LA/h;` is a horizontal class merge
  (field `a` mode int + packed-switch ctor paths: SparseIntArray pair / s/h+ArrayDeque / filled-new-array
  variants), but the `z(TypeToken)` dispatch (Map.get cache fast-path from a DIFFERENT merged origin) ran on an
  instance whose executed ctor path left field `b=null` → Map.get on null receiver → APP BOUNDARY.
- **Next action:** (1) build a minimal R8-full-mode horizontal-merge probe APK (two merged origins sharing one
  class, distinct ctor paths, cross-origin method dispatch) to pin the semantics; (2) implement per-origin
  field-slot separation (or a merged-class field-table keyed by executed ctor path) in the DEX object model —
  same shape as the F-NEW-160 field-identity and F-NEW-251 split-brain fixes; (3) re-run the opencalc Gson face,
  then droidify4/5 (F-NEW-217 evidence APKs) as the second live proof; regression gate anchors 5/5 ×3.

### #2 — F-144 + F-NEW-157 GL/EGL SurfaceView family (GL/NATIVE/ENV, OPEN / OBSERVED-FAIL, P2/P1)
- **Fan-out:** master-worklist-declared class "all SurfaceView games (65 OBSERVED corpus)" + the libGDX title
  class — the largest single *named* class among open roots; every 2D/3D game that renders through
  GLSurfaceView dies at the same first divergence today.
- **State:** F-144 OPEN (EGLContext.getEGL → checkGL20 → GdxRuntimeException); F-NEW-157 OBSERVED-FAIL
  (libGDX AndroidGraphics.createGLSurfaceView NPE → app-boundary unwind). The EGL JSR-239 facade law closed
  checkGL20 only (§4 of the #371 closeout); tictactoedeluxe is additionally BLOCKED-BY-IDENTITY (arm-only
  libgdx.so → ARM translation boundary UPP-001 — an environment decision, not an engine law).
- **Next action:** (1) implement the EGL object law family (EGLDisplay/EGLContext/EGLSurface records +
  eglGetError contracts) and the GLSurfaceView GLThread lifecycle shadow so `createGLSurfaceView` constructs
  and the render thread pumps; (2) first live target = spacevertex (x86_64, already reaching APP_PIXELS with
  "GL surface draw never fires" recorded by R-NEW-459) — the A/B is 0 GL draw ops → N; (3) keep
  tictactoedeluxe honestly BLOCKED pending the UPP-001 ARM-translation decision; (4) regression: NATX 10/10 ×3
  + anchors ×3.

### #3 — F-NEW-256 Compose draw path (COMPOSE, CLASSIFIED, P1) — contains the PRIORITY-1 app
- **Fan-out:** every Compose app (declared class fan-out "Compose family" F-NEW-205; F-NEW-247 "every Compose
  app using MeasureAndLayoutDelegate/DepthSortedSet — all androidx.compose 1.6.x"). Smaller named count than
  #1/#2 but it is the sole remaining root between dooz (PRIORITY-1) and real pixels, and Compose titles are
  the fastest-growing corpus class.
- **State:** CONT-9/CONT-10 re-proved the chain link-by-link; F-NEW-259/259b/R-NEW-360 fixed the
  DEX-iterator/copy cascade; destination content NOW MATERIALIZES (LayoutNodes o6128..o6225 + applier
  inserts). Remaining single root: layer drawContent chains run (`Lpz0;.M0/L0/T0`) but the AndroidCanvas
  bridge (`Ljt1;`) is never constructed → 0 canvas ops → framebuffer background-only.
- **Next action:** (1) construct the AndroidCanvas bridge when Compose drawContent layers run (route the
  `Lpz0;.M0/L0/T0` draw chains into the render-task canvas — the same ViewShadow canvas the UI-KIT already
  paints with); (2) assert 0→N canvas ops on dooz and close R-NEW-381 (OBSERVED-FAIL first-frame face) in the
  same wave; (3) then F-NEW-250 (kotlinx.serialization nav args, sudokusolver) and R-NEW-340 (recomposer
  frame-pump PARTIAL-FIX) become the next links; regression: anchors 5/5 ×3 byte-identical.

**Honorable mentions (4th–6th by fan-out among open roots):** F-NEW-217 kotlinx MutexImpl waiter-resume
("every kotlinx-coroutines app"; CAS already proven NOT the cause — attack the waiter-resume protocol across
the virtual-thread model with the F-NEW-254 exception-chain law as template); F-NEW-229 CL MATCH_PARENT spec
law ("every ConstraintLayout-based APK"; one fix was attempted and reverted — re-derive as a generic
container law with the [U007-SPEC] trace, then execute the never-run §10-item-3 fan-out sweep over installed
store APKs); F-NEW-168/169 androidx FragmentManager host + WhatsApp DI provider lattice (every
androidx-fragment app; F-NEW-156 family).

---

## 4. The legacy unlabeled block (honest)

330 roots (R-NEW-001..340 era, S38–S61 deep-audit rows) carry no semantic fields in `root_registry.json`
(their titles live in git commit messages and `docs/maintenance/worklog.md` history). Status distribution:
PARTIAL 101, UNPROVEN 72, VERIFIED-CORRECT 45, NOT-APPLICABLE 42, VERIFIED-FIXED 34,
RESEARCHED-NOT-IMPLEMENTED 16, ROOT-CAUSED-FIXED 8, SUPERSEDED-BY-EVIDENCE 7, OBSERVED-FAIL 3, IMPLEMENTED 1,
FIXED-S75 1, ROOT-CAUSED-SEMANTIC 1. Priorities: P3 147, P2 73, P1 59, P0 46, NONE 6. Known semantic anchors
from CAMPAIGN_STATE: R-NEW-301/303/242/246/256/259/261/279/281/285 = dooz compose/lifecycle family;
R-NEW-335 = dooz ScatterMap AIOOBE (closed via F-086/R-NEW-361); open_frontiers R-NEW-228/303/331 sit here.
A title-backfill pass (git-archaeology) would make these classifiable — recommended as a follow-up triage.

---

## 5. Cross-checks against prior fan-out work (no contradictions found)

- `docs/LOADING_ROOT_FANOUT.md` and `docs/FILE_RESOURCE_LOADING_COMPATIBILITY.md` (38 roots / 7 families):
  the LOADING/FS row here is their superset; their 7 families map to rows 2 + parts of 5/13/14.
- `CAMPAIGN_STATE` checklist item 11 "Families A–W root/fan-out audit — IN PROGRESS; deferred-UI fan-out
  family identified (7+ titles)": confirmed and extended — SCHED/FRAME has 7 roots, ~30+ title class.
- `docs/DIFFERENTIAL_WORKING_VS_WHITE.md` (9 apps → 5 distinct generic roots): consistent — those roots
  (VIEWTREE/ATTACH, COMPOSE, NATIVE/JNI, FRAGMENT, ANDROIDX-LIFECYCLE) map to rows 8/15/7 here, and all five
  landed or advanced (R-NEW-458..462).
- `docs/DEEP_ROOT_CROSSMATCH.jsonl` (10 candidates A–F, zero duplicate roots): consistent — no family here
  merges roots that crossmatch marked distinct.
- F-NEW-212 ("high-fan-out missing-laws search — once the successful path is known, inspect failed titles
  through it") is PENDING: this document is the static-first, registry-side version of that search.

## 6. Honesty notes

- Est. fan-out numbers are class-reach estimates anchored on declared registry strings and worklist classes —
  they are NOT measured per-title runs. The measured truths are: 236 classified roots, per-family status
  counts, DIRECT named titles, and the 202/79/119/4 corpus reconciliation.
- The 330-root legacy block is excluded from family stats because it has no machine-readable semantics; any
  family number that included it would be invented.
- Co-occurrence title counts were deliberately NOT used in the table (shared ledgers make them inflate toward
  "everything affects everything"); they corroborated ~50 of the DIRECT names and are available in the triage
  scratch output.
- Families overlap by nature (one app exercises 10+ families); rows rank *law-class reach*, not exclusivity.
- Registry drift: `root_registry.json` says 566 roots; `canonical/root_cause_registry.json` projection is at
  535 (generated 2026-10-03, pre-CONT-10/11 additions). The projection is stale by 31 roots — regeneration
  owed in the next commit-affecting wave (not done here: read-only stream).

*Generated by CONT-11-TRIAGE (read-only analysis stream); classification scratch:
236 roots → 17 families via pinned IDs + keyword fallback; zero writes outside this doc + worklog append.*
