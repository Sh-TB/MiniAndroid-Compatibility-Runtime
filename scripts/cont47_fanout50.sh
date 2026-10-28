#!/usr/bin/env bash
# cont47_fanout50.sh — «۵۰ قطار موازی»: parallel mass-audit of every runnable APK
# through the HEAD engine binary. Each program = one train; results = evidence rows.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont47/fanout
mkdir -p "$OUT"
cd "$BASE"

# --- train roster: every APK on disk (deep corpus, deduped) ---
MAPFILE_LIST=$(mktemp)
cat > "$MAPFILE_LIST" <<'EOF'
canonical|app.varlorg.unote_30.apk|unote
canonical|bouncy.apk|bouncy
canonical|com.dozingcatsoftware.bouncy_43.apk|bouncy43
canonical|com.emmanuelmess.tictactoe_3.apk|ttt3
canonical|com.github.muellerma.stopwatch_6.apk|stopwatch6
canonical|de.duenndns.gmdice_8.apk|gmdice
canonical|dubrowgn.microtimer_8.apk|microtimer
EOF
ls "$BASE/upload/canonical_apks/"*.apk 2>/dev/null | while read -r a; do
  b=$(basename "$a"); echo "canonical|$b|${b%.apk}" >> "$MAPFILE_LIST"
done
ls "$BASE/upload/cont73_apks/"*.apk 2>/dev/null | while read -r a; do
  b=$(basename "$a"); echo "cont73|$b|${b%.apk}" >> "$MAPFILE_LIST"
done
ls "$BASE/upload/foundation_apks/"*.apk 2>/dev/null | while read -r a; do
  b=$(basename "$a"); echo "foundation|$b|${b%.apk}" >> "$MAPFILE_LIST"
done
for f in chess_jwtc_298.apk chessclock_29.apk klondike_veldsoft_3.apk \
         opencalculator_53.apk sudoku_secuso_101.apk notes_secuso_105.apk; do
  [ -f "$BASE/upload/$f" ] && echo "misc|$f|${f%.apk}" >> "$MAPFILE_LIST"
done
[ -f "$BASE/upload/cont50_apks/de.tobiasbielefeld.solitaire_71.apk" ] && \
  echo "misc|cont50_apks/de.tobiasbielefeld.solitaire_71.apk|solitaire71" >> "$MAPFILE_LIST"
[ -f "$BASE/run/cont11/store_solitaire/data/app/de.tobiasbielefeld.solitaire/base.apk" ] && \
  echo "misc|STORE-solitaire|store_solitaire" >> "$MAPFILE_LIST"

run_train() {
  local src="$1" rel="$2" label="$3"
  local apk=""
  case "$src" in
    canonical) apk="$BASE/upload/canonical_apks/$rel";;
    cont73)    apk="$BASE/upload/cont73_apks/$rel";;
    foundation) apk="$BASE/upload/foundation_apks/$rel";;
    misc)      apk="$BASE/upload/$rel";;
    STORE-solitaire) apk="$BASE/run/cont11/store_solitaire/data/app/de.tobiasbielefeld.solitaire/base.apk";;
  esac
  [ -f "$apk" ] || { echo "SKIP $label (no apk)"; return; }
  local o="$OUT/$label"
  rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 5 --max-seconds 25 --dump-view-tree -o "$o" \
    > "$o/run.log" 2>&1
  local rc=$?
  local sha pxs unc
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  pxs=$(python3 - "$o/screenshot.png" <<'PY' 2>/dev/null
import sys,zlib,struct
try:
    d=open(sys.argv[1],'rb').read()
    print(f"{len(d)//1024}KB")
except Exception:
    print("?")
PY
)
  unc=$(grep -cE "Uncaught|FATAL" "$o/run.log" 2>/dev/null || echo 0)
  echo "TRAIN|$label|rc=$rc|sha=$sha|logKB=$pxs|uncaught=$unc"
}
export -f run_train
export BIN OUT BASE

# dedup by label, run 10-wide parallel
cut -d'|' -f1,2,3 "$MAPFILE_LIST" | awk -F'|' '!seen[$3]++' > "$MAPFILE_LIST.d"
echo "== launching $(wc -l < "$MAPFILE_LIST.d") parallel trains =="
while IFS='|' read -r src rel label; do
  echo "$src $rel $label"
done < "$MAPFILE_LIST.d" | xargs -P 10 -n 3 bash -c 'run_train "$0" "$1" "$2"' \
  2>&1 | tee "$OUT/summary.txt" | grep -E "TRAIN|SKIP" 

echo "FANOUT-DONE rows=$(grep -c TRAIN "$OUT/summary.txt" 2>/dev/null)"
