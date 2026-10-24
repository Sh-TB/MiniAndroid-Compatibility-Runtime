#!/usr/bin/env python3
"""CONT-28 W1 — post the wave ledger to issue #387."""
import subprocess, json, sys

def token():
    out = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no github credential")

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

BODY = """## CONT-28 / W1 banked — مشکلش حل شد (the f141 null-contract family)

**Wave type (per the recurring-patterns directive):** one repeated pattern
root-caused and fixed once → every census title carrying the pattern
advances at the same time. Binary `bc855252d150815d`, remote main
`b8213493..08c2c40f`, secret-guard PASS.

### The repeated pattern (الگوی تکراری)
R8 compiles its implicit null-check instrumentation as an immediate
`X.getClass()` on factory results — usually inside `<clinit>`. A framework
factory answering null kills the whole class at first touch; on ART the
same bytecode never sees null (never-null contracts). DEX-decoded roots
(cont26 disassembler, pc-exact):
- webstack `Lru1;.<clinit> pc=47` = **Logger.getLogger → null**
- audiobook `Lox5;.<clinit> pc=14` = **LocalTime.of(22,0) → null**
- wocheneinkauf `Lqm;.<clinit> pc=25` = **TrustManagerFactory.getInstance → null** + `Ly7;.a pc=34` = **BreakIterator → null**

### FIX — the F516 battery (4 laws, bridge_to_api)
- **L1** `java.util.logging.Logger` (OpenJDK demand-create+cache; getLevel
  null = the contract, not a stub)
- **L2** `java.time.LocalTime` (nano-of-day value objects; DateTimeException
  on out-of-range, never null)
- **L3** `javax.net.ssl.TrustManagerFactory` (X509; non-null factory;
  getTrustManagers 1-elem array)
- **L4** `java.text.BreakIterator` (never-null; DONE-contract boundaries)

### VERIFY
- All 4 named faces DEAD — clinits `result=OK` (`run/cont28/f141/`).
- **dooz advanced by its own family hit**: `Logger.getLogger('o0')` (OkHttp
  clinit) now completes → 90s anchor re-pins `31ddd4d5 → 851cc176` (the
  recorded CONT-12 deeper state, reached within 90s). Lawful, root-caused.

### Regression wall
- anchors ×6: opencalc/chess/microtimer/unote/tower3d **byte-identical** + dooz lawful re-pin
- games ×7 (2048/Tetris/SnakeDeluxe/SnakeNeon/TTTDeluxe/MiniCraft/gmdice): rc=0, r1=r2=r3, **byte-identical to pre-W1**
- user goldens **4/4** (REAL_APP_UI pixel gates), negatives **19/19**, skill selftest **13/13**
- batch-20 census verdict lines honest-unchanged (each title's layer-2 face named)

### Division-of-work stream results (research subagent)
`evidence/cont28/RECURRING_FACES_LAW_SPEC.md`: **S102 compose-locals CNF +
DataStore ENOENT = PROVEN ART-faithful decoys** (both censuses' "next-wave"
families) — reclassified EXPECTED-HANDLED, zero engine change needed. The
real shared frontier stays the **APP_DRAW_OPS draw path**.

### Next (registered)
F-NEW-520 collections view/iterator stub family (Map.put REC-MISS →
entrySet/iterator/Entry stubs — GPG-107 kin, biggest fan-out), then the
named per-title dives (audiobook fragment chain, webstack Lp21;.<init>,
prism cursor, surgeengine Sensors, goodtime). Registry 835→836 id-unique.
Evidence: `evidence/cont28/CONT28_W1_LEDGER.md`.
"""

def post(issue):
    tok = token()
    out = subprocess.run(
        ["curl", "-sfSL", "-X", "POST",
         "-H", f"Authorization: token {tok}",
         "-H", "Accept: application/vnd.github+json",
         "-d", json.dumps({"body": BODY}),
         f"https://api.github.com/repos/{REPO}/issues/{issue}/comments"],
        capture_output=True, text=True)
    try:
        j = json.loads(out.stdout)
        return j.get("html_url") or j.get("message", "unknown error")
    except Exception:
        return out.stdout[:200] or out.stderr[:200]

if __name__ == "__main__":
    print("comment:", post(387))
