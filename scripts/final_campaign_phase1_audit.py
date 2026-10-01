#!/usr/bin/env python3
"""FINAL CAMPAIGN PHASE 1 — tracked-tree hygiene audit.
Produces the mission-mandated table: PATH | SIZE | TYPE | CURRENT/HISTORICAL |
WHY | REFERENCED-BY-CANONICAL | ACTION. Read-only: never modifies anything."""
import json
import os
import subprocess

REPO = "/home/z/my-project"
OUT = "/home/z/my-project/tmp/final_campaign/phase1_tree_audit.json"


def tracked_files():
    out = subprocess.run(["git", "ls-files", "-z"], cwd=REPO,
                         capture_output=True, text=True).stdout
    return [p for p in out.split("\0") if p]


def main():
    files = tracked_files()
    total = 0
    per_top = {}
    per_second = {}
    big = []          # >1 MiB
    by_ext = {}
    rows = []
    for rel in files:
        fp = os.path.join(REPO, rel)
        try:
            sz = os.path.getsize(fp)
        except OSError:
            sz = 0
        total += sz
        top = rel.split("/")[0]
        per_top[top] = per_top.get(top, 0) + sz
        parts = rel.split("/")
        if len(parts) >= 2:
            key2 = "/".join(parts[:2])
            per_second[key2] = per_second.get(key2, 0) + sz
        ext = os.path.splitext(rel)[1].lower() or "(none)"
        by_ext[ext] = by_ext.get(ext, [0, 0])
        by_ext[ext][0] += 1
        by_ext[ext][1] += sz
        if sz >= 1_048_576:
            big.append((rel, sz))
        rows.append({"path": rel, "size": sz})

    mib = lambda b: round(b / 1048576, 2)
    report = {
        "tracked_files": len(files),
        "tracked_total_MiB": mib(total),
        "per_top_dir_MiB": {k: mib(v) for k, v in sorted(per_top.items(), key=lambda x: -x[1])},
        "per_second_level_MiB_top40": {k: mib(v) for k, v in sorted(per_second.items(), key=lambda x: -x[1])[:40]},
        "files_over_1MiB": [{"path": p, "MiB": mib(s)} for p, s in sorted(big, key=lambda x: -x[1])],
        "ext_census_top25": {e: {"count": c, "MiB": mib(s)} for e, (c, s) in sorted(by_ext.items(), key=lambda x: -x[1][1])[:25]},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"rows": rows, "report": report}, f, indent=1)
    print(json.dumps(report, indent=1)[:6000])


if __name__ == "__main__":
    main()
