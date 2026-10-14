# CONT-55 RESULT — the AOSP AttributeResolution DEF-STYLE stages (F-NEW-327)

Binary: `6014ae17af2ecd60` (HEAD `090d4a8a` = the CONT-54 closeout + the
def-style law on both TypedArray producers). No APK-specific hacks, no R8-name
special-casing, no fake objects. A/B probe + runtime SGET/CS-PRODUCER/
R347-MEASURE proof chain; zero-drift gate green (15 anchors x3 + probe battery).

## Phase 0 — reconciliation + the CONT-54 frontier decode

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | HEAD == origin/main == `090d4a8a` (the CONT-54 closeout push) | git rev-parse |
| TESTED | the CONT-54 recorded next frontier = the menu-content render pipeline: NavigationMenuView (view=322) exists, attaches — and the CONT-54 measure rows showed `R347-MEASURE view=298 NavigationView ... -> 0x1920` = **NavigationView measured 0 wide x 1920** | run/cont54/sol_post/r1.err |
| TESTED | `NavigationMenuView.setMeasuredDimension(0, 1920)` (ARG-TRACE) — the menu view measured 0 wide THROUGH the running DEX chain (ay.e -> setMeasuredDimension) | run/cont55/sol_argtrace.err |

## Phase 1 — the decode: the width died in the STYLE stage

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED (byte-level) | NavigationView.onMeasure (50 units, DEX): sparse-switch on the width-spec mode — **payload parsed (keys FIRST then targets): AT_MOST -> `makeMeasureSpec(min(specSize, mMaxWidth), EXACTLY)` @0x000d; UNSPECIFIED -> `makeMeasureSpec(mMaxWidth, EXACTLY)` @0x001c; EXACTLY -> straight to `invoke-super f.onMeasure`** | scripts/cont55_sparse_switch.py (payload @0x0024: keys [0x80000000, 0, 0x40000000] -> targets [+7, +22, +3]) |
| TESTED (byte-level) | NavigationView.<init>: `mMaxWidth (f@2041) = bn.e(f@1681 = a$i.NavigationView_android_maxWidth, v1)` where `v1 = sget a$h.Widget_Design_NavigationView` — the 4-arg TintTypedArray wrapper -> `Context.obtainStyledAttributes(set, styleable, defStyleAttr, defStyleRes)` (proto verified `(Landroid/util/AttributeSet;[III)I`, cnt=5) | /tmp/navview_all.txt; bn.a disasm (m@179) |
| TESTED (runtime) | `[SGET] NavigationView.<init> pc=24 field=a$h.Widget_Design_NavigationView value=2131755392` (0x7f100180) — the defStyleRes value was ON the register; the CS-PRODUCER array probe pinned the 10-attr call `attrs=[0x10100d4,0x10100dd,0x101011f(maxWidth),...]` with **dSA=0x0 dSR=0x0** | run/cont55/sol_attr2..4.err |
| TESTED (engine) | TWO stacked gaps: (a) both TypedArray producers (ContextShadow F-093 + the S101 Resources$Theme producer) walked only XML (1) + theme (5) — the AOSP AttributeResolution style stages (2 xmlStyle / 3 defStyleAttr / 4 defStyleRes) never ran; (b) the bridge maps a literal-0 int arg to NULL_REF (kind 7) — the def-style pair extraction gated on Kind::INT dropped BOTH args (`a2:k7=0 a3:k0=0x7f100180` — the value WAS in args[3]) | run/cont55/sol_attr4.err |

## Phase 2 — the fix (minimal, generic, ART-faithful; three layers)

