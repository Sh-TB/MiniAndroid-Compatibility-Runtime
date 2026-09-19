# FOUNDATION_LAYOUT_MATRIX — canonical (S67)

Verified via micro-fixtures f11 (weights), f13 (FrameLayout gravity), f14
(RelativeLayout rules), f18 (LL cross-axis), each with ViewTree geometry +
independent pixel assertions.

| Contract | Status | Evidence / Law |
|---|---|---|
| layout_width/height (match/fill/wrap/dp/px) | PROVEN | f01/f11/f13/f14 pixel-exact; resolve_size_or_match law |
| layout_margin (+L/T/R/B) | PROVEN | f11/f13 margins honored in measure+layout |
| padding | PROVEN | hello_color + f13; content-origin law |
| layout_weight (LL, 0dp+weight, re-measure) | PROVEN | f11: 640px thirds byte-exact; AOSP L985-1045 port |
| weightSum | PROVEN | measure+layout share cap |
| orientation (unset=HORIZONTAL law) | PROVEN | f18 horizontal default |
| FrameLayout gravity (container+child) | PROVEN | f13 TL/center/BR exact |
| FrameLayout margins (R-NEW-302) | PROVEN | prior golden + f13 |
| LinearLayout vertical stacking | PROVEN | f01 bands |
| LinearLayout horizontal | PROVEN | f18 (C3 fixed) |
| LinearLayout cross-axis gravity | PROVEN (S67 C3 fix) | f18: layout_gravity="top" → y=0; was centered (0x30 fell into center) |
| RelativeLayout alignParent* / center* | PROVEN | f14: anchor/belowv/centerInParent pixel-exact |
| RelativeLayout below/above | PROVEN | f14 belowv y=300 (anchor bottom) |
| RelativeLayout toRightOf / toLeftOf | PROVEN | f14 rightof x=300 |
| RelativeLayout alignLeft/Right/Top/Bottom | PROVEN | f14 alignTop |
| RL solver→replay→measured_left chain | PROVEN | b60f753c closed the loop (R-NEW-388 as phrased REFUTED) |
| RL programmatic children (rl_edges_valid=false) | PARTIAL | fixed-point fallback (C1, registered) |
| RL render-without-measure path | PARTIAL | legacy fallback lacks RL branch → (0,0) pile (C2, registered; TriPeaks PARTIAL) |
| wrap_content | PROVEN | aggregate + AT_MOST min law (census) |
| match_parent | PROVEN | f01/f11/f13 |
| Nested ViewGroups | PROVEN | f14 (RL root) + corpus |
| AbsoluteLayout / programmatic x-y LayoutParams | MISSING (B5) | x/y silently dropped |
| View.setX/setTranslationX/setY | MISSING (B5) | not implemented |
| ScrollView scrolling (scrollY) | MISSING (B6) | no scroll offset anywhere |
| View-level android:theme at inflate | MISSING (B11) | ?attr/theme branch absent (A1) |
| gravity attr → container+text conflation | PARTIAL (C4) | harmless in practice; documented |
| requestLayout/invalidate | PARTIAL (C5/C6) | whole-tree re-measure per frame; invalidate no-op; no dirty region |
| ViewTree↔pixel coordinate same-source | PROVEN | single write site layout_inflater.cpp:2353-2358 (x==measured_left) |
