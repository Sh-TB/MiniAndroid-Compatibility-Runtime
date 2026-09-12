# G06–G08 FINAL REPORT — INTERACTION / LIFECYCLE / MULTI-ACTIVITY CLOSURE

Recorded 2026-09-06 at campaign HEAD 9e99a74c. Rule 0.1 vocabulary only.

## A. Baseline

```text
Session-start HEAD: 67812290 (main, clean) — origin/main SYNCED
G04+G05 evidence published at campaign start:
  Issue #8 comment 5558532580 (payload prepared in the prior session)
Battery at baseline: ALL PASS (31 stages) — reproduced after a full sandbox
wipe (runtime rebuilt; fixtures re-frozen SHA-exact)
G01–G05 frozen hashes reproduced byte-identically:
  EXT-01 3-run 142238fd92b69e11 · EXT-02 frame_001 e242ac1e9c8cc224
  density-matrix 351340a7a92e645c
```

## B. G01–G05 audit (current-HEAD, blind re-verified)

| Layer | Evidence at 67812290 | Status |
|---|---|---|
| G01 typography | 9/9 golden + 3-run byte-identity | verified |
| G02 interaction | 12/12 golden + frozen frame hash | verified |
| G03 resources | 48/48 config · 42/42 core · 18/18 hostile · 18/18 encoded-value | verified |
| G04 drawable/image | density oracle 11/11 · hostile 24/24 | verified |
| G05 layout/measure | 24/24 law battery · goldens intact | verified |

Residuals: FIND-G06AUDIT-001 (resource_trace not auto-built by battery —
NON-BLOCKING, FIXED in 7ba05034) · FIND-G06AUDIT-002 (rebuild-from-clean now
proven — NON-BLOCKING, evidence) · FIND-G06AUDIT-003 (aapt2 typed COLOR
background values dropped — G03/AXML layer, FIXED in a0ac4544, regression-
covered by the G06 golden) · FIND-G06AUDIT-004 (LinearLayout margin
placement law, both axes — G05 layer, FIXED in a0ac4544, regression-covered
by all goldens + layout dumps). None deferred.

## C. G06 findings + implementation

| ID | Finding → Fix (commit) | Status |
|---|---|---|
| FIND-G06-001 | No generic MotionEvent pipeline — tap was a direct performClick | FIXED — TouchDispatcher (7ba05034) |
| FIND-G06-002 | No pressed state, no state-list drawable switching (input→state→render chain missing) | FIXED — setPressed law + StateListDrawable per-frame re-pick (7ba05034) |
| FIND-G06-003 | hit_test/response ignored `enabled` | FIXED — disabled law: consumes-without-response (7ba05034) |
| FIND-G06-004 | No focus/focusable/selected state machine | FIXED — focusTaken law (UP focus suppresses click), selected state (7ba05034) |

Laws ported (android-14.0.0_r2): View.java L17044-17047 touchable;
L17049-17057 disabled; L17113-17125 DOWN press + long-press arm;
L17133-17169 UP post(PerformClick) + UnsetPressedState(PRESSED_STATE_
DURATION=64ms); L17140-17143 focusable-in-touch-mode; L17172-17184 CANCEL;
L17198-17208 MOVE-outside touch slop (8dp→21px @420dpi); CheckForLongPress
mHasPerformedLongPress suppression; ViewConfiguration TAP_TIMEOUT=100.

Verification: input_pipeline_law_test 45/45; G06 interaction golden 21/21
(real-toolchain fixture g06_interaction, real DEX listeners): frame_000
#2196F3 → frame_001 pressed #FF5252 (state VISIBLE) → frame_002 #2196F3 +
"Taps: 1" (queued PerformClick mutated app state); disabled tap: 3 frames
byte-identical; 3-run determinism (frame SHAs identical).

## D. G07 findings + implementation

| ID | Finding → Fix (commit) | Status |
|---|---|---|
| FIND-G07-001 | No runtime-driven onPause/onStop/onDestroy; finish() set DESTROYED synchronously skipping every callback | FIXED — finish() = REQUEST; cascade onPause→onStop→onDestroy via real DEX at frame boundaries (83ebbf3f) |
| FIND-G07-002 | No explicit PROCESS_CREATED→…→DESTROYED machine | FIXED — LifecycleController with AOSP-guarded transitions + restart law + evidence trace (83ebbf3f) |
| FIND-G07-003 | HandlerShadow::drain_ready was HEAD-GATED FIFO — a due message queued behind a not-due entry NEVER fired | FIXED — MessageQueue.next (when, enqueue-seq) law (83ebbf3f) |

Boot lifecycle: onStart/onResume dispatched through try_recursive_invoke on
the launcher class (REAL bytecode — 16 instructions on the fixture; the
framework stub answers for non-overriding apps — super-class law).

Verification: lifecycle_law_test 22/22; G07 lifecycle golden 16/16 (fixture
g07_lifecycle): the app's own mark() DEX code writes C/S/R/P/H/D — launch
frame "CSR", post-finish frame "CSRPHD"; cascade callbacks 16 instructions
each; lifecycle_trace.json = canonical order, timestamps monotonic; tick
chain (postDelayed 250ms self-limiting 3) steps across frame boundaries;
3-run determinism.

