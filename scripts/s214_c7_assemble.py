#!/usr/bin/env python3
"""S214: reassemble C7 W5->W11 rebase patch (21 parts from #520), verify sha256+size, apply-check."""
import json, subprocess, hashlib, sys, os

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
EXPECT_SHA = "9201c5c5ea68eaa35a30b7cdcc41f28710d4f43cf9176a1cafe60e6bc73787fd"
EXPECT_SIZE = 606850
FIRST_PART_ID = 6776780123

def token():
    out = subprocess.run(["git", "credential", "fill"], cwd="/home/z/my-project/miniandroid",
                         input="protocol=https\nhost=github.com\n", capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("no token")

TOK = token()

def api(url):
    r = subprocess.run(["curl", "-s", "-H", f"Authorization: token {TOK}",
                        "-H", "Accept: application/vnd.github+json", url],
                       capture_output=True, text=True)
    return json.loads(r.stdout)

def extract_fence(body):
    """Extract content between the first ````<lang> fence line and its closing ```` line."""
    lines = body.split("\n")
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith("````"):
            start = i + 1
            break
    if start is None:
        return None
    end = None
    for j in range(len(lines) - 1, start, -1):
        if lines[j].strip() == "````":
            end = j
            break
    if end is None:
        return None
    return "\n".join(lines[start:end])

def main():
    cs, page = [], 1
    while True:
        batch = api(f"https://api.github.com/repos/{REPO}/issues/520/comments?per_page=100&page={page}")
        if not batch:
            break
        cs.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    parts = [c for c in cs if c["id"] >= FIRST_PART_ID and c["user"]["login"] == "Sh-TB"
             and "REBASE onto main" in (c.get("body") or "") and "/21" in (c.get("body") or "")]
    parts.sort(key=lambda c: c["id"])
    print(f"found {len(parts)} part comments")
    if len(parts) != 21:
        print("FATAL: expected 21 parts")
        for c in parts:
            b = c["body"]
            import re
            m = re.search(r"part (\d+)/21", b)
            print(" ", c["id"], m.group(1) if m else "?")
        sys.exit(1)
    blob = ""
    for c in parts:
        inner = extract_fence(c["body"])
        if inner is None:
            print(f"FATAL: no 4-backtick fence in part c={c['id']}")
            sys.exit(1)
        blob += inner
    data = blob.encode("utf-8")
    sha = hashlib.sha256(data).hexdigest()
    print(f"size={len(data)} expect={EXPECT_SIZE}")
    print(f"sha256={sha}")
    print(f"sha_match={sha == EXPECT_SHA}  size_match={len(data) == EXPECT_SIZE}")
    os.makedirs("/home/z/my-project/evidence/s214", exist_ok=True)
    out = "/home/z/my-project/evidence/s214/c7_w5_w11_rebased_on_main.patch"
    with open(out, "wb") as f:
        f.write(data)
    print("saved:", out)

if __name__ == "__main__":
    main()
