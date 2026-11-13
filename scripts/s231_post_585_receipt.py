#!/usr/bin/env python3
"""S231: post the §5 receipt on #585 (mandate §5 view/resource contracts)."""
import json
import subprocess
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

BODY = """# S231 receipt — EXECUTION MANDATE §5 (view/resource contracts) IMPLEMENTED + TESTED; §7 cohort evidence grew this wave

**Reviewed HEAD:** `d4e48d6c` (S231 wave, pushed). Binary under test: post-fix `2f2af2694984933f`; the cold-run baseline ran on the release RC `06f98d2a9c21ea92` (rebuilt byte-identically from a clean tree first — a reproducible-build proof).

## §5 — view/resource contracts: the two gaps the §5 text names with live corpus evidence are now closed

**F-S231-A — AbsListView RecycleBin scrap contract** (AOSP ListView.java RecycleBin @android-14):

- Prior state (honest): the S191 re-materialization law rebuilt rows but passed `convertView = null` EVERY bind — a real adapter's inflated rows were thrown away and re-inflated every layout pass (the code comment itself recorded "until a recycler pass exists"). That was a §5-named gap.
- Landed: `miniandroid/src/framework/adapter_scrap_bin.h` — per-ListView scrap bins **keyed by the adapter item-view type** (getViewTypeCount()/getItemViewType() resolved through the REAL DEX chain, default 1 per BaseAdapter); previous active rows stash to scrap at relayout; obtainView pops a scrap view of the SAME type as `convertView`; **ITEM_VIEW_TYPE_IGNORE (−1) rows are never recycled**; an **out-of-range type is a COUNTED violation** (recycle_type_violations_, bound as type 0 — bounded-lenient, never silent; AOSP throws ISE there); beyond kScrapCapPerType=16 the OLDEST scrap is dropped, counted; bins of dead ListViews are pruned.
- Wiring: `DalvikExecutionEngine::materialize_adapter_rows_for` now runs the full contract; honest counters exposed (`recycle_rows_reused()` / `recycle_rows_inflated()` / `recycle_type_violations()`) + a `[S231-RECYCLE]` evidence line per rebuild.

**F-S231-B — GridView column contract** (AOSP GridView.java), wired into the **LIVE** measure/layout law (`LayoutInflater::measure_layout` — the UNIFIED_007 single source of truth, not a dormant path):

- `android:numColumns=N>1` → N column tracks, row-major flow; `numColumns="auto_fit"` (−1) → columns = floor((content_w + hSpacing)/(columnWidth + hSpacing)), **1 column when no columnWidth** (AOSP AUTO_FIT needs columnWidth); `stretchMode=columnWidth` → tracks stretch to (content_w − (cols−1)·hSpacing)/cols and items fill the cell; `stretchMode=no_stretch` → track keeps columnWidth, items keep their measured width (leftover right-packed); `verticalSpacing`/`horizontalSpacing` stride rows/columns; wrap height = rows·(row-max-h + vSpacing) − vSpacing.
- **No silent behavior change**: an INACTIVE grid (unparsed numColumns / 1 / AUTO_FIT without columnWidth) keeps the CONT-102 vertical stack. Items do NOT span tracks — recorded as a structured approximation on the ViewNode (span is GridLayout semantics), never silent.
- Parsed: numColumns / columnWidth / verticalSpacing / horizontalSpacing / stretchMode (string + compiled-int forms) onto the ViewNode.

## §5 sub-item dispositions (nothing silently re-labelled)

- WRAP_CONTENT custom views: **already covered** (g10 battery + R-NEW-438/MASTER-2 laws) — pinned by the existing tests, not re-implemented.
- LayoutInflater attachToRoot true/false + parent-generated LayoutParams + merge/include: **already covered** (G11 FIX-G11-002, F-C4-603 id/params override law, attach-before-measure law) — pinned by g10/g11.
- FragmentFactory: **already covered** (no-arg-constructor instantiate law).
- ConstraintLayout: **already covered** (F-148 anchor family + onLayout replay).
- Resource qualifier selection: **already covered** (resource_config_selection_test 576-line battery); the "selected drawable is the one consumed by the final frame" provenance link rides on the C9 bitmap-density + src_w/src_h evidence fields.
- ListView/Adapter recycling: **WAS the gap → NOW CLOSED** (F-S231-A).
- GridView columns/spacing/stretch: **WAS the gap → NOW CLOSED** (F-S231-B).
- ViewStub inflate: **PENDING** (honest) — ViewStub is name-mapped only; no corpus APK in the current cohort hits it. It stays an explicit open item, not a claim.

## TESTED

- `tests/s231_view_resource_law_test.cpp` — **24/24** (scrap mechanics 9: LIFO same-type pop, type-bucket independence, IGNORE no-op, capacity drop-oldest + counted drops, dead-bin prune; engine counter surface 2; grid law 13: fixed-N row-major + track math, AUTO_FIT derivation, AUTO_FIT-without-columnWidth regression guard, spacing strides, wrap law, law-off regression guard). Registered in the battery → **`make test-all` 29/29**.
- **FULL 6-PIN GATE ALL HOLD byte-exact** on the post-fix binary `2f2af2694984933f`: bouncy `98abca38` / unote `3b8dcb0a` / dooz `a0fae907` / gmdice `3891679d` ×2 identical / microtimer `b39665f6` 0-uncaught / ttt `7354c1b2` ×3 deterministic — the §5 wave is **pin-neutral** (no engine behavior change outside the two contracts).
- Policy validator **0 violations**.

## §7 — real-app cohort (minimum 10, target 20): evidence grew this wave

- The GP-census cold-run batch (#582 directive 6821150791 §3/§4, mandate-referenced) executed **3 cold runs × 8 cohort APKs** on ONE frozen binary with fresh data-roots: record `evidence/s228_census/s231_cold_runs_batch.json`, route matrix posted on #582 (comment 6860848974) with per-row status + exact first-divergence stage + next experiment.
- Shared-root-cause finding feeding §7's clustering rule: FOUR native routes (SDL2, SDL3, JNI-AI, libGDX-with-input) collapse to the SAME uniform (48,48,48) presented frame — the stage-H composition/presentation family (== #583's Mindustry `DEFAULT_BACKGROUND_ONLY`), with the SDL family's earliest shared divergence at stage C (`System.loadLibrary` REC-MISS in SDLActivity.<clinit>). The next shared fix (loadLibrary receiver law + structured ABI rows) and the full 10–20-title 3-baseline/3-post-fix protocol remain **honestly OPEN** — this receipt claims the census + the two §5 contracts, not the cohort completion.
"""

cred = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True, cwd=str(BASE)).stdout
token = [l.split("=", 1)[1] for l in cred.splitlines() if l.startswith("password=")][0]
req = urllib.request.Request(
    "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/585/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers={"Authorization": f"token {token}",
             "Accept": "application/vnd.github+json",
             "User-Agent": "s231-receipt"},
    method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    out = json.loads(r.read().decode())
    print(f"posted #585 comment id={out['id']}")
