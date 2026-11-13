#!/usr/bin/env python3
"""S231: post the #582 GP-census route matrix — the directive's "Immediate
next deliverable" (comment 6821150791) that S228 promised on #582 but never
posted. Backed by the executed cold-run batch evidence/s228_census/
s231_cold_runs_batch.json (binary 06f98d2a9c21ea92 == release RC, byte-exact
rebuild)."""
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

BODY = """# S231 — the GP-census route matrix, DELIVERED (the "Immediate next deliverable" this directive asked for, which S228 recorded as posted but never actually posted)

**Directive:** comment 6821150791 §3/§4 + "Immediate next deliverable: a route matrix for the smallest open-source native APKs already in the corpus, with each row marked IMPLEMENTED / TESTED / OBSERVED / PARTIAL / BLOCKED / PENDING, exact first-divergence stage, and the next discriminating experiment."

**Honest provenance first:** the S228 wave wrote `scripts/s228_cold_runs.py` and a #570 audit comment (6854127754) claimed the route matrix was "posted on #582" — **it never was** (the last #582 comment before this one is the directive itself). The S231 wave executed the batch for real: **3 cold runs × 8 cohort APKs on ONE frozen binary**, fresh data-root per run, per-run first-divergence capture. Raw runs stay untracked in `.cache/s228_cold_runs/` (S213/S214 run-output law); the compact record is `evidence/s228_census/s231_cold_runs_batch.json`.

**Frozen binary:** `06f98d2a9c21ea92` (sha16) — the release-candidate binary, rebuilt byte-identically from a clean tree this session (a reproducible-build proof in itself). Main HEAD at batch time: `9309c9bd`.

## 1. Route matrix (mandate §3 — route diversity, not 10 copies of libGDX)

| route | APK (sha16) | 3-cold-run status | face (sha16) | first-divergence stage + signature | next discriminating experiment |
|---|---|---|---|---|---|
| PURE-DEX control | `de.duenndns.gmdice_8` | **TESTED** — SUCCESS ×3, deterministic, 0 uncaught | `d540433a06dc6431` | none — tap @6 (roll button y≈1836) → RNG advance → app-owned roll-6 face == the standing S208 record | extend the input cohort to the full roll loop (6→5→3 chain, S208 already demonstrated) |
| libGDX (physics) | `com.dozingcatsoftware.bouncy_43` | **TESTED** — SUCCESS ×3, deterministic | `98abca389fb01380` | none — face == the standing golden pin | input-driven plinko drop as the state-transition row |
| JNI-libs + Compose | `io.github.yamin8000.dooz_23` | **PARTIAL** — boot + tap→NewGame transition real (face `eccabf418a7cce52` recurring), but **face NOT stable ×3**: 3 distinct faces, 1/3 runs FATAL | 3 faces; FATAL row: `Llo;.K` KillApplicationHandler | **stage I/J** — the kotlinx corrupted-Segment decode family (S210/S211): `AbortFlowException` → deferred unwind → ART process-death law fires intermittently; post-NavGame screen still renders no board pixels (S223 frontier) | the S211 probe: `.d 0x6b/0x292` + `.e` return-site tuple to locate the re-entrancy scan-claim divergence; then the W21 17/17 integration |
| libGDX (view game) | `com.emmanuelmess.tictactoe_3` | **PARTIAL** — no-tap run: SUCCESS, face `7354c1b231cd581d` == the standing pin (re-proven on the RC binary this wave); WITH tap @ center cell: the presented frame collapses to the uniform (48,48,48) face `b5a7a35d…` (recorded separately as the tap probe) | tap-row face `b5a7a35d5fe0564b` | **stage I** (input→present): the click dispatches into the libGDX surface (`F117-TAP` → `UI-EVENT CLICK DISPATCHED`) but the NEXT presented frame is uniform background — the S203 named frontier (wedge art draws via scene2d SpriteBatch `DrawElements`; zero glDrawElements in the whole run) | ShortBuffer.put([SII) index fill + DrawElements dispatch probe (the two named suspects from S203); then L-05/L-06 tap reachability |
| SDL2 | `com.traffar.gomoku_4` | **BLOCKED** — FAILURE ×3, deterministic | `b5a7a35d5fe0564b` (uniform gray) | **stage C** (loader lifecycle): `System.loadLibrary` **REC-MISS** inside `Lorg/libsdl/app/SDLActivity;.<clinit>` — the SDL2 libs are ELFCLASS32 (armeabi-v7a/x86 only) and never reach a native main | a loadLibrary receiver law: APK-native-lib path resolution + an explicit structured ABI row for ELFCLASS32 (ABI_UNSUPPORTED contract, mandate §4-2/P0) instead of the silent miss |
| SDL3 | `org.kirkezz.rttt_3` | **BLOCKED** — FAILURE ×3, deterministic | `b5a7a35d5fe0564b` (uniform gray) | **stage C** — same shape as gomoku (SDLActivity init chain misses, libs never load) | same loadLibrary law (SDL3 variant), then RmlUi surface lifecycle |
| JNI-AI (libserver) + GL (libktx) | `de.saschahlusiak.freebloks_184` | **BLOCKED** — FAILURE ×3, deterministic | `b5a7a35d5fe0564b` (uniform gray) | **stage D/E** — DEX runs (`LifecycleRegistry` chain) but `kotlin.reflect.jvm.internal.ReflectionFactoryImpl` ClassNotFound deferred + the presented window stays default-background; `libserver`/`libktx` load not proven reached | kotlin-reflect class resolution law; then a libserver JNI load probe (the smallest-DYNAMIC-lib probe S228 left PENDING) |
| libGDX extra | `stack.tower3d_1` | **BLOCKED** — FAILURE ×3, deterministic | `11a38a5aeeff45a6` | **stage I/J** — UNCAUGHT → APP BOUNDARY unwind (process-death law), distinct from the gray face | crash.log chain decode (same discipline as the dooz family) |

**The shared finding this matrix exists to expose:** FOUR different native routes (SDL2, SDL3, JNI-AI, libGDX-with-input) collapse to the **same uniform (48,48,48) presented frame** while their upstream stages differ (loader miss / DEX-runs-but-no-native / GL-loop-runs-but-tap). That is the mandate's stage **H (composition/presentation)** contract exactly — "#583's Mindustry DEFAULT_BACKGROUND_ONLY" family — and stage **C (loader)** is the earliest shared divergence for the SDL family. Per the mandate: fix the earliest observed shared divergence first, smallest generic contract (the loadLibrary receiver law + structured ABI rows), then rerun every affected route.

## 2. Reconciliation (mandate: "First reconcile #557, #559, #570, #521, #519/#533, #520, #583")

- **#557** (A24/S188 tictactoe): the L-08 verdict stands — texture-upload noise fixed (S202/S203 laws), wedge art + tap reachability remain the named frontier; this matrix's ttt tap-row is the live reproduction of that frontier on the RC binary.
- **#559** (S188 route map): route labels are discovery evidence only — exactly why this matrix adds per-route cold-run execution truth instead of more labels.
- **#570** (external tool audit): S228's verdicts stand (F-JNI-1 ALREADY-FIXED in `d5c14b83`; the 43-lib bridge census column stale at 181 slots vs main's 240). The **library-side metadata (43 libs × ABI/DT_NEEDED/route)** is retained as route-discovery evidence and feeds this matrix's stage-B rows; the **PENDING smallest-dynamic-lib load probe** (`libandroidx.graphics.path.so`, 10,760 B) is folded into the freebloks/next row as the loadLibrary-law fixture.
- **#519/#533** (coder-8 concurrency): no new native-APK route evidence added there since the last sweep; the mandate's D/J stage contracts (thread attach, lifecycle) map onto the S225-M locked-section/registration laws already landed.
- **#520** (coder-7 PMS-Lite): component-index rows are app_registry-adjacent, not native-execution evidence; APP-016..019 (S226 transfer) remain the canonical app rows.
- **#521** (coder-9 resources/assets): the ttt `assets/i18n` FileNotFoundException deferred-exception row in this census is the asset stage's live signature; G-stage (assets→GPU) provenance work rides on the S203/S206 pipeline laws already landed.
- **#583** (cross-lane integration): the Mindustry `DEFAULT_BACKGROUND_ONLY` face and this census's four gray faces are ONE family (stage H). The fix route is shared: presentation gate law (a presented frame must carry app-owned pixels or a structured PARTIAL row) rather than per-app patches.

## 3. Statuses

- Route matrix: **IMPLEMENTED + TESTED** (24 cold runs + 1 no-tap probe executed this wave on the frozen RC binary; record `evidence/s228_census/s231_cold_runs_batch.json`).
- PURE-DEX control + libGDX-physics pins: **TESTED** (byte-exact pin faces reproduced ×3).
- ttt: **PARTIAL** (pin holds without input; input→present is the I-stage divergence).
- dooz: **PARTIAL** (Compose boot + navigation real; kotlinx death family intermittent; board render still absent).
- SDL2/SDL3/freebloks/tower3d: **BLOCKED** at the named stages with deterministic faces.
- ViewStub inflate + Adapter convertView recycling + GridView numColumns laws (#585 §5): **IMPLEMENTED** this wave in source with a law battery — delivered in the following receipt.
- What this matrix does NOT claim: no native-route APK is declared FIXED; the gray-face family is a shared-root-cause finding, not per-app status.

## 4. Method / reproducibility

- 3 cold runs per APK, fresh `--data-root` per run, one binary SHA, `--execution-mode real-dalvik`, `--frames 12 (40 ttt)`, `--frame-delay 250`; exact console logs + per-run dirs preserved under `.cache/s228_cold_runs/runs/` (untracked per the run-output law; the compact JSON is the promoted record with per-run face SHAs, screenshot verdicts, first-divergence patterns and report statuses).
- Screenshot discipline (S213/S214): every census screenshot ≤800 KB (largest 36 KB) — `screenshot_verdict: OK` on all rows; no noise frames accepted as evidence.
"""

def token():
    cred = subprocess.run(["git", "credential", "fill"],
                          input="protocol=https\nhost=github.com\n\n",
                          capture_output=True, text=True, cwd=str(BASE)).stdout
    return [l.split("=", 1)[1] for l in cred.splitlines()
            if l.startswith("password=")][0]


def post(num, body):
    import urllib.request
    req = urllib.request.Request(
        f"https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{num}/comments",
        data=json.dumps({"body": body}).encode(),
        headers={"Authorization": f"token {token()}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "s231-route-matrix"},
        method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.loads(r.read().decode())
        print(f"posted #{num} comment id={out['id']}")


if __name__ == "__main__":
    post(582, BODY)
