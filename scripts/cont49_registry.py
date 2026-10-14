#!/usr/bin/env python3
"""cont49_registry.py — CONT-49 registry update (628 -> 631).

F-NEW-309: CLASSIFIED -> ROOT-CAUSED-FIXED (the generateLayoutParams law:
the parent's OWN LayoutParams subclass constructed by its real DEX
(Context, AttributeSet) ctor from the child's XML attrs).
F-NEW-318: appended ROOT-CAUSED-FIXED (Gravity.getAbsoluteGravity law).
F-NEW-319: appended ROOT-CAUSED-FIXED (Resources.getStringArray ARSC array
law). Solitaire's next divergence recorded in the F-NEW-309 row.
"""
import json

REG = "/home/z/my-project/root_registry.json"

with open(REG) as f:
    reg = json.load(f)
roots = reg["roots"] if isinstance(reg, dict) and "roots" in reg else reg

existing_ids = {r["id"] for r in roots}
assert "F-NEW-318" not in existing_ids and "F-NEW-319" not in existing_ids, \
    "ID collision — check upstream first"
assert len(roots) == 628, f"expected 628 roots, got {len(roots)}"

# ── F-NEW-309: CLASSIFIED -> ROOT-CAUSED-FIXED ──────────────────────────
for r in roots:
    if r["id"] == "F-NEW-309":
        r["status"] = "ROOT-CAUSED-FIXED"
        r["title"] = (
            "Solitaire (de.tobiasbielefeld.solitaire) DrawerLayout drawer-gravity "
            "check: DrawerLayout.g(View)/j(View) threw IAE \"View AppBarLayout@209 "
            "is not a drawer\" because every DrawerLayout child's LayoutParams was "
            "materialized as a plain ViewGroup$LayoutParams (ROOT-055 fallback) with "
            "gravity=0 — the XML android:layout_gravity of the drawer children never "
            "resolved into the LayoutParams (the NavigationView carries 0x00800003=START)."
        )
        r["root_cause"] = (
            "AOSP ViewGroup.generateLayoutParams law: at XML inflation the PARENT "
            "container generates each child's LayoutParams from the CHILD's attrs; "
            "for a DEX-defined parent that class is the parent's OWN LayoutParams "
            "subclass constructed by its real DEX (Context, AttributeSet) ctor "
            "(solitaire DrawerLayout$g: super MarginLayoutParams(Context,AttributeSet) "
            "bridge + Context.obtainStyledAttributes(attrs, DrawerLayout.a=[0x010100F3])"
            ".getInt(0,0) -> iput a:I). The runtime inflated DEX-parent children with "
            "NO LayoutParams at all; ROOT-055 answered a by-fiat plain "
            "ViewGroup$LayoutParams only when DEX code later asked. FIX (structural, "
            "rename-proof, no name/package conditions): new generate_child_layout_params "
            "in dalvik_engine.cpp — discover the parent's '$'-prefixed inner class whose "
            "super is ViewGroup$MarginLayoutParams and which declares the "
            "(Context,AttributeSet) ctor, allocate it, run the REAL DEX ctor with the "
            "child's XML attrs (F-NEW-197 AttributeSetStore precedence), write back the "
            "semantic width/height/margins, stash on the child node; ROOT-055 answers "
            "the stashed object. Wired as a Factory-law hook "
            "(set_generate_child_lp_hook) at the end of inflate_element with the same "
            "dual gate as the view-ctor hook (is_app_class_descriptor OR DEX-existence)."
        )
        r["next_wave"] = (
            "SOLITAIRE MOVED THREE DIVERGENCE LAYERS on binary 6c478a224ab1b3f4: "
            "(1) the F-NEW-309 IAE is GONE (DrawerLayout$g objects generated for all "
            "DrawerLayout children incl. NavigationView with gravity 0x00800003); "
            "(2) the follow-on DrawerLayout.onMeasure ISE \"does not have a valid "
            "layout_gravity\" is GONE (F-NEW-318); (3) the settings-singleton NPE family "
            "(c/m.a aget-null -> b.g null -> b.g.aR() NPE at GameSelector.onCreate "
            "pc=83/87) is GONE (F-NEW-319). CURRENT first divergence (next-wave root): "
            "[SYNTH-EXC] f141-null-recv NPE 'Landroid/support/v4/widget/ah;.a on null "
            "object reference' at DrawerLayout.computeScroll pc=35 (ah = the R8-renamed "
            "ViewDragHelper — mLeftDragger/mRightDragger construction chain), plus the "
            "menu-hub NPE 'Landroid/support/v7/view/menu/h;.i on null' at "
            "design/internal/c$b.f pc=31. Screenshot face ba50a4d28ea62fe7 UNCHANGED "
            "(x3) — the face moves only when the app's own content pipeline reaches "
            "drawing; the machine under it now runs DrawerLayout.onMeasure, "
            "NavigationView real-DEX onMeasure, ContentFrameLayout 1080x1920, and "
            "computeScroll."
        )
        r["evidence"] = "evidence/cont49/CONT49_RESULT.md"

