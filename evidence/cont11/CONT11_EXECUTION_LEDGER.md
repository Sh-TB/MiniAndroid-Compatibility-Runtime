# CONT-11 / WAVE 7 — Execution Ledger
Binary lineage: clean rebuild from HEAD e99c2fbd reproduced the frozen CONT-10
binary `aed46450c103f2ea` BYTE-IDENTICALLY before any change; post-fix binary
`d701221b9bb78317` (F-NEW-264 + F-NEW-264b + F-NEW-264c + diagnostics).

## SECTION A — EXTERNAL RUNTIME FEASIBILITY (§2-§7, §13, §14)

Full survey: tmp/cont11_external_runtime_research.md (source-inspected;
cloned: A2OH/dalvik-universal, A2OH/westlake, Mihon-Runner; ART source
fetched file-by-file). Classification:

| Candidate | DEX | Kotlin | Coroutines | Android API | Compose | Real Dooz | Real pixels | Bridge size | Effort | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| AOSP ART host | YES (038/039) | YES | YES | NO (java.* only) | NO | NO | NO | full framework | high | USE-AS-ORACLE |
| A2OH/dalvik-universal | YES (035; 038 tag) | partial | untested | partial (Westlake) | NO | NO | NO | ~2,056 classes | high | PORT-SELECTED-COMPONENTS (possible) |
| A2OH/westlake | YES (real APKs) | YES | YES | YES (Views, 193K LOC AOSP Java) | NO | n/a | view-level DLST | ~30 C bridges (their OS) | 6-12 mo | USE-AS-ORACLE (architecture) |
| Robolectric | NO (JVM bytes) | YES | YES | YES (real android-all) | YES (Gradle classes) | NO | JVM-rendered | n/a (not an APK runtime) | n/a | USE-AS-ORACLE |
| Compose Desktop | NO | YES | YES | NO | YES | NO | own Skia | n/a | n/a | REFERENCE-ONLY |
| host JVM + dex2jar | converted only | lossy | lossy | NO | NO | NO | NO | n/a | n/a | REJECT (converter ≠ runtime; identity broken) |
| kotlinx.coroutines (in-APK) | executes verbatim in any correct DEX VM | — | — | Main dispatcher needs Looper/Handler | — | — | — | — | — | USE-AS-ORACLE (Apache-2.0) |
| droidsaw / DroidVM / Skydnir / AndroidRecomp | parser / manager / manager / ARM recompiler | — | — | — | — | — | — | — | — | REJECT / IRRELEVANT (parser≠runtime, manager≠runtime, ARM-recomp≠x86 Kotlin) |
| Anbox/Waydroid/redroid/Cuttlefish/Celadon | inside full Android OS | — | — | — | — | — | — | — | — | REJECT (premise: without Android OS) |

KEY MEASURED FACTS:
- ART host reuse = 11 missing layers (framework.jar, framework-res/libandroidfw,
  system_server trio, Binder, ~200 libandroid_runtime natives, HWUI/SF, Looper-
  epoll/Choreographer vsync, ViewRootImpl glue, bionic deltas, APEX, ashmem/memfd).
- Westlake prior art: the android.* framework bridge (193K LOC Java / 2,056 classes)
  is the DOMINANT cost and is INDEPENDENT of the VM choice — MiniAndroid already
  owns that layer; an external VM would keep it AND add a guest-identity boundary
  on every API call (MiniAndroid keeps guest objects in ONE heap: DalvikValue/OBJECT_REF).
- Empirical root density (MiniAndroid's own registry: 566 roots across ~12 apps)
  ≈ 1 root per 60-100 bridged framework classes — the VM swap eliminates none of them.
- NO open-source project runs real Compose APKs on a host without Android OS.
- kotlinx.coroutines: no port needed — the real library is inside the APK DEX
  (dooz carries 1.9.0; R8-renamed Ltp1;=StateFlowImpl confirmed using
  sun.misc.Unsafe CAS, no VarHandle); a correct DEX VM executes it verbatim.

## SECTION E — FINAL DECISION (exactly one)

**KEEP MINIANDROID PATH.**

Evidence: (1) no candidate provides the framework/graphics layer where
MiniAndroid's complexity lives; (2) westlake proves the bridge equals a second
runtime (2,056 classes for View apps; Compose adds more — they have none);
(3) MiniAndroid's DEX core already executes modern R8/Kotlin/Compose/coroutines
bytecode; (4) the VM swap would double the identity-boundary surface while
eliminating zero of the 566 registry roots. External projects retained as
ORACLES only (ART semantics, westlake architecture, kotlinx sources, JDK laws).

## SECTION D — MINIANDROID GENERIC PATH (this wave's fixes)

### F-NEW-264 — exception-integrity delivery law (move-exception)
- UPSTREAM LAW: ART InterpDoThrow/JVM athrow-catch — a catch handler ALWAYS
  receives the REAL in-flight java.lang.Throwable object, never null.
- FIRST DIVERGENCE (dooz draw-path investigation): the compose exception-report
  helper Lel0;.Y(Throwable) received a NULL throwable argument from its caller
  frame and NPE'd on `t.getClass()` (the R8 kotlin-report idiom), killing the
  frame chain that includes the measure/layout pass.
- FIX: move-exception delivery falls back through the engine's exception slots
  (pending → deferred → in-flight unwind) with a bounded env-gated diagnostic
  (MINIANDROID_F264_TRACE). Honest status: defensive net — the diagnostic
  proved the live dooz null-delivery takes a DIFFERENT arm (an argument
  register inside the caller frame), so this fix never fired in the probe
  suite; kept as a JVM-law guard + the diagnostic that bounds the true site.

### F-NEW-264b — stale-mirror registry fallback (collection-copy cascade)
- UPSTREAM LAW: OpenJDK ArrayList.addAll(Collection) → c.toArray(): the
  source's OWN authoritative store decides the element set, whatever layer
  owns it.
- FIX: (a) the R-NEW-464 step-0 registry read gate broadened (f101_n < 0 →
  <= 0); (b) after the contract-mismatch guard resets copied=0, a registry
  fallback consumes the source's CollectionState (kind-faithful STRING/INT/
  OBJECT). Diagnostic MINIANDROID_F264_ADDALL_DIAG (store census at entry) +
  [F264-ADDALL] line when the fallback fires.
