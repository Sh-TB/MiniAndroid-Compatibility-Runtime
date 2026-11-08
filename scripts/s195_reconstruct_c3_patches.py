#!/usr/bin/env python3
"""S195 AUDIT — reconstruct the Coder-3 S196/S197/S198 wave patches from
#557 comment bodies (MAIN CODER MASTER TASK §6: reconstruct, hash, record
base SHA). Saves evidence/s195_audit/patches/c3_s19{6,7,8}*.patch"""
import json, hashlib, re
from pathlib import Path

BASE = Path('/home/z/my-project')
OUT = BASE / 'evidence/s195_audit/patches'
OUT.mkdir(parents=True, exist_ok=True)
cs = json.load(open(BASE / 'evidence/s195_audit/comments_raw.json'))


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def extract_diffs(body):
    """pull the diff text out of a comment body: lines from 'diff --git'
    to the end of that file's hunk block. Handles ``` fences."""
    lines = body.splitlines()
    out, cur = [], None
    for ln in lines:
        if ln.strip().startswith('```'):
            continue
        if ln.startswith('diff --git') or ln.startswith('--- a/') \
           or ln.startswith('+++ b/') or ln.startswith('@@') \
           or ln.startswith('+') or ln.startswith('-') or ln.startswith(' '):
            if ln.startswith('--- ') and not ln.startswith('--- a/'):
                continue
            out.append(ln)
    return '\n'.join(out) + '\n'


# ── S196_PORTED: comments at 04:56:14 (part1), 04:56:19 (part2),
#    04:56:22 (part3/3) ─────────────────────────────────────────────────
c3_557 = cs['557']
s196_parts = []
for c in c3_557:
    b = c['body'] or ''
    if 'S196_PORTED' in b and 'diff --git' in b:
        s196_parts.append((c['id'], c['created_at'], b))
print('S196 candidate parts:', [(p[0], p[1], len(p[2])) for p in s196_parts])

# part3 comment explicitly labels part3/3; the two big ones are 1 and 2 by
# order (04:56:14 = part 1, 04:56:19 = part 2)
s196_text = ''
for cid, cat, b in s196_parts:
    seg = extract_diffs(b)
    s196_text += seg
(OUT / 'c3_s196_ported_raw_concat.patch').write_text(s196_text)
print('S196 concat:', len(s196_text), 'bytes, sha16', sha16(s196_text.encode()))

# ── S197 §8: comment at 09:38:26 (F-NEW-606 ancestry) ────────────────
s197_text = None
for c in cs['557']:
    b = c['body'] or ''
    if 'F-NEW-606' in b and 'diff --git' in b and c['created_at'].startswith('2026-11-08T09:38:26'):
        s197_text = extract_diffs(b)
if s197_text:
    (OUT / 'c3_s197_f606_ancestry.patch').write_text(s197_text)
    print('S197:', len(s197_text), 'bytes, sha16', sha16(s197_text.encode()))
else:
    print('S197 patch NOT found by marker')

# ── S198 §8: part 1/2 at 16:19:46 + part 2/2 at 16:19:48 ─────────────
s198_parts = []
for c in cs['557']:
    b = c['body'] or ''
    if c['created_at'].startswith('2026-11-08T16:19') and 'diff --git' in b:
        s198_parts.append((c['id'], c['created_at'], b))
print('S198 candidate parts:', [(p[0], p[1], len(p[2])) for p in s198_parts])
s198_text = ''
for cid, cat, b in sorted(s198_parts, key=lambda x: x[1]):
    s198_text += extract_diffs(b)
(OUT / 'c3_s198_gles_raster_raw_concat.patch').write_text(s198_text)
print('S198 concat:', len(s198_text), 'bytes, sha16', sha16(s198_text.encode()))

# quick sanity: list the files each patch touches
for name, txt in [('S196', s196_text), ('S197', s197_text or ''),
                  ('S198', s198_text)]:
    files = sorted(set(re.findall(r'diff --git a/(\S+) b/', txt)))
    print(f'{name} touches {len(files)} files:', files[:10])
