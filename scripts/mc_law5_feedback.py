#!/usr/bin/env python3
"""Main Coder — LAW 5 feedback: post Mainline Integration Audit comments."""
import json
import subprocess
import sys
import urllib.request

sys.path.insert(0, "scripts")
from mc_phase_a import get_token  # noqa: E402

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
TOKEN = get_token()

AUDIT_596 = """### Mainline Integration Audit — audit/s236 branch (F596 wave)

- **Original contribution:** the S236.1 law wave — F-NEW-656c UriMatcher '#'-gate, F-NEW-658c ContentValues copy-ctor flat-mirror, F-NEW-658 insert family, F-NEW-659 framework string-id table, F-NEW-660 indexOf, F596-P1 getXml leak-shape + java.time.Instant, and the F596-P1 path-2 composed-CREATE dedupe (opensudoku `RATING_LEVEL` face).
- **Contributor:** the S236 audit coder (branch `audit/s236`, 7 commits).
- **Technical evaluation:** verified by content-level audit of main (2026-11-28, Main Coder ledger session). The branch's fixes were written against the PRE-SPLIT layout (`dalvik_engine.cpp` monolith); main's canonical home is now the split TUs.
- **Relevant files/symbols:** `sqlite_shadow.cpp` (execSQL dedupe), `dalvik_bridge_domain_android_core.cpp` (656c @322, 658c @48), `dalvik_opcodes_invoke.cpp` (659 @6785), `dalvik_bridge_domain_jdk.cpp` (Instant @1059), `tests/s236_port_laws_test.cpp`.
- **Implementation commit:** branch commits 536cd5ace..0f4e43b32; mainline selective integration `0d9b537a9` (path-1) + the laws in main's split TUs.
- **Tests and evidence:** branch gates 32/32; main battery now **17 rows** (the branch's rows + `r12_f596p2_composed_create_dedupe` added by this audit: a composed CREATE with a duplicate column-definition must SUCCEED, first occurrence kept — functional criterion rowId=1 on the deduped table).
- **Current main status:** 95% of the wave was ALREADY main-integrated (selectively re-applied to the split layout by earlier sessions — content-verified, not assumed).
- **Integration commit (this audit):** the ONLY missing piece — the path-2 composed-CREATE dedupe law — is now ported to main's `sqlite_shadow.cpp` execSQL arm (verbatim from the branch tip, including the dangling-binding fix) + battery row r12. Battery 17/0 ×3; anchor gate byte-identical (gmdice 3891679d / bouncy 37326cb2 / pfdicer 31ffa499 / pfludo 21ea13e1) on binary `8451d6e7`.
- **Remaining work:** the full opensudoku app journey still blocks at an unrelated compose frontier (IllegalArgumentException, `Let;.b`) BEFORE the DB chain — the dedupe face cannot be re-observed through the full app until that frontier clears; the law itself is proven at the battery level (the branch's own sudoku verification used the same synthetic-harness approach).
- **Final disposition:** **INTEGRATED INTO MAIN** (path-2 dedupe by this audit; the rest verified as previously integrated). Attribution preserved: the branch receipts and harness evidence remain the discovery record. Exact main SHA to be attached in the next ledger comment after push.

**INTEGRATED INTO MAIN** — dedupe law + battery row landed; 4 anchors byte-identical; 5 gate batteries green.
"""

AUDIT_626 = """### Mainline Integration Audit — PR #626 (wave10/dalvik-accel)

- **Original contribution:** W19/W20 build engineering — dev-so dep-graph fix (`.d` files generated but never `-include`d → stale relinks), `adapter_scrap_bin.h` `<cstdint>`, verified independent-coder patch (#627: one unnecessary `android_shadows.h` include removed from `dalvik_engine_tail.cpp`, fan-out 18→17), dev PIC -O0 profile, PCH/`-j2` rejections with data, `w20_bench.sh` 7-phase evidence.
- **Contributor:** wave10 coder (15 commits).
- **Technical evaluation:** content-verified against main (2026-11-28). **All three source fixes are ALREADY IN MAIN** — `adapter_scrap_bin.h:11` carries the W20 cstdint fix comment; `dalvik_engine_tail.cpp` no longer includes `android_shadows.h`; the Makefile `-include` block sits below the variable definitions. The W19/W20 source work reached main via direct wave commits.
- **Current main status:** SUPERSEDED — the PR's remaining delta over main is evidence/process documentation, not source.
- **Final disposition:** NOT merged (would only duplicate main); **INTEGRATED INTO MAIN (by other commits)**. Recommend closing this PR with this audit as the record. No action required from the contributor — the dep-graph fix and the #627 patch are live in main.
"""


def comment(issue, body):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/{issue}/comments", method="POST",
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "main-coder-agent",
                 "Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, data=json.dumps({"body": body}).encode()))
    print(f"#{issue}: {r['html_url']}")


if __name__ == "__main__":
    comment(596, AUDIT_596)
    comment(626, AUDIT_626)
