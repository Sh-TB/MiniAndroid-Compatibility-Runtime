#!/usr/bin/env python3
"""cont70 batch-2 registry update (evidence-only; no engine changes).

  F-138      REGISTERED -> ROOT-CAUSED-FIXED (the F-NEW-372 canvas-text
             real-size law renders the bouncy ScoreView 'Touch to start'
             hint at real size/position; before-face had no visible hint)
  F-NEW-373  NEW CLASSIFIED P2 — view-lane tap hit-test returns target=0 for
             the whole Secuso tree (memory: toolbar/Easy/New Game; notes:
             Next), while the CONT-66 calculator lane hit target=176.
"""
import json
from collections import Counter

PATH = "/home/z/my-project/root_registry.json"
r = json.load(open(PATH))
roots = r["roots"]
by_id = {x["id"]: x for x in roots}

x = by_id["F-138"]
x["status"] = "ROOT-CAUSED-FIXED"
x["title"] = (
    "ScoreView hint HUD text — ROOT-CAUSED-FIXED via the F-NEW-372 canvas-text "
    "real-size law (cont70): the 'Touch to start' hint (ScoreView.java:226 "
    "getString) previously fell to the tiny legacy bitmap path (text_size=0 "
    "shape); with the F-NEW-226 state read live the hint renders at real size "
    "in the bouncy top bar (before dd0c1425 no visible hint text; after "
    "1b87e9ef the yellow 'Touch to start' bar renders, deterministic x3).")
x["evidence"] = (
    "evidence/cont70/before/bouncy_old_dd0c14257fa1f2af.png vs "
    "run/cont70/accept/v2_bouncy/screenshot.png; worklog R-NEW-389 op-diff "
    "line (drawText content '' -> 'Touch to start')")

roots.append({
    "id": "F-NEW-373",
    "status": "CLASSIFIED",
    "priority": "P2",
    "layer": "input/touch-target (view lane, F117 dispatcher walk)",
    "title": (
        "VIEW-LANE TAP HIT-TEST DEAD FOR THE SECUSO TREE SHAPE (cont70, "
        "evidence-only): every --tap on the memory app answers target=0 "
        "(toolbar (980,80), 'Easy' row (540,1405), 'New Game' (540,1868)) and "
        "every --tap on notes_secuso answers target=0 ('Next' (828,1794)); "
        "faces byte-unchanged (c559b630 / d0a40904 records). Contrast: the "
        "CONT-66 calculator lane hit target=176 ('7' Button) — the walk works "
        "for the shallow FrameLayout/GridLayout tree but loses the "
        "DrawerLayout+Toolbar+AppBarLayout+ViewPager(+fragment children) "
        "shape. Named lever: F117 walk decode on the Secuso tree — which hop "
        "drops it (decor/content-root attach chain, fragment-hosted children, "
        "transform/visibility gates, or the position store for non-compose "
        "deep nesting). Sibling of F-NEW-267 (compose lane store disconnect)."),
    "evidence": (
        "run/cont70/accept/mem_tap1..3.err (three target=0 rows); "
        "run/cont70/accept/notes_tap1.err (target=0, face record intact)"),
    "date": "2026-10-16",
})

r["total_roots"] = len(roots)
r["count"] = len(roots)
r["status_counts"] = dict(Counter(x["status"] for x in roots))
ids = [x["id"] for x in roots]
assert len(set(ids)) == len(ids)
json.dump(r, open(PATH, "w"), indent=1, ensure_ascii=False)
print("roots:", len(roots), "| F-138:", by_id["F-138"]["status"],
      "| F-NEW-373 registered")
