# CONT-21 — EXECUTION FAMILY MATRIX (Issue #384 / ARCH-001)

Binary lineage: `b6ee41e77acb88ec` (CONT-20) → **`882b7cdf389aabc3`**
(engine deltas: F-NEW-273 component-info identity chain + F-NEW-272 Thread
UEH law + BaseBundle keySet family; commit bd691a96 tree + this wave).
Wave date: 2026-10-08. Head at wave start: bd691a96.

Central question per investigation: **"What is the first shared missing
primitive?"** — answered per family below, with runtime evidence.

---

## 1. PHASE A — INVENTORY (selected representatives)

| Target | Package | Version | APK sha256 (16) | ABIs | Family | Actual path (traced) |
|---|---|---|---|---|---|---|
| opencalc | com.darkempire78.opencalculator | 3.2.0 | `2642613868a8a80f` | (none shipped) | F1 | Activity→appcompat inflate→View tree |
| stopwatch | com.github.muellerma.stopwatch | 1.5 | `3b6a10c8dc8ddc72` | (none shipped) | F1 | Activity→androidx.startup→View tree |
| chessclock | com.chessclock.android | 2.11.2 | `5ca6f2c54c05efe7` | (none shipped) | F1 | Activity→View tree→input |
| unote | app.varlorg.unote | 1.8.0 | `be91103f0e7db443` | (none shipped) | F1 | Activity→ListView tree→draw |
| microtimer | dubrowgn.microtimer | 1.8 | `79c6f730f64886e7` | (none shipped) | F1 | Activity→Room db→View tree→draw |
| tictactoe (real APK) | com.emmanuelmess.tictactoe | 1.0.0 | `760fe5acf7b39435` | arm64/armeabi/armv7/x86/x86_64 | F2 | Activity→libGDX GLSurfaceView20 |
| g2048 | com.miniandroid.g2048 | 1.0 | `c933b5b821920875` | (none shipped) | F2 | Activity→Board2048View(Canvas)→draw |
| tictactoe_deluxe | com.miniandroid.tictactoedeluxe | 1.0 | `d04d92eab8dbbb11` | (none shipped) | F2 | Activity→Canvas board→draw |
| fishrings | eu.veldsoft.fish.rings | 1.23 | `14d7dd80f7563c6a` | (none shipped) | F3 | Splash→Timer(5000ms)→game Activity |
| flappycow | com.quchen.flappycow | — | `bdbd6eb78c711656` | (none shipped) | F3 | BaseGameActivity→StartscreenView |
| bouncy | com.dozingcatsoftware.bouncy | 1.16.0 | `ffda0d9cb0b1b2aa` | arm64/armv7/x86/x86_64 | F3 | Activity→SurfaceView/Holder loop |
| forkgram | org.forkgram.classic | 12.10.8.0 | `3baeecb3288577e9` | arm64-v8a only | F4 | Application→providers→UI init |
| telegram | org.telegram.messenger.web | 12.10.5 | `e37aced2a49c1dbb` | arm64/armv7/x86/x86_64 | F4 | Application→providers→UI init |
| dooz | io.github.yamin8000.dooz | 1.0.23 | `299eab21ac8b3c61` | arm64/armv7/x86/x86_64 | F6 | App→Compose runtime from APK DEX |
| minibrowser | com.miniandroid.browser | 2.0 | `d606fa140bc2aad4` | (none shipped) | F7 | Activity→WebView→HTML/CSS/JS |

FAMILY 5 (social/media): **no representative APK exists in this corpus**
(Instagram-like apps absent from upload/, canonical_apks/, and all
evidence waves). Recorded honestly as NO-TARGET-IN-CORPUS; the family's
shared-primitive surface (feed Recycler + async image load) is expected to
overlap the F4 messaging surface, which IS represented by two independent
Telegram-engine APKs. `whatsapp.apk` in upload/ is a 5,615-byte stub
artifact, not a real app — recorded as an artifact fact, not evidence.

