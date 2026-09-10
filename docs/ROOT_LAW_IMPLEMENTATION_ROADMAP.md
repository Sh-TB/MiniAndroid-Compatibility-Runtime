# ROOT LAW IMPLEMENTATION ROADMAP (MASTER-6 → MASTER CAMPAIGN 4)

Prioritized implementation order. Priority classes per §5 of the campaign
brief: P0 = fundamental/runtime blocker, P1 = high-value common, P2 = useful
broad, P3 = specialized, P4 = defer. Scores are engineering judgment, not
measurements.

## Tier P0 — landed and regression-verified (keep protected)

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

10. **Dispatcher/delayed-task law — the Compose first-frame pump (HIGHEST
    PRIORITY after Campaign-4).** With F-044 landed, dooz's attach runs to
    completion and the AndroidUiDispatcher/MonotonicFrameClock machinery
    (J;.O, J$c runnables, coroutine-context chain) EXECUTES. The remaining
    blocker is the Recomposer's first frame: delayed dispatch through the
    frame clock with the virtual clock. The scheduler-discriminator
    questions (owner, queue, state variable, second actor) must be
    answered from the live trace first — no pump on faith. Unblocks:
    Compose measure/layout/draw → the first non-blank Compose frame.

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
