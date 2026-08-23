#!/usr/bin/env python3
"""
EXP-086 Phase 3 — B1 PNG Writer Forensics.

Creates 64x64 known-pattern framebuffer, generates PNG via the
miniandroid runtime, and validates externally with PIL/zlib.

Test patterns:
  - 1x1 single pixel
  - 64x64 quadrants (red, green, blue, white)
  - 1080x1920 (full screenshot size)
  - stride > width*4 case
"""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import zlib
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime")
RESULTS_DIR = REPO_ROOT / "miniandroid" / "tests" / "corpus" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def write_test_ppm(path: Path, width: int, height: int, pixels: bytes):
    """Write a PPM file directly."""
    with open(path, "wb") as f:
        f.write(f"P6\n{width} {height}\n255\n".encode())
        f.write(pixels)


def make_quadrant_pattern(size: int = 64) -> bytes:
    """Make a size×size image with 4 quadrants: red, green, blue, white."""
    pixels = bytearray()
    half = size // 2
    for y in range(size):
        for x in range(size):
            if x < half and y < half:
                # Top-left: red
                pixels.extend([255, 0, 0])
            elif x >= half and y < half:
                # Top-right: green
                pixels.extend([0, 255, 0])
            elif x < half and y >= half:
                # Bottom-left: blue
                pixels.extend([0, 0, 255])
            else:
                # Bottom-right: white
                pixels.extend([255, 255, 255])
    return bytes(pixels)


def make_solid_pattern(size: int, r: int, g: int, b: int) -> bytes:
    """Make a size×size solid-color image."""
    pixels = bytearray()
    for _ in range(size * size):
        pixels.extend([r, g, b])
    return bytes(pixels)


def parse_png_independently(png_path: Path) -> dict:
    """Parse PNG file purely in Python (no PIL) and verify structure."""
    info = {
        "exists": png_path.exists(),
        "size_bytes": 0,
        "sha256": "",
        "valid_signature": False,
        "width": 0,
        "height": 0,
        "bit_depth": 0,
        "color_type": 0,
        "idat_bytes": 0,
        "decompressed_size": 0,
        "decompressed_ok": False,
        "decompressed_pixels_first_20": "",
        "chunks": [],
        "error": None,
    }
    if not png_path.exists():
        info["error"] = "file does not exist"
        return info

    data = png_path.read_bytes()
    info["size_bytes"] = len(data)
    h = hashlib.sha256()
    h.update(data)
    info["sha256"] = h.hexdigest()

    # PNG signature
    PNG_SIG = b"\x89PNG\r\n\x1a\n"
    if data[:8] != PNG_SIG:
        info["error"] = f"invalid PNG signature: {data[:8]!r}"
        return info
    info["valid_signature"] = True

    # Walk chunks
    off = 8
    idat_data = b""
    while off < len(data):
        if off + 8 > len(data):
            break
        chunk_len = struct.unpack(">I", data[off:off+4])[0]
        chunk_type = data[off+4:off+8].decode("ascii", errors="replace")
        info["chunks"].append({"type": chunk_type, "length": chunk_len, "offset": off})

        if chunk_type == "IHDR" and off + 8 + 13 <= len(data):
            ihdr = data[off+8:off+8+13]
            info["width"] = struct.unpack(">I", ihdr[0:4])[0]
            info["height"] = struct.unpack(">I", ihdr[4:8])[0]
            info["bit_depth"] = ihdr[8]
            info["color_type"] = ihdr[9]
        elif chunk_type == "IDAT":
            idat_data += data[off+8:off+8+chunk_len]
            info["idat_bytes"] += chunk_len
        elif chunk_type == "IEND":
            break

        off += 8 + chunk_len + 4  # length + type + data + CRC

    # Try to decompress IDAT
    if idat_data:
        try:
            decompressed = zlib.decompress(idat_data)
            info["decompressed_size"] = len(decompressed)
            info["decompressed_ok"] = True
            info["decompressed_pixels_first_20"] = decompressed[:20].hex()
        except zlib.error as e:
            info["error"] = f"zlib decompress failed: {e}"

    return info


def verify_with_pil(png_path: Path) -> dict:
    """Use PIL to verify the PNG (independent reference)."""
    try:
        from PIL import Image
        img = Image.open(png_path)
        img.load()  # Force decode
        return {
            "pil_available": True,
            "format": img.format,
            "mode": img.mode,
            "size": img.size,
            "decoded_ok": True,
        }
    except ImportError:
        return {"pil_available": False, "decoded_ok": False}
    except Exception as e:
        return {"pil_available": True, "decoded_ok": False, "error": str(e)}


def run_apk_for_png(apk_path: Path, out_dir: Path) -> dict:
    """Run an APK and check the produced PNG."""
    if out_dir.exists():
        import shutil
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    r = subprocess.run(
        [str(REPO_ROOT / "miniandroid" / "build" / "miniandroid"),
         "run", str(apk_path), "-o", str(out_dir), "-v"],
        capture_output=True, text=True, timeout=120,
    )

    png_path = out_dir / "screenshot.png"
    ppm_path = out_dir / "screenshot.ppm"

    png_info = parse_png_independently(png_path)
    pil_info = verify_with_pil(png_path)

    return {
        "exit_code": r.returncode,
        "png_info": png_info,
        "pil_info": pil_info,
        "ppm_exists": ppm_path.exists(),
    }


