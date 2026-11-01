#!/usr/bin/env bash
# s145_game_family_sweep.sh — S145 TRAIN-62: the game family re-tested on the
# T61-rebate binary ae97daf4fe549b9d (user directive: «بازی هم یادت رفته»).
# Fresh install + 40-frame run each; face sha16 + Errors/SQLiteException counts.
B=/home/z/my-project/miniandroid/build/miniandroid
OUT=/home/z/my-project/run/s148_games
mkdir -p "$OUT"
declare -A APK=(
  [g2048]=/home/z/my-project/upload/s83_games/build_g2048/g2048_v1.0_vc1.apk
  [tetris]=/home/z/my-project/upload/s83_games/build_tetris/tetris_v1.0_vc1.apk
  [snakedeluxe]=/home/z/my-project/upload/s83_games/build_sd/snake_deluxe_v1.0_vc1.apk
  [minicraft]=/home/z/my-project/upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk
  [gmem]=/home/z/my-project/upload/s80_games/build_mem/gmem_v1.0_vc1.apk
  [snakeneon]=/home/z/my-project/upload/s98_games/build_snakeneon/snakeneon_v1.0_vc1.apk
  [sqlnotes]=/home/z/my-project/upload/s142_sqlnotes/build/sqlnotes_v1.0_vc1.apk
)
declare -A PKG=(
  [g2048]=com.miniandroid.g2048
  [tetris]=com.miniandroid.tetris
  [snakedeluxe]=com.miniandroid.snakedeluxe
  [minicraft]=com.miniandroid.minicraft
  [gmem]=com.miniandroid.gmem
  [snakeneon]=com.miniandroid.snakeneon
  [sqlnotes]=com.miniandroid.sqlnotes
)
for name in g2048 tetris snakedeluxe minicraft gmem snakeneon sqlnotes; do
  st="$OUT/store_$name"
  rm -rf "$st"; mkdir -p "$st"
  "$B" install "${APK[$name]}" --data-root "$st" > "$OUT/${name}_install.txt" 2>&1
  o="$OUT/${name}_run1"
  rm -rf "$o"; mkdir -p "$o"
  "$B" run --package "${PKG[$name]}" --data-root "$st" --trace --max-seconds 120 --frames 40 -o "$o" > "$OUT/${name}_run.txt" 2>&1 || true
  s=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  errs=$(grep -c "\[ERROR\]" "$o/log.txt" 2>/dev/null || echo "?")
  sqle=$(grep -ci "SQLiteException" "$o/log.txt" 2>/dev/null || echo "?")
  frames=$(grep -c "frame " "$o/log.txt" 2>/dev/null || echo "?")
  echo "$name: face=$s errors=$errs sqlex=$sqle frames=$frames"
done
