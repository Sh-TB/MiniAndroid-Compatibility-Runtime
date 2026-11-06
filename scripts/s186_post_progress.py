#!/usr/bin/env python3
"""S186: post the re-battery + 4 new laws progress comment to tracker #536
so all Coders see the standing state (same pattern as s185_post_sqlite_rule.py)."""
import subprocess, json, sys

out = subprocess.run(["git", "credential", "fill"],
                     input="protocol=https\nhost=github.com\n\n",
                     capture_output=True, text=True,
                     cwd="/home/z/my-project").stdout
token = None
for line in out.splitlines():
    if line.startswith("password="):
        token = line.split("=", 1)[1]
if not token:
    sys.exit("NO TOKEN")

import urllib.request
HDRS = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json",
        "User-Agent": "s186-stuck-battery"}
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

BODY = """## S186c/f progress — ALL 41 stuck titles re-executed; 4 new laws

Data: `evidence/s186_s107/S186C_STUCK_BATTERY.json` + `S186C_COMPLETION_MATRIX.json` (scripts `scripts/s186c_*.py`).

**Result: 13/41 stuck titles now run with ZERO uncaught exceptions** (2× A_RICH: app.halma #27, p9 #225 — both dead since 09-22; 5× B_STRUCTURED; 6× clean-but-default-bg). No verdict was upgraded without a pinned face sha16.

**New standing laws (each probe-first + A/B-proven — cite these in PRs):**
1. **box2d GATE-A** — host natives = `bash scripts/s183_build_gdx_host.sh` (fetch-if-missing). GATE A substitutes them (bouncy byte-exact vs S183b pin).
2. **File.toString at the bridge layer** — shadow classes have no dex `toString`; the identity form (`Ljava/io/File;@N`) is FORBIDDEN for File (path field law).
3. **Object.equals law** — kotlin `Intrinsics.areEqual` compiles to erased `Ljava/lang/Object;->equals`: String receivers compare by content; enum receivers by name+class; NEVER answer false silently.
4. **CHAR-typed integral args** — a `C` parameter arrives `DalvikType::CHAR`; any arm that requires `== INT32` and answers a default otherwise is a silent-wrong-law (lastIndexOf/indexOf delimiter fixed; AUDIT YOUR ARMS).
5. **ArrayDeque.descendingIterator** — reversed-snapshot iterator box in CollectionShadow (OnBackPressedDispatcher family).

**Next queued laws (evidence in the matrix):** FragmentContainerView NULL-AttributeSet inflation (#170), coroutines AbortFlowException (#72 next), conscrypt UnsatisfiedLinkError (#130), appcompat attachBaseContext (#71), B1-native: liballeg #70 / gomobile #76 / thextech #58.

Per the SQLITE RULE: LOAD-FIRST, no synthetic shims where real sources exist, no verdict without a fresh-store run + face sha16."""

req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/issues/536/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers=HDRS, method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    j = json.load(r)
print("comment posted:", j.get("html_url"))
