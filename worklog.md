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

---
Task ID: G04+G05
Agent: Super Z (main agent)
Task: Unified G04 (drawable/image) + G05 (layout/measure/render) compatibility
closure campaign on the frozen-APK corpus.

Work Log:
- Baseline blind-verified: HEAD cc42a891, battery ALL PASS, G03 reproducible,
  EXT-01 fixture + reference + aapt2 + corpus re-frozen after sandbox wipe
  (SHA-exact), 3-run determinism re-proven (142238fd92b69e11).
- §0 finding: resource_trace.cpp never committed (FIND-001) → make target
  broken at HEAD; device split 480/420 (FIND-002); drawable selection by
  ZIP-path string rank (FIND-003); zero density scaling (FIND-004);
  Fossify Notes = Compose (FIND-005); KISS/Markor blank = AppCompat shell
  (FIND-006).
- AOSP laws fetched at android-14.0.0_r2 (ImageView/ViewGroup/LinearLayout/
  BitmapFactory java+native/ResourceTypes/BitmapDrawable/View).
- C2 768b1481: unified 420dpi device; select_file (canonical chain-safe
  drawable selection with selected-config density); BitmapFactory scaling;
  FIT_CENTER; header-only ImageSizeProbe; intrinsic measure.
- C3 291914c7: resource_trace recreated (repair) + G04/G05 channels
  (density, file/XML/BINARY, intrinsic, --bag, --layout inflate+measure dump).
- C4 894e6ef3: EXACT LinearLayout weight law (sequential shares, 0dp+weight
  skip/from-scratch, base+share shrinkable, weightSum, subtree re-measure) +
  3 MeasureSpec/layout fixes (padding double-count; cross-axis measured dims;
  re-measure propagation) + 24-check battery.
- C5 e7e6ec1b: density-matrix differential oracle — aapt2-built fixture,
  color-coded buckets, 11-check gate, 3-run deterministic (351340a7…).
  Proves: straddle law (420dpi→xxxhdpi 26×13), exact bucket (320dpi→xhdpi
  40×20), DENSITY_NONE never scaled, alias chain, FIT_CENTER.
- C6 ae37abf4: hostile battery 24/24 (probe/decoder/cycles/depth/weights).
- C7 3d1eba51: DIRECT resid→select_file resolution (FIND-007, Markor 0/35
  root cause) + AppCompat boundary record.
- Final battery: ALL PASS (31 stages) at e371a82b. GitHub PUSH/COMMENT
  BLOCKED (no token this session; 403 on anonymous write — recorded).

Stage Summary:
- G04+G05 CLOSED — VERIFIED WITH EXPLICIT NON-BLOCKING BOUNDARIES:
  pipeline REAL APK→ARSC→config→TypedValue→drawable→density→inflate→
  measure→layout→render→deterministic PNG runtime- and pixel-proven on
  classic-View APKs; boundaries: AppCompatDelegateImpl shell (G06+),
  NinePatch chunks, nearest-neighbour resampling note.
- 8 commits local (e98cf4b0…e371a82b), fast-forward-ready on origin/main.
- NEXT: provide GitHub token → push + post scripts/issue_comment_g0405.md;
  G06 candidate: AppCompatDelegate shell emulation.

---
Task ID: G06-G08
Agent: Super Z (main agent)
Task: Unified G06 (state/input/interaction) + G07 (lifecycle/main thread/
frames) + G08 (multi-Activity/Intent/result/back) compatibility closure.

Work Log:
- P0 persistence: token verified, 10 unpushed G04+G05 commits pushed
  (67812290), payload posted → issuecomment-5558532580.
- §1 baseline after full sandbox wipe: runtime rebuilt, EXT-01/reference/
  aapt2/corpus re-frozen SHA-exact; battery 31/31; all frozen hashes
  reproduced (142238fd92b69e11, e242ac1e9c8cc224, 351340a7a92e645c).
