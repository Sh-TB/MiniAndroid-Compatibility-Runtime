# Compose Study — the Compose boundary as seen by a userspace runtime

Scope: what MiniAndroid needs to know about Jetpack Compose to run apps
that use it (corpus evidence: dooz = Compose Tic-Tac-Toe), NOT a study of
Compose internals for their own sake.

Sources: androidx references in `master_repos.txt` (androidx/compose
multiplatform, skiko); AOSP frameworks/base RenderNode/RecordingCanvas
(mirror `1cdfff55`); MiniAndroid compose shadows and dooz evidence from
prior campaigns (`docs/campaign014_evidence/dooz/`, COMPOSE_REPORT_013.md).

## CMP-001 — The only boundary an APK runtime sees
ComposeView → AndroidComposeView → (ViewTreeLifecycleOwner /
ViewTreeSavedStateRegistryOwner) → Compose runtime → RenderNode-recording
canvas. An out-of-Android runtime intercepts at exactly three points:
1. view-tree construction must tolerate unknown subclass names
   (`androidx.compose.ui.platform.ComposeView`,
   `AndroidComposeView`) — instantiate via base-class shadows;
2. owner/registry attached properties (lifecycle, saved-state) must
   exist as no-op-compatible shadows;
3. draw calls arrive through Canvas/RenderNode recording — accept and
   collapse to immediate software draws (see GFX-003).
- MiniAndroid status: point 1/2 shadows implemented (dooz launches and
  renders through the chain); point 3 partial (property setters accepted,
  no-op). The dooz depth question (how far into Compose semantics we can
  drive input/state/redraw) remains the open frontier — same conclusion as
  prior campaign, now with the boundary model documented.

## CMP-002 — Recomposition makes frame-diff testing hostile
Compose redraws by invalidating composition, not by Activity state
callbacks; pixel diffs alone cannot distinguish "state updated" from
"recompose loop". The reliable observable for interaction testing on
Compose apps is the API-trace (which shadow methods fired) + frame hash,
not the frame alone.
- MiniAndroid action: keep `api_trace.json` as the compose-app interaction
  evidence channel (it already is: dooz click evidence is trace + frames).
- Status: VERIFIED methodology.

## CMP-003 — GraphicsEnvironment parity targets are RenderNode properties
Corpus Compose apps commonly set: alpha, translationX/Y, clip bounds,
outline/clipToOutline. MiniAndroid shadow coverage should be prioritized
by THIS list (not by full RenderNode surface).
- Status: DISCOVERED (coverage priority list recorded).
