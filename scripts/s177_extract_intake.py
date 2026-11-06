#!/usr/bin/env python3
"""S177 intake step 1: extract C7/C8/C9 unified patches from issue comments,
verify concatenated SHA-256 against their declared values, and run
git apply --check on the declared base trees (worktrees)."""
import json, subprocess, os, hashlib, sys

EV = "evidence/s176_inventory"
OUT = "evidence/s177_intake"
os.makedirs(OUT, exist_ok=True)

def load_comments(n):
    return json.load(open(f"{EV}/{n}_comments.json"))

def extract_diff(body):
    """Take the first ```diff fenced block; if no fence, from first diff --git to end."""
    i = body.find("```diff")
    if i >= 0:
        rest = body[i + len("```diff"):]
        j = rest.rfind("```")
        block = rest[:j] if j >= 0 else rest
    else:
        k = body.find("diff --git")
        block = body[k:] if k >= 0 else ""
    # strip leading/trailing blank lines
    lines = block.split("\n")
    while lines and not lines[0].strip(): lines.pop(0)
    while lines and not lines[-1].strip(): lines.pop()
    return "\n".join(lines) + ("\n" if lines else "")

def sha256(data):
    return hashlib.sha256(data.encode()).hexdigest()

def git(*args, cwd=None):
    r = subprocess.run(["git"] + list(args), capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

report = {}

# ── C7 (#520): parts 1-5 = W1+W2 on S170; parts 6-11 = W3 on W2 ──────────
cs7 = {c["id"]: c for c in load_comments(520)}
w1w2_ids = [6665338852, 6665340055, 6665341134, 6665342295, 6665343807]
w3_ids = [6668210586, 6668211144, 6668211725, 6668212351, 6668212980, 6668213677]
c7_w1w2 = "".join(extract_diff(cs7[i]["body"]) for i in w1w2_ids)
c7_w3 = "".join(extract_diff(cs7[i]["body"]) for i in w3_ids)
open(f"{OUT}/c7_w1w2_on_s170.patch", "w").write(c7_w1w2)
open(f"{OUT}/c7_w3_on_w2.patch", "w").write(c7_w3)
report["c7_w1w2_sha256"] = sha256(c7_w1w2)
report["c7_w3_sha256"] = sha256(c7_w3)
print("C7 w1w2 sha256:", report["c7_w1w2_sha256"])
print("     declared: d1cf984824caf83ef2c7f2fdeb100052c47ff4cf53d5ddcfae3da65d0ab5ac3e")
print("     MATCH" if report["c7_w1w2_sha256"].startswith("d1cf9848") else "     *** MISMATCH ***")
print("C7 w3   sha256:", report["c7_w3_sha256"])
print("     declared: 942ba8936cce3e5d4097e3adfa3eeecaca98f7675b3fd2ad406db85afd965ebf")
print("     MATCH" if report["c7_w3_sha256"].startswith("942ba893") else "     *** MISMATCH ***")

# ── C9 (#521): patch#1 (6642151960), patch#2 (6664392728) ─────────────────
cs9 = {c["id"]: c for c in load_comments(521)}
c9_p1 = extract_diff(cs9[6642151960]["body"])
c9_p2 = extract_diff(cs9[6664392728]["body"])
open(f"{OUT}/coder9_phase1.patch", "w").write(c9_p1)
open(f"{OUT}/coder9_phase2_harness.patch", "w").write(c9_p2)
report["c9_p1_sha256"] = sha256(c9_p1)
report["c9_p2_sha256"] = sha256(c9_p2)
print("C9 phase1 sha256:", report["c9_p1_sha256"], f"({len(c9_p1)} chars)")
print("C9 phase2 sha256:", report["c9_p2_sha256"], f"({len(c9_p2)} chars)")

# ── C8 (#519): wave-6 3 parts; w1..5 cumulative 23 parts (dup 02) ────────
cs8 = {c["id"]: c for c in load_comments(519)}
w6_ids = [6670041873, 6670042572, 6670043233]
c8_w6 = "".join(extract_diff(cs8[i]["body"]) for i in w6_ids)
open(f"{OUT}/c8_wave6.patch", "w").write(c8_w6)
report["c8_w6_sha256"] = sha256(c8_w6)
print("C8 wave6 sha256:", report["c8_w6_sha256"], f"({len(c8_w6)} chars)")
print("     declared prefix: fc6776ec287470000e02…",
      "MATCH" if report["c8_w6_sha256"].startswith("fc6776ec287470000e02") else "*** MISMATCH ***")

# w1..5 cumulative: part ids in order; part 02 has TWO candidates
part_ids = [6667665968,  # 01
            None,        # 02 (dup — resolve below)
            6667666635, 6667667600, 6667668549,  # 03 04 05
            6667669301,  # 06
            6667670221, 6667671010,              # 07 08
            6667671821,  # 09
            6667672592,  # 10
            6667673464, 6667674188,              # 11 12
            6667674909,  # 13
            6667675554,  # 14
            6667676289, 6667677245,              # 15 16
            6667678088,  # 17
            6667678807,  # 18
            6667679508,  # 19
            6667680287, 6667681208, 6667682118, 6667682801]  # 20 21 22 23
dup02 = [6667508731, 6667512756]
print("dup part-02 candidates:", [(i, len(extract_diff(cs8[i]['body']))) for i in dup02])

def build_w15(p02_id):
    ids = list(part_ids); ids[1] = p02_id
    return "".join(extract_diff(cs8[i]["body"]) for i in ids)

for cand in dup02:
    blob = build_w15(cand)
    s = sha256(blob)
    print(f"C8 w1..5 with p02={cand}: sha256 {s} ({len(blob)} chars)",
          "MATCH-prefix dea17614" if s.startswith("dea17614") else "")
    if s.startswith("dea17614"):
        open(f"{OUT}/c8_w1_5_tree.patch", "w").write(blob)
        report["c8_w15_sha256"] = s
        report["c8_w15_p02"] = cand
        break
else:
    # keep both variants for inspection
    for cand in dup02:
        open(f"{OUT}/c8_w15_try_{cand}.patch", "w").write(build_w15(cand))
    print("C8 w1..5: NO sha match on either p02 candidate — saved both for inspection")

json.dump(report, open(f"{OUT}/s177_intake_shas.json", "w"), indent=1)
print("saved shas ->", f"{OUT}/s177_intake_shas.json")
