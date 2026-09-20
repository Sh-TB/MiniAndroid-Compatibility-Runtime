"""s70_register_s67_s69_fixes.py — back-register S67/S69 F-numbers + A/C gaps.

S70 audit finding: the §17 law ("every F-number needs a regression record")
presumed registry completeness, but the S67 hardening wave (commit 62402341)
and S69's F-135 never entered root_registry.json — they lived only in the
matrix docs + commit messages. Same registry↔docs split as R-NEW-388/A7.
This restores single-source-of-truth: every campaign F-number is a registry
root with its full evidence chain (text from the commit message / session
ledger, byte-for-byte provenance).
"""
import json
from pathlib import Path

REG = Path("/home/z/my-project/root_registry.json")
reg = json.loads(REG.read_text())
ids = {r["id"] for r in reg["roots"]}

new = [
    {"id": "F-121", "priority": "P1",
     "title": "click-probe must drain pending intent/finish before re-render",
     "evidence": "AOSP Looper queue law; S67 commit 62402341: --dump-view-tree; "
                 "F-121 click-probe drains pending intent/finish before re-render "
                 "per AOSP Looper law; foundation battery fixture f27_nav PASS."},
    {"id": "F-122", "priority": "P1",
     "title": "Color.rgb/argb/parseColor static factories were REC-MISS→0→invisible",
     "evidence": "OpenJDK/AOSP Color.java law (argb channels, alpha=255 for rgb); "
                 "S67 commit 62402341; silent-wrong at smallest primitive with "
                 "fan-out to every custom-drawing app; f01_color/f08 pixel-proof."},
    {"id": "F-123", "priority": "P1",
     "title": "drawRoundRect AOSP arg order (l,t,r,b,rx,ry,PAINT) + real radius",
     "evidence": "AOSP Canvas.drawRoundRect parameter law; S67 commit 62402341; "
                 "f08_canvasops per-op pixel census PASS."},
    {"id": "F-124", "priority": "P1",
     "title": "XML visibility enum space {0,1,2}→View {0,4,8}",
     "evidence": "AOSP View.java visibility constants law (VISIBLE/INVISIBLE/GONE); "
                 "S67 commit 62402341; f06_invisible all-white-frame PASS."},
    {"id": "A2", "priority": "P1",
     "title": "getDimensionPixelSize args[1]-not-this + ARSC-first + "
              "complexToDimensionPixelSize (100dp→263px exact)",
     "evidence": "AOSP TypedValue.complexToDimensionPixelSize + display metrics law; "
                 "S67 commit 62402341; f32_dimen PX=263 PASS (AOSP exact)."},
    {"id": "A4", "priority": "P1",
     "title": "INVISIBLE own-content gate (children render per dispatchDraw)",
     "evidence": "AOSP View.dispatchDraw/invisibility law; S67 commit 62402341; "
                 "f06_invisible PASS."},
    {"id": "C3", "priority": "P1",
     "title": "horizontal-LL cross-axis TOP(0x30) was centered",
     "evidence": "AOSP LinearLayout cross-axis gravity law; S67 commit 62402341; "
                 "f18_lltop child y=0 PASS."},
    {"id": "F-135", "priority": "P0",
     "title": "OpenJDK NaN/infinite/compare family (Double/Float isNaN, isInfinite, "
              "compare) — 694 static sites × 7 APKs, bouncy 480× STUB→IMPL",
     "evidence": "OpenJDK Double.java isNaN:1031 (v!=v), isInfinite:1048 (abs>MAX), "
                 "compare:1538 canonical-bits ordering NaN>+Inf / -0.0<+0.0; "
                 "Float.java:631/:1324. S69 commit b88e09d9: generic implementation "
                 "in dalvik_engine.cpp; micro fixture f52_nanlaw (9 rows, NaN/±Inf "
                 "PRODUCED via IEEE div, exact-color assertions, 9/9); determinism "
                 "×3 byte-identical; regression 22/22 fixtures + battery 92/94 + "
                 "canonical corpus frames byte-identical; bouncy frames byte-stable. "
                 "Oracle: docs/foundation/upstream_oracle.json F-135-* records."},
]
added = 0
for n in new:
    if n["id"] not in ids:
        reg["roots"].append({
            "id": n["id"], "status": "ROOT-CAUSED-FIXED", "priority": n["priority"],
            "title": n["title"], "fg": True,
            "first_seen": "S67 hardening wave (62402341)" if not n["id"].startswith("F-135")
                          else "S69 source-linked campaign (b88e09d9)",
            "evidence": n["evidence"],
        })
        added += 1
reg["note"] = reg.get("note", "") + (
    f" | S70: S67/S69 F-numbers back-registered (F-121..F-124, A2, A4, C3, F-135); "
    f"registry {len(reg['roots'])} roots.")
if added:
    REG.write_text(json.dumps(reg, indent=1))
print(f"registered {added}: registry now {len(reg['roots'])} roots")
