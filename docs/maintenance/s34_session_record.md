# S34 SESSION RECORD — R-NEW-333 root chain fully mapped

## Session start state
- HEAD = b56474f7 (S33: F-098/F-099 closed R-NEW-332; R-NEW-333 registered: composition
  content-state pairing, ops=0 residual, 802px placeholder SHA 193466ead8fd21d6).
- Live S34 workspace found at /tmp/my-project (uncommitted F-100 + probe suite 1-12,
  built binary 12:06, det/regression runs 12:24-12:32). Session had died before recording.

## §0 Recovery (first hour)
- Verified S34 leftover state: F-100 idle-drain pump law APPLIED to
  execution_engine.cpp (pump_compose_frames drains the handler queue every tick);
  12 bounded probes in dalvik_engine.cpp; binary fresh (built 12:06 after last edit).
- Post-F-100 evidence confirmed from leftover runs (run/s34_f100_run3, s34_mode,
  s34_det1-3, s34_reg_microtimer/gmdice/stopwatch):
  - dooz ×3 deterministic 193466ead8fd21d6 (placeholder unchanged — honest).
  - Regression trio byte-matches S33 baselines: microtimer c51269309cd14594,
    gmdice 22f3730f452b562c, stopwatch 81481eb2aa581c53.
- F-100 verified WORKING: J$c.run → J.O trampoline (z1/i queue non-empty) →
  Recomposer runner W1/N.run pumped 16× (mode=1) → NavController created →
  trampoline dispatches flow. The S33 "runner queued forever" hypothesis RESOLVED.

## §1 R-NEW-333 root chain — fully mapped (evidence-grade, static DEX + live trace)

Upstream law base (GitHub androidx/androidx, navigation 2.7.7 blob 531a3fb1:
NavHost.kt 448) + dooz v18 classes.dex (androguard ground truth):

1. setContent → composition → app content lambda n1/u.k RUNS (F/y.a=Content →
   N/a.k → n1/u.k). Content-state pairing is FINE (S33 divergence superseded).
2. n1/u.k emits the ONE LayoutNode (composer.m #1) and calls:
   - W1/G.s = rememberNavController ✓ (NavController = Landroidx/navigation/c;,
     NavHostController = Lh1/r; with zero methods)
   - p.b = public NavHost(navController, startDestination="game", builder=n1/n, …)
3. p.b → remember slow path → h1/q (NavGraphBuilder) ctor ✓ → builder dispatch at
   p.b:010e (invoke-interface LL1/l.o on n1/n) ✓ → n1/n.o registers THREE
   destinations via navigation/compose/n.a: "game" (n1/q), "settings" (n1/s),
   "about" (n1/t) — trace evidence: e$a.s(route)/e$a.c deep-links ×3 ✓
4. p.a (internal NavHost) runs ONCE. Inlined `navController.graph = graph` →
   navigate("game"): c.h ✓ → h.d (NavGraph.navigate) ✓ → start-dest resolution ✓ →
   c$a.a = createBackStackEntry ✓ (probe TSTATE: ret=o2855) → e.d = ComposeNavigator
   push ✓ (its own l.b state getter visible) → c$a.e ✓ → h1/t.e (super push) ✓ →
   flow writes Z1/M.setValue recv=o2809 val=o2901 ✓ and c.b notifies backFlow
   (recv=o2555/o2557) ✓. **The ENTIRE navigation machinery executes as real bytecode.**
5. p.a then reads the visible-entries state: 0dd8 F/w.b(tracker o2558) (F/w.b =
   remember { mutableStateOf(tracker.j.value) } + F/M.c LaunchedEffect sync F/Z0);
   0e06 F/w.d(remember p$r) → 0e22 f1.getValue → 0e2e z1/r.A (lastOrNull)
   → 0e78 `if-eqz v5` GATE.
6. Sync collectors RUN: Z1/z.c collect ×4 (F/a1.t) and the state writes land —
   F/V0.setValue o2919←o2901 (ArrayList with the entry), o2990←o2914 ✓.
7. **THE REMAINING BREAK: p.a never re-runs.** F/w.b from p.a = exactly 1× per
   site (probe READSIDE/LISTMAP/NSPUSH across 3 fresh runs). The 18 n1/u.k
   invocations are dominated by skip paths (F/i.k skipping + F/i.i). The state
   writes (step 6) do NOT re-activate the recompose scope that read them →
   lastOrNull stays the first-composition EMPTY list (o3013) → the 0e78 gate
   skips the WHOLE AnimatedContent region (j/b.b at p.a:0fc8 — ZERO dispatches,
   probe S34-RANGE/S34-JBB prove the engine never even attempts the call) →
   p$e.g (AnimatedContent content) / l.a (LocalOwnersProvider) / N/a.g /
   n1/q.g (game screen) never dispatch (probe S34-DCHAIN: all six = 0) →
   exactly 1 LayoutNode (EMITCHAIN #1) → 0 canvas ops → 802px placeholder.

## §2 Candidate root for the next session (R-NEW-333 successor attack)
The recomposition-scope invalidation law for the F/w.b-synced states:
- Either (a) the reads (F/f1.getValue → F/k0's inherited F/V0.getValue at
  p.a:0e22) are not RECORDED on p.a's recompose scope (snapshot read-recording
  law), or (b) the scope identity/derivation for the p.b→p.a group never
  re-arms after the write.
- Probe plan: hook the 35c invoke-interface handler for LF/f1;->getValue
  (log receiver runtime class — currently SILENT, zero visibility), and trace
  the recordRead/invalidation path for the o2990 state write (F/V0.setValue
  a0=o2990 a1=o2914 seen in F074 lines).
- NOTE: app-level state invalidation WORKS (18 recompositions from the dooz
  settings DataStore chain — Y0/l/Y0/j machinery — n1/c.a), so the general
  write→invalidate→recompose loop exists; the p.a scope specifically does not
  re-arm.

## §3 Tooling added (all persisted in scripts/)
- s34_disasm.py (androguard 4.x EncodedMethod full disassembler), s34_xrefs.py
  (invoke-target cross-refs), s34_dexscan.py (method_ids sig scanner — fixed
  method_id layout class(u16)/proto(u16)/name(u32) + type_list u32-size law),
  s34_find_callers.py (first cut, superseded by dexscan), s34_dump_class.py (S34),
- Engine probes 13-20 (bounded, env-gated): TSTATE (createBackStackEntry
  dispatch), DCHAIN (content-invoke chain), ACBOUND (AnimatedContent boundary),
  JBB (j/b.b static-range forensics), NSPUSH (NavigatorState pushes), READSIDE
  (read side), LISTMAP/LISTSZ (list identity/sizes).

## §4 Regression (probe binary, fresh runs)
- dooz ×5 byte-identical 193466ead8fd21d6 (det1-3 + det4/det5 with probes).
- microtimer c51269309cd14594 / gmdice 22f3730f452b562c / stopwatch
  81481eb2aa581c53 — ALL byte-match S33 baselines. Zero regressions.

## Stage summary
- R-NEW-333 root chain FULLY mapped: every link from setContent to the
  destination-content gate now has trace or static-DEX evidence; the compose
  navigation stack (graph build, navigate, back-stack push, flow writes, sync
  collectors) executes as real bytecode.
- One break remains: the recompose-scope re-arm for the p.a state reads
  (successor frontier — registered as R-NEW-334).
- F-100 validated post-hoc: the idle-drain pump unlocked the Recomposer runner
  (16 pumps) which made this whole deeper chain observable.
- Registry: R-NEW-333 narrowed + R-NEW-334 registered (recompose-scope invalidation).
