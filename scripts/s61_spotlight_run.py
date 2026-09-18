#!/usr/bin/env python3
"""S61 Runtime Spotlight Corpus — execution sweep.

Runs every manifest APK through the MiniAndroid runtime with a bounded
budget, then classifies the achieved L-level from the run artifacts:

  L0  APK/container parsed            (report.md exists)
  L1  DEX/class loading               (dex loaded, no fatal parse crash)
  L2  Activity/lifecycle dispatched   (onCreate/onResume in trace)
  L3  runtime objects/ViewTree        (render walk visited >=2 nodes)
  L4  resource + geometry             (inflated views with real measured bounds)
  L5  drawing/framebuffer             (screenshot with non-background pixels)
  L6/L7  input→state                  (follow-up interactive stage; not in base sweep)

Evidence per app: screenshot.png + SHA256 + non-white pixel count + report.
Results append to docs/corpus/spotlight_results.json (canonical input for
the coverage matrix).

Usage: python3 scripts/s61_spotlight_run.py [--budget 75] [--limit N] [--only pkg]
"""
import hashlib
import json
import os
import subprocess
import sys
import time

REPO = '/home/z/my-project'
BIN = os.path.join(REPO, 'miniandroid', 'build', 'miniandroid')
MANIFEST = os.path.join(REPO, 'docs', 'corpus', 'spotlight_manifest.json')
RESULTS = os.path.join(REPO, 'docs', 'corpus', 'spotlight_results.json')
RUNROOT = os.path.join(REPO, 'run', 's61_spotlight')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def classify(run_dir, stderr_path, report_path):
    """Evidence-driven L-level classification (no PASS theater)."""
    lvl = 0
    evidence = {}
    stderr = ''
    if os.path.exists(stderr_path):
        with open(stderr_path, 'r', errors='replace') as f:
            stderr = f.read()
    report = ''
    if os.path.exists(report_path):
        with open(report_path, 'r', errors='replace') as f:
            report = f.read()

    # L0: report exists (the runtime completed its pipeline)
    if os.path.exists(report_path):
        lvl = max(lvl, 0)

    # L1: DEX parsed — look for class loading evidence or absence of
    # catastrophic dex failure
    dex_fail = ('Failed to parse DEX' in stderr) or ('invalid dex' in stderr.lower())
    if not dex_fail:
        lvl = max(lvl, 1)

    # L2: lifecycle reached onCreate/onResume. Evidence sources: the
    # stderr dispatch lines AND lifecycle_trace.json (final_state +
    # transitions are engine-recorded artifacts).
    final_state = None
    try:
        with open(os.path.join(run_dir, 'lifecycle_trace.json')) as f:
            lt = json.load(f)
        final_state = lt.get('final_state')
        transitions = lt.get('transitions', [])
        reasons = ' '.join(str(t.get('reason', '')) for t in transitions)
        if final_state in ('RESUMED', 'PAUSED', 'STOPPED') or transitions:
            lvl = max(lvl, 2)
            evidence['lifecycle_final'] = final_state
            evidence['lifecycle_transitions'] = len(transitions)
        _ = reasons
    except Exception:
        pass
    if 'onResume dispatched' in stderr or 'onResume' in stderr:
        lvl = max(lvl, 2)
    elif 'onCreate' in stderr:
        lvl = max(lvl, 2)

    # L3: ViewTree walk visited nodes
    import re
    nodes = re.findall(r'\[EXP092-RENDER\] node=(\d+)', stderr)
    evidence['render_nodes'] = len(nodes)
    if len(set(nodes)) >= 2:
        lvl = max(lvl, 3)

    # L4: real measured geometry (a node with nonzero measured size)
    geo = re.findall(r'\[EXP092-RENDER\].*size=\((\d+)x(\d+)\)', stderr)
    real_geo = [(int(w), int(h)) for w, h in geo if int(w) > 40 and int(h) > 40]
    evidence['geometric_nodes'] = len(real_geo)
    if real_geo:
        lvl = max(lvl, 4)

    # L5: framebuffer content
    m = re.search(r'\[EXP092-COPY\] fb has (\d+) non-white pixels out of (\d+)', stderr)
    if m:
        nonwhite = int(m.group(1))
        evidence['nonwhite_pixels'] = nonwhite
        evidence['total_pixels'] = int(m.group(2))
        if nonwhite > 0:
            lvl = max(lvl, 5)

    # errors + screenshot hash
    merr = re.search(r'Errors.*?(\d+)', report)
    evidence['errors'] = int(merr.group(1)) if merr else None
    shot = os.path.join(run_dir, 'screenshot.png')
    if os.path.exists(shot):
        evidence['screenshot_sha256'] = sha256(shot)
        evidence['screenshot_bytes'] = os.path.getsize(shot)
    return lvl, evidence, stderr


