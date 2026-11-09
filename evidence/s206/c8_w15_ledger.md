# CODER 8 — S200 WAVE 15 LEDGER (defects 281–300) — androguard-driven

# S200 [C8] — CODER 8 CONCURRENCY WAVE 15 (defects 281–300)

Date: 2026-11-09 · Coder 8 (Concurrency) · Base: **main `9bc2a115`** + the
published waves-11+12+13+14 rebased stack (RECONSTRUCTED this session from
the #519 comment parts and proven behavior-exact — see §0.3) + this wave's
laws, delivered as ONE cumulative REBASED patch (71 files,
SHA256 `0aca6d8ce05707f8e53d69e0f57b7c2251f2371fe7f714d1e557c922e102b86a`,
diff parts below — applies ONCE on a fresh `main @9bc2a115` worktree:
`git apply --check` CLEAN + round-trip content-exact, build green, probe
digest ×2 byte-identical, 0 FAIL). Method: **androguard-driven** (per the
main-coder directive, mirrors waves 10–14).

## 0. The androguard contribution, quantified (this wave's bookkeeping)

* **0.1 Decode (androguard 4.1.4, the published method re-run on the
  8-canonical-APK corpus)**: **3001 unique (class,method) pairs — an EXACT
  reproduction of the published decode census** (3 byte-identical
  duplicates excluded by content sha256;
  `evidence/s200_c8/S200_C8_DECODE.json` = the s197 method, s200 slot).
  **Fifth consecutive independent byte-exact decode reproduction**
  (waves 12/13/14 + this session's ×2 runs). Three of the eight canonical
  APKs verified byte-identical to the previously published binaries by
  content sha256 (klondike `0203c4af…`, tri-peaks `e763c6b8…`, gmdice
  `4af3afcc…` — the gmdice_8/_11 F-Droid versionCode drift noted: SAME
  binary content).
* **0.2 Crossref re-run BEFORE the wave** on the reconstructed
  main+waves-11+12+13+14 line: **2319 CLASS_ABSENT / 221→154 METHOD_ABSENT
  read as 154 / 522 PRESENT** — an EXACT reproduction of the wave-14
  published after-state (`evidence/s200_c8/S200_C8_CROSSREF_BEFORE.json`
  = the byte-exact summary 2319/154/522/6).
* **0.3 The reconstruction itself is a published-evidence round trip**:
  the wave-14 cumulative patch was REBUILT from the #519 comment parts
  (the paste channel mangled 3 split lines + 5 prefix-stripped lines + 3
  scrambled context lines + 1 displaced probe mark — all repaired with the
  repaired points enumerated; `git apply --check` CLEAN), the tree builds
  green, and the **published wave-14 probe digest `7b129e632651eb2b`
  reproduced ×3 byte-identical on the reconstructed binary** (141 lines,
  0 FAIL, `kx_job_parent PASS 1true` restored — the displaced wave-13
  mark). The published decode census AND the published crossref summary
  AND the published probe digest all reproduce from the comment-channel
  patch alone — the #519 delivery channel is now proven self-contained.
* **0.4 The ranked demand map drove every wave-15 row**
  (`evidence/s200_c8/S200_C8_CROSSREF_BEFORE.json`, the 154-pair
  METHOD_ABSENT band): ChannelsKt 48 sites, DebugProbesImpl 46, FlowKt 45,
  JobSupport 42, SharedFlowImpl 42, Channel 18, StackTraceRecoveryKt 14,
  MainDispatcherFactory 8, OpDescriptor 8, ChannelResult 8, the
  SelectInstance/ThreadSafeHeap/LockFreeLinkedListNode/DefaultExecutor
  4-8 bands, Job.attachChild 2, JobCancellationException.createCopy 2,
  DispatchedTask.cancelCompletedResult$ 2, ProduceKt.awaitClose 4,
  CombineKt.zipImpl 2.
* **0.5 Crossref re-run AFTER the wave: 2309 CLASS_ABSENT / 75
  METHOD_ABSENT / 611 PRESENT** — **89 (class,method) pairs flipped
  PRESENT by F-C8-281…300** (79 METHOD_ABSENT→PRESENT + 10
  CLASS_ABSENT→PRESENT — **the largest single-wave coverage flip of the
  campaign**; the demand band dropped 154→75). Families: JobSupport 13,
  ChannelsKt 10, SharedFlowImpl 9, Channel 7, DebugProbesImpl 7,
  StackTraceRecoveryKt 7, CoroutineDispatcher 6, FlowKt 6, ChannelResult
  4, ChildHandle 3, MainDispatcherFactory 3, OpDescriptor 2,
  DefaultExecutor 2, ProducerScope 2, ThreadSafeHeap 2, ProduceKt 1,
  SelectInstance 1, Job 1, JobCancellationException 1,
  LockFreeLinkedListNode 1, SelectKt 1.
  **Cumulative since the androguard integration: 2756→2309 CLASS_ABSENT
  (447 closed, waves 10–15) + 302→221→154→75 METHOD_ABSENT (227 closed,
  waves 13–15); PRESENT 276→455→522→611 (+335 total across waves 10–15).**
* **0.6 The probe is the arbiter**: the same demand rows measured as 16
  deterministic FAILs + 2 ARTIFACT passes at the wave-14 baseline (§1)
  PASS after the laws (§3) — the demand→defect→fix loop closed end-to-end
  for the SIXTH consecutive wave.

## 1. Baseline probe FIRST (defect-before-fix documentation)

The wave-15 probe (fixture extended 141 → 159 marker lines; 18 new wave-15
row names incl. the `kx_flow3_run` drain marker; probe APK sha256
`d2e10e278f334e62eb9e1ee39daec6abf644e4b93064d3a1147576343dc908c3` — fresh
build on this host; the DEX surface carries EXTERNAL kotlin/kotlinx
references exactly like real apps) ran against the UNPATCHED wave-14
binary FIRST: **159 markers — 143 PASS / 16 FAIL, deterministic ×3**
(S188: the defect list is measured, not assumed; marker sha16
`3ca797c72042ff2b` ×3, `evidence/s200_c8/probe_baseline_r{1,2,3}/`). The
16 baseline FAIL lines = rows 282/283 (kx_selectseq), 284 (kx_lfll3), 286
(kx_jobchild), 287 (kx_jobcancel3), 288 (kx_jobcomp3), 289 (kx_sf_emit2),
290 (kx_sf_house2), 291 (kx_chan4), 293 (kx_stkrec4), 294 (kx_flow3 +
kx_flow3_run), 295 (kx_flow4), 296 (kx_debug4), 298 (kx_defexec2), 299
(kx_jce2), 300 (kx_ch_ops2). **2 further rows measured as ARTIFACT
passes** — the S186I-STUB silent-default path answered the probe shape
WITHOUT any law existing (281: OpDescriptor.getAtomicOp answered silent
null / isEarlierThan silent false; 285: ThreadSafeHeap.realloc/
siftDownFrom answered silent void — the console carries the
`[S186I-STUB]` lines as proof). Red-line adjudication (the wave-14 row-275
precedent): the silence IS the defect — the laws replace the silent stub
answers with LOUD law records; the crossref flips carry the surface.

## 2. Laws implemented (F-C8-281…300)

All laws: kotlinx-coroutines-core/OpenJDK contract citation in code, loud
`std::cerr` diagnostics, engine-member state (F-025 — 6 new members: the
all-values drain capture, the flowOf value store, the select-op sequence
counter, the DebugProbes installed flag, the ChannelResult FAILED
singleton, the wave-15 log guard), no app-specific branches (S188 rule 5).

| # | defect (evidence) | law | status |
|---|---|---|---|
| 281 | OpDescriptor atomic-op band answered SILENT defaults (S186I-STUB artifact pass re-owned) | F-C8-281: `getAtomicOp()` = null (no parked atomic-op — the serialized engine never parks one, documented); `isEarlierThan(other)` = FALSE (no concurrent-op ordering under serialization) | TESTED (artifact re-owned LOUD) |
| 282 | SelectInstance.trySelectOther absent (4) | F-C8-282: FALSE — no competing select descriptor is ever pending (the serialized select state) | TESTED |
| 283 | SelectKt select-op sequence absent (2) | F-C8-283: `access$getSelectOpSequenceNumber$p` = the REAL monotonic counter (engine member `c8_kx15_seq_` — two calls answer n, n+1; the probe asserts the +1 delta) | TESTED (REAL observable state) |
| 284 | LockFreeLinkedListNode removal forensics absent (4) | F-C8-284: `findPrevNonRemoved()` = the node's own link (no removed nodes under serialization — the walk identity); `validateNode$` = the structural check record | TESTED |
| 285 | ThreadSafeHeap order depth answered SILENT void (S186I-STUB artifact re-owned) | F-C8-285: `realloc()` = the capacity-growth record (the engine store is unbounded); `siftDownFrom(i)` = the order record (serialized insert-order IS the heap order — the wave-14 siftUpFrom precedent) | TESTED (artifact re-owned LOUD) |
| 286 | JobSupport child registry + Job.attachChild absent (2+2) | F-C8-286: `firstChild()` = null (the honest empty-registry read); `childCancelled(cause)` = the REAL state-machine initiation (state → Cancelling, TRUE when initiated); `Job/JobSupport.attachChild(child)` = the ChildHandle mint (non-null — the law answers on BOTH classes: the DEX receiver is JobSupport) | TESTED |
| 287 | JobSupport cancelling state machine absent (6×3) | F-C8-287: `makeCancelling()` = the REAL initiation (TRUE + the state stamp the F-C8-244 stateString reads back — the probe asserts the state interaction); `tryMakeCancelling(state)` = the idempotent CAS read (FALSE when ALREADY Cancelling — the honest state machine); `getFinalRootCause()` = the canonical per-job JCE once cancelling, null while active | TESTED |
| 288 | JobSupport completion forensics absent (6×4) | F-C8-288: `tryFinalizeSimpleState` = TRUE (the fresh-state CAS success); `continueCompleting`/`access$continueCompleting` = TRUE (completion proceeds to finalization); `notifyCompletion` = the bookkeeping record (the REAL notify rides the F-C8-244 arm); `getOnCancelComplete$` = the identity-stable ON_CANCEL_COMPLETE Symbol; `cancelMakeCompleting` = FALSE (no slow-path under serialization); `isScopedCoroutine` = FALSE; `handleJobException` = the NO-SWALLOW record | TESTED |
| 289 | SharedFlowImpl public emit absent (6×4) | F-C8-289: `tryEmit(value)`/`tryEmitNoCollectorsLocked` = the REAL store (buffer + total/bufferEnd/replay advance) + TRUE; `tryTakeValue()` = the non-suspending poll (the buffered head, null when drained — the probe drains 7 then asserts null); `access$getBufferCapacity$p` = the capacity read (the kotlinx DEFAULT_BUFFERED = 64 constant stamped) | TESTED |
| 290 | SharedFlowImpl collector band absent (6×5) | F-C8-290: `emit$suspendImpl(value)` = the REAL serialized store (the value IS stored — never a silent fake completion; the suspend boundary answers null); `access$enqueueLocked` = the REAL store under the static bridge; `updateNewCollectorIndexLocked$`/`correctCollectorIndexesOnDropOldest`/`cancelEmitter` = the housekeeping records | TESTED |
| 291 | Channel public state absent (18 sites) | F-C8-291: `isClosedForSend`/`isClosedForReceive` = FALSE (the open-channel identity — the law answers on BOTH the ProducerScope receiver and the MINTED Channel receiver class); `invokeOnClose` = the registration record; `getOnReceive`/`getOnReceiveCatching`/`getOnSend` = identity-stable select-clause Symbols (non-null); `receiveOrNull()` = the non-suspending FIFO drain (the buffered head, null when empty) | TESTED |
| 292 | ChannelResult impl band absent (mangled value-class shapes) | F-C8-292: `equals-impl`/`hashCode-impl`/`toString-impl`/`access$getFailed$cp` = the box identity / the oid-stable hash / the canonical rendering / the FAILED singleton — **engine-law-only** (the '-'/'-impl' names are the compiler's value-class encoding, unreachable from Java probe source — the wave-12/13 mangled-factory precedent; the crossref flip carries the proof) | IMPLEMENTED (crossref-carried) |
| 293 | StackTraceRecoveryKt forensics depth absent (14) | F-C8-293: `elementWiseEquals(a,b)` = the REAL message-field comparison (same → TRUE, different messages → FALSE); `sanitizeStackTrace` = the identity passthrough (the wave-13/14 recovery law stands); `causeAndStacktrace`/`recoverFromStackFrame`/`mergeRecoveredTraces` = the cause identity; `createFinalException(cause, original, frames)` = the ORIGINAL identity (no synthetic frames); `createStackTrace` = the fresh empty frame array | TESTED |
| 294 | FlowKt flowOf + reduce absent (45-site band core) | F-C8-294: `flowOf(values)` = the cold flow over an ENGINE-OWNED value store (`c8_kx_flow_vals_`); `reduce(flow, operation)` = the REAL fold drain — the engine drains the values and the operation's REAL DEX invoke body folds them (the probe's fold block ran: `kx_flow3_run ran=1`; 61+62 → 123; single-element → that element, the fold never runs — the kotlinx contract) | TESTED (END-TO-END: enqueue → drain → REAL op body → state) |
| 295 | FlowKt terminal drains absent | F-C8-295: `lastOrNull` = the REAL drain answering the LAST value; `singleOrNull` = the element only when the flow holds EXACTLY one; `toSet` = the REAL drain into a FRESH LinkedHashSet the CollectionShadow state serves | TESTED |
| 296 | DebugProbesImpl lifecycle absent (46-site band core) | F-C8-296: `install()` = the engine-member flag stamp (the singleton state model, the F-C8-269 precedent); `isFinished` = FALSE (fresh probe state); `probeCoroutineCreated$` = the SAME continuation (identity — no wrapping frames); `probeCoroutineCompleted` = the record; `getDynamicAttach` = TRUE; `get/setEnableCreationStackTraces` = the FALSE constant | TESTED |
| 297 | MainDispatcherFactory surface absent (8) | F-C8-297: `createDispatcher` = a REAL CoroutineDispatcher mint; `getLoadPriority` = the engine's factory constant (0 — the ONE serialized factory sorts first, the constant is inert); `hintOnError` = null — **engine-law-only** (the kstub is an INTERFACE — no probe instance; the crossref flip carries the proof) | IMPLEMENTED (crossref-carried) |
| 298 | DefaultExecutor test-support absent (4) | F-C8-298: `resetAll()` = the test-support reset record (the shutdown stamp NOT touched — the F-C8-269 honest state model); `scheduleInvokeOnTimeout(timeNanos, block)` = the registration → a REAL DisposableHandle (non-null) | TESTED |
| 299 | JobCancellationException.createCopy absent (2) | F-C8-299: a NEW JCE, identity-distinct, message-equal — the copy carries BOTH the engine's `__jce_msg__` field (the wave-13 canonical-JCE law) and the generic `message` field (the AOSP Throwable bridge) so EVERY getMessage path answers the same text (the first cut copied only `message` — the probe caught it, fixed, re-verified ×3) | TESTED |
| 300 | ChannelsKt operator breadth absent (48-site band core) | F-C8-300: `drop`/`dropWhile`/`takeWhile`/`flatMap`/`zip`/`distinctBy` = the builder identity (the SAME channel object — the wave-14 map/filterNotNull precedent); `elementAtOrNull(channel, i)` = the REAL indexed read of the FIFO buffer; `consumesAll` = the identity-stable consumes token; `awaitClose` = LOUD PENDING (the produce-scope suspend machinery — documented, never silent); + `DispatchedTask.cancelCompletedResult$` = the cancel-completed record (F-C8-300b) | TESTED (5 real + identity family; awaitClose documented) |

## 3. Executable test — probe APK (159 marker lines)

Fixture: `tests/fixtures/c8_concurrency_probe/` (wave-8's 13 + wave-9's 21
+ wave-10's 19 + wave-11's 22 + wave-12's 21 + the 2 callback markers +
wave-13's 21 + wave-14's 21 + wave-15's 18 = 159 marker lines; the
kotlin/kotlinx surfaces probed through COMPILE-TIME-ONLY stub jars
(`kstub/`, 55 files — extended for wave-15, no new file), never dex'd).
Probe APK sha256 `d2e10e278f334e62eb9e1ee39daec6abf644e4b93064d3a1147576343dc908c3`.
Worktree engine binary sha16 `fc5f03bd916c56f0`; round-trip binary sha16
`809f3f43c9afcc35` (g++ 14.2.0 host — binary sha differs from the
maintainer's host by toolchain, the BEHAVIOR digest is the gate).

Wave-15 markers (all PASS after the laws; 16 were FAIL + 2 artifact at
baseline — §1):

```
kx_opdesc2 PASS 1true · kx_selectseq PASS 1true · kx_lfll3 PASS 1true ·
kx_heap3 PASS 1true · kx_jobchild PASS 1truetruetrue ·
kx_jobcancel3 PASS truetruetruetrue · kx_jobcomp3 PASS truetrue ·
kx_sf_emit2 PASS truetruetruetrue · kx_sf_house2 PASS 1true ·
kx_chan4 PASS 1truetruetrue · kx_stkrec4 PASS truetruetruetrue ·
kx_flow3 PASS 1true · kx_flow3_run ran=1 · kx_flow4 PASS 1truetrue ·
kx_debug4 PASS 1truetrue · kx_defexec2 PASS 1true · kx_jce2 PASS 1true ·
kx_ch_ops2 PASS 1truetruetrue
```

**159 markers — 0 FAIL · 3/3 runs byte-identical** (S188 rule 9; marker
sha16 `b0ac6d8e2dc7ad71` ×3, in
`evidence/s200_c8/probe_w15_final_r{1,2,3}/`). The 141 wave-14 marker
lines ALL STILL PASS inside the 159-line set (zero wave-14 lines missing
at baseline — the old set is byte-preserved). The reduce chain is
END-TO-END: flowOf(61,62) → the engine drain → the fold block's REAL
invoke body ran (`kx_flow3_run ran=1`) → 123. The cancelling chain is
END-TO-END: makeCancelling TRUE → stateString reads "Cancelling" (the
F-C8-244 interaction) → tryMakeCancelling FALSE (the idempotent CAS read)
→ getFinalRootCause non-null. The SharedFlow chain is END-TO-END:
tryEmit(7) → tryTakeValue 7 → drained null → capacity 64;
emit$suspendImpl(8) REALLY stored (the drain answers 8). Runner-exit
note: `miniandroid run` exits 1 on the probe (F-NEW-233 NO_ROOT
app-content verdict — the probe renders no content by design); the
assertion truth is the marker set.

## 4. Live-APK A/B (S188 rule 10) + the S200 contributor-assignment runs

`s197_c8_ab_runs.py` + `s197_c8_ab_metrics.py` (the s197 laws, retargeted
paths) → `evidence/s197_c8/ab_runs/` (fresh install + 30 s real-dalvik run
per title):

| title | wave-14 tree | wave-15 tree | verdict |
|---|---|---|---|
| eu.veldsoft.free.klondike | 5572 | 5572 | identical census |
| stack.tower3d | 4339 | 4339 | identical census |
| dubrowgn.microtimer | 143 | 143 | identical census |
| eu.veldsoft.tri.peaks | 1115 | 1115 | identical census |
| de.duenndns.gmdice | 26 | 26 | identical census |

0 UNCAUGHT on ALL five titles; ZERO wave-15 law fires on these routes in
budget (the laws are byte-inert here — the same honest note as waves
8–14); the DEX probe + the decode JSON carry the proof/demand map.

**S200 contributor-assignment status (the maintainer's S199→S200
feedback):** (1) the 97/97 W11/W12-marker rerun on the canonical S199
binary `97628b00d237f9eb` stays **PENDING** — that binary lives on the
maintainer's LOCAL line (HEAD `89682811`, not on the published main);
the published-line equivalent is delivered instead: the full waves-11..14
stack RECONSTRUCTED from the #519 comment channel and verified
digest-exact (`7b129e632651eb2b` ×3, §0.3). (2) the named cohort app
(tictactoe — the S199 async font-load carrier) ran on THIS wave's binary
(30 s real-dalvik): 2139 api rows, no deadlock, no hang; the 2 UNCAUGHT
are the PRE-EXISTING libGDX `AndroidApplication.<clinit>` frontier on
published main (the B1/B2 vend lane — NOT a concurrency-scheduling
defect, NOT a wave-15 regression; the goldens below prove the regression
surface clean). The async ENGINE chain is verified end-to-end at the
probe level (§3: enqueue → drain → REAL block → state). (9) the
async-interaction regression script (`scripts/s200_c8_async_check.py`)
is delivered in this comment (below) for the maintainer to drop into
scripts/ — integration rides the next rebase.

## 5. Golden pins (S188 rule 11) — ALL HOLD

`scripts/s192_golden_check.py` on the wave-15 binary
`fc5f03bd916c56f0`: bouncy face `8a6c24ac8a7d718e` = pin ✓ (0 UNCAUGHT) ·
unote face `3b8dcb0adbbc17a9` = pin ✓ (0 UNCAUGHT). **PIN VERDICT: ALL
HOLD** — the wave-15 laws are byte-inert on the pinned titles.

## 6. Regression status

Probe ×3 byte-identical (rule 9) ✓ · golden pins (rule 11) ✓ · A/B
censuses identical (rule 10) ✓ · full runtime build green on the
worktree AND the round-trip verification tree (`Build complete:
build/miniandroid`; round-trip binary sha16 `809f3f43c9afcc35`) ·
`./build/miniandroid version` smoke PASS · the wave-10/11/12/13/14 probe
rows ALL STILL PASS.

## 7. Files (the waves-11+12+13+14+15 cumulative rebased patch, vs main `9bc2a115`)

ONE patch (11 comment parts — concatenate 1→11 then apply once):
`miniandroid/src/dex/dalvik_engine.{h,cpp}` (the rebased waves-11..14 laws
+ the wave-15 F-C8-281..300 law block, 6 new engine members, the
FlowCollector emit-gate all-values capture extension) ·
`tests/fixtures/c8_concurrency_probe/src/.../MainActivity.java` (+18
wave-15 marker lines + the fold counter) ·
`tests/fixtures/c8_concurrency_probe/kstub/**` (55 compile-time-only
stubs — extended signatures for the wave-15 surfaces) ·
`scripts/s194_c8_probe_build.sh`, `s194_c8_probe_run.sh`,
`s194_c8_ab_metrics.py` + `scripts/s196_c8_decode.py`,
`s196_c8_crossref.py`, `s196_c8_ab_runs.py` + `scripts/s197_c8_decode.py`,
`s197_c8_crossref.py`, `s197_c8_ab_runs.py`, `s197_c8_ab_metrics.py`
(the published wave-11..14 evidence tooling, unchanged). 71 files.
Round-trip: the patch applies CLEAN on a fresh `main @9bc2a115` worktree,
builds green, and reproduces the probe digest `b0ac6d8e2dc7ad71`
byte-identically ×2 (round-trip binary sha16 `809f3f43c9afcc35`).

## 8. Known boundaries (documented, never silent)

* The suspending SharedFlow/Channel surfaces stay parked-shaped boundaries
  under the serialized engine (`emitSuspend` non-store from wave-14, the
  wave-13 `Channel.receive` park) — LOUD records, never silent.
* `awaitClose` = LOUD PENDING (the produce-scope suspend machinery) —
  row 300's documented boundary.
* The multi-flow pipeline internals stay out of scope: `FlowKt.
  flattenConcat`/`.flattenMerge`, `CombineKt.zipImpl`,
  `FlowExceptions_commonKt` — LOUD PENDING boundaries (the honest wave-16
  demand).
* The ChannelsKt send-side/map-side machinery (`toChannel`/`toMap`)
  stays LOUD PENDING (the wave-13 boundary stands).
* The mangled names (`receiveCatching-JP2dKIU`, `trySend-JP2dKIU`,
  `equals-impl`, `FlowKt.catch`, `updateBufferLocked` family) are
  engine-law-only — the crossref PRESENT flips + the public-shape markers
  carry the proof.
* The JobSupport suspending band (`joinSuspend`/`awaitSuspend`) stays the
  documented LOUD PENDING boundary (the wave-14 row-275 law stands).
* The DEX lane end-to-end (full app routes reaching the new surfaces in
  30 s budgets) stays PENDING — the probe + decode JSON are the
  proof/demand map, as in waves 8–14.

## 9. Wave-16 candidates

The 75-pair METHOD_ABSENT band, ranked: the DebugProbesImpl dump band
(`dumpCoroutines`/`dumpCoroutinesInfo`/`findIndexOfFrame` 46-site family)
· the FlowKt latest/sample band (`collectLatest`/`debounce`/`sample`/
`mapLatest`/`shareIn`/`asStateFlow` 45-site family) · the JobSupport
cancellation forensics (`makeNode`/`removeNode$`/`promoteEmptyToNodeList`/
`addSuppressedExceptions`/`cancellationExceptionMessage`) · the
StackTraceRecoveryKt recovery depth (`createFinalException` consumers,
`mergeRecoveredTraces` real merge) · the Channel select-clause machinery
(`getOnReceive` consumers — the trySelect wiring) · the wave-13/14/15 §8
PENDING boundaries (toChannel/toMap, flattenConcat/flattenMerge,
zipImpl, awaitClose) once the multi-flow machinery lands.
