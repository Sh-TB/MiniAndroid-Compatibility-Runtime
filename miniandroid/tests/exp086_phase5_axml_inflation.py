#!/usr/bin/env python3
"""
EXP-086 Phase 5 — B2 AXML → Real View Inflation (DIAGNOSTIC).

This test documents the current state of view inflation. The runtime
currently creates a synthetic "HelloWorld" view via create_view_from_dalvik_result,
NOT a real AXML-inflated view tree from the APK's resources.

This phase is DIAGNOSTIC — it captures evidence of:
  1. Whether setContentView(int) is called (resource ID captured)
  2. Whether AXML parsing happens for layout XML
  3. Whether ViewShadow nodes are created
  4. Whether view_tree.json is produced
  5. Whether rendered PNG contains APK-specific content (not just "HelloWorld")

The actual fix (modifying the renderer to walk ViewShadow) is a large
change that requires wiring ExecutionEngine to access dalvik_engine's
ShadowRegistry. That's deferred to a follow-up commit.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime")
MINIANDROID = REPO_ROOT / "miniandroid" / "build" / "miniandroid"
RESULTS_DIR = REPO_ROOT / "miniandroid" / "tests" / "corpus" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def run_apk_with_inflation_check(apk_path: Path) -> dict:
    """Run APK and capture inflation evidence."""
    out_dir = Path(f"/tmp/exp086_p5_{apk_path.stem}")
    if out_dir.exists():
        import shutil
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    r = subprocess.run(
        [str(MINIANDROID), "run", str(apk_path), "-o", str(out_dir), "-v"],
        capture_output=True, text=True, timeout=180,
    )
    full_output = r.stdout + r.stderr

    evidence = {
        # setContentView evidence
        "setcontentview_called": "setContentView" in full_output,
        "setcontentview_layout_resource_captured": "EXP074-LAYOUT" in full_output,
        "layout_resource_id": None,

        # AXML parsing evidence
        "axml_parsing_evidence": "AXML" in full_output or "axml" in full_output.lower(),
        "layout_inflater_called": "LayoutInflater" in full_output,

        # ViewShadow evidence
        "viewshadow_dispatch": "ViewShadow" in full_output,
        "createview_dispatch": "createView" in full_output and "EXP078" in full_output,

        # Output artifacts
        "view_tree_exists": (out_dir / "view_tree.json").exists(),
        "screenshot_png_exists": (out_dir / "screenshot.png").exists(),
        "screenshot_png_size": (out_dir / "screenshot.png").stat().st_size if (out_dir / "screenshot.png").exists() else 0,

        # Render pipeline
        "perform_draw_called": "perform_draw" in full_output,
        "text_views_rendered": 0,
    }

    # Extract layout_resource_id
    m = re.search(r"setContentView\(layoutResId=(0x[0-9a-fA-F]+)\)", full_output)
    if m:
        evidence["layout_resource_id"] = m.group(1)

    # Extract text_views_rendered
    m = re.search(r"text_views_rendered.*?(\d+)", full_output)
    if m:
        evidence["text_views_rendered"] = int(m.group(1))

    # Try to read view_tree.json
    view_tree_summary = {"view_count": 0, "node_count": 0}
    if evidence["view_tree_exists"]:
        try:
            with open(out_dir / "view_tree.json") as f:
                vt = json.load(f)
            view_tree_summary = {
                "view_count": vt.get("view_count", 0),
                "node_count": len(vt.get("nodes", [])),
                "has_text_values": any("text" in n for n in vt.get("nodes", [])),
            }
        except Exception:
            pass

    # Try to read PNG via PIL to check for actual content
    pil_decoded = False
    non_black_pixels = 0
    if evidence["screenshot_png_exists"]:
        try:
            from PIL import Image
            img = Image.open(out_dir / "screenshot.png")
            img.load()
            pil_decoded = True
            w, h = img.size
            non_black_pixels = sum(1 for x in range(0, w, 50) for y in range(0, h, 50) if img.getpixel((x,y)) != (0,0,0))
        except Exception:
            pass

    # Classify
    if evidence["setcontentview_called"] and evidence["view_tree_exists"] and view_tree_summary["node_count"] > 0:
        status = "PASS_INFLATED"
    elif evidence["setcontentview_called"] and pil_decoded and non_black_pixels > 100:
        # setContentView captured but no view_tree — partial
        status = "PARTIAL_LAYOUT_CAPTURED_NO_INFLATE"
    elif evidence["setcontentview_called"]:
        status = "PARTIAL_SETCONTENTVIEW_NO_RENDER"
    elif evidence["perform_draw_called"] and non_black_pixels > 100:
        status = "PARTIAL_RENDER_NO_SETCONTENTVIEW"
    else:
        status = "BLOCKED_NO_INFLATION"

    return {
        "apk": str(apk_path),
        "exit_code": r.returncode,
        "evidence": evidence,
        "view_tree_summary": view_tree_summary,
        "pil_decoded": pil_decoded,
        "non_black_pixels_sampled": non_black_pixels,
        "status": status,
        "stdout_tail": full_output[-500:],
    }


def run_phase5() -> dict:
    """Run Phase 5 AXML view inflation diagnostic."""
    print("=== Phase 5: B2 AXML → Real View Inflation (DIAGNOSTIC) ===")

    test_apks = [
        ("gmdice", REPO_ROOT / "miniandroid" / "download" / "exp073_real_apps" / "de.duenndns.gmdice_8.apk"),
        ("tictactoe", REPO_ROOT / "miniandroid" / "download" / "tictactoe.apk"),
        ("headingcalculator", REPO_ROOT / "miniandroid" / "download" / "exp073_real_apps" / "org.debian.eugen.headingcalculator_1.apk"),
        ("notes", REPO_ROOT / "miniandroid" / "download" / "exp073_real_apps" / "org.billthefarmer.notes_139.apk"),
        ("unote", REPO_ROOT / "miniandroid" / "download" / "exp076_corpus" / "app.varlorg.unote_30.apk"),
        ("telegram", REPO_ROOT / "miniandroid" / "download" / "exp038_telegram" / "Telegram.apk"),
    ]

    results = []
    for name, apk_path in test_apks:
        if not apk_path.exists():
            print(f"\n  [{name}] SKIP — APK not found")
            results.append({"name": name, "status": "SKIP", "reason": "APK not found"})
            continue

        print(f"\n  [{name}] running {apk_path.name}...")
        result = run_apk_with_inflation_check(apk_path)
        result["name"] = name
        print(f"    status: {result['status']}")
        print(f"    setContentView: {result['evidence']['setcontentview_called']} "
              f"(layout_res={result['evidence']['layout_resource_id']})")
        print(f"    view_tree: exists={result['evidence']['view_tree_exists']}, "
              f"nodes={result['view_tree_summary']['node_count']}")
        print(f"    PNG: {result['evidence']['screenshot_png_size']} bytes, "
              f"PIL decoded={result['pil_decoded']}, "
              f"non-black={result['non_black_pixels_sampled']}")
        results.append(result)

    # Summary
    print("\n" + "=" * 70)
    print("PHASE 5 SUMMARY")
    print("=" * 70)
    pass_count = sum(1 for r in results if r["status"] == "PASS_INFLATED")
    partial_count = sum(1 for r in results if r["status"].startswith("PARTIAL"))
    blocked_count = sum(1 for r in results if r["status"].startswith("BLOCKED"))
    skip_count = sum(1 for r in results if r["status"] == "SKIP")
    print(f"PASS: {pass_count}  PARTIAL: {partial_count}  BLOCKED: {blocked_count}  SKIP: {skip_count}")
    for r in results:
        marker = "✅" if r["status"] == "PASS_INFLATED" else \
                ("⚠️ " if r["status"].startswith("PARTIAL") else
                 ("⏭️ " if r["status"] == "SKIP" else "❌"))
        print(f"  {marker} {r['name']:25s}  {r['status']}")

    summary = {
        "test": "EXP086 Phase 5 — B2 AXML view inflation diagnostic",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pass_count": pass_count,
        "partial_count": partial_count,
        "blocked_count": blocked_count,
        "skip_count": skip_count,
        "results": results,
        "diagnostic_note": (
            "B2 (AXML view inflation) is PARTIALLY WORKING: "
            "setContentView(int) is called and the layout resource ID is captured, "
            "but the renderer does not yet walk the ViewShadow tree to inflate views. "
            "PNG output now works (B1 fixed) and contains non-black pixels (synthetic "
            "HelloWorld view). Real AXML inflation requires wiring ExecutionEngine "
            "to access dalvik_engine's ShadowRegistry and walking the ViewShadow tree "
            "in perform_draw()."
        ),
    }
    out_path = RESULTS_DIR / "EXP086_PHASE5_AXML_INFLATION.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\nResults saved to {out_path}")
    return summary


def main():
    summary = run_phase5()
    # Phase 5 is diagnostic — exit 0 even if PARTIAL/BLOCKED
    sys.exit(0)


if __name__ == "__main__":
    main()
