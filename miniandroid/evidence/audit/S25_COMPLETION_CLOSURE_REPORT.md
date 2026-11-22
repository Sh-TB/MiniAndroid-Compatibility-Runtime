# S25 EASY-APK CONTINUATION — THE NEXT-BLOCKER LAWS — 2026-11-22

**Base: S24 `b2b7ef25` (verified == origin/main after a sandbox snapshot restore; the S24 tip was re-fetched and local main reset --hard to it — the restore had rolled the sandbox back to a stale W23-D snapshot with an unpushed amend, preserved on branch `w23-local-tip`, content-verified identical to what later landed via W23-E/F/G + W24 on main). Tracker #635; the ten handoff APKs re-verified SHA-256-identical to `evidence/s23/s23_apk_sha256.tsv` pins (flip `63730ec2…`, minos `af769233…`, notepad `b7cf30c1…`; randomix/HelloWorldToast/chess from the same handoff set). Host 2 cores / 3 GB RAM; clean bootstrap build `make -j2 all` rc=0 (541→bootstrap log).**

## PH0 — state reconciliation (all verified, not assumed)

- HEAD chain: S24 `b2b7ef25` == origin/main (API + `git ls-remote` cross-checked); S24 report + `evidence/s24/s24_run_matrix.tsv` present; the S24-W1 ADOPT law and the S24-W2 List/Iterator model verified in-tree.
- **Baselines reproduced before any edit** (S24 tip binary, `--max-seconds 120 --frames 30 --trace`): flip rc=1 with the exact S24 chain (DataBindingUtil bind-null → `ActivityMainBinding.setPresenter` NPE at `MainActivity.onCreate pc=22`, `[S24-W1-ADOPT]` firing); minos rc=1 with the exact S24 chain (`SubscriberMethodFinder.findSubscriberMethods pc=63` → uncaught EventBusException).
- Dormant-copy discipline: the live `bridge_to_api` is `dalvik_bridge.cpp` (the S24 ODR map holds); `dalvik_engine.o` still never compiled (the monolith remains dormant). Every S25 edit targeted live TUs; `core_sources.manifest` unchanged (no new files).

## S25-W1 — flip_a_coin: the DataBinding chain, three layers deep

1. **S25-W1a — the bind-time content-parent law** (`dalvik_bridge.cpp`, live `bridge_to_api`): the engine defers the appcompat sub-decor to the attach wave, so `DataBindingUtil.setContentView`'s follow-up `decorView.findViewById(android.R.id.content)` finds NO content host (measured: `nodes=8, ContentFrameLayout=0` at lookup — diag print) and materialized an EMPTY parallel FrameLayout; the child loop never ran → `bind()` → null → the setPresenter NPE. Law: on `View.findViewById(android.R.id.content)` with a live activity + decor, (a) materialize ONE content host under the decor when the decor subtree has none, (b) adopt the activity's ORPHAN content root into it (AOSP `ViewGroup.addView(mContentParent, root)`), then delegate — the shadow BFS now answers a host WITH the root. The attach-wave S24-W1 adoption stays as the safety net (the adopted root is no longer an orphan; the laws compose, never fight).
2. **S25-W1b — the AOSP View tag law** (`layout_inflater.cpp`): `android:tag` stamps the ViewNode's `default_tag` at INFLATE time (STRING kind). The compiler-stamped binding tags now surface: measured on flip — root `layout/activity_main_0` (view 406), ImageView `head` (569), Button `binding_1` (594) — the `bind()` entry contract.
3. **S25-W1c — the Arrays.asList slot-count + dual-store law** (`dalvik_bridge_domain_jdk.cpp`, JDK-domain home): an array minted WITHOUT `__array_length__` (flip `MainActivity.<init>` varargs face) yields its REAL elements (bounded slot count), stored in BOTH conventions (`array[i]` + `__al_i<k>__`/`__al_n__`) so every List consumer — array-fields readers and the S24-W2 model arms — walks the same elements. `Ljava/util/Arrays$ArrayList;` joined the S24-W2 model family (the interface normalization re-dispatches on this runtime class).
4. **S25-W1d — the AnimatorSet Builder law** (jdk domain): `AnimatorSet.play(anim)` returns a NON-NULL `AnimatorSet$Builder`; `with/before/after` chain the SAME builder identity; the ValueAnimator/ObjectAnimator setters are fluent; start/cancel/playTogether void. Previous face: `Builder.with on null` NPE at `MainActivity.animationSetup pc=94`.

