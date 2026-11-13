#!/usr/bin/env python3
"""S230: apply the 13 clean segments of the S226 TRANSFER patch on the
a4516511 worktree; reconstruct the 3 truncated segments from their posted
lines with explicit truncation markers; commit as the S226 transfer."""
import re
import subprocess

WT = "/tmp/wt_a4516511"
whole = open("/tmp/s226_transfer.patch").read()
idx = [m.start() for m in re.finditer(r"^diff --git ", whole, re.M)]
idx.append(len(whole))
segs = []
for i in range(len(idx) - 1):
    seg = whole[idx[i]:idx[i + 1]]
    m = re.match(r"diff --git a/(\S+)", seg)
    segs.append((m.group(1), seg))


def git(*args, **kw):
    return subprocess.run(["git", *args], cwd=WT, capture_output=True,
                          text=True, **kw)


applied, reconstructed = [], []
for name, seg in segs:
    r = subprocess.run(["git", "apply", "--check", "/dev/stdin"], cwd=WT,
                       input=seg, capture_output=True, text=True)
    if r.returncode == 0:
        r2 = subprocess.run(["git", "apply", "/dev/stdin"], cwd=WT, input=seg,
                            capture_output=True, text=True)
        assert r2.returncode == 0, (name, r2.stderr)
        applied.append(name)
        continue
    # truncated new-file hunk: salvage the posted + lines as file content
    body = []
    in_hunk = False
    for l in seg.splitlines():
        if l.startswith("@@"):
            in_hunk = True
            continue
        if in_hunk and l.startswith("+") and not l.startswith("+++"):
            body.append(l[1:])
        elif in_hunk and l.startswith(" ") and not l.startswith("---"):
            body.append(l[1:])
    out = "\n".join(body) + "\n"
    m = re.search(r"declared (\d+)", "")  # noqa
    # count declared lines from the hunk header
    hm = re.search(r"@@ -\d+,\d+ \+\d+,(\d+) @@", seg)
    declared = int(hm.group(1)) if hm else -1
    actual = len(body)
    if actual < declared:
        out += (f"\n--- S230 RECOVERY NOTE: the patch segment as posted on "
                f"#586 was TRUNCATED by the comment body: hunk declares "
                f"{declared} new lines, {actual} were posted. The recovered "
                f"content above is everything that arrived; the tail was "
                f"not recoverable from the comment. ---\n")
    full = f"{WT}/{name}"
    import os
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w").write(out)
    reconstructed.append((name, declared, actual))

git("add", "-A")
git("commit", "-q", "-m",
    "S226 TRANSFER reconstruction (S230): 13/16 segments applied verbatim "
    "via git apply on base a4516511; 3 segments (T7_CONNECTBOT.md, "
    "s226_post_issue.py, and any truncated hunk) reconstructed from the "
    "posted + lines with explicit truncation markers (hunk-declared vs "
    "posted-line counts recorded)")
print("applied verbatim:", len(applied))
for n in applied:
    print("  ", n)
print("reconstructed:", len(reconstructed))
for n, d, a in reconstructed:
    print(f"   {n} declared={d} posted={a}")
print(git("log", "--oneline", "-1").stdout.strip())
