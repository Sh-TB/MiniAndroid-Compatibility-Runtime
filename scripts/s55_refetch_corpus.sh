#!/usr/bin/env bash
# S55: container reset wiped /home/z/corpus + apk_cache. Re-fetch the corpus
# subset needed for Phase 2 (Notes blocker A, Dooz blocker B, game gates,
# determinism corpus) + the EXT HelloWorldSelfAware fixture.
# Every download is SHA256-verified against miniandroid/APK_REGISTRY.json
# (or the documented fixture ledger). No APK ever enters the repo (zero-APK policy).
set -uo pipefail
CACHE=/home/z/my-project/apk_cache
EXT=/home/z/corpus/external_hello
mkdir -p "$CACHE" "$EXT"

fetch() { # fetch <url> <dest> <expected_sha256_16-prefix>
    local url=$1 dest=$2 want=$3
    if [ -f "$dest" ]; then echo "HAVE $(basename "$dest")"; return 0; fi
    echo "GET $(basename "$dest")"
    curl -sfSL --retry 2 -o "$dest.part" "$url" || { echo "  FETCH-FAIL $url"; rm -f "$dest.part"; return 1; }
    mv "$dest.part" "$dest"
    local got
    got=$(sha256sum "$dest" | cut -c1-16)
    if [ -n "$want" ] && [ "$got" != "$want" ]; then
        echo "  SHA-MISMATCH got=$got want=$want — removing"; rm -f "$dest"; return 1
    fi
    echo "  SHA-OK $got${want:+ (verified)}"
}

# Blocker A + gates + determinism corpus (registry SHAs)
fetch https://f-droid.org/repo/org.billthefarmer.notes_139.apk        "$CACHE/org.billthefarmer.notes_139.apk"        82cf8bc44c163748
fetch https://f-droid.org/repo/de.duenndns.gmdice_8.apk              "$CACHE/de.duenndns.gmdice_8.apk"               1621eda11b5dbc0c
fetch https://f-droid.org/repo/com.chessclock.android_29.apk         "$CACHE/com.chessclock.android_29.apk"          5ca6f2c54c05efe7
fetch https://f-droid.org/repo/dubrowgn.microtimer_8.apk             "$CACHE/dubrowgn.microtimer_8.apk"              79c6f730f64886e7
fetch https://f-droid.org/repo/omegacentauri.mobi.simplestopwatch_26.apk "$CACHE/omegacentauri.mobi.simplestopwatch_26.apk" b3ec1a5ec24ce53b
fetch https://f-droid.org/repo/org.debian.eugen.headingcalculator_1.apk  "$CACHE/org.debian.eugen.headingcalculator_1.apk" 274ec873098eea51
fetch https://f-droid.org/repo/app.varlorg.unote_30.apk              "$CACHE/app.varlorg.unote_30.apk"               be91103f0e7db443
# Blocker B: Dooz v18 (registry) + v23 (S45+ face)
fetch https://f-droid.org/repo/io.github.yamin8000.dooz_18.apk       "$CACHE/io.github.yamin8000.dooz_18.apk"        d81292cd346dcb23
fetch https://f-droid.org/repo/io.github.yamin8000.dooz_23.apk       "$CACHE/io.github.yamin8000.dooz_23.apk"        ""

# EXT fixture (docs/evidence/EXTERNAL_FIXTURE_HELLOWORLDSELFAWARE.md ledger)
fetch https://github.com/Appliberated/HelloWorldSelfAware/releases/download/v1.1.0/HelloWorldSelfAware-1.1.0-android.apk \
      "$EXT/HelloWorldSelfAware-1.1.0-android.apk" 009b467109c4d48d
fetch https://github.com/Appliberated/HelloWorldSelfAware/raw/v1.1.0/repo-assets/helloworldselfaware-android-phone-screenshot.png \
      "$EXT/helloworldselfaware-android-phone-screenshot.png" ""

echo "=== SUMMARY ==="
ls -la "$CACHE" "$EXT" 2>/dev/null | grep -E "apk|png" || true
