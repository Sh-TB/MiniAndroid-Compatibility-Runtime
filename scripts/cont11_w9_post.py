#!/usr/bin/env python3
"""Post the W9 review comments to GitHub."""
import json, subprocess, sys

BASE = '/home/z/my-project'
REPO = 'Sh-TB/MiniAndroid-Compatibility-Runtime'

def api(endpoint, method='GET', data=None):
    cmd = ['curl', '-s', '-X', method,
           '-H', f'Authorization: Bearer {open("/tmp/.ghtoken").read().strip()}',
           '-H', 'Content-Type: application/json']
    if data:
        cmd += ['-d', json.dumps(data)]
    cmd += [f'https://api.github.com/repos/{REPO}/{endpoint}']
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return json.loads(r.stdout)

def post_comment(issue_num, body):
    r = api(f'issues/{issue_num}/comments', 'POST', {'body': body})
    if 'id' in r:
        print(f'  POSTED #{issue_num}: comment id {r["id"]} -> {r["html_url"]}')
        return True
    else:
        print(f'  FAILED #{issue_num}: {str(r)[:200]}')
        return False

# 1. per-issue comments
with open(f'{BASE}/docs/CONT11_W9_REVIEW_COMMENTS.json') as f:
    C = json.load(f)
ok = 0
for issue, body in C.items():
    num = issue.lstrip('#')
    if post_comment(num, body):
        ok += 1
print(f'per-issue: {ok}/{len(C)} posted')

# 2. master ledger on #380
with open(f'{BASE}/docs/CONT11_W9_MASTER_LEDGER.md') as f:
    master = f.read()
post_comment('380', master)
