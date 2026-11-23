#!/usr/bin/env python3
"""S27-AUDIT-2 memcpy sweep — the friend-method applied by the engine itself.

Every memcpy call site in src/ is extracted with context and classified:
  GUARDED   — a bounds comparison / min() involving the length expression
              appears within the 4 lines above the call.
  CONSTANT  — the length argument is a literal or sizeof expression.
  FLAGGED   — non-constant length whose variable appears in NO nearby
              comparison; these are the sites a hostile input could steer.

Output: evidence/s27/s27_audit2_memcpy_sweep.csv (all sites) and a stdout
list of the FLAGGED sites in the I/O-boundary directories for manual review.
"""
import csv
import re
from pathlib import Path

ROOT = Path("/home/z/my-project/miniandroid")
OUT = Path("/home/z/my-project/evidence/s27")
OUT.mkdir(parents=True, exist_ok=True)

IO_DIRS = ("resources", "apk", "storage", "api", "jni", "webview", "runtime",
           "dex")

memcpy_re = re.compile(r"\bmemcpy\s*\(([^;]*)\)\s*;")
guard_tokens = re.compile(r"[<>=!]=?|std::min|min\(|cap|clamp|avail|_size\b")


def split_top_level(args: str):
    """Split a memcpy arg list on top-level commas (paren/bracket-aware)."""
    out, buf, depth = [], [], 0
    for ch in args:
        if ch in "(<[":
            depth += 1
        elif ch in ")>]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        out.append("".join(buf).strip())
    return out

rows = []
for path in sorted(ROOT.glob("src/**/*.cpp")):
    lines = path.read_text(errors="replace").splitlines()
    for i, line in enumerate(lines):
        for m in memcpy_re.finditer(line):
            # join continuation lines for the full arg list
            args = line[m.start(1):m.end(1)]
            j = i + 1
            depth = args.count("(") - args.count(")")
            while depth > 0 and j < len(lines) and j - i < 4:
                args += lines[j]
                depth += lines[j].count("(") - lines[j].count(")")
                j += 1
            parts = split_top_level(args)
            dst, src = (parts + ["", "", ""])[0], (parts + ["", "", ""])[1]
            length = (parts + ["", "", ""])[2]
            above = "\n".join(lines[max(0, i - 4):i])
            length_vars = re.findall(
                r"[A-Za-z_]\w*", re.sub(r"sizeof|static_cast<[^>]*>|\d+", " ",
                                        length))
            if not length:
                cls = "UNPARSED"
            elif not length_vars:
                cls = "CONSTANT"  # literal / sizeof-only
            elif any(v in above and guard_tokens.search(above)
                     for v in set(length_vars)):
                cls = "GUARDED"
            else:
                cls = "FLAGGED"
            rows.append({
                "file": str(path.relative_to(ROOT)),
                "line": i + 1,
                "length_expr": length[:90],
                "class": cls,
                "io_boundary": "1" if any(f"/src/{d}/" in str(path) or f"\\src\\{d}\\" in str(path) or f"src/{d}/" in str(path) for d in IO_DIRS) else "0",
            })

with open(OUT / "s27_audit2_memcpy_sweep.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["file", "line", "length_expr", "class", "io_boundary"])
    w.writeheader()
    w.writerows(rows)

from collections import Counter
c = Counter(r["class"] for r in rows)
print("total memcpy sites:", len(rows))
print("classes:", dict(c))
flagged_io = [r for r in rows if r["class"] == "FLAGGED" and r["io_boundary"] == "1"]
print(f"FLAGGED in I/O-boundary dirs: {len(flagged_io)}")
for r in flagged_io[:25]:
    print(f"  {r['file']}:{r['line']}  len= {r['length_expr'][:70]}")
