#!/usr/bin/env python3
"""S167: brute-force the W6 raw-patch byte form until claimed sha16 matches.

The #517 claims: w6_stack 1305L d92efd2d32db128d; w6_laws 569L 65699ca9a235e915.
Fenced extraction carries +/-2 line artifacts; try normalisation variants.
"""
import hashlib
import re
from pathlib import Path

W = Path("/home/z/my-project/evidence/s167_w6")

CLAIMS = {
    "w6_stack.patch": (1305, "d92efd2d32db128d"),
    "w6_laws.patch": (569, "65699ca9a235e915"),
}


def sha16(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def fenced(body: str) -> str:
    m = re.search(r"```diff\n(.*?)```", body, re.DOTALL)
    return m.group(1) if m else body


def variants(text: str):
    t = text.replace("\r\n", "\n")
    yield "as-is", t
    yield "lf-strip-blank-lead", t.lstrip("\n")
    yield "lf-single-trailing", t.rstrip("\n") + "\n"
    yield "lf-lead+trail", t.lstrip("\n").rstrip("\n") + "\n"
    yield "lf-strip", t.strip() + "\n"
    yield "lf-no-trailing", t.rstrip("\n")
    yield "strip-full", t.strip()


def load_stack() -> str:
    p1 = fenced((W / "w6_comment_6634649186.patch").read_text())
    p2 = fenced((W / "w6_comment_6634649953.patch").read_text())
    for glue in ("", "\n"):
        yield_name = f"stack glue={'newline' if glue else 'none'}"
        yield yield_name, p1 + glue + p2


results = {}
for target in CLAIMS:
    want_n, want_sha = CLAIMS[target]
    cands = []
    if target == "w6_laws.patch":
        cands.append(("laws-fenced", fenced((W / "w6_comment_6634643760.patch").read_text())))
    else:
        cands.extend(load_stack())
    for base_name, base in cands:
        for vname, text in variants(base):
            n = text.count("\n")
            s = sha16(text.encode())
            if s == want_sha or n == want_n:
                results.setdefault(target, []).append(
                    (base_name, vname, n, s, s == want_sha))

for target, rows in results.items():
    want_n, want_sha = CLAIMS[target]
    print(f"== {target} (want lines={want_n} sha={want_sha})")
    for r in rows[:12]:
        print("   ", r)
if not results:
    print("NO variant matched lines or sha — claims may be over a different byte form")
