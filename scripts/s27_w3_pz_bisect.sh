#!/usr/bin/env bash
# s27_w3_pz_bisect.sh — attribute the pz face delta: run pz on a binary
# WITHOUT the S27-W3 source changes (stash), then restore + rebuild + smoke.
set -u
cd /home/z/my-project/miniandroid
EV=evidence/s27
APK=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk

echo "=== stash S27-W3 source changes ===" | tee -a $EV/w3_pz_bisect.log
git stash push -m s27w3-bisect -- \
  src/framework/android_shadows.h \
  src/framework/android_shadows.cpp \
  src/dex/dalvik_bridge_domain_app_runtime.cpp \
  2>&1 | tee -a $EV/w3_pz_bisect.log
git stash list | head -2 | tee -a $EV/w3_pz_bisect.log

echo "=== rebuild clean-origin TUs ===" | tee -a $EV/w3_pz_bisect.log
make -j2 all > $EV/w3_build_bisect_clean.log 2>&1
rc=$?
echo "clean build rc=$rc" | tee -a $EV/w3_pz_bisect.log
if [ $rc -eq 0 ]; then
  rm -rf $EV/w3_pz_clean && mkdir -p $EV/w3_pz_clean
  MINIANDROID_VERSION_HEADER=build/generated/miniandroid_version.h \
    timeout 400 ./build/miniandroid run --max-seconds 200 --frames 50 --trace \
    --tap 197,112@25 -o $EV/w3_pz_clean --execution-mode real-dalvik "$APK" \
    > $EV/w3_pz_clean/stdout.log 2> $EV/w3_pz_clean/stderr.log
  pzc_rc=$?
  pzc_hash=$(sha256sum $EV/w3_pz_clean/screenshot.png 2>/dev/null | cut -c1-16)
  echo "PZ-CLEAN-ORIGIN rc=$pzc_rc hash=$pzc_hash (S27-W2 canonical=6375a3a3813af176, mine=35c4e53b14561b2f)" | tee -a $EV/w3_pz_bisect.log
fi

echo "=== restore S27-W3 changes ===" | tee -a $EV/w3_pz_bisect.log
git stash pop 2>&1 | tee -a $EV/w3_pz_bisect.log
echo "=== rebuild with S27-W3 ===" | tee -a $EV/w3_pz_bisect.log
make -j2 all > $EV/w3_build_bisect_restore.log 2>&1
echo "restore build rc=$?" | tee -a $EV/w3_pz_bisect.log
rm -rf $EV/w3_flip_smoke && mkdir -p $EV/w3_flip_smoke
MINIANDROID_VERSION_HEADER=build/generated/miniandroid_version.h \
  timeout 150 ./build/miniandroid run --max-seconds 120 --frames 30 --trace \
  -o $EV/w3_flip_smoke --execution-mode real-dalvik \
  /home/z/my-project/upload/handoff_apks/org.ecos.logic.flip_a_coin_3.apk \
  > $EV/w3_flip_smoke/stdout.log 2> $EV/w3_flip_smoke/stderr.log
echo "FLIP-SMOKE rc=$? face=$(sha256sum $EV/w3_flip_smoke/screenshot.png 2>/dev/null | cut -c1-16)" | tee -a $EV/w3_pz_bisect.log
