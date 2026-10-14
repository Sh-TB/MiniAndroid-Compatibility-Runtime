# CONT-53 RESULT — the framework-owned field slot law (F-NEW-325)

Binary: `ff261b1bc2940bc2` (HEAD `999ffe2c` = the CONT-52 push + one generic
law on the interpreter field-key path). No APK-specific hacks. A/B probe +
runtime FIELD-TRACE proof; zero-drift gate green.

## Phase 0 — reconciliation + the recorded next frontier

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | HEAD == origin/main == `999ffe2c` (the CONT-52 push, verified) | git rev-parse |
| TESTED | the CONT-52 face reproduced: `[R347-MEASURE] view=298 NavigationView dex_onmeasure=YES wspec=0x0 hspec=0x0` — the measure chain hands the drawer spec 0; upstream = the DrawerLayout DEX onMeasure reads the child's LayoutParams fields | run/cont52/sol/r1..r3 |
| TESTED | the DrawerLayout child LP is the F-NEW-309-generated `DrawerLayout$g o409`; a write-back diagnostic pinned what was stored: **`[F-NEW-309-WB] lp=o409 node_w=-2 node_h=-1`** (wrap/match — the XML carries NO layout_width/height and the inflater default -2 is AOSP-correct) | run/cont53/wb1.err |

## Phase 1 — the decode: write -2, read 0

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED (runtime) | **FIELD-TRACE `get DrawerLayout$g;.width obj#409 value=0` ×4** — the REAL DEX DrawerLayout.onMeasure read 0 where -2 was written | run/cont53/ftw.err |
| TESTED (engine) | the interpreter iget/iput key construction used `resolved_field_declarer(ref_cls, name)` whose contract returns ref_cls AS-IS when no DEX body declares the field; `is_dex_defined_class(ref_cls)` then keyed the read with `Landroid/support/v4/widget/DrawerLayout$g;->width` (a fabricated qualified identity) — while `DrawerLayout$g` declares NO width: the field lives in the framework `ViewGroup$LayoutParams`, and every non-interpreter writer (the F-NEW-309 write-back via set_object_field, the set_field_key_resolver bare law) lands on the ONE bare slot | dalvik_engine.cpp:18466..18482; 538..565 |
| TESTED (static) | the XML truth: NavigationView carries only layout_gravity/id/fitsSystemWindows — no layout_width/height (AOSP MarginLayoutParams default = WRAP_CONTENT via getLayoutDimension's defValue); the v4 DrawerLayout.onMeasure's child-spec chain runs `getChildMeasureSpec(spec, padding, lp.width)` through real DEX | aapt2 dump xmltree activity_game_selector.xml |

## Phase 2 — A/B probe (fixtures/fnew325_probe, APK `4ba0f9edebd9d20b`)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | shape: `MyLP extends LinearLayout.LayoutParams` (DEX, declares only `tag`) + `MyBox extends LinearLayout` whose DEX methods read `((MyLP) getLayoutParams()).width/height/tag` — iget ref class = MyLP (DEX), fields declared by the FRAMEWORK | fixtures/fnew325_probe |
| TESTED | **PRE ×3 (unpatched binary `b5998a50a679c2e3`)**: P1-FRAMEWORK-WIDTH `readWidth=0` FAIL, P2-FRAMEWORK-HEIGHT `readHeight=0` FAIL — the fabricated qualified key answered the default; N1 (DEX-declared `tag` — qualified slot) and N2 (framework-typed ref — bare) PASS | run/cont53/f325_pre/r1..r3 (first pass) |
| TESTED | **POST ×3 (binary `ff261b1bc2940bc2`)**: 4/0 — P1 `readWidth=77`, P2 `readHeight=88`, N1 `readTag=held` (the DEX-declared qualified face UNTOUCHED), N2 `plain.width=77` | run/cont53/f325_pre/r1..r3 (rebuild pass) |

## Phase 3 — the fix (minimal, generic, ART-faithful)

| Law | Change | Scope guard |
|-----|--------|-------------|
| F-NEW-325 | `true_dex_field_declarer(ref_cls, name)` — the chain walk must VERIFY the field body and return "" when no DEX class declares it (framework-owned → ONE bare slot); applied at the 4 interpreter key sites (execute_iget, execute_iget_object, execute_iput, execute_iput_object). Real DEX declarers keep the qualified slot + the raw bare mirror (F-NEW-321 law unchanged); the set_field_key_resolver already had the correct verify-the-body logic — the interpreter families now agree with it | dalvik_engine.cpp:18484..18518 + 4 call sites; dalvik_engine.h declaration |

## Phase 4 — POST verification (final binary `ff261b1bc2940bc2`)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | **FIELD-TRACE `get DrawerLayout$g;.width obj#409 value=-2` ×4** — the REAL DEX measure chain now reads the WRITTEN wrap value (0 → -2) | run/cont53/ftw2.err |
| TESTED | solitaire ×3: 0 uncaught (only the two historical benign deferreds), GameSelector.onResume dispatches, detach-IAE 0, ay$w.q NPE 0; screenshot face `ba50a4d28ea62fe7` UNCHANGED ×3 (honest) | run/cont53/sol/r1..r3 |
| TESTED | zero-drift regression gate: **33/33 REG rows MATCH** (11 canonical anchors ×3 byte-identical incl. dooz `31ddd4d5b8e6d18e`); probe battery == records; **support group BMI `b52252c2de19b03a` / alex `c8d69f811b23f245` / notes `eb5ebd559cad1028` MATCH ×2**; fnew325 4/0 ×3 | run/cont53/gate_cont37.log; run/cont53/gate_* |

## Honest bounds + next frontier

F-NEW-325 makes the interpreter's field-slot identity agree with ART on the
framework-owned leg (a class-agnostic law: every framework field reached
through a DEX ref class gains the single bare slot). The solitaire frame
verdict is UNCHANGED (DEFAULT_BACKGROUND_ONLY / APP_PIXELS) and the drawer
spec is still 0: with the field now reading -2, the NEXT divergence sits one
layer deeper — the v4 `DrawerLayout.getChildMeasureSpec(III)I` DEX body
answers an invalid value (-1/0) for the (EXACTLY\|1080, padding, wrap=-2)
input (METHOD-TRACE: pc=302 invoke-static → move-result -1), so its inner
MeasureSpec.getMode/getSize dispatch or branch shape is the recorded next
decode (F-NEW-309 row refreshed). No fix was made for that face this wave —
no fix without its own decode cycle.

**Registry 635→636** (F-NEW-325 appended ROOT-CAUSED-FIXED; F-NEW-309
next_wave refreshed). Evidence: `evidence/cont53/CONT53_RESULT.md`.
