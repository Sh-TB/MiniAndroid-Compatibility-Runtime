#!/usr/bin/env python3
"""s141_train45b_snake_plan.py — lag-robust snake-neon autoplay plan.

The tap pipeline (main.cpp G06 law) lands the click 1-2 frames after the
--tap frame; the tick fires every 2 frames (--frame-delay 110). So a tap
scheduled at tick T lands the pendingDir change at tick T..T+2 depending on
queue ordering. This plan finds a tap schedule that eats >=3 foods for EVERY
lag in {0,1,2} — the app's logic stays authoritative; the run must show
score>0 + len>3 whatever the real lag.
"""
import json


def sim(ticks, dirs_at, lag):
    COLS, ROWS, MAXBLOCK = 15, 16, 4
    seed = 0x5EEDBEEF

    def rnd(b):
        nonlocal seed
        seed = (seed * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        return ((seed >> 33) & 0x7FFFFFFF) % b

    sx = [0] * (COLS * ROWS); sy = [0] * (COLS * ROWS)
    LEN = 3; dir_ = 1; pend = 1
    foodC, foodR = 10, 8
    score = 0; foods = 0; dead = None; blocks = 0
    bC = [0] * MAXBLOCK; bR = [0] * MAXBLOCK
    sx[0], sy[0] = 4, 8; sx[1], sy[1] = 3, 8; sx[2], sy[2] = 2, 8

    def occupied(c, r):
        for i in range(LEN):
            if sx[i] == c and sy[i] == r: return True
        for i in range(blocks):
            if bC[i] == c and bR[i] == r: return True
        return False

    def spawn_food():
        nonlocal foodC, foodR
        for _ in range(500):
            c = rnd(COLS); r = rnd(ROWS)
            if not occupied(c, r) and not (c == foodC and r == foodR):
                foodC, foodR = c, r; return

    def spawn_block():
        nonlocal blocks
        if blocks >= MAXBLOCK: return
        for _ in range(500):
            c = rnd(COLS); r = rnd(ROWS)
            if not occupied(c, r) and not (c == foodC and r == foodR):
                bC[blocks], bR[blocks] = c, r; blocks += 1; return

    for t in range(ticks):
        # lag model: a tap scheduled for tick T lands at tick T+lag
        if (t - lag) in dirs_at:
            pend = dirs_at[t - lag]
        dir_ = pend
        hc, hr = sx[0], sy[0]
        if dir_ == 0: hr -= 1
        elif dir_ == 1: hc += 1
        elif dir_ == 2: hr += 1
        else: hc -= 1
        if hc < 0: hc = COLS - 1
        if hc >= COLS: hc = 0
        if hr < 0: hr = ROWS - 1
        if hr >= ROWS: hr = 0
        for i in range(LEN - 1):
            if sx[i] == hc and sy[i] == hr:
                dead = f'tail@{t}'; break
        if dead: break
        for i in range(blocks):
            if bC[i] == hc and bR[i] == hr:
                dead = f'block@{t}'; break
        if dead: break
        for i in range(LEN - 1, 0, -1):
            sx[i] = sx[i - 1]; sy[i] = sy[i - 1]
        sx[0], sy[0] = hc, hr
        if hc == foodC and hr == foodR:
            score += 10; foods += 1; LEN += 1
            sx[LEN - 1] = sx[LEN - 2]; sy[LEN - 1] = sy[LEN - 2]
            spawn_food()
            if foods % 3 == 0: spawn_block()
    return dict(dead=dead, score=score, foods=foods, len=LEN)


import random
random.seed(7)
best = None
DIRS = [0, 1, 2, 3]
for trial in range(4000):
    sched = {}
    t = 10
    while t < 70:
        sched[t] = random.choice(DIRS)
        t += random.choice([8, 10, 12, 14])
    oks = []
    for lag in (0, 1, 2):
        r = sim(90, sched, lag)
        oks.append((lag, r['score'], r['foods'], r['len'], r['dead']))
    min_score = min(o[1] for o in oks)
    alive = all(o[4] is None for o in oks)
    if not alive:
        continue
    cand = (min_score, alive, sched, oks)
    if best is None or min_score > best[0]:
        best = cand
        if min_score >= 30:
            break
print(json.dumps({'min_score': best[0], 'alive_all_lags': best[1],
                  'sched': best[2], 'per_lag': best[3]}, indent=1))
