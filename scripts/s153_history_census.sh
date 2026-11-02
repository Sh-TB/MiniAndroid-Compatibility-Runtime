#!/bin/bash
# S153: full census of git history blob weight by category
cd /home/z/my-project
TMP=$(mktemp -d)
git rev-list --objects --all > "$TMP/objs.txt"
git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' --batch-all-objects > /dev/null 2>&1
# map objects to paths, keep blobs >100KB
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' 2>/dev/null \
 | awk '$1=="blob" && $3>=100000 {size=$3; $1=$2=$3=""; sub(/^ +/,""); print size "\t" $0}' > "$TMP/big.txt"

cat "$TMP/big.txt" | awk -F'\t' '{s+=$1} END {printf "TOTAL blobs>=100KB: %d files, %.1f MB\n", NR, s/1048576}'

echo "== by extension =="
cut -f2 "$TMP/big.txt" | awk '{n=split($0,a,"."); ext=(n>1)?tolower(a[n]):"(none)"; c[ext]++; s[ext]}' /dev/null 2>/dev/null
awk -F'\t' '{n=split($2,a,"."); ext=(n>1)?tolower(a[n]):"(none)"; c[ext]++; s[ext]+=$1} END {for(e in c) printf "%8.1f MB  %6d  .%s\n", s[e]/1048576, c[e], e}' "$TMP/big.txt" | sort -rn | head -20

echo "== by category regex =="
census() { # name regex
  awk -F'\t' -v re="$2" '$2 ~ re {c++; s+=$1} END {printf "%9.1f MB  %5d files  %s\n", s/1048576, c, "'"$1"'"}' "$TMP/big.txt"
}
census "APK files"              '\.apk($| )|\.apks($| )|\.aab($| )'
census "logs (.log/.txt logs)"  '\.log$|console\.txt$|logcat'
census "PPM screenshots"        '\.ppm$'
census "PNG screenshots"        '\.png$'
census "JPG screenshots"        '\.jpg$|\.jpeg$'
census "dex/odex"               '\.dex$|\.odex$|\.vdex$'
census "smali/decompiled"       'smali|decomp|jadx|disasm|/dalvik/'
census "view_tree dumps"        'view_tree'
census "toolchain jars/zips"    '\.jar$|\.zip$|kotlinc|r8\.|android-34|aapt2|d8$|dx$'
census "engine/binaries a.out"  'a\.out$|miniandroid_pre|miniandroid_post|/miniandroid$'
census "arsc/framework_res"     '\.arsc$|framework_res'
census "index json big"         'archidx|index-v1|index\.json'
census "font files"             '\.ttf$|\.otf$'
census "tmp/ dir anything"      '^tmp/'
census "run/ dir anything"      '^run/'
census "evidence/ dir"          '^evidence/'
census "docs/ dir"              '^docs/'
census "miniandroid/ dir"       '^miniandroid/'
census "upstream/ dir"          '^upstream/'
census "tools/ dir"             '^tools/'
census "top-30 heaviest overall" '' # placeholder
echo "== TOP 25 heaviest blobs =="
sort -rn "$TMP/big.txt" | head -25 | awk -F'\t' '{printf "%8.1f MB  %s\n", $1/1048576, $2}'
rm -rf "$TMP"
