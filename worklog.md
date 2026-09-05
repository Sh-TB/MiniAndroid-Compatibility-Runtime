# Worklog — /home/z/my-project/worklog.md (system-level)

---
Task ID: G31-G48 (MiniAndroid typography campaign)
Agent: Super Z (main agent)
Task: Close G31–G48 REAL FONT / TEXT / TYPOGRAPHY gates on the external
EXT-01 HelloWorldSelfAware fixture; rerun GOLDEN-01; extend battery;
persist evidence to GitHub.

Work Log:
- Read prior state (repo worklog at MiniAndroid-Compatibility-Runtime/worklog.md,
  gate records under docs/evidence/). HEAD d1244ec9, clean tree.
- Re-established wiped sandbox state: fixture APK + reference re-fetched with
  exact SHA-256 match; aapt2 restored; gh token missing → PUSH/COMMENT BLOCKED.
- G31: APK AXML attr dump (scripts/dump_axml_attrs.py) — fontFamily='monospace',
  lineSpacingMultiplier=2.0, elegantTextHeight=true, textAppearance=Large, no
  textSize. AOSP fonts.xml/styles.xml laws fetched at android-14/15/16 tags.
- G32: DroidSansMono.ttf shipped (system image), family resolution law +
  ARSC version-qualifier law fixed (device size=0 bug; apk_path_for config
  matching bug). Runtime FONT_RESOLUTION evidence line added.
- G33–G35: FreeType probe harness (tests/font_pipeline_probe.cpp) — glyph
  metrics evidence committed.
- G36/G37: Paint.FontMetrics + StaticLayout line-box laws implemented; ad-hoc
  leading laws removed.
- G46: TextAppearance.Large→22sp→58px law (TypedValue rounding) implemented.
- G47: lineSpacingMultiplier/Extra/includeFontPadding/elegantTextHeight
  parsed and plumbed into measure+draw.
- G48: typography comparator (scripts/compare_ext01_typography.py) — 9/9
  static checks PASS; 3-run byte-identical determinism; docs written.
- Battery extended to 16 stages; BATTERY GATE ALL PASS at final HEAD.
- Commits d2d4469a, ea51d96a, 598e2432, b9e6e66f, 98794ed0, f2717ab6 (+C1
  d2d4469a diag). Push attempted → no credentials (recorded). Comment
  payloads prepared at scripts/post_typography_comments.py.

Stage Summary:
- GOLDEN-01 typography closed: 9/9 static visual checks PASS; regression
  unchanged (26/26, 8/8, 14/14, 96/96, corpus apps SUCCESS); battery 16/16.
- Campaign worklog appended at MiniAndroid-Compatibility-Runtime/worklog.md.
- NEXT GATE: GOLDEN-02-EXTERNAL-INTERACTIVE-VISUAL. Persistence needs a
  GitHub token (fast-forward push + 3 prepared issue comments).

---
Task ID: GOLDEN-02 (+P1/P2/P3)
Agent: Super Z (main agent)
Task: GOLDEN-02 external interactive visual gate; resource-config
regression; DexFile + dexHunter research integration; regression battery;
GitHub persistence.

Work Log:
- Ground truth verified at bb54cdb1: clean tree, battery present and
  committed, EXT-01 hash 009b4671…cc41 matched, full regression reproduced
  (26/26, 8/8, 14/14, 96/96, GOLDEN-01 9/9, corpus 3/3).
- Interaction chain proven from APK bytes (scripts/dump_apk_interaction.py,
  7/7 links): MainActivity implements View$OnLongClickListener; onCreate →
  TextView.setOnLongClickListener(this); onLongClick(View)Z = copyText →
  ClipData.newPlainText → setPrimaryClip → Toast.makeText/show, returns
  TRUE (const/4 v1,0x1; return v1 @[29]).
- Implemented generic platform behavior: dispatch_long_click (AOSP
  performLongClick + consumption law, BOOLEAN-or-INT32 return), --long-press
  <x>,<y> + stage_long_press (hit test → 500ms law → UP-click suppression
  per mHasPerformedLongPress), LONG_CLICKABLE touchability in hit testing,
  ClipboardShadow (newPlainText/setPrimaryClip/getPrimaryClip/getText +
  legacy setText) registered on BOTH engine-facing registries (root cause
  of first-run miss: main.cpp owns a separate ShadowRegistry).
- GOLDEN-02 evidence: BEFORE/AFTER frames committed; Rule-10 comparator
  (scripts/compare_ext01_interaction.py) 12/12 static checks PASS —
  toast bbox (428,1768)-(650,1823), 12,488 changed px, text block
  pixel-identical; 3 runs byte-identical (frame_001 SHA e242ac1e…d7a0).
- P1: ResolvedResource::best_for(device) + apk_path_for(device) overloads
  (pure refactor) + tests/resource_config_selection_test.cpp — synthetic
  ARSC builder, 19/19 checks (version tie-break law, requested.size gate,
  both table orders). Battery stage added.
- P2/P3: audited vova7878/DexFile @1616ed0c + zyq8709/dexHunter @9d829a9f.
  FIND-REUSE-DEX-001/002/003 implemented+tested (ARRAY/ANNOTATION desync,
  sign-extension law, CHAR unsigned + FLOAT/DOUBLE right-zero-extension)
  via src/dex/encoded_value.h + tests/encoded_value_law_test.cpp (18/18).
  FIND-REUSE-ART-001..004 recorded (alignment + researched gaps). Nothing
  marked verified from source inspection alone.
- Battery now 23 stages: BATTERY GATE ALL PASS at HEAD 65a839a7.
- Commits: 7babcbd6 (GOLDEN-02), e38109a0 (P1), 65a839a7 (P2/P3).
- GitHub: push BLOCKED (no token/gh/credential helper; "could not read
  Username" recorded) — 13 commits pending push, evidence complete local.

Stage Summary:
- GOLDEN-02 = CLOSED: real external APK interaction (user-like long press
  → real listener dispatch → clipboard state mutation → Toast → second
  frame → 12/12 checks → 3-run determinism → full regression PASS).
- NEXT GATE (proposal only): resource variant selection is now
  regression-guarded; candidate next: input-path depth (ACTION_MOVE
  cancel semantics / multi-touch) or Toast typography law vs device
  reference — to be decided by the next execution request.
