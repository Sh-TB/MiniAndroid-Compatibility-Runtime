#!/usr/bin/env python3
"""S167: repair w6_stack.patch seam hunk against the AUTHOR BASE oracle.

Findings:
  - seam hunk @@ -44021,6 +44237,242 (patch line 410): declared (6,242)
  - blob truth (8c622c9): no empty line between 44023 and 44024 -> the empty
    line at glued 631 between two + lines is a lost '+' (trailing-whitespace
    strip on paste), and the trailing context is 3 lines (44024..44026)
  - true hunk = ctx(3) + adds(237 incl one empty) + ctx(3) = (6,243)
Oracle: git apply --check on the reconstructed author base at /tmp/w6check.
"""
import subprocess
import sys
from pathlib import Path

PATCH = Path("/home/z/my-project/evidence/s167_w6/w6_stack.patch")
OUT = Path("/home/z/my-project/evidence/s167_w6/w6_stack_repaired.patch")
CHECK = Path("/tmp/w6check")

lines = PATCH.read_text().split("\n")
if lines and lines[-1] == "":
    lines = lines[:-1]

# locate seam hunk header and next @@ after it
seam_i = next(i for i, l in enumerate(lines) if l.startswith("@@ -44021,6"))
nxt_i = next(i for i in range(seam_i + 1, len(lines))
             if lines[i].startswith("@@ "))
print(f"seam header at line {seam_i+1}: {lines[seam_i][:60]}")
print(f"next @@ at line {nxt_i+1}: {lines[nxt_i][:60]}")
body = lines[seam_i + 1:nxt_i]
print(f"body lines: {len(body)}  adds={sum(1 for b in body if b.startswith('+'))}"
      f" ctx={sum(1 for b in body if b.startswith(' ') or b == '')}")

# candidate repairs: (empty-line treatment, trailing-ctx span, header)
def build(empty_add_idx, trailing_n, hdr):
    b = list(body)
    if empty_add_idx is not None:
        b[empty_add_idx] = "+"
    if trailing_n is not None:
        # trailing context = last trailing_n lines of current body (all ctx)
        b = b[:-trailing_n] if trailing_n == 0 else b
    return [hdr] + b


cands = []
for name, empty_idx, trailing, hdr in (
        ("A: empty->'+', ctx=3, hdr=(6,243)",
         631 - (seam_i + 1) - 1, 3,
         "@@ -44021,6 +44237,243 @@ bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,"),
        ("B: empty->ctx, drop stray, hdr=(6,242)",
         None, 2,
         "@@ -44021,6 +44237,242 @@ bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,")):
    cands.append((name, empty_idx, trailing, hdr))

best_text = None
for name, empty_idx, trailing, hdr in cands:
    patched = lines[:seam_i] + [hdr] + lines[seam_i + 1:nxt_i] + lines[nxt_i:]
    if empty_idx is not None:
        patched[seam_i + 1 + empty_idx] = "+"
    if name.startswith("B"):
        # candidate B: strip the stray last ctx line from the body
        del patched[seam_i + 1 + (len(body) - 1)]
    text = "\n".join(patched) + "\n"
    r = subprocess.run(["git", "apply", "--check", "-"], cwd=CHECK,
                       input=text, capture_output=True, text=True)
    ok = r.returncode == 0
    if ok:
        best_text = text
    print(f"candidate {name}: {'CLEAN' if ok else 'FAIL'}"
          + ("" if ok else "  stderr: " + r.stderr.strip()[:200]))

if best_text:
    OUT.write_text(best_text)
    print("repaired patch (first CLEAN candidate) written:", OUT)
else:
    print("NO CLEAN candidate — do not proceed")
    sys.exit(1)
