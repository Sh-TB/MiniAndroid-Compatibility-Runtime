# G11/G12 FINAL REPORT — REAL DEX CONSTRUCTOR + CUSTOM VIEW HIERARCHY + MEASUREMENT/LAYOUT CROSS-APK COMPATIBILITY CAMPAIGN

Base HEAD: `167c27fb` recovered → rebased as `d8b66526` on top of origin `3d063e01` (G10 publication record; origin content verified byte-identical subset).
Final HEAD: `28c1bfe1`.
Battery: **52/52 ALL PASS** (48 pre-G11 stages + G10 law stage + 2 new G11 stages), zero golden changes.
Corpus: same 8-APK set before/after, SHA-256-verified (18-APK frozen manifest).

## 1. Phase-0 baseline integrity

Baseline captured BEFORE engine changes (proof: 4 screenshot hashes == G10 frozen goldens —
microtimer `57503a12`, simplestopwatch `ed1dfc89`, gmdice `db0f4c4b`, unote `8197687f`).
Environment restored per §1.7: aapt2 8.13.2-14304508 (Google Maven), HelloWorldSelfAware
external fixture (SHA `009b4671…` matches recorded), 8 campaign APKs hash-verified.

## 2. Table 1 — per-APK constructor/hierarchy/measurement/visual state (before → after)

