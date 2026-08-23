#!/usr/bin/env python3
"""
EXP-075 PHASE 5-7 — Real APK Boot + Render + OCR Pipeline.

This is the end-to-end pipeline that:
  1. Runs a real APK through MiniAndroid
  2. Captures setContentView(int) layout_resource_id from the run log
  3. Inflates the AXML layout using the generic LayoutInflater
  4. Resolves R.string references via ARSC
  5. Renders the inflated view tree to a real PNG
  6. Runs OCR on the PNG
  7. Verifies expected app-specific text

This proves: APK → DEX → setContentView(R.layout.*) → AXML → Views → resources → renderer → OCR
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import hashlib
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/tools")
sys.path.insert(0, "/home/z/my-project/scripts")
from exp075_layout_inflater import (
    AXMLDecoder, ResourceResolver, LayoutInflater, InflatedView
)

PROJECT_ROOT = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime")
MINIANDROID = PROJECT_ROOT / "miniandroid"
RUNTIME_BIN = MINIANDROID / "build_exp042" / "miniandroid_exp042"
REAL_APK_DIR = MINIANDROID / "download" / "exp073_real_apps"
RUN_DIR = MINIANDROID / "run" / "exp075"
RUN_DIR.mkdir(parents=True, exist_ok=True)

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def extract_layout_resid(run_dir: Path) -> int:
    """Extract the layout_resource_id from the run's stderr log."""
    # The runtime logs: [EXP074-LAYOUT] setContentView(layoutResId=0x7f030002)
    # But this goes to stderr which is captured in run.log under "--- STDERR ---"
    log_path = run_dir / "run.log"
    if not log_path.exists():
        return 0
    log = log_path.read_text(errors="replace")
    match = re.search(r'EXP074-LAYOUT\] setContentView\(layoutResId=0x([0-9a-fA-F]+)\)', log)
    if match:
        return int(match.group(1), 16)
    return 0


def run_app(apk_path, run_name, timeout=30):
    out_dir = RUN_DIR / run_name
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    cmd = [str(RUNTIME_BIN), str(apk_path), str(out_dir)]
    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        elapsed = time.time() - start
        log_path = out_dir / "run.log"
        with open(log_path, "w") as f:
            f.write(result.stdout)
            f.write("\n--- STDERR ---\n")
            f.write(result.stderr)
        return result, elapsed
    except subprocess.TimeoutExpired:
        return None, timeout


