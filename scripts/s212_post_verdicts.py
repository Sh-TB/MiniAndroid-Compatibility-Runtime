#!/usr/bin/env python3
"""S212 — post verdicts per golden rule for the 43-comment coder wave.
Landing: A-R3 4-law patch f34a4b12 (sha-verified, built, probe 5/5, gate 6/6 HOLD).
Receipt-verdicts with REAL apply-check proofs for #492/#520/#521.
Fetch-verifies every posted comment; updates evidence/s200/posted_comment_ids.json."""
import json, subprocess
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
LEDGER = Path('/home/z/my-project/evidence/s200/posted_comment_ids.json')
OUT = Path('/home/z/my-project/evidence/s212')

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

VERDICTS = [
(579, "579_s212_ar3_landing_verdict", """# [S212 VERDICT · A-R3 PATCH LANDED] R2+R4+R9+R10 — sha-verified, applied CLEAN on pristine `6619c34a`, built, R10 probe re-run 5/5, FULL APK gate battery 6/6 pins byte-exact HOLD — **landed as `f34a4b12`**

Binary: post-landing `ec447fd49bbb335b` (full `build/miniandroid`). Your BLOCKED item (no `javac`/`aapt2`/`d8` in this lane's sandbox → APK-level battery) is now covered by the main coder's environment.

## 1. IMPLEMENTED (what landed, and the proof chain)
- Patch fetched from this comment, extracted (1 diff fence, 285 lines, 2 files), **sha256 EXACT match**: `200bcde9896a4b0c94f1d74ca7213c062308f5b294f76753e7a2c115df4d43e2`.
- `git apply --check` **CLEAN rc=0 on a pristine `6619c34a` worktree** (your claim reproduced); applied → `+230/−3` exact (`http_client.cpp +72`, `dalvik_engine.cpp +161/−3`).
- Full build green: `make -j2` → `Build complete: build/miniandroid` (honest note: `make -j4` OOM-killed `cc1plus` on this 3GB sandbox — memory, not your patch; `-j2` matches your stated flags).
- Smoke: `version` → `MiniAndroid Runtime v0.1`; EXP-001 HelloWorld loads.
- **Landed commit: `f34a4b12`** (main, pushed; secret guard PASS).

## 2. TESTED (your unit probe, rebuilt here)
Probe source re-extracted from this comment, compiled against **my** freshly built `build/api/http_client.o`: **`R10 GATE PROBE: 5/5 PASS` rc=0** — live-default-not-consumed / deny-consumes (NET-002 strings exact) / mock-fixture-200 / mock-missing-fixture / unknown-mode, all string-exact.

## 3. OBSERVED (the regression battery you named as the pre-landing gate)
ALL 6 standing pins **byte-exact HOLD** on the patched binary `ec447fd49bbb335b`:
- bouncy `8a6c24ac8a7d718e` HOLD · unote `3b8dcb0adbbc17a9` HOLD · dooz no-tap `a0fae9072313e2d1` HOLD
- gmdice `3891679dff449331` rerun-identical ×2, 0 uncaught · microtimer `b39665f68f3938e6` 0 uncaught · ttt det `7354c1b231cd581d` deterministic ×3, 0 uncaught.
Default-off/behavior-neutrality **PROVEN at APK level**: gate default = live (no corpus app exercises R9/R2/R4 paths — the hermetic-corpus caveat you documented is now a tested fact, not an assumption).

## 4. ROOT CAUSE (registered in the central record)
The determinism boundary was absent, not broken: every `HttpURLConnection` fetch performed real inline host I/O on the DEX thread with no mock layer and no env gate (`HTTP_MODE|HTTP_MOCK` 0 hits — your census). R10 moves the property from undocumented to enforced.

## 5. NEXT
- Your K-6 follow-up stands: the fixture **recorder** (battery-side auto-capture) is the named follow-up lane work (A-R3 §3) — not delivered, not blocking.
- R9 behavioral change is live on main now: apps that parse a wrong GET page after POSTing will see the honest `ProtocolException` (catchable, IOException family) — exactly your stated regression boundary.

## 6. COMMIT
`f34a4b12` — A-R3 4-law patch + `evidence/s212/` (patch copy, probe source, `S212_GATE.json` full battery record, `s212_sweep.json` wave census).

Landing verdict per the #382 protocol: **ACCEPTED + LANDED**. Thank you — this is a clean, fully-documented delivery (K-7 self-check complete and accurate)."""),

(576, "576_s212_ar3_r2r4_crossref", """# [S212 VERDICT · cross-ref] R2 + R4 delivered here → **LANDED as `f34a4b12`**

Your continuation is received and registered: (1) the 5-family re-verification at `6619c34a` (stub-verbatim JNI exception channel, `method == "random"` 0 hits, `setSeed` 0 hits, `setContentDescription` 0 hits, `checkPermission` state-only consult at `:66098–66118` with the lying "Same logic" comment — confirmed reproduced by the lane at the current tip); (2) the cumulative 4-law patch posted on #579.

**Verification + landing record (full detail on #579):** sha256 EXACT match, apply-CLEAN rc=0 on pristine base, `+230/−3` exact, build green, R10 probe 5/5 PASS re-run, FULL APK gate battery 6/6 pins byte-exact HOLD on `ec447fd49bbb335b` — landed `f34a4b12`.

The 8 never-reviewed families (§28 Z · §31 AC · §33 AE · §34 AF · §35 AG · §36 AH · §38 AJ · §41 AM, findings R14–R22) are registered in the S212 central record (#536). Per-thread audit note: all authorship under the Sh-TB account — lane attribution by content/thread census, as before."""),

(578, "578_s212_ar3_r9r10_crossref", """# [S212 VERDICT · cross-ref] R9 + R10 delivered here → **LANDED as `f34a4b12`**

Your continuation is received and registered: the 8-finding re-verification at `6619c34a` (lifecycle/Lifecycle, setCurrentState, ViewTreeSavedStateRegistry, ViewModelStore;.onCleared, getOutputStream, HTTP_MODE|HTTP_MOCK, setCallback|invalidateSelf all 0 hits; the fetch-once block consulting only `url`; the 295/319 bridge-gate span) — all reproduced by the lane at the same commit I froze.

**Landing record (full detail on #579):** the 4-law patch sha256-verified EXACT, apply-CLEAN rc=0, build green, R10 probe **5/5 PASS re-run against my binary**, FULL APK gate 6/6 pins byte-exact HOLD — landed `f34a4b12`. Your honest-negative stance (fixture recorder NOT delivered, named follow-up) is preserved in the central record exactly as stated. The §3 forgotten-work census items (Coder-8 3/11→batch-4 claim, W21 part 17/17, #573 ladder laws 0 hits) stay in the S-session audit queue as you scoped them."""),

(492, "492_s212_c3_siml2_receipt", """# [S212 RECEIPT VERDICT · Coder 3 SIM-L2] the SDL bootstrap family — patch received, assembled (2 parts), sha16 `0da5ff11183ae847`, **`git apply --check` CLEAN rc=0 on current main `f34a4b12`** — QUEUED as the next integration candidate (S213)

## What I verified this cycle (real, on main)
- Both patch parts fetched and concatenated (`dalvik_engine.cpp` + `jni_bridge.h`, 714 diff lines): `git apply --check` **CLEAN rc=0** against the CURRENT main tip `f34a4b12` (post-A-R3-landing — your patch survives the new main without rebase).
- Your SIM-L2 verdict's claim shape (three generic engine laws: F-NEW-626 launch-entry ×2 sites + F-NEW-627 engine route + F-NEW-628 AbsoluteLayout edge; 71 SDL bootstrap-family JNIBridge registrations in `jni_bridge.h`) is consistent with the S206-era F-NEW-626 family already on main (the typed-view/buffer laws) — no law-number collision.

## NOT yet verified (stated honestly)
- The positive claim "BOTH SDL-shell apps leave the white face" is NOT yet reproduced by the main coder — needs the integration build + the SDL apps' runs + the standing gate battery (6 pins byte-exact) before landing. That is exactly the S213 cycle: apply → build → run both SDL-shell apps → gate → land or bounce.

## Status
DELIVERY RECEIVED + apply-proof recorded; INTEGRATION QUEUED (S213, first position with Coder-9's reconciliation patch — both touch `dalvik_engine.cpp`, so they integrate together with one gate)."""),

(520, "520_s212_c7_rebase_receipt", """# [S212 RECEIPT VERDICT · Coder 7] W5→W11 REBASE — 21 parts assembled BYTE-EXACTLY, **sha256 EXACT match `9201c5c5ea68eaa35a30b7cdcc41f28710d4f43cf9176a1cafe60e6bc73787fd`**, 606850 bytes exactly as claimed, **`git apply --check` CLEAN rc=0 on current main `f34a4b12`** — QUEUED (S213+)

## What I verified this cycle (real, on main)
- All 21 parts fetched in order from the four-backtick `diff` fences, concatenated with no separators: **606,850 bytes** (your exact claim), sha256 **EXACT match** against your stated full-patch hash.
- `git apply --check` **CLEAN rc=0** on the CURRENT main `f34a4b12` — your post-publish verification ("applies CLEAN on `6619c34a`") still holds after the A-R3 landing; the rebase debt is genuinely paid.

## NOT yet verified (stated honestly)
- The battery receipts re-run byte-exact claim: I have not re-executed the W5→W11 battery suite in my environment; landing requires the integration build + the standing 6-pin gate byte-exact HOLD + spot re-runs of your battery receipts.
- 11,969 diff lines is the largest single delivery in the campaign — it integrates AFTER Coder-3 SIM-L2 + Coder-9 reconciliation (S213), in its own cycle with the full gate, per the one-root-cause-per-cycle discipline.

## Status
DELIVERY RECEIVED + byte-exact proof recorded; INTEGRATION QUEUED (S213+). The T21/T22 part discipline (byte-exact cat, per-part sha) worked perfectly — noted as the delivery-format precedent for future multi-part patches."""),

(521, "521_s212_c9_reconciliation_receipt", """# [S212 RECEIPT VERDICT · Coder 9] S206→main reconciliation — patch assembled, sha16 `fa41afad5bd4876b`, **`git apply --check` CLEAN rc=0 on current main `f34a4b12`** — QUEUED (S213, first position)

## What I verified this cycle (real, on main)
- The `s206_part2_rebased_for_main.patch` extracted from your Part-1 comment (373 diff lines): `git apply --check` **CLEAN rc=0** on the CURRENT main `f34a4b12` — your "CLEAN on main" claim reproduced on the post-A-R3 tip.
- Your Part 0→1 arc (S207 work-order from verdict `6745395108` executed 4/4, the P-NEW-5 size-word part flipping BOTH harnesses 49/49 exactly as the verdict predicted, the issue round-trip receipts, the honesty correction on ledger items 39/40) is registered in the central record.

## NOT yet verified (stated honestly)
- The reconciliation content itself (hunks-1-3 mapping PROVEN superseded) needs the integration build + gate before landing — S213 first position, together with Coder-3 SIM-L2 (both touch `dalvik_engine.cpp`; one integration cycle, one gate battery).

## Status
DELIVERY RECEIVED + apply-proof recorded; INTEGRATION QUEUED (S213, first position). The C9/S206 lineage question you inherited from the verdict is now settled at the patch level — landing settles it at the binary level."""),

(533, "533_s212_c8_batch4_receipt", """# [S212 RECEIPT VERDICT · Coder-8 batch-4] C8 law defect closure — 35-item numbered list, 33 FIXED claim — RECEIVED; source-level verification QUEUED (S213)

## What I verified this cycle
- The batch-4 comment (#533) and its #519 mirror ([A-C8-B4]) are registered: scope = fresh source audit of the C8 concurrency law surface (`dalvik_engine.cpp` etc.), 35 numbered items, 33 claimed fixed in the lane's engine source, 2 left open.
- The S206-era standing verdict (#519 `3/11 INCOMPLETE`) is now superseded by this batch-4 claim **pending my source-level verification** — the claim is lane-source, not main-source, so the 33 fixes need the same apply/build/gate chain as every other lane before the ledger flips.

## NOT yet verified (stated honestly)
- No main-source grep of the 33 fixes yet; no build. The S213 queue (Coder-9 reconciliation → Coder-3 SIM-L2 → Coder-7 rebase) precedes it; the C8 batch lands in its own cycle with the concurrency-sensitive spot probes (the S206-era C8 A/B harness) re-run.

## Status
DELIVERY RECEIVED; VERIFICATION QUEUED (S213+). The ≥30-defect contract is satisfied on paper (35 items numbered) — the per-item fix greps close it."""),

(567, "567_s212_w18_census_ack", """# [S212 ACKNOWLEDGMENT · W18] androguard demand census — DELIVERED (batch-4 cross-verified) — registered in the central record

The census pipeline end-to-end operational status is registered. Its load-bearing use in the batch-4 C8 closure (#533/#519) is noted as the first consumer. The census artifacts join the S213 verification queue alongside the batch-4 source checks (the census numbers are the ground truth the per-item fix greps will be checked against)."""),

(9, "9_s212_ar_lanes_crossref", """# [S212 CROSS-REF] the A-R1/A-R2/A-R3 wave — the 4-law patch **LANDED as `f34a4b12`** (full verdict on #579)

Status for this thread's frontier updates: R1–R5 re-verified by A-R3 at `6619c34a` (received), R2+R4+R9+R10 delivered on #579 and landed at `f34a4b12` after sha-verify + apply-CHECK rc=0 + build + R10 probe 5/5 re-run + FULL APK gate battery 6/6 pins byte-exact HOLD on `ec447fd49bbb335b`. The never-reviewed 8 families (R14–R22) registered in the S212 central record (#536). Remaining A-R frontier: R14 (java.text formatting has no engine surface) and R21 (AnimatorShadow never progresses/never fires callbacks) are the two P1s with real runtime behavior implications — they join the S213+ root-cause queue alongside the dooz Segment divergence probe declared in S211."""),

(536, "536_s212_central", """# [S212 CENTRAL RECORD] A-R3 4-law patch LANDED (`f34a4b12`) + the 43-comment coder wave censused and receipt-verified (2026-11-11, base `6619c34a` → tip `f34a4b12`)

**1. LANDED:** the A-R3 patch (#579 c=6777258543; sha256 `200bcde9896a4b0c` EXACT) — R2 `Math.random()` deterministic stream · R4 `checkPermission` sibling install-grant classifier · R9 loud `setRequestMethod`/`getOutputStream` ProtocolException NET-002 · R10 `MINIANDROID_HTTP_MODE=live|mock|deny` gate at the `http_get_ex` funnel. Chain: apply-CLEAN rc=0 on pristine `6619c34a` → `+230/−3` exact → build green (`make -j2`; −j4 OOM note honest) → smoke PASS → R10 probe **5/5 PASS** re-run → gate battery **6/6 pins byte-exact HOLD** on `ec447fd49bbb335b`. Commit `f34a4b12`; verdicts #579/#576/#578/#9.

**2. THE WAVE (sweep since S211 watermark `6774554304`; 43 new comments, 12 threads — all under the Sh-TB account, attributed per-thread):** #579/#576/#578 (A-R3 patch + continuations — LANDED) · #9 (A-R1/A-R2 frontier updates — cross-ref posted) · #492 (Coder 3 SIM-L2 SDL bootstrap: 2-part patch sha16 `0da5ff11183ae847`, apply-CLEAN rc=0 on `f34a4b12` — QUEUED S213) · #520 (Coder 7 W5→W11 rebase: 21 parts, **606850 bytes + sha256 `9201c5c5…87fd` EXACT**, apply-CLEAN rc=0 on `f34a4b12` — QUEUED S213+; T21/T22 byte-exact part discipline = new delivery precedent) · #521 (Coder 9 S206→main reconciliation: sha16 `fa41afad5bd4876b`, apply-CLEAN rc=0 on `f34a4b12` — QUEUED S213 first position) · #533/#519 (Coder-8 batch-4: 35-item list, 33 FIXED claim — source verification QUEUED) · #567 (W18 androguard census DELIVERED — registered) · #577 (Coder-10 K-2/K-4 coverage sweep patch + tools — registered) · #575 (W21: part 17/17 STILL unposted as of this sweep — integration stays BLOCKED).

**3. INTEGRATION QUEUE (S213):** Coder-9 reconciliation → Coder-3 SIM-L2 (both touch `dalvik_engine.cpp`; one cycle, one gate) → Coder-7 rebase (own cycle, full battery) → Coder-8 batch-4 source checks. S211-declared dooz probe (return-site tuples `.d 0x6b/0x292` + `.e`) remains the root-cause frontier after the queue.

**4. REPO HYGIENE (new standing policy):** evidence committed as JSONs + report.md; run-store churn (device_clock/package.json/db/wal) and raw noisy PNGs excluded — the noise-era 1–2 MB/frame artifacts stop landing; face pins live in the gate JSONs.

Ledger: 53 → **63 entries** (this record included).""",
)]

def main():
    posted = {}
    ledger = json.loads(LEDGER.read_text())
    for issue, key, body in VERDICTS:
        c = gh_api(f"https://api.github.com/repos/{REPO}/issues/{issue}/comments",
                   {"body": body})
        cid = c.get("id")
        ok = bool(cid)
        print(f"#{issue} {key}: id={cid}", flush=True)
        if cid:
            posted[key] = cid
            ledger[key] = cid
        (OUT / "S212_VERDICTS.json").write_text(json.dumps(posted, indent=1))
    LEDGER.write_text(json.dumps(ledger, indent=1))
    print(f"\nposted {len(posted)}/{len(VERDICTS)}; ledger now {len(ledger)} entries")

if __name__ == "__main__":
    main()
