#!/usr/bin/env python3
"""cont51_registry.py — CONT-51 registry update (632 -> 634).

F-NEW-322: ROOT-CAUSED-FIXED — the View.mLayoutParams IDENTITY law: the
setLayoutParams bridge recorded only semantic w/h, so every later
getLayoutParams fell through to the ROOT-055 by-fiat materialization and
handed DEX code a DIFFERENT object — the RecyclerView.LayoutParams
mViewHolder attach (solitaire ay$i.c = holder, written by ay$o.a
tryGetViewHolderForPositionByDeadline on obj#1802) read back NULL through
the fresh fallback obj#1805 (ay.e getChildViewHolderInt) → NPE at
ay$h.a pc=8 (measureChildWithMargins' holder.q()) ×5/run → uncaught at
GameSelector.onCreate invoke_pc=120 (APP BOUNDARY unwind).
F-NEW-323: ROOT-CAUSED-FIXED — the AOSP ViewGroup detach/attach family
(detachViewFromParent / attachViewToParent / removeDetachedView) had NO
bridge at all: every call was a silent no-op, so after the FIRST detach
the children table stayed full-length and the NEXT detachAndScrap cycle
re-caught the same FLAG_TMP_DETACHED child, tripping the DEX-side defense
(IAE "called detach on an already detached child" in ay$5.c = the
ChildHelper.Callback) — the post-F-NEW-322 first divergence.
Also refreshes the F-NEW-309 next_wave frontier (GameSelector now reaches
onResume; NavigationMenuView.onMeasure writes back with real specs; the
new frontier is the APP_PIXELS stage — the menu content render) and
records the solitaire screenshot face ba50a4d28ea62fe7 UNCHANGED (honest).
"""
import json

REG = "/home/z/my-project/root_registry.json"

with open(REG) as f:
    reg = json.load(f)
roots = reg["roots"] if isinstance(reg, dict) and "roots" in reg else reg

existing_ids = {r["id"] for r in roots}
assert "F-NEW-322" not in existing_ids and "F-NEW-323" not in existing_ids, \
    "ID collision — check upstream first"
assert len(roots) == 632, f"expected 632 roots, got {len(roots)}"

for r in roots:
    if r["id"] == "F-NEW-309":
        r["next_wave"] = (
            "CONT-51 UPDATE (binary f11d542108cd611b, HEAD 533ecf61): the recorded "
            "ay$w.q NPE and the NavigationView.onMeasure spec=0 face are both "
            "ROOT-CAUSED and FIXED on one causal chain — F-NEW-322 (the "
            "View.mLayoutParams identity law: setLayoutParams never recorded the "
            "object identity so getLayoutParams re-materialized a fresh fallback "
            "obj and the mViewHolder attach read back null) and F-NEW-323 (the "
            "ViewGroup detach/attach family was a silent no-op so the second "
            "detachAndScrap re-caught a FLAG_TMP_DETACHED child and the DEX-side "
            "defense threw IAE 'called detach on an already detached child'). "
            "POST: ay$w.q NPE 0 (was 5/run), detach-IAE 0, 0 uncaught x3, "
            "GameSelector.onCreate SURVIVES (was: APP BOUNDARY unwind at "
            "invoke_pc=120) and GameSelector.onResume dispatches via DEX "
            "(ok=1, 22361 insns x3); NavigationMenuView.onMeasure now measures "
            "with REAL specs (0x40000000/0x40000780) and writes back 0x1920 "
            "(was: spec=0 FAILED no write-back). Screenshot face ba50a4d28ea62fe7 "
            "UNCHANGED x3 (honest — DEFAULT_BACKGROUND_ONLY, first_missing_stage "
            "=APP_PIXELS): the NEW frontier is the menu-content render pipeline "
            "(NavigationMenuView second measure pass runs spec=0; the menu items "
            "never draw app-owned pixels)."
        )
        r["evidence"] = ("evidence/cont49/CONT49_RESULT.md; evidence/cont50/CONT50_RESULT.md; "
                         "evidence/cont51/CONT51_RESULT.md")

