# ROADMAP_STATUS — Canonical, Reconciled (S60)

> **SINGLE SOURCE OF TRUTH for what is done, what is open, and what is next.**
> Reconciles ALL historical roadmaps against actual committed evidence: nothing
> disappeared because it got old; nothing is checked without evidence.
> Canonical by the S54 documentation law. Supersedes `docs/ROADMAP.md` (S52/S53
> canonical — now a pointer), `docs/runtime/FUTURE_ROADMAP.md`,
> `docs/runtime/EXP037_IMPLEMENTATION_ROADMAP.md`,
> `docs/research/ROOT_LAW_IMPLEMENTATION_ROADMAP.md` (kept as the live tier
> source), and campaign TODO blocks in session records.
>
> Status vocabulary: `DONE / VERIFIED / IMPLEMENTED / TESTED / OBSERVED /
> PARTIAL / BLOCKED / PENDING / SUPERSEDED`. Evidence states per
> `docs/ACHIEVEMENTS.md` §0.

## 1. What already works (evidence-pinned)

| Capability | Status | Evidence |
|---|---|---|
| APK → DEX → lifecycle → View → render pipeline | **VERIFIED** | battery 94/94; §28 helloworld_golden; 6 real-APK GUI successes |
| **HelloWorld complete execution (control target)** | **VERIFIED** | EXT-01 typography 9/9 + EXT-02 interaction 12/12 + `s54_frames/helloworld_ext01_base.jpg` (real text incl. app-computed hash) |
| Real game with input→state→render chain | **VERIFIED** | GM Dice 8/8 clicks → app-rolled dice rendered (L7 + app-specific result); Chess Clock click → active-player switch (80,289 px); battery §29 tictactoe_golden 9/9 + determinism |
| Real corpus APKs rendering recognizable GUI | **VERIFIED** | 6 apps (Chess Clock, GM Dice, MicroTimer, Simple Stopwatch, Heading Calculator, uNote) |
| Screenshot quality gate + canonical gallery | **VERIFIED** | `s54_frames/` 12 JPGs + SHA256SUMS + REJECTED section; S53→S54 byte-identical replay proof |
| Lifecycle/input/persistence dispatch | **VERIFIED** | G06/G07/G08 law goldens; SharedPreferences/SQLite round-trips (R-NEW-367) |
| Regression battery | **VERIFIED** | "BATTERY GATE: ALL PASS (96 stages)" at current HEAD (92 stages when the external EXT fixture is absent — the two EXT run stages collapse; the count law is documented in the battery script) |
| Autonomous gameplay on a real APK (input→state→render→repro) | **OBSERVED [S73]** | AndroidGameSnake: 88 moves / 22 turns / 1 food capture, 3/3 runs byte-identical, trace + GIF — docs/evidence/s73_snake_autoplay/ (see ACHIEVEMENTS §0h) |
| Canonical GitHub execution ledger | **IMPLEMENTED [S73]** | [EXEC] issues #10–#23 (one per tracked app, duplicate-checked) + dated evidence comments |
| Compatibility platform (5 layers: app dossiers / tool profiles / canonical knowledge / execution skill / capability matrix) | **IMPLEMENTED [S74]** | docs/compatibility/ (14 app dossiers + 12 tool profiles + 15 capabilities), docs/knowledge/laws/ (31 records, 20 VERIFIED), docs/execution-skill/SKILL.md, docs/compatibility/CAPABILITY_MATRIX.md |
| Compatibility-graph validator + knowledge-promotion tool | **TESTED [S74]** | tools/validate_compatibility_graph.py (PASS at S74 HEAD: references/statuses/provenance/evidence/registry-drift/index) — caught and forced the F-120 back-registration + stale registry-summary repair; tools/promote_knowledge.py (single-step pipeline, VERIFIED requires test+evidence+source, journal) |
| Operational execution evidence layer (S74 FOLLOW-UP) | **TESTED [S74-FOLLOW-UP]** | 14/14 app dossiers audited; per-app human-reviewed evidence bundles (docs/evidence/s74_ops/) with session checkpoints + SHA256SUMS + sandbox probes; 11 apps HUMAN_VISIBLE, 3 truthful NOT_HUMAN_VISIBLE (dooz/stopwatch/telegram blocker evidence); unote notes.db close/reopen persistence probe; microtimer input->state->render at HEAD; tripeaks lobby newly proven at HEAD; validator extended with §35 gates (PASS); tool/law utilization honest labeling (8 USED / 3 RESEARCHED_ONLY / 1 AVAILABLE_NOT_USED tools; 20 USED_BY_EXECUTION / 8 OBSERVED_ONLY / 2 RESEARCHED_ONLY / 1 SUPERSEDED laws) |
| Master ledger truth closure (ITEM75 47-row audit + truth refresh) | **TESTED [S75]** | docs/audit/ITEM75_CLOSURE.md (19 TESTED / 11 PARTIAL / 17 PENDING, 0 conflicts; root cause of the blanket UNVERIFIED = ledger builder truncated matrix rows at column 2 — fixed); master ledger 375 rows, UNVERIFIED 59 → 4 (only source-not-recoverable rows remain) |
| A7 manifest label/icon ARSC resolve (last P0 "law known, no code") | **TESTED [S75]** | ManifestReader resid capture + resolve_resid_string (PackageParser labelRes/loadLabel law) wired at ResourceRuntime ensure_loaded; f54_manifestlabel 6/6 asserts ([A7] resolution line "F54 LabelProof" + icon resid @0x7f010000 captured, decode honestly not claimed); battery 26/26 rc=0; Level C snake replay byte-identical 90/90 (A7 render-neutral) — docs/foundation/s75/S75_REPORT.md §2 |
| Queued-lead re-verification at HEAD (no unfounded fixes) | **OBSERVED [S75]** | R-NEW-388 record CONFIRMED (f14 RL laws exact at HEAD; TriPeaks splash-block is app-specific — docs/foundation/s75/R-NEW-388_HEAD_REVERIFY.md); dooz F-146/F-147 reproduced + NEW p0=NULL observation at the F-147 site (secondary-to-F-146 reading recorded, not claimed as law); gmdice roll invisible reproduced (listener fires, frames byte-identical); snake game-over@frame-94 reproduced + restart-via-START still NOT observed (honest open re-verified) — docs/evidence/s75/ |

