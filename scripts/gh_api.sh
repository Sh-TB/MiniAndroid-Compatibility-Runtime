#!/bin/bash
# Fetch GitHub API using repo credential helper (token never printed)
CRED=$(printf "protocol=https\nhost=github.com\n" | git credential fill 2>/dev/null)
TOKEN=$(echo "$CRED" | grep '^password=' | cut -d= -f2-)
exec curl -sS -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github+json" "$@"
