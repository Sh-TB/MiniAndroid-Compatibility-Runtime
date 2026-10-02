#!/bin/bash
# F-NEW-228 3-RUN REGRESSION + GOLDEN GATE (v2, dual-config golden detect)
cd /home/z/my-project/miniandroid
OUT=run/f228/regress2
rm -rf "$OUT"; mkdir -p "$OUT"

run3() { # app apk height -> echoes "sha1 sha2 sha3 rcs"
  local app="$1" apk="$2" h="$3"
  local shas="" rcs=""
  for i in 1 2 3; do
    local o="$OUT/$app$h/run$i"
    mkdir -p "$o"
    if [ "$h" = "1920" ]; then
      timeout 200 ./build/miniandroid run "$apk" -o "$o" > /dev/null 2>&1
    else
      timeout 200 ./build/miniandroid run "$apk" --width 1080 --height "$h" -o "$o" > /dev/null 2>&1
    fi
    rcs="$rcs$?"
    if [ -f "$o/screenshot.png" ]; then
      shas="$shas $(sha256sum "$o/screenshot.png" | cut -c1-16)"
    else
      shas="$shas NOSCREEN"
    fi
  done
  echo "$shas|$rcs"
}

check() { # name apk golden
  local name="$1" apk="$2" golden="$3"
  local r1920 r2340 s rc det verdict
  r1920=$(run3 "$name" "$apk" 1920); s="${r1920%%|*}"; rc="${r1920##*|}"
  local a b c; a=$(echo $s|awk '{print $1}'); b=$(echo $s|awk '{print $2}'); c=$(echo $s|awk '{print $3}')
  det="VARIES"; [ "$a" = "$b" ] && [ "$b" = "$c" ] && det="x3id"
  verdict="NO-SCREEN"; [ "$a" != "NOSCREEN" ] && verdict="GOLDEN-MATCH@1920"
  [ "$verdict" = "NO-SCREEN" -o "$a" != "$golden" ] && {
    r2340=$(run3 "$name" "$apk" 2340)
    local s2="${r2340%%|*}"; local a2=$(echo $s2|awk '{print $1}')
    local det2="VARIES"
    local b2 c2; b2=$(echo $s2|awk '{print $2}'); c2=$(echo $s2|awk '{print $3}')
    [ "$a2" = "$b2" ] && [ "$b2" = "$c2" ] && det2="x3id"
    if [ "$a2" = "$golden" ]; then verdict="GOLDEN-MATCH@2340"
    else verdict="DRIFT(1920:$a 2340:$a2)"; fi
    echo "$name | rc=$rc | 1920:$s ($det) | 2340:$s2 ($det2) | golden=$golden | $verdict"
    return
  }
  echo "$name | rc=$rc | 1920:$s ($det) | golden=$golden | $verdict"
}

check dooz        /tmp/my-project/apk_cache/corpus/dooz.apk                                   d602648e8e401895
check ssw         /tmp/my-project/apk_cache/com.github.muellerma.stopwatch_6.apk              f48ae6d467d1e746
check headingcalc /tmp/my-project/apk_cache/org.debian.eugen.headingcalculator_1.apk          be1cea9cf994b26a
check microtimer  /tmp/my-project/apk_cache/dubrowgn.microtimer_8.apk                         da73010a37dd0189
check unote       /tmp/my-project/apk_cache/app.varlorg.unote_30.apk                          4f1a9e4e8f64fae8
check secuso      /home/z/my-project/upload/notes_secuso_105.apk                              eb5ebd559cad1028
check whatsapp    /tmp/my-project/apk_cache/whatsapp.apk                                      31ddd4d5b8e6d18e
check opencalc    /home/z/my-project/upload/opencalculator_53.apk                             2291d74de0b6bac5
