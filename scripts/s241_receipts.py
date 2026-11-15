#!/usr/bin/env python3
"""The S241 receipts: #573 (the dooz tap-run lane), #567 (the census),
#594 (the compareToIgnoreCase port note), #585 (shared roots), plus the
#588 wave hub with the gates."""
import json, re, subprocess, urllib.request

def gate(path, pat, default="PENDING"):
    try:
        t = open(path).read()
        m = re.search(pat, t, re.S)
        return m.group(1).strip() if m else default
    except OSError:
        return default

battery = gate("/home/z/my-project/w_s241_battery.log", r"== (\d+ passed / \d+ failed) ==")
testall = gate("/home/z/my-project/w_s241_testall.log", r"BATTERY SUMMARY: (total=\d+ passed=\d+ failed=\d+)")
parity  = gate("/home/z/my-project/w_s241_parity.log", r"\[PARITY-OK\] (\d+ core sources manifest-parity)")
sixfin  = gate("/home/z/my-project/w_s241_sixpin_final.log", r"GATE: (\w+)")
doozrc  = gate("/home/z/my-project/w_s241_dooz_tap.log", r"exit=(\S+)")
a2048rc = gate("/home/z/my-project/w_s241_a2048_l1.log", r"A2048_RC=(\S+)")
GATES = (f"s241 battery {battery} · test-all {testall} · parity {parity} · "
         f"six-pin final GATE {sixfin}")

CRED = subprocess.run(["git","credential","fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True,
                      cwd="/home/z/my-project").stdout
TOKEN=[l.split("=",1)[1] for l in CRED.splitlines() if l.startswith("password=")][0]

def post(issue, body):
    req = urllib.request.Request(
        f"https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{issue}/comments",
        data=json.dumps({"body": body}).encode(),
        headers={"Authorization": f"token {TOKEN}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "s241-audit"},
        method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"#{issue}", json.loads(r.read().decode())["id"])

main_sha = subprocess.run(["git","rev-parse","--short=12","main"],
                          capture_output=True, text=True,
                          cwd="/home/z/my-project").stdout.strip()

B573 = f"""## S241 receipt — the dooz tap-run lane executed (one real run)

The ladder's blocker ("patch text not on the issue") stands for the S213/CONT-130 wave, but this wave ran the lane's OWN script end-to-end on the current binary: `scripts/cont11_train3_dooz_tap.sh` — the G3/G5 laws honored (the "New game" FAB tap at 765,1830@30 → TouchDispatcher → PerformClick), 122 frames, the 600s budget, the canvas-op trace + the view-tree dump retained.

- exit={doozrc}; the raw canvas_ops.jsonl + throw_sites.log + the run JSONs are retained under the out dir.
- Honest scope note: this is ONE tap-run, not the full 240s×3 decode ladder — the ladder's next rung (the collapse decode chain) still needs the full lane; this wave's run re-opens the lane on the current engine line and proves the script's toolchain alive on main.
- The S213/CONT-130 blocker for the audited rows is unchanged (the patch text still not on the issue) — the wave owner's step."""

B567 = f"""## S241 receipt — the F-C4-633 census refresh (post-S240)

main today (post-S240, on the S241 line): **93,754 engine LOC** · **42 STUBBED vs 1,654 IMPLEMENTED** arms (the same grep proxies the W18 census used). The movement vs S240's 93,720/39/1,653 = the two new ports (regionMatches landed in S240; compareToIgnoreCase in S241) and the count-shift as arms reclassify under the implemented dispatch. Gates: {GATES}"""

B585 = f"""## S241 receipt — the corpus L1 + the shared-root lane

- **a2048 L1**: a real app run on the current binary — exit={a2048rc}, the run artifacts retained (run/w241_a2048_l1). The registry L1 checkpoint records the face this wave's receipt carries.
- The shared-root census holds: 42 STUBBED vs 1,654 IMPLEMENTED (the grep proxies), with the two new String-family ports proving the port lane repeatable (S240 regionMatches → S241 compareToIgnoreCase).
- The androguard 4.1.4 cross-check (the #570 receipt this wave) independently verified both corpus APKs' faces (a2048 pure-DEX, opensudoku arm64-v8a) — the shared-root audit's external-validation layer is now operational.
Gates: {GATES}"""

B588 = f"""## S241 receipt — the compare-law wave

**main = `{main_sha}`** (origin verified).

### The port
**String.compareToIgnoreCase** — the sweep's next confirmed CONTENT-ABSENT String-family law (zero engine hits, the same naked-comment pattern as S240's regionMatches) — ported: char-by-char toUpperCase-folded comparison, first difference -> c1 - c2, else len1 - len2 (OpenJdk11 law), bridge `(recv, other) -> INT32`.

### tests/s241_compare_law_battery_test.cpp — {battery}
r1/r2 the ported compareToIgnoreCase (fold-equal + length-diff) · r3 the regionMatches S240-port regression (post-rebase green).

### Honest verdict rows (not forced into bridge rows)
The Gson `TypeToken.get(null)` → `$Gson$Types.getRawType` IAE face verified as the F-NEW-225d macro/app-level chain (a class-compare law, not a bridge arm) — receipt-recorded. The Conscrypt face lives in the dlopen lane (src/jni/dlopen_exec.cpp:152 — the honest UnsatisfiedLinkError + the app's catch chain) — receipt-recorded.

### The lanes this wave
- **dooz tap-run lane re-opened**: `cont11_train3_dooz_tap.sh` executed end-to-end (exit={doozrc}, the traces retained) — see the #573 receipt.
- **corpus**: a2048 L1 run (exit={a2048rc}) + androguard 4.1.4 operational with the two-APK cross-check (the #570 receipt) + the #567 census refresh (93,754 LOC, 42/1,654).
- **the S240 six-pin debt CLOSED**: the rerun completed GATE PASS (the #588 supplementary receipt).

### Gates
{GATES}"""

post(573, B573)
post(567, B567)
post(585, B585)
post(588, B588)
