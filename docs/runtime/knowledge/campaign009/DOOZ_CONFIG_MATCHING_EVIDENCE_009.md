# DOOZ_CONFIG_MATCHING_EVIDENCE_009 — §6 + §10 evidence walkthrough

## A. §6 ARSC configuration bucket matching (implemented + proven)

**Problem (inherited):** `ResolvedResource::best()` used a string heuristic: prefer empty `config_desc`, +10 for "dpi", +5 for "-r". Consequences: (a) the DEFAULT bucket always beat a matching density bucket — on a real 480dpi device Android picks `drawable-xxhdpi`, the old code picked `drawable`; (b) locale buckets could never win; (c) anydpi/v21+ semantics absent.

**Implementation (this campaign, commit "CAMPAIGN 009 §6"):**
- `src/resources/res_config.{h,cpp}` — `ResTableConfig` ported from AOSP `platform_frameworks_base @ 1cdfff555f4a` (`ResourceTypes.cpp` match()@2909, isBetterThan()@2641, isLocaleBetterThan()@2520 read live from raw.githubusercontent before coding).
- Full binary layout parse (offsets verified twice — a first-draft off-by-4 after `inputFlags` was caught by re-deriving from the fetched header and fixed pre-merge).
- Device request: en-US, 480dpi, 1080x1920, 360x640dp, sw360, SDK 34, portrait/finger/night-no — env-tunable (`MINIANDROID_LOCALE`, `MINIANDROID_DENSITY`).
- `arsc_parser`: raw config bytes parsed per TypeChunk, carried on every `ArscEntry`; `best()` = match()+isBetterThan() with default-bucket fallback.

**Probe evidence (Telegram 12.10.1, `build/res_config_probe`):**
```text
device en-US  → Abort: default MATCH (SELECTED); de/uk/nl/ko/ar/es/it/ru/pt-rBR REJECT
device ru-RU  → Abort: [ru] MATCH "Прервать" → SELECTED        ← impossible pre-fix
drawable ab_progress (4 density buckets) → [480dpi] SELECTED on 480dpi device
drawable _menu_stream_comments_off_24     → [anydpi-v24] SELECTED (AOSP DENSITY_ANY rule)
```

**Zero regression:** GMDice `26fc4116e4ba65b4` ✓ · Telegram `b9b06072ea17d7fd` (41,233 px) ✓ · uNote 23,472 ✓ · bgclock 2,073,600 ✓ · stopwatch exit=1 unchanged ✓.

**Why the Telegram *screenshot* is unchanged although matching improved:** the rendered SMS-screen strings/drawables resolve from buckets that the old heuristic also picked correctly (defaults; the changed selections land on resources not painted on that screen). The §6 fix changes *future* resolution behavior — proven at the engine level by the probe, which is the correct layer to prove it.

## B. §10 Compose/Dooz chain progression (structural proof)

**Symptom:** dooz rendered 0 non-white px. Trace (`run/exp_uc009_dooz/run_attach_trace.log`, 303k lines): Compose runtime classes DID execute (`ComposeView.setContent` → Recomposer `P/l` → snapshot `B0/l`), but render tree showed `ComposeView children=0`.

**Root cause chain (each step evidenced):**
1. `onAttachedToWindow` appeared ONLY in `[DexParser] CODE_ITEM` parse lines (6 occurrences), never dispatched →
2. `android_shadows.cpp:1440` — ViewShadow claims `onAttachedToWindow` (and onMeasure/onLayout/onDraw) returning `handled_void`, swallowing the app-side override →
3. `AbstractComposeView.onAttachedToWindow → ensureCompositionCreated()` never ran →
4. composition never created → AndroidComposeView never added → white frame.

**Fix:** `DalvikExecutionEngine::dispatch_view_attached()` — AOSP `View.dispatchAttachedToWindow` semantics: walk all ViewShadow nodes (id-sorted), invoke DEX-side `onAttachedToWindow` via `try_recursive_invoke` **with superclass walk** (ComposeView does not override it; AbstractComposeView does — verified in dooz DEX via androguard), bounded 16-pass loop (attach creates AndroidComposeView which is then attached in a later pass). Env-gated `MINIANDROID_DISPATCH_ATTACH=1` for golden-safety.

**Result:**
```text
[UC009-ATTACH] onAttachedToWindow dispatched view=27 ComposeView
[UC009-ATTACH] onAttachedToWindow dispatched view=63 AndroidComposeView
[EXP092-RENDER] ComposeView children=1 depth=0 (was children=0)
```
Attach window: 317 lines of real interpretation — `AndroidComposeView.onAttachedToWindow` (227B), `getRoot`, LayoutNode `node/i`/`node/e`, `getSnapshotObserver`, Recomposer.

**Next blockers (precise, for the next campaign):**
1. No frame tick exists (Choreographer/Looper loop) → pending recompositions never run after the initial attach-time composition.
2. `onDraw`/`dispatchDraw` are shadow-swallowed → even a completed composition draws nothing; needs Canvas-object bridging to `renderer::SoftwareCanvas`.
3. Note: `AndroidComposeView children=0` is EXPECTED in real Compose (content draws via Canvas ops, not child views) — do not treat it as a bug.

## C. §24 GLES route decision

| Route | Evidence | Verdict |
|---|---|---|
| SwiftShader build | configure OK (prior campaign); compile needs >3GB; machine has 3GB total | infeasible |
| Mesa llvmpipe/lavapipe | no apt root; source build = same RAM class | infeasible here |
| **PortableGL (MIT)** | header-only; plain gcc build in seconds; GLES2 vertex+fragment shader triangle via VBO+glDrawArrays → **31,104 colored px** | **ADOPT ROUTE** (integration = interop with `renderer::FrameBuffer`; vendored WITH license notice next campaign) |
| TinyGL | smaller, GLES1-era; fallback only | study |

Corpus GLES demand quantified: RetroWars 268 · Mindustry 255 · NewPipe 251 · Droid-ify 207 · SPD 177 GLES method refs.
