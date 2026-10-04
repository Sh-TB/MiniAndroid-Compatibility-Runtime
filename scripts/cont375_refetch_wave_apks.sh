#!/usr/bin/env bash
# cont375_refetch_wave_apks.sh — refetch the new-wave + corpus APKs after
# container reset, SHA-pinned to the recorded ledgers (zero-drift law).
set -uo pipefail
CACHE=/home/z/my-project/apk_cache
mkdir -p "$CACHE"

fetch() { # fetch <url> <dest> <expected_sha256_16>
    local url=$1 dest=$2 want=$3
    if [ -s "$dest" ]; then echo "HAVE $(basename "$dest")"; return 0; fi
    echo "GET $(basename "$dest")"
    curl -sfSL --retry 2 --max-time 240 -o "$dest.part" "$url" || { echo "  FETCH-FAIL $url"; rm -f "$dest.part"; return 1; }
    mv "$dest.part" "$dest"
    local got
    got=$(sha256sum "$dest" | cut -c1-16)
    if [ -n "$want" ] && [ "$got" != "$want" ]; then
        echo "  SHA-MISMATCH got=$got want=$want — removing"; rm -f "$dest"; return 1
    fi
    echo "  SHA-OK $got${want:+ (verified)}"
}

fetch "https://f-droid.org/repo/org.fossify.clock_10.apk"                  "$CACHE/org.fossify.clock_10.apk"              43cf9f0ec45f1f1f
fetch "https://f-droid.org/repo/com.fairytrick.fairymahjong_5.apk"         "$CACHE/com.fairytrick.fairymahjong_5.apk"     88a4cbbea3e365c1
fetch "https://f-droid.org/repo/com.galaxyrio.sudokusolver_8.apk"          "$CACHE/com.galaxyrio.sudokusolver_8.apk"      d114d479df66b0f6
fetch "https://f-droid.org/repo/com.sidhant.blockblast_43.apk"             "$CACHE/com.sidhant.blockblast_43.apk"         64589a3a7e5c0f73
fetch "https://f-droid.org/repo/com.sanskritbasics.memory_34.apk"          "$CACHE/com.sanskritbasics.memory_34.apk"      830798a6e70653d6
fetch "https://f-droid.org/repo/com.yepgoryo.EggReturnsHome_1.apk"         "$CACHE/com.yepgoryo.EggReturnsHome_1.apk"     74220e46faec9517
echo DONE
