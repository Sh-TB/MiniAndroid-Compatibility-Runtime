#!/usr/bin/env python3
"""cont151_train5_registry.py — TRAIN 5 (CONT-151) registry update.
Adds F-NEW-478 (Lwt0; draw-block chain law: T0 walk vs U0 candidates kind-int
mismatch) + appends to F-NEW-477. Syncs main + mirror."""
import json

F478_EVIDENCE = (
    "CONT-151 TRAIN 5 (binary f6b272ea, dooz v23): the T0(4) lookup decoded "
    "to its terminal law. (1) T0 pc0 = invoke-STATIC Lqz0;.g(kind)Z — a "
    "BIT-MASK TEST, not a container query: g(mask) = ((mask & 0x80) != 0) | "
    "((mask & 0x400000) != 0) (raw-byte verified: and-int/lit16 0x80 + "
    "const/high16 0x400000 + and-int/2addr + or-int). Kind 4 (the content "
    "draw-block) has NEITHER bit -> g(4)=FALSE 12/12. (2) Slow path: S0() "
    "chain head -> Lwt0;.i/.j links -> U0() candidate — U0 RETURNS NON-NULL "
    "candidates 10x obj#2708 Lg4; + Ltt0;/Lkn1;/Lzm1;/Lc70; per RET-TRACE — "
    "the SAME classes as the 65 insert containers (Lkz0;.e <- Lel0;.d). "
    "(3) The candidate kind-int checks (.h then .g, with cache write-backs) "
    "never match kind 4 -> pc38 const/4 0 -> return NULL 12/12 -> M0 skips "
    "content. VERDICT: the draw-block chain HAS entries; the kind-int "
    "semantics written at insert time vs tested at walk time never agree "
    "for kind 4. NEXT LEVER (precise): decode the .g/.h kind-int writers "
    "(Lfw;.<init> e-insert + Lkz0;.a/b/e/h paths) and the pc22-33 compare "
    "law; candidate engine surfaces: iget-int/iput-boolean interleaving in "
    "T0's cache write-back, and the Lqz0;.b insert helper's key math. "
    "Opcode law corrected en route: 0x71 = invoke-STATIC (0x72 = interface); "
    "static args live at v(Regs-Ins) — both verified against raw bytes."
)

F477_APPEND = (
    " || CONT-151 TRAIN 5: T0's g() is a BIT-MASK test (kind & 0x80 | kind & "
    "0x400000), not a container query; the Lwt0; chain walk (S0/U0) returns "
    "real candidates (Lg4;/Ltt0;/Lkn1;/Lzm1;/Lc70;) whose kind-ints never "
    "match kind 4 — promoted to F-NEW-478 (chain kind-int mismatch law)."
)

for path in ("root_registry.json", "canonical/root_cause_registry.json"):
    r = json.load(open(path))
    ids = {e.get("id") for e in r}
    assert "F-NEW-478" not in ids, f"F-NEW-478 already in {path}"
    r.append({
        "id": "F-NEW-478",
        "title": ("F-NEW-478 — Lwt0; draw-block chain law: T0(4) g-bit-test "
                  "FALSE + chain walk returns candidates whose kind-ints "
                  "never match kind 4 -> NULL -> content skipped"),
        "status": "CLASSIFIED",
        "priority": "P0",
        "layer": "compose-draw",
        "evidence": F478_EVIDENCE,
        "opened": "CONT-151 TRAIN 5",
    })
    for e in r:
        if e.get("id") == "F-NEW-477":
            ev = e.get("evidence")
            if not isinstance(ev, str):
                ev = json.dumps(ev, ensure_ascii=False) if ev is not None else ""
            e["evidence"] = ev + F477_APPEND
    json.dump(r, open(path, "w"), ensure_ascii=False, indent=1)
    print(f"{path}: {len(r)} roots")
ids_a = {e["id"] for e in json.load(open("root_registry.json"))}
ids_b = {e["id"] for e in json.load(open("canonical/root_cause_registry.json"))}
print("main==mirror:", ids_a == ids_b)
