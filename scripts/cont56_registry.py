#!/usr/bin/env python3
"""cont56_registry.py — CONT-56 registry update (638 -> 639).

F-NEW-328: ROOT-CAUSED-FIXED — the framework LinearLayout.onMeasure SUPER
law. A DEX subclass of LinearLayout (the appcompat AppBarLayout family —
every ActionBar/Toolbar host) invokes super.onMeasure on the FRAMEWORK
class (no DEX body). The S109 ROOT-042 bridge law claimed the call but
diverged from AOSP twice: (a) the child-spec source read the node's legacy
width/height mirrors instead of the LayoutParams (lp_width/lp_height) —
every programmatic child measured EXACTLY(parent) on BOTH axes regardless
of its real lp; (b) the container self-size initialized to the FULL spec
size and max()'d children in — every AT_MOST (wrap-content) container
answered the FULL available size and the vertical SUM law never existed.
Runtime face: the solitaire Toolbar measured 0 wide, its nav ImageButton
became a 0-width untappable target (F117-TAP target=0/189 fallthrough),
the drawer — and the whole menu-content pipeline — was unreachable BY
INPUT.
"""
import json

REG = "/home/z/my-project/root_registry.json"

with open(REG) as f:
    reg = json.load(f)
roots = reg["roots"] if isinstance(reg, dict) and "roots" in reg else reg

existing_ids = {r["id"] for r in roots}
assert "F-NEW-328" not in existing_ids, "ID collision — check upstream first"
assert len(roots) == 638, f"expected 638 roots, got {len(roots)}"

roots.append({
    "id": "F-NEW-328",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "layer": "framework/measure-linearlayout-super",
    "title": "The framework LinearLayout.onMeasure SUPER law diverged from AOSP at two points: (a) the child-spec source read the node's legacy width/height mirrors instead of the LayoutParams (lp_width/lp_height — the programmatic addView law ViewShadow::set_layout_params writes lp_*, the [EXP095-ADDVIEW-LP] shape), so every programmatic child measured EXACTLY(parent) on BOTH axes regardless of its real lp; (b) the container self-size initialized mw/mh to the FULL spec size and max()'d children in — every AT_MOST (wrap-content) container answered the FULL available size and the vertical/horizontal SUM laws never existed. Face: the solitaire Toolbar measured 0 wide (its nav ImageButton a 0-width untappable target; every F117-TAP fell through to the DrawerLayout, target=189), the appcompat AppBarLayout super pass answered the raw spec (1080x1920), and the drawer menu-content pipeline stayed unreachable BY INPUT. Generic blast radius: every DEX LinearLayout subclass host (AppBarLayout/Toolbar apps, programmatic LinearLayout UIs).",
    "root_cause": "Stacked, class-agnostic: (1) LP-SOURCE — the S109 child-spec law (BOTH copies: the bridge S109 ROOT-042 onMeasure site and the R347 measure-wrapper ROOT-045 recursion) read cn->width/height; the programmatic lp lives in cn->lp_width/lp_height (INT_MIN sentinel when unset) — the addView lp write-back never reached the spec source. (2) SELF-SIZE — the S109-VG container answer initialized to spec and max()'d children (AOSP: EXACTLY -> spec; AT_MOST -> min(want, specSize); UNSPECIFIED -> want, with want = the orientation law: vertical sum-of-heights/max-of-widths, horizontal sum-of-widths/max-of-heights, margins+padding included). FIX (F-NEW-328, both sites): child_dim_of = lp_* authoritative (non-INT_MIN) with the legacy mirror fallback; the LinearLayout self law implemented per AOSP (orientation from the EXP-095 node field; the other families keep their legacy self answer — their own decode cycles own any change). No app knowledge; the framework container semantics only. A ViewShadow-level wall law was attempted FIRST and proved DEAD CODE for this path (the bridge claims onMeasure before any shadow dispatch) — reverted with the proof recorded.",
    "next_wave": "Probe fnew328_probe.apk 1cd25382d8a29a35 (real aapt2/ECJ/D8; a DEX LinearLayout subclass (vertical MyBar + horizontal MyRow) whose onMeasure calls super then REPORTS self+child measured values — the exact AppBarLayout read-back shape): PRE x1 on the CONT-55 binary 1f81036989a12a7d = P1/P2/P3 FAIL (self=1080x1920 child=1080x1920 — the raw getDefaultSize face); POST x3 on 11e5fa2c3b4b5037 = 4/0 x3 (P1 self=1080x48 child=1080x48 wrap; P2 self=100x50 horizontal sum; P3 EXACTLY keeps spec with childH=48; N1 sanity). Solitaire runtime at POST: AppBarLayout 1080x105 (was 1080x1920 — the appbar's DEX reshape now reads real child values); NavigationView/NavigationMenuView y=2025 (was y=3840 — the drawer stacking still sequential, the DrawerLayout child-edge law still open); the VISIBLE frame UNCHANGED ba50a4d28ea62fe7 (the closed drawer's pixels sit off-screen). Zero-drift gate on 11e5fa2c3b4b5037: 15 canonical anchors/controls x3 = 45/45 MATCH (dooz 31ddd4d5, micro da73010a, unote 4f1a9e4e, gmdice f3b483fe, opencalc a976d2f9, ttt af609429, flappy 13cf4746, g2048 59ca1526, tanana 5f7e0114, csw 3442d9a9, simplecalc e847ca03, BMI b52252c2, alex c8d69f81, notes eb5ebd55, sol ba50a4d2); probe battery == records (fnew326 13/0, fnew326b 13/0, fnew327 3/0) + fnew328 4/0 x3. NEW frontier: the Toolbar's OWN DEX onMeasure still answers 0 wide (the support Toolbar DEX body divergence — its child measure leg measureChildWithMargins + the spec-mode arithmetic; the nav-button width chain), then the DrawerLayout child-edge layout law (NavigationView pinned at the drawer edge, y=0, full height — not sequential stacking at y=2025).",
    "evidence": "evidence/cont56/CONT56_RESULT.md",
})

for r in roots:
    if r["id"] == "F-NEW-309":
        prev = r.get("evidence", "")
        r["evidence"] = (prev.rstrip() + "; evidence/cont56/CONT56_RESULT.md"
                         if prev else "evidence/cont56/CONT56_RESULT.md")

reg["count"] = len(roots)
reg["total"] = len(roots)
from collections import Counter
reg["status_counts"] = dict(Counter(x.get("status", "UNKNOWN") for x in roots))
reg["meta"] = reg.get("meta", {})
reg["meta"]["last_update"] = ("CONT-56 session 2026-10-12: the framework "
    "LinearLayout.onMeasure SUPER law (F-NEW-328) — the lp-aware child-spec source "
    "(lp_width/lp_height authoritative over the legacy mirrors) + the AOSP "
    "orientation self-size law (sum/max, AT_MOST clamps) at BOTH S109 sites. Probe "
    "fnew328 PRE FAIL x1 (self=1080x1920 child=1080x1920) -> POST 4/0 x3. Solitaire: "
    "AppBarLayout 1080x1920 -> 1080x105; visible frame unchanged ba50a4d2. Zero-drift "
    "15 anchors x3 (45/45) + probe battery == records. Registry 638->639.")
reg["meta"]["last_updated"] = "2026-10-12 F-NEW-328 ROOT-CAUSED-FIXED at binary 11e5fa2c3b4b5037"

json.dump(reg, open(REG, "w"), indent=1, ensure_ascii=False)
print("registry updated: 638 -> 639 (F-NEW-328 appended ROOT-CAUSED-FIXED)")
