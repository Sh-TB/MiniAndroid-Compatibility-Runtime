#!/usr/bin/env python3
"""cont28_registry_update.py — CONT-28 W1 registry update.
F-NEW-516: the named null-contract singles root-caused to framework
factories answering null; L1-L4 landed. Remaining singles re-scoped to the
layer-2 families. New: F-NEW-520 collections-view/iterator stub family.
"""
import json, sys

PATH = "/home/z/my-project/root_registry.json"
reg = json.load(open(PATH))
roots = reg["roots"] if isinstance(reg, dict) else reg

def find(rid):
    for r in roots:
        if r.get("id") == rid:
            return r
    return None

f516 = find("F-NEW-516")
assert f516, "F-NEW-516 missing"
f516["status"] = "ROOT-CAUSED-FIXED (named singles) + LAYER-2 RESCOPED"
f516["evidence"] = (
    "CONT-28 W1 (binary bc855252d150815d): the DEX-decoded census roots are "
    "framework factories answering null where AOSP contracts never-null, "
    "killed by R8's X.getClass() null-check idiom inside <clinit>: "
    "webstack Lru1;.<clinit> pc=47 = Logger.getLogger; audiobook Lox5;.<clinit> "
    "pc=14 = LocalTime.of; wocheneinkauf Lqm;.<clinit> pc=25 = "
    "TrustManagerFactory.getInstance + Ly7;.a pc=34 = BreakIterator. "
    "L1-L4 landed in bridge_to_api (F516 battery): Logger demand-create/cache, "
    "LocalTime value objects, TrustManagerFactory non-null factory, "
    "BreakIterator never-null. Named clinits result=OK at verify "
    "(run/cont28/f141/); dooz advanced by its own family hit "
    "Logger.getLogger('o0') -> 90s anchor re-pin 31ddd4d5 -> 851cc176 "
    "(lawful, root-caused). Regression: anchors 5/6 byte-identical (+dooz "
    "lawful re-pin), games 7/7 rc=0 deterministic byte-identical, goldens "
    "4/4, negatives 19/19, selftest 13/13. Remaining f141 faces rescope: "
    "layer-2 = collections view/iterator stub family (F-NEW-520) + named "
    "dives (audiobook Lhm;.n f@22103 chain, webstack Lp21;.<init>, prism "
    "unifiedpush cursor, surgeengine Sensors list, goodtime Lap2;.a). "
    "Evidence: evidence/cont28/CONT28_W1_LEDGER.md + "
    "evidence/cont28/RECURRING_FACES_LAW_SPEC.md."
)

if not find("F-NEW-520"):
    roots.append({
        "id": "F-NEW-520",
        "title": "Collections view/iterator stub family (CONT-28 layer-2): "
                 "framework Map/Collection put+view+iterator chain answers "
                 "stubs where OpenJDK answers live views — Map.put REC-MISS "
                 "(entry never stored), entrySet/keySet/values on a REAL "
                 "map answer empty singletons or stubs, Iterator.hasNext/"
                 "next + Map$Entry.getKey REC-MISS → null. Census faces: "
                 "wocheneinkauf Ll7;.b pc=13 (OkHttp logger-name map "
                 "iteration → getLogger(null)) + Ly7;.a pc=118 "
                 "(Iterator.hasNext on null); prism unifiedpush "
                 "Database.listApps cursor producer; surgeengine Sensors "
                 "static list. GPG-107 kin (values() view law); needs the "
                 "live-view completion for entrySet/keySet + Map.put "
                 "storage + Entry views.",
        "status": "REGISTERED",
        "priority": "P1",
        "layer": "framework/collections-views"
    })

if isinstance(reg, dict):
    reg["roots"] = roots
    json.dump(reg, open(PATH, "w"), indent=1, ensure_ascii=False)
else:
    json.dump(roots, open(PATH, "w"), indent=1, ensure_ascii=False)

ids = [r["id"] for r in roots]
assert len(ids) == len(set(ids)), "id collision!"
print("registry roots:", len(roots), "id-unique OK")
print("F-NEW-516 status:", find("F-NEW-516")["status"])
print("F-NEW-520 present:", bool(find("F-NEW-520")))
