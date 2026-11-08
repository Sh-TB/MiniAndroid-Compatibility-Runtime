#!/usr/bin/env python3
"""S195 AUDIT — build CONTRIBUTOR_ACHIEVEMENT_INVENTORY.json (MAIN CODER
MASTER TASK §2): machine-readable records for every valuable contribution
discovered in the priority issue set, each with law-ID mainline-presence
verification against the current source tree."""
import json, re, subprocess
from collections import defaultdict
from pathlib import Path

BASE = Path('/home/z/my-project')
AUD = BASE / 'evidence/s195_audit'

issues = {i['number']: i for i in
          json.load(open(AUD / 'issues_raw.json'))['issues']}
comments = json.load(open(AUD / 'comments_raw.json'))

# ── coder attribution ────────────────────────────────────────────────────
CODER_BY_ISSUE = {}
CODER_RANGES = [
    (range(430, 437), 'C4'), (range(446, 469), 'C2/C5'),
    (range(475, 492), 'C2/C5'), (range(510, 519), 'C4'),
    (range(519, 521), 'C8'), (521, 'C9'), (522, 'C4'), (525, 'C4'),
    (526, 'C4'), (528, 'C4'), (530, 'C3'), (533, 'C8'), (534, 'C4'),
    (535, 'C3'), (536, 'GOV'), (537, 'C3'), (538, 'C4'), (540, 'C3'),
    (541, 'GOV'), (542, 'GOV'), (515, 'C6'), (516, 'C3'), (517, 'C4'),
    (518, 'C4'), (492, 'C3'), (505, 'C5'), (450, 'C2'), (472, 'C2'),
    (437, 'C6'), (438, 'C6'), (439, 'C6'), (440, 'C6'), (441, 'C6'),
    (520, 'C7'), (556, 'INT'), (557, 'C3'), (558, 'C4'), (559, 'GOV'),
    (560, 'C3'), (561, 'C3'), (562, 'C4'), (563, 'C4'), (564, 'C4'),
    (565, 'GOV'), (566, 'C4'),
]
for rng, c in CODER_RANGES:
    if isinstance(rng, range):
        for n in rng:
            CODER_BY_ISSUE[n] = c
    else:
        CODER_BY_ISSUE[rng] = c

LAW_PATTERNS = [
    (r'F-C4-(\d+[a-z]?)', 'C4'),
    (r'F-C8-(\d+[a-z]?)', 'C8'),
    (r'\bC9-(\d+[b]?)\b', 'C9'),
    (r'P-NEW-(\d+[a-z]?)', 'C9'),
    (r'F-NEW-(\d+[a-z]?)', 'MAIN'),
    (r'\bACH-([A-Z0-9\-]+)', 'ANY'),
    (r'NP-([A-Z]+\d+)', 'C5'),
    (r'JP-([A-Z]+\d+)', 'C5'),
    (r'\bdefects? (\d+)', 'C8'),
]
PATCH_MARKERS = re.compile(
    r'PART \d+/\d+|diff --git|git am|apply_check|patch \(|\.patch\b',
    re.IGNORECASE)


def text_of(n):
    parts = []
    i = issues.get(n)
    if i:
        parts.append(i.get('title') or '')
        parts.append(i.get('body') or '')
    for c in comments.get(str(n), []):
        parts.append(c['body'] or '')
    return '\n'.join(parts)


def mainline_grep(law_id):
    """is the law ID present in the current source/evidence/worklog?"""
    hits = {'src': 0, 'worklog': 0, 'evidence': 0}
    for sub, key in (('miniandroid/src', 'src'), ('worklog.md', 'worklog')):
        try:
            r = subprocess.run(
                ['grep', '-rF', law_id, str(BASE / sub),
                 '--include=*.cpp', '--include=*.h', '--include=*.md',
                 '--include=*.py', '-l'] if sub != 'worklog.md'
                else ['grep', '-rF', law_id, str(BASE / sub), '-l'],
                capture_output=True, text=True, timeout=60)
            hits[key] = len([l for l in r.stdout.splitlines() if l.strip()])
        except Exception:
            pass
    try:
        r = subprocess.run(['grep', '-rlF', law_id,
                            str(BASE / 'evidence'), '--include=*.json'],
                           capture_output=True, text=True, timeout=60)
        hits['evidence'] = len(r.stdout.splitlines())
    except Exception:
        pass
    return hits


