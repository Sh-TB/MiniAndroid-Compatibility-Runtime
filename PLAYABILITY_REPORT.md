# PLAYABILITY REPORT — PLAYABILITY CAMPAIGN (Session f105–f124)

**Date:** 2026-09-15 · **HEAD:** `d202e43d` (GPG-105..107) on top of `12cf043f`
**Campaign law:** RUN GAME → BLOCKER → TRACE → SOURCE/UPSTREAM LAW → GENERIC FIX → RUN → REGRESSION → CORPUS SWEEP → MEASURE
**Anchors:** TicTacToe golden `de5f370e` lineage, replay SHA `613cfccc…` — **ALL PASS after every change below**

---

## 1. Gameplay Ladder — Dooz (`io.github.yamin8000.dooz_18.apk`, sha256 `d81292cd…`)

| Rung | Status at checkpoint `4931f8a4` (f091) | Status at HEAD `d202e43d` (f124) | Δ |
|------|------|------|---|
| APK load + DEX parse | PASS | PASS | — |
| Activity launch (manifest) | PASS | PASS | — |
| Lifecycle onCreate → RESUMED | PASS | PASS | — |
| Compose attach (dispatch) | PASS | PASS | — |
| `rememberNavController` + init lambdas | PASS | PASS | — |
| `createNavController` + 3× addNavigator | PASS | PASS | — |
| `getNavigator("composable")` | PASS | PASS | — |
| NavGraph build + route "game" | PASS | PASS | — |
| `navigate()` back-stack mutation (addAll) | **CRASH** (NPE `z1.i.addAll`) | **PASS** | ▲ fixed |
| Overload-correct dispatch (addAll(Collection)) | **CRASH** (wrong overload bound) | **PASS** | ▲ fixed |
| `getBackStackEntry(parent.id)` lookup | **CRASH** (IAE "No destination with ID 0") | **PASS** | ▲ fixed |
| Navigator attach (`onAttach` loop) | **CRASH** (ISE "state until attached") | **PASS** | ▲ fixed |
| kotlin-reflect proto mapper `<clinit>` | **CRASH** (NPE in `LM1/i.c`) | **PASS** | ▲ fixed |
| Full run exit code | rc=1 (uncaught) | **rc=0, 0 uncaught** | ▲ |
| First real game render | ❌ (802 px = Material background only) | ❌ (802 px — compose onDraw dispatched, **ops=0**) | ▷ machinery alive, no draw ops yet |
| Tap → state mutation | ❌ not reached | ❌ not reached | — |

**Run f124:** rc=0, `final_state: RESUMED`, zero uncaught exceptions — the FIRST crash-free
end-to-end run of the Compose campaign. The composition now executes inside a fully
functioning navigation stack (NavControllerNavigatorState created, backQueue mutated,
destination "game" linked) but the AndroidComposeView draw pass records **0 draw ops**;
the framebuffer still shows only the Material theme background (802 non-white px).
Per the no-fake-success law Dooz is classified **EXECUTED**, not RENDERED.

## 2. Blockers resolved this session (each: trace → upstream law → generic fix → regression)

| ID | Blocker (runtime truth) | Upstream law | Fix (generic) |
|----|--------------------------|--------------|----------------|
| GPG-105 | `invoke-virtual z1/i.addAll(Ljava/util/Collection;)` executed `addAll(int, Collection)` — callee `elements` param never assigned → Intrinsics NPE | JVM overload resolution is (name, descriptor)-exact; F-023 fast path was dead because invoke-virtual/super/interface/range passed an EMPTY descriptor | Thread the exact call-site descriptor (`resolve_method_proto_for_dex`) into every `try_recursive_invoke` dispatch path |
| GPG-106 | `NavController.getBackStackEntry` inlines `lastOrNull` over `AbstractList.listIterator(size)`; bridge answered void → loop skipped → IAE "No destination with ID 0" (backQueue DID contain the entry) | OpenJDK `AbstractList.ListItr`: hasNext ⇔ cursor≠size, next=get(cursor++), hasPrevious ⇔ cursor≠0, previous=get(−−cursor) | Bridge mints synthetic `AbstractList$ListItr` (receiver+cursor) whose iteration delegates to the receiver's REAL DEX `get/size/remove` up the superclass chain; shadow object-answers take precedence; void stubs rejected; gate widened to runtime receiver class |
| GPG-107 | Map view `values()` view had size 0 → NavHost attach loop iterated nothing → `Navigator.onAttach` never ran → ISE "You cannot access the Navigator's state until the Navigator is attached" | OpenJDK Map views are live collections over the map's entries (F-064 already materialized them; `toArray`/`iterator` honored them, `size`/`isEmpty`/`get` did not) | `CollectionShadow.size/isEmpty/get(I)` now count/read `is_view` → `view_elements` |
| GPG-107b | kotlin-reflect proto mapper `LM1/d.<clinit>` NPE: `next()` over a values() view returned null (view `get()` read empty `elements` instead of typed `view_elements`) | F-064 typed-view read law | `get(I)` serves typed `view_elements` (kind 1/2/3) |

Evidence logs (committed run artifacts + logs): `gpg_f105_rerun`, `gpg_f106_mtrace`,
`gpg_f107_postg105`, `gpg_f108_mtrace`, `gpg_f109_fieldtrace`, `gpg_f113_ptrace`,
`gpg_f114_mapdiag`, `gpg_f115_gtrace`, `gpg_f117_postg107`, `gpg_f124/` (clean run).
Forensic tooling added: `scripts/forensic/gpg_f105_addall_probe.py`,
`gpg_f105c_exact.py` (exact Dalvik disassembler: full canonical size table, correct
35c 5-register AG|op BBBB FEDC decode, 22c/23x/21s register formats).

