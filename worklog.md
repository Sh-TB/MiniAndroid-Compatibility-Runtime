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
---
Task ID: GOLDEN-03
Agent: Super Z (main agent)
Task: GOLDEN-03 RESOURCE COMPATIBILITY INFRASTRUCTURE + RESOURCE→PIXEL; plus
user-requested GitHub persistence of all prior GOLDEN-01/GOLDEN-02 commits.

Work Log:
- GitHub persistence (user request): token installed at /home/z/.gh_token
  (mode 600, never printed), auth verified (login Sh-TB), 14 unpushed
  commits (G31–G48 + GOLDEN-01 + GOLDEN-02) pushed to main, verified
  0/0 with ls-remote; G31–G48 + GOLDEN-02 evidence comments posted to
  Issue #8 with read-back (issuecomment-5555363421, -5555363541).
- Ground truth: sandbox wipe had removed aapt2 + the EXT-01 fixture — both
  restored per documented procedures (Google Maven 8.13.2-14304508;
  Appliberated v1.1.0 release URL), SHA-256 verified exactly
  (009b4671…cc41). Battery reproduced.
- §3/§4/§6/§7/§9 core (3c87e279): res_id.{h,cpp} canonical ResId +
  TypedValue laws; ArscParser::resolve_full → ResolutionResult with
  selected-config-per-step, bounded depth (16), cycle detection, NAMED
  errors; bag_value with parent inheritance; FRACTION decode.
  tests/synthetic_arsc.h + resource_core_law_test 42/42.
- §5 (724e5a0b): config matrix 19 → 48 checks (locale/density/orientation/
  sw/w/uiMode/screen; density does NOT reject in match() — AOSP
  closest-bucket law documented).
- §7/§10 (86f47365): resource_values.json sidecar override REMOVED from
  production path; integers/raw ARSC-first; drawable paths ARSC-first via
  value-IS-path law; manifest AxmlDataType aligned to AOSP Res_value.
- §8/§9 (bf3056c1): key-aware apply_style (byte-verified attr ids),
  style values reach the node, textAppearance generic via bag_value +
  byte-verified framework table, ONE dimension path everywhere, engine
  setTextSize unit constants fixed (PX=0 DIP=1 SP=2).
- §12/§13 (d306f1e2): tools/resource_trace (make resource_trace) +
  docs/RESOURCE_MATRIX.md + dump_ext01_attr_ids.py oracle.
- §14 (40eaca85): parse_type_chunk hardening (entryCount OOB read fixed)
  + resource_hostile_test 18/18; battery 23 → 27 stages.
- §15/§16 (6c352981): evidence harness EXPOSED a real determinism
  violation — DroidSansMono.ttf resolved cwd-relative; fixed via
  /proc/self/exe-relative law. 3-run byte-identity restored to the frozen
  G48 golden SHA 142238fd…bbf2; chains A/B/C 6/6; typography 9/9.
- Docs: FIND_REUSE_RES.md (FIND-REUSE-RES-001..008), GOLDEN03 record A–H.

Stage Summary:
- GOLDEN-03 = VERIFIED per §22 checklist (all 17 boxes): canonical ids,
  generic config selection, traceable selected config, TypedValue
  semantics, generic references with cycle safety, generic bags/themes,
  dimension/density law, ARSC-first strings (sidecar removed), AXML
  canonical resolver, hostile-input safety, resource_trace tooling,
  external resource→view→pixel (chains A/B/C), 3-run determinism,
  battery 27/27, no fixture-specific code, reproducible from HEAD.
- Battery is now 27 stages: ALL PASS at HEAD 6c352981 (pre-push).
- Next gate proposal is NOT part of this execution (per §21/§22 rule).
