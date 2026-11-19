# W21 RUNTIME HOTSPOT REPORT (Phase 5) — gprof-measured, hypotheses evaluated

Method: dedicated `-pg` instrumented binary (same production flags + `-pg`, `build_pg/`,
built in 587 s, separate from the production `build/`), gprof sampled profiles of
chess (35 s cap run), tallybook, minos, HelloWorldToast. Raw profiles +
`chess_profile.txt` under `evidence/w21/gprof/`. gprof distorts absolute times (mcount
overhead) but rank-orders hotspots — exactly what the mission asks for.

## Top measured hotspots (chess = the largest runtime consumer, 35 s window)

| rank | function | self s | % time | calls | classification |
|---|---|---:|---:|---:|---|
| 1 | `std::set<unsigned int>::~set()` | 8.85 | **34.8%** | **78,179,073** | per-call/instruction temporary set churn |
| 2 | `unordered_map<string,DalvikValue>::clear()` | 3.48 | 13.7% | 17,832,355 | per-invoke temp map cleared |
| 3 | `HeapObject::HeapObject(const&)` | 1.06 | 4.2% | 17,746,960 | whole-heap CLONE (~82K objects) × 215 snapshots |
| 4 | `_Hashtable::_M_assign` (heap map assignment) | 1.05 | 4.1% | 215 | same clone (children = the HeapObject copies) |
| 5 | `Sha256::block` | 0.92 | 3.6% | 3,893,214 | hashing in a hot path |
| 6 | `is_subclass_of::R530Memo::~R530Memo` | 0.37 | 1.5% | 19,744,995 | memo OBJECT created/destroyed per lookup |
| 7 | `try_recursive_invoke` | 0.37 | 1.4% | 1,449,320 | method resolution walk |
| 8 | string `operator==` (2 overloads) | 0.66 | 2.6% | 762M + 447M | string-heavy keys everywhere |
| 9 | `execute_invoke_interface` | 0.49 | 1.9% | 251,829 | interpreter invoke path |
| 10 | `stage_frame_sequence` (inclusive) | 18.43 | 72% | 1 | the whole frame loop (contains all of the above) |

The interpreter itself (`fetch_decode_execute`, 449,750 entries) shows only 1.1% self —
**the DEX interpreter is NOT the dominant bottleneck** (the mission's caution was
correct). The dominant cost is **allocation/destruction churn of temporary containers
around every invoke/instruction**, plus periodic **whole-heap clones**.

## The three mission hypotheses vs the measured profile

| Hypothesis | Profile verdict |
|---|---|
| A. Method/class resolution cache | try_recursive_invoke (1.4%) + R530Memo churn (1.5%) + string eq (~2.6% shared) ≈ **~5.5% combined** — real but NOT the dominant hotspot; a resolution cache would recover a minority slice. PARTIALLY supported. |
| B. Bitmap decode cache | NOT in the chess top-10 (img decode not chess-relevant); `img_cache` already exists in the WebView engine. NOT supported as a shared top hotspot. |
| C. Incremental StateList re-pick | NOT in the top-10 (state-list pick is per-frame but far below the container churn). NOT supported by this profile. |

**Measured #1 shared hotspot = per-invoke/instruction temporary container churn
(set + unordered_map + HeapObject copies) and the periodic whole-heap clone** — a
fourth hotspot not among the proposed three.

## Decision (evidence-first, no speculative implementation)

W21 does NOT implement an optimization this session: the measured winner is not one of
the three proposed hypotheses, and implementing it correctly (identify the 78M set
creations' owning scope, replace with reusable storage, bound the heap-clone) requires
its own verified change + full 5-rep acceptance pass — started too late in the session
budget to complete honestly. Next session's ranked plan (all measured, no speculation):

1. Attribute the 78M `std::set<uint32_t>` constructions (gprof call-graph parents point
   into the invoke/arg-processing paths; `grep -n "std::set<uint32_t>" src/dex/*.cpp`
   narrows candidates) → replace with a reusable/cleared-per-thread structure or
   small_vector; expected recovery ≈ up to ~35% of chess CPU.
2. Find the 215-call whole-heap `_M_assign` clone site (frame capture/snapshot law) →
   copy-on-write or id-set diffing; expected ≈ 4-6%.
3. THEN re-evaluate A with a resolution cache against the post-fix profile.

Acceptance gates (Phase 6) still apply to any future change: same APK/binary/machine,
5 reps, median improvement ≥15-20% on the affected workload, 15/15 sha identity,
test-all green, bounded memory.
