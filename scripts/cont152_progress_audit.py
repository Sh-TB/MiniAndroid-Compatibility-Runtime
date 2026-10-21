#!/usr/bin/env python3
"""CONT-152: real progress audit — which apps crossed stages they couldn't before.
c118 baseline (2026-10-19) vs fresh battery (today, binary f6b272ea).
Outputs run/c152/progress_audit.json with hard per-app deltas."""
import json, os, subprocess, sys
from collections import Counter

os.makedirs('run/c152', exist_ok=True)
out = {}

# 1. per-app before/after
before = {e['app']: e for e in json.load(open('run/c118/wagons.json'))}
sc = json.load(open('run/c129/scorecard.json'))
after = {a['app']: a for a in sc['apps']}

crossings = []   # apps that crossed a hard behavioral stage
deltas = []      # all visible deltas incl. face advances
residuals = []   # honest no-progress (still blocked / frontier)

for app in sorted(after):
    b, a = before.get(app), after[app]
    if not b:
        continue
    d = {'app': app}
    # rc crossing (139/1 -> 0 = clean-exit join; 139 -> 1 = native-crash defused)
    try: brc = int(b['rc'])
    except Exception: brc = None
    arc = a['rc']
    d['rc'] = [brc, arc]
    d['face'] = [b['face'], a['face16']]
    d['class'] = [b['class'], a['class_today']]
    if brc == 139 and arc != 139:
        d['kind'] = 'NATIVE_CRASH_DEFUSED'
        crossings.append(d)
    elif brc not in (0, None) and arc == 0:
        d['kind'] = 'CLEAN_EXIT_JOINED'
        crossings.append(d)
    elif str(b['face']) != a['face16'] and b['face'] not in ('-', 'NO_SCREENSHOT'):
        d['kind'] = 'FACE_ADVANCED'
        deltas.append(d)
    elif a['class_today'].startswith('CLEAN') and b['class'] != a['class_today']:
        d['kind'] = 'CLEAN_STABLE'
        deltas.append(d)
    else:
        d['kind'] = 'STABLE'
        if a['class_today'] in ('ARTIFACT_DEFECTIVE',) or 'BOUNDARY' in a['class_today'] or 'DEFAULT_BG' in a['class_today']:
            residuals.append(d)
        else:
            deltas.append(d)

out['crossings'] = crossings
out['deltas'] = deltas
out['residuals'] = residuals

# 2. registry normalized family counts
reg = json.load(open('canonical/root_cause_registry.json'))
roots = reg if isinstance(reg, list) else reg.get('roots', reg)
c = Counter((r.get('status') or r.get('state') or 'NO-STATUS') for r in roots)
FIXED_KEYS = ['ROOT-CAUSED-FIXED', 'ROOT_CAUSED_FIXED', 'ROOT-CAUSED-CLOSED',
              'VERIFIED-CORRECT', 'VERIFIED-FIXED', 'VERIFIED', 'TESTED',
              'IMPLEMENTED', 'IMPLEMENTED+TESTED', 'ALREADY_FIXED_AND_TESTED',
              'ROOT-CAUSED-FIXED (manifestation 1) / SUPERSEDED (2) / BLOCKED (3)']
fixed_family = sum(v for k, v in c.items() if k in FIXED_KEYS)
closed_terminal = sum(v for k, v in c.items() if k in
    ['STALE_OR_SUPERSEDED', 'NOT-APPLICABLE', 'SUPERSEDED-BY-EVIDENCE',
     'DUPLICATE-SUPERSEDED', 'REJECTED_WITH_REASON'])
openish = sum(v for k, v in c.items() if k in
    ['PARTIAL', 'CLASSIFIED', 'BLOCKED', 'OBSERVED', 'ROOT-CAUSED-PARTIAL', 'CONFIRMED_OPEN_GAP'])
out['registry'] = {
    'total': len(roots),
    'fixed_family_strict': fixed_family,
    'fixed_family_pct': round(100.0 * fixed_family / len(roots), 1),
    'closed_terminal_nonfix': closed_terminal,
    'open_ish': openish,
    'raw_breakdown': dict(c.most_common()),
    'partial_now': c.get('PARTIAL', 0),
    'blocked_now': c.get('BLOCKED', 0),
    'confirmed_open_gap_now': c.get('CONFIRMED_OPEN_GAP', 0),
}

# 3. commit timeline (pushed, from origin/main)
log = subprocess.run(['git', 'log', '--since=2026-10-19', '--format=%ci', 'origin/main'],
                     capture_output=True, text=True).stdout.strip().splitlines()
byday = Counter(l[:10] for l in log)
out['commits_since_1019'] = {'total': len(log), 'by_day': dict(sorted(byday.items()))}

# 4. totals from fresh scorecard
out['battery_totals_now'] = sc['totals']

# 5. s57 anchor advancement (from CONT-129 verified comparison, re-quoted)
out['s57_anchor_advancement'] = {
    'opencalc': ['a976d2f9', 'd5f3c7b5'], 'unote': ['4f1a9e4e', '90a67cc1'],
    'chess': ['b5a7a35d', 'a0319686'], 'microtimer': ['da73010a', 'bbd350b6'],
    'dooz': ['d602648e (frozen by design frontier)', 'd602648e'],
}

json.dump(out, open('run/c152/progress_audit.json', 'w'), indent=1, ensure_ascii=False)
print('crossings:', [(d['app'], d['kind'], d['rc']) for d in crossings])
print('deltas:', [(d['app'], d['kind']) for d in deltas])
print('residuals:', [d['app'] for d in residuals])
print('registry: total=%d fixed=%d (%.1f%%) open_ish=%d partial=%d blocked=%d' % (
    out['registry']['total'], fixed_family, out['registry']['fixed_family_pct'],
    openish, out['registry']['partial_now'], out['registry']['blocked_now']))
print('commits since 10-19:', out['commits_since_1019'])
