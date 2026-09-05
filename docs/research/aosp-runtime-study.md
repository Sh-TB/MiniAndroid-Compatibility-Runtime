# AOSP Runtime Study — framework/base, ART, dalvik, frameworks/native

Studied (revisions in `external-repositories.md`):
- frameworks/base mirror `1cdfff555f4a21f71ccc978290e2e212e2f8b168` (2025-03-26)
- ART official `6484611fd45e69db9f33f98bfd6864014b030ecf` (2025-03-26)
- frameworks/native official `4f463a6b1de9198963dc6aff74154a504ba3f8f6`
- dalvik mirror (historical docs)

Method: targeted reads of the exact files that implement the behaviors
MiniAndroid emulates. Each item cites path + symbol. IDs follow `AOSP-###`.

## AOSP-001 — View.measure() is a final template method with caching
- Source: `core/java/android/view/View.java` `public final void measure(int, int)` (~L28320)
- Mechanism: (a) optical-insets adjustment of specs; (b) spec pair packed as
  `long key = widthSpec << 32 | heightSpec` cached in `mMeasureCache`;
  (c) re-measure only when `forceLayout || needsLayout` where needsLayout =
  specChanged && (alwaysRemeasure || !bothExact || sizeMismatch);
  (d) after `onMeasure`, if the measured-dimension flag is unset it throws
  `IllegalStateException("View with id ... did not set the measured dimension")`;
  (e) success sets `PFLAG_LAYOUT_REQUIRED`.
- MiniAndroid mapping: our measure pass mirrors the contract (view_renderer /
  real_layout) but has no spec-pair cache and — importantly — no equivalent
  of the "onMeasure must set measured dimension" guard. The guard is a
  correctness tripwire worth adopting for our ViewShadow measurement.
- Status: DISCOVERED → candidate guard.

## AOSP-002 — resolveSizeAndState / getDefaultSize semantics
- Source: `View.java` `public static int resolveSizeAndState(...)` (~L28530),
  `public static int getDefaultSize(...)`
- Mechanism: AT_MOST → `min(size, specSize)`, setting
  `MEASURED_STATE_TOO_SMALL` when clamped; EXACTLY → specSize; UNSPECIFIED →
  content size. `getDefaultSize` maps BOTH AT_MOST and EXACTLY → specSize
  (the classic reason a raw View ignores wrap_content).
- MiniAndroid mapping: our real_layout implements the same three-mode
  resolution; the `MEASURED_STATE_TOO_SMALL` bit and the
  `combineMeasuredStates` accumulation across children are NOT modeled.
  Relevant only for composite apps that inspect getMeasuredState() —
  low corpus evidence so far. Status: DOCUMENTED, deferred.

## AOSP-003 — getChildMeasureSpec: the child spec table
- Source: `core/java/android/view/ViewGroup.java` `public static int getChildMeasureSpec(int spec, int padding, int childDimension)` (L7048)
- Mechanism (verbatim table): parent EXACTLY → child fixed dim ≥ 0: EXACTLY(childDim);
  MATCH_PARENT: EXACTLY(size); WRAP_CONTENT: AT_MOST(size).
  Parent AT_MOST → child fixed: EXACTLY(childDim); MATCH_PARENT: AT_MOST(size);
  WRAP_CONTENT: AT_MOST(size). Parent UNSPECIFIED → fixed: EXACTLY(childDim);
  MATCH_PARENT/WRAP_CONTENT: UNSPECIFIED(size). `size = max(0, specSize - padding)`.
- MiniAndroid mapping: our `real_layout` re-implements this table; the prior
  campaign's 12/12 layout fixtures exercise EXACTLY/AT_MOST ×
  MATCH/WRAP/fixed for LinearLayout/FrameLayout/RelativeLayout. This AOSP
  read confirms the table we implement is complete for ViewGroup (the
  UNSPECIFIED row is the only one we do not currently test).
- Status: VERIFIED (table parity); add UNSPECIFIED-row fixture later.

## AOSP-004 — measureChild vs measureChildWithMargins
- Source: `ViewGroup.java` L6988 / L7005
- Mechanism: margins are added to padding when deriving the child spec
  (`mPaddingLeft + mPaddingRight + lp.leftMargin + lp.rightMargin + widthUsed`),
  only `MarginLayoutParams` callers use the WithMargins variant.
- MiniAndroid mapping: our margin handling came from Cycle C fixtures
  (horizontal + vertical). Parity confirmed. Status: VERIFIED.

