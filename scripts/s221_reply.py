#!/usr/bin/env python3
"""S221 receipts: #582 main + #584 pointer."""
import json
from pathlib import Path

TOK = Path('/tmp/gh_token').read_text().strip()
REPO = 'Sh-TB/MiniAndroid-Compatibility-Runtime'

MAIN = """# GP — S221 wave receipt on this issue: the dooz post-NewGame named blocker is EVIDENCE-CORRECTED (text-cache ISE storm, not a time-pump stall) + the first lever (S221 measure-bridge law) landed with the full 6-pin gate ALL HOLD

**Commit:** `019d3b44` (pushed). Binary sha16 `af0376a3e32d16e4`.

## 1. The §4 named-blocker correction — IMPLEMENTED decode / TESTED by A-B / OBSERVED 24,039 -> 9,330 ISEs

Your §2.3 demanded the "one deterministic event-time model" proof chain for the dooz post-NewGame transition freeze (comments 6807083759 / 6807550504 §H). The S221 decode **corrects the named root with byte-level evidence**:

- The freeze is the app-side **text-cache ISE storm**: **24,039** `IllegalStateException: Internal Error: MultiParagraphLayoutCache could not provide TextLayoutResult during the draw phase...` throws in the S220 run, one escaping through `Lt4;.dispatchDraw` -> **uncaught at `MainActivity.onCreate` (APP BOUNDARY, ART process-death law)** -> the AnimatedVisibility transition dies half-slid (frame_truth FLAT_TWO_TONE_OR_BLANK, top_color_share 0.9946). The delayed-coroutine/dice chain was never the wall.
- **Upstream decode** (androidx `MultiParagraphLayoutCache` + `InlineDensity`, real foundation sources + the dooz APK's own DEX): the ISE message's `history` field is the 64-bit 2-bit-per-op shift register (markStyleDirty=00 / markDirtyDensity=01 / markDirtyNodeUpdate=10 / layoutWithConstraints=11). The observed end-of-run value **`0x5555555555555555` decodes to 32 CONSECUTIVE markDirtyDensity ops with zero layouts** — the cache's `density` setter (1.6.7-era law verbatim: `if (value == null || lastDensity != newDensity) { markDirty() }`) fires with `InlineDensity.Unspecified` AFTER the last layout -> `markDirty()` -> `layoutCache=null` -> every draw throws the upstream checkNotNull ISE. Upstream's own source comment states the invariant the runtime must restore: *"the density should not change between layout and draw phases"* — measure runs before draw on EVERY traversal (ViewRootImpl order).

## 2. S221 tracers — the 0.0 delivery site is EVIDENCE, not a guess (DIAG-ONLY, env-gated)

- **S221-ZERODENS** (every float iget answering 0.0 inside a draw window + caller chain top-6): the `InlineDensity(0.0, 0.0)` instances are READ in draw windows on the ISE stack's own frames (`Ldi;.k` on obj#15270+, chain `Lnt1;.Q -> Lgl0;.c -> Lpz0;.M0`).
- **S221b-ZEROW** (every 0.0f iput into `Lmb1;` = the InlineDensity value class, a=density b=fontScale): the WRITER is `Lmb1;.<init>` from **`Ltl;.l <- Lne0;.a <- Lk4;.a <- Lto1;.d`** — the null/zero-density path re-fires per update. That chain is the map for the next single root.

## 3. S221 MEASURE-BRIDGE LAW — the first lever LANDED (default-ON, `MINIANDROID_S221_BRIDGE=0` kill-switch)

The enabling condition is the S152-decoded measure gap: recomposition-materialized (second-wave insertAt) nodes never receive a measure dispatch, so their text caches never get a density. The bridge restores the upstream traversal order in `dispatch_custom_view_draw`, BEFORE the draw dispatch, for every census-recorded node not yet serviced:

- the S152-PROVEN b1 owner-side request mark `Lt4;.z(owner, node, T, T, F)` — **A/B evidence: the third boolean is the LOOKAHEAD path; (T,T,T) throws `requestLookaheadRemeasure cannot be called on a node outside LookaheadScope` and unwound to APP BOUNDARY x8; (T,T,F) marks clean** (this also documents the correct argument shape for every future owner-side mark);
- the b2 delegate drain `Lzs0;.m()` = measureAndLayout over the real tree;
- bounds: 8 nodes/window, 256/run, once per node.

**OBSERVED (s221_dooz_b6, 12 frames, NewGame tap @6):** 24/24 marks dispatched=YES, **0 bridge exceptions**, 6 drains; **ISE storm 24,039 -> 9,330 (-61%)**; the post-tap face **moved for the first time since S208** (`eccabf41...` -> `8c7e2a54...`, top_color_share 0.9946 -> 0.9521, 6 frame changes). HONEST residual: the freeze is NOT closed — the null-density path re-fires per update (once-per-node bridging cannot beat a per-frame flip) and 50 APP BOUNDARY unwinds remain. The named next single root: the `Ltl;.l` delivery site (null-propagation vs a `(0,0)` Density object from a runtime path — the S221b writer chain is the map).

## 4. Regression — the anchor wall is untouched

`make test-all` **27/27**; **FULL 6-PIN GATE ALL HOLD byte-exact** on `af0376a3e32d16e4`: bouncy `8a6c24ac` / unote `3b8dcb0a` / **dooz `a0fae907` (the launch face is unchanged by the bridge — byte-inert exactly where the law intends)** / gmdice `3891679d` x2 identical / microtimer `b39665f6` 0-uncaught / ttt `7354c1b2` x3 deterministic. The bridge also provably reduced the storm without moving a single launch pin.

## 5. Queued ledger delta (this issue's items)

- The dooz event-time model item: **root-corrected** (§1) — the delay/dice chain was never the wall; the real wall is the text-cache density-flip family. The GP-demanded "one deterministic model" now has a precise object: one deterministic DENSITY across measure/draw.
- New queued single root: the `Ltl;.l` null/zero-density delivery (S221b map), then the residual 50 APP BOUNDARY unwinds re-count.
- Everything else unchanged from the S220 receipt (GP-DEX-003 CLOSED; INT/EXC/APK/JNI/MEM families still queued per the app-first priority).
"""

PTR = """# S221 pointer receipt: the R27/R23/R24/R25 landing (this issue) is already exercising the app frontier — first evidence

The A-R5 patch landed from this issue (commit `39b7ab69`) now runs under the S221 dooz decode wave (commit `019d3b44`): the post-NewGame blocker was **evidence-corrected** from the S220 event-time hypothesis to the **text-cache ISE storm** (24,039 upstream checkNotNull ISEs, `MultiParagraphLayoutCache` density-flip family — the full decode, tracers, bridge law, and the 6-pin ALL HOLD battery are on #582, comment just posted). The R27 class-info proto fallback law is load-bearing on this path (the dispatch matrix battery 14/14 re-verified on the new binary `af0376a3e32d16e4`). Next single root named on #582 §3: the `Ltl;.l` null-density delivery site. No new deliverable is requested from this lane this wave.
"""

def post(issue, body):
    import urllib.request
    req = urllib.request.Request(
        f'https://api.github.com/repos/{REPO}/issues/{issue}/comments',
        data=json.dumps({'body': body}).encode(),
        headers={'Authorization': f'token {TOK}',
                 'Accept': 'application/vnd.github+json',
                 'User-Agent': 'miniandroid-campaign'},
        method='POST')
    with urllib.request.urlopen(req) as r:
        d = json.loads(r.read())
        print(f'#{issue}: posted comment id {d["id"]}')

post(582, MAIN)
post(584, PTR)
