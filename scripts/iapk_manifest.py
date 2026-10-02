#!/usr/bin/env python3
"""iapk_manifest.py — recursive filesystem manifest for the installed-app campaign.

Produces a machine-readable JSON manifest + a concise human-readable tree:
  - recursive walk of the given roots
  - file/dir counts, total bytes, largest files, extension histogram
  - SHA-256 for representative (largest) files
  - per-directory summary for the diff phases (STATE A..E)

Usage:
  python3 scripts/iapk_manifest.py <root1> [root2 ...] --json out.json [--tree out.txt]
  python3 scripts/iapk_manifest.py <root1> <root2> --diff --json diff.json
"""
import hashlib
import json
import os
import sys
from collections import Counter


def sha256_file(path, buf=65536):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(buf)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def walk_root(root):
    """Return (files dict, dirs list, totals dict) for one root tree."""
    files = {}
    dirs = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        rel_dir = os.path.relpath(dirpath, root)
        dirs.append(rel_dir)
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            try:
                st = os.stat(full)
                entry = {
                    "size": st.st_size,
                    "mtime": int(st.st_mtime),
                }
                files[rel] = entry
            except OSError as e:
                files[rel] = {"size": -1, "error": str(e)}
    total_bytes = sum(f["size"] for f in files.values() if f["size"] > 0)
    totals = {
        "root": root,
        "exists": os.path.exists(root),
        "file_count": len(files),
        "dir_count": len(dirs),
        "total_bytes": total_bytes,
    }
    return files, dirs, totals


def ext_histogram(files):
    c = Counter()
    for rel in files:
        _, ext = os.path.splitext(rel)
        c[ext.lower() if ext else "<none>"] += 1
    return dict(c.most_common())


def snapshot(roots, hash_top=8):
    """Full snapshot across several roots (e.g. store root + one package dir)."""
    snap = {"roots": [], "files": {}, "dirs": []}
    for root in roots:
        files, dirs, totals = walk_root(root)
        t = dict(totals)
        t["ext_histogram"] = ext_histogram(files)
        # largest files with SHA-256 of top N (representative integrity)
        big = sorted(
            ((rel, f["size"]) for rel, f in files.items() if f["size"] > 0),
            key=lambda kv: -kv[1])[:hash_top]
        hashes = []
        for rel, size in big:
            full = os.path.join(root, rel)
            h = sha256_file(full)
            hashes.append({"path": rel, "size": size, "sha256": (h[:16] + "…") if h else None})
        t["largest_files"] = hashes
        snap["roots"].append(t)
        for rel, f in files.items():
            snap["files"][os.path.join(root, rel)] = f
        snap["dirs"].extend(os.path.join(root, d) for d in dirs)
    snap["total_files"] = len(snap["files"])
    snap["total_bytes"] = sum(f["size"] for f in snap["files"].values() if f["size"] > 0)
    return snap


def diff_snap(a, b):
    """Diff two snapshots by absolute file path."""
    af, bf = a["files"], b["files"]
    created = sorted(set(bf) - set(af))
    deleted = sorted(set(af) - set(bf))
    modified = sorted(
        p for p in set(af) & set(bf)
        if af[p].get("size") != bf[p].get("size") or af[p].get("mtime") != bf[p].get("mtime"))
    return {
        "INSTALL_OR_LAUNCH_CREATED": created,
        "DELETED": deleted,
        "MODIFIED": modified,
        "created_count": len(created),
        "deleted_count": len(deleted),
        "modified_count": len(modified),
    }


def render_tree(root, max_entries=400):
    lines = []
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        rel = os.path.relpath(dirpath, root)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        indent = "  " * depth
        name = os.path.basename(root) if rel == "." else os.path.basename(dirpath)
        lines.append(f"{indent}{name}/")
        count += 1
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            try:
                sz = os.path.getsize(full)
            except OSError:
                sz = -1
            lines.append(f"{indent}  {fn} ({sz} B)")
            count += 1
            if count > max_entries:
                lines.append(f"{indent}  … TRUNCATED at {max_entries} entries "
                             f"(full data in JSON manifest)")
                return "\n".join(lines)
    return "\n".join(lines)


def main():
    argv = sys.argv[1:]
    diff_mode = "--diff" in argv
    json_out = None
    tree_out = None
    roots = []
    snap_paths = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--json":
            i += 1
            json_out = argv[i]
        elif a == "--tree":
            i += 1
            tree_out = argv[i]
        elif a == "--diff":
            pass
        elif a == "--snap":
            # snapshot over multiple roots: --snap rootA rootB --json snap.json
            pass
        else:
            roots.append(a)
        i += 1

    if diff_mode:
        # diff mode: exactly two snapshot jsons given as roots
        a = json.load(open(roots[0]))
        b = json.load(open(roots[1]))
        d = diff_snap(a, b)
        text = json.dumps(d, indent=1)
        print(text)
        if json_out:
            open(json_out, "w").write(text)
        return

    # snapshot mode: roots may carry a "::label" suffix
    parsed = []
    for r in roots:
        if "::" in r:
            path, label = r.split("::", 1)
        else:
            path, label = r, r
        parsed.append((path, label))

    snap = snapshot([p for p, _ in parsed])
    snap["labels"] = {p: l for p, l in parsed}
    text = json.dumps(snap, indent=1)

    tree_parts = []
    for p, l in parsed:
        tree_parts.append(f"### {l}\n{render_tree(p) if os.path.exists(p) else '(ABSENT)'}")
    tree_text = "\n\n".join(tree_parts)

    if json_out:
        open(json_out, "w").write(text)
    else:
        print(text)
    if tree_out:
        open(tree_out, "w").write(tree_text)
    else:
        print(tree_text, file=sys.stderr)


if __name__ == "__main__":
    main()
