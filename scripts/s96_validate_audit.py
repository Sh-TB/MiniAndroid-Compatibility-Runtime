#!/usr/bin/env python3
"""S95-FOLLOWUP/S96 final validation gate:
1. every repo-relative markdown link in the new/changed docs resolves;
2. no duplicate titles/packages in the executed-games machine index;
3. every screenshot path+SHA in the machine index matches canonical SHA256SUMS;
4. status words used are inside the strict vocabulary;
5. machine-index summary counts equal the recomputed counts (self-consistency)."""

import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
fails = []

# 1. link validation
DOCS = ['docs/VERIFIED_EXECUTED_GAMES.md', 'docs/EXECUTED_GIFS.md',
        'docs/SOURCE_REUSE_ROI.md', 'README.md', 'docs/KNOWLEDGE_INDEX.md',
        'docs/MINIANDROID_CONTRIBUTING.md']
link_re = re.compile(r'\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)')
img_re = re.compile(r'<img src="([^"]+)"')
for d in DOCS:
    base = os.path.dirname(d)
    txt = open(d).read()
    targets = link_re.findall(txt) + img_re.findall(txt)
    for t in targets:
        if t.startswith(('http://', 'https://', 'mailto:')):
            continue
        p = os.path.normpath(os.path.join(base, t))
        if not os.path.exists(p):
            fails.append(f"{d}: broken link -> {t}")

# 2/3/4/5. machine index checks
M = json.load(open('docs/verified_executed_games.json'))
SUMS = {}
for line in open('docs/evidence/canonical/SHA256SUMS'):
    parts = line.split()
    if len(parts) == 2:
        SUMS[parts[1]] = parts[0]

titles = [g['title'] for g in M['games']]
pkgs = [g['package'] for g in M['games']]
if len(set(titles)) != len(titles):
    fails.append('duplicate game titles in machine index')
if len(set(pkgs)) != len(pkgs):
    fails.append('duplicate packages in machine index')

for g in M['games']:
    p = g['screenshot']['path']
    want = SUMS.get(p)
    if not want:
        fails.append(f"{g['title']}: artifact not in canonical SHA256SUMS: {p}")
    elif g['screenshot']['sha256'] != want:
        fails.append(f"{g['title']}: screenshot SHA mismatch vs SHA256SUMS")
    if not os.path.exists(p):
        fails.append(f"{g['title']}: artifact file missing: {p}")

VOCAB = {'VERIFIED', 'TESTED', 'OBSERVED', 'PARTIAL', 'FAILED', 'BLOCKED', 'PENDING'}
for g in M['games']:
    if g['audit_status'] not in VOCAB:
        fails.append(f"{g['title']}: illegal audit status {g['audit_status']}")
for o in M['observed_games']:
    if o['audit_status'] not in VOCAB:
        fails.append(f"{o['title']}: illegal observed status {o['audit_status']}")

S = M['summary']
rec = {
    'games_with_real_execution_evidence': len(M['games']),
    'games_verified': len([g for g in M['games'] if g['audit_status'] == 'VERIFIED']),
    'games_partial': len([g for g in M['games'] if g['audit_status'] == 'PARTIAL']),
    'games_downgraded': len([g for g in M['games'] if g.get('downgrade')]),
    'games_observed_no_artifact': len(M['observed_games']),
    'verified_games_with_state_change': len([g for g in M['games'] if g['audit_status'] == 'VERIFIED' and g['state_change_evidence']]),
    'games_with_meaningful_screenshot': len([g for g in M['games'] if g['audit_status'] in ('VERIFIED', 'PARTIAL')]),
    'games_with_repeated_run_proof': len([g for g in M['games'] if g['recorded_runs'] >= 2 and g['audit_status'] in ('VERIFIED', 'PARTIAL')]),
    'games_at_E5': len([g for g in M['games'] if g['evidence_level'] == 'E5']),
}
for k, v in rec.items():
    if S[k] != v:
        fails.append(f'summary mismatch {k}: {S[k]} != {v}')

if fails:
    print('VALIDATION FAILED:')
    for f in fails:
        print(' -', f)
    sys.exit(1)
print('AUDIT GATE PASS: links resolve, no duplicates, SHAs consistent, statuses legal, counts self-consistent')
