# R-NEW-388 — S71 FORENSIC RE-MEASUREMENT (source→layout chain)

## Chain (per mandate: source → model → View → measure → layout → bounds → draw)

1. SOURCE (pinned VelbazhdSoftwareLLC/TriPeaksSolitaireForAndroid @ 62f3609,
   docs/upstream/apps/tripeaks/activity_game.xml): board labels/cards use the
   RelativeLayout idiom `alignParentBottom/alignParentLeft + marginBottom/
   marginLeft` stacks and sibling anchors — generic Android XML, no custom
   layout class.
2. MODEL: engine RelativeLayout laws present and source-linked
   (miniandroid/src/resources/layout_inflater.cpp:1071-1119 attribute parse;
   :1691/:1812 applyHorizontalSizeRules/VerticalSizeRules port; rl_cached_left
   recorded :1870, consumed :2755).
3. MEASURE/LAYOUT/BOUNDS re-measured TODAY on the S66-planned generic fixture
   (f14_relative.apk, current binary, real-dalvik):
   - alignParentRight child → x = 780 = parentW - childW  (correct)
   - centerInParent child → (340, 760) = exact center math (correct)
   - below=/margin chain child → y = 300 stack (correct)
   - no child collapsed at (0,0)
4. DRAW: painter already proven faithful in S66 (canvas probe byte-identical).

## Verdict (classification per S71 rule for R-NEW-388)

- The GENERIC foundation law (RelativeLayout measure/anchor rules) is
  **IMPLEMENTED-CORRECT** on the current binary — the S66 "cards collapsed at
  (0,0)" state does NOT reproduce on the generic fixture. The S66-era claim
  was source-linked to the then-current wiring and is stale for HEAD.
- The TriPeaks game-screen geometry is **NOT RE-MEASURABLE in the canonical
  window today**: fresh s71_live run shows the app blocked at SplashActivity
  (ViewTree = RelativeLayout + WebView + splash handler only, 3 nodes,
  9 frames). The blocker is the app's splash-navigation structure (WebView
  splash + timer), i.e. an app-level sequencing fact, not a foundation
  layout law.
- Per the S71 mandate ("app-specific logic → not counted as foundation"),
  TriPeaks card geometry is **demoted from the foundation gap list** until
  splash navigation is crossed; the evidence-backed residual is recorded as
  `BLOCKED-AT-SPLASH (app-specific path; generic RL law proven on fixture)`.

Evidence: run/s71_f14/view_tree.json (current binary);
docs/foundation/s71/family_ranking.json; fresh diagnose bundle
run/s71_diag/R-NEW-388.txt.
