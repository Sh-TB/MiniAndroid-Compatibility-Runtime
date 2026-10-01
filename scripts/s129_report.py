#!/usr/bin/env python3
"""s129_report.py — post the S129 campaign report to the tracking issue (#354)."""
import json
import subprocess
import sys

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"


def token():
    out = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return None


BODY = """## S129 — R-NEW-425 VelocityTracker law + R-NEW-426 TouchDelegate / MOVE-delivery law (campaign SS18 loop: the master worklist's own priority queue selected this root)

**Next automatic roots after S128b (CAP-INPUT-108 → CAP-INPUT-110) — both CLOSED this session.** AOSP android-14.0.0_r2 sources fetched and quoted first (`docs/upstream/aosp/input_laws/`: `VelocityTracker.java`, native `VelocityTracker.h/.cpp` (LSQ2), `TouchDelegate.java`, `View.java` L17060-17064, `ViewGroup.dispatchTouchEvent`).

### R-NEW-425 — VelocityTracker law (CAP-INPUT-108 → TESTED)
- 1:1 port of the native LSQ2 estimator: `LeastSquaresVelocityTrackerStrategy(degree 2, Weighting::NONE)`, HORIZON = 100 ms, HISTORY_SIZE = 20, ASSUME_POINTER_STOPPED_TIME = 40 ms, `solveUnweightedLeastSquaresDeg2` closed form, velocity = coeff[1], `getComputedVelocity` scale+clamp (`v*units/1000`).
- `VelocityTrackerShadow` DEX bridge: `obtain/recycle/clear/addMovement/computeCurrentVelocity/getXVelocity/getYVelocity/getAxisVelocity/isAxisSupported`.
- `MotionEvent` materialization now carries `__time__` (virtual-clock ms — deterministic) at all 3 sites + `getEventTime/getTime` bridge + `AXIS_X/Y/SCROLL` constants.
- **MOVE-delivery law** (the bigger fan-out): the dispatcher only ever delivered DOWN/UP to app code — every MOVE was dropped, starving VelocityTracker/GestureDetector streams. Fixed per AOSP `dispatchTransformedTouchEvent`; also fixed the S128 MOVE action code (was 1 = AOSP UP, now 2 = MOVE).
- Generic `--swipe x1,y1,x2,y2[@frame]` driver gesture (DOWN → 12 MOVEs @16 ms 60 Hz → UP through the dispatcher law pipeline; F-NEW-199 manifest record).

### R-NEW-426 — TouchDelegate law (CAP-INPUT-110 → IMPLEMENTED)
- `TouchDelegateShadow` ctor capture + `View.setTouchDelegate` bridge + ViewNode delegate fields.
- Dispatcher consult law: target's own delegate first; then the AOSP **fallback arm** (no child claims the DOWN → deepest visible view containing the point + ancestor unwind, touchability NOT required per `isTransformedTouchPointInView`); delegate retarget + event translation (`setLocation(w/2,h/2)` / outside-slop); EXACT mBounds on DOWN; slopBounds gating on MOVE/UP; CANCEL clears `mDelegateTargeted`.

### Evidence (real DEX, zero app-specific code)
- Real-DEX fixture `tests/fixtures/s129_input_law` (aapt2+ECJ+D8): a tap at (900,700) — outside the 48dp button, inside the delegate rect, no touchable child — produces **DELEGATE-CLICK** through the fallback law; `--swipe 100,1400,100,1592` makes the app's own `VelocityTracker` code compute **VY=999;VX=0** (192 px / 12 MOVEs @16 ms; 999 vs 1000 is float32 LSQ2 precision — the same characteristic as AOSP's float solver). 3-run frame SHA identical.
- `velocity_tracker_law_test` 17 checks + `touch_delegate_law_test` 23 checks — ALL PASS; shadow registry invariant law updated 29→31 (measured: two new shadows).
- **Battery gate: ALL PASS (114 stages, zero FAIL)** — incl. restored post-reset infra (EXT-01 fixture re-fetched byte-exact per the frozen ledger SHA `009b4671…`, reference SHA `121d479c…`; `resource_trace` tool rebuilt; density oracle 11/11).
- **S129 INPUT wave 11/11** (`scripts/s129_input_wave.py`): calc goldens `a169346e` ×3 + flappy menu `13cf4746` ×3 PRESERVED; ttt byte-identical `b5a7a35d`; uNote BOOT-ORDER 7/7 + swipe MOVE-delivery recorded; telegram/whatsapp honest **NOT-A-RENDER** (3/2 colors — unchanged frontier, never claimed as renders).

### Master worklist (canonical, visible — docs/MASTER_WORKLIST.md + canonical/master_worklist.json)
- 643 items (424 roots + 197 caps + 22 mandates) · open 256 · closed 387 · VERIFIED 156 · TESTED 46 · IMPLEMENTED 133 · PENDING 140 · PARTIAL 106 · SUPERSEDED 49 · BLOCKED 3
- P0 20 · P1 64 · P2 64 · P3 105 · P4 3 (open) — INPUT caps PENDING 37 → **33**
- Evidence: `evidence/s129_input_law/` (8 JPGs, 460 px, English-only) + `s129_input_wave_report.json`

**Next automatic root (worklist-computed):** CAP-SCROLLING-126 `computeScroll` → CAP-SCROLLING-127 `EdgeEffect` (the INPUT→SCROLLING fling consumer chain), then M-03 GAME `lockCanvas` loop; M-01 residual intercept wave on sudoku/opencalculator stays queued.

![delegate tap law](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/raw/main/evidence/s129_input_law/s129_delegate_tap_real_dex_DELEGATE_CLICK.jpg)
![velocity law](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/raw/main/evidence/s129_input_law/s129_velocity_real_dex_VY999.jpg)

<!-- standing-note: MiniAndroid Compatibility Runtime campaign — honest-status vocabulary; goldens are frozen; blank/grey/black frames are NOT renders; evidence is always reproducible from the committed scripts. -->
"""

tok = token()
rc = subprocess.run(
    ["curl", "-s", "-X", "POST",
     f"https://api.github.com/repos/{REPO}/issues/354/comments",
     "-H", f"Authorization: Bearer {tok}",
     "-H", "Accept: application/vnd.github+json",
     "-d", json.dumps({"body": BODY})],
    capture_output=True, text=True).stdout
try:
    print("comment url:", json.loads(rc)["html_url"])
except Exception:
    print("ERROR:", rc[:400])
    sys.exit(1)