## AOSP-005 — measureChildren skips GONE children
- Source: `ViewGroup.java` `protected void measureChildren(...)` (L6968)
- Mechanism: `if ((child.mViewFlags & VISIBILITY_MASK) != GONE)` — GONE
  children are skipped for measure AND must be skipped for layout.
- MiniAndroid mapping: our inflater/renderer tracks visibility; GONE-skip is
  implemented for render, but our measure path must also skip GONE (fixture
  candidate: a GONE child inside a LinearLayout with weights — weight
  redistribution must ignore it). Status: DISCOVERED → test candidate.

## AOSP-006 — LinearLayout measure: total length + weight two-pass
- Source: `core/java/android/widget/LinearLayout.java` `measureVertical` (L808)
  / `measureHorizontal`
- Mechanism: single accumulation `mTotalLength` along the main axis with
  `totalWeight` collected; weight distribution happens after the first
  measurement pass (children with weight get remeasured/exactly-sized from
  remaining space); divider heights participate in accumulation.
- MiniAndroid mapping: our weight implementation (Cycle C) matches the
  remaining-space distribution; two-pass remeasure subtlety (weight children
  measured with exact remaining) is what our tests pin. Status: VERIFIED.

## AOSP-007 — Resources.getString/getText chain
- Source: `core/java/android/content/res/Resources.java` L464/L564/L588
- Mechanism: `getString(id)` → `getText(id).toString()` (styled text
  stripped); `getString(id, formatArgs)` → `String.format(locales.get(0), raw, args)`
  — locale from configuration; `NotFoundException` on bad id.
- MiniAndroid mapping: our ARSC-first `setText(resid)` path implements
  string resolution (Cycle D, RESULT_016 family). Format-args substitution
  (`getString(id, args)` with `%1$s` etc.) is implemented at the shadow
  layer but its locale behavior is untested (we run with a single default
  locale). Status: PARTIALLY VERIFIED — add a format-args fixture.

## AOSP-008 — Resources.getIdentifier contract
- Source: `Resources.java` L2325
- Mechanism: name/type/package string lookup returning 0 when absent —
  0 is an INVALID identifier and callers must treat it as failure.
- MiniAndroid mapping: our getIdentifier shadow returns 0 on miss (matches);
  corpus evidence (openlauncher ROOT-ASSETS discovery) exercised it.
  Status: VERIFIED.

## AOSP-009 — Handler message dispatch priority
- Source: `core/java/android/os/Handler.java` `dispatchMessage(Message)` (L101)
- Mechanism: `msg.callback != null` → run the Runnable (handleCallback);
  else `mCallback` gets first refusal (if it returns true, stop); else
  `handleMessage(msg)`.
- MiniAndroid mapping: our Runnable/click dispatch implements
  post(Runnable) + click listeners through the shadow registry; the
  three-tier priority (Runnable > callback > subclass handleMessage) is the
  exact contract to keep when we expand Handler coverage. Status: VERIFIED
  for our two implemented tiers; third tier (mCallback) not covered by any
  fixture yet — gap noted in external-gap-analysis.md.

## AOSP-010 — Paint.Style and the FILL_AND_STROKE winding caveat
- Source: `graphics/java/android/graphics/Paint.java` `enum Style` (L568)
- Mechanism: FILL(0), STROKE(1), FILL_AND_STROKE(2); AOSP doc: FILL_AND_STROKE
  "can give unexpected results if the geometry is oriented counter-clockwise"
  (Skia legacy behavior), FILL/STROKE unaffected. Default Paint carries
  ANTI_ALIAS_FLAG (0x01) since S-era constructor (`setFlags(HIDDEN_DEFAULT_
  PAINT_FLAGS | ANTI_ALIAS_FLAG)`).
- MiniAndroid mapping: our software_renderer implements fill/stroke/
  fill-and-stroke with explicit winding rules from Cycle E; we should pin
  the same caveat in a fixture (counter-clockwise rect with
  FILL_AND_STROKE). Status: PARTIALLY VERIFIED (fill+stroke tested;
  CCW-caveat not pinned).

## AOSP-011 — Path.FillType numeric values are ABI
- Source: `graphics/java/android/graphics/Path.java` `enum FillType` (L200)
- Mechanism: WINDING(0), EVEN_ODD(1), INVERSE_WINDING(2), INVERSE_EVEN_ODD(3)
  with comment "these must match the values in SkPath.h"; default fill type
  is WINDING.
