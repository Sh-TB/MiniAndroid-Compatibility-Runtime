#!/usr/bin/env python3
"""S128 Phase-0 audit: dump the FULL state needed to build the canonical MASTER WORKLIST.
Reads: canonical registries, root_registry.json (writable store), worklog, docs, source scans.
Writes: /home/z/my-project/audit/s128_state_dump.json + human-readable summary to stdout."""
import json, os, re, glob, collections, datetime

ROOT = '/home/z/my-project'
OUT = os.path.join(ROOT, 'audit')
os.makedirs(OUT, exist_ok=True)

state = {}

# ---------- 1. capability registry ----------
caps = json.load(open(f'{ROOT}/canonical/capability_registry.json'))['capabilities']
print(f'== CAPABILITIES: {len(caps)}')
by_status = collections.Counter(c.get('status','?') for c in caps)
print('  status:', dict(by_status))
pend = [c for c in caps if c.get('status') == 'PENDING']
print(f'  PENDING ({len(pend)}):')
for c in pend:
    print(f"    {c.get('id')} [{c.get('layer','?')}] {c.get('name','?')}")
state['capabilities'] = caps

# ---------- 2. root registry (writable store) ----------
rr_path = None
for cand in [f'{ROOT}/root_registry.json', f'{ROOT}/canonical/root_registry.json',
             f'{ROOT}/docs/root_registry.json']:
    if os.path.exists(cand):
        rr_path = cand; break
if not rr_path:
    hits = glob.glob(f'{ROOT}/**/root_registry.json', recursive=True)
    rr_path = hits[0] if hits else None
print(f'== ROOT REGISTRY at {rr_path}')
if rr_path:
    rr = json.load(open(rr_path))
    roots = rr['roots'] if isinstance(rr, dict) and 'roots' in rr else rr
    print(f'  total roots: {len(roots)}')
    st = collections.Counter(r.get('status','?') for r in roots)
    print('  status counts:', dict(st.most_common()))
    # open roots = anything not closed
    OPEN_ST = {'PARTIAL','UNPROVEN','RESEARCHED-NOT-IMPLEMENTED','IN_PROGRESS','OPEN','DISCOVERED','ANALYZING','TODO'}
    open_roots = [r for r in roots if r.get('status','') in OPEN_ST]
    print(f'  OPEN roots: {len(open_roots)}')
    for r in open_roots:
        print(f"    {r.get('id')} [{r.get('status')}] {str(r.get('title',r.get('summary','')))[:110]}")
    state['roots'] = roots
    state['root_registry_path'] = rr_path

# ---------- 3. app registry ----------
apps = json.load(open(f'{ROOT}/canonical/app_registry.json'))
alist = apps.get('apps', apps)
print(f'== APPS: {len(alist)}')
for a in alist:
    cps = a.get('checkpoints', {})
    cp_s = ' '.join(f"{k}={v}" for k,v in sorted(cps.items())) if isinstance(cps, dict) else str(cps)
    print(f"  {a.get('id')} {a.get('name','?')[:34]:34s} status={a.get('status','?'):10s} {cp_s[:130]}")
state['apps'] = alist

# ---------- 4. game registry ----------
games = json.load(open(f'{ROOT}/canonical/game_registry.json'))
glist = games.get('games', games)
print(f'== GAMES: {len(glist)}')
gst = collections.Counter(g.get('status','?') for g in glist)
print('  status counts:', dict(gst.most_common()))
for g in glist:
    if g.get('status') in ('PARTIAL','BLOCKED','VERIFIED'):
        cps = g.get('checkpoints', {})
        cp_s = ' '.join(f"{k}={v}" for k,v in sorted(cps.items())) if isinstance(cps, dict) else str(cps)
        print(f"  {g.get('id')} {g.get('name','?')[:30]:30s} status={g.get('status'):10s} {cp_s[:120]}")
state['games'] = glist

# ---------- 5. keyword scan over source + docs ----------
KW = ['TODO','FIXME','HACK','STUB','PLACEHOLDER','HARDCODED','not implemented','NotImplemented',
      'PARTIAL','FOLLOW-UP','NEXT STEP','unimplemented','for now','simplified','approximat']
scan_dirs = [f'{ROOT}/miniandroid/src', f'{ROOT}/scripts', f'{ROOT}/docs']
kw_hits = collections.defaultdict(list)
for d in scan_dirs:
    for path in glob.glob(d + '/**/*', recursive=True):
        if os.path.isfile(path) and path.endswith(('.cpp','.h','.hpp','.py','.md','.java','.kt')) and os.path.getsize(path) < 800000:
            try: txt = open(path, errors='ignore').read()
            except Exception: continue
            for kw in KW:
                for m in re.finditer(re.escape(kw), txt, re.IGNORECASE if kw.islower() else 0):
                    line_no = txt[:m.start()].count('\n') + 1
                    line = txt.splitlines()[line_no-1].strip()[:120]
                    kw_hits[kw].append({'file': os.path.relpath(path, ROOT), 'line': line_no, 'text': line})
print('== KEYWORD SCAN (source+scripts+docs):')
for kw, hits in sorted(kw_hits.items(), key=lambda x:-len(x[1])):
    print(f'  {kw}: {len(hits)}')
    for h in hits[:12]:
        print(f"     {h['file']}:{h['line']}  {h['text']}")
state['keyword_scan'] = {k: v for k, v in kw_hits.items()}

# ---------- 6. worklog tail (last 3 entries headers) ----------
wl = open(f'{ROOT}/worklog.md').read()
entries = wl.split('\n---\n')
print(f'== WORKLOG: {len(entries)} entries; last 3 session headers:')
for e in entries[-4:]:
    for line in e.splitlines()[:6]:
        if line.strip(): print('   ', line[:130])

json.dump(state, open(f'{OUT}/s128_state_dump.json','w'), indent=1, default=str)
print(f"\nDUMPED -> {OUT}/s128_state_dump.json")
