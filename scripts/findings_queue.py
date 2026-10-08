#!/usr/bin/env python3
"""findings_queue.py — turn root_registry.json into a RANKED, ACTIONABLE queue.

The CONT-17 census (evidence/cont17/ijk_census.json) classified 217 open rows
by runnability; the CONT-18 orphan-findings audit gave every discrete finding
an explicit disposition. This tool makes the result USABLE day-to-day: it is
the single command that answers "what is the highest-priority unfinished
work, with its evidence pointer?" without reading 576 registry rows.

Disposition law (mirrors ORPHAN_FINDINGS_AUDIT.md):
  terminal  = ROOT-CAUSED-FIXED | VERIFIED-FIXED | VERIFIED-CORRECT |
              VERIFIED | TESTED | IMPLEMENTED+TESTED | NOT-APPLICABLE |
              REJECTED* | SUPERSEDED* | ROOT-CAUSED-CLOSED | USED_BY_EXECUTION |
              OBSERVED-RESOLVED
  queued    = everything else, ranked by priority (P0..P3), then by status
              class (OPEN < CLASSIFIED < PARTIAL < UNPROVEN < IMPLEMENTED),
              then id — a deterministic, evidence-first work order.

Usage:
  python3 scripts/findings_queue.py [--out DIR] [--top N] [--status S ...]
Output:
  <out>/findings_queue.json  (machine: full queue + counts)
  <out>/findings_queue.md    (human: top-N table + counts)
"""
import argparse, json, os
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(BASE, 'root_registry.json')

TERMINAL_EXACT = {
    'ROOT-CAUSED-FIXED', 'VERIFIED-FIXED', 'VERIFIED-CORRECT', 'VERIFIED',
    'TESTED', 'IMPLEMENTED+TESTED', 'NOT-APPLICABLE', 'ROOT-CAUSED-CLOSED',
    'USED_BY_EXECUTION', 'OBSERVED-RESOLVED',
}
TERMINAL_PREFIX = ('REJECTED', 'SUPERSEDED')

# status class = smaller sorts first (earlier = closer to actionable closure)
STATUS_CLASS = {
    'OPEN': 0, 'PENDING': 0, 'BLOCKED': 0, 'OBSERVED': 1, 'OBSERVED-FAIL': 1,
    'CLASSIFIED': 1, 'REGISTERED': 1, 'PARTIAL': 2, 'UNPROVEN': 3,
    'IMPLEMENTED': 4, 'RESEARCHED-NOT-IMPLEMENTED': 5, 'PENDING-APK': 6,
}
PRIORITY_CLASS = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3}


def status_class(s):
    if s in STATUS_CLASS:
        return STATUS_CLASS[s]
    return 9


def priority_class(p):
    p = (p or '').strip()
    if p in PRIORITY_CLASS:
        return PRIORITY_CLASS[p]
    return 9


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(BASE, 'evidence', 'cont18f'))
    ap.add_argument('--top', type=int, default=40)
    args = ap.parse_args()

    d = json.load(open(REG))
    roots = d['roots']

    queued, terminal = [], []
    for r in roots:
        s = str(r.get('status', ''))
        if s in TERMINAL_EXACT or s.startswith(TERMINAL_PREFIX):
            terminal.append(r)
        else:
            queued.append(r)

    queued.sort(key=lambda r: (priority_class(r.get('priority')),
                               status_class(str(r.get('status'))),
                               str(r.get('id'))))

    counts_status = Counter(str(r.get('status', '')) for r in roots)
    counts_prio_q = Counter(str(r.get('priority', '') or 'unspecified')
                            for r in queued)

    def brief(r):
        return {
            'id': r.get('id'),
            'status': r.get('status'),
            'priority': r.get('priority'),
            'layer': (r.get('layer') or '')[:48],
            'title': (r.get('title') or '')[:160],
            'evidence': (r.get('evidence') or '')[:120],
        }

    out_json = {
        'generated_by': 'scripts/findings_queue.py',
        'total_rows': len(roots),
        'queued_rows': len(queued),
        'terminal_rows': len(terminal),
        'counts_by_status': dict(counts_status.most_common()),
        'queued_by_priority': dict(counts_prio_q.most_common()),
        'queue_top': [brief(r) for r in queued[:args.top]],
        'note': ('rank = (priority P0<P1<P2<P3, status class OPEN/CLASSIFIED < '
                 'PARTIAL < UNPROVEN < IMPLEMENTED, id); terminal rows excluded; '
                 'full order deterministic; dispositions per '
                 'evidence/cont18f/ORPHAN_FINDINGS_AUDIT.md'),
    }
    os.makedirs(args.out, exist_ok=True)
    jp = os.path.join(args.out, 'findings_queue.json')
    json.dump(out_json, open(jp, 'w'), indent=1, ensure_ascii=False)

    mp = os.path.join(args.out, 'findings_queue.md')
    with open(mp, 'w') as f:
        f.write('# FINDINGS QUEUE (generated — do not edit by hand)\n\n')
        f.write("Source: root_registry.json (%d rows). Regenerate: "
                "`python3 scripts/findings_queue.py`.\n\n" % len(roots))
        f.write('Queued (actionable): **%d**   Terminal (closed/rejected/'
                'superseded/not-applicable): **%d**\n\n' % (len(queued), len(terminal)))
        f.write('Queued by priority: %s\n\n' % json.dumps(
            dict(counts_prio_q.most_common()), ensure_ascii=False))
        f.write('## Top %d of the queue\n\n' % min(args.top, len(queued)))
        f.write('| # | id | pri | status | layer | title |\n|--:|----|-----|--------|-------|-------|\n')
        for i, r in enumerate(queued[:args.top], 1):
            t = (r.get('title') or '').replace('|', '\\|')[:110]
            f.write('| %d | %s | %s | %s | %s | %s |\n' % (
                i, r.get('id'), r.get('priority') or '—', r.get('status'),
                (r.get('layer') or '—')[:36], t))
    print('wrote %s and %s' % (jp, mp))
    print('queued=%d terminal=%d total=%d' % (len(queued), len(terminal), len(roots)))


if __name__ == '__main__':
    main()
