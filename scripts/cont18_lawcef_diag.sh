#!/usr/bin/env bash
# CONT-18: LAW-C/E/F determination diagnostics.
# Runs the fcol probe with a chosen MINIANDROID diag env and captures stderr.
# Usage: cont18_lawcef_diag.sh <outdir> [EXTRA_ENV_NAME ...]
set -u
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$1; shift
mkdir -p "$OUT"
STORE=$OUT/store_fcol
rm -rf "$STORE"; mkdir -p "$STORE"

PKGJSON=$("$BIN" install "$BASE/run/w7/fcol.apk" --data-root "$STORE" 2>/dev/null)
PKG=$(echo "$PKGJSON" | python3 -c "import json,sys; s=sys.stdin.read(); print(json.JSONDecoder().raw_decode(s[s.index('{'):])[0]['package'])")
echo "pkg=$PKG"

ODIR=$OUT/fcol
rm -rf "$ODIR"; mkdir -p "$ODIR"
# Keep only MINIANDROID_* diags we explicitly pass; strip others.
env | grep -o '^MINIANDROID_[A-Z0-9_]*' > "$OUT/envlist.txt" || true
# Build clean env
envstd=$(env | grep -v '^MINIANDROID_' | grep -v '^_=')
{
  echo "$envstd"
} > /dev/null
# Run with explicit diag passthrough
{
  set -a
  # shellcheck disable=SC2046
  for v in "$@"; do
    val=$(printenv "$v" 2>/dev/null)
    [ -n "$val" ] && export "$v=$val"
  done
  set +a
  "$BIN" run --package "$PKG" --data-root "$STORE" --max-seconds 150 --frames 40 -o "$ODIR"
} > "$ODIR/run.log" 2> "$ODIR/diag.log"
echo "=== rows ==="
grep -E 'K[0-9]+\|(PASS|FAIL)' "$ODIR/run.log" | head -20
echo "=== diag size: $(wc -l < "$ODIR/diag.log") lines"
