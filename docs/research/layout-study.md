# Layout Study — MeasureSpec propagation and container laws

Sources: AOSP frameworks/base View.java / ViewGroup.java /
LinearLayout.java (mirror `1cdfff55`); MiniAndroid
`src/resources/real_layout.cpp`, `layout_inflater.cpp`, view shadows.

The core AOSP facts are cataloged as AOSP-001..AOSP-006 in
aosp-runtime-study.md; this file records what they MEAN for MiniAndroid.

## LAY-001 — The child spec table is complete and closed
getChildMeasureSpec (ViewGroup L7048) defines a 3×3 table
(parent EXACTLY/AT_MOST/UNSPECIFIED × child fixed/MATCH_PARENT/
WRAP_CONTENT). MiniAndroid implements this table; our fixtures cover
EXACTLY and AT_MOST parent modes across LinearLayout/FrameLayout/
RelativeLayout. The UNSPECIFIED parent row is untested (no corpus APK in
our set drives it; it appears in real Android for horizontal RV +
ScrollView measurement subtleties).
- Action: add one synthetic fixture with an UNSPECIFIED-measuring parent
  (or record explicitly as NOT EXERCISED BY CORPUS).
- Status: VERIFIED (covered rows) / documented (uncovered row).

## LAY-002 — measure() caching + guard are the correctness contract
Two View.measure() behaviors MiniAndroid should mirror (AOSP-001):
(a) spec-pair caching (performance only — skip), (b) the
"onMeasure must setMeasuredDimension" IllegalStateException guard
(correctness tripwire — adopt as debug assertion in view measurement).
- Status: IMPLEMENTATION CANDIDATE (guard only).

## LAY-003 — GONE children: skipped at measure AND layout (AOSP-005)
Weight redistribution in LinearLayout must ignore GONE children (they are
not measured, contribute 0 to mTotalLength and 0 weight).
- MiniAndroid action: fixture with GONE weighted child.
- Status: TEST CANDIDATE.

## LAY-004 — Two-pass weight distribution (AOSP-006)
LinearLayout collects totalWeight during the accumulation pass and
distributes remaining space AFTER all children measured; children with
weight are then measured with EXACTLY(remaining·weight/totalWeight) on the
main axis. MiniAndroid Cycle C weight implementation matches (12/12 PASS at
prior HEAD, horizontal + vertical).
- Status: VERIFIED (prior HEAD; re-run queued).

## LAY-005 — RelativeLayout edge rules and sentinel cleanup
No new AOSP reads this session (RelativeLayout.java is ~2600 lines of
dependency-graph sorting — my priority constraint views: sort children by
RELATIVE dependencies, then two passes horizontal/vertical). MiniAndroid's
Cycle C pinned edge rules + removed the `-1` sentinel pollution; the
implementation stands on its own fixtures.
- Status: VERIFIED (prior HEAD fixtures); deep AOSP diff deferred until a
  corpus app exercises advanced RTL/baseline rules.

## LAY-006 — min-width/min-height and text metrics interaction
View.java applies `mMinWidth/mMinHeight` in `resolveSizeAndState`-adjacent
default handling (resolveAdjustedSize path) — min clamps beat WRAP
shrinkage. MiniAndroid Cycle C implemented min w/h; interplay with text
metrics (baseline alignment) is covered by the baseline/vertical gravity
fixtures.
- Status: VERIFIED (prior HEAD).
