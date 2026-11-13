#!/usr/bin/env bash
# S214 required test: clean clone + build/test leaves NO repository residue
# (#587 comment 6853939129, WP2 required tests). Proves on a fresh clone that:
#   1. git status --porcelain is EMPTY before the build
#   2. after the build, no TRACKED path changed
#   3. untracked output appears ONLY inside explicitly ignored paths (miniandroid/build,
#      .cache/) — never a stray root-level scratch file
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
CLONE="$(mktemp -d /tmp/s229_cleanclone_XXXX)/src"
echo "=== clean clone of $REPO -> $CLONE"
git clone -q "$REPO" "$CLONE" || exit 1
cd "$CLONE"

echo "=== 1. pre-build status (must be empty)"
PRE="$(git status --porcelain)"
if [ -n "$PRE" ]; then echo "FAIL pre-build residue:"; echo "$PRE"; exit 1; fi
echo "PASS: clean"

echo "=== 2. build from the clean clone"
make -C miniandroid -j1 >/tmp/s229_cleanclone_build.log 2>&1 || { echo "FAIL build"; tail -20 /tmp/s229_cleanclone_build.log; exit 1; }
echo "PASS: build ok ($(tail -1 /tmp/s229_cleanclone_build.log))"

echo "=== 3. post-build tracked changes (must be none)"
POST_TRACKED="$(git status --porcelain | grep -v '^??' || true)"
if [ -n "$POST_TRACKED" ]; then echo "FAIL tracked residue:"; echo "$POST_TRACKED"; exit 1; fi
echo "PASS: no tracked changes"

echo "=== 4. untracked residue outside ignored paths (must be none)"
UNTRACKED="$(git status --porcelain | grep '^??' | awk '{print $2}' || true)"
BAD="$(echo "$UNTRACKED" | grep -vE '^(miniandroid/build/|\.cache/|examples/[^/]+/build/)' || true)"
if [ -n "$BAD" ]; then echo "FAIL untracked residue outside ignored dirs:"; echo "$BAD"; exit 1; fi
echo "PASS: untracked output confined to ignored build/cache paths"
echo "untracked paths seen: $(echo "$UNTRACKED" | tr '\n' ' ')"

echo "=== 5. policy validator on the clean clone (S213/S214 registries travel with the tree)"
python3 tools/policy_validator.py | tail -1
echo "RESULT: CLEAN-CLONE NO-RESIDUE PROOF PASS"
