#!/usr/bin/env bash
# cont12_gates.sh — CONT-12 wave gates at the F-NEW-517 binary.
# Anchors x2 (90s): opencalc 63020bc7, chess a0319686, microtimer bbd350b6,
#                   unote 7481e9b4, tower3d 11a38a5a
# dooz x2 at 300s:  851cc176 (the F-NEW-314/381 budget law, census record)
# negatives (s41_gatea_negative) + skill selftest.
set -u
cd /home/z/my-project
B=./miniandroid/build/miniandroid
OUT=run/cont12/gates
mkdir -p "$OUT"
echo "== binary: $(sha256sum $B | cut -c1-16)"

declare -A APK=(
  [opencalc]=upload/opencalculator_53.apk
  [chess]=upload/chess_jwtc_298.apk
  [microtimer]=upload/canonical_apks/dubrowgn.microtimer_8.apk
  [unote]=upload/canonical_apks/app.varlorg.unote_30.apk
  [tower3d]=upload/canonical_apks/stack.tower3d_1.apk
  [dooz]=upload/canonical_apks/io.github.yamin8000.dooz_23.apk
)
declare -A PKG=(
  [opencalc]=com.darkempire78.opencalculator
  [chess]=jwtc.android.chess
  [microtimer]=dubrowgn.microtimer
  [unote]=app.varlorg.unote
  [tower3d]=stack.tower3d
  [dooz]=io.github.yamin8000.dooz
)
declare -A WANT=(
  [opencalc]=63020bc7
  [chess]=a0319686
  [microtimer]=bbd350b6
  [unote]=7481e9b4
  [tower3d]=11a38a5a
  [dooz]=851cc176
)
fail=0
for name in opencalc chess microtimer unote tower3d dooz; do
  st="$OUT/store_$name"
  [ -d "$st" ] || "$B" install "${APK[$name]}" --data-root "$st" > /dev/null 2>&1
  ms=90; [ "$name" = dooz ] && ms=300
  shas=""
  for i in 1 2; do
    o="$OUT/${name}_run$i"
    rm -rf "$o"; mkdir -p "$o"
    "$B" run --package "${PKG[$name]}" --data-root "$st" --max-seconds "$ms" --frames 40 -o "$o" > /dev/null 2>&1 || true
    s=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
    shas="$shas $s"
  done
  match="MATCH"
  for s in $shas; do [ "$s" = "${WANT[$name]}" ] || match="DRIFT(want ${WANT[$name]})"; done
  echo "$name:$shas -> $match"
  [ "$match" = "MATCH" ] || fail=1
done
echo "== negatives =="
timeout 550 python3 scripts/s41_gatea_negative.py 2>&1 | tail -4
neg_rc=$?
echo "negatives rc=$neg_rc"
echo "== selftest =="
timeout 550 python3 scripts/skill_selftest.py 2>&1 | tail -6
st_rc=$?
echo "selftest rc=$st_rc"
echo "== GATES: $([ $fail -eq 0 ] && echo ANCHORS-GREEN || echo ANCHORS-FAIL) =="
exit $fail
