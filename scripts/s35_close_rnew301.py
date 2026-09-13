#!/usr/bin/env python3
"""S35: close R-NEW-301 (F-077 twin) in root_registry.json with honest
closed-by-supersession wording + refresh summary/frontier list."""
import json

P = "/home/z/my-project/root_registry.json"
d = json.load(open(P))
changed = []
for r in d["roots"]:
    if r.get("id") == "R-NEW-301":
        r["status"] = "VERIFIED-FIXED"
        r["evidence"] = (
            r.get("evidence", "")
            + " || S35 CLOSURE (closed-by-supersession): symptom GONE at b3409007 — dooz rc=0 x5 "
            "deterministic with initial composition completing past the former K/t.s death point "
            "(content lambda n1/u.k executes x18, rememberNavController returns, 3 destinations "
            "register, full navigation stack executes as real bytecode; S34 record sec.1, probes "
            "TSTATE/READSIDE/NSPUSH). The break was eliminated collectively by the F-090..F-100 "
            "law chain; the single fixing law was not isolated (forensics debt, "
            "MINIANDROID_S22_TRACE=1 probe retained). Closure record: "
            "docs/maintenance/F_LEDGER_CLOSURE_S35.md. F-100's twin ledger entry closed same session."
        )
        r["commit"] = "S35-F-LEDGER-CLOSURE"
        changed.append("R-NEW-301")
    if r.get("id") == "R-NEW-301":
        r.setdefault("priority", "P0")

s = d["summary"]
s["total_roots"] = len(d["roots"])
of = [x for x in s.get("open_frontiers", []) if x != "R-NEW-301"]
s["open_frontiers"] = of
s["last_updated"] = "S35 2026-09-13"
s["note"] = ("S35: R-NEW-301 (F-077) closed-by-supersession — dooz composition completes at HEAD; "
             "F-ledger 100% resolved (docs/maintenance/F_LEDGER_CLOSURE_S35.md); "
             "live frontier = R-NEW-334 (recompose-scope re-arm).")

with open(P, "w") as f:
    json.dump(d, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("changed:", changed, "| open_frontiers now:", of, "| total:", len(d["roots"]))

