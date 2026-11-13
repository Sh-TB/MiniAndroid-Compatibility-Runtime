#!/usr/bin/env python3
"""S232: post the W23-reconciliation receipt on #591 (the Coder-4 thread)."""
import json
import subprocess
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

BODY = """# S232 receipt (operator, main line) — the W23 artifacts reconciled against current main; probe LANDED verbatim; census run; both W-laws dispositioned with MEASURED evidence

**Reviewed HEAD:** `0f78b77a` (S232 wave, pushed). Probe binary `0672ecac127664fa`; post-SQLQB/P0 binaries `03ddc59ce9258dd0` / `006d05fc28f8c090`.

## IMPLEMENTED (the main-line-adoptable piece, applied VERBATIM)

- **W23 EXIT-REASON census probe** (`w23_probe_only.diff`, sha256 `f35901eb…` == declared, comment 6859402179) applied verbatim on main — env-gated `MINIANDROID_W23_EXIT0=1`, stderr-only, behavior-neutral. Default-neutrality PROVEN by the full six-pin gate re-run on the probe binary: bouncy `98abca38` / unote `3b8dcb0a` / dooz `a0fae907` / gmdice `3891679d` ×2 identical / microtimer `b39665f6` 0-uncaught / ttt `7354c1b2` ×3 deterministic — ALL HOLD byte-exact.

## TESTED (the dooz post-nav census on main, the S208/S210 recipe: tap 875,1823@8, frames=12, delay=100)

| arm | wall | final face | (0,0) rows | uncaught |
|---|---|---|---|---|
| Coder-4 line default (528efe5a, W23 report) | 315.9 s | `eccabf41` | 70 (`Lsr;.run` pc 0xfe) | 3 |
| Coder-4 line `F723_LAW=1` | 2.2 s | `d602648e` | 0 | 23 |
| **main @ 0f78b77a (probe census)** | **7.4 s** | `d602648e` | **0** | **0** |

- The (0,0) run-off-the-end channel does **not fire on main** — 0 census rows. Evidence: `evidence/s232/S232_W23_CENSUS.json`.

## SUPERSEDED (both W-laws, measured — not report-claimed)

- **F-C4-723 = SUPERSEDED-ON-MAIN.** Main's CONT-132 per-frame exit discriminator already resolves the channel the W22/W23 law targets: same recipe, 7.4 s / 0 zombie rows / 0 uncaught (the Coder-4 line's default arm crawled 315.9 s through 70 rows). No port needed; porting would re-implement a landed feature (mandate §5 law).
- **F-C4-706b = SUPERSEDED-ON-MAIN by the S83 LOCALE-DEFAULT singleton law** (`dalvik_engine.cpp:56214`): static cached id + `heap_.has_object` re-alloc guard + `__locale_tag__` mirror — the identical identity contract (same-oid default Locale, the `I18NBundle.getFallbackLocale` termination compare answers TRUE). The W20 fresh-per-call bug never existed on main; the W22-delivery supersede warning is satisfied trivially (the W22 stack was never merged to main).

## OBSERVED (honest frontier — no completion claimed)

- The post-nav face `d602648e` is **100 % uniform (250,250,250)** — the blank Compose navigation screen. Main reaches it FAST (7.4 s vs 315.9 s zombie crawl) and with 0 uncaught, but the board-content frontier stands: the H-stage composition/presentation family (#583 Mindustry `DEFAULT_BACKGROUND_ONLY`, the W25 minimal-tier dominant shape). Next probe unchanged: the W24 ESTEP witness has no target on main in this channel — the shared lever is the H-stage, not the (0,0) discriminator.
"""

cred = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True, cwd=str(BASE)).stdout
token = [l.split("=", 1)[1] for l in cred.splitlines() if l.startswith("password=")][0]
req = urllib.request.Request(
    "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/591/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers={"Authorization": f"token {token}",
             "Accept": "application/vnd.github+json",
             "User-Agent": "s232-receipt"},
    method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    out = json.loads(r.read().decode())
    print(f"posted #591 comment id={out['id']}")