roots.append({
    "id": "F-NEW-322",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P1",
    "title": "The AOSP View.mLayoutParams IDENTITY law was split at the bridge: setLayoutParams recorded only semantic w/h on the ViewShadow node, so every later getLayoutParams fell through to the ROOT-055 by-fiat materialization and handed DEX code a DIFFERENT object. Solitaire face: ay$o.a (RecyclerView Recycler.tryGetViewHolderForPositionByDeadline, real DEX) wrote ay$i.c = mViewHolder on obj#1802 after setLayoutParams; the measure pass then read ay$i.c on obj#1805 (a FRESH ROOT-055 fallback) → null → NPE 'ay$w.q on null object reference' at ay$h.a pc=8 (LayoutManager.measureChildWithMargins' holder.q()) x5/run → uncaught at GameSelector.onCreate invoke_pc=120 (APP BOUNDARY unwind, ART process-death law).",
    "root_cause": "FIELD-TRACE runtime proof: 5 put/get pairs — put ay$i.c obj#1802 value=obj#1794 (caller ay$o.a), get ay$i.c obj#1805 (caller ay.e) — the write and read landed on DIFFERENT heap objects. Engine: android_shadows.cpp getLayoutParams bridge answers lp_node->layout_params_object when set (F-NEW-309 precedence) else allocates a fresh parent-type LP EVERY call (silent — the ROOT-055 log only prints for CoordinatorLayout receivers); the setLayoutParams bridge recorded width/height but never the object identity. FIX (minimal, generic, AOSP-faithful): the setLayoutParams bridge records the EXACT object identity + heap class into the SAME node slot the getLayoutParams bridge already answers first (n->layout_params_object / layout_params_class) — AOSP View.java stores ONE mLayoutParams reference; set writes it, get reads the same object; a later set replaces the slot (overwrite semantics). Views never given params keep the ROOT-055 fallback (blidraughts case untouched); XML-inflated F-NEW-309 objects keep their precedence.",
    "next_wave": "Probe fixtures/fnew322_probe (real aapt2/ECJ/D8, APK 56de7a4ef25cf4f9): DEX-defined LpTag extends MarginLayoutParams carrying a String field written BEFORE setLayoutParams; PRE faces x3 deterministic (P1-LP-IDENTITY FAIL back=LayoutParams/<no-tag>/100x200, P2-LP-OVERWRITE FAIL) — the exact solitaire obj#1805 face; POST 5/0 x3 on the fix binary (P1/P2 identity+overwrite PASS, N1/N2/N3 ROOT-055 fallback faces PASS). Solitaire POST: ay$w.q NPE 0 (was 5/run).",
    "evidence": "evidence/cont51/CONT51_RESULT.md",
})

roots.append({
    "id": "F-NEW-323",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P1",
    "title": "The AOSP ViewGroup detach/attach family (detachViewFromParent(int|View), attachViewToParent(View,int,LayoutParams), removeDetachedView(View,boolean)) had NO engine bridge — every call from real DEX was a silent no-op. Solitaire face (post-F-NEW-322 first divergence): the FIRST ChildHelper detach succeeded (holder flags 1→257 = FLAG_BOUND|FLAG_TMP_DETACHED, FIELD-TRACE put row), the children table stayed full-length, the NEXT detachAndScrap cycle re-caught the same child and the DEX-side defense threw IAE 'called detach on an already detached child c$a;@1787' at ay$5.c pc=45 (ChildHelper.Callback.detachViewFromParent) → uncaught at GameSelector.onCreate.",
    "root_cause": "AOSP ViewGroup.java: detachViewFromParent removes the child from mChildren (childCount decrements, array compacts) but KEEPS child.mParent — detachment is a transient state inside ONE layout traversal; attachViewToParent re-inserts at the given index (index<0 → append) and REPLACES child.mLayoutParams; removeDetachedView is the full removal (mParent cleared). The runtime shadow layer implemented only removeView/removeAllViews; grep 'detachView' in the engine = zero hits. RUNTIME proof chain: FIELD-TRACE ay$w.n obj#1787 1→257 (b(256) FLAG_TMP_DETACHED written by the FIRST detach), the second detach's r() (isTmpDetached) read 257 → throw; THROWABLE-STACK #0 ay$5.c #1 ah.e(I) (ChildHelper.detachViewFromParent) #2 ay$h.a(I,View) (LayoutManager.detachViewAt) #6 LinearLayoutManager.c #7 ay.N #8 ay.onMeasure. FIX (minimal, generic, AOSP-faithful): three bridges in android_shadows.cpp — detachViewFromParent compacts n->children (idx from int arg or indexOf(object arg)) WITHOUT clearing child parent_id; attachViewToParent re-inserts (clamped index, no double-add, parent_id kept) and records the params object into the child's layout_params_object slot (F-NEW-322 cooperation); removeDetachedView delegates to remove_child (full removal + R-NEW-302 requestLayout). No app/R8 conditions.",
    "next_wave": "Probe fixtures/fnew323_probe (real aapt2/ECJ/D8, APK 634ebf19d04ab00d): DEX Detacher extends LinearLayout exposing detachIdx/attachIdx/removeDet; PRE faces x3 deterministic (P1-DETACH-COUNT FAIL count=2 after detach(0) — the exact children-table-stays-full face; P2 slot0==c1 FAIL; P5-ATTACH-LP-IDENTITY FAIL; N1-REMOVEDETACHED FAIL) — POST 6/0 x3 on the fix binary. Solitaire POST: detach-IAE 0, 0 uncaught x3, GameSelector.onResume dispatches via DEX (ok=1, 22361 insns); NavigationMenuView.onMeasure measures with real specs and writes back 0x1920.",
    "evidence": "evidence/cont51/CONT51_RESULT.md",
})

with open(REG, "w") as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)

ids = {r["id"] for r in roots}
print(f"registry 632 -> {len(roots)} (F-NEW-322, F-NEW-323 appended ROOT-CAUSED-FIXED; F-NEW-309 next_wave refreshed)")
print("unique-ID check:", "OK" if len(ids) == len(roots) else "COLLISION")
