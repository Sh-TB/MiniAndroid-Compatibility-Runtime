#!/usr/bin/env bash
# cont5_resume_fetch.sh — resumable, SHA-pinned APK fetch for CONT-5.
# No --max-time cap (73MB @ slow CDN exceeded the 240s budget in
# cont375_refetch_wave_apks.sh); curl -C - resumes partial files.
set -u
CACHE=/home/z/my-project/apk_cache
mkdir -p "$CACHE"

fetch() { # fetch <url> <dest> <expected_sha256_16>
  local url=$1 dest=$2 want=$3
  if [ -s "$dest" ]; then echo "HAVE $(basename "$dest")"; return 0; fi
  for attempt in 1 2 3 4 5 6 7 8; do
    echo "GET(try $attempt) $(basename "$dest")"
    curl -sfSL -C - -o "$dest.part" "$url" && break
    sleep 3
  done
  if [ -s "$dest.part" ]; then mv "$dest.part" "$dest"; fi
  if [ -s "$dest" ]; then
    local got
    got=$(sha256sum "$dest" | cut -c1-16)
    if [ -n "$want" ] && [ "$got" != "$want" ]; then
      echo "  SHA-MISMATCH got=$got want=$want"; rm -f "$dest"; return 1
    fi
    echo "  SHA-OK $got"
    return 0
  fi
  echo "  FETCH-FAIL $url"; return 1
}

fetch "https://f-droid.org/repo/com.fairytrick.fairymahjong_5.apk" \
      "$CACHE/com.fairytrick.fairymahjong_5.apk" 88a4cbbea3e365c1
fetch "https://f-droid.org/repo/com.galaxyrio.sudokusolver_8.apk" \
      "$CACHE/com.galaxyrio.sudokusolver_8.apk" d114d479df66b0f6
fetch "https://f-droid.org/repo/com.sidhant.blockblast_43.apk" \
      "$CACHE/com.sidhant.blockblast_43.apk" 64589a3a7e5c0f73
fetch "https://f-droid.org/repo/com.sanskritbasics.memory_34.apk" \
      "$CACHE/com.sanskritbasics.memory_34.apk" 830798a6e70653d6
fetch "https://f-droid.org/repo/com.yepgoryo.EggReturnsHome_1.apk" \
      "$CACHE/com.yepgoryo.EggReturnsHome_1.apk" 74220e46faec9517
echo DONE