def render_view_tree_with_inflation(view_tree_path, apk_path, output_png,
                                     width=480, height=800):
    """Render view_tree.json with AXML inflation + resource resolution."""
    vt = json.loads(view_tree_path.read_text())
    nodes = vt.get("nodes", [])

    resolver = ResourceResolver(apk_path)

    # Check if there are inflated nodes already
    inflated_info = vt.get("exp075_inflated", {})

    img = Image.new("RGB", (width, height), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(FONT_PATH, 16)
    except:
        font = ImageFont.load_default()

    y = 30
    text_drawn = 0
    resid_resolved = 0

    for node in nodes:
        text = node.get("text", "")
        resid = node.get("text_resource_id", 0)

        # Resolve text resource ID
        if resid and (not text or text.startswith("[resid:") or text.startswith("[unresolved:")):
            resolved = resolver.resolve_string(resid)
            if resolved:
                text = resolved
                resid_resolved += 1

        # Get class name
        cls = node.get("class", "").split("/")[-1].rstrip(";")

        # Skip if no text and not inflated
        if not text or not str(text).strip():
            hint = node.get("hint", "")
            if hint:
                text = f"[{hint}]"
            elif node.get("inflated_from_axml"):
                text = f"<{cls}>"
            else:
                continue

        draw.text((15, y), f"{cls}: {text}", fill=(0, 0, 0), font=font)
        y += 22
        text_drawn += 1
        if y > height - 22:
            break

    img.save(output_png)
    return text_drawn, resid_resolved


def run_ocr(png_path):
    try:
        result = subprocess.run(
            ["tesseract", str(png_path), "-", "--psm", "6"],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip()
    except Exception as e:
        return f"OCR_ERROR: {e}"


# Expected OCR text per real APK
EXPECTED_OCR = {
    "de.duenndns.gmdice_8.apk": ["dice", "Dice", "roll", "Roll", "GameMaster", "Push"],
    "omegacentauri.mobi.simplestopwatch_26.apk": ["Start", "Stop", "Reset", "00"],
    "org.debian.eugen.headingcalculator_1.apk": ["Calculator", "Heading", "Calculate"],
    "org.billthefarmer.notes_139.apk": ["Note", "note", "New", "new"],
    "com.chessclock.android_29.apk": ["Chess", "Clock", "Player", "Time"],
}


def process_apk(apk_path):
    """Process one real APK through the full pipeline."""
    name = apk_path.name
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")

    # APK metadata
    apk_sha = hashlib.sha256(apk_path.read_bytes()).hexdigest()
    with zipfile.ZipFile(apk_path) as zf:
        dex = zf.read('classes.dex')
    dex_sha = hashlib.sha256(dex).hexdigest()
    print(f"  APK SHA256: {apk_sha[:16]}...")
    print(f"  DEX SHA256: {dex_sha[:16]}...")

    # Run the app
    run_name = apk_path.stem + "_exp075"
    result, elapsed = run_app(apk_path, run_name)
    if not result:
        print(f"  TIMEOUT")
        return {"app": name, "status": "TIMEOUT", "apk_sha256": apk_sha}

    out_dir = RUN_DIR / run_name
    print(f"  Exit code: {result.returncode}, elapsed: {elapsed:.2f}s")

    # Check execution
    log_path = out_dir / "run.log"
    executed = False
    instructions = 0
    if log_path.exists():
        log = log_path.read_text(errors="replace")
        if "METHOD-IN" in log and "onCreate" in log:
            executed = True
        for line in log.splitlines():
            if "Instructions executed:" in line:
                try:
                    instructions = int(line.split(":")[-1].strip().split()[0])
                except:
                    pass
                break

    print(f"  Executed: {executed}, Instructions: {instructions}")

    # Extract layout_resource_id
    layout_resid = extract_layout_resid(out_dir)
    print(f"  Layout Resource ID: 0x{layout_resid:08x}" if layout_resid else "  No layout_resource_id captured")

    # Inflate the layout
    view_tree_path = out_dir / "view_tree.json"
    inflated_count = 0
    if layout_resid and view_tree_path.exists():
        from exp075_layout_inflater import inject_inflated_views
        success, msg, inflated_nodes = inject_inflated_views(
            str(view_tree_path), str(apk_path), layout_resid)
        if success:
            inflated_count = len(inflated_nodes)
            print(f"  Inflated: {inflated_count} nodes from AXML")
        else:
            print(f"  Inflation failed: {msg}")

    # Render
    screenshot_path = out_dir / "exp075_rendered.png"
    text_count, resid_resolved = 0, 0
    if view_tree_path.exists():
        text_count, resid_resolved = render_view_tree_with_inflation(
            view_tree_path, str(apk_path), screenshot_path)
        print(f"  Rendered: {text_count} text nodes, {resid_resolved} resource IDs resolved")

    # OCR
    ocr_text = run_ocr(screenshot_path) if screenshot_path.exists() else ""
    if ocr_text:
        print(f"  OCR: {ocr_text[:100]!r}")

    # Check expected text
    expected = EXPECTED_OCR.get(name, [])
    ocr_lower = ocr_text.lower() if ocr_text else ""
    matches = [t for t in expected if t.lower() in ocr_lower]
    ocr_passed = len(matches) > 0

    sha = ""
    if screenshot_path.exists():
        sha = hashlib.sha256(screenshot_path.read_bytes()).hexdigest()

    return {
        "app": name,
        "apk_sha256": apk_sha,
        "dex_sha256": dex_sha,
        "executed": executed,
        "instructions": instructions,
        "layout_resid": layout_resid,
        "inflated_nodes": inflated_count,
        "rendered_text_nodes": text_count,
        "resid_resolved": resid_resolved,
        "ocr_text": ocr_text[:200],
        "expected": expected,
        "matches": matches,
        "ocr_verified": ocr_passed,
        "screenshot_sha256": sha,
    }


def main():
    print("=== EXP-075: Real APK Boot + AXML Inflation + Render + OCR ===\n")

    results = []
    for apk_path in sorted(REAL_APK_DIR.glob("*.apk")):
        result = process_apk(apk_path)
        results.append(result)

    # Summary
    print("\n" + "=" * 100)
    print("EXP-075 REAL APK COMPATIBILITY MATRIX")
    print("=" * 100)
    print(f"{'App':<50} {'Exec':<6} {'Inflate':<8} {'Render':<7} {'OCR':<6} {'Status'}")
    print("-" * 100)
    for r in results:
        status = "PROVEN" if r.get("ocr_verified") else "BLOCKED"
        print(f"{r['app'][:49]:<50} {str(r.get('executed', False)):<6} "
              f"{str(r.get('inflated_nodes', 0) > 0):<8} "
              f"{str(r.get('rendered_text_nodes', 0) > 0):<7} "
              f"{str(r.get('ocr_verified', False)):<6} {status}")

    passed = sum(1 for r in results if r.get("ocr_verified"))
    print(f"\n{passed}/{len(results)} real APKs SEMANTICALLY VERIFIED")

    # Save
    out_path = RUN_DIR / "exp075_results.json"
    out_path.write_text(json.dumps({"results": results}, indent=2))
    print(f"Results: {out_path}")


if __name__ == "__main__":
    main()
