#!/usr/bin/env python3
"""The W27 F-NEW-639 integration receipt -> #597."""
import json, subprocess, urllib.request
CRED = subprocess.run(["git","credential","fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True,
                      cwd="/home/z/my-project").stdout
TOKEN=[l.split("=",1)[1] for l in CRED.splitlines() if l.startswith("password=")][0]
BODY = """## W27 integration receipt (main-coder push responsibility) — F-NEW-639 LANDED ON MAIN

**main = `f58cdaac`** (`origin/main` verified via ls-remote == `f58cdaac692d75f8b32bb29e3b77ad07fbe2335b`; fast-forward over `ebad37e8`, no history rewrite). The bounded-append law was re-implemented from the issue's law definitions and integrated code-only.

**The law (F-NEW-639):** `StringBuilder/StringBuffer.append(CharSequence|char[], int start, int end)` appends the SLICE `[start, end)`; OpenJDK bounds (`start<0 || end>len || start>end`) defer `StringIndexOutOfBoundsException` (the R24 message shape, `[F-NEW-639]` caller-tagged diagnostics, first-8); a null sequence appends the `"null"` literal with bounds on length 4; the bounded face returns `this` (chaining). Bounds run on the stored UTF-8 BYTE length (the documented R24 byte-length approximation). The generic 2-arg append arm is UNCHANGED.

**Verification matrix (on the integrated tree, pristine = the untouched main binary):**
| Gate | Result |
|---|---|
| new battery `tests/s237_append_bounded_law_test.cpp` (TEST_LAW) | **5/5 PASS** — r1 the EXACT #597 rebuild chain append(acc,0,0).append("7").append(acc,1,1) → "7" (pre-law: "777"), r2 real slice [2,4) + returns-this chaining, r3 start<0/end>len deferred with the buffer UNCHANGED, r4 start>end deferred, r5 null in-bounds → "null" + null out-of-bounds deferred |
| test-all aggregate battery | **33/33 PASS**, RC=0 (the s237 battery included) |
| check-source-parity | **75/75 PARITY-OK** |
| integrated build | RC=0 |
| six-pin gate (gmdice/microtimer/unote/dooz/bouncy/tictactoe ×3, screenshot-sha16, pristine-vs-candidate) | **PASS** — all six pins byte-identical between the untouched main binary and the F-NEW-639 candidate (gmdice `3891679d`, unote `3b8dcb0a`, dooz `a0fae907`, bouncy `60182d11`, ttt `9b4105ca`, microtimer `bbd350b6` — the W26-documented environment face) — **zero pin movement from the law** |

**Notes:** (1) the generic append arm keeps serving the 2-arg faces verbatim — the law only adds the 4-arg bounded arm, so the cold faces cannot move (confirmed by the six-pin). (2) The OpenCalc operator-insert path (the × that never renders; the W28 frontier per the issue) is OUTSIDE this law — untouched, recorded. (3) The candidate on the interactive face now reproduces the issue's endpoint: one tap on "7" = exactly one "7".

**Repository size added to main:** 3 files (dalvik_engine.cpp +62 lines, the new battery 244 lines, Makefile +1) — no evidence artifacts, no binaries."""
req = urllib.request.Request(
    "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/597/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers={"Authorization": f"token {TOKEN}",
             "Accept": "application/vnd.github+json",
             "User-Agent": "w27-integration"},
    method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    print("#597 comment", json.loads(r.read().decode())["id"])
