# ROOT LAW IMPLEMENTATION ROADMAP (MASTER-6 → MASTER CAMPAIGN 4 → MASTER CAMPAIGN 3/M8)

Prioritized implementation order. Priority classes per §5 of the campaign
brief: P0 = fundamental/runtime blocker, P1 = high-value common, P2 = useful
broad, P3 = specialized, P4 = defer. Scores are engineering judgment, not
measurements.

## Tier P0 — landed and regression-verified (keep protected)

0. **F-050 family (M8/Campaign-3 continuation, 2026-09-10)** — the
   Choreographer frame-pump battle, four generic roots landed + micro-proven
   (f050_frame_pump 7/7 bands, 3-run byte-identical) + battery 91/91:
   - **F-050a** Choreographer shadow family + deterministic vsync pump
     (getInstance singleton identity; postFrameCallback/removeFrameCallback
     FIFO schedule; one shared monotonic frame time per tick, fixed
     16666667 ns quantum, zero wall clock; engine pump drains resumption
     work on the same MessageQueue). Real-APK evidence: dooz
     AndroidUiDispatcher/AndroidUiFrameClock registered a J$c frame
     callback that NOTHING ever fired — 0 doFrame dispatches in a 14.6 MB
     trace; withFrameNanos parked forever.
   - **F-050c** AtomicLongFieldUpdater.getAndIncrement wrote oldv-1 (a
     DECREMENT) via a prefix-match delta bug. OpenJDK law pinned: exact-name
     dispatch, getAnd* returns OLD, *AndGet returns NEW. Real-APK evidence:
     dooz Recomposer BufferedChannel.sendersAndCloseStatus went 0 → -1 on
     the first send → `(state shr 60).toInt()` = -1 → ISE "unexpected close
     status: -1" (message recovered via F-050b) → cancellation cascade.
   - **F-050d** Boolean.TRUE/FALSE static synthesis (OpenJDK Boolean.java;
     R8 rewrites valueOf(true) into the sget; the miss returned NULL, the
     channel iterator unboxed false, exited as if exhausted, and
     cancelConsumed cancelled the Recomposer's awaitWork channel →
     CancellationException "Channel was cancelled").
   - **F-050b** Throwable message law (OpenJDK Throwable.java): ctor
     String stores detailMessage, getMessage() returns it. Forensics
     unlock: every DEX-constructed exception is now message-visible.
   - **F-050e** §6 shadow registry invariant count law 19 canonical
     (18 + ChoreographerShadow) / 21 visible with pre-registered pair.
1. **F-030** zero-is-null-at-reference-use (invoke boundary) — protects
   every coroutine/atomic identity path.
2. **F-028/F-028h** untyped-register raw-bits + AtomicReferenceArray
   identity/volatile law.
3. **F-041** encoded_catch_handler negative-size law (`|size|` typed pairs
   + catch-all) — every real R8/ECJ typed+catch-all handler entry.
4. **F-040** Arrays.fill family — Kotlin scatter-map/`ArrayMap` metadata
   init; guards the whole Kotlin-collection internals family.
5. **F-042** VALUE_LONG static-default 64-bit law.
6. **F-035/F-035b** 23x shifts + leading-zeros law.
7. **F-029** reflection core (with the FIX-M3-012b reconciliation guard).
8. **F-044 (CAMPAIGN-4)** per-frame return-descriptor law — the recursive
   frame save/restore now covers `current_method_descriptor_`; an int
   return can no longer collapse to a boolean under a callee's stale
   descriptor. Closed the Compose derived-state staleness law (dooz rc
   1→0; NPE eliminated). Micro-proof f044 7/7 + 3-run byte-identical.
9. **F-045 (CAMPAIGN-4)** System.identityHashCode law (OpenJDK; was
   fail-soft 0-for-everything — silent-corruption class).

## Tier P0 — next battle (root-located, not yet implemented)

10. **Job isActive / coroutine-completion law (HIGHEST PRIORITY after
    M8).** With F-050a/c/d landed, the remaining first-frame blocker is
    precisely localized: the Recomposer's frame-await continuation is
    CANCELLED shortly after registration (cancel cascade: LE1/a.y resume →
    Choreographer.removeFrameCallback via the K$a invokeOnCancellation
    handler). The doFrame pump never sees a pending callback at the frame
    boundary. The scheduler-discriminator questions (which Job owns the
    await, why isActive collapses, which state variable the cancellation
    reads) must be answered from the live trace first — no job-pump on
    faith. Unblocks: Compose measure/layout/draw → the first non-blank
    Compose frame.

## Tier P0 — previous battle (root-located, IMPLEMENTED in M8)

10-bis. *(moved to landed: F-050 family above — the dispatcher/frame-pump
    law. The pump itself is implemented and micro-proven; the surviving
    blocker moved to item 10, the Job-active law.)*

## Tier P1 — high-value, demand-driven

11. **F-046 candidate — remaining system-service entries** (INPUT_METHOD,
    LAYOUT_INFLATER, WINDOW, NOTIFICATION, CLIPBOARD, DISPLAY): AOSP
    SystemServiceRegistry names → manager shadows. Cost S each; fan-out
    high across real APKs that call getSystemService in onCreate.
12. **F-047 candidate — Long/Integer remaining bit methods** used by
    hashing tables (bitCount, rotateLeft/Right, compare,
    parseUnsignedLong family): implement on trace evidence.
13. **F-048 candidate — measure/weight edge semantics** (LinearLayout
    weight distribution exactness; baseline alignment): quantify against a
    real weights-heavy APK before implementing.
14. **F-049 candidate — dedicated identityHashCode fixture band** (F-045
    has no micro band of its own yet; the f044 arithmetic bands cover the
    hash arithmetic indirectly).

## Tier P2 — broad compatibility, evidence-gated

15. IntentFilter matching fidelity (action/category/data/MIME precedence
    per AOSP IntentFilter.java) — when a real APK relies on implicit
    intents.
16. Resource qualifier/config selection beyond density (locale, night,
    smallest-width) — when a corpus APK uses them.
17. Canvas save/clip/bitmap-density corners — when screenshot diffs demand.
18. Reflection hidden gaps (inherited members walk, exception wrapping
    fidelity).
19. JNI/ELF loader contract — only for a corpus APK with native libs;
    classify missing-library separately (never as a Java blocker).
20. Arrays family inventory (copyOf/copyOfRange/sort/binarySearch/
    deepEquals/deepHashCode) — on corpus demand.

## Tier P3 — specialized

21. Room @Update/@Delete adapter tests; Math.random determinism law;
    HashMap iteration-order documentation law (FORGOTTEN P1 items).
22. Text line-breaking; emoji fallback.

## Deferred / rejected

- Snapshot "v0" as a standalone subsystem: REJECTED as stated by the
  forensic report — the live-evidenced law was F-044 (closed C4), and the
  snapshot machinery executes as app DEX.
- Observer-scope pairing law (the M6 "F-044 candidate" as framed):
  REJECTED by Campaign-4 DEX ground truth — the scope calls execute; the
  real defect was the return-descriptor leak.
- Scheduler pump on faith: REJECTED pending discriminator answers.
- Any app-specific shortcut (package-name hacks, blank-frame acceptance,
  rc=0 as success): FORBIDDEN (§7).

## Regression gate

Every implementation lands with: micro-proof fixture (ECJ+D8 real DEX) →
pixel golden (7-band) → 3-run byte-identical determinism → full battery
(currently 88 stages) → affected real APK (dooz) re-run → honest frontier
update. Do not silently reduce the battery.
