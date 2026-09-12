# COMPATIBILITY_SCOREBOARD_013

All values computed from `triage/{baseline,after}/triage_summary.json` artifacts.

| Metric | v0.11.3 (BEFORE) | v0.13.0-rc (AFTER) | Δ |
|--------|------------------|--------------------|---|
| APK tested | 17 | 17 | — |
| REAL_UI | 3 | 5 | +2 |
| PARTIAL_UI | 2 | 2 | 0 |
| REAL_INTERACTION (click → framebuffer change) | 1 | 4 | +3 |
| ACTIVITY_FAILED | 10 | 6 | -4 |
| BOOT_FAILED | 1 | 0 | -1 |
| VISIBLE_STATE_CHANGE (views with changed_px>0, AFTER) | 4 apps | — | — |
| DIALOG_VISIBLE | 0 (dialog layer absent) | 1 (gmdice two-dialog chain) | +1 |
| LIST_VISIBLE | 0 | 1 (unote 64-view list UI) | +1 |
| GLES_FRAME | 0 | 0 (Stage-1 not reached this campaign — see GLES_REPORT) | 0 |
| LIBGDX_FRAME (app-drawn pixels) | 0 | 1 (bouncy ScoreView.onDraw replayed) | +1 |
| COMPOSE_FRAME | 0 | 0 (unchanged boundary — see COMPOSE_REPORT) | 0 |
| Telegram golden | 088ea640 (3/3 prior campaigns) | 088ea640 EXACT | = |
| SimpleStopwatch golden | 2a12587a | 2a12587a EXACT | = |
| Semantic fixtures | 8/8 + 5/5 | 8/8 + 5/5 | = |

## Multi-frame / interaction evidence (AFTER, from click_test_report.json)

- **gmdice**: 4 clicks dispatched, 4 produced visible second frames (per-view px in click_test_report.json)
- **simplestopwatch**: 2 clicks dispatched, 2 produced visible second frames (per-view px in click_test_report.json)
- **unote**: 4 clicks dispatched, 2 produced visible second frames (per-view px in click_test_report.json)
- **bouncy**: 12 clicks dispatched, 10 produced visible second frames (per-view px in click_test_report.json)

