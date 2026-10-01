# S135 — VISUAL RUNTIME BOOT/TRACE LOGGER (canonical document)

> Status: IMPLEMENTED + TESTED (3-run deterministic, goldens byte-identical)
> Architecture decision: **EXTEND** (one backbone on the existing TraceEngine;
> one new sink component for the visual overlay). No duplicate logger.

## 1. What it is

A dual-path runtime observability system for the white/black/grey/blank/stale
screen campaign (S134/S135), independent of the RenderVerificationGate
(the gate is the verdict system; the logger is runtime observability):

1. **Machine-readable runtime logger** — a canonical event stream
   (`trace.jsonl` + `trace_summary.json`) with seq/timestamp/thread/
   component/event/class/method/descriptor/renderer-family/state/
   provenance/result/exception/parent/first-divergence.
2. **Visual On-Screen Runtime Trace** — a semantic-color panel composed
   onto a COPY of the authoritative frame (`trace_overlay.png`), readable
   even when the app itself rendered a white/blank screen.

The question it answers for EVERY run (S135 §2):
> "What EXACTLY produced what I see on screen — and if I see nothing,
> what was the last stage that really executed and where was the first
> stage that should have run but did not?"

## 2. Architecture (S135 §9/§23 law)

```
APP RENDERING  →  AUTHORITATIVE FRAME  →  VISUAL TRACE COMPOSITION  →  SCREENSHOT
(app pixels)      screenshot.png          trace_overlay.png (COPY)     + sha256.json
```

- ONE RUNTIME EVENT BACKBONE = `TraceEngine` (existing, EXP-001) extended
  with `runtime_event()` + sinks. Existing `record_error`/`log_screenshot`
  calls auto-emit canonical events — zero duplicate wiring.
- The overlay NEVER touches the app ViewShadow tree, measure/layout/draw,
  event ordering, the Canvas, or `framebuffer_` (S135 §8 hard rule).
  PROOF: dooz authoritative SHA byte-identical with logger ON and OFF
  (`ba8a95eb2278594f`, = S134 golden).
- The overlay is never an app pixel owner (S135 §27): it composes a COPY
  after the authoritative PNG write; it never fabricates a frame.

## 3. Files

| File | Role |
|------|------|
| `src/diagnostics/runtime_event.h` | canonical event schema + vocabulary (`ev::*`, `rf::*`, stage machine order) |
| `src/diagnostics/trace_engine.h/.cpp` | backbone: ring buffer, JSONL sink, stage machine, FIRST-DIVERGENCE engine, frame analysis, summary |
| `src/diagnostics/trace_overlay.h/.cpp` | visual composer (semantic colors, 8x16 font reuse, custom status glyphs) |
| `src/runtime/execution_engine.cpp` | wiring at existing emission points (boot stages, lifecycle, render, capture) |
| `src/main.cpp` | `--trace` / `--trace-ui` CLI flags |

## 4. Event schema

`RuntimeEvent` (all fields omitted-when-empty in JSON; nothing guessed):

```
seq ts_ms run_id package activity thread component event class method
descriptor renderer_family state provenance result exception parent_event sev extra
```

`extra` carries cross-layer correlation ids (S135 §13): `apk` identity,
`pc`, `view_id`, `bytes`, `path`, census numbers.

Canonical events (curated — only events with real emission points):
`RUN_START RUN_END APK_LOADED APK_LOAD_FAILURE MANIFEST_PARSED DEX_PARSED
DEX_FAILURE RUNTIME_READY CLASSES_LOADED APPLICATION_CREATE ACTIVITY_RESOLVED
ACTIVITY_ATTACH ACTIVITY_CREATE ACTIVITY_START ACTIVITY_RESUME ACTIVITY_PAUSE
ACTIVITY_STOP ACTIVITY_DESTROY LIFECYCLE_STATE SET_CONTENT_VIEW
VIEWTREE_CREATED MEASURE_START MEASURE_END LAYOUT_START LAYOUT_END
DRAW_START DRAW_END RENDER_START RENDER_OK RENDER_FAIL FRAME_SUBMIT
FRAME_CAPTURE FRAME_ANALYSIS SURFACE_CREATED SURFACE_CHANGED
GL_FRAME_PRESENT WEBVIEW_* COMPOSE_FRAME RESOURCE_* EXCEPTION MISSING_API
NATIVE_CALL DISPATCH_FAILURE CLASS_INIT_FAILURE SCHED_STALL TRACE_MARK`

