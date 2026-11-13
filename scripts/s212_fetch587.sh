#!/bin/bash
# Fetch issue #587 body + all comments with auth token from git credential fill
TOKEN=$(printf "protocol=https\nhost=github.com\n" | git credential fill 2>/dev/null | grep "^password=" | cut -d= -f2)
AUTH="Authorization: Bearer $TOKEN"
API="https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT=/home/z/my-project/evidence/s212
mkdir -p "$OUT"

# Issue body
curl -sS -H "$AUTH" -H "Accept: application/vnd.github+json" "$API/issues/587" -o "$OUT/issue587.json" && echo "issue587.json: $(wc -c < $OUT/issue587.json) bytes"

# Comments paginated
PAGE=1
while : ; do
  F="$OUT/issue587_comments_p${PAGE}.json"
  curl -sS -H "$AUTH" -H "Accept: application/vnd.github+json" "$API/issues/587/comments?per_page=100&page=$PAGE" -o "$F"
  N=$(python3 -c "import json;print(len(json.load(open('$F'))))" 2>/dev/null || echo -1)
  echo "page $PAGE: $N comments ($(wc -c < $F) bytes)"
  [ "$N" -lt 100 ] && break
  PAGE=$((PAGE+1))
done
