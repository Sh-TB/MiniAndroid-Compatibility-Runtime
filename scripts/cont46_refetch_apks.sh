#!/usr/bin/env bash
# cont46_refetch_apks.sh — CONT-46 Phase-0: restore the tmp/ APKs lost to
# the container reset, SHA-pinned to the CONT-43/44 records (the same
# recovery class CONT-43 performed; evidence/cont43 §4).
set -uo pipefail
CACHE=/home/z/my-project/apk_cache
TMPA=/home/z/my-project/tmp/cont35_apks
mkdir -p "$CACHE" "$TMPA"

fetch() { # fetch <url> <dest> <expected_sha256_16>
    local url=$1 dest=$2 want=$3
    if [ -s "$dest" ]; then echo "HAVE $(basename "$dest")"; return 0; fi
    echo "GET $(basename "$dest")"
    curl -sfSL --retry 2 --max-time 240 -o "$dest.part" "$url" || { echo "  FETCH-FAIL $url"; rm -f "$dest.part"; return 1; }
    mv "$dest.part" "$dest"
    local got
    got=$(sha256sum "$dest" | cut -c1-16)
    if [ "$got" != "$want" ]; then
        echo "  SHA-MISMATCH got=$got want=$want — removing"; rm -f "$dest"; return 1
    fi
    echo "  SHA-OK $got (verified vs record)"
}

# com.tananaev.calculator v1.10 (vc11) — pin 294a68bd00debbdc (CONT-43 §4)
fetch "https://f-droid.org/repo/com.tananaev.calculator_11.apk" \
      "/home/z/my-project/tmp/com.tananaev.calculator_11.apk" 294a68bd00debbdc
cp -n /home/z/my-project/tmp/com.tananaev.calculator_11.apk "$CACHE/" 2>/dev/null || true

# com.simplemobiletools.calculator vc8 — pin 68da25fd9fdf54b4 (CONT-43 §4)
if [ ! -s "$TMPA/simplecalc_8.apk" ]; then
  fetch "https://f-droid.org/archive/repo/com.simplemobiletools.calculator_8.apk" \
        "$TMPA/simplecalc_8.apk" 68da25fd9fdf54b4 \
  || fetch "https://f-droid.org/repo/com.simplemobiletools.calculator_8.apk" \
        "$TMPA/simplecalc_8.apk" 68da25fd9fdf54b4
fi

# com.justdeax.composeStopwatch v1.9.1 (vc1009011) — pin dbf937ebbe7c0b3d
fetch "https://f-droid.org/repo/com.justdeax.composeStopwatch_1009011.apk" \
      "$TMPA/composeStopwatch_1009011.apk" dbf937ebbe7c0b3d

echo "== final identities =="
for f in /home/z/my-project/tmp/com.tananaev.calculator_11.apk \
         "$TMPA/simplecalc_8.apk" "$TMPA/composeStopwatch_1009011.apk"; do
  [ -f "$f" ] && echo "$(sha256sum "$f" | cut -c1-16)  $f" || echo "STILL-MISSING $f"
done
