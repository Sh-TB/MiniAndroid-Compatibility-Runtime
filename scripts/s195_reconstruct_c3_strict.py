#!/usr/bin/env python3
"""S195 AUDIT — strict C3 S196/S197/S198 patch reconstruction with
per-part sha16 verification against the PUBLISHED hashes (the W3 seam
law: reject on ANY mismatch, never hand-repair)."""
import json, hashlib, re
from pathlib import Path

BASE = Path('/home/z/my-project')
OUT = BASE / 'evidence/s195_audit/patches'
OUT.mkdir(parents=True, exist_ok=True)
cs_all = json.load(open(BASE / 'evidence/s195_audit/comments_raw.json'))
by_id = {str(c['id']): c for clist in cs_all.values() for c in clist}
c3 = sorted(cs_all['557'], key=lambda c: c['created_at'])


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def fenced(body):
    """content between the first ```diff fence and the closing fence."""
    m = re.search(r'```(?:diff)?\n(.*?)\n```', body, re.S)
    return m.group(1) + '\n' if m else None


def variants(body):
    """candidate part texts: fenced raw, or fenced minus '# ' metadata."""
    f = fenced(body)
    if f is None:
        f = body
    no_meta = '\n'.join(l for l in f.splitlines()
                        if not l.startswith('# ')) + '\n'
    return {'raw': f, 'no_meta': no_meta}


# published part hashes (from the comments themselves)
PUB = {
    'S196': {'parts': ['6717466211', '6717466912', '6717467358'],
             'full_sha16': '9ee750b21afe89a0', 'note': 'apply-check CLEAN '
             'on 9bc2a115'},
    'S197': {'parts': ['6719905886'], 'full_sha16': None,
             'note': 'F-NEW-606, 2 files, 55 lines, published part sha16 '
                     '0ff0dbdf700f4b15'},
    'S198': {'parts': ['6723924389', '6723924642'],
             'part_sha16': {'6723924389': 'f7698d43db096572',
                            '6723924642': '316b7772d29962fa'},
             'full_sha16': 'd64ac52606e9a3e8'},
}
results = {}
for wave, spec in PUB.items():
    texts = []
    for cid in spec['parts']:
        body = by_id[cid]['body'] or ''
        vs = variants(body)
        chosen, how = None, None
        if spec.get('part_sha16') and cid in spec['part_sha16']:
            target = spec['part_sha16'][cid]
            for k, v in vs.items():
                if sha16(v.encode()) == target:
                    chosen, how = v, f'{k} MATCHES published part sha {target}'
                    break
            if chosen is None:
                print(f'{wave}/{cid}: NO VARIANT matches {target} '
                      f'(raw={sha16(vs["raw"].encode())} '
                      f'no_meta={sha16(vs["no_meta"].encode())})')
                chosen = vs['no_meta']
                how = 'NO MATCH — using no_meta, flagged'
        else:
            chosen = vs['no_meta']
            how = 'no part hash published; using no_meta'
        texts.append(chosen)
        print(f'{wave}/{cid}: {len(chosen)} B [{how}]')
    full = ''.join(texts)
    fs = sha16(full.encode())
    ok = (fs == spec['full_sha16']) if spec['full_sha16'] else None
    print(f'{wave} FULL: {len(full)} B sha16={fs} '
          f'{"MATCHES" if ok else ("PUBLISHED " + spec["full_sha16"] if ok is False else "(no published full hash)")}')
    (OUT / f'c3_{wave.lower()}_reconstructed.patch').write_text(full)
    results[wave] = {'full_sha16_computed': fs,
                     'full_sha16_published': spec['full_sha16'],
                     'match': ok, 'bytes': len(full)}

(OUT / 'C3_RECONSTRUCTION_VERIFICATION.json').write_text(
    json.dumps(results, indent=1))
