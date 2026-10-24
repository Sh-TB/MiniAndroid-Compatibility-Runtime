#!/bin/bash
# cont11_buildloop.sh — resilient single-threaded build with OOM-retry.
# Each retry resumes from persisted .o files; loop until the binary links.
cd /home/z/my-project/miniandroid
for i in $(seq 1 40); do
  if [ -x build/miniandroid ]; then echo "BIN_EXISTS after $i attempts"; exit 0; fi
  echo "=== attempt $i $(date +%H:%M:%S) ==="
  make -j1 >> /tmp/buildloop.log 2>&1
  rc=$?
  if [ $rc -eq 0 ] && [ -x build/miniandroid ]; then
    echo "BUILD_OK after $i attempts"; sha256sum build/miniandroid | cut -c1-16; exit 0
  fi
  sleep 2
done
echo "BUILD_FAILED_AFTER_40"
exit 1
