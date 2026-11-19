# INDEPENDENT KNOWLEDGE INVENTORY — cODER-ohc transfer (W20)

Repo HEAD at audit: `wave10/dalvik-accel` @ `8d843248` + W20 build commit
`671d2577`. The coder's work was performed on `main` @ `0dae5fb8` (S237
campaign) and `ba178ed4` (PLAY wave) — a DIFFERENT lineage, issues-only lane,
**nothing was ever pushed by the coder**. Every artifact from
`CODER_ohc_PLAY_WAVE_ISSUE.zip` (12 files) is inventoried below; each finding
was verified against THIS repo's actual HEAD before integration.

## Legend
- INTEGRATED — implemented on this HEAD in this wave (with regression test)
- CONFIRMED — defect verified present on HEAD, integrated
- RESOLVED-NO-PATCH — verified by-design behavior; no change warranted
- PENDING — verified real, not yet integrated in this wave
- OBSERVED — the coder's evidence accepted; re-verification queued

## WS2 — SolitaireCG splash (WS2_02_SOLITAIRE_SPLASH_FINDING.md, ws2_comment.md)
- Finding: the grey first frame is the app's BY-DESIGN splash
  (`PlayedBefore=false`); board renders byte-identically after the first tap
  (5× identical `1787d115…`); the WS2.01 "wrong blit source" hypothesis was
  REFUTED by the coder themselves.
- Disposition: **RESOLVED-NO-PATCH** — no runtime defect. Do NOT label the
  splash a failure. (Confirmed against the current engine: the state machine
  decompile in the artifact matches the documented AOSP ordering.)

## WS4 — 2048 input (WS4_2048_INPUT_FINDING.md, ws4_comment.md, ws4_fix_comment.md)
- Root cause (3 stacked defects): (1) no MOVE stream reaches the WebView
  browser (only caller of `pointer_event` was the single-point click burst);
  (2) synthetic TouchEvent lacked `changedTouches`/`targetTouches`;
  (3) `touches` not emptied on touchend + no preventDefault/stopPropagation.
- The coder's fix was LOCAL-ONLY + env-gated default-off
  (`MINIANDROID_WV_CHANGED_TOUCHES`, `MINIANDROID_WV_DRAG_FORWARD`).
- Disposition: **INTEGRATED (this wave)** — re-implemented on this lineage:
  `src/webview/webview_engine.cpp` (W3C completeness under
  MINIANDROID_WV_CHANGED_TOUCHES) + `src/runtime/execution_engine.cpp` (real
  multi-point gesture forward under MINIANDROID_WV_DRAG_FORWARD).
- **WS4B (PENDING)**: the coder's own residual stands — logical game state
  mutates (`GameManager.move` → grid `0200|…`) but the board does NOT
  visibly repaint. DOM mutation → computed layout → paint invalidation →
  surface blit is a separate investigation. **2048 is NOT claimed playable.**

## WS5 — SQLite/Cursor (ws5_comment.md)
- Finding: `getColumnIndex`/`getColumnIndexOrThrow` matched exactly (no
  qualifier strip, no case-fold) and threw a non-AOSP message. Fixture
  s241_sqlite_cursor_contract_test 4/8 pre-fix → 8/8 post-fix.
- HEAD verification: defect CONFIRMED (`sqlite_shadow.cpp` exact-match loop).
- Disposition: **INTEGRATED (this wave)** — shared `column_index_ci` helper
  (strip after last `.`, case-fold), AOSP message shape with available-columns
  list; regression test `tests/s248_sqlite_cursor_contract_test.cpp`.

## WS6 — ListView/Adapter (ws6_comment.md)
- Finding: `AdapterView.getItemIdAtPosition` returned INT32 (Adapter.getItemId
  returns LONG) and 0 for negative positions (AOSP: INVALID_ROW_ID =
  Long.MIN_VALUE). Their harness decoder gap (s235 r11a INT32-only) is a
  TEST-HARNESS fix, not a runtime change — kept distinct here.
- HEAD verification: defect CONFIRMED (`make_int(pos >= 0 ? pos : 0)` in the
  live bridge arm).
