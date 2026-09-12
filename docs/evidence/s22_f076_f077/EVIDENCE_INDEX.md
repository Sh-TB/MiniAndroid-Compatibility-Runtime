# S22 EVIDENCE INDEX — F-076 (R-NEW-300) fixed, F-077 (R-NEW-301) discovered

Session: S22 MASTER MISSION — ROOT CLOSURE + REAL APK EXECUTION
Baseline: HEAD 5a2b7d99 (= origin/main, ls-remote verified), clean tree, rebuilt.

## Environment reconcile (Law 3)
- Container reset had rewound local main to d358a0c9 (M5 era); fetched origin
  5a2b7d99 (36 commits) and fast-forwarded. Toolchain re-bootstrapped
  (aapt2 2.20-14304508). Corpus restored 15/16 (dooz d81292cd… exact).
- dooz baseline re-run at 5a2b7d99 BEFORE any change: rc=0 ×3, uncaught=0 ×3,
  screenshot SHA 31ddd4d5b8e6 ×3 byte-identical (matches S21 record),
  0/2,073,600 non-white. Environment fully reconciled.

## F-076 (R-NEW-300) — active-cycle guard stubbed re-entrant coroutine start helpers

ROOT
  try_recursive_invoke's M3-19/F-017 active-cycle guard keyed STATIC
  invocations by (class, method) only. kotlinx.coroutines start helpers are
  static and STRUCTURALLY re-entrant: B1/a.B =
  IntrinsicsKt.startCoroutineUninterceptedOrReturn and W1/l0.a =
  CoroutineScope.launch. An outer coroutine-start frame is still active on the
  call stack when an inner one begins (withContext starts the Recomposer
  runner body; the runner body's coroutineScope starts the loop block;
  suspendCancellableCoroutine inside the loop starts another). The guard
  stubbed the inner start (returns null). W1/D.c (coroutineScope) is a tail
  call of B1/a.B, so recompositionRunner saw null != COROUTINE_SUSPENDED,
  treated the scope as completed, disposed the apply observer, cleared the
  runner job, and returned: the Recomposer runner died BEFORE its first
  awaitWorkAvailable/withFrameNanos. No frame request #2 → toRunOnFrame stayed
  empty → J$c removed itself (the S21-legal remove) → no frames → 0 pixels.

PROOF (env-gated, read-only; files in this directory)
  1. r2 pre-fix trace: exactly ONE [S22] E0.t entry, ZERO E0$a.t / F0.t / K.u
     entries; [M3-19-CYCLE] LB1/a;.B re-entered (depth=17) at the exact
     W1/D.c call site; also LW1/l0.a and LW1/E.invoke#480 stubs in the
     UNDISPATCHED launch machinery. post_fix_gate_events.txt vs
     pre_fix_gate_events.txt.
  2. DEX ground truth (scripts/forensic/s21_frame_probe.py + androguard):
     - LW1/D.c(L1/p, C1/d) = coroutineScope: new b2/u (ScopeCoroutine) then
       tail-invoke B1/a.B — the stub site.
     - W1/l0.e = withContext → B1/a.B; W1/l0.a = CoroutineScope.launch.
     - LF/E0.t = recompositionRunner body (registerRunnerJob →
       registerApplyObserver → knownCompositions().invalidateAll() →
       W1/D.c(coroutineScope){LF/E0$a}).
     - LF/E0$a.t → L1/q.j → LF/F0.t = the while(shouldKeepRecomposing) loop
       with awaitWorkAvailable + parentFrameClock.withFrameNanos.
  3. Upstream law (androidx-main fetched this session, /home/z/my-project/upstream):
     kotlinx.coroutines IntrinsicsKt.startCoroutineUninterceptedOrReturn is a
     static, depth-bounded, legitimately re-entrant helper;
     Recomposer.kt recompositionRunner; AndroidUiDispatcher.android.kt
     dispatch() posts BOTH handler runnable AND choreographer frame callback;
     dispatchCallback.run removes itself ONLY when toRunOnFrame is empty.

FIX (generic, no app-specific code)
  dalvik_engine.cpp active-cycle key identity law extended to statics: key
  carries the identities of the LEADING OBJECT ARGUMENTS (up to 2). For
  coroutine helpers that is the target continuation/coroutine — unique per
  logical coroutine → nested starts take distinct keys and execute real DEX;
  same-identity re-entry still collides (genuine-cycle stub preserved);
  MAX_RECURSION_DEPTH remains the backstop.

IMPACT
  after fix: [S22] entry#3 E0$a.t, #4 F0.j, #5 F0.t — the runner loop STARTS;
  the initial composition advances into slot-table writes; cycle stubs
  8 → 5. M3-19-CYCLE false stubs on the coroutine-start family eliminated.

## F-077 (R-NEW-301) — TrieNode buffer/bitmaps invariant violation (DISCOVERED, next frontier)

Observed after F-076: the initial composition (WrappedComposition.setContent
→ ComposerImpl → SlotTable) dies at
  NPE "null cannot be cast to non-null type TrieNode"
  stack: M1/i.d ← K/t.s(i) ← K/t.m(merge) ← K/f.putAll ← F/l.s0 ← F/y.b ← …
  ← b1.k (f077_trienode_stack.txt).
Probe (MINIANDROID_S22_TRACE=1 [TRIENODE] state dumps): receiver node o1820
  s(12): a=134676546 b=-2147483648 len=13 null_slots=12
  s(27): a=160401768 b=-2147483646 len=28 null_slots=26
kotlinx.collections.immutable law: TrieNode buffer.size MUST equal
  popcount(dataMap) + popcount(nodeMap) and no node-map slot may be null.
  o1820: bitmaps claim 15 entries, buffer holds 2 non-null — INVARIANT
  VIOLATED during engine-executed trie insertion/merge arithmetic.
STATUS: DISCOVERED (root-cause window: the numeric/bit ops of K/t.m/K/f.put
  node construction). [TRIENODE] probe + [S22] gate remain in place.

## Runner chain status after F-076 (honest)
- Runner starts, parks on withFrameNanos (frame clock family) as designed;
  lifecycle-replay drives the initial composition; composition crashes at
  F-077 before withFrameNanos→postFrameCallback#2 ever fires. Pixels remain
  0 on dooz (honest). ChessClock/uNote prove the rendering stack is capable
  of full painted frames (see EXECUTION_MATRIX).
