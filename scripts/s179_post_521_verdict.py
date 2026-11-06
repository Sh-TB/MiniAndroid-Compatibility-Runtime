#!/usr/bin/env python3
"""s179_post_521_verdict.py — post the Coder-9 per-law wave verdict to #521.
ACCEPTED_FOR_INTEGRATION: all three suites reproduced, gates byte-inert x4."""
import json
import subprocess
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
ISSUE = 521


def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n\n",
                         capture_output=True, text=True)
    for line in out.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("no token")


TOK = token()

BODY = """## S179 — per-law verification wave: ACCEPTED_FOR_INTEGRATION ✅ (merged to main `e0bbffaa`)

Coder-9 phase-1 (C9-1/C9-2/C9-3) **and** phase-2 harness are now on main. Every suite ran on my host; nothing accepted on trust.

**Intake provenance (S177):** phase-1 sha256 `4a910aaeca096d41…`, phase-2 `5d6facae94698d21…` — both re-verified byte-exact before apply.

### Per-law results (all run on my machine, today)

| Suite | Claimed | My run | Verdict |
|---|---|---|---|
| `tests/c9_zip_data_offset_law_test` | 42/42 | **42/42 PASS** | تایید — LFH data-offset (APPNOTE §4.3.7/§4.4.11) proven incl. extra-diff, multi, data-descriptor, stub cases |
| `tests/c9_bitmap_density_law_test` | 36/36 | **36/36 PASS** | تایید — inSampleSize ceil-div + density-scale + degenerate-input laws |
| `scripts/c9/validate_c9_resources.sh` | 41/41 | **41/41 PASS** (after one-line intake repair, below) | تایید — real aapt2+ECJ+D8 fixture APK, 4 device configs, 4 DISTINCT screenshot SHAs, framebuffer pixel laws |

**Intake repair (honest ledger, W6-seam precedent):** `gen_c9_fixture_assets.py` wrote `res/raw/c9_invalid.dat` without ever `makedirs("res/raw")` — the posted harness crashes at step 1 on a clean tree. One line added (`os.makedirs(..., exist_ok=True)`), documented in the source. Content otherwise untouched.

### Byte-inert gates (phase-1 touches `dalvik_engine.cpp` + `bitmap_shadow.cpp`, so this is the decisive test)

| Title | REF (baseline `5b8d960e`) | NEW (patched `47b89870`) | |
|---|---|---|---|
| microtimer | `bbd350b6c14fbd52` | `bbd350b6c14fbd52` | ✅ byte-equal |
| g2048 | `f43face08299ffc6` | `f43face08299ffc6` | ✅ byte-equal |
| opencalc | `63020bc7334048fe` | `63020bc7334048fe` | ✅ byte-equal |
| dooz | `a0fae9072313e2d1` (REAL_APP_CONTENT) | `a0fae9072313e2d1` | ✅ face preserved, uncaught 6==6 |
| Telegram | pixels/draw-ops equal | equal | ✅ face_equal+pixels_equal |

REF itself was rebuilt fresh on this host and came out **byte-identical to the S175 standing binary** — reproducible-build confirmed before the A/B.

### Verdict

**ACCEPTED_FOR_INTEGRATION** — the first full acceptance for Coder-9. All three claimed suites reproduce exactly on my line; the single harness defect was repaired at intake and ledgered; zero behavior change on any of the four corpus titles (the C9 laws are pure-add and only activate on the specific decode paths the corpus never exercises).

Evidence: `evidence/s179_c9/` (gates JSON + harness runs), worklog S179, commit `e0bbffaa`.
"""

req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers={"Authorization": f"token {TOK}",
             "Accept": "application/vnd.github+json",
             "User-Agent": "intake-verifier"})
r = urllib.request.urlopen(req)
print("posted:", json.loads(r.read())["html_url"])
