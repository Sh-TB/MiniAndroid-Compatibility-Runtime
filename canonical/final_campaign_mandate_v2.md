# FINAL GENERIC RUNTIME COMPATIBILITY CAMPAIGN — MANDATE V2 (user directive, 2026-10-02)

## STANDING LAW S-REPORT (user-set, IRREVOCABLE)

Every work session MUST end with a status table that enumerates EVERY item of the
active work list with: DONE / PARTIAL / NOT-STARTED counts and the exact remaining
items. Skipping items silently is FORBIDDEN — the user must never be left believing
the list is complete when it is not. The report is delivered in-chat AND appended
to worklog.md at session end. This law applies to every future session of this
campaign, no exceptions.

## WORK LIST (v2 — 22 items)

Items 1–20 = FINAL GENERIC RUNTIME COMPATIBILITY CAMPAIGN phases 0–20 (phase 0–2
DONE, phase 3 waves 1–2 DONE, wave 3 = F-NEW-173 frontier pending; see worklog).

Item 21 (NEW, user-supplied verbatim mandate): STRICT SECOND-LAYER AUDIT of
`miniandroid/src/runtime/execution_engine.cpp` — source-first
(SOURCE → AOSP law → exact divergence → generic fix → runtime test → 3-run proof).
Zero APK-specific branches, zero class-name hacks, zero screenshot-specific
exceptions. Sub-items:

- 21-P0-1 Authoritative window/render root (remove `last_set_params_view()`,
  `SmsView`, `PhoneView` heuristics ~2757–2823). First-divergence diagnostic
  proving Window→DecorView→content root→ViewTree→draw. Same root law for render
  + tap + swipe + dialogs + final capture.
- 21-P0-2 No SUCCESS without authoritative content root (~4693
  `if (!result.content_view) ... return true;`). Distinguish: no app window /
  window empty / ViewTree but zero app pixels / real app pixels / chrome only.
  Rootless fixture must NOT produce RENDER_OK; trace_summary names first
  missing stage.
- 21-P0-3 No synthetic fallback from REAL_DALVIK render (~4683–4716). Real
  renderer exception = honest failure; framebuffer discarded if partially
  mutated; synthetic `api::View` renderer only in isolated non-authoritative mode.
- 21-P0-4 No host lifecycle fallback in REAL_DALVIK (~1458–1474 HOST_SHORTCUT
  onCreate/onStart/onResume). Missing DEX lifecycle = PARTIAL/BLOCKED with first
  divergence. Check double-lifecycle. 3-run identical lifecycle event counts.
- 21-P0-5 Diagnostic placeholders NEVER in authoritative frame ("custom view
  (not rendered)", "IMG?", "IMG", grey boxes ~3740–3845, ~4123–4144,
  ~4516–4597). AUTHORITATIVE vs DIAGNOSTIC frame separation; verdict marks
  region UNRENDERED; screenshot.png zero placeholder pixels; trace_overlay.png
  may contain them; authoritative SHA independent of overlay SHA.
- 21-P0-6 Fix false RENDER_OK / false REAL_APP_CONTENT (~4896–4930 color
  statistics). Pixel ownership: SYSTEM_CHROME / AUTHORITATIVE_APP_CONTENT /
  DIAGNOSTIC_OVERLAY. RENDER_OK requires correlated proof (valid root, MEASURE
  reached, LAYOUT reached, DRAW reached, app-owned draw op, pixels in app
  content region). "nonwhite" is never the primary truth signal.
- 21-P0-7 No silent ViewTree truncation (MAX_NODES=500, depth>20 skip). Cycle
  detection + configurable budget + explicit budget-exhaustion state. Report
  nodes_visited/nodes_skipped/depth_max/budget_exhausted/unreachable_children.
  Budget hit = PARTIAL/BLOCKED, never clean SUCCESS.
- 21-P0-8 Compose/WebView frame pump per frame (~5497 pump_compose_frames
  called once). Per boundary: virtual clock, Choreographer callbacks, Handler
  queue, resumed Compose work, WebView JS/rAF tick, yielded work, lifecycle
  transitions, render, capture. One canonical frame pump.
- 21-P1-1 Remove hard-coded +30px root status-bar offset (~4420 depth==0
  cursor_y+=30). Insets geometry from authoritative window.
- 21-P1-2 Eliminate two layout truths (ResourceRuntime::inflater().measure_layout
  vs local heuristic measure_node). One canonical measure/layout source;
  programmatic trees through framework-semantic measurement; no BitmapFont
  second geometry truth.
- 21-P1-3 Remove `w>40 && h>40` custom-onDraw gate (~3643–3647).
- 21-P1-4 `drew_real=true` only on real canvas ops / decoded pixels (~3780–3800).
- 21-P1-5 Apply translation AFTER measured geometry (~3034–3046). Canonical
  order: measured bounds → translation → scroll → clip → draw.
- 21-P1-6 Preserve ancestor scroll clips through descendants (RenderTask clip
  recreation). Render clip == input hit-test geometry.
- 21-P1-7 Tap/swipe same root law (tap effective_content_root_() vs swipe
  activity_shadow->content_view_id()).
- 21-P1-8 PNG requested + PNG failed = capture failure, no PPM silent fallback
  as authoritative artifact (stage_capture_output).
- 21-P1-9 Remove "blank enough" (nw<5000) placeholder screen gate from
  authoritative rendering entirely.
- 21-REG Regression retests after renderer fixes: (1) field identity
  reflection/Unsafe == DEX iget/iput identity; (2) StandardCharsets platform
  statics + clinit honesty; (3) MOVE_OBJECT_16 32x width/PC; (4) 16-bit
  register file (access/wide/invoke-range/param write); (5) written_bits_
  diagnostics-only proof or dynamic resize; (6) F-NEW-173 frontier continuation
  (RegularImmutableMap/create F084), no Guava-specific patch.

Item 22 = FINAL 21-section deliverable report + session-end status tables
(S-REPORT law) for the remainder of the campaign.

## ACCEPTANCE GATE (per fix, verbatim user mandate)

laws/rules read first · exact source/API law identified · generic implementation ·
targeted unit/law test · runtime test · 3 identical runs · screenshot SHA ·
first-divergence trace · ViewTree provenance · no diagnostic pixels in
authoritative screenshot. Classification vocabulary: IMPLEMENTED / TESTED /
OBSERVED / PARTIAL / BLOCKED / PENDING / SUPERSEDED. No issue closed merely
because PNG exists, rc=0, DEX parsed, instructions>0, frame nonwhite, or
"agent says rendered". Visual success = REAL WINDOW ROOT → REAL VIEWTREE →
MEASURE → LAYOUT → DRAW → APP-OWNED PIXEL PROVENANCE → AUTHORITATIVE PNG →
3-RUN REPRODUCIBILITY. After each fix: re-run target, identify NEXT first
divergence, continue until blocker provably outside execution_engine.cpp.
