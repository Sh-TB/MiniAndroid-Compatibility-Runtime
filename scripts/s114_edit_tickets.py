#!/usr/bin/env python3
"""S114 — edit tickets #353/#354/#355 to the user's standard structure:
- remove the Persian TL;DR sections (user: no Persian on GitHub)
- fix broken image markdown
- slim oversized inline image sets (convert secondary images to links)
- keep: fix methodology, metric tables, core proof images, comment credits
"""
import json, re, subprocess, sys

TOKEN = open('/tmp/.gh_token').read().strip()
REPO = 'Sh-TB/MiniAndroid-Compatibility-Runtime'
API = f'https://api.github.com/repos/{REPO}'

def gh(method, url, payload=None):
    cmd = ['curl', '-s', '-X', method, '-H', f'Authorization: token {TOKEN}',
           '-H', 'Content-Type: application/json']
    if payload is not None:
        cmd += ['-d', json.dumps(payload)]
    cmd.append(f'{API}{url}')
    out = subprocess.check_output(cmd)
    return json.loads(out) if out else {}

def strip_persian(body):
    # drop any section whose heading or content block is Persian TL;DR
    # the section starts at a heading containing فارسی/خلاصه and runs to the
    # next heading of the same-or-higher level or EOF
    lines = body.split('\n')
    out, skipping = [], False
    skip_level = 0
    persian_re = re.compile(r'[\u0600-\u06FF]')
    for i, ln in enumerate(lines):
        m = re.match(r'^(#{1,6}) ', ln)
        if m and ('فارسی' in ln or 'خلاصه' in ln):
            skipping = True
            skip_level = len(m.group(1))
            continue
        if skipping and m:
            if len(m.group(1)) <= skip_level:
                skipping = False  # next real section — keep it
        if not skipping:
            out.append(ln)
    return '\n'.join(out).rstrip() + '\n'

def slim_images(body, keep=2):
    """Convert extra inline images past the first `keep` to bare links."""
    img_re = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    seen = 0
    def repl(m):
        nonlocal seen
        seen += 1
        if seen <= keep:
            return m.group(0)
        alt, url = m.group(1), m.group(2)
        return f'[{alt or "evidence"}]({url})'
    return img_re.sub(repl, body)

for n in (353, 354, 355):
    issue = gh('GET', f'/issues/{n}')
    body = issue.get('body') or ''
    orig_len = len(body)
    body2 = strip_persian(body)
    if n == 354:
        body2 = body2.replace('| !otdeath](', '| ![hotdeath](')
        # any other malformed image openers
        body2 = re.sub(r'!\s*([a-z]+)\]\((http[^)]+)\)', r'![\1](\2)', body2)
    body2 = slim_images(body2, keep=2)
    body2 = re.sub(r'\n{3,}', '\n\n', body2)
    gh('PATCH', f'/issues/{n}', {'body': body2})
    print(f'#{n}: {orig_len} -> {len(body2)} chars; persian removed: '
          f'{bool(re.search(r"[\u0600-\u06FF]", body)) and not bool(re.search(r"[\u0600-\u06FF]", body2))}')
