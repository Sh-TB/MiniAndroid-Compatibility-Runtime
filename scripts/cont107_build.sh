#!/bin/bash
# CONT-107 container-fresh binary rebuild (loop chunks until success, max 8 x 550s)
cd /home/z/my-project
for i in 1 2 3 4 5 6 7 8; do
  echo "=== chunk $i start $(date +%s) ==="
  timeout 550 make -j2 -C miniandroid >> /tmp/cont107_build.log 2>&1
  rc=$?
  echo "=== chunk $i rc=$rc $(date +%s) ==="
  if [ $rc -eq 0 ]; then
    echo "BUILD OK"
    ls -la miniandroid/build/miniandroid
    sha256sum miniandroid/build/miniandroid | cut -c1-16
    exit 0
  fi
  if [ $rc -eq 124 ]; then
    echo "chunk timed out, continuing (make resumes)"
  else
    echo "build error rc=$rc, tail:"
    tail -30 /tmp/cont107_build.log
    exit $rc
  fi
done
echo "EXHAUSTED 8 chunks"
exit 1