- Disposition: **INTEGRATED (this wave)** — INT64 + INVALID_ROW_ID in both
  the coordinator arm and the split domain; regression test
  `tests/s249_adapter_position_contract_test.cpp`.

## WS7 — Dialog lifecycle (ws7_comment.md)
- Finding: the three listener setters were a shared no-op bucket (listener
  discarded); show/dismiss/cancel never delivered the app overrides.
- HEAD verification: defect CONFIRMED (single `handled_void()` bucket).
- Disposition: **INTEGRATED (this wave)** — listeners stored on DialogWindow;
  exactly-once pending tokens; cancel → onCancel THEN onDismiss ordering;
  engine drain (`deliver_pending_dialog_callbacks`, defined in the always-
  linked runtime TU, called from bridge_to_api entry + per-frame pump);
  regression test `tests/s250_dialog_lifecycle_contract_test.cpp`.

## WS8 — Activity result delivery (ws8_comment.md)
- Finding: `take_result` returned false when the child never called
  setResult; the cascade guarded dispatch on `has_result` → onActivityResult
  never fired for the plain-finish path. Contract-level evidence only (the
  corpus does not drive the path live).
- HEAD verification: defect CONFIRMED (`if (!has_result_) return false;`).
- Disposition: **INTEGRATED (this wave)** — take_result always delivers the
  AOSP default; cascade dispatches whenever `launched_for_request >= 0`;
  regression test `tests/s251_activity_result_contract_test.cpp`.

## WS9 — View state flags (ws9_comment.md)
- Finding: the whole setX/isX family (selected/pressed/activated/
  longClickable/hovered) had NO dispatch arms; pick_state_list ignored
  state_activated/state_window_focused; renderer hardcoded hovered=false.
  Real demand: openlauncher 17 call sites, stopwatch 3, tictactoe 2,
  opensudoku 2, dooz/a2048 1.
- HEAD verification: defects CONFIRMED (0 arms; no activated enforcement).
- Disposition: **INTEGRATED (this wave)** — ViewNode.activated/hovered; 10
  dispatch arms; pick_state_list activated/window_focused first-match
  enforcement (window_focused default true); render caller forwards the real
  node flags; regression test `tests/s252_view_state_flags_contract_test.cpp`.

## PLAY WAVE receipts (CODER_ohc_PLAY_WAVE_ISSUE.md, base ba178ed4)
| Title | sha16 | Coder status | This wave |
|---|---|---|---|
| TicTacToe Classic (GAME-011) | 760fe5acf7b39435 | OBSERVED — real libGDX board, NO tap-to-play (assets/i18n/TicTacToe_en_US.properties FileNotFoundException → GdxRuntimeException) | PENDING (P2) |
| SolitaireCG (GAME-090) | d4afb74d28680712 | BLOCKED — DrawPortraitCards createBitmap(w=0,h=-1) IAE (getIntrinsicWidth/Height -1 when __dr_width__ absent) | **INTEGRATED** — bitmap-dims fallback (AOSP BitmapDrawable law) |
| uNote (APP-002) | be91103f0e7db443 | OBSERVED — full list UI, empty ListView, editor unverified | PENDING (P2) |
| Notes/billthefarmer (APP-006) | 82cf8bc44c163748 | OBSERVED — near-blank MarkdownView despite 183/187 census | PENDING (P2) |
| Frozen Bubble (bonus) | fababf48eafa5e45 | real GL render, deferred NSFE (inScaled) keeps PARTIAL | **INTEGRATED** — Options public fields registered (both =0 + split copies) |

## j12_collections + 5 additional findings (PART C)
Carried forward from the previous transfer (already covered earlier); all are
data points in INDEPENDENT_FINDINGS_STATUS.csv. Not re-verified this wave.

## Test-battery corrections preserved
- s98_text_law_test + s106_text2_law_test failures are PRE-EXISTING font-env
  battery failures on the coder's lineage — NOT regressions of any wave.
- The coder's s235 r11a decoder fix = harness gap, not runtime behavior.
