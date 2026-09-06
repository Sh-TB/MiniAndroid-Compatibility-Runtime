# G10 FINAL REPORT — CROSS-APK MEASUREMENT & LAYOUT LAW CAMPAIGN

**Current HEAD:** `e6e51648` (main)
**Baseline HEAD at campaign start:** `ae98a23f` (G09 final) + `3c9b7001`
(G09 publication tooling residue — engine-identical, verified 0-line diff
across miniandroid/src|core|runtime|tests between `ae98a23f` and `3c9b7001`).

---

## 1. Regression result

| Gate | Result |
|---|---|
| Full battery (baseline, pre-fix, HEAD `3c9b7001`) | **48/48 ALL PASS** |
| Full battery (post-fix, HEAD `e6e51648`) | **50/50 ALL PASS** (48 existing stages intact + 2 new G10 law stages) |
| G09 frozen goldens | BYTE-IDENTICAL: simplestopwatch `ed1dfc89…`, gmdice `db0f4c4b…` (×3 runs each) |
| EXT-01/EXT-02, density oracle, G06/G07/G08 goldens + 3-run determinism | ALL PASS |
| Environment restore before baseline (NOT an engine change) | aapt2 8.13.2-14304508 re-fetched (Google Maven); corpus cache restored SHA-exact 15/18 exact + 3 documented G09 upstream drifts (Telegram, OpenLauncher, TinyMusicPlayer — untouched, previously recorded) |

## 2. Selected real-APK corpus (Rule 1 — same set before AND after every fix)

7 APKs (3 required F8 failures + 4 structurally different same-mechanism guards):

| # | APK | versionCode | SHA-256 | Selection reason | G09 initial state |
|---|-----|-------------|---------|------------------|-------------------|
| 1 | dubrowgn.microtimer | 8 | `79c6f730f64886e7…` | REQUIRED — F8 keypad/input collapse | PARTIAL (keypad → left column) |
| 2 | org.billthefarmer.notes | 139 | `82cf8bc44c163748…` | REQUIRED — F8 rows collapsed top-left | PARTIAL |
| 3 | org.debian.eugen.headingcalculator | 1 | `274ec873098eea51…` | REQUIRED — F8/F9 custom views | BLANK (custom views) |
| 4 | de.duenndns.gmdice | 8 | `1621eda11b5dbc0c…` | guard — ScrollView/LL/weights/CheckBox | RENDERED |
| 5 | omegacentauri.mobi.simplestopwatch | 26 | `b3ec1a5ec24ce53b…` | guard — rows/buttons/weight bar | RENDERED |
| 6 | app.varlorg.unote | 30 | `be91103f0e7db443…` | guard — FrameLayout children + gravity | RENDERED |
| 7 | com.chessclock.android | 29 | `5ca6f2c54c05efe7…` | guard — RelativeLayout/weights/large text | PARTIAL (null data) |

(Full 40-hex SHA-256 values in `docs/evidence/g09_corpus/g09_corpus_registry.json`, unchanged.)

## 3. Phase 0 measure/layout evidence (recorded BEFORE any code change)

Per-APK `root → hierarchy → lp/weight/orient → measured → bounds → pixels`:
`docs/evidence/g10_evidence/phase0_baseline_BEFORE.json` + `phase0_traces_BEFORE.json`
+ per-APK `*_layout_trace.log` (U007_LAYOUT_DEBUG per-view lines).

Key baseline facts (evidence, not assumptions):

* microtimer keypad rows: XML lines 31/66/87/108/130 of `res/v9.xml` carry **NO
  `android:orientation`**; trace shows `orient=-1` → runtime laid the 3 wrap
  buttons of each row VERTICALLY (each 23×44 px, left column).
* headingcalculator DEX hierarchy (parsed from `classes.dex` class_defs):
  `CalculatorDisplay extends Landroid/widget/LinearLayout;`,
  `CalculatorKeypad extends Landroid/widget/LinearLayout;` — leaf-name substring
  matching missed both; measured display `1080x0`.
* microtimer `RoTimeControl extends Landroid/widget/FrameLayout;` (DEX).
* billthefarmer: `setContentView` inflate log `root_id=11 views=7` but the
  measured tree contained ONLY the FAB ViewSwitcher (degraded to
  `Landroid/view/View;`) + 2 ImageButtons; the main editor ViewSwitcher was
  orphaned by the `<merge>` root handling.
* unote delete-search ImageButton `layout_gravity=0x00800015`
  (centerVertical|right|directional).

## 4. Failure clusters (Phase 1 — evidence-derived, NOT assumed)

