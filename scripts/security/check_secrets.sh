#!/usr/bin/env bash
# ============================================================================
# check_secrets.sh — S49 permanent secret guard (FAIL CLOSED).
#
# Runs before commit / release / packaging / push. If ANY credential-shaped
# string is detected, the caller MUST abort (exit 1 propagates).
#
# SECURITY PROPERTY OF THIS TOOL: it NEVER prints a matched value or the line
# containing it. Output is limited to: pattern type + file:line (masked).
# Matched content flows only through internal pipes (grep -> cut), never to
# stdout/stderr.
#
# NOTES
#  - Detection deliberately avoids awk: mawk 1.3.4 mishandles ERE interval
#    expressions ({20,}), producing BOTH false positives and missed hits
#    (S49 finding). GNU grep -E is the single regex engine used here.
#  - Token patterns use two-sided boundary guards so that random matches
#    INSIDE long base64 asset blobs (images/videos embedded in HTML) are
#    filtered: inside a base64 run, the char before/after a would-be token is
#    another base64 char; a real key is delimited by quotes/space/newline/=.
#
# Usage:
#   check_secrets.sh --tree      scan the whole working tree (excluding .git)
#   check_secrets.sh --staged    scan files staged for commit (git index)
#   check_secrets.sh PATH...     scan given files/dirs (release staging; zips
#                                must be extracted first — see
#                                scripts/release/check_release_artifacts.sh)
#   check_secrets.sh --selftest  plant synthetic dummy tokens in a temp dir
#                                and prove detection + FP filtering
#
# Exit: 0 = clean, 1 = SECRET FOUND (fail closed), 2 = usage error.
# ============================================================================
set -uo pipefail

SELF="$(readlink -f "$0")"
REPO="$(git -C "$(dirname "$SELF")" rev-parse --show-toplevel 2>/dev/null || echo "")"
ALLOWLIST="$REPO/scripts/security/secret_scan_allowlist"

VIOLATIONS=0

# ---------------------------------------------------------------------------
# Pattern table: NAME|extended-regex (GNU grep -E).
# ---------------------------------------------------------------------------
PATTERNS=(
  'GITHUB_FINEGRAINED_PAT|(^|[^A-Za-z0-9_-])github_pat_[A-Za-z0-9_]{20,}([^A-Za-z0-9_-]|$)'
  'GITHUB_CLASSIC_TOKEN|(^|[^A-Za-z0-9_-])gh[pousr]_[A-Za-z0-9]{16,}([^A-Za-z0-9_-]|$)'
  'AWS_ACCESS_KEY|(^|[^A-Za-z0-9+/])AKIA[A-Z0-9]{16}([^A-Za-z0-9+/=]|$)'
  'AWS_TEMP_KEY|(^|[^A-Za-z0-9+/])ASIA[A-Z0-9]{16}([^A-Za-z0-9+/=]|$)'
  'PRIVATE_KEY_BLOCK|-----BEGIN [A-Z ]*PRIVATE KEY'
  'URL_EMBEDDED_CREDENTIAL|https?://[A-Za-z0-9._%-]+:[A-Za-z0-9._%~!@$%^&*()+={}|;,<>/?-]{3,}@'
  'AUTH_HEADER_TOKEN|[Aa]uthorization.{0,3}(Bearer|Basic|token)[[:space:]]+[A-Za-z0-9._~+/=-]{8,}'
  'OPENAI_STYLE_KEY|(^|[^A-Za-z0-9_-])sk-[A-Za-z0-9]{20,}([^A-Za-z0-9_-]|$)'
  'GOOGLE_API_KEY|(^|[^A-Za-z0-9_-])AIza[0-9A-Za-z_-]{30,}([^A-Za-z0-9_-]|$)'
  'GITLAB_PAT|(^|[^A-Za-z0-9_-])glpat-[A-Za-z0-9_-]{20,}([^A-Za-z0-9_-]|$)'
  'GENERIC_TOKEN_ASSIGN|(GITHUB_TOKEN|GH_TOKEN|GIT_TOKEN|REPO_TOKEN|ACCESS_TOKEN|API_TOKEN|PERSONAL_ACCESS_TOKEN)[      ]*[=:][         ]*[A-Za-z0-9_-]{16,}'
)

# Placeholder filter: matched text containing these is documentation.
PLACEHOLDER_RE='(placeholder|your[_-]?token|changeme|change[_-]?me|example|redacted|masked|user:pass|user:password|john:doe)'

report_hit() { # $1=pattern $2=file $3=line
    echo "SECRET-PATTERN type=$1 at $2:$3 (value=****MASKED****)"
    VIOLATIONS=$((VIOLATIONS + 1))
}

is_allowed() { # $1=file  $2=pattern-name
    [ -f "$ALLOWLIST" ] || return 1
    local rule fre pre
    while IFS= read -r rule; do
        case "$rule" in ''|'#'*) continue ;; esac
        fre="${rule%%|*}"; pre="${rule#*|}"
        if [[ "$1" =~ $fre && "$2" =~ $pre ]]; then return 0; fi
    done < "$ALLOWLIST"
    return 1
}

