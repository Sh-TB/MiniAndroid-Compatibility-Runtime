#!/usr/bin/env python3
"""FINAL CAMPAIGN PHASE 20 — registry + audit-wave root.
F-NEW-192 (P2 residue: z-order elevation/translation-Z not modeled) +
audit-wave census recorded. Regenerates the master worklist.
"""
import json, subprocess
from pathlib import Path

REG = Path('/home/z/my-project/canonical/root_cause_registry.json')
data = json.loads(REG.read_text())
roots = data['roots'] if isinstance(data, dict) and 'roots' in data else data

have = {r['id'] for r in roots}
if 'F-NEW-192' not in have:
    roots.append({
        'id': 'F-NEW-192',
        'status': 'REGISTERED',
        'priority': 'P2',
        'layer': 'renderer/z-order',
        'title': 'PHASE 10 draw/z-order audit residue: AOSP View.draw order '
                 '(drawBackground -> onDraw -> dispatchDraw -> decorations) '
                 'is enforced in the frame walk (21-P0-6 census law; forward '
                 'child pop; S86 visibility gates; item-21 placeholders out '
                 'of the authoritative frame) but elevation/translationZ '
                 '(RenderNode Z ordering, outline shadows) is NOT modeled — '
                 'sibling overlap order on elevated views may diverge.',
        'law': 'AOSP View.draw + RenderNode Z law: children draw in '
               'program order; Z-elevated siblings reorder above flat ones '
               'with shadow decoration.',
        'evidence': 'scripts/fc_audit_stubs.py census (34 void-answer '
                    'sites: 12 lawful-void / 21 state-capture verified / 1 '
                    'silent-void FIXED = setIntent state identity); draw '
                    'walk audit execution_engine.cpp L3640-4460.'})

if isinstance(data, dict) and 'roots' in data:
    data['roots'] = roots
    json.dump(data, REG.open('w'), indent=1)
else:
    json.dump(roots, REG.open('w'), indent=1)
print('registry roots:', len(roots))

# regenerate the master worklist
r = subprocess.run(['python3', 'scripts/s128_build_master_worklist.py'],
                   capture_output=True, text=True, timeout=300)
print('worklist regen rc:', r.returncode)
print((r.stdout or r.stderr)[-400:])
