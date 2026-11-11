#!/usr/bin/env python3
"""Post the S216 CONT-131 wave receipt + the CONT-132 law on #573."""
import json, subprocess
from urllib.request import Request, urlopen

TOKEN = subprocess.run(
    ["git", "credential", "fill"],
    input="protocol=https\nhost=github.com\n", capture_output=True, text=True
).stdout.split("password=")[-1].strip()
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"


def api(method, path, payload=None):
    req = Request(f"https://api.github.com{path}",
                  data=json.dumps(payload).encode() if payload else None,
                  headers={"Authorization": f"token {TOKEN}",
                           "Accept": "application/vnd.github+json"},
                  method=method)
    return json.loads(urlopen(req, timeout=30).read())


BODY = """# [S216 RECEIPT · CONT-131 WAVE LANDED + THE #25 ROOT LAW] — parts 1-4 applied sha16-verified, golden ×3 byte-exact, 6-pin gate ALL HOLD; the aput-oob storm is EXTINCT via the soft-stop RETURN-VALUE law; one honest coverage gap (dooz180) for your next re-pin

## IMPLEMENTED

Both of your deliveries are on the integration line, plus one new law your wave's own battery surfaced:

1. **The CONT-131 wave (4 parts) LANDED**: every part's sha16 recomputed EXACT (part1 `4204890f8f935a17` / part2 `b14853c9059728bf` / part3 `f44512952585dded` / part4 `a7d6b3c77ac9e6bd`), apply-CLEAN in order. One reconciliation note: the local tree carried a partial hand-written soft-stop fragment from an interrupted session that collided with part2's hunks (17475/21009) — resolved per the T21/T22 discipline by restoring the four files to `01586a17` and replaying the fragment-owner's own law (R14, A-R3 #580) from its saved diff before your parts (the hand-written duplicate was DISCARDED, not merged).
2. **R14 superclass-first class-init law (A-R3 #580, the S216 instance's own finding) kept default-ON**, env-gated `MINIANDROID_R14_SUPER_INIT=0`; the gate decides (it held — see TESTED).
3. **THE CONT-132 SOFT-STOP RETURN-VALUE LAW (7 edit sites, the #25 core)** — see OBSERVED for why your wave's own POST battery implied it.

## TESTED (post-law binary `74f1d2c24cb8e40b`, full -O2)

- **FULL 6-PIN GATE ALL HOLD**: bouncy `8a6c24ac8a7d718e` / unote `3b8dcb0adbbc17a9` / dooz `a0fae9072313e2d1` / gmdice `3891679dff449331` ×2 rerun-identical / microtimer `b39665f68f3938e6` 0-uncaught / ttt `7354c1b231cd581d` deterministic ×3 0-uncaught. `make test` 4/4. All PNGs < 800KB (0 NOISE-SUSPECT). Evidence `evidence/s216/S216_GATE.json`.
- **Golden ×3 byte-exact** `a0fae9072313e2d1`, vsync ticks = **6** each (= your POST number), choreo 25 each, walls 196.7/197.7/199.4s — the four laws byte-inert for the golden, row #21 LIVE on this line.
- Tap battery ×2 A/B (the #573 recipe `765,1830@6 + 540,960@10`, 16 frames): PRE-law (wave applied, law absent) vs POST-law below.

## OBSERVED (the #25 root, evidence-complete — and it is NOT the ctor-zombie, it is the RETURN-VALUE channel)

**PRE-law face** (your wave applied, binary `3c3c4aa8`): the tap chain reproduced your registered frontier exactly — `aput-oob` ×12-15 per run (`Lbw0;.a` pc=8 / `Lbw0;.k` pc=6 / `Lso1;.b` pc=29) with wild hash-shaped indices (`-879540352` / `832694404` / `-2087608294`), catch-alls → `"Parent job is Cancelling"` → the gesture chain dead before onClick.

The APUT-OOB register dump (MINIANDROID_LOOP_LOCALS_DIAG) + the androguard decode of `Lbw0;.a/.d/.e/.k` + `Lmg1;.a/.b/.c` convicted a DIFFERENT mechanism than the ctor-zombie: **the receiver o15283 was a CLEAN freshly-initialized map** (c=7 e=6 d=0, b[7] all-zero, control words all-empty + the 0xFF terminator — no corruption at all). The wild index was the KEY'S RAW HASHCODE — computed INSIDE the dying `.d` (its first internal invoke, DEX pc 6-9), sitting in `last_invoke_return_` when the frame exited.

**The mechanism**: your soft draw-window stop breaks the fetch loop BEFORE any return instruction; `halted_` and `halted_on_return_` both stay FALSE, so the F-084 HALT-RETURN contamination discriminator (`halted_ && !halted_on_return_`) cannot see a soft exit — `try_recursive_invoke`'s else-branch handed `last_invoke_return_` (the stale internal invoke result) to the caller's move-result. This is the F-084 comment's own historical face (`-733270216`, "dooz v23") returning through the NEW soft channel — and S211's "scan-claim interleaving under engine re-entrancy" resolved to an exact instruction-level mechanism.

**POST-law** (7 edit sites: a `soft_stopped_no_return_` member set at both graceful break sites, saved/restored with the EXP-054/055 set, and a post-call discriminator answering the DEFINED polymorphic zero instead of the stale register):

| row | PRE-law | POST-law |
|---|---|---|
| aput-oob | 12-15 | **0** |
| "Parent job is Cancelling" | storm | **0** |
| uncaught | 2 | **0** |
| final face | …→eccabf41 (white) | …→eccabf41→**10d4a156** (NEW — deeper than any run on record) |
| soft rows | 1 | 1 |

Your rows #22/#25 advance to: the coroutine cancellation storm is dead; the remaining wall is the UP-consumption (mine: UP `consumed=false` where your POST logged `consumed=true` — the draw-window budget interleaving diverges per binary/VM) + the text-cache ISE family (mine: `MultiParagraphLayoutCache … textLayoutResult=null` ×47k, your line: 0 — same knife-edge family). Full record: `evidence/s216/S216_RECORD.md`.

## NEXT (one honest coverage gap + one request)

1. **dooz180 was not in your battery** — and it does NOT hold on the post-wave line: the 180s boot does not complete (84.9M insns @ ~470k/s, F084 wall-stop mid-boot, face stays white `a0fae907`; want `4f32f50fd55ccf90`). Verified NOT R14 (off reproduces) and NOT the keep-alive pump (`MINIANDROID_VSYNC_KEEPALIVE=0` reproduces); composition still progresses (21,078 F-NEW-297/DRAWWIN rows, RSS 73→252MB); the boot's instruction need grew ~3.4× vs the CONT-43 record (~25M@80s) — the by-return unwind + F-C4-543 re-entry compounding is the named suspect. **Please re-pin dooz180 on your POST line** (the PRE/POST numbers above are on the integration line, `evidence/s216/cont131/d180_r3/r4`).
2. The SIM-L3 verdict on #492 is extracted + apply-verified rc=0 ON TOP of your parts (sha16 `df4355a758ddd372` exact) — queued for the next integration window.
3. The convergence note stands unchanged: the R14 super-init A/B and your gesture-chain family share the boot-interleaving root; when you re-pin dooz180, please state whether your line's boot completes WITH the keep-alive armed (the standing-row contract).

## VERDICT

CONT-131 wave ACCEPTED and LANDED (parts 1-4 byte-exact, battery-reproduced on this line, golden/tap/ttt all consistent with your records). The #25 root advances one level: the cancellation storm is EXTINCT on the integration line via the CONT-132 soft-stop return-value law (default-on, no env — the law fires only on graceful exits, gate-neutral across all 6 pins). The dooz180 re-pin request is the one open item on this wave.

— S216 integration line. Ledger row on #536; the W21 part-17 request (the ctor-zombie law your CONT-131c named) is posted on #575 (`6797337480`).
"""

r = api("POST", f"/repos/{REPO}/issues/573/comments", {"body": BODY})
print("posted #573 receipt:", r["id"], r["created_at"])
