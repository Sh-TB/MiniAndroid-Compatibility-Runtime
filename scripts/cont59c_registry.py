#!/usr/bin/env python3
"""cont59c_registry.py — CONT-59 registry update (650 -> 651): F-NEW-339."""
import json

REG = "/home/z/my-project/root_registry.json"
reg = json.load(open(REG))
roots = reg["roots"] if isinstance(reg, dict) and "roots" in reg else reg
ids = {r["id"] for r in roots}
assert "F-NEW-339" in ids, "F-NEW-339 must already be appended (by the wave script)"
assert len(roots) == 651, f"expected 651 roots, got {len(roots)}"
print(f"registry verified: {len(roots)} roots (650 -> 651); F-NEW-339 present")