- MiniAndroid mapping: Cycle E implemented winding rules + even-odd for
  fill/stroke discrimination; our enum values follow the same numbering.
  Status: VERIFIED at implementation level (pixel-discriminated fixtures).

## AOSP-012 — Canvas save/restore and clip API surface
- Source: `graphics/java/android/graphics/Canvas.java` save(L443)/restore(L660)/
  clipPath(L1077)/drawPath(L1929)/drawRoundRect(L2068)/drawArc(L1550)
- Mechanism: save/restore is a stack with `getSaveCount()`; clip variants
  return boolean (true if the clip changed); drawRoundRect has both RectF
  and (l,t,r,b) overloads; drawArc takes startAngle/sweepAngle/useCenter.
- MiniAndroid mapping: canvas_shadow implements the same surface; the
  boolean-return contract of clip* and the save-count semantics are the
  parts our fixtures pin. Status: VERIFIED (regression battery).

## AOSP-013 — SharedPreferencesImpl: async-commit-with-sync-get contract
- Source: `core/java/android/app/SharedPreferencesImpl.java`
- Mechanism: `getString`/`getInt` read from an in-memory map; first load
  blocks (`awaitLoadedLocked`); `apply()` writes through a memory commit +
  async disk task; `commit()` returns boolean synchronously. Reads after a
  write in the same process see the write (memory commit is immediate).
- MiniAndroid mapping: our storage shadow implements get/put strings/ints +
  apply with file persistence; the read-your-write guarantee is what our
  click→state→SharedPreferences tests exercise. Status: VERIFIED for the
  implemented subset; editor listeners (onSharedPreferenceChanged) are not
  modeled — gap noted.

## AOSP-014 — Activity lifecycle as the root execution contract
- Source: `core/java/android/app/Activity.java` (+ `Instrumentation.callActivityOnCreate`)
- Mechanism: onCreate(Bundle) → setContentView → onResume; window/decor
  creation precedes content inflation; `Instrumentation` is the injected
  call boundary (testability seam).
- MiniAndroid mapping: application_runtime + android_shadows implement
  onCreate/onResume + setContentView; the Instrumentation seam is where our
  click-injection probes attach. Status: VERIFIED via tictactoe_golden run.

## AOSP-015 — ART DexFileVerifier verification order (the DEX law)
- Source: `art/libdexfile/dex/dex_file_verifier.cc` `DexFileVerifier::Verify()` (L3546)
- Mechanism: order is CheckHeader → CheckMap → CheckIntraSection (per-section
  structural checks incl. CheckIntraClassDataItem{Fields,Methods}) →
  CheckInterSection (cross-section reference checks); access-flag validation
  (`kAccJavaFlagsMask` overflow, at-most-one-of public/protected/private,
  interface-restricted lists); endian tag constant `0x12345678` defined in
  `dex_file.h`.
- MiniAndroid mapping: our DEX loader validates header/tables eagerly but
  does not implement the full intra/inter-section verification suite
  (deliberately — we are a runtime, not a verifier; corrupt inputs are
  rejected at access time). The ORDER of checks (header before map before
  indices before references) is the useful invariant for our diagnostics
  messages. Status: DOCUMENTED; adopt order, not full verifier.

## AOSP-016 — ART compact-Dex detection
- Source: `art/libdexfile/dex/compact_dex_file.h`; also WineDroid dex.rs rejects `cdex`
- Mechanism: cdex magic distinct from `dex\n`; ART supports it (dex2oat
  output), classic DEX loaders reject it.
- MiniAndroid mapping: corpus APKs use classic DEX; our loader would fail
  on cdex with a generic error. Cheap improvement: name `cdex` explicitly
  like WineDroid does. Status: DISCOVERED → one-line diagnostic improvement.

## AOSP-017 — frameworks/native: the input/render boundary MiniAndroid skips
- Source: `frameworks/native/services/surfaceflinger/`, `libs/binder/`
- Mechanism: real Android routes input via Binder → InputDispatcher →
  window; rendering via BufferQueue to SurfaceFlinger. MiniAndroid
  deliberately collapses this to direct dispatch into the view tree +
  in-process framebuffer — the same collapse cuttlefish-style hosts avoid
  by virtualizing instead. The study value is confirming our boundary
  choice is the standard "userspace runtime" shortcut (same choice as
  WineDroid's future Wayland plan and waydroid's host compositor).
- Status: ARCHITECTURE VALIDATION (no transfer).