# ── F-NEW-318 ───────────────────────────────────────────────────────────
roots.append({
    "id": "F-NEW-318",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P1",
    "layer": "framework/bridge-to-api/gravity",
    "title": (
        "android.view.Gravity.getAbsoluteGravity(I,I) had no bridge — the generic "
        "fallback answered a value whose HORIZONTAL_GRAVITY_MASK bits did not honor "
        "the START/END -> LEFT/RIGHT resolution, so DrawerLayout's findDrawerWithGravity "
        "scan matched a gravity-0 child and the onMeasure drawer-leg validation threw "
        "ISE \"Child NavigationView@289 at index 2 does not have a valid layout_gravity - "
        "must be Gravity.LEFT, Gravity.RIGHT or Gravity.NO_GRAVITY\" (DrawerLayout.onMeasure "
        "pc=356, uncaught) — the face past the F-NEW-309 fix."
    ),
    "root_cause": (
        "AOSP Gravity.java law: RELATIVE_LAYOUT_DIRECTION (0x00800000) marks the "
        "START/END family (START = LEFT|REL = 0x00800003, END = RIGHT|REL = 0x00800005); "
        "getAbsoluteGravity(gravity, layoutDirection) answers gravities WITHOUT the "
        "relative bit UNCHANGED (0->0, LEFT->3, RIGHT->5), resolves START->LEFT(3)/RTL:"
        "RIGHT(5) and END->RIGHT(5)/RTL:LEFT(3), consumes the relative bit and preserves "
        "all other bits. FIX: a real static bridge in bridge_to_api (next to the "
        "android.graphics.Color family, F-122 pattern) — pure bit math, no receiver, "
        "deterministic; no name/package conditions."
    ),
    "evidence": "evidence/cont49/CONT49_RESULT.md",
})

# ── F-NEW-319 ───────────────────────────────────────────────────────────
roots.append({
    "id": "F-NEW-319",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P1",
    "layer": "resources/arsc/string-array",
    "title": (
        "Resources.getStringArray(int) had no bridge — REC-MISS answered null and the "
        "app's aget on the null array NPE'd inside the settings-singleton construction "
        "(solitaire c/m.a pc=1200 'Attempt to read from null array'), null-killing the "
        "app-wide settings object b.g (downstream: b.g.aR() null-receiver NPE at "
        "GameSelector.onCreate pc=83/87)."
    ),
    "root_cause": (
        "AOSP ResourcesImpl.getStringArray resolves an ARRAY-type entry (res/array or "
        "res/string-array) — a COMPLEX entry whose ResTable_map items are keyed "
        "0x02000000|index. FIX: ArscParser::resolve_string_array (canonical resolver: "
        "type gate string-array/array, complex-item walk in key order, STRING items "
        "verbatim, REFERENCE items dereferenced through resolve_string, non-string "
        "items decimal-coerced — never a silent skip) + the bridge in bridge_to_api "
        "materializing the F-036 heap-array convention ([Ljava/lang/String; + "
        "__array_length__ + array[i] — the MatrixCursor.getColumnNames precedent). "
        "GATE-A honesty: unresolvable id throws Resources$NotFoundException (the AOSP "
        "contract), never a silent null. No package/name conditions."
    ),
    "evidence": "evidence/cont49/CONT49_RESULT.md",
})

reg["roots"] = roots
with open(REG, "w") as f:
    json.dump(reg, f, indent=2, ensure_ascii=False)
print(f"registry: 628 -> {len(roots)} roots (last {roots[-1]['id']})")
