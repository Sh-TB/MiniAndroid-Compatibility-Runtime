#!/usr/bin/env python3
"""Extract the A-R4 patch from the two GitHub comments, assemble parts 1+2,
verify sha256 == 8bdf0881e0d39bcd..., split into two patch files."""
import hashlib, re

p1 = open("/tmp/c_6787429312.md").read()
p2 = open("/tmp/c_6787429768.md").read()

def extract_diff(text):
    m = re.search(r"```diff\n(.*?)```", text, re.S)
    if not m:
        raise SystemExit("no ```diff block found")
    return m.group(1)

d1, d2 = extract_diff(p1), extract_diff(p2)
full = d1 + d2
sha = hashlib.sha256(full.encode()).hexdigest()
print(f"parts: {len(d1)} + {len(d2)} bytes; combined {len(full)} bytes")
print(f"sha256: {sha}")
print(f"sha16:  {sha[:16]}  (expect 8bdf0881e0d39bcd)")
ok = sha.startswith("8bdf0881e0d39bcd")
print("SHA MATCH" if ok else "SHA MISMATCH")

open("/tmp/ar4_part1.patch", "w").write(d1)
open("/tmp/ar4_part2.patch", "w").write(d2)
open("/tmp/ar4_full.patch", "w").write(full)
print("written /tmp/ar4_part1.patch /tmp/ar4_part2.patch /tmp/ar4_full.patch")
print(f"diff --git count in full: {full.count('diff --git')} (expect 16)")
