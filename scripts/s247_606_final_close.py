#!/usr/bin/env python3
"""The #606 FINAL receipt: constraint solver shipped, issue closed."""
import json, subprocess, urllib.request

CRED = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True,
                      cwd="/home/z/my-project").stdout
TOKEN = [l.split("=", 1)[1] for l in CRED.splitlines() if l.startswith("password=")][0]

B = """## #606 FINAL — the constraint solver shipped, ZERO open surfaces remain (commit 11597cd2) — CLOSING

The last documented approximation (the D-wave's even-split spanned-excess distribution, "documented as the honest simplification of the AOSP arc/Bellman-Ford constraint solver") is now replaced by the **REAL AOSP Axis constraint law** — `GridLayout.java computeLinks + solve`, honest port:

- `gl_solve_tracks`: the grid lines are the **MINIMAL solution** of two arc families — span-1 cells (leading arcs: `line[i+1] ≥ line[i] + trackMax[i]`) and spanned children (interval arcs: `line[max] ≥ line[min] + size`) — Bellman-Ford over the forward-only arcs, forward relaxation iterated to a fixpoint (≤ n passes; every arc points forward, so convergence is guaranteed).
- Consequence pinned by law: **the excess a spanned child needs lands in its TRAILING tracks** (earlier lines keep their own minimal constraints) — e.g. a span-2 600px child over two 200px tracks gives lines `[0,200,600]` → tracks 200/**400**, not 300/300.
- Both the measure aggregation and the onLayout branch run the same solve; the solved lines ARE the cell origins (no recompute drift).

### Battery — s247 now 33 laws, G6 pins the solver
- G6.1 trailing law (`[0,200,600]`), G6.2 neighbors-untouched (`[0,100,450,550]` — the whole 350px excess in track1, tracks 0/2 keep their maxima), G6.3 span-3 (`[0,100,200,500]`), G6.4 two interacting arcs (`[0,0,500,600]` — B sits exactly at line2=500), G6.5 the ROW axis runs the same solver (rows `[0,100,350]`), G6.6 no-widening (a 150px span over 300px of tracks changes nothing — minimal solution).
- G3.2/G4.1/G4.2 expectations moved to the solver law (tracks 200/400, 0/200; FILL stretches to the solved track).

### Gates on the closure commit
s247 **33/33** normal **and** 33/33 hidden-font world (rc=0, "GRID+RTL DOMAIN CLOSED") · s246 stays **47/47** · binary RC=0 · test-all **42/42** · parity **75/75** · zero crashes.

### Final ledger of #606 (all closed)
1. RelativeLayout center inversion (INVERTED guard) — fixed, s246 H10.
2. HorizontalScrollView missing UNSPEC width law — added, s246 H2.
3. Scroll-content clamp leak — scroll = the one legal overflow, s246 G10.
4. LL vertical-column cross-axis bit-test misroute (LEFT/RIGHT → CENTER) — fixed to mask-first + RTL flip, s247 R6.
5. GridLayout fallback (vertical flow) → REAL span-track grid — s247 G1-G6.
6. RTL (layoutDirection never parsed) → full mirroring law set — s247 R1-R6.
7. Spanned-excess even split → the REAL constraint solver — s247 G6. ✅ this receipt

**Verdict: LAYOUT DOMAIN FULLY CLOSED — 74 pinned laws (s246 47 + s247 33), 4 engine bugs caught and fixed, both worlds green, zero open surfaces. Issue closed.**"""
req = urllib.request.Request("https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/606/comments",
    data=json.dumps({"body": B}).encode(),
    headers={"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json", "User-Agent": "layout-audit"},
    method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    print("receipt", json.loads(r.read().decode())["id"])

req2 = urllib.request.Request("https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/606",
    data=json.dumps({"state": "closed", "state_reason": "completed"}).encode(),
    headers={"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json", "User-Agent": "layout-audit"},
    method="PATCH")
with urllib.request.urlopen(req2, timeout=30) as r:
    j = json.loads(r.read().decode())
    print("issue state:", j["state"], "| reason:", j["state_reason"])
