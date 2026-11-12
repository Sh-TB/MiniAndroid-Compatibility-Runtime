#!/bin/bash
# S222: pull ALL comments + issue bodies for #582, #583, #584 (per_page=100 pagination)
set -u
REPO="Sh-TB/MiniAndroid-Compatibility-Runtime"
CRED=$(printf 'protocol=https\nhost=github.com\n\n' | git credential fill 2>/dev/null | grep '^password=' | cut -d= -f2)
OUT=/home/z/my-project/evidence/s222
mkdir -p "$OUT"
for N in 582 583 584; do
  PAGE=1
  while : ; do
    F="$OUT/issue_${N}_comments_p${PAGE}.json"
    HTTP=$(curl -sS -w '%{http_code}' -o "$F" \
      -H "Authorization: token $CRED" -H "Accept: application/vnd.github+json" \
      "https://api.github.com/repos/$REPO/issues/$N/comments?per_page=100&page=$PAGE")
    CNT=$(python3 -c "import json;print(len(json.load(open('$F'))))" 2>/dev/null || echo -1)
    echo "issue $N page $PAGE http=$HTTP count=$CNT"
    [ "$CNT" -lt 100 ] && break
    PAGE=$((PAGE+1))
  done
done
# bodies
for N in 582 583 584; do
  curl -sS -H "Authorization: token $CRED" -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/$REPO/issues/$N" -o "$OUT/issue_${N}_body.json"
done
# compact index of all comments
python3 - <<'EOF'
import json, glob, os
out_dir = "/home/z/my-project/evidence/s222"
rows = []
for f in sorted(glob.glob(os.path.join(out_dir, "issue_*_comments_p*.json"))):
    for c in json.load(open(f)):
        body = c.get("body") or ""
        rows.append({
            "issue": f.split("issue_")[1].split("_")[0],
            "id": c["id"], "user": c["user"]["login"],
            "created": c["created_at"], "updated": c["updated_at"],
            "len": len(body),
            "head": body[:150].replace("\n", " | "),
        })
rows.sort(key=lambda r: (r["issue"], r["created"]))
print(f"total comments: {len(rows)}")
for r in rows:
    print(f"#{r['issue']} id={r['id']} {r['user']:16s} created={r['created']} updated={r['updated']} len={r['len']}")
    print(f"   head: {r['head']}")
EOF
