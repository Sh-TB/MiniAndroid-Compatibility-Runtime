# COMPOSE_DOOD_ANALYSIS_010 — Dooz progression record (R14/R30)

Target: io.github.yamin8000.dooz (real Jetpack Compose tic-tac-toe, GPL-3,
F-Droid). Per campaign law: NO fake Dooz UI.

## 1. Baseline entering Campaign 010 (from 009)

- Attach dispatch (env-gated `MINIANDROID_DISPATCH_ATTACH=1`):
  ComposeView children 0→1; AndroidComposeView attached; 317 lines of real
  Compose-runtime interpretation inside the attach window.
- Screenshot with flag OFF: white (0 non-white px); attach chain evidence in
  stderr only.

## 2. Campaign 010 findings

### 2.1 The wall after attach: HALT-LOOP in LM1/i;.f
dooz attach-run log (304,527 lines): Compose layout-node internals
(`androidx/compose/ui/node/e` methods), `AndroidComposeView.getSnapshotObserver`
etc. execute — then interpretation livelocks in `LM1/i;.f` (3× HALT-LOOP,
50001 visits each, PC≈0x22, bytecode 101 units).

### 2.2 Root cause chain (this campaign's advance)
1. `LM1/i;` = **obfuscated Kotlin `Intrinsics`**. `.f` disassembly
   (androguard on the real APK): `checkNotNullParameter` — `if-nez param,
   +64 → return-void`; on null it walks `Thread.currentThread().getStackTrace()`
   comparing `StackTraceElement.getClassName()` against the Intrinsics class
   name to build the NPE message.
2. Our `Thread.getStackTrace` returned the EXP-093 empty array / shadow null;
   OOB `aget-object` returned silent null → the walk never terminated →
   the loop guard HALTed. (R17 note: this was a genuine livelock the loop
   guard correctly caught — not call-count throttling.)
3. **Fix implemented** (commit f9190da): real frames from
   `CallStack::snapshot_top_first()` → real `StackTraceElement[]` heap arrays
   (`__class_name__` dotted, `__method_name__`) + accessor dispatch + the
   ThreadShadow null-stub retired (falls through to the engine).
4. **Measured result**: `[UC010-STACKTRACE] 6 real frames (top=LM1/i;)` —
   and Intrinsics now throws **real NullPointerException**s (9 `[EXCEPTION]`
   records, e.g. `LM1/i;.d pc=17`, handler=NOT_FOUND → propagates as on
   device). The null-check mechanism itself now works.

### 2.3 Remaining blocker (precisely located, not hand-waved)
After the walk terminates, `.f` builds the message with StringBuilder and
livelocks in the append region (PROGRESS lines pin PC=44/101 then 48/101
inside `LM1/i;.f`, 400k+ instructions in-frame). Working hypothesis: the
`invoke-virtual StringBuilder.append` path with a null argument re-executes
without advancing PC (return-address handling for invoke-virtual on the
shadow StringBuilder object). Next step: instruction-trace flag scoped to
`LM1/i;.f` and audit PC advance in the invoke-virtual return path. A deeper
question queued behind it: WHY does a @NotNull parameter receive null (which
stubbed upstream API returns null into Compose)?

### 2.4 R30 ledger (per-step state)

| Step | State this campaign | Evidence |
|---|---|---|
| children count | ComposeView children = 1 (unchanged) | `EXP092-RENDER node=44 ... children=1` |
| composition nodes | real Compose classes execute in attach window (009 evidence) | 009 §10 trace |
| measure/layout nodes | not yet dispatched (wall before onMeasure) | 0 onMeasure dispatch records |
| draw calls | not yet | — |
| visible pixels | 0 (white) — honest | screenshot |
| touch targets | not yet | — |
| state changes | Intrinsics NPE path now real (9 NPEs thrown correctly) | f9190da log evidence |

## 3. Compose generality note (R15)

Compose-method demand from the 009 profiles stands: droidify 7,917 compose
methods, newpipe 7,162. Campaign 010 added kvaesitso (Compose-M3 launcher):
honest early FAILURE (exit 1, 1 METHOD-IN) — recorded, not faked. The five-
APK Compose matrix remains: dooz (real runtime, deepest execution), droidify
(profiled), kvaesitso (fails early), newpipe (profiled; Views+Compose mix),
persiancalendar (Views; runs 629 METHOD-IN). The Compose-runtime
interpretation work advances through dooz because it is the only corpus app
whose Compose execution gets far enough to exercise the stack.
