# ROOT LAW COMPLETENESS MATRIX (MASTER CAMPAIGN 4)

**HEAD at matrix build:** `5a139afd` + F-044/F-045 working tree (commit pending)
**Question answered:** for every root family — is the FAMILY closed, or did
we only fix one API? (Campaign 4 §4 discipline: ROOT COMPLETE ≠ FAMILY
CLOSED.)

Status vocabulary: `CLOSED` (law + family coverage + proof + real APK),
`CLOSED-FOR-CORPUS` (closed for every APK the corpus can reach; extended
only on live evidence), `PARTIAL` (law proven, members missing),
`RESEARCHED` (no implementation), `PENDING` (root-located, not implemented),
`REJECTED_CLAIM`.

---

## Family closure ledger

| Family | Law status | Coverage state | Missing members | Proof chain | FAMILY STATUS |
|---|---|---|---|---|---|
| A — DEX/Dalvik semantics | F-028 (raw-bits), F-030 (zero-null), F-035 (23x shifts), F-041 (catch handlers), F-044 (return descriptors) all REGRESSION-VERIFIED | const/move/invoke/arith/shift/cmp/return/exception families exercised by 88-stage battery + dooz | rem-int/long, packed/sparse-switch payload edges, div overflow (Long.MIN/-1) | micro-proof f028/f030/f040/f044 + dooz | **CLOSED-FOR-CORPUS** |
| B — DEX loading/verifier/resolver | F-042 (VALUE_LONG 64-bit), multi-dex enumeration, delta chains | 16-APK corpus + R8 shapes | annotations beyond static values, full verifier | battery + corpus | **CLOSED-FOR-CORPUS** |
| C — Tagged-value boundaries | F-030/F-028/F-042/F-044 closed produce/store/convert/RETURN boundaries | return-side was the last open boundary (CHAR-PROBE stale descriptor) — closed by F-044 | consume-side descriptor guidance at iget/iput sites (P2) | f044 fixture 7/7 + dooz live | **CLOSED** (return boundary was the live frontier) |
| D — Atomic/lock-free | F-028h identity CAS + volatile semantics | AtomicReference/Integer/Long/Array/FieldUpdater | weakCAS spurious semantics NOT_RELEVANT (single logical thread) | f030 L5/L6 + dooz | **CLOSED-FOR-CORPUS** |
| E — kotlinx.coroutines | Segment/queue/EventLoop construct; MainDispatcherLoader loads | scheduler machinery now EXECUTES post-F-044 (J$c runnables drain) | **AndroidUiDispatcher/MonotonicFrameClock delayed dispatch — the first-frame pump (PENDING, next battle)** | dooz live trace | **PARTIAL** — root-located next battle |
| F — Kotlin Intrinsics | exception-honesty law honored (every NPE traced to producer) | areEqual/checkNotNull exercised | compiler-version variance | battery | **CLOSED-FOR-CORPUS** |
| G — Collections | F-036/F-039/F-040 | asList/iterator/singleton/fill family | Arrays full inventory (copyOf/sort/binarySearch) = P2 on demand | f040 7/7 | **PARTIAL** (core closed) |
| H — Reflection | F-029 core | methods/ctors/invoke/newInstance | inherited-member walk, exception wrapping (P2) | microtimer Room guard | **CLOSED-FOR-CORPUS** |
| I — View object model | F-031/F-023 laws | context/parent/tags/attach | measure edge semantics (Q) | battery goldens | **CLOSED-FOR-CORPUS** |
| J — Context/service registry | F-032/F-033 | ACCESSIBILITY + Class overload | INPUT_METHOD/WINDOW/NOTIFICATION/CLIPBOARD/DISPLAY (P1 on demand) | battery | **PARTIAL** |
| K — Activity/lifecycle | G07 golden | onCreate→onStart→onResume ordering | — | G07 | **CLOSED** |
| L — Intent/PackageManager | explicit intents | component identity/extras | implicit IntentFilter matching (P2) | corpus | **PARTIAL** |
| M — Handler/Looper | F-029a + virtual clock | createAsync/postDelayed/ChessClock | removeCallbacks (P3) | ChessClock 3-run | **CLOSED-FOR-CORPUS** |
| N — PendingIntent/Alarm | F-018 | AMS record law | — | battery | **CLOSED** |
| O — Resources/ARSC | aapt2-built fixtures authoritative | string/drawable/density | locale/night/width qualifiers (P2) | battery | **PARTIAL** |
| P — AXML/Manifest | manifest/typed values | activities/permissions | overlay (NOT_RELEVANT yet) | corpus | **CLOSED-FOR-CORPUS** |
| Q — Layout/Measure | m3_style_weight | EXACTLY/AT_MOST/weight | baseline alignment; weights-heavy real APK | fixture | **PARTIAL** |
| R — Canvas/rendering | 7 pixel-golden fixtures | software renderer determinism | drawBitmap density, save/clip corners (P2) | goldens | **CLOSED-FOR-CORPUS** |
| S — Text/fonts | FreeType/HarfBuzz/FriBidi wired | shaping pipeline | line-breaking, emoji (P3) | fixtures | **PARTIAL** |
| T — Compose | F-044 closed the observation/validity law — composition machinery EXECUTES | attach completes; dispatcher drains | **first-frame render (measure/layout/draw via Recomposer frame) — PENDING** | f044 7/7 + dooz live | **PARTIAL** — frontier advanced, UI not yet proven |
| U — SnapshotIdSet/bitset | F-035 + F-040 SWAR laws | contains/or/and/bit ops | — | f040 L7 | **CLOSED** |
| V — Math/primitive | F-043 bits family, F-045 identityHashCode | nlz/ntz/min/abs/bits/ihc | rotations, floor/ceil (NOT_RELEVANT yet) | f040 L6 | **CLOSED-FOR-CORPUS** |
| W — Arrays | EXP-071 + F-040 | aget/aput/fill/filled-new-array | copyOf/sort family (P2) | f040 | **PARTIAL** |
| X — Exceptions | F-041 + F-016 honesty | typed/catch-all/finally/negative size | nested-try torture corpus (P2 idea) | f040 L2 | **CLOSED-FOR-CORPUS** |
| Y — SQLite/Room | F-012/F-026 | persistence/rawQuery/txn | @Update/@Delete adapters (P3) | F-026 fixture | **CLOSED-FOR-CORPUS** |
| Z — JNI/native/ELF | boundary classification only | — | loader contract (P2/P3, no corpus demand) | — | **RESEARCHED** |

---

## ROOT COMPLETENESS SCORES (§17 scale, evidence-backed)

| Root | Score | Evidence |
|---|---|---|
| F-028 | 9 | 10 = family closed; −1 for rem/div edges |
| F-028h | 9 | AOSP-law micro + dooz scheduler proof |
| F-029 | 9 | reflection core + regression guard |
| F-030 | 10 | Zero law fully closed (produce/convert/invoke boundary) |
| F-031..F-033 | 9 | closed at corpus demand level |
| F-035/F-035b | 9 | shifts + nlz closed |
| F-036/F-039 | 9 | iterator/singleton laws closed |
| F-040 | 10 | fill family fully closed (all primitives + ranges) |
| F-041 | 10 | handler-decode law fully closed (spec cross-checked) |
| F-042 | 10 | VALUE_LONG law fully closed |
| F-043 | 9 | bits family closed; raw-variants + NaN canon proven |
| **F-044** | **10** | per-frame descriptor law: micro 7/7, 3-run byte-identical, dooz NPE eliminated, dooz 3-run deterministic |
| **F-045** | **8** | ihc law implemented + live-reached in dooz; no dedicated fixture band yet |

No score of 10 is claimed without the listed evidence (§17: "10 without
evidence is forbidden").
