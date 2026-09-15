#!/bin/bash
# S44 corpus sweep — all game APKs against the S44 engine
# (R-NEW-353 charAt result-out, R-NEW-354 framework registry, R-NEW-355 pc-advance)
# Default config (no R350 gate) — matches S43 sweep methodology.
# per-game: rc + nonwhite(full) + key error markers
BIN=/home/z/my-project/miniandroid/build/miniandroid
OUT=/home/z/my-project/miniandroid/run/s44_sweep
CORPUS=/tmp/my-project/apk_cache/corpus
S36=/tmp/my-project/apk_cache/s36new
mkdir -p "$OUT"

nonwhite() {
python3 - "$1" <<'EOF'
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert('RGB')
w,h = im.size; px = im.load()
n = sum(1 for y in range(h) for x in range(w) if px[x,y] != (255,255,255))
print(n)
EOF
}

run_game() {
  local name="$1"; local apk="$2"; local extra="$3"
  local dir="$OUT/$name"
  mkdir -p "$dir"
  env $extra "$BIN" run -o "$dir" "$apk" > "$dir.log" 2>&1
  local rc=$?
  local nw=$(nonwhite "$dir/screenshot.png" 2>/dev/null || echo -1)
  local errs=$(grep -c "EXC-UNWIND\|EXC-UNCAUGHT" "$dir/crash.log" 2>/dev/null || echo 0)
  echo "$name rc=$rc nonwhite=$nw errs=$errs"
}

echo "=== S44 SWEEP $(date -u +%H:%M:%S) ==="
run_game chessclock    "$CORPUS/chessclock.apk"                 ""
run_game gmdice        "$CORPUS/gmdice.apk"                     ""
run_game unote         "$CORPUS/unote.apk"                      ""
run_game microtimer    "$CORPUS/microtimer.apk"                 ""
run_game tictactoe     "$CORPUS/tictactoeemmanuelmess.apk"      ""
run_game tttclassic    "$CORPUS/tictactoeclassic.apk"           ""
run_game dooz18        "$CORPUS/dooz.apk"                       ""
run_game doozvariant1  "$CORPUS/dooztictactoevariant.apk"       ""
run_game doozvariant2  "$CORPUS/dooztictactoegvariant.apk"      ""
run_game bouncy        "$CORPUS/bouncy.apk"                     ""
run_game stopwatch     "$CORPUS/stopwatch.apk"                  ""
echo "=== s36new games ==="
run_game dooz23        "$S36/io.github.yamin8000.dooz_23.apk"   ""
run_game dooz23_gated  "$S36/io.github.yamin8000.dooz_23.apk"   "MINIANDROID_R350_LAW=1"
run_game bouncy39      "$S36/com.dozingcatsoftware.bouncy_39.apk" ""
run_game braincup      "$S36/com.inspiredandroid.braincup_158.apk" ""
run_game solitaire     "$S36/de.tobiasbielefeld.solitaire_69.apk" ""
run_game memory        "$S36/org.secuso.privacyfriendlymemory_8.apk" ""
run_game sudoku        "$S36/org.secuso.privacyfriendlysudoku_19.apk" ""
echo "=== SWEEP DONE $(date -u +%H:%M:%S) ==="