scan_one_pattern() { # $1="NAME|regex", remaining = paths (dirs recursed)
    local spec="$1"; shift
    local name="${spec%%|*}"
    local regex="${spec#*|}"
    # ONE grep per pattern over all paths. Matched line content flows only
    # through the internal pipe and is never emitted to stdout/stderr; the
    # sed reformatter keeps only "path:line" of each hit. Process
    # substitution keeps report_hit's counter in the CURRENT shell.
    local loc f ln
    while IFS= read -r loc; do
        [ -n "$loc" ] || continue
        # HARDENING: only perfectly-formed "path:digits" lines are reported.
        # If upstream formatting ever degrades, the hit is DROPPED (never
        # printed) — a secret value must have no path to stdout, even if
        # detection reporting degrades. selftest catches that state loudly.
        if [[ "$loc" =~ ^([^:]+):([0-9]+)$ ]]; then
            f="${BASH_REMATCH[1]}"
            ln="${BASH_REMATCH[2]}"
            f="${f#./}"
            if is_allowed "$f" "$name"; then continue; fi
            report_hit "$name" "$f" "$ln"
        fi
    done < <(grep -rHnE -- "$regex" "$@" 2>/dev/null \
        | grep -vE -- "$PLACEHOLDER_RE" \
        | sed -E 's#^([^:]+):([0-9]+):.*$#\1:\2#')
    return 0
}
scan_files() {
    for spec in "${PATTERNS[@]}"; do
        scan_one_pattern "$spec" "$@"
    done
}

collect_tree_files() {
    find . -path ./.git -prune -o -path ./scripts/security/check_secrets.sh -prune -o -type f -print \
        | sed 's#^\./##' | sort
}

main() {
    local mode="${1:-}"
    case "$mode" in
        --tree)
            echo "secret guard: scanning working tree (fail-closed) ..."
            mapfile -t files < <(collect_tree_files)
            scan_files "${files[@]}"
            ;;
        --staged)
            echo "secret guard: scanning staged content (fail-closed) ..."
            mapfile -t files < <(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null | sort -u)
            scan_files "${files[@]}"
            ;;
        --selftest)
            selftest
            return $?
            ;;
        -h|--help|'')
            sed -n '2,45p' "$SELF"
            exit 2
            ;;
        *)
            [ -e "$mode" ] || { echo "usage: $0 --tree|--staged|--selftest|PATH..." >&2; exit 2; }
            scan_files "$@"
            ;;
    esac

    if [ "$VIOLATIONS" -gt 0 ]; then
        echo "SECRET GUARD: FAIL ($VIOLATIONS finding(s)) — values masked; remove the credential and re-run. BLOCKING."
        exit 1
    fi
    echo "SECRET GUARD: PASS (no credential-shaped strings found)"
    exit 0
}

selftest() {
    local tmp
    tmp=$(mktemp -d)
    # Synthetic DUMMY tokens - built by concatenation with 'A' padding, NOT
    # real credentials. The full token shape never appears verbatim in this
    # file; the dummy value only exists inside the temp file at runtime.
    local pad20 pad16 pad33
    pad20=$(printf 'A%.0s' {1..20})
    pad16=$(printf 'A%.0s' {1..16})
    pad33=$(printf 'A%.0s' {1..33})
    printf 'fine=%s%s\n'  "github_" "pat_${pad20}"                > "$tmp/t1.txt"
    printf 'classic=%s\n' "ghp_${pad20}"                           > "$tmp/t2.txt"
    printf 'aws %s\n'     "AKIA${pad16}"                           > "$tmp/t3.txt"
    local urlcred="https://deploy:"       # built across lines so no single
    urlcred+="51eab9c0abcd@"              # source line contains the full
    urlcred+="hooks.internal-svc"         # credential shape (self-scan safe)
    printf 'url=%s\n'     "$urlcred"                              > "$tmp/t4.txt"
    local tokval="GITHUB"
    tokval+="_TOKEN=aaaaaaaaaaaaaaaaaaaa"
    printf 'tok=%s\n'     "$tokval"                               > "$tmp/t5.txt"
    printf 'key %s\n'     "AIzaSy${pad33}"                         > "$tmp/t6.txt"
    printf 'privkey\n-----BEGIN %s %s %s-----\n' RSA "PRIVATE" "KEY" > "$tmp/t7.txt"
    # false-positive battery: placeholders + base64-embedded lookalikes
    printf 'placeholder TOKEN=changeme\n'                            > "$tmp/ok1.txt"
    printf 'doc URL https://user:password@server.example\n'          > "$tmp/ok2.txt"
    printf 'data:image/png;base64,iVBORw0KGgoAKIAAAAAAAAAAAAAAAAACkgAAA'"\n" > "$tmp/ok3.txt"
    printf 'video base64 run with sk- embedded: AAAAAsk-AAAAAAAAAAAAAAAAAAAAAAAAAKIAAA\n' > "$tmp/ok4.txt"
    printf 'mask-icon and desk-items in prose\n'                     > "$tmp/ok5.txt"

    local t before
    for t in t1 t2 t3 t4 t5 t6 t7; do
        before=$VIOLATIONS
        scan_files "$tmp/$t.txt"
        if [ "$VIOLATIONS" -gt "$before" ]; then
            echo "selftest: DETECTED dummy secret in $t.txt (correct)"
        else
            echo "selftest: MISSED dummy secret in $t.txt (GUARD BROKEN)"; rm -rf "$tmp"; exit 1
        fi
    done
    for t in ok1 ok2 ok3 ok4 ok5; do
        before=$VIOLATIONS
        scan_files "$tmp/$t.txt"
        if [ "$VIOLATIONS" -eq "$before" ]; then
            echo "selftest: false-positive source ignored in $t.txt (correct)"
        else
            echo "selftest: FALSE POSITIVE on $t.txt"; rm -rf "$tmp"; exit 1
        fi
    done
    rm -rf "$tmp"
    echo "selftest: GUARD OPERATIONAL (detection + base64/placeholder filtering verified)"
    exit 0
}

main "$@"
