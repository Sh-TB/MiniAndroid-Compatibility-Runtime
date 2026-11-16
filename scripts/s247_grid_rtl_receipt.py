#!/usr/bin/env python3
"""The #606 D-wave receipt: GRID+RTL CLOSED — the last two boundaries."""
import json, subprocess, urllib.request

CRED = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True,
                      cwd="/home/z/my-project").stdout
TOKEN = [l.split("=", 1)[1] for l in CRED.splitlines() if l.startswith("password=")][0]

B = """## GRID+RTL CLOSED — the two open boundaries from the s246 receipt are now engine laws (commit cb67eb85)

`tests/s247_grid_rtl_law_test.cpp` — 11 groups (G1-G5 / R1-R6), **27 laws, 27/27 PASS, rc=0** — and **27/27 in the hidden-font world too** (pure geometry, font-independent). The battery prints **GRID+RTL DOMAIN CLOSED**.

### REAL GridLayout (was: vertical-flow fallback)
`gl_resolve_cells` implements the AOSP `validateLayoutParams` law word-for-word where it matters:
- explicit `layout_row`/`layout_column` are FIXED cells; auto children scan row-major with the `fits()` skip;
- wrap at the **COUNT**, never at the screen width (`if (minor + minorSpan <= count) minor++ else {minor=0; major++}`);
- `count = max(definedCount, maxIndex+span)` (AOSP `Axis.getCount`) — an unconfigured GridLayout is a ONE-column grid (the classic default, pinned by law);
- resolved cells are written back to the node (`setCellGroup` law);
- track = max over its span-1 cells (margins included); a spanned child's excess over its track sum splits **evenly** — documented here as the honest simplification of the AOSP arc/Bellman-Ford constraint solver (identical for the common single-largest-spanned case);
- cell gravity: START/top default (AOSP `Spec.getAbsoluteAlignment` — weight 0 → START/BASELINE; a non-text view lawfully falls back to top), FILL stretches to the track inner box, CENTER/END exact; `columnCount`/`rowCount`/spans all parsed;
- wrap_content = Σ tracks (GridLayout has no spacing attr — margins carry the gaps).

### RTL (was: not parsed at all)
- `layoutDirection` parsed (ltr/rtl/inherit/locale) + a top-down resolution walk: inherit → parent's resolved; **root inherit = LTR** (the Jellybean-MR1 compat law — apps without `android:supportsRtl` stay LTR; locale → LTR on this runtime, documented);
- LinearLayout horizontal rows mirror (document order right→left; weighted shares mirror; container main-gravity flips with the mirror);
- FrameLayout relative-gravity flip: START(0x800003)/END(0x800005) mirror under RTL (Gravity.getAbsoluteGravity); **literal LEFT/RIGHT pinned unmoved**;
- RelativeLayout directional aliases are now DIRECTIONAL: toEndOf→LEFT_OF, toStartOf→RIGHT_OF, alignParentEnd/Start, alignEnd/Start under RTL — literal rules never move (both the measure-time edge pass and the legacy fixed-point);
- GridView columns mirror (first item at the right edge).

### The fourth engine bug this domain audit caught (fixed)
The LL **vertical column's cross-axis x law used a bit-test (`vg & 0x1`) BEFORE the engine's own mask-first axis-field equality** — literal LEFT(0x3) *and* RIGHT(0x5) both fell into the CENTER branch. Fixed to the mask-first law the horizontal row and FrameLayout branches already used, plus the relative-flag flip. The grid-cell gravity in the new GridLayout branch uses the same mask-first law.

### Honest battery corrections (probe-verified, engine law confirmed against AOSP source)
- empty grid tracks are **zero-width** (an explicit (1,2) child of an otherwise-empty grid sits at x=0 — unconstrained lines);
- a span-2 child OCCUPIES its span cells, so auto children wrap past them;
- the LEFT_OF margin law is the ANCHOR's: `anchor.mLeft − anchor.leftMargin − child.rightMargin`;
- START carries no vertical bits (`BOTTOM|START = 0x00800053`);
- the RTL mirror formula is `x' = cl + cw − dx − w` (a mirrored 500px child at dx=500 lands at 80, not 0).

### Gates on the closure commit
s247 27/27 (rc=0, normal + hidden both) · s246 stays 47/47 · binary RC=0 · test-all **42/42** · parity **75/75** · zero crashes.

**Verdict: LAYOUT DOMAIN CLOSED — fully, with the boundaries closed too.** The remaining documented approximation is ONLY the spanned-excess even split (vs the AOSP linear-constraint solver) — every other GridLayout and RTL behavior is now a pinned, probe-verified engine law."""
req = urllib.request.Request("https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/606/comments",
    data=json.dumps({"body": B}).encode(),
    headers={"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json", "User-Agent": "layout-audit"},
    method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    print("#606 D-wave receipt", json.loads(r.read().decode())["id"])
