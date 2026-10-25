#!/bin/bash
# cont32_build_loop.sh — auto-resume make (container OOM/watchdog kills the
# compiler mid-TU; each resume continues from cached .o files).
cd /home/z/my-project/miniandroid
for i in $(seq 1 40); do
  if make -j1 >> /home/z/my-project/run/cont32_build_loop.log 2>&1; then
    echo "BUILD COMPLETE after $i segments" >> /home/z/my-project/run/cont32_build_loop.log
    exit 0
  fi
  echo "--- segment $i failed, resuming --- $(date)" >> /home/z/my-project/run/cont32_build_loop.log
  sleep 3
done
echo "BUILD FAILED after 40 segments" >> /home/z/my-project/run/cont32_build_loop.log
exit 1
