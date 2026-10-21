#!/usr/bin/env python3
"""cont151_train6_registry.py — TRAIN 6 (CONT-151) registry update.
Adds F-NEW-479 (draw-block chain severed at bind: Lel0;.c padChain writes
NULL into the linked chain) + appends to F-NEW-478. Syncs main + mirror."""
import json

F479_EVIDENCE = (
    "CONT-151 TRAIN 6 (binary f6b272ea, dooz v23): the empty-chain terminal "
    "is now pinned to a CONCRETE severed link. FIELD-TRACE Lwt0;.i timeline "
    "(473 events): (1) Lkz0;.a BUILDS the shared-scope chain — put obj#2708."
    "i = obj#2060 (line 1754, a real link) plus head links 2357.i = "
    "2708/1508/1521; (2) Lel0;.c (padChain — 532 insns; its own const-string "
    "'padChain called on already padded chain' proves the identity) then "
    "READS obj#2708.i and WRITES value=0 — the link is SEVERED (line 1763); "
    "(3) NO later put re-links 2708.i — every subsequent T0 walk (12 draw "
    "windows) reads NULL -> content draw-block unreachable -> blank face. "
    "Lel0;.c runs 18x, ALWAYS from Lel0;.d (node->view binding cascade: "
    "Lt4;.<init> root + applier Lv02;.c), a0=node, a1=Lol;/Lut0; pad source. "
    "Lkz0;.a puts 94x = the builder; Lel0;.c puts 36x = the restructurer. "
    "Tooling law fixed en route: Lpz0;.S0 resolves through the SUPERCLASS "
    "Lfr0; (method_ids[11177] says Lpz0;.S0 but the declaring entry lives "
    "in the Lfr0; hierarchy — CL/RET filters must match the declaring "
    "class). NEXT LEVER (single question): inside padChain's 532 insns, "
    "does the re-pad re-link execute and where does it write — METHOD-TRACE "
    "the .c call that owns the 2708 wipe; candidate surfaces: the pad "
    "insert's new-link writes landing on a different Lwt0; (obj#2060's "
    "own .i/.j) vs the head, or the re-pad pass never running after the "
    "sever (upstream runs it on the SAME bind; engine may order the "
    "Lkz0;.a build AFTER the pad, eating the re-link)."
)

F478_APPEND = (
    " || CONT-151 TRAIN 6: the empty chain is a SEVERED chain — Lkz0;.a "
    "built obj#2708.i = obj#2060, then Lel0;.c (padChain, called from the "
    "Lel0;.d binding cascade) wrote it back to NULL with no re-link — "
    "promoted to F-NEW-479."
)

for path in ("root_registry.json", "canonical/root_cause_registry.json"):
    r = json.load(open(path))
    ids = {e.get("id") for e in r}
    assert "F-NEW-479" not in ids, f"F-NEW-479 already in {path}"
    r.append({
        "id": "F-NEW-479",
        "title": ("F-NEW-479 — dooz draw-block chain severed at bind: "
                  "Lel0;.c padChain writes NULL into the linked obj#2708.i "
                  "with no re-link -> T0 walks an empty chain 12/12"),
        "status": "CLASSIFIED",
        "priority": "P0",
        "layer": "compose-draw",
        "evidence": F479_EVIDENCE,
        "opened": "CONT-151 TRAIN 6",
    })
    for e in r:
        if e.get("id") == "F-NEW-478":
            ev = e.get("evidence")
            if not isinstance(ev, str):
                ev = json.dumps(ev, ensure_ascii=False) if ev is not None else ""
            e["evidence"] = ev + F478_APPEND
    json.dump(r, open(path, "w"), ensure_ascii=False, indent=1)
    print(f"{path}: {len(r)} roots")
ids_a = {e["id"] for e in json.load(open("root_registry.json"))}
ids_b = {e["id"] for e in json.load(open("canonical/root_cause_registry.json"))}
print("main==mirror:", ids_a == ids_b)
