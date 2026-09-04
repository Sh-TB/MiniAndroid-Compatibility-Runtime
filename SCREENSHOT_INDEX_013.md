# SCREENSHOT_INDEX_013 (§24 evidence standard)

All screenshots produced by the standard pipeline (`stage_capture_output` /
click probe) from real runs of the SHA-locked corpus APKs on branch
`campaign-013`. Framebuffer hashes are SHA256 of `screenshot.png`.
Run trees: `~/miniandroid_ws/triage/{baseline,after}/<apk>/`.

## Frame-1 screenshots (AFTER campaign fixes)

| APK | PNG SHA256 (first 16) | non-white px | curated copy |
|-----|----------------------|--------------|--------------|
| gmdice | `4fd3ce0e0c419119` | 1,744,539 (first-launch dialog visible) | docs/evidence/u013/screens/gmdice-frame1.png |
| simplestopwatch | `2a12587a0acf196c` | 916,815 — GOLDEN EXACT | (golden, unchanged) |
| unote | `d6b854c45a16539f` | 2,073,600 | docs/evidence/u013/screens/unote-frame1.png |
| bouncy | `dc6a565ee96ed5d7` | 2,073,600 | docs/evidence/u013/screens/bouncy-frame1.png |
| headingcalculator | `7d2a68606ae18d76` | 2,073,600 | docs/evidence/u013/screens/headingcalculator-frame1.png |
| chessclock | `ba017f5183ac5747` | 2,072,520 | docs/evidence/u013/screens/chessclock-frame1.png |
| notesbillthefarmer | `9149bbb885a43d9e` | 31,752 | docs/evidence/u013/screens/notesbillthefarmer-frame1.png |
| bgclockhansdezwart | `2f85dd74aa54e463` | 2,073,600 | (run tree) |
| telegram_v12 | `088ea640587ec0d2` | 41,233 — GOLDEN EXACT | (golden, unchanged) |

## Interaction frames (click probe — real dispatch → re-render → diff)

| APK | Frame | Evidence |
|-----|-------|----------|
| gmdice | dice-set dialog visible after REAL click on "…" | click_frame_0.png → docs/evidence/u013/screens/gmdice-dialog-visible.png (1,737,264 px diff) |
| gmdice | item which=2 dispatched → second dialog stacked + dice display "1 1 1" | click_frame_3.png → docs/evidence/u013/screens/gmdice-item-selected-2nd-dialog.png (1,868,540 px diff) |
| bouncy | click probe frames | click_frame_2..6.png (run tree); sample → docs/evidence/u013/screens/bouncy-click-frame.png |
| simplestopwatch | Start/Reset second frames | click_frame_*.png (run tree; 2/2 changed, golden-preserving probe) |

## Determinism / repeatability

- simplestopwatch `2a12587a…` and Telegram `088ea640…` re-verified IDENTICAL
  across separate binary builds during the campaign (multiple runs each).
- Per-view click JSON (`click_test_report.json` in every run tree) carries
  view id/class/dispatch/changed_px per probe — the input→callback→mutation→
  redraw chain is auditable per row.
- Run number convention: `triage/baseline` = pre-campaign binary (ea81e00);
  `triage/after` = final campaign binary (cd0463f).
