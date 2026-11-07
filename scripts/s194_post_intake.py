#!/usr/bin/env python3
"""S194: post the integration-of-coder-achievements record to issue #556."""
import json, subprocess

TOKEN = subprocess.run(
    ["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
    capture_output=True, text=True).stdout
TOKEN = [l.split("=", 1)[1] for l in TOKEN.splitlines()
         if l.startswith("password=")][0]
API = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"

body = """## S194 INTAKE — the FULL contributor stack is now integrated onto the W12 maintainer line (all `git apply` CLEAN; W2 goldens ALL HOLD; battery 11/11 CLEAN on the integrated binary)

Directive frame (user): «ادامه بده … قرار شد دستاورد های کدر ها رو هم بررسی بکن» — the #556 pattern (connecting and USING the coder achievements) executed: the maintainer's W9–W12 line (25 unpushed commits pushed: `d3a8d0ec..cbc9058e`) adopted the published §8 patches and re-verified end to end.

### 1. The maintainer-line push (was missing from origin)
- **25 commits pushed** `d3a8d0ec..cbc9058e`: W9 (F-NEW-588/589 — the five-thread stall attributed+fixed, the real-GL lane, queens CLEAN EXIT + Impeller ACCEPTED), W10 (F-NEW-590..594 env census + RunBundle fault classes; F-NEW-595 measure opt-in), W11 (the impact back-review), W12 (F-NEW-596 the arena/interner lifetime contract — the RunBundle bad_alloc ROOT-CAUSED as an arena_clear UAF on interned ids/class tokens; F-NEW-598 the S109 FrameLayout AOSP resolve law — the height-split COMPLETED; measure law default-ON battery-verified; blackjack first CLEAN EXIT with a real B face).
- Plus the tracker comments for W8–W12 posted to this issue (#556) — the record was 16h behind the work.

### 2. The contributor patches — fetched from the §8 publications, applied on `cbc9058e`
| set | source | apply check | content |
|---|---|---|---|
| CODER 8 waves-8+9 CUMULATIVE | #519 (5 parts) | **CLEAN (rc=0)** on the maintainer line | defects 141–180 |
| CODER 8 wave-10 | #519 (2 parts) | CLEAN after waves-8+9 (dependency-ordered) | defects 181–200 |
| CODER 3 S191 gmdice stack | #561 | **CLEAN (rc=0)** | the ListActivity/ArrayAdapter stack (+469 ins) |
| CODER 4 W15 laws | #562 (4 parts) | **CLEAN (rc=0)** with MID-WORD concat (the S192-KT recipe honored) | F-C4-616/617/618 + re-land |
| CODER 3 S189/A24 | #557 | **NO ACTION** (per the Phase-D matrix: F-NEW-588/589/590 already in the maintainer W9/W10 line; the evidence hunks were truncated in publication — code hunks already integrated) | — |

Publication repairs applied during intake (all recorded in evidence/s194_intake): fence extraction across part boundaries, PART N/N marker strips, truncated-evidence-hunk count rewrites (CODER-3 recipe, code hunks untouched), mid-word concatenation for W15 (no newline between the 60,000-char parts).

### 3. The Future.isDone owner decision (CODER 3's §2 gate)
The S192-KT verdict stands: both isDone bridges kept **sequential** (F-NEW-590 in the maintainer line + the C8 wave block) — one handler answers per dispatch order, no double-dispatch; recorded per the proposed (NAME, owner, wave, SHA) ledger.

### 4. Integration gates on the ONE binary (`dae43220cd9d0c1a`)
- **W2 goldens ALL HOLD**: bouncy `8a6c24ac` + unote `3b8dcb0a` + dooz `31ddd4d5` byte-exact on the integrated binary.
- **Battery 11/11 CLEAN — ZERO tier drops** vs the W2/W10 floor; no.thanks holds its C_TEXT_ON_FLAT advance (a maintainer-line W12 result).
- Route matrix 11/11, ROUTE_VIOLATION=0.

### 5. Honest scope
- The five-title byte-exact cohort reproduction (microtimer `f82743fe…` / opencalc `479382e1…` / gmdice `3891679d…` / pf2048 `eb5ebd55…` / dooz `a0fae907…` — the S193-KT pins) is the named next gate: 4 of the 5 cohort APKs are not present in this container yet. Note: this line's dooz golden is the W1-stable `31ddd4d5` (the two integration lineages have divergent dooz pins — both recorded, neither weakened).
- Next: the cohort APK intake → the five-title battery on `dae43220…` → then the remaining walls (the androidx FragmentManager.dispatchStateChange face → GodotLib.initialize; the ts APP_DRAW_OPS paint).

Cross-refs: #556 (this issue — the pattern), #519, #557, #561, #562. Evidence: `evidence/s194_intake/S194_INTAKE.json` + `patches/` (commit `5119a933`, pushed).
"""

r = subprocess.run(
    ["curl", "-s", "-X", "POST", "-H", f"Authorization: token {TOKEN}",
     "-H", "Content-Type: application/json", "-d", json.dumps({"body": body}),
     f"{API}/issues/556/comments"], capture_output=True, text=True, timeout=60)
resp = json.loads(r.stdout)
print('posted:', resp.get('html_url', resp))
