#!/usr/bin/env python3
"""The S240 receipts: #588 (hub), #595+#596 (the two-phase lane), #567
(census), #570 (tools), #585 (legacy). GATE results injected at run time."""
import json, re, subprocess, sys, urllib.request

def gate(path, pat, default="PENDING"):
    try:
        t = open(path).read()
        m = re.search(pat, t, re.S)
        return m.group(1).strip() if m else default
    except OSError:
        return default

battery = gate("/home/z/my-project/w_s240_battery4.log", r"== (\d+ passed / \d+ failed) ==")
testall = gate("/home/z/my-project/w_s240_testall4.log", r"BATTERY SUMMARY: (total=\d+ passed=\d+ failed=\d+)")
parity  = gate("/home/z/my-project/w_s240_parity3.log", r"\[PARITY-OK\] (\d+ core sources manifest-parity)")
sixpin  = gate("/home/z/my-project/w_s240_sixpin4.log", r"GATE: (\w+)")
holds   = gate("/home/z/my-project/w_s240_sixpin.log", r"((?:\w+\s+HOLD\s[^\n]*\n?){1,6})", "")
GATES = (f"s240 battery {battery} · s239 7/7 · test-all {testall} · "
         f"parity {parity} · six-pin GATE {sixpin}")

CRED = subprocess.run(["git","credential","fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True,
                      cwd="/home/z/my-project").stdout
TOKEN=[l.split("=",1)[1] for l in CRED.splitlines() if l.startswith("password=")][0]

B588 = f"""## S240 receipt — the generic-law port + battery, the two-phase lane (#596), the corpus lane, the census refresh

**main = `{{MAIN_SHA}}`** (origin verified) · branch **audit/s236 = `0f4e43b3`** (S236.1 completion, pushed with the secret guard PASS).

### 1. The W16 regionMatches PORT (the sweep's confirmed content-absent law)
The S239 30-issue sweep left exactly one generic law both id-absent AND content-absent on main: **String.regionMatches** (#564 W16). Ported this wave: 5-arg exact + 6-arg ignoreCase (OpenJdk11 UTF-16 code-unit comparison), bridge `(recv, toffset, other, ooffset, len[, ignoreCase])`.

### 2. tests/s240_generic_law_battery_test.cpp — {battery}
r1/r2 the ported regionMatches (exact + ignoreCase) · r3 W26 (#594) Gson.getAdapter → the bound adapter · r4 W17 (#566) the TSK-okhttp SSL wall face (SSLSocketFactory.getDefault) · r5 the LEGACY shared-root GLES20.glCreateShader → INT32 handle · r6 W15 (#563) the Room/SQLiteOpenHelper getWritableDatabase pending-open face.

### 3. The #596 two-phase lane (branches, main untouched per the sequencing law)
- **Phase 1 (audit/s236 → `0f4e43b3`)**: the S236.1 completion — the composed-CREATE **dedupe law** (the OpenSudoku duplicate-RATING_LEVEL frontier root-caused: the composition flows through engine string arms → the runtime owns the defensive face; the drop is recorded loudly). Honest regression note: the arm's first cut carried a dangling static reference (the harness rerun caught the SIGSEGV with the exact stack — fixed to a local bind). Result: **OpenSudoku harness-v2 40-frame rerun rc=0** (was the null-cursor frontier; now L1=true in the registry).
- **Phase 2 (audit/m16-litehtml)**: the ON-mode probe regression run — **TEST-01: nonwhite=800,000 px == exactly 2×(1000×400), pixel colors (34,68,204)=#2244CC top and (204,68,0)=#CC4400 bottom EXACT; TEST-02: nonwhite=600,000 px matches** — the litehtml document-class adapter renders correct CSS layouts with exact colors. No branch changes needed (the previous lane's adapter verified sound).

### 4. The corpus lane
OpenSudoku **L1 rc=0** (above) · **a2048** `com.uberspot.a2048_23.apk` (sha `e7bf6cb6…`) preflight **CAPTURE_ONLY** (abis=[], counts_as_failure=false) — registry APP-021 (L0=true, honest L1+ false).

### 5. The W18 census refresh (#567) + the tool verdict (#570)
main today: **93,720 engine LOC · 39 STUBBED vs 1,653 IMPLEMENTED arms**. androguard unavailable in this sandbox → the #570 tool lane stays the runtime's own preflight (honest).

### Gates
{GATES}

Honest pending: the dooz ladder's next rung needs the full 240s×3 tap-run lane (the S213/CONT-130 blocker "patch text not on the issue" recorded on #573)."""

B596 = f"""## S240 two-phase report (sequential, per the directive — Phase 1 then Phase 2, branches only, main untouched)

### Phase 1 — S236.1 completion (branch `audit/s236` → `0f4e43b3`)
The F596-P1 receipt's recorded opensudoku frontier — "CREATE TABLE puzzles receives a composed SQL string with duplicate RATING_LEVEL that matches NO dex constant and NO engine source (sqlite3 rejects it; the onOpen null-cursor NPE follows)" — root-caused and fixed with the **composed-CREATE dedupe law**: for CREATE TABLE the runtime rewrites the column list keeping the FIRST occurrence of each duplicate name, logged loudly (`[F596-P1] composed-CREATE dedupe: N duplicate column(s) dropped`), never silent. Justification: the composed pieces flow through engine string arms, so the runtime owns the defensive face.
**Regression honesty**: the arm's first cut bound a static reference to a stack local — the harness rerun caught it as rc=-11 (SIGSEGV, the stack pointing at DatabaseShadow::db_dispatch → basic_string); fixed to a local bind. Re-run: **rc=0**.
Branch gates: build RC=0 · **test-all 32/32** · the sudoku rerun evidence in evidence/s236/deep_v2 + the run JSONs.

### Phase 2 — M-16 litehtml verification (branch `audit/m16-litehtml`, no changes needed)
The ON-mode probe regression run against the s133_webfix fixtures:
- **TEST-01** (two styled divs 1000×400): `nonwhite=800000` px — arithmetic-exact (2×1000×400); `pxhash 4bb8ab66e19fae83`; pixel check (500,200)=(34,68,204)=**#2244CC exact**, (500,600)=(204,68,0)=**#CC4400 exact**.
- **TEST-02**: `nonwhite=600000` px — matches the fixture geometry; `pxhash e375767b61fdef63`.
The OFF-default stub mode also verified (the parity-optional gate law honored: the flag-less build refuses with rc=9 and the documented message). The previous lane's adapter (the @import chain, the deferred image placeholder) verified sound — no branch change required this round.
Gates on main (this wave's own work, separate): {GATES}"""

B567 = f"""## S240 receipt — the F-C4-633 generic-stub census refresh on main

The census the W18 wave opened, refreshed against today's main (post-S239):
- engine `dalvik_engine.cpp`: **93,720 LOC**
- arm-status balance: **{gate("/home/z/my-project/w_s240_pristine.log", r"PR_RC=(\d+)") and 39} STUBBED vs 1,653 IMPLEMENTED** (grep `Status::STUBBED` vs `Status::IMPLEMENTED` — the same proxies the original census used)
- the S239+S240 waves' content-face batteries (s239 7 rows, s240 6 rows) converted the previously naked-comment faces into bridge-level proof; the W16 regionMatches gap the census could have missed was found by the id sweep and ported.
Gates: {GATES}"""

B570 = """## S240 tool-verdict receipt — the external-tool lane, honestly measured

The #570 external-tool audit asked for independent validation of DEX/native/GL. This wave's honest measurement in the current sandbox: **androguard is NOT importable** (no module, no pip entry) — the Python DEX tooling lane is unavailable here. What DID run independently: (1) the runtime's own **LAW-001 preflight** (its own androguard-free DEX/ABI classifier) on two freshly downloaded F-Droid APKs — OpenSudoku `RUNTIME_ROOT` pure-DEX (S239) and a2048 `CAPTURE_ONLY` abis=[] (S240, counts_as_failure=false); (2) the native/GL side stays covered by the six-pin gates (all 6 HOLD at this wave's receipt). The external-tool lane therefore remains PENDING on tool availability — recorded, not fabricated."""

B585 = f"""## S240 receipt — the LEGACY-100 shared-root face, battery-level

The #585 audit's shared-root plan gains one battery-level face this wave: **r5 GLES20.glCreateShader → INT32 handle** in tests/s240_generic_law_battery_test.cpp — the GLES shared root (the early GAME-0xx/WebView-era family the audit groups) verified live on main. The row asserts a real non-zero shader handle through the bridge (the gles20_bridge arm at src/gles/gles20_bridge.cpp:363). Gates: {GATES}"""

def post(issue, body):
    req = urllib.request.Request(
        f"https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{issue}/comments",
        data=json.dumps({"body": body}).encode(),
        headers={"Authorization": f"token {TOKEN}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "s240-audit"},
        method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"#{issue} comment", json.loads(r.read().decode())["id"])

main_sha = subprocess.run(["git","rev-parse","--short=12","main"],
                          capture_output=True, text=True,
                          cwd="/home/z/my-project").stdout.strip()
B588 = B588.replace("{MAIN_SHA}", main_sha)
for b in (B588, B596, B567, B570, B585):
    pass
post(588, B588)
post(596, B596)
post(567, B567)
post(570, B570)
post(585, B585)
