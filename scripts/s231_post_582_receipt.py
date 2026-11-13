#!/usr/bin/env python3
"""S231: post the cross-link receipt on #582 (the §5/§6-adjacent shared
contracts the route matrix promised 'in the following receipt')."""
import json
import subprocess
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

BODY = """# S231 receipt — the shared contracts this census's next-fix rows ride on, LANDED (pin-neutral); matrix rows updated

**Reviewed HEAD:** `d4e48d6c` (S231 wave, pushed). Binary under test: post-fix `2f2af2694984933f`.

## IMPLEMENTED (the "following receipt" the route matrix promised — full detail on #585, comment 6861818272)

- **AbsListView RecycleBin scrap contract** (mandate §4-3/P0 family — JNI/array/direct-buffer lifetime already landed in earlier waves; this closes the VIEW-side rebind contract): per-ListView scrap bins keyed by the adapter item-view type (getViewTypeCount/getItemViewType through the real DEX chain), previous rows stash to scrap at relayout, obtainView hands a SAME-TYPE scrap back as `convertView`, ITEM_VIEW_TYPE_IGNORE never recycled, out-of-range types COUNTED (never silent), capacity drop-oldest, dead-bin prune. `tests/s231_view_resource_law_test.cpp` 24/24; `make test-all` **29/29**.
- **GridView column contract** in the LIVE measure/layout law: numColumns / AUTO_FIT-from-columnWidth / stretchMode no_stretch+columnWidth / h+v spacing / wrap = rows·(row-max+vSpacing)−vSpacing; INACTIVE grids keep the CONT-102 vertical stack (no silent behavior change); non-spanning recorded as a structured approximation.

## TESTED (regression discipline, mandate §4-7)

- **FULL 6-PIN GATE ALL HOLD byte-exact** on the post-fix binary: bouncy `98abca38` / unote `3b8dcb0a` / dooz `a0fae907` / gmdice `3891679d` ×2 identical / microtimer `b39665f6` 0-uncaught / ttt `7354c1b2` ×3 deterministic → the §5 wave is **pin-neutral**.
- The cold-run census record (`evidence/s228_census/s231_cold_runs_batch.json`) is the §4 baseline this wave measured against; the matrix's row statuses are unchanged by the §5 contracts (they touch ListView rebind + GridView layout, not the native loader/GL/present chain the BLOCKED rows diverge at).

## OBSERVED (correction to the gomoku stage-C row, honest)

- The deeper console decode shows the loadLibrary bridge IS reached (`[GATEA-NATIVE]` reports "bridge-satisfied" — 70 real SDL implementations registered) but the host `dlopen` of `libSDL2.so` is REFUSED (wrong ELF class: ELFCLASS32 — the APK ships only 32-bitarmeabi-v7a/x86 libs) and the app's native main (libmain.so, started by SDLActivity's surface thread) never produces pixels. So the gomoku/rttt first divergence is more precisely: **stage B→C boundary — 32-bit-only APKs on the x86_64 runtime have NO structured ABI row and their shadow-satisfied load hides the refusal** (exactly the mandate's §4-2/P0 "structured unsupported case" + "prevent fake success when native initialization fails"). Next experiment stands: an explicit ABI_ELFGCLASS32 row + a REAL native-main dispatch path for the SDL surface thread; the "bridge-satisfied ≠ native-main-ran" distinction is now a named fake-success shape this census adds to the mandate's §1 vocabulary.

## What this receipt does NOT claim

- No native-route APK declared FIXED; the four gray-face rows stay BLOCKED/PARTIAL at their named stages; the SDL2/SDL3/JNI-AI/GL presentation family (stage H) and the dooz kotlinx death family remain the open shared levers, next probes unchanged from the matrix.
"""

cred = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True, cwd=str(BASE)).stdout
token = [l.split("=", 1)[1] for l in cred.splitlines() if l.startswith("password=")][0]
req = urllib.request.Request(
    "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/582/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers={"Authorization": f"token {token}",
             "Accept": "application/vnd.github+json",
             "User-Agent": "s231-receipt"},
    method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    out = json.loads(r.read().decode())
    print(f"posted #582 comment id={out['id']}")
