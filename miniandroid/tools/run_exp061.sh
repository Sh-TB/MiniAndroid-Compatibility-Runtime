#!/bin/bash
# EXP-061: End-to-end Login UI rendering pipeline.
#
# Builds MiniAndroid, runs Telegram, dispatches synthetic CLICK to reach
# LoginActivity, dumps View tree, renders CPU-only PNG screenshot.
#
# Usage: bash tools/run_exp061.sh [apk_path] [output_dir]
set -e

ROOT=/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid
APK="${1:-$ROOT/download/exp038_telegram/Telegram.apk}"
OUT="${2:-$ROOT/run/exp061}"
WIDTH=1080
HEIGHT=1920

echo "============================================================"
echo "  EXP-061: CPU-Only Login UI Rendering"
echo "============================================================"
echo "  APK:      $APK"
echo "  Output:   $OUT"
echo "  Resolution: ${WIDTH}x${HEIGHT}"
echo "  GPU:      DISABLED (CPU-only)"
echo "============================================================"
echo ""

# Step 1: Build
echo "[1/6] Building MiniAndroid..."
cd "$ROOT"
bash build_exp042.sh 2>&1 | tail -1
echo ""

# Step 2: Run Telegram
echo "[2/6] Running Telegram APK..."
rm -rf "$OUT"
mkdir -p "$OUT"
timeout 60 ./build_exp042/miniandroid_exp042 "$APK" "$OUT" > "$OUT/stdout.log" 2> "$OUT/stderr.log"
echo "  Exit code: $?"
echo "  Unique methods: $(grep -c '^\[METHOD-IN\]' "$OUT/stderr.log")"
echo "  Instructions: $(grep 'Instructions executed' "$OUT/stdout.log" || echo 'N/A')"
echo ""

# Step 3: Check view tree was dumped
echo "[3/6] Checking View tree dump..."
if [ -f "$OUT/view_tree.json" ]; then
    VIEWS=$(python3 -c "import json; print(json.load(open('$OUT/view_tree.json'))['view_count'])")
    echo "  View tree: $OUT/view_tree.json ($VIEWS nodes)"
else
    echo "  ERROR: view_tree.json not found"
    exit 1
fi
echo ""

# Step 4: Render PNG (CPU-only)
echo "[4/6] Rendering PNG (CPU software renderer)..."
python3 tools/exp061_render.py "$OUT/view_tree.json" "$OUT/login_screen.png" "$OUT/login_screen_debug.png" $WIDTH $HEIGHT
echo ""

# Step 5: Validate PNG
echo "[5/6] Validating PNG..."
python3 tools/exp061_image_validator.py "$OUT/login_screen.png" $WIDTH $HEIGHT
echo ""

# Step 6: Summary
echo "[6/6] Summary"
echo "  Renderer backend: CPU"
echo "  GPU used: NO"
echo "  OpenGL used: NO"
echo "  Emulator used: NO"
echo "  Screenshot: $OUT/login_screen.png"
echo "  Debug:      $OUT/login_screen_debug.png"
echo "  Provenance: $OUT/render_provenance.json"
echo ""
echo "DONE"
