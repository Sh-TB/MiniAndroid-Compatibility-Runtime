#!/usr/bin/env python3
"""cont11_w8_registry.py — append the W8 roots to root_registry.json
(discipline: ids unique, main==mirror, 823 → 825)."""
import json

R = "/home/z/my-project/root_registry.json"
reg = json.load(open(R))

assert isinstance(reg, list) and len(reg) == 823, f"unexpected registry size {len(reg)}"
ids = {r["id"] for r in reg}
assert "F-NEW-510" not in ids and "F-NEW-511" not in ids, "id collision"

reg.append({
    "id": "F-NEW-510",
    "title": "F-NEW-510 (CONT-11 W8: Bundle.keySet/ContentValues keySet wrapper iteration — androidx.startup discovery zero-initializer root)",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "layer": None,
    "evidence": (
        "ROOT CAUSE: the engine-side keySet materialization (EXP-093 Bundle law, "
        "CONT-21 F-NEW-273; ContentValues keySet law — same shape) answers with an "
        "'Ljava/util/ArrayList;' WRAPPER whose backing array hangs off the 'array' "
        "heap field; the wrapper itself carries NO __array_length__. Set/Collection-"
        "declared iteration over that shape fell through the F-036 engine iterator "
        "gate (class pattern lacks Set;/Collection; AND the receiver lacks "
        "__array_length__) into CollectionShadow, whose hasNext/next read the "
        "parent's parallel CollectionState — EMPTY for engine-minted objects → "
        "hasNext=false over a NON-empty set. Shared-primitive evidence (W8 "
        "survivalmanual, binary 55c5e06b): androidx.startup AppInitializer."
        "discoverAndInitialize iterated metadata.keySet() (F273-PROVINFO metaData "
        "entries=4) and saw hasNext=false → ZERO initializers discovered → Kotpref "
        "'has not been initialized' ISE ×34 uncaught (theInitializationProvider "
        "flow runs in EVERY androidx-startup app). FIX (CollectionShadow "
        "hasNext/next, one-hop wrapper resolution, f510_resolve_wrapper): when the "
        "iterator parent lacks __array_length__ but carries a REF 'array' field "
        "whose target HAS __array_length__, resolve the hop so the array-backed "
        "fallback (F-NEW-237 family) serves the real length/elements. Scope law: "
        "fires ONLY on the keySet-wrapper shape — every other parent untouched "
        "(no dispatch-order change; the F-036 gate stays byte-identical). "
        "VERIFY: trace shows the full discovery loop (4/4 keys iterated, "
        "metadata.get per key, Class.forName + isAssignableFrom per key); anchor "
        "wall 6/6 ×3 zero drift; negatives 19/19; selftest 14/14; gate A multiapp "
        "ALL PASS; reinstall 8/8. Binary 060fdbefd3e9f9d2."
    ),
    "date": "2026-10-23",
    "wave": "CONT-11 W8",
}),
reg.append({
    "id": "F-NEW-511",
    "title": "F-NEW-511 (CONT-11 W8: Class-token identity — forName ref_id=instruction-counter heap-oid aliasing; 511a landed, 511b container arm deferred)",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "layer": None,
    "evidence": (
        "ROOT CAUSE (511a — LANDED): Class.forName (R350 law) returned "
        "DalvikValue::make_class(want_desc, instruction_sequence_) — ref_id = the "
        "monotonic INSTRUCTION COUNTER, not a heap id. dalvik_value_to_arg's "
        "CLASS_REF case carries a.object_id = v.ref_id, so the shadow/arg boundary "
        "aliased an ARBITRARY live heap object with a colliding id. Live face (W8 "
        "survivalmanual): forName tokens aliased heap ids 24/45/66/87 (PackageManager "
        "owned 24) → the androidx.startup initializerClasses HashSet stored "
        "'Class<KotprefInitializer>' backed by the PackageManager object → "
        "doInitialize received Class<PackageManager> → getDeclaredConstructor "
        "dispatched on PackageManager (bridge api_cls=Landroid/content/pm/PackageManager;) "
        "→ null → Constructor.newInstance NPE → StartupException. THE SAME DEFECT "
        "F-NEW-249 (CONT-6) fixed for Object.getClass — forName never got the "
        "update. FIX: return_val = make_stable_class_token(want_desc) (F-069/F-249 "
        "per-descriptor heap token, __referent_desc). VERIFY: chess anchor preserved "
        "(a0319686 ×3 — bisected: the wrapper-hop-only binary and the 511a-only "
        "binary BOTH keep the recorded face), anchors 6/6 ×3, negatives 19/19, "
        "selftest 14/14 at 060fdbefd3e9f9d2. "
        "DEFERRED ARM (511b — container materialization, patch preserved at "
        "evidence/cont11/w8/fnew511_patch.diff + fnew511_dalvik_engine_candidate.cpp): "
        "the Collections.singletonList materializer stores the RAW CLASS_REF "
        "(object_id=0) and every heap-field ref reader requires OBJECT_REF+oid!=0 → "
        "initializer dependencies() lists read back EMPTY → 'iterator exhausted "
        "(pos=0)' NoSuchElementException → StartupException. With 511b applied the "
        "whole startup chain completes (Kotpref ISE GONE, survivalmanual 34→26 "
        "uncaught, app advances to Material FAB layout inflation) BUT chess "
        "regresses (a0319686 → b270ff04, Toolbar.setSubtitle → x0/f.t NPE chain, "
        "face PARTIAL 160-colors → blank) — the correct-token semantics expose the "
        "next engine gap. W9 OWNS: land 511b TOGETHER with the Toolbar/x0-family "
        "decode (Ll/a1;→Ll/w;→Lx0/g;→Lx0/f; instance-of/check-cast/iget on the "
        "wrapped TransformationMethod holder) + the Resources$NotFoundException "
        "getColorStateList family (survivalmanual FAB + alexcalc Toolbar — same "
        "signature)."
    ),
    "date": "2026-10-23",
    "wave": "CONT-11 W8",
})

ids = [r["id"] for r in reg]
assert len(ids) == len(set(ids)), "duplicate ids after append"
assert len(reg) == 825
json.dump(reg, open(R, "w"), indent=1, ensure_ascii=False)
print("registry 823 ->", len(reg), "ids unique OK")
