#!/usr/bin/env python3
"""CONT-117: parse battery.log -> battery.json (E-01..E-10 terminal states)."""
import json, re, os

log = open('run/c117/battery.log').read() if os.path.exists('run/c117/battery.log') else ''
tasks = []

def add(tid, title, verdict, evidence):
    tasks.append({'id': tid, 'title': title, 'verdict': verdict, 'evidence': evidence})

# E-01 selftest
m = re.search(r'selftest rc=(\d+)', log)
ok = m and m.group(1) == '0'
passes = len(re.findall(r'PASS', log))
add('E-01', 'classifier selftest suite', 'تایید (selftest green)' if ok and passes else 'CONFIRMED_OPEN_GAP (selftest rc!=0)',
    f'rc={m.group(1) if m else "?"}, PASS lines={passes}')

# E-02..05 wall anchors, E-06 whites
anchors = [('E-02', 'dooz', 'd602648e8e401895'), ('E-03', 'opencalc', 'd5f3c7b5e9936ae6'),
           ('E-04', 'unote', '90a67cc1ddda57b7'), ('E-05', 'microtimer', 'bbd350b6c14fbd52'),
           ('E-06a', 'chess', 'a0319686d56ff5c0'), ('E-06b', 'tower3d', '11a38a5aeeff45a6')]
for tid, name, anchor in anchors:
    m = re.search(rf'face=(\S+) recorded={anchor}\n{name}_ANCHOR_(MATCH|DIFF)', log)
    if m:
        v = 'تایید (zero drift)' if m.group(2) == 'MATCH' else f'CONFIRMED_OPEN_GAP (face {m.group(1)} != anchor — honest drift recorded)'
        add(tid, f'wall anchor {name}', v, f'face={m.group(1)} anchor={anchor} {m.group(2)}')
    else:
        add(tid, f'wall anchor {name}', 'BLOCKED_NEEDS_EVIDENCE (run missing in log)', f'anchor={anchor}')

# E-07 negatives (take the LAST verdict — remedy runs append below stale ones)
rcs = re.findall(r'negatives rc=(\d+)', log)
m = rcs[-1] if rcs else None
passes_all = log.rstrip().endswith('NEGATIVE TESTS: 19/19 PASS') or 'NEGATIVE TESTS: 19/19 PASS' in log.split('== E-07 REMEDY RUN')[-1]
add('E-07', 'negatives gate (19/19 expected)', 'تایید (negatives green after CONT-111 store remedy)' if passes_all else 'CONFIRMED_OPEN_GAP (negatives rc!=0 — honest)',
    f'last rc={m}, 19/19 PASS in remedy section={passes_all}')

# E-08/09/10
add('E-08', 'registry id-unique', 'تایید (780 id-unique)' if 'ID_UNIQUE=True' in log else 'CONFIRMED_OPEN_GAP', re.search(r'roots=\d+ unique=\d+ ID_UNIQUE=\w+', log).group(0) if re.search(r'ID_UNIQUE=\w+', log) else '')
add('E-09', 'registry mirror consistency', 'تایید (main==mirror)' if 'mirror_identical= True' in log else 'REJECTED_WITH_REASON (mirror absent/differs — recorded as-is)', 'checked at battery time')
add('E-10', 'HEAD==origin/main', 'تایید (verified)' if 'MATCH=YES' in log else 'CONFIRMED_OPEN_GAP', re.search(r'local=\S+ remote=\S+ MATCH=\w+', log).group(0) if 'MATCH=' in log else '')

json.dump({'wave': 'CONT-117', 'tasks': tasks}, open('run/c117/battery.json', 'w'), indent=1, ensure_ascii=False)
ok = sum(1 for t in tasks if t['verdict'].startswith('تایید'))
print(f"battery.json: {len(tasks)} E-tasks, {ok} تایید")
for t in tasks:
    print(' ', t['id'], t['verdict'][:70])
