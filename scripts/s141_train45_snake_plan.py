#!/usr/bin/env python3
"""s141_train45_snake_plan.py — deterministic autoplay plan for Snake Neon
(mirror of NeonSnakeView logic — the app stays authoritative per C4).

Layout law: 1080x1920 runtime, vertical LL = game (weight 1) + button bar
(wrap_content, 10dp padding). Button taps are committed AFTER a first
--dump-view-tree run pins the real button bounds (the dump is authoritative;
this plan emits DIRECTION + count, the runner script maps to real coords).

Start law (reset): len=3 head (4,8) dir=1 (right); food (10,8) — the FIRST
food is a straight-line eat: 6 ticks RIGHT with zero taps. Then the LCG
(0x5EEDBEEF, law: seed*6364136223846793005+1442695040888963407, r=(seed>>>33)
&0x7FFFFFFF, r%bound) picks food (c,r) among free cells.

This plan simulates N ticks, emitting a tap list (dir changes only) and the
expected score trajectory. DIRS: 0 up, 1 right, 2 down, 3 left.
"""
COLS, ROWS = 15, 16
MAXBLOCK = 4


def deal_sim(ticks, dirs_at):
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
                foodC, foodR = c, r
                return

    def spawn_block():
        nonlocal blocks
        if blocks >= MAXBLOCK: return
        for _ in range(500):
            c = rnd(COLS); r = rnd(ROWS)
            if not occupied(c, r) and not (c == foodC and r == foodR):
                bC[blocks], bR[blocks] = c, r
                blocks += 1
                return

    taps = []
    traj = []
    for t in range(ticks):
        if t in dirs_at:
            pend = dirs_at[t]
            taps.append((t, pend))
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
                dead = f'tail@tick{t}'; break
        if dead: break
        for i in range(blocks):
            if bC[i] == hc and bR[i] == hr:
                dead = f'block@tick{t}'; break
        if dead: break
        for i in range(LEN - 1, 0, -1):
            sx[i] = sx[i - 1]; sy[i] = sy[i - 1]
        sx[0], sy[0] = hc, hr
        if hc == foodC and hr == foodR:
            score += 10; foods += 1; LEN += 1
            sx[LEN - 1] = sx[LEN - 2]; sy[LEN - 1] = sy[LEN - 2]
            spawn_food()
            if foods % 3 == 0: spawn_block()
            traj.append((t, score, LEN, foods, foodC, foodR))
    return dict(dead=dead, score=score, foods=foods, len=LEN, taps=taps, traj=traj,
                head=(sx[0], sy[0]), blocks=blocks, bC=bC[:blocks], bR=bR[:blocks],
                food=(foodC, foodR))


if __name__ == '__main__':
    import json, sys
    # plan: no taps at all — straight run; the LCG deal makes food land ON the
    # head path when possible; we search a small tap schedule that eats >=3
    # foods without dying (greedy per-food direction search).
    best = None
    for up in range(0, 3):
        for down in range(0, 3):
            for left in range(0, 4):
                for right in range(0, 4):
                    # taps interleaved: up at t=8, down at t=14, left t=22, right t=30 variants
                    dirs_at = {}
                    pool = [(8, 0, up), (14, 2, down), (22, 3, left), (30, 1, right),
                            (38, 0, up), (46, 2, down), (54, 3, left), (62, 1, right)]
                    for t, d, n in pool:
                        if n > 0:
                            dirs_at[t] = d
                    r = deal_sim(80, dirs_at)
                    if best is None or r['score'] > best['score']:
                        best = r; best['dirs_at'] = dirs_at
    print(json.dumps(best, indent=1))
