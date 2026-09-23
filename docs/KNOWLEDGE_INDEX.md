# KNOWLEDGE_INDEX — Canonical Inventory of Knowledge & Research Files

> **SINGLE SOURCE OF TRUTH for knowledge navigation** (S52). Complements
> [`docs/INDEX.md`](INDEX.md) (concept navigation hub) and
> [`docs/EXECUTION_ACHIEVEMENTS.md`](EXECUTION_ACHIEVEMENTS.md) (execution
> evidence). Generated from the tracked file tree; regenerate with
> `python3 scripts/s52_gen_knowledge_index.py`. Knowledge files are NEVER
> deleted without classification first; duplicates are merged only after
> duplication is proven (S52 policy §7).

Snapshot: 745 tracked `.md` files — 441 KEEP (knowledge/process), 185 HISTORY (era records), 111 EVIDENCE (compact, cited), plus 290 tracked `.json` (indexes/fixtures/oracles — classified below).

## 0e. S74 additions

| Artifact | Class | Role |
|---|---|---|
| `docs/compatibility/` (apps/ tools/ capabilities/ + README + CAPABILITY_MATRIX.md) | KEEP | Compatibility Platform: 14 app dossiers, 12 tool/source profiles, 15 capability records, evidence-backed matrix — the fast-access layer over raw research (agents read this FIRST) |
| `docs/knowledge/laws/*.json` + `docs/knowledge/KNOWLEDGE_RECORDS.json` | KEEP | 31 canonical knowledge records (20 VERIFIED semantic laws, 8 honest OBSERVED open-frontier, 2 RESEARCHED, 1 SUPERSEDED false-claim `CLAIM-DOOZ-23472-VISUAL` preserved per evidence-quality law) |
| `docs/execution-skill/SKILL.md` | KEEP | vendor-neutral Android Execution Skill: 22-step execution loop, read order, status/evidence laws, autonomous-gameplay ladder, safe stop/resume |
| `tools/validate_compatibility_graph.py` | KEEP | graph integrity gate (PASS = references/statuses/provenance/evidence/registry-drift/index all green); forced F-120 back-registration + registry summary repair at S74 |
| `tools/promote_knowledge.py` | KEEP | knowledge promotion pipeline (RAW→…→VERIFIED; single-step; VERIFIED requires test+evidence+source; append-only journal) |
| `scripts/s74_*.py` | KEEP | emitter (evidence-derived records + status/cross-ref validation before write) + registry hygiene |
| `root_registry.json` F-120 entry | KEEP-law | back-registered S66 button-gravity law after validator gap detection; summary totals repaired (397) |

## 0d. S73 additions

