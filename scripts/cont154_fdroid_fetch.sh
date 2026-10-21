#!/usr/bin/env bash
# cont154_fdroid_fetch.sh — expand corpus toward 100 apps via F-Droid repo.
# Phase A: probe https://f-droid.org/api/v1/packages/<pkg> for suggestedVersionCode
# Phase B: download https://f-droid.org/repo/<pkg>_<vc>.apk (cap 25MB) into upload/fdroid_batch/
set -u
cd /home/z/my-project
mkdir -p run/c154 upload/fdroid_batch
LIST=run/c154/fdroid_candidates.txt
MANI=run/c154/fdroid_manifest.tsv
export MANI

probe() {
  local pkg="$1"
  local api="https://f-droid.org/api/v1/packages/$pkg"
  local vc
  vc=$(timeout 25 curl -sL --max-time 20 "$api" 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin); print(d.get('suggestedVersionCode',''))
except Exception: print('')
" 2>/dev/null)
  if [ -n "$vc" ] && [ "$vc" != "None" ]; then
    echo -e "$pkg\t$vc" >> "$MANI"
    echo "PROBE OK $pkg vc=$vc"
  else
    echo "PROBE MISS $pkg"
  fi
}
export -f probe

dl() {
  local pkg="$1" vc="$2"
  local out="upload/fdroid_batch/${pkg}_${vc}.apk"
  [ -s "$out" ] && { echo "DL SKIP $pkg (exists)"; return 0; }
  if timeout 180 curl -sL --max-time 170 --max-filesize 25000000 \
      -o "$out" "https://f-droid.org/repo/${pkg}_${vc}.apk" 2>/dev/null && [ -s "$out" ]; then
    # verify it is a real zip (APK)
    if ! unzip -tqq "$out" >/dev/null 2>&1; then
      rm -f "$out"; echo "DL BADZIP $pkg"; return 0
    fi
    local sz sha
    sz=$(stat -c%s "$out"); sha=$(sha256sum "$out" | cut -c1-16)
    echo "DL OK $pkg sz=$sz sha16=$sha"
  else
    rm -f "$out"; echo "DL FAIL $pkg"
  fi
}
export -f dl

case "${1:-}" in
  probe)
    : > "$MANI"
    while read -r p; do echo "$p"; done < "$LIST" | xargs -P 4 -I{} bash -c 'probe {}'
    echo "=== manifest: $(wc -l < "$MANI") packages ==="
    ;;
  download)
    n=0
    while IFS=$'\t' read -r p v; do
      [ -z "$p" ] && continue
      dl "$p" "$v" &
      n=$((n+1))
      if [ $((n % 3)) -eq 0 ]; then wait; fi
    done < "$MANI"
    wait
    echo "=== downloaded: $(ls upload/fdroid_batch/*.apk 2>/dev/null | wc -l) APKs ==="
    ;;
  *) echo "usage: $0 probe|download" ;;
esac
