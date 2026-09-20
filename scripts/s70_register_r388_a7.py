#!/usr/bin/env python3
"""s70_register_r388_a7.py — register R-NEW-388 + A7 into root_registry.json.

S70 finding: both were tracked ONLY in docs/foundation/FOUNDATION_GAP_MATRIX.md
(S66/S67/S69 session records) — the canonical root registry (source of
failure_index.json) never received them. Registry and campaign docs disagreed
about what is registered. This restores single-source-of-truth law: every
campaign-visible gap lives in root_registry.json; the gap matrix may reference
but never substitute.

Evidence provenance for the two entries:
- R-NEW-388: S66 commit 289e33d3 message + FOUNDATION_GAP_MATRIX row +
  FOUNDATION_LAYOUT_MATRIX C1/C2 (TriPeaks RL geometry: upstream
  alignParent+margin idiom vs engine rl_cached_left→measured_left wiring gap +
  narrow-wrap overlap; card ImageViews collapsed at (0,0); painter proven
  faithful; TriPeaks PARTIAL).
- A7: FOUNDATION_GAP_MATRIX row (manifest label/icon: label REFERENCE
  resolves to "@0x…" raw string, icon unparsed; law = PackageParser
  label/icon resolve through ARSC; corpus-wide launcher identity wrong).
"""
import json
from pathlib import Path

REG = Path("/home/z/my-project/root_registry.json")
reg = json.loads(REG.read_text())
ids = {r["id"] for r in reg["roots"]}

new = [
    {
        "id": "R-NEW-388",
        "status": "ROOT-CAUSED-NOT-FIXED",
        "priority": "P1",
        "title": "TriPeaks card ImageViews collapsed at (0,0) — RL "
                 "alignParent+margin wiring gap",
        "fg": True,
        "first_seen": "S66 TriPeaks visual forensics (commit 289e33d3)",
        "evidence":
            "SOURCE (pinned TriPeaks@62f3609): board XML uses RelativeLayout "
            "alignParent* + margin idiom per card ImageView. TRACE: engine "
            "rl_cached_left → measured_left wiring gap + narrow-wrap overlap "
            "→ cards render collapsed at (0,0); painter proven faithful "
            "(canvas probe byte-identical). UPSTREAM: AOSP RelativeLayout "
            "applyHorizontalSizeRules/VerticalSizeRules (measure pass law). "
            "PLAN: source-linked geometry chain — inflate params → measure "
            "rules → measured_left/top wiring → render bounds; fixture first "
            "(RL margin+alignParent), then TriPeaks real APK, pixel proof, "
            "determinism ×3, regression battery. Evidence: "
            "docs/foundation/FOUNDATION_GAP_MATRIX.md; "
            "docs/foundation/FOUNDATION_LAYOUT_MATRIX.md (C1/C2); "
            "docs/evidence/visual_forensics/ (S66).",
    },
    {
        "id": "A7",
        "status": "ROOT-CAUSED-NOT-FIXED",
        "priority": "P2",
        "title": "Manifest label/icon — label REFERENCE unresolved, icon "
                 "unparsed (launcher identity wrong corpus-wide)",
        "fg": True,
        "first_seen": "S67 foundation matrix A-series (95040a39/75f62771 wave)",
        "evidence":
            "SOURCE: every APK manifest label of REFERENCE form resolves to "
            "the raw '@0x…' string; icon attribute never parsed. UPSTREAM "
            "LAW: AOSP PackageParser + Resources.resolveReference — label/"
            "icon resolve through ARSC (pkg-local + android: namespace "
            "fallback). IMPACT: launcher identity wrong for every corpus "
            "APK (visual: activity title bar / app label surfaces). PLAN: "
            "ARSC-first reference resolution reuse (A2 law path), fixture "
            "(f53_manifest_label), real APK proof, determinism ×3. Evidence: "
            "docs/foundation/FOUNDATION_GAP_MATRIX.md row A7.",
    },
]
added = 0
for n in new:
    if n["id"] not in ids:
        reg["roots"].append(n)
        added += 1

reg["note"] = reg.get("note", "") + (
    " | S70: R-NEW-388 + A7 registered from gap-matrix provenance "
    "(registry↔docs single-source-of-truth restored); registry 372→"
    f"{len(reg['roots'])} roots.")

if added:
    REG.write_text(json.dumps(reg, indent=1))
    print(f"registered {added}: registry now {len(reg['roots'])} roots")
else:
    print("nothing to add (already present)")
