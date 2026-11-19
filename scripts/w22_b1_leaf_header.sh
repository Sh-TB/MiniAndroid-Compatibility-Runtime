#!/usr/bin/env bash
# w22_b1_leaf_header.sh — B1 leaf-edit probes + central-header cascade probe.
# Comment-only edits (codegen-neutral). After each revert the original mtime
# is restored so no redundant rebuild follows.
set -u
cd /home/z/my-project/miniandroid
RUN="/usr/bin/python3 /home/z/my-project/scripts/w22_build_run.py"
OUT=evidence/w22/b1_experiments.jsonl
LOGD=evidence/w22/b1_logs
mkdir -p "$LOGD"

phase() {
  local tag="$1"; shift
  echo "=== PHASE $tag $(date -Is)" >> "$LOGD/progress.txt"
  $RUN --log "$LOGD/$tag.log" --out "$OUT" "$@" >/dev/null 2>>"$LOGD/progress.txt"
  python3 - "$tag" "$OUT" <<'EOF'
import json, sys
tag, out = sys.argv[1], sys.argv[2]
last = None
for line in open(out):
    r = json.loads(line)
    if r["cmd"] and r["cmd"][0] == "make":
        last = r
print("RESULT %s wall=%.2fs rc=%d cpu=%.2f rss=%dMB" % (
    tag, last["wall_s"], last["rc"], last["cpu_user_s"] + last["cpu_sys_s"],
    last["maxrss_kb"] // 1024))
EOF
}

revert_keep_mtime() { # <repo-relative file>
  local f="$1" m
  m=$(stat -c %Y "/home/z/my-project/miniandroid/$f")
  git -C /home/z/my-project checkout -- "miniandroid/$f"
  touch -d @"$m" "/home/z/my-project/miniandroid/$f"
}

# --- leaf probe 1: smallest manifest TU ---
LEAF1=$(for f in $(grep -v '^#' core_sources.manifest); do
          [ -f "$f" ] && echo "$(wc -l < "$f") $f"; done | sort -n | head -1 | awk '{print $2}')
echo "LEAF1=$LEAF1" >> "$LOGD/progress.txt"
printf '\n// W22-B1 leaf probe (codegen-neutral comment)\n' >> "$LEAF1"
phase "leaf_edit_smallest" make -j1 --output-sync all
revert_keep_mtime "$LEAF1"

# --- leaf probe 2: representative mid-size leaf TU ---
LEAF2=src/dex/class_resolver.cpp
echo "LEAF2=$LEAF2 lines=$(wc -l < $LEAF2)" >> "$LOGD/progress.txt"
printf '\n// W22-B1 leaf probe 2 (codegen-neutral comment)\n' >> "$LEAF2"
phase "leaf_edit_mid" make -j1 --output-sync all
revert_keep_mtime "$LEAF2"

# --- central-header cascade: dalvik_engine.h (the 4-minute-op reproduction) ---
HDR=src/dex/dalvik_engine.h
echo "HDR=$HDR lines=$(wc -l < $HDR)" >> "$LOGD/progress.txt"
printf '\n// W22-B1 header-cascade probe (codegen-neutral comment)\n' >> "$HDR"
phase "header_cascade_engine_h" make -j1 --output-sync all
revert_keep_mtime "$HDR"
phase "noop_confirm" make -j1 --output-sync all
echo "=== B1 leaf+header DONE" >> "$LOGD/progress.txt"