records = []
law_mainline_cache = {}
for n in sorted(CODER_BY_ISSUE):
    if n not in issues:
        continue
    i = issues[n]
    txt = text_of(n)
    coder = CODER_BY_ISSUE[n]
    laws = []
    for pat, owner in LAW_PATTERNS:
        for m in re.findall(pat, txt):
            lid = pat.split('(')[0].replace('\\b', '').replace('(\\', '-'). \
                replace(')', '').replace('[b]?', '') + m \
                if False else None
    # simpler: direct findall with full-match construction
    laws = set()
    for pat, owner in [(r'F-C4-\d+[a-z]?', 'C4'), (r'F-C8-\d+[a-z]?', 'C8'),
                       (r'C9-\d+[b]?', 'C9'), (r'P-NEW-\d+[a-z]?', 'C9'),
                       (r'F-NEW-\d+[a-z]?', 'MAIN'), (r'NP-[A-Z]+\d+', 'C5'),
                       (r'JP-[A-Z]+\d+', 'C5')]:
        for m in re.findall(pat, txt):
            laws.add(m)
    law_list = sorted(laws)
    # patch delivery evidence
    has_patch = bool(PATCH_MARKERS.search(txt))
    n_comments = len(comments.get(str(n), []))
    last_c = comments.get(str(n), [None])[-1] if n_comments else None

    # mainline presence per law (cached across issues)
    law_presence = {}
    for lid in law_list:
        if lid not in law_mainline_cache:
            law_mainline_cache[lid] = mainline_grep(lid)
        law_presence[lid] = law_mainline_cache[lid]

    records.append({
        'coder': coder,
        'issue': n,
        'title': (i.get('title') or '')[:150],
        'state': i['state'],
        'created_at': i['created_at'],
        'updated_at': i['updated_at'],
        'last_comment_at': last_c['created_at'] if last_c else None,
        'last_comment_user': last_c['user'] if last_c else None,
        'comments_fetched': n_comments,
        'patch_delivery_evidence': has_patch,
        'law_ids': law_list,
        'law_mainline_presence': law_presence,
    })

inv = {
    'wave': 'S195 AUDIT',
    'directive': 'MAIN CODER MASTER TASK §2 — machine-readable achievement '
                 'inventory over the priority issue set (§1)',
    'generated_from': {
        'issues_corpus': 'evidence/s195_audit/issues_raw.json (566 issues, '
                         'updated_at DESC)',
        'comments_corpus': 'evidence/s195_audit/comments_raw.json (92 '
                           'priority issues, 480 comments)',
    },
    'mainline': {
        'origin_main_head': '9bc2a11533036ff6f1b8c96ea1d8039ec0af0daa',
        'local_binary_sha16': '1f05270d793a43b5',
        'binary_note': 'local integration line; W18 gates re-verified '
                       'post-wipe (goldens 3/3 ALL HOLD, floor 11/11)',
    },
    'status_vocabulary': ['IMPLEMENTED', 'TESTED', 'OBSERVED', 'TRANSFERRED',
                          'INTEGRATED', 'REGRESSION_VERIFIED', 'PARTIAL',
                          'PENDING', 'BLOCKED', 'SUPERSEDED', 'REJECTED'],
    'status_semantics': 'a tested patch is not automatically integrated; '
                        'presence = law ID found in current source tree; '
                        'evidence = found in evidence JSONs; worklog = found '
                        'in the campaign worklog',
    'records': records,
}
(AUD / 'CONTRIBUTOR_ACHIEVEMENT_INVENTORY.json').write_text(
    json.dumps(inv, indent=1))

# census print
all_laws = sorted({l for r in records for l in r['law_ids']})
present_src = [l for l in all_laws
               if any(r['law_mainline_presence'][l]['src'] for r in records
                      if l in r['law_mainline_presence'])]
print(f"records: {len(records)} issues across coders "
      f"{sorted(set(r['coder'] for r in records))}")
print(f"distinct law IDs discovered: {len(all_laws)}")
print(f"law IDs present in CURRENT SOURCE: {len(present_src)}")
for l in present_src[:40]:
    print('  ', l)
absent = [l for l in all_laws if l not in present_src]
print(f"law IDs NOT in source ({len(absent)}): {absent[:30]}")
