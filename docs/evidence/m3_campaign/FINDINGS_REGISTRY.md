# MASTER-3 OPEN-ENDED FORENSIC — FINDING REGISTRY

Campaign: MASTER-3 OPEN-ENDED FORENSIC / FULL COMPATIBILITY CLOSURE
Started: session 6 (baseline HEAD 0b6f85bb, battery 59/59)
Registry law: findings are never renumbered or deleted; superseded findings stay.
Status vocabulary: RESEARCHED | OBSERVED | IMPLEMENTED | TESTED | RUNTIME-PROVEN |
VISUALLY-PROVEN | CROSS-APK VERIFIED | REGRESSION-VERIFIED | BLOCKED | OUT-OF-SCOPE |
RESEARCH-ONLY
Priority: P0 foundational/multi-APK · P1 families/visual closure · P2 breadth · P3 infra

---

## FINDING-001
- Subsystem: BUILD (toolchain reproducibility, AE gate)
- Trigger: container reset wiped /home/z/my-project/tools/aapt2 → 17 battery stages rc=2
- APK: all aapt2-built fixtures (G06/G07/G08/M3 style fixture, density matrix)
- Static evidence: scripts/build_fixture_apk.sh documents aapt2 8.13.2-14304508 provenance
- Runtime evidence: battery FAIL before restore, ALL PASS after
- Root cause: toolchain not reconstructible from the repo; undocumented manual steps
- Law: AE — "a fresh container should reconstruct the environment without manual steps"
- Fix: scripts/bootstrap_toolchain.sh (idempotent, hash-verifiable Google Maven fetch)
- Reusable scope: all future sessions; fixture builds
- Tests: battery fixture-build stages
- Status: REGRESSION-VERIFIED (59/59 after restore)
- Priority: P3
- Commit: 3ea265be
- GitHub evidence: PUBLISH BLOCKED — TOKEN ABSENT

## FINDING-002
- Subsystem: BUILD (corpus cache reproducibility)
- Trigger: miniandroid/download/ held only 3 of 25 campaign APKs after reset
- APK: microtimer, chessclock, headingcalculator, KISS, uNote, master_campaign 7
- Static evidence: fetch_corpus.py covers tests/corpus/apks.json (18) but not the 7
  wave-2 additions (registry_additions.json)
- Runtime evidence: fetch_master_campaign.py restores all 7 from f-droid frozen URLs
- Root cause: two registry files, only one had a fetch script
- Law: zero-skip law §39 companion
- Fix: scripts/fetch_master_campaign.py (idempotent, SHA-256-verified)
- Tests: hash verification output (OK per entry)
- Status: IMPLEMENTED / TESTED
- Priority: P3
- Commit: 3ea265be
- GitHub evidence: PUBLISH BLOCKED — TOKEN ABSENT

## FINDING-003
- Subsystem: DIAGNOSTICS (DEX tooling)
- Trigger: legacy scripts/dex_method_dump.py emitted only raw hex words; useless for
  branch-level forensics; my first rewrite used inverted 35c layout and single-chain
  method_idx accumulation — caught by cross-validation against androguard + the live
  AOSP instruction-formats page + the runtime's own resolution
- APK: all (tool)
- Static evidence: AOSP instruction-formats: 35c = Ag|op, BBBB@index, FEDC@regs
  ("the unusual choice in lettering… same label as in format 3rc")
- Runtime evidence: runtime resolved La/e;.h (Intrinsics) where the mis-decode showed
  Intent.putExtra — register-type consistency settled the law
- Root cause: N/A (tooling gap, not a runtime bug)
- Law: dalvik-bytecode + instruction-formats (authoritative pages fetched and parsed)
- Fix: scripts/m3_disasm.py — spec-conformant disassembler, cross-validated 28/30
- Reusable scope: all future DEX forensics
- Tests: androguard diff harness (inline), 30-method random sample
- Status: RUNTIME-PROVEN (tool-level)
- Priority: P2
- Commit: 3ea265be
- GitHub evidence: PUBLISH BLOCKED — TOKEN ABSENT

## FINDING-004
- Subsystem: HANDLER / MESSAGEQUEUE (P0)
- Trigger: microtimer tick loop never scheduled; posts with garbage delay
- APK: dubrowgn.microtimer_8 (SHA256 in corpus registry); chessclock family shares
  removeCallbacks law