Renderer families (S135 §14): `CLASSIC_CANVAS SURFACE_VIEW OPENGL_GLES
COMPOSE WEBVIEW LIBGDX NATIVE UNKNOWN` — GL surfaces promote
OPENGL_GLES (stage_gl_surfaces), the Compose choreographer pump promotes
COMPOSE, the classic walk defaults CLASSIC_CANVAS.

## 5. Stage machine + FIRST-DIVERGENCE engine (S135 §12)

Canonical boot contract (AOSP order):

```
BOOT → APK → DEX → CLASS-INIT → LIFECYCLE → VIEWTREE → MEASURE → LAYOUT → DRAW → FRAME
```

States: `CONFIRMED / PENDING / FAILURE / NOT_REACHED`. Laws:

- **Walk-through confirmation**: a stage that CONFIRMED proves earlier
  PENDING stages completed (BOOT's RUN_START, the measure/layout legs of
  one render pass). NOT_REACHED earlier stages are NOT promoted — an
  unstarted lifecycle is real evidence.
- **Derivation**: first FAILURE stage in canonical order is the divergence;
  else the first non-CONFIRMED stage while earlier stages confirmed.
- **FIRST_DIVERGENCE != LAST_EXCEPTION** (hard law): exceptions travel as
  `EXCEPTION` events + `first_failure_event`/`last_exception` evidence.
  A run with a completed boot chain and an in-flight exception reports
  NO stage divergence (measured: dooz, 1 uncaught NPE, chain complete,
  REAL_APP_CONTENT — the exception is separate evidence, not the verdict).

## 6. Frame analysis (S135 §7 — default background vs real content)

`record_frame_analysis` computes on the authoritative frame:
dominant color (the default-background candidate — never assumed white),
dominant %, unique colors, **non-default pixels** (pixels differing from
the dominant), verdict `DEFAULT_BACKGROUND_ONLY` (0 non-default) vs
`REAL_APP_CONTENT`, screenshot SHA-256. Measured: droidify renders
`#fafafa`, non-default 0 → DEFAULT_BACKGROUND_ONLY while its boot chain
is green through LIFECYCLE — the logger separates "app failed to produce
pixels" from "runtime failed to boot".

## 7. Visual overlay (S135 §4/§5/§20/§21)

- Semantic colors: GREEN confirmed / YELLOW pending / RED failure /
  BLUE info / PURPLE renderer-provenance / GRAY not reached.
- Custom-drawn status glyphs (✓ ✗ tilde dash) — the ASCII font cannot
  draw ✓/✗; colors are semantic, shapes disambiguate for colorblind eyes.
- Panel rows: header (run/apk/activity/lifecycle) → 10-stage machine with
  per-stage detail → RENDERER → FIRST DIVERGENCE → LAST EVENT → FRAME
  verdict → PIXELS → (expanded: EXPECTED/ACTUAL/LAST OK/NEXT REQUIRED/
  EXCEPTION/LAST CLASS/METHOD + last-N event tail) → TRACE ID footer.
- Modes: `--trace-ui` (=1 default panel), `MINIANDROID_TRACE_UI=header`
  (tiny status strip), `expanded` (full forensic panel).

## 8. Performance (S135 §22)

Default terminal sink prints FAILURE/PENDING + FRAME_ANALYSIS only
(`[TRACE] seq EVENT state=... [FRONTIER]`); `MINIANDROID_TRACE_VERBOSE=1`
prints all. Ring buffer default 512 (`MINIANDROID_TRACE_BUFFER=N`).
Heavy per-opcode/per-draw events stay in their existing env-gated
instruments (InstructionTrace, GfxProvenance) — not duplicated here.

## 9. Evidence bundle (per run, S135 §24)

```
<outdir>/trace.jsonl              streaming canonical events (one JSON/line)
<outdir>/trace_summary.json       stages + first divergence + tail(32) + census
<outdir>/screenshot.png           AUTHORITATIVE (logger-free, byte-stable)
<outdir>/trace_overlay.png        DIAGNOSTIC (panel composed on a copy)
<outdir>/screenshot_metrics.json  frame analysis + both SHAs + law note
<outdir>/sha256.json              AUTHORITATIVE_SHA256 vs TRACE_SHA256
```