## E. G08 findings + implementation

| ID | Finding → Fix (commit) | Status |
|---|---|---|
| FIND-G08-001 | has_pending_intent()/take_pending_intent_target_class() DEAD CODE — startActivity recorded an Intent nothing consumed; second Activity never instantiated | FIXED — consume_pending_intent() at frame boundaries: A.onPause → B.onCreate(Intent) → B.onStart → B.onResume → A.onStop (TransactionExecutor law), all real DEX (38f9f202) |
| FIND-G08-002 | No Activity stack / back navigation | FIXED — ActivityShadow stack (push/pop/restore); finish() pops and restores the previous entry via restart law (38f9f202) |
| FIND-G08-003 | No A.onPause→B.onCreate→…→A.onStop transition order | FIXED — implemented + asserted in the golden (callback records with instruction counts) (38f9f202) |
| FIND-G08-004 | No setResult/onActivityResult result delivery | FIXED — startActivityForResult captures request code; setResult recorded; onActivityResult delivered BEFORE onStart (Activity.java law) (38f9f202) |
| FIND-G08-006 | IntentShadow never registered on the cmd_run registry (legacy path only) — Intent.<init>/setClassName/putExtra silently no-op'd | FIXED — registered (38f9f202) |
| FIND-G08-007 | startActivityForResult consumed by the legacy not_handled fall-through before the real handler | FIXED — dispatch order (38f9f202) |
| Crash | pop_activity_record read stack_.back() on an emptied stack (UB → std::length_error abort) | FIXED — popped record IS the restore source (38f9f202) |

Verification: G08 navigation golden 17/17 (fixture g08_navigation, TWO real
DEX activities): pixel-real window switch (frame_002 zero A pixels, B's red
button present; frame_004 A restored); B.onCreate = 34 real instructions
reading getIntent().getStringExtra("greet")="hello" + getIntExtra("num")=7 →
renders "hello:7"; result contract request 42 + RESULT_OK(-1) delivered
through real-DEX onActivityResult (17 instructions) → A renders "R42:-1";
hostile intents (implicit intent, no component) → named ACTIVITY_NOT_FOUND
record, no crash; 3-run determinism.

## F. AOSP laws transferred (sources at /home/z/corpus/aosp_laws/, android-14.0.0_r2)

| Law | Source anchor |
|---|---|
| Touchable = CLICKABLE ∨ LONG_CLICKABLE; disabled consumes-without-response | View.java L17044-17057 |
| DOWN → setPressed + checkForLongClick(500); UP → post(PerformClick) + UnsetPressedState(64ms); focusTaken suppresses click; CANCEL/MOVE-outside cleanup | View.java L17113-17208 |
| PRESSED_STATE_DURATION=64, TAP_TIMEOUT=100, longPress=500, touch slop 8dp | ViewConfiguration.java L72/L122 |
| StateListDrawable first-match-in-document-order re-pick per state change | StateListDrawable.getStateDrawableIndex |
| Launch: performLaunchActivity(onCreate) → onStart → onResume; onPause FIRST on switch; onStop LAST | ActivityThread.java L3653/L4986/L5152/L5408 + TransactionExecutor |
| finish() = request; cascade at frame boundary; destroy from STOPPED | Activity.finish + handleDestroyActivity |
| onActivityResult immediately before onStart/onResume on return | Activity.java contract L5553ff |
| MessageQueue dispatch in (when, enqueue-seq) order | os/MessageQueue.java next() |

## G. Commit-by-commit implementation

| Commit | Content |
|---|---|
| c3a083e4 | Initial audit (G01–G05 blind re-verification + capability matrix) |
| 7ba05034 | G06 input pipeline: TouchDispatcher + StateListDrawable + 45-check law battery + --tap CLI + FIND-G06AUDIT-001 battery fix |
| a0ac4544 | G06 golden: g06_interaction fixture + 21-check comparator + FIND-G06AUDIT-003/004 fixes |
| 83ebbf3f | G07 lifecycle: state machine + real-DEX callbacks + finish cascade + FIND-G07-003 queue law + golden 16/16 + 22-check battery |
| 38f9f202 | G08 navigation: intent consumption + stack + result/back + FIND-G08-001/006/007 + crash fix + golden 17/17 |
| 9e99a74c | §18 hostile battery 16/16 + EXT-08 corpus |

## H. Test battery — 46 named stages ALL PASS at 9e99a74c

```text
build ×2 · semantic 14/25/57 (96/96) · MUTF-8 14/14 · resource-config 48/48
resource core law 42/42 · resource hostile 18/18 · LinearLayout/MeasureSpec 24/24
G04 hostile 24/24 · G06 input pipeline law 45/45 · G07 lifecycle law 22/22
G06-G08 hostile 16/16 · encoded-value 18/18 · helloworld 26 · tictactoe 8
EXT-01 run + typography 9/9 · EXT-02 long-press 12/12 · density oracle 11/11
G06 fixture + interaction golden 21/21 + 3-run determinism
G07 fixture + lifecycle golden 16/16 + 3-run determinism
G08 fixture + navigation golden 17/17 + 3-run determinism
corpus fetch hash-verified + 3/3 runs
```