- Static evidence: Lk/e.b disassembly — postDelayed(Runnable, Object token, J) — the
  hidden AOSP overload; token = boxed expires Long; removeCallbacksAndMessages(token)
  per pause; AOSP Handler.java law
- Runtime evidence: [WIDE-DIAG]+[QUEUE] traces; after fix token=378 posts enqueue and
  drain through Lk/c runnables
- Root cause: HandlerShadow.postDelayed read args[1].long_val as delay — on the token
  overload that is the token object id; delay never scheduled correctly;
  removeCallbacksAndMessages always cleared ALL posts (multi-timer unsafe)
- Law: AOSP Handler.postDelayed(Runnable, Object, long) + removeCallbacksAndMessages
  (null → all; non-null → identity match)
- Fix: enqueue_tokened + token_id on QueuedRunnable + remove_by_token
- Reusable scope: every app using token posts (Room/AlarmManager wrappers, Kotlin
  countdowns); multi-timer UIs
- Tests: battery 59/59 green after fix; microtimer tap sequence shows token posts
- Status: IMPLEMENTED / TESTED (tick visual closure still pending the delay law, see
  FINDING-008 residual)
- Priority: P0
- Commit: 3ea265be
- GitHub evidence: PUBLISH BLOCKED — TOKEN ABSENT

## FINDING-005
- Subsystem: LAYOUT (view_renderer horizontal LinearLayout law)
- Trigger: microtimer timer row renders with left Button at 1080x0 (w/h inverted vs the
  LP (wrap, match)) pushing the RoTimeControl off-screen (x=1080, w=0)
- APK: dubrowgn.microtimer_8 (programmatically built rows — K/g.<init>)
- Static evidence: K/g.<init> passes LP(-2,-1) per button; EXP095-ADDVIEW-LP logs prove
  the LP arrives intact (w=-2 h=-1); final render tree shows Button 1080x0
- Runtime evidence: EXP092-RENDER dumps (fresh sandbox runs)
- Root cause: layout_children_linear / measure path applies main-axis wrap semantics
  incorrectly for (wrap-width, match-height) children in a horizontal row — main/cross
  axes crossed for the width resolution (Button measured 1080 = full row width)
- Law: AOSP LinearLayout.onLayout/onMeasure — horizontal row: child width wrap =
  measured content; height match_parent = container content height
- Fix candidate: view_renderer.cpp layout_children_linear Pass-1 width resolution for
  (lp_width==-2, lp_height==-1) children
- Reusable scope: any app building rows programmatically (lists, custom rows)
- Tests: battery LinearLayout/MeasureSpec law (24) + G10 (23) + G11 (37) + M3
  style geometry golden; microtimer created-row geometry
- Status: TESTED (fix landed in a0d71c15; session-7 visual proof: created row
  renders Lk/g (0,0) 1080x126 with 126x126 buttons — no 1080x0 anywhere in the
  92-frame stream). CROSS-APK extension (2nd programmatic-row APK) open.
- Priority: P1
- Commit: a0d71c15
- GitHub evidence: PUBLISH BLOCKED — TOKEN ABSENT

## FINDING-006
- Subsystem: LAYOUT (dynamic addView relayout)
- Trigger: freshly created timer row laid out off-screen (x=1080) on its first frame;
  later frames correct it
- APK: dubrowgn.microtimer_8
- Static evidence: EXP092-RENDER intermediate vs final frames
- Runtime evidence: mtA/mt5 dumps — intermediate frame node pos=(1080,0) size=(0x123)
- Root cause: first layout pass after dynamic addView runs before the parent re-measure
  propagates (cross-pass invariant gap, PHASE 4 family)
- Law: cross-pass geometry invariant (MEASURE→LAYOUT→DRAW)
- Fix candidate: dynamic-addView invalidation hook
- Session-7 evidence: the created timer row's FIRST render dump (mt_fin_a line
  13647) shows Lk/g pos=(0,0) size=1080x126 — the off-screen first frame
  (x=1080) is GONE at the fixed HEAD; 92/92 frames have sane geometry.
- Status: TESTED (symptom absent at HEAD a0d71c15+session-7 work; re-open if
  another addView path reproduces it)
- Priority: P2
- Commit: a0d71c15
- GitHub evidence: PUBLISH BLOCKED — TOKEN ABSENT

## FINDING-007
- Subsystem: JAVA CORE (java.lang.Math surface, P0)
- Trigger: microtimer countdown remaining zeroed at bind; label 00:00:00; tick
  scheduling branch dead
