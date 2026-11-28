#!/usr/bin/env bash
# t279c_restore_apks.sh — restore the 9 APKs missing from disk at T279
# (8 S182 PARTIAL titles + com.nononsenseapps.notepad), the same
# hash-verified-from-F-Droid protocol as s182_restore_apks.sh: versioned
# F-Droid artifacts are immutable, /archive/ fallback for rotated versions.
set -u
cd /home/z/my-project
mkdir -p upload/fdroid_batch
OUT=scripts/t279c_restore_receipt.txt
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

fetch com.aeropayout.game 12
fetch com.awagam.android 5
fetch org.secuso.privacyfriendlyludo 100
fetch com.curryplayer.quicksettingssoundprofile 11
fetch com.cg.lrceditor 57
fetch app.floatdeck 8
fetch com.chiranth7.webstack 6
fetch org.dmfs.tasks 82200
fetch com.nononsenseapps.notepad 72700
echo "=== DONE $(date -u +%FT%TZ)" >> "$OUT"
cat "$OUT"
