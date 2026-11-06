#!/usr/bin/env python3
"""S178: extract per-finding essentials from #529 (body + 3 round comments):
ID, status line, file/symbol references, and the core claim paragraph."""
import re, json

sources = {}
body = open("evidence/s178_issue529/529_body.md").read()
sources["body"] = body
cs = json.load(open("evidence/s178_issue529/529_comments.json"))
for i, c in enumerate(cs):
    sources[f"comment{i+1}_{c['id']}"] = c.get("body") or ""

out = {}
for src, text in sources.items():
    # split into finding blocks by ### headings
    blocks = re.split(r"(?m)^### ", text)
    for b in blocks[1:]:
        lines = b.split("\n")
        head = lines[0].strip()
        m = re.match(r"(D-P\d-\d+)", head)
        if not m: continue
        fid = m.group(1)
        status = ""
        sm = re.search(r"\*\*Status:\*\*\*\s*(.+)", b) or re.search(r"\*\*Status:\*\*\s*(.+)", b)
        if sm: status = sm.group(1).strip()
        # file references
        files = sorted(set(re.findall(r"`([\w/]+\.(?:cpp|h))`", b)))
        # symbol-ish backticked identifiers
        syms = re.findall(r"`([A-Za-z_][\w:<>~]*::[\w:~]+|[\w:]+_\s*\[|pc_visit_count_|[\w]+_[\w]*\(\))`", b)
        # core claim: first non-empty paragraph after '**A. Finding**' or after the heading
        core = ""
        am = re.search(r"\*\*A\.\s*Finding\*\*(?:\s*\([^)]*\))?\n(.*?)(?:\n\*\*[A-Z]|\n---)", b, re.S)
        if am:
            core = " ".join(am.group(1).split())[:700]
        if not core:
            am2 = re.search(r"\n\n(.*?)(?:\n\*\*|\n---)", b, re.S)
            if am2: core = " ".join(am2.group(1).split())[:700]
        out[fid] = out.get(fid, [])
        out[fid].append({"src": src, "head": head[:150], "status": status,
                         "files": files[:6], "core": core})

json.dump(out, open("evidence/s178_issue529/findings_extract.json", "w"), indent=1)
for fid in sorted(out, key=lambda x: (int(x.split("-")[1][1:]), int(x.split("-")[2]))):
    rows = out[fid]
    r0 = rows[0]
    print(f"\n=== {fid} [{r0['status'][:40]}] files={r0['files']}")
    print(f"    {r0['core'][:420]}")
print(f"\ntotal unique findings: {len(out)}")
