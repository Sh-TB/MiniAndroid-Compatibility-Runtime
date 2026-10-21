#!/usr/bin/env python3
"""cont153_train10_registry.py — CONT-153 TRAIN 10: S0 dispatch decoded.
S0/h1 ABSTRACT on Lpz0;; overrides Lc70;39/Lm;91/Lug0;3/Lxk0;7;
Lxk0;.S0 = ((Lwt0;)this.V).e; Lwt0;.e = ctor self-ref (414 events, all self);
stale site = scope.V binding (early scopes -> early chains)."""
import json

F480_APPEND3 = (
    " || CONT-153 TRAIN 10 DISPATCH DECODE (dooz v23, binary f6b272ea; "
    "corrected per-list-restart class_data walker — discovered cls/disasm "
    "tools carry a cumulative direct+virtual midx bug, fixed in "
    "cont153_cleanwalk.py): (1) S0 and h1 are ABSTRACT on Lpz0; (no-code "
    "in class_data) — runtime dispatches to subclass overrides; scan: "
    "Lc70;.S0 (39 insns), Lm;.S0 (91), Lug0;.S0 (3), Lxk0;.S0 (7). "
    "(2) Lxk0;.S0 per-unit decode: return ((Lwt0;) this.V).e — the chain "
    "root = scope.V then .e. (3) LIVE CENSUS Lwt0;.e (414 events, "
    "run/c152/dooz_e_trace.log): EVERY put is a CONSTRUCTOR SELF-REFERENCE "
    "(obj#X.e = obj#X for X in 1508/1521/2060/2357/2396/2708/6308.../"
    "late 9xxx) — .e is identity, so S0 effectively returns scope.V. "
    "(4) THE STALE SITE IS NOW NAMED: the draw query's chain root = "
    "scope.V (Lxk0;.V : Lvk0;). The traced draw windows queried EARLY "
    "scopes (obj#2717 -> V=2708 re-terminated/empty; obj#2061 -> V=2357 "
    "early chain whose .g/.h lack bit 0x4) while the bit-4-capable nodes "
    "(Lfw;.N0/L0-written, obj#6xxx/9xxx) hang under LATE chains built in "
    "later layout passes. The draw loop (Lel0;.i -> Lpz0;.L0 -> M0 -> T0) "
    "never queries the late scopes. NEXT LEVER (single question): who "
    "binds scope.V and when — FIELD-TRACE Lxk0;.V writes + the scope "
    "iteration above Lel0;.i (Lho1;.d / Lt4;.getRoot): is V a one-time "
    "early bind that the app re-binds on real ART (engine-missed "
    "invalidation) or does the app's own draw-loop scope list stay early "
    "(upstream state)."
)

for path in ("root_registry.json", "canonical/root_cause_registry.json"):
    r = json.load(open(path))
    n = 0
    for e in r:
        if e.get("id") == "F-NEW-480":
            ev = e.get("evidence")
            if not isinstance(ev, str):
                ev = json.dumps(ev, ensure_ascii=False) if ev is not None else ""
            e["evidence"] = ev + F480_APPEND3
            n += 1
    assert n == 1, f"F-NEW-480 not found exactly once in {path}"
    json.dump(r, open(path, "w"), ensure_ascii=False, indent=1)
    print(f"{path}: {len(r)} roots")

ids_a = {e["id"] for e in json.load(open("root_registry.json"))}
ids_b = {e["id"] for e in json.load(open("canonical/root_cause_registry.json"))}
print("main==mirror:", ids_a == ids_b)
