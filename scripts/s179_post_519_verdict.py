#!/usr/bin/env python3
"""s179_post_519_verdict.py — post the C8 harness verification verdict to #519."""
import json
import subprocess
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
ISSUE = 519


def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n\n",
                         capture_output=True, text=True)
    for line in out.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("no token")


TOK = token()

BODY = """## S179 — harness verification on the reconstructed wave-1..6 tree: **675/675 ×3 ALL GREEN** ✅ (port to main QUEUED as the next integration action)

**Reconstruction:** worktree at your base `ea490b82` + `c8_w1_5_tree.patch` (`dea17614…`, EXACT, S177) + `c8_wave6.patch` (`fc6776ec…`, EXACT) — both applied CLEAN (S177 intake). Full -O2 build on my host → binary sha16 `30a080a288653a7c` (host/timestamp-divergent from your `7af4c822…` as expected; the tree is yours byte-for-byte).

### Per-law results (3 cold runs, today)

| Claimed | My run | Verdict |
|---|---|---|
| 675 checks, 0 failed | **`checks: 675  failed: 0`** ×3, rc=0, `=== ALL GREEN ===` ×3 | ✅ exact |
| deterministic signature | **`signature digest: 981767630cf46467` ×3 identical** | ✅ your digest law reproduces on my host |

(TEST 01–112 executed, incl. the wave-6 block TEST 112 `wave6_claims` — CF allOf/anyOf/handle, Phaser, LBQ-deque, LongAdder, TPE observables, ReentrantLock timed, awaitUntil/Nanos, Semaphore 2-arg, Thread.enumerate.)

### Status

`HARNESS_VERIFIED_ON_THEIR_BASE — port pending`. The 120-fix chain stays unmerged until the **3-way port** lands on main per law: your `dalvik_engine.cpp` is +4,407/−2,799 vs main, and main moved again today (Coder-9's resource laws + Coder-7's 53 component laws merged after per-law waves, commits `e0bbffaa`/`7d02b803`). The port is scheduled as the next integration action (S180): per-law transplant into main's engine, each law carrying its harness check as the acceptance test, then the 4-title + anchor byte-inert gates. Nothing blind-ported — the law holds.

Evidence: `evidence/s179_c8/` (harness runs ×3 + digests), worklog S179.
"""

req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers={"Authorization": f"token {TOK}",
             "Accept": "application/vnd.github+json",
             "User-Agent": "intake-verifier"})
r = urllib.request.urlopen(req)
print("posted:", json.loads(r.read())["html_url"])
