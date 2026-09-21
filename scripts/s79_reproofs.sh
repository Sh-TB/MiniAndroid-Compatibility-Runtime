#!/usr/bin/env bash
# s79_reproofs.sh — S79: current-HEAD execution re-proofs for the open
# [EXEC] campaign issues (#14-#23). Real APKs, real-dalvik, real click-test.
# Output: run/s79_reproofs/<app>_run<n>/
set -u
ROOT=/home/z/my-project
ENG=$ROOT/miniandroid/build/miniandroid
OUT=$ROOT/run/s79_reproofs
CA=$ROOT/upload/canonical_apks
mkdir -p "$OUT"

run_one() {                      # app_name apk_path frames
  local app="$1" apk="$2" extra="$3" n="$4"
  local run="$OUT/${app}_run${n}"
  rm -rf "$run"; mkdir -p "$run"
  (cd "$run" && timeout 240 "$ENG" run --execution-mode real-dalvik \
      $extra -o "$run" "$apk" > engine.log 2>&1)
  local rc=$?
  echo "$app run$n rc=$rc"
}

BATCH="$1"
case "$BATCH" in
  1)
    for n in 1 2; do
      run_one gmdice     "$CA/de.duenndns.gmdice_8.apk"     "--click-test" "$n"
      run_one microtimer "$CA/dubrowgn.microtimer_8.apk"    "--click-test" "$n"
      run_one unote      "$CA/app.varlorg.unote_30.apk"     "--click-test" "$n"
    done
    ;;
  2)
    for n in 1 2; do
      run_one fishrings  "$CA/fishrings_v1.23_vc6.apk"      "--click-test" "$n"
      run_one bouncy     "$CA/bouncy.apk"                   "--click-test" "$n"
      run_one opmt       "$CA/opmt_v0.1.2_vc1.apk"          "--click-test" "$n"
    done
    ;;
  3)
    for n in 1 2; do
      run_one dooz       "$CA/dooz_23_toplevel.apk"         "" "$n"
      run_one tripeaks   "$CA/tripeaks_v1.2.1_vc4.apk"      "--click-test" "$n"
    done
    ;;
  *) echo "unknown batch"; exit 1 ;;
esac
echo "BATCH $BATCH DONE"
