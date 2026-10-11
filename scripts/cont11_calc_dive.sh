#!/bin/bash
# CONT-11 WAVE 7 — Front B: AlexCalc + BMI first-ever runs (installed identity).
# These two calculators were DEFERRED pre-build at S64: AlexCalc = PreferenceFragmentCompat,
# BMI = support-v4 FragmentManager. First dives record first divergences; no fix claims.
set -e
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont11

dive() {  # dive <apk> <pkg> <label> [extra-env]
  local APK=$1 PKG=$2 LABEL=$3
  local STORE=$OUT/store_$LABEL RUN=$OUT/${LABEL}_run1
  mkdir -p "$OUT"
  if [ ! -d "$STORE" ]; then
    "$BIN" install "$APK" --data-root "$STORE" > "$OUT/install_$LABEL.log" 2>&1 || true
    echo "install $LABEL rc=$? (see install_$LABEL.log)"
  fi
  rm -rf "$RUN"; mkdir -p "$RUN"
  env $EXTRA "$BIN" run --package "$PKG" --data-root "$STORE" \
    --dump-view-tree --trace --max-seconds 110 --frames 40 -o "$RUN" \
    > "$RUN/run.log" 2>&1 || true
  local SHA ERRS VIEWS
  SHA=$(sha256sum "$RUN/screenshot.png" 2>/dev/null | cut -c1-16 || echo NO_SCREENSHOT)
  ERRS=$(grep -cE "EXC-UNCAUGHT" "$RUN/run.log" 2>/dev/null || echo "?")
  VIEWS=$(grep -oE "views=[0-9]+" "$RUN/run.log" 2>/dev/null | tail -1 || echo "views=?")
  echo "== $LABEL: sha16=$SHA $VIEWS uncaught=$ERRS"
  grep -E "EXC-UNCAUGHT|SYNTH-EXC" "$RUN/run.log" 2>/dev/null | head -6 || true
}

EXTRA="MINIANDROID_METHOD_TRACE=1 MINIANDROID_METHOD_TRACE_BUDGET=300000"
dive "$BASE/upload/cont11_apks/alexcalc_20.apk" net.alexbarry.calc_android alexcalc
dive "$BASE/upload/cont11_apks/bmi_402.apk" com.zola.bmi bmi
