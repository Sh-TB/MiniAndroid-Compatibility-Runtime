#!/usr/bin/env bash
# w22_b1_fast.sh — B1 fast baseline experiments (serial, quiet machine).
# Appends a codegen-neutral comment to a target source, rebuilds, reverts.
# Every measurement goes through scripts/w22_build_run.py -> jsonl + log.
set -u
cd /home/z/my-project/miniandroid
RUN="/usr/bin/python3 /home/z/my-project/scripts/w22_build_run.py"
OUT=evidence/w22/b1_experiments.jsonl
LOGD=evidence/w22/b1_logs
mkdir -p "$LOGD"
touch "$OUT"

phase() { # phase tag, then command...
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

# --- no-op x3 ---
for i in 1 2 3; do phase "noop_$i" make -j1 --output-sync all; done

# --- link-only: refresh a mid .o stamp -> relink only ---
find build/dex -name 'mutf8.o' -exec touch {} \;
phase "link_only" make -j1 --output-sync all

# --- pick smallest manifest TU as the leaf probe ---
LEAF=$(for f in $(grep -v '^#' core_sources.manifest); do
         [ -f "src/$f" ] && echo "$(wc -l < "src/$f") $f"; done | sort -n | head -3 | tail -1 | awk '{print $2}')
echo "LEAF_TU=$LEAF" >> "$LOGD/progress.txt"
printf '\n// W22-B1 leaf-edit probe (codegen-neutral comment)\n' >> "src/$LEAF"
phase "leaf_edit" make -j1 --output-sync all
git -C /home/z/my-project checkout -- "miniandroid/src/$LEAF"

# --- domain TU edit (bridge domain family) ---
DOMAIN=src/dex/dalvik_bridge_domain_io_lang.cpp
wc -l "$DOMAIN" >> "$LOGD/progress.txt"
printf '\n// W22-B1 domain-edit probe (codegen-neutral comment)\n' >> "$DOMAIN"
phase "domain_edit" make -j1 --output-sync all
git -C /home/z/my-project checkout -- miniandroid/src/dex/dalvik_bridge_domain_io_lang.cpp

# --- no-op confirmation after reverts ---
phase "noop_after" make -j1 --output-sync all
echo "=== B1 fast DONE" >> "$LOGD/progress.txt"