- APK: dubrowgn.microtimer_8 (MainActivity.e compute path); any app using Math
- Static evidence: Ll/a.a + MainActivity.e disassembly — Math.ceil(D)D in the remaining
  computation; runtime Math shadow handled only min/max/abs
- Runtime evidence: MINIANDROID_WIDE_DIAG — cmpg-double read b=0.0 where 82.0 expected;
  after the fix cmpg b=82 c=0 → 1 → normalize path taken, remaining computed 122
- Root cause: unimplemented Math.ceil fell to the silent default 0.0 return — the
  "silent stub corrupts real apps" class
- Law: OpenJDK Math (ceil/floor/sqrt/pow/round/floorDiv/floorMod/trig; saturated round)
- Fix: full Math surface implemented in dalvik_engine.cpp Math block
- Reusable scope: effectively every arithmetic-using APK
- Tests: battery 59/59; microtimer label mutation 00:01:22 → 00:00:01
- Status: IMPLEMENTED / TESTED (RUNTIME-PROVEN for the MicroTimer path)
- Priority: P0
- Commit: 3ea265be
- GitHub evidence: PUBLISH BLOCKED — TOKEN ABSENT

## Residuals / next-step queue (not yet numbered)
- Tick re-post delay law: 68× delay=0 spins observed; the app's delay =
  (expires-now)%1000 (K/e.b 0x016e-0x172) — verify Ll/a.c interval semantics and
  whether the spin matches real ART (delay=0 → next-loop) or is a runtime clock gate
  artifact; after 68 spins a real delay=930 post appears (sub-second alignment).
- Row label "00:00:null" after the finish branch — Le/b.b formatter reading a null
  Long (Ll/a.c or d) in the tick path.
- SECUSO ColorStateList (F-ARGS, PHASE 2), shadow ancestry (PHASE 3), image pipeline
  (PHASE 6), shape/stroke (PHASE 7), SIMPLE VISUAL GOLDEN (PHASE 8) — per campaign plan.

---

## FINDING-008
- Subsystem: HANDLER / RENDERER (tick visual closure residual, P0 family)
- Trigger: microtimer row label renders "00:01:null" once and never re-renders per tick
- APK: dubrowgn.microtimer_8
- Static evidence: Le/b.b formatter (192 words) appends a null Long for the seconds
  part in the tick path; row RoTimeControl re-render not triggered after the first tick
- Runtime evidence: mtP/mtick1 EXP092-RENDER dumps — node=387 text="00:01:null" (1
  render); token posts (65) drain and MainActivity.e re-runs (label input computed),
  but the row subtree render is not re-emitted per tick
- Root cause (two parts):
  (a) formatter receives a null Long for the seconds component in the tick path
      (identity/propagation gap between Ll/a.d null-out in the pause branch and the
      label formatter input);
  (b) the per-tick setText on the off-screen row does not re-emit a render task
      (FINDING-005 geometry interacts: off-screen subtree render elision).
- Law: TextView mutation → framebuffer change (tick law, GATE F); null never renders
  as text in ART without String.valueOf(null) being explicit app intent
- Fix candidate: (a) trace the exact null producer via FIELD-TRACE=Ll/a + formatter
  arg dump; (b) re-render invalidation for subtree setText under FINDING-005 fix
- Reusable scope: every countdown/timer UI
- Tests: GATE F tick count + 3-run determinism once closed
- Status: VISUALLY-PROVEN (session 7). (a) fixed in a0d71c15 — String.subSequence
  + Object.toString/String.toString laws; session-7 scan: ZERO "null" texts in
  92 frames × 3 runs. (b) closed by FINDING-009/010 — per-second tick frames
  00:00:82→00:00:00 visible, finish branch red expired state rendered.
  3-run aggregate PNG SHA 2a425979ef7d32bf2acf identical; battery 59/59.
- Priority: P0 (CLOSED — GATE F evidence complete)
- Commit: a0d71c15 (+ session-7 drain-law commit)
- GitHub evidence: PUBLISH BLOCKED — TOKEN ABSENT

## FINDING-009
- Subsystem: HANDLER / LOOPER (deterministic drain termination law, P0)
- Trigger: microtimer countdown stops after ONE tick in tap mode; tick re-post
  (Runnable 410, delay=999ms, ready_at=1000001290) stranded in the queue forever
