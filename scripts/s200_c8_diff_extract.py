#!/usr/bin/env python3
"""Extract C8 wave-15 diff parts 1-11 from harvested comments, assemble,
verify SHA256 against the claim, and report."""
import json, hashlib, re
from pathlib import Path

HARVEST = Path('/home/z/my-project/evidence/s200/harvest')
OUT = Path('/home/z/my-project/evidence/s200/c8_wave15')
OUT.mkdir(parents=True, exist_ok=True)

c8 = json.load(open(HARVEST / 'issue_519_comments.json'))
PART_IDS = [6727646579, 6727647291, 6727648006, 6727648733, 6727649420,
            6727650049, 6727650685, 6727651365, 6727652079, 6727652680,
            6727653360]
CLAIMED_SHA = "0aca6d8ce05707f8e53d69e0f57b7c2251f2371fe7f714d1e557c922e102b86a"

by_id = {c["id"]: c["body"] for c in c8}

def extract_diff(body):
    # strip a leading header line, then code fence if present
    m = re.search(r"```(?:diff)?\n(.*?)```", body, re.S)
    if m:
        return m.group(1)
    # otherwise: body from the first 'diff --git' line
    i = body.find("diff --git")
    return body[i:] if i >= 0 else body

pieces = []
for n, cid in enumerate(PART_IDS, 1):
    body = by_id.get(cid)
    if not body:
        print(f"part {n}: MISSING (id {cid})"); continue
    d = extract_diff(body)
    (OUT / f"part_{n:02d}.diff").write_text(d)
    pieces.append(d)
    head = d.splitlines()[0] if d else "(empty)"
    print(f"part {n:02d}: {len(d)} ch | starts: {head[:60]}")

full = "".join(pieces)
(OUT / "c8_waves11_15_cumulative.diff").write_text(full)
sha = hashlib.sha256(full.encode()).hexdigest()
print(f"\nassembled: {len(full)} ch  sha256={sha}")
print(f"claimed : {CLAIMED_SHA}")
print("MATCH" if sha == CLAIMED_SHA else "MISMATCH")
