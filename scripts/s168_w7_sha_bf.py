#!/usr/bin/env python3
"""S168: brute-force w7_laws.patch byte form until claimed sha16 matches
(ea55443a44263012, 137 lines claimed). S167 protocol reuse."""
import hashlib
import re
from pathlib import Path

W = Path("/home/z/my-project/evidence/s168_w7")
CLAIM = (137, "ea55443a44263012")

body = (W / "w7_comment_6638731163.md").read_text()
m = re.search(r"```diff\n(.*?)```", body, re.DOTALL)
t = (m.group(1) if m else body).replace("\r\n", "\n")


def sha16(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def variants(text: str):
    yield "as-is", text
    yield "lead-strip", text.lstrip("\n")
    yield "single-trail", text.rstrip("\n") + "\n"
    yield "lead+single-trail", text.lstrip("\n").rstrip("\n") + "\n"
    yield "strip", text.strip() + "\n"
    yield "no-trail", text.rstrip("\n")
    yield "strip-full", text.strip()
    yield "rstrip-each", "\n".join(
        l.rstrip() for l in text.splitlines()) + "\n"
    yield "rstrip-each-no-trail", "\n".join(
        l.rstrip() for l in text.splitlines())
    yield "rstrip-each-strip", "\n".join(
        l.rstrip() for l in text.splitlines()).strip()
    yield "rstrip-each-strip-no-trail", "\n".join(
        l.rstrip() for l in text.splitlines()).strip().rstrip("\n")


hits = []
for name, v in variants(t):
    n = v.count("\n") + (0 if v.endswith("\n") else 1)
    s = sha16(v.encode())
    mark = "  <== MATCH" if s == CLAIM[1] else ""
    print(f"{name:<26} lines={n:<4} sha16={s}{mark}")
    if s == CLAIM[1]:
        hits.append((name, v, n))

if hits:
    name, v, n = hits[0]
    out = W / "w7_laws.patch"
    out.write_text(v)
    print(f"\nsaved canonical form '{name}' ({n} lines) -> {out}")
else:
    print("\nNO exact sha match — fence byte-form unreproducible (S167 "
          "w6_stack precedent); content validity defers to apply-check + "
          "hunk review + gates.")
