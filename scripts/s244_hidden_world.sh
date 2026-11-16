#!/usr/bin/env bash
# s244 hidden-world reproduction: the no-default-font chain proof.
# Hides /usr/share/fonts via a user-namespace mount (no root needed) and
# runs both font batteries. HONEST outcome contract: rc=1 (the batteries'
# own honest failure — the system-truth rows fail), NEVER rc=139 (crash),
# and s244's N4 (app-font render proof) must PASS — the app's own font
# rescues text even with zero system fonts (AOSP createFromAsset law).
set -u
cd /home/z/my-project/miniandroid
unshare -rm bash -c '
mkdir -p /tmp/emptyf && mount --bind /tmp/emptyf /usr/share/fonts
cd /home/z/my-project/miniandroid
./build/tests/s244_app_font_discovery_law_test > /tmp/s244_hidden.log 2>/dev/null
echo "s244_hidden_rc=$?"
./build/tests/s243_font_pipeline_law_test > /tmp/s243_hidden.log 2>/dev/null
echo "s243_hidden_rc=$?"'
for f in /tmp/s244_hidden.log /tmp/s243_hidden.log; do
  echo "== $f: $(grep -oE '[0-9]+ passed / [0-9]+ failed' $f | tail -1)"
done
grep -E "N4_app_face_render_proof" /tmp/s244_hidden.log
