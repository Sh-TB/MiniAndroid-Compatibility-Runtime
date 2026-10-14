# CONT-54 RESULT — the framework-boundary static resolution law + the AOSP
# ViewGroup.getChildMeasureSpec spec law (F-NEW-326)

Binary: `94d626170bc86331` (HEAD `d5bbf5d4` = the CONT-53 push + two generic
laws on the invoke-static path). No APK-specific hacks, no R8-name
special-casing, no fake objects. A/B probes (two variants) + runtime
R347-MEASURE proof; zero-drift gate green (15 anchors x3 + probe battery).

## Phase 0 — reconciliation + fresh app measurements (the standing question:
## "did Dooz and the calculator progress?")

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | HEAD == origin/main == `d5bbf5d4` (the CONT-53 push) after the recurring stale-container recovery (local was the CONT-10-era `e99c2fbd`; 93 commits fetched) | git fetch + rev-parse |
| TESTED | binary REBUILT from HEAD == recorded `ff261b1bc2940bc2` byte-identical (build reproducibility) | sha256sum build/miniandroid |
| TESTED | **Dooz progress re-measured at HEAD**: the canonical 15s anchor `31ddd4d5b8e6d18e` holds x3 (the honest keep-empty face at the gate budget); the FULL-budget run (no wall cap) renders the REAL Scaffold `6841d52a20e6597e` x3 byte-identical — the CONT-48 real-content face re-proven at HEAD (the boot composition completes; the 15s gate face is a budget class per F-NEW-314, not a correctness defect) | run/cont54/dooz_anchor/r1..r3; run/cont54/dooz15/r1..r3 |
| TESTED | **BMI Calculator re-measured at HEAD**: `b52252c2de19b03a` x3 — the CONT-47 REAL_APP_CONTENT face (real EditText/Spinner/Button "Calculate BMI" tree) holds | run/cont54/bmi/r1..r3; gate2/g3 runs |
| TESTED | support group re-measured: alex `c8d69f811b23f245`, notes `eb5ebd559cad1028`, sol `ba50a4d28ea62fe7` — all held | run/cont54/{alex,unote,sol_post} + canonical gate rows |

## Phase 1 — the decode: the "-1/0" face is an UNDECLARED method_id

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED (byte-level) | `DrawerLayout.getChildMeasureSpec(III)I` is invoked twice inside DrawerLayout.onMeasure (@0x0123 width, @0x012e height) — and **NO class in the whole DEX declares it**: DrawerLayout's class_data (sf=4, inf=35, dm=14, vm=67, 120 members) jumps `m@5124 -> m@5143`, skipping m@5133; NestedScrollView (78 methods), ActionMenuView (4), Toolbar (77), ar (9) likewise list NO declaration. FIVE method_ids name their OWN class as owner: DrawerLayout m@5133, NestedScrollView m@5251, ActionMenuView m@7364, Toolbar m@8216, ar m@8737 — all sig `(III)I` (proto parser validated against DrawerLayout.onMeasure=(II)V and View.measure=(II)V) | scripts/cont54_scan_method_ids.py; scripts/cont54_find_method.py; /tmp/drawerlayout_all.txt |
| TESTED (Dalvik spec) | ART invoke-static resolution walks the named class's FULL superclass chain — past the DEX boundary into the framework — to the declarer: the only reachable target is the framework `ViewGroup.getChildMeasureSpec(III)I` (public static, API 1). Real devices run this APK fine — the framework law is what executes | Dalvik spec + AOSP ViewGroup.java |
| TESTED (engine) | try_recursive_invoke (local exact + F-074/F-280 super-walk) only walks DEX ancestors (class_info_index_ = APK classes) → miss; bridge_to_api keyed on the APP class → no shadow → the STUBBED typed-default tail answered for an `I` return `make_int(0)` — the CONT-53 recorded face | dalvik_engine.cpp: try_recursive_invoke REC-MISS branch + bridge_to_api typed-default tail |

## Phase 2 — probe FIRST (fixtures/fnew326_probe, real aapt2/ECJ/D8)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | TWO variants from ONE source tree: `fnew326_probe.apk 36c7cb1a183b006a` (direct ViewGroup owner) and `fnew326b_probe.apk eee1a164d1a74b60` (the method_id class_idx byte-rewritten to MyBox — the exact R8 artifact shape; scripts/cont54_patch_method_id.py patched 1 method_id) | run/cont54/fnew326{,b}_probe.apk |
| TESTED | **PRE x3 on the unpatched binary `ff261b1bc2940bc2`**: 12 FAIL / 1 PASS (N1 negative control) on BOTH variants — every row `got=0x0` (the STUBBED default) | run/cont54/pre_fnew326*/r1..r3 |
| TESTED | **POST x3 on `94d626170bc86331`**: **13/0 x3 on BOTH variants** — the full AOSP matrix (P1..P10: EXACTLY/AT_MOST/UNSPECIFIED x dim>=0/MATCH/WRAP with padding), N1 (EX-NEG-DIM → 0, AOSP-true), and the subclass-owner faces P11/P12 through the re-dispatch chain (MyBox → LinearLayout STUBBED → ViewGroup LAW) | run/cont54/post_fnew326*/r1..r3 |

