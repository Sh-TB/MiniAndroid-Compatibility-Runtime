#!/usr/bin/env python3
"""#595 follow-up: post the deep-verification RAW findings (still no merge)."""
import json
import subprocess
import urllib.request
from pathlib import Path

BASE = Path("/home/z/my-project")
CRED = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True, cwd=str(BASE)).stdout
TOKEN = [l.split("=", 1)[1] for l in CRED.splitlines()
         if l.startswith("password=")][0]

BODY = """## S236 audit follow-up — the deep-verification RAW evidence (acceptance-criteria 6 + the onDraw question)

**Main still untouched.** All new evidence lives on `audit/s236` (new head `c45573c8`), path `evidence/s236/deep/` (full RAW console logs). The sandbox recycle wiped the build tree, so the candidate was rebuilt from the branch: binary sha16 **`9745c3e7a09d0194`**, battery re-proven **12/12** on it (the six-pin ×3 record from the earlier rebuild `f76b6df780c6d468` stands; one fresh gate pass on the new binary is listed as a pre-merge follow-up).

### The 2,380-row / onDraw question — RAW-log causality pair (the issue's §D demand)

- **The provider chain is REAL:** `MyPGNProvider.onCreate` → `SQLiteOpenHelper` → `getReadableDatabase` → `rawQuery rows=8 cols=6 "PRAGMA table_info(games)"` answered from the REAL sqlite file — compilation/registry-only claims are excluded; the db layer genuinely runs.
- **The causality instrument:** a diagnostic-only, env-gated probe (`MINIANDROID_S236_PROBE_DEFER_DRAW`, zero default cost) skips the custom-view onDraw dispatch. Verified live: paired fresh-root runs show `C013-ONDRAW` **244 → 0** between probe-off and probe-on.
- **The verdict:** with the draw storm FULLY suppressed, the seeding still inserts 0–1 rows per 60-frame run (census `games=1` on BOTH arms). So on this build the draw storm is **NOT** the seeding interrupter — the frontier is the seed **THREAD scheduling** (the background seeding thread never reaches INSERT within the frame budget; every one of the 244 draws is a menu view at `ops=0`, and the board screen — where the lane's `_fieldColor` storm lived — is never reached). The lane's storm face and this thread-gating face are the SAME next-law wave; nothing in the S236 port set regressed either one.

### Chess execution-chain state (criterion 6 — honest)

- Seeded root carries 1 REAL row (`games=1`).
- The Practice tap reaches the LIST stage: `rawQuery rows=1` answers the seeded row — the cursor→adapter stage is real.
- The board-load stage (`loadPGNHead`/FEN/GameControl and the real-app reachability traces for 657/658b/659/660) needs the exact puzzle-row tap coordinates + the thread law — **PENDING**, precisely classified, not claimed.

### OpenSudoku

- The deep run's console-capture bug (the runner prints to stdout, not to the `-o` dir) was found and the RAW path fixed; the sudoku RAW logs are in the deep evidence. The row-bind census still needs the deep run re-executed with the fixed capture — **PENDING** for criterion 6, no evidence claimed.

### Bottom line (unchanged verdict, now with RAW instrumentation)

The S236 candidate stays evidence-backed and green (battery 12/12 ×3, test-all 32/32, parity, four pins byte-exact ×3, bouncy/ttt pre-existing boundary drift neutral). Criteria 6 and the 2380-row fix-proof remain **PENDING on the next law wave** (thread scheduling + the interaction coordinates), now with a working causality instrument committed for that wave. **Still STOP-after-report: no merge until the separate explicit approval.**"""

req = urllib.request.Request(
    "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/595/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers={"Authorization": f"token {TOKEN}",
             "Accept": "application/vnd.github+json",
             "User-Agent": "s236-audit"},
    method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    c = json.loads(r.read().decode())
print(f"follow-up posted: comment id {c['id']} at {c['created_at']}")
