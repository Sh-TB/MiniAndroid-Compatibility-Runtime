#!/usr/bin/env python3
"""
EXP-059: Dump the View hierarchy from the runtime's heap state.

Reads the runtime's stderr.log and the application_runtime.json, then
extracts all heap objects that look like Views (subclasses of View,
ViewGroup, etc.). Produces a JSON tree showing the View hierarchy.

This is a post-processing step — the runtime itself doesn't need to
be modified.
"""
import json, os, sys, re

LOG_DIR = sys.argv[1] if len(sys.argv) > 1 else \
    '/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/run/exp059_lifecycle'

stderr_path = os.path.join(LOG_DIR, 'stderr.log')
if not os.path.exists(stderr_path):
    print(f'Log file not found: {stderr_path}', file=sys.stderr)
    sys.exit(1)

with open(stderr_path) as f:
    log_lines = f.readlines()

# Collect all [METHOD-IN] entries to see what View classes were instantiated
view_classes = set()
view_creations = []
for line in log_lines:
    m = re.search(r'\[METHOD-IN\]\s+(L[\w/$]+;)\.<init>\s+\(bytecode_size=(\d+)\)', line)
    if m:
        cls = m.group(1)
        size = int(m.group(2))
        view_creations.append({'class': cls, 'bytecode_size': size})
        # Heuristic: any class that extends View, ViewGroup, or has 'View'/'Layout' in name
        if any(k in cls for k in ('View', 'Layout', 'Pager', 'Button', 'Text', 'Image',
                                   'Frame', 'Scroll', 'List', 'Adapter', 'Drawable',
                                   'Fragment', 'Activity')):
            view_classes.add(cls)

# Count creations per class
from collections import Counter
counter = Counter(c['class'] for c in view_creations)

# Output
result = {
    'log_dir': LOG_DIR,
    'total_init_calls': len(view_creations),
    'unique_classes_initialized': len(counter),
    'view_like_classes': sorted(view_classes),
    'top_classes': [
        {'class': cls, 'count': count}
        for cls, count in counter.most_common(30)
    ],
}

out_path = os.path.join(LOG_DIR, 'login_view_tree.json')
with open(out_path, 'w') as f:
    json.dump(result, f, indent=2)

print(f'View tree written to: {out_path}')
print(f'Total <init> calls: {result["total_init_calls"]}')
print(f'Unique classes: {result["unique_classes_initialized"]}')
print(f'View-like classes: {len(result["view_like_classes"])}')
print()
print('Top 20 classes by <init> count:')
for item in result['top_classes'][:20]:
    print(f'  {item["count"]:4d}  {item["class"]}')
print()
print('View-like classes:')
for cls in sorted(result['view_like_classes']):
    print(f'  {cls}')
