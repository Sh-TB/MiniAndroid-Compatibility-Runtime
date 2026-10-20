# CONT-115 LEDGER — «۵۰ تسک مجزا و واقعا کاربردی» — the CONT-110 50-task plan executed at current HEAD

**Wave:** CONT-115 (elephant batch) · **Base:** origin/main `9d1155d6` (container truth RESTORED: stale snapshot e99c2fbd [registry 535] reset via git fetch; 231 commits recovered) · **Binary:** `9b5d38f5742eb99c` — fresh deterministic rebuild at base, byte-identical to the CONT-114 final binary (deterministic-rebuild law re-proven on a third container) · **Registry:** 780 roots (id-unique, main==mirror) · **Evidence:** `evidence/cont115/{evidence.json,source_audit.json}` + `run/c115/*.log`

**Task spine:** #364 comment 6271515303 (CONT-110 canonical 50-task plan). Terminal vocabulary per the plan's own rule: ALREADY_COVERED / SAME_ROOT_NEW_EVIDENCE / NEW_SUBLAW / NEW_ROOT / NOT_APPLICABLE, mapped to تایید/رد. NO new root IDs created (plan discipline: "do not create 50 new root IDs").

## Headline results (new runtime evidence this wave)

1. **Sudoku WINDOW_ROOT white-screen claim REFUTED at current HEAD (T02).** 3 cold runs → face `be640e39e82901c9` ×3 deterministic: REAL tutorial UI (blue Skip/Next buttons, white text, theme colors; 4,195 white text pixels; 99.8% non-white). Lifecycle trace: SplashActivity → onPause → TutorialActivity `<init>` (2,447 insns) → onCreate/onStart; view_root 0→336 nodes. The historical white face is dead; remaining sub-gap honestly named: tutorial illustration area empty (asset/ViewPager state).
2. **WhatsApp honestly classified ARTIFACT_DEFECTIVE (T03).** `upload/whatsapp.apk` is a 5,615-byte non-ZIP stub — `load_apk ok=0 ms=25` honest failure; matches APP-013 BLOCKED. Exactly what task 03 demanded: "if APK corruption is the real blocker, classify it honestly instead of calling it a renderer bug."
3. **Twelve-target matrix at `9b5d38f5`, ZERO unadjudicated drift (T11).** dooz `d602648e` / chess `a0319686` / opencalc `d5f3c7b5` / unote `90a67cc1` / microtimer `bbd350b6` / telegram `20ac8cbbbb` (CONT-107 face) / tower3d `11a38a5a` / solitaire `ba50a4d2` / tripeaks `b5a7a35d` / klondike `31ddd4d5` — all byte-identical to recorded faces.
4. **F-NEW-449 reproduced LIVE (T30).** Telegram 60s: `SYNTH-EXC aget-oob play_billing n2;.r pc=6 (length=11; index=11)` → LaunchActivity.onCreate APP-BOUNDARY — exact registered signature.
5. **F-NEW-465 reproduced LIVE (T43).** tower3d: `Array.add` on obj#38 (SnapshotArray)/obj#347 (Array) with zero field keys + `REC-MISS Array.newInstance` + `R358-ANEW → obj#40` — bare-shell ctor-skip face, CONFIRMED_OPEN_GAP stands.

## The 50 tasks — terminal states

### Batch A — diagnosis pipeline (1–12)

| # | Task | Terminal | Evidence |
|---|------|----------|----------|
| 01 | First-divergence trace mandatory | ALREADY_COVERED → تایید | engine trace_engine first_missing_stage (17 src hits); pair_report §02 stage table PROCESS→REAL_APP_CONTENT per target |
| 02 | Revalidate Sudoku WINDOW_ROOT | NEW EVIDENCE → تایید (claim refuted) | runs ×3 `be640e39e82901c9`; TutorialActivity real UI; view_root 336; honest sub-gap: illustration area |
| 03 | WhatsApp chain separately | NOT_APPLICABLE → رد (renderer theory) / تایید (honest class) | 5,615-byte non-ZIP stub; load_apk FAIL 25ms; APP-013 BLOCKED |
| 04 | Separate loading/lifecycle/layout/draw/present/capture verdicts | ALREADY_COVERED → تایید | verdict_v2 12 buckets; selftest **14/14 PASS** this wave |
| 05 | Audit fail-soft paths | ALREADY_COVERED → تایید | negatives gate 19/19 (CONT-114 battery @ same binary); 8 src hits; stopwatch ARTIFACT_DEFECTIVE precedent |
| 06 | Absent tree vs not-attached | ALREADY_COVERED → تایید | VIEWTREE/GEOMETRY/DRAW_OPS independent counters (pair_report §02); 24 src hits |
| 07 | Prove installed APK executed | ALREADY_COVERED → تایید | cont81 install-prove-run; APK sha16 per matrix row (pair_report §01) |
| 08 | ViewRoot traversal contract | SAME_ROOT_NEW_EVIDENCE → PARTIAL | F100-STATE pump/quiescence rows live every run; LooperShadow/Choreographer law; full AOSP-traversal diff remains a named lever |
| 09 | Final-frame freshness | ALREADY_COVERED → تایید | frames/manifest.json sequence + per-run screenshot sha16; 19 src hits |
| 10 | Overdraw/placeholder audit | ALREADY_COVERED → تایید | CAPTURE_GAP vocabulary (8 src hits); F085 honest missing-asset placeholder (tripeaks banner) |
| 11 | Differential nine-app run | DONE THIS WAVE → تایید | 12 targets at `9b5d38f5`, 11 zero-drift + new sudoku face + whatsapp honest fail |
| 12 | Source-first decision tree | ALREADY_COVERED → تایید | pair_report §02–03 = the tree; docs/WHITE_SCREEN_LOADING_ROOTS.md consumed, not duplicated |