| APK | ctor executes? | super chain real? | addView real? | child count > XML? | measure proof | layout proof | visual | 3-run | status |
|---|---|---|---|---|---|---|---|---|---|
| headingcalculator | YES (CalculatorDisplay, CalculatorKeypad, ExplainableTextView ×6, ExplainableButton — all `<init>(Context, AttributeSet)` real DEX) | YES (`CalculatorKeypad→LinearLayout→ViewGroup→View→Object`; `ExplainableTextView→TextView→View→Object`; `ExplainableButton→Button→TextView→View→Object`) | YES (`inflate(res, this)` + framework addView mount ctor subtrees) | YES (3 XML nodes → 46+ node final tree: display grid + 4 keypad rows) | YES (`CalculatorDisplay 1080x0 → 1080x158`; rows `158x44/169x44/146x44`; `TableLayout` vertical law) | YES (keypad rows re-measured `EXACTLY(480)` by AOSP weight second pass) | CHANGED `6ab39944→0f933ff8` (268,977 px diff; 0.263%→6.72% nonbg) | PASS (3× byte-identical) | **RUNTIME-PROVEN + VISUALLY-PROVEN** |
| microtimer | YES (obfuscated `Lk/g;.<init>(Context, AttributeSet)` — setOrientation + new Button + `new RoTimeControl` + `addView` ×2; `RoTimeControl.a()` programmatic TextView) | YES (`Lk/g→LinearLayout→…`; `RoTimeControl→FrameLayout`) | YES (real app `addView(RoTimeControl)` + `addView(Lk/f)`) | YES (25 → 26 nodes; new real TextView 640x123) | YES (row `1080x210` unchanged; new label `640x123`) | YES (pixel delta band rows 951–1076 == exactly the new real TextView) | CHANGED `57503a12→0c90e960` (classified LAWFUL — 'null:null:null' is the app's own Java null-concat at construction; timer-tick update = G07 future layer) | PASS (3× byte-identical) | **RUNTIME-PROVEN + VISUALLY-PROVEN (cross-verified obfuscated code)** |
| billthefarmer_notes | n/a (no custom-tag XML on the rendered screen) | — | — | — | — | — | SAME | — | regression-guard PASS |
| muellerma_stopwatch | SKIP by law (bundled `android.app.AppComponentFactory.<clinit>` = constructed-and-threw stub; parent-delegation forbids executing it) | — | — | — | — | — | SAME (diff=0) | — | **CLASSIFIED (new cluster FIND-G11-NOACTIVITY-001)** |
| simplestopwatch | n/a (guard) | — | — | — | — | — | SAME | — | regression-guard PASS |
| gmdice | n/a (guard) | — | — | — | — | — | SAME | — | regression-guard PASS |
| unote | n/a (guard) | — | — | — | — | — | SAME | — | regression-guard PASS |
| chessclock | n/a (guard) | — | — | — | — | — | SAME | — | regression-guard PASS |

Cross-APK standard (§32): constructor law proven on **2 independent real APKs** (different packages,
different UI architectures: headingcalculator = XML custom tags; microtimer = obfuscated programmatic
build) + 6 byte-identical guards → **CROSS-APK VERIFIED** for FIX-G11-001/002; ancestry/normalization
laws verified on the same corpus.

## 3. Table 2 — capability × law × evidence

| Capability | AOSP law | APKs exercised | runtime proof | visual proof | regression | status |
|---|---|---|---|---|---|---|
| Real DEX View constructor execution `FIX-G11-001` | LayoutInflater.createView (XML tag → resolve → verify View subtype → `<init>(Context, AttributeSet)`) | headingcalculator, microtimer | MINIANDROID_G11_TRACE constructor+super-chain proof; 37-check law battery | screenshot diff | 52/52 | **VERIFIED** |
| LayoutInflater.inflate(res, root, attachToRoot) `FIX-G11-002` | LayoutInflater.inflate (2-arg == root!=null; returns ROOT) | headingcalculator (calculator_display.xml + calculator_keypad.xml inflate into `this`) | ctor-built subtrees mounted in final window tree | display grid renders | 52/52 | **VERIFIED** |
| LayoutInflater Factory survival (process-wide hook) | AppCompatDelegateImpl.installViewFactory re-applies Factory2 on every new inflater | headingcalculator (hook was silently wiped by ensure_loaded recreation — root cause F5-C1) | regression test in g11 law battery [B] | — | 52/52 | **VERIFIED** |
| AOSP framework ancestry law `FIX-G12-001` | framework `extends` hierarchy is fixed (TableRow/TableLayout→LinearLayout, ScrollView→FrameLayout, Button→TextView) | headingcalculator (TableRow was leaf-classified 0x0 under 44px children) | U007_LAYOUT_DEBUG=3 spec dumps; final tree `TableLayout 1080x158` | display grid renders | 52/52 | **VERIFIED** |
| Descriptor form normalization `FIX-G12-001b` | DEX=slash-form, AXML=dot-form; cross-layer compare must normalize | headingcalculator (dot-form app descriptors vs slash-form maps), muellerma (framework-skip bypassed by dot-form) | container probe `vgsub=1` after fix | screenshot diff | 52/52 | **VERIFIED** |
| Classifier Factory survival `FIX-G12-002` | same Factory law for is_a | headingcalculator (is_a wired only on renderer path — window path classified app containers as leaves) | window path final pass `CalculatorDisplay 1080x158` | screenshot diff | 52/52 | **VERIFIED** |
| TableLayout vertical stacking `FIX-G12-001` | TableLayout stacks rows vertically (its orientation field never XML-set) | headingcalculator (measured as ONE horizontal row: content_w=473=sum) | `content=169x158 → 1080x158` | — | 52/52 | **VERIFIED** |
| addView single-mount + cycle hostility (§28) | ViewGroup.addView "child already has a parent" | g11 law battery [D] 14 checks | self-mount rejected, duplicate no-op, ancestor-cycle rejected | — | 52/52 | **VERIFIED** |
| Parent-delegation for framework `<clinit>` `FIX-G12-003` | ART boot classpath owns android.*/java.* | muellerma (bundled ACF stub constructed-and-threw — disassembly-verified) | `[G12-ACF] skipped` in log | screenshot diff=0 | 52/52 | **VERIFIED** |
| Activity-less app boot `FIND-G11-NOACTIVITY-001` | launcher never opens activity-less apps | muellerma (manifest: no activity — tile-only app) | EXP-031.5 assertion scoped to activity apps | PARTIAL state preserved | 52/52 | **CLASSIFIED + LAW-TESTED** |
| LinearLayout weight second pass (pre-existing G04 §9) | LinearLayout.java measureVertical weighted re-measure | headingcalculator keypad (rows 0dp+weight=1000 → EXACTLY(480) re-measure) | spec dumps | keypad renders | 52/52 | **VERIFIED (pre-existing law exercised by new corpus)** |

## 4. Determinism (§31)

- headingcalculator: 3 clean runs → screenshot SHA-256 unique count = 1 (`0f933ff8…`).
- microtimer: 3 clean runs → unique count = 1 (`0c90e960…`).
- Battery 3-run gates (G06 tap, G07 finish-cascade, G08 navigation): ALL PASS at final HEAD.

## 5. Regression (§30)

- Battery 52/52 ALL PASS at `28c1bfe1`. G06/G07/G08 interaction goldens, EXT-01 typography golden
  (9 checks), EXT-02 interaction golden (12 checks), density-matrix oracle, resource/lifecycle/input
  law batteries — all unchanged. Zero golden updates were needed (no golden was proven wrong).

## 6. Remaining blockers (ranked by affected APKs / severity / depth)

1. **F8-residual: headingcalculator keypad width** — keypad buttons render left-packed (~343px of
   1080). Runtime parses buttons as wrap/wrap without weights; need the app's reference screenshot
   to decide whether the lawful render spreads them (row gravity/weightSum) or left-packs. Blocked
   on reference evidence, not on runtime capability.
2. **F12 AppCompat/Compose/WebView/GL shells** (11/18 G09 corpus) — unchanged scope, next-campaign
   tier (recorded, not patched per §29).
3. **G07 timer-tick label updates** — microtimer 'null:null:null' construction-era label would be
   replaced by the first tick on a real device; needs MessageQueue timer scheduling (recorded).
4. **F10 implicit intents** (chessclock, unote) — unchanged.
5. **TableLayout column stretch/shrink law** — rows render with per-row wrap widths; AOSP column
   distribution is deeper (recorded as future layer).

## 7. Commits (semantic grouping per §36)

- `d8b66526` phase-0 corpus baseline (8 APKs) + FIX-G11-001 real DEX ctor execution + FIX-G11-002 inflate(res, root, attachToRoot) [recovered WIP, honestly reworded, rebased]
- `f42cf79c` Factory-law fix: ctor hook survives LayoutInflater recreation (ResourceRuntime ownership)
- `62257d6f` 37-check G11 ctor/Factory/addView law battery + addView single-mount hardening
- `e7a00f3b` G12 framework ancestry law + descriptor normalization + TableLayout vertical law
- `28c1bfe1` parent-delegation law for framework `<clinit>` + activity-less app boot law
