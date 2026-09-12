
---
## S21 — MASTER CAMPAIGN 3, session 21: the frame-callback gate opened into two generic roots (F-074/F-075)

**Gate inherited**: b7d654a5 "frame callback removed-not-run (withFrameNanos awaits forever)".

**Lineage reconcile (first action, از صفر شروع نکن)**: local container was reset;
local HEAD d358a0c9 (M5) was STALE vs remote. Fast-forwarded to remote main
b7d654a5 (S18..S20 lineage intact: F-058..F-073, 297 roots, 17 VERIFIED-FIXED).
ls-remote verified b7d654a5 == remote before work started.

**The gate trace, refined (not re-litigated)**:
1. `[CHOREO] postFrameCallback cb=388 (J$c)` — the AndroidUiDispatcher
   dispatchCallback, posted by dispatch() (upstream law, audited against
   androidx-main AndroidUiDispatcher.android.kt).
2. UC009 drain: [687 b2/h, 388 J$c]. **687 = DispatchedContinuation — its run()
   was NEVER dispatched (0 records / 306k-line log)** — try_recursive_invoke
   resolved only the exact class (no superclass walk).
3. 388 J$c.run() → trampoline → `toRunOnFrame.isEmpty()` → removeFrameCallback —
   **LEGAL upstream semantics** (the one-shot cleanup branch of
   dispatchCallback.run) — NOT the root. F-070..F-073 not implicated.

**F-074 (R-NEW-298) — engine-level virtual dispatch must walk the hierarchy.**
DEX truth: Lb2/h declares no run(); run() lives on LW1/N (DispatchedTask);
Ld2/g implements Runnable. kotlinx law: every dispatched continuation resumes
through the superclass run(). ART law: runtime-class resolution + hierarchy
walk. FIX: try_recursive_invoke_on_super() at both give-up points (receiver
identity preserved, depth-capped). 712 super-dispatches on re-run.
Micro-proof: f074_super_run L1/L2/L3/L4 GREEN.

**F-075 (R-NEW-299) — polymorphic zero at reference use.** After F-074 the
chain reached PersistentOrderedSet.remove: HASH-TRACE proved the set's put
never hashed (its entry was lost) — TRIE-TRACE pinned K/t.v returning null
(trie emptied, correct) while LL/b.<init> received the UNREBUILT map —
androguard CFG: `if (node !== newNode)` guards the EMPTY-map rebuild — the
compare answered EQUAL for (OBJECT_REF, const/4-null) because Kotlin
`return null` = const/4 0 + return-object, and the engine propagated
INT32(0) as the return → move-result-object kept the tag → the 22t compare
fell to the int path (dalvik_int_value(OBJECT_REF)=0 vs 0). FIX: the
ART Zero-reg-type law at three boundaries — return-object, move-result-object,
and mixed ref-vs-zero 22t compares. CME 1→0; fatal resumes 0.
Micro-proof: f074_super_run L5/L6 GREEN.

**Impact (dooz, honest)**: onCreate+composition chain now exception-free
through the recomposition dispatch layer (CME eliminated); dooz 3-run
byte-identical 31ddd4d5…; framebuffer still 0/2073600 non-white — the
runner parks at its await-work continuation and the resume is not yet
dispatched (NEXT FRONTIER, precisely located: the parked Recomposer
await-work resume does not reach J.L dispatch — no post #2, pump 0 frames).

**Regression**: 92-stage battery: 89 PASS incl. helloworld §28 (26 checks),
tictactoe §29 (8 checks), F-050 family, F-074 stage 3/3. 3 environmental
failures, bisect-proven NOT caused by S21: EXT-01/EXT-02 (external corpus
/home/z/corpus lost to container reset) and GATE H (fails identically at
pre-S21 source — stash-bisect run recorded). dooz 3-run determinism held.

**Probes added**: scripts/forensic/s21_frame_probe.py (binary-exact DEX walker;
FIXED the s17/s20 lineage SZ-table drift: const/4, monitor-enter/exit,
array-length, throw are 1 unit; filled-new-array 3 — recorded in the
failure ledger) + MINIANDROID_HASH_TRACE / MINIANDROID_TRIE_TRACE /
[F074-SUPER-DISPATCH] arg-forensics diagnostics (env-gated, read-only).
