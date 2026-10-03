#!/bin/bash
# reg_reinstall_goldens.sh — rebuild run/audit/regression stores from the
# canonical source APKs (hidden_sources) with installed-identity proof:
#   source SHA == installed base.apk SHA -> pkgaudit live re-hash -> hide source.
# Then the normal gate (working_vs_failing_probe.sh) can run on CURRENT HEAD.
set -uo pipefail
B=/home/z/my-project/miniandroid/build/miniandroid
REG=/home/z/my-project/run/audit/regression
HID=/home/z/my-project/run/diff366/hidden_sources
mkdir -p "$REG"

# name | package | source apk (in HID)
TARGETS=(
  "opencalc|com.darkempire78.opencalculator|opencalculator_53.apk"
  "chess|jwtc.android.chess|chess_jwtc_298.apk"
  "dooz|io.github.yamin8000.dooz|io.github.yamin8000.dooz_23.apk"
  "microtimer|dubrowgn.microtimer|dubrowgn.microtimer_8.apk"
  "unote|app.varlorg.unote|app.varlorg.unote_30.apk"
)

fails=0
for t in "${TARGETS[@]}"; do
  IFS='|' read -r name pkg apk <<< "$t"
  src="$HID/$apk"
  # stage a private copy so the hidden source never leaves its directory
  tmp=/tmp/reg_stage_$name.apk
  cp "$src" "$tmp"
  src_sha=$(sha256sum "$tmp" | cut -d' ' -f1)
  st="$REG/store_$name"
  rm -rf "$st"; mkdir -p "$st"
  if ! $B install "$tmp" --data-root "$st" >"$REG/${name}_install.log" 2>&1; then
    echo "FAIL  $name install"; fails=$((fails+1)); rm -f "$tmp"; continue
  fi
  inst="$st/data/app/$pkg/base.apk"
  inst_sha=$(sha256sum "$inst" | cut -d' ' -f1)
  pa=$($B pkgaudit --package "$pkg" --data-root "$st" 2>/dev/null \
       | python3 -c "import json,sys; print(json.load(sys.stdin).get('liveBaseApkSha256',''))")
  if [ "$src_sha" = "$inst_sha" ] && [ -n "$pa" ] && [ "$pa" = "$inst_sha" ]; then
    echo "PASS  $name identity src=$src_sha inst=$inst_sha pkgaudit=$pa"
  else
    echo "FAIL  $name identity src=$src_sha inst=$inst_sha pkgaudit=$pa"
    fails=$((fails+1))
  fi
  rm -f "$tmp"
done
echo "REINSTALL-IDENTITY: $([ $fails = 0 ] && echo ALL PASS || echo "$fails FAIL")"
exit $fails
