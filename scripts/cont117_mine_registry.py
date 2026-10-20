#!/usr/bin/env python3
"""CONT-117 task mining, source 1: registry OPEN gaps -> task clusters."""
import json, re, collections, sys

REG = 'canonical/root_cause_registry.json'
data = json.load(open(REG))
roots = data['roots'] if isinstance(data, dict) and 'roots' in data else data
print(f"total roots: {len(roots)}")

status_counter = collections.Counter()
open_gaps = []
for r in roots:
    st = (r.get('status') or r.get('verdict') or 'UNKNOWN').strip()
    status_counter[st] += 1
    if any(k in st.upper() for k in ('OPEN', 'CONFIRMED', 'PARTIAL', 'CANDIDATE', 'BLOCKED', 'GAP')):
        open_gaps.append(r)

print("\n== status histogram ==")
for st, n in status_counter.most_common():
    print(f"  {n:4d}  {st}")

print(f"\n== open-ish roots: {len(open_gaps)} ==")
# cluster by area keyword
def area_of(r):
    rid = r.get('id', '')
    txt = (r.get('title') or r.get('summary') or r.get('note') or '').lower()
    for kw, area in [
        ('telegram', 'telegram'), ('billing', 'billing/F-NEW-449'), ('protobuf', 'billing/F-NEW-449'),
        ('canvas', 'canvas/compose'), ('compose', 'canvas/compose'), ('webview', 'webview'),
        ('shader', 'shaders/GL'), ('glsl', 'shaders/GL'), ('opengl', 'shaders/GL'), ('egl', 'shaders/GL'),
        ('text', 'text/layout'), ('font', 'text/layout'), ('emoji', 'text/layout'),
        ('recycler', 'recycler/list'), ('viewpager', 'viewpager'), ('motion', 'motion/animator'),
        ('animator', 'motion/animator'), ('notification', 'notification'), ('audio', 'audio/media'),
        ('media', 'audio/media'), ('camera', 'camera'), ('sensor', 'sensors'),
        ('network', 'network/http'), ('http', 'network/http'), ('tls', 'network/http'),
        ('sqlite', 'sqlite/db'), ('database', 'sqlite/db'), ('file', 'fs/io'),
        ('key', 'crypto/keystore'), ('crypto', 'crypto/keystore'), ('signature', 'crypto/keystore'),
        ('input', 'input/touch'), ('touch', 'input/touch'), ('keyboard', 'input/touch'),
        ('surface', 'surfaces'), ('bitmap', 'graphics/bitmap'), ('draw', 'graphics/draw'),
        ('path', 'graphics/draw'), ('paint', 'graphics/draw'), ('color', 'graphics/draw'),
        ('measure', 'view/lifecycle'), ('layout', 'view/lifecycle'), ('inflat', 'view/lifecycle'),
        ('window', 'window/focus'), ('focus', 'window/focus'), ('dialog', 'window/focus'),
        ('intent', 'intent/pm'), ('service', 'services'), ('receiver', 'services'),
        ('handler', 'concurrency'), ('looper', 'concurrency'), ('thread', 'concurrency'),
        ('parcel', 'parcel/serialization'), ('serial', 'parcel/serialization'), ('json', 'parcel/serialization'),
        ('date', 'i18n/format'), ('locale', 'i18n/format'), ('timezone', 'i18n/format'),
    ]:
        if kw in txt:
            return area
    return rid.split('-')[0] if rid else 'misc'

clusters = collections.defaultdict(list)
for r in open_gaps:
    clusters[area_of(r)].append(r.get('id', '?'))

print(f"\n== {len(clusters)} area clusters ==")
for area, ids in sorted(clusters.items(), key=lambda kv: -len(kv[1])):
    print(f"  {len(ids):3d}  {area}: {', '.join(ids[:8])}{' ...' if len(ids) > 8 else ''}")

# dump full open list for ledger build
out = {
    'total_roots': len(roots),
    'status_histogram': dict(status_counter),
    'open_count': len(open_gaps),
    'open_ids': [r.get('id') for r in open_gaps],
    'clusters': {k: v for k, v in clusters.items()},
}
json.dump(out, open('run/c117/registry_mine.json', 'w'), indent=1)
print("\nwrote run/c117/registry_mine.json")
