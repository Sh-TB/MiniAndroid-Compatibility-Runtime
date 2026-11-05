#!/usr/bin/env python3
"""S167: validate unified-diff hunk counts in w6_stack.patch; find the first
corruption point; report fence parity of each #517 comment body."""
import json
import re
from pathlib import Path

W = Path("/home/z/my-project/evidence/s167_w6")
PATCH = (W / "w6_stack.patch").read_text()
LINES = PATCH.split("\n")

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
FILE = re.compile(r"^diff --git ")

# --- fence parity of the three comments ---
comments = json.load(open("/tmp/i517_comments.json"))
for c in comments:
    body = c["body"]
    n = body.count("```")
    print(f"comment {c['id']}: fence markers={n} ({'paired' if n % 2 == 0 else 'UNPAIRED'})")


def validate(lines, label):
    print(f"--- validate {label}: {len(lines)} lines")
    i = 0
    cur_file = None
    problems = 0
    while i < len(lines):
        ln = lines[i]
        if FILE.match(ln):
            cur_file = ln
            i += 1
            continue
        m = HUNK.match(ln)
        if m:
            old_n = int(m.group(2)) if m.group(2) is not None else 1
            new_n = int(m.group(4)) if m.group(4) is not None else 1
            j = i + 1
            oc = nc = 0
            while j < len(lines) and (oc < old_n or nc < new_n):
                b = lines[j]
                if b.startswith("+"):
                    nc += 1
                elif b.startswith("-"):
                    oc += 1
                elif b.startswith(" ") or b == "":
                    oc += 1
                    nc += 1
                elif b.startswith("\\"):
                    pass  # \ No newline at end of file
                else:
                    print(f"  line {j+1}: NON-DIFF BODY LINE inside hunk "
                          f"(file={cur_file}): {b[:110]!r}")
                    problems += 1
                    break
                j += 1
            if oc == old_n and nc == new_n:
                i = j
                continue
            print(f"  line {i+1}: HUNK COUNT MISMATCH file={cur_file} "
                  f"@{ln[:60]} declared=({old_n},{new_n}) "
                  f"actual=({oc},{nc}) next-line={lines[j][:80]!r}")
            problems += 1
            i = j
            continue
        if ln.startswith(("--- ", "+++ ", "index ", "new file", "old mode",
                          "deleted file", "\\ No newline")) or ln == "":
            i += 1
            continue
        print(f"  line {i+1}: TOP-LEVEL STRAY LINE: {ln[:110]!r}")
        problems += 1
        i += 1
    print(f"  problems={problems}")


validate(LINES, "w6_stack.patch (glued)")