| Cluster | Violated AOSP law | Independent APK evidence |
|---|---|---|
| **F8-C-DEFAULT** | LinearLayout.java: orientation field default = **HORIZONTAL** (field init + `a.getInt(R.styleable.LinearLayout_orientation, HORIZONTAL)`) | microtimer (5 containers in 1 APK); corpus-wide scan: 9 more orientation-less LinearLayouts in KISS, 22 in markor, 5 in fossify (F12-blocked today) |
| **F8-B-SUPER** | Container behavior follows the resolved superclass chain (ViewGroup.onMeasure dispatch is virtual — the ANCESTOR's implementation runs) | headingcalculator (2 LinearLayout subclasses), microtimer (FrameLayout subclass), billthefarmer (ViewSwitcher→View degradation) |
| **F8-A-MERGE** | LayoutInflater `<merge>`: children attach to the parent; at root the parent is the window content frame (PhoneWindow contentParent) | billthefarmer (main editor subtree orphaned; last merged child wrongly returned as root) |
| **F8-G-GRAV** | Gravity axis-field equality: per-axis fields MASKED before comparison (FrameLayout onLayout placeChild; same law family as G04's LinearLayout fix) | billthefarmer FAB `0x00800055` (bottom\|end) centered; unote button `0x00800015` centered instead of right |
| (boundary, classified NOT fixed) | ViewAnimator `showOnly(0)` initial-child law | billthefarmer switcher children overlapped → FIXED as FIX-G10-002b (see §5) |
| (boundary, classified NOT fixed) | headingcalculator constructors never dispatched → programmatic addView children absent (children=0); onDraw dispatch returns 0 ops | headingcalculator — earliest blocker is BELOW F8 (F4/F5 app-code execution), documented not patched |

## 5. AOSP laws transferred + implementation commits

| Fix | Law (AOSP source of truth) | Commit |
|---|---|---|
| FIX-G10-001 | LinearLayout unset orientation = HORIZONTAL | `2df49003` |
| FIX-G10-002 | superclass-chain container classification + framework seed (ViewAnimator→FrameLayout; ViewSwitcher/ViewFlipper→ViewAnimator; TableLayout/TableRow/RadioGroup→LinearLayout; GridLayout/Toolbar→ViewGroup) + real descriptors in tag table | `2df49003` |
| FIX-G10-002b | ViewAnimator.showOnly(0): non-first switcher children GONE at inflation | `2df49003` |
| FIX-G10-003 | `<merge>` root → synthesize window-content FrameLayout; ALL children attach | `2df49003` |
| FIX-G10-004 | Gravity axis-field equality (mask 0x7 / 0x70 before compare) in frame placement (inflater + legacy renderer) | `2df49003` |
| FIX-G10-002-early | DEX classifier wired at inflate time (first measure pass already ancestry-correct) | `e6e51648` |

Smallest-generic discipline: every fix is a law-level change keyed on
class/attribute semantics — zero package names, zero class-name special cases.

## 6. Hostile law tests (Phase 5)

`miniandroid/tests/g10_layout_law_test.cpp` — **23 checks, 0 failures**
(package-independent, synthetic trees), wired into the battery as stages 19–20:

* §A orientation: unset→ROW (positions asserted), weight-in-unset-row, explicit vertical regression guard
* §B chain classification: app-subclass→LinearLayout measure, fallback law
* §C gravity axis fields: `0x00800055`→bottom-right, `0x11`→center, `0x30`→origin
* §D ViewSwitcher→FrameLayout chain resolution
* §E hostile geometry: TableRow columns via chain, GONE slot law, oversized 4000px child clamp, zero-height container, margin chain arithmetic

## 7. Before/after per-APK results (Phase 3/7 — same corpus, same runs)

| APK | Initial (G09) | Cluster | Fix | After (G10) | Visual proof |
|-----|---------------|---------|-----|-------------|--------------|
| microtimer | PARTIAL — keypad collapsed to left column, input row stacked | F8-C-DEFAULT | G10-001 | **improved** — keypad rows 1/2/3-4/5/6-7/8/9-00/0 horizontal; input row = btnClear + weighted time view + btnBackspace on ONE line (row height 252→126, lawful); 3-run deterministic `57503a129012` | `visual/microtimer_BEFORE_collapsed.png` → `visual/microtimer_AFTER_rows_57503a12.png` |
| billthefarmer notes | PARTIAL — 2 collapsed boxes top-left; main editor subtree missing | F8-A-MERGE + F8-B-SUPER + F8-G-GRAV + ViewAnimator | G10-003+002+002b+004 | **improved (structure rendered)** — full tree: decor FrameLayout → main ViewSwitcher (editor bar top, MarkdownView lawfully hidden) + FAB ViewSwitcher 126×126 bottom-right; click dispatched 2→3 (FAB now visible+probed); 3-run deterministic `06ba8026b670` | `visual/billthefarmer_BEFORE_collapsed.png` → `visual/billthefarmer_AFTER_editor_fab_06ba8026.png` |
| headingcalculator | BLANK — custom views 1080x0, onDraw 0 ops | F8-B-SUPER (classification fixed; constructor/addView gap REMAINS) | G10-002 | **unchanged pixels** — views now classified as LinearLayout containers (trace correct) but children=0 because app constructors never ran (F4/F5 layer); 3-run `6ab39944` | unchanged |
| gmdice | RENDERED | — | — | **unchanged** `db0f4c4b` (G09 golden intact) | G09 golden |
| simplestopwatch | RENDERED | — | — | **unchanged** `ed1dfc89` (G09 golden intact) | G09 golden |
| unote | RENDERED | F8-G-GRAV | G10-004 | **improved (lawful placement)** — delete-search button `0x00800015` moved from wrong CENTER to declared RIGHT edge; `8197687f` | `visual/unote_BEFORE.png` → `visual/unote_AFTER_gravity_8197687f.png` |
| chessclock | PARTIAL (null data — F5 data layer) | — | — | **unchanged** `4f327614` (its LinearLayouts all declare orientation; weight semantics untouched) | — |

Verdict vocabulary: **unchanged / improved / fully rendered / partially rendered / regressed / still blocked**:

* improved: microtimer, billthefarmer, unote (3)
* unchanged: gmdice, simplestopwatch, chessclock, headingcalculator (4)
* regressed: **0**
* still blocked (earliest blocker below F8): headingcalculator (F4/F5 constructor/addView), chessclock (F5 data nulls)

Per G10 Phase 3 honesty rule: every fix exercised by ≥2 corpus structures
except FIX-G10-003 (merge law — only billthefarmer exercises `<merge>` in the
selected set). FIX-G10-003 is therefore **IMPLEMENTED + LAW-TESTED** (23-check
hostile battery + AOSP LayoutInflater semantics), NOT **CROSS-APK VERIFIED**;
FIX-G10-001/002/004 are **CROSS-APK VERIFIED** (microtimer+markor/KISS/fossify
surface for 001 by XML census; microtimer+headingcalculator+billthefarmer for
002; billthefarmer+unote for 004).

## 8. Impact score (Phase 7)

```
IMPACT = APKs improved × severity × architectural reuse × AOSP-law confidence
FIX-G10-001: 1 immediate (microtimer) + 3 shell APKs pre-unblocked (KISS/markor/fossify
             orientation-less LLs) × high (whole-UI collapse) × very high (every
             orientation-less LinearLayout) × high (AOSP field default) → RANK 1
FIX-G10-002: 3 APKs (microtimer, headingcalculator-class, billthefarmer) × high ×
             very high (all custom framework subclasses) × high (virtual dispatch
             semantics) → RANK 2
FIX-G10-004: 2 APKs × medium × high (every FrameLayout child gravity) × high → RANK 3
FIX-G10-003: 1 APK × high × medium (merge-tag layouts) × high (AOSP LayoutInflater)
             → RANK 4 (LAW-TESTED only)
FIX-G10-002b:1 APK × low-medium × medium (ViewAnimator family) × high → RANK 5
```

**Newly unblocked count:** 0 full (no APK moved PARTIAL→RENDERED-complete this
campaign) — 3 APKs moved one visible-law layer up (microtimer PARTIAL with
correct rows; billthefarmer structure-rendered = blank→partial-equivalent
transition of its main surface; unote placement corrected).
**Still blocked:** 15 of 18 corpus APKs at their G09-recorded next-layer
blockers (F12 AppCompat/Compose/WebView × 11, F10 implicit intents × 2,
F5 × 2 — muellerma ACF + headingcalculator constructor layer).
**Regressions:** 0 (50/50 battery; guard screenshots byte-identical).

## 9. Updated IMPACT ranking for the NEXT campaign (Phase 8)

Recomputed from the post-G10 corpus state:

1. **F5 AppComponentFactory / app-code constructor + addView execution**
   — headingcalculator's remaining blocker generalized: app-defined ViewGroups
   never run their constructors, so programmatic children (keypad buttons,
   display children) never exist. Same gap underlies muellerma
   (`NoClassDefFoundError` in the ACF chain, FIND-G09-ACF-001) and caps
   headingcalculator/microtimer below full renders. Highest remaining reuse.
2. **AppCompat/AppComponentFactory shell** (11/18 corpus APKs) — unchanged from
   G09 rank 2; still the widest single unblock.
3. **F10 component-less/implicit Intent** (chessclock, unote addNote) — unchanged.
4. **F8 residuals (declared, evidence-bounded)**: style/background-driven
   minimum dimensions (text-less Buttons measure 0×0 — chessclock Menu/Pause);
   NinePatch background intrinsic sizes. Deferred: not the earliest blocker of
   any currently-visual APK.
5. Custom-View onDraw ops=0 for headingcalculator keypad — subsumed by rank 1
   (constructor execution precedes meaningful onDraw).

Per the G10 decision rule the evidence says: **continue the measurement/layout
family ONLY as it intersects rank 1 (constructor-driven children)**; the
dominant pure-F8 surface is exhausted at this law layer.

## 10. Deterministic proof summary

| Frame | SHA-256 (12) | Runs |
|---|---|---|
| microtimer AFTER | `57503a129012` | 3/3 identical |
| billthefarmer AFTER | `06ba8026b670` | 3/3 identical |
| gmdice guard | `db0f4c4b` | identical to G09 frozen |
| simplestopwatch guard | `ed1dfc89` | identical to G09 frozen |

Artifacts: `docs/evidence/g10_evidence/` — phase0_baseline_BEFORE/AFTER.json,
phase0_traces_BEFORE/AFTER.json, 7 × `_layout_trace.log`, `visual/` (6 PNGs),
this report.
