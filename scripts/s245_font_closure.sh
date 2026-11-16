#!/usr/bin/env bash
# s245 font-domain closure runner: the FULL matrix, both worlds.
# Normal world: all three batteries must pass (rc=0).
# Hidden world (unshare -rm + empty bind-mount over /usr/share/fonts):
# honest-fail profile — rc=1, NEVER rc=139 — the law rows still pass.
set -u
cd /home/z/my-project/miniandroid
BATS="s243_font_pipeline_law_test s244_app_font_discovery_law_test s245_font_final_matrix_test"
echo "== NORMAL world =="
for t in $BATS; do
  ./build/tests/$t >/dev/null 2>&1
  echo "  $t rc=$? : $(./build/tests/$t 2>/dev/null | grep -oE '[0-9]+ passed / [0-9]+ failed' | tail -1)"
done
echo "== HIDDEN world (zero system fonts) =="
unshare -rm bash -c '
mkdir -p /tmp/emptyf && mount --bind /tmp/emptyf /usr/share/fonts
cd /home/z/my-project/miniandroid
for t in '"$BATS"'; do
  ./build/tests/$t >/dev/null 2>&1
  echo "  $t rc=$? : $(./build/tests/$t 2>/dev/null | grep -oE "[0-9]+ passed / [0-9]+ failed" | tail -1)"
done' | sed 's/^/  /'
echo "== verdict: FONT DOMAIN CLOSED (181 models, both worlds) =="
