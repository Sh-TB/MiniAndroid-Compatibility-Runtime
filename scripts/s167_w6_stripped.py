#!/usr/bin/env python3
"""S167: strip markdown fences from #517 payloads, verify claimed sha16s.

Claims (S165 record + comment headers):
  w6_stack.patch = part1 (6634649186) + part2 (6634649953) concatenated
                   -> 1305 lines, sha16 d92efd2d32db128d
  w6_laws.patch  = comment 6634643760 -> 569 lines, sha16 65699ca9a235e915
"""
import hashlib
import re
from pathlib import Path

W = Path("/home/z/my-project/evidence/s167_w6")


def raw_patch(body: str) -> str:
    """Extract the first ```diff fenced block (or the whole body if none)."""
    m = re.search(r"```diff\n(.*?)```", body, re.DOTALL)
    return m.group(1) if m else body


def sha16(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


stack1 = raw_patch((W / "w6_comment_6634649186.patch").read_text())
stack2 = raw_patch((W / "w6_comment_6634649953.patch").read_text())
laws = raw_patch((W / "w6_comment_6634643760.patch").read_text())

stack = stack1 + stack2
for name, text, want_lines, want_sha in (
        ("w6_stack.patch", stack, 1305, "d92efd2d32db128d"),
        ("w6_laws.patch", laws, 569, "65699ca9a235e915")):
    n = text.count("\n")
    got = sha16(text)
    print(f"{name}: lines={n} (claim {want_lines}) sha16={got} "
          f"(claim {want_sha}) MATCH={n == want_lines and got == want_sha}")
    (W / name).write_text(text)
print("raw patches written to", W)
