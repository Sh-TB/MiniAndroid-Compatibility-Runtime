# CONT-49 — solitaire past the drawer wall: three generic resource/bridge laws

Continued from remote HEAD `44dd14db` (CONT-48), per the standing "continue from
the latest remote HEAD" directive. Every row is **STATUS — RESULT — EVIDENCE**.
Work binary: rebuilt from HEAD first (identity proof), then the wave's fix
binary `6c478a224ab1b3f4`. No APK-specific hacks, no fake objects, no forced
lifecycle transitions; every law is structural.

## Phase 0 — reconciliation (measured, not assumed)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | origin/main == local HEAD == `44dd14db` after fetch + reset (local container was the CONT-10-era snapshot `e99c2fbd` again — same recovery class CONT-43/45/46 recorded); work tree had only a `tmp/flappycow` mtime artifact | git fetch + rev-parse + status |
| TESTED | binary REBUILT from HEAD: `c0f31ade222bdf9a…` == the recorded CONT-48 binary exactly (build reproducibility proven again after the container reset wiped build/) | sha256sum |
| TESTED | 7 canonical APK pins exact (dooz 299eab21, micro 79c6f730, unote be91103f, gmdice 1621eda1, opencalc 26426138, bmi 2dbd8ebe, alex b1383bc9, notes 71e874f4); tananaev_11 `294a68bd`, simplecalc_8 `68da25fd`, composeStopwatch `dbf937eb` REFETCHED SHA-exact after the reset | sha256sum |
| TESTED | solitaire store base.apk (`fdfaf7ca`) was LOST to the reset; exact bytes unrecoverable from F-Droid (vc69/70/71/66/62 hashed, none match; no GitHub release assets) — **vc71 (`9d782be2`, F-Droid suggested 3.13) substituted and BEHAVIORAL EQUIVALENCE PROVEN: it reproduces the recorded face `ba50a4d28ea62fe7` byte-identically on the CONT-48 binary, with the recorded F-NEW-309 IAE row** | run/cont49/sol71_r1; f-droid.org/api/v1/packages |
| TESTED | baseline gate on the rebuilt binary: **33/33 anchors ×3 byte-identical, ZERO DRIFT**; probe battery == records exactly (fcol 140/0 … fnew298 19/0 KEEP=5, fnew302 48/24); skill 13/13 (after rebuilding the reset-lost gate_a_probe/hmap_probe fixtures); fnew260 13/0, fnew262 19/0 | /tmp/cont49_phase0_gate2.log, gate_fix*, gate_fix2*, skill logs |
| TESTED | registry = 628 roots (last F-NEW-317) | root_registry.json |

## Phase 1 — F-NEW-309 decode (the static chain, before any fix)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | solitaire main layout truth: DrawerLayout root (fitsSystemWindows) → `<include>` (content: AppBarLayout) + NavigationView `android:layout_gravity=0x00800003` (START) — **the AppBarLayout genuinely has NO layout_gravity in real Android either; the drawer child is the NavigationView** | aapt2 dump xmltree activity_game_selector.xml |
| TESTED | DrawerLayout$g (R8-renamed LayoutParams): own int field `a` ONLY; (Context,AttributeSet) ctor = super(Context,AttributeSet) → iput 0 → obtainStyledAttributes(attrs, DrawerLayout.a) → TypedArray.getInt(0,0) → iput a:I; DrawerLayout.a = `[16842931]` = 0x010100F3 (android:layout_gravity) | scripts/cont46_disasm.py |
| TESTED | DEX-wide caller census of g(View)/j(View) — 17 callers, ALL inside DrawerLayout: addView pc=9 (pure predicate use), **g(I) pc=6: `View d = c(gravity); if (d != null) return j(d);`** (c(I) = findDrawerWithGravity: scan children, compare masked horizontal bits) — the throw rides the FOUND-drawer check | scripts/cont49_lp_caller_scan.py (new; two tool lessons: op = LOW byte, code() returns a BYTE offset) |
| TESTED | PRE-fix face: the engine answers getLayoutParams with a plain `ViewGroup$LayoutParams` (ROOT-055 fallback; no gravity field) → findDrawerWithGravity spuriously matched a gravity-0 child → j(View) threw the recorded IAE at DrawerLayout.j pc=34 | run/cont49/sol71_r1/run.log:1093 |

