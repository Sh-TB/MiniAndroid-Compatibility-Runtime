#!/usr/bin/env python3
"""cont54_issue_comment.py — post the CONT-54 line-by-line audit to Issue #375.

Lineage: continued from remote HEAD d5bbf5d4 (CONT-53). Rebuilt binary
ff261b1b (identity proof) -> 94d62617 (two generic laws). Every row is
STATUS — RESULT — EVIDENCE; nothing claimed DONE beyond its row.
"""
import json, subprocess

BODY = """## CONT-54 execution-stage audit — the framework-boundary static resolution law + the AOSP ViewGroup.getChildMeasureSpec spec law (F-NEW-326)

Continued from remote HEAD `d5bbf5d4` (CONT-53), per the "continue from the latest remote HEAD" directive. Every row is **STATUS — RESULT — EVIDENCE** with exact artifacts. Work binary: rebuilt-from-HEAD `ff261b1b…` (identity proof) → fix binary `94d62617…`. No APK-specific hacks, no R8-name special-casing, no fake objects.

### Phase 0 — reconciliation + the standing app-progress question (measured, not assumed)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | origin/main == local == `d5bbf5d4` after fetch+reset (local was the CONT-10-era `e99c2fbd` again — the recorded recovery class); 93 commits fetched | git fetch + rev-parse |
| TESTED | binary REBUILT from HEAD == recorded `ff261b1bc2940bc2` byte-identical — build reproducibility | sha256sum build/miniandroid |
| TESTED | **Dooz progress re-measured at HEAD**: the canonical 15s anchor `31ddd4d5b8e6d18e` ×3 held (the honest keep-empty face at the gate budget); the FULL-budget run renders the **REAL Scaffold `6841d52a20e6597e` ×3 byte-identical** — the CONT-48 real-content face re-proven at HEAD (boot composition completes; the 15s face is a budget class per F-NEW-314, not a correctness defect) | run/cont54/dooz_anchor/r1..r3; run/cont54/dooz15/r1..r3 |
| TESTED | **BMI Calculator re-measured at HEAD**: `b52252c2de19b03a` ×3 — the CONT-47 REAL_APP_CONTENT face holds (real EditText/Spinner/"Calculate BMI" tree) | run/cont54/bmi/r1..r3 |
| TESTED | support group held: alex `c8d69f81` / notes `eb5ebd55` / sol `ba50a4d2` | run/cont54/* + canonical gate rows |

### Phase 1 — the decode: the CONT-53 "-1/0" face is an UNDECLARED method_id

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED (byte-level) | `DrawerLayout.getChildMeasureSpec(III)I` is invoked twice in DrawerLayout.onMeasure (@0x0123 width, @0x012e height) and **NO class in the whole DEX declares it** — DrawerLayout's class_data (sf=4/inf=35/dm=14/vm=67) jumps `m@5124 → m@5143`; NestedScrollView (78 methods), ActionMenuView (4), Toolbar (77), ar (9) likewise list no declaration. FIVE method_ids name their OWN class as owner: DrawerLayout m@5133, NestedScrollView m@5251, ActionMenuView m@7364, Toolbar m@8216, ar m@8737 — all `(III)I` (parser validated against DrawerLayout.onMeasure=(II)V / View.measure=(II)V) | scripts/cont54_scan_method_ids.py; scripts/cont54_find_method.py |
| TESTED (Dalvik spec) | ART invoke-static resolution walks the named class's FULL superclass chain — past the DEX boundary into the framework — to the declarer: the only reachable target is the framework `ViewGroup.getChildMeasureSpec(III)I` (public static, API 1) | Dalvik spec + AOSP ViewGroup.java |
| TESTED (engine) | try_recursive_invoke (local + F-074/F-280 super-walk) walks DEX ancestors only; bridge_to_api keyed on the APP class → STUBBED typed-default `0` — the CONT-53 face | dalvik_engine.cpp |

### Phase 2 — probe FIRST (two variants, real toolchain)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | `fnew326_probe.apk 36c7cb1a183b006a` (direct ViewGroup owner) + `fnew326b_probe.apk eee1a164d1a74b60` (the method_id class_idx byte-rewritten to MyBox — the exact R8 artifact shape; 1 method_id patched) | run/cont54/fnew326{,b}_probe.apk; scripts/cont54_patch_method_id.py |
| TESTED | **PRE ×3 on `ff261b1bc2940bc2`**: 12 FAIL / 1 PASS (N1 negative control) on BOTH variants — every row `got=0x0` (the STUBBED default) | run/cont54/pre_fnew326*/r1..r3 |
| TESTED | **POST ×3 on `94d626170bc86331`: 13/0 ×3 on BOTH variants** — the full AOSP matrix (P1..P10 with padding), N1 (AOSP-true 0), and the subclass-owner faces P11/P12 through the re-dispatch chain (MyBox → LinearLayout STUBBED → ViewGroup LAW) | run/cont54/post_fnew326*/r1..r3 |

### Phase 3 — the fix (minimal, generic, ART-faithful)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| FIXED | **F-NEW-326a (resolution)**: execute_invoke_static retries the bridge under the framework ancestors (nearest first, bounded 16) ONLY after the first dispatch ended **STUBBED** (the typed-default tail is side-effect-free — a retry cannot double-fire any handler; the original answer stands byte-identically otherwise) | dalvik_engine.cpp |
| FIXED | **F-NEW-326b (the law)**: the exact AOSP `ViewGroup.getChildMeasureSpec` switch (EXACTLY/AT_MOST/UNSPECIFIED × dim≥0/MATCH(−1)/WRAP(−2); size = max(0, specSize − padding); in-place modes per F-096b), framework-exact guard | dalvik_engine.cpp, co-located with the MeasureSpec statics |

### Phase 4 — runtime verification (solitaire)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | `[F-NEW-326] static re-dispatch …Toolbar;.getChildMeasureSpec as Landroid/view/ViewGroup;` fires; real specs answered (`0x80000438`, `0x40000780`) | run/cont54/sol_post/r1.err |
| TESTED | **the CONT-52/53 spec-0 face is DEAD**: `[R347-MEASURE] view=298 NavigationView dex_onmeasure=YES wspec=0x80000390 (AT_MOST\\|912) hspec=0x40000780 (EXACTLY\\|1920) → 0x1920`; NavigationMenuView (view=322) exists, addView'd, attaches | run/cont54/sol_post/r1..r3 |
| TESTED (honest) | screenshot face `ba50a4d28ea62fe7` UNCHANGED ×3; 0 uncaught / 0 APP-BOUNDARY; **NEW frontier = the menu-content render pipeline** (NavigationMenuView's own DEX onMeasure dispatch — DEFAULT-MEASURE view=322 overrides_onMeasure=1 flag=0 — + the RecyclerView chain) | run/cont54/sol_post/r1..r3 |

### Phase 5 — zero-drift regression gate

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | **15 canonical anchors/controls ×3 byte-identical** under the canonical config (`--frames 5 --max-seconds 15`): dooz `31ddd4d5` / micro `da73010a` / unote `4f1a9e4e` / gmdice `f3b483fe7b7cf51b` / opencalc `a976d2f9` / tttdeluxe `af6094295ecb50e3` / flappycow `13cf4746` / g2048 `59ca1526` / tanana `5f7e0114c3bfd6b5` / csw `3442d9a9` / simplecalc `e847ca0346708f07` + BMI `b52252c2` / alex `c8d69f81` / notes `eb5ebd55` / sol `ba50a4d2` — **45/45 MATCH, ZERO DRIFT** | run/cont54/gate2_*, g3_* |
| TESTED | probe battery == records: fnew309 8/0, fnew320 7/0, fnew322 5/0, fnew323 6/0, fnew324 3/0, fnew325 4/0 (rebuilt after the reset; res-less fixture rebuild APK-SHA deltas recorded, judgment by ROWS) | run/cont54/probe_* |
| TESTED | reset-lost gate APKs refetched SHA-exact: tananaev vc11 `294a68bd` (vc10 is a different build — honestly noted), simplecalc `68da25fd`, composeStopwatch `dbf937eb` | upload/cont54_refetch/ |

**Bottom line**: the invoke-static resolution now agrees with ART across the framework boundary, and the framework spec law answers for the first time — the drawer child-spec chain is AOSP-faithful end to end. Dooz renders its real Scaffold on the full budget and BMI is REAL_APP_CONTENT (both re-measured fresh at HEAD, not assumed). **Registry 636→637** (F-NEW-326 appended ROOT-CAUSED-FIXED; F-NEW-309 next_wave refreshed — the menu-content render pipeline is the recorded next decode). Evidence: `evidence/cont54/CONT54_RESULT.md`. Commit `6f56c143`.
"""

r = subprocess.run(
    ["curl", "-sf", "-X", "POST",
     "-H", "Authorization: token " + subprocess.run(
         ["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
         capture_output=True, text=True).stdout.split("password=")[1].split()[0],
     "-H", "Accept: application/vnd.github+json",
     "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/375/comments",
     "-d", json.dumps({"body": BODY})],
    capture_output=True, text=True)
resp = json.loads(r.stdout)
print("comment id:", resp.get("id"), "| url:", resp.get("html_url"))
