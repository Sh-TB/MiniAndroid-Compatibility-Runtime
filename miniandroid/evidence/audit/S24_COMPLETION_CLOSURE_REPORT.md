# S24 EASY-APK COMPLETION & SHARED RUNTIME CLOSURE — 2026-11-21

**Base: S23 `a86d3e03` (verified ancestor of origin/main; session HEAD before work: `c42bc79f`). Host unchanged (2 cores / 3 GB / 6.3 GB disk). Tracker #635; registry #632; issues #610/#616/#618/#619/#620 + #588 read in full.**

## PH0 — state reconciliation (all verified, not assumed)

- HEAD chain verified: `a86d3e03` ∈ origin/main; S23 report + `evidence/s23/s23_apk_sha256.tsv` + interaction TSV present; S23-W1 (interpreter) and S23-W3 (GSS bridge) markers present in the live TUs.
- **Dormant-copy discipline enforced**: two ODR shadows found and mapped — `dispatch_attached_subtree_from` has a guarded copy in `dalvik_engine.cpp:21148` (MONOLITH; `dalvik_engine.o` is never compiled in the modular build — the live `T` symbol is `dalvik_engine_invoke.o`, verified via `nm`) and `bridge_to_api` lives in `dalvik_bridge.cpp:82` (live; `dalvik_engine_core.o` only references it, `U`). Every S24 edit targeted the LIVE copy only.
- `core_sources.manifest` check: both edited files are live manifest entries; no dormant patching.

## Baseline → after matrix (all runs = original handoff APKs, SHA-256s in `evidence/s23/s23_apk_sha256.tsv`)

| Target | S23 | S24 after | Shared law that moved it |
|---|---|---|---|
| flip_a_coin | rc=1 blank | **rc=0 ×3, deterministic face `b492ee85`**, content children 0→1, tree 856→860→461(5 kids), ImageView 331×331 @ (374,794) | **S24-W1** |
| minos | rc=1 (Random IAE) | **rc=0 ×3** (face still blank; next blocker = EventBus reflection) | **S24-W2b** |
| n-Puzzle | interactive | unchanged, deterministic | — |
| ugaday | interactive | **semantic proof: frame diff (222,8,857,50) = app-authored "Invalid number" band** — the app's own handler ran and its UI answered | — |
| blockinger | interactive | unchanged | — |
| notepad | rc=1 DataStore | unchanged (blocker recorded) | — |
| itsfrz | census 0 | unchanged; blocker = R8 theme chain `LC4/a` via `LB4/x.b` precedes listener registration | recorded |
| randomix / HelloWorldToast / chess | golden | **byte-identical** (`31ddd4d5` / `acdd9f05` / `d602648e`) | regression guards |

## Shared implementations (3 laws, all app-agnostic, live TUs only)

1. **S24-W1 — mContentParent adoption law** (`dalvik_engine_invoke.cpp`, live `dispatch_attached_subtree_from`): the appcompat sub-decor path (R005) linked the FitWindows stack under the window decor but the U007 res-inflate root was only recorded, never adopted — the renderer walked the decor alone (ContentFrameLayout children=0 → blank; S23 evidence `attached=0`). Law: an orphan first-traversal root (parent_id==0, node exists) is adopted by the ContentFrameLayout-family node of the current activity's decor subtree — AOSP `PhoneWindow.setContentView` ownership, keyed by class family. Measured: flip_a_coin ADOPT=1/run, children=1, rc 1→0 ×3; zero fires elsewhere; anchors unchanged.
2. **S24-W2 — JDK interface receiver normalization + W2b — the java.util.List/Deque/Iterator heap model** (`dalvik_bridge.cpp` normalization; `dalvik_bridge_domain_jdk.cpp` model): invoke-interface arrives with the declared token, the bridge receives the runtime class (F-090d) — but NO ArrayList/List/ArrayDeque handler existed: `size()` answered the int default 0 → minos `MazeFactory.createMaze` → `Random.nextInt(0)` → IAE "bound must be positive" → onCreate died. Model: the f578 `__bq_n__` field pattern — `__al_n__` + `__al_i<k>__` slots; add/add(idx)/get/set/contains/remove(index|object)/isEmpty/clear/size/iterator; Deque aliases push/offer/poll/pop/peek/removeFirst/Last; Iterator law (`__it_src__`/`__it_pos__`) gated **conservatively** to cursors this model created (the F-238 array-iterator family keeps its own fields). Measured: minos rc 1→0 ×3.
3. **S24 regression guard (found + fixed)**: the first blanket Iterator arm broke randomix's golden face (`31ddd4d5`→`b5a7a35d`) — every for-each over F-238 array iterators answered hasNext=0. Root-caused (existing iterator laws in other domains), gated, **randomix restored byte-identical**; battery spot 8/8 (lifecycle, linear, s98-text, resource_core, r25, input_pipeline, g10-layout, g11-ctor).

