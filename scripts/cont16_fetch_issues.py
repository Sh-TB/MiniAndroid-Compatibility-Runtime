#!/usr/bin/env python3
"""CONT-16 PHASE 0: fetch GitHub issues (#375/#379/#380) bodies + comments via HTML.
API is rate-limited; HTML pages are public. Extract comment-body blocks."""
import re, html, json, sys, urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
ISSUES = [375, 379, 380]

def fetch(num):
    url = f"https://github.com/{REPO}/issues/{num}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (cont16-lineage-reader)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def extract(page):
    # New GitHub React HTML: bodies live in <div class="markdown-body ..."> with nested divs.
    # Use div-depth scanning from each markdown-body opening tag.
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
        txt = re.sub(r'[ \t]+\n', '\n', txt)
        txt = re.sub(r'\n{3,}', '\n\n', txt).strip()
        blocks.append(txt)
    return blocks

def extract_title(page):
    m = re.search(r'<title>(.*?)</title>', page)
    return html.unescape(m.group(1))[:160] if m else "?"

result = {}
for num in ISSUES:
    try:
        page = fetch(num)
        title = extract_title(page)
        blocks = extract(page)
        result[f"issue_{num}"] = {"title": title, "n_blocks": len(blocks),
                                  "bodies": [b[:50000] for b in blocks]}
        print(f"#{num}: {title}  ({len(blocks)} comment-body blocks)")
    except Exception as e:
        result[f"issue_{num}"] = {"error": str(e)}
        print(f"#{num}: ERROR {e}")

with open("/home/z/my-project/evidence/cont16/github_issues.json", "w") as f:
    json.dump(result, f, indent=1)
print("saved evidence/cont16/github_issues.json")
