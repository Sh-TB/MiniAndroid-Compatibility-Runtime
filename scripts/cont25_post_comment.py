#!/usr/bin/env python3
"""cont25_post_comment.py — post the PHASE-1 checklist closeout comment to Issue #384."""
import json, os, subprocess, sys
from urllib.request import Request, urlopen

TOKEN = subprocess.run(
    ["bash", "-c",
     "git credential fill <<< $'protocol=https\\nhost=github.com\\n' 2>/dev/null | grep password | cut -d= -f2"],
    capture_output=True, text=True, cwd="/home/z/my-project").stdout.strip()
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
ISSUE = 384

body = """# CONT-25 / PHASE 1 wave report — the real-Compose root tested against the white-screen corpus (one generic fix landed; composition progress honestly still NO)

**Workflow:** READ LOCAL SOURCE → READ AUTHORITATIVE UPSTREAM SOURCE (Recomposer.kt 1.11.4 / AndroidUiDispatcher.android.kt / GlobalSnapshotManager.android.kt / NavHost.kt 2.9.8 / AOSP MessageQueue.next) → STATE SEMANTIC LAW → IDENTIFY LOCAL DIVERGENCE → CHECK ROOT REGISTRY (F-277 REUSED, zero new roots) → MINIMAL GENERIC FIX → RUNTIME PROOF → CROSS-FAMILY REGRESSION.

## ROOT VERDICT

The "Composer / slot-tracking" wording from the external probe is **NOT proven** — corrected: the Composer is **healthy** (slot ops execute: Lrn1 ×10366, composition #1 legal end-to-end; measure ×9 with zero exceptions; place-writers execute; draw walk descends). The first divergence is the **scheduler**: **F-NEW-277 recomposition starvation at the frame-pump quiescence boundary** — `pump_compose_frames` treated "nothing due NOW" as quiescence, stranding future-due dispatcher work, so the Recomposer runner never wakes and composition #2 (the one that inserts the navigation destination content) never starts.

## COMPOSE TARGETS

| target | first divergence | pre-Composer? |
|---|---|---|
| dooz 1.0.23 | F-277 (scheduler) — reaches Composer | no |
| itsfrz 1.0.5 (control B) | `FragmentContainerView.<init>` fm=null NPE → APP-BOUNDARY | **YES** |
| droidify 0.7.7 (control C) | `DelayKt.runBlocking` HALT-LOOP → F084 VirtualMachineError → APP-BOUNDARY | **YES** |

Rejected with evidence: rttt (ARM-only SDL native = environment blocker), PF Dicer + Antimine (0 compose strings — not Compose).

## FIX (one law, +34 lines, zero app/package checks)

**F-NEW-277 poll-timeout parity** in `pump_compose_frames`: quiescence is an EMPTY queue, not a future-dated head (AOSP `MessageQueue.next` law — the engine's own `drain_quiescent`/FINDING-009 already states it; the compose pump predates it). Scoped to `fired_frames > 0` (the S135 COMPOSE renderer-family signal) — apps that never post a frame callback keep the F-115b frozen launch-frame law byte-exactly.

## HONEST RESULT

`[F277-POLL]` fires on dooz and the stranded 16ms strand now RUNS — but **composition still does not progress**: the runner's wake-up work is not in the handler queue (only 13 trampoline tasks in the whole 15 s run). **NEXT FIRST DIVERGENCE: the invalidation-delivery chain** (produceState/LaunchedEffect collect dispatch / StateFlow first-emit / GlobalSnapshotManager channel monitor never materializes as queue work). The right instrument: the un-renamed real-Compose oracle (CONT-12 dexes survive; needs the aapt2 link re-run). **Real app-owned pixels: NO — nothing is claimed as fixed.**

Patch binary `e980887e39aee977`; patch pushed as 963da9c3; full evidence `evidence/cont25/COMPOSE_ROOT_TEST.md`.

## CHECKLIST (§18, line-by-line)

```text
[x] Current HEAD verified — TESTED — 05f6d162 == origin/main (fetched); after commit 963da9c3 == origin/main
[x] Current baseline binary verified — TESTED — rebuilt BYTE-EXACT fa88902fdee6e982 (CONT-22/23/24 lineage)
[x] Issue #383 read — OBSERVED — BASE-FIRST plan + upstream-source-first amendment comment
[x] Issue #384 read — OBSERVED — ARCH-001 + CONT-21/22/23 wave reports
[x] Issue #385 read — OBSERVED — skeleton-light hazards (verdict inflation, Surface/GL destruction) honored: skeleton stayed OFF
[x] Existing Compose roots audited — OBSERVED — registry 586 rows; F-NEW-277 CLASSIFIED P0, F-266/271 ROOT-CAUSED-FIXED
[x] Real Compose probe reproduced — OBSERVED — CONT-12 oracle artifacts located (tmp/cont12_oracle_build/dex); rebuild recorded as next-wave opening probe
[x] Dooz baseline captured — TESTED — rc=1, d602648e8e401895, DEFAULT_BACKGROUND_ONLY, 0 uncaught, 0 app draw ops (run/cont25/base_dooz)
[x] Independent Compose target B baseline captured — TESTED — itsfrz d55056a8 x3, fm=null NPE pre-Composer (run/cont25/base_itsfrz)
[x] Independent Compose target C baseline captured — TESTED — droidify b5a7a35d x3, runBlocking HALT pre-Composer (run/cont25/base_droidify)
[x] First Composer divergence identified — OBSERVED — NOT slot tracking; F-277 scheduler starvation (tick-3 quiescence; no Lj9 re-post; runner asleep on workContinuation)
[x] Upstream Compose source read — OBSERVED — Recomposer.kt awaitWorkAvailable/hasSchedulingWork/onNewFrameAwaiter; AndroidUiDispatcher whichever-first + toRunOnFrame.isEmpty removal law; GlobalSnapshotManager channel law; NavHost visibleEntries gate; MessageQueue.next poll law
[x] MiniAndroid semantic mismatch identified — OBSERVED — pump_compose_frames `!did_work → break` contradicts FINDING-009 (internal parity gap)
[x] Existing root duplicate check completed — OBSERVED — F-277 REUSED; itsfrz attached to R-NEW-331 family; droidify attached to R-NEW-345 residual arm; ZERO new roots
[x] Minimal generic fix implemented — IMPLEMENTED — poll-timeout parity, +34 lines, forbidden-pattern grep audit clean (matches are comments only)
[x] Dooz rerun — TESTED — [F277-POLL] fires; 16ms strand runs; d602648e unchanged (run/cont25/fix_dooz)
[x] Compose B rerun — TESTED — unchanged d55056a8 (fix inert: fired_frames=0 — scope-guard proof)
[x] Compose C rerun — TESTED — unchanged b5a7a35d (fix inert — scope-guard proof)
[ ] Real draw proven — NOT ACHIEVED — composition #2 still never runs; honest NO (evidence/cont25/COMPOSE_ROOT_TEST.md §5)
[ ] Framework chrome excluded — OBSERVED — verdict law held (DEFAULT_BACKGROUND_ONLY); no chrome counted as content
[ ] Skeleton pixels excluded — OBSERVED — skeleton-light untouched, default OFF, branch-only (never merged)
[ ] Meaningful pixels proven — NOT ACHIEVED — 1-color frames on all three Compose targets
[x] Screenshot SHA recorded — TESTED — dooz d602648e/itsfrz d55056a8/droidify b5a7a35d (+metrics: colors=1 each, nondom=0)
[x] 3-run proof completed — TESTED — dooz x3, itsfrz x3, droidify x3, all byte-deterministic
[x] View negative control passed — TESTED — opencalc a976d2f9 x3, gmdice f3b483fe x3 (in 18/18)
[x] Canvas/game negative control passed — TESTED — tictactoe b5a7a35d == baseline; tictactoedeluxe af609429 x3; g2048 59ca1526
[x] Surface/GL negative control passed — TESTED — flappycow rc=0, 13cf4746, 507 colors, byte-identical to baseline binary
[x] No package-specific logic — OBSERVED — grep audit: only comments mention dooz; `fired_frames>0` is the S135 family signal
[x] No exception suppression — OBSERVED — diff contains no catch/suppress changes
[x] No fake object — OBSERVED — no heap fabrication in the diff
[x] No forced PC advancement — OBSERVED — diff touches only the pump's clock/quiescence law
[x] Root registry updated/reused — IMPLEMENTED — scripts/cont25_registry.py: F-277 + R-NEW-331 + R-NEW-345 evidence extended; 586 rows, zero new roots
[x] Evidence artifact committed — TESTED — evidence/cont25/COMPOSE_ROOT_TEST.md @ 963da9c3
[x] Current HEAD verified after commit — TESTED — 963da9c3 == origin/main (push verified)
```

**Classification rule:** every line above carries TESTED / OBSERVED / IMPLEMENTED / NOT ACHIEVED — the four `NOT ACHIEVED` lines are the honest core of this report: the divergence moved one link deeper; no visual claim is made.

## NEXT WAVE OWNS

1. Rebuild the un-renamed real-Compose oracle (aapt2 link re-run over surviving CONT-12 artifacts) → trace `GlobalSnapshotManager.ensureStarted` / `LaunchedEffectImpl.onRemembered` / `StateFlowImpl.collect` by real name → pin the invalidation-delivery link (L1 effect-dispatch vs L2 StateFlow first-emit vs L3 channel monitor).
2. Land the delivery-arm fix with the same source-first workflow.
3. Fragment-host law (itsfrz) and runBlocking event-loop law (droidify) as separate generic roots — each unlocks one more Compose corpus control for the fanout proof.
"""

data = json.dumps({"body": body}).encode()
req = Request(f"https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments",
              data=data, method="POST",
              headers={"Authorization": f"token {TOKEN}",
                       "Content-Type": "application/json",
                       "User-Agent": "miniandroid-cont25"})
with urlopen(req) as resp:
    out = json.load(resp)
    print("comment posted:", out.get("html_url"))