| Law | Change | Scope guard |
|-----|--------|-------------|
| F-NEW-327a (the stages) | `ResourceRuntime::resolve_def_style_attr_value(apk, attr, dSA, dSR, xmlStyle)`: stage 2 (xml style= bag), stage 3 (defStyleAttr -> the theme's style reference -> bag), stage 4 (defStyleRes bag) — each `bag_value` (the ResTable_map_entry parent chain) + REFERENCE deref (package-routed app -> framework); DIMENSION -> device px (`complex_unit_to_dimension_pixel_size`, the AOSP TypedArray getDimensionPixelSize contract) | resource_runtime.{h,cpp} |
| F-NEW-327b (wiring) | BOTH producers call the resolver between XML (1) and theme (5) — the AOSP order XML -> xmlStyle -> defStyleAttr -> defStyleRes -> theme; the theme path kept verbatim as stage 5; the S101 producer also gained the stage-1 raw-XML read (the xml_attr_is_int_family law) | android_shadows.cpp (ContextShadow) + dalvik_engine.cpp (S101) |
| F-NEW-327c (arg law) | the def-style pair extraction is POSITIONAL (the overloads place it right after the styleable int[]) accepting INT and NULL_REF alike (`dalvik_int_value`/int_val) — a literal-0 int arrives as NULL_REF | both producers |

## Phase 3 — probe A/B (fixtures/fnew327_probe, real aapt2/ECJ/D8 with res)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | `fnew327_probe.apk 57ec5cdf6806255c` — res carries boxMax/boxMin attrs + F327_BoxStyle (280dp/48dp) + a theme WITHOUT them (the style stage is the ONLY source); the app reads through the exact NavigationView ctor shape (defStyleAttr=0, defStyleRes=the style, def=-1) | run/cont55/fnew327_probe.apk |
| TESTED | **PRE x3 on the CONT-54 binary `ff261b1bc2940bc2`**: P1 `got=-1` FAIL, P2 `got=-1` FAIL (the def channel survived, the style value lost), N1 sanity PASS | run/cont55/pre_f327p/r1..r3 |
| TESTED | **POST x3 on `6014ae17af2ecd60`: 3/0 x3** — P1 `got=735 want=735 (280dp px-decoded)`, P2 `got=126 want=126 (48dp)` | run/cont55/post_f327p/r1..r3 |

## Phase 4 — runtime verification (solitaire, binary `6014ae17af2ecd60`)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | **`[R347-MEASURE] view=298 NavigationView wspec=0x80000390 hspec=0x40000780 -> 735x1920`** x2 (was 0x0) — 735 = 280dp x 2.625, the style's maxWidth clamping the AT_MOST drawer spec through the AOSP min() law | run/cont55/sol_f327c.err |
| TESTED | **`NavigationMenuView.setMeasuredDimension(735, 1920)`** (was 0, 1920) — the FULL drawer measure chain is AOSP-faithful end to end: F-NEW-326 specs -> the real DEX NavigationView.onMeasure min() -> the style-sourced mMaxWidth -> the menu view inherits | run/cont55/sol_menu.err |
| TESTED (honest) | screenshot face `ba50a4d28ea62fe7` UNCHANGED — the closed drawer's pixels sit off-screen; the OPEN-drawer flow (the menu-content draw pipeline) is the recorded next decode | run/cont55/sol_f327c/screenshot.png |

## Phase 5 — zero-drift regression gate (binary `6014ae17af2ecd60`)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | **15 canonical anchors/controls x3 byte-identical — 45/45 MATCH**: dooz `31ddd4d5` / micro `da73010a` / unote `4f1a9e4e` / gmdice `f3b483fe7b7cf51b` / opencalc `a976d2f9` / tttdeluxe `af6094295ecb50e3` / flappycow `13cf4746` / g2048 `59ca1526` / tanana `5f7e0114c3bfd6b5` / csw `3442d9a9` / simplecalc `e847ca0346708f07` + BMI `b52252c2` / alex `c8d69f81` / notes `eb5ebd55` / sol `ba50a4d2` | run/cont55/smoke_*, g3_* |
| TESTED | probe battery == records on the NEW binary: fnew309 8/0, fnew320 7/0, fnew322 5/0, fnew323 6/0, fnew324 3/0, fnew325 4/0, fnew326 13/0 | run/cont55/probe_* |

## Honest bounds + next frontier

The drawer measure chain is now AOSP-faithful end to end (real specs -> real
DEX min() -> the style-sourced mMaxWidth -> real child dims). The visible frame
is unchanged because the closed drawer's pixels sit off-screen; the next
decode is the menu-content DRAW pipeline (the open-drawer flow:
NavigationMenuView's RecyclerView draw chain at its real 735x1920 geometry).
No fix was attempted for that face this wave — no fix without its own decode
cycle.

**Registry 637->638** (F-NEW-327 appended ROOT-CAUSED-FIXED). Evidence:
`evidence/cont55/CONT55_RESULT.md`.
