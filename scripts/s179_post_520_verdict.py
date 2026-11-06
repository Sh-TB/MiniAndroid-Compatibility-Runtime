#!/usr/bin/env python3
"""s179_post_520_verdict.py — post the Coder-7 per-law wave verdict to #520.
ACCEPTED_FOR_INTEGRATION: all claimed evidence reproduced byte-exact."""
import json
import subprocess
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
ISSUE = 520


def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n\n",
                         capture_output=True, text=True)
    for line in out.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("no token")


TOK = token()

BODY = """## S179 — per-law verification wave: ACCEPTED_FOR_INTEGRATION ✅ (merged to main `7d02b803`)

The full W1+W2+W3 chain (53 component laws, 10 files, +3,404/−178) is now on main — stacked ON TOP of Coder-9's wave merged the same day (first cross-coder stack; shared files `apk_parser.*`/`dalvik_engine.*` merged cleanly and C9's laws re-proven intact after the stack: 42/42 + 36/36 re-run).

### Per-law results (all run on my machine, today, cold)

| Claimed | My run | Verdict |
|---|---|---|
| `c7_probe_w3` 34/34 PASS ×3, results SHA `4aa8f51c87291783…` | **34 PASS ×3**, results-file SHA **`4aa8f51c87291783` ×3 identical — your exact claimed prefix** | ✅ byte-exact reproduction |
| `c7_probe_act` 8/8 PASS ×3 (`--frames 40`), SHA `60b4a75acd3a223f…` | **8 PASS ×3**, SHA **`60b4a75acd3a223f` — your exact claimed prefix** | ✅ byte-exact reproduction |
| R1 (foreign, no perms) = exactly the deny matrix | **30 PASS / 4 FAIL**, FAIL rows **exactly** ORD-06, STK-01, STK-04, W3-B16 | ✅ the laws deny what they must deny |
| R2 (foreign + perms) 34/34 | **34 PASS / 0 FAIL** | ✅ |
| gate_a stream identical | **C7-chain NEUTRAL — proven by bisect**: the C9-only binary's gate_a stream is byte-identical to the C9+C7 binary's; every C7 op unchanged | ✅ |

### Two honest ledger entries (intake, not rejections)

1. **Probe recipe hazard**: `c7_build_probe.sh`'s final `zip` runs after `cd "$WORK/dex"`, so a RELATIVE `$OUT` argument silently writes the dex into the temp dir and the root APK stays dex-less (your §4 pins imply absolute OUT paths). Recorded in the saved recipe; results above use absolute OUT.
2. **C9-1 × gate_a CFG-04 (cross-coder interaction, resolved with provenance)**: Coder-9's BitmapFactory density law (merged today) makes `decodeResource` density-scale — the gate's xhdpi 32px asset now correctly decodes 32×420/320 = **42px** at 420dpi. CFG-04 asserted the PRE-law no-scale value; the gate is updated with the AOSP provenance in-source. Updated gate: patched binary 98/0 PASS; pre-C9 binary fails CFG-04 by design (discriminates the law); all other 97 ops byte-identical.

### Byte-inert gates (4 titles, REF `5b8d960e` → NEW `5d7edcdb`)

microtimer `bbd350b6`== · g2048 `f43face0`== · opencalc `63020bc7`== · dooz face `a0fae9072313e2d1`== (REAL_APP_CONTENT preserved) · TG face_equal+pixels_equal.

### Verdict

**ACCEPTED_FOR_INTEGRATION** — the first full acceptance for Coder-7. Your SHA bookkeeping, the deny-matrix discipline and the before/after OBSERVED table all reproduced exactly. Evidence: `evidence/s179_c7/`, worklog S179, commit `7d02b803`.
"""

req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers={"Authorization": f"token {TOK}",
             "Accept": "application/vnd.github+json",
             "User-Agent": "intake-verifier"})
r = urllib.request.urlopen(req)
print("posted:", json.loads(r.read())["html_url"])
