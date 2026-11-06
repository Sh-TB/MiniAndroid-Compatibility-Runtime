#!/usr/bin/env python3
"""S186: full incomplete-title census from GitHub issues + progress audit.
Output: evidence/s186_s107/S186_INCOMPLETE_CENSUS.json (+ console table)."""
import json, re, os
from collections import Counter, defaultdict
from datetime import datetime

ia = json.load(open('forensic_data/issues_all.json'))
op = [i for i in ia if i.get('state') == 'open']

def pkg_of(i):
    b = i.get('body') or ''
    m = re.search(r'- Package: `([^`]+)`', b)
    return m.group(1) if m else None

def labels(i):
    return {l['name'] for l in i.get('labels', [])}

def fam_of(pkg, title):
    tl = (title + ' ' + (pkg or '')).lower()
    if re.search(r'libgdx|badlogic|\bgdx\b', tl): return 'F-B1/libgdx'
    if re.search(r'compose|material3', tl): return 'F-B3/compose'
    if re.search(r'\bkotlin', tl): return 'F-B5/kotlin'
    if re.search(r'mupdf|pdf', tl): return 'F-B1/native-pdf'
    if re.search(r'surge|thextech|gnubg|boxcars|freebloks|asteroids|mahjong|sudoku', tl): return 'F-B1/native-game'
    if re.search(r'telegram|forkgram|thunderbird|tusky|nextcloud', tl): return 'F-B7/tg-family'
    return 'F-UI/framework'

rows = []
for i in op:
    lb = labels(i)
    pkg = pkg_of(i)
    st = re.search(r'- State: `([^`]+)`', i.get('body') or '')
    state = st.group(1) if st else None
    # bucket
    if 'fail-oncreate' in lb: bucket = 'EXECUTED_CRASHED'
    elif state == 'STATE-NOT-LOADED' or 'state-not-loaded' in lb: bucket = 'INTAKE_QUEUE'
    elif 'state-nonblank' in lb: bucket = 'LOADED_PARTIAL'
    elif 'executed' in lb: bucket = 'EXECUTED_PARTIAL'
    else: bucket = 'META_TRACKER'
    rows.append(dict(issue=i['number'], title=i['title'][:70], package=pkg,
                     bucket=bucket, state=state,
                     labels=sorted(lb & {'fail-oncreate','state-not-loaded','state-nonblank','executed','graphics','game','app'}),
                     updated=i['updated_at'][:10], comments=i.get('comments', 0),
                     family=fam_of(pkg, i['title'])))

buck = Counter(r['bucket'] for r in rows)
print('=== buckets ===')
for k, v in buck.most_common(): print(f'{v:4d} {k}')
real = [r for r in rows if r['bucket'] in ('EXECUTED_CRASHED', 'LOADED_PARTIAL', 'EXECUTED_PARTIAL')]
print(f'\nREAL STUCK (executed, crashed/partial): {len(real)}')
fam = Counter(r['family'] for r in real)
for k, v in fam.most_common(): print(f'{v:4d} {k}')
# progress proxy: updated in Nov 2026 (recent activity = someone worked on it)
recent = [r for r in real if r['updated'] >= '2026-11-01']
stale = [r for r in real if r['updated'] < '2026-11-01']
print(f'\nprogress signal: {len(recent)} touched since 2026-11-01, {len(stale)} stale')
json.dump(dict(schema='s186_incomplete_census/v1', generated='2026-11-06',
               buckets=dict(buck), n_open=len(op), rows=rows),
          open('evidence/s186_s107/S186_INCOMPLETE_CENSUS.json', 'w'), indent=1)
print('\n=== stale REAL-STUCK oldest 12 (no progress) ===')
for r in sorted(stale, key=lambda r: r['updated'])[:12]:
    print(f"#{r['issue']} {r['updated']} {r['family']:18s} {r['title'][:52]}")
print('\n=== recent REAL-STUCK (has progress) 12 ===')
for r in sorted(recent, key=lambda r: r['updated'], reverse=True)[:12]:
    print(f"#{r['issue']} {r['updated']} {r['family']:18s} {r['title'][:52]}")
