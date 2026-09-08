# MASTER-3 SESSION 12 FINAL REPORT (fixed §15 format)

Date: 2026-09-09 · Campaign: MiniAndroid Compatibility Runtime
Session type: Ground-Truth Re-Verification + F-020 Completion + Java Core / Executor / Room Closure

## A) START_HEAD
`9fe2d773` — unpushed UUID-message commit (`cb73f49f-cd22-4106-…`) left by the
interrupted session, containing its F-020 work (AtomicShadow, ExecutorShadow,
vtable most-derived-override law, ctor direct-invocation law, f020 fixtures,
battery 64→67). Tree clean at session start.

## B) FINAL_HEAD
`d26fbafd` (branch main)

## C) REMOTE_HEAD
`61fd7f17` — **PUSH BLOCKED**: this container holds no GitHub credentials
(`/home/z/.gh_token` absent, no gh auth). Recorded as an environment boundary;
nothing was faked. All four session commits are safe locally.

## D) Unpushed commits (oldest→newest)
1. `9fe2d773` (interrupted session's F-020 work, verified this session)
2. `e9304898` F-022 invariant count-law fix (17→18 / 19→20)
3. `948e104d` F-024 EOF fixture + F-025 executor double-run fix + battery stages
4. `d26fbafd` F-026 rawQuery + F-027 contentEquals + §6/§7 audit docs

## E) Fresh battery
**76/76 ALL PASS** at frozen `d26fbafd` (resume=0 header verified; every stage
genuinely executes). Progression this session: 67/67 (after F-022 law fix) →
73/73 (+F-024, F-025 stages) → 76/76 (+F-026+F-027 stage).
Environment note: harness-level intermittent process kills were observed and
worked around with a forensic monitor (`scripts/monitor_battery.sh`); not an
OOM (cgroup oom_kill=0), not a ulimit; kills are external and intermittent.

## F) NEW findings (registry continued from F-021)
- **F-021** Activity.getLayoutInflater window-inflater law — back-registered
  (implemented by interrupted session, never registered). IMPLEMENTED +
  REGRESSION-VERIFIED (f020 fixture law5).
- **F-022** Battery tool integrity: commit 9fe2d773 froze a HALF-EDITED §6
  invariant count law (registered 2 shadows, law updated for 1). Caught by
  fresh re-verification. FIXED (e9304898). P1, measurement integrity.
- **F-023** dooz blank frame: Compose composition deferred on the view-attach
  protocol (`isAttachedToWindow` fail-soft false + `addOnAttachStateChange
  Listener` never dispatched → composition parked; ComposeView children=0).
  ROOT-LOCATED, P1 — the Compose host frontier (attach dispatch already
  exists env-gated `MINIANDROID_DISPATCH_ATTACH=1`; with it ON, composition
  starts and the next layer surfaces: windowToken/composition-locals NPE at
  `LM1/i;.f`). Next battle.
- **F-024** InputStream EOF law — proof-added (implementation predated proof).
- **F-025** Executor double-run: C++ function-local `static const bool`
  init-once bug froze the ownership guard on the first call's class_name →
  every executor task ran twice (executedCount=9). FIXED.
- **F-026** bare `SQLiteDatabase.rawQuery(String,String[])` had NO handler →
  fail-soft null cursor on every scalar read. FIXED (raw_query_common).
- **F-027** `String.contentEquals` answered api_dispatcher's ALWAYS-FALSE
  stub — §8 fail-wrong-law class. FIXED (real comparison, sb_value law).

## G) Fixed this session
F-022, F-025, F-026, F-027 (+ F-020's three root defects verified at HEAD:
AtomicShadow family, ART vtable most-derived-override walk, Enum.compareTo
ordinal-sign bridge).

## H) Verified this session
- F-020 snapshot primitive laws — REGRESSION-VERIFIED (5-band fixture golden
  + battery). Only the primitive layer; the full Compose host remains F-023.
- F-024 EOF family (7-band), F-025 executor queue law (4-band), F-026+F-027
  persistence family (7-band) — each 3-run byte-identical + permanent battery
  stages.
- §3B Enum.compareTo — VERIFIED (fixture law3 + bridge code at HEAD).
- Cross-APK: microtimer F-012 legs re-verified after EVERY engine change
  (rows 1→2 law intact); unote = second independent persistence APK
  (notes.db v2 end-to-end: helper→open→onCreate→real ORDER BY query, fresh-
  empty law, real UI + clicks); simplekeyboard SUCCESS/RESUMED at HEAD.

## I) Blocked
- F-023 Compose host chain (P1 frontier; plan documented in registry).
- Push (no credentials in container).
- TextWatcher / onRequestPermissionsResult dispatch — DETECTED_NOT_EXERCISED
  (no corpus demand at HEAD; TODOs documented, not fake-implemented).

## J) Major generic improvements
AtomicShadow (java.util.concurrent.atomic exact-prefix family); ART vtable
most-derived-override dispatch law; constructor direct-invocation law;
ExecutorShadow ownership + deterministic queue law; SQLiteDatabase.rawQuery
shared cursor materialization; String.contentEquals real comparison; 12 new
permanent regression stages (fixtures f024/f020-executor/f026 + goldens).
Zero app-specific code in any fix.

## K) New real-APK proofs
unote (persistence #2, SUCCESS + interaction), simplekeyboard (re-verified),
dooz advanced PARTIAL→SUCCESS rc=0 (lifecycle RESUMED, 3-run deterministic —
blank frame remains, F-023 boundary, NOT counted as visual proof per §7/§10).

## L) Visual proof
Four new band-goldens (5/7/4/7 laws, all green), verified pixel-wise with
gutter checks; dooz/unote/simplekeyboard screenshots inspected visually
(unote renders real toolbar + action bar + clickable buttons).

## M) Determinism
3-run byte-identical: f020_snapshot (battery), f024 `32b8a456…`,
f020_executor `30c4696f…`, f026_room_sql `32b8a456…` (same all-green visual
verdict), dooz `31ddd4d5…`, F-012 frame pairs A≡C / B≡D (92 frames each).

## N) Regression
Focused → affected-APK → full battery after every engine change. F-012
persistence protocol re-verified post-F-025/F-026/F-027. Final fresh battery
76/76 at the frozen HEAD.

## O) Remaining blockers
1. F-023 Compose host chain (attach → composition → windowToken locals →
   slot table → measure/layout/draw) — P1, the only blocker for real Compose
   APKs' render chain.
2. Push credentials (environment).
3. Harness process-kill intermittency (workaround in place; root outside repo).

## P) Remaining LARGE Base Closure stages (exact)
1. Compose host (F-023) — attach default-on + golden re-baseline, composition
   engine (slot table/recomposer), Compose measure/layout/draw.
2. Room-generated-adapter @Update/@Delete path — DETECTED_NOT_EXERCISED (no
   corpus APK demands it; SQLite layer beneath is VERIFIED).
3. TextWatcher + onRequestPermissionsResult dispatch — DETECTED_NOT_EXERCISED.
4. Foreground drawable pipeline + foregroundGravity dedicated goldens —
   IMPLEMENTED_NOT_EXERCISED.
5. SQLite WAL determinism golden — BOUNDARY (journal pinned; law documented).
6. Stream-reading corpus APK — NOT_REQUIRED_BY_CORPUS (demand source exoplayer2
   APK outside current corpus).
Base Closure verdict: **NOT COMPLETE** (Compose host alone forbids it).

## Q) Forgotten-items reconciliation
Done — 16 items classified in FINDINGS_REGISTRY.md §6 section with the
8-word status vocabulary; nothing deleted; no silent stubs introduced
(F-027 REMOVED one fail-wrong-law stub instead).

## ACHIEVEMENTS PRESERVED
F-016/F-017/F-018/F-019 all intact (battery re-proves them at every run);
GOLDEN-03 resource authority untouched; typography G31–G48 intact; ChessClock
async evidence intact; F-012 64→76-stage battery law intact and re-verified.

## REMAINING WORK
See O) and P). Recommended next battle: **F-023** — promote the attach
dispatch from env-gated to lawful default (real Android always dispatches
attach), re-baseline affected goldens, then walk the composition chain with
bounded probes (windowToken locals → slot table → node factory), each step
fixture-proven per the forensic protocol.
