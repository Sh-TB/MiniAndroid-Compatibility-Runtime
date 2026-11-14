#!/usr/bin/env python3
"""#596 paths 1+2 receipts: post the two reports on #595/#596."""
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
                 "User-Agent": "s596-paths-receipt"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        c = json.loads(r.read().decode())
    print(f"#{issue} comment {c['id']}")

P1 = """## Path-1 receipt (#596): framework-res/0xFFFFFFFF + Instant laws implemented, Chess/OpenSudoku re-runs recorded

**main untouched** (a5eb0bc7). Branch `audit/s236` head **`99fe3ac5`** — two laws implemented, rebuilt, battery re-proven, both re-runs captured with raw logs.

### The laws (F596-P1)
1. **371-GETXML-NOTFOUND scoped per the F513 AOSP contract**: the NotFound throw now fires ONLY for genuinely-missing APP-table ids (0x7f…). Non-app leak shapes (0xFF… / 0x01… theme-attr -1 leaks — the W9 recorded family: throwing on these killed chess + opencalc onCreate) serve a REAL K-35 XmlPullParser over an empty document — the androidx consumer's parse loop ends at END_DOCUMENT and yields the null/empty drawable default (the same observable family as the F513 zero-state TypedValue). Recorded rows, never counted as content.
2. **java.time.Instant modeled** (`now`/`ofEpochMilli`/`toEpochMilli`) on the F516-L2 LocalTime shadow shape — OpenJDK law: now() NEVER returns null; wall-clock = the EXP-043 System.currentTimeMillis law. The opensudoku f141 NPE on `Instant.toEpochMilli` is gone at the source.

### Re-run results
**Chess** (fresh roots, real APK `3245b9ec35f6c1df`):
- boot uncaughts **12 → 0**; `371-GETXML-NOTFOUND` **12 → 0** (the F596-P1 empty-parser arm fired ×11)
- the RecyclerView `IllegalStateException: "Layout state should be one of 100 but it is 10"` storm is **GONE** (the CardView drawable load now completes cleanly)
- the menu renders (353 C013-ONDRAW draws); the menu tree is REAL: "Practice"/"Puzzles"/"WiFi board"/"Game database"… TextViews recorded by EXP092
- **the board screen remains PENDING with a NEW first divergence**: the menu rows render **zero-height** (`Practice` TextView `pos=(312,809) size=(456x0)`) — no tap target exists, so the Practice screen never opens. This is the next law wave (menu item layout height), documented with the full trace.

**OpenSudoku** (`ac4c6c8d0bc9058c`):
- `Instant.now` fires REAL (F596-P1 `oid=1532 epoch_milli=1794682221365`), the Instant NPE is gone
- **the rows→render chain remains PENDING with a NEW first divergence**: `CREATE TABLE puzzles` receives a COMPOSED SQL string with duplicate `RATING_LEVEL` that matches **NO dex constant and NO engine source** (sqlite3 rejects it; the app's real INSERTs then fail with "no such table"; the `Cursor.getColumnIndex` null-cursor NPE at `Ltf;.onOpen pc=135` follows from it). The composed-SQL face is the next frontier; the full SQL trace line + the raw stderr are on the branch.

### Gates after the fixes (zero regression)
battery **32/32** + test-all RC=0 + rebuild RC=0 on `audit/s236` @ `99fe3ac5`. Evidence: `evidence/s236/deep_v2/{chessflow2,chessflow3,sudokufix_80f,path1_rerun_results.json}` + the screenshots. **STOP honored — main untouched, no merge.**"""

P2 = """## Path-2 receipt (#596): the litehtml prototype is REAL and rendered — behind `MINIANDROID_USE_LITEHTML`, OFF by default

**main untouched** (a5eb0bc7). Branch `audit/m16-litehtml` head **`9ff960c4`** (based on the immutable `ba184db9`, never on the S236 candidate).

### What is implemented and TESTED
- Vendored **pinned litehtml `ebb9d32b28cb`** (BSD-3 + bundled gumbo Apache-2.0) under `third_party/litehtml`.
- The full `document_container` adapter (`src/webview/litehtml_adapter.cpp`, PARITY-OPTIONAL-gated) on the EXISTING engine primitives: REAL font shaping via `fonts::TextShaper` (FreeType/HarfBuzz), painting into the existing `renderer::FrameBuffer`, clipping stack, borders/solid fills/list markers, text transforms, media-query viewport, and the **`import_css` hook for external stylesheets (http:// + file://)**. Image decode + gradients = recorded placeholders (honest PENDING). litehtml's DOM is RENDER-ONLY — html_dom stays the single JS-facing owner (no unsynchronized DOM pair).
- The probe (`tests/litehtml_probe`): **REAL RUN PROVEN** — local HTML + external HTTP stylesheet (`http://127.0.0.1:8901/style.css` status=200, 62 bytes) through BOTH the user-stylesheet path AND the `<link>` import_css path; fonts 16px/28px-bold/15px(+bold) created; **nonwhite=384000/384000, pxhash `6333e77d5a4c41b4`** vs the no-CSS control **nonwhite=1491, pxhash `caa8376b0cbd9140`** — the CSS cascade provably changes the pixel output. The render was verified visually: h1 `#1a4480` 28px bold, external `p{color:#204020}` + `<b>`, `.box{background:#ffd080;border:2px solid #804000}`, `ul{color:#4040a0}` with bullets, table borders — all correct.
- **The OFF-default law holds**: `build/miniandroid` on this branch builds with NO litehtml define (OFFBUILD_RC=0); the OFF-default probe binary answers the OFF-law stub (rc=9). The ON path adds ONLY the separate probe binary — zero code reaches the portable runtime without the explicit flag; QuickJS + Canvas2D + html_dom untouched.

### Regression proof (path-2 acceptance)
- OFF-default engine build: RC=0; **parity 75/75 core sources** (new documented `PARITY-OPTIONAL` class for the flag-gated adapter); **test-all battery 31/31 PASS** (the 31-row ba184db9 baseline battery; audit/s236's 32/32 covers the S236 row on its own branch).
- Windows x64: still BLOCKED (no Windows in this sandbox). The remaining §2.7 matrix items (Grid/flex-heavy fixtures, image decode, the webview_engine routing hook) = PENDING with the contract already in the branch (`docs/M16_AUDIT_596_PHASE2.md`).

### Receipts
Branch `audit/m16-litehtml` @ `9ff960c4`; probe PPM + PNG in `download/`; the local httpd fixtures recorded in the run logs. **STOP honored — main untouched, no merge.**"""

post(595, P1)
post(596, P2)