## 2. What was fixed THIS session (root cause → law → proof)

S72-W4 rows above the S61 row for continuity.

| ID | Blocker | Root cause (evidence) | Fix | Proof |
|---|---|---|---|---|
| **F-148 (S72-W4)** | ConstraintLayout anchor family unimplemented — children 0-wide/stacked (snake real APK: SnakePanelView 0×105, buttons sequential at x=0) | layout_constraint* attrs unparsed; no CL measure/layout semantics in the inflater | parse 12 anchors + 2 biases; per-axis topological CL measure branch (MATCH_CONSTRAINT spread, bias, one/no-anchor laws, padding-box parent anchors); layout phase replay (RL contract) | snake_view EXACTLY(1080)×780; biased button pad EXACT (BOTTOM span 799 × 0.5); corpus 10/10 + fixtures 25/25 pixel-SAME |
| **F-149 (S72-W4)** | app dp2px computed 0px → SnakePanelView.onMeasure 0x0 (three stacked silent gaps, §038) | Resources.getDisplayMetrics unimplemented (silent null); DisplayMetrics singleton density=1.0 contradicting the 2.625 device authority; TypedValue.applyDimension DEX bridge missing | getDisplayMetrics answers the device law (2.625/420, scaledDensity, xdpi/ydpi); applyDimension exact AOSP switch over heap fields; singleton aligned | SnakePanelView 1080×780 = 20×15dp×2.625 EXACTLY; buttons 197×118 = 75×45dp; corpus 10/10 pixel-SAME |
| **F-150 (S72-W4)** | Thread game-loop family dead: F084 halt (50001 visits) at GameMainThread.run — VirtualMachineError poisoned onCreate | 4 stacked roots: ThreadShadow no-op swallowed sleep; javac emits the SUBCLASS descriptor for sleep/start (method_ids ground truth) vs literal Thread guards; starts drained only in parks; no yield-resume for sleep-blocked bodies | sleep de-nooped; is_thread_receiver() DEX-chain law (3 sites); frame-boundary start/yield drains (bounded 4/8); wake-time registry (thread→{target,wake}); sleep inside drained bodies records wake without advancing the shared clock | 2 ticks/frame EXACT; direction taps steer cell-by-cell; reverse-guard honored; final snake+food frame ×3 BYTE-IDENTICAL (pixel sha 1a419545419deb3a); corpus 10/10 pixel-SAME |

S61 rows above the S60 row for continuity.

