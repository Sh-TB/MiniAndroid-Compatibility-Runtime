# S35 SESSION RECORD — R-NEW-334 narrowed to the lifecycle-gated visibility law

HEAD: `b3409007` → +S35 commits · Binary: rebuilt from HEAD source (the 12:14 binary was
STALE vs source — root cause of "probes went silent"; fresh build fires all probes).

## §0 User-directed deliverables (this session, before the attack)

- ALL old refs pushed with the fresh PAT: `main`, 3 archive branches, tags verified.
- `docs/evidence/APPS_EXECUTION_LEDGER.md` + `apps_ledger/` (15 compressed screenshots,
  1080×1920 → 540×960, 297 KB → 211 KB): every executed app with real screenshot +
  SHA-256 + APK name/version + download link, honest grades. Dooz row says PLACEHOLDER.
- F-LEDGER 100% closure (`docs/maintenance/F_LEDGER_CLOSURE_S35.md`): F-046/F-047/F-049/
  F-051/F-077 closed with HEAD evidence; F-048 superseded; F-052 void; F-037/F-038/F-061
  never-assigned. Registry R-NEW-301 → VERIFIED-FIXED (closed-by-supersession).

## §1 R-NEW-334 attack — the upstream chain, fully mapped (live + static + GitHub)

Binary staleness fix: source 15:28 > binary 12:14 — probes were silent because the
S34-era binary predated the probe suite. After rebuild: dooz `193466ead8fd21d6` ×3
(baseline unchanged), full S34 probe suite fires.

### The read side (DEX ground truth, p.a disasm + live trace)

`Landroidx/navigation/compose/p;.a` (internal NavHost) — ONE invocation (METHOD-IN
count = 1; exit probe confirms clean return). Its own body contains BOTH collectAsState
sites (two `LF/w.b` call sites 0d80/0dd8 — S34's "two-navcontroller" confusion resolved):

| DEX | meaning | live objects (run J/H) |
|---|---|---|
| 0d70-0d80 | `l.b().e` back-stack tracker → `F/w.b` = collectAsState #1 | tracker `o2811`, state `o2809` |
| 0dcc | `B1/a.w` = rememberSaveableStateHolder | — |
| 0dd4-0dd8 | `c.j` visible-entries tracker → `F/w.b` = collectAsState #2 | tracker `o2558`, state `o2557` |
| 0e06 | `F/w.d` = `derivedStateOf(p$r)` | derived `o2999` |
| 0e22-0e2e | `f1.getValue` → `z1/r.A` (lastOrNull) | returns `o3013` |
| 0e78 | `if-eqz` — the gate that never opens | FALSE |

`W1/G.s` = the generic `remember` (NOT rememberNavController — S34 label corrected);
`rememberNavController` = `n1/u.k → G.s` creating `c o2550` via `B0/b.g → C/a.c`.
ONE navController; the "2 ctor" = NavHostController ctor chain. NO composition abort,
NO second NavHost.

### The write side (live, [S35]+[S35-COLL] probes, engine heap + shadow truth)

- Push: `h1/t.e` writes back-stack flow `o2809 ← o2901` — **o2901 elems = 1** ✓ real entry.
- `c.b()` (dispatchOnBackChanged) then writes visible list `o2557 ← o2914` —
  **o2914 elems = 0** ← THE EMPTY LIST.
- remember captured what the trackers held: `o2919 → o2901` (1 entry, back stack ✓),
  `o2990 → o2914` (0 entries, visible ✗).
- Derived filter is CORRECT: `o3013` empty because its input is empty. **There is NO
  stale-read bug and NO recompose-scope re-arm bug at this layer** — R-NEW-334's
  original hypothesis is SUPERSEDED: the scope never re-arms because the WRITE ITSELF
  carried an empty list.

### THE UPSTREAM LAW (androidx/navigation navigation-runtime internal/NavControllerImpl.kt
`populateVisibleEntries()`, fetched via GitHub PAT):

```kotlin
entries += backQueue.filter { entry ->
    !entries.contains(entry) && entry.maxLifecycle.isAtLeast(Lifecycle.State.STARTED)
}
return entries.filter { it.destination !is NavGraph }
```

The pushed entry reaches visibleEntries **only when `entry.maxLifecycle >= STARTED`**.
maxLifecycle is driven by the HOST lifecycle (`updateBackStackLifecycle`: last entry →
`hostLifecycleState`) and the Compose transition completion (`onTransitionComplete` →
RESUMED). dooz's visible list is empty because the pushed NavBackStackEntry's
maxLifecycle never advances to STARTED.

**R-NEW-334 narrowed (single verified break):** the NavBackStackEntry lifecycle chain —
`updateBackStackLifecycle` / `prepareForTransition` / entry-lifecycle dispatch — does
not advance the entry to STARTED (or reads a host lifecycle that is not STARTED+), so
`populateVisibleEntries` legitimately returns empty. Next attack surface: the
`androidx.lifecycle` (obfuscated `Landroidx/lifecycle/i;`) state machine on the entry +
the host-lifecycle source the runtime feeds it. NOT a recompose-scope bug.

## §2 Evidence runs

- `run/s35_r334_a..k` — probe ladder (census gate discovery, METHOD-IN windows,
  RET-TRACE, S35 heap probes, S35-COLL shadow truth).
- Probe additions (all env-gated `MINIANDROID_S35_TRACE=1`, bounded, read-only):
  `scripts/s35_patch1_stale.py`, `scripts/s35_patch2_navhost.py`, S35-COLL block in
  `android_shadows.cpp`, `scripts/s35_string_xref.py` (raw const-string xref tool).
- Determinism: dooz ×3 `193466ead8fd21d6`; microtimer `c51269309cd14594` ✓;
  gmdice `22f3730f452b562c` ✓; stopwatch `eb16ab5c68fa9b6c` == u011-era standard-path
  capture (the S33 `81481eb2…` was the GATE H dim variant — provenance corrected).

## §3 GitHub sources used (per the user's law — search first)

- https://github.com/search?q=repo:androidx/androidx+filename:SnapshotStateObserver.kt&type=code
- https://github.com/search?q=repo:androidx/androidx+filename:NavController.kt+path:navigation&type=code
- https://github.com/androidx/androidx/blob/4e41da212d09/compose/runtime/runtime/src/commonMain/kotlin/androidx/compose/runtime/snapshots/SnapshotStateObserver.kt (1.6.7-era)
- https://github.com/androidx/androidx/blob/4e41da212d09/compose/runtime/runtime/src/commonMain/kotlin/androidx/compose/runtime/snapshots/Snapshot.kt
- https://github.com/androidx/androidx/blob/27cf9a7d5788aa0f5f2d8b6699ce279560daf326/navigation/navigation-compose/src/commonMain/kotlin/androidx/navigation/compose/NavHost.kt
- https://github.com/androidx/androidx/blob/27cf9a7d5788aa0f5f2d8b6699ce279560daf326/navigation/navigation-runtime/src/commonMain/kotlin/androidx/navigation/internal/NavControllerImpl.kt