- APK: dubrowgn.microtimer_8 (same path drives every countdown/animation UI)
- Static evidence: MainActivity.e tail (0x015d-0x016a) — every tick re-posts via
  Handler.postDelayed(new Lk/c, token, (now-expires)%1000); AOSP MessageQueue.next()
  polls nativePollOnce(timeout = head.when - now) — the looper NEVER exits while
  messages are pending; it sleeps until the head's `when`
- Runtime evidence (fresh 3-tap run @ a0d71c15, /tmp/mt_r1): [QUEUE] Runnable id=410
  enqueued (delay=999ms, ready_at=1000001290ms, token=365) → next dequeue is a
  gesture token @ now=1000000361 → drain returns; tick 410 never dispatched;
  label set once per tick = "00:00:82", no per-second mutation
- Root cause: drain_quiescent's `if (drain_ready()==0) return;` treats "nothing due
  NOW" as quiescence. Real ART quiescence = queue EMPTY; a non-empty queue with a
  future head means the looper sleeps (poll timeout), then dispatches. The 1ms
  quantum added for the delay=0 spin (F-008b) cannot bridge a 999ms gap — 64-cap
  exhausts 64× before the tick becomes due, and even without the cap the drain
  returns before advancing.
- Law: AOSP MessageQueue.next — when the head message's `when` is in the future,
  nextPollTimeoutMillis = head.when - now; the loop does not terminate; dispatch
  happens when the clock reaches `when`. Deterministic model: advance the virtual
  clock to the earliest ready_at (exact, zero wall-clock), bounded by the existing
  §18 hostile-storm iteration cap.
- Fix candidate: HandlerShadow::next_ready_ms() (read-only min-peek) + drain loop
  fast-forward branch (n==0 && queue non-empty → advance_virtual(next_ready-now)
  → re-loop) + per-tick frame capture: after each dispatch round, if the
  framebuffer changed vs the last saved frame, save a tick frame (GATE F visual
  per-second mutation proof; deterministic — fixed quanta, fixed tap schedule).
- Reusable scope: every timer/animation UI (countdowns, stopwatches, marquee,
  progress bars) — anything that schedules future work from a tick
- Tests: microtimer 3-run determinism; per-tick label mutation visible in frames;
  battery 59/59 (G06/G07/G08 tap determinism goldens must not regress)
- Status: VISUALLY-PROVEN + REGRESSION-VERIFIED (session 7). Evidence: [QUEUE]
  Runnable 410 delay=999ms now dispatched via poll-timeout fast-forward;
  countdown 00:00:82→00:00:00 across 84 mutating frames; finish branch reached
  (red expired state, queue drains empty, clean return). 3×92 frames
  byte-identical (agg SHA 2a425979ef7d32bf2acf). Battery 59/59 after the G06/G07
  comparators were made stream-law-true (the old "Ticks: 1" frozen check encoded
  THIS bug — stranded future messages).
- Priority: P0 (CLOSED)
- Commit: session-7 (drain fast-forward + next_ready_ms)
- GitHub evidence: PUBLISH BLOCKED — TOKEN ABSENT

## FINDING-010
- Subsystem: VISUAL GATE (tick frame evidence missing from the tap pipeline)
- Trigger: even with ticks flowing, the frames manifest only captures gesture
  stages (DOWN pressed / post-gesture) — a per-second label mutation between
  gesture events has no frame, so GATE F "visible countdown" cannot be proven
- APK: dubrowgn.microtimer_8 (family: stopwatch, chessclock, bgclock)
- Static evidence: stage_tap saves frames only at fixed gesture points
  (execution_engine.cpp: DOWN @+20ms, post-drain); drain_quiescent never renders
- Runtime evidence: /tmp/mt_r1 manifest — 7 frames, all gesture-stage; drains
  list shows queue activity with zero corresponding frames
- Root cause: frame capture is keyed to gesture stages, not to framebuffer
  mutations during queue drains
- Law: GATE F law — a tick that mutates the label MUST be observable as a
  framebuffer change (the "TextView mutation → redraw" law); visual goldens
  require the mutating frames to EXIST, be deterministic, and hash-stable
- Fix candidate: after each dispatch round inside drain_quiescent, re-render and
  save an intermediate frame iff the framebuffer differs from the last saved
  frame (event="tick", virtual_ms recorded) — mutation-keyed, zero false frames
  when nothing changes
