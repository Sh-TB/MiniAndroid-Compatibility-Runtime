# W21 PLAYABILITY 2048 REPORT — WS4B (DOM mutation → visible repaint) CLOSED

Status: **WS4B RESOLVED** — 2048 (original `com.uberspot.a2048_23`) now produces visible,
repeatable, deterministic board state changes from real swipe gestures, through shared
runtime fixes only. Commit: `c1602b754ddf5d00`.

## 1. The traced chain and the first broken transition

Required chain: `Input event → app callback → state mutation → View invalidation →
layout/draw scheduling → frame pump → rendered output`.

W21 instrumentation (WV_TRACE=1, original APK) found FIVE stacked breaks upstream of the
frame pump — the frame pump itself (vsync tick + per-frame WebView surface blit,
`execution_engine.cpp` `[WV-RENDER]`) and the ViewTree invalidation path were already correct:

| # | Break (measured) | Fix (shared law) |
|---|---|---|
| 1 | **CSS float unimplemented** — `.grid-cell{float:left}` stacked 16 cells vertically; the auto-sized `position:absolute` `.grid-container` collapsed to `106x1741` (the exact residual the independent coder recorded) instead of a 4×4 board. `[WV-LAYOUT] div .grid-container box=305,372 106x1741` | CSS 2.1 §9.5 float/clear: float rows with wrap, `clear` pulls the cursor to the float bottom, floats extend auto height (flex items exempt — CSS Flexbox §4); `measure_w` adds the float-row sum |
| 2 | **transform:translate unimplemented** — every `.tile` rendered at the container origin (tile-position classes are translate-only). `.tile tile-position-1-4 box=305,372` | CSS Transforms: `translate(Xpx,Ypx)` parsed (incl. `-webkit-` twin) into `tf_tx/tf_ty`, applied in `layout_inflow` (children follow; idempotent across 2-pass re-layouts) |
| 3 | **Hit-test miss dropped the gesture** — `touchstart at (540,1300) hit=none` → `pointer_event` returned `false`; 2048's listeners live on `.container` (verified in the APK's `keyboard_input_manager.js`), which is only reachable via the ancestor chain of a HIT node | (partially covered by #1: with the correct 469×469 board, in-board touches hit; off-board touches still target nothing — see limitations) |
| 4 | **W3C implicit capture missing** — a swipe ENDING off-board (`540,700→140,700`, x=140 < board left 290) dropped `touchend` entirely → the game never computed its delta → no move. W3C Touch Events §5.6: every event of a gesture targets the touchstart element | Implicit capture in `WebViewEngine::pointer_event`: `touch_capture` set on touchstart, used as target for touchmove/touchend, released on touchend |
| 5 | **CSS cascade never re-matched** — `HTMLActuator.addTile` first applies the PRE-move class (`positionClass(previousPosition)`), then re-classes to the NEW position in a second rAF; the S114 append-time cascade baked the old transform, so every MOVED tile kept its pre-move position while spawned tiles rendered correctly — the exact "DOM mutates, raster frozen" WS4B symptom | Cascade invalidation: `css_mark_dirty` on classList write / className / setAttribute("class"/"style") / appendChild / removeChild → `apply_css` re-runs before the next paint |

## 2. Acceptance evidence (original APK, `MINIANDROID_WV_CHANGED_TOUCHES=1 MINIANDROID_WV_DRAG_FORWARD=1`)

| Scenario | Command (delta) | screenshot sha16 | Verdict |
|---|---|---|---|
| Launch face (no gesture) | `--frames 12` | `a52c222075d842b4` | baseline |
| LEFT swipe ×3 | `--swipe 540,700,140,700@5` | `271cb5d0ffbe598c` ×3 | **deterministic ×3**, ≠ launch |
| UP swipe | `--swipe 540,700,540,300@5` | `589ffcd793096497` | different board |
| DOWN swipe | `--swipe 540,300,540,700@5` | `03806943ce4606d7` | different board |
| RIGHT swipe (in-board) | `--swipe 350,700,770,700@5` | `56d567f44a4156a7` | different board |
| Off-board (invalid) gesture | `--swipe 540,900,140,900@5` | `a52c222075d842b4` | **unchanged, rc=0** — safe no-op |
| DEFAULT-OFF proof | same LEFT swipe, no env vars | `a52c222075d842b4` | byte-identical pristine |

- Pixel diffs (PIL) between faces cover exactly the moved/spawned tile regions
  (left-vs-launch bbox `(305,405)-(775,633)` = the new tile cell + the spawn cell).
- `Score: 4` badge painted after the move (visible app state, not just tile geometry).
- Layout after fix: `.game-container 500x500 @ (290,269)`, `.grid-container 469x469 @
  (305,284)` — matches the browser geometry.
- Board paints in the app's own night mode (white tiles over gray cells, dark chrome).
- No package-name checks anywhere in the fix (pure CSS/W3C/DOM laws in `webview_engine.cpp`
  + `html_dom.h`).

## 3. Status upgrade (honest scope)

- **Board gameplay: INTERACTIVE** (was NOT PLAYABLE). Real swipes visibly, repeatedly,
  deterministically mutate the board.
- **Not yet claimed (recorded limitations, not hidden):**
  1. In-page INLINE `<a>` buttons (`New Game`, retry/confirm) are not hit-testable yet —
     `inline_el` boxes keep 0×0 geometry, so the tap hit lands on `div.heading` and the
     anchor's click listener never runs (measured: tap `755,45` → `hit=div.heading
     listeners=0`, face unchanged). Restart via button is therefore not drivable yet.
  2. Game-over flow not driven — the CLI accepts one gesture per run and cross-run board
     persistence was NOT observed (each run restarts from a fresh board; localStorage does
     not restore game state across runs — measured over a 6-run chain with a shared
     data-root, which cycled the same 3 one-move faces).
  3. The newest archive version `com.uberspot.a2048_25` crashes at `MainActivity.onCreate`
     on this runtime (3 uncaught NPEs: `XmlPullParserFactory.newPullParser` on null,
     `AlertDialog.show` on null, `WebView.loadUrl` on null) — a pre-WS4B version-specific
     blocker recorded in `W21_APK_VALIDATION_REPORT.md`; version _23 runs SUCCESS rc=0.

## 4. Artifacts

- Evidence dir: `miniandroid/evidence/w21/a2048_probe/` (pristine / gated / traced /
  v23d acceptance matrix / chain runs / run logs per scenario).
- Fix commit: `c1602b75` (source diff: `src/webview/html_dom.h`,
  `src/webview/webview_engine.cpp`, `CMakeLists.txt` parity restore).
- Zero regressions: 15/15 corpus APKs byte-identical screenshots vs W20-K2
  (`W21_RUNTIME_BASELINE.md`); full test-all certified after the fix.