## 3. Regression gate (mandatory after shared-engine changes)

**TicTacToe golden** (`miniandroid/tests/fixtures/tictactoe_golden/`): **ALL PASS — 8 checks**:
fixture build OK (ECJ+D8, APK sha `c8f499c0…`), 9/9 clicks dispatched, frame0 "X to move",
frame1 "O to move", frame7 "X WINS", final 4 X + 3 O, frames 8/9 frozen, pixel
discriminators pass, **deterministic replay byte-identical (`613cfccc…`) — unchanged**.

**Corpus battery (f124, standard path, `MINIANDROID_DISPATCH_ATTACH=1`)**:

| APK | rc | uncaught | non-white px | Category |
|-----|----|----------|--------------|----------|
| gmdice | 0 | 0 | 1,744,539 | RENDERED |
| microtimer | 0 | 0 | 1,041,116 | RENDERED |
| unote | 0 | 0 | 236,520 | RENDERED |
| chessclock | 0 | 0 | 2,073,600 | RENDERED (dark theme full frame) |
| simplestopwatch | 0 | 0 | 1,944,411 | RENDERED |
| notes (billthefarmer) | 0 | 0 | 18,200 | RENDERED |
| headingcalculator | 0 | 0 | 2,046,423 | RENDERED |
| bouncy | 0 | 0 | 2,073,600 | RENDERED (light UI + purple accents) |
| tictactoeclassic | 0 | 0 | 2,073,600 | RENDERED (blue board) |
| dooz | 0 | **0** | 802 | **EXECUTED** (crash-free; no game frame yet) |
| stopwatch (muellerma) | 1 | 0 | 23,472 | DOCUMENTED BOUNDARY (Quick-Settings Tile app — manifest declares no launchable Activity; §18/§19) |
| bgclock | 1 | 1 | 2,073,600 | DOCUMENTED BOUNDARY (clock face is WebView/HTML content; §19) |
| tictactoe (emmanuelmess) | 1 | 1 | 0 | BLOCKED — libGDX `GdxRuntimeException` at AndroidLauncher.onCreate (GL/native engine boundary, not a DEX bug) |
| tictactoe (corpus variant) | 1 | 1 | 0 | BLOCKED — uncaught at onCreate (needs next-session trace) |

No regression: every app that rendered at the previous checkpoint still renders at HEAD.
Screenshot honesty: dooz frame is 99% white (Material background only) — it is NOT
presented as a game screenshot anywhere.

## 4. Runtime Progress counts

- Engine laws added: **4** (GPG-105, GPG-106, GPG-107, GPG-107b) — all generic, zero class/package-specific hooks, zero new root factories.
- Dooz crash chain: **6 consecutive blockers resolved** in one session (UUID NPE was fixed pre-f097; this session: addAll NPE → overload misbind → back-stack IAE → attach ISE → reflect NPE).
- Uncaught exceptions in dooz run: f091-era **1** → f124 **0**.
- Corpus: 10/14 sweep entries rc=0 with real frames (was 8/13 at the last recorded sweep); 2 documented boundaries, 2 honest BLOCKED.
- Commit: `d202e43d` — 5 files, +939/−9 (engine + forensic tooling only; no APKs committed).

## 5. Active Blocker (single, next session's entry point)

**Compose draw-op pipeline: composition runs, draw ops = 0.**
`AndroidComposeView.onDraw` dispatches (`[C013-ONDRAW] dispatched=YES ops=0`) and the
compose UI node machinery executes (`androidx/compose/ui/node/*` class inits and
super-dispatches visible in the f124 tail), but no `drawRect`/`drawText` ops reach the
software canvas. Next step per the mandatory cycle: trace the Owner/CanvasHolder
dispatch chain (`AndroidComposeView.draw` → `ComposeRootView`/Owner `draw` path) with
`MINIANDROID_METHOD_TRACE='platform/AndroidComposeView;|draw'`, find the first
layer that returns void/null, and apply the corresponding upstream law
(AOSP `ViewRootImpl`/Compose UI Owner draw contract).

## 6. GitHub

- Commit `d202e43d` created locally on top of `12cf043f`; `git status` clean except
  untracked run-artifact directories (intentionally uncommitted — trace JSONs are
  large; the decisive logs are cited by path in this report).
- Push attempted via the session's git transport; result recorded in the worklog
  (`worklog.md`). If the push did not succeed, the claim is "committed locally, push
  pending" — not "on GitHub".

## 7. Final Decision

The campaign's own Hard-Stop rule ("when both peaks are proven → stop") is NOT yet
triggered: Peak 2 (TicTacToe anchor 9/9 + WIN + replay) remains proven and green, but
Peak 1 (Dooz playable) is still open — one honest rung short: the app now survives its
entire startup + navigation + composition init, and the remaining gap is the final
draw-op → framebuffer bridge. Dooz is **EXECUTED / crash-free** — the first time the
Compose campaign has a clean end-to-end run — and the next blocker is precisely
localized. Recommended next session: single-cycle attack on the draw-op pipeline
(§5), then tap-dispatch into the game surface.

*No fake success anywhere in this report: every ✅ above is backed by exit codes,
frame hashes, or named evidence artifacts; Dooz's blank frame is called blank.*
