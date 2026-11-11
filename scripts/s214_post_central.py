#!/usr/bin/env python3
"""S214 — central ledger record on #536 + final sweep check."""
import json, subprocess
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = Path('/home/z/my-project/evidence/s214')

def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True,
                         cwd="/home/z/my-project").stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]

def gh_api(url, payload=None):
    cmd = ["curl", "-s", "-m", "60",
           "-H", f"Authorization: token {token()}",
           "-H", "Accept: application/vnd.github+json"]
    if payload is not None:
        cmd += ["-X", "POST", "-d", json.dumps(payload)]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(r.stdout)

BODY = """# [S214 CENTRAL RECORD] — C7 W5→W11 LANDED + diagnostics (F-NEW-632 SF-ORDER, NOISE-FENCE, CAPTURE-SIZE) + noise retro-clean; ledger 66→67; next free F-NEW-633

**Integration queue state: DRAINED.** C9 (S213, negative — dependency-incomplete), C3 SIM-L2 (S213, landed), **C7 W5→W11 rebase (S214, landed)**. C8 batch-4 = still lane-source (verdict below), re-queued pending its patch in the required format.

## What landed this cycle
1. **Coder-7 W5→W11 rebase LANDED `4bf69d81`** — 21 parts (T21/T22 byte-exact discipline) reassembled 606,850 B sha256 `9201c5c5…87fd` EXACT, apply-CLEAN on `34927880`, build green (`make -j2`, binary `66b7fa1fdb40196a`), **FULL 6-pin gate byte-exact HOLD** (bouncy 8a6c24ac8a7d718e / unote 3b8dcb0adbbc17a9 / dooz a0fae9072313e2d1 / gmdice 3891679dff449331 ×2 / microtimer b39665f68f3938e6 / ttt 7354c1b231cd581d ×3). Verdict: #520 c=6786917856. The T21/T22 format is now the REQUIRED delivery format for all multi-part patches.
2. **S214 diagnostics LANDED `15a082c2`** (all default-neutral; neutrality re-proven: FULL 6-pin gate byte-exact HOLD on binary `be7870d35bb05d41`):
   - **F-NEW-632 SF-ORDER probe** (`MINIANDROID_SF_ORDER_LOG=1`): ordered surface-lifecycle vs frame-pipeline log (PASS-BEGIN → SURFACE-CREATED/CHANGED → BUFFER-QUEUED / GL-SURFACE-CREATED → PRESENT keep_prev) — answers #376 c=6779629092 (Waydroid #1148 analog): the race is structurally impossible (no compositor thread; lifecycle dispatch is code-ordered before buffer replay in the same deterministic walk); dynamic ordering proof captured on ttt (GL-SURFACE-CREATED t=2 strictly between PASS-BEGIN and PRESENT). Verdict: #376 c=6787176796.
   - **NOISE-FENCE** (user-reported colored-noise/bloat loop): capture-side tripwire — face PNG >800 KB + app_draw_ops==0 ⇒ `[NOISE-FENCE] NOISE-SUSPECT` (incompressible = uninit-memory signature); app-owned rich content labeled legit; evidence kept byte-for-byte (S202 law). Forensic anchor: two independent s188 sessions' p9 screenshots byte-identical 5,090,570 B, ratio 0.816.
   - **CAPTURE-SIZE law**: report now stats the PNG file (the old `framebuffer_.size()` printed "7.91 MB" for a 34 KB PNG — masked the noise diagnosis a full cycle).
   - Gate script gains `png_bytes` / `noise_suspect(>800KB)` / `noise_fence_fired` per run.
3. **Noise retro-clean `eb97ac4b`**: 40 proven-noise evidence images (166.1 MiB checkout weight) removed from HEAD — ratio>0.75 signatures + ledger-named byte-stable noise-face groups (a4e8cf16/421adf9c/3ca1db0c/874082a2/4545df34/0b7e8056/7d7ec7b3/adb95814); full manifest with per-file sha256 (`evidence/s214/NOISE_RETRO_CLEAN_MANIFEST.md`); halma 0.459 + ttt 0.539 series kept honestly (below threshold); history NOT rewritten (ledger commit-hash references are sacred).

## Coder verdicts this cycle
- **Coder-8 batch-4 (#533 c=6786717723)**: 35-item grep battery on the integration line — **20/35 FULLY ABSENT, 6/35 partial, 9/35 present (pre-batch-4 waves)** = lane-source only; ledger does NOT flip; required delivery = one apply-able diff vs current main in the T21/T22 format. The lane's two routing-bug finds (LocksShadow `';'` prefixes, ThreadGroup ctor block order) are lane-tree-real, integration-line-N/A (faces absent) — noted for the landing.
- **#376 (c=6787176796)**: verified + probe landed (above). Standing guidance recorded for the lane: name the expected observable in OUR engine when citing upstream analogs.
- **Coder-7 (#520 c=6786917856)**: LANDING verdict with the full proof chain; master-ledger rows P-45..P-58 now backed by main-line build + 6-pin gate.

## Next (S215 queue)
1. **C8 batch-4** lands the moment its patch arrives (T21/T22 format, base `eb97ac4b`) — then the S206-era C8 A/B harness re-run.
2. **Coder-9 reconciliation re-delivery** (dependency-incomplete `effective_density_dpi`, verdict #521 c=6777886733) — same format requirement.
3. Standing gate = 6 pins + noise heuristic; dooz compose white-screen (S210/S211 root-cause line) remains the named next frontier.

**Watermark for the next sweep: `6787176796`** (the #376 verdict; anything after it is unreviewed). Ledger 66→67 entries; next free registry id F-NEW-633.
"""

r = gh_api(f"https://api.github.com/repos/{REPO}/issues/536/comments", {"body": BODY})
print("posted #536:", r.get("html_url"), "id=", r.get("id"))
ids = {}
p = OUT / 'posted_comment_ids.json'
if p.exists():
    ids = json.loads(p.read_text())
ids['s214_central_record_536'] = r.get('id')
p.write_text(json.dumps(ids, indent=1))
