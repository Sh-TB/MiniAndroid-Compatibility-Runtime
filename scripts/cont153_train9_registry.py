#!/usr/bin/env python3
"""cont153_train9_registry.py — CONT-153 TRAIN 9: F-NEW-480 bit-0x4 census.
Live FIELD-TRACE Lwt0;.g: 20/69 puts carry bit 0x4 (Lfw;.N0/L0 vals 0x408085,
0x64a5bd), all on LATE instances (obj#6xxx/9xxx), all BEFORE the draw windows;
the draw query walks the EARLY chain (obj#2357 root) whose nodes lack bit 4."""
import json

F480_APPEND2 = (
    " || CONT-153 TRAIN 9 LIVE CENSUS (MINIANDROID_FIELD_TRACE=Lwt0;.g on dooz "
    "v23, binary f6b272ea, run/c152/dooz_gh_trace.log, 579 field events): "
    "(1) 69 puts to Lwt0;.g; 20/69 carry bit 0x4 — writers: Lfw;.N0 "
    "(0x408085 x4+2, 0x64a5bd x4, 0x64a09d x2), Lfw;.L0 (0x408085 x2+), "
    "Lkz0;.a (0xd, 0x7, 0x5, 0xf, 0x1007) — the capability flags ARE set "
    "with bit 0x4 at runtime; (2) OBJECT CENSUS: every bit-4 put lands on "
    "LATE chain instances (obj#6497/9273/9317/9368/9456/9457/9487/9504/"
    "9535/9588/9589/9610/9625/9630) — the SAME late-instance family as the "
    "130 later .i puts (F-NEW-479 correction); (3) TEMPORAL CENSUS: the "
    "bit-4 puts land at lines 140376-140495, the first T0 draw window at "
    "line 155826 — capable nodes EXIST BEFORE the draw queries; (4) the "
    "draw query T0 walks the EARLY chain rooted at S0(receiver)->obj#2357 "
    "(nodes 1521/1508/2708) whose .g/.h never carry bit 4 -> reject-all -> "
    "h1 overlay -> blank. STRUCTURAL LAW: the kind-4 draw query is bound "
    "to an EARLY/STALE chain instance while the draw-capable (bit-4) nodes "
    "populate LATER instances built by the same Lkz0;.a/Lel0;.c builder-"
    "trim pair in subsequent layout passes — same stale-state shape as "
    "F-NEW-472 (EmptyMap publish path). NEXT LEVER (single question): M0's "
    "receiver provenance — where does v11 (obj#2717/2061) come from and "
    "does the app re-bind that reference to the late instance (an engine-"
    "missed invalidation) or genuinely query the early scope (upstream "
    "state)."
)

for path in ("root_registry.json", "canonical/root_cause_registry.json"):
    r = json.load(open(path))
    n = 0
    for e in r:
        if e.get("id") == "F-NEW-480":
            ev = e.get("evidence")
            if not isinstance(ev, str):
                ev = json.dumps(ev, ensure_ascii=False) if ev is not None else ""
            e["evidence"] = ev + F480_APPEND2
            n += 1
    assert n == 1, f"F-NEW-480 not found exactly once in {path}"
    json.dump(r, open(path, "w"), ensure_ascii=False, indent=1)
    print(f"{path}: {len(r)} roots")

ids_a = {e["id"] for e in json.load(open("root_registry.json"))}
ids_b = {e["id"] for e in json.load(open("canonical/root_cause_registry.json"))}
print("main==mirror:", ids_a == ids_b)