**Measured (final binary, `--max-seconds 120 --frames 30 --trace`, ×3 deterministic):** `[S25-W1-BIND-HOST]` + `[S25-W1-BIND-ADOPT]` fire ×1/run (same node ids 761/760 across runs); `ActivityMainBindingImpl.setPresenter` RUNS (`mDirtyFlags=3`); `setOnClickListener` registers the app's generated callback on the Button (view 594, `OnClickListener` listener 777) ×1/run — **the app's interactive wiring is live for the first time**; `MainActivity.animationSetup` completes; the coin drawable reaches `setImageDrawable view=569` where the honest P1-2 image law records `IMAGE-BLOCKED: VectorDrawable` (the campaign-recorded #633/#634 vector-drawable fixture blocker — the exact next layer, unchanged from the S24 record). Frame face: single deterministic hash `b270ff04` ×3, verdict DEFAULT_BACKGROUND_ONLY (blank only because the coin image is a vector resource — no bitmap to paint).

## S25-W2 — minos: past the recorded EventBus blocker

**The collection copy-construction law** (jdk domain, inside the S24-W2 list model): `new ArrayList<E>(Collection c)` copies the source's live `__al_i<k>__` slots and sets `__al_n__`. EventBus `SubscriberMethodFinder.getMethodsAndRelease` moves `FindState.subscriberMethods` out with `new ArrayList<>(...)` — without the copy the freshly registered @Subscribe methods were lost and the scan re-answered EMPTY → EventBusException (the S24-recorded next blocker). **Measured ×3: the EventBusException is GONE** — `findSubscriberMethods` reaches the `METHOD_CACHE.put` success path (registration completes), `EventBus.subscribe` appends to CopyOnWriteArrayList registrations.

**Remaining minos layer (recorded with the exact chain, unchanged by S25):** the app then dies deferred at `MazeFactory.createMaze pc=33` (`Random.nextInt` bound=0): `GameMetrics.<init>` reads the container `FrameLayout.getWidth/getHeight` (+ `Resources.getDimension` stub) at onCreate time → rows/cols compute 0 → `Maze.createCells` loop runs zero iterations → empty cell list → the classic nextInt(0) IAE. This is a view-measurement-timing layer (pre-layout dims), recorded honestly as the next minos blocker; it predates S25 (present in the S24 run log at line 347).

## Regression guards (final binary)

- **HelloWorldToast 1.4.0**: golden `acdd9f05` present. **chess 5022**: golden `d602648e` present. **Six-pin (production binary, last-frame hash)**: guess `87fe26766fc48d06`, np `31ddd4d5b8e6d18e`, dice `0de952bf75f89409`, ttt `d55056a8928a26ff` — **4/4 IDENTICAL to the W23 canonicals** (`evidence/w23/gate_hashes_postsplit.txt`); pz face differs (`6375a3a3813af176` vs canonical `ceb1a6adf7ba1391`, with-tap rerun `35c4e53b14561b2f`) — attribution build at the exact S24 tip (git worktree, in-flight at session close) recorded below.
- **randomix 42 second-order record**: the pre-S25 golden `31ddd4d5` is the shared pre-render face (np's canonical == the same hash — the blank-face family). The S25 asList richness drives randomix DEEPER into real init; the deeper path dies at `f141-null-recv: Lvk;.a on null` at `Landroidx/fragment/app/q;.d pc=44` (the R8 fragment-container lookup whose backing store the engine never populates — the recorded NEXT law: the fragment-container registry backfill), BEFORE the blank face renders → measured face `b5a7a35d` ×3 deterministic (`anchor_com.minar.randomix_42` + `_r1` + `_r2`). Named cause, exact hashes both recorded; HelloWorldToast/chess prove the asList family change itself is face-neutral elsewhere.
- The conservative Iterator gate (S24-W2b) untouched; the F-238 array-iterator family unaffected.

## Battery + gates

`tests/s25_laws_test.cpp` registered in TEST_LAW — 4 rows, **4/4 PASS**: r1 the copy-ctor law (no-alias proof), r2 the asList slot-count + dual-store law (drives the S24-W2 interface normalization trace: `List.size → runtime class Arrays$ArrayList`), r3 the AnimatorSet Builder chain-identity law, r4 the axml tag-stamp law (hand-built AxmlElement through the real `LayoutInflater::inflate_element`). Gate result on the final binary: test-core 4/4 PASS, test-hostile 3/3 PASS, **law battery 53/53 PASS** (per-test build→run→delete loop — the 5.4G disk budget cannot hold 53 test binaries at once, recorded; `evidence/s25/s25_testlaw_loop.log`), source-parity PASS.

## Dispatch trace note (honest)

The ui_graphics F-235 asList arm (dooz history) sits behind a dispatch layer the direct battery path does not reach; the chain-trace diag (temporary, removed) showed `ui_graphics entered` with a matching guard yet the arm never claimed the call, while every jdk arm claims. The asList + AnimatorSet laws therefore live in the jdk domain TU (the dispatch-proven home — the S24-W2 model already lives there); the ui_graphics F-235 arm is untouched for the dooz path and the removed ui_graphics AnimatorSet copy is documented in-tree.

## Blockers recorded — exact first divergences + next concrete action

1. **flip paint**: `setImageDrawable(view 569)` receives a VectorDrawable → P1-2 honest IMAGE-BLOCKED. Next: the vector-drawable decode law (#633/#634 — the recorded document-loader workstream), then the face paints through UNIFIED_011.2.
2. **minos**: the GameMetrics dims layer (above). Next: the pre-layout measure contract (the DEFAULT-MEASURE family answering the container dims at GameMetrics init, or the app's own re-measure path).
3. itsfrz LC4/a theme chain, notepad DataStore protobuf init, dicer ActionBar measure, compose throw-null layer — unchanged from S24's record.

## Build

bootstrap clean `make -j2 all` rc=0 (log: `evidence/s25/bootstrap_clean_build.log`); incremental iterations 1–7 TU-level (~20–40 s each + link); binary v0.0.6.2+`b2b7ef25` lineage, VERSION unchanged this wave.

## Evidence files

`evidence/s25/`: flip_base/flip_w1(b..e)/flip_r1..3 (stderr.log + frames), minos_base/minos_w2/minos_r1..3, anchor_randomix/anchor_HelloWorldToast/anchor_chess, s25_run_matrix.tsv, bootstrap_clean_build.log, s25_build1..7.log, s25_testall.log, six-pin gate log. Report: `evidence/audit/S25_COMPLETION_CLOSURE_REPORT.md` (this file).

**Status vocabulary**: IMPLEMENTED (W1a bind-time content parent, W1b axml tag stamp, W1c asList dual-store, W1d AnimatorSet Builder, W2 collection copy-ctor) / TESTED (flip ×3, minos ×3, anchors ×3, battery 4/4, test-all) / OBSERVED (flip interactive wiring live: setPresenter + setOnClickListener registered ×3) / PARTIAL (flip paint — vector-drawable layer) / BLOCKED (minos GameMetrics dims — recorded; #633/#634 vector decode unchanged) — nothing claimed PASS beyond what a run shows.