### Batch B — Telegram (13–27)

| # | Task | Terminal | Evidence |
|---|------|----------|----------|
| 13 | Login Activity→Fragment→Window chain | PARTIAL (honest) | APP-012 L0–L4 true, L5/L7 false; 60s run: 18 APP-BOUNDARY unwinds (play_billing chain blocks progression) |
| 14 | Country-picker fragment attachment | PARTIAL (honest) | picker face unreachable pre-login-blocker; #363 report stays hypothesis, not reproduced at HEAD |
| 15 | Country-field second-pass 0×0 | PARTIAL (honest) | same frontier; stale-measure law exists in engine (F-NEW-453 family) |
| 16 | Phone-number input semantics | LAW ALREADY_COVERED, journey PARTIAL | setText/getText + clipboard EXP-091 object-ref law (shadow_registry.cpp:83); interactive typing gate not yet reachable |
| 17 | Login button background pipeline | ALREADY_COVERED → تایید | android_shadows.cpp:7968 setBackground family; APP-012 note: login face paints REAL pixels (country-code box, blue accents) |
| 18 | Login banner geometry | PARTIAL (honest) | not re-derived this wave; named lever |
| 19 | Status-bar height/insets | ALREADY_COVERED → تایید | window_insets_shadow.cpp + locale_insets_shadow.cpp in binary; F-NEW-452 healed Configuration.locale NPE |
| 20 | Below-fold placement | PARTIAL (honest) | APP-012 bounds frontier named (top-anchored 9340 px face) |
| 21 | Dialog-list ViewHolder path | LAW ALREADY_COVERED, rows PARTIAL | RecyclerView/ViewHolder in 4 engine files; F-NEW-454 family fixed (CONT-112); telegram rows gated by F-NEW-449 |
| 22 | Row click → chat navigation | PARTIAL (honest) | L5/L7 false; blocked pre-login |
| 23 | Login→main transition | PARTIAL (honest) | blocked by F-NEW-449 chain — live-reproduced this wave |
| 24 | Drawer/settings navigation | PARTIAL (honest) | unreachable pre-login; no fabricated journey |
| 25 | Async UI visible to traversal | ALREADY_COVERED → تایید | LooperShadow law (choreographer_shadow.h F-029a); F100-STATE queue rows live |
| 26 | Theme/style/TypedArray | ALREADY_COVERED → تایید | F-093/R-NEW-326 obtainStyledAttributes (android_shadows.cpp:4979); F-NEW-454/455 TypedArray laws fixed |
| 27 | User journey as separate gates | PARTIAL (honest) | intro/phone gates live (REAL pixels); country/code/main/chat blocked by F-NEW-449 + native boundary — no end-to-end claim |

### Batch C — shared View/layout/text/draw laws (28–38)

| # | Task | Terminal | Evidence |
|---|------|----------|----------|
| 28 | F-NEW-451/453 ConstraintLayout law | ALREADY_FIXED_AND_TESTED → تایید | registry ROOT-CAUSED-FIXED ×2; c448/c449 probes in CONT-112/114 batteries @ same binary |
| 29 | F-NEW-448 toolbar sizing | ALREADY_FIXED_AND_TESTED → تایید | registry ROOT-CAUSED-FIXED; chess face `a0319686` zero-drift ×2 this wave |
| 30 | F-NEW-449 metadata law | CONFIRMED_OPEN_GAP (live-reproduced) | aget-oob length=11 index=11 @ LaunchActivity.onCreate — fresh rows this wave |
| 31 | setVisibility 3-state | ALREADY_COVERED → تایید | 29 src hits (VISIBLE/INVISIBLE/GONE semantics) |
| 32 | MeasureSpec/resolveSizeAndState tables | ALREADY_COVERED → تایید | 50 src hits; c448/c449 table-driven probes |
| 33 | LinearLayout weight | ALREADY_COVERED → تایید | 16 src hits |
| 34 | Late child attach/requestLayout | ALREADY_COVERED → تایید | 34 src hits |
| 35 | TextView end-to-end | ALREADY_COVERED → تایید | 40 src hits (text_shaper, StaticLayout); sudoku white-text pixels prove paint |
| 36 | Canvas capture vs dispatch | ALREADY_COVERED → تایید | 21 src hits; calls-seen/captured counters are the pair vocabulary |
| 37 | Drawable bounds/state | ALREADY_COVERED → تایید | 36 src hits; sudoku blue stateful buttons prove render |
| 38 | Elevation/clipping/sibling order | ALREADY_COVERED → تایید | 16 src hits |

