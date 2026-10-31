#!/usr/bin/env python3
"""s138_mem_winplan.py — deterministic WIN plan for Memory Match (gmem).

The deal is deterministic (fixed LCG seed 0x8EAD0), so the full win tap
sequence can be computed offline against a mirror of the app logic, then
committed to the REAL APK run via --tap. The app's own logic stays
authoritative (C4): the final frame must show YOU WIN.
"""
N = 8  # faces (16 cards)

def deal():
    cards = [i // 2 for i in range(16)]
    seed = 0x8EAD0
    def rnd(b):
        nonlocal seed
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        return seed % b
    for i in range(15, 0, -1):
        j = rnd(i + 1)
        cards[i], cards[j] = cards[j], cards[i]
    return cards

# mirror of MemBoardView state
cards = deal()
state = [0] * 16
cursor = 0
selA, selB = -1, -1
moves = 0
matched = 0
won = False

# measured button coords (frame probe, y=1599 FLIP/NEW row, y=1809 d-pad)
BTN = {"LEFT": (170, 1809), "UP": (414, 1809), "DOWN": (667, 1809),
       "RIGHT": (920, 1809), "FLIP": (280, 1599)}
DIR = {0: "LEFT", 1: "UP", 2: "RIGHT", 3: "DOWN"}

taps = []
k = 3  # first tap frame

def step_frame():
    global k
    k += 2

def tap(name):
    global k
    x, y = BTN[name]
    taps.append((x, y, k))
    step_frame()

def move_cursor_to(target):
    global cursor
    r, c = cursor // 4, cursor % 4
    tr, tc = target // 4, target % 4
    # move with wrap (app wraps both axes)
    while c != tc:
        c = (c - 1) % 4 if (abs((c - 1) % 4 - tc) <= abs((c + 1) % 4 - tc)) else (c + 1) % 4
        tap(DIR[0 if c == (cursor % 4 - 1) % 4 else 2])
        cursor = (cursor // 4) * 4 + c
    while r != tr:
        nr = (r - 1) % 4 if (abs((r - 1) % 4 - tr) <= abs((r + 1) % 4 - tr)) else (r + 1) % 4
        tap(DIR[1 if nr == (r - 1) % 4 else 3])
        r = nr
        cursor = r * 4 + (cursor % 4)

def flip():
    global selA, selB, moves, matched, won, state
    i = cursor
    if state[i] != 0:
        return
    tap("FLIP")
    # mirror app logic
    if selA < 0:
        selA = i; state[i] = 1
    elif selB < 0 and i != selA:
        selB = i; state[i] = 1; moves += 1
        if cards[selA] == cards[selB]:
            state[selA] = 2; state[selB] = 2
            matched += 1; selA = -1; selB = -1
            if matched == 8:
                won = True
    else:
        if selA >= 0 and selB >= 0 and cards[selA] != cards[selB]:
            state[selA] = 0; state[selB] = 0
        selA = i; selB = -1; state[i] = 1

print("deal:", cards)
guard = 0
while not won and guard < 400:
    guard += 1
    if selA >= 0 and selB < 0:
        # complete the pair
        js = [j for j in range(16) if state[j] == 0 and cards[j] == cards[selA] and j != selA]
        if not js:
            break
        move_cursor_to(js[0]); flip()
    else:
        # start a new known pair
        pairs = [(i, j) for i in range(16) for j in range(i + 1, 16)
                 if state[i] == 0 and state[j] == 0 and cards[i] == cards[j]]
        if not pairs:
            break
        move_cursor_to(pairs[0][0]); flip()

print("won:", won, "moves:", moves, "matched:", matched, "taps:", len(taps), "last frame:", k)
if won:
    print("TAPS=" + " ".join(f"--tap {x},{y}@{f}" for x, y, f in taps))