- Reusable scope: every future interaction golden (animation frames for free)
- Tests: microtimer run shows N≥60 tick frames with byte-identical SHAs across
  3 independent runs
- Status: VISUALLY-PROVEN (session 7): 84 mutation-keyed tick frames in the
  microtimer run (per-second label mutation), G06 gains 2 drain-mutation frames
  (PerformClick applied, then UnsetPressedState restored), G07 gains Ticks:2/3
  frames proving the finite chain law stream-level. 3-run byte-identical.
- Priority: P0 (CLOSED)
- Commit: session-7
- GitHub evidence: PUBLISH BLOCKED — TOKEN ABSENT

## GATE SCORECARD (session 6 end)
- GATE A build: PASS (bootstrap_toolchain.sh; binary builds clean)
- GATE B regression: PASS 59/59 (twice: pre-commit 3ea265be and post object-trace)
- GATE F micro-timer: PARTIAL — INSERT/Room/DEX ✓; token postDelayed ✓; Lk/c ticks
  drain ✓; remaining compute ✓ (Math.ceil law); row label mutation ✓ BUT seconds
  part renders "null" + per-tick re-render missing (FINDING-008) → NOT complete
- GATE P toolchain reproducibility: PASS (FINDING-001/002 fixes)
- GATE Q diagnostics: PASS (MINIANDROID_FIELD_TRACE / MINIANDROID_WIDE_DIAG /
  m3_disasm.py / m3_invoke_inventory.py / DUMP_CLICKABLES in tap mode pending)

## FINDING-011
- Subsystem: VIEW / ANDROIDX (keyed View tags — the ViewTree* backbone, P0)
- Trigger: dooz (AndroidX game, 1.7MB) boots SUCCESS but renders a 100% WHITE
  frame; unote/bouncy render skeleton/flat screens — every modern AndroidX app
  double-initializes its ViewTree owners
- APK: ir.yamin8000.dooz1 (androidx + lifecycle-viewmodel-savedstate); the family
  (droidify, openlauncher, tinymusicplayer, bouncy) shares the pattern
- Static evidence: androidx ViewTreeViewModelStoreOwner/ViewTreeLifecycleOwner/
  SavedStateHandleSupport cache their per-owner state via
  View.setTag(R.id.view_tree_*, owner) + View.getTag(R.id.*) — the AOSP keyed-tag
  law (View.java mKeyedTags SparseArray). grep: ViewShadow has NO tag field; the
  runtime has ZERO setTag/getTag implementation — the call silently no-ops
  (the FINDING-007 silent-stub class).
- Runtime evidence (dooz run + MINIANDROID_METHOD_TRACE="savedstate/a|d"):
  SavedStateRegistry.registerSavedStateProvider is invoked THREE times:
    (1) key="androidx.lifecycle.internal.SavedStateHandlesProvider" — OK (entry
        created),
    (2) key="android:support:activity-result" — OK,
    (3) key="androidx.lifecycle.internal.SavedStateHandlesProvider" AGAIN —
        g/b.c lookup finds entry (1) with a non-null provider → the app's own
        IAE("SavedStateProvider with the given key is already registered") →
        no handler in androidx/savedstate/a.d → 10-exception unwind cascade →
        empty window.
  The double registration is the SECOND lazy-init of SavedStateHandleSupport:
  with tags lost, androidx cannot see that the owner is already installed and
  re-creates it (real Android: the tagged cache makes the second access a no-op).
- Root cause: missing View keyed-tag API (setTag(I,Ljava/lang/Object;)V /
  getTag(I)Ljava/lang/Object; / setTag(Ljava/lang/Object;)V / getTag()) —
  androidx's owner-cache contract silently degrades.
- Law: AOSP View.java — mTag (default) + mKeyedTags SparseArray<Integer,Object>;
  getTag(key) with no value = null; values are object references with preserved
  identity (androidx check-casts and calls methods on the retrieved owner).
- Fix candidate: ViewShadow node storage {default_tag; keyed_tags map<int,tag>}
  with object-identity round-trip; dispatch for the 4 methods; silent-no-op
  eliminated (loud IMPLEMENTED status).
