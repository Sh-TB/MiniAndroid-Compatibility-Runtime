#!/usr/bin/env python3
"""The S236 integration decision report -> #595 (cross-noted on #596)."""
import json
import subprocess
import urllib.request

CRED = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True,
                      cwd="/home/z/my-project").stdout
TOKEN = [l.split("=", 1)[1] for l in CRED.splitlines()
         if l.startswith("password=")][0]


def post(issue, body):
    req = urllib.request.Request(
        f"https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{issue}/comments",
        data=json.dumps({"body": body}).encode(),
        headers={"Authorization": f"token {TOKEN}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "s236-integration-decision"},
        method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        c = json.loads(r.read().decode())
    print(f"#{issue} comment {c['id']}")


BODY = """## S236 integration decision report (main-coder push responsibility executed)

**PUSHED — main is now `bef9e2ac`** (`origin/main == main == bef9e2ac54eead887129fb3a169901a536c5282a`, fast-forward only, no history rewrite). Three clean commits over the previous main `2e714a6a`:

1. `9027223a` — **S236 pre-merge port laws + battery, code-only** (F-NEW-655/656c/657/658/658b/658c/659/660 + the env-gated `MINIANDROID_S236_PROBE_DEFER_DRAW` diagnostic, zero default cost + `tests/s236_port_laws_test.cpp` registered in TEST_LAW). NO evidence artifacts integrated — raw evidence stays on `audit/s236` (historical).
2. `0d9b537a` — **F596-P1** (371-GETXML scoped per the F513 AOSP contract + java.time.Instant) **with 4 executable contract rows r11-r14** added to the battery per the review demand.
3. `bef9e2ac` — `scripts/s236_sixpin_gate.py` (the reusable pristine-vs-candidate gate runner used for this decision).

### Verification matrix (all on the INTEGRATED tree, pristine-main-vs-candidate)
| Gate | Result |
|---|---|
| s236 battery (12 law rows + 4 contract rows) | **16/16 PASS** |
| test-all aggregate battery | **32/32 PASS**, RC=0 |
| check-source-parity | **75/75 PARITY-OK** |
| integrated build | RC=0 |
| six-pin gate (gmdice/microtimer/unote/dooz/bouncy/tictactoe ×3, screenshot-sha16) | **PASS — all six byte-identical between the untouched main binary and the integrated candidate**; gmdice `3891679d`/unote `3b8dcb0a`/dooz `a0fae907`/bouncy `60182d11` match the recorded goldens; microtimer and tictactoe faces moved IDENTICALLY on BOTH binaries (`bbd350b6`/`9b4105ca`) — environment drift, zero S236-induced move |

### Contract verification (the review demands, now executable)
- **Instant identity**: two `now()` calls → distinct object ids (r11: oid 24≠25), each answering its own real epoch-milli; same-millisecond values are EQUAL (the correct OpenJDK wall-clock face — the row initially over-asserted distinct VALUES, fixed before push).
- **Negative epoch-milli**: `ofEpochMilli(-1234567890123)` → verbatim round-trip (r12), no clamp, no throw.
- **getXml valid app ids**: a real 0x7f XML id parses to a real parser (existing rows); a genuinely-missing 0x7f id → the deferred NotFoundException (r14: `obj#0`, no fabricated parser) — **legitimate resource errors stay visible**.
- **getXml leaked/invalid ids**: 0xFFFFFFFF → a real XmlPullParser over the empty document (r13: `obj#27`, no throw) — the W9/F513 recorded family.

### Repository size added
6 files changed, **+1280/−18 lines**; new-file blobs ≈ 35KB (the battery + the gate script) — no evidence files, no screenshots, no binaries, no build dirs entered main.

### M-16 litehtml — kept EXPERIMENTAL (not merged)
`audit/m16-litehtml` head `951ea2bf` (the review round found and FIXED two real defects: relative `@import` now resolves against the importing stylesheet's URL; the probe sets the document base). Probe matrix this round: @import chain fetched (style3.css 38B + link style.css 62B, pxhash `74ab6f94e152d9b4`), image → honest placeholder + deferred record (`fedb5f694474f1ed`), fonts 16/18/28-bold. It is a separate probe binary behind `MINIANDROID_USE_LITEHTML=OFF` (default) — NOT a WebView integration: no engine HTTP client (HTTPS), no WebView lifecycle wiring, DOM stays html_dom-owned. Default runtime carries ZERO litehtml code (parity + the OFF build prove it).

### Remaining blockers (honest, unchanged by this integration)
- **Chess**: zero-height Practice menu rows (`EXP092: Practice pos=(312,809) size=(456x0)`) — no tap target; PGN/board stage unreached. NOT complete.
- **OpenSudoku**: the composed `CREATE TABLE puzzles` SQL with duplicate `RATING_LEVEL` matching no dex constant and no engine source; the onOpen null-cursor NPE follows. NOT complete.
- **M-16**: HTTPS via the engine http_client, WebView lifecycle wiring, image decode, gradients — PENDING on the experimental branch."""

post(595, BODY)
post(596, "**S236 integration executed per the path-1 receipt: main `bef9e2ac` carries F596-P1 (371-GETXML scope + java.time.Instant) WITH 4 executable contract rows (r11-r14: identity/value, negative epoch, leak-shape parser, app-missing throw) — 16/16 + test-all 32/32 + parity 75/75 + six-pin pristine==candidate byte-exact ×3. M-16 stays experimental at `951ea2bf` with the @import/base-URL defects fixed and the probe matrix green. Full matrix on #595.**")