## Phase 2 — F-NEW-309 fix: the generateLayoutParams law (probe FIRST)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | Phase-3 probe BUILT BEFORE patching: fixtures/fnew309_probe — DrawerBox (DEX-defined container, the unrenamed DrawerLayout shape: inner LayoutParams extends MarginLayoutParams with (Context,AttributeSet) ctor reading styleable {16842931}.getInt(0,0)) + XML children with layout_gravity=start / end / absent | fixtures/fnew309_probe; scripts/cont49_build_probe.sh |
| TESTED | PRE face: P4 FAIL (`left lp class=android.view.ViewGroup$LayoutParams`) — the defect reproduced exactly, 0 uncaught | run/cont49/probe_f309_pre |
| TESTED | FIX: `generate_child_layout_params` in dalvik_engine.cpp — structural discovery (parent's `$`-prefixed inner class with super ViewGroup$MarginLayoutParams + a (Context,AttributeSet) direct ctor; (II)-ctor preference; NO name conditions — the R8-renamed DrawerLayout$g is found), real DEX ctor dispatch (ctx + AttributeSetStore records → obtainStyledAttributes → F-NEW-197 XML precedence), semantic width/height/margins write-back, stash on the ViewNode; ROOT-055 answers the stashed object; wired as a Factory-law hook (`set_generate_child_lp_hook`) at the end of inflate_element with the view-ctor dual gate | miniandroid/src/dex/dalvik_engine.cpp, framework/android_shadows.{h,cpp}, resources/layout_inflater.{h,cpp}, resources/resource_runtime.{h,cpp}, runtime/execution_engine.cpp |
| TESTED | POST face: **8/8 PASS ×3** — P4 class identity (`DrawerBox$LayoutParams`), P1/P2 start=0x800003/8388611 exact, P3 end=8388613, P5 isDrawerView(left) true, N3 plain child also carries the container class, **N1 absent-attr gravity stays 0** (AOSP getInt default), **N2 isDrawerView(plain) false** | run/cont49/probe_f309_post*, final2_f309 |
| TESTED | solitaire A/B: `[F-NEW-309] generated LP parent=Landroid/support/v4/widget/DrawerLayout; lp=DrawerLayout$g` rows for all children; the recorded IAE **GONE** (0 THROWABLE-MSG vs 9 pre-wave) | run/cont49/sol_post2_r1..r3 |

## Phase 3 — the two follow-on faces, root-caused and fixed the same way

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | Face past 309: DrawerLayout.onMeasure ISE "Child NavigationView@289 at index 2 does not have a valid layout_gravity" — the engine had NO `Gravity.getAbsoluteGravity` bridge → **F-NEW-318**: real static bridge next to the Color family (F-122 pattern): RELATIVE_LAYOUT_DIRECTION (0x00800000) family resolution START→LEFT / RTL:RIGHT, END→RIGHT / RTL:LEFT, no-rel-bit gravities UNCHANGED, other bits preserved | run/cont49/sol_post_r1/run.log:1205; dalvik_engine.cpp F-NEW-318 block |
| TESTED | Face past 318: settings-singleton NPE — `Resources.getStringArray` REC-MISS → null array → `aget-null` NPE at c/m.a pc=1200 → b.g null → `b.g.aR()` null-recv at GameSelector.onCreate pc=83/87 → **F-NEW-319**: ArscParser::resolve_string_array (canonical resolver; type gate string-array/array; complex-item walk in key order; REFERENCE items dereferenced; non-string coerced — never a silent skip) + bridge materializing the F-036 heap-array convention (MatrixCursor.getColumnNames precedent); GATE-A NotFoundException for unresolvable ids (never a silent null) | run/cont49/sol_post2_r1/run.log:570,1022,1140; arsc_parser.{h,cpp}; dalvik_engine.cpp F-NEW-319 block |
| TESTED | POST: `[F-NEW-319] getStringArray resid=0x7f03000b → String[15]` (+2/3/4-item arrays) — the settings singleton **initializes**; 0 THROWABLE-MSG rows; 6 frames rendered | run/cont49/sol_post3_r1/run.log |

## Phase 4 — regression (the closing binary 6c478a224ab1b3f4)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | **33/33 canonical anchors ×3 byte-identical, ZERO DRIFT** (dooz 31ddd4d5 / micro da73010a / unote 4f1a9e4e / gmdice f3b483fe / opencalc a976d2f9 / tttdeluxe af609429 / flappycow 13cf4746 / g2048 59ca1526 / tanana 5f7e0114 / csw 3442d9a9 / simplecalc e847ca03) | /tmp/cont49_final_gate.log |
| TESTED | probe battery == records exactly; fnew260 13/0, fnew262 19/0, **fnew309 8/0**; skill 13/13 | same |
| TESTED | support group on ONE binary: BMI `b52252c2de19b03a` ×3 (REAL_APP_CONTENT held), notes `eb5ebd559cad1028` ×3 (androidx scope held), alex `c8d69f811b23f245` ×3, sol `ba50a4d28ea62fe7` ×3 | run/cont49/support |
| TESTED | solitaire machine state: moved through THREE divergence layers (IAE gone / onMeasure ISE gone / settings NPE gone); now runs DrawerLayout.onMeasure, NavigationView real-DEX onMeasure, ContentFrameLayout 1080x1920, computeScroll; **new first divergence recorded**: f141-null-recv `Landroid/support/v4/widget/ah;.a` (R8 ViewDragHelper — mLeftDragger/mRightDragger chain) at DrawerLayout.computeScroll pc=35 + menu-hub `menu/h;.i` null-recv at design/internal/c$b.f pc=31 | run/cont49/sol_post3_r1/run.log |

## Cross-app impact (standing CONT-42 directive, measured on THIS wave)

One binary carries three generic laws: the generateLayoutParams hook fires only
for DEX-parent children at inflation (BMI's support chain / solitaire / alex —
ALL faces byte-identical ×3, BMI's REAL_APP_CONTENT held); the Gravity law only
fires on getAbsoluteGravity calls (none in the corpus faces); the string-array
law only fires on getStringArray calls (only solitaire). The fix helps exactly
the apps that ship drawer-style containers and string-array resources and
drifts nothing else — BMI improved in CONT-47/48 and stayed; every other
corpus member byte-identical ×3.

## Honest bounds

1. Solitaire's screenshot face is UNCHANGED (`ba50a4d28ea62fe7`, ×3) — the wave
   moved the MACHINE three layers deeper (0 THROWABLE rows vs 9), which is the
   honest progress definition under the "past the first runtime divergence"
   directive; the face moves only when the app's own content pipeline reaches
   drawing (ViewDragHelper + NavigationView menu + draw chain are the next roots).
2. The LP hook's margins write back from the semantic model; XML w/h flow
   through the node (ROOT-055 parity). The bridged MarginLayoutParams(Context,
   AttributeSet) still does not read XML w/h itself — the semantic model
   remains the runtime's measure truth (unchanged behavior, recorded).
3. Solitaire exact APK bytes remain unrecoverable; vc71 behavioral equivalence
   is proven by the recorded face reproducing byte-identically (Phase 0) — if
   the original bytes surface, re-pin and re-run.
4. The fnew309 probe's N2 row passes pre-fix for a false reason (instanceof
   fails → isDrawerView false) — the row set is still discriminating (P4 + 6
   FAIL rows pre-fix), noted for the record.
