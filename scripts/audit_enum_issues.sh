#!/bin/bash
# s59: paginate all open GitHub issues (excl PRs) into run/audit/issues_p*.json
set -e
cd "$(dirname "$0")/.."
CRED=$(printf "protocol=https\nhost=github.com\n" | git credential fill 2>/dev/null)
TOKEN=$(echo "$CRED" | grep '^password=' | cut -d= -f2-)
REPO="Sh-TB/MiniAndroid-Compatibility-Runtime"
PAGE=1
while : ; do
  curl -sS --max-time 90 -H "Authorization: token $TOKEN" \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/$REPO/issues?state=open&per_page=100&page=$PAGE&sort=created&direction=asc" \
    -o "run/audit/issues_p${PAGE}.json"
  COUNT=$(python3 -c "import json; print(len(json.load(open('run/audit/issues_p${PAGE}.json'))))")
  echo "page $PAGE: $COUNT items"
  [ "$COUNT" -lt 100 ] && break
  PAGE=$((PAGE+1))
done
echo "done: $PAGE pages"
