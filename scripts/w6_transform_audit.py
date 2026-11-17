#!/usr/bin/env python3
"""W6 audit: verify the arm transform preserved every between-arm segment.
Pristine (git HEAD) segments: prologue (fn start -> arm1), gaps between
consecutive arms, tail (last arm end -> fn end). Each must appear verbatim
in the transformed file (as an exact line-subsequence block)."""
import json, re, subprocess

BR = "src/dex/dalvik_bridge.cpp"
pristine = subprocess.run(["git", "show", "HEAD:miniandroid/" + BR],
                          capture_output=True, text=True, check=True).stdout.split("\n")
transformed = open(BR, errors="replace").read().split("\n")
am = json.load(open("evidence/wave6/w6_arm_map.json"))
arms = sorted(am["bridge_to_api"]["arms"], key=lambda a: a["start"])
span = am["bridge_to_api"]["span"]

segs = []  # (label, start, end) 1-based inclusive, pristine line numbers
prev_end = span["start"]  # fn brace line; prologue starts after it
first = arms[0]["start"]
# prologue: fn start..first cond line start (arm start = brace line; cond above)
segs.append(("prologue", span["start"], first - 1))
for i in range(len(arms) - 1):
    a, b = arms[i], arms[i + 1]
    if b["start"] - 1 >= a["end"] + 1:
        segs.append((f"gap{a['start']}-{b['start']}", a["end"] + 1, b["start"] - 1))
segs.append((f"tail{arms[-1]['end']}", arms[-1]["end"] + 1, span["end"] - 1))

def find_subseq(needle, hay_start=0):
    n = len(needle)
    for i in range(hay_start, len(transformed) - n + 1):
        if transformed[i:i + n] == needle:
            return i
    return -1

missing = []
cursor = 0
for label, s, e in segs:
    seg = pristine[s - 1:e]
    # skip pure-empty segments
    if not [l for l in seg if l.strip()]:
        continue
    pos = find_subseq(seg, cursor)
    if pos < 0:
        # try trimming leading/trailing blank lines
        while seg and not seg[0].strip(): seg.pop(0)
        while seg and not seg[-1].strip(): seg.pop()
        pos = find_subseq(seg, cursor)
    if pos < 0:
        missing.append((label, s, e, len(seg)))
    else:
        cursor = pos + len(seg)
print(f"segments={len(segs)} missing={len(missing)}")
for m in missing[:8]:
    label, s, e, n = m
    print(f"  MISSING {label} (pristine {s}-{e}, {n} lines):")
    for l in pristine[s - 1:min(e, s + 4)]:
        print("    |", l[:100])
