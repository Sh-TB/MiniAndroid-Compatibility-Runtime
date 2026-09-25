#!/usr/bin/env python3
"""s99_report.py — post the S99 wave report on the master ticket #233."""
import json
import os
import subprocess
import sys

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
API = f"https://api.github.com/repos/{REPO}"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

BODY = """# S99 WAVE REPORT — Fish Rings homepage fix + 9 runtime bug laws + 61-title full-load sweep

**Trigger:** owner directive — run every open bug down, execute as many games
as possible to full completion, file a ticket for every new bug found
(issue-per-problem law), fix the Fish Rings homepage demo (static JPG, not a
GIF, never fully loaded).

---

## 1. Fish Rings homepage demo — FIXED (the owner's direct finding)

The four homepage demos were Snake Deluxe / 2048 / Mini Tetris / Fish Rings —
but Fish Rings embedded a **static JPG**. Now it carries the canonical
interactive GIF built from a real measured tap sequence on the external
F-Droid APK:

- Run: real-dalvik, 61 frames, taps at frames 30/40/50 (RC=0, 0 errors)
- Measured state changes: **splash→board transition 2,073,600 px; TAP 1
  board paints 4,304 px; TAP 2 ring rotation 4,320 px; TAP 3 4,308 px**
- Canonical GIF: docs/evidence/canonical/eu.veldsoft.fish.rings.gif (SHA
  f225a04b9187…), 5 distinct states with dwell timing, loop=0
- README demo table + demo grid now embed the GIF; EXECUTED_GIFS.md index
  is now **13/13 interactive** (12/12 before)

## 2. Runtime bug laws — 9 real bugs found AND fixed (all battery-certified)

Every fix below is evidence-backed (real APK reproduction), AOSP-cited, and
the canonical battery re-ran **ALL PASS (105 stages)** after landing:

| # | Law | Real-APK evidence |
|---|---|---|
| 1 | AnimatorShadow: ValueAnimator.ofInt/ofFloat static factories returned NULL (MG-223, **#323 CLOSED**) | babydots setRepeatCount NPE |
| 2 | getResources: View-root added — widget receivers named without "View" (FloatingActionButton) got NULL Resources | babydots FAB init NPE |
| 3 | View.animate() never-null + ViewPropertyAnimator fluent family | babydots SpeedDialView.init |
| 4 | TypedArray.hasValue PRESENCE law — resolved attr with value false/0 was conflated with ABSENT (the appcompat "Theme.AppCompat" ISE family) | babydots createSubDecor gate |
| 5 | `<include>` namespace + compiled-reference law — every include silently resolved to NOTHING (attr lookup used wrong namespace AND ignored typed references) | babydots abc_screen_content_include → ContentFrameLayout null |
| 6 | View.getContext() never-null fallback | Toolbar → TintTypedArray(null) |
| 7 | SharedPreferences.getFloat reader (only missing typed getter) | babydots setSpeed |
| 8 | prefs XML loader `<float>` entry (writer/reader symmetry) | typed round-trip break |
| 9 | SharedPreferences per-name IDENTITY law (AOSP ContextImpl cache) — writes through one object were invisible to readers holding another | first-run defaults never materialized |

Plus two framework-boundary no-op laws (ContentFrameLayout.setDecorPadding/
setAttachListener; checkVectorDrawableSetup — the vector pipeline is native
by law). Shadow invariant count law updated 27→28.

## 3. Full-load wave — 61 titles executed (54 F-Droid APKs re-sourced + 7 in-house)

- APK sourcing: scripts/s99_fetch_apks.py — F-Droid API-validated, SHA-pinned,
  with a truncation-repair loop (4 broken downloads re-fetched + verified)
- Sweep: scripts/s99_full_load.py — obs run + click probe per title, exact
  state-change pixel measurement, resume-safe
- **Census: 14 INTERACTIVE-EVIDENCE · 1 RENDERED-L2+ · 33 PARTIAL · 14 FAIL**
- All 7 in-house games INTERACTIVE-EVIDENCE (snake-deluxe, snake-neon, 2048,
  tetris, tictactoedeluxe, minicraft, snake) + external interactive evidence
  (privacyfriendlymemory, nounours, dodge, hotdeath, bobball, ballbreak,
  mentalmath-class titles)

## 4. New bug tickets filed (issue-per-problem law) — #342–#346

- **#342** theme-gate frontier (mykanji family)
- **#343** ConstraintLayout core interpreter frontier (no.thanks family)
- **#344** blank-render L0 family — 8 rc=0 titles that never draw (klondike/
  tripeaks/memory/blackjack/counting/accelerace/kingpong/bouncy)
- **#345** crash-on-launch family + **dooz rc=-11 process-death** (robustness law first)
- **#346** SpeedDialView library frontier (babydots cascade)

## 5. Ticket closed with evidence

- **#323 (MG-223 ValueAnimator basic timing) — CLOSED** by the AnimatorShadow law.

## 6. Gates at close

- Canonical battery: **105/105 ALL PASS**
- Control system: **160/160**
- Hygiene gate: PASS (5,314 files; zero APK/so, zero secrets)
- EXT-01/EXT-02 fixtures restored after container reset (SHA-verified
  009b4671… per zero-APK law)
- Pushed: d69f405c..d0f03cb7

## Next queue (largest measurable value first)

1. #345 dooz robustness law (no interpreter path may kill the process)
2. #342 theme-attr library-chain walk → mykanji + the appcompat gate family
3. #344 counting/accelerace custom-View onDraw → renderer path
4. #343 ConstraintLayout solve frontier → no.thanks + every CL-layout app
5. Per-title corpus sweep toward the 50-game bar (PARTIAL tails first)
"""

r = subprocess.run(["curl", "-sS", "-X", "POST",
                    "-H", f"Authorization: Bearer {TOKEN}",
                    "-H", "Accept: application/vnd.github+json",
                    "-d", json.dumps({"body": BODY}),
                    f"{API}/issues/233/comments"], capture_output=True)
d = json.loads(r.stdout.decode())
print("comment id:", d.get("id"), "| url:", d.get("html_url"))
