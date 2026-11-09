#!/usr/bin/env python3
"""S204 — reassemble Coder-3's S202-W2 patch (2 comment parts), verify sha16
against their claim (15d0adf8cfb63e91), and apply --check on two bases:
(a) pristine 1b4d0293 (their claimed base)  (b) current HEAD 63b2edf3."""
import json, re, subprocess, sys
from pathlib import Path

EV = Path('/home/z/my-project/evidence/s204')
EV.mkdir(parents=True, exist_ok=True)
REPO = Path('/home/z/my-project/miniandroid')

p1 = (Path('/home/z/my-project/evidence/s203/issue_557_c6736942949.md')).read_text()
p2 = (Path('/home/z/my-project/evidence/s203/issue_557_c6736945005.md')).read_text()


def extract(body):
    # take everything from the first ```diff fence to the closing fence
    m = re.search(r'```diff\n(.*)\n?```', body, re.S)
    return m.group(1) if m else ''


d1, d2 = extract(p1), extract(p2)
full = d1 + ("\n" if not d1.endswith("\n") else "") + d2
(EV / 's202w2_ftwrap_mint.diff').write_text(full)
print(f"reassembled bytes={len(full)} sha16={__import__('hashlib').sha256(full.encode()).hexdigest()[:16]}  claim=15d0adf8cfb63e91")


def git(*a, cwd=REPO):
    return subprocess.run(['git'] + list(a), cwd=cwd, capture_output=True, text=True)


# (a) pristine base 1b4d0293 via git worktree of that commit
r = git('worktree', 'add', '--detach', str(EV / 'wt_1b4d0293'), '1b4d0293')
if r.returncode != 0 and 'already exists' not in r.stderr:
    print('worktree add failed:', r.stderr[:200]); sys.exit(1)
W1 = EV / 'wt_1b4d0293'
c1 = git('apply', '--check', str(EV / 's202w2_ftwrap_mint.diff'), cwd=W1)
print(f"apply --check on pristine 1b4d0293: rc={c1.returncode} {c1.stderr.strip()[:300]}")

# (b) current HEAD 63b2edf3 worktree
W2 = EV / 'wt_head'
r2 = git('worktree', 'add', '--detach', str(W2), 'HEAD')
if r2.returncode != 0 and 'already exists' not in r2.stderr:
    print('head worktree failed:', r2.stderr[:200])
c2 = git('apply', '--check', str(EV / 's202w2_ftwrap_mint.diff'), cwd=W2)
print(f"apply --check on HEAD {git('rev-parse','--short','HEAD').stdout.strip()}: rc={c2.returncode} {c2.stderr.strip()[:400]}")

# stats
st = git('apply', '--stat', str(EV / 's202w2_ftwrap_mint.diff'), cwd=W1)
print(st.stdout[-800:])