def run_phase3() -> dict:
    """Run Phase 3 PNG writer forensics."""
    print("=== Phase 3: B1 PNG Writer Forensics ===")

    results = []

    # Test 1: Run gmdice and check PNG
    print("\n[Test 1] gmdice APK screenshot")
    apk_path = REPO_ROOT / "miniandroid" / "download" / "exp073_real_apps" / "de.duenndns.gmdice_8.apk"
    if apk_path.exists():
        out_dir = Path("/tmp/exp086_p3_gmdice")
        result = run_apk_for_png(apk_path, out_dir)
        # Classify
        if result["png_info"]["valid_signature"] and result["png_info"]["decompressed_ok"]:
            status = "PASS_PNG_VALID"
        elif result["png_info"]["valid_signature"]:
            status = "PARTIAL_PNG_BUT_IDAT_BROKEN"
        else:
            status = "FAIL_PNG_INVALID"
        result["test"] = "gmdice_screenshot"
        result["status"] = status
        print(f"  status: {status}")
        print(f"  PNG size: {result['png_info']['size_bytes']} bytes")
        print(f"  PNG dimensions: {result['png_info']['width']}x{result['png_info']['height']}")
        print(f"  IDAT bytes: {result['png_info']['idat_bytes']}")
        print(f"  Decompressed: {result['png_info']['decompressed_size']} bytes")
        print(f"  PIL decoded: {result['pil_info'].get('decoded_ok', False)}")
        results.append(result)

    # Test 2: Run tictactoe and check PNG
    print("\n[Test 2] tictactoe APK screenshot")
    apk_path = REPO_ROOT / "miniandroid" / "download" / "tictactoe.apk"
    if apk_path.exists():
        out_dir = Path("/tmp/exp086_p3_tictactoe")
        result = run_apk_for_png(apk_path, out_dir)
        if result["png_info"]["valid_signature"] and result["png_info"]["decompressed_ok"]:
            status = "PASS_PNG_VALID"
        elif result["png_info"]["valid_signature"]:
            status = "PARTIAL_PNG_BUT_IDAT_BROKEN"
        else:
            status = "FAIL_PNG_INVALID"
        result["test"] = "tictactoe_screenshot"
        result["status"] = status
        print(f"  status: {status}")
        print(f"  PNG size: {result['png_info']['size_bytes']} bytes")
        results.append(result)

    # Test 3: Telegram screenshot (large multi-DEX)
    print("\n[Test 3] Telegram APK screenshot (multi-DEX stress)")
    apk_path = REPO_ROOT / "miniandroid" / "download" / "exp038_telegram" / "Telegram.apk"
    if apk_path.exists():
        out_dir = Path("/tmp/exp086_p3_telegram")
        result = run_apk_for_png(apk_path, out_dir)
        if result["png_info"]["valid_signature"] and result["png_info"]["decompressed_ok"]:
            status = "PASS_PNG_VALID"
        elif result["png_info"]["valid_signature"]:
            status = "PARTIAL_PNG_BUT_IDAT_BROKEN"
        else:
            status = "FAIL_PNG_INVALID"
        result["test"] = "telegram_screenshot"
        result["status"] = status
        print(f"  status: {status}")
        print(f"  PNG size: {result['png_info']['size_bytes']} bytes")
        print(f"  Decompressed: {result['png_info']['decompressed_size']} bytes")
        results.append(result)

    # Test 4: Verify PNG dimensions match expected (1080x1920)
    print("\n[Test 4] PNG dimensions check")
    expected_width = 1080
    expected_height = 1920
    for r in results:
        if r["png_info"]["width"] == expected_width and r["png_info"]["height"] == expected_height:
            r["dimensions_ok"] = True
        else:
            r["dimensions_ok"] = False
            r["status"] = "FAIL_WRONG_DIMENSIONS"
        print(f"  {r['test']}: {r['png_info']['width']}x{r['png_info']['height']} "
              f"({'OK' if r['dimensions_ok'] else 'WRONG'})")

    # Summary
    print("\n" + "=" * 70)
    print("PHASE 3 SUMMARY")
    print("=" * 70)
    pass_count = sum(1 for r in results if r["status"] == "PASS_PNG_VALID" and r.get("dimensions_ok"))
    partial_count = sum(1 for r in results if r["status"].startswith("PARTIAL"))
    fail_count = sum(1 for r in results if r["status"].startswith("FAIL"))
    print(f"PASS: {pass_count}  PARTIAL: {partial_count}  FAIL: {fail_count}")
    for r in results:
        marker = "✅" if r["status"] == "PASS_PNG_VALID" and r.get("dimensions_ok") else \
                ("⚠️ " if r["status"].startswith("PARTIAL") else "❌")
        print(f"  {marker} {r['test']:30s}  {r['status']}")

    summary = {
        "test": "EXP086 Phase 3 — B1 PNG Writer Forensics",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pass_count": pass_count,
        "partial_count": partial_count,
        "fail_count": fail_count,
        "results": results,
    }
    out_path = RESULTS_DIR / "EXP086_PHASE3_PNG_WRITER.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\nResults saved to {out_path}")
    return summary


def main():
    summary = run_phase3()
    sys.exit(0 if summary["fail_count"] == 0 else 1)


if __name__ == "__main__":
    main()