- Fix STATUS (session 7): TAG LAW LANDED (ViewShadow setTag/getTag both forms,
  identity-preserving; [TAG-PROBE]×11 bridge entries fire; battery 59/59). BUT
  dooz STILL renders white with the SAME double registration — the dedupe driver
  for the SavedStateHandlesProvider re-register is NOT (only) the View tag:
  the second registration arrives via the REFLECTIVE lifecycle path
  (ReflectiveGenericLifecycleObserver → c.a invokeCallbacks) while the first
  came via savedstate/a.b (performAttach/restore). The tag round-trip itself is
  implemented; the androidx lazy-init guard that should prevent the second
  attach is still unidentified (candidates: ViewTree owner getTag receiver
  identity, ViewModelProvider caching, ON_CREATE double dispatch — probes
  planted: [TAG-PROBE]/[TAG-BRIDGE] bounded diagnostics kept for next session).
- Reusable scope: EVERY androidx.library app (the dominant modern APK family)
- Tests: dooz boots past the savedstate IAE (EXCEPTION count 10→0) and renders
  non-white; battery 59/59; 3-run determinism on the new dooz frame
- Status: OBSERVED — PARTIAL FIX LANDED (tag law implemented+battery-verified;
  dooz closure BLOCKED on identifying the real second-attach driver)
- Priority: P0 (gates the whole AndroidX corpus family; GATE K breadth)
- Commit: session-7 (tag law); investigation open
- GitHub evidence: PUBLISH BLOCKED — TOKEN ABSENT

## GATE SCORECARD (session 7 — current)
- Session-7 baseline: container reset wiped aapt2 + EXT fixture; restored via
  FINDING-001/002 scripts (SHA-verified); battery 59/59 re-established at a0d71c15.
- GATE A build: PASS (59/59 battery incl. all fixture builds)
- GATE B regression: PASS 59/59 (post drain-law change; G06/G07 comparators
  upgraded to stream-law checks — old G07 "Ticks: 1" frozen-state check encoded
  the FINDING-009 bug, replaced by the finite-chain law 1→2→3 + no overflow)
- GATE C DEX: PASS (semantic + opcode law batteries unchanged green)
- GATE D resources: PASS (48+42+18+17 checks)
- GATE E layout: PASS (24+23+37 law checks + M3 style geometry 6)
- GATE F micro-timer: **PASS — FULLY CLOSED**: INSERT/Room/DEX ✓; token
  postDelayed ✓; tick chain flows (FINDING-009 poll-timeout law) ✓; countdown
  00:00:82→00:00:00 per-second visible (FINDING-010 mutation-keyed frames) ✓;
  finish branch red expired state ✓; zero "null" texts (FINDING-008a) ✓;
  row geometry sane from the FIRST frame (FINDING-005/006) ✓;
  3-run byte-identical (agg SHA 2a425979ef7d32bf2acf) ✓
- GATE G interaction: PASS (G06 21/21 + EXT-02 12 checks)
- GATE H image: PARTIAL (density matrix ✓; real-APK image golden still open)
- GATE I shape: PARTIAL (M3 style fixture ✓; 2nd-APK shape golden open)
- GATE J activity: PASS (G07 16/16 + G08 17/17)
- GATE K corpus: PASS (simplestopwatch/gmdice/microtimer SUCCESS; 25-corpus
  matrix still not exhaustive)
- GATE L determinism: PASS (3-run byte-identical at every golden)
- GATE M reproducibility: PASS (bootstrap + frozen-SHA corpus restore,
  re-executed this session after a real container reset)

---

# FORGOTTEN-NNN — END-OF-CAMPAIGN "WHAT DID WE MISS?" PASS

Independent audit performed after the forensic closure work. Each item is
evidence-grounded (runtime traces, static scans, or battery behavior from this
session). These are items the campaign plan did NOT explicitly list.

## FORGOTTEN-001
- What: 33 bare `catch (...)` blocks in runtime code (gap-hunter scan) — every
  swallowed exception must carry a diagnostic category per the F-exception law.
- Why it matters: silent exception swallowing is the #1 false-pass generator.
- Priority: P1. Action: classify each catch site (ART artifact vs app exception
  vs unsupported), tag with EXC-PROPAGATE categories. Test: exception battery.
- Status: RESEARCHED (scan only).

## FORGOTTEN-002
- What: 17 STUBBED-status shadow methods (dalvik_engine.cpp) lack per-method
  demand evidence; the battery does not fail on STUBBED returns.
- Why it matters: FINDING-007 proved a silent stub (Math.ceil) breaks real apps.
- Priority: P1. Action: inventory STUBBED methods × real-corpus demand; convert
  the demanded ones to implementations, the rest to loud diagnostics.
