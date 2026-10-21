#!/usr/bin/env python3
"""cont153_train7_registry.py — CONT-153 TRAIN 7 registry update.
Corrects F-NEW-477 (12/12-NULL retracted: 6/12 real node), refines F-NEW-478
(mask = pre-walk gate), retrains F-NEW-479 (deliberate re-termination, not
corrupt sever — pc400 v7=0 law), adds F-NEW-480 (T0 receiver census +
kind-4 provenance lever). Syncs main + mirror."""
import json

F479_CORRECTION = (
    " || CONT-153 TRAIN 7 CORRECTION (same binary f6b272ea, full padChain "
    "per-pc evidence run/c152/padchain_disasm.txt + mt_c.log register "
    "snapshots + t_wt0i.log timeline): the value=0 write is NOT a corrupt "
    "sever — RETRACTION of the 'severed with no re-link as an anomaly' "
    "framing. Machine-verified law: the write is pc400 in Lel0;.c "
    "(iput-object v7=0 into v9=obj#2708 Lwt0;.i) inside a COORDINATED "
    "re-termination block pc394-417 executed end-to-end (trace path "
    "...304->240->383->385->391->392->394->396->399->400->402->404->405->"
    "407->409->411->417->419->421->424->426->429->435->436->458->531): "
    "pc400 2708.i=0; pc402 2060.j=0; pc404-405 2060.h=-1; pc407 2060.l=0; "
    "pc409 'trimChain did not update the head' assertion GUARD PASSED "
    "(2708 != 2060, no throw); pc417 head-holder 2059.f = 2708 — the head "
    "is RE-POINTED as designed. v7=0 is the method's NULL-terminator "
    "constant (also v3=v7=0 at pc391 feeding 2059.h=0 at pc392). The 130 "
    "later .i puts belong to OTHER chain instances (6312/6337/6455/6361/"
    "6466/6385/...) — same builder/trim pair running per scope; 2708's "
    "chain is never re-linked because the app re-terminated it. Walkers "
    "(Lkz0;.g, Lk4;.a, Lpz0;.l1, Lle1;.q, Lpz0;.T0) traverse the stale "
    "2357-root chain 2357->1521->1508->2708 and hit the deliberate NULL "
    "at 2708; content node 2060+ is unreachable BY THE APP'S OWN "
    "RE-TERMINATION. Remaining question moved to F-NEW-480."
)

F477_CORRECTION = (
    " || CONT-153 TRAIN 7 CORRECTION: 'T0 returns NULL 12/12 windows' is "
    "RETRACTED at the return-value level. Full return census (mt_t0.log, "
    "pc39 return-object events, p0=0 receiver shape): 6/12 return "
    "v1=obj#1521 (a REAL chain node — 1521 is the 2357->1521->1508->2708 "
    "chain member) and 6/12 return v1=0/NULL. The walk is never reached "
    "in either case because the kind-mask gate (F-NEW-478) fires FIRST: "
    "kind 4 lacks both mask bits, so T0 early-returns v1 (caller-context "
    "value) without dereferencing the NULL receiver — no NPE on ART "
    "either; upstream-faithful. The blank face follows from the caller "
    "of T0 rejecting/misusing the returned candidate + the NULL-receiver "
    "call shape, NOT from a chain walk returning NULL 12/12."
)

F478_APPEND2 = (
    " || CONT-153 TRAIN 7 PROMOTION: the bit-mask test is a PRE-walk gate "
    "— T0(kind=4) fails (4 & (0x80|0x400000))==0 and early-returns v1 at "
    "pc38-39 BEFORE any p0 dereference (proven by p0=0 calls returning "
    "normally with v1=obj#1521/0 and zero NPE — both engine and ART "
    "semantics). The mask gate is therefore the terminal decision point "
    "for kind-4 content draws; the chain walk and its NULL terminator "
    "(F-NEW-479) are downstream of a gate that already rejected kind 4."
)

F480_EVIDENCE = (
    "CONT-153 TRAIN 7 (binary f6b272ea): T0 receiver census from "
    "mt_t0.log METHOD-TRACE (181657 lines, 12 full windows): T0 is "
    "invoked ONLY with p1=kind=4; receiver p0 distribution: obj#2717 x54, "
    "obj#2061 x54, obj#2708 x30, NULL x12. All four shapes converge on "
    "the same terminal: kind 4 fails the pre-walk mask gate (F-NEW-478). "
    "2708-receiver walks are empty by the app's own re-termination "
    "(F-NEW-479 correction). The content draw is unreachable at the "
    "KIND level: no node in any walked chain ever carries a kind with "
    "bit 0x80 or 0x400000. NEXT LEVER (single question): kind-4 "
    "PROVENANCE — who calls T0 with kind=4 and where should the kind "
    "ints on chain nodes be WRITTEN (the iput of the kind field on "
    "Lwt0;/Lpz0; nodes); if the kind-writer never runs, the upstream "
    "state that feeds it is the real root (same shape as the dooz "
    "EmptyMap publish-path law F-NEW-472)."
)

for path in ("root_registry.json", "canonical/root_cause_registry.json"):
    r = json.load(open(path))
    ids = {e.get("id") for e in r}
    assert "F-NEW-480" not in ids, f"F-NEW-480 already in {path}"
    for e in r:
        if e.get("id") == "F-NEW-479":
            ev = e.get("evidence")
            if not isinstance(ev, str):
                ev = json.dumps(ev, ensure_ascii=False) if ev is not None else ""
            e["evidence"] = ev + F479_CORRECTION
            e["title"] = ("F-NEW-479 — draw-block chain re-termination at "
                          "bind: Lel0;.c padChain deliberately re-terminates "
                          "the obj#2708 chain (pc400 v7=0 law, head re-point "
                          "pc417) -> walkers hit deliberate NULL")
        if e.get("id") == "F-NEW-477":
            ev = e.get("evidence")
            if not isinstance(ev, str):
                ev = json.dumps(ev, ensure_ascii=False) if ev is not None else ""
            e["evidence"] = ev + F477_CORRECTION
        if e.get("id") == "F-NEW-478":
            ev = e.get("evidence")
            if not isinstance(ev, str):
                ev = json.dumps(ev, ensure_ascii=False) if ev is not None else ""
            e["evidence"] = ev + F478_APPEND2
    r.append({
        "id": "F-NEW-480",
        "title": ("F-NEW-480 — kind-4 provenance: T0 invoked only with "
                  "kind=4 (census 2717x54/2061x54/2708x30/NULLx12); no "
                  "walked node ever carries mask bits 0x80/0x400000 — "
                  "who writes the kind ints"),
        "status": "CLASSIFIED",
        "priority": "P0",
        "layer": "compose-draw",
        "evidence": F480_EVIDENCE,
        "opened": "CONT-153 TRAIN 7",
    })
    json.dump(r, open(path, "w"), ensure_ascii=False, indent=1)
    print(f"{path}: {len(r)} roots")

ids_a = {e["id"] for e in json.load(open("root_registry.json"))}
ids_b = {e["id"] for e in json.load(open("canonical/root_cause_registry.json"))}
print("main==mirror:", ids_a == ids_b)
