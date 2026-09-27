#!/usr/bin/env python3
"""S112: fetch tickets #353/#354/#355 + comments; dump to tmp/; print digest."""
import json, os, re, urllib.request

TOKEN = open('/tmp/.gh_token').read().strip()
REPO = 'Sh-TB/MiniAndroid-Compatibility-Runtime'
OUT = '/home/z/my-project/tmp'
os.makedirs(OUT, exist_ok=True)

def api(path):
    req = urllib.request.Request(f'https://api.github.com{path}',
        headers={'Authorization': f'Bearer {TOKEN}', 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

digest = []
for n in (353, 354, 355):
    iss = api(f'/repos/{REPO}/issues/{n}')
    cmts = api(f'/repos/{REPO}/issues/{n}/comments')
    json.dump({'issue': iss, 'comments': cmts}, open(f'{OUT}/ticket_{n}.json', 'w'), indent=1)
    body = iss['body'] or ''
    imgs = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', body)
    digest.append(f"=== #{n} [{iss['title']}] state={iss['state']} body={len(body)}ch images={len(imgs)} comments={len(cmts)}")
    # text-only digest of body (strip image lines)
    txt = re.sub(r'!\[[^\]]*\]\([^)]*\)', '[IMG]', body)
    txt = re.sub(r'<img[^>]*>', '[IMGHTML]', txt)
    digest.append(txt[:2500])
    for c in cmts:
        ct = re.sub(r'!\[[^\]]*\]\([^)]*\)', '[IMG]', c['body'] or '')
        ct = re.sub(r'<img[^>]*>', '[IMGHTML]', ct)
        digest.append(f"  --- comment {c['id']} by {c['user']['login']} ({len(c['body'] or '')}ch): {ct[:600]}")
    digest.append('')

print('\n'.join(digest))
