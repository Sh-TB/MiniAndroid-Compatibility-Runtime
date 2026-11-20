# BATCH 8 — Sweep S2: the 174 dropped attributes (verbatim from comment 7037681554)

## The 174 dropped attributes, grouped, with impact ranked

### NEW-34 (P0) — TextView: 56 dropped, including the ones that change measured size
`maxLines`, `minLines`, `lines`, `maxEms`, `minEms`, `ems`, `maxLength`, `textAlignment`, `textDirection`, `letterSpacing`, `breakStrategy`, `hyphenationFrequency`, `lineBreakStyle`, `textAllCaps`, `typeface`, `textFontWeight`, `fontVariationSettings`, `inputType`, `imeOptions`, `imeActionId`, `imeActionLabel`, `privateImeOptions`, `digits`, `numeric`, `password`, `phoneNumber`, `capitalize`, `editable`, `bufferType`, `autoLink`, `linksClickable`, `textColorHint`, `textColorLink`, `textColorHighlight`, `textIsSelectable`, `selectAllOnFocus`, `cursorVisible`, `scrollHorizontally`, `freezesText`, `editorExtras`, `marqueeRepeatLimit`, `shadowColor`, `shadowDx`, `shadowDy`, `shadowRadius`, `drawableLeft`, `drawableRight`, `drawableTop`, `drawableBottom`, `drawableStart`, `drawableEnd`, `drawablePadding`, `compoundDrawableTint`, `autoSizeTextType`, `autoSizeMinTextSize`, `autoSizeMaxTextSize`, `autoSizeStepGranularity`

**Note the contradiction that proves the gap is real:** `fonts/text_shaper.cpp:1386-1435` implements the AOSP `maxLines` / `singleLine` / `StaticLayout` law and `:1448-1484` implements `TextUtils.ellipsize` — but **`maxLines` is never parsed from XML**, so the shaper's `max_lines` can only be non-default when the app sets it programmatically. The law exists downstream and is starved upstream. Same for `letterSpacing` (HarfBuzz supports it) and `textAlignment`/`textDirection` (NEW-23's heuristic gap is partly *caused* by `textDirection` never being parsed).

Highest impact: **`maxLines`/`minLines`/`lines`** (height), **`drawableLeft/Start/…` + `drawablePadding`** (width and compound-drawable geometry), **`textAlignment`/`textDirection`** (RTL), **`letterSpacing`** (advance width), **`inputType`** (keyboard + height of EditText), **`autoSize*`** (text size).
`[R]` `TextView` XML attrs https://developer.android.com/reference/android/widget/TextView#xml-attributes · `StaticLayout` https://developer.android.com/reference/android/text/StaticLayout · autosizing https://developer.android.com/develop/ui/views/text-and-emoji/autosizing-textview · compound drawables https://developer.android.com/reference/android/widget/TextView#setCompoundDrawablesRelative(android.graphics.drawable.Drawable,%20android.graphics.drawable.Drawable,%20android.graphics.drawable.Drawable,%20android.graphics.drawable.Drawable)

### NEW-35 (P0) — `paddingStart` / `paddingEnd` / `paddingHorizontal` / `paddingVertical` dropped
Only `padding`, `paddingLeft/Right/Top/Bottom` are parsed. **Every RTL-aware layout in a modern app uses `paddingStart`/`paddingEnd`** (Android Studio templates emit them by default). Dropping them means content-box width/height are wrong for those views — a direct, systematic geometry error, and it compounds the RTL story even though the gravity RTL flip itself is correct.
`[R]` https://developer.android.com/reference/android/view/View#setPaddingRelative(int,%20int,%20int,%20int) · RTL support guide https://developer.android.com/training/basics/supporting-devices/languages

### NEW-36 (P0) — `clipChildren` / `clipToPadding` dropped → confirms NEW-30
Both have **zero occurrences** in the inflater. Combined with NEW-14 (no clip at the ImageView draw site), **there is no parent→child clipping anywhere**. Every oversized child overflows. This is now verified from both ends.
`[R]` https://developer.android.com/reference/android/view/ViewGroup#setClipChildren(boolean) · https://developer.android.com/reference/android/view/ViewGroup#setClipToPadding(boolean)

