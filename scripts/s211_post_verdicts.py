#!/usr/bin/env python3
"""S211 — post verdicts: dooz Segment-state forensics deep-dive (marker-slot
handouts + capacity-growth protocol + engine-primitive verification) and the
regression gate on the diag-patched binary."""
import json, subprocess
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
LEDGER = Path('/home/z/my-project/evidence/s200/posted_comment_ids.json')
ledger = json.loads(LEDGER.read_text())

def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True,
                         cwd="/home/z/my-project").stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""

def post(issue, body, key):
    if key in ledger:
        print(f"SKIP {key} (already posted: {ledger[key]})")
        return None
    tok = token()
    r = subprocess.run(["curl", "-s", "-m", "60", "-X", "POST",
                        "-H", f"Authorization: token {tok}",
                        "-H", "Accept: application/vnd.github+json",
                        f"https://api.github.com/repos/{REPO}/issues/{issue}/comments",
                        "-d", json.dumps({"body": body})],
                       capture_output=True, text=True)
    resp = json.loads(r.stdout)
    cid = resp.get("id")
    if cid:
        ledger[key] = cid
        LEDGER.write_text(json.dumps(ledger, indent=1))
        print(f"POSTED #{issue} comment id={cid} key={key}")
    else:
        print(f"FAILED #{issue}: {r.stdout[:300]}")
    return cid

