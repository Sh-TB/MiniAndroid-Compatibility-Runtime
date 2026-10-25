#!/usr/bin/env python3
"""CONT-29 W1 — post the wave ledger to issue #387."""
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

BODY = """## CONT-29 / W1 — مشکلش حل شد (F-NEW-520 PriorityQueue) + ریشه‌یابی صادقانه (F-NEW-521) + R-NEW-467 throughput law

**Wave type:** container resync (the remote was **322 commits ahead** — the
stale local head e99c2fbd fast-forwarded to `7f8d639c`, registry 837, dooz
`851cc176` REAL_APP_CONTENT@300s reproduced ×3 byte-identical) + one
repeated-pattern fix + one honest re-classification + one throughput law.
Binary `e4da5315cfd95e46` (deterministic; pre-memo A/B binary preserved).

### مشکلش حل شد — F-NEW-520 PriorityQueue (census crossing)

The class was claimed by **NO shadow**: `iterator()` answered NULL →
`Iterator.hasNext` NPE (DEX-decoded face: wocheneinkauf `Ly7;.a` — the
BreakIterator line-breaking worklist never ran). CollectionShadow now
claims `Ljava/util/PriorityQueue;` with the OpenJDK laws:

- add/offer kind-faithful append; **peek/poll least-element** — int keys
  INCLUDING autoboxed `Integer` (kind-5: the unboxed key comes from the
  heap `value` field; the serve returns the OBJECT faithfully so the
  caller's check-cast stays lawful), all-STRING lexicographic min,
  mixed/app-object FIFO head (**approximation recorded in the law
  comment** — no shadow-side compareTo exists; the bridge is the
  follow-up lever).
- contains unboxes autoboxed-Integer args; iterator() = the generic
  Iterable law in **array order** (OpenJDK: "The Iterator does not
  traverse the elements in any particular order" — faithful, no sorted
  law needed).
- Probe `fixtures/fnew520_probe` (real aapt2/ECJ/D8): **6/6 PASS**.
- **CENSUS CROSSING: wocheneinkauf 0 content px (1 color) → 1356 colors /
  8,579 content px real UI** — batch-20 at this binary = **5/20 content
  rows** (bouncy 72,622 / fossify_math 13,071 / calendar 12,336 EXACT
  sha zero-drift; netguard 27,059 content-retained minor delta).

### ریشه‌یابی — F-NEW-521 register evidence (honest: stays CLASSIFIED)

Raw-byte ground-truth decode (`scripts/w8_hexdump_method.py`; w7_disasm
pcs = code units confirmed). Growth decision: eu 0x84 `iget Lhv0;.f:I`
(threshold) → 0x88 `if-nez` → place path / fall-through deleted-check →
0xaa growth; tail eu 0x277 decrements by (fresh-slot ? 1 : 0);
`Lhv0;.f(I)`: threshold = cap - cap/4 - size (8→6 ✓).

MINIANDROID_PC_WATCH over `Lhv0;.d` {0x84,0x88,0x9c,0xaa} — **194 rows**:
the threshold round-trips PERFECTLY at the branch (v2 6→5→4 on obj#2418)
but every map is **ABANDONED after 2-3 puts** (~97 puts across dozens of
maps, each restarting at 6); the growth region is unreached because **no
map reaches the threshold at this head** — NOT a branch/alias bug. The W7
full-table spin face was the CONT-10-era binary; at CONT-28+ the family
signature burns as **wall-clock halts in the draw window** (HALT-HISTO:
39× Lt4;.dispatchDraw, wide walks visits=1, zero tight loops) = the
**F-NEW-381 throughput wall**. Root stays CLASSIFIED (P0 latent); the
probe stays honestly PENDING (the synthetic trigger needs the dooz APK's
own DEX classes and cannot be source-built).

### R-NEW-467 — field-resolution memoization (throughput law, P0)

MINIANDROID_PERF_PHASES: `iget-object` 2.29M calls = the #1 burn opcode
(~1.9µs each — fresh DEX re-parse + declarer chain walk + string concat
**per access**). Fix: `resolve_field` memo fast path + FieldMemo bank
(res + S134 declarer/fkey); the four hot field ops route through
`resolved_field_memo`; epoch = dex_index ^ super-table ^ class-info sizes
(any mid-run hierarchy growth invalidates once).

- **Semantic trap caught by the first A/B**: res-only bank entries
  (s134_valid=false, empty fkey) leaked through the hit condition →
  every access keyed with an EMPTY string → dooz anchor 851cc176 →
  d602648e collapse. Fixed (hit requires resolved AND s134_valid).
- Perf: iget-object **-30.6%**, iget **-30.5%**, iget-wide -26.9%,
  iput-object -22.2% (top-12 burn **-10.5%**).
- snakeneon attribution: 2617c81c deterministic ×3 **identical on both
  A/B arms** (pre-memo vs post-memo binaries) — not the memo; the
  recorded b669ce89 was the CONT-28-container face; real-content verdict
  unchanged.

### Regression wall (binary e4da5315)

dooz `851cc176` ×3 byte-identical; anchors 6/6 pinned faces (opencalc
63020bc7 / chess 3f7e6707 / microtimer bbd350b6 / unote 7481e9b4 /
tower3d 11a38a5a / dooz 851cc176); negatives **19/19** (after
run/gatea/probe_store regeneration — the 9/19 was the CONT-158
stale-store artifact, not a regression); skill selftest 13/13; user
goldens 4/4; games battery 6/7 EXACT sha + snakeneon A/B-neutral.

### Next (registered)
The heap field-map representation (the next F-NEW-381 structural lever —
string-keyed maps per object), the shadow→DEX compareTo bridge (PQ
ordering completion), the 14 named census faces' first-dives, and the
Telegram-specific trains per the standing 10-20 allocation. Registry
837→838 id-unique. Evidence: `evidence/cont29/CONT29_W1_LEDGER.md`.
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