### NEW-37 (P0) — View transforms dropped: `alpha`, `translationX/Y/Z`, `scaleX/Y`, `rotation`, `rotationX/Y`, `pivotX/Y`, `transformPivotX/Y`
All zero-occurrence. Any XML-declared transform is ignored. (Programmatic setters may still work via `android_shadows.cpp` — that is a separate check — but the XML path loses them.) `alpha` in particular changes compositing, and the framebuffer has a correct SRC-OVER path that never gets exercised from XML.
`[R]` https://developer.android.com/reference/android/view/View#setAlpha(float) · https://developer.android.com/reference/android/view/View#setTranslationX(float) · property animation vs view transforms https://developer.android.com/develop/ui/views/animations/prop-animation

### NEW-38 (P0) — GridLayout weights and alignment dropped
`layout_rowWeight`, `layout_columnWeight`, `alignmentMode`, `useDefaultMargins`, `defaultMargin`, `rowOrderPreserved`, `columnOrderPreserved` — all zero-occurrence. The Bellman-Ford solver (batch 4) is real, but **`layout_columnWeight` is the attribute most real GridLayouts use to make equal columns**. Without it the solver has no weight arcs, so "three equal columns" cannot be expressed. This is very likely the actual mechanism behind the user's grid complaint — not a missing solver.
`[R]` `GridLayout.LayoutParams.weight` https://developer.android.com/reference/android/widget/GridLayout.LayoutParams · `GridLayout` XML attrs https://developer.android.com/reference/android/widget/GridLayout#xml-attributes · solver rationale [[44]] · spec/weight examples https://developer.android.com/reference/android/widget/GridLayout.Spec

### NEW-39 (P1) — LinearLayout: `baselineAligned`, `baselineAlignedChildIndex`, `measureWithLargestChild`, `divider`, `showDividers`, `dividerPadding` dropped
`baselineAligned` defaults to **true** in AOSP and changes horizontal-row child placement. `measureWithLargestChild` changes measurement of all weighted children. Both silently off.
`[R]` https://developer.android.com/reference/android/widget/LinearLayout#setBaselineAligned(boolean) · https://developer.android.com/reference/android/widget/LinearLayout#setMeasureWithLargestChildEnabled(boolean) · divider attrs https://developer.android.com/reference/android/widget/LinearLayout#setShowDividers(int)

### NEW-40 (P1) — `ScrollView.fillViewport` dropped
Zero occurrence. AOSP: when the content is shorter than the viewport, `fillViewport=true` stretches the child to fill it. Without it, short content leaves a gap and `match_parent` children inside collapse.
`[R]` https://developer.android.com/reference/android/widget/ScrollView#setFillViewport(boolean)

### NEW-41 (P1) — ImageView: `tint`, `tintMode`, `imageAlpha`, `cropToPadding`, `baseline`, `baselineAlignBottom` dropped
`cropToPadding` interacts directly with NEW-14 (the clip fix must respect it). `tint` is how most modern apps recolor vector icons — dropping it yields wrong colors, matching the "colors missing/flattened" symptom.
`[R]` https://developer.android.com/reference/android/widget/ImageView#setImageTintList(android.content.res.ColorStateList) · https://developer.android.com/reference/android/widget/ImageView#setCropToPadding(boolean)

### NEW-42 (P1) — ConstraintLayout: 17 dropped, including the sizing core
`layout_constraintWidth_default`, `layout_constraintHeight_default`, `layout_constraintWidth_min/max`, `layout_constraintHeight_min/max`, `layout_constraintWidth_percent`, `layout_constraintHeight_percent`, `layout_constraintDimensionRatio`, `layout_goneMarginLeft/Right/Top/Bottom`, `layout_constraintCircle`, `layout_constraintCircleRadius`, `layout_constraintCircleAngle`, `layout_optimizationLevel`.
The anchor attrs *are* parsed (batch-1 grep showed `layout_constraint*_to*Of`), but **percent sizing, dimension ratio and gone-margins are not** — those are the attributes that determine size, so anchors alone cannot produce correct rects.
`[R]` ConstraintLayout docs https://developer.android.com/develop/ui/views/layout/constraint-layout · `ConstraintLayout.LayoutParams` https://developer.android.com/reference/androidx/constraintlayout/widget/ConstraintLayout.LayoutParams · source https://github.com/androidx/constraintlayout