`overlay_mutated_authoritative_frame: false` is PROVEN by construction
(compose-after-write onto a copy) and by the dooz byte-identity A/B.

## 10. Enabling

```
miniandroid run --trace-ui -o run/ app.apk        # machine trace + visual overlay
miniandroid run --trace    -o run/ app.apk        # machine trace only
MINIANDROID_BOOT_TRACE=1 MINIANDROID_TRACE_UI=1|header|expanded  # env form
MINIANDROID_TRACE_VERBOSE=1 MINIANDROID_TRACE_BUFFER=512          # optional
```

## 11. Tests executed (S135 §26, all on current HEAD, real APKs)

| # | Case | APK | Result |
|---|------|-----|--------|
| 1 | real render | dooz | chain green ×3, REAL_APP_CONTENT, SHA stable `ba8a95eb2278594f` |
| 2 | successful TextView render | headingcalc | chain green, 823 colors, 466062 non-default px |
| 3 | crash after render | chessclock | chain green + EXCEPTION lane (NPE at app boundary), rc=1 |
| 4 | white screen | droidify | chain green→LIFECYCLE, VIEWTREE NOT_REACHED, DEFAULT_BACKGROUND_ONLY, 0 non-default |
| 5 | two-color blank | WhatsApp | VIEWTREE NOT_REACHED, 2 colors, 23472 non-default px (F-NEW-156 family fingerprint) |
| 6 | pure-Dalvik game | FlappyCow | chain green, 636 colors, CLASSIC_CANVAS (no native libs — family law correct) |
| 7 | missing APK | (nonexistent) | graceful BOOT divergence, no fabricated stages |
| 8 | overlay OFF | dooz | zero trace artifacts, authoritative byte-identical |
| 9 | 3-run reproducibility | dooz ×3 | 56-event sequence IDENTICAL (modulo run_id/ts/pid/out-path), metrics identical |
| 10 | gates | laws130 | 51/51 PASS |
| 11 | goldens | ballbreak/dooz | `8a951f5f975c4742` / `ba8a95eb2278594f` byte-identical to S134 record |

## 12. Font-law fix discovered by the logger (S135 §29 knowledge)

The visual overlay EXPOSED a pre-existing runtime defect:
`bitmap_font_data.h` (EXP-092) shipped 5 CORRUPT glyphs —
`glyph_dot_bitmap` = 16×0xFF (solid block!), `glyph_minus` 3 full rows,
`glyph_E/I/z` corrupted. Every '.' rendered by the BitmapFont path drew
a solid block. Root cause of the corruption pattern: a generator that
tight-crops the ink bbox before scaling turns wide-flat glyphs into an
all-ink cell. FIX (scripts/s135_fix_font_glyphs.py): re-render from the
same source font (DejaVuSansMono) on the FULL CELL (no tight-crop),
LANCZOS downscale to 8x16, threshold <140. Patched glyphs verified by
ASCII-art dump. Golden impact: NONE (dooz/ballbreak byte-identical).

## 13. Limitations / remaining gaps (S135 §31L)

- WebView lane events (WEBVIEW_CREATED/NAVIGATION_START/…) are NOT yet
  individually wired — the WebView path currently surfaces through
  record_error auto-emission + the browser engine's own markers.
  Wiring them into `runtime_event` is mechanical (same pattern).
- SurfaceView-family events fire only when GL surfaces exist
  (stage_gl_surfaces); a non-GL SurfaceView run reports CLASSIC_CANVAS
  honestly (measured: FlappyCow has zero native libs).
- SET_CONTENT_VIEW is observable indirectly (VIEWTREE root_id) — the
  inflater does not yet emit its own event.
- Per-drawChild / per-opcode granularity remains in the existing
  env-gated instruments by design (performance law §22).

## 14. Registry links

- Capability: `S135-BOOT-TRACE-LOGGER` (IMPLEMENTED/TESTED)
- Roots it serves: F-NEW-156 family (WhatsApp VIEWTREE fingerprint),
  next-root droidify VIEWTREE divergence (white screen, 0 non-default px)
- Companion instruments: RenderVerificationGate (verdicts), GfxProvenance
  (pixel chain C7), crash_forensics (native frames) — UNCHANGED, the
  logger does not replace them.
