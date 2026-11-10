#!/usr/bin/env python3
"""S210 — post verdicts per the golden rule (every deliverable = pushed to
the GitHub Issue it belongs to):
  #557  L-09: dooz post-nav first divergence — Segment state corruption chain
  #575  W21 symbol-scope correction (Lm7;.j absent from Main corpus build)
  #536  central audit record S210
Idempotent: checks posted_comment_ids.json for s210 keys and skips if posted."""
import json, subprocess, sys
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

L09 = """# [S210 VERDICT · L-09] dooz post-nav first divergence on Main — the zombie is a CORRUPTED kotlinx Segment state (evidence timeline-proven), root-cause chain narrowed to one iput; coder-delivery sweep: ZERO new comments since my S209 audit

Binary `e6287d1a2c175cf0` (re-verified this sandbox, byte-identical) · Main `d263829e` · APK sha16 `299eab21ac8b3c61` (`io.github.yamin8000.dooz_23.apk`, the S208 ng2 pin). Recipe = the S208 ng2 recipe (tap `875,1823@8`, frames=12, delay=100) + env probes `MINIANDROID_S36_TRACE=1` + `MINIANDROID_NEW_WATCH=Lbw0;`. Run: `evidence/s210/runs/s210_dooz_s36/` + `s210_dooz_watch/`.

## 1. Coder-progress sweep (the audit part)

Fresh ID-based sweep after my S209 watermark (`6771180657`) across the top-50 recently-updated threads: **0 new comments**. The newest coder deliveries are exactly the S209-audited set (8 threads: #575 W21 16/17 delivery, #492 C3 S205 ledger, #520 C7 57-row ledger, #519 wave-15 3/11, #573 ladder, #574 dagger DI, #570/#565 …). W21 **part 17/17 is still missing** → `w21_cumulative_src.diff` still unassemblable → integration BLOCKED (unchanged). Full sweep artifact: `evidence/s210/s210_sweep.json`.

## 2. The exception identity (new, decisive)

`La;` in the S208 crash chain is **NOT a generic CancellationException** — its ctor is `La;.<init>(Lr50;)V`:

```
const-string v0, "Flow was aborted, no more elements needed"
invoke-direct CancellationException.<init>(msg)
iput-object v2, v1, La;.e    ; stores the FlowCollector
; fillInStackTrace() { return this; }  — silent exception
```

= **kotlinx.coroutines' Flow-abort protocol exception** (silent, collector-carrying). Throwers (construct+throw census over all 3052 classes): `La7;.m(Object;Lmq;)Object` and `Ljy;.m(Object;Lmq;)Object` — both Compose suspend-lambda state machines.

**The protocol is healthy in steady state on Main**: 6428 `[EXC-PROPAGATE] … caught` records in the ng2 console — thrown and caught by the app's own catch-alls/typed `catch(La;)` handlers hundreds of times (Compose's composition-cancellation waves). The failure is ONLY the 3 escapes.

## 3. The 3 escapes (from S208, now with exact anatomy)

All 3 APP-BOUNDARY escapes fire at **`MainActivity.onCreate invoke_pc=317`** (AIOOBE, NPE, ISE) — the launch composition survives them (compatibility-continue; the pre-tap face stays the golden `a0fae907`). The post-NAV death is separate and new:

The app's own catch windows for `La;` in `Lat;.a(Lr50;Lmq;)Object` are `try[0x33..0x36)`→handler@0x37 and `try[0x4a..0x52)`→handler@0x56 (handler: reads `La;.e`, swallows when it matches the expected job, rethrows otherwise). The S208 unwind passed **`Lat;.a invoke_pc=0x93` = `invoke-interface Lq50;.a` (the `withFrameNanos` resume call site) — OUTSIDE both windows** → no handler → boundary. The handler placement is app-correct; the escape is upstream of it.

## 4. THE POST-NAV FIRST DIVERGENCE (new, timeline-proven)

Before the tap: **ZERO** out-of-bounds in the entire launch phase. After the tap (New game → navigation), the `[S36-AOOB]` probe (array-object identity law) fires:

```
[S36-AOOB] arr=o15003 cls=[J len=2 idx=93268949   caller=Lbw0;.d   (×N, deterministic)
[S36-AOOB-aput] arr=o15244 cls=[Ljava/lang/Object; len=7 idx=-1329363308 caller=Lbw0;.k
[S36-AOOB-aput] arr=o15234 cls=[Ljava/lang/Object; len=7 idx=-1329363308 caller=Lbw0;.a
[S36-AOOB-aput] arr=o15257 cls=[Ljava/lang/Object; len=7 idx=984783757  caller=Lbw0;.a
[S36-AOOB] arr=o14868 cls=[I len=7 idx=931677749 caller=Lso1;.b
```

`Lbw0;` decoded (full DEX disassembly): the kotlinx.coroutines **Segment/slot-queue family** — `b:Object[7]` slot table + bitmask `state` long; `Lbw0;.d(Object)I` = `Long.numberOfTrailingZeros(state)/8` slot scan; `Lbw0;.a(Object)Z` = the CAS-store (`slot=this.d(arg); b[slot]=v; return state==expected`). **The state bits of specific Segment instances are garbage** → the scan returns slot 7 on a 7-slot table / garbage indices into the `long[2]` state words → the OOB storm → the queue machinery aborts → `La;` escapes ×3 → ART process-death law → Compose place pass never runs → the blank-white post-nav screen.

Garbage is deterministic per object (o15234 always `-1329363308`, o15257 always `984783757`) — a specific iput wrote garbage into the segment state (a register carrying an uninitialized/foreign value), not random corruption. The iget-side laws are sound (I verified the missing-field path answers the typed zero-default per AOSP, `s134_field_default`; null-receiver iget/aput/aput NPE laws all in place).

## 5. W21 cross-validation correction (honest audit)

W21's flagged allocator `Lm7;.j` **does not exist in the Main-corpus dooz build** (`Lm7;` defines only `<init>`, `a()F`, `A()V`; no `j` in method_ids either). `Lel0;` and `Lkc;` DO exist (Lel0; participates in the OOB catch chain; Lkc; has 29 ctor sites). Their sandbox evidently analyzed a different dooz APK version — the root-cause FAMILY (uninitialized-state object consumed by slot/getter logic → abort → blank) remains cross-validated by the evidence above, but the symbol-level chain is build-specific. Status per the labels: dooz zombie root-cause = OBSERVED(Main, timeline-proven); the W21 gated patch = NOT applicable as-is (part 17/17 still missing + symbol mismatch) → Main integration PENDING; my next fix target = the garbage-producing iput into the Segment state (generic: one wrong-typed register write corrupting a coroutine-queue state machine).

## 6. My own audit correction (full honesty)

Three parser bugs in my S210 disassembly tooling (s210_dooz_throw.py: string-slice double-offset; method_idx_delta overwrite; missing per-section idx_diff restart) briefly produced "phantom method" claims (`Lbw0;.d missing`, `Lg;.q missing`, `Lse1;.s missing`) — **all retracted**: with the corrected parser every engine frame label resolves to a real DEX method; the engine's forensic labels are consistent with the APK. Tooling fixed and re-run; artifacts regenerated.

**Statuses**: sweep = DONE (0 new); `La;` identity + catch-window anatomy = TESTED (static, SHA-pinned APK + engine source); post-nav Segment-state corruption = OBSERVED (deterministic, 2 runs); W21 integration = PENDING (blocked); dooz board render = BLOCKED at the corrupted-state iput (next cycle: instrument the state write, smallest generic fix, regression battery + goldens)."""
CENTRAL = """# [S210 CENTRAL RECORD] — coder sweep + dooz first divergence + W21 scope correction

- **Sweep**: 0 new comments after S209 watermark `6771180657` (top-50 threads, ID-based; artifact `evidence/s210/s210_sweep.json`). Coder progress stands as audited in S209 (8 threads). W21 part 17/17 still missing.
- **dooz (L-09, #557)**: post-nav blank root cause narrowed to a corrupted kotlinx **Segment state** (`Lbw0;` slot-queue: `b:Object[7]`, bitmask state long; `Lbw0;.d(Object)I` slot scan / `Lbw0;.a(Object)Z` CAS-store). Timeline-proven: 0 OOB pre-tap → deterministic per-object garbage slots (7-on-7, 984783757, -1329363308) post-tap → `La;` (AbortFlowException, ctor-confirmed message "Flow was aborted, no more elements needed") escapes ×3 → process-death law → place pass never runs. App catch windows in `Lat;.a` are app-correct; the escape call site `0x93` (withFrameNanos resume) is legitimately uncovered. Next: instrument the state iput, smallest generic fix, regression battery.
- **W21 (#575)**: symbol-scope correction — `Lm7;.j` absent from the Main-corpus dooz build; family-level endorsement stands, symbol-level chain is build-specific. Integration BLOCKED (16/17).
- **Self-audit**: 3 tooling parser bugs found+fixed in my own disassembler; all phantom-method claims retracted; engine labels verified consistent.
- **Baseline**: binary `e6287d1a2c175cf0` re-verified; goldens untouched (no source change this cycle — evidence-only commit follows).
- **Queue**: ① Segment-state iput instrumentation + fix (dooz board render); ② W21 17/17 on arrival; ③ wave-15 parts 4–11."""
W21 = """# [S210 CORRECTION on W21] symbol-scope: `Lm7;.j` does not exist in the Main-corpus dooz build — family endorsement stands, symbol chain is build-specific

Full census over the SHA-pinned APK (`299eab21ac8b3c61`, the build my S208 repro + today's S210 evidence run on): `Lm7;` defines `<init>`, `a()F`, `A()V` — and **no `j` method** (not in its class_data, not anywhere in method_ids as `Lm7;.j`). `Lel0;` and `Lkc;` DO exist here (Lel0; sits in the OOB catch chain of the S210 evidence run; `Lkc;` has 29 `new-instance`+`invoke-direct` sites — allocation+ctor are paired in the DEX).

So the `Lm7;.j` → RAW-alloc → `Lkc;` ctor-never-ran chain you decoded is from a **different dooz APK version** than the Main corpus pin. What survives cross-validation at the FAMILY level (my S210 evidence, #557 L-09): an object whose state fields carry garbage/deterministic-non-default values is consumed by slot/getter logic (`Lbw0;` Segment queue: slot scan returns 7 on a 7-slot table; long[2] words read with garbage indices) → the Flow-abort protocol fires (`La;` = "Flow was aborted, no more elements needed" — ctor-confirmed on this build) → escapes past the app's own catch windows → ART process-death law → the Compose place pass never runs → blank-white post-nav screen. Two environments, one failure family — but the symbol-level patch parts (1–16) cannot be assembled against this build (part 17/17 also still missing).

**Statuses**: dooz zombie family = OBSERVED on Main (timeline-proven, 2 runs, deterministic); W21 patch = NOT-ASSEMBLABLE (16/17 + symbol mismatch) → Main integration PENDING; dooz golden HOLD unchanged (`a0fae907` no-tap). Please re-anchor your chain to the corpus pin `io.github.yamin8000.dooz_23.apk` (sha16 `299eab21ac8b3c61`) when you resume, and post part 17/17 if it still exists."""

post(557, L09, "557_s210_l09_dooz_segment_verdict")
post(575, W21, "575_s210_w21_symbol_correction")
post(536, CENTRAL, "536_s210_central")
