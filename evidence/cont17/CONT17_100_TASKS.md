# CONT-17 — THE 100-TASK MARCH (user directive 2026-10-07)

"Create 100 tasks 0..100, execute each one. If an important related finding emerges
during a task, add it to that same task as a sub-task (e.g. 99_1), then go to the next."

Session lock: HEAD a0184622 · binary a8761a482a186eac (= CONT-16 record) · registry 575.
Results file: evidence/cont17/TASK_RESULTS.md (one block per task, appended live).
Sub-task rule: discoveries spawn <task>_N executed inline before moving on.

| ID | Task | Family | Status |
|----|------|--------|--------|
| T-00 | Session lock + this plan file | LOCK | PENDING |
| T-01 | GitHub #375 body re-fetch + directive-census recheck | GITHUB | PENDING |
| T-02 | GitHub #379 body re-fetch + extract any un-consumed directives | GITHUB | PENDING |
| T-03 | GitHub #380 body re-fetch + extract any un-consumed directives | GITHUB | PENDING |
| T-04 | Git lineage map CONT-1..16 → JSON (commit, binary, key events) | GITHUB | PENDING |
| T-05 | Registry integrity audit: counters, dup IDs, status vocabulary, orphans | REGISTRY | PENDING |
| T-06 | Evidence census cont1..cont16 → missing-artifact list | AUDIT | PENDING |
| T-07 | KB manifest searchlight-compliance recheck (no bulk import) | AUDIT | PENDING |
| T-08 | F-NEW-266 protection check: both dispatch sites + probe + registry intact | PROTECT | PENDING |
| T-09 | CONT-16 fix re-verify: f266 6/6 + f259g 12/13 at current binary | VERIFY | PENDING |
| T-10 | F-NEW-265 ARM-1 source trace: Lvs0.c null CharSequence producer | F-265 | PENDING |
| T-11 | F-NEW-265 ARM-2 law: deferred-throw continuation unwinding probe | F-265 | PENDING |
| T-12 | F-NEW-265 ARM-3 law: null-Throwable report path (Lel0.Y) | F-265 | PENDING |
| T-13 | F-NEW-265 fix design: generic upstream law (no R8 names) | F-265 | PENDING |
| T-14 | F-NEW-256 → SUPERSEDED-BY-EVIDENCE linkage to 265 | REGISTRY | PENDING |
| T-15 | R-NEW-381 linkage: dooz v23 first-frame → 265 chain | REGISTRY | PENDING |
| T-16 | 264d LAW-A read-your-mutation (K1) design + implement | 264d | PENDING |
| T-17 | 264d LAW-B iterator write-back (K2/K11/K12) design + implement | 264d | PENDING |
| T-18 | 264d LAW-C Java-8 default methods (K13/K16/K17/K18) design + implement | 264d | PENDING |
| T-19 | 264d LAW-D deque views (K4/K5) design + implement | 264d | PENDING |
| T-20 | 264d LAW-E hash view coherence (K6/K9) design + implement | 264d | PENDING |
| T-21 | 264d LAW-F subList/Stream (K3/K15) design + implement | 264d | PENDING |
| T-22 | ONE REBUILD with all accumulated engine changes | BUILD | PENDING |
| T-23 | fcol probe re-run at new binary → record row flips | 264d | PENDING |
| T-24 | F-NEW-265 fix verify: dooz live run at new binary (measure advance?) | F-265 | PENDING |
| T-25 | F-NEW-265 registry flip + evidence (or honest BLOCKED note) | F-265 | PENDING |
| T-26 | #375 partial: ViewPager mCurItem exact-identity gate | 375 | PENDING |
| T-27 | #375 partial: Fragment host law A/B on one native+fragment app | 375 | PENDING |
| T-28 | F-NEW-084 halt-cap bounded-law design (MutexImpl.spin family) | 084 | PENDING |
| T-29 | F-NEW-229 CL MATCH_PARENT spec law + probe | 229 | PENDING |
| T-30 | R-NEW-001 live re-verify at HEAD binary | SWEEP | PENDING |
| T-31 | R-NEW-061 live re-verify | SWEEP | PENDING |
| T-32 | R-NEW-242 live re-verify | SWEEP | PENDING |
| T-33 | R-NEW-246 superseded-check vs F-NEW-246 Vector laws | SWEEP | PENDING |
| T-34 | R-NEW-259/260 re-verify (CONT-10 fixes landed) | SWEEP | PENDING |
| T-35 | R-NEW-279/285 live re-verify | SWEEP | PENDING |
| T-36 | R-NEW-303/331 re-read + re-run + reclassify | SWEEP | PENDING |
| T-37 | chessclock null-Uri producer attribution (RingtoneManager family) | ATTRIB | PENDING |
| T-38 | libGDX createGLSurfaceView NPE attribution (E-classify or bounded shadow) | ATTRIB | PENDING |
| T-39 | WhatsApp provider-null lattice next-arm naming at HEAD | ATTRIB | PENDING |
| T-40 | F-NEW-197 white-frontier 2-node family attribution refresh | ATTRIB | PENDING |
| T-41 | F-NEW-156 onCreate-unwind: pick ONE new face, name first divergence | ATTRIB | PENDING |
| T-42 | F-138 ScoreView hint HUD text_size=0 law + probe | SINGLE | PENDING |
| T-43 | F-143 Service.onCreate/onStartCommand minimal lifecycle law | SINGLE | PENDING |
| T-44 | F-145 capture-surface follows top-of-stack window: verify + fix if bounded | SINGLE | PENDING |
| T-45 | F-147 findViewById resolution gap (dooz v10 null receiver) | SINGLE | PENDING |
| T-46 | F-NEW-192 z-order residue: verify at HEAD, close or keep with note | SINGLE | PENDING |
| T-47 | F-NEW-218/219 JNI entry probe (GLSurfaceView20 reflection) — fresh ID | JNI | PENDING |
| T-48 | F-NEW-250 serializerOrNull chain probe at HEAD (sudokusolver) | VERIFY | PENDING |
| T-49 | F-NEW-221 R8 merged-class TypeToken dispatch re-verify at HEAD | VERIFY | PENDING |
| T-50 | SP-1 success corpus + per-title signature JSON | SUCCESS | PENDING |
| T-51 | SP-2/3/12 common-successful-chain proof artifact on one title | SUCCESS | PENDING |
| T-52 | SP-4..8 renderer-selection authority audit (FALSE_ADVERTISED candidates) | SUCCESS | PENDING |
| T-53 | DEEP-AUDIT legacy rendering path reachability proof | SUCCESS | PENDING |
| T-54 | F-NEW-205 view_tree_lifecycle_owner window-canonical cross-check | SUCCESS | PENDING |
| T-55 | F-NEW-206 traversal-order cross-check vs AOSP ViewRootImpl | SUCCESS | PENDING |
| T-56 | F-NEW-207 final visual gate hardening matrix | SUCCESS | PENDING |
| T-57 | F-NEW-204 unconditional std::cerr/cout audit in shadows | AUDIT | PENDING |
| T-58 | F-NEW-214 logs-as-data law: distill run logs into bounded records | SUCCESS | PENDING |
| T-59 | dooz anchor x3 byte-identity at final binary | BATTERY | PENDING |
| T-60 | microtimer anchor x3 | BATTERY | PENDING |
| T-61 | unote anchor x3 | BATTERY | PENDING |
| T-62 | gmdice anchor x3 | BATTERY | PENDING |
| T-63 | opencalc anchor x3 | BATTERY | PENDING |
| T-64 | chess anchor x3 | BATTERY | PENDING |
| T-65 | f259 probe 7/7 | BATTERY | PENDING |
| T-66 | f259g probe (expect ≥12/13, no regression) | BATTERY | PENDING |
| T-67 | f266 probe 6/6 | BATTERY | PENDING |
| T-68 | negatives 19/19 | BATTERY | PENDING |
| T-69 | skill selftest 13/13 | BATTERY | PENDING |
| T-70 | gate A probe (available families) | BATTERY | PENDING |
| T-71 | six-game validation x3 byte-identity | BATTERY | PENDING |
| T-72 | Telegram forkgram re-verify at final binary | BATTERY | PENDING |
| T-73 | tictactoe_emmanuel census refresh (JNI entry unchanged?) | BATTERY | PENDING |
| T-74 | 14-APK census spot re-verify (2 APKs) | BATTERY | PENDING |
| T-75 | independent Compose APK run from corpus | BATTERY | PENDING |
| T-76 | non-Compose Kotlin/R8 APK run from corpus | BATTERY | PENDING |
| T-77 | PHASE-18 exception-classified census on the above runs | BATTERY | PENDING |
| T-78 | registry rows T-81-pick-1 (highest-value PENDING row) | REGISTRY | PENDING |
| T-79 | registry rows T-81-pick-2 | REGISTRY | PENDING |
| T-80 | registry rows T-81-pick-3 | REGISTRY | PENDING |
| T-81 | registry rows T-81-pick-4 | REGISTRY | PENDING |
| T-82 | registry rows T-81-pick-5 | REGISTRY | PENDING |
| T-83 | registry rows T-81-pick-6 | REGISTRY | PENDING |
| T-84 | registry rows T-81-pick-7 | REGISTRY | PENDING |
| T-85 | registry rows T-81-pick-8 | REGISTRY | PENDING |
| T-86 | registry rows T-81-pick-9 | REGISTRY | PENDING |
| T-87 | registry rows T-81-pick-10 | REGISTRY | PENDING |
| T-88 | stale CONT-16 backlog statuses updated in place | REGISTRY | PENDING |
| T-89 | status_counts refresh + counter reconciliation | REGISTRY | PENDING |
| T-90 | emergent sub-task slot (auto-assign first spawned sub-task) | SLOT | PENDING |
| T-91 | emergent sub-task slot | SLOT | PENDING |
| T-92 | emergent sub-task slot | SLOT | PENDING |
| T-93 | emergent sub-task slot | SLOT | PENDING |
| T-94 | emergent sub-task slot | SLOT | PENDING |
| T-95 | CONT-17 report section A: lineage + lock | REPORT | PENDING |
| T-96 | CONT-17 report section B: task ledger + evidence | REPORT | PENDING |
| T-97 | CONT-17 report section C: roots closed/flipped | REPORT | PENDING |
| T-98 | CONT-17 report section D: next frontier + worklog + commit | REPORT | PENDING |
| T-99 | Final verification pass: report complete, worklog appended, commit pushed | REPORT | PENDING |

## Execution rules

- One law = one generic fix + probe + regression slice. No app-specific code, no R8-name
  tables, no suppression, no budget inflation, no source-only status flips.
- Engine changes accumulate → ONE rebuild (T-22) → probes → anchors → registry.
- Every registry flip needs fresh runtime evidence at the current binary.
- Honest statuses only: DONE / PARTIAL / BLOCKED(+reason) / NOT-APPLICABLE / FAILED.
