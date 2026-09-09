# ROOT LAW IMPLEMENTATION ROADMAP (MASTER-6)

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

## Tier P0 — next battle (root-located, not yet implemented)

8. **F-044 — Compose snapshot-observation scope law (HIGHEST PRIORITY).**
   Live blocker: `LP/v$c;.o` fires with `observer.i == null` because the
   observation block is created by `LP/v$a;.a`, which never ran. Map the
   dooz Compose version's scope pairing (register observer ⟺ enter block
   ⟺ exit block) from DEX ground truth, then implement whichever law the
   bytecode proves: (a) the scope-entry call missing in the readiness
   validation path, or (b) observer tolerance for "no active block".
   Unblocks: every Compose app that reads derived state during attach —
   dooz first frame, then measure/layout/draw.

9. **Dispatcher/delayed-task law** (M4 spotlight, now behind F-044):
   AndroidUiDispatcher + MonotonicFrameClock delayed dispatch with the
   virtual clock. The scheduler-discriminator questions (owner, queue,
   state variable, second actor) must be answered from the live trace
   first — no pump on faith.

## Tier P1 — high-value, demand-driven

10. **F-045 candidate — remaining system-service entries** (INPUT_METHOD,
    LAYOUT_INFLATER, WINDOW, NOTIFICATION, CLIPBOARD, DISPLAY): AOSP
    SystemServiceRegistry names → manager shadows. Cost S each; fan-out
    high across real APKs that call getSystemService in onCreate.
11. **F-046 candidate — Long/Integer remaining bit methods** used by
    hashing tables (bitCount, rotateLeft/Right, compare,
    parseUnsignedLong family): implement on trace evidence.
12. **F-047 candidate — measure/weight edge semantics** (LinearLayout
    weight distribution exactness; baseline alignment): quantify against a
    real weights-heavy APK before implementing.

## Tier P2 — broad compatibility, evidence-gated

13. IntentFilter matching fidelity (action/category/data/MIME precedence
    per AOSP IntentFilter.java) — when a real APK relies on implicit
    intents.
14. Resource qualifier/config selection beyond density (locale, night,
    smallest-width) — when a corpus APK uses them.
15. Canvas save/clip/bitmap-density corners — when screenshot diffs demand.
16. Reflection hidden gaps (inherited members walk, exception wrapping
    fidelity).
17. JNI/ELF loader contract — only for a corpus APK with native libs;
    classify missing-library separately (never as a Java blocker).

## Tier P3 — specialized

18. Room @Update/@Delete adapter tests; Math.random determinism law;
    HashMap iteration-order documentation law (FORGOTTEN P1 items).
19. Text line-breaking; emoji fallback.

## Deferred / rejected

- Snapshot "v0" as a standalone subsystem: REJECTED as stated by the
  report — implement the live-evidenced laws (F-044) instead.
- Scheduler pump on faith: REJECTED pending discriminator answers.
- Any app-specific shortcut (package-name hacks, blank-frame acceptance,
  rc=0 as success): FORBIDDEN (§7).

## Regression gate

Every implementation lands with: micro-proof fixture (ECJ+D8 real DEX) →
pixel golden (7-band) → 3-run byte-identical determinism → full battery
(currently 85 stages) → affected real APK (dooz) re-run → honest frontier
update. Do not silently reduce the battery.
