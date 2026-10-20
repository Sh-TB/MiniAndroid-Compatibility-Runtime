#!/usr/bin/env python3
"""CONT-124 registry update: F-NEW-469 (superinterface closure law) +
F-NEW-267 evidence refresh. No inflation: 783 -> 784 (one new root), both
files (main + canonical mirror) updated by ID."""
import json

MAIN = 'root_registry.json'
MIRROR = 'canonical/root_cause_registry.json'

F469 = {
    "id": "F-NEW-469",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P1",
    "layer": "runtime/type-system",
    "title": "SUPERINTERFACE CLOSURE LAW: dalvik_class_assignable checked only "
             "DIRECTLY declared interfaces per walk node — a class implementing "
             "I3 where I3 extends I2 extends I1 answered FALSE against [LI1;, "
             "so the aput-object store-check (R-NEW-010) threw a BOGUS "
             "ArrayStoreException on a JVMS-legal store.",
    "law": "JVMS 5.1 / ART Class::IsAssignableFrom — subinterface chains of "
           "any depth count; the assignable walk must BFS the superinterface "
           "graph (class_to_interfaces_ + F-NEW-236 framework tables) from "
           "the start class's own list AND every superclass hop's list, "
           "visited-set bounded (64).",
    "evidence": json.dumps({
        "wave": "CONT-124",
        "live_face_at_04a89c52": [
            "ASC-REJECT x9: arr=[Lxt0; src=Lf6; caller=Liw0;.b (dooz v23)",
            "DEX ground truth (scripts/c124_dex_classdef.py): Lxt0;=INTERFACE, "
            "Lvt0;=INTERFACE extends Lxt0;, Lbu0;=INTERFACE extends Lvt0;, "
            "Lf6;=class implements Lbu0; -> Lf6; IS-A Lxt0; (store legal)",
            "crash.log: AIOOBE caught by Lr;.g catch-all, recovery re-throw "
            "at pc=57 uncovered, APP-BOUNDARY unwind through Lel0;.c/.d "
            "(LayoutNode placement) at MainActivity.onCreate invoke_pc=306",
            "effect: zero Ld61;.i (Placeable.position) writes at HEAD; dooz "
            "face d602648e = 100% themed background, placement dead"],
        "post_fix": [
            "binary 6bb7150a91bacda1: ASC-REJECT 9->0, ArrayStoreException "
            "27->0 in the same run window",
            "180s dooz: Ld61;.i0 (updateSizeAndPosition) writes REAL packed "
            "positions (2319282340800) for the first time in the current "
            "lineage — the placement pass survives onCreate",
            "9/9 anchors byte-identical zero drift; selftest rc=0; negatives "
            "19/19 (probe store regenerated per CONT-111 remedy)"],
        "residuals": [
            "place-then-reset: a later pass rewrites Ld61;.i to 0 (the "
            "CONT-64-era double-measure poison re-visible now that placement "
            "runs) — hit-test reads still answer 0",
            "compose draw path: face still 100% bg at 180s — the draw-op "
            "frontier (F-NEW-256 family) stays"],
        "probe": "three-level interface chain fixture owed (I3 extends I2 "
                 "extends I1; class X implements I3; store X into I1[])",
    }),
    "probe": "fixtures/cont124_iface_chain (spec): iface A; iface B extends A; "
             "iface C extends B; class X implements C; Object[] t = new C[2]; "
             "t[0] = X-instance must pass; unrelated Y into C[] must still "
             "throw ArrayStoreException",
}

F267_EVIDENCE_ADD = (
    " CONT-124: the F-NEW-469 store-check fix (binary 6bb7150a) removed the "
    "bogus AIOOBE that killed the placement pass — Ld61;.i0 now writes real "
    "packed positions (first writes in the current lineage, run "
    "run/c124/dooz180_fixed.log). The place-then-reset poison re-surfaces as "
    "the named next lever: a later pass rewrites .i to 0 before the hit-test "
    "reads; then the draw-op frontier stays."
)


def load(path):
    with open(path) as f:
        data = json.load(f)
    return data['roots'] if isinstance(data, dict) and 'roots' in data else data


def save(path, roots):
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict) and 'roots' in data:
        data['roots'] = roots
    else:
        data = roots
    with open(path, 'w') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)


def main():
    main_roots = load(MAIN)
    mirror_roots = load(MIRROR)

    ids = {r['id'] for r in main_roots}
    assert 'F-NEW-469' not in ids, 'F-NEW-469 already exists — no inflation'

    main_roots.append(F469)
    mirror_roots.append(dict(F469))

    # F-NEW-267 evidence refresh
    for r in main_roots:
        if r['id'] == 'F-NEW-267':
            r['evidence'] = r.get('evidence', '') + F267_EVIDENCE_ADD
    for r in mirror_roots:
        if r['id'] == 'F-NEW-267':
            r['evidence'] = r.get('evidence', '') + F267_EVIDENCE_ADD

    save(MAIN, main_roots)
    save(MIRROR, mirror_roots)

    # verification
    m = load(MAIN)
    c = load(MIRROR)
    mids = [r['id'] for r in m]
    cids = [r['id'] for r in c]
    print(f"main={len(mids)} unique={len(set(mids))} "
          f"ID_UNIQUE={len(mids) == len(set(mids))}")
    print(f"mirror={len(cids)} MAIN_EQ_MIRROR={set(mids) == set(cids)}")
    row469m = next(r for r in m if r['id'] == 'F-NEW-469')
    row469c = next(r for r in c if r['id'] == 'F-NEW-469')
    print("F-NEW-469 status:", row469m['status'],
          "ROW-EQUAL:", row469m == row469c)


if __name__ == '__main__':
    main()