- Initial audit published (c3a083e4 → issuecomment-5558625727).
- G06 (7ba05034 + a0ac4544): TouchDispatcher (View.onTouchEvent law:
  touchable/disabled/DOWN-press/UP-post(PerformClick)+UnsetPressed(64ms)/
  focusTaken/CANCEL/MOVE-slop), StateListDrawable per-frame re-pick,
  framework tokens on the ONE HandlerShadow queue, --tap CLI; fixed
  FIND-G06AUDIT-003 (typed COLOR bg) + -004 (LinearLayout margin law,
  both axes); law battery 45/45; interaction golden 21/21 + 3-run
  byte-identity (pressed #FF5252 visible mid-gesture; disabled 0 px).
- G07 (83ebbf3f): LifecycleController (guarded machine + restart law),
  real-DEX onStart/onResume/onPause/onStop/onDestroy, finish()=request +
  cascade at frame boundaries, FIND-G07-003 MessageQueue (when,seq) fix;
  law battery 22/22; lifecycle golden 16/16 + 3-run identity ("CSRPHD").
- G08 (38f9f202): consume_pending_intent (A.onPause→B.onCreate(Intent)→
  B.onStart→B.onResume→A.onStop, real DEX both sides), task stack +
  restart law + onActivityResult-before-onStart, FIND-G08-001/006/007
  fixes + pop-law crash fix; navigation golden 17/17 + 3-run identity
  (pixel-real window switch, "hello:7", "R42:-1").
- §18 hostile (9e99a74c): 16/16 (floods, zombies, drain caps) + EXT-08
  ConnectBot 11009000 frozen (191e6990…742f; boots SUCCESS).
- Final report A–P (dbbe4057, docs/evidence/G06G08_FINAL_REPORT.md);
  G06/G07/G08/final evidence comments posted with DIRECT URLs
  (scripts/comment_urls.json).

Stage Summary:
- Battery: 46 named stages ALL PASS at dbbe4057; G01–G05 goldens unchanged.
- Campaign G06–G08 CLOSED — VERIFIED with explicit non-blocking boundaries
  (AppCompat shell, NinePatch, implicit intents, KEYCODE_BACK, multi-touch).
- All GitHub artifacts published with direct URLs per Rule 0.2.

---
Task ID: G09-P0
Agent: Super Z (main agent)
Task: G09 Phase 0 — current-HEAD baseline (46-stage battery + frozen hashes
+ determinism) before any real-APK corpus validation.

Work Log:
- HEAD af99f763 (main, clean; 1 unpushed commit vs origin/main@5e33f198 —
  runtime/data telegram shared-prefs residue commit, engine untouched).
- Environment constraint discovered: background processes are killed with
  the tool call's process group → battery now runs FOREGROUND with
  same-HEAD resume checkpoints (run_test_battery.sh patched; stage results
  checkpointed to /tmp/g09_battery_state keyed by HEAD).
- Battery reproduced: 48 stage gates ALL PASS at af99f763 (build ×2,
  semantic 6, law batteries, goldens, EXT-01/02, density oracle, G06/G07/G08
  goldens + 3-run determinism, corpus fetch + 3 runs).
- Frozen hashes reproduced BYTE-IDENTICALLY:
  EXT-01/EXT-02 frame_000 png 142238fd92b69e11…
  EXT-02 frame_001 png e242ac1e9c8cc224…
  density-matrix 351340a7a92e645c (det2/det3 identical)
  (note: manifest `sha256` field ≠ PNG file hash; frozen constants are the
  png_sha256 / file-bytes values — false alarm resolved and documented)
- Corpus cache restored SHA-exact for 17/18 manifest APKs; findings:
  CORPUS-DRIFT OpenLauncher_39 (F-Droid now serves b3320463…, frozen
  b7900f56…), TinyMusicPlayer URL 404 (dead), Telegram URL not a frozen APK.

Stage Summary:
- PHASE 0 = COMPLETE. Baseline recorded; engine NOT modified.
- NEXT: Phase 1 corpus metadata freeze (g09_corpus_metadata.py).

---
Task ID: G09-P1..P9
Agent: Super Z (main agent)
Task: G09 Phases 1-9 — real APK corpus validation + G06-G08 cross-app proof.

Work Log:
- P1: 18-APK frozen corpus (registry committed; binaries gitignored).
  Findings: OpenLauncher F-Droid URL content drift (b3320463 vs b7900f56),
  TinyMusicPlayer 404, Telegram non-freezable URL. ConnectBot 11009000
  manifest = 1 Activity + 3 Services (corrects "multi-Activity" record).
- P2-P4: g09_corpus_runner over all 18 (base + --click-test), lifecycle
  traces, g08 signal scan, pixel-content audit of every screenshot.
  Verdicts: 4 RENDERED, 4 partial-visible, 10 blank; per-APK blockers
  classified F5/F8/F10/F12.
- P5: API-level audit (code-anchored): SDK_INT=34 constant, device
  sdkVersion=34, min/targetSdk = metadata only → API 9/10 matrix = NOT
  APPLICABLE as a runtime switch; v-qualifier law is the real version
  axis (48/48). Phase 8 = N/A same rationale.
- P6/P7: clusters identified; GENERIC LAW FIX FIND-G09-LC-001 (commit
  84f0fb55): boot lifecycle record advances on the FRAMEWORK path
  (ActivityThread.handleStartActivity law) — corpus evidence: 10+ apps
  skipped STARTED, 4+ had guard-rejected finish cascades. Law test 22→25
  ALL PASS; corpus re-run 6/6 now RESUMED (unote full lawful chain).
  48-gate battery ALL PASS at 98c25ba2; frozen goldens byte-identical.
- Corpus 3-run determinism: simplestopwatch ed1dfc89… ×3, gmdice
  db0f4c4b… ×3 byte-identical.
- Classified-not-fixed (Phase 9 ranked): F8 item-width collapse (microtimer
  + billthefarmer — TOP next-campaign pick), F12 AppCompat/Compose/WebView/
  GL shells (11/18), F10 component-less intents (chessclock + unote),
  FIND-G09-ACF-001 AppComponentFactory (6-app cluster entry law).
- P9 + final report: docs/evidence/G09_FINAL_REPORT.md (required table +
  12 statistics + IMPACT ranking); 16 visual-evidence PNGs committed.

Stage Summary:
- G09 CLOSED: 18 real APKs tested, classified with earliest-blocker
  taxonomy; 1 cross-APK generic law implemented + verified; zero regression;
  fixture-proof vs real-APK-proof separation now quantified.
- GitHub publication to Issue #8 follows (Rule 0.2 direct URLs).

---
Task ID: G09-PUB
Agent: Super Z (main agent)
Task: G09 GitHub publication (Rule 0.2) + closure.

Work Log:
- Pushed 5 commits to origin/main, verified via ls-remote:
  af99f763 (pre-existing residue) → 84f0fb55 (FIND-G09-LC-001 fix) →
  98c25ba2 (corpus registry + harness + results) → 48c2883b (final report
  + 16 visual frames) → ae98a23f (post-fix re-run evidence).
- 6 evidence comments posted to Issue #8 (auth Sh-TB), URLs read back from
  the API and recorded in scripts/comment_urls.json:
  baseline 5559440911 · corpus registry 5559441025 · matrix 5559441103 ·
  fix+regression 5559441172 · API audit 5559441251 · Phase-9 ranking
  5559441356.

Stage Summary:
- G09 CLOSED — 18 real APKs REAL-APK TESTED; 4 RENDERED / 4 partial /
  10 blank with earliest-blocker taxonomy; 1 generic law fixed and
  corpus-verified; 48/48 battery green at ae98a23f; all evidence published
  with direct URLs.

---
Task ID: G10-P0..P8
Agent: Super Z (main agent)
Task: G10 — cross-APK measurement & layout law campaign (microtimer +
billthefarmer + headingcalculator + 4 guard APKs, same corpus before/after).

Work Log:
- Env restore (NOT engine change): aapt2 re-fetched, corpus cache restored
  SHA-exact (15/18 exact, 3 documented G09 drifts); baseline battery 48/48 at
  3c9b7001 (G09 residue commit, engine-identical to ae98a23f).
- Phase 0: 7-APK subset baseline + pixel audits + U007_LAYOUT_DEBUG traces
  (orientation added to trace dump — diagnostic only). Screenshot hashes
  matched G09 frozen (simplestopwatch ed1dfc89, gmdice db0f4c4b).
- Phase 1 clusters (evidence): F8-C-DEFAULT (LL unset orientation → AOSP
  HORIZONTAL; microtimer XML lines 31/66/87/108/130 lack the attribute),
  F8-B-SUPER (DEX superclass chain: CalculatorDisplay/Keypad extend
  LinearLayout, RoTimeControl extends FrameLayout, ViewSwitcher degraded to
  View), F8-A-MERGE (merge root returned LAST child; main editor orphaned),
  F8-G-GRAV (frame gravity axis fields not masked: 0x00800055 → center).
- Fixes (commits 2df49003, e6e51648): FIX-G10-001/002/002b/003/004 + early
  classifier wiring at inflate time. Zero package branches; all law-level.
- Phase 5: tests/g10_layout_law_test.cpp — 23 hostile checks ALL PASS;
  battery extended 48→50 stages.
- Phase 3/4: same 7-APK corpus re-run — microtimer improved (rows horizontal,
  3-run det 57503a12), billthefarmer improved (editor bar + bottom-right FAB,
  3-run det 06ba8026, clicks 2→3), unote lawful gravity correction
  (8197687f), guards byte-identical, headingcalculator unchanged (remaining
  blocker = F4/F5 constructor/addView layer, classified not patched).
- Phase 6 regression: 50/50 ALL PASS at e6e51648; G09 goldens intact.
- Phase 8 re-rank: next campaign = F5 app-constructor/addView (headingcalc
  keypad, muellerma ACF), then AppCompat shells (11/18), then implicit Intent.

Stage Summary:
- G10 CLOSED: 4 generic AOSP laws implemented + verified; 3 APKs improved,
  0 regressions; merge law honestly marked LAW-TESTED (single-APK exerciser);
  updated evidence in docs/evidence/g10_evidence/ (report + JSONs + traces +
  6 visual frames). GitHub publication to Issue #8 follows.

---
Task ID: G10-PUB
Agent: Super Z (main agent)
Task: G10 GitHub publication (Rule 0.2 direct URLs) + closure.

Work Log:
- Token file restored to /home/z/.gh_token (600, outside worktree); pushed
  4 commits: ae98a23f → 3c9b7001 (residue) → 2df49003 (5 law fixes + 23-check
  battery) → e6e51648 (inflate-time classifier) → 403b0689 (report+visuals);
  verified via push output ae98a23f..403b0689 main->main.
- 4 evidence comments posted to Issue #8, URLs read back from the API and
  recorded in scripts/comment_urls.json:
  baseline+clusters 5560118010 · laws+fixes 5560118079 ·
  cross-APK validation 5560118162 · impact+ranking 5560118251.

Stage Summary:
- G10 CLOSED — 4 generic AOSP measurement/layout laws + 1 ViewAnimator law
  implemented and verified on the same 7-APK corpus; 3 APKs improved,
  0 regressions; 50/50 battery; merge law honestly marked LAW-TESTED.
- Next campaign (evidence-ranked): F5 app-constructor/addView execution.

---
Task ID: G11-1
Agent: Super Z (main agent)
Task: G11/G12 campaign — §1 current-HEAD recovery, §4-§8 constructor layer verification + Factory-law fix, corpus verification loop.

Work Log:
- §1 HEAD recovery: local HEAD was 167c27fb (stale "docs(g10)" message) containing the lost
  session's G11 WIP; origin/main 3d063e01 was a verified byte-identical subset. Rebased onto
  origin (linear 3d063e01 -> d8b66526), reworded commit honestly, pushed 3d063e01..d8b66526.
- §1 environment restore: aapt2 8.13.2-14304508 (Google Maven, hash-verified usage), external
  fixture HelloWorldSelfAware (SHA 009b4671... == doc), 18-APK corpus manifest fetch (8 campaign
  APKs hash-verified). Build green.
- §1 baseline battery: 50/50 ALL PASS at d8b66526 (battery checkpoints at uncommitted-then-
  committed WIP HEAD; goldens intact).
- Verified phase0 baseline was captured PRE-change (4 screenshot hashes == G10 goldens:
  microtimer 57503a12, simplestopwatch ed1dfc89, gmdice db0f4c4b, unote 8197687f).
- F5-C1 ROOT CAUSE (trace-proven): per-instance ctor hook installed on the LAZY DEFAULT
  LayoutInflater; the subsequent ensure_loaded() recreate (make_unique) silently wiped it.
  headingcalculator inflated factory-less (3 views, screenshot byte-identical to G10 baseline).
- FIX (AOSP Factory law, commit f42cf79c): ResourceRuntime now OWNS the process-wide
  custom-view ctor hook and re-applies it to EVERY LayoutInflater it creates
  (ensure_loaded + lazy inflater() accessor) — AppCompatDelegateImpl.installViewFactory law.
- Runtime proof (headingcalculator, MINIANDROID_G11_TRACE=1): CalculatorDisplay,
  CalculatorKeypad, ExplainableTextView, ExplainableButton real DEX <init>(Context, AttributeSet)
  EXECUTED; real super chains (CalculatorKeypad -> LinearLayout -> ViewGroup -> View -> Object);
  ctor-built subtrees MOUNTED (display grid TC/TAS/WD/WS/TH/GS + 4 keypad rows digit1..9/DEL/CE);
  initializeDisplay() ran (text '0'); screenshot 6ab39944 -> 47646e76.
- Corpus 8-APK after-run (phase1_after): 6 guards byte-identical (ZERO regression);
  headingcalculator 0.263% -> 6.455% nonbg (25x real content); microtimer hash CHANGED with
  identical pixel stats — classified LAWFUL: obfuscated Lk/g;.<init> real DEX executes
  setOrientation + new Button + new RoTimeControl + addView(x2) (F5-C7/F5-C8 laws exercised by
  real app code); RoTimeControl.a() creates TextView programmatically; 'null:null:null' label =
  app's own format of null fields at construction (Java String.valueOf law); pixel delta band
  rows 951-1076 == exactly the new real TextView 640x123. Timer-tick label update = G07 domain,
  recorded as future layer.
- Battery re-run after fix: 50/50 ALL PASS at f42cf79c.

Stage Summary:
- G11 constructor layer: implemented + runtime-proven on 2 real APKs (headingcalculator,
  microtimer) + 6 guards byte-identical. G12 blockers MOVED to measurement layer:
  (a) TableLayout/TableRow wrap-height aggregation (rows 0x0 with 44px children),
  (b) vertical-LL weight=1000 row redistribution (rows 1080x0, buttons 0 height).
- Next: g11 law/hostile test battery, G12 measurement clusters, muellerma ACF trace.

---
Task ID: G11/G12-CLOSE
Agent: Super Z (main agent)
Task: G11/G12 closure — G12 measurement laws, muellerma independent trace, determinism, evidence publication.

Work Log:
- G12 clusters root-caused via opt-in U007_LAYOUT_DEBUG=3 spec dumps (§3 chain):
  (1) framework classes had NO ancestry layer (TableRow substring-missed "Layout"
  → leaf → 0x0 rows under 44px children); FIX-G12-001: src/framework/view_ancestry.h
  single authority (view_ancestry.h) consulted by is_subclass_of + inflater fallback.
  (2) descriptor form law: AXML dot-form vs DEX slash-form — normalize_class_desc()
  at every cross-layer compare (FIX-G12-001b). (3) TableLayout stacks rows VERTICALLY
  (was measured as one horizontal row, content_w=473). (4) is_a classifier Factory
  survival (was only wired on the renderer pass — window path classified app
  containers as leaves) (FIX-G12-002).
- Result: headingcalculator final pass CalculatorDisplay 1080x0 → 1080x158; TableLayout
  1080x158; screenshot 47646e76 → 0f933ff8 (268,977 px diff); 3-run determinism unique
  hash count 1.
- muellerma independent trace (§25): NOT the headingcalculator cluster. Evidence:
  (a) manifest AXML string pool shows NO activity (StopwatchApp/Service/Tile/provider
  only — a QS-tile-only app real Android never opens from a launcher) → new cluster
  FIND-G11-NOACTIVITY-001, EXP-031.5 zero-bytecode assertion scoped to activity apps;
  (b) bundled android.app.AppComponentFactory.<clinit> disassembly = unconditional
  construct-and-throw — FIX-G12-003 parent-delegation law: framework-namespace <clinit>
  never executes from app DEX (choke-point skip in execute_method_internal).
  Result: PARTIAL preserved with byte-identical screenshot (diff=0), stub skipped.
- microtimer classified LAWFUL (Lk/g; real ctor + addView; RoTimeControl programmatic
  TextView; 'null:null:null' = app's own Java null-concat at construction).
- Battery 52/52 ALL PASS at every commit (d8b66526 → 28c1bfe1); zero golden changes.
- Evidence published to Issue #8 (URLs read back from the API, recorded in
  scripts/comment_urls.json): recovery+baseline 5561889945, laws+fixes 5561890236,
  cross-APK validation 5561890536.

Stage Summary:
- G11/G12 CLOSED: real DEX constructor execution + custom hierarchy + measurement laws
  runtime-proven + visually-proven on 2 independent real APKs (different packages, UI
  architectures); 6 byte-identical guards; determinism proven; 5 semantic commits
  d8b66526/0115452b chain pushed; final HEAD 0115452b.
- Remaining (ranked): headingcalculator keypad width (needs reference evidence),
  AppCompat/Compose shells, G07 timer ticks, implicit intents, TableLayout column law.

---
Task ID: MASTER (Real APK Compatibility Recovery)
Agent: Super Z (main agent)
Task: Audit CURRENT HEAD from APK container to first rendered frame + user
interaction across real external APKs; root-cause and fix the highest-value
reusable layers; regression + determinism gates; GitHub evidence.

Work Log:
- Baseline at cc9e67ef: clean tree, origin verified in sync, battery harness
  restored from sandbox, fresh 52-stage battery ALL PASS before code changes.
- Corpus: 16 frozen APKs; KISS restored SHA-matched; bouncy_43 + scope_140
  frozen as new independent additions; Fossify/Markor/TinyMusic/Telegram
  URL-drift + HTML-page findings recorded honestly (no substitutes).
- Phase-0 matrix (16 APKs) via scripts/master_phase0.py: per-APK status +
  pixel audit + view trees; blank/partial set triaged per first failing layer.
- Cluster A root-caused (R8 horizontal class merging ground truth: 24 classes
  extend DBHelper merge target; Object.<init> fallthrough + ViewShadow
  catch-all claim; dual shadow registry hid Thread/Looper/ArchTaskExecutor
  shadows; capped-ring lifecycle inference) → 3 law fixes + diagnostics.
- Cluster B: real-DEX onMeasure execution + getDefaultSize + MeasureSpec +
  Math laws; scope custom views measured by their own bytecode.
- F16 proofs: simplestopwatch/unote/bouncy tap→DEX→state→frame, 3× identical.
- Regression: fresh battery ALL PASS after every fix; goldens unchanged.
- Evidence posted to Issue #8 (4 comments, direct URLs verified, dupes purged).

Stage Summary:
- Commits b812c214, ef691b35, e49b9bdd, e86f5d51, b343b969; remote b343b969.
- kiss PARTIAL(rc=1) → SUCCESS(5/5); scope blank → real app-measured render.
- Honest blockers remain: scope Scope/Unit hook gap, G07 timer-tick labels,
  bouncy field draw coverage, §29 shells, Telegram freeze-blocked.

---
Task ID: M3-C1+C2 (MASTER CAMPAIGN 3 session summary)
Agent: Super Z (main agent)
Task: MASTER-3 §1-§2 baseline+frontier; §6/§7 cross-pass geometry + weight
law; §13 resource law; §9 event loop; §15 API coverage; §26 regression gates.

Work Log:
- Baseline at c0f178a7 (origin verified, clean tree): env restored from
  scratch, 22 frozen APKs SHA-verified, 52-stage battery ALL PASS.
- 20-APK frontier matrix: 12 real-content / 4 partial / 3 blank / 1 timeout,
  all 2x-deterministic; zero drift vs MASTER-2.
- 9 law commits: 83f1a04d (ARSC stride+bag_parent), 5d8303e4 (style-bag
  layout params + parent chain), 1df3b263 (ancestry hook lifecycle +
  match-parent remeasure), 2f91c63f (spec margins/padding + convergence
  memo), 008573bd (17-check ARSC law test + fixture), 1aff4b97 (55-stage
  harness), 32d38b53 (setText stub removal, setTextColor, Integer math,
  ARSC-first getColor), 97876119+916174fc (worklogs).
- headingcalculator 6.71%→82.51% (3x byte-identical); 19/20 corpus APKs
  pixel-identical; battery ALL PASS at every boundary; goldens unchanged.
- §9 scheduling path proven (chessclock 11 consecutive real-DEX ticks);
  3 named blockers: F-TIMER-COMPUTE, F-ARGS, F-TIMER-STACK.
- BLOCKED: GitHub push+publication — sandbox reset lost /home/z/.gh_token;
  poster prepared at scripts/post_m3_comments.py (Rule 0.23 honesty).

Stage Summary:
- 10 commits on local main (c0f178a7 → 32d38b53 + docs), push pending token.
- Next frontier: heap class identity law → F-TIMER-COMPUTE; synthetic stack
  boundaries → microtimer; §3 ViewShadow ancestry migration; SECUSO
  color-state-list; corpus +5; interaction tier ≥8.

---
Task ID: M3-C3 (MASTER CAMPAIGN 3 — session 3: F-TIMER closure)
Agent: Super Z (main agent)
Task: Continue M3 from d9625153 — §1 baseline re-capture, §19 F-TIMER-COMPUTE/
F-TIMER-STACK closure, §15 API family, regression gates, evidence.

Work Log:
- §1 baseline re-captured at d9625153 (clean tree, origin c0f178a7): battery
  59/59 ALL PASS, corpus 20/20 SHA-verified ZERO drift, 8 golden files hashed,
  toolchain verified (g++ 14.2.0, make — cmake absent). GitHub push BLOCKED
  (no gh CLI/token/credential helper — probed). MASTER3_BASELINE_MATRIX.md
  committed (54c0deef).
- §19 F-TIMER-COMPUTE root-caused with staged forensics (35c/3rc/direct/try):
  NOT dispatch identity at all — the EXP-058 generic loop guard is a
  PROCESS-LIFETIME call counter that silently stubs any (class,method) after
  10 invocations. chessclock formatTime exceeded 10 calls during setUpGame;
  from tick 2 the real DEX body was replaced by bridge → ActivityShadow →
  "null" label. Same family as the tictactoe access$ CHAR-PROBE bug.
- FIX-M3-008 (fef1cb19): 3rc invoke-virtual/interface-range now dispatch on
  the receiver's RUNTIME heap class first (EXP-059 parity); direct/super-range
  keep declaring-class (AOSP).
- FIX-M3-009 (fef1cb19): ACTIVE-CYCLE LAW — loop guard may only fire when the
  same (class,method) re-enters while active on the call stack (RAII
  active-key set + visible [M3-19-CYCLE] diagnostic). Lifetime counter
  removed; MAX_RECURSION_DEPTH stays the backstop. AOSP/ART has no per-method
  lifetime call cap.
- Evidence: chessclock --tap 540,480 --frames 30 → label decrements EXACTLY
  every 10 ticks (9:59:59 → 9:59:58 → 9:59:57; TICK_LENGTH=100ms math), 30
  consecutive real-DEX ticks, zero "null". 3-run PNG-sequence determinism
  PROVEN (identical across 3 runs).
- Corpus re-run (97812cc0): 16/20 byte-identical (zero regression); secuso_todo
  CRASH(rc=-9) → SUCCESS (94.53% nonbg, 16 views — inflateColorStateList was
  itself a throttle victim); gmdice +0.2%; microtimer label now computes.
- FIX-M3-010 (82dd045f): Integer unsigned/bit family — toUnsignedString,
  toBinaryString, toHexString, toOctalString, numberOfLeading/TrailingZeros,
  bitCount, rotateLeft/Right, highest/lowestOneBit, compareUnsigned,
  parseUnsignedInt, signum, min/max/sum (microtimer Lk/a;.toString chain).
- FIX-M3-011 (82dd045f): Throwable.getStackTrace()/fillInStackTrace()/
  getStackTraceDepth() real-frames law (parity with Thread.getStackTrace,
  CAMPAIGN 010 R14) — microtimer La/e;.m Kotlin-Intrinsics caller discovery
  now materializes 3 real frames ([M3-19-THROWTRACE]); F-TIMER-STACK AIOOBE
  GONE.
- F-THREAD-TICK (NEW, honestly blocked): microtimer countdown ticks via a
  background Executor/ThreadFactory (La/a;.execute, La/c;.newThread) —
  outside the G07 Handler/Looper virtual-time law. Named, not hacked.
- Battery 59/59 ALL PASS after EACH law commit (fef1cb19, 82dd045f); goldens
  unchanged.

Stage Summary:
- Commits: 54c0deef, fef1cb19, 97812cc0, 82dd045f (+ 4 pre-session docs at
  d9625153). Local main = 82dd045f, 15 commits ahead of origin c0f178a7;
  push BLOCKED pending token (payload ready: scripts/post_m3_comments.py).
- F-TIMER-COMPUTE: CLOSED (runtime-proven + 3-run determinism).
- F-TIMER-STACK: CLOSED (real frames materialized).
- secuso_todo: CRASH → SUCCESS (unblocked by the same law).
- Remaining frontier: F-THREAD-TICK (executor virtualization), F-ARGS
  (chessclock color(int) resid=0), §3 ViewShadow ancestry migration,
  §20 corpus +5, §21 interaction tier ≥8, GitHub evidence A–J (token).

---
Task ID: M3-S4 (MASTER CAMPAIGN 3 — session 4: publish + F-THREAD-TICK forensics + reflection laws)
Agent: Super Z (main agent)
Task: User supplied the GitHub token: publish ALL unpushed commits and pending
evidence comments; then continue MASTER CAMPAIGN 3 from current HEAD
(PHASE 1 F-THREAD-TICK first).

Work Log:
- Token verified (repo Sh-TB/MiniAndroid-Compatibility-Runtime, push permission).
- PUSHED 17 commits c0f178a7..24356b22 (local main == origin/main).
- POSTED 3 pending evidence comments (scripts/post_m3_comments.py) + 1
  session-3 closeout comment → 4 DIRECT URLs recorded in
  scripts/comment_urls.json; +1 session-4 comment (below). All published.
- PHASE 1 forensics (evidence-first, real DEX + master source):
  * microtimer v8 decompiled semantics: START = foreground-icon Button in the
    last keypad row (node 100 family), Clear = right ImageButton (view 83),
    Backspace = left (77); digit taps route Lk/d.onClick → onDigit →
    RoTimeControl.setValue.
  * F-THREAD-TICK premise CORRECTED: the app tick law is
    tickHandler.postDelayed({tick(tc)}, alarm.id, deltaMs) on the MAIN looper
    (G07 law, self-rescheduling). The Executor/ThreadFactory/Thread.sleep in
    the DEX is Room's internal worker, not the tick path.
  * Click-path runtime evidence: btnStart → createTimer → Lm/c;
    (UninitializedPropertyAccessException, sanitizeStackTrace via La/e;.m)
    thrown at alarmDao.create — lateinit never assigned because initDb()
    died: Class.getPackage() returned null → Intrinsics NPE (compat
    swallowed) → fullPackage "" → Database_Impl lookup broken.
- LAWS IMPLEMENTED (commit c4cfe6ab):
  * FIX-M3-012: Class.getPackage → per-name Package object;
    Package.getName; Class.getCanonicalName/getSimpleName (dotted law).
  * FIX-M3-012b: Class.forName (DEX-index resolution, CNFE law);
    getDeclaredConstructor; Constructor.newInstance (allocates + runs real
    DEX <init>); Object.getClass (runtime-class CLASS_REF identity).
    Evidence: Database_Impl resolved + constructed; run exceptions 3 → 0.
  * FIX-M3-013: StringBuilder(int capacity) → buffer only, never content.
    (Old bug: content became "2" → padStart(2,'0') poisoned → label
    "200:200:201"; after fix "00:00:01" byte-exact.)
  * FIX-M3-014: SystemClock.elapsedRealtime/uptimeMillis/currentTimeMillis
    read the G07 virtual clock (one clock, one authority); sleep advances it.
- Validation: battery 59/59 ALL PASS; corpus re-run microtimer/chessclock/
  secuso_todo byte-identical to committed baseline; 16/20 unchanged; det2x ✓.
- NAMED NEW BLOCKER (F-ROOM-CHAIN): tick reschedule still short-circuited —
  Intrinsics stack-walk aget-oob (La/e;.h pc=34, index==length on our
  materialized stack array) + compat-swallowed NPEs in Room transaction path
  (Lh/f;.u) leave Alarm.expiresMs/remaining broken at first tick (expired →
  Vibration.start instead of postDelayed countdown).
- Forensics tools committed: scripts/mt_dex_disasm.py, scripts/mt_callers.py
  (lead tools; runtime trace remains the evidence authority).
- Final push state: origin/main == bb61749e, tree clean, 0 unpushed.

Stage Summary:
- Closed: publication backlog (ALL commits + ALL pending comments now on
  GitHub with DIRECT URLs).
- Laws closed: M3-012/012b/013/014 — regression-clean (59/59, zero drift).
- F-THREAD-TICK: premise corrected (main-looper postDelayed); superseded by
  F-ROOM-CHAIN (named, evidence-anchored, not hacked).
- Next: F-ROOM-CHAIN (stack-walk OOB law + Room path), F-ARGS (chessclock
  color), §3 ViewShadow ancestry migration, corpus +5.
