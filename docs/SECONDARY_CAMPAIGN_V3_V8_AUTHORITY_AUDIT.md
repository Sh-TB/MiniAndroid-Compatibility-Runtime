# SECONDARY CAMPAIGN PHASES V3 + V8 — ONE AUTHORITATIVE LAYOUT & RENDERER DUPLICATION

Campaign: SECONDARY · Date: 2026-10-02 · Base: HEAD 67064b95
Directive: determine which path OWNS authoritative geometry; no two
independent layout engines may rewrite the same ViewNode geometry; every
legacy/synthetic renderer classified REFERENCE_ONLY or DIAGNOSTIC_ONLY.
Do not blindly delete existing code — first prove which path real APK
execution uses.

---

## §1 V3 — Layout authority census (source-audited)

Candidate authorities enumerated by the directive, with measured reality:

| # | Candidate | Verdict | Evidence (call-graph audit) |
|---|---|---|---|
| 1 | **LayoutInflater::measure_layout** (resources/layout_inflater.cpp:3412) | **AUTHORITATIVE** — the ONLY layout engine that runs during real APK frames | Sole measure entry invoked by stage_render_frame_impl (execution_engine.cpp:3073 `rt.inflater().measure_layout(view_shadow, root_id)`), gated by `rt.loaded() \|\| view_shadow->layout_dirty \|\| inflated_attach_consumed` (R-NEW-302 re-measure law + 21-P0-1 attach-before-measure law). Sets census `measure_ran/layout_ran/layout_source="inflater"`. |
| 2 | ViewShadow layout (framework/android_shadows.cpp) | **STATE STORE, not an authority** | ViewNode carries measured_left/top/width/height + laid_out; writers = measure_layout + the layout()-dispatcher (dispatch_view_lifecycle_once). No independent pass walks the tree and rewrites geometry. |
| 3 | ViewRenderer::measure_view/layout (renderer/view_renderer.cpp:72) | **DEAD CODE — REFERENCE_ONLY** | `grep ViewRenderer` across src/ = ZERO call sites outside its own files; view_renderer.h included by NOBODY. Historical EXP-122 semantics. Deletion gated by no-blind-delete law; classified REFERENCE_ONLY this wave. |
| 4 | custom View onMeasure (DEX) | **SUB-AUTHORITY inside #1** (by design, not duplication) | measure_view_spec dispatches the REAL DEX override via custom_view_measure_hook_ (F10/R-NEW-347); R-NEW-438 incomplete-emulation + arm-2 contract laws make the native law the fallback — one negotiation per node per pass, no second engine. |
| 5 | custom View onLayout (DEX) | **NOTIFY-ONLY** | dispatch_view_lifecycle_once (execution_engine.cpp:3236) runs the DEX onLayout with final geometry AFTER the authoritative pass — it observes; it cannot re-anchor the walk (21-P1-5 law: walk positions come from measured geometry + ancestor deltas). |
| 6 | ResourceRuntime measure/layout | **SAME ENGINE as #1** | ResourceRuntime::inflater() IS the LayoutInflater of #1 — not a separate implementation. |
| 7 | software_renderer.h LayoutNode/LayoutBounds structs | **UNUSED TYPES** | grep: only comment references (dalvik_engine LayoutNode hits are the COMPOSE app-side LayoutNode DEX classes, unrelated). |

**Census layout_source field** records "inflater" on every canonical pass;
"programmatic" trees still measure through #1 (the R-NEW-302 dirty gate).

**Residual risk (recorded, not fixed this wave):** the F-096 one-time DEX
measure+layout lifecycle dispatch at draw-visit time is a SECOND onMeasure
entry point (per-view, memoized "once"). It is contractually downstream of
#1 (specs = the laid-out rect) and memoization prevents oscillation, but it
remains the only other writer of ViewShadow measure state. Registered as
follow-up audit note V3-R1.

## §2 V8 — Renderer duplication census (source-audited)

| Path | Can it produce a screenshot? | Reachable from cmd_run? | Classification |
|---|---|---|---|
| ExecutionEngine::stage_render_frame + stage_capture_output (runtime/execution_engine.cpp) | YES — authoritative framebuffer + PNG + verdict + census | **YES — THE path** (main.cpp cmd_run → ExecutionEngine) | **AUTHORITATIVE** |
| renderer/software_renderer.cpp | Provides PRIMITIVES (FrameBuffer, SoftwareCanvas, BitmapFont, PNGWriter) consumed by the authoritative path; no independent driver | Shared substrate | **SUBSTRATE** (not a competing renderer) |
| renderer/view_renderer.cpp (ViewRenderer) | Owns no framebuffer writes (no call sites at all) | NO (zero call sites) | **REFERENCE_ONLY** (classified this wave) |
| runtime/application_runtime.cpp (ApplicationRuntime::save_screenshot/render_pipeline_) | YES — legacy exp00x entry points only | NO — cmd_run never constructs ApplicationRuntime (grep: main.cpp uses ExecutionEngine; ApplicationRuntime referenced only in comments/history) | **REFERENCE_ONLY** (legacy EXP runtime) |
| synthetic api::View renderer | painted placeholders historically | Suppressed in REAL_DALVIK (21-P0-3, verified live: WhatsApp frame fake band GONE) | **DIAGNOSTIC_ONLY** (legacy demo mode keeps historical behavior, explicitly non-authoritative) |
| GLSurfaceView/GL chain (gl_surface_shadow + pgl_backend) | Composites INTO the authoritative framebuffer (record_gl_presented provenance) | Via the same stage_render_frame walk | **AUTHORITATIVE (family branch)** |
| diagnostics/trace_overlay.cpp | Composes a COPY after the authoritative write (separate trace_overlay.png, sha256 != authoritative) | Yes, --trace-ui only | **DIAGNOSTIC_ONLY** (by construction; S135 §24 sha law) |

**Conclusion:** exactly ONE screenshot-producing path is reachable from
`cmd_run` (ExecutionEngine), with one diagnostic copy (TraceOverlay) and two
legacy code bodies (ViewRenderer, ApplicationRuntime) that are UNREACHABLE
and now explicitly classified. No competing verdict can originate elsewhere:
the FrameRenderCensus ledger + record_frame_analysis exist only in
ExecutionEngine.

## §3 Actions taken this wave

1. ViewRenderer + ApplicationRuntime annotated REFERENCE_ONLY in this doc
   (no code deletion — no-blind-delete law; call-graph evidence recorded).
2. The one residual dual-writer risk (F-096 one-time dispatch) registered
   as V3-R1 follow-up with its containment laws stated.
3. Verification: `grep -rn ViewRenderer src/` (zero external call sites),
   `grep -rn ApplicationRuntime src/main.cpp` (comment-only), executed as
   part of this audit session (evidence in worklog V-SECONDARY entry).
