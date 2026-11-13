#!/usr/bin/env python3
"""S230: extract the 3-part S226 TRANSFER patch from issue #586 comments,
verify the combined sha256 against the posted patch sha16 09768a2375a08cff,
and write /tmp/s226_transfer.patch."""
import json
import hashlib
import os
import re

cs = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evidence", "s230", "issue586_comments.json")))
parts = []
for c in cs:
    body = c["body"]
    m = re.search(r"```diff\n(.*?)```", body, re.S)
    if not m:
        print(f"comment {c['id']}: NO DIFF BLOCK")
        continue
    diff = m.group(1)
    parts.append(diff)
    print(f"comment {c['id']}: diff chars={len(diff)}")

whole = "".join(parts)
h = hashlib.sha256(whole.encode()).hexdigest()
print("combined sha256:", h[:16], "match 09768a2375a08cff:",
      h.startswith("09768a2375a08cff"))
open("/tmp/s226_transfer.patch", "w").write(whole)
# file list
files = sorted(set(re.findall(r"^diff --git a/(\S+)", whole, re.M)))
print("files in patch:", len(files))
for f in files:
    print(" ", f)
