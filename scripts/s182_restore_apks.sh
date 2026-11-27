#!/usr/bin/env bash
# s182_restore_apks.sh — restore the 7 fdroid_batch APKs lost in the sandbox
# recycle. F-Droid versioned artifacts are immutable; the exact
# <pkg>_<vcode>.apk URL reproduces the byte-identical original artifact
# (the campaign's hash-verified-from-F-Droid protocol). /archive/ fallback
# for versions rotated out of the main pool. sha256 + size recorded per file.
set -u
cd /home/z/my-project
mkdir -p upload/fdroid_batch
OUT=scripts/s182_restore_receipt.txt
: > "$OUT"

fetch() { # pkg vcode
  local pkg="$1"; local vc="$2"
  local f="upload/fdroid_batch/${pkg}_${vc}.apk"
  if [ -s "$f" ]; then echo "EXIST $f" >> "$OUT"; return 0; fi
  for base in "https://f-droid.org/repo" "https://f-droid.org/archive"; do
    if curl -fsSL -m 300 -o "$f" "$base/${pkg}_${vc}.apk"; then
      echo "OK $base $(sha256sum "$f" | cut -d' ' -f1) $(stat -c%s "$f") $f" >> "$OUT"
      return 0
    fi
  done
  rm -f "$f"; echo "FAIL ${pkg}_${vc}" >> "$OUT"; return 1
}

fetch ac.stresa.uturn 22
fetch org.secuso.privacyfriendlydicer 101
fetch org.secuso.privacyfriendlysolitaire 4
fetch com.ashkanrafiee.librecontactsbackup 32
fetch app.wocheneinkauf 199
fetch com.maxistar.textpad 63
fetch app.simple.peri 983
echo "=== DONE $(date -u +%FT%TZ)" >> "$OUT"
cat "$OUT"
