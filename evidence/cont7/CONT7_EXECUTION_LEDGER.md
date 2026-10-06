# CONT-7 EXECUTION LEDGER — CURRENT-HEAD RECONCILIATION + UNSAFE/SEMAPHORE ROOT FIX

HEAD at execution: `e172fd7b` (working tree CONT-7) · FINAL BINARY SHA16: `382e595771901c00`
SKILL VERSION: manifest at docs/execution-skill/skill_manifest.json · SKILL SELFTEST: **13/13 PASS**
LAW-001: WIRED as gate law 0 (16-verdict contract 1.1, pre-install scope check) — verified this wave

## 1. SECTION 8 ANSWER — Unsafe dispatch (PROVEN VERIFIED_CURRENT)

The externally reported chain (`Unsafe.getObjectVolatile → REC-MISS → null volatile state → Semaphore ISE`, depth 36) **does not reproduce at current HEAD** — it predates the current dispatch wiring. Live proof with new bounded diagnostics (MINIANDROID_R337_TRACE=1):

```
[R337-UNSAFE] get obj=253 off=16 key="Ltp1;->_state$volatile" -> REF o171 caller=Ltp1;.j
[R337-UNSAFE] cas obj=761 off=80 cur=REF o372 exp=o372 upd=o883  (real CAS on real state)
```

