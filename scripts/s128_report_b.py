#!/usr/bin/env python3
"""S128b: post the cycle-close report (A-U) after R-NEW-424 execution."""
import json, urllib.request

TOK = open('/tmp/.gh_token').read().strip()
REPO = 'Sh-TB/MiniAndroid-Compatibility-Runtime'

BODY = """**S128b — MASTER WORKLIST EXECUTED: R-NEW-424 CLOSED (INPUT TouchTarget + onInterceptTouchEvent law)** — campaign loop continues after the worklist landed (`df18cc30`).

## What was executed (highest fan-out unresolved pipeline layer = INPUT, per the worklist's own priority computation)
**R-NEW-424 (P0) — ROOT-CAUSED-FIXED.** The AOSP `ViewGroup.dispatchTouchEvent` core was only partially modeled. Three generic laws implemented (zero app checks, AOSP android-14 anchors):

1. **CAP-INPUT-102 TouchTarget law** — DOWN hit-test now walks children in REVERSE draw order (AOSP `for (i = childrenCount-1; i >= 0; i--)`): the TOPMOST sibling wins overlaps; first-in-order used to win (z-order inversion). The **TouchTarget chain** (`mFirstTouchTarget` law) is captured for every gesture and exported in every dispatch record.
2. **CAP-INPUT-100 onInterceptTouchEvent law** — real DEX bridge (`dispatch_intercept`), `overrides_intercept_touch_event` captured at both constructor sites; intercept-at-DOWN retargets the gesture to the ViewGroup; mid-gesture interception sends ACTION_CANCEL to the child and retargets (scrolling-container law). `requestDisallowInterceptTouchEvent` = documented boundary.
3. TouchTarget chain + intercept records are exported per-event in `manifest.json` `interactions[]`.

## Verification (campaign §25 fan-out)
- **116-stage battery gate: ALL PASS** (zero regressions from the input-law wave).
- **S128 INPUT wave 9/9 PASS** (`run/s128/s128_report.json`):
  - heading calculator golden **a169346e ×3 PRESERVED**; flappycow menu golden **13cf4746 ×3 PRESERVED**
  - calc taps: `touch_target_chain` **max depth 5**, PerformClick dispatched ×3 through real DEX listeners, display state change (`90080684` ≠ golden; before-frame == golden byte-exact)
  - flappy G08-LAUNCH: StartscreenView chain + `onTouchEvent` override arm ×10
  - uNote BOOT-ORDER **7/7**; tictactoe byte-identical to S127 baseline `b5a7a35d` (honest target=0 tree-visibility frontier recorded)
  - Telegram grey (3 colors) / WhatsApp b/w (2 colors) — **honest NOT-A-RENDER, unchanged**
- Evidence: `evidence/s128_input_law/` (8 JPGs, 460px, English-only; before==golden, after≠before proves input→state→render).
- Registries: R-NEW-424 registered (422 roots); CAP-INPUT-102 → TESTED, CAP-INPUT-100 → IMPLEMENTED; **PENDING caps 37 → 35**.

## Updated campaign report (A–U)
A. MASTER WORKLIST UPDATED (`ecb7f2cb`): now **641 items** = 422 roots + 197 caps + 22 mandates — status upgrades EDIT records, never remove them.
B. TOTAL ITEMS: 641. C. VERIFIED 154 (+3 VERIFIED_3RUN). D. TESTED 46 (+CAP-INPUT-102). E. IMPLEMENTED 131 (+CAP-INPUT-100). F. OBSERVED 6. G. PARTIAL 106 (M-01 now PARTIAL). H. PENDING 142. I. BLOCKED 3. J. SUPERSEDED 49.
K. P0 20 · L. P1 66 · M. P2 64 (open; P3 105, P4 3).
N. CRITICAL PATH unchanged: R-NEW-294 MonotonicFrameClock → 295 composition render → 246/279/285 → 256 → 242 → dooz unblock; parallel M-01 residuals (VelocityTracker → TouchDelegate), M-03 lockCanvas.
O. ROOTS CLOSED THIS CYCLE: **1 (R-NEW-424, P0, INPUT)**. P. CAPABILITIES COMPLETED: 2 upgraded (CAP-INPUT-102→TESTED, CAP-INPUT-100→IMPLEMENTED). Q. APKs IMPROVED: heading calculator (tap chain evidence), FlappyCow (chain + arm evidence). R. STILL BLOCKED: Telegram, WhatsApp, dooz v23, FlappyCow gameplay. S. REGRESSIONS: 0 (battery 116/116 + both goldens ×3). T. NEW ROOTS: 1 registered with fix attached (R-NEW-424); boundary flags: requestDisallowInterceptTouchEvent, ttt tree visibility.
U. NEXT AUTOMATIC ROOT: **M-01 residual — CAP-INPUT-108 VelocityTracker**, then CAP-INPUT-110 TouchDelegate + intercept wave on a scrollable-container APK (sudoku / OpenCalculator SlidingUpPanelLayout family); then M-03 GAME lockCanvas loop.

---
*Standing note: MiniAndroid renders frames into a real framebuffer and verifies them by pixel metrics + SHA; honest labels are enforced everywhere — Telegram's grey frame and WhatsApp's black/white frame remain load frontiers and are called NOT-A-RENDER in every generated panel; no "100% rendered" claims exist or are allowed; evidence images are published as small English-only JPGs (no gameplay GIFs per directive).*
"""

req = urllib.request.Request(
    f'https://api.github.com/repos/{REPO}/issues/354/comments',
    data=json.dumps({'body': BODY}).encode(),
    headers={'Authorization': f'Bearer {TOK}', 'Accept': 'application/vnd.github+json'})
r = urllib.request.urlopen(req)
print('posted:', json.load(r)['html_url'])
