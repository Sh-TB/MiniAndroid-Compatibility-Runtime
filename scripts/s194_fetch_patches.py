#!/usr/bin/env python3
"""S194 intake: fetch the contributor patch comments (issues #519/#557/#561/#562),
extract the ```diff blocks, reconstruct the full patch files, git apply --check
each on the current main (cbc9058e)."""
import json, re, subprocess, os
from pathlib import Path

BASE = Path('/home/z/my-project')
OUT = BASE / 'evidence/s194_intake/patches'
OUT.mkdir(parents=True, exist_ok=True)

# (issue, [(comment_id, part_label)])
SETS = {
    'c8_s192_waves89_cumulative': (519, [6710219759, 6710220639, 6710221868, 6710223021, 6710224109]),
    'c8_s193_wave10': (519, [6711266453, 6711266717]),
    'c3_s191_gmdice': (561, [6704878786]),
    'c4_w15_laws': (562, [6708453756, 6708454699, 6708455783, 6708456694]),
    'c3_s189_a24': (557, [6707480718, 6707480969]),
    'c8_s191_wave8_standalone': (519, [6708827140, 6708827473, 6708827766]),
}

def fetch(issue):
    cache = BASE / f'/tmp/issue_{issue}.json'
    if cache.exists():
        return json.load(open(cache))
    TOKEN = subprocess.run(['git', 'credential', 'fill'],
                           input='protocol=https\nhost=github.com\n',
                           capture_output=True, text=True).stdout
    TOKEN = [l.split('=', 1)[1] for l in TOKEN.splitlines() if l.startswith('password=')][0]
    r = subprocess.run(['curl', '-s', '-H', f'Authorization: token {TOKEN}',
                        f'https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{issue}/comments?per_page=100'],
                       capture_output=True, text=True, timeout=60)
    data = json.loads(r.stdout)
    json.dump(data, open(cache, 'w'))
    return data

results = {}
for name, (issue, ids) in SETS.items():
    cs = {c['id']: c['body'] for c in fetch(issue)}
    diffs = []
    for cid in ids:
        body = cs.get(cid, '')
        # extract the ```diff fenced block (or a bare diff after a ```diff marker)
        m = re.search(r'```diff\s*\n(.*)', body, re.S)
        if m:
            block = m.group(1)
            # close fence at the LAST ``` or strip a trailing fence
            end = block.find('\n```')
            if end != -1:
                block = block[:end]
            diffs.append(block)
        else:
            diffs.append(None)
    parts_ok = [d for d in diffs if d]
    results[name] = {'parts': len(ids), 'fetched': len(parts_ok), 'bytes': sum(len(d) for d in parts_ok)}
    if parts_ok:
        full = '\n'.join(parts_ok)
        p = OUT / f'{name}.patch'
        p.write_text(full)
        # git apply --check
        r = subprocess.run(['git', 'apply', '--check', '--ignore-whitespace', str(p)],
                           cwd=BASE, capture_output=True, text=True)
        results[name]['apply_check_rc'] = r.returncode
        results[name]['apply_check_err'] = (r.stderr or '')[:400]
print(json.dumps(results, indent=1))
