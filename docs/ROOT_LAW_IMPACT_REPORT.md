# ROOT LAW IMPACT REPORT (MASTER-6 → MASTER CAMPAIGN 4)

Question answered here: **which root fixes have the greatest expected
effect on real APK loading/execution/UI compatibility — and which only
polish an already-running app?**

## The two metrics (per campaign §8/§15)

- **Metric L (loading/execution):** increases the number of real APKs that
  parse, resolve classes, and execute past framework init.
- **Metric U (UI of a running app):** improves pixels for apps already
  executing.

Per-root loading classification (§15 taxonomy): see
ROOT_LAW_COMPLETENESS_MATRIX.md and the audit ledger columns
(`LOAD-BLOCKING / POST-LOAD EXECUTION / FRAMEWORK / UI`).

## Ranked impact table (post Campaign-4)

| Rank | Law | Metric | Why |
|---|---|---|---|
| 1 | **F-044** per-frame return-descriptor law (C4) | **L+U** | A whole CLASS of silent corruption: every int return from a method whose last callee returned boolean collapsed to 0/1 — version hashes, sizes, counts, ids. Proven live: the Compose derived-state version hash 6729 returned as BOOLEAN(1); dependency-change detection was dead; derived state permanently stale; dooz died at the app boundary (rc=1). Post-fix: rc=0, attach completes, Compose dispatch machinery executes. Every Compose app and every int-return-heavy Kotlin app benefits. |
| 2 | **F-041** catch-handler negative-size law (M6) | **L+U** | Every real app DEX uses typed+catch-all handler entries (size<0). The old decode mis-directed exception dispatch to garbage addresses. |
| 3 | **F-040** Arrays.fill family (M6) | **L+U** | Kotlin stdlib internals (scatter maps, ArrayMap, builders) call Arrays.fill during init; missing = silent no-op = probe loops (the live dooz 38k-equals spin). |
| 4 | **F-042** VALUE_LONG static-default law (M6) | **L+U** | Long constants in static fields truncated to 32 bits — silent-corruption class (the dooz 0x8080808080808080 marker). |
| 5 | **F-045** System.identityHashCode law (C4) | **L (leaning U)** | Was fail-soft 0-for-everything: distinct objects hashed identically — the version-hash term in Compose's dependency scan, HashMap identities, anywhere identity hashing matters. |
| 6 | **F-043** Double/Float bit-conversion family (M6) | U (leaning L) | IEEE-bits bridges used by hashing/serialization; was REC-MISS → null → 0. |
| 7 | F-030/F-028/F-029/F-035/F-036/F-039 (M4/M5) | **L+U** | The foundational register/atomic/reflection/shift/iterator laws — all protected by the battery. |
| 8 | Dispatcher/delayed-task law (PENDING) | **L+U** | The remaining Compose first-frame blocker (see honest frontier below). |

## Which fixes increase real-APK loading/execution success?

F-044 (return-value integrity), F-041 (exception dispatch integrity), F-040
(collection internals init), F-042 (long static fidelity), F-045
(identity hashing), F-030/F-028/F-029 (prior sessions), and the pending
first-frame pump. These are load-bearing for the pipeline
`APK → DEX → class resolution → execution → framework → lifecycle`.

## Which only improve an already-running app's UI?

Layout/measure edge semantics (Q), Canvas corners (R), text line-breaking
(S), resource qualifiers beyond density (O): they matter AFTER an app
executes and builds a view tree. Important — but a different metric.

## Measured before/after (Campaign-4, dooz lighthouse)

| State | Behavior |
|---|---|
| Before (M6 HEAD `5a139afd`) | rc=1; NPE (Intrinsics checkNotNull) from AndroidComposeView.onAttachedToWindow @0x0112 crossing the app boundary; ComposeView children=1 but composition dead; framebuffer 0/2073600 non-white (SHA 31ddd4d5…, deterministic BLANK) |
| After F-044 + F-045 | rc=0; app-boundary NPE GONE; onAttachedToWindow executes to its LAST DEX instruction; queue drain runs AndroidUiDispatcher (J;.O) + J$c runnables + MonotonicFrameClock context chain; framebuffer still 0 non-white (HONEST — no visual claim; the first-frame pump is the remaining frontier); 3-run byte-identical |
| Micro-proof (f044_return_descriptor_law) | 7/7 bands GREEN; 3-run byte-identical (32b8a456…); battery stage added (85→88) |

## Honest accounting (§43)

- DOOZ still renders a blank frame. No visual success claim is made.
- The frontier MOVED (app-boundary NPE → first-frame pump) — measured via
  rc, exception traces, attach-completion depth, and queue-drain evidence,
  not asserted.
- The version-hash collapse was proven with an engine probe (return-value
  tag) + register-file dump, then fixed generically; the micro fixture
  demonstrates 6729→6731 dependency-change detection (L6 band).
