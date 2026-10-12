#!/usr/bin/env python3
"""cont50_registry.py — CONT-50 registry update (630 -> 632).

F-NEW-320: ROOT-CAUSED-FIXED — per-frame instance dispatch (computeScroll /
onScrollChanged override family) executed the DEX body with the receiver
NEVER BOUND (args={} → this=<unset>): every iget silently answered null and
the first virtual invoke raised the per-frame f141-null-recv NPE at
DrawerLayout.computeScroll pc=35.
F-NEW-321: ROOT-CAUSED-FIXED — the S134 dual-write legacy mirror routed its
bare-name write through the F-NEW-251 runtime-class redirect, so a
SUPERCLASS field write's mirror landed in the SUBCLASS's shadowed qualified
slot (ay$a.a mObservable mirror clobbered c$b.a = the NavigationMenuPresenter
outer → the menu-hub NPE at design/internal/c$b.f pc=31). Fixed by a RAW
exact-key mirror write + the QUALIFIED-FIRST read law (one logical field,
one storage identity). Also updates the F-NEW-309 row's next_wave frontier
and records the recovered original solitaire bytes.
"""
import json

REG = "/home/z/my-project/root_registry.json"

with open(REG) as f:
    reg = json.load(f)
roots = reg["roots"] if isinstance(reg, dict) and "roots" in reg else reg

existing_ids = {r["id"] for r in roots}
assert "F-NEW-320" not in existing_ids and "F-NEW-321" not in existing_ids, \
    "ID collision — check upstream first"
assert len(roots) == 630, f"expected 630 roots, got {len(roots)}"

# ── F-NEW-309: refresh the next_wave frontier ───────────────────────────
for r in roots:
    if r["id"] == "F-NEW-309":
        r["next_wave"] = (
            "CONT-50 UPDATE (binary d19d5ba63c47a19f): BOTH recorded divergences "
            "ROOT-CAUSED and FIXED — the computeScroll per-frame NPE family "
            "(F-NEW-320: the dispatch passed args={} so the DEX body ran with "
            "this=<unset>) and the menu-hub NPE family (F-NEW-321: the S134 "
            "dual-write bare mirror redirect clobbered the subclass's shadowed "
            "c$b.a slot, so the NavigationMenuPresenter's menu read back null). "
            "Solitaire moved TWO more divergence layers: ah-NPE=0, menu-NPE=0; "
            "NEW first divergence recorded for the next wave: f141-null-recv NPE "
            "'Landroid/support/v7/widget/ay$w;.q on null object reference' at "
            "ay$h.a pc=8 x9 per run — ay.e(View) (AOSP getChildViewHolderInt: "
            "(RecyclerView.LayoutParams) child.getLayoutParams()).c = mViewHolder "
            "answers null (the RecyclerView.LayoutParams holder-attachment law, "
            "in the same family as the F-NEW-309 LP generation), upstream of "
            "NavigationView.onMeasure spec=0 FAILED(no write-back). Screenshot "
            "face ba50a4d28ea62fe7 UNCHANGED x3 (honest — the face moves when "
            "the app's own content pipeline draws). ORIGINAL store base.apk "
            "bytes RECOVERED (F-Droid repo vc71 = fdfaf7cad18e4416, the exact "
            "CONT-46 pin) and verified byte-identical x3 on the fix binary — "
            "the CONT-49 substitution note is superseded; pin restored to the "
            "original bytes."
        )
        r["evidence"] = "evidence/cont49/CONT49_RESULT.md; evidence/cont50/CONT50_RESULT.md"

