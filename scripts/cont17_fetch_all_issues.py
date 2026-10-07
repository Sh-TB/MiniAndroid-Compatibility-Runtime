#!/usr/bin/env python3
"""CONT-17 W0: fine-grained GitHub sweep — fetch the FULL issue list (all states,
all pages) via public HTML, extract number/state/title from the embedded React data,
then fetch each issue page for comment counts. Output: evidence/cont17/github_issue_index.json"""
import re, json, os, urllib.request, time

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = "/home/z/my-project/evidence/cont17/github_issue_index.json"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (cont17-issue-sweep)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

# Page 1: open issues sorted by number asc
issues = {}
seen_pages = 0
for state in ("open", "closed"):
    page = 1
    while True:
        url = f"https://github.com/{REPO}/issues?q=is%3Aissue+is%3A{state}&page={page}"
        try:
            page_html = fetch(url)
        except Exception as e:
            print(f"FETCH-FAIL {state} p{page}: {e}")
            break
        # Embedded JSON in script[type=application/json] data-target="react-app.embeddedData"
        m = re.search(r'<script type="application/json" data-target="react-app\.embeddedData">(.*?)</script>', page_html, re.S)
        items = []
        if m:
            try:
                data = json.loads(m.group(1))
                # walk for issue nodes
                def walk(o):
                    if isinstance(o, dict):
                        if "number" in o and "title" in o and ("state" in o or "stateOrKind" in o):
                            items.append(o)
                        for v in o.values():
                            walk(v)
                    elif isinstance(o, list):
                        for v in o:
                            walk(v)
                walk(data)
            except Exception as e:
                print(f"JSON-PARSE-FAIL {state} p{page}: {e}")
        new = 0
        for it in items:
            n = it.get("number")
            if n and n not in issues:
                issues[n] = {
                    "number": n,
                    "state": it.get("state") or state,
                    "title": (it.get("title") or "").strip(),
                    "comments": it.get("commentCount", it.get("comments", 0)),
                }
                new += 1
        seen_pages += 1
        print(f"{state} page {page}: {new} new (cum {len(issues)})")
        if new == 0:
            break
        page += 1
        if page > 30:
            break
        time.sleep(0.4)

issues = dict(sorted(issues.items()))
with open(OUT, "w") as f:
    json.dump({"fetched_at": "2026-10-08", "repo": REPO, "count": len(issues), "issues": list(issues.values())}, f, indent=1)
opens = [i for i in issues.values() if i["state"] == "open"]
print(f"TOTAL {len(issues)} | OPEN {len(opens)} | CLOSED {len(issues)-len(opens)}")
for i in issues.values():
    mark = "OPEN " if i["state"] == "open" else "clos "
    print(f"#{i['number']:<4} {mark} c={i['comments']:<3} {i['title'][:100]}")
