# CONT-21 — Issue #384 ARCH-001 Execution Family Matrix wave report

Binary lineage: `b6ee41e77acb88ec` (CONT-20) → **`882b7cdf389aabc3`**.
Registry: 581 → **585** (F-NEW-272 → ROOT-CAUSED-FIXED; F-NEW-273
ROOT-CAUSED-FIXED; F-NEW-274/275/276 CLASSIFIED). Queue counts refreshed by
`scripts/findings_queue.py` protocol. Matrix:
`evidence/cont21/EXECUTION_FAMILY_MATRIX.md`.

## A — Family Matrix

14 representative APKs inventoried across 7 families (sha256/package/
version/ABI/actual-path recorded in `run/cont21/family_inventory.json`;
paths runtime-traced in `run/cont21/family_paths.json`):
- F1 Base/View: opencalc, stopwatch, chessclock, unote, microtimer
- F2 2D Canvas/View: g2048, tictactoe_deluxe, real-APK tictactoe (libGDX)
- F3 SurfaceView/game-loop: bouncy, flappycow, fishrings
- F4 Messaging: telegram (12.10.5, x86_64-capable), forkgram (12.10.8, arm64)
- F5 Social/media: no target in corpus — honest NO-TARGET record
- F6 Compose: dooz 23
- F7 WebView/HTML5: minibrowser VC2 rebuilt this wave (`d606fa140bc2aad4`)

## B — First Divergences (one per representative, runtime-captured)

| Target | First divergence at wave start (pre-fix binary) |
|---|---|
| opencalc | ProviderInfo.metaData iget-null (androidx.startup; then ServiceInfo sibling) — startup continues via compat mode; REAL_APP_CONTENT kept |
| stopwatch | AppInitializer.discoverAndInitialize pc=34 iget ProviderInfo.metaData on null → APP BOUNDARY (white screen) |
| chessclock | `Uri.toString on null` in ChessClock.onCreate (input-URI face) |
| unote / microtimer | none (SUCCESS; anchors byte-identical) |
| tictactoe (real) | libGDX GLSurfaceView20.setPreserveEGLContext NoSuchMethod → AndroidInput null → onCreate death |
| g2048 / ttt_deluxe | none (REAL_APP_CONTENT anchors ×3) |
| fishrings | Splash Timer 5000ms scheduling face (classified CONT-8; not a render root) |
| flappycow | none (SUCCESS; StartscreenView render 636 colors) |
| bouncy | SurfaceHolder.setFormat + Iterator.hasNext null (deferred; render continues) |
| forkgram | ProviderInfo.metaData (shared cluster) → GATEA-NATIVE ABI face → Telegram UI init d6$w.c |
| telegram | ProviderInfo.metaData (shared cluster) → Ll9/j; APP BOUNDARY + GATEA-NATIVE |
| dooz | F-271(fixed) → ProviderInfo.metaData → Bundle.keySet Set.iterator NPE → F-272 UEH NPE (each closed in sequence this wave) |
| minibrowser | none (SUCCESS) |

## C — Shared Primitive Clusters

P1 component-info identity chain (5 targets / 3 families — FIXED as
F-NEW-273); P2 Thread UEH null (FIXED as F-NEW-272); P3 kotlin-reflect
(handled, observed); P4 Telegram ContactsController (family-internal);
P5 native-ABI extraction face (family); P6 SurfaceHolder (family
candidate); P7 Uri null (single-target candidate — NOT fixed); P8
data-path duplication (storage law — F-NEW-276); P9 ServiceInfo.metaData
(sibling — F-NEW-275); P10 libGDX surface/input (family candidate).

## D — Source/Semantic Law

1. F-273 chain: local PackageManager block read first (getActivityInfo/
   getPackageInfo/S1-PROVIDER/component_meta_data_ all present;
   getProviderInfo absent); live DEX law disassembled from dooz
   (getProviderInfo(cn,128) → iget metaData → keySet/iterator); AOSP laws:
   getProviderInfo never-null + manifest identity + metaData under
   GET_META_DATA; BaseBundle.keySet never-null; ComponentName ctor identity.
2. F-272: local ThreadShadow no-op family read first; upstream libcore
   Thread + RuntimeInit (KillApplicationHandler non-null default; instance
   getter falls back to default); app DEX law at Llo;.K pc=0x52.

## E — Fix

`miniandroid/src/dex/dalvik_engine.cpp` (+ one state field block in
`dalvik_engine.h`): four laws — (1) ComponentName.<init> identity;
(2) PackageManager.getProviderInfo + ProviderInfo seed + NameNotFoundException;
(3) BaseBundle keySet/containsKey/isEmpty; (4) Thread UEH family with
non-null lazy default + per-thread map + `[UEH-DEFAULT]` log contract.
All framework-level, zero app checks. Diagnostics: `[F273-PROVINFO]`,
`[UEH-DEFAULT]` (both bounded).

## F — Runtime Proof

dooz: rc 1→0; APP BOUNDARY 2→0; startup chain `[F273-PROVINFO] ... metaData
entries=3`; `[UEH-DEFAULT] ... caller=Llo;.K`; anchor d602648e8e401895
unchanged (visual frontier honestly still F-265 measure-pass chain +
F-NEW-274 face). stopwatch rc 1→0 (startup fatal face gone). opencalc/
telegram/forkgram rc 1→0 with byte-identical screenshots. minibrowser
SUCCESS (222 colors); flappycow SUCCESS (636 colors); bouncy FRAME_CAPTURED
(145 colors / 978,380 nondom px).

## G — Regression

anchors 18/18 ×3 byte-identical; fcol 20/20; f259 7/7; f259g 12/13 (known
honest L); f266 6/6; f268 12/12; g2048 REAL_APP_CONTENT anchor match; probe
APKs rebuilt canonically at this container (scripts/cont21_build_probes.sh).

## H — Coverage Decision

BASE (fixed): F-NEW-271 (CONT-20), F-NEW-272, F-NEW-273.
BASE candidates (registered, unfixed): F-NEW-274 (single-target so far),
F-NEW-275 (sibling family law), F-NEW-276 (multi-target storage law).
FAMILY-SPECIFIC/APP-SPECIFIC candidates (clustered only, NOT fixed):
ContactsController (Telegram-engine), native-ABI extraction, SurfaceHolder
identity, chessclock Uri null, libGDX surface/input.

## I — Remaining Work (evidence-backed next roots only)

1. **F-NEW-274 (P0)**: dooz `Lwg0;.y pc=17 iget Lrf1;.f on null` —
   savedstate/coroutine chain; the sole remaining uncaught face in dooz.
2. **F-NEW-275 (P1)**: PackageInfo GET_SERVICES law (opencalc sibling face).
3. **F-NEW-276 (P2)**: data-path duplication (P8 cluster; microtimer/
   unote/telegram/forkgram/dooz logs).
4. F-265 measure-pass completion chain (place-writers) — still the dooz
   visual gate; F-267 tap bridge behind it.
5. Family-level: SurfaceView identity law (bouncy), libGDX surface/input
   (real-APK F2), native-ABI extraction law (F4), chessclock input-URI face.

Honest status vocabulary: dooz = PARTIAL (RENDER_STARTED; frame-truth
verdict DEFAULT_BACKGROUND_ONLY); F4 targets = LOADED (rc 0, UI not
materialized); F5 = UNEXECUTED (no target); F1/F2/F3/F7 anchors = 
FRAME_CAPTURED / REAL_APP_CONTENT as recorded.
