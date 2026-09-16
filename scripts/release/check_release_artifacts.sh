#!/usr/bin/env bash
# ============================================================================
# check_release_artifacts.sh — S48 §23 pre-release guard.
#
# Fails if a release staging directory contains forbidden content or if an
# artifact size blows past the recorded baseline envelope. Run AFTER
# scripts/release/package_release.sh and BEFORE publishing/pushing anything.
#
# Forbidden inside release artifacts (the "1.5GB dump" incident law):
#   raw campaign logs, per-instruction traces, run outputs, forensic session
#   dirs, VCS internals, build caches, temporary/backup files.
# Documented exception: examples/demo-app/build/miniandroid-demo.apk — a
# FIRST-PARTY demo built from in-repo sources, deliberately shipped since
# v0.0.2 as the runnable proof app (see scripts/release/README-windows.txt).
# The zero-APK-in-repo law targets third-party/corpus APKs, not this demo.
#
# Usage: bash scripts/release/check_release_artifacts.sh <staging-dir|archive>...
# Exit:  0 = clean, 1 = violation (message lists every finding).
# ============================================================================
set -uo pipefail

if [ $# -lt 1 ]; then
    echo "usage: $0 <staging-or-dist-dir>..." >&2
    exit 1
fi

# size sanity envelope (bytes) — per-artifact hard fail ceiling.
# Baseline: v0.0.6 Windows zip ~= 6 MB, linux tar.gz ~= 6 MB (exe ~9.6 MB
# statically linked). A 100 MB artifact is already 10x the envelope and
# almost certainly contaminated; 1 GB+ means a campaign dump leaked in.
FAIL_BYTES=$((100 * 1024 * 1024))
WARN_BYTES=$((20 * 1024 * 1024))

FORBIDDEN_NAMES='(^|/)(\.git|run|archive|gpg_[A-Za-z0-9_]*|tmp|cache|build|build-win|work|win_src|win_deps|llvm-mingw[^/]*|corpus_cache|node_modules)(/|$)'
FORBIDDEN_SUFFIX='\.(log|trace|dump|o|obj|ppm|aar|jar|pyc|class|dex)$'
ALLOWED_NAMES='(^|/)miniandroid-demo\.apk$'

VIOLATIONS=0
report() { echo "VIOLATION: $1"; VIOLATIONS=$((VIOLATIONS + 1)); }

for target in "$@"; do
    if [ -d "$target" ]; then
        DIR="$target"
    elif [ -f "$target" ] && [[ "$target" == *.tar.gz ]]; then
        DIR=$(mktemp -d)
        tar xzf "$target" -C "$DIR"
        CLEANUP_DIRS+=("$DIR")
    elif [ -f "$target" ] && [[ "$target" == *.zip ]]; then
        DIR=$(mktemp -d)
        unzip -q "$target" -d "$DIR"
        CLEANUP_DIRS+=("$DIR")
    else
        report "not a directory or supported archive: $target"
        continue
    fi
    echo "== auditing $target"

    # audit with RELATIVE paths so the auditor's own temp roots (/tmp/…)
    # can never trip the forbidden-component rules
    # 1. forbidden path components / names (first-party demo APK allowed)
    while IFS= read -r -d '' p; do report "forbidden path: $p"; done \
        < <(cd "$DIR" && find . -type f -print0 2>/dev/null | grep -zvE "$ALLOWED_NAMES" | grep -zE "$FORBIDDEN_NAMES")

    # 2. forbidden file types (logs/traces/dumps/build byproducts; demo APK allowed)
    while IFS= read -r -d '' p; do report "forbidden file type: $p"; done \
        < <(cd "$DIR" && find . -type f -print0 2>/dev/null | grep -zvE "$ALLOWED_NAMES" | grep -zE "$FORBIDDEN_SUFFIX")

    # 3. oversize files (>10 MB single file inside a package is suspicious;
    #    the runtime binary itself is the only expected multi-MB file)
    while IFS= read -r -d '' p; do
        sz=$(stat -c %s "$p")
        case "$(basename "$p")" in
            MiniAndroid.exe|miniandroid) ;;
            *) report "oversize file (${sz} B): $p" ;;
        esac
    done < <(cd "$DIR" && find . -type f -size +10M -print0 2>/dev/null)

    # 4. artifact-level size sanity
    if [ -d "$target" ]; then
        total=$(du -sb "$target" | cut -f1)
    else
        total=$(stat -c %s "$target")
    fi
    if [ "$total" -gt "$FAIL_BYTES" ]; then
        report "artifact far above baseline envelope (${total} B): $target"
    elif [ "$total" -gt "$WARN_BYTES" ]; then
        echo "WARNING: artifact above expected envelope (${total} B): $target"
    fi
done

for d in "${CLEANUP_DIRS[@]:-}"; do [ -n "$d" ] && rm -rf "$d"; done

if [ "$VIOLATIONS" -gt 0 ]; then
    echo "RELEASE GUARD: FAIL ($VIOLATIONS violations)"
    exit 1
fi
echo "RELEASE GUARD: CLEAN"
