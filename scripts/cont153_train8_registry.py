#!/usr/bin/env python3
"""cont153_train8_registry.py — CONT-153 TRAIN 8: F-NEW-480 kind-4 provenance SOLVED.
M0 pc0 const/4 #4 -> T0; acceptance law (h&kind)&&(g&kind) register-verified;
T0-null -> M0 h1 overlay fallthrough. Next experiment: bit-0x4 writer census."""
import json

F480_APPEND = (
    " || CONT-153 TRAIN 8 SOLVED (dooz v23, binary f6b272ea; "
    "run/c152/t0_disasm_dooz.txt + mt_t0.log windows + cont153_t0callers.py "
    "xref): KIND-4 PROVENANCE = Lpz0;.M0 pc0 'const/4 v0, #4' — the kind is "
    "a HARD-CODED constant, never state-derived; M0 pc1 invokes T0(v0=4, "
    "v11=receiver). T0's acceptance law register-verified end-to-end: walk "
    "root = S0(receiver) (2717->2708 = empty post-re-termination chain; "
    "2061->2357 = full chain 2357->1521->1508->2708), U0 fetches candidate, "
    "accept iff (candidate.h & kind)!=0 AND (candidate.g & kind)!=0 (pc22-32: "
    "2708.h=5039275=0x4CE0AB has bits 0x80+0x400000 but NOT 0x4; 0x4CE0AB & 4 "
    "= 0 -> REJECT), loop advances v2=v2.j with cycle-guard v2==v1(root). "
    "T0 returns NULL -> M0 pc5-7 falls through to Lpz0;.h1 = the layout-"
    "bounds overlay draw (F-NEW-477's overlay law CONFIRMED at caller level) "
    "-> zero content canvas ops -> blank content block. T0 non-null -> M0 "
    "masks candidate.g (pc56-59), check-cast Lfw; (pc61-66), reads .t and "
    "proceeds to the real draw execution (Lgl0;.c with shared draw scope "
    "Lt4;.getSharedDrawScope + Leo;.S). Flag writers xref (16 iput sites): "
    "Lkz0;.a g@pc14/26, Lkz0;.f h@pc915, Lfw;.N0 g/h x5 (or-int combiner = "
    "the flag-SETTER), Lfw;.L0/M0, Lel0;.c h@pc296/405, ctors. NO runtime "
    "trace yet of any .g/.h write carrying bit 0x4. NEXT EXPERIMENT (single "
    "question): FIELD-TRACE Lwt0;.g/.h writes at runtime + decode Lfw;.N0's "
    "caller chain — does ANY node ever carry bit 0x4 (if none: the flag-"
    "writer precondition never holds = upstream state root, same shape as "
    "dooz EmptyMap F-NEW-472; if some node carries it but is absent from "
    "the walked chain: chain-membership mismatch)."
)

for path in ("root_registry.json", "canonical/root_cause_registry.json"):
    r = json.load(open(path))
    n = 0
    for e in r:
        if e.get("id") == "F-NEW-480":
            ev = e.get("evidence")
            if not isinstance(ev, str):
                ev = json.dumps(ev, ensure_ascii=False) if ev is not None else ""
            e["evidence"] = ev + F480_APPEND
            e["title"] = ("F-NEW-480 — kind-4 provenance SOLVED: M0 pc0 "
                          "hard-coded const #4 -> T0; acceptance (h&kind)&&"
                          "(g&kind) verified; T0-null -> h1 overlay fallthrough; "
                          "next: bit-0x4 writer census (Lfw;.N0 caller chain)")
            n += 1
    assert n == 1, f"F-NEW-480 not found exactly once in {path} (n={n})"
    json.dump(r, open(path, "w"), ensure_ascii=False, indent=1)
    print(f"{path}: {len(r)} roots")

ids_a = {e["id"] for e in json.load(open("root_registry.json"))}
ids_b = {e["id"] for e in json.load(open("canonical/root_cause_registry.json"))}
print("main==mirror:", ids_a == ids_b)