- Status: RESEARCHED.

## FORGOTTEN-003
- What: TextWatcher callback dispatch unimplemented (dalvik_engine.cpp:5544).
- Why it matters: text-field UIs (notes/diary family) depend on it.
- Priority: P2. Status: RESEARCHED.

## FORGOTTEN-004
- What: onRequestPermissionsResult never dispatched (execution_engine.cpp TODO).
- Why it matters: permission-flow apps (KISS, survival manual family) stall.
- Priority: P2. Status: RESEARCHED.

## FORGOTTEN-005
- What: packed-switch payload with non-zero first_key (negative/large keys)
  untested; hostile AXML/ARSC fuzz corpus absent from the battery as a gate.
- Priority: P2. Action: hostile-input gate (GATE C extension).
- Status: RESEARCHED.

## FORGOTTEN-006
- What: the clickable dump runs only in non-interactive mode — tap-mode runs
  (the forensic mainline!) cannot dump the live hit-test targets.
- Why it matters: this session had to reconstruct button geometry manually.
- Priority: P2 (diagnostics). Action: move the dump into the tap driver.
- Status: RESEARCHED (observed twice this session).

## FORGOTTEN-007
- What: `Math.random()`/`Random` determinism law undefined (no seeded PRNG law
  documented) — a latent nondeterminism source for visual goldens.
- Priority: P1 (determinism gate). Status: RESEARCHED.

## FORGOTTEN-008
- What: `HashMap` iteration order — the runtime must fix an iteration law
  (insertion-order is observable in R8 Kotlin apps using LinkedHashMap
  semantics; HashSet/HashMap order leaks into screenshots via list UIs).
- Priority: P1. Status: RESEARCHED (Database_Impl.j used HashSet this session).

## FORGOTTEN-009
- What: Thread.getStackTrace frame-count law (FIX-M3-011 gave 3 frames for one
  app) — the "one app's expectation" must be re-derived as a general law
  (shadow-dispatch boundary frames), else the next stack-walking app breaks.
- Priority: P2. Status: RESEARCHED.

## FORGOTTEN-010
- What: SQLite journal/WAL files appear in the sandbox dir (app-data only this
  session) — determinism gate must define semantic vs binary DB determinism
  (task brief §L) before goldens depend on DB-derived renders.
- Priority: P2. Status: RESEARCHED.

## FORGOTTEN-011
- What: `G06-TAP` gesture queue replays taps at fixed virtual offsets — tap
  timestamps are not part of the determinism contract documentation; two runs
  with different tap counts reuse stale tokens (token base 0xF0000000 counter
  not reset per run — observed runnables 4026531841+ identical across runs).
- Priority: P3. Status: RESEARCHED.

## FORGOTTEN-012
- What: the `--tap` hit-test uses the live view geometry, but FINDING-005/006
  mean off-screen views silently eat taps intended for dynamic rows — a
  "tap landed on nothing" diagnostic (target=0 path) is missing.
- Priority: P2 (diagnostics). Status: RESEARCHED.

## FORGOTTEN-013
- What: aapt2 version pinning has no checksum gate in bootstrap_toolchain.sh
  (the fetch is verified by version string only).
- Priority: P3. Action: add the jar SHA-256 to the script.
- Status: RESEARCHED.

## FORGOTTEN-014
- What: battery stage IDs are positional strings, not stable IDs — the AF gate
  ("every test has a stable ID") is partially met; `cached` gates can mask a
  stage that silently stops running.
- Priority: P2. Status: RESEARCHED.

## FORGOTTEN-015
- What: Room `@Query` UPDATE/DELETE paths (GATE H beyond CREATE/INSERT) — the
  corpus demanded CREATE/INSERT/SELECT this session; UPDATE/DELETE (Le/f.d
  EntityDeleteAdapter) execute but have no dedicated law test.
- Priority: P1. Status: RESEARCHED (demand-observed, test missing).

## FORGOTTEN-016
- What: `ColorStateList.valueOf(int)` used by K/g row buttons (background/foreground
  tint) — resolves to a constant CSL; the tint pipeline for programmatic rows is
  untested visually (ties to PHASE 7).
- Priority: P2. Status: RESEARCHED.

## FORGOTTEN-017
- What: foreground drawables (`setForeground` + `Context.getDrawable(resid)`) on
  the row buttons — the drawable pipeline must resolve icon resources for
  programmatic views, not just XML android:src (PHASE 6 gap).
