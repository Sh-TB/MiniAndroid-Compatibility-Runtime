#!/bin/bash
# storage_tree_proof.sh — dump the persisted per-package store tree + the
# logical↔physical mapping proof rows (INSTALL_TREE_PROOF source).
set -u
STORE="${1:-/home/z/my-project/run/audit/regression}"
echo "== per-package data trees (physical backing) =="
for pkg_dir in "$STORE"/store_*/data/data/*; do
  [ -d "$pkg_dir" ] || continue
  echo "--- ${pkg_dir#*/store_}"
  find "$pkg_dir" -type f -printf "  %10s  %P\n" | sort -k2
done
echo
echo "== identity (installed base.apk SHA-16) =="
for apk in "$STORE"/store_*/data/app/*/base.apk; do
  [ -f "$apk" ] || continue
  echo "  $(sha256sum "$apk" | cut -c1-16)  ${apk##*/data/app/} (base.apk)"
done