## I. External APK corpus

| ID | APK | SHA-256 | Capability |
|---|---|---|---|
| EXT-01 | HelloWorldSelfAware 1.1.0 (Appliberated) | 009b4671…cc41 | typography + long-press goldens |
| EXT-02..04 | SimpleStopwatch 26 / gmdice 8 / MicroTimer 8 | hash-verified via scripts/test/fetch_corpus.py | boot/render regression |
| EXT-05 | fr.neamar.kiss 3.26.0 vC 224 | da6ab0b1…98c9 | AppCompat boundary |
| EXT-06 | org.fossify.notes 1.7.0 vC 13 | 5a56e0e3…bced | NOT APPLICABLE — Compose |
| EXT-07 | net.gsantner.markor 2.16.1 vC 163 | 3f9f260d…84b9 | classic Views; AppCompat boundary |
| EXT-08 | org.connectbot 11009000 (F-Droid) | 191e6990…742f | real multi-Activity app; boots Status:SUCCESS, real DEX; AppCompat shell boundary applies (same as EXT-05/07) |
| G06-FIX | g06_interaction (project, aapt2 2.20-14304508 + ECJ + D8; per-build SHA in build log — 85062c5f…3e40 at freeze) | — | tap/press/state-list/disabled laws with real DEX listeners |
| G07-FIX | g07_lifecycle (project toolchain; 8bdab41c…3841e at freeze) | — | lifecycle machine with real DEX callbacks |
| G08-FIX | g08_navigation (project toolchain; c17cb57c…700c at freeze) | — | two-Activity Intent/result/back with real DEX |

Corpus honesty: fixtures are real APKs built by the real Android toolchain
(provenance = in-repo sources + build logs); zero fixture-specific branches
in the runtime (grep-auditable: no "g06_"/"g07_"/"g08_" in src/).

## J. Runtime evidence

Canonical pipelines proven end-to-end on real DEX + virtual-clock frames:
input (DOWN→pressed→UP→queued PerformClick→app state mutation→render);
lifecycle (onCreate→onStart→onResume→…→onDestroy, each via DEX interpreter);
navigation (A→Intent→B→setResult+finish→onActivityResult→A restored) —
all with per-frame SHA-256 and JSON manifests (touch_trace, drains,
finish_cascade, lifecycle_trace.json).

## K. Visual evidence

G06 golden: pressed state VISIBLE (#FF5252 fills the button mid-gesture) +
counter mutation; disabled button visually inert. G08 golden: pixel-real
window switch (A's green button 126235 px → 0 px; B's red button 123268 px;
A restored 126235 px). All frames + manifests reproducible from HEAD.

## L. Determinism evidence

3-run byte-identity for every new golden (G06 tap, G07 finish cascade, G08
navigation — frame SHAs identical) + all prior frozen hashes unchanged
(EXT-01/EXT-02/density-matrix). No sleeps: the HandlerShadow virtual clock
is the ONLY time source.

## M. Hostile/security evidence

16 new §18 checks: extreme/out-of-window coordinates; 512 repeated DOWNs
(queue bounded); CANCEL + UP floods (zero clicks); unknown framework-token
flood; 1000 hostile re-launches (all rejected + recorded); zombie
transitions post-DESTROY (immutable); 4096-entry queue drained under the
64-pass bounded-iteration cap. Prior hostile layers unchanged (18+24/24).

## N. Regression evidence

46/46 stages ALL PASS after every implementation unit; G01–G05 goldens and
frozen hashes byte-identical; two G03/G05-layer defects found during the
campaign were fixed with regression coverage instead of deferral.

## O. GitHub evidence

See the campaign evidence comments on Issue #8 (direct URLs in the final
message + scripts/maintenance/comment_urls.json). Every commit pushed to origin/main
and verified via ls-remote.

## P. Remaining gaps

**Blocking:** none.

**Non-blocking boundaries (explicit, evidence-backed):**
1. AppCompatDelegateImpl shell (KISS/Markor/ConnectBot blank windows) —
   unchanged G06+ boundary, root-caused in G04+G05.
2. NinePatch chunk stretching — still queued behind the shell.
3. Implicit-intent resolution (action/category matching) — the runtime
   records ACTIVITY_NOT_FOUND for component-less Intents; no PackageManager
   matching law yet.
4. System back-gesture/key events — back is proven via finish() (the app's
   own path); KEYCODE_BACK dispatch is a separate input path.
5. Multi-touch / pointer isolation — single-pointer model.

**Researched only:** Choreographer vsurface pipelines; activity
launchMode/taskAffinity laws.

**Future:** AppCompat shell emulation (unlocks EXT-05/07/08 content).

**Not applicable:** Compose UI (EXT-06) to the classic View pipeline.
