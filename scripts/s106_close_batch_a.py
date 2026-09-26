#!/usr/bin/env python3
"""S106 Batch A — close root tickets #347 #349 #350 #352 with fresh
HEAD-176710b1 evidence (3-run semantic invariants + commit SHAs)."""
import json, os, sys, urllib.request

TOKEN = os.environ["GH_TOKEN"]
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

def api(path, data=None, method=None):
    url = f"https://api.github.com/repos/{REPO}/{path}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method or ("POST" if body else "GET"))
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(req) as r:
        txt = r.read().decode()
        return json.loads(txt) if txt else None

CLOSURES = {
    352: {
        "reason": "completed",
        "comment": """## CLOSED — root executed to L5, fresh evidence at HEAD `176710b1` (S105 ROOT-010 / S106 re-verification)

**Ticket symptom:** `F084 interpreter halt` — infinite loop at PC=0x8d in `CoroutineScheduler$Worker.tryPark` (visited 50001x) because `LockSupport.park` had no blocking semantics (answered void, worker spun park→scan→park).

**Root cause (deeper than the ticket's proposal — evidence-first):** the park bridge destroyed the *enclosing drain depth* before its quiescence check read it. The engine already had PARK-DRAIN machinery (R-NEW-345), but `LockSupport.park`'s synchronous queue drain restored `park_drain_last_depth_` to 0 before the check, so a parked worker never suspended — the depth save/restore discipline (same as `run_thread_start_body`) was missing.

**Fix (commit `871e209c`, S105 ROOT-010 WORKER-PARK-DEPTH):**
1. Save/restore the enclosing drain depth across the park drain — one shared semantic, no class-name special casing (coroutines, ArrayBlockingQueue.take, FutureTask.get all share it).
2. Parked body re-registered due at `now + 1ms` — exactly one park/rescan per scheduler boundary (0-wake re-pops ≤ 8-slice cap; measured `resumed=8, parks=9`).

**Upstream law enforced:** kotlinx-coroutines `CoroutineScheduler.Worker` — empty queue ⇒ PARKING ⇒ `LockSupport.parkNanos`; parked worker consumes no CPU, resumes on unpark/task arrival. Serialized-engine counterpart: park in a drained body with zero work = deterministic suspension + one bounded rescan per boundary.

**Fresh runtime evidence (S106 re-verification, 3/3 runs, HEAD `176710b1`):**
```
io.github.yamin8000.dooz_23:            Status PARTIAL SUCCESS, Errors: 6, F084 rows: 0
io.github.yamin8000.dooz_23_toplevel:   Status PARTIAL SUCCESS, Errors: 6, F084 rows: 0
exception-set hash (3x): d5c33116c62eff1d (deterministic semantic invariant)
screenshot SHA (3x):     59fdbfcd60b86a23... (identical to S105 record)
instruction burn in spin: 2.2M+ -> ~0.1M (22x less work to same end state)
```
The remaining 6 rows are the EXC-UNWIND bookkeeping of ONE handled `kotlinx.coroutines.CancellationException` (caught by typed handler at `Llo;.B`) — not uncaught failures.

**Probe:** `fixtures/s105_park_probe/` + `scripts/s105_park_probe_check.sh` — post-fix 8/8 PASS ×3 (active → idle-park → one-rescan-per-boundary → wake → task-exactly-once → terminate); pre-fix binary rc=1 + HALT-LOOP + frozen screen (probe *detects* the spin, not just the error delta).

**Fan-out:** 4/42 corpus APKs carry LockSupport; 2 affected titles fixed (dooz ×2 variants); stopwatch/bouncy controls byte-identical before/after (park not on their active paths — presence ≠ fan-out, no inflation).

**Regression:** canonical battery 105/105 ALL PASS (rc=0) at the fix tree.
Logs: `evidence/s106_fresh/` (committed); report `docs/S105_REPORT.md` §1–8.""",
    },
    349: {
        "reason": "completed",
        "comment": """## CLOSED — root executed to L5, fresh evidence at HEAD `176710b1` (S104 FIX-005 / S106 re-verification)

**Ticket symptom:** `[SYNTH-EXC] f141-null-recv`: NPE — `getSavedStateProvider` invoked on null receiver (R8-horizontal-class-merged `Lkotlin/text/MatcherMatchResult;`) inside `ComponentActivity.<init>` pc=224 → APP BOUNDARY unwind. 12 total errors at S102.

**Root cause (raw-DEX ground truth, `scripts/s104_*`):** the APK's `Lkotlin/text/MatcherMatchResult;` is an R8 horizontal-class-merging **super-class** (`$r8$classId:B` field, packed-switch ctor dispatch). The engine's switch-key extraction only handled INT32/INT64 registers; the key lived in a **BYTE-typed** register which collapsed to 0 → wrong constructor branch (classId=5 should dispatch to the savedstate-controller branch) → controller field `input` never set → NPE. This was THE shared root behind the S103 "R8 merged-lambda wrong branch" observation.

**Fix (commit `4feaaeda`, FIX-005 SWITCH-KEY-WIDENING):** switch key extraction now flows through the existing shared `dalvik_int_value` widening — one line, one law (byte/short/char/int/long all widen through the same path), no special-casing. Post-fix probe: `key=5 → dest=11`, `key=4 → dest=5` (both branches correct); the `[NULLFIELD] input-UNSET` line is gone.

**Fresh runtime evidence (S106 re-verification, 3/3 runs, HEAD `176710b1`, APK re-fetched from F-Droid `com.vayunmathur.games.solitaire` vc 20260804, SHA `e87536851b7e9edc…`):**
```
Status: PARTIAL SUCCESS, Errors: 0  (was 12; the SYNTH-EXC null-recv row: 0 occurrences x3)
getSavedStateProvider now EXECUTES (REC-MISS optional-instrumentation rows only, no exception)
compose chain: ComponentActivity.<init> full saved-state wiring passes; AndroidComposeView <clinit> OK;
               chain reaches Recomposer.composeInitial$runtime (next frontier, tracked separately)
```
rc=1 reflects the recorded visual-blank frontier (runtime progress = YES, visual progress = NOT YET PROVEN — honest per §31); zero uncaught errors.

**Regression:** canonical battery 105/105 ALL PASS; sgtpuzzles (the other `$r8$classId` APK) unchanged 0 errors.

Logs: `evidence/s106_fresh/solitaire_run{1,2,3}/`; measured rows in `docs/REAL_APK_IMPACT.md`.""",
    },
    350: {
        "reason": "completed",
        "comment": """## CLOSED — named blocker no longer occurs; fresh evidence at HEAD `176710b1`

**Ticket symptom:** `ISE "CompositionLocal LocalDensity not present"` at `CompositionLocalsKt.noLocalProvidedFor` unwinding through `WindowRecomposer_androidKt.getWindowRecomposer` ← `AbstractComposeView.resolveParentCompositionContext` ← `onMeasure` ← `ComponentActivity.setContentView` — WindowRecomposer host wiring root.

**What closed it (cumulative, each commit independently evidenced):**
- `7f3b1314` (S104-r2 GETHANDLER-ANCESTRY): `View.getHandler` dispatches via `is_subclass_of(class, Landroid/view/View;)` instead of a class-name substring — the AOSP law "every attached View answers getHandler".
- `f5849b87` (S104-r3 GR-07): `View.getRootView` NEVER-NULL law — walk parent chain (bounded 64-hop ViewShadow walk); an unattached view returns ITSELF (AOSP `View.getRootView`). The compose owner cached `getRootView()` into a register and called `getWidth()/getHeight()` on it → engine had no getRootView → null → NPE upstream of the recomposer path.
- `176710b1` (S105 R-005 DECOR-LINKAGE): `Window.setContentView(View)` was a silent no-op — sub-decor never linked into the window decor hierarchy + one global decor singleton leaked across activities. Fix = attach under the current activity's decor + per-activity decor map (AOSP `PhoneWindow.mDecor` identity law). This is the host wiring the ticket's root analysis demanded (ViewTree* owners become reachable on the decor chain).

**Fresh runtime evidence (S106, 3/3 runs, solitaire vc 20260804):**
```
"LocalDensity not present" / noLocalProvidedFor rows: 0 occurrences x3   (was the primary ISE)
Errors: 0 x3; AndroidComposeView <clinit> OK; chain reaches
  Recomposer.composeInitial$runtime -> processCompositionError (composition frontier, separate ticket)
```
**Regression:** battery 105/105 ALL PASS; ballbreak SUCCESS 0 errors (decor fix cross-proof); dooz 6-errors unchanged.

The remaining frontier is composition *content* (Recomposer error processing), which is a different root than the WindowRecomposer host wiring named here. Logs: `evidence/s106_fresh/solitaire_run{1,2,3}/`.""",
    },
    347: {
        "reason": "completed",
        "comment": """## CLOSED — all 3 named roots + 2 cascades executed with commits; fresh evidence at HEAD `176710b1`

The ticket listed 3 roots after the rc=-11 (SIGSEGV) fix, plus 2 handled-but-degraded items. Each was attacked individually:

| # | Ticket symptom | Root + commit | Status |
|---|----------------|---------------|--------|
| 1 | `Handler.postAtFrontOfQueue` on null receiver at `Lr;.onAttachedToWindow pc=50` | `View.getHandler` law matched `class_name.find("View")` — receiver's runtime class is `Lr;` (R8-obfuscated `AndroidComposeView`, no "View" substring) → law missed → null. Fix `7f3b1314`: dispatch via `is_subclass_of(class, Landroid/view/View;)` ancestry walk. | **GONE** |
| 2 | `Object.getClass` on null at `Lox0;.a pc=30` → `Leo;.V pc=44` (follows `Lej0;.<clinit>` `Field.get` null — reflection family) | `Lsr;.run` worker spin root: park bridge destroyed enclosing drain depth → F084 halt; fix `871e209c` (depth save/restore + one rescan per boundary). The nav-NPE chain (`Lox0;.a → Leo;.V → Lnb0;.n → Lwo;.j → Lfb1;.J`) and Job double-completion ISE (`Loj0;.T`) were downstream cascades of the same scheduler root — all 0 rows post-fix. | **GONE** |
| 3 | `View.getWidth` on null at `Lt4;.L pc=112` (inside Lt4.onLayout) | `Lt4;.L` caches `View.getRootView()` then calls `getWidth()/getHeight()`; engine had NO getRootView → null. Fix `f5849b87`: getRootView NEVER-NULL law (AOSP walk-parents / unattached-returns-self), bounded 64-hop ViewShadow ancestry walk. | **GONE** |

**Fresh runtime evidence (S106 re-verification, 3/3 runs, HEAD `176710b1`, both APK variants):**
```
io.github.yamin8000.dooz_23:          6 errors x3 (was 17-18), exception-set hash d5c33116c62eff1d x3
io.github.yamin8000.dooz_23_toplevel: 6 errors x3 (was 17 + HALT)
F084 halt rows: 0 | APP BOUNDARY rows: 0 | Job ISE (Loj0;.T): 0 | nav NPE (Lox0;.a): 0
screenshot SHA 59fdbfcd60b86a23... x3 (matches S105 record)
remaining 6 rows = EXC-UNWIND bookkeeping of ONE handled CancellationException (caught at Llo;.B)
```
**Regression:** battery 105/105 ALL PASS ×3 gates this wave-line; solitaire 0 errors; ballbreak SUCCESS 0 errors.

Next dooz frontier (recomposition content) is tracked in the S105 report §10; it is a different root than this ticket's 3. Logs: `evidence/s106_fresh/`.""",
    },
}

for num, c in CLOSURES.items():
    api(f"issues/{num}/comments", {"body": c["comment"]})
    api(f"issues/{num}", {"state": "closed", "state_reason": c["reason"]}, method="PATCH")
    print(f"#{num} CLOSED with evidence comment")
print("Batch A done")
