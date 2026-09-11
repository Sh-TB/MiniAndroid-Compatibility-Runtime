"""Symbol index probe (brief §8/§16): fast C++ symbol discovery.
grep result != proof — DISCOVERY ACCELERATOR only."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))               # <repo>/tools/verify/probes
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))  # repo root
SRC = os.path.join(REPO, "miniandroid", "src")
def run():
    idx = []
    pat = re.compile(r"^(?:[\w:<>,&*\s]+?)\b(\w+)\s*\([^;{}]*\)\s*(?:const\s*)?\{")
    for root, _, files in os.walk(SRC):
        for fn in files:
            if not fn.endswith((".cpp", ".h")):
                continue
            p = os.path.join(root, fn)
            try:
                for i, line in enumerate(open(p, errors="replace"), 1):
                    m = pat.match(line)
                    if m:
                        idx.append({"symbol": m.group(1), "file": os.path.relpath(p, SRC),
                                    "line": i})
            except OSError:
                continue
    return {"count": len(idx), "sample": idx[:8]}