| File | Class | Role |
|---|---|---|
| `docs/evidence/S73/S73_REPORT.md` | EVIDENCE | S73 canonical report: GitHub ledger (issues #10–#23), app matrix with current-HEAD re-execution metrics, autonomous-snake chain + C4 probes (wrap law, reverse-guard, game-over; restart open), dooz 23472-px metric reclassification (engine-default black region shared with activity-less apps), regression numbers, git/push state |
| `docs/evidence/s73_snake_autoplay/` | EVIDENCE | autonomous gameplay package: run_01..03 (frames + gameplay_trace.json + SHA256SUMS), determinism_proof.json (3/3 identical, 90 frames), snake_autoplay.gif (real frames), screenshot_metrics.json (B3 gate) |
| `scripts/s73_snake_controller.py` / `s73_snake_finalize.py` / `s73_snake_c4_probes.py` / `s73_snake_c4b_death_restart.py` / `s73_screenshot_gate.py` | KEEP | autonomous controller (pixel-only vision + scheduled real taps), 3-run finalizer, C4 probe batteries, B3 gate |
| `scripts/s73_corpus.sh` / `s73_corpus_one.sh` / `s73_fixtures.sh` / `s73_github_issues.py` / `s73_github_comments.py` | KEEP | corpus/fixtures batteries (current HEAD), GitHub ledger tooling (env-var token only) |
| engine `--tap x,y@frame` (F-117 extension) | KEEP-law | scheduled-input cadence (tap fires after frame k renders); legacy form byte-identical to stored W4 evidence; all-or-none CLI validation |

## 0c. S72-W4 additions

| File | Class | Role |
|---|---|---|
| `docs/foundation/S72_WAVE4.md` | EVIDENCE | W4 record: AndroidGameSnake source-first SCREENSHOT-PROVEN chain + F-148 (ConstraintLayout anchors) / F-149 (getDisplayMetrics + applyDimension + density unity) / F-150 (Thread game-loop: sleep de-noop, subclass receivers, frame-boundary drains, wake registry) + constitution-impact re-test |
| `docs/evidence/s72_w4_snake/` | EVIDENCE | 4 annotated frames + built APK + SHA256SUMS (final pixel sha 1a419545419deb3a ×3 byte-identical) |
| `scripts/s72_w4_*.py/.sh` | KEEP | build/corpus/fixtures/measure/proof/registry tooling (deterministic recipes) |
| `CONSTITUTION_V2.md` (root, W2) | KEEP-law | binding operation law for every claim in this wave |

## 0c. S63 additions

| Law / finding | Layer | Statement | Status | Priority | In-repo | Evidence |
|--------|-------|-----------|--------|----------|---------|----------|
| F-113 SecureRandom IS-A Random bridge law (R-NEW-382) | engine | bridge_to_api receives the STATIC receiver class; SecureRandom instances never reached the F-086 Random law (Random + ThreadLocalRandom only) → nextInt(bound) typed-zero 0 (all gmdice dice read 1). OpenJDK law: SecureRandom.java:157 extends java.util.Random, :828 next(int) override supplies the bit stream while Random.nextInt(bound) keeps the contract. Fix: law family += Ljava/security/SecureRandom; | IMPLEMENTED+TESTED (battery ALL PASS 94 executed; dice 6/5/3/2; pixel diff 1,584 px in result band; 3-run det ×3) | P0 | YES | docs/evidence/s63_spotlight/S63_REPORT.md §1 |
| S63 spotlight: first SOURCE-FIRST L6 | corpus | gmdice v12 (ge0rg/gamemasterdice @6353926f) APK ee9f7396 built aapt2/ECJ/D8 → executed → UI → render (1,744,539 px) → 5/5 clicks → real handler → state mutation (dice 6/5/3/2) → changed frame (SHA 5312266e→fa1d8612, diff confined to the result band) — repeatable ×3. siggen v1.76 (billthefarmer/sig-gen) APK c83d21c6 → rc=0, FQCN-tag custom views inflated, 47,809 px == S61 prebuilt count, 5/5 clicks, R.id.sine case + audio.waveform mutation (S7 honest) | EXECUTED+OBSERVED (S10/L6 + S7/L5) | P0 | YES | docs/evidence/s63_spotlight/S63_REPORT.md §1-§2 |
| zoekt large-file under-report root cause | tools | zoekt-index default max_trigram_count silently EXCLUDES very large files (dalvik_engine.cpp 1.2MB → 0 hits); raised cap (100000000) → complete results (found F-113 lines at 20878). Explains the S61/S62 "under-report" open question. csearch per-file trigram limit reproduced 3rd time (candidate sources fine at 3ms). zoekt+cindex/csearch rebuilt this session (Go 1.26.0; go module proxy stalls — GOPROXY=direct works) | OBSERVED (tool law) | P1 | YES | docs/evidence/s63_spotlight/S63_REPORT.md §4 |

| F-114 prefs law family (R-NEW-383) | engine | (a) SharedPreferences.getString @Nullable default → NULL reference (was "") — AOSP SharedPreferencesImpl.java:307-313; (b) PreferenceManager.setDefaultValues parses the defaults XML (any xml-bearing type; real face: PreferenceScreen under res/layout/) and persists key/defaultValue + _has_set_default_values one-shot flag (PreferenceManager.java:661-673/:67); (c) getDefaultSharedPreferences = <pkg>_preferences (was NULL receiver) | ROOT-CAUSED-FIXED (pmk rc=1 NFE → rc=0 views=179 det×3; second consumer simplestopwatch defaults=24) | P0 | YES | docs/evidence/s64_spotlight/S64_REPORT.md §2 |
| F-115 Timer + virtual-clock law family (R-NEW-384) | engine | java.util.Timer.schedule rides the ONE MessageQueue (OpenJDK sched/mainLoop fixed-delay law; period>0 re-enqueues via __timer_period__); F-115b: launch-frame quiescence does NOT advance the clock (GATE H/G07 goldens frozen) — deferred timers fire under time-driven --frames capture | ROOT-CAUSED-FIXED (FreeKlondike splash-trap → S10; simplestopwatch timer = second consumer) | P0 | YES | docs/evidence/s64_spotlight/S64_REPORT.md §3 |
| F-116 meta-data law family (R-NEW-384) | engine+manifest | <meta-data> captured per activity+application; getActivityInfo(ComponentName,flags).metaData Bundle (numeric→INT32, else STRING); Context.getComponentName law | ROOT-CAUSED-FIXED (FK splash timeout/redirect) | P0 | YES | docs/evidence/s64_spotlight/S64_REPORT.md §3 |
| F-117 scheduled-tap law (R-NEW-384) | harness | when --frames drives the virtual clock, queued taps fire one per frame boundary (AOSP input timing = touch lands at its Looper time) | IMPLEMENTED+TESTED (FK deferred-screen interaction) | P1 | YES | docs/evidence/s64_spotlight/S64_REPORT.md §3 |
| S64 spotlight: breadth +3 (S6/S10/S9) | corpus | pmk-android v3.3.6 (0b3bfdc3) S6 det render c9a2a703 ×3, 179 views; FreeKlondike v2.0.1 (985afeb0) S10 chain splash→Timer→menu→tap→GameActivity→"Deal!" changed frame det×3; shopping-list-calc v2.0 (b51e6ecf) S9 7/7 clicks→real lambdas→state_changed→8,348-px diff det×3. Survey: F-Droid index local scan (4,408 pkgs) + zoekt/csearch on pinned clones + AOSP/OpenJDK upstream laws | EXECUTED+OBSERVED (S6 + S10 + S9) | P0 | YES | docs/evidence/s64_spotlight/S64_REPORT.md §0-§10 |
| F-118 activity-constructor law (R-NEW-385) | engine | every activity-construction path must run the declared no-arg <init>()V before onCreate — AOSP Instrumentation.java:1448 newActivity(ClassLoader,String,Intent) → instantiateActivity (performLaunchActivity contract; OpenJDK Class.newInstance). G08 consume_pending_intent now dispatches <init> with a [G08-LIFECYCLE] record | ROOT-CAUSED-FIXED (TriPeaks 52 dead taps listener_id=0 → 38 + CLICK to GameActivity$1; consumers day one: OPMT <init> 26 insns, FishRings chain) | P0 | YES | docs/evidence/s65_spotlight/S65_REPORT.md §3 |
| F-119 X.TYPE + primitive-array descriptor law (R-NEW-386) | engine | (a) Box .TYPE fields (Integer/Boolean/Byte/Character/Short/Long/Float/Double/Void) answer canonical primitive Class objects I/Z/B/C/S/J/F/D/V — OpenJDK Integer.java:106 TYPE = Class.getPrimitiveClass("int") (JVM-injected, never in <clinit>); (b) Array.newInstance with primitive components builds "[I"-style descriptors recursively (no L...; wrapper) — OpenJDK Array.java:74/110 + DEX/JLS descriptor spec | ROOT-CAUSED-FIXED (FishRings Integer.TYPE SGET-MISS → null matrix → 3× aput-null NPE rc=1 → rc=0, [[I matrix, S10 det×3; TicTacToe R-NEW-358 Button[][] golden PASS on the changed path) | P0 | YES | docs/evidence/s65_spotlight/S65_REPORT.md §4 |
| OBJECT-IDENTITY family (open) | engine | field/array-element object-ref identity churn: cardsViews[] element comparisons fail (view refs stored via aput-object then compared with if-eq), listener field re-reads churn (38→273) — blocks field-initialized-listener apps at S8 and string-equality state chains (OPMT empty move list → app-own nextInt(0)) | OBSERVED (open family; forensic trail tp_f118.log/opmt_full.log; NEXT highest-leverage target) | P0 | YES | docs/evidence/s65_spotlight/S65_REPORT.md §7 |
| S65 spotlight: breadth +3 (S7/S10/S6) | corpus | TriPeaks v1.2.1 (52272ae6) S7 full chain + det×3; FishRings v1.23 (14d7dd80) S10 PROVEN 3× input→GameActivity$5/$6→changed frames 483,395/478,169/7,347 px det×3; OPMT v0.1.2 (4f91e380) S6 + GameActivity chain det×3. Survey: F-Droid 45-keyword scan → 120 shortlist → parallel raw-gradle probes (flutter/libgdx/kivy excluded by signature) | EXECUTED+OBSERVED (S7 + S10 + S6) | P0 | YES | docs/evidence/s65_spotlight/S65_REPORT.md §0-§9 |

## 0c. S62 additions

| Law / finding | Layer | Statement | Status | Priority | In-repo | Evidence |
|--------|-------|-----------|--------|----------|---------|----------|
| S62+ spotlight: 2 NEW open-source APKs executed source-first | corpus+engine | anuto 8794573d (mjaun/android-anuto @33ed89e3) L5 PROVEN + tap→onTouch consumed=true in real DEX; OpenSudoku 712b4a41 (romario333/opensudoku @d1914649) L5 PROVEN + 3/3 CLICK dispatched to real FolderListActivity$1; 3-run det 11a38a5a/11671b9c ×3 each | IMPLEMENTED+TESTED | P0 | YES | docs/evidence/s62plus_spotlight/S62PLUS_REPORT.md |
| F-110 family IMPLEMENTED (a-e) | engine | (a) result-snapshot deferral: outermost-only result.heap/call_stack copy (was EVERY nested method exit = O(N×heap) quadratic; gprof 387.6M pair<string,string> copies) → 57.8× instruction rate A/B (128,076→7,400,000+ insns in the same 25s anuto startup budget). (b) Thread.sleep inside a drained body = deterministic yield. (c) ArrayList add(int,E)/remove(int)/remove(Object) heap-backed laws. (d) currentThread() = drained thread object inside its body. (e) touch-target law (onTouch-able views are targets) + MotionEvent materialization/getters + framework static-int table | IMPLEMENTED+TESTED (A/B + battery 96/96 + goldens) | P0 | YES | docs/evidence/s62plus_spotlight/S62PLUS_REPORT.md §2 |
| F-111 <view class> namespace law | resources | AOSP createViewFromTag reads class via getAttributeValue(null,...) — no namespace; the android-ns-default lookup missed it and degraded custom views to generic View (G11 ctor law never fired). Fix: namespace-agnostic lookup; anuto GameView now really constructed + onDraw dispatched | ROOT-CAUSED-FIXED | P0 | YES | docs/evidence/s62plus_spotlight/S62PLUS_REPORT.md §3 |
| F-112 manifest Application buildClassName law | apk | ".Name"/"Name" application classes join the manifest package (AOSP PackageParser law; same law the main-activity name already had). Without it .AnutoApplication → L/AnutoApplication; → default-Application fallback → app singleton never created | ROOT-CAUSED-FIXED | P0 | YES | docs/evidence/s62plus_spotlight/S62PLUS_REPORT.md §3 |

| Law / finding | Layer | Statement | Status | Priority | In-repo | Evidence |
|---|---|---|---|---|---|---|
| S62 measured decomposition of R-NEW-381 | engine | (a) F-107 A/B honest verdict: throughput UNCHANGED on dooz v23 (700K vs ~690K instr @480s identical budgets); the 0→197px move was F-108's draw contract. (b) S62 bucket timers: loop bookkeeping CLEAN (insn.pre 0.026%, insn.post 0.084% of wall). (c) Per-<clinit> duration law: top-10 chains = 74% of class-init time, top-50 = 95% (Lug0; 23-instr <clinit> = 7.1s). (d) The 7.1s chain = 1,024 × Lnd1;.c = androidx ColorSpace Rgb transfer-table static init = 90% of ALL executed instructions (register evidence: "Display P3","NTSC (1953)","SMPTE-C RGB","scRGB"). (e) Op self-time: sget-object 23.3ms/call (37% wall), new-instance 9.4ms (14.5%), sget 88ms — ~69% of wall = first-touch sget/new-instance carrying cold-init subtrees of REAL interpreted work | OBSERVED+MEASURED (TSC=3.20GHz calibrated; scripts/s62_clinit_costs.py; METHOD-TRACE causal window) | P1 | YES (docs/evidence/s62_r381/S62_REPORT.md) | run/s62_buckets, run/s62_opself, run/s62_f107_ab_*, run/s62_lbl_trace |
| F-109 (a/c) register-write bitmap + strcmp arith | engine | F-109a: DexRegisterFile written-set std::set<uint8_t> RB-tree insert per register write → fixed 256-bit bitmap (identical ordered get_written_registers/dump output). F-109c: 23 × `std::string(op)` temporaries per arith instruction → strcmp dispatch | IMPLEMENTED+TESTED (helloworld 26/26, tictactoe 8/8, battery ALL PASS 96) | P2 | YES (dalvik_engine.h/cpp) | docs/evidence/s62_r381/ |
| F-109 honest impact + F-110 lever | engine | F-109 gain ~9-10% instruction rate (100K @ 25.0s vs 27.4s) — marginal; composition frontier unchanged. Measured next lever: per-invoke constants (tri.resolve 15.8µs + em.setup 22.7µs) + DalvikValue copy cost (2×std::string per register access) | REGISTERED (measured, not guessed) | P1 | — | docs/evidence/s62_r381/S62_REPORT.md §2 |
| R-NEW-331 S62 face (fragment host attach law) | framework | 3 spotlight games (minesweeper, memory, 2048) die at the SAME real-DEX ISE: FragmentManager.ensureExecReady "not been attached to a host" (pc=24) at Splash/Main onCreate → app-boundary unwind. First-engine precision: the FULL real androidx chain dispatches and returns OK (FragmentActivity.<init> → HostCallbacks → FragmentController.createController → FragmentHostCallback → FragmentManagerImpl → FragmentActivity.onCreate → ComponentActivity.onCreate → performRestore) — yet FragmentController.attachHost never dispatches; APK string pool contains "attachHost". 4th consumer: Telegram golden (csearch cross-hit) | OBSERVED (3 runs + trace + cross-evidence) | P1 | — | run/s62_game_mines, run/s62_probe_*; run/s62_mines_trace.log |
| Games corpus first L6 | corpus | bouncy (com.dozingcatsoftware.bouncy): --click-count 6 → 6/6 clicks dispatched into real DEX XML-onClick handlers on BouncyActivity; 7 frames; render-state transition proven by frame SHA pair 4219c5116ea2 → 52e4ddacc8ac; representative frames committed (35.5 KB + 20 KB). Honest: not claimed L7 | EXECUTED+OBSERVED | P1 | YES (docs/evidence/s62_r381/bouncy_frame*.png) | run/s62_bouncy_l6 |
| Search ledger S62 rows | tooling | zoekt under-report reproduced on `attachHost` (2nd instance); csearch `ensureExecReady` 2ms → Telegram cross-evidence reuse (duplicate research avoided) | EXECUTED | P2 | YES (docs/corpus/SEARCH_LEDGER.md) | docs/corpus/SEARCH_LEDGER.md §S62 |

## 0c. S61 additions

| Law / finding | Layer | Statement | Status | Priority | In-repo | Evidence |
|---|---|---|---|---|---|---|
| F-107 (a/b/b2/c/c2/d, evidence-cost law family) | engine | The interpreter's evidence/diagnostic machinery must never tax execution. Measured (gprof + rdtsc phase timers, dooz v23 60-90s runs): `__tcf_0` static-destructor churn 739M entries ≈ 50% of wall + 464M std::function manager calls (function-local statics of std::string); per-instruction InstructionTrace (Clock::now ×2) with O(n) `erase(begin)` ring; ApiCallTrace cap front-erase per push; `is_subclass_of` interface closure = LINEAR SCAN of all classes per chain step inside the is_a classifier; `all_methods()/get_method()` by-value copies (native check copied the method table per try_recursive_invoke — 773k MethodInfo copies; overload search ~40 KB per invoke). Fixes: trivially-destructible `const char*` tables; `batched_cap_push` bounded-lag FIFO; per-instruction traces default OFF (`MINIANDROID_TRACE_CAP` opt-in; API traces stay on — primary evidence); interface closure via the F-103 `class_to_interfaces_` index; non-copying `for_each_method/find_method` accessors; in-place overload selection over stable pointers (dex_report_->classes never mutates after load) | IMPLEMENTED+TESTED (battery ALL PASS 96 after the test-oracle opt-in: the three semantic harnesses read instruction_traces for HALT_RETURN and set trace_cap=2000 explicitly — the runtime default stays OFF; goldens PASS; `__tcf_0` gone from the profile) | P1 | YES (dalvik_engine.cpp/h, execution_engine.cpp/h, main.cpp, 3 semantic test cpp) | run/s61_r381_prof*, /tmp/gprof*.txt; docs/corpus/UPSTREAM_INVENTORY.md §2.3 |
| F-108 (R8-rename identity law) | engine+framework | Package-prefix identity is NOT a contract under R8 minification: dooz v23 DEX has 0 `Landroidx/compose/` class names (AndroidComposeView=Lt4;, ComposeView=Lho; → ViewGroup; 21 androidx names kept only for Parcelizer/serialization). The SURVIVING identity is the DEX hierarchy + the AOSP ViewGroup contract: a non-framework class that OVERRIDES dispatchDraw carries the compose draw-dispatch contract. The UC009 parent-rect expansion, the F-099 owner gate, and a new children-empty contract branch all key on `chain_overrides_method(class, "dispatchDraw")` — no app names hardcoded | IMPLEMENTED+TESTED (deep 560s run: UC009-DRAW expanded Lt4; to 1080x1920; C013-ONDRAW dispatched the interpreted dispatchDraw of the R8-renamed owner; framebuffer 197 non-white px — was 0; goldens PASS; battery ALL PASS 96) | P1 | YES (execution_engine.cpp stage_render_frame) | scripts/s61_r381_dex_truth.py; docs/evidence/s61_r381/ |
| R-NEW-381 S61 face (composition volume) | runtime | The dooz v23 composition's remaining cost is REAL interpreted work: 627 cold `<clinit>` class-init chains (AOSP ClassLinker::EnsureInitialized law: 5,784 warm + 42 framework-skip + 627 cold), ~23K invokes, ~700K instructions per 560s run; the interpreted dispatchDraw runs but the composition has not produced LayoutNodes → 0 canvas ops. The draw chain itself is WIRED end-to-end (F-108) | OBSERVED (phase-timer profile; not a semantic bug — a throughput/budget frontier) | P1 | — | run/s61_r381_deep/; docs/evidence/s61_r381/ |
| Runtime Spotlight Corpus Phase A | corpus | 53 F-Droid apps fetched SHA-verified (api/v1-driven, capability-tagged) + 52 executed in the S61 sweep (L5=7, L4=3, L2=39, L1=3) + 9 pre-existing = **61 corpus apps**. Capability-selection law (no random picks); honest L-levels per app; Phase B (100) deferred with an idempotent pipeline | EXECUTED+OBSERVED | P1 | YES (scripts/s61_spotlight_fetch.py, scripts/s61_spotlight_run.py) | docs/corpus/spotlight_manifest.json; docs/corpus/spotlight_results.json; docs/corpus/SPOTLIGHT_COVERAGE.md |
| Search tools real benchmark | tooling | zoekt (sourcegraph) + codesearch (google) built from source (go1.22.5→1.26.8) and benchmarked vs ripgrep on 5 real campaign queries: rg 7-8 ms complete ground truth; zoekt 35-49 ms (under-reported 2/5 — recorded limitation); csearch 2 ms (silently under-indexed the 1.2 MB dalvik_engine.cpp). Probe: UNAVAILABLE (multi-round negative). Ledger prevents duplicate research (2 reuse decisions recorded) | EXECUTED+OBSERVED | P2 | YES (docs/corpus/SEARCH_LEDGER.md; tools/gopath/bin) | docs/corpus/SEARCH_LEDGER.md |

## 0b. S56/S57/S58/S59 additions

| Law / finding | Layer | Statement | Status | Priority | In-repo | Evidence |
|---|---|---|---|---|---|---|
| F-106 (law family) | engine | R-NEW-380 closure: **(a)** Class.getDeclaredConstructor/getConstructor full upstream contract — referent resolution through __referent_desc (F-103 authority), exact parameter-descriptor ctor selection from the (possibly null) Class[] arg, getConstructor=public-only, no match → NoSuchMethodException (throw_deferred; the caller catch block is the designed path), match → record carries class_desc=REFERENT + __reflect_mods + __reflect_params; Constructor.getModifiers/getParameterTypes laws; the java.lang.reflect.Modifier static bit family (isPublic..isStrict — JVM/DEX shared bit positions); Class.toString() token law ("class "/"interface " + getName()) in the Class-token section AND the StringBuilder stringify_arg law (CLASS_REF + heap-token shapes — the literal mechanism behind the EMPTY name in the R-NEW-380 message). **(b)** Collections.unmodifiableMap/Set/Collection — the unmodifiable view delegates every read to the backing container (the unmodifiableList precedent; single-threaded engine). **(c)** Long.toString(J) / Long.toString(J, I) — signed 64-bit radix 2..36, MIN_VALUE-safe magnitude, out-of-range radix → IAE — the Compose rememberSaveable registry key law (Long.toString(compositeKeyHash, 36)) | IMPLEMENTED+TESTED (six f106 records incl. the discriminating f106_newinstancefactory_full_chain (const-class → getDeclaredConstructor(null) → getModifiers → isPublic → newInstance → real <init> → 127) and f106_getdeclaredconstructor_missing_throws_nsm; semantic 32/32; dooz v23 post-fix ZERO exceptions — create chain resolves through the app's OWN Hilt factory (Lk2; case-1) and the GameViewModel constructs; dooz v18 healthy; battery ALL PASS 96) | P1 | YES (dalvik_engine.cpp) | R-NEW-380 closure + R-NEW-381 registration; docs/evidence/s60_r380/ |
| F-105 (law family) | engine+framework | R-NEW-379 closure: **(a)** declaration↔heap class reconciliation for object references (`reconcile_class_decl()` shared by instance-of + check-cast): generic declaration → heap wins (F-103 preserved); consistent pair → the more specific wins; CONTRADICTION → the creation-site declaration wins (the engine shares ONE integer id space between shadow entities and heap objects BY DESIGN — the F-023 activity-as-view node — so a heap record at a referenced id may belong to a DIFFERENT entity; re-homing onto proxies was REJECTED — the proxy id breaks the next shadow hop). **(b)** ComponentActivity view-tree owner contract: ActivityShadow setContentView(View) installs the ACTIVITY object under the app's OWN view_tree_lifecycle_owner id (name-resolved via arsc find_id) on the activity-as-view node BEFORE the attach wave. **(c)** instance-of classifies CLASS_REF values (const-class tokens) by the token's heap record — the token's runtime class IS java.lang.Class (X.class instanceof Class == TRUE; X.class instanceof X == FALSE) | IMPLEMENTED+TESTED (f105_instanceof_classtoken_is_class + f105_instanceof_classtoken_not_referent; semantic battery 26/26; dooz v23 ISE 0 (was ×4), depth 8→81; corpus determinism chessclock/notes/unote == S57/S58 records; battery ALL PASS) | P1 | YES (dalvik_engine.cpp instance-of/check-cast/reconcile; android_shadows.cpp setContentView owner install) | R-NEW-379 closure + R-NEW-380 discovery; docs/evidence/s59_r379/ |

| File | Topic | Purpose | Status | Priority | Canonical? | Related |
|---|---|---|---|---|---|---|
| F-102 (law) | engine | 3rc invoke-*/range descriptor dispatch law: the call-site method PROTO is part of the invoke contract — hoist + pass `range_proto` to both try_recursive_invoke attempts; exact (class,name,desc) selection per F-023, heuristic path unchanged when the proto misses | IMPLEMENTED+TESTED (f102_range_ctor_overload_exact_dispatch, discriminating; dooz v18+v23 RECURSION-LIMIT 0; battery 96/96) | P0 | YES (dalvik_engine.cpp range-invoke case) | R-NEW-376 closure; docs/evidence/s58_r376/ |
| F-103 (law) | engine | java.lang.Class type-question family: isInstance/isAssignableFrom walk the real class hierarchy (superclass + declared-interfaces index); const-class mints HEAP-BACKED tokens (real Ljava/lang/Class; object, `__referent_desc` field, identity map — kills the token/heap id-space collision); instance-of runtime-type authority (heap class wins over the register tag) | IMPLEMENTED+TESTED (f103_* 3 checks; dooz saved-state IAE 0, key-class IAE 0; battery 96/96) | P0 | YES (dalvik_engine.cpp bridge + const-class + instance-of) | R-NEW-378 closure; docs/evidence/s58_r376/ |
| F-104 (law family) | engine+framework | io/state surface: FileInputStream/FileReader sandbox ctor + "file:" stream keys; Uri.fromFile/getPath/getScheme/getLastPathSegment; ContentResolver.openInputStream; AsyncTask.execute (doInBackground+onPostExecute, ancestor-walk); EnumSet.of (array-backed, R-NEW-360 copy law consumes); java.util.regex Pattern/Matcher over std::regex (find/matches/group/appendReplacement/appendTail); requestPermissions→onRequestPermissionsResult dispatch; BufferedInputStream in the EXP-071 propagation chain; [EXP093-FNA] env-gated | IMPLEMENTED+TESTED (Notes real read chain live: 10 real readLine lines, 230-char setText+markdownCheck verified; battery 96/96) | P1 | YES (dalvik_engine.cpp bridge, android_shadows.cpp setText) | F-085 content path; docs/evidence/s58_r376/ |
| R-NEW-379 (frontier) | knowledge | Dooz post-F-102/F-103 face: compose init died at ISE "ViewTreeLifecycleOwner not found from Lho;@1074" — CLOSED S59 via F-105 (owner install + declaration/heap reconciliation + CLASS_REF token instance-of); successor face R-NEW-380 (ViewModelProvider create chain) | ROOT-CAUSED-FIXED (S59) | P1 | YES (root_registry.json) | docs/evidence/s59_r379/; ROADMAP_STATUS §3.1 |
| F-086 (law) | engine | java.lang.Long 64-bit comparison bridge family: compare(J,J)=signed -1/0/+1, compareUnsigned on the unsigned domain (OpenJDK Long.java law); closes the STUBBED-typed-zero class for wide-arg static invokes — R8's unsigned-compare idiom `Long.compare(x^MIN, y^MIN)+if-gtz` silently took the wrong branch when the handler was absent | IMPLEMENTED+TESTED (semantic_long_cmp_conv_test f086 group 6/6, battery stage "expect 20"; dooz23 runtime proof: ScatterMap capacity 7→15→31 via MINIANDROID_FIELD_TRACE, HALT-LOOP 0, F084 fires 0) | P0 | YES (dalvik_engine.cpp F-055 Long block) | R-NEW-344 closure; docs/evidence/s57_dooz23/F086_EVIDENCE.md |
| F-084 (law) | engine | HALT-RETURN containment: a callee exiting via the loop-detector/budget halt has NO return value — the stale last_invoke_return_ must never reach the caller's move-result; discriminator `halted_ && !halted_on_return_`; escalates as deferred VirtualMachineError (F084-HALT-RETURN) | IMPLEMENTED+TESTED (battery 96/96; first attempt without the discriminator broke stages 59-63, fixed pre-commit) | P0 | YES (dalvik_engine.cpp invoke boundary) | R-NEW-344; dooz v23 garbage-index face |
| F-085 (model) | framework | Generic WebView content model: ViewShadow dispatches the WebView family (getSettings memoized per-instance, setWebViewClient/load family); WebSettingsShadow = symmetric set/get property bag; load family stores the document; render law = generic HTML→visible-text (no markdown special-casing) | IMPLEMENTED+TESTED (battery 96/96; shadow-count invariant 19→20/22) | P1 | YES (android_shadows.cpp/h + shadow_registry.cpp) | R-NEW-377; Notes content face |
| R-NEW-368 (verdict) | knowledge | uNote touch-target premise REFUTED: the 16-probe grid (y 300..1780) never covered the bottom-44px button band (y=1876..1920); coordinate-correct tap (270,1898) → G06-TAP DOWN target=13 consumed → UP click_posted → startActivity(NoteEdition) | VERIFIED-FIXED (no engine defect) | P1 | YES (root_registry.json) | docs/evidence/s56_unote/ |
| R-NEW-344 (refinement) | knowledge | dooz v23 face moved: Recomposer/ControlledComposition reached; blocker = androidx.collection ScatterMap insert into a FULL table (cap 15, size 15, zero EMPTY bytes); the second grow (e==0, size 14) ran the R8-inlined resize at newCap=15 (epilogue e=0 = loaded(15)-14) instead of 31 | **ROOT-CAUSED-FIXED at S57** (F-086: the missing Long.compare bridge made the growth decision take the cleanup branch; 15→31 proven at the runtime boundary) | P0 | YES (root_registry.json) | docs/evidence/s56_dooz23/ + docs/evidence/s57_dooz23/ |
| docs/evidence/s56_dooz23/ | evidence | F-084 pre/post-fix faces + the budget-counter (e-field) history + metadata-store timeline; SHA256SUMS | EVIDENCE | P1 | YES | ROADMAP_STATUS §2/§3 |
| docs/evidence/s56_unote/ | evidence | uNote tap-target refutation: view-tree geometry + canonical tap pipeline + NoteEdition navigation, SHA256SUMS | EVIDENCE | P1 | YES | R-NEW-368 |
| scripts/s56_dump_v23.py + s56_registry_update*.py | tooling | v23 DEX method disasm probe (diff-chain-correct) + S56 registry updaters | KEEP | P1 | YES | R-NEW-344 evidence |
| S55 rows below | — | retained for continuity | — | — | — | — |

## 0c. S55 additions (prior session)

| File | Topic | Purpose | Status | Priority | Canonical? | Related |
|---|---|---|---|---|---|---|
| F-082 (law) | framework | ViewAnimator displayed-child laws on ViewShadow: setDisplayedChild/getDisplayedChild/showNext/showPrevious (AOSP clamp `which≥count→count-1; <0→0` incl. childless, showOnly visibility walk, requestLayout flag) | IMPLEMENTED+TESTED (18-check law test in battery) | P0 | YES (android_shadows.cpp/h) | R-NEW-377; Notes v139 L7 |
| F-083 (law) | engine | ART contract for app recursion: engine runs on a 1GB-virtual-stack pthread; MAX_RECURSION_DEPTH 2048 (EXP-053 80KB/frame law); limit-drop ALWAYS loud; F-074 trace env-gated (MINIANDROID_F074_TRACE) | IMPLEMENTED+TESTED | P0 | YES (main.cpp + dalvik_engine.h/cpp) | R-NEW-361 → VERIFIED-FIXED |
| R-NEW-377 (entry) | knowledge | Notes read↔edit state machine (F-082) + content-face root cause: MarkdownView extends WebView → generic WebView content model is the next dependency (app-specific rendering forbidden) | VERIFIED-FIXED (state machine) / BLOCKED-PINNED (content) | P1 | YES (root_registry.json) | ACHIEVEMENTS §3.2 |
| R-NEW-376 (entry) | knowledge | Post-F-083 Dooz v18 frontier: ctor chains exceed the 2048-frame budget (9 cap-climbs; j0/t0/E0 hop evidence; next steps ranked) | OBSERVED-FAIL (pinned) | P1 | YES (root_registry.json) | ROADMAP_STATUS §3.1 |
| docs/evidence/s55_notes/ | evidence | S55 Notes click-test evidence (mid-investigation binary): frames + click_test_report.json + run.log + SHA256SUMS | EVIDENCE | P1 | YES | ACHIEVEMENTS §3.2 |
| docs/evidence/s55_notes_v2/ | evidence | FINAL-binary Notes evidence: frames byte-identical to s55_notes (determinism), census_delta.json (2,057,718 px face-swap delta, 99.23%), SHA256SUMS | EVIDENCE | P1 | YES | ACHIEVEMENTS §3.2 |
| docs/evidence/s55_dooz/ | evidence | R-NEW-361/376 key dispatch traces: pre-F-083 (ghost metadata, depth=80 drops) vs post-F-083 (healthy init, ctor-climb caps), SHA256SUMS | EVIDENCE | P1 | YES | ROADMAP_STATUS §2/§3 |
| scripts/s55_notes_evidence.py | tooling | per-frame census + pixel-delta audit for click-test runs (§19/§20) | KEEP | P1 | YES | screenshot gate law |
| scripts/s55_refetch_corpus.sh | tooling | SHA-verified corpus re-fetch after container reset (zero-APK policy kept) | KEEP | P1 | YES | APK_REGISTRY.json |
| scripts/s55_dump_methods.py + s55_j0_inits.py | tooling | DEX method disasm probes (ScatterMap face + j0/t0/E0 ctor delegation ground truth) | KEEP | P1 | YES | R-NEW-361/376 evidence |
| scripts/s55_registry_update.py | tooling | S55 registry updater (R-NEW-361 verdict, R-NEW-376/377 registration) | KEEP | P1 | YES | root_registry.json |
| S53/S54 rows below | — | retained for continuity | — | — | — | — |

## 0c. S54 additions (prior session)

| File | Topic | Purpose | Status | Priority | Canonical? | Related |
|---|---|---|---|---|---|---|
| docs/ACHIEVEMENTS.md | executions | canonical execution record (renamed from EXECUTION_ACHIEVEMENTS.md) | KEEP | P0 | YES | replaces EXECUTION_ACHIEVEMENTS.md (pointer) |
| docs/ROADMAP_STATUS.md | roadmap | canonical roadmap (renamed from ROADMAP.md) | KEEP | P0 | YES | replaces ROADMAP.md (pointer) |
| docs/evidence/s54_frames/ | evidence | 12 gate-passing JPGs + SHA256SUMS (chessclock restored, helloworld dark-content, 5 interactive apps) | EVIDENCE | P0 | YES | ACHIEVEMENTS §6 |
| scripts/s54_image_audit.py | tooling | generic gate checker (S54 refined law: DARK-CONTENT class) | KEEP | P1 | YES | gate law |
| scripts/s54_gallery_emit.py | tooling | canonical gallery emit (JPG ≤100KB + SHA256SUMS) | KEEP | P1 | YES | gate law |
| scripts/s54_evidence_runs.sh | tooling | reproducible fresh-evidence run set (§5/§6/§20) | KEEP | P1 | YES | reproducibility |
| scripts/s54_evidence_audit.py | tooling | gate+delta+SHA audit over fresh runs | KEEP | P1 | YES | evidence QA |
| scripts/forensic/s54_chessclock_disasm.py | tooling | ChessClock DEX disasm probe (F-080/F-081 evidence) | KEEP | P1 | YES | root-cause record |
| F-080 (law) | engine | Resources.getColor(I,Theme) resid = first INT arg | IMPLEMENTED+TESTED | P0 | YES (dalvik_engine.cpp) | ChessClock L7 |
| F-081 (law) | engine | M3-19 cycle key overload-distinct (name+descriptor) | IMPLEMENTED+TESTED | P0 | YES (dalvik_engine.cpp) | ChessClock L7 |
| docs/history/campaign-reports/ | history | era campaign reports; DIVERGENT-LINEAGE caution: Sep 9–15 reports cite HEADs that are not objects in this repo | HISTORY | P3 | partial | ACHIEVEMENTS §7 |

## 1. Status legend

| Status | Meaning |
|---|---|
| KEEP | current canonical knowledge — read these first |
| KEEP (knowledge core) | distilled upstream/engine knowledge under `docs/runtime/knowledge/` |
| HISTORY | era record (experiment/campaign report) — valid for its era, not current truth |
| EVIDENCE | compact, cited evidence tree under `docs/evidence/` |
| GENERATED | machine-generated index (regenerable) |
| LOCAL-AGENT | working notes for the agent loop (`.agent/`), not project docs |
| SUPERSEDED | pointer added; content absorbed by a canonical file |

## 2. Knowledge files — per-file inventory (knowledge-class trees)

| Path | Topic (first heading) | Subsystem | Status |
|---|---|---|---|
| `docs/research/compose-study.md` | Compose Study — the Compose boundary as seen by a userspace runtime | Compose | KEEP |
| `docs/architecture/dalvik_architecture_notes.md` | Dalvik Virtual Machine Architecture - Technical Research Notes | DEX/Dalvik | KEEP |
| `docs/architecture/miniandroid_vs_dalvik.md` | MiniAndroid vs Dalvik (AOSP) Architecture Comparison | DEX/Dalvik | KEEP |
| `docs/research/FIND_REUSE_DEX_ART_AUDIT.md` | P2/P3 — DexFile + dexHunter RESEARCH AUDIT (FIND-REUSE-DEX / FIND-REUSE-ART) | DEX/Dalvik | KEEP |
| `docs/research/aosp-runtime-study.md` | AOSP Runtime Study — framework/base, ART, dalvik, frameworks/native | DEX/Dalvik | KEEP |
| `docs/research/dex-runtime-study.md` | DEX Runtime Study — Dalvik semantics across ART, DaliVM, dexterpreter, DroidSaw, WineDroid | DEX/Dalvik | KEEP |
| `docs/runtime/knowledge/SOURCE_REFERENCE_INDEX_UPDATE.md` | SOURCE_REFERENCE_INDEX — Unified campaign update (append-only) | DEX/Dalvik | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign005/EXP-111_baksmali_auth_chain.md` | EXP-111 — Independent baksmali/dexlib2 verification of the SMS auth chain (Campaign 004) | DEX/Dalvik | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign005/EXP-115_opcode_crosscheck.md` | EXP-115 — Opcode census cross-check: androguard vs dexlib2/baksmali (T15) | DEX/Dalvik | KEEP (knowledge core) |
| `docs/runtime/upstream_reference_aput_aosp.md` | Upstream reference — AOSP ART aput semantics (UNIFIED_014 / DEX-APUT-BOUNDS) | DEX/Dalvik | KEEP |
| `docs/runtime/knowledge/campaign008/DOOZ_PATH_008.md` | DOOZ PATH — UNIFIED_008 (charter §6/§7, Target B) | Dooz | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign009/DOOZ_CONFIG_MATCHING_EVIDENCE_009.md` | DOOZ_CONFIG_MATCHING_EVIDENCE_009 — §6 + §10 evidence walkthrough | Dooz | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign010/COMPOSE_DOOD_ANALYSIS_010.md` | COMPOSE_DOOD_ANALYSIS_010 — Dooz progression record (R14/R30) | Dooz | KEEP (knowledge core) |
| `docs/runtime/knowledge/CROSS_WORKSTREAM_TRANSFERS.md` | CROSS-WORKSTREAM TRANSFERS — cross-stream transfer records (§10) | OpenJDK/desugar | KEEP (knowledge core) |
| `docs/upstream/INDEX.md` | UPSTREAM LAW INDEX — MiniAndroid | OpenJDK/desugar | KEEP |
| `docs/runtime/knowledge/PAPARAZZI_STATUS.md` | PAPARAZZI / ROBORAZZI VISUAL ORACLE — STATUS (§23) | Paparazzi | KEEP (knowledge core) |
| `docs/compatibility/RESOURCE_MATRIX.md` | RESOURCE MATRIX — parsed → resolved → consumed → rendered → pixel-verified | Resources/ARSC/AXML | KEEP |
| `docs/research/FIND_REUSE_RES.md` | FIND-REUSE-RES — AOSP resource-subsystem laws transferred to MiniAndroid | Resources/ARSC/AXML | KEEP |
| `docs/research/arsc-resource-study.md` | ARSC / Resource System Study | Resources/ARSC/AXML | KEEP |
| `docs/runtime/knowledge/WS-C3_KNOWLEDGE.md` | WS-C3 KNOWLEDGE — Android Framework / Resources / Streams / Components / Corpus | Resources/ARSC/AXML | KEEP (knowledge core) |
| `docs/runtime/knowledge/ROBOLECTRIC_ORACLE_RESULTS.md` | ROBOLECTRIC ORACLE EXPERIMENT — EXP-095 (§22) | Robolectric | KEEP (knowledge core) |
| `docs/runtime/knowledge/FRIEND_TELEGRAM_KNOWLEDGE.md` | Friend Telegram Knowledge Archive | Telegram | KEEP (knowledge core) |
| `docs/runtime/knowledge/TELEGRAM_SCREEN_INVENTORY.md` | TELEGRAM SCREEN INVENTORY — Source-Backed Element Map | Telegram | KEEP (knowledge core) |
| `docs/runtime/knowledge/TELEGRAM_SOURCE_MAPPING.md` | Telegram APK ↔ Source Mapping | Telegram | KEEP (knowledge core) |
| `docs/research/WINEDROID_DEEP_STUDY.md` | WineDroid Deep Study — REUSE-FIRST synthesis (WINEDROID_DEEP_STUDY.md) | WineDroid | KEEP |
| `docs/research/winedroid-study.md` | WineDroid Study — Source-Level, File-by-File | WineDroid | KEEP |
| `docs/research/apk-toolchain-study.md` | APK Toolchain Study — Apktool, JADX, Bundletool (and the fixtures tooling lesson) | bundletool | KEEP |
| `docs/maintenance/s45_session_record.md` | S45 SESSION RECORD — GAME PLAYABILITY FINAL ATTACK (R-NEW-359/360 landed, R-NEW-361 registered) | game compatibility | KEEP (process) |
| `docs/maintenance/s35_session_record.md` | S35 SESSION RECORD — R-NEW-334 narrowed to the lifecycle-gated visibility law | lifecycle | KEEP (process) |
| `docs/research/font-runtime-study.md` | Font Runtime Study — Typeface resolution, shaping, measurement, rendering | rendering | KEEP |
| `docs/research/graphics-rendering-study.md` | Graphics / Rendering Study — Canvas, Paint, Path, and the software pipeline | rendering | KEEP |
| `docs/runtime/knowledge/FREETYPE_VS_BITMAPFONT.md` | FreeType vs BitmapFont Comparison (§10) | rendering | KEEP (knowledge core) |
| `docs/compatibility/APP_COMPATIBILITY_REGISTRY.md` | MiniAndroid App Compatibility Registry | runtime bugs (root registry) | KEEP |
| `docs/maintenance/s33_session_record.md` | S33 SESSION RECORD — R-NEW-332 closed (F-098 + F-099), R-NEW-333 registered | runtime bugs (root registry) | KEEP (process) |
| `docs/maintenance/s34_session_record.md` | S34 SESSION RECORD — R-NEW-333 root chain fully mapped | runtime bugs (root registry) | KEEP (process) |
| `docs/research/ROOT_DISCOVERY_EVIDENCE.md` | ROOT DISCOVERY EVIDENCE — the F-044 worked example | runtime bugs (root registry) | KEEP |
| `docs/research/ROOT_DISCOVERY_GUIDE.md` | ROOT DISCOVERY GUIDE — how MiniAndroid locates a root candidate | runtime bugs (root registry) | KEEP |
| `docs/research/ROOT_DISCOVERY_INDEX.md` | ROOT DISCOVERY INDEX — MASTER CAMPAIGN 3/M8 (2026-09-10) | runtime bugs (root registry) | KEEP |
| `docs/research/ROOT_IMPACT_MATRIX.md` | ROOT IMPACT MATRIX — MASTER CAMPAIGN 3/M8 (2026-09-10) | runtime bugs (root registry) | KEEP |
| `docs/research/ROOT_LAW_COMPLETENESS_MATRIX.md` | ROOT LAW COMPLETENESS MATRIX (MASTER CAMPAIGN 4) | runtime bugs (root registry) | KEEP |
| `docs/research/ROOT_LAW_GLOBAL_AUDIT.md` | ROOT LAW GLOBAL AUDIT (MASTER-6 → MASTER CAMPAIGN 4 update) | runtime bugs (root registry) | KEEP |
| `docs/research/ROOT_LAW_IMPACT_REPORT.md` | ROOT LAW IMPACT REPORT (MASTER-6 → MASTER CAMPAIGN 4) | runtime bugs (root registry) | KEEP |
| `docs/research/ROOT_LAW_IMPLEMENTATION_ROADMAP.md` | ROOT LAW IMPLEMENTATION ROADMAP (MASTER-6 → MASTER CAMPAIGN 4 → MASTER CAMPAIGN 3/M8) | runtime bugs (root registry) | KEEP |
| `docs/runtime/EXP_RULES.md` | MiniAndroid Golden Debug Protocol | runtime bugs (root registry) | KEEP |
| `docs/runtime/knowledge/campaign008/MINIANDROID_EXTERNAL_KNOWLEDGE_MASTER_008.md` | MINIANDROID EXTERNAL KNOWLEDGE MASTER — UNIFIED_008 | runtime bugs (root registry) | KEEP (knowledge core) |
| `docs/agent-index/REPO_MAP.md` | REPO_MAP — deterministic repository summary (generated; HEAD `bcfd4405`) | runtime general / project infra | GENERATED |
| `docs/build/HELPER_SOURCE_LIST.md` | HELPER_SOURCE_LIST — MiniAndroid Open-Source Source & Tool Intelligence | runtime general / project infra | KEEP |
| `docs/compatibility/ANDROID_BOOTSTRAP_MATRIX.md` | Android Bootstrap Matrix | runtime general / project infra | KEEP |
| `docs/compatibility/APK_LOADING_IMPACT_MATRIX.md` | APK LOADING IMPACT MATRIX — M8 (2026-09-10) | runtime general / project infra | KEEP |
| `docs/compatibility/COMPATIBILITY_CLOSURE_MATRIX.md` | COMPATIBILITY CLOSURE MATRIX — M8 (2026-09-10) | runtime general / project infra | KEEP |
| `docs/compatibility/EXECUTION_MATRIX.md` | docs/compatibility/EXECUTION_MATRIX.md — S22 MASTER MISSION (ROOT CLOSURE + REAL APK EXECUTION) | runtime general / project infra | KEEP |
| `docs/compatibility/MASTER_CURRENT_GAP_MATRIX.md` | MASTER_CURRENT_GAP_MATRIX — UNIFIED_011.3 | runtime general / project infra | KEEP |
| `docs/compatibility/MASTER_RECONCILIATION_APK_EVIDENCE.md` | MASTER RECONCILIATION — real-APK evidence (PHASE 6, 2026-09-03) | runtime general / project infra | KEEP |
| `docs/decisions/README.md` | Architectural Decision Records | runtime general / project infra | KEEP |
| `docs/demos/EVIDENCE.md` | Real APK Execution Proof — Evidence Report (2026-09-04) | runtime general / project infra | KEEP |
| `docs/development/DO_NOT_REINVENT.md` | DO_NOT_REINVENT — the central law, operationalized | runtime general / project infra | KEEP |
| `docs/development/START_HERE.md` | UNIFIED_011_1_CANONICAL_HANDOFF — START HERE | runtime general / project infra | KEEP |
| `docs/development/STUB_DEBT.md` | MiniAndroid STUB_DEBT Ledger | runtime general / project infra | KEEP |
| `docs/forensics/HISTORICAL_BLOAT_REPORT.md` | S51 — Historical Bloat Report (PHASE 9) | runtime general / project infra | KEEP |
| `docs/forensics/HISTORY_PURGE_PLAN.md` | S51 — History Purge Plan (PHASE 9) | runtime general / project infra | KEEP |
| `docs/maintenance/CLOSURE_QUEUE.md` | docs/maintenance/CLOSURE_QUEUE.md — MASTER MISSION: ROOT CLOSURE + REAL APK EXECUTION (S22) | runtime general / project infra | KEEP (process) |
| `docs/maintenance/F_LEDGER_CLOSURE_S35.md` | F-LEDGER CLOSURE — S35 (session 35): every open F-number resolved | runtime general / project infra | KEEP (process) |
| `docs/maintenance/NOT_DONE.md` | NOT_DONE — what remains broken, missing, or unproven (updated 2026-09-03) | runtime general / project infra | KEEP (process) |
| `docs/maintenance/recovery/RECOVERY_README.md` | Recovery forensics snapshot | runtime general / project infra | KEEP (process) |
| `docs/maintenance/repository-structure-migration.md` | Repository Structure Migration (2026-09-12) | runtime general / project infra | KEEP (process) |
| `docs/maintenance/s27_session_record.md` | S27 — MASTER CAMPAIGN 3 continuation — session evidence record | runtime general / project infra | KEEP (process) |
| `docs/maintenance/worklog.md` | MiniAndroid Project Worklog | runtime general / project infra | KEEP (process) |
| `docs/research/AGENT_FINDINGS_VALIDATION.md` | AGENT_FINDINGS_VALIDATION — findings are leads, HEAD is the judge | runtime general / project infra | KEEP |
| `docs/research/AGENT_FINDING_AUDIT.md` | AGENT_FINDING_AUDIT (campaign §4 — master status table) | runtime general / project infra | KEEP |
| `docs/research/CAMPAIGN_EXTERNAL_REFERENCE_AND_EXECUTION_FINAL.md` | CAMPAIGN FINAL — EXTERNAL REFERENCE + EXECUTION (§40/§37) | runtime general / project infra | KEEP |
| `docs/research/COMPATIBILITY_REFERENCE_MATRIX.md` | MiniAndroid Compatibility Reference Matrix | runtime general / project infra | KEEP |
| `docs/research/EXTERNAL_KNOWLEDGE_TRANSFER.md` | EXTERNAL KNOWLEDGE TRANSFER — what we learned and what we did with it (§33) | runtime general / project infra | KEEP |
| `docs/research/FINAL_EXTERNAL_RESEARCH_AUDIT.md` | FINAL EXTERNAL RESEARCH AUDIT | runtime general / project infra | KEEP |
| `docs/research/GITHUB_EVIDENCE_INDEX.md` | GITHUB_EVIDENCE_INDEX — §20/§21 authoritative achievement→evidence map | runtime general / project infra | KEEP |
| `docs/research/GITHUB_RESEARCH_INDEX.md` | GITHUB_RESEARCH_INDEX — §26 permanent institutional memory | runtime general / project infra | KEEP |
| `docs/research/MASTER_EXTERNAL_REFERENCE_MATRIX.md` | MASTER EXTERNAL REFERENCE MATRIX (§31) | runtime general / project infra | KEEP |
| `docs/research/REFERENCE_PROJECT_MATRIX.md` | REFERENCE_PROJECT_MATRIX — canonical reference inventory (§18/§3/§4) | runtime general / project infra | KEEP |
| `docs/research/REUSE_REDUCTION_REPORT.md` | REUSE_REDUCTION_REPORT — §11/§22 measurable reuse-first outcomes | runtime general / project infra | KEEP |
| `docs/research/REUSE_TRANSFER_MATRIX.md` | REUSE_TRANSFER_MATRIX — §37 research→code tracker | runtime general / project infra | KEEP |
| `docs/research/TRANSFER_MATRIX.md` | TRANSFER_MATRIX — research-to-code, this campaign's §18 table | runtime general / project infra | KEEP |
| `docs/research/auxiliary-repo-studies.md` | Auxiliary Repository Studies — Task 5 (source-level, exact-URL law) | runtime general / project infra | KEEP |
| `docs/research/external-gap-analysis.md` | External Gap Analysis — what MiniAndroid still lacks, ranked by evidence | runtime general / project infra | KEEP |
| `docs/research/external-mechanism-matrix.md` | External Mechanism Matrix — provenance-tracked | runtime general / project infra | KEEP |
| `docs/research/external-repositories.md` | External Repositories — Canonical Inventory | runtime general / project infra | KEEP |
| `docs/research/knowledge-transfer-log.md` | Knowledge Transfer Log — external mechanism → MiniAndroid | runtime general / project infra | KEEP |
| `docs/research/layout-study.md` | Layout Study — MeasureSpec propagation and container laws | runtime general / project infra | KEEP |
| `docs/research/source-forensics/MASTER_SOURCE_DIFFERENTIAL_LEDGER.md` | MASTER SOURCE DIFFERENTIAL LEDGER | runtime general / project infra | KEEP |
| `docs/research/source-forensics/SOURCE_ARCHIVE_MATRIX.md` | SOURCE ARCHIVE MATRIX — COMPLETE CROSS-ARCHIVE DIFFERENTIAL AUDIT | runtime general / project infra | KEEP |
| `docs/research/source-forensics/SOURCE_FORENSICS_REPORT.md` | SOURCE FORENSICS REPORT — COMPLETE CROSS-ARCHIVE SOURCE DIFFERENTIAL AUDIT | runtime general / project infra | KEEP |
| `docs/research/source-forensics/SOURCE_KNOWLEDGE_CROSSCHECK.md` | SOURCE KNOWLEDGE CROSSCHECK | runtime general / project infra | KEEP |
| `docs/research/source-forensics/SOURCE_ZIP_HYGIENE_REPORT.md` | SOURCE ZIP HYGIENE REPORT — FINAL CANONICAL DISTRIBUTION ARTIFACT | runtime general / project infra | KEEP |
| `docs/research/source-forensics/evidence/A10_unique_blobs/3aff1e07cc56_MASTER_PROJECT_STATE_011.md` | MASTER_PROJECT_STATE_011 — canonical project state | runtime general / project infra | KEEP |
| `docs/research/source-forensics/evidence/A10_unique_blobs/4d521892ee4e_README.md` | MiniAndroid | runtime general / project infra | KEEP |
| `docs/research/source-forensics/evidence/A10_unique_blobs/9a5d236ffa4f_START_HERE.md` | START_HERE — UNIFIED_011_CANONICAL_HANDOFF package | runtime general / project infra | KEEP |
| `docs/research/source-forensics/evidence/A10_unique_blobs/9f251137ea29_RELEASE_NOTES_UNIFIED_011.md` | RELEASE NOTES — UNIFIED_011_CANONICAL (tag `v0.11-unified-011`) | runtime general / project infra | KEEP |
| `docs/research/source-forensics/evidence/A10_unique_blobs/f16d3c2c2e09_MASTER_CHANGELOG_KNOWLEDGE_011.md` | MASTER_CHANGELOG_KNOWLEDGE_011 — full history & provenance-graded knowledge | runtime general / project infra | KEEP |
| `docs/runtime/AI_AGENT_CONTEXT.md` | MiniAndroid Project - AI Agent Context Document | runtime general / project infra | KEEP |
| `docs/runtime/COLLECTION_RUNTIME_STATUS.md` | EXP-054 — Collection Runtime Status | runtime general / project infra | KEEP |
| `docs/runtime/CURRENT_TRUTH_011_1.md` | CURRENT_TRUTH_011_1 | runtime general / project infra | KEEP |
| `docs/runtime/DEVELOPMENT_WORKFLOW.md` | Development Workflow Guide | runtime general / project infra | KEEP |
| `docs/runtime/FRESH_CLONE_VERIFICATION.md` | Fresh Clone Verification Report | runtime general / project infra | KEEP |
| `docs/runtime/FUTURE_ROADMAP.md` | Future Roadmap: EXP-023 Onward | runtime general / project infra | KEEP |
| `docs/runtime/GITHUB_UPLOAD_PLAN.md` | GitHub Upload Plan | runtime general / project infra | KEEP |
| `docs/runtime/PRE_GITHUB_PUSH_AUDIT.md` | Pre-GitHub Push Integrity Audit | runtime general / project infra | KEEP |
| `docs/runtime/PROJECT_STATE_AUDIT.md` | MiniAndroid Project State Audit | runtime general / project infra | KEEP |
| `docs/runtime/TEST_CORPUS_POLICY.md` | MiniAndroid Test Corpus Policy | runtime general / project infra | KEEP |
| `docs/runtime/architecture-current.md` | MiniAndroid Current Architecture (Source-Based) | runtime general / project infra | KEEP |
| `docs/runtime/architecture.md` | MiniAndroid Runtime v0.1 — Architecture Document | runtime general / project infra | KEEP |
| `docs/runtime/dependency-map.md` | MiniAndroid Runtime — Dependency Map | runtime general / project infra | KEEP |
| `docs/runtime/execution-flow.md` | MiniAndroid Runtime — Execution Flow Document | runtime general / project infra | KEEP |
| `docs/runtime/knowledge/ANDROID_SILENT_FALSE_SUCCESS_MAP.md` | Android Silent False-Success Map | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/CODER2_KNOWLEDGE.md` | Coder 2 Knowledge Archive | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/CODER3_KNOWLEDGE.md` | Coder 3 Knowledge Archive | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/CODER_KNOWLEDGE_INDEX.md` | Coder Knowledge Index | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/CODER_MAIN_KNOWLEDGE.md` | Coder-Main (Primary) Knowledge Archive | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/MINIANDROID_EXTERNAL_RUNTIME_INDEX.md` | MINIANDROID EXTERNAL RUNTIME INDEX — (mirror of WS-C5 index for repo placement) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/MINIANDROID_EXTERNAL_RUNTIME_KNOWLEDGE.md` | MINIANDROID EXTERNAL RUNTIME KNOWLEDGE (WS-C5) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/OA_API_MAP.md` | Open-Source App API Map | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/SOURCE_REFERENCE_INDEX.md` | Source Reference Index | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/UNIFIED_CODER_MASTER_TRANSFER.md` | UNIFIED_CODER_MASTER_TRANSFER | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/WS-C2_EVIDENCE.md` | WS-C2 EVIDENCE — campaign evidence list (per §14) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/WS-C2_KNOWLEDGE.md` | WS-C2 KNOWLEDGE — Graphics / Text / Image / Animation / Audio-Visual | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/WS-C2_PRIMARY_TRANSFER.md` | WS-C2 PRIMARY TRANSFER | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/WS-C3_CORPUS.md` | WS-C3 CORPUS — Corpus status in the Unified campaign | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/WS-C3_PRIMARY_TRANSFER.md` | WS-C3 PRIMARY TRANSFER | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/WS-C4_PRIMARY_TRANSFER.md` | WS-C4 PRIMARY TRANSFER | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/WS-C4_TOOL_MATRIX.md` | WS-C4 TOOL MATRIX — open-source tooling matrix (WS-C4-RESEARCH merged) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/WS-C4_TO_C2_C3.md` | WS-C4 → WS-C2 TRANSFER (tooling findings relevant to graphics/text/animation) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/WS-C5_PRIMARY_TRANSFER.md` | MINIANDROID EXTERNAL RUNTIME INDEX (WS-C5) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign005/TASKS_UNIFIED_005.md` | TASKS_UNIFIED_005.md — MiniAndroid Unified Campaign 005 | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign005/UNIFIED_005_INDEX.md` | UNIFIED_005_INDEX.md | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign006/EXP-117_to_120_runtime_push.md` | EXP-117/118/119/120 — Runtime push evidence (Campaign 004, T31-T43) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign006/TASKS_CAMPAIGN005_MASTER.md` | TASKS_CAMPAIGN005_MASTER.md — CODER 5: Open-Source Reuse + Real APK Validation | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign008/API_U007.md` | API — UNIFIED_007 | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign008/ARCHITECTURE_U007.md` | ARCHITECTURE — UNIFIED_007 runtime | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign008/CODE_REDUCTION_008.md` | CODE REDUCTION — UNIFIED_008 (charter §25) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign008/DO_NOT_REINVENT_008.md` | DO NOT REINVENT — UNIFIED_008 | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign008/GLES_INVESTIGATION_008.md` | GLES INVESTIGATION — UNIFIED_008 (charter §14/§15) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign008/OPEN_SOURCE_AUDIT_008.md` | OPEN SOURCE AUDIT — UNIFIED_008 (methodology + catalog summary, charter §2/§23/§35) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign008/OPEN_SOURCE_REJECTED_008.md` | OPEN SOURCE REJECTED — UNIFIED_008 (with reasons, charter §36/§29) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign008/OPEN_SOURCE_USED_008.md` | OPEN SOURCE USED — UNIFIED_008 (adoption evidence, charter §36) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign008/QUICKSTART_U007.md` | QUICKSTART — 60 seconds to real APK execution | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign008/README_U007.md` | MiniAndroid — UNIFIED_007 FINAL | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign008/REGRESSION_008.md` | REGRESSION — UNIFIED_008 (charter §27) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign008/SELF_VERIFY_008.md` | SELF-VERIFICATION — UNIFIED_008_FINAL.zip (charter §43) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign008/STATUS_U007.md` | STATUS — UNIFIED_007 (auto-generated from evidence) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign009/CODE_REDUCTION_009.md` | CODE_REDUCTION_009 — §29 source-reduction audit | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign009/DO_NOT_REINVENT_009.md` | DO_NOT_REINVENT_009 — standing orders derived from evidence | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign009/GITHUB_MINING_009.md` | GITHUB_MINING_009 — Open-Source Deep Mining Catalog | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign009/OPEN_SOURCE_AUDIT_009.md` | OPEN_SOURCE_AUDIT_009 — Campaign 009 Open-Source Audit | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign009/OPEN_SOURCE_REJECTED_009.md` | OPEN_SOURCE_REJECTED_009 — every rejection carries a reason | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign009/OPEN_SOURCE_USED_009.md` | OPEN_SOURCE_USED_009 — what was actually used, with provenance | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign009/REAL_APK_MATRIX_009.md` | REAL_APK_MATRIX_009 — per-APK independent criteria (§33) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign009/REGRESSION_009.md` | REGRESSION_009 — every adoption re-verified (§35) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign009/UNIFIED_009_INDEX.md` | UNIFIED_009_FINAL — Campaign 009 Index & Scoreboard | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign010/CODE_REDUCTION_010.md` | CODE_REDUCTION_010 — LoC before/after per replacement (R27) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign010/DIFFERENTIAL_TESTING_010.md` | DIFFERENTIAL_TESTING_010 — oracles and three-way comparisons (R22) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign010/DO_NOT_REINVENT_010.md` | DO_NOT_REINVENT_010 — the standing law + ledger updates | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign010/GLES_BACKEND_COMPARISON_010.md` | GLES_BACKEND_COMPARISON_010 — R9 evaluation record | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign010/OPEN_SOURCE_ADOPTIONS_010.md` | OPEN_SOURCE_ADOPTIONS_010 — what was actually adopted, with evidence (§1) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign010/OPEN_SOURCE_REJECTIONS_010.md` | OPEN_SOURCE_REJECTIONS_010 — candidates evaluated and not adopted (evidence-based) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign010/OPEN_SOURCE_REPLACEMENT_AUDIT_010.md` | OPEN_SOURCE_REPLACEMENT_AUDIT_010 — MiniAndroid subsystem census (§2) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign010/REAL_APK_MATRIX_010.md` | REAL_APK_MATRIX_010 — 31 real APKs, honest per-criteria (R23) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/knowledge/campaign010/REGRESSION_010.md` | REGRESSION_010 — after EVERY major adoption (R28/R29/R31) | runtime general / project infra | KEEP (knowledge core) |
| `docs/runtime/runtime-status.md` | MiniAndroid Runtime v0.1 - Runtime Status | runtime general / project infra | KEEP |
| `docs/security/SECURITY_AUDIT.md` | Security Audit — S49 | runtime general / project infra | KEEP |
| `docs/testing/CURRENT_HEAD_BASELINE.md` | CURRENT_HEAD_BASELINE — REUSE-FIRST CAMPAIGN §1 | runtime general / project infra | KEEP |
| `docs/testing/MASTER3_BASELINE_MATRIX.md` | MASTER CAMPAIGN 3 — §1 BASELINE MATRIX (RE-CAPTURE) | runtime general / project infra | KEEP |
| `docs/testing/TEST_MATRIX.md` | TEST_MATRIX — domain status (CAMPAIGN 011 §18) | runtime general / project infra | KEEP |
| `docs/testing/VERIFIED_TESTS.md` | VERIFIED_TESTS — how to rebuild and rerun every protecting test (2026-09-02) | runtime general / project infra | KEEP |
| `docs/tooling/TOOLING_BASELINE.md` | TOOLING BASELINE — PHASE 0 REPORT (brief §45) | runtime general / project infra | KEEP |
| `miniandroid/docs/evidence/APPS_EXECUTION_LEDGER.md` | APPS EXECUTION LEDGER — every app, every claim, every hash | runtime general / project infra | KEEP |

_rows: 172_

## 3. Era trees — directory-level summaries (full lists via `git ls-files <dir>`)

| Tree | Files (.md) | Status | What lives here |
|---|---|---|---|
| `docs/history/` | 63 | HISTORY | archived campaign/session history moved out of the active tree |
| `docs/evidence/` | 111 | EVIDENCE | compact per-issue/per-campaign evidence + screenshot galleries + s52_asc cards + residue record |
| `docs/releases/` | 7 | HISTORY | release notes + manifests |
| `docs/runtime (root era reports)` | 100 | HISTORY (era experiment report) | era experiment/campaign reports |
| `docs/runtime/compatibility` | 1 | HISTORY (era experiment dir) | era experiment/campaign reports |
| `docs/runtime/evidence` | 1 | HISTORY (era experiment dir) | era experiment/campaign reports |
| `docs/runtime/exec-plans` | 2 | HISTORY (era experiment dir) | era experiment/campaign reports |
| `docs/runtime/exp036` | 2 | HISTORY (era experiment dir) | era experiment/campaign reports |
| `docs/runtime/exp042` | 5 | HISTORY (era experiment dir) | era experiment/campaign reports |
| `docs/runtime/exp045` | 2 | HISTORY (era experiment dir) | era experiment/campaign reports |
| `docs/runtime/light_corpus` | 2 | HISTORY (era experiment dir) | era experiment/campaign reports |

Tracked JSON classes: battery/test indexes (`docs/testing/BATTERY_INDEX.json`),
release manifests (`docs/releases/RELEASE_MANIFEST.json`), nav twins
(`docs/INDEX.json`), generated agent index (`docs/agent-index/SYMBOL_INDEX.json`),
per-run result records (`docs/evidence/**.result.json`), golden/expected oracles
(`miniandroid/golden/`), registry (`miniandroid/APK_REGISTRY.json`,
`root_registry.json` at repo root, 349 roots). Raw web-scrape dumps under
`docs/runtime/research/raw/` were removed from the tree in S52 (record:
`docs/evidence/S52_RESIDUE_RECORD.md`); conclusions survive in the research docs.

## 4. Duplicate / merge candidates (merge only after proof; S52 findings)

| Files | Finding | Action |
|---|---|---|
| `docs/evidence/SCREENSHOT_INDEX.md`, `_013.md`, `_S51.md` | era screenshot indexes — all superseded by the canonical achievements file | SUPERSEDED pointer added; content frozen |
| `docs/INDEX.md` + `docs/INDEX.json` | twins by design (human + machine) | KEEP both, linked |
| `docs/evidence/CURRENT_COMPATIBILITY_MATRIX.md` vs `docs/compatibility/MASTER_CURRENT_GAP_MATRIX.md` | two compatibility matrices with overlapping scope | MERGE-CANDIDATE — consolidate into `docs/APPLICATION_MATRIX.md` when the matrix lands |
| `docs/CAMPAIGN_FINAL_REPORT*.md`, `MASTER_CAMPAIGN4_FINAL_REPORT.md`, `docs/evidence/campaign014/MASTER4_FINAL_REPORT.md` | era campaign finals, distinct scopes | KEEP as HISTORY (distinct era boundaries; merging would erase them) |

## 5. Knowledge map — where to read for each pipeline stage

`Android APK` → Manifest → Resources → DEX → Class loading → Interpreter →
Android API → Lifecycle → View → Layout → Input → Rendering → Storage →
Concurrency → Compose

| Stage | Upstream knowledge | MiniAndroid implementation | Tests | App evidence | Blocker | Knowledge files |
|---|---|---|---|---|---|---|
| APK/zip | `docs/runtime/knowledge/` (zip/apk structure) | APK parser + `analyze` | battery G06-G08 | every corpus run | — | `docs/runtime/knowledge/*.md` |
| Manifest | AXML docs (`docs/research/`) | AXML decoder, manifest binding | G-chain fixtures | ASC card: Telegram/chessclock manifests | — | research: axml/manifest files |
| Resources/ARSC | ARSC research | aapt2-linked resources, ARSC/style chain (M3) | M3 battery chain | typography goldens | styles edge cases | `G31_FONT_SOURCE.md`, M3 docs |
| DEX/class loading | `docs/runtime/knowledge/` dex files | dalvik_engine.cpp loader | EXP030/032 chain | all runs | — | dex/dalvik knowledge set |
| Interpreter (opcodes) | bytecode docs | real-dalvik interpreter | semantic battery (long/cmp/conv/switch) + EXP052 reg suite | Dooz18 halt = opcode-level evidence | R-NEW-361 ScatterMap long-law | s38 shift-law fixture docs, `R-NEW-361` card |
| Android API (shadows) | EXP032 AOSP reference map | shadow registry | API law battery | per-app REC-MISS counters | long-tail REC-MISS | `EXP032_AOSP_REFERENCE_MAP.md`, `COLLECTION_RUNTIME_STATUS.md` |
| Lifecycle | EXP03x lifecycle research | ActivityThread law chain | F-0xx laws | all SUCCESS apps | fragment-host family R-NEW-331 | lifecycle knowledge set |
| View/Layout | view shadow knowledge | ViewShadow/inflate | hello_widgets golden | unote R-NEW-368 (touch vs paint geometry) | **R-NEW-368** | S38/S39 records |
| Input | AOSP touch law (View.java 17xxx) | tap/long-press pipeline | tictactoe 9/9 | tictactoe L9; chessclock L7 | IME stack boundary | input law docs |
| Rendering | rendering research | frame pipeline + JPG evidence | pixel goldens | 6 full-render apps | blank Compose class `31ddd4d5` | rendering knowledge set |
| Storage | prefs/db laws | SharedPreferences (R-NEW-367), SQLite file | S52 persistence experiment | chessclock/unote round-trip | state-delta ladder pending | R-NEW-367 record |
| Concurrency | Unsafe/atomicfu contract (S39) | shadow dispatch + CAS | S24-COLL probe | dooz23 DI chain | R-NEW-344 recomposer suspension | S39/S40 records |
| Compose | compose sources (`upstream/s43`) | composition machinery | F-016 honesty | dooz23 pipeline; blank frames | **R-NEW-344** + `31ddd4d5` frame class | `docs/upstream/INDEX.md`, S40-S43 records |
| Telegram init | ASC startup card | — (init frontier) | — | 540 s init, no frame | REC-MISS init chain | `docs/evidence/s52_asc/README.md` |

## 6. Subsystem coverage census (files per subsystem)

| Subsystem | .md files |
|---|---|
| runtime general / project infra | 451 |
| Dooz | 118 |
| runtime bugs (root registry) | 50 |
| DEX/Dalvik | 27 |
| Telegram | 21 |
| rendering | 18 |
| game compatibility | 14 |
| concurrency | 13 |
| Resources/ARSC/AXML | 9 |
| Compose | 7 |
| lifecycle | 4 |
| input | 3 |
| AOSP | 2 |
| WineDroid | 2 |
| OpenJDK/desugar | 2 |
| bundletool | 1 |
| Paparazzi | 1 |
| Robolectric | 1 |
| storage | 1 |

_Generated by `scripts/s52_gen_knowledge_index.py` — do not hand-edit rows;
hand knowledge belongs in the files themselves._