- Priority: P1. Status: RESEARCHED (K/g buttons render 1080x0 partly because of
  icon measurement).

## FORGOTTEN-018
- What: `View.setForegroundGravity(17)` — gravity constant honored in the
  renderer for foreground layers? untested.
- Priority: P3. Status: RESEARCHED.

## FORGOTTEN-019
- What: the interpreter's `last_invoke_return_` is a single slot — a wide move-
  result-wide after an intervening recursive dispatch (shadow callback firing a
  DEX call) would clobber it. The token-law fix made recursive dispatch more
  likely (run() drains re-enter the interpreter). Needs a return-value stack.
- Priority: P1 (correctness under nesting). Status: RESEARCHED.

## FORGOTTEN-020
- What: Kotlin `Intrinsics.checkNotNullParameter` (La/e.h) runs 96+ times per
  microtimer session — each is a real DEX call with string allocs; a fast-path
  law (validate + trace once) would cut runtime cost without semantics change.
- Priority: P3 (performance). Status: RESEARCHED.

## FINDING-012
- Subsystem: STORAGE / DETERMINISM GATE (app-data root anchoring, P0)
- Trigger: independent re-verification of the session-7 microtimer 3-run
  byte-determinism claim at HEAD e27fe846 FAILED — 3 runs from the same CWD
  produced 3 different frame sets (frame_000 white-dominant vs blue-dominant)
- APK: dubrowgn.microtimer_8 (Room/SQLite-backed); ANY persistence-using app
  (unote, notes, chessclock) shares the exposure
- Static evidence: the app-data root was the CWD-relative literal
  "runtime/data" in FOUR places — DatabaseShadow::databases_dir_ default,
  DalvikExecutionEngine::set_package_info ("runtime/data/"+pkg+"/databases"),
  shared_prefs.cpp listPreferences/deleteAllPreferences, and the Telegram
  prefs paths in dalvik_engine.cpp; set_databases_dir had NO caller
- Runtime evidence: [SQLITE-SHADOW] opened db path=runtime/data/... shared by
  every run from $MA; after 3 tap-runs the Room `alarm` table held exactly
  3 rows (one INSERT leaked per run); run 2 loaded run 1's row and rendered a
  DIFFERENT first frame. Session-7's byte-identical runs were an ACCIDENT of
  launching from a different CWD (per-CWD implicit isolation), not a protocol
  guarantee — the determinism evidence chain had a hidden precondition.
- Root cause: app private storage anchored to the invoking shell's CWD with
  no per-invocation override; determinism protocol had no data-state control
- Law: AOSP Context/Environment — /data/data/<pkg>/ is anchored to the DEVICE
  INSTANCE, never to the CWD; determinism gate law — identical INITIAL STATE
  (incl. storage) is a precondition of byte-identical replay, and durable
  persistence across process death is itself testable Android behavior
- Fix: src/storage/data_root.{h,cpp} — ONE process-wide app-data root
  (default "runtime/data", back-compat), set via --data-root <dir> or
  MINIANDROID_DATA_ROOT; forwards to DatabaseShadow; ALL four consumers now
  derive from Storage::app_data_root(); battery corpus runs are hermetic
- Tests: NEW battery stage "M3 F-012 persistence+fresh-state determinism
  golden": pair A(fresh root, 3 taps, alarm rows=1) → B(SAME root, rows=2)
  vs independent pair C,D — LAW 1 durable persistence: B.frame_000 renders
  A's committed row (blue row + red expired label 00:00:00 visually
  confirmed); LAW 2 byte determinism: frames(A)≡frames(C), frames(B)≡frames(D)
  92/92 frames both pairs
- Runtime proof: microtimer 3-tap countdown 00:00:78→00:00:02 per-second
  mutation re-verified at e27fe846+fix; 86 unique frames / 92 saved
  (mutation-keyed saving law intact)
- Visual proof: /tmp persisted-row crop (frame_000 stateful: row + red
  expired label); label strip 78→60→40→20→02
- Regression result: battery 60/60 ALL PASS (59 prior + 1 new golden);
  zero comparator weakened; corpus runs now hermetic
- Status: REGRESSION-VERIFIED
- Priority: P0 (determinism gate unsound for every persistence-bearing APK)
- Commit: (this commit)
- GitHub evidence: PUBLISH BLOCKED — TOKEN ABSENT