| ID | Blocker | Root cause (evidence) | Fix | Proof |
|---|---|---|---|---|
| **F-107 a/b/b2/c/c2/d (S61)** | R-NEW-381 supporting fix: the dooz v23 composition could not complete inside ANY practical budget — measured evidence-machinery overhead dominating the interpreter (gprof + rdtsc phase timers, 60-90s dooz v23 runs) | MEASURED facts: (1) function-local `static` containers of std::string in the hot path cost thread-safe-init guards + `__cxa_atexit` cleanup-thunk churn — `__tcf_0` entered **739M times ≈ 50% of wall** plus 464M std::function `_M_manager` calls; (2) per-instruction InstructionTrace (Clock::now ×2 + operand strings) with an O(n) `erase(begin)` ring (the engine's own EXP-045 note: top-2 cost) — `trace_cap` defaulted ON at 2000; (3) the ApiCallTrace cap erased one element from the FRONT of a 5000-element vector per push after saturation (7230 erases ≈ 0.9 s); (4) `is_subclass_of`'s interface-closure `collect()` did a LINEAR SCAN of every `dex_report_->classes` entry (up to 3052 ClassInfo records) per chain step inside the is_a classifier (millions of queries); (5) `ClassInfo::all_methods()/get_method()` returned BY VALUE — the native-method check copied the whole method table on EVERY `try_recursive_invoke` (773k MethodInfo copies); (6) the overload search copied the class's method table (~40 KB) per invoke | **F-107a**: hot-path statics → trivially-destructible `const char*` tables (zero guard, zero thunk; framework_views, builtin_exc_parent, content_measure ×2, kLocaleConsts, kOrdinals(KvInt), svc maps, kSystemProps, kCharsetAliases, view_parents, normal_permissions, service maps). **F-107b**: `batched_cap_push` — bounded-lag FIFO (cap+BATCH then one range-erase; identical order semantics, 1/64 the memmove). **F-107b2**: per-instruction traces default OFF (`trace_cap=0`), opt-in `MINIANDROID_TRACE_CAP` (API traces stay on — primary evidence); ExecutionConfig plumb. **F-107c**: interface closure via the F-103 `class_to_interfaces_` index (O(log n)) instead of the linear scan. **F-107c2**: `for_each_method/method_count/find_method` non-copying accessors; native check + `class_chain_defines_method` iterate in place. **F-107d**: overload selection iterates direct/virtual tables via stable pointers (dex_report_->classes never mutates after load — verified zero mutation sites); F-023 exact-descriptor + EXP-080 lambda-name laws unchanged | `__tcf_0` GONE from the profile (post-fix 60s run: 0 entries); goldens PASS; battery ALL PASS 96 (after the test-oracle opt-in fix: the three semantic harnesses read `instruction_traces` for HALT_RETURN and now set `engine.config_.trace_cap = 2000` explicitly — the runtime default stays OFF per the law). Phase-timer evidence retained (`MINIANDROID_PERF_PHASES=1` prints `[PERF-PHASE]` + `[PERF-OPS]` opcode histogram at exit). Honest note: the composition still exceeds practical budgets — the remaining cost is 627 cold `<clinit>` class-init chains + the invoke tree (real interpreted work; AOSP EnsureInitialized law), visible per-run via the phase timers |
| **F-108 (S61)** | R-NEW-381 draw-path face: the render walk NEVER dispatched the Compose owner under R8 minification — dooz v23's AndroidComposeView is `Lt4;` and ComposeView is `Lho;` (DEX ground truth `scripts/s61_r381_dex_truth.py`: **0** `Landroidx/compose/` class names survive R8; 21 androidx names kept only for Parcelizer/serialization) | The UC009 expansion + F-099 owner gates keyed the compose identity on the literal `Landroidx/compose/` prefix — wiped by R8; with the degenerate measure (0x105, budget-casualty) the size gate also failed, so `dispatch_custom_view_draw` never ran → white frame | **F-108 R8-rename identity law**: a non-framework class whose ancestry OVERRIDES `dispatchDraw` carries the compose draw-dispatch contract (F-099's own rationale, now the gate). UC009 expansion + the owner gate + a children-empty contract branch all key on `chain_overrides_method(class, "dispatchDraw")` — the DEX hierarchy survives renaming, package names do not. No app names hardcoded | Deep 560s run (run/s61_r381_deep): `[UC009-DRAW] dispatchDraw-contract view expanded to parent rect 1080x1920`; `[C013-ONDRAW] view=1359 class=Lt4; dispatched=YES` (the interpreted dispatchDraw of the R8-renamed AndroidComposeView EXECUTED — 0 canvas ops because the composition has not produced LayoutNodes yet); framebuffer **197 non-white px (was 0)**. Evidence: docs/evidence/s61_r381/ |

S60 rows below the S61 row for continuity.

