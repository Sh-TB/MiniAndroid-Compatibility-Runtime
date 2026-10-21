#!/usr/bin/env python3
"""CONT-130: F-NEW-471 CLASSIFIED -> ROOT-CAUSED-FIXED in both registry files (id-keyed sync)."""
import json

NEW_EV = (
    "CONT-130 ROOT-CAUSED-FIXED (superclass-chain super resolution, byte-truth reclassification): "
    "scripts/cont130_dex_truth.py re-decoded tictactoe v3 classes.dex class_def[1563] (class_data_off "
    "0x3185fe) with an independent uleb128 walk: header 0/19/3/49 (engine count matches); DM diffs "
    "1135/1/38 = <clinit>/<init>/init; 49 VM diffs are list-local and resolve 1137..1196 with 1184 "
    "SKIPPED by the encoded stream itself — the dex does NOT declare AndroidApplication.onCreate while "
    "method_ids[1184] references it (method_ids is a REFERENCE pool, not a declaration table). The "
    "CONT-127 'blob-walk desync / GLES30.glUniformBlockBinding' hypothesis is RETRACTED: that symptom "
    "came from a 12-byte stride misread in the diagnostic tool; the engine's class_data walk is "
    "byte-exact (verbose dex dump run/c130/dex_verbose.log CLASS_DEF[1563]: names "
    "addAndroidEventListener..useImmersiveMode, code_offs byte-identical to ground truth). The real "
    "gap: the engine's invoke-super path only tried the EXACT declaring class — no app-parsed "
    "superclass walk. FIX (slice 2): try_recursive_invoke_on_super (the F-074/S21 law, receiver "
    "identity preserved, 16-hop cap) now runs after the exact-class miss and BEFORE the shadow "
    "bridge; the slice-1 loud law is reclassified to document framework-boundary shadow dispatch "
    "(ART JVMS 5.4.3.3-equivalent) instead of claiming a parse gap. VERIFIED live: tictactoe face "
    "b5a7a35d byte-identical, exc 6->6, RES-GAP now correctly describes the reference-only slot; "
    "wall at binary 9e755c3dde69510c: 9/9 anchors byte-identical, selftest rc=0, negatives 19/19 "
    "(probe store regenerated per CONT-111 remedy), registry 786 id-unique main==mirror."
)

for f in ("root_registry.json", "canonical/root_cause_registry.json"):
    r = json.load(open(f))
    hit = False
    for x in r:
        if x.get("id") == "F-NEW-471":
            x["status"] = "ROOT-CAUSED-FIXED"
            x["evidence"] = NEW_EV
            hit = True
    assert hit, f"F-NEW-471 not found in {f}"
    json.dump(r, open(f, "w"), indent=2, ensure_ascii=False)
    print(f, "updated")

# consistency
a = json.load(open("root_registry.json"))
b = json.load(open("canonical/root_cause_registry.json"))
ids_a = [x["id"] for x in a]; ids_b = [x["id"] for x in b]
assert len(set(ids_a)) == len(ids_a) == 786 and ids_a == ids_b
e471 = [x for x in a if x["id"] == "F-NEW-471"][0]
print("sync OK; F-NEW-471:", e471["status"])
