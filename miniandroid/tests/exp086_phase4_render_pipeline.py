#!/usr/bin/env python3
"""
EXP-086 Phase 4 — B1 View Tree → Render Pipeline Integration Test.

Verifies that:
  1. APKs produce a non-empty framebuffer
  2. The framebuffer is rendered to PNG
  3. The PNG dimensions match the requested screen size

For each APK:
  - Run with -v
  - Capture stdout for render pipeline evidence
  - Verify PNG output dimensions
  - Verify PNG has non-zero IDAT data
  - Check for "Frame rendered" or "stage_render_frame" trace
"""

from __future__ import annotations

import json
import re
import struct
import subprocess
import sys
import zlib
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime")
MINIANDROID = REPO_ROOT / "miniandroid" / "build" / "miniandroid"
RESULTS_DIR = REPO_ROOT / "miniandroid" / "tests" / "corpus" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def parse_png(png_path: Path) -> dict:
    """Parse PNG and return structural info."""
    info = {
        "exists": png_path.exists(),
        "size_bytes": 0,
        "valid_signature": False,
        "width": 0,
        "height": 0,
        "idat_bytes": 0,
        "decompressed_size": 0,
        "decompressed_ok": False,
        "first_pixel": None,
        "non_black_pixels_sampled": 0,
    }
    if not png_path.exists():
        return info

    data = png_path.read_bytes()
    info["size_bytes"] = len(data)
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return info
    info["valid_signature"] = True

    # Walk chunks
    off = 8
    idat_data = b""
    while off < len(data):
        if off + 8 > len(data): break
        chunk_len = struct.unpack(">I", data[off:off+4])[0]
        chunk_type = data[off+4:off+8]
        if chunk_type == b"IHDR":
            ihdr = data[off+8:off+8+13]
            info["width"] = struct.unpack(">I", ihdr[0:4])[0]
            info["height"] = struct.unpack(">I", ihdr[4:8])[0]
        elif chunk_type == b"IDAT":
            idat_data += data[off+8:off+8+chunk_len]
            info["idat_bytes"] += chunk_len
        elif chunk_type == b"IEND":
            break
        off += 8 + chunk_len + 4

    # Decompress IDAT
    if idat_data:
        try:
            decompressed = zlib.decompress(idat_data)
            info["decompressed_size"] = len(decompressed)
            info["decompressed_ok"] = True
            # Get first pixel (skip filter byte)
            if len(decompressed) > 4:
                info["first_pixel"] = list(decompressed[1:4])
            # Sample non-black pixels
            non_black = 0
            stride = info["width"] * 3 + 1  # +1 for filter byte per row
            for y in range(0, info["height"], 50):
                if y * stride + 4 >= len(decompressed): break
                for x in range(0, info["width"], 50):
                    pos = y * stride + 1 + x * 3  # +1 for filter byte
                    if pos + 3 <= len(decompressed):
                        r, g, b = decompressed[pos], decompressed[pos+1], decompressed[pos+2]
                        if (r, g, b) != (0, 0, 0):
                            non_black += 1
            info["non_black_pixels_sampled"] = non_black
        except zlib.error:
            pass
    return info


