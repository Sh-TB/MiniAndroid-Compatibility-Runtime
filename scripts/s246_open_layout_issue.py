#!/usr/bin/env python3
"""Open the LAYOUT-PIPE-001 issue: the view-layout domain closure, the
same methodology that closed the font domain (#605)."""
import json, subprocess, urllib.request

CRED = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True,
                      cwd="/home/z/my-project").stdout
TOKEN = [l.split("=", 1)[1] for l in CRED.splitlines() if l.startswith("password=")][0]

B = """## LAYOUT-PIPE-001: the view-layout domain is implemented but UNPROVEN — closure needed (the #605 methodology)

The font domain was closed once and for all (#605: 181 models, 3 batteries, both worlds). The SAME audit applied to the **view-layout domain** (the placement of buttons, texts, labels, scrolls, images — measure/layout/gravity) shows the engine is implemented far beyond what any battery proves.

### Coverage matrix (audit result)

| surface | implemented | proven by battery |
|---|---|---|
| MeasureSpec / getChildMeasureSpec | yes | **yes** — linear_layout_law (25 checks) |
| LinearLayout weights/margins/GONE/nested | yes | **yes** |
| FrameLayout child gravity (subset) | yes | **yes** — g10 (3 rows) |
| ScrollView scroll STATE (scrollTo/By, translation) | yes | **yes** — s98 (14) |
| requestLayout dirty flags | yes | **yes** — s106 |
| **ScrollView CONTENT measure law** (child height UNSPECIFIED → content grows past viewport, then viewport clamp) | partial | **NO rows anywhere** |
| **HorizontalScrollView** width law | partial | **NO** |
| **ImageView scaleType geometry** (fitXY/centerCrop/fitCenter/centerInside box math) | yes — `scale_image_rect` | **NO** |
| **TextView → box law** (wrap, maxLines, line_height from the CLOSED font metrics, vertical gravity of text in its box) | partial | **NO** |
| **RelativeLayout rules** (below/above/toRightOf/alignParent*/centerInParent) | parsed + consumed | **NO** |
| **GridLayout cell placement** | classifier only | **NO** |
| **Composite screens** (form: header+input+button-row; list: scroll+rows; profile: relative card) | — | **NO** |
| RTL row order (`layoutDirection="rtl"`) | ? | **NO** |

### Why this matters
Every app whose UI stopped at "text renders" still breaks at "text is IN THE RIGHT PLACE". The dominant crash classes reported on real apps (Dooz keypad collapse, compose-surface 1×1 kill) were all layout-law violations caught by accident, not by a standing battery.

### The standard to satisfy (pure AOSP, no shortcuts)
- `ViewGroup.getChildMeasureSpec` (spec-pure negotiation, padding/margin subtraction)
- `LinearLayout.measureHorizontal/Vertical` + `WeightedSum` distribution incl. overweight shrink + weightSum cap
- `FrameLayout.onLayout` gravity math (child_gravity, foreground, oversized clamp)
- `ScrollView.onMeasure`: child measured `MeasureSpec.UNSPECIFIED` height, viewport clamp at layout
- `ImageView` scaleType matrix laws (`scale_image_rect` is the engine's word-for-word candidate)
- `RelativeLayout` dependency graph resolve (topological, `RelayGroup`) with alignParent/below/centerInParent
- `GridLayout` spec/cell placement
- RTL: `layoutDirection` flips horizontal order (View.LAYOUT_DIRECTION_RTL)

### The deliverable (acceptance criteria)
1. `tests/s246_layout_closure_law_test.cpp` — ≥60 laws over the gap rows above, each asserting the AOSP law (world-independent, conditional rows honest like s245 G-groups).
2. My own simple test programs (synthetic but realistic screens: login form, scrolling list, profile card with relative rules, image viewer, dashboard grid) — each must land where a real device lands, within tolerance.
3. Every real bug found → fixed in the engine (loud fix comments referencing the law), never patched in the battery.
4. Both-world honesty (empty-font world still lays out boxes — fonts are CLOSED, layout must not regress under it).
5. Gates: battery green + binary RC=0 + test-all green + parity green; closure receipt on THIS issue; `FONT DOMAIN CLOSED`-style verdict: **LAYOUT DOMAIN CLOSED**."""
req = urllib.request.Request("https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues",
    data=json.dumps({"title": "LAYOUT-PIPE-001: view-layout domain closure — gravity/scroll/image/text/relative/grid placement laws (the #605 methodology)",
                     "body": B,
                     "labels": ["layout", "law-battery", "closure"]}).encode(),
    headers={"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json", "User-Agent": "layout-audit"},
    method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    d = json.loads(r.read().decode())
    print("ISSUE", d["number"], d["html_url"])
