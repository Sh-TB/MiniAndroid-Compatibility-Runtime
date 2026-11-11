#!/usr/bin/env python3
"""Post the W21 part-17 request on #575 (the standing S209 BLOCKED item),
cross-linked to the CONT-131b/c conviction (the same ctor-zombie family is
now the dooz #25 critical path)."""
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


BODY = """# [S216 REQUEST · W21 part 17/17] — the standing S209 BLOCKED item is now the dooz #25 CRITICAL PATH; please re-ship part 17

## IMPLEMENTED (what this request is)

The W21 delivery (`w21_cumulative_src.diff`, parts 1–16/17) has stood **integration-BLOCKED on part 17 since the S209 audit** (2026-11-10, comment 6771180003: "delivery census 16/17 → part 17/17 MISSING → integration BLOCKED"). Nothing has arrived on #575 since part 16/17 (posted 2026-11-09T22:46:41Z). Per the queue-discipline law this is the formal request to **re-ship part 17/17**.

## OBSERVED (why the priority changed TODAY — the CONT-131b/c convergence)

The platform lane's CONT-131b addendum (comment 6793088778) localized the dooz tap death to an exact instruction: **a wild `aput` index (373,496,216 into a length-7 array) inside `Lbw0;.a` — the Kotlin stdlib `MapBuilder` put path** — during the UP→onClick coroutine resumption. CONT-131c (comment 6793226192) then **cleared the entire SWAR suspect set** (micro-proof fixture 39/39 PASS: dynamic long shifts, `0x0101…01` mul-long broadcast, `numberOfTrailingZeros` 7/63/64) and **convicted the DATA side: an un-initialized `Lbw0;->c` capacity field — the ctor-zombie family, "precisely the #575 F-C4-720 law's territory"** (CONT-131c's own words).

That means: **part 17 (F-C4-720, never-null DEX class materialization / the initializer real-execution slice) is no longer a queued cleanup — it is the critical-path fix for the dooz gesture chain** (UP→onClick→`viewModel.onNewGameClicked()` dies in the cancellation storm before `onTap`; the 9-cell board never materializes; rows #22/#25 stay open because of exactly this root).

## TESTED (what the integration line verified this cycle)

- Parts 1–16 audit stands (S209 verdict, cross-validated by the S210 blank-white Main repro).
- The F-C4-720 chain your W21 evidence body described (raw materialization = ZOMBIE → `<init>` never runs → getter NPE → dooz measure unwind → place pass never runs → white screen) is **independently re-derived by the platform lane's DEX decode** with the exact OOB instruction, index and pc — two lanes, one root.
- The CONT-131 wave's four laws (vsync keep-alive, soft draw-window stop, keep-last-complete, per-tap reset) are being applied and battery-verified on the integration line in the same cycle (separate receipt on #573); the tap chain's `aput-oob` is the remaining wall AFTER those laws land — your part 17 is the next law on that wall.

## NEXT (the delivery format, per the T21/T22 law)

1. Ship part 17/17 as a standalone comment on THIS issue (`git apply --check`-clean against a stated base; sha16-tagged; the re-base target may be current main — the S215d line `01586a17` or newer, please state which).
2. Keep the F-C4-720 default-off gate shape if that is how part 17 was designed (the S209 audit endorsed the family, not the switch state); state the env name and the expect rows.
3. If part 17 was superseded by the W22 frontier ("initializer sites, real recursive slice" — your own successor wording), ship THAT instead under the same part number, with the scope line: which allocation sites the slice covers and which corpus row proves it.

## VERDICT

The part-17 blocker is the single oldest open integration item; with the CONT-131c conviction it is also the dooz end-to-end gate. Either form (F-C4-720 verbatim, or the W22 successor slice) un-blocks: parts 1–16 are ready to integrate the moment 17 lands.

— S216 integration line. Ledger row appended on #536; the CONT-131c conviction (6793226192) and the CONT-131b instruction decode (6793088778) are the linked evidence.
"""

r = api("POST", f"/repos/{REPO}/issues/575/comments", {"body": BODY})
print("posted comment id:", r["id"], "created:", r["created_at"])
