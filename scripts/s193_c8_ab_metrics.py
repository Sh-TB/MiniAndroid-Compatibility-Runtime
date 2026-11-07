#!/usr/bin/env python3
"""S193 [C8] A/B metric extraction: api_trace.json calls minus engine-session
bookkeeping rows + UNCAUGHT count — the wave-9 A/B metric shape."""
import json
from pathlib import Path

RUNS = Path('/home/z/my-project/work/miniandroid/evidence/s193_c8/ab_runs')
W9 = {"eu.veldsoft.free.klondike": "494/33", "stack.tower3d": "9214/63",
      "dubrowgn.microtimer": "1052/19", "eu.veldsoft.tri.peaks": "19/2"}

rows = []
for rj in sorted(RUNS.glob('run_*/api_trace.json')):
    pkg = rj.parent.name[4:]
    d = json.loads(rj.read_text())
    calls = d.get('calls', [])
    # Wave-9 counted API-surface rows (the per-call trace), which excludes
    # the TraceEngine session bookkeeping rows.
    api = [c for c in calls
           if c.get('class') != 'TraceEngine' and c.get('category') != 'SYSTEM']
    console = RUNS / (rj.parent.name + '.err')
    uncaught = console.read_text(errors='replace').count('UNCAUGHT') \
        if console.exists() else -1
    rows.append({"pkg": pkg, "api_rows": len(api),
                 "total_trace_rows": len(calls), "uncaught": uncaught,
                 "wave9_metric": W9.get(pkg, "-")})
    print(json.dumps(rows[-1]))
out = RUNS / 'ab_metrics.json'
out.write_text(json.dumps(rows, indent=1))
print("→", out)
