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
- Tests: needs fixture + microtimer row geometry
- Status: OBSERVED (root cause localized, fix pending)
- Priority: P1
- Commit: —
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
- Status: OBSERVED
- Priority: P2
- Commit: —
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
- Status: OBSERVED
- Priority: P0 (blocks GATE F visual closure)
- Commit: —
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
