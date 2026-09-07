#!/usr/bin/env python3
"""Dump clickable view bounds from api_trace.json (live view geometry)."""
import json, sys
tr = json.load(open(sys.argv[1]))
seen = []
def emit(e):
    if isinstance(e, dict):
        cls = e.get('class',''); m = e.get('method','')
        if 'setOn' in m or m in ('setOnClickListener','setClickable','setEnabled') or 'layout' in m.lower() or 'setText' in m:
            seen.append((cls, m, [e.get(k) for k in ('view_id','x','y','width','height','left','top','right','bottom') if any(k in e for k in ('view_id','x','y','width','height','left','top','right','bottom'))]))
for e in (tr if isinstance(tr, list) else tr.get('calls', tr.get('trace', []))):
    emit(e)
for s in seen[:60]: print(s)
