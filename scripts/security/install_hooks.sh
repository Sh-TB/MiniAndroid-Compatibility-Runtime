#!/usr/bin/env bash
# install_hooks.sh — wire the S49 secret guard into local git hooks.
# Idempotent: safe to run repeatedly. Overwrites the two hook files below
# (they are guard-managed; other hooks, if any, are left untouched).
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
HOOKS="$ROOT/.git/hooks"
mkdir -p "$HOOKS"
for h in pre-commit pre-push; do
    cp "$ROOT/scripts/security/hooks/$h" "$HOOKS/$h"
    chmod +x "$HOOKS/$h"
    echo "installed: $HOOKS/$h"
done
echo "secret guard wired: commit + push are now fail-closed (scripts/security/check_secrets.sh)."