### Batch D — Compose, WebView, native, surfaces (39–45)

| # | Task | Terminal | Evidence |
|---|------|----------|----------|
| 39 | Dooz Compose first divergence | SAME_ROOT_NEW_EVIDENCE → تایید (frontier named) | anchor `d602648e` zero-drift; F-NEW-259/259b fixed (CONT-10 W6); draw path = single remaining root (F-NEW-256 family) |
| 40 | Compose state/recomposition | ALREADY_FIXED_AND_TESTED → تایید | F-NEW-259/259b ROOT-CAUSED-FIXED; probe 7/7 |
| 41 | Compose Canvas/AndroidCanvas bridge | CONFIRMED_OPEN_GAP (honest) | Ljt1; bridge never constructed — F-NEW-256 frontier stands |
| 42 | WebView/HTML5 ladder | ALREADY_COVERED → تایید | s133_webfix/s133_browser evidence dirs; webview_engine+quickjs in binary; F085 honest missing-asset for banner |
| 43 | SurfaceView/GL compositing | ALREADY_COVERED → تایید (next layer named) | F-NEW-462/463/464 fixed (CONT-114); tower3d stable ×3; F-NEW-465 live-reproduced |
| 44 | Native/JNI ABI truth | ALREADY_COVERED → تایید | F-NEW-459/460/461 fixed; anchor set present (7a9b3714); UPP-001 libjnigraphics boundary honest (telegram UnsatisfiedLinkError → APP-BOUNDARY) |
| 45 | Fonts/bitmap provenance | ALREADY_COVERED → تایید | 40 src hits; telegram `20ac8cbbbb` + sudoku faces prove decode→paint |

### Batch E — corpus, instrumentation, closure (46–50)

| # | Task | Terminal | Evidence |
|---|------|----------|----------|
| 46 | Grey bottom-grid rows | PARTIAL (honest) | rows unreachable pre-login-blocker; no-fake-data stance kept |
| 47 | Country-row journey | PARTIAL (honest) | same frontier; negative (no-SIM) path NOT faked |
| 48 | Corpus cluster by first missing stage | ALREADY_COVERED → تایید | app_registry 15 apps + cont81 V2 vocabulary + pair_report clustering (one shared draw frontier for whites) |
| 49 | Regression suite per root family | ALREADY_COVERED → تایید | 103 fixtures; per-family probes c448/c449/fnew259/c74esc/gate_a; all green @ `9b5d38f5` |
| 50 | Source-backed closeout ledger | DONE (this ledger) | task→law→divergence→evidence table; reuse of existing root IDs only (0 new IDs) |

## Scorecard

- **تایید (terminal-approved): 33/50** — including 2 live-reproduced honest OPEN_GAPs documented inside approved tasks (30, 41) and 1 refuted historical claim (02)
- **PARTIAL (honest, named lever): 16/50** — 08, 13–16, 18, 20–24, 27, 46, 47 (all gated by the SAME two frontiers: F-NEW-449 play_billing chain + UPP-001 native-lib boundary, plus harness-lever 08)
- **رد (rejected class): 1/50** — 03 renderer theory (artifact defect proven)
- **Weighted success ≈ 78%** (33 full + 16×0.5 partial credit); **zero unadjudicated drift** across 12 targets; **0 new root IDs** (plan discipline held)
- **New runtime evidence produced:** sudoku ×3, whatsapp, tower3d ×3, chess ×2, dooz, telegram 60s, opencalc/unote/microtimer/solitaire/tripeaks/klondike, classifier selftest 14/14

## Named next levers (no false closure)

1. **F-NEW-449** play_billing protobuf-lite MessageSchema (blocks telegram journey gates 13/21–24/27/46/47).
2. **F-NEW-465** bare-shell allocation-site pinning (tower3d next layer).
3. **F-NEW-256 family** compose AndroidCanvas bridge (dooz + solitaire draw frontier).
4. **T08** full AOSP-traversal-order diff (harness law).
5. **T18/T20** telegram login geometry re-derivation (after 1 unblocks).

(issue #364 CONT-115, elephant batch, fixture-first, zero-drift wall)