| ID | Blocker | Root cause (evidence) | Fix | Proof |
|---|---|---|---|---|
| **F-106 (S60)** | R-NEW-380 dooz ViewModelProvider create chain: `RuntimeException "Cannot create an instance of "` at Leo;.n pc=53 depth=81 (the throwing factory fallback) — later faces after each step: IAE "Registered key is empty or blank" (Ldf1;.a, depth 21) | THREE generic gaps, all the F-086 family (missing handler → typed-zero → wrong branch). (1) The legacy getDeclaredConstructor record lost the referent identity (keyed "Ljava/lang/Class;" — the F-103 token's RUNTIME class) and Constructor.getModifiers()/Modifier.isPublic(I) had NO handlers → typed-zero 0 → the NewInstanceFactory `if (!isPublic) throw` branch ALWAYS taken; the message rendered EMPTY (no Class.toString law). DEX truth: scripts/s60_r380_forensic.py (Leo;.n shape); upstream tag 1.0.23: GameViewModel is @HiltViewModel with ONE ctor <init>(SettingsRepository), NO no-arg ctor. (2) Collections.unmodifiableMap missing → the Hilt ViewModelStore-key binding (Lls;.a() → unmodifiableMap({hb0,bm1}) → new Lwl0;(null)) carried a NULL map → Lwl0;.containsKey(hb0) FALSE (guard TRUE per INSTANCEOF-DIAG) → the provider fell to the DEFAULT chain instead of the app Hilt factory. (3) Long.toString(J,I) missing → the rememberSaveable key Long.toString(compositeKeyHash,36) = "" → registerProvider("") IAE | **F-106 law family (all generic)**: (a) Class.getDeclaredConstructor/getConstructor full upstream contract — referent via __referent_desc, exact param-descriptor selection from the (possibly null) Class[] arg, getConstructor=public-only, no match → NoSuchMethodException (throw_deferred; the caller catch block is the designed path), match → record carries class_desc=REFERENT + __reflect_mods + __reflect_params; Constructor.getModifiers/getParameterTypes; the Modifier static bit family; Class.toString() token law ("class "/"interface " + getName()) in the Class-token section AND the StringBuilder stringify_arg law. (b) Collections.unmodifiableMap/Set/Collection — the view delegates every read to the backing container (unmodifiableList precedent). (c) Long.toString(J) / (J,I) — signed 64-bit radix 2..36, MIN_VALUE-safe, out-of-range → IAE. Harness: --max-seconds wall-clock soft budget (graceful evidence stop); EXP093-APUT + parser dumps env-gated (F-074 hygiene law) | POST-FIX dooz v23 (run/s60_r380_post7, --max-seconds 480): ZERO exceptions before the budget stop; the create chain resolves through the app's OWN Hilt factory (Lk2;.b case-1 SavedStateHandle machinery; Lqs;/Lxd0; attach OK obj#5385); the GameViewModel constructs (Lq32;.c + the game-state class inits from the ctor body); the healthy frame loop runs (onStart/onResume dispatched). Regressions: semantic 32/32 (six f106 records incl. the discriminating full-chain + NSM fixtures); dooz v18 healthy (0 errors, doFrame loop alive); BATTERY GATE ALL PASS 96. Evidence: docs/evidence/s60_r380/ |
| **F-105 (S59)** | R-NEW-379 dooz ViewTreeLifecycleOwner ISE "ViewTreeLifecycleOwner not found from Lho;@1074" (Log0;.c) — ×4, APP BOUNDARY unwind at MainActivity.onCreate invoke_pc=317; the themed window paints before death | (D1) The lifecycle 2.8 walk `Lxd1;.g` loops getTag(view, 2131230840=R.id.view_tree_lifecycle_owner, aapt2-verified) → getParent → `instance-of parent, Landroid/view/View;`. ViewShadow node 20 is the F-023 ACTIVITY-AS-VIEW node (its id IS the activity heap id BY DESIGN); heap#20 is the MainActivity, so the F-103 heap-authority classified the VIEW reference as the ACTIVITY → `parent as? View` FALSE → the walk dead-ended at hop 1. (D2) NOBODY ever wrote the owner tag: DEX census (scripts/s59_setfind.py) — ZERO setTag sites for key 2131230840; the install is androidx ComponentActivity library machinery, absent from the APK | Three generic laws: **(a)** `reconcile_class_decl()` shared by instance-of + check-cast — generic declaration → heap wins (F-103 preserved); consistent pair → the MORE SPECIFIC wins; CONTRADICTION → the creation-site declaration wins (re-homing onto proxies was prototyped and REJECTED — the proxy id breaks the next shadow hop, which keys by the shadow node id). **(b)** ActivityShadow setContentView(View) installs the ACTIVITY object (implements LifecycleOwner in the app DEX: Ljm; implements Lvo0;) under the app's OWN view_tree_lifecycle_owner id (name-resolved via arsc find_id — no hardcoded id) on the activity-as-view node BEFORE the attach wave. **(c)** instance-of classifies CLASS_REF values (const-class tokens, F-069/F-103) by the token's heap record — the token's runtime class IS java.lang.Class | Walk success: getTag(1074, key) miss → parent 20 → getTag(20, key) **hit=1** → owner returned; the app's own dialog machinery (Le81;.<init>) propagated it onto the decor (setTag view=308 key=2131230840 obj=20) — the androidx contract cascade runs end-to-end in the app's own DEX. ISE count 0 (was ×4); execution advanced from depth 8 to depth 81. Regressions f105_instanceof_classtoken_is_class + f105_instanceof_classtoken_not_referent (semantic battery 26/26); corpus determinism chessclock ecc001fd8e33519a / notes cf521b168a9b4ed2 / unote 7b30d52201bb22ac — all == the S57/S58 records. Evidence: docs/evidence/s59_r379/ |
| **R-NEW-380 discovery (S59)** | The dooz frontier PAST F-105: ViewModelProvider create chain falls to the throwing factory fallback — `RuntimeException "Cannot create an instance of "` (class-name portion EMPTY) caller=Leo;.n pc=53 depth=81; chain Lyd0;.b → Ltf1;.b → Lt32;.b → Lt32;.d → Leo;.n while constructing the app GameViewModel | The Lwl0;.containsKey Class-key guard now PASSES (F-105c) and the create chain proceeds to factory selection; the create path itself does not complete — the Class.toString/arg surface for CLASS_REF values renders an empty name in the message, and the getDeclaredConstructor → Constructor.newInstance → real <init> path for the app's GameViewModel does not finish ([M3-REFLECT] surface exists but this chain does not reach it) | Registered as R-NEW-380 (OBSERVED-FAIL, P1) — the honest pinned successor of R-NEW-379. NEXT: trace Leo;.n's exact failure input; Class.toString/getName for CLASS_REF args; Constructor.newInstance → try_recursive_invoke on GameViewModel.<init> | miniandroid/run/s59_f105_post2/ (key lines hashed in docs/evidence/s59_r379/post2_keylines.log) |

S58 rows below the S59 row for continuity.

| ID | Blocker | Root cause (evidence) | Fix | Proof |
|---|---|---|---|---|
| **F-102 (S58)** | R-NEW-376 dooz ctor-climb: Compose init ctor chains hit the 2048-frame cap — v23 `Lgz1;.<init>` ×3 + `Lbp1;.<init>` ×1, v18 `Lj/j0;` ×7 + `Lt0/t;`/`LE0/c;` ×2, caller==callee, same receiver | The 3rc invoke path (invoke-*/range) DROPPED the call-site method PROTO at the try_recursive_invoke boundary (default "") → the F-023 exact-descriptor overload law could not fire → the arity heuristic (prefer LARGEST bytecode body) re-selected the CALLING ctor overload itself → same-receiver self-recursion. DEX ground truth (androguard, scripts/s58_gz1_forensic.py): Kotlin default-args ladders — overload1(mask+I)→overload2, argc identical, descriptors distinct, NO self-call in valid DEX | Range-invoke dispatch passes the resolved proto (`range_proto` hoisted + passed on both attempts); when the proto misses, the heuristic path is unchanged | RECURSION-LIMIT count **0** on v18 AND v23 (was 4 on v23); v18 rc=0 at 310k+ instructions with the Choreographer doFrame loop alive (Compose composing); regression `f102_range_ctor_overload_exact_dispatch` (discriminating: pre-fix picks the larger (I)V overload → f==0; post-fix exact-descriptor → f==127). Evidence: docs/evidence/s58_r376/ |
| **F-103 (S58)** | R-NEW-378 cascade past R-NEW-376: compose rememberSaveable IAE "Can't put value with type null into saved state" (Lje;.<init> ACCEPTABLE_CLASSES loop) + IAE "Key must be a class" (Lwl0;.containsKey instance-of) → APP BOUNDARY unwind at MainActivity.onCreate | (1) `Class.isInstance/isAssignableFrom` had NO handler → STUBBED typed-zero 0 for all 29 elements; (2) Class tokens minted from a private counter collided with real heap ids → §19 runtime-class dispatch sent Class-token receivers to UNRELATED objects; (3) instance-of trusted the register's cached class_desc unless EMPTY — the CollectionShadow round-trip degraded the token tag to "Ljava/lang/Object;" | Class type-question laws over class_to_superclass_/class_to_interfaces_; HEAP-BACKED Class tokens (const-class allocates a real Ljava/lang/Class; object with `__referent_desc`; F-069 identity preserved); instance-of runtime-type authority law (heap class wins over the register tag) | Both IAE faces = 0 post-fix; regressions f103_isInstance_string_exact / f103_isAssignableFrom_subclass / f103_instanceof_heap_subclass; same failure family as F-086 (missing handler → typed-zero → wrong branch). Evidence: docs/evidence/s58_r376/ |
| **F-104 (S58)** | F-085 Notes content path: the app's real read chain died silently (file ABSENT → stream EOF → empty model → empty markdown body) | io/state surface gaps: no FileInputStream sandbox reads (assets only), no Uri.fromFile/getPath/getLastPathSegment, no ContentResolver.openInputStream, no AsyncTask.execute dispatch, no EnumSet.of, no java.util.regex Pattern/Matcher (appendTail destroyed the text in mediaCheck), requestPermissions auto-grant never dispatched the callback | Law family: FileInputStream/FileReader sandbox ctor + "file:" stream keys (4 MiB bound); Uri file-scheme family; ContentResolver.openInputStream; AsyncTask.execute (doInBackground+onPostExecute, ancestor-walk recognized); EnumSet.of; regex Pattern.compile/Matcher.find/matches/group/appendReplacement/appendTail (std::regex); onRequestPermissionsResult dispatch; BufferedInputStream joins EXP-071 propagation; [EXP093-FNA] trace env-gated (F-074 hygiene) | Notes real read chain PROVEN live: seeded sandbox doc → app defaultFile/readNote/ReadTask → openInputStream present=1 → readLine ×10 REAL lines → setText sb_value extraction (230 chars verified) → markdownCheck appendTail (230 chars preserved). REMAINING: commonmark parse→render yields an empty body (F-085 open at that face). Battery 96/96 at this HEAD |
| **R-NEW-352 closure (S58)** | microtimer Room initDb 50k forName retry loop starving the run budget (the R-NEW-350 default-OFF reason) | STALE BLOCKER: the S43 A/B pre-dated R-NEW-355 (S44) — the retry loop was the missing pc-advance contract, already root-caused+fixed | Re-proved A/B at the fixed HEAD: microtimer law-ON vs law-OFF PIXEL-IDENTICAL (1,041,437 non-white both; rc=0; HALT-LOOP 0; 2 forName resolutions); the forName law is DEFAULT-ON (MINIANDROID_R350_LAW=0 opt-out) | Corpus pixel-identical to S57 records: chessclock 2,040,736 nb / notes 2,073,600 nb / unote 236,520 nb; 3-run determinism (dooz v23 ef47a2d3cdc6929e ×3) |

S55/S56/S57 rows retained below for continuity.

| ID | Blocker | Root cause (evidence) | Fix | Proof |
|---|---|---|---|---|
| **F-086 (S57)** | dooz v23 (R-NEW-344): ScatterMap full-table probe spin — the second grow computed newCapacity=15 instead of nextCapacity(15)=31 and re-filled the same arrays → zero EMPTY metadata → HALT-LOOP → blank first frame | `java.lang.Long.compare(JJ)I` / `compareUnsigned` had NO bridge handler → STUBBED typed-zero exit returned 0 → the R8-compiled growth decision `if-gtz Long.compare(size*32 ^ MIN, capacity*25 ^ MIN)` fell through to the cleanup-instead-of-resize branch. The cap-7 grow never touches the compare (capacity≤8 branches straight to resize), which is why only the SECOND grow failed | 64-bit compare family (compare signed -1/0/+1, compareUnsigned) in the F-055 Long block (OpenJDK law); regression group in semantic_long_cmp_conv_test (6 checks incl. the bit-exact dooz23 idiom) | Capacity field trace on obj#2658: 7 → 15 → 31; HALT-LOOP 0; F084 fires 0; aput-oob gone; battery ALL PASS; post-fix run advances into the R-NEW-376 ctor-climb (now observed on v18 AND v23 — alias absorbed into R-NEW-376). Evidence: docs/evidence/s57_dooz23/ |
| **F-085 (S56)** | WebView-family apps: getSettings/setWebViewClient/loadUrl/loadData were REC-MISS silent no-ops → content face blank (Notes read face) | No WebView content model existed — the markdown/WebView pipeline died at its first call | Generic model (app-agnostic): ViewShadow dispatches the WebView family; WebSettingsShadow = symmetric set/get property bag; load family stores the document and the render law extracts visible text via a generic HTML→text pass (no markdown special-casing) into the node text so the standard pipeline paints it | Notes v139 getSettings → settings object identity memoized ([F085-WV] logs); battery ALL PASS 96/96; shadow-count invariant updated 19→20/22 |
| **F-084 (S56)** | Halted callee (loop-detector) fed a STALE last_invoke_return_ to the caller's move-result → garbage slot index −733270216 → AIOOBE → APP BOUNDARY death (dooz v23) | The invoke boundary blanket-cleared halted_ without discriminating the abnormal-halt signature (halted_ && !halted_on_return_) from a normal return (which also sets halted_) | HALT-RETURN containment law: the halt escalates to the caller as a deferred VirtualMachineError (F084-HALT-RETURN); no return value is fabricated | Battery ALL PASS 96/96 (first attempt without the discriminator broke stages 59-63 and was fixed pre-commit); dooz v23 face changed from garbage-index AIOOBE to honest halt propagation; docs/evidence/s56_dooz23/ |
| **F-082 (S55)** | Notes v139 read↔edit face swap was a silent no-op (S53 "RENDER_ONLY") | `ViewSwitcher.setDisplayedChild` (the whole ViewAnimator family) was REC-MISS — no displayed-child law in ViewShadow. S55 tree forensics REFUTED the S53 "ListView item paint" hypothesis: v139 has NO ListView | AOSP ViewAnimator law on the ViewShadow node model: setDisplayedChild/getDisplayedChild/showNext/showPrevious (exact AOSP clamp `which≥count→count-1; <0→0`, showOnly visibility walk, requestLayout flag) | law test 18/18 (battery "F-082 ViewAnimator law"); Notes FAB click → face swap **2,057,718 px (99.23%)**, probed=3 changed=1 (was 0/3); frames byte-identical across runs (s55_notes_v2/SHA256SUMS) |
| **F-083 (S55)** | Dooz v18 R-NEW-361: ScatterMap probe spin (HALT-LOOP → aput-oob) | DOWNSTREAM of a depth-cap drop: 56th `Ln/a;.r` (LongArray-fill helper) entered at depth=80 == MAX_RECURSION_DEPTH → silently dropped → metadata stayed heap-zero → sentinel write made ghost bytes `0xff007f6600000000` (zero EMPTY) → probe never terminates. EXP-053: ~80KB C++ stack/DEX frame → 80-frame cap on the 8MB stack | (1) cmd_run executes on a dedicated 1GB-virtual-stack pthread (ART contract: recursion bounded by thread stack); (2) MAX_RECURSION_DEPTH 80 → 2048 (~164MB worst case); (3) limit-drop is ALWAYS loud (`[RECURSION-LIMIT]` stderr); (4) hygiene: F-074 always-on trace (heap lookup per inherited call, ~1.6K instr/s throttle) now env-gated `MINIANDROID_F074_TRACE` | dispatch trace: 55/56 r calls OK, failing call at depth=80; [R361-STORE] ghost vs healthy metadata words; post-fix: NO HALT-LOOP/aput-oob, metadata `0xff80808080808080`, MainActivity.onStart/onResume dispatched (first time); key traces docs/evidence/s55_dooz/ (SHA256SUMS) |
| **F-080 (S54)** | ChessClock "2-color dark blank" | `Resources.getColor(I, Theme)` two-arg overload: shadow read a fixed arg slot and resolved the NULL THEME (int 0) as the resid → every lookup black | resid = first INT-typed arg (robust under receiver-included/excluded conventions; AOSP law: references can never be the resid) | `[RES] resid=0x7f050005 → 0xff499ebd`; frame 99.3% nb/2 colors → 187 colors |
| **F-081 (S54)** | ChessClock clock text = "null" | M3-19 active-cycle key was name-only: legal `formatTime(J)` overload delegation inside active `formatTime(J Z)` falsely matched as re-entry → stubbed null | include the method descriptor in the active-invoke key (JVM identity = name+descriptor) | 0 cycle stubs; `setText "10:00"` ×2; real clock face rendered |
| (infra S54) | battery 54-fixture collapse | disk 100% full + un-bootstrapped aapt2/ECJ/D8 toolchain on this machine | residue freed (7 GB, manifest recorded); `scripts/build/bootstrap_toolchain.sh` re-run; EXT fixture re-fetched SHA-verified | battery 92→94 stages ALL PASS |

## 3. Active frontier (P0 first, attack order)

S65 state (open-source APK spotlight 4 — breadth first continues): **3 NEW
SOURCE-FIRST APPS EXECUTED** — FishRings v1.23 (VelbazhdSoftwareLLC/
FishRingsForAndroid @dc3807e, APK 14d7dd80) **S10 PROVEN**: launch →
F-115 Timer splash → GameActivity → 3× tap → REAL handlers GameActivity$5/$6
→ rings.ccwa/cwa state → changed frames 2,072,211 → 483,395 → 478,169 →
7,347 px, det ×3 byte-identical. TriPeaks v1.2.1 (VelbazhdSoftwareLLC/
TriPeaksSolitaireForAndroid @62f3609, APK 52272ae6) **S7**: full chain
splash→lobby→New Game→GameActivity; 52 card taps reached the REAL
GameActivity$1 handler post-**F-118/R-NEW-385** (activity-constructor law:
AOSP Instrumentation.java:1448 newActivity → the declared no-arg <init>()
MUST run before onCreate — the G08 path skipped it, so field-initialized
listeners were typed-zero; 3 consumers day one). OPMT v0.1.2 (20Nick/OPMT
@3240c4cf, APK 4f91e380) **S6**: real-strings menu → real lambda →
GameActivity onCreate; app-own nextInt(0) stopper. **F-119/R-NEW-386**:
Integer.TYPE JVM-injected Class constant (OpenJDK Integer.java:106) +
Array.newInstance primitive descriptors ("[I"-style, JLS/DEX) — FishRings
rc=1 PARTIAL → rc=0 S10; TicTacToe R-NEW-358 golden PASS on the changed
path. Battery 92/94 + EXT-01/02 environmental — ZERO regressions. Survey
breadth: F-Droid 45-keyword scan → 120 shortlist → parallel raw-gradle
signature probes (flutter/libgdx/kivy excluded by evidence) → 3 picks
cloned pinned; 8 deferred-by-facts. NEW OPEN FAMILY: **OBJECT-IDENTITY**
(field/array-element object-ref churn — cardsViews[] comparisons fail,
listener field 38→273) — the NEXT highest-leverage target (blocks
TriPeaks S8 + OPMT S7+; field-initialized listeners are a very common app
pattern). S64 commit carried PENDING-PUSH into this session (no credential);
the S65 commit carries both. Evidence: docs/evidence/s65_spotlight/
S65_REPORT.md.

S63 state (open-source APK spotlight 2 — breadth first continues): **FIRST
SOURCE-FIRST L6 (S10)** — gmdice v12 (ge0rg/gamemasterdice @6353926f,
APK ee9f7396) built aapt2/ECJ/D8 → executed → UI → render (1,744,539 px)
→ 5/5 clicks → real GameMasterDice.onClick → StandardDiceSet.roll →
SecureRandom.nextInt → dice 6/5/3/2 → setText → frame SHA 5312266e →
fa1d8612 with a 1,584-px diff confined to the rollresult band; 3-run
deterministic ×3. Enabler: **F-113 / R-NEW-382** (SecureRandom IS-A Random
bridge law; OpenJDK SecureRandom.java:157/:828; bridge receives the STATIC
receiver class) — battery ALL PASS (94 executed incl. goldens + corpus) on
the fixed binary. Second new app: siggen v1.76 (billthefarmer/sig-gen,
APK c83d21c6) S7 — FQCN-tag custom views inflated, 47,809 px == S61
prebuilt count (cross-validation), 5/5 clicks → Main.onClick →
audio.waveform mutation (audio-path state, honest no pixel face; custom
view measure 0x0 = frontier). Tool law: zoekt under-report ROOT-CAUSED
(default trigram cap excludes 1.2MB files; raised cap = complete results);
csearch per-file limit reproduced 3rd time. Blockinger surveyed and
DEFERRED (support-v4 FragmentActivity + SurfaceView). Evidence:
docs/evidence/s63_spotlight/S63_REPORT.md.

S62+ state (open-source APK spotlight mission — breadth first): **2 NEW
open-source apps built FROM SOURCE and executed** — anuto (L5 + real
onTouch consumed=true) and OpenSudoku (L5 + 3/3 real click dispatch).
F-110 lever IMPLEMENTED (result-snapshot deferral = measured 57.8x
instruction-rate A/B) + 5 companion laws (F-110b/c/d/e, F-111, F-112) —
all with first-hit evidence and battery 96/96 + goldens + G06-G08
determinism ALL PASS after the changes (docs/evidence/s62plus_spotlight/
S62PLUS_REPORT.md). Games corpus first L6: bouncy (input -> callback ->
state transition -> render change, frame SHA pair 4219c5116ea2 /
52e4ddacc8ac). R-NEW-331 gained 3 game consumers (minesweeper / memory /
2048 all die at FragmentManager.ensureExecReady ISE) + the first-engine
precision: the real androidx chain runs and returns OK, but the
FragmentController.attachHost leg never dispatches.

1. **R-NEW-381 — Dooz first-frame content / composition volume (P1, pinned
   S60; S61 face refined)** (OBSERVED-FAIL). The Compose draw path is now
   WIRED: F-108 identifies the R8-renamed owner by the dispatchDraw-override
   contract (Lt4; expanded to 1080x1920) and the interpreted dispatchDraw
   EXECUTED (C013-ONDRAW dispatched=YES) — 0 canvas ops because the
   composition has not produced LayoutNodes yet. MEASURED (S61 phase timers):
   the composition volume = 627 cold `<clinit>` class-init chains + ~23K
   invokes + ~700K instructions (560s run) — real interpreted work, not a
   semantic bug. NEXT: (a) composition completion — longer evidence budget
   or the cold-init/invoke throughput frontier; (b) when LayoutNodes exist,
   verify dispatchDraw → CanvasShadow ops → pixels. *R-NEW-380 must NOT be
   reopened — the creation chain is closed.*
2. **F-085 content probe — chain live, commonmark face remains** (P1).
   The real read chain is PROVEN live end-to-end through the app's own
   code (seeded doc → defaultFile/readNote/ReadTask → openInputStream →
   readLine ×10 real lines → setText 230 chars → markdownCheck appendTail
   230 chars). REMAINING: the commonmark Parser.parse → HtmlRenderer.render
   DEX chain yields an empty body (loadData bytes=251, text_chars=0).
3. **uNote NoteEdition ladder** (P2) — continues from the S56-proven
   L6 input→navigation (PreferenceManager/getApplicationContext surface).
4. **Persistence ladder L10** (P2) for the interactive apps — ChessClock
   first (start clock → close → reopen → state kept).
5. **Telegram init chain** (P2). Ranked: REC-MISS static-init surface →
   SafeIterableMap iterator law → NativeLoader boundary decision.

## 4. BLOCKED (external dependency — do not spend runtime sessions)

| Item | Blocker | Evidence |
|---|---|---|
| WhatsApp | no legitimate APK (0-byte placeholder proven) | ledger §3.3 |
| TicTacToe Classic re-verification | APK lost with legacy cache; F-Droid `com.palahsu.ttt` NOT_FOUND (checked S54) | ledger §3.3; historical S37/S44 records stand |

## 5. Reconciliation of historical roadmaps (unchanged from S52 unless noted)

- FUTURE_ROADMAP (EXP-023 era): all rows DONE/SUPERSEDED as recorded in
  S52; nothing re-opened.
- EXP037 phases: unchanged (B SQLite PARTIAL, C Execution PARTIAL).
- ROOT_LAW tier ladder: P0 landed set now includes **F-080/F-081 (S54)**;
  F-046/F-047/F-048/F-049 items 15-18/20 unchanged; regression-gate law
  VERIFIED with the 92/94 count law documented.
- Campaign worklist S51–S54: S54 rows = canonical doc rename
  (ACHIEVEMENTS/ROADMAP_STATUS), F-080/F-081, gate refinement (DARK-CONTENT),
  divergent-lineage residue classification (campaign reports referencing
  foreign HEADs quarantined as unverified), gallery s54_frames (12 JPGs),
  toolchain bootstrap re-proven, EXT fixture re-fetched SHA-verified.

## 6. Direct answers (S54 §12, S60 refresh)

**What is the biggest runtime blocker?** The dooz first-frame content:
**R-NEW-381** — the ENTIRE creation chain is now closed (R-NEW-344 F-086,
R-NEW-376 F-102, R-NEW-378 F-103, R-NEW-379 F-105, R-NEW-380 F-106 — all
ROOT-CAUSED-FIXED with regression protection); the composition runs end-to-end
with zero exceptions and the gap is INSIDE the Compose draw path (the UI
content does not reach pixels yet).

**What prevents complete HelloWorld?** Nothing — HelloWorldSelfAware is
visually proven end-to-end (L7 via EXT-01/02) at the current HEAD.

**What prevents a playable game?** Nothing for the proven set — GM Dice (real
F-Droid game) and Chess Clock both demonstrate launch→input→state→rendered
change at this HEAD, and tictactoe_golden proves 9-tap win-state play.

**What prevents Dooz?** R-NEW-381 (the Compose draw path — first-frame
content; the pinned frontier). The ENTIRE creation chain is closed:
R-NEW-380 (ViewModelProvider/Hilt creation) is ROOT-CAUSED-FIXED via
F-106 — the app's own Hilt factory resolves GameViewModel and the instance
constructs with zero exceptions; R-NEW-379 (F-105), R-NEW-376 (F-102),
R-NEW-378 (F-103), R-NEW-344 (F-086) all closed earlier.

**What prevents Notes content rendering?** The WebView content model is
SHIPPED (F-085) and the real read chain is now PROVEN live through the
app's own code (F-104: file→stream→reader→model, 230 chars verified into
the EditText and through markdownCheck). The remaining gap is INSIDE the
commonmark Parser.parse → HtmlRenderer.render DEX chain (empty body at
loadData). The app's state machine itself is FIXED (F-082). uNote's
main-menu input chain is PROVEN at S56 (R-NEW-368 premise refuted).

**What prevents Telegram?** Init-chain depth (REC-MISS surface, SafeIterableMap
stub, NativeLoader boundary) — no frame within the 540 s budget. Note: F-083's
deep-stack thread directly attacks the depth side of this frontier too.

**What prevents general APK compatibility?** The long tail of framework REC-MISS
surface plus the Compose P0s; every fixed law transfers (F-080/F-081/F-082/
F-083/F-084/F-085/F-102/F-103/F-104/F-105/F-106 were found in one app and are
corpus-generic).

**What prevents one genuinely fully runnable application?** Nothing —
HelloWorldSelfAware IS the fully runnable reference application (full chain +
visual proof + interaction + reproducibility), and Chess Clock is the first
real corpus app at L7 with a visual state transition.

## 7. Binding laws (restated)

- Regression gate: micro-proof fixture → pixel golden → 3-run determinism →
  full battery (96 stages with the EXT fixture) → affected real-APK re-run →
  honest frontier update. Never silently reduce the battery.
- Forbidden: app-specific shortcuts, package-name hacks, blank-frame
  acceptance, rc=0-as-success, committing raw logs/traces/APKs/blank
  screenshots, token/secret material anywhere.
- One file per role: `ACHIEVEMENTS.md` (executions), `KNOWLEDGE_INDEX.md`
  (knowledge), `ROADMAP_STATUS.md` (this file), `README.md` (landing).
  Everything else: roleful, merged, archived, or deleted.

_Era roadmaps remain in place as history with header pointers where their
claims were absorbed here. Do not update them._
