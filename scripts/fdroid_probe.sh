#!/bin/bash
# Probe F-Droid package API for candidate games; print pkg -> latest vc/name
for pkg in "$@"; do
  R=$(curl -sS --max-time 20 "https://f-droid.org/api/v1/packages/$pkg" 2>/dev/null)
  echo "$R" | python3 -c "
import json,sys
pkg='$pkg'
try:
    d=json.load(sys.stdin)
    p=d.get('packages',[])
    if p: print(f'{pkg}: OK vc={p[0][\"versionCode\"]} v={p[0][\"versionName\"]} n={len(p)}')
    else: print(f'{pkg}: -')
except Exception: print(f'{pkg}: -')
"
done
