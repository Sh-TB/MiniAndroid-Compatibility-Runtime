#!/usr/bin/env python3
"""CONT-121 W-04: B-cluster UNPROVEN re-scan against fresh c121 run logs.
CONT-119 discipline: inventory mentions != behavioral evidence. An UNPROVEN
root only upgrades when a DATED (this-wave) log carries its BEHAVIORAL
signature (exception/death/law line), not an inventory mention."""
import json, glob, re

reg = json.load(open('root_registry.json'))
roots = reg['roots'] if isinstance(reg, dict) and 'roots' in reg else reg
unproven = [r for r in roots if r.get('status') == 'UNPROVEN']
print(f"UNPROVEN roots: {len(unproven)}")

# fresh logs from this wave only
logs = {}
for f in glob.glob('run/c121/*.log'):
    try:
        logs[f] = open(f, 'rb').read().decode('utf-8', errors='replace')
    except Exception:
        pass
print(f"scanned {len(logs)} fresh logs")

upgrades, stays = [], 0
for r in unproven:
    rid = r.get('id', '')
    title = r.get('title', '') or r.get('summary', '')
    # behavioral signature keys: root id + distinctive tokens from title
    toks = [t for t in re.findall(r'[A-Za-z_][A-Za-z0-9_$.]{5,}', title)][:6]
    hit_logs = []
    for lf, data in logs.items():
        if rid in data:
            hit_logs.append(lf)
            continue
        # require >=2 distinctive tokens co-occurring = weak; only flag
        joined_hits = sum(1 for t in toks if t and t in data)
        if toks and joined_hits >= len(toks):
            hit_logs.append(lf + "?all-tokens")
    if hit_logs:
        upgrades.append((rid, hit_logs[:3], title[:80]))
    else:
        stays += 1

print(f"\npotential upgrades (id or full-token-set hits in c121 logs): {len(upgrades)}")
for rid, hl, t in upgrades[:12]:
    print(f"  {rid}: {hl}  | {t}")
print(f"stays UNPROVEN (no fresh behavioral evidence): {stays}")
json.dump({"scanned": len(unproven), "potential": len(upgrades), "stays": stays},
          open('run/c121/w04_scan.json', 'w'), indent=1)