## PH7 — game semantics (honest)

- **ugaday**: real semantic state change captured — the app's own "Invalid number" validation band appears after the dispatched click (frame-diff bbox recorded). The handler is the app's XML onClick on `activity_main`.
- **n-Puzzle**: GamePlay listener dispatch ×12/run + 2 frame hashes ×3 (S23 + re-verified). Full tile-move semantics are downstream of the app's picture-choose flow (the board is empty until the user adds pictures — the initial screen IS the "To add your pictures click Menu button" state; recorded as PARTIAL with the exact next action: the Menu → picture-picker dialog chain).
- **blockinger**: 6 click events + 2 frame hashes ×3. Deeper reveal semantics need coordinate-targeted taps into the custom board canvas (recorded).

## Remaining blockers — exact first divergences + next concrete action

1. **flip_a_coin paint+interaction** (next after W1): DataBinding `bind(rootView)` returned null → `ActivityMainBinding.setPresenter` NPE → the app's listener registration never ran (0 click listeners, 0 draw ops). Root: the wrapped DataBinding layout (`layout/activity_main_0`, tag `binding_1`) requires `android:tag` stamping on the inflate root + the tag/getTag bridge (ViewNode has no tag field yet) before `mapBindings` can map `head`/`button`. **Next action**: node tag field + setTag/getTag bridges + the wrapped-layout tag law; then the ImageView src (`android:src` present in res/v9.xml, pool verified) paints through the existing UNIFIED_011.2 image law.
2. **minos**: EventBus `SubscriberMethodFinder.findSubscriberMethods` pc=63 `EventBusException` — the reflection method scan doesn't surface `@Subscribe` methods. Next: the getDeclaredMethods method-scan law (pairs with Notepad's DataStore reflection family).
3. **itsfrz**: `LC4/a` thrown at `LB4/x.b` pc=97 (R8-mangled appcompat theme chain), caught/rethrown across frames — precedes listener registration. Next: decode the `LC4/a` message + the theme-app chain.
4. **notepad**: DataStore/protobuf worker-thread NPE (`J3/d.Q` getClass-on-null after R337-UNSAFE objectFieldOffset succeeded). Next: the protobuf message-default-instance init law.
5. **dicer**: `ActionBarContextView.onMeasure` pc=318 layout_width ISE (#616: the welcome DialogFragment is mandatory). Next: the AbsActionBar LayoutParams width contract.
6. **compose (janken/authsrng/dooz)**: janken reached 4 provider provisions/run (S23-W1) then `throw null` ×22 (composition state); authsrng SoftReference.get null in the font cache. Next: the composition-state model (B1 scale) — unchanged from S22's honest PARTIAL.

## Build (S24 vs S23)

no-change 1.07 s (S23 1.07) | 1-TU 20.5–25.8 s (S23 25.8) | 2-TU 25.7–39.5 s (S23 39.5) | link 1.40 s (S23 1.48) | clean: none this session (preserved artifacts; S23 measured 6m38–7m48).

## Evidence files

`evidence/s24/s24_run_matrix.tsv` (20 rows: per-run unique frame hashes + W1/W2 firing counts + semantic notes) · `evidence/s24/flip_r1..3`, `minos_r1..3`, `itsfrz_r1`, anchors · S23 TSVs unchanged. Report also at `/home/z/my-project/download/` and posted to #635.

**Status vocabulary used**: IMPLEMENTED (W1, W2/W2b) / TESTED (flip ×3, minos ×3, anchors ×3, battery 8/8) / OBSERVED (ugaday semantic band) / PARTIAL (n-Puzzle tile semantics — picture flow next) / BLOCKED (itsfrz theme chain, notepad DataStore, dicer measure, compose state) — nothing claimed PASS beyond what a run shows.