### NEW-43 (P1) — `fitsSystemWindows` dropped
Zero occurrence. `framework/window_insets_shadow.cpp` is a compiled TU, so insets machinery exists, but the XML flag that opts a view into inset padding is never read. Content stays under the status/navigation bars.
`[R]` https://developer.android.com/reference/android/view/View#setFitsSystemWindows(boolean) · edge-to-edge/insets guide https://developer.android.com/develop/ui/views/layout/edge-to-edge

### NEW-44 (P1) — `backgroundTint` / `backgroundTintMode` / `foreground` / `foregroundGravity` / `foregroundTint` / `clipToOutline` / `outlineProvider` dropped
Material buttons and cards rely on `backgroundTint` for their color; dropping it yields the untinted drawable — again the "wrong color" family. `clipToOutline` + `outlineProvider` are how rounded-corner clipping is done on API21+.
`[R]` https://developer.android.com/reference/android/view/View#setBackgroundTintList(android.content.res.ColorStateList) · https://developer.android.com/reference/android/view/View#setClipToOutline(boolean) · `ViewOutlineProvider` https://developer.android.com/reference/android/view/ViewOutlineProvider

### NEW-45 (P1) — AbsListView/GridView: 10 dropped
`listSelector`, `drawSelectorOnTop`, `choiceMode`, `cacheColorHint`, `dividerHeight`, `fastScrollEnabled`, `smoothScrollbar`, `stackFromBottom`, `transcriptMode`, `scrollIndicators`. `stackFromBottom` + `transcriptMode` change item placement order in chat-style lists; `dividerHeight` changes every item offset.
`[R]` https://developer.android.com/reference/android/widget/AbsListView#xml-attributes · https://developer.android.com/reference/android/widget/ListView#setStackFromBottom(boolean)

### NEW-46 (P1) — Focus / accessibility / misc View attrs dropped (remaining ~30)
`focusable`, `focusableInTouchMode`, `nextFocusUp/Down/Left/Right/Forward`, `longClickable`, `contentDescription`, `importantForAccessibility`, `labelFor`, `screenReaderFocusable`, `accessibilityTraversalBefore/After`, `keepScreenOn`, `hapticFeedbackEnabled`, `soundEffectsEnabled`, `filterTouchesWhenObscured`, `duplicateParentState`, `saveEnabled`, `layerType`, `hardwareAccelerated`, `isScrollContainer`, `scrollbars`, `scrollbarSize`, `scrollbarStyle`, `fades`, `fadeScrollbars`, `fadingEdgeLength`, `requiresFadingEdge`, `tooltipText`, `defaultFocusHighlightEnabled`, `keyboardNavigationCluster`.
`longClickable` matters for input tests (the mission requires a real input event + state change); `scrollbars`/`fadingEdgeLength` affect visible pixels; `layerType` affects compositing.
`[R]` https://developer.android.com/reference/android/view/View#xml-attributes · accessibility https://developer.android.com/guide/topics/ui/accessibility/apps

### NEW-47 (P1) — ViewGroup animation/flags dropped
`animateLayoutChanges`, `layoutAnimation`, `splitMotionEvents`, `descendantFocusability`, `addStatesFromChildren`, `layoutMode`, `animationCache`, `persistentDrawingCache`. `animateLayoutChanges` triggers `LayoutTransition` which animates child rects — unimplemented means both wrong pixels and wrong intermediate geometry.
`[R]` https://developer.android.com/reference/android/view/ViewGroup#setAnimateLayoutChanges(boolean) · `LayoutTransition` https://developer.android.com/reference/android/animation/LayoutTransition

### NEW-48 (P1) — `FrameLayout.measureAllChildren` and `RelativeLayout.ignoreGravity` and `layout_alignBaseline` dropped
`measureAllChildren=true` forces GONE children to be measured too (affects the parent's wrap size). `layout_alignBaseline` is a commonly used RelativeLayout rule that the otherwise-complete dependency graph (batch 4) cannot receive from XML.
`[R]` https://developer.android.com/reference/android/widget/FrameLayout#setMeasureAllChildren(boolean) · https://developer.android.com/reference/android/widget/RelativeLayout.LayoutParams#addRule(int,%20int)

---

