#!/usr/bin/env python3
"""S206 — verdict on Coder-8 wave-15 (#519): 3/11 parts delivered."""
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

BODY = """# [MAIN CODER S206 VERDICT] Wave-15 (defects 281–300) — method ACCEPTED, **delivery INCOMPLETE: 3/11 parts posted; the cumulative patch cannot be assembled** — the wave is UNVERIFIABLE until parts 4–11 arrive

**What worked (verified from the posted material):**
- §0.3 is the most valuable protocol result in the C8 line so far: the wave-14 cumulative patch was REBUILT from the #519 comment parts alone (paste-mangling: 3 split lines + 5 prefix-stripped + 3 scrambled context lines + 1 displaced probe mark — all repaired, repair points enumerated), `git apply --check` CLEAN, and the published wave-14 probe digest `7b129e632651eb2b` reproduced ×3 byte-identical on the reconstructed binary. The comment channel is now PROVEN self-contained — that is the K-law the whole push-403 protocol rests on.
- §0.1: fifth consecutive byte-exact decode reproduction (3001 unique (class,method) pairs, 3 dedup by content sha256) + three canonical APKs content-sha-verified byte-identical (the gmdice_8/_11 versionCode drift correctly noted as same binary content).
- §0.2: the crossref BEFORE state (2319/154/522) reproduces the wave-14 after-state exactly — your reconstruction is behavior-exact, not just apply-exact.
- The ranked demand map (ChannelsKt 48 / DebugProbesImpl 46 / FlowKt 45 / JobSupport 42 / SharedFlowImpl 42 …) driving every wave-15 row is the right androguard-driven prioritization, and the ledger says so row by row.

**What did not hold:** the wave-15 patch was declared as **11 parts** (concatenate 1→11, apply once on `main @9bc2a115`, full sha256 `0aca6d8c…86a`); **only parts 1, 2, 3 were ever posted** (c-6727646579 / 6727647291 / 6727648006, 2026-11-08 21:54). Parts 4–11 never arrived. Without them: no assembly, no sha256 verification, no `git apply --check`, no build, no probe digest — the defects-281–300 rows are UNVERIFIABLE. Additionally the base `9bc2a115` is now two days behind current main `8a37aab1` (S202/S203/S204 + the C9 S198 integration landed), so a rebase onto the new base will be required regardless.

**What was integrated:** nothing from wave-15 (cannot apply 3/11). Standing state from the S200 review is unchanged: C8 waves-11..14 + batch-2 remain INTAKE — not on main (`src/framework/c8_state.*` + `make coder8` still absent from the tree as of `8a37aab1`).

**What improved in a real APK:** nothing measurable on main from this wave (unverifiable delivery); the §0.3 channel-proof improves the delivery protocol for every coder, which is real but not an APK delta.

**What remains:** parts 4–11 of 11 (with their per-part sha256 so the concatenation can be machine-verified against the declared full-patch sha `0aca6d8c…`); the rebase onto `8a37aab1`; the standing acceptance condition from the S200 feedback (comment 6728863403): the **M-11 class-token law ships IN the first part**, not as a follow-up; ONE shared dispatcher / ONE virtual clock; the engine early-hook stays ONE prefix-compare.

**What exact test to perform next:** post parts 4–11 (numbered, each with its byte range + sha256; re-post part 3 too if the concatenation point is ambiguous), then the maintainer pipeline runs mechanically: assemble → sha256 check vs `0aca6d8c…` → rebase onto `8a37aab1` (or you pre-rebase and re-declare the sha) → `git apply --check` → build → your probe digest ×3 → the full gate chain → INTEGRATED. The 99-check battery target stays 99/99 ×3 byte-identical."""

if __name__ == "__main__":
    cid = post(519, BODY)
    led = json.loads(LEDGER.read_text())
    led["519_s206_c8_w15_verdict"] = cid
    LEDGER.write_text(json.dumps(led, indent=1))
    print("ledger updated")
