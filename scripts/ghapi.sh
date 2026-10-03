#!/bin/bash
# ghapi.sh — minimal GitHub API helper (gh CLI absent in this container).
# Usage:
#   ghapi.sh issue <number>                 — issue body (JSON)
#   ghapi.sh comments <number>              — issue comments (JSON)
#   ghapi.sh comment <number> <file>        — post comment from file body
#   ghapi.sh state <number> <open|closed>   — set issue state
set -euo pipefail
REPO="Sh-TB/MiniAndroid-Compatibility-Runtime"
TOKEN=$(printf "protocol=https\nhost=github.com\n" | git credential fill 2>/dev/null | sed -n 's/^password=//p')
if [ -z "$TOKEN" ]; then echo "ERROR: no token" >&2; exit 1; fi
api() { curl -sS -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github+json" "$@"; }
cmd="${1:-}"; num="${2:-}"
case "$cmd" in
  issue)     api "https://api.github.com/repos/$REPO/issues/$num" ;;
  comments)  api "https://api.github.com/repos/$REPO/issues/$num/comments?per_page=100" ;;
  comment)   python3 - "$3" <<'PY' > /tmp/_gh_body.json
import json,sys
print(json.dumps({"body": open(sys.argv[1]).read()}))
PY
            api -X POST "https://api.github.com/repos/$REPO/issues/$num/comments" -d @/tmp/_gh_body.json | python3 -c "import json,sys; d=json.load(sys.stdin); print('comment_id:', d.get('id'), 'url:', d.get('html_url'))" ;;
  state)     python3 - > /tmp/_gh_state.json <<PY
import json
print(json.dumps({"state": "$3"}))
PY
            api -X PATCH "https://api.github.com/repos/$REPO/issues/$num" -d @/tmp/_gh_state.json | python3 -c "import json,sys; print('state:', json.load(sys.stdin).get('state'))" ;;
  *) echo "unknown cmd" >&2; exit 2 ;;
esac
