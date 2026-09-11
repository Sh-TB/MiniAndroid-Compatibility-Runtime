# S21 FINAL REPORT — F-074/F-075: the frame-callback gate opened into two generic roots

Mission: S21 "close the real frame-callback gate" (inherited gate b7d654a5:
dooz frame callback posted then removed, doFrame never executed,
withFrameNanos awaits forever, screenshot 0 non-white).

## 1. Lineage reconcile (first action)
- Container reset detected: local HEAD d358a0c9 (M5 era) vs remote main
  b7d654a5. Fast-forwarded; ls-remote verified equal before work.
- Toolchain re-bootstrapped (aapt2 2.20-14304508, ecj, r8/d8, android-34).
- Runtime rebuilt; dooz APK re-fetched hash-verified (d81292cd…).

## 2. The gate, refined
The S20 gate trace was re-captured and RE-INTERPRETED against upstream law:

| step | observed | verdict |
|---|---|---|
| post cb=381/388 (J$c) | `[CHOREO] postFrameCallback … pending=1` | legal (AndroidUiDispatcher.dispatch) |
| drain [687 b2/h, 388 J$c] | 687 had **0 dispatch records** | **F-074 break** |
| J$c.run() → toRunOnFrame empty → removeFrameCallback | upstream lines 58-66 | **LEGAL cleanup, not the root** |
| withFrameNanos (K.u) | 0 executions | downstream of F-074 |

Upstream sources fetched and audited (androidx-main):
AndroidUiDispatcher.android.kt (dispatchCallback = the J$c singleton;
postFrameCallback/removeFrameCallback/run/doFrame semantics),
AndroidUiFrameClock.android.kt (withFrameNanos →
uiDispatcher.postFrameCallback + invokeOnCancellation).

## 3. F-074 (R-NEW-298) — engine-level virtual dispatch walk
- **ROOT**: try_recursive_invoke resolved methods only on the exact class.
  dooz `b2/h` = kotlinx.coroutines DispatchedContinuation — no run() of its
  own; the entrypoint is DispatchedTask.run (W1/N) on the superclass. The
  drained continuation silently vanished (silent `return false`, line 5391).
- **PROOF**: runtime trace (0 b2/h.run records; [QUEUE] enqueue + drain
  present) + DEX (s21_frame_probe.py, androguard oracle) + upstream
  (DispatchedTask.kt law; ART ClassLinker semantics).
- **FIX**: `try_recursive_invoke_on_super` — walks class_to_superclass_
  (depth-capped 16, stops at Object) at both give-up points; retries on the
  first ancestor declaring the method; receiver identity preserved.
- **IMPACT**: 712 super-dispatches on the re-run; dooz composition chain
  advanced past the dispatch layer for the first time.

## 4. F-075 (R-NEW-299) — polymorphic zero at reference use
- **ROOT**: Kotlin `return null` = `const/4 v0, 0; return-object v0`. The
  engine stored INT32(0) and propagated it as the return; move-result-object
  kept the tag; `if (node !== newNode)` (LL/b.remove, PersistentOrderedSet —
  androguard CFG) fell to the int path (dalvik_int_value(OBJECT_REF)=0 vs 0)
  → EQUAL → the EMPTY-map rebuild skipped → set (sentinel, sentinel, size-1
  map) → iterator walked the sentinel → map.get(sentinel)=null → CME "Hash
  code of an element (LM/b;@410) has changed after it was added to the
  persistent set" → caught by run()'s catch → handleFatalException no-op —
  the composition coroutine died silently.
- **PROOF**: HASH-TRACE (hashCode fired only from K/d.get — the put never
  hashed), TRIE-TRACE (K/t.v → null while the ctor got the unchanged map),
  androguard CFG, and the three-boundary post-fix (CME 1→0).
- **FIX**: ART Zero-reg-type law at three boundaries: execute_return_object,
  execute_move_result_object (INT32(0)/VOID → NULL_REF), and the 22t
  if-eq/if-ne macro (mixed ref-vs-zero compares by reference identity;
  ref-vs-nonzero-int never-equal). Primitive contexts untouched
  (F-028/F-030/CHAR-PROBE continuity).

## 5. Micro-proof (Phase 8)
`tests/fixtures/f074_super_run` — real APK (aapt2+ECJ+D8), six 180px verdict
bands: **6/6 GREEN** (L1 super-run, L2 receiver identity, L3 two-hop walk,
L4 most-derived override, L5 polymorphic-zero if-ne, L6 identity round-trip).
Battery stage added (`F-074 super-run …`, 3 stages, all PASS).

## 6. Regression (Phase 11)
- Battery: **89/92 PASS** (92 stages). Environmental failures, bisect-proven
  NOT S21: EXT-01/EXT-02 (external corpus /home/z/corpus lost to the
  container reset), GATE H (white=0 reproduces identically with the S21 fix
  stashed — stash-bisect run recorded).
- helloworld §28: ALL PASS (26 checks). TicTacToe §29: ALL PASS (8 checks).
- F-050 frame-pump family: PASS. dooz 3-run: rc=0 ×3, screenshot SHA
  31ddd4d5… ×3 byte-identical, uncaught=0 ×3, 0/2073600 non-white (honest).

## 7. Remaining frontier (honest)
The dooz Recomposer runner parks at its await-work continuation; the resume
that should re-dispatch through AndroidUiDispatcher (J.L → handler.post +
choreographer post #2 → pump → doFrame) never enqueues. NEXT FRONTIER: trace
the parked-resume dispatch path (W1/u0.C/c0 tail — the resume machinery
completes without a dispatch). Only after that: frame pump → measure/layout/
draw → pixels.

## 8. Deliverables
- src/dex/dalvik_engine.{h,cpp}: F-074 walk + F-075 retype laws
- tests/fixtures/f074_super_run/ + scripts/f074_pixel_golden.py + battery stage
- scripts/s21_frame_probe.py (spec-exact DEX walker; fixes the s17/s20
  probe size-table drift recorded in the failure ledger)
- docs/evidence/s21_f074_f075/{GATE_TRACE_S20,F074_silent_drop_proof,
  F075_cme_chain_trie_trace}.txt
- Registry: 297 → 299 roots; VERIFIED-FIXED 17 → 19 (worklist, json,
  ROOT_WORKLOG, ledgers)
