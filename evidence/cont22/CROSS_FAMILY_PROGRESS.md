# CONT-22 — CROSS-FAMILY PROGRESS SCOREBOARD

Binary lineage: `882b7cdf389aabc3` (CONT-21) → **`fa88902fdee6e982`**
(engine deltas: F-NEW-274 R414 constructor-contract gate + F-NEW-275
getServiceInfo/GET_SERVICES laws; dalvik_engine.cpp/.h only). Head at wave
end: see git log. All rows are FRESH runs this wave — no copied artifacts.

Render-stage ladder (project vocabulary): UNEXECUTED → LOADED →
LIFECYCLE_VERIFIED → RENDER_STARTED → FRAME_CAPTURED → VISUALLY_PARTIAL →
VISUALLY_VERIFIED → INTERACTION_VERIFIED → FULLY_VERIFIED.

| Family | APK | Root(s) hit this wave | Before (882b7cdf) | After (fa88902f) | Render stage | App pixels (nondom) | Interaction | 3-run |
|---|---|---|---|---|---|---|---|---|
| F1 Base/View | opencalc | F-NEW-275 (getServiceInfo→NameNotFoundException, app-handled) + F-NEW-274 gate (Lm0/i0;.e) | 5 uncaught / 5 APP BOUNDARY / ServiceInfo NPE ×1 | 4 uncaught / 4 APP BOUNDARY / ServiceInfo NPE **0** | REAL_APP_CONTENT (anchor a976d2f9) | 1,052,351 | tap-tested in prior waves (untouched this wave) | anchors ×3 MATCH |
| F1 Base/View | stopwatch | — (F-275 n/a: no getServiceInfo call) | startup clean, rc=1, white frame | unchanged (honest) | LOADED (frame white — startup-cluster closed CONT-21) | 0 | no | 1 run |
| F1 Base/View | unote | — | SUCCESS | SUCCESS (anchor 4f1a9e4e) | REAL_APP_CONTENT | 302,400 | no | anchors ×3 MATCH |
| F1 Base/View | microtimer | — | SUCCESS | SUCCESS (anchor da73010a) | REAL_APP_CONTENT | 1,029,909 | no | anchors ×3 MATCH |
| F1 Base/View | chessclock | — (P7 Uri-null stays unfixed: single-target candidate) | 1 uncaught (Uri.toString on null) | unchanged | LOADED | 66,246 | no | 1 run |
| F2 2D Canvas | g2048 | — | REAL_APP_CONTENT | anchor 59ca1526 MATCH ×3 | REAL_APP_CONTENT | 1,175,625 | yes (prior waves) | ×3 MATCH |
| F2 2D Canvas | tictactoe_deluxe | — | REAL_APP_CONTENT | anchor af609429 MATCH ×3 | REAL_APP_CONTENT | (anchor) | yes (prior waves) | ×3 MATCH |
| F2 2D Canvas | tictactoe (libGDX) | — (P10 libGDX surface: family candidate, 2 targets now incl. bouncy) | 2 uncaught (GLSurfaceView20 EGL) | unchanged | LOADED (onCreate death) | 0 | no | 1 run |
| F3 game-loop | flappycow | — | SUCCESS | SUCCESS (636 colors) | REAL_APP_CONTENT | 1,065,551 | no | 1 run |
| F3 game-loop | bouncy | — (SharedLibraryLoadRuntimeException = native-law family face) | FRAME_CAPTURED, 2 uncaught | unchanged | FRAME_CAPTURED | 978,380 | no | 1 run |
| F3 game-loop | fishrings | — (Splash Timer face, CONT-8) | default-bg | unchanged | LOADED | 0 | no | 1 run |
| F4 Messaging | telegram | **F-NEW-275** (Firebase ComponentDiscovery served ×2, app catches NameNotFoundException) | REC-MISS ×2 → null-degradation | F275-SVCINFO ×2, caught | LOADED (rc=1 honest; UI-init family faces remain — 9 uncaught, family-internal) | 0 | no | 2 runs |
| F4 Messaging | forkgram | — (no getServiceInfo in its path) | rc=1, UI-init faces | unchanged | LOADED | 0 | no | 1 run |
| F5 Social/media | **NO-TARGET-IN-CORPUS** | — | — | — | UNEXECUTED | — | — | — |
| F6 Compose | dooz | **F-NEW-274** (R414 ctor-contract gate: uncaught **1→0**; UEH kill-path gone; +113 log lines deeper) | 1 uncaught (iget Lrf1;.f on null) / [UEH-DEFAULT] fires | **0 uncaught** / zero fatal exceptions / [F274-CTORGATE] fires | RENDER_STARTED (composition live; frame-truth DEFAULT_BACKGROUND — F-265 measure frontier is the visual gate) | 0 | tap pipeline bridged F-267 (prior wave) | anchors ×3 MATCH |
| F7 WebView/HTML5 | minibrowser | — | SUCCESS | SUCCESS (222 colors) | REAL_APP_CONTENT | 31,208 | no | 1 run |

## Regression gate (binary fa88902fdee6e982)

| Suite | Result | Recorded baseline |
|---|---|---|
| anchors ×3 (dooz, microtimer, unote, gmdice, opencalc, tictactoedeluxe) | **18/18 MATCH byte-identical** | 18/18 |
| g2048 F2 anchor ×3 | **MATCH** (59ca1526611c4622) | recorded |
| fcol (K1–K20) | **20/20** | 20/20 |
| f259 | **7/7** | 7/7 |
| f259g | **12/13** (same known honest F259-L row) | 12/13 |
| f266 | **6/6** | 6/6 |
| f268 | **12/12** | 12/12 |
| 5-target sweep screenshots | byte-identical to pre-fix SHAs (no visual drift) | new evidence |
| probe APKs | reused CONT-21 canonical builds (run/w7, run/w8, run/cont18g) | canonical |

## Face-delta table (same params, before vs after binary)

| Target | Metric | Before | After |
|---|---|---:|---:|
| dooz | uncaught faces | 1 | **0** |
| dooz | `Lrf1;.f` log mentions | 37 | **0** |
| dooz | [UEH-DEFAULT] kill path | 1 | **0** |
| dooz | run.log lines (depth) | 3,842 | 3,955 |
| opencalc | uncaught / APP BOUNDARY | 5 / 5 | **4 / 4** |
| opencalc | ServiceInfo.metaData NPE | 1 | **0** |
| telegram | getServiceInfo served | 0 | **2** |
