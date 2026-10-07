#!/usr/bin/env python3
"""CONT-17 W0b: fetch ALL comments on the trailing issues (#375..#380) via HTML,
extract comment author + date + body. Detect any friend-agent postings after CONT-16."""
import re, html, json, os, urllib.request, time

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = "/home/z/my-project/evidence/cont17/github_trailing_comments.json"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (cont17-comment-sweep)"})
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
for num in (375, 376, 377, 378, 379, 380):
    page = fetch(f"https://github.com/{REPO}/issues/{num}")
    blocks = extract_markdown_blocks(page)
    # first block = issue body; rest = comments
    body = blocks[0] if blocks else ""
    comments = blocks[1:] if len(blocks) > 1 else []
    # authors/dates via relative-time tags
    times = re.findall(r'<relative-time[^>]*datetime="([^"]+)"', page)
    authors = re.findall(r'class="[^"]*author[^"]*"[^>]*>([^<]+)<', page)
    result[num] = {"body_head": body[:600], "num_blocks": len(blocks), "times": times, "authors": authors[:20], "comments": comments}
    print(f"#{num}: body {len(body)} chars, {len(comments)} comment blocks, {len(times)} timestamps")
    if comments:
        last = comments[-1]
        print(f"   LAST COMMENT HEAD: {last[:200].replace(chr(10),' | ')}")
    time.sleep(0.4)

with open(OUT, "w") as f:
    json.dump(result, f, indent=1)
print("saved:", OUT)
