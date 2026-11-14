#!/usr/bin/env python3
"""#596 deliverables: Phase-1 report on #595, Phase-2 report + the combined
summary on #596. STOP honored — no merge, main untouched."""
import json
import subprocess
import urllib.request
from pathlib import Path

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
                 "User-Agent": "s236-s2361-audit"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        c = json.loads(r.read().decode())
    print(f"#{issue} comment {c['id']}")

P1 = """## S236.1 Phase-1 report (#596 §1) — harness corrected, causality verdict NARROWED, gates re-run on `9745c3e7a09d0194`

**main untouched.** Branch `audit/s236` head **`0121eeb0`** (evidence in `evidence/s236/deep_v2/`, raw stdout+stderr+run-metadata per run). main ancestry note: main moved `ba184db9`→`a5eb0bc7` = **3 script-only commits (+277 lines, zero runtime/rules change)** — the runtime baseline the issue names is intact.

### §1.1 harness — CORRECTED and self-tested
`scripts/s236_deep_verify.py` v2: every run persists stdout, stderr, rc, command, duration, env overrides, timeout state (`*.run.json` + raw `*.stdout.log`/`*.stderr.log`); a no-output run is a **HARNESS FAIL** (never zero-markers); marker counts parse ONLY the retained raw stdout. Self-tests **5/5 PASS** (stdout-only / stderr-only / mixed / non-zero-rc-preserved / silent-raises).

### §1.2 causality — the pair proves LESS than previously claimed, and the real chain is now captured
240-frame pair, independent fresh roots, same binary/APK/env except the probe:
- Probe OFF vs ON faces are **identical** (stdout 2,049 vs 2,041 B, census `games=1` both, same uncaughts) — the draw-storm deference changes **nothing** on the seeding face.
- **R-NEW-345 Thread-start pump = 0 hits** and **ZERO `practice.pgn`/AssetManager reads** in 240 frames → the seed routine **never runs at all**. `games=1` is the `DatabaseHelper.onCreate` default row, NOT a PGN-import product — my earlier "seed thread starvation" framing is hereby corrected: there is no seed thread dispatch to starve.
- Expected seed count from SOURCE: **1,204 `[Event]` entries** in `assets/practice.pgn` (+500 in puzzles.pgn). The **2,380 number is NOT confirmed by the APK** — provenance unverified.
- True first divergence: `Lg4/g;.r` reads XML id **`0xFFFFFFFF`** (`F513` framework-res unmodeled) → deferred `Resources$NotFoundException` → uncaught at `Ljwtc/android/chess/start;.onCreate` (compatibility-continue) + `RecyclerView.onLayout` `IllegalStateException: "Layout state should be one of 100 but it is 10"` (×12 uncaughts total).
- Narrow statement: the pair proves the onDraw storm is not the seeding gate **on this binary**; it does NOT prove thread scheduling is the sole cause — no thread dispatch exists to blame; the gate is upstream (unmodeled XML id at `start.onCreate`).

### §1.3/§1.4 chains — honest
- **Chess**: provider init REAL (`MyPGNProvider.onCreate`, `PRAGMA table_info(games)` rows=8 from the real sqlite file); Practice-list tap reaches `rawQuery rows=1` (the 1 default row); board-load (`loadPGNHead`/FEN/64-cell verification) **PENDING** — the row-bounds hit-test work was superseded by the §1.2 finding (the app's boot faces the `0xFFFFFFFF` XML uncaughts; the board screen requires the next-law wave).
- **OpenSudoku**: `SQLiteOpenHelper.onOpen` runs REAL DEX; decor/fragment boot alive; but the query→cursor→adapter→rows→render chain is **NOT reached** in 40 frames (no sudoku DB file created). First divergences: `f141-null-recv` NPE (`Instant.toEpochMilli` on null) + `R350` kotlin-reflect CNFE. Classification **PARTIAL/PENDING**, raw traces in `deep_v2/`.

### §1.5 gates on the CURRENT binary `9745c3e7a09d0194`
- Battery **12/12 ×3** fresh runs ✓
- Source parity **75 core sources** manifest-parity ✓ (`PARITY-OK`)
- test-all: **GATES_RC=0** ✓ (full battery)
- Six-pin fresh (GATE json in evidence): gmdice **3891679d identical=True**, microtimer **b39665f6** (=golden), unote **HOLD** (3b8dcb0a), dooz **HOLD** (a0fae907), bouncy **BREAK vs 98abca38 — the KNOWN S235-1 boundary drift (its drifted face 60182d11 reproduced exactly)**, ttt **d005914b ×3** (=the recorded boundary face). **No new movement vs the S235-1 record.**
- 10 additional apps: not run this pass (time-bounded) — PENDING, listed honestly.

### §1.6 artifacts
Branch `audit/s236` @ `0121eeb0`; APKs: chess `3245b9ec35f6c1df`, opensudoku `ac4c6c8d0bc9058c`; binary `9745c3e7a09d0194`; raw logs + `*.run.json` in `evidence/s236/deep_v2/` on the branch. Rollback: `git checkout main && git branch -D audit/s236` (main never touched). **STOP honored — no merge.**"""

