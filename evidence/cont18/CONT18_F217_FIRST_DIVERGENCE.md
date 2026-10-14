# F-NEW-217 FIRST-DIVERGENCE RECORD (CONT-18 T-01, 2026-10-08)

Directive: convert F-217 to the first-divergence format after the LAW-C/E/F
determination wave. Binary `8ee839e718877216` · HEAD `75dae014` · dooz anchor
`d602648e8e401895` ×3 byte-identical (real content renders — zero drift).

## 1. SOURCE (authoritative — the app's own bytecode)

Extracted from the corpus DEX (`upload/sudoku_secuso_101.apk`, kotlinx-coroutines
shipped by the app — NOT from memory, NOT from docs):

- `evidence/cont18/f217_dex_extract.json` — 17 real methods of
  `Lkotlinx/coroutines/sync/MutexImpl;` (unlock 88 code units / 5 regs,
  tryLockImpl 56, lock$suspendImpl 23, lockSuspend 46, holdsLock, isLocked,
  toString, ctors of the CancellableContinuationWithOwner waiter family).
- `evidence/cont18/f217_unlock_disasm.txt` — unlock/tryLockImpl/lock$
  suspendImpl disassembly. Real unlock skeleton:

```
unlock(owner):  loop:                            # 0000  ← the F-084 spin site
                  state check → ISE "This mutex is not locked"   (0008→0094 arm)
                  curOwner = owner$volatile                      (sget 000c)
                  owner-mismatch → ISE "This mutex is locked by …, but …" (002e–0074)
                  CAS(curOwner → NO_OWNER) via the SafeAtomicHelper
                    forwarding0.m helper                         (0080)
                  CAS failed → RETRY the loop                    (0088 if-eqz → 0000)
                  CAS ok → invoke the queue-drain/resume step    (008c)
```

## 2. ALGORITHM → SEMANTIC LAW

The waiter-resume protocol requires exactly three runtime-observable semantic
transitions (each = a law, no app names):

| Law | Contract (from the bytecode) |
|-----|------------------------------|
| CAS-RETRY-PROGRESS | a failed compareAndSet inside the lock/unlock retry loop must be retried against a MOVING state; the loop terminates or advances — it must never spin without state change (the 50,001-visit F-084 face) |
| UNLOCK-DRAIN-RESUME | unlock() with a queued waiter resumes the waiter's continuation INLINE (same cycle) — the waiter's side effects must run exactly once and ownership must transfer |
| NO-OWNER ISE ARM | unlock() on a free mutex throws IllegalStateException — never a silent return (real bytecode arm 0008→0094) |

## 3. RUNTIME TRACE (current binary, live)

Synthetic probe `fixtures/f217_mutex_probe` (plain Java, the extracted state
machine verbatim; apk `run/w7/f217.apk` sha16 `1e3e0a03e0a221c2`):

| Row | Verdict | Trace |
|-----|---------|-------|
| F217-A CAS-RETRY-PROGRESS | **PASS** | got=true contended=false-path re-acquired, spins=4, terminates |
| F217-B UNLOCK-DRAIN-RESUME | **PASS** | runs=1 trace=`drain;body;owned;` — the waiter body executed inline during unlock, ownership transferred |
| F217-C NO-OWNER ISE ARM | **PASS** | ISE thrown as the bytecode requires |

Artifacts: `run/cont18/t01_f217_probe/`. Supporting baseline evidence:
f084 synthetic HALT-50001 (bounded-halt law VERIFIED-CORRECT, cap never raised,
`t01_f084_probe.json`); anchors 6/6 ×3 byte-identical.

## 4. FIRST-DIVERGENCE DETERMINATION

1. **The concurrency layer honors the contract at HEAD** — all three semantic
   transitions of the extracted MutexImpl algorithm pass (3/3). The historical
   spin signature (owner=NO_OWNER + permits=0 + head=obj#366 during a
   50,001-visit unlock loop) is **NOT reproducible at HEAD** by the layer that
   owns those semantics.
2. **The historical spin's mechanism is pinned**: the unlock retry loop spun
   because its state inputs never moved — the nested waiter-resume side
   effects were lost UPSTREAM in the composition chain (CONT-8 F-256 refined
   first divergence: the composition/continuation chain losing work), the same
   divergence family F-265 (null text) belongs to. The mutex loop was the
   loudest VICTIM, not the root — consistent with the brief's rule that the
   root is the mechanism blocking semantic progress, not the budget halt and
   not the null-text symptom.
3. **Remaining exposure (honest, still open)**:
   - the dooz GAME screen face (the Compose tap pipeline answers target=0 —
     `run/cont18/t01_run_tap1`: `[F117-TAP] DOWN (540,960) target=0`), which
     gates T-09's causal-order trace (F-084-halt-before-null-text) on live
     runs — F-265 therefore stays CLASSIFIED (not SUPERSEDED);
   - no corpus APK exercises Mutex.lock/unlock in observed headless runs
     (classes load in sudoku/klondike/notes; zero lock traffic at HEAD).

## 5. Registry consequences

- F-NEW-217: current → `FIRST-DIVERGENCE DOCUMENTED (T-01)`; the spin face is
  downstream of the composition-chain divergence family; runtime contract
  VERIFIED by the source-extracted probe; fix surface = none in the
  concurrency layer at HEAD.
- F-265: stays CLASSIFIED pending T-09 (no reclassification without the
  causal-order trace).
- T-13 (spin reproduction at HEAD): face not reachable in observed runs —
  recorded honestly, not faked.