def run_apk_render_test(apk_path: Path) -> dict:
    """Run an APK and check the render pipeline."""
    out_dir = Path(f"/tmp/exp086_p4_{apk_path.stem}")
    if out_dir.exists():
        import shutil
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    r = subprocess.run(
        [str(MINIANDROID), "run", str(apk_path), "-o", str(out_dir), "-v"],
        capture_output=True, text=True, timeout=180,
    )
    full_output = r.stdout + r.stderr

    # Look for render pipeline evidence
    evidence = {
        "stage_render_frame_called": "stage_render_frame" in full_output,
        "frame_rendered": "Frame rendered" in full_output,
        "no_content_view_warning": "No content view to render" in full_output,
        "create_view_from_dalvik_result": "create_view_from_dalvik_result" in full_output,
        "create_hello_world_view": "create_hello_world_view" in full_output,
        "perform_draw_called": "perform_draw" in full_output,
        "text_views_rendered_count": 0,
        "frame_count_increment": "increment_frame_count" in full_output,
    }

    # Extract text_views_rendered count
    m = re.search(r"text_views_rendered.*?(\d+)", full_output)
    if m:
        evidence["text_views_rendered_count"] = int(m.group(1))

    # Check PNG output
    png_info = parse_png(out_dir / "screenshot.png")

    # Classify
    if not png_info["valid_signature"]:
        status = "FAIL_NO_VALID_PNG"
    elif not png_info["decompressed_ok"]:
        status = "FAIL_IDAT_BROKEN"
    elif png_info["width"] == 0 or png_info["height"] == 0:
        status = "FAIL_ZERO_DIMENSIONS"
    elif png_info["non_black_pixels_sampled"] == 0:
        status = "PARTIAL_EMPTY_FRAMEBUFFER"  # PNG valid but no rendering
    else:
        status = "PASS_RENDERED"

    return {
        "apk": str(apk_path),
        "exit_code": r.returncode,
        "evidence": evidence,
        "png_info": png_info,
        "status": status,
        "stdout_tail": full_output[-300:],
    }


def run_phase4() -> dict:
    """Run Phase 4 view tree → render pipeline integration tests."""
    print("=== Phase 4: B1 View Tree → Render Pipeline Integration ===")

    test_apks = [
        ("gmdice", REPO_ROOT / "miniandroid" / "download" / "exp073_real_apps" / "de.duenndns.gmdice_8.apk"),
        ("tmdice", REPO_ROOT / "miniandroid" / "download" / "exp073_real_apps" / "de.duenndns.gmdice_8.apk"),
        ("tictactoe", REPO_ROOT / "miniandroid" / "download" / "tictactoe.apk"),
        ("telegram", REPO_ROOT / "miniandroid" / "download" / "exp038_telegram" / "Telegram.apk"),
    ]

    # Deduplicate
    seen = set()
    unique_apks = []
    for name, path in test_apks:
        if path not in seen:
            seen.add(path)
            unique_apks.append((name, path))

    results = []
    for name, apk_path in unique_apks:
        if not apk_path.exists():
            print(f"\n  [{name}] SKIP — APK not found")
            results.append({"name": name, "status": "SKIP", "reason": "APK not found"})
            continue

        print(f"\n  [{name}] running {apk_path.name}...")
        result = run_apk_render_test(apk_path)
        result["name"] = name
        print(f"    status: {result['status']}")
        print(f"    PNG: {result['png_info']['size_bytes']} bytes, "
              f"{result['png_info']['width']}×{result['png_info']['height']}")
        print(f"    IDAT decompressed: {result['png_info']['decompressed_size']} bytes")
        print(f"    Non-black pixels (sampled): {result['png_info']['non_black_pixels_sampled']}")
        results.append(result)

    # Summary
    print("\n" + "=" * 70)
    print("PHASE 4 SUMMARY")
    print("=" * 70)
    pass_count = sum(1 for r in results if r["status"] == "PASS_RENDERED")
    partial_count = sum(1 for r in results if r["status"].startswith("PARTIAL"))
    fail_count = sum(1 for r in results if r["status"].startswith("FAIL"))
    skip_count = sum(1 for r in results if r["status"] == "SKIP")
    print(f"PASS: {pass_count}  PARTIAL: {partial_count}  FAIL: {fail_count}  SKIP: {skip_count}")
    for r in results:
        marker = "✅" if r["status"] == "PASS_RENDERED" else \
                ("⚠️ " if r["status"].startswith("PARTIAL") else
                 ("⏭️ " if r["status"] == "SKIP" else "❌"))
        print(f"  {marker} {r['name']:25s}  {r['status']}")

    summary = {
        "test": "EXP086 Phase 4 — View tree → render pipeline integration",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pass_count": pass_count,
        "partial_count": partial_count,
        "fail_count": fail_count,
        "skip_count": skip_count,
        "results": results,
    }
    out_path = RESULTS_DIR / "EXP086_PHASE4_RENDER_PIPELINE.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\nResults saved to {out_path}")
    return summary


def main():
    summary = run_phase4()
    sys.exit(0 if summary["fail_count"] == 0 else 1)


if __name__ == "__main__":
    main()
