#!/usr/bin/env python3
"""S177 intake step 1b: try multiple concat strategies until the declared
SHA-256 matches, then save the canonical patch files."""
import json, hashlib, os

EV = "evidence/s176_inventory"
OUT = "evidence/s177_intake"
os.makedirs(OUT, exist_ok=True)

def load(n): return {c["id"]: c for c in json.load(open(f"{EV}/{n}_comments.json"))}

def raw_block(body):
    i = body.find("```diff")
    if i < 0:
        k = body.find("diff --git")
        return body[k:] if k >= 0 else ""
    rest = body[i + 7:]
    j = rest.rfind("```")
    return rest[:j] if j >= 0 else rest

def variants(blocks):
    yield "raw", "".join(blocks)
    yield "raw_nl", "".join(b if b.endswith("\n") else b + "\n" for b in blocks)
    stripped = [b.strip("\n") for b in blocks]
    yield "strip_join_nl", "\n".join(stripped) + "\n"
    yield "strip_join_none", "".join(stripped)

def try_match(name, blocks, prefix, save_as):
    for tag, blob in variants(blocks):
        s = hashlib.sha256(blob.encode()).hexdigest()
        if s.startswith(prefix):
            open(save_as, "w").write(blob)
            print(f"{name}: MATCH strategy={tag} sha256={s} ({len(blob)}ch) -> {save_as}")
            return s
    print(f"{name}: no strategy matched prefix {prefix}")
    return None

# C7 W3 (declared 942ba893…)
cs7 = load(520)
ids = [6668210586, 6668211144, 6668211725, 6668212351, 6668212980, 6668213677]
try_match("C7 w3", [raw_block(cs7[i]["body"]) for i in ids], "942ba893",
          f"{OUT}/c7_w3_on_w2.patch")

# C8 wave-6 (declared fc6776ec287470000e02…)
cs8 = load(519)
ids = [6670041873, 6670042572, 6670043233]
try_match("C8 wave6", [raw_block(cs8[i]["body"]) for i in ids],
          "fc6776ec287470000e02", f"{OUT}/c8_wave6.patch")

# C8 w1..5 cumulative (declared dea17614…)
part_ids = [6667665968, 6667508731, 6667666635, 6667667600, 6667668549,
            6667669301, 6667670221, 6667671010, 6667671821, 6667672592,
            6667673464, 6667674188, 6667674909, 6667675554, 6667676289,
            6667677245, 6667678088, 6667678807, 6667679508, 6667680287,
            6667681208, 6667682118, 6667682801]
try_match("C8 w1..5", [raw_block(cs8[i]["body"]) for i in part_ids],
          "dea17614", f"{OUT}/c8_w1_5_tree.patch")
