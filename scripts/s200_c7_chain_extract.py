#!/usr/bin/env python3
"""C7 patch-chain test: extract W5..W9 parts from harvested comments,
assemble, sha-verify where claimed, and report per wave."""
import json, hashlib, re
from pathlib import Path

HARVEST = Path('/home/z/my-project/evidence/s200/harvest')
OUT = Path('/home/z/my-project/evidence/s200/c7_chain')
OUT.mkdir(parents=True, exist_ok=True)

c7 = json.load(open(HARVEST / 'issue_520_comments.json'))
by_id = {c["id"]: c["body"] for c in c7}

WAVES = {
    "w5":  {"parts": [6665338852, 6665340055, 6665341134, 6665342295, 6665343807,
                      6668210586, 6668211144, 6668211725, 6668212351, 6668212980,
                      6668213677], "claimed": "b286c828f1034d797f9651c500df5d2134aa24a01e48fe18a9755abefd397565"},
    "w6":  {"parts": [6708666427, 6708666837], "claimed": "df35cac717918e580ac208f2c32bd0ba55966c0c41ceec12a67886cb74023943"},
    "w7":  {"parts": [6709889923], "claimed": "8c76baccabba5cf28bf31e71e8a2855889ab45ca187ed99747647f86f617cdc7"},
    "w8":  {"parts": [6711440744, 6711441147], "claimed": "a2518d1d60cc054cee2566dc84f4a2fd05d3ec585e729cfe162b679741581898"},
    "w9":  {"parts": [6712716858, 6712717574, 6712718300], "claimed": "fc38091deaae71f0c2e12a0eea5dd48ab43f928639d58b4d82ad7e5f3e0f8f46"},
}

def fence(b):
    m = re.search(r"```(?:diff)?\n(.*?)```", b, re.S)
    return m.group(1) if m else None

for w, spec in WAVES.items():
    pieces = []
    ok = True
    for cid in spec["parts"]:
        d = fence(by_id.get(cid, ""))
        if d is None:
            print(f"{w}: part id {cid} NO FENCE")
            ok = False
            continue
        pieces.append(d)
    full = "\n".join(p.rstrip("\n") for p in pieces) + "\n"
    sha = hashlib.sha256(full.encode()).hexdigest()
    (OUT / f"c7_{w}.patch").write_text(full)
    match = "MATCH" if sha == spec["claimed"] else ("N/A(claim)" if not spec["claimed"] else "MISMATCH")
    print(f"{w}: parts={len(pieces)} bytes={len(full)} sha256={sha[:16]}… claimed={spec['claimed'][:16]}… -> {match}")
