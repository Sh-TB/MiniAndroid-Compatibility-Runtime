#!/usr/bin/env python3
"""Post the S216 central record append on #536."""
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


BODY = """**S216 CENTRAL RECORD — APPEND** (the dooz critical-path cycle)

- **CONT-131 wave LANDED** (4 parts, sha16-verified ×4, apply-CLEAN after the source-restore reconciliation): receipt + battery on #573 (`6800130309`). Golden ×3 byte-exact `a0fae9072313e2d1`, vsync ticks 6 (= lane POST), 6-pin gate ALL HOLD on the post-law binary `74f1d2c24cb8e40b`.
- **NEW LAW F-NEW-635 (CONT-132, soft-stop return-value)**: the CONT-131 soft draw-window stop breaks frames BEFORE any return instruction; the F-084 discriminator misses soft exits (both halt flags false) and `try_recursive_invoke` handed the stale `last_invoke_return_` (the callee's last internal invoke result — the raw key hashCode inside `Lbw0;.d`) to the caller's move-result → the wild-aput storm → coroutine cancellation → rows #22/#25. The law defines the interrupted callee's return as the polymorphic zero (7 edit sites, `soft_stopped_no_return_`). POST-law: aput-oob 12-15→**0**, "Parent job is Cancelling"→**0**, uncaught 2→**0**, face chain advanced to a NEW face `10d4a156`. Root decoded via APUT-OOB register dump + androguard (the receiver map was CLEAN — the ctor-zombie mechanism is NOT this face's cause on this line).
- **Coverage gap found**: the wave battery missed the dooz180 row; on the post-wave line the 180s boot does NOT complete (84.9M insns, wall-stop mid-boot, white face) — NOT R14, NOT the keep-alive pump; re-pin request posted to the lane on #573.
- **Requests**: W21 part 17/17 formal re-ship request on #575 (`6797337480`, cross-linked to the CONT-131b/c conviction; the S209 BLOCKED item is now the gesture-chain critical path). SIM-L3 (Coder-3, #492) extracted + apply-verified rc=0 on top of the wave (sha16 `df4355a758ddd372` exact) — QUEUED next integration window.
- **Sweep pass 2** (edit-detection vs the 08:54Z snapshot, `scripts/s216_sweep2.py`): 11 NEW comments (CONT-131 wave/b/c/honesty + SIM-L3 verdict), **0 EDITED**. Full-comment snapshot baseline for the next cycle: `evidence/s216/s216_full_snapshot.json` (13 issues, incl. #580).
- **Watermark advance: `6797337480`** (the S216 posted comments themselves; the next sweep baseline). Verdicts this cycle: #573 `6800130309` + #575 `6797337480` + this record.
- Evidence: `evidence/s216/S216_RECORD.md` + `S216_GATE.json` + `cont131/` (battery logs, d180 runs, the OOB dumps) + `cont132_soft_stop_return_law.diff`.
"""

r = api("POST", f"/repos/{REPO}/issues/536/comments", {"body": BODY})
print("posted #536 central record:", r["id"], r["created_at"])