- Honest status: defensive — the live R/S rows turned out to be the 264c gate
  (below); 264b never fired in the probe suite (kept: it is the OpenJDK law
  for the stale-mirror shape).

### F-NEW-264c — RECEIVER-BASED GATE EXTENSION (the wave's proven fix)
- UPSTREAM LAW: OpenJDK inherited-method dispatch — `class Guest extends
  ArrayList<T>` inherits addAll(Collection)/<init>(Collection); a call on a
  Guest receiver must execute the inherited contract on the receiver's OWN
  store.
- FIRST DIVERGENCE (probe-proven, [F264-ADDALL-DIAG]): the F-101/F-NEW-259b
  cascade matched the method-ref DECLARING class only ("Ljava/util/
  ArrayList;"); for a DEX-defined subclass receiver the engine's runtime
  dispatch classifies by the RECEIVER class → string match missed → the
  append was a SILENT NO-OP (probe rows R: shadow→guest size=0, S:
  guest→guest size=0 — while every plain-ArrayList receiver row fired).
- FIX: mirrors the F-097 TreeSet dispatch law — any declaring class when the
  receiver's runtime class is an ArrayList/LinkedList-family subclass
  (heap hierarchy walk via is_subclass_of).
- PROBE: fixtures/fnew259g_probe (real aapt2/ECJ/D8, apk 1a41daa1262c3169)
  — 13-row genericity matrix: H (2-hop chain walk) / I (covariant boxed
  bridge) / J (array identity) / M (empty addAll) / N (dupes) / O (boxed
  ints) / P (array elements) / Q (guest→shadow) / R (shadow→guest) /
  S (guest→guest) / T (object identity) ALL PASS post-fix; K/L honestly
  FAIL with NEW findings (see below).
- REGRESSION: dooz d602648e8e401895 ×3 (unchanged), CONT-10 f259 probe 7/7,
  anchors opencalc a976d2f9fb675cb3 / chess b5a7a35d5fe0564b / microtimer
  da73010a37dd0189 / unote 4f1a9e4e8f64fae8 all ×3 byte-identical, gate A
  98 PASS/0 FAIL/1 INFO, negatives 19/19, skill 13/13, sudoku_secuso
  (Kotlin-heavy game) 45962e018344e94d ×3 REAL_APP_CONTENT.

### New findings registered (NOT fixed this wave — honest)
- F-NEW-265 (dooz first divergence RE-ROOTED): the compose DRAW machinery is
  PROVEN CORRECT end-to-end (dispatchDraw runs per frame; the coordinator
  walk reaches InnerNodeCoordinator.performDraw; canvas.translate executes on
  the live compose-canvas wrapper; the walk faithfully honors
  `child.isPlaced` = real DEX field chain Lel0.J→Lil0.p→Lbt0.w = FALSE). The
  tree never draws because the measure/layout pass (Lzs0.m) dies MID-FLIGHT:
  a text-layout ctor (Lm7;.<init>, TextPaint/TextStyle fields) receives a
  null text CharSequence (Lkb; object constructed with a1=NULL at entry,
  caller Lvs0;.c) → the LEGAL R8 kotlin null-check (`invoke-virtual
  getClass`) throws → the engine's deferred-throw semantics let the frame
  continue (multi-NPE blast radius) → a NULL Throwable argument reaches
  Lel0;.Y → cascade kills Lzs0.m → Lt4.onMeasure. isPlaced stays false
  everywhere → 0 content draws. THE remaining dooz root is the measure-pass
  exception cascade, NOT the canvas bridge (W6's "Ljt1 never constructed"
  was a downstream consequence, not the root).
- F-NEW-259g-a: AbstractList slot `get(I)` out-of-range does not throw
  IndexOutOfBoundsException (probe row K, n=4; JDK AbstractList$Itr law).
- F-NEW-259g-b: java.util.Vector materialization NPEs (probe row L —
  Vector unimplemented; caught as NPE instead of the slot's ISE).
- F-NEW-264d (§8 collection semantic-law audit — the fat seam, 15/18 rows
  FAIL in a plain-Java probe): grouped by law —
  LAW-A read-your-mutation coherence (K1 set/remove/indexOf);
  LAW-B iterator write-back (K2 listIterator set, K11 Iterator.remove,
  K12 ListIterator.add);
  LAW-C Java-8 default-method family (K13 removeIf, K14 sort, K16
  removeAll/retainAll, K17 merge/computeIfAbsent, K18 forEach);
  LAW-D deque views (K4 LinkedList head/tail, K5 ArrayDeque peek/poll);
  LAW-E hash view coherence (K6 getOrDefault, K9 HashSet.contains);
  LAW-F missing families (K3 subList view NPE, K15 Stream NPE).
  PASS today: entrySet iteration (K7), LinkedHashMap insertion order (K8),
  LinkedHashSet order (K10).

## SECTION B — REAL DOOZ RESULT
- Before (CONT-10): DEFAULT_BACKGROUND_ONLY, 1→5+ nodes materialized, 0
  canvas ops, anchor d602648e8e401895.
- After (CONT-11): anchor d602648e8e401895 ×3 byte-identical (no visual
  change — honest). Canvas ops: 0. Pixels: background-only. The REAL
  progress is forensic: the draw path is exonerated and the true remaining
  root is precisely named (F-NEW-265) with the full runtime-proof chain.

## SECTION C — BRIDGE (if external were adopted)
Required Android APIs/classes: ~2,000-2,800 classes / 100-200K lines
(westlake-measured 2,056 classes + 193K lines for View apps; Compose adds
graphics/text/Choreographer surface). Identity boundary: EVERY API call
crosses guest↔host heap (MiniAndroid needs none). JNI: 30-60 bridge
functions (westlake) to 8,000-20,000 registrations (per-call JNI-out).
Graphics: full HWUI/Skia surface replay still required for Compose.
Estimated complexity: 6-24 months — REJECTED (see Section E).

## §12 APK MATRIX
| APK | SHA16 ×3 | Compose | Kotlin | Result |
|---|---|---|---|---|
| dooz 23 | apk 299eab21ac8b3c61 / frame d602648e8e401895 ×3 | YES | YES | DEFAULT_BACKGROUND_ONLY (F-NEW-265 root named) |
| stopwatch 6 | frame 31ddd4d5b8e6d18e ×3 | NO | YES (coroutines) | deterministic byte-identical |
| sudoku_secuso 101 | frame 45962e018344e94d ×3 | NO | YES (coroutines, heavy) | REAL_APP_CONTENT ×3 |
| sudokusolver 8 (Compose Navigation) | — | YES | YES | BLOCKED-APK-ABSENT (F-Droid fetch stalled; SHA d114d479df66b0f6 recorded, script in place) |
| blockblast 43 (independent Compose) | — | YES | YES | BLOCKED-APK-ABSENT (same) |
| f259g probe | 1a41daa1262c3169 | synthetic | — | 11/13 rows PASS post-fix |
| fcol audit probe | d607406c23fb205b | synthetic | — | 3/18 PASS (§8 matrix banked) |
| f259 CONT-10 probe | 969b267a1cd232fb (rebuild) | synthetic | — | 7/7 PASS |

## §17 F — NEXT SINGLE ROOT
ROOT: F-NEW-265 — measure/layout pass dies mid-flight on the deferred
exception cascade (null text CharSequence into the text-layout ctor +
deferred-throw blast radius + null-Throwable-to-catch-handler).
SOURCE LAW: (1) kotlin/R8 null-check contract fires ONCE at the violating
invoke and the caller's frame aborts there (ART semantics); (2) a caught
Throwable is a real object (JVM); (3) measure/layout of newly inserted
LayoutNodes gates all downstream placement (compose 1.11.4
MeasureAndLayoutDelegate/NodeCoordinator/InnerNodeCoordinator.performDraw).
FIRST DIVERGENCE: Lzs0.m (measure pass) dies with the SECONDARY NPE from
Lel0.Y(null); the primary null is Lkb's text (Lvs0.c).
GENERIC FIX (two bounded arms): (a) deferred-throw must abort the throwing
frame at the throw point (ART-faithful) instead of continuing it;
(b) the catch-handler argument must be the real in-flight throwable.
REAL APK: dooz 23. INDEPENDENT CONSUMER: any Compose app measuring text
(blockblast/sudokusolver when refetched). 3-RUN EVIDENCE: dooz ×3 at
d602648e (this wave's baseline — unchanged, the fix wave is next).