The absent-DEX → bridge_to_api → R337 shadow law (directive §9's desired semantic law) is ALREADY the implemented generic behavior: `try_recursive_invoke` DEX-miss → `[REC-MISS]` diagnostic → hierarchy walk → `bridge_to_api` → `try_shadow_dispatch` → family handlers. No fix needed; the null-volatile face was fixed by earlier waves (R-NEW-337/345/395 + F-NEW-160 field identity). Recorded VERIFIED_CURRENT with instrumentation, not re-fixed (no duplicate root).

## 2. THE LIVE ROOT — F-NEW-251 (ROOT-CAUSED-FIXED, generic)

The dooz ISE ("The number of released permits cannot be greater than 1", `Lek1;.b pc=268`, depth 37, 17 in-flight errors) was NOT the Unsafe dispatch — it was **split-brain heap field storage**:

* interpreter iput/iget + Unsafe R337 → S134 qualified key `Lek1;->_availablePermits$volatile`
* AtomicShadow `Atomic*FieldUpdater` family (M4 F-028d) → **bare name** `availablePermits$volatile`

Two slots for one logical field: lock moved the qualified slot 1→0; the release entry `getAndIncrement` read the STALE bare slot (pre=1), wrote a parallel slot, and the kotlinx decomposed-permits guard then read the qualified slot and fired. Branch evaluation was proven FAITHFUL at runtime (`[C7-IF] if-le pc=249 v4=0 v5=1 taken → 260`) — the STATE diverged, not the branch.

**Fix (one point, generic)**: `DalvikHeap` field-key resolver (engine-installed): every bare-name heap field access from ANY layer resolves through the DEX instance-field tables of the class chain to the interpreter's qualified slot; engine-synthetic fields (`__*`, `array[i]`), framework-owned objects and non-DEX names keep bare keys (S134 law preserved).

**A/B (§12)**: BASE errors=17, ISE ×17 → PATCH ISE occurrences = **0**, errors=6. dooz 3-run byte-identical `d602648e8e401895` = the recorded dooz anchor SHA (zero visual drift, determinism preserved). NOT called "fixed" beyond evidence: dooz verdict stays DEFAULT_BACKGROUND_ONLY (honest) — the next face is a separate root (F-NEW-252).

## 3. SEPARATE ROOTS (§13 discipline)

* **F-NEW-252 (CLASSIFIED, P1)**: Compose Snapshot tracking IAE "Only add dependencies during a tracking" (`Lng0;.a pc=2 → Lel0;.Y pc=26 → Lt4;.dispatchDraw pc=148`) — the dooz draw frontier now; source-first next wave with a synthetic tracking-block probe. NOT fixed this wave.
* Dispatchers.Main ("Module with the Main dispatcher is missing") — not yet reached at HEAD (the run dies earlier); remains a tracked frontier.

## 4. REGRESSION BATTERY (§23) — ALL GREEN at binary 382e595771901c00

| Gate | Result |
|---|---|
| Anchors ×3 | 5/5 BYTE-IDENTICAL: opencalc `e364b001`, chess `b5a7a35d`, dooz `d602648e`, microtimer `da73010a`, unote `4f1a9e4e` |
| User goldens | 4/4 PASS (2048 / snakedeluxe / minicraft REAL_APP_CONTENT, helloworld L6) |
| Gate A probe | 97 PASS / 0 FAIL / 2 INFO |
| Negatives | 19/19 PASS |
| Reinstall matrix | 8/8 PASS |
| Uninstall proof | ALL PASS |
| Skill self-test | 13/13 PASS |

## 5. GOLDEN ABI CENSUS (§5 — from ACTUAL APK bytes, never package names)

`evidence/cont7/golden_abi_census.json` — ELF machines verified from real `lib/<abi>/*.so` headers:
dooz **MIXED** (183=AArch64, 3=x86, 40=ARM ELF32) IN-SCOPE via x86_64 · chess **MIXED** (183, 3, 40, 62=x86-64) IN-SCOPE · minicraft / snakedeluxe / sudokusolver / microtimer / unote / opencalc **PURE_DEX** IN-SCOPE. Zero ARM-only titles in the recorded set → zero census flips.

## 6. HONEST LIMITATIONS (NOT COMPLETE)

* **PENDING**: §6 acquisition of ≥12 new in-scope APKs (games/apps/Compose/storage-heavy) — NOT run this wave; the LAW-001 gate (16-verdict contract) and SKIP statistics bucket are ready to classify them. Acquire next wave from F-Droid/upstream releases, SHA-pin, run the full §6 protocol.
* **PENDING**: second independent APK live proof for F-NEW-251 fan-out (the law is heap-central; per-APK wiring is not required, but the directive's second-APK A/B is still owed).
* **PENDING**: §4 full 25-item achievement reconciliation → recorded as continuation work (the control-system files are marked HISTORICAL in-repo; CAMPAIGN_STATE.md is the live source; no contradiction found in the read subset).
* **PENDING**: R8 class-identity matrix (§14) — the dooz evidence STRENGTHENS conclusion A (R8 names are valid; the bug was generic field identity), but the 2-Compose-APK causal matrix is owed.
* **CLASSIFIED, open**: F-NEW-252 (Snapshot tracking), F-NEW-250 (serialization), Dispatchers.Main, and the ranked P0-P3 closeout set from CONT-5.
* External KB (§18): not imported this wave (no root added from it); F-NEW-251 originated from local runtime evidence only.

---

# WAVE 2 — F-NEW-252 ROOT CAUSE + DOOZ REAL EXECUTION (2026-10-06)

HEAD at execution: `07a2d538` (code base) · FINAL BINARY SHA16: `5006834b2d2ae63b` (base `382e595771901c00`)
SKILL VERSION: docs/execution-skill/skill_manifest.json · SKILL SELFTEST: **13/13 PASS** (after re-staging the two probe APKs lost in the environment reset — fixture builds, byte-deterministic)
LAW-001: fresh byte-level census re-verified (ELF e_machine from real lib/ entries): dooz MIXED(3/40/62/183) IN-SCOPE, chess MIXED IN-SCOPE, 2048/snakedeluxe/minicraft/microtimer/unote/opencalc PURE_DEX IN-SCOPE; zero ARM-only titles, zero flips.

## 1. SECTION 3 — DOOZ BASELINE (before any code change)

APK io.github.yamin8000.dooz_23.apk sha256 `299eab21…362b` (v23; full-abi-tree MIXED). Install OK; launch RESUMED; baseline reproduced the registered F-NEW-252 face exactly: IAE "Only add dependencies during a tracking [block]" thrown via R8 throw-helper `Lng0;.a` pc=2, propagated `Lyl;.z@268 → Lpz0;.L0 → … → Lel0;.i@4 → Lel0;.Y(Throwable)@26 → Lt4;.dispatchDraw catch@144 rethrow@148` → APP BOUNDARY ×3; APP_DRAW_OPS=0; verdict DEFAULT_BACKGROUND_ONLY. Evidence: `evidence/cont7/dooz_wave2_baseline.json`.

## 2. SECTION 2 — F-NEW-252 FIRST DIVERGENCE (proven, not the final exception)

Chain (static DEX decode + runtime PARAM-TRACE/FIELD-TRACE):
1. `Lt4;.dispatchDraw` pc=45-46: `const/4 v5,0` + `invoke-virtual {v4,v2,v5} Lel0;.i(Ldi;Lrc0;)V` — the APP passes **null** as the draw-state param (real Android semantics).
2. `Lel0;.i` pc=4 passes it through to `Lpz0;.L0`; **PARAM-TRACE: p2 = NULL_REF(t=8) at entry** (param marshalling correct — F-030 already handles the int-0→null boundary).
3. `Lpz0;.L0` pc=34 stores the null into the draw-context holder `Lkc;.c` (`iput-object v7,v1`; FIELD-TRACE: receiver obj#5223). **Storing null is the app's own law.**
4. `Lyl;.z` reads `Lkc;.c` (pc=14) — **R-NEW-414 treated the PRESENT NULL_REF entry as "missing" and fabricated `new Object`** (the declared type), then the nested `.r` read fabricated `new Lfj;` (isTracking=false).
5. Because v2 was now non-null, the app's own null-guard (`if-eqz v2 →+345`, pc=258) did NOT skip the tracker block → isTracking=false → `Lng0;.a("Only add dependencies during a tracking block")` → IAE.

**Semantic law**: ART reads an explicitly-written null field AS NULL (null passes check-cast; the app's null-guard then avoids the tracker path). The engine's initializer-materialization law overrode executed bytecode with a fabricated default.

## 3. GENERIC FIX (no app-specific patches — section 12)

**F-NEW-252 explicit-null-beats-initializer law** (dalvik_engine.cpp, R414 read-side, one point): a heap ENTRY holding NULL_REF is an explicitly written null → reads null; materialization only for ABSENT entries / dangling refs. Chess `ContentFrameLayout.mDecorPadding` (the original R414 case = ABSENT entries on an inflater-materialized object) unchanged — anchors byte-identical. Considered and dropped: a param-slot-integrity law in get_register (0 firings — the param marshalling was already correct; removed per minimalism).

## 4. SECTIONS 4/5/6 — DISPATCHERS.MAIN MECHANISM, R8 IDENTITY, SERVICELOADER

- **R8 class identity: NOT_ROOT_CAUSE.** The entire R8-renamed chain executed correctly; the divergence was a heap-read law. The proposed `Lv;.o` intercept was NOT added; no R8-name mapping was touched.
- **Dispatchers.Main mechanism (source + APK evidence):** dooz v23 bundles R8-RENAMED service entries — `META-INF/services/e6` → `m6` (= MainDispatcherFactory → AndroidDispatcherFactory) and `META-INF/services/pr`. The engine's S102 law reads META-INF/services/<name> from real APK entries, so renamed contracts ride the same generic mechanism. Dispatchers.Main itself remains UNREACHED (blocked by F-NEW-253); no fix owed this wave.
- **ServiceLoader synthetic probe (section 6):** SLPOS initially FAILED (hasNext=false with the provider file present): the generic CollectionShadow iterator law claimed the ServiceLoader receiver and answered empty. Fixed generically: (a) CollectionShadow DECLINES receivers carrying the S102 `service` load-marker; (b) S102's iterator block accepts the ServiceLoader-typed runtime dispatch (javac emits hasNext against the receiver's runtime type) and re-stamps `__sld_service__` from the load-time `service` field (OpenJDK LazyIterator binds its service at construction — same contract). After: SLPOS PASS (provider discovered+instantiated+dispatched) and SLNEG PASS (missing provider → honest empty). Evidence: `evidence/cont7/service_loader_probe.json`.

## 5. SECTION 7 — CAS/ATOMICFIELDUPDATER CONTRACT (F-NEW-251 NOT reopened)

Directive-required synthetic contract on ONE logical field: CAS(1→0)=true read 0; CAS(1→2)=false read 0; CAS(0→2)=true read 2; updater get/set/getAndIncrement/getAndDecrement coherent — **all PASS** at `5006834b2d2ae63b`. F-NEW-251 stays ROOT-CAUSED-FIXED/VERIFIED_CURRENT; no second field resolver. Evidence: `evidence/cont7/cas_probe.json`.

## 6. SECTIONS 9/10 — DOOZ AFTER THE FIX + 3-RUN

| Run | Install | Launch | First divergence | Exception | App content | Screenshot SHA16 |
|---|---|---|---|---|---|---|
| 1 | OK | RESUMED | F-NEW-253 rememberSaveable IAE (Lxe1;.a pc=85) | 1 uncaught IAE | DEFAULT_BACKGROUND_ONLY | d602648e8e401895 |
| 2 | OK | RESUMED | same | 1 uncaught IAE | DEFAULT_BACKGROUND_ONLY | d602648e8e401895 |
| 3 | OK | RESUMED | same | 1 uncaught IAE | DEFAULT_BACKGROUND_ONLY | d602648e8e401895 |

3/3 byte-identical AND equal to the recorded dooz anchor (zero visual drift through two engine law changes). Tracking IAE: 0 occurrences (was 1 at baseline, 17 pre-F-NEW-251). Stub census IMPLEMENTED 29602→29735 (more DEX executing). Honest verdict: DEFAULT_BACKGROUND_ONLY — dooz does NOT yet produce real app content; the exact remaining blocker is proven: **F-NEW-253 (CLASSIFIED, P1)** — SaveableStateRegistry.canBeSaved rejects the app's Bundle during rememberSaveable (Bundle-contents type fidelity in the engine Bundle shadow). NOT investigated further per section-0 scope lock.

## 7. SECTION 11 — REGRESSION BATTERY at binary 5006834b2d2ae63b

| Gate | Result |
|---|---|
| Anchors ×3 (opencalc/chess/dooz/microtimer/unote) | 5/5 BYTE-IDENTICAL: e364b001/b5a7a35d/d602648e/da73010a/4f1a9e4e |
| User goldens (F-NEW-233 pixel gate) | 4/4 PASS: 2048 REAL_APP_CONTENT (owned_px=1175590, draw_ops=34), snakedeluxe REAL_APP_CONTENT (1425075, 262), minicraft REAL_APP_CONTENT (1211493, 735), helloworld canonical 83720c1028f832d0 |
| Negatives | 19/19 PASS (after re-running the gate-A probe to regenerate its results file — environment-reset artifact, not a regression) |
| Reinstall matrix | 8/8 PASS |
| Uninstall proof | install→uninstall→pkginspect "Package not installed"→reinstall OK (dooz store, live run) |
| ABI gate (LAW-001) | fresh byte-level census: zero ARM-only, zero flips; dooz/chess MIXED IN-SCOPE, six PURE_DEX IN-SCOPE |
| Skill self-test | 13/13 PASS |
| CAS synthetic (§7) | 7/7 PASS |
| F-NEW-251 proof | dooz anchor byte-identical + §7 contract green |

GATE A multiapp harness NOT re-run this wave: its staged corpus (run/diff366/hidden_sources/*) was lost in the environment reset; the install/inspect-stage surface it proves is untouched by this wave's changes (field-read + ServiceLoader-dispatch laws only), and the staged corpus is restored next wave before the next gate-A refresh.

## 8. SECTION 15 — COMPLETION STATES

- F-NEW-252: **ROOT-CAUSED-FIXED** (registry updated; 559 roots).
- F-NEW-253 (NEW): **CLASSIFIED** — SaveableStateRegistry canBeSaved / Bundle contents type fidelity; first divergence proven at Lxe1;.a pc=85; synthetic Bundle probe owed before any engine change.
- Dispatchers.Main: **PENDING** (unreached; mechanism answered from evidence, no Lv;.o hack — none needed).
- R8-identity hypothesis: **NOT_ROOT_CAUSE** (proven by the executed chain; no resolver change).
- F-NEW-251: **VERIFIED_CURRENT** (§7 contract green; not reopened).

---

# WAVE 3 — CONT-6 EXECUTION + F-NEW-253/254/255 (2026-10-06)

HEAD at execution: `2938a888` (code base) · FINAL BINARY SHA16: `daeb0aa8daaec2b3`
(deterministic repro of wave-2 binary `5006834b2d2ae63b` FIRST — byte-identical rebuild from source after the container reset, zero code delta — then the three new generic laws)
SKILL SELFTEST: 13/13 PASS · LAW-001 ABI census: zero flips (ELF e_machine from real bytes)

## 1. ISSUE #377 READ COMPLETELY + SNAPSHOT PROTOCOL

The full CONT-6 contract was read (tmp/issue377.html, committed). Snapshot
printout: **archive bytes ABSENT this container** (post-reset loss) —
Phases 1/2 (per-record reconciliation, clustering) NOT performed, honestly
recorded. `research/external-root-kb/current/MANIFEST.md` created with the
snapshot-history table and re-supply requirement. Runtime duties (Phase 4
six-game re-validation + Phase 5 discipline) WERE executed.

## 2. F-NEW-253 ROOT CAUSE (ROOT-CAUSED-FIXED) — SaveableStateRegistry / Class.isInstance

Baseline reproduction at rebuilt HEAD: IAE "Landroid/os/Bundle;@5037 cannot
be saved…" via Lxe1;.a pc=88 (message from Lpm;.A). The canBeSaved chain
proven at runtime: Lxe1;.a → Lcf1;.d (obj#3216=Lfy;) → Ldf1;.d → Lf90;.i
(obj#3194 = R8 merged-lambda Lm4;, sparse-switch selector 19) →
invoke-static Le72;.k — the platform check walks the R8-trimmed
acceptable-classes array (Serializable, Parcelable, String, SparseArray,
Binder, Size, SizeF) via **java.lang.Class.isInstance (reflection)** — NOT
instance-of bytecode (widened INSTANCEOF trace: zero Bundle-target checks;
CLASS-LAW trace captured the exact rows: Parcelable.isInstance(Bundle) →
FALSE). ROOT: dalvik_class_assignable consulted only APK-DEX + framework
Views tables; Landroid/os/Bundle; (engine shadow, no DEX class_def) had no
Parcelable edge. ART truth: Bundle implements Parcelable.
FIX (generic, two points, one law): AOSP parcel family added to
framework_class_interfaces + dalvik_class_assignable falls back to
framework_interface_closure (F-NEW-236 tables = boot-classpath metadata).

## 3. F-NEW-254 ROOT CAUSE (ROOT-CAUSED-FIXED) — platform exception chain

Next face: ISE "State is Lij0;@5405" (kotlinx Finishing Lnj0;.a; fields
_rootCause/_isCompleting/_exceptionsHolder via Unsafe offsets 336/344/352).
Lij0; extends java.util.concurrent.CancellationException (DEX class_def) —
the holder class-test (instance-of Throwable) answered FALSE because the
DEX superclass walk ends at the platform boundary and
framework_direct_superclass had no CancellationException edge.
FIX (generic): libcore exception chain added (CancellationException→
IllegalStateException + the standard family) + dalvik_class_assignable's
walk falls back to framework_superclass_of on DEX-map miss — the SAME
fallback is_subclass_of already implements; DEX+framework hierarchies now
compose into ONE walk everywhere.

## 4. F-NEW-255 ROOT CAUSE (ROOT-CAUSED-FIXED) — ListIterator shadow law

Next face: NPE "ListIterator.hasPrevious on null" at Lyl;.g pc=1746. Chain
proven: R8 Ljd1; (implements ListIterator) ctor calls List.listIterator()
(ctor pc=23) to store backing field f — CollectionShadow routed
'listIterator' to the handled_void() stub → NULL for an OBJECT-returning
method → f never stored → hasPrevious NPE.
FIX (generic, OpenJDK AbstractList.ListItr law): real listIterator()/
listIterator(int) minting F-NEW-237-compatible iterator boxes + hasPrevious/
previous/nextIndex/previousIndex cursor laws (kind-faithful element serving
through the same view/array/elements layers as next()).

## 5. SYNTHETIC PROBE (§6 discipline) — 12/12 PASS

fixtures/cont7w3_probe (w3_probe.apk, SHA 7db7ef0d…): W3-01..05 F-NEW-253
positives+honest negatives (Parcelable.isInstance(Bundle)=true; String/null
stay FALSE); W3-06..09 F-NEW-254 (CancellationException→Throwable chain,
app subclass, null negative); W3-10..12 F-NEW-255 (cursor walk,
index-start, empty-list honesty). Zero uncaught exceptions.

## 6. DOOZ RESULT (§9/§10 — honest)

| Metric | Wave 1 | Wave 2 | Wave 3 (this) |
|---|---|---|---|
| Uncaught exceptions | 17 ISE errors | 1 | **0** |
| Saveable IAE | — | 1 | **0** |
| 'State is' ISE | — | — | **0** (fixed pre-bite) |
| hasPrevious NPE | — | — | **0** (fixed pre-bite) |
| Composition | died | died | **clean to budget** |
| Stub census (implemented) | 29602 | 29735 | **34736** |
| Verdict | DEFAULT_BACKGROUND_ONLY | DEFAULT_BACKGROUND_ONLY | **DEFAULT_BACKGROUND_ONLY (honest)** |
| Screenshot SHA16 ×3 | d602648e8e401895 | d602648e8e401895 | **d602648e8e401895** (= anchor, zero drift) |

Remaining blocker registered **F-NEW-256 (CLASSIFIED)**: dispatchDraw runs
clean (AndroidOwner:draw → Lel0;.i root draw → Luc0;.g draw-manager loop)
but records ZERO canvas content ops (only Canvas.translate ×10) — the
LayoutNode/layer draw recursion face; first divergence proven, no blind
patch (synthetic Canvas-op probe first next wave).

## 7. FAN-OUT (§11)

* chess (Compose anchor): byte-identical b5a7a35d ×3 — zero drift; its own
  frontier (DEFAULT_BACKGROUND_ONLY/APP_DRAW_OPS) unchanged; it does not
  reach the saveable/listIterator paths (only 2 isInstance calls) — deeper
  fan-out owed when its frontier advances.
* sudokusolver: NO_ROOT/WINDOW_ROOT (pre-existing frontier, unchanged).
* The three laws are heap/shadow-central with zero app conditions; the
  structural genericity is proven by the 12-row synthetic probe + zero
  anchor drift. Second-APK live fan-out for F-NEW-253/254/255 stays OWED
  (recorded) until another Compose title reaches those paths.

## 8. REGRESSION BATTERY (§12) — ALL GREEN at daeb0aa8daaec2b3

| Gate | Result |
|---|---|
| Anchors ×3 | 5/5 BYTE-IDENTICAL: opencalc e364b001 / chess b5a7a35d / dooz d602648e / microtimer da73010a / unote 4f1a9e4e |
| User goldens | 4/4 PASS (2048 / snakedeluxe / minicraft REAL_APP_CONTENT, helloworld L6) |
| Gate A probe | **97 PASS / 0 FAIL / 2 INFO** (after fixture restoration — see §9) |
| Negatives | 19/19 PASS |
| Reinstall matrix | 8/8 PASS |
| Uninstall proof | ALL PASS |
| Loading probe | ALL PASS (restart persistence ×2, WAL/db + file persisted) |
| Skill self-test | 13/13 PASS |
| ABI census | zero flips; dooz/chess MIXED IN-SCOPE; others PURE_DEX |

## 9. ENVIRONMENT REPAIRS (post-reset, deterministic)

* Engine rebuilt from source twice: first rebuild reproduced wave-2's
  binary BYTE-IDENTICALLY (5006834b2d2ae63b) — clean repro proof.
* gate_a_probe.apk rebuilt (fixture build) — first attempt drifted vs the
  recorded probe (97/0/2 → 95/2/2, NAT-03/04 FAIL): the native libs were
  lost in the reset. fixtures/native_probe/build_native_libs.sh rebuilt
  libprobe.so (x86_64 SHA d5ec1f57fef3d2713958 == the recorded value,
  byte-deterministic); staged into fixtures/gate_a_probe/lib/ → probe back
  to 97/0/2 with NAT-04 real dlopen+JNI_OnLoad success. The gate-A FAILs
  were fixture-byte drift, NOT a runtime regression.
* hmap_probe.apk + loading_probe.apk rebuilt; loading + uninstall gates
  restored to ALL PASS.

## 10. HONEST LIMITATIONS (NOT COMPLETE)

* **F-NEW-256** (dooz draw-ops frontier) CLASSIFIED, not fixed — the app
  content frontier needs the Canvas-op synthetic probe first.
* **CONT-6 Phases 1/2/3**: blocked on archive re-supply (bytes absent);
  recorded in research MANIFEST + CONT6_FINAL_TABLE.
* **Second-APK live fan-out** for the three new laws: owed (chess/sudoku
  don't reach the paths at their current frontiers).
* **Gate-A multiapp harness corpus** (run/diff366/hidden_sources): still
  lost; unaffected surface; restore next wave.
* Registry: 559 → **562 roots** (F-NEW-253 upgraded to ROOT-CAUSED-FIXED;
  F-NEW-254/255 added ROOT-CAUSED-FIXED; F-NEW-256 added CLASSIFIED).
