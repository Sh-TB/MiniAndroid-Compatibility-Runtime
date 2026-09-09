# ROOT LAW IMPACT REPORT (MASTER-6)

Question answered here: **which root fixes have the greatest expected
effect on real APK loading/execution/UI compatibility — and which only
polish an already-running app?**

## The two metrics (per campaign §8)

- **Metric L (loading/execution):** increases the number of real APKs that
  parse, resolve classes, and execute past framework init.
- **Metric U (UI of a running app):** improves pixels for apps already
  executing.

## Ranked impact table (M6 session)

| Rank | Law | Metric | Why |
|---|---|---|---|
| 1 | **F-041** catch-handler negative-size law | **L+U** | Every real app DEX uses typed+catch-all handler entries (size<0). The old decode mis-directed exception dispatch to garbage addresses — a corrupted-control-flow class that can silently break ANY app whose catch blocks run. Proven live: the f040 fixture's typed IAE handler jumped to mid-instruction @0x14 pre-fix; correct typed dispatch @0x6a post-fix. |
| 2 | **F-040** Arrays.fill family | **L+U** | Kotlin stdlib internals (scatter maps, ArrayMap, `StringBuilder`-free builders) call Arrays.fill during init. Missing = silent no-op = all-zero metadata = probe loops (the live dooz spin: 38k+ equals calls, rc=124). Restores the whole "hash-table init" family for every Kotlin-heavy APK. |
| 3 | **F-042** VALUE_LONG static-default 64-bit law | **L+U** | Long constants in static fields (`0x8080808080808080` markers, masks, hashes) truncated to 32 bits — a silent-corruption class hitting any Kotlin/Java class with long static initializers. Live-proven with the dooz EMPTY marker shape. |
| 4 | **F-043** Double/Float bit-conversion family | U (leaning L) | IEEE-bits bridges used by hashing/serialization/bit tables; REC-MISS → null → 0 corrupted downstream logic. Implemented with NaN canonicalization laws. |
| 5 | F-044 (pending) Compose observation scope law | **L+U** | The live dooz blocker; gates every Compose app at attach-time derived-state reads. Root-located this session (block never created; observer fires with null). |
| 6 | Dispatcher/delayed-task law (pending) | **L+U** | Gates coroutine delay/timeouts post-attach (M4 spotlight). |

## Which fixes increase real-APK loading/execution success?

F-041 (exception dispatch integrity), F-040 (collection internals init),
F-042 (long static fidelity), F-030/F-028/F-029 (prior sessions), and the
pending F-044 + dispatcher laws. These are load-bearing for the pipeline
`APK → DEX → class resolution → execution → framework → lifecycle`.

## Which only improve an already-running app's UI?

Layout/measure edge semantics (Q), Canvas corners (R), text line-breaking
(S), resource qualifiers beyond density (O): they matter AFTER an app
executes and builds a view tree. Important — but a different metric.

## Measured before/after (this session, dooz lighthouse)

| State | Behavior |
|---|---|
| Before (d358a0c9 + attach gate) | rc=124 timeout; `Lh/u;.a` probe spin inside DerivedSnapshotState dependency put; 38,179 `Object.equals` calls; framebuffer 0/2073600 non-white |
| After F-040/F-041/F-042/F-043 | rc=1 (honest failure at the NEXT layer); dependency-table insert COMMITS; derived value computes; owners object constructs; blocker moved to the observation-block law; framebuffer still 0 non-white (honest — no visual claim) |
| Micro-proof (f040_arrays_fill) | 7/7 bands GREEN; 3-run byte-identical (`b3610c68…`) |

## Honest accounting

- DOOZ still renders a blank frame. No visual success claim is made.
- The frontier MOVED (spin → observation-scope law) — measured, not
  asserted: rc 124→1, spin call-site eliminated, blocker identified at
  `P/v$c.o` with the missing `P/v$a.a` scope entry.
- The 82-stage battery baseline at `d358a0c9` was verified by the M5
  session worklog and the tree was clean at session start; the M6 battery
  adds 3 stages (f040 build/run/golden) — see the battery log in the repo
  evidence.
