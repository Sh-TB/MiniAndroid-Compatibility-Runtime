#!/usr/bin/env python3
# cont97_registry_update.py — register the CONT-97 T1 outcomes in
# root_registry.json (and mirror to canonical/root_cause_registry.json):
#   INFRA-BRIDGECENSUS-1  — the bridge dispatch census tool (INFRA-LANDED)
#   INFRA-BRIDGEINTR-1    — the bridge intrinsic entry fast path (IMPLEMENTED+TESTED)
import json, copy

PATH = "root_registry.json"
MIRROR = "canonical/root_cause_registry.json"

with open(PATH) as f:
    reg = json.load(f)
roots = reg["roots"] if isinstance(reg, dict) and "roots" in reg else reg
if isinstance(roots, dict):
    root_list = list(roots.values())
    dict_mode = True
else:
    root_list = roots
    dict_mode = False

n0 = len(root_list)
ids = {r.get("id") for r in root_list}

def make(id_, **kw):
    e = {"id": id_}
    e.update(kw)
    return e

new_entries = [
    make(
        "INFRA-BRIDGECENSUS-1",
        status="INFRA-LANDED",
        priority="P1",
        title="Bridge dispatch cost was an unattributed 145.7K cycles/call aggregate (102.5G ticks / 702K calls at the Telegram 30s gate) — no tool could name which (class,method) keys burn it",
        layer="interpreter/bridge/measurement",
        root_cause="bridge_to_api is a ~33.5K-line sequential law chain; the phase clock only measured the whole phase. CONT-96 named the dispatch chain the NEXT frontier but could not rank the keys.",
        fix="MINIANDROID_BRIDGE_CENSUS=1: RAII per-call (class|method) -> (count, ticks) map, atexit top-48 dump. Stack-local per-call key (the first draft shared a thread_local and nested bridge subtrees clobbered the attribution — caught and fixed same wave; the 14.9M cy/call Attributes.getLength artifact in the intermediate run was this tool bug, not engine behavior).",
        evidence={
            "wave": "CONT-97",
            "measured": "tg1 census: 684 keys; Ljava/lang/Character;|isWhitespace 88,001 calls x 994,399 cy/call = 85.4% of all bridge ticks; Ljava/lang/String;|charAt 535,506 calls x 20,164 cy/call = 10.5%; tg3 clean census: XMLReader|parse = 1 call = the parse subtree, charAt down to 3.8K cy/call",
            "logs": "run/cont97/census/tg1.stderr (pre), tg3.stderr (post-fix clean)",
        },
    ),
    make(
        "INFRA-BRIDGEINTR-1",
        status="IMPLEMENTED+TESTED",
        priority="P0",
        title="ART-parity bridge intrinsic entry fast path: the two hottest bridge keys (Character.isWhitespace/isSpaceChar, String.charAt) walked ~33.5K lines of sequential law chain per call (994K and 20K cycles/call respectively)",
        layer="interpreter/bridge/dispatch",
        root_cause="Both laws live mid/late-chain (isWhitespace ~59091, String.charAt ~57089) inside a 33.5K-line if-chain; the walk IS the cost (law bodies are trivial). The SVG parse hot loop calls these 624K+88K times per 30s gate.",
        fix="Entry fast path at bridge_to_api top, BEFORE the chain: same arg-shape guards as the deep sites, law bodies copied verbatim (same ws/sc sets, same UTF-8 decode + surrogate law, same honest-0 OOB rule, R-NEW-353 result-out contract); charAt reads the receiver via const ref (the deep site's local copy was read-only). SOUNDNESS: exactly one match site per key in the chain; no class_name.find/starts_with prefix condition mentions String/Character anywhere in the chain, so the skipped prefix is provably non-matching; other-shaped calls still fall through. The deep sites remain in place (unreachable for these keys, kept as the law origin).",
        evidence={
            "wave": "CONT-97",
            "measured": "isWhitespace 994,399 -> 727 cy/call (1369x); charAt 20,164 -> 3,816 cy/call; Telegram 30s gate 12.7M -> 16.1M instructions (+27% on top of CONT-96's +24%); bridge phase calls 702K -> 80K",
            "battery": "wall 12/12 MATCH byte-identical, goldens 4/4, negatives 19/19, reinstall 8/8, MG-310 rc=0, MG-150 rc=0, selftests 13/13, F-NEW-376 70/70, sax1 PASS, clock1 4/4, clinit1 law-correct, swipe1 OK, c74esc containment OK, perf1 4/4 checksums byte-identical (3688000/31744000/14534196240) — ZERO DRIFT at b6073e78a45dc7fa",
            "logs": "run/cont97/battery.log, run/cont97/anchor_*.log, evidence/cont97/",
        },
    ),
]

added = 0
for e in new_entries:
    if e["id"] not in ids:
        root_list.append(e)
        added += 1

n1 = len(root_list)
print(f"registry: {n0} -> {n1} (+{added})")

with open(PATH, "w") as f:
    if dict_mode:
        json.dump(reg, f, indent=1, ensure_ascii=False)
    else:
        json.dump(root_list, f, indent=1, ensure_ascii=False)

# mirror
with open(PATH) as f:
    data = json.load(f)
with open(MIRROR, "w") as f:
    json.dump(data, f, indent=1, ensure_ascii=False)
print("mirror synced:", MIRROR)
