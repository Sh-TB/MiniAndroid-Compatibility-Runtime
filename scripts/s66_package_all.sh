#!/usr/bin/env bash
# s66_package_all.sh — §13: assemble the full visual-forensics evidence tree.
set -uo pipefail
REPO=/home/z/my-project
V="$REPO/docs/evidence/visual_forensics"
RUN="$REPO/run"
M="$REPO/scripts/s66_png_metrics.py"

mkdir -p "$V/canvas_probe" "$V/dooz" "$V/s65_reval/fishrings" "$V/s65_reval/tripeaks" "$V/s65_reval/opmt"

# ── canvas probe ──
cp "$RUN/s66_probe_v/screenshot.png" "$V/canvas_probe/probe_full.png"
cp "$RUN/s66_probe_v/screenshot.ppm" "$V/canvas_probe/probe_raw_framebuffer.ppm"
python3 "$M" metrics "$V/canvas_probe/probe_full.png" \
  200,150 550,130 750,130 500,400 800,300 200,1000 620,1250 550,1230 150,695 100,1500 \
  > "$V/canvas_probe/metrics.json"
python3 "$M" rawppm "$V/canvas_probe/probe_raw_framebuffer.ppm" "$V/canvas_probe/probe_full.png" \
  > "$V/canvas_probe/raw_vs_png.json"
python3 "$M" puredecode "$V/canvas_probe/probe_full.png" > "$V/canvas_probe/puredecode_check.json"

# ── dooz ──
cp "$RUN/s66_dooz18/screenshot.png" "$V/dooz/v18_full.png"
cp "$RUN/s66_dooz23/screenshot.png" "$V/dooz/v23_full.png"
python3 "$M" metrics "$V/dooz/v18_full.png" > "$V/dooz/v18_metrics.json"
python3 "$M" metrics "$V/dooz/v23_full.png" > "$V/dooz/v23_metrics.json"
cp "$RUN/s66_dooz23/crash.log" "$V/dooz/v23_crash.log" 2>/dev/null || true

# ── s65 revalidation full frames ──
cp "$RUN/s66_reval/fishrings/frames/frame_000.png" "$V/s65_reval/fishrings/splash_full.png"
cp "$RUN/s66_reval/fishrings/frames/frame_004.png" "$V/s65_reval/fishrings/board_full.png"
cp "$RUN/s66_reval/fishrings/frames/frame_005.png" "$V/s65_reval/fishrings/after_tap1_full.png"
cp "$RUN/s66_reval/fishrings/frames/frame_006.png" "$V/s65_reval/fishrings/after_tap2_full.png"
cp "$RUN/s66_reval/fishrings/frames/frame_007.png" "$V/s65_reval/fishrings/after_tap3_full.png"
python3 "$M" metrics "$V/s65_reval/fishrings/board_full.png" > "$V/s65_reval/fishrings/board_metrics.json"

cp "$RUN/s66_reval/tripeaks2/frames/frame_000.png" "$V/s65_reval/tripeaks/splash_full.png"
cp "$RUN/s66_reval/tripeaks2/frames/frame_004.png" "$V/s65_reval/tripeaks/lobby_full.png"
cp "$RUN/s66_reval/tripeaks2/frames/frame_005.png" "$V/s65_reval/tripeaks/board_full.png"
python3 "$M" metrics "$V/s65_reval/tripeaks/lobby_full.png" > "$V/s65_reval/tripeaks/lobby_metrics.json"
python3 "$M" metrics "$V/s65_reval/tripeaks/board_full.png" > "$V/s65_reval/tripeaks/board_metrics.json"

cp "$RUN/s66_reval/opmt/frames/frame_000.png" "$V/s65_reval/opmt/menu_full.png"
cp "$RUN/s66_reval/opmt/frames/frame_001.png" "$V/s65_reval/opmt/game_partial_full.png"
python3 "$M" metrics "$V/s65_reval/opmt/menu_full.png" > "$V/s65_reval/opmt/menu_metrics.json"
python3 "$M" metrics "$V/s65_reval/opmt/game_partial_full.png" > "$V/s65_reval/opmt/game_partial_metrics.json"

# ── diffs: fishrings board before/after taps (§3-style proof for S65 apps) ──
python3 "$M" diff "$V/s65_reval/fishrings/board_full.png" "$V/s65_reval/fishrings/after_tap3_full.png" \
  "$V/s65_reval/fishrings/board_vs_after_tap3_diff.png" > "$V/s65_reval/fishrings/diff_metrics.json"
python3 "$M" diff "$V/s65_reval/tripeaks/lobby_full.png" "$V/s65_reval/tripeaks/board_full.png" \
  "$V/s65_reval/tripeaks/lobby_vs_board_diff.png" > "$V/s65_reval/tripeaks/diff_metrics.json"
python3 "$M" diff "$V/s65_reval/opmt/menu_full.png" "$V/s65_reval/opmt/game_partial_full.png" \
  "$V/s65_reval/opmt/menu_vs_game_diff.png" > "$V/s65_reval/opmt/diff_metrics.json"

# ── upstream searchlight law files (§17) ──
mkdir -p "$V/upstream"
curl -sL --max-time 60 -o "$V/upstream/aosp_Button.java" \
  "https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/main/core/java/android/widget/Button.java" 2>/dev/null || true
curl -sL --max-time 60 -o "$V/upstream/aosp_styles_Widget_Button.xml" \
  "https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/main/core/res/res/values/styles.xml" 2>/dev/null || true
# TriPeaks app source facts (pinned clone @62f3609)
mkdir -p "$V/upstream/tripeaks_62f3609"
cp /tmp/tp_src/TriPeaksSolitaireForAndroid/src/main/res/layout/activity_game.xml \
   "$V/upstream/tripeaks_62f3609/" 2>/dev/null || true
cp /tmp/tp_src/TriPeaksSolitaireForAndroid/src/main/java/eu/veldsoft/tri/peaks/CardBoard.java \
   "$V/upstream/tripeaks_62f3609/" 2>/dev/null || true

# ── SHA manifest ──
cd "$V" && find . -type f \( -name "*.png" -o -name "*.json" -o -name "*.ppm" \) -exec sha256sum {} \; | sort -k2 > SHA256SUMS
echo "PACKAGED:"; find "$V" -type f | wc -l