P2 = """## M-16 Phase-2 report (#596 §2) — audit-only on `audit/m16-litehtml`, zero runtime change

Branch **`audit/m16-litehtml`** from the immutable `ba184db9` (NOT from the S236 candidate), head pushed this pass. Full record: `docs/M16_AUDIT_596_PHASE2.md` on the branch.

### §2.1 architecture (verified from source — the engine EXISTS)
`src/webview/`: webview_engine.cpp **338,897 B**, html_dom.cpp 32,555 B, canvas2d.cpp 23,714 B + headers; QuickJS 2024-01-13 wired at L220/L2050/L2179; **WV_DIAG + webview_resource_trace.json instrumentation already present** (L150/L180-194). All three TUs in core_sources.manifest. No "there is no WebView engine" claim possible.

### §2.2 the CSS-failing 2048 APK — NOT IDENTIFIED (BLOCKED)
- `org.secuso.privacyfriendly2048_100.apk` (sha256 `02c799d3…`): S195 record re-read — `frame_analysis: NO_ROOT ×2`, `NameNotFoundException ×1`, VIEW primary, **zero HTML assets**. Divergence = content root absent **before** Measure/Layout. **Not a CSS failure** (re-verified today).
- `org.andstatus.game2048_47.apk` (sha256 `2d670762…`): **korge-based** (`korlibs.korge.ViewsCompleter`), **0 html/css/js assets**. Not a WebView/CSS failure.
- `games/2048` + `s80/s83 g2048`: repo-native custom-View.
- The coder's reported WebView/CSS 2048 is **not among the artifacts** — BLOCKED until the exact APK/sha256 is provided. No CSS diagnosis is honest without it.

### §2.3 stage separation
The WV_DIAG resource-trace format is preserved; the per-stage CSS diagnostics (parse/cascade/layout/paint first-divergence) are **designed, not implemented** — PENDING, gated on §2.2.

### §2.4 litehtml — upstream verified AND measured (2026-11-14)
HEAD **`ebb9d32b28cb`**; **BSD-3-Clause** + bundled gumbo (Apache-2.0, vendored `src/gumbo`); **66,137 LOC measured** across src+include (src 2.9 MB, include 476 KB) — the M-16 decision's "~30k LOC" is **outdated**; CMake ≥3.20; **CSS Grid PARTIAL**; core build needs **no external libraries** (Cairo/Pango/GTK/curl/fontconfig optional, OFF default). It is a layout engine only — QuickJS + Canvas2D stay (S131 REUSE-FIRST law).

### §2.5 prototype — PENDING (audit-only this pass), contract written
The full integration contract is on the branch: pin `ebb9d32b28cb` vendored under `third_party/litehtml`; CMake option **`MINIANDROID_USE_LITEHTML` OFF by default**; `document_container` adapter on the EXISTING font/image/software-render/clipping primitives; **litehtml's DOM is render-only** — `html_dom` stays the single JS-facing DOM (owner), invalidation wired at its mutation points (no unsynchronized DOM pair); A/B = the option; gate = the 124-stage battery.

### §2.6 host-browser optional backend
Linux **WebKitGTK ABSENT** in this sandbox (`pkg-config webkit2gtk-4.1` fails) → feasibility eval PENDING on a host with it installed; **WebView2 BLOCKED** (no Windows here). Runtime stays host-browser-free by law.

### §2.7/§2.8 matrix + regressions
Windows x64 build **BLOCKED** (no Windows environment). Linux prototype build/measure + the 12-item matrix **PENDING** with §2.5. **Regression exposure of this branch: ZERO** (audit docs only — S100/S112/S114/S133 and the 124-stage battery untouched by construction)."""

COMB = """## Combined summary (#596) — both phases done, STOP honored

- **What is implemented/tested**: Phase 1 — corrected harness v2 (5/5 self-tests), the 240-frame causality pair with RAW logs and a NARROWED verdict (the seed routine never runs; `games=1` is the onCreate default row; expected seed = 1,204 from source; the true first divergence = the `0xFFFFFFFF` XML id at `start.onCreate`), battery 12/12 ×3 + parity 75 + test-all RC=0 + the six-pin fresh set on `9745c3e7a09d0194` with **no new movement** (gmdice/microtimer/unote/dooz HOLD; bouncy BREAK = the known S235-1 drift; ttt d005914b = the known face). Phase 2 — the architecture/2048/litehtml/host-backend audit on `audit/m16-litehtml` with measured numbers (66,137 LOC, BSD-3, Grid partial) and the written integration contract.
- **PARTIAL/BLOCKED/PENDING**: Chess board-load + 64-cell chain (PENDING — needs the `0xFFFFFFFF` framework-res law wave), OpenSudoku rows→render (PARTIAL), the coder's CSS-2048 APK (BLOCKED — not in artifacts), CSS stage diagnostics (PENDING), litehtml prototype code (PENDING, contract ready), Windows build + WebView2 (BLOCKED), WebKitGTK eval (PENDING — absent here), 10-additional-apps run (PENDING, time-bounded).
- **Branches**: `audit/s236` @ `0121eeb0` (Phase 1), `audit/m16-litehtml` @ the audit-record commit (Phase 2) — created from `ba184db9`, never from the S236 candidate.
- **main proof**: `a5eb0bc7bfa9fe12cf65251e8504f4d5901f5f92` at audit time = `ba184db9` + 3 script-only commits (+277 lines, no runtime/rules change) — **untouched by me**.
- **Hashes**: binary `9745c3e7a09d0194`; APKs chess `3245b9ec35f6c1df`, opensudoku `ac4c6c8d0bc9058c`, secuso-2048 `02c799d3…`, andstatus-2048 `2d670762…`; litehtml `ebb9d32b28cb`.
- **Achievements/regressions**: none changed; no previously passing face moved.
- **For an approved merge**: (a) the framework-res `0xFFFFFFFF` XML-id law + the RecyclerView layout-state divergence fix, then re-verify the Chess board-load and OpenSudoku rows→render chains with the corrected harness; (b) the litehtml prototype per the §2.5 contract with the 124-stage battery green + Windows build; (c) the six-pin + battery re-run on the final binary. **No merge performed — STOP after reports.**"""

post(595, P1)
post(596, P2)
post(596, COMB)
