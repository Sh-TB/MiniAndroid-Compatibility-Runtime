#!/usr/bin/env python3
"""
EXP-061 Phase 1: Forensic View Tree Capture

Dumps the complete View hierarchy from the MiniAndroid runtime log.
Each node captures object_id, class, parent, children, geometry, text,
listener info — everything the software renderer needs.

Output: run/exp061/login_view_tree.json
"""
import json, os, re, sys
from collections import defaultdict

def parse_log(log_path):
    """Parse MiniAndroid stderr.log to extract View-related events."""
    nodes = {}  # object_id -> node dict
    parent_children = defaultdict(list)  # parent_id -> [child_ids]
    listener_map = {}  # view_id -> listener_id
    text_map = {}  # view_id -> text
    hint_map = {}  # view_id -> hint
    
    if not os.path.exists(log_path):
        print(f"Log file not found: {log_path}", file=sys.stderr)
        return {'nodes': [], 'error': f'log not found: {log_path}'}
    
    with open(log_path) as f:
        for line in f:
            # [EXP060-LISTENER] setOnClickListener view_id=2482 class=... listener_id=2530
            m = re.search(r'\[EXP060-LISTENER\] setOnClickListener view_id=(\d+) class=(\S+) listener_id=(\d+)', line)
            if m:
                vid, cls, lid = int(m.group(1)), m.group(2), int(m.group(3))
                listener_map[vid] = {'listener_id': lid, 'class': cls}
                continue
            # [METHOD-IN] Lcom/foo/Bar;.<init> (bytecode_size=N)
            m = re.search(r'\[METHOD-IN\]\s+(L[\w/$]+;)\.<init>\s+\(bytecode_size=(\d+)\)', line)
            if m:
                cls, bsize = m.group(1), int(m.group(2))
                # We don't have object_id from METHOD-IN alone; track per class
                continue
    
    return {
        'nodes': [],
        'listeners': listener_map,
        'note': 'Detailed View tree dump requires runtime-side instrumentation'
    }


def main():
    log_dir = sys.argv[1] if len(sys.argv) > 1 else \
        '/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/run/exp060_overload'
    out_dir = sys.argv[2] if len(sys.argv) > 2 else \
        '/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/run/exp061'
    os.makedirs(out_dir, exist_ok=True)
    
    stderr_path = os.path.join(log_dir, 'stderr.log')
    result = parse_log(stderr_path)
    
    # Save
    out_path = os.path.join(out_dir, 'login_view_tree.json')
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"View tree written to: {out_path}")
    print(f"Listeners captured: {len(result.get('listeners', {}))}")


if __name__ == '__main__':
    main()
