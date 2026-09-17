#!/usr/bin/env bash
# S52 PHASE 1 — full repository census (evidence policy baseline)
cd /home/z/my-project
echo "=== A. WORKING TREE SIZE ==="
du -sh --exclude=.git . 2>/dev/null
du -sh .git

echo; echo "=== B. TRACKED FILE COUNT ==="
git ls-files | wc -l

echo; echo "=== C. TRACKED FILES BY EXTENSION (top 25) ==="
git ls-files | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -25

echo; echo "=== D. FORBIDDEN CLASSES IN TREE (policy: must be 0) ==="
echo -n "tracked .apk/.aab: "; git ls-files | grep -ciE '\.(apk|aab)$'
echo -n "tracked .dex:      "; git ls-files | grep -ciE '\.dex$'
echo -n "tracked .so/.dll/.exe: "; git ls-files | grep -ciE '\.(so|dll|exe)$'
echo -n "tracked .log:      "; git ls-files | grep -ciE '\.log$'
echo -n "tracked png/jpg:   "; git ls-files | grep -ciE '\.(png|jpg|jpeg)$'
echo -n "tracked .json:     "; git ls-files | grep -ciE '\.json$'
echo -n "tracked .md:       "; git ls-files | grep -ciE '\.md$'

echo; echo "=== E. TRACKED PATH-KEYWORD AUDIT (extraction residue classes) ==="
for kw in META-INF _extracted apk_unpacked corpus_cache tmp decompiled artifacts dump extracted; do
  n=$(git ls-files | grep -ci "$kw")
  echo "$kw: $n"
done

echo; echo "=== F. LARGEST TRACKED FILES (top 20) ==="
git ls-files -z | xargs -0 du -b 2>/dev/null | sort -rn | head -20 | awk '{printf "%10.1f KB  %s\n", $1/1024, $2}'

echo; echo "=== G. LARGEST HISTORICAL BLOBS (top 10, current main chain) ==="
git rev-list --objects --all 2>/dev/null | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' 2>/dev/null | awk '$1=="blob" && $3 > 1048576 {print $3, $4}' | sort -rn | head -10 | awk '{printf "%10.1f MB  %s\n", $1/1048576, $2}'

echo; echo "=== H. DIRECTORY CENSUS (tracked files per top dir) ==="
git ls-files | cut -d/ -f1 | sort | uniq -c | sort -rn

echo; echo "=== I. SCREENSHOTS / IMAGES INVENTORY ==="
git ls-files | grep -iE '\.(png|jpg|jpeg)$' | sed 's|/[^/]*$||' | sort | uniq -c | sort -rn | head -20

echo; echo "=== J. MD FILES UNDER docs/ (count) + top-level dirs ==="
git ls-files 'docs/*.md' | wc -l
git ls-files 'miniandroid/docs/*.md' 2>/dev/null | wc -l

echo; echo "=== K. UNTRACKED-IGNORED BIG ITEMS (local-only) ==="
git status --ignored --short 2>/dev/null | grep '^!!' | head -20
