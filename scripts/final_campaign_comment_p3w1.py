#!/usr/bin/env python3
"""FINAL CAMPAIGN — post Phase 1/2/3-wave-1 progress comment to issue #354."""
import json
import subprocess
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
API = f"https://api.github.com/repos/{REPO}/issues/354/comments"
HEADER = "## FINAL CAMPAIGN — Phases 2-3 wave 1: field identity closed + THREE generic roots fixed on the WhatsApp white-screen chain"

BODY = HEADER + """

Commits `12cea554` (Phase 2), `f0f0fd05`+`192e1a42` (Phase 3 wave 1).

### PHASE 2 — FIELD IDENTITY CLOSED (canonical table: `docs/FIELD_IDENTITY.md`)
- **Two real divergences found and fixed** (mission property audit, not a paper audit):
  1. reflection `Field.get/set` used **bare names only** — a reflection `Field.set` wrote a slot the interpreter's F-NEW-160 qualified read could never see (silent-wrong, Constitution §17). Fixed: reflection now uses the SAME identity law (qualified primary for DEX-defined declarers, dual-write on set).
  2. all 14 `sun.misc.Unsafe` get/put/CAS variants addressed storage by **bare name** from the offset registry — same silent-wrong class for the atomicfu volatile-state path. Fixed at a single edit point (`field_name_for337` now returns the identity key).
- 10-property checklist proven in the doc (declarer resolution, no cross-class aliasing, framework-shadow bare interop preserved, initializer defaults, goldens byte-identical).
- Golden label correction: the recorded `simplestopwatch_26` golden (e00fe7e0) ≠ `com.github.muellerma.stopwatch_6` (which deterministically renders `eb16ab5c` ×3 — its own frame; the wave-6 worklog line conflated labels).

### PHASE 3 WAVE 1 — the WhatsApp white-screen chain, three roots (every fix generic, ZERO package checks)

**Frame truth first:** WhatsApp AND stopwatch_6 produce **byte-identical** screenshots (`eb16ab5c…`): 2 colors, 98.87% white, 23,472 non-white px — pixel forensics shows ALL non-white pixels are rows y=0..44 = **the 45px status-bar band**. The S134-wave "REAL_APP_CONTENT 23472px" verdict was a **false positive** (framework chrome counted as app content). WhatsApp is still in the white-screen family; verdict-law fix queued (Phase 7/16).

**Root 1 — F-NEW-170 `StandardCharsets` platform-constant law (ROOT-CAUSED-FIXED):**
bounded first-divergence trace (`--trace` + crash log correlation, log lines 988-997): `08C.<clinit>` → `08D.<clinit>` → **`sget StandardCharsets.UTF_8` → SGET-MISS → null** → `Charset.name()` NPE → `08C.<clinit>` unwound leaving its static `Set` fields unwritten → `00S.A03` read the null Set → `Set.contains` NPE → `Main.onCreate` pc=34 (caught) → pc=1470 (fatal). FIX: sget platform-constant arm materializes the six JDK charset constants under the same heap identity as `Charset.forName`. Residual recorded: clinit-failure honesty (CLASS_INIT records OK despite unwind; ART EIIIE law) = own wave.

**Root 2 — F-NEW-171 DEX register-width law (ROOT-CAUSED-FIXED, three faces one root):**
- opcode **0x09 `move-object/16` had NO interpreter case** — the default UNIMPLEMENTED arm skipped 1 unit instead of 3 → pc desync → garbage decode → "invoke 00D.<init> on null" inside `07r.<init>`. Implemented per DEX spec (32x, 3 units).
- the new `[IGET-MISS-DIAG]` probe caught the smoking gun: `asked=ImmutableMap$Builder->size obj#21003 cls=Ljava/lang/Integer` — **the receiver of `Builder.put` was a boxed Integer**. Cause: `DexRegisterFile` accessors were `uint8_t` — `/16` formats (emitted exactly when R8 needs >255 registers) truncated v256+ onto v0.. = live-register aliasing. Widened read_v/write_v/get_register/set_register/set_wide_pair to uint16_t; written_bits_ 4→16 words.
- `write_p` computed the absolute register as `uint8_t(param_start_ + idx)` — for >255-register methods **arguments including `this` landed in wrong registers**. Arithmetic widened to uint32.

**Result:** the `00D.<init>`-on-null chain is GONE; WhatsApp now executes DEEPEST EVER — `07r.<init>` to pc=0x5662, `ImmutableMap$Builder.put/ensureCapacity/build` + `RegularImmutableMap.create` all reached (the DI lattice from F-NEW-169 is genuinely being filled now).

**New frontier — F-NEW-172 (OBSERVED-FAIL, registered):** `RegularImmutableMap.createHashTable` hash-probe loop spins >50001 visits → F084 halt (guava is O(tableSize) — never spins on ART). Bounded disassembly investigation queued.

### GATES (Phase 3 wave 1)
laws130 **51/51** · dooz `ba8a95eb2278594f` ×3 **byte-identical** · stopwatch_6 `eb16ab5c68fa9b6c` ×3 deterministic · zero regressions. Registry 461→**465** roots. Also: hygiene follow-up — a WhatsApp run-scratch file leaked into `f0f0fd05` and was immediately untracked (`192e1a42`); `.gitignore` extended for tmp run dirs.

### NEXT
F-NEW-172 attack (createHashTable probe semantics) → then Phases 4-5 (context/fragment-host chain, canonical window stack)."""


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