# ── F-NEW-320 ───────────────────────────────────────────────────────────
roots.append({
    "id": "F-NEW-320",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P1",
    "title": (
        "Per-frame instance dispatch (R-NEW-430 computeScroll / R-NEW-428 "
        "onScrollChanged override family) invoked the DEX body with an EMPTY "
        "args vector — the receiver this was NEVER bound (frame ins=1 with "
        "args=0 → p0/v5 = UNSET): every iget on this silently answered null "
        "(no FIELD-TRACE row — the receiver is not a live heap object) and "
        "the first virtual invoke raised a per-frame f141-null-recv NPE. "
        "Solitaire face: 'Landroid/support/v4/widget/ah;.a on null object "
        "reference' at DrawerLayout.computeScroll pc=35 x6 per run (the "
        "mLeftDragger iget is a faithful consequence, NOT the root)."
    ),
    "root_cause": (
        "call_compute_scroll(view_object_id) built std::vector<DalvikValue> "
        "args; and passed it to try_recursive_invoke — violating the "
        "engine-wide receiver-first convention (onDraw passes {this, canvas}, "
        "onSizeChanged passes {this, w, h, 0, 0}, the onScrollChange listener "
        "arm passes {view, ...}). METHOD-TRACE proof: computeScroll's param "
        "window printed p0=<unset> from pc=0; the method still 'ran' "
        "(getChildCount on an unbound receiver answered 0 → the loop body "
        "never executed) so the corruption was silent until the first field "
        "read. FIX (minimal, generic, convention-faithful): bind the receiver "
        "as args[0] — args.push_back(make_object(view_object_id, "
        "node->class_desc)) — in BOTH the computeScroll dispatch and the "
        "onScrollChanged override arm (same ins-mismatch: (IIII)V with "
        "ins=5). No app/R8 conditions; every overriding view in the corpus "
        "gains a bound receiver."
    ),
    "next_wave": (
        "Probe fixtures/fnew320_probe (real aapt2/ECJ/D8): Flinger view "
        "overriding computeScroll reads its own ctor field inside the "
        "override — PRE face P4-CS-RECV FAIL x3 ('tag=null = unbound "
        "receiver'), POST PASS (11/0 x3 on the fix binary). Solitaire POST: "
        "the computeScroll NPE family GONE (0 rows vs 6)."
    ),
    "evidence": "evidence/cont50/CONT50_RESULT.md",
})

# ── F-NEW-321 ───────────────────────────────────────────────────────────
roots.append({
    "id": "F-NEW-321",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P1",
    "title": (
        "The S134 F-NEW-160 dual-write's bare legacy mirror was written "
        "through the F-NEW-251 bare-name REDIRECT, so every interpreter "
        "field write on a DEX object re-resolved the bare name against the "
        "receiver's most-derived declarer: a SUPERCLASS field write's "
        "mirror landed in the SUBCLASS's shadowed qualified slot. Solitaire "
        "face: c$b (NavigationMenuPresenter$Adapter) ctor stored the outer "
        "presenter (obj#304) into c$b.a; the super ay$a (RecyclerView$Adapter) "
        "ctor's later mObservable iput (obj#403) mirror-clobbered 'Lc$b;->a'; "
        "c$b.f pc=27 read the mObservable back as the 'outer', pc=29 read "
        "menu=null on it, pc=31 raised the menu-hub NPE x1 per run."
    ),
    "root_cause": (
        "ART law: a field occupies one slot per (declaring class, name, "
        "type); a superclass field cannot alias a subclass field of the same "
        "name (the F-NEW-160 registry row's own words). The dual-write "
        "mirror is a legacy compatibility channel, not a second identity "
        "resolution — routing it through the runtime-class resolver gave it "
        "identity authority it must not have. RUNTIME PROOF: S134-QGET "
        "key='Lc$b;->a' obj#402 hit=Y val=ay$b#403 (the qualified key was "
        "correct AND its slot corrupted); FIELD-TRACE put rows show the "
        "correct 304 write; the only interleaved writer is the super ctor's "
        "mirror. FIX (two coherent halves, one storage identity): (1) "
        "set_object_field_raw — the dual-write mirror is now a RAW exact-key "
        "write (no redirect) in BOTH dual-write sites (execute_iput + "
        "execute_iput_object); (2) QUALIFIED-FIRST read — for a resolvable "
        "bare name on a DEX-defined object the qualified slot is "
        "authoritative, the plain slot is the legacy channel (the old "
        "plain-first order made the Atomic*FieldUpdater family read the "
        "stale mirror: fnew252 21/35 face during the fix's first draft, "
        "restored to 56/0 by the qualified-first law). Framework-owned "
        "objects keep bare keys end to end."
    ),
    "next_wave": (
        "Probe fixtures/fnew320_probe (the exact shadowing shape): SubA "
        "extends SupA, both declare field 'a' of different types, super "
        "ctor writes Inner, sub ctor writes Outer — PRE: N2-SUB-UNTOUCHED "
        "FAIL x3 (outer() answered null after a super-slot write; the "
        "solitaire c$b face in miniature); POST: 11/0 x3 (P1 sub slot, P2 "
        "super slot, P3 per-instance, N1 round-trip, N2 sub untouched, "
        "P4-CS-RECV receiver binding). Solitaire POST: menu-hub NPE GONE "
        "(0 rows vs 1); the RecyclerView fill chain now RUNS (first "
        "child=406 addView)."
    ),
    "evidence": "evidence/cont50/CONT50_RESULT.md",
})

reg["roots"] = roots
with open(REG, "w") as f:
    json.dump(reg, f, indent=1)

ids = [r["id"] for r in roots]
assert len(ids) == len(set(ids)), "duplicate IDs after update"
print(f"registry updated: {len(roots) - 2} -> {len(roots)} roots; unique-ID check OK")
