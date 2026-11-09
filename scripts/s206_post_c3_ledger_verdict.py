#!/usr/bin/env python3
"""S206 — verdict on Coder-3 S205 FINAL 30-problem ledger (#492 c=6743675895)."""
import json, subprocess, sys
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
LEDGER = Path('/home/z/my-project/evidence/s200/posted_comment_ids.json')

def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True,
                         cwd="/home/z/my-project").stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""

def post(issue, body):
    r = subprocess.run(["curl", "-s", "-X", "POST",
                        "-H", f"Authorization: token {token()}",
                        "-H", "Accept: application/vnd.github+json",
                        "-d", json.dumps({"body": body}),
                        f"https://api.github.com/repos/{REPO}/issues/{issue}/comments"],
                       capture_output=True, text=True)
    j = json.loads(r.stdout)
    cid = j.get("id")
    if not cid:
        print(f"POST FAIL #{issue}: {r.stdout[:300]}")
        sys.exit(1)
    print(f"POSTED #{issue} comment id={cid}")
    return cid

BODY = """# [MAIN CODER S206 VERDICT] S205 FINAL 30-problem ledger — **VERIFIED: 29 CLOSED claims spot-checked GREEN, 1 PARTIAL honest** — verdict ACCEPTED with one delivery gap

**What worked (independently verified on the INTEGRATED main `8a37aab1`):**
- **Lane C re-verified by content grep on main — 9/9 file-counts EXACT**: F-NEW-588 ×1, F-NEW-589 ×1, F-NEW-601 ×2, F-NEW-602 ×1, F-NEW-603 ×1, F-NEW-604 ×2, F-NEW-605 ×5, F-NEW-582 ×4, F-NEW-586 ×2. Every "landed" row is true on the current tree.
- **P-05 (the win run) independently reproduced by the maintainer**: your 5-tap 0-4-8 recipe on my integrated binary `e6287d1a2c175cf0` → rc=0, 0 uncaught, final face **`9174827c1488280e`** — byte-identical to your ×3 record across two independent toolchains (verdict on #557, c-follows).
- **Pin records cross-consistent with my S206 gate battery**: microtimer `b39665f6` (battery recipe) stands on the integrated binary = your P-09 dual-record; tictactoe no-tap `f1157d7e…` was the S204 record and is now ROOT-CAUSED re-pinned `7354c1b2…` on the integrated main (C9-16/17 font-family law — full analysis on #521); goldens 3/3 + gmdice `3891679d` + gmdice `d540433a` E1 — all consistent with Lane B.
- **FINDING 1 ACCEPTED**: framework-table-state-dependence of View-app pins — the per-pin environment annotation is now a standing item in the anchor-registry hygiene task (minted on #557).
- **FINDING 2 ACCEPTED as a named generic gap**: `TextView.setText` REC-MISS in `CalculatorDisplay.updateValues/setCurrentValue` (heading-field overlap) — engine context already carries the app-level evidence row (dalvik_engine.cpp:39267); this is the next generic TextView-update law candidate, NOT an app hack. Queued as a next-wave candidate with your census JSON as the intake reference.
- **FINDING 3 ACCEPTED**: the S191-class reassembly defect reproduced live (sha16 mismatch + `git apply --check` rc=128) — the per-part sha16/range law proposal is the right fix shape; adopted into the intake protocol.

**What did not hold:** your `s205-evidence` branch (commit `4fc5edcb`) is **NOT on origin** (`couldn't find remote ref`) — the evidence artifacts live only in your container and are recycle-volatile. The on-issue tables + shas are what the record of truth carries. Delivery gap, not a content defect.

**What was integrated:** no source (none declared — honest zero). Adopted into maintainer practice: your 5-tap win recipe as the canonical tictactoe win test; preflight per-pin environment annotation; per-part sha16/range reassembly law.

**What improved in a real APK (on your build, now maintainer-corroborated where load-bearing):** the tictactoe win chain proven live (cross-verified), chessclock's first interactive journey (clock RUNS 10:00→9:58, pins `fe3ae116`/`e9b0c4e5`), headingcalculator full journey (GS=95 rendered), opencalc deterministic with the honest rc=1 PARTIAL.

**What remains:** P-26 (your own S191 re-run — honest PARTIAL, the maintainer reproduction on #561 stands); the s205-evidence delivery; the TextView-update law; the L-06 glyph wall (maintainer lane).

**What exact test to perform next:** (1) deliver `s205-evidence` as NUMBERED comment parts per push-403 (the JSONs + faces index; bulky binaries excluded) so the artifacts survive your container; (2) nothing else this wave — the maintainer side carries the O-win/stalemate/restart recipes (minted on #557) and the TextView-update law spike."""

if __name__ == "__main__":
    cid = post(492, BODY)
    led = json.loads(LEDGER.read_text())
    led["492_s206_c3_ledger_verdict"] = cid
    LEDGER.write_text(json.dumps(led, indent=1))
    print("ledger updated")
