#!/usr/bin/env python3
"""CONT-18g: FINAL sweep — fetch ALL issue threads (364..381) fresh via HTML,
extract every comment body, and mine finding-shaped statements that may have
been stated but never registered/fixed. Output feeds the missed-root audit."""
import re, html, json, os, urllib.request, time, hashlib

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = "/home/z/my-project/evidence/cont18f/issue_comments_fresh.json"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (cont18f-final-sweep)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def extract_markdown_blocks(page):
    blocks = []
    for m in re.finditer(r'<div class="markdown-body', page):
        i = m.start()
        j = page.find('>', i)
        depth, k = 1, j + 1
        while depth > 0 and k < len(page):
            no = page.find('<div', k)
            nc = page.find('</div>', k)
            if nc == -1:
                break
            if no != -1 and no < nc:
                depth += 1
                k = no + 4
            else:
                depth -= 1
                k = nc + 6
        block = page[j + 1:k - 6]
        txt = re.sub(r'<br\s*/?>', '\n', block)
        txt = re.sub(r'</(p|li|h\d|pre|div|tr)>', '\n', txt)
        txt = re.sub(r'<li[^>]*>', '- ', txt)
        txt = re.sub(r'<[^>]+>', '', txt)
        txt = html.unescape(txt)
        blocks.append(txt.strip())
    return blocks

result = {}
for num in range(353, 382):
    try:
        page = fetch(f"https://github.com/{REPO}/issues/{num}")
    except Exception as e:
        result[num] = {"error": f"{type(e).__name__}: {e}"[:200]}
        print(f"#{num}: FETCH FAIL {e}")
        time.sleep(0.3)
        continue
    blocks = extract_markdown_blocks(page)
    body = blocks[0] if blocks else ""
    comments = blocks[1:] if len(blocks) > 1 else []
    result[num] = {"body_head": body[:800], "num_blocks": len(blocks),
                   "comments": comments}
    print(f"#{num}: body {len(body)} chars, {len(comments)} comment blocks")
    time.sleep(0.35)

with open(OUT, "w") as f:
    json.dump(result, f, indent=1)
print("saved:", OUT)
