#!/usr/bin/env python3
"""CONT-21 / Issue #384 ARCH-001 — Phase A inventory helper.

Scans root_registry.json for per-target status evidence and prints a
family-oriented summary. Read-only.
"""
import json, re, sys

BASE = "/home/z/my-project"
d = json.load(open(f"{BASE}/root_registry.json"))
roots = d["roots"]

TARGETS = [
    "opencalc", "unote", "microtimer", "stopwatch", "chessclock", "2048",
    "g2048", "tetris", "snake", "tictactoe", "minicraft", "fishrings",
    "flappy", "bouncy", "gmdice", "forkgram", "telegram", "whatsapp",
    "dooz", "browser", "webview", "blockblast", "fairymahjong", "klondike",
    "sudoku", "opmt", "tripeaks", "chess", "glxy", "notes", "flashlight",
    "keyboard", "inputmethod",
]

summary = {}
for r in roots:
    if not isinstance(r, dict):
        continue
    rid = str(r.get("id", "?"))
    if not isinstance(r, dict):
        continue
    txt = json.dumps(r)
    for t in TARGETS:
        if re.search(r"(?i)" + re.escape(t), txt):
            st = r.get("status", "?")
            pr = r.get("priority", "")
            summary.setdefault(t, []).append((rid, st, pr))

for t in sorted(summary):
    rows = sorted(summary[t], key=lambda x: x[0])
    print(f"== {t} ({len(rows)} rows) ==")
    for rid, st, pr in rows[:8]:
        print(f"   {rid:12s} {st:26s} {pr}")