## Phase 3 — the fix (minimal, generic, ART-faithful; two layers)

| Law | Change | Scope guard |
|-----|--------|-------------|
| F-NEW-326a (resolution) | execute_invoke_static: after the first bridge dispatch ends **STUBBED** (the typed-default tail — side-effect-free, so a retry cannot double-fire any handler), walk the superclass chain past the DEX boundary (nearest framework ancestor first, bounded 16 hops) and accept the first IMPLEMENTED framework law; otherwise the original STUBBED answer stands byte-identically. Bounded [F-NEW-326] re-dispatch diagnostic | dalvik_engine.cpp (execute_invoke_static bridge arm) |
| F-NEW-326b (the law) | the exact AOSP `ViewGroup.getChildMeasureSpec(III)I` switch: EXACTLY parent (dim>=0 → EXACTLY\|dim; MATCH → EXACTLY\|size; WRAP → AT_MOST\|size), AT_MOST parent (dim>=0 → EXACTLY\|dim; else AT_MOST\|size), UNSPECIFIED parent (dim>=0 → EXACTLY\|dim; else UNSPEC\|size); size = max(0, specSize − padding); in-place mode representation (F-096b law); framework-exact guard `Landroid/view/ViewGroup;` + method name + argc | dalvik_engine.cpp (bridge_to_api, co-located with the MeasureSpec statics block) |

## Phase 4 — runtime verification (solitaire, binary `94d626170bc86331`)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | `[F-NEW-326] static re-dispatch ...Toolbar;.getChildMeasureSpec as Landroid/view/ViewGroup; (framework boundary)` fires; the law answers real specs: `(spec=0x40000438 pad=0 dim=-2) -> 0x80000438` (AT_MOST\|1080), `(spec=0x40000780 pad=0 dim=-1) -> 0x40000780` (EXACTLY\|1920) | run/cont54/sol_post/r1.err |
| TESTED | **the CONT-52/53 spec-0 face is DEAD**: `[R347-MEASURE] view=298 NavigationView dex_onmeasure=YES wspec=0x80000390 (AT_MOST\|912) hspec=0x40000780 (EXACTLY\|1920) -> 0x1920` x2 — the drawer child now measures at real specs through the REAL DEX chain; NavigationMenuView (view=322) exists, is addView'd (NavigationView.<init> pc=194) and attaches (UC009-ATTACH view=322) | run/cont54/sol_post/r1..r3 |
| TESTED (honest) | screenshot face `ba50a4d28ea62fe7` UNCHANGED x3 — the menu-content render pipeline is the recorded NEXT frontier (NavigationMenuView's own DEX onMeasure dispatch: DEFAULT-MEASURE view=322 overrides_onMeasure=1 flag=0 — the override exists, its DEX body not yet observed executing); 0 uncaught / 0 APP-BOUNDARY | run/cont54/sol_post/r1..r3 |

## Phase 5 — zero-drift regression gate (binary `94d626170bc86331`)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | **15 canonical anchors/controls x3 byte-identical** under the canonical config (`--frames 5 --max-seconds 15`): dooz `31ddd4d5` / micro `da73010a` / unote `4f1a9e4e` / gmdice `f3b483fe7b7cf51b` / opencalc `a976d2f9` / tttdeluxe `af6094295ecb50e3` / flappycow `13cf4746` / g2048 `59ca1526` / tanana `5f7e0114c3bfd6b5` / csw `3442d9a9` / simplecalc `e847ca0346708f07` + support BMI `b52252c2` / alex `c8d69f81` / notes `eb5ebd55` / sol `ba50a4d2` — **45/45 MATCH, ZERO DRIFT** | run/cont54/gate2_*, g3_* |
| TESTED | probe battery == records: fnew309 8/0, fnew320 7/0, fnew322 5/0, fnew323 6/0, fnew324 3/0, fnew325 4/0 (rebuilt after the reset; APK SHA deltas from the res-less fixture rebuilds recorded honestly — judgment is by ROWS) | run/cont54/probe_* |
| TESTED | reset-lost gate APKs refetched SHA-exact: tananaev `294a68bd` (vc11 — vc10 is a different build, honestly noted), simplecalc `68da25fd`, composeStopwatch `dbf937eb` | upload/cont54_refetch/ |

## Honest bounds + next frontier

F-NEW-326 closes the resolution face CONT-53 recorded. The solitaire frame
verdict is UNCHANGED (DEFAULT_BACKGROUND_ONLY / APP_PIXELS): with the drawer
child now measured at real specs, the next divergence is the menu-content
render pipeline — NavigationMenuView's own DEX onMeasure (the override exists;
the DEX body has not been observed executing) and the RecyclerView/menu-
adapter chain behind it. No fix was attempted for that face this wave — no
fix without its own decode cycle.

**Registry 636→637** (F-NEW-326 appended ROOT-CAUSED-FIXED; F-NEW-309
next_wave refreshed). Evidence: `evidence/cont54/CONT54_RESULT.md`.
