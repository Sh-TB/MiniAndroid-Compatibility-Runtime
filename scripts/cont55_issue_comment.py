#!/usr/bin/env python3
"""cont55_issue_comment.py — post the CONT-55 line-by-line audit to Issue #375."""
import json, subprocess

BODY = """## CONT-55 execution-stage audit — the AOSP AttributeResolution DEF-STYLE stages (F-NEW-327)

Continued from remote HEAD `090d4a8a` (the CONT-54 closeout), per the "continue from the latest remote HEAD" directive. Every row is **STATUS — RESULT — EVIDENCE**. Work binary: fix binary `6014ae17…`. No APK-specific hacks, no R8-name special-casing, no fake objects.

### Phase 0 — the CONT-54 frontier re-decoded

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | the CONT-54 "menu-content" frontier re-read precisely: NavigationView measured **0 WIDE × 1920** (the row `-> 0x1920` = w0/h1920) and `NavigationMenuView.setMeasuredDimension(0, 1920)` — through the RUNNING DEX chain (ay.e → setMeasuredDimension, ARG-TRACE) | run/cont55/sol_argtrace.err |

### Phase 1 — the decode: the width died in the STYLE stage

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED (byte-level) | NavigationView.onMeasure sparse-switch payload parsed (keys FIRST then targets): **AT_MOST → `makeMeasureSpec(min(specSize, mMaxWidth), EXACTLY)`**; UNSPECIFIED → `makeMeasureSpec(mMaxWidth, EXACTLY)`; EXACTLY → straight to `invoke-super` | scripts/cont55_sparse_switch.py |
| TESTED (byte-level) | `mMaxWidth = bn.e(NavigationView_android_maxWidth, sget a$h.Widget_Design_NavigationView)` via the 4-arg `Context.obtainStyledAttributes(set, styleable, defStyleAttr, defStyleRes)` (proto `(AttributeSet;[III)I`, cnt=5) | bn.a disasm |
| TESTED (runtime) | `[SGET] …Widget_Design_NavigationView value=0x7f100180` — the defStyleRes value WAS on the register; the CS-PRODUCER probe pinned the 10-attr call `attrs=[0x10100d4,0x10100dd,0x101011f(maxWidth),…]` with **dSA=0x0 dSR=0x0**; the arg-kind probe found `a3:k0=0x7f100180` + `a2:k7=NULL_REF` — the bridge maps a literal-0 int to NULL_REF and the `Kind::INT` gate dropped BOTH args | run/cont55/sol_attr2..4.err |
| TESTED (engine) | TWO stacked gaps: (a) BOTH TypedArray producers (ContextShadow F-093 **and** the S101 Resources$Theme producer — the appcompat ContextThemeWrapper chain routes the NavigationView ctor's call THERE) walked only XML(1)+theme(5) — the AOSP ApplyStyle style stages never ran; (b) the NULL_REF arg-conversion face | dalvik_engine.cpp; android_shadows.cpp |

### Phase 2 — the fix (minimal, generic, ART-faithful)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| FIXED | **F-NEW-327a**: `resolve_def_style_attr_value` — the AOSP order XML(1) → xmlStyle(2) → defStyleAttr(3) → defStyleRes(4) → theme(5, kept verbatim); each style stage = `bag_value` (the ResTable_map_entry parent chain) + REFERENCE deref (package-routed) + DIMENSION → device px (the AOSP TypedArray getDimensionPixelSize contract) | resource_runtime.{h,cpp} |
| FIXED | **F-NEW-327b**: wired into BOTH producers; the S101 producer also gained the stage-1 raw-XML read | android_shadows.cpp; dalvik_engine.cpp |
| FIXED | **F-NEW-327c**: positional INT-or-NULL_REF arg extraction (a literal-0 int arrives as NULL_REF) | both producers |

### Phase 3 — probe A/B (real toolchain, WITH res)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | `fnew327_probe.apk 57ec5cdf…` — boxMax/boxMin attrs + F327_BoxStyle (280dp/48dp) + a theme WITHOUT them (the style stage is the only source); the exact NavigationView ctor shape (dSA=0, dSR=the style, def=-1) | run/cont55/fnew327_probe.apk |
| TESTED | **PRE ×3 on `ff261b1b…`: got=-1 FAIL ×2** (the def channel survived, the style value lost) | run/cont55/pre_f327p/r1..r3 |
| TESTED | **POST ×3 on `6014ae17…`: 3/0 ×3** — `got=735` (280dp px-decoded), `got=126` (48dp) | run/cont55/post_f327p/r1..r3 |

### Phase 4 — runtime verification (solitaire)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | **`[R347-MEASURE] view=298 NavigationView wspec=0x80000390 hspec=0x40000780 → 735×1920`** (was 0×0) — 735 = 280dp × 2.625: the style's maxWidth clamping the AT_MOST drawer spec through the AOSP min() law | run/cont55/sol_f327c.err |
| TESTED | **`NavigationMenuView.setMeasuredDimension(735, 1920)`** (was 0, 1920) — the FULL drawer measure chain is AOSP-faithful end to end | run/cont55/sol_menu.err |
| TESTED (honest) | screenshot face `ba50a4d28ea62fe7` UNCHANGED — the closed drawer's pixels sit off-screen; **the open-drawer menu-content draw pipeline is the recorded next decode** | run/cont55/sol_f327c |

### Phase 5 — zero-drift regression gate

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | **15 canonical anchors/controls ×3 = 45/45 MATCH**: dooz `31ddd4d5` / micro `da73010a` / unote `4f1a9e4e` / gmdice `f3b483fe7b7cf51b` / opencalc `a976d2f9` / tttdeluxe `af6094295ecb50e3` / flappycow `13cf4746` / g2048 `59ca1526` / tanana `5f7e0114c3bfd6b5` / csw `3442d9a9` / simplecalc `e847ca0346708f07` + BMI `b52252c2` / alex `c8d69f81` / notes `eb5ebd55` / sol `ba50a4d2` | run/cont55/smoke_*, g3_* |
| TESTED | probe battery == records on the NEW binary: fnew309 8/0, fnew320 7/0, fnew322 5/0, fnew323 6/0, fnew324 3/0, fnew325 4/0, fnew326 13/0 | run/cont55/probe_* |

**Bottom line**: the TypedArray resolution now walks the FULL AOSP AttributeResolution order on both producers, DIMENSION slots answer device px, and the solitaire drawer gained its real geometry (735×1920) from the same style law real Android uses (Widget.Design.NavigationView's android:maxWidth). **Registry 637→638** (F-NEW-327 appended ROOT-CAUSED-FIXED). Evidence: `evidence/cont55/CONT55_RESULT.md`. Commit `678ff67b`.
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