def run_one(entry, budget):
    pkg = entry['package']
    apk = os.path.join(REPO, 'apk_cache', 'spotlight', pkg + '.apk')
    if not os.path.exists(apk):
        return None
    out = os.path.join(RUNROOT, pkg.replace('/', '_'))
    os.makedirs(out, exist_ok=True)
    err_path = os.path.join(out, 'stderr.log')
    if os.path.exists(os.path.join(out, 'classified.json')):
        with open(os.path.join(out, 'classified.json')) as f:
            return json.load(f)  # resume support
    cmd = [BIN, 'run', apk, '-o', out, '--execution-mode', 'real-dalvik',
           '--max-seconds', str(budget)]
    t0 = time.time()
    try:
        with open(err_path, 'w') as errf:
            subprocess.run(cmd, stdout=subprocess.DEVNULL,
                           stderr=errf, timeout=budget + 45)
    except subprocess.TimeoutExpired:
        pass
    wall = time.time() - t0
    lvl, ev, _ = classify(out, err_path, os.path.join(out, 'report.md'))
    rec = {
        'package': pkg,
        'version_code': entry.get('version_code'),
        'capabilities': entry.get('capabilities', []),
        'sha256': entry.get('sha256'),
        'run_dir': os.path.relpath(out, REPO),
        'wall_seconds': round(wall, 1),
        'l_level': lvl,
        **ev,
    }
    with open(os.path.join(out, 'classified.json'), 'w') as f:
        json.dump(rec, f, indent=1)
    return rec


def main():
    budget = 75
    limit = 999
    only = None
    args = sys.argv[1:]
    if '--budget' in args:
        budget = int(args[args.index('--budget') + 1])
    if '--limit' in args:
        limit = int(args[args.index('--limit') + 1])
    if '--only' in args:
        only = args[args.index('--only') + 1]

    manifest = json.load(open(MANIFEST))
    results = {'schema': 'spotlight-results-v1', 'budget_seconds': budget,
               'apps': []}
    if os.path.exists(RESULTS):
        try:
            old = json.load(open(RESULTS))
            results['apps'] = old.get('apps', [])
        except Exception:
            pass
    done = {r['package'] for r in results['apps']}

    n = 0
    for entry in manifest['apps']:
        pkg = entry['package']
        if only and only not in pkg:
            continue
        if pkg in done:
            continue
        if n >= limit:
            break
        n += 1
        rec = run_one(entry, budget)
        if rec is None:
            continue
        results['apps'] = [r for r in results['apps'] if r['package'] != pkg]
        results['apps'].append(rec)
        print(f"L{rec['l_level']}  {pkg}  "
              f"nodes={rec.get('render_nodes', 0)} "
              f"px={rec.get('nonwhite_pixels', 0)} "
              f"err={rec.get('errors')} wall={rec['wall_seconds']}s",
              flush=True)
        with open(RESULTS, 'w') as f:
            json.dump(results, f, indent=1)
    # summary
    lvls = {}
    for r in results['apps']:
        lvls[r['l_level']] = lvls.get(r['l_level'], 0) + 1
    print('\nL-level distribution:', dict(sorted(lvls.items())))


if __name__ == '__main__':
    main()