L09B = """# [S211 VERDICT · L-09 follow-up] dooz Segment forensics deep-dive — the corrupted objects decoded (capacity-growth protocol live-traced), engine primitives ALL verified correct, divergence narrowed to the scan-claim state interleaving; gate: ALL pins HOLD on the diag-patched binary

Binary: diag-patched (`40db2fc5f200f0db` — two env-gated probes added, **all pins byte-exact HOLD**: bouncy `8a6c24ac` / unote `3b8dcb0a` / dooz no-tap `a0fae907` / gmdice `3891679d` rerun-identical / microtimer `b39665f6` / ttt det `7354c1b2`) · APK `299eab21ac8b3c61`.

## 1. The corrupted objects fully decoded

`Lbw0;` = the kotlinx.coroutines Segment/slot-queue family: fields `a:[J` (packed state words), `b:[Ljava/lang/Object;` (slot table), `c:I` (capacity mask), `d:I` (claimed counter), `e:I` (remaining). Initializer `.f(I)V`: `c = max(7, cap)`; state words = `((cap+15) & -8) >> 3` longs; slots = `new Object[max(7,cap)]`; **a marker byte (0xFF) is pre-claimed at slot index `cap`** (the terminator — slot `cap` must never be handed out). The claim chain: `.a(Object)Z` = the inlined-CAS try-store (`slot = .d(arg); b[slot]=v; return d==expected`), `.d(Object)I` = claim (two scan paths: the `numberOfTrailingZeros` word scan returning at `0x6b`, and the `.e`-scanner path returning at `0x292`), `.e(I)I` = the free-slot scan (cross-word stitch + `(~w<<7)&w&MAGIC` free-pattern + `Long.numberOfTrailingZeros/8`, masked `(start+slot)&c`).

**Live capacity-growth traced** (`[S211-IPUT]` probe, writer = `.f pc=14`): `obj#2901: c 7→15→31→63`, `obj#2946: 7→15→31→63` — the app's own doubling protocol runs on the same segment object; masks at scan time always read correct (7/31/63 per object, `[S211-IGET]` trace).

## 2. The corruption signature (deterministic, cross-run)

- **Marker-slot handouts**: `.d` returns slot **7** for a 7-slot table (`o15059`) — repeatedly, from callers `.k`/`.l`/`.d` — exactly the pre-claimed terminator index.
- **Unbounded garbage slots**: `797218574` (→ word idx `99652321` = the pc=618 aget-wide OOB), `984783757`, `993147359`, `1458633404`, `123097969`, `-1329363308` — byte-stable per object across 4 independent runs.
- Register dumps at the OOB instants (`MINIANDROID_LOOP_LOCALS_DIAG`, new AGET-OOB hook) captured the segment state: state words `0xFF80000000000000` / `0xFF80...` (marker byte set + partial claims), `c=7 d=1 e=5`, one slot of `b` holding a typed-INT `i=0` (a reference slot containing a raw INT32 value — secondary type-confusion witness).

## 3. Engine primitives — every link verified this cycle (the honest-negative list)

`and-int/and-long` (`b&c` direct) ✓ · long shifts mask `&0x3f` / int shifts `&0x1f` ✓ (no UB-shift path) · `const-wide` (51l, 4×16-bit LE, wide-pair) ✓ · `Long.numberOfTrailingZeros` (64-for-0 law, S102) ✓ · `Math.max` ✓ · `Lmg1;` = pure index math (NOT a CAS engine — self-correction from the previous hypothesis) · the CAS is **inline DEX** (atomicfu-inlined retry loops — no framework atomic in the Segment chain) ✓ · iget missing-field → typed zero default ✓ · iget/aput/aput-null NPE laws ✓ · aget/aput OOB confirmed-length laws ✓.

Conclusion: no single primitive is wrong — **the divergence is in the scan-claim state INTERLEAVING**: the post-navigation recomposition drives concurrent claim/retry sequences whose state-word interleavings our engine produces differently from ART (the re-entrancy points of the frame pump vs the app's suspension points), yielding marker-slot and overflow-slot handouts the ART schedule never reaches.

## 4. Next probe (queued, concrete)

Log at `.d`'s two return sites (`0x6b`, `0x292`) + `.e`'s return: `(recv-obj, start, tz, mask, slot)` tuples for Lbw0; — with the state words `(a[0], a[1])` at entry — bounded to post-tap. That pins whether the garbage slot escapes the mask read (a stale-c window during the 7→15→31→63 resize) or the scan's free-pattern on the ART-divergent state bits.

## 5. Statuses

Segment decode + growth protocol = TESTED (static + live trace) · marker-slot/unbounded handouts = OBSERVED (deterministic, 4 runs) · engine primitives = VERIFIED correct (7 checks) · dooz board render = BLOCKED at the scan-claim interleaving (next probe queued) · baseline = HOLD (all pins, diag-patched binary, gate JSON updated) · Main = unchanged (evidence-only commit follows)."""
CENTRAL2 = """# [S211 CENTRAL RECORD] — dooz Segment forensics deep-dive + gate re-proof

- **#557 L-09 follow-up**: the corrupted kotlinx Segment objects fully decoded (`a:[J` state words / `b` slot table / `c` capacity mask / marker-byte terminator); live capacity-growth traced (`c 7→15→31→63` on one object); corruption = marker-slot(7) handouts + deterministic unbounded slots (byte-stable across 4 runs); register dumps captured at OOB instants.
- **Engine primitives verified (7/7)**: int/long arithmetic+shifts (masked), const-wide, `Long.numberOfTrailingZeros` (64-for-0), `Math.max`, missing-field typed-zero defaults, null-receiver laws, OOB confirmed-length laws. No primitive wrong → divergence = scan-claim state interleaving under the engine's re-entrancy schedule (frame pump vs suspension points).
- **Self-correction**: `Lmg1;` is an index helper, not a CAS engine; the Segment CAS is inline DEX (atomicfu-inlined retry loops).
- **Gate**: ALL pins byte-exact HOLD on the diag-patched binary `40db2fc5f200f0db` (two env-gated probes; behavior-neutral by design, re-proven by the gate).
- **Next**: return-site probe at `.d 0x6b/0x292` + `.e` (`recv, start, tz, mask, slot` + state words) → then the smallest generic correction.
- W21 part 17/17: still missing (unchanged)."""
post(557, L09B, "557_s211_l09_segment_forensics")
post(536, CENTRAL2, "536_s211_central")
