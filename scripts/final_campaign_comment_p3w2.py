#!/usr/bin/env python3
"""FINAL CAMPAIGN — post Phase 3 wave 2 comment to issue #354."""
import json
import subprocess
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
API = f"https://api.github.com/repos/{REPO}/issues/354/comments"
HEADER = "## FINAL CAMPAIGN — Phase 3 wave 2: the probe-spin root cause, decoded by arithmetic (F-NEW-172 → F-NEW-173)"

BODY = HEADER + """

Commits `5daf987f`. All evidence from live instrumented runs on current HEAD.

### PERMANENT EVIDENCE UPGRADE (one instrumentation, every future halt)
The F084 infinite-loop halt now dumps, one-shot per halt: **SPIN-REGS** (live frame registers, heap classes + first fields per object), **SPIN-HISTO** (pc visit histogram of the spinning frame), **SPIN-TABLE** (hash-table state census), **F172-AGET** (bounded element-read trace). Every future F084 is now live-state evidence instead of a one-line message.

### THE DECODE (each step measured, none guessed)
1. `SPIN-TABLE o24744: len=32768, empty=3781, occupied=315 (first 4096 scanned), missing=0` — the `Arrays.fill(table, -1)` markers ARE present; 315 entries placed. Fill correctness hardening shipped anyway: the fill's length resolution now reads `__new_array_length__` (the uniform new-array convention, same fallback the ARRAY_GET macros use — R-NEW-361 silent-no-op-fill family closed at the API level).
2. `SPIN-HISTO`: `pc0xaf=50001, pc0xb0/b2/b5/b6=50000, pc0xc8..0xdf=49685` — the probe cycles the FULL occupied path (mask → aget-short → if-ne occupied → equals → if-eqz → slot++ → back).
3. `SPIN-REGS`: `v6=315, v12=230, v10=o1987<Ljava/lang/Integer;> value=22183, v9=17750`.
4. **The arithmetic**: 49,685 occupied-probe visits ≈ **Σ(0..314) = 49,612** — the exact QUADRATIC COLLISION signature: every key probed the same chain from slot 0. Guava's `smear(k) = C2 * rotl(k, 15)`; `rotl(h,15)` has low-15-bits = `h >> 17` = **0 for every integer key < 2^17** → `smear(k) & (tableSize-1) = 0` for ALL of them.
5. Real Android never sees this storm — because the real MobileConfig map is NOT keyed by small placeholder Integers. The keys materialized as boxed AppContext slot-id Integers downstream of the DI lattice.

### ROOT RE-ATTRIBUTION
- **F-NEW-172 → PARTIAL**: the fill-length face is fixed; the spin is an honest consequence of upstream key identity.
- **F-NEW-173 (NEW, OBSERVED-FAIL, P0)**: key-materialization divergence — `07r.A0Q` feeds `Integer(22183)`-style slot ids where the real app map expects richer key objects; same identity family as the F-NEW-171 register-aliasing face (the §3 central hypothesis at the object-identity layer). Next bounded step: trace the `map.put` key feed to the materializing constructor/parameter.

### GATES
laws130 **51/51** after every rebuild · zero regressions (dooz ×3 byte-identical re-verified this session) · registry 465/466 roots · commits pushed (`5daf987f`).

### STATE OF THE WHITE-SCREEN CHAIN (WhatsApp)
`StandardCharsets` statics law (F-NEW-170) → `move-object/16` + register-width law (F-NEW-171) → ImmutableMap build now EXECUTES (deepest ever, pc=0x5662 in `07r.<init>`) → key identity divergence isolated (F-NEW-173). Each wave removes a generic layer; zero app-specific branches. Phases 4-5 (context/fragment-host chain, canonical window stack F-145) queued behind the F-NEW-173 attack."""


def gh_token():
    out = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True, cwd="/home/z/my-project",
    ).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line[len("password="):]
    raise RuntimeError("no token")


def req(url, token, data=None):
    r = urllib.request.Request(url, method="POST" if data else "GET")
    r.add_header("Authorization", f"token {token}")
    r.add_header("Accept", "application/vnd.github+json")
    r.add_header("User-Agent", "miniandroid-campaign")
    body = json.dumps(data).encode() if data else None
    if body:
        r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, body) as resp:
        return json.loads(resp.read().decode())


def main():
    token = gh_token()
    existing = req(f"{API}?per_page=100", token)
    if any(c["body"].split("\n")[0] == HEADER for c in existing):
        print("SKIP (exists)")
        return
    c = req(API, token, {"body": BODY})
    print(f"POSTED: {c['html_url']}")


if __name__ == "__main__":
    main()
