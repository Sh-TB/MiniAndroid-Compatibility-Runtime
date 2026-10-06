# CONT-8 EXECUTION LEDGER — WAVE 4: SUCCESS-PATH CLOSURE

Directive: CONT-8 / WAVE 4 (multi-root execution/rendering closure). HEAD `50b63bc7` (origin/main `c1407326` + W3 evidence commits). Binary `c0fa65ccc7f284e7` — ZERO engine code changed this wave (evidence + probes + artifacts only; no Dooz-specific, R8-specific, or fake-content patch anywhere).

## PHASE 0 — Skill + HEAD + issue reconciliation (§0)
- Skill read (docs/execution-skill/SKILL.md v1.0 + v2 surface) and used (CLI contract for every run).
- **Skill self-test 13/13 PASS** at HEAD (docs/execution-skill/selftest_report.json).
- HEAD reconciled: `50b63bc7` == W3 re-proof evidence commit; binary byte-lineage `c0fa65ccc7f284e7` verified against the W3 recorded value; git tree clean of unrelated changes.
- Issues #354/#371–#378: bodies fetched (200 OK). Comment THREADS blocked (GitHub API rate limit + logged-out lazy-load + atom 404) — recorded honestly; the authoritative per-wave record = worklog.md + commit messages (the same content posted as dated issue comments each wave).
- LAW-001: all tested APKs PURE_DEX or x86/x86_64-MIXED IN-SCOPE; zero ARM-only artifacts touched.

## §1/§2 — F-NEW-256 first priority: synthetic rendering ladder
- **Probe A (native View: drawRect/drawText/drawBitmap/drawPath + save/translate)** and **Probe B (ViewGroup containing Probe A + TextView)**: built with the real toolchain (aapt2/ECJ/D8) as `fixtures/w4_ladder_probe`, APK sha20 `93d9224a9b9265accd88`, run **SUCCESS**.
  - drawRect framebuffer pixel == paint color EXACT ((204,34,34)=0xFFCC2222); drawCircle EXACT; drawPath EXACT; drawText 31k glyph pixels; drawBitmap **recorded but 0 pixels** for an in-memory createBitmap source — honest OBSERVED gap (§16: not root-ified without first-divergence work; resource-drawable bitmaps DO composite — proven by the fish provenance below).
  - screenshot sha16 `b525b4b67fdb86f4`; ladder table in `evidence/cont8/fnew256_w4_ladder.json`.
- **Probes C/D/E (minimal Compose Box/Text/Image): NOT buildable** — no kotlinc/Compose compiler in the toolchain (recorded honestly). Dooz serves as the Compose consumer (its UI is Box/Text/Image/Canvas composables).
- **Probe F (Dooz)**: baseline ×3 at HEAD — verdict `DEFAULT_BACKGROUND_ONLY`, `first_missing_stage=APP_DRAW_OPS`, anchor `d602648e8e401895` byte-identical ×3 (zero drift).
- **FIRST NO IN THE LADDER = the Compose node-tree materialization** (between Probe B and Probe C) — NOT the Canvas bridge, NOT layer routing.

## §1 F-NEW-256 — refined first divergence (the wave's core result)
- R8 class map for this dooz build established (Lt4;=AndroidComposeView, Lel0;=LayoutNode, Lpz0;/Lug0;=layers, Lv02;=UiApplier, Lnb0;=Composer, Lsl0;=SubcomposeLayoutState, Lrr0;/Ld;=app content lambdas, Ljt1;=AndroidCanvas...).
- 24,539-entry method trace (`MINIANDROID_METHOD_TRACE=1`) decisive counts: **exactly ONE Composer, ONE Applier, ONE applier insert (Lel0;.B), 4 change records, 4 LayoutNode ctors**; SubcomposeLayout family **0 entries**; AndroidCanvas `Ljt1;` **0 entries**; content lambdas invoked 6× all BEFORE the game-screen composable.
- **The apply ran at line 43094 INSIDE the app UI composable Ld;.i's live span (31698→44545)**: the change list materializes mid-content-pass, delivering only the 4 recorded changes; afterwards recording stops permanently. Upstream Compose law: applyChanges runs strictly AFTER the content lambda returns. This desynchronizes the slot table and suppresses all subsequent node emission → 1-node tree → faithful draw of an empty root → 0 canvas content ops.
- W3 candidate faces **(b) Canvas-bridge draw-op family and (c) LayerBuilder software routing are REFUTED** by the ladder (state ops flow; layers walk children; native path is color-exact).
- Artifacts: `evidence/cont8/fnew256_w4_trace.json` + `fnew256_w4_ladder.json` + `fnew256_w4_baseline.json`; registry F-NEW-256 updated (stays CLASSIFIED — not fixed per §16 discipline; repair surface = compose coroutine continuation ordering, the same chain as R-NEW-340/Dispatchers.Main).

## §3 — Previous-root reconciliation
- `evidence/current_head/root_reconciliation_wave4.md` — full 22-row table (F-NEW-158/160/162/175, ROOT-062/064, F-NEW-228, 251, 252, 253, 254, 255, 256, 257, 258, Dispatchers.Main, Looper/Choreographer, resources, filesystem, View measure/layout, Canvas bridge, Compose state/recomposition, LayoutNode draw) each with status/current-evidence/action/3-run.