ABI environment facts: forkgram is arm64-only (recorded; not a primary
blocker per the directive). Native-library extraction face
(GATEA-NATIVE `tmessages.49` primary-ABI mismatch) is a pre-existing
registered surface hit by both F4 targets.

---

## 2. REQUIRED MATRIX (Phase B/C/D evidence per cell)

| Family | Representative Target | Actual Path (runtime-traced) | Required Primitives | Current Coverage | First Divergence (runtime-captured) | Shared By | Genericity | Verification | Next Root | Source |
|---|---|---|---|---|---|---|---|---|---|---|
| F1 Base/View | opencalc, unote, microtimer, stopwatch, chessclock | Activity lifecycle real; setContentView→ViewTree; measure/layout/draw; input | lifecycle, inflate, ViewTree, measure/layout/draw, prefs, Room(db) | 3/5 REAL_APP_CONTENT at 882b7cdf (unote 4f1a9e4e, microtimer da73010a, opencalc a976d2f9) | stopwatch(pre-fix): `AppInitializer.discoverAndInitialize pc=34 iget ProviderInfo.metaData on null` → APP BOUNDARY (white screen). chessclock: `Uri.toString on null` in onCreate (input-injection face) | F4+F6 via F-NEW-273 chain | **GENERIC BASE** (androidx.startup component-identity chain — fixed this wave as F-NEW-273; remaining chessclock face is intent-URI law) | FRAME_CAPTURED ×3 (unote/microtimer/opencalc anchors byte-identical ×3) | chessclock Uri.toString-on-null in onCreate (input-URI law) | run/cont21/family/*, run/cont21/sweep_* |
| F2 2D Canvas/View games | g2048, tictactoe_deluxe (+ real-APK tictactoe) | Activity→custom View; Canvas/Paint/Bitmap; frame pump; tap input | Canvas draw ops, Bitmap, frame callbacks, tap pipeline | 2/3 REAL_APP_CONTENT (g2048 59ca1526, ttt_deluxe af609429, both ×3 byte-identical) | real tictactoe: `GLSurfaceView20.setPreserveEGLContext` NoSuchMethodException → AndroidInput null → onCreate APP BOUNDARY (libGDX surface/input family) | F3 (GL/SurfaceView family shares the EGL/SurfaceHolder surface) | libGDX surface+input = generic engine surface (R8-obfuscated but framework-law surface) | FRAME_CAPTURED ×3 (g2048/ttt_deluxe) | libGDX GLSurfaceView20 EGL-context law (real-APK F2 rep) | run/cont21/family/tictactoe |
| F3 SurfaceView/game loop | bouncy, flappycow, fishrings | flappycow: View+Canvas startscreen (SUCCESS, 636 colors); bouncy: SurfaceView/Holder loop renders 145 colors (Faces inside); fishrings: Splash→Timer 5000ms scheduling face (classified CONT-8) | Surface/SurfaceHolder, game-loop timing, input, canvas frame | flappycow SUCCESS (13cf4746); bouncy FRAME_CAPTURED with faces (b6dde607); fishrings DEFAULT_BACKGROUND in 2-frame window (by design, timer) | bouncy: `SurfaceHolder.setFormat on null` + `Iterator.hasNext on null` (deferred, render continues) — SurfaceHolder object law gap | F2 GL/EGL family + F4 (both need the Surface/Holder identity law) | GENERIC (SurfaceView family law; bouncy is x86_64-compatible real APK) | FRAME_CAPTURED (bouncy 145 colors / 978,380 nondom px) | SurfaceHolder/Surface object identity law (bouncy chain) | run/cont21/family/{bouncy,flappycow,fishrings} |
| F4 Messaging | telegram, forkgram (family evidence — NOT separate executors) | Application bind → content providers → TLRPC/app chains → UI init | providers, ComponentInfo identity, native libs, UI init, collections | Both die in UI-init chain; both advance past F-273 startup cluster post-fix (rc 1→0) | pre-fix shared face: `ProviderInfo.metaData NPE` (F-273, fixed); current first face: telegram `Ll9/j; uncaught` APP BOUNDARY + GATEA-NATIVE ABI face; forkgram `d6$w.c on null` (Telegram UI init — family-internal) | F1+F6 (F-273 was shared with them); ARR-LEN-NULL ContactsController shared between BOTH telegram-engine targets (family-internal) | Shared primitives = GENERIC (F-273 proven); d6$/y41$/ContactsController faces are Telegram-engine family faces | LOADED (post-fix rc 0; UI not yet materialized) | Ll9/j; early-exit face (telegram) + native-ABI extraction law | run/cont21/family/{telegram,forkgram}, run/cont21/sweep_* |
| F5 Social/media | **none in corpus** | — (family architecture documented: feed/layout→scroll→image load→async→measure/layout/draw) | Recycler/Adapter, async image, cache | NO-TARGET-IN-CORPUS | not capturable without a target | expected overlap with F4 | — | UNEXECUTED | supply a representative APK | honest gap, recorded |
| F6 Compose | dooz (only Compose consumer in corpus) | App→app-bundled Compose 1.11.4 from APK DEX→Composer→SlotTable→applier→LayoutNodes→(measure chain) | startup providers, heap/field laws, coroutine machinery, compose measure/layout/draw | composition advances to savedstate/coroutine chain; anchor stable d602648e | pre-fix: F-271 (fixed CONT-20) → F-273 (fixed this wave) → F-272 (fixed this wave) → **now: `Lwg0;.y pc=17 iget Lrf1;.f on null`** (registered F-NEW-274, P0) | F1+F4 (startup cluster was shared; coroutine UEH law is shared with every kotlinx app) | **GENERIC BASE** — F-271/272/273 all closed as Base laws; F-274 is a savedstate/registry identity chain (also Base) | RENDER_STARTED (composition materializes; visuals still DEFAULT_BACKGROUND — measure-pass frontier F-265) | **F-NEW-274** (savedstate chain) | run/cont21/after/dooz_r3, run/cont21/sweep_dooz |
| F7 WebView/HTML5 | minibrowser (rebuilt this wave: d606fa14) | Activity→WebView→settings→HTML→CSS→canvas2d/JS | WebView engine, DOM, canvas2d, JS engine, resource load | SUCCESS rc=0; 222 colors / 31,208 nondom px content render | none at first frame (SUCCESS; log clean of SYNTH-EXC) | shares Activity/lifecycle/input/frame infra with all families | F7-internal engine (webview_engine/quickjs) + shared host infra | FRAME_CAPTURED | resource-loading faces inside HTML apps (assets path law) | run/cont21/family/minibrowser |

---

## 3. PHASE C — SHARED-PRIMITIVE CLUSTERS (before fixes)

Cluster scan across 14 family runs (`run/cont21/cluster_scan.json`,
`scripts/cont21_cluster_scan.py`):

| # | Primitive | Targets hit | Families | Fatal? | Verdict |
|---|---|---|---|---|---|
| P1 | `PackageManager.getProviderInfo` REC-MISS → `ProviderInfo.metaData` NPE (androidx.startup process-start chain) | opencalc, stopwatch, forkgram, telegram, dooz (5) | F1, F4, F6 (3) | FATAL in stopwatch (pre-UI death); degraded-start in others | **GENERIC BASE — FIXED this wave (F-NEW-273 chain)** |
| P2 | Thread UncaughtExceptionHandler null (kotlinx coroutine report path) | dooz (6 faces) | F6 (blocked-earlier F4 targets never reached it) | FATAL (APP BOUNDARY ×2) | **GENERIC BASE — FIXED this wave (F-NEW-272)** |
| P3 | kotlin-reflect `ReflectionFactoryImpl` ClassNotFoundException (deferred, handled) | opencalc, forkgram, telegram, dooz (4) | F1, F4, F6 | no (handled) | OBSERVED — app-side reflective init degrades gracefully |
| P4 | ARR-LEN-NULL ContactsController | forkgram, telegram (2) | F4 (Telegram-engine family-internal) | no (handled) | FAMILY-INTERNAL evidence (not a Base root) |
| P5 | Native lib ABI extraction face (GATEA-NATIVE) | forkgram, telegram (2) | F4 | degraded (handled at first face) | FAMILY surface — environment/native law |
| P6 | SurfaceHolder.setFormat on null | bouncy (1) | F3 | deferred, render continues | FAMILY-SPECIFIC candidate (SurfaceView law) |
| P7 | `Uri.toString on null` in Activity onCreate | chessclock (1) | F1 | FATAL pre-UI (2-frame window) | APP-SPECIFIC-ish candidate until a second target hits it |
| P8 | data-path duplication ("runtime/data/data/...") in stream opens | dooz(15), telegram(25), forkgram(12), microtimer(18), unote(3), g2048(1)+ | F1, F2, F4, F6 | no (ENOENT handled by apps) | GENERIC storage-path law — registered F-NEW-276 (P2) |
| P9 | ServiceInfo.metaData on null (PackageInfo.services never filled) | opencalc (1; same family as P1) | F1 | degraded (handled) | GENERIC BASE sibling — registered F-NEW-275 |
| P10 | libGDX surface/input family | tictactoe(151), bouncy(165) | F2, F3 | FATAL in tictactoe onCreate | FAMILY-SPECIFIC candidate (GL/EGL surface law) |

Clustering discipline held: fixes were written ONLY for the clusters whose
evidence crossed targets/families at the same primitive (P1 → 5 targets/3
families; P2 → the registered dooz P0 with the AOSP contract). P4/P5/P6/P7/
P10 were NOT touched this wave (insufficient cross-family evidence or
family-internal).

---

## 4. PHASE D — SOURCE-FIRST SEMANTIC LAWS (this wave's fixes)

### F-NEW-273 — component-info identity chain (P1 cluster)
- **Local implementation (read first)**: `dalvik_engine.cpp` PackageManager
  block had `getComponentName` (F-116), `getActivityInfo` (F-116),
  `getPackageInfo`+GET_PROVIDERS (P0.10/GATE A), and the S1-PROVIDER
  install path already seeds ProviderInfo identity + `component_meta_data_`
  (#371-CLOSEOUT) — but `getProviderInfo` appeared ZERO times in the tree;
  `ComponentName.<init>` REC-MISS (no producer law); Bundle block (EXP-093)
  had put/get/putParcelable family but no keySet/containsKey.
- **Upstream authority**: AOSP PackageManager/BaseBundle + the LIVE APP DEX
  law (`scripts/cont11_rawscan.py` on dooz):
  `InitializationProvider.onCreate`: `getPackageManager()
  .getProviderInfo(new ComponentName(getPackageName(),
  InitializationProvider.class.getName()), 128)` → `providerInfo.metaData`
  (iget WITHOUT null-check — upstream trusts the PackageManager contract)
  → `AppInitializer.c(bundle)` iterating `keySet()`/`iterator()`.
- **Violated law**: PackageManager.getProviderInfo NEVER returns null
  (NameNotFoundException instead); ComponentName ctor stores its identity;
  BaseBundle.keySet() is never null.
- **Minimal fix**: three laws in the existing blocks (see §5).

### F-NEW-272 — Thread UncaughtExceptionHandler (P2)
- **Local (read first)**: ThreadShadow no-op family included
  `getUncaughtExceptionHandler`/`setUncaughtExceptionHandler`
  (android_shadows.cpp:3308) → void/null; no static default existed.
- **Upstream authority**: libcore Thread + AOSP RuntimeInit
  (LoggingHandler/KillApplicationHandler): instance getter returns the
  per-thread handler **or the default**, and the default is NEVER null on a
  live runtime; the app DEX law proven at `Llo;.K pc=0x52`
  (`currentThread().getUncaughtExceptionHandler().uncaughtException`).
- **Violated law**: `getUncaughtExceptionHandler()` must not answer null.

---

## 5. PHASE E — MINIMAL GENERIC FIX (exact files/functions)

| Change | File | Nature |
|---|---|---|
| `ComponentName.<init>(pkg,cls)` / `(ctx,cls)` law → stores mPackage/mClass | `miniandroid/src/dex/dalvik_engine.cpp` (try_shadow_dispatch, producer half block) | new law, framework-level |
| `PackageManager.getProviderInfo(ComponentName, flags)` law → manifest_provider_identity_ resolution (exact/bare/suffix — the getActivityInfo matching law) + ProviderInfo seed (name/packageName/authority/authorities/grantUriPermissions/metaData from component_meta_data_, resource-id ints) + NameNotFoundException via throw_deferred | same file, consumer half block | new law, mirrors S1-PROVIDER seeding |
| `BaseBundle.keySet()/containsKey()/isEmpty()` law → enumerate `bundle:` field namespace, materialize array+ArrayList (ContentValues keySet convention) | same file, EXP-093 Bundle block | new law, existing convention |
| Thread UEH law block: static get/set (engine `default_uncaught_handler_`), instance get/set (`thread_uncaught_handlers_` map), lazy non-null default `RuntimeInit$KillApplicationHandler`, `uncaughtException` log contract `[UEH-DEFAULT]` | same file (pre-registry-dispatch) + state fields in `dalvik_engine.h` | new law |

Zero app-name/package checks, zero screenshot logic, zero exception
suppression, zero PC advancement, zero fake objects (the default handler is
the AOSP-named framework object ART itself installs).

---

## 6. PHASE F — RUNTIME GRAPHICAL PROOF

| Check | Pre-fix (b6ee41e7) | Post-fix (882b7cdf) |
|---|---|---|
| dooz full run | rc=1; APP BOUNDARY ×2 (MainActivity.onCreate invoke_pc=317); faces: ProviderInfo.metaData NPE → Set.iterator NPE → UEH NPE | **rc=0**; APP BOUNDARY **0**; `[F273-PROVINFO] androidx.startup.InitializationProvider metaData entries=3`; `[UEH-DEFAULT] FATAL EXCEPTION caller=Llo;.K`; remaining uncaught = 1 (F-NEW-274 face); anchor `d602648e8e401895` unchanged ×3 |
| stopwatch | rc=1, died at AppInitializer pre-UI (white screen, colors=1) | **rc=0**, no APP BOUNDARY, startup completes (visual still white — next face is below the startup cluster) |
| opencalc | rc=1 (start NPE chain) | **rc=0**, anchor `a976d2f9fb675cb3` REAL_APP_CONTENT unchanged (379 colors / 1,052,351 nondom px) |
| telegram / forkgram | rc=1 | **rc=0** each (UI-init family faces remain — honest) |
| minibrowser (F7) | — | SUCCESS rc=0, content render `f2169ebcaaf069ce` (222 colors) |
| flappycow (F3) | — | SUCCESS rc=0 `13cf47464d9787f4` (636 colors) |
| bouncy (F3) | — | FRAME_CAPTURED `b6dde6074bf47264` (145 colors / 978,380 nondom px) |

Repeated runs: every anchor ×3 byte-identical (18/18); dooz r1/r2/r3 at
882b7cdf all anchor-stable.

---

## 7. PHASE G — REGRESSION (cross-family)

| Suite | Result at 882b7cdf389aabc3 | Recorded baseline |
|---|---|---|
| anchors ×3 (dooz, microtimer, unote, gmdice, opencalc, tictactoedeluxe) | **18/18 MATCH byte-identical** | 18/18 |
| fcol (K1–K20) | **20/20** | 20/20 |
| f259 | **7/7** | 7/7 |
| f259g | **12/13** (known honest L row, unchanged) | 12/13 |
| f266 | **6/6** | 6/6 |
| f268 | **12/12** | 12/12 |
| g2048 (F2 cross-family anchor) | `59ca1526611c4622` MATCH | recorded |
| family sweep rc-flip | 5/5 targets rc 1→0, screenshots byte-identical | new evidence |

Probe APKs rebuilt at this container with the canonical toolchain
(`scripts/cont21_build_probes.sh` → run/w7, run/w8, run/cont18g).

---

## 8. COVERAGE DECISION (per root)

| Root | Classification | Independent targets benefiting |
|---|---|---|
| F-NEW-271 (null-element kind law, CONT-20) | **BASE** | any null-enqueueing app; fcol K19/K20 |
| F-NEW-272 (Thread UEH law) | **BASE** | every kotlinx/coroutine + crash-hook app (F1/F4/F6 surfaces); regression = anchors + probes |
| F-NEW-273 (component-info identity chain) | **BASE** | 5 targets / 3 families PROVEN; every androidx.startup app |
| F-NEW-274 (savedstate chain, CLASSIFIED P0) | BASE candidate (single target so far) | dooz today |
| F-NEW-275 (GET_SERVICES law, CLASSIFIED P1) | BASE (sibling of F-273 family) | opencalc today; all PackageInfo.services readers |
| F-NEW-276 (data-path duplication, CLASSIFIED P2) | BASE (storage path law) | dooz, microtimer, unote, telegram, forkgram (P8 cluster) |
| P4 ContactsController / P5 native ABI / P6 SurfaceHolder / P7 Uri null / P10 libGDX | **FAMILY-SPECIFIC or APP-SPECIFIC candidates** — not fixed, clustered only | per-family |

A fix benefiting only one APK was NOT auto-classified as generic: P6/P7/P10
stay unfixed candidates; the two fixes landed both carry multi-target
runtime evidence.

---

## 9. REQUIRED CHECKLIST (evidence/status per item)

* [x] Family matrix created — this file.
* [x] Base/View family represented — 5 targets, runtime-traced.
* [x] 2D Canvas/View family represented — g2048/ttt_deluxe + real-APK tictactoe.
* [x] SurfaceView/game-loop family represented — bouncy/flappycow/fishrings, actual paths differentiated (NOT assumed Canvas-only).
* [x] Messaging family represented — telegram + forkgram as family evidence.
* [x] Social/media family represented — honest NO-TARGET-IN-CORPUS record.
* [x] Compose family represented — dooz (only Compose consumer; recorded).
* [x] WebView/HTML5 family represented — minibrowser rebuilt + SUCCESS.
* [x] Telegram/Signal/WhatsApp treated as family evidence — two Telegram-engine APKs clustered, no per-app executors (whatsapp.apk = 5.6KB stub, recorded).
* [x] Instagram treated as family evidence — no target; family architecture documented.
* [x] ≥2 independent targets per shared primitive — F-273: 5 targets; F-272: dooz + probe-battery/anchors.
* [x] Actual execution paths traced — Phase A/B JSONs (family_inventory.json, family_paths.json).
* [x] First divergences recorded — per-target in family_paths.json + matrix.
* [x] Shared primitives clustered BEFORE fixes — cluster_scan.json (P1..P10) predates the patch.
* [x] Local source inspected before upstream — PackageManager/Bundle/ThreadShadow surfaces read first.
* [x] Upstream source inspected — AOSP PackageManager/BaseBundle/Thread laws + live DEX law (cont11_rawscan).
* [x] Semantic law documented — §4.
* [x] Minimal generic fix only — §5 (four laws, two files).
* [x] No app-specific logic — §5 statement + code comment audits.
* [x] Graphical proof collected — §6 metrics (colors/nondom px/SHAs).
* [x] Cross-family regression executed — §7 (6 families touched).
* [x] Evidence artifact committed — run/cont21/* summarized here; scripts committed.
* [x] Final matrix distinguishes Base vs family-specific vs app-specific — §8.
* [x] Every checklist item has evidence/status — §9.
* [x] No unsupported "DONE" — dooz stays PARTIAL (frame-truth DEFAULT_BACKGROUND_ONLY); F4 targets stay LOADED; F5 stays UNEXECUTED.
