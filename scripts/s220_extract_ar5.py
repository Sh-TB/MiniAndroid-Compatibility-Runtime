#!/usr/bin/env python3
"""S220: extract A-R5 patch parts 1-3 from issue #584 comments into .diff files."""
import json, re, os

d = json.load(open('/home/z/my-project/forensic_data/s220_issues.json'))
comments = sorted(d['584']['comments'], key=lambda c: c['created_at'])
outdir = '/home/z/my-project/forensic_data/ar5_patch'
os.makedirs(outdir, exist_ok=True)

total_extracted = 0
for c in comments:
    body = c['body']
    # find fenced diff blocks
    blocks = re.findall(r'```(?:diff)?\n(.*?)```', body, re.DOTALL)
    for b in blocks:
        if not b.strip().startswith('diff --git'):
            continue
        total_extracted += 1
        # which part?
        m = re.search(r'PATCH PART (\d)/3', body)
        part = m.group(1) if m else '?'
        fn = os.path.join(outdir, f'part{part}.diff')
        # append if part file exists (multiple blocks per comment)
        mode = 'a' if os.path.exists(fn) else 'w'
        with open(fn, mode) as f:
            f.write(b if b.endswith('\n') else b + '\n')
        print(f"comment {c['id']} part {part}: {len(b)} chars -> {fn} (files: {b.count('diff --git')})")

print(f"total diff blocks: {total_extracted}")
for fn in sorted(os.listdir(outdir)):
    p = os.path.join(outdir, fn)
    n = open(p).read().count('diff --git')
    print(f"{fn}: {os.path.getsize(p)} bytes, {n} file headers")