## §4/§5/§6 — Verify (not blindly reopen)
- **F253PROBE 21/21 PASS** (B-01..B-08 Bundle parcel-family = F-NEW-257; S-01..S-07 SaveableStateRegistry = F-NEW-253; M-01..M-06 isInstance matrix + B-07 = F-NEW-258) — re-RUN live at HEAD.
- **W3PROBE 12/12 PASS** (F-NEW-253/254/255 rows) — live.
- **F252 probe 7/7 PASS** (CAS1-3/UPD = **F-NEW-251 VERIFIED_CURRENT, NOT reopened**; PNULL = F-NEW-252; **SLPOS/SLNEG = §6 generic ServiceLoader test**: provider found → instantiated → tag()==svcimpl; no-provider honest false). Note: first rebuild omitted META-INF/services (aapt2 doesn't package it) → repackaged → 7/7; root cause was the probe package, not the runtime.
- Dispatchers.Main: mechanism VERIFIED_CURRENT (SLPOS + W2 R8-renamed-provider live evidence; no `Lv;.o` intercept); MainDispatcherLoader selection remains UNREACHED behind F-NEW-256 — honest PENDING.

## §7/§8/§9 — Scheduling + budget classifications
- **FishRings**: full directive chain PROVEN — `Timer.schedule(5000ms)` enqueued (source=Timer.schedule, ready_at=5000ms virtual) → with `--frames 400` virtual time reaches 5100ms → Runnable dequeued → `startActivity(GameActivity)` → GameActivity onCreate (MediaPlayer PREPARED) → **real game board renders** (ImageView fish pieces; final frame sha16 `a341e3ad9092f640` ×3 byte-identical). CLASSIFICATION: **SCHEDULER-VIRTUAL-TIME face, NOT a rendering face** — the default 2-frame launch window never reaches the 5-second splash delay. `evidence/cont8/w4_fishrings_scheduling.json`.
- **FairyMahjong**: SUPERSEDED + ARTIFACT-LOST. The directive's 55M-instruction/VirtualMachineError premise predates the recorded fixes (F-NEW-243 org.json laws + F-NEW-244 kotlin-stdlib clinit spin = a PROVEN infinite semantic loop, NOT instruction starvation; recorded SUCCESS ×3 `76e097244767d6c3`). APK lost in the container reset; re-verification PENDING on re-supply. `evidence/cont8/w4_fairymahjong_budget.json`.

## §10–§13 — Dooz stress test + fan-out + scoreboard + visual proof
- Dooz checkpoints at HEAD: install/Application/Activity/Window/Compose root/attach ✓, measure/layout ✓ (1080×1920), state/recomposition machinery live, LayoutNode draw recursion ✓, **first_missing_stage=APP_DRAW_OPS with the refined upstream divergence above**.
- Fan-out (every result at current HEAD, no Dooz proof by Dooz alone): gmdice **SUCCESS full-frame ×3** (`ad35f81bd02328b2`), chess **anchor byte-identical** (`b5a7a35d`, 3 deterministic recorded NPEs unchanged — not a new root), 2048/tnake/Tetris/MiniCraft/Snake-Neon **REAL_APP_CONTENT**, goldens 4/4, opencalc/microtimer/unote anchors ×3 byte-identical.
- `evidence/current_head/SUCCESS_PATH_CURRENT.md` — the scoreboard (definition of "work" = explicit stage columns).
- 3-run evidence: gmdice ×3, FishRings ×3, anchors 5/5×3, dooz ×3, ladder ×2 (deterministic), goldens deterministic.

## §14 — Resource/image provenance
- `evidence/cont8/w4_resource_provenance.json`: FishRings APK entries `res/mipmap-mdpi-v4/{red,blue,green}.png` → dominant colors (212,0,0)/(0,0,212)/(44,160,44) → **EXACT** framebuffer pixel values (831/474/474 px). Provenance is pixel-true (identity), not "screenshot has color".

## Regression battery (§19/DoD 16-17)
- Skill self-test **13/13**; anchors **5/5 ×3 byte-identical** (opencalc e364b001, chess b5a7a35d, dooz d602648e, microtimer da73010a, unote 4f1a9e4e); goldens **4/4 PASS** (REAL_APP_CONTENT pixel gate); negatives **19/19 PASS**; probes **21/21 + 12/12 + 7/7**; zero engine changes → zero drift by construction, and verified live.

## Honest gaps (not hidden)
- F-NEW-256 remains CLASSIFIED (refined, not fixed): the generic repair (compose continuation ordering) was not attempted this wave — ladder-first discipline.
- Compose probes C/D/E not independently buildable (no kotlinc).
- drawBitmap for in-memory (non-resource) bitmaps: recorded-but-0-pixels — OBSERVED, not root-classed.
- FairyMahjong/BlockBlast APKs lost to container reset — re-supply needed.
- GitHub comment threads unreadable this session (rate limit) — bodies only.

## ADDENDUM — push hygiene
- tmp/issue377_saved.html (an automated-commit accident from the previous session, a raw GitHub HTML scrape) removed from the tree: its embedded GitHub feature-flag JSON trips the fail-closed guard, and the issue content is already preserved in tmp/issue377.html, tmp/issue377.txt, and the worklog. Also documented: when the staged file list is EMPTY, the guard's per-pattern grep runs with no path arguments and recurses into .git/ — it then hits the container's .git/config remote URL (env-var policy violation by the environment, not repo content). Guard fix candidates recorded for the next engine-touching wave: (a) fail the scan cleanly when the path list is empty, (b) always exclude .git/.
