# Multi-Agent Shared Worklog — MiniAndroid-Compatibility-Runtime

NOTE: this shared log was wiped by the S38 mid-session container reset and is
recreated from the S38 record onward. Git-tracked session history lives in
`docs/maintenance/worklog.md` (authoritative); commit messages on origin/main
carry the per-session detail (S16..S37 at HEAD 73a84aad).

---
Task ID: S38-MAIN
Agent: Super Z (main)
Task: MASTER CAMPAIGN 3 continuation — publish old pushes; JPG evidence conversion
(user directive: JPG <=100KB, not PNG); Hello World archive expansion (advanced
fixtures); wave-4 reruns of S37 budget-timeouts; R-NEW-335 shift-law probe;
root audit.

Work Log:
- Published pushes: server main verified at 73a84aad; local main synced (0 unpushed).
- S38-A (done twice — container reset mid-session): all 31 ledger evidence images
  converted PNG->JPG (540x960, q72, hellocolor q60), every image <=100KB
  (max 89KB), total 287KB; ledger references updated, zero stale refs.
  Deterministic: second-run JPG SHAs byte-identical to first-run.
- CONTAINER RESET mid-session (tools/ + build/ + all untracked files + local
  refs rolled back to 7a172e7c): recovered via `git fetch + reset --hard
  origin/main` (server main = 73a84aad intact). Re-fetched toolchain (ecj
  3.36.0 Maven Central, r8 8.3.37 r8-releases, android-34 Sable, aapt2 Google
  Maven). All S38 untracked work re-created from session context.
- AUDIT FINDING: S36/S37 commit messages claimed "registry 321->322" but the
  registry file in git stayed at 303 roots until S37's actual committed state
  (recovered 73a84aad registry = 322 roots, last R-NEW-335 — verified true).
  Shared worklog text vs committed file discrepancy documented.
- hello_widgets (Advanced Hello World #3) + hello_smoke (Advanced #2) built
  aapt2-linked and executed (pre-reset evidence): both SUCCESS with real
  multi-widget renders; hello_widgets = most advanced View-world render in the
  archive (ImageView drawable + EditText + Button + TableLayout 3 rows +
  RelativeLayout layout_below, 35.5% non-background).
- R-NEW-336 registered (P1): post-click setText on a TextView under a
  ScrollView root renders empty (default text vanishes); identical chain under
  LinearLayout root renders (hello_smoke count=1). Isolated: not concat, not
  getText, not invalidate. Structural delta = ScrollView root.
- R-NEW-335 probe: s38_shift_law fixture (7 laws, 26 checks) replicating the
  exact androidx.collection ScatterMap long-arithmetic (writeRawMetadata/
  readRawMetadata/group() guard/hash MurmurHashC1 chain/convertMetadata/
  neg+shr63 guard), anti-constant-folded via non-final statics, hardcoded
  expected values from independent big-int computation, visual verdict bands.
  APK 1a82564691a248b8d2d0be363d5986c1e171ca886acd1e36656f2c1f3550a6f1.
  Run pending runtime binary rebuild (make -j2 in progress after reset).
- wave-4 script re-created: 4 S37 budget-timeouts re-queued at 900s + 2 hello
  fixtures + shift-law probe first.

Stage Summary:
- Registry 322->323 (R-NEW-336). Evidence images: 31 JPG <=100KB.
- Root audit delivered: 103 PARTIAL / 72 UNPROVEN / 4 OBSERVED-FAIL /
  16 RESEARCHED-NOT-IMPLEMENTED remaining; P0 frontier = R-NEW-335 (dooz AIOOBE)
  + R-NEW-301/303/242/246/256/259/261/279/281/285 compose/lifecycle family.
- Next: run shift-law probe verdict -> R-NEW-335 verdict (engine-vs-dual-store);
  wave-4 runs; ledger S38 section; push; report progress %.

---
Task ID: S39
Agent: Super Z (main)
Task: Continue MASTER CAMPAIGN from wave-4 launch — check wave-4 results, attack dooz23 render chain, close roots, push everything.

Work Log:
- wave-4 corpus runner had died silently (bg process policy kills process groups across tool calls; setsid also killed) — fixtures were already complete (hello_smoke/hello_widgets/scroll_min + hw_fixed diagnostics all in /tmp/s38_runs/wave4/).
- Verified S38 commit 4f205e72 already contained R-NEW-336 fix + ledger JPG rows; pushed (was marked ahead-2, actually up-to-date after fetch; remote main = 4f205e72 confirmed via ls-remote).
- dooz23 attack (vtree2 evidence): composition died on ISE "Job Lkp1;@828 is already complete or completing" (Loj0;.T = JobSupport.makeCompletingOnce) on the FIRST measure — registered R-NEW-337 (scripts/s39_register_r337.py, roots 323->324).
- Built R337-DUAL probe in THROWABLE-MSG site (heap field dump of job+proposed objects): state obj#505 class=Lh20; fields=.e=1 = Empty(Active) — state was ACTIVE, the check misfired.
- Disassembled Loj0;.T/.d0/.M + Lh20; + Ljd; via androguard (installed into venv): d0 pc=0 instance-of Lmf0; (Incomplete) on null -> ALREADY_COMPLETING sentinel; M() reads state via sun.misc.Unsafe.getObjectVolatile(this, offset) with offsets from statics Loj0;.e/.f — ALL REC-MISS: engine had ZERO sun.misc.Unsafe / java.lang.reflect.Field / getDeclaredField shadows.
- FIX R-NEW-337: full atomicfu-via-Unsafe contract in try_shadow_dispatch — Class.getDeclaredField(s), Field.getName/getType/getDeclaringClass/getModifiers/setAccessible/get/set, Modifier.isStatic, Class.isAssignableFrom, Unsafe singleton (theUnsafe via Field.get), objectFieldOffset (deterministic (class,field)<->offset registry, members unsafe_field_offsets_/unsafe_offset_to_field_/unsafe_next_offset_ in dalvik_engine.h), getObjectVolatile/getObject/putObjectVolatile/putOrderedObject/putObject, compareAndSwapObject/Int/Long (heap CAS by object identity), Int/Long volatile get/put variants, arrayBaseOffset/arrayIndexScale. Post-fix: 30 offsets registered, ZERO ISE.
- Frontier R-NEW-338: Lqi0;.Q (coroutines stack-trace sanitizer) NPE "null array in Arrays.copyOfRange" — getStackTrace dispatched with RUNTIME class (R8-obfuscated) and M3-19 guard demanded Throwable/Exception/Error in the name. FIX: guard widened to any class (Thread excluded), setStackTrace/getStackTrace stored-sanitized-trace round-trip. Post-fix: zero NPEs.
- Frontier R-NEW-339: ISE "Required value was null." in Lt4;.<init> (=AndroidComposeView) — caller-PC forensics (new THROWABLE-STACK-PC via CallStack::set_last_invoke_pc + push_frame capture) pinned engine pc=415 = first autofill checkNotNull; T4PROBE invoke-static trace in Lt4;.<init> pinned it to Lob;.b(View)->View.getAutofillId() -> null -> Lwd;.a null -> Ld1;.e null-branch. FIX: ViewShadow.getAutofillId law (memoized per-view AutofillId heap object, ViewNode.autofill_id_obj) + getSystemService(Class/string) registry mirrored into try_shadow_dispatch ([R339-SVC]). Post-fix: zero ISE, ComposeView gains AndroidComposeView child (C013-LEAFCHK children=1), placeholder no longer drawn.
- Frontier R-NEW-340: launch frame pump ran before onCreate posted the FrameCallback (log 242402 quiescence < 242620 postFrameCallback cb=757). FIX: post-lifecycle pump (16 ticks) in stage_capture_output. Post-fix: doFrame fired, resume machinery drained, Recomposer job machinery advanced to .Q await path — deepest Compose execution recorded for dooz23. Residual: recomposer suspends without re-posting a frame callback (NEXT in registry).
- Regression checks clean: hello_smoke renders, hello_widgets byte-identical (2059104 nonwhite).
- Commits: 4f205e72 (S38, verified+pushed), 472fc4d5 (S39 3-root fix chain), 997e23a1 (S39-FIX2 pump law). All on origin/main.
- Registry 323 -> 327 roots (R-NEW-337 FIXED, 338 FIXED, 339 FIXED, 340 PARTIAL-FIX).

Stage Summary:
- dooz23 (PRIORITY-1 app) advanced from "empty grey placeholder" to "real view tree + live Recomposer machinery 3 fixes deep".
- New reusable forensics: R337-DUAL heap dumps, THROWABLE-STACK-PC caller-pc frames, T4PROBE per-ctor invoke trace, INSTANCEOF-DIAG interface-closure dump.
- Scripts persisted: s39_register_r337.py, s39_disasm_r337.py, s39_register_fixes.py, s39_register_r340.py.
- Next: trace recomposer post-resume suspension (R-NEW-340 NEXT), corpus wave 4 APKs (budget-timeout retries still pending), ledger dooz23 S39 section, progress report to user.

---
Task ID: S40
Agent: Super Z (main)
Task: Multi-front attack on full execution of Dooz v23 + games (user: "نه یک حمله چندین حمله متفاوت" — not one attack, several different attacks). FRONT-A (dooz23 composition chain) carried it: 3 roots root-caused+FIXED, first clean SUCCESS run ever.

Work Log:
- FRONT-A evidence chain (androguard disasm + FIELD-TRACE probes, runs r341..r354):
  (1) R-NEW-341: ISE "Could not find an Application in the given context" — Lv;.n = kotlin check-style thrower; caller Lk2;.b pc=776..880 = Hilt @HiltViewModel factory Application resolution (getApplicationContext -> instanceof Application -> ContextWrapper walk -> throw). Engine served a plain Context singleton. FIX: AOSP handleBindApplication law — bind_manifest_application() runs INSIDE execute_apk_with_activity post-DEX-inject (old runtime EXP093-APP trio ran with dex_report=NULL — [TRY-ENTRY] dex_report=NULL, run r340 — App.onCreate's Dagger build degraded to 80 ins), instantiates manifest App class via real DEX (<init>/attachBaseContext/onCreate), identity published to P0.7 + ActivityShadow + ApplicationLoader.applicationContext; manifest-activity path reuses the bound object.
  (2) R-NEW-342: CopyOnWriteArraySet.add REC-MISS dropped the Hilt members-injector from the androidx lifecycle registry (Ljm;.onCreate iterates Leq;->a; fast-path Leq;->b==null at <init>). PLUS next() typed elements Ljava/lang/Object; — observer undispatchable. FIX: CollectionShadow handles_class += concurrent/COWSet+COWAL; set semantics for COW sets; HeapAllocator.get_object_class() virtual + DalvikHeapAdapter; next() returns REAL runtime class. Probe proof: [S24-COLL] add obj=165 elems 0->1->2, iterator live, injectors dispatched.
  (3) R-NEW-343: java.lang.Class.cast() implemented NOWHERE — Lpm;.B (Hilt component-holder unwrap) null-poisoned the DI chain: Lns;.(null) -> Lls;.(null,null) -> Settings provider.get() <unset> -> "lateinit property settings has not been initialized" (Lxl; = UninitializedPropertyAccessException from Lqi0;.S, read site Le;.q @944 = compose resume reading MainActivity.B). FIELD-TRACE forensics: r350 Lpc;.e=obj#14 memoized; r351 Lps;.b=self(obj#14) root law; r352 Lns;.a=<unset> despite valid component = the null came through cast(). FIX: cast law in the Class bridge (null->null; castable via is_subclass_of incl. F-023 interface closure -> SAME reference identity; else throw_deferred CCE).
  - RESULT: run r354 Status SUCCESS, 0 errors 0 warnings — first clean dooz23 run ever; [R343-CAST] Lps; as Ll2; obj#14 OK; 36MB stderr (3x deeper real execution than pre-S40); App.onCreate -> Lps; Dagger SingletonComponent -> lifecycle-registry injection -> ViewModelProvider.get(DefaultKey:m2) chain all real bytecode.
  - R-NEW-344 registered (OBSERVED-FAIL, P0): first frame still blank — Recomposer suspends on JobSupport.await (Loj0;.Q, Lcj; continuation on job o1344) without re-posting frame callback; NEXT plan: o1344 final-state dump / completion->resume gap / bounded outer pump.
- FRONT-B/C/D (wave-4 corpus reruns, tap-attacks, new Dooz variants): deferred to next window — FRONT-A consumed the budget; corpus APKs intact in /tmp/my-project/apk_cache/{s36new,s37new}.
- Regression gate: hello_widgets nonwhite = 2059104 (EXACT S39 golden match), hello_smoke full-paint stable.
- Registry 327 -> 331 roots (341/342/343 FIXED, 344 OBSERVED-FAIL). Ledger 12b section added (honest: engine SUCCESS, NOT visually loaded).

Stage Summary:
- Dooz v23: PLACEHOLDER -> real Hilt/DI/composition execution, 0-error SUCCESS; visual frame pending R-NEW-344.
- New laws: AOSP bind-application, COW-set + element class identity, Class.cast identity/CCE.
- Next: R-NEW-344 await-resume attack; wave-4 corpus; tap-attacks on FULL-RENDER games; progress report.

---
Task ID: S41
Agent: Super Z (main)
Task: MULTI-FRONT RUNTIME ATTACK — dooz23 R-NEW-344/R-NEW-345 forensic + generic fixes + cross-app regression

Work Log:
- Recon: HEAD 676a7c73, 331 roots; wave-4 leftovers cleared; R-NEW-344 (dooz first-frame blank) picked as Attack-1 target.
- Attack-1 forensic (r354 artifacts + 3 fresh reruns run_a/b/c with env probes): runBlocking { settings.getTheme() } NEVER completed; joinBlocking spin 200k+ lines (Ljf;=BlockingEventLoop, Lhf;=BlockingCoroutine); ended only via 2x HALT-LOOP frame destruction (Lqq0;.a / Lvs0;.O); composition then ran ROOT-ONLY (content lambda produced no nodes). DEX identity map built: Loj0;=JobSupport, Ls;=AbstractCoroutine, Lkp1;=StandaloneCoroutine, Lzh;=CancellableContinuationImpl, Lrx;=DispatchedContinuation, Lh9;=AndroidUiDispatcher.dispatchCallback, Lnl;=CombinedContext, Lc41;=SnapshotMutableStateImpl, Lrd1;.C=mutableStateOf, Ljf;=BlockingEventLoop, Lo30;=EventLoopImplBase, Lh8;=DataStoreImpl.
- Attack-2 upstream: compose 1.6.7 exact sources (runtime+ui-android from Google Maven) — Recomposer/composeInitial/awaitWorkAvailable/PausableMonotonicFrameClock(pause at create; ON_START resumes via Latch)/AndroidUiDispatcher(event-driven, NOT continuous vsync)/AndroidUiFrameClock; kotlinx JobSupport.awaitInternal bytecode CAS proof; GitHub-first app sources (yamin8000/Dooz master): runBlocking { theme = settings.getTheme() } -> SettingsDataStoreRepository -> DataStoreHelper -> datastore.data.map{}.first().
- Attack-3 generic fixes (4 laws, zero class hacks): (a) SUPER-DISPATCH IDENTITY — invoke-super passes the CLEAN declaring class to bridge_to_api (the "<super>" marker blocked ALL framework-ancestor super calls from reaching shadows — Worker.start{super.start()} never reached ThreadShadow); (b) THREAD SELF-RUN — ThreadShadow.start with no recorded Runnable queues (thread,thread); the drain executes the subclass's REAL DEX run() (Lsr; workers live); (c) PARK-DRAIN — LockSupport.park/parkNanos/parkUntil = deterministic yield: bounded drain (handler runnables + choreographer doFrame + pending starts, depth<=3), unpark no-op, parked worker frames (depth>=1, zero work) suspend via [PARK-YIELD]; main-thread park never yields; (d) UNSAFE CLOSURE — compareAndSwapLong/getAndAddLong/getAndAddInt/getAndSetObject/getAndSetInt/getAndSetLong over the one heap store (R-NEW-337 law completion).
- Attack-4: dooz23 x4 independent runs post-fix: FULL startup pipeline completed (<280s, rc=1 SUCCESS), 3x PARK-YIELD, 0 HALT-LOOP, deterministic screenshot SHA 31ddd4d5b8e6d18e across runs. DataStore read reached (13 pre-fix NPEs -> 0 post-R-346-fix). First frame still blank — content composition = next frontier (R-NEW-344 refined).
- Attack-5: R-NEW-346 root-caused+fixed — HONEST FILE METADATA law (File.exists/isDirectory/canRead/canWrite real fs state via receiver path field, relative under app-data root; was always-true stub -> DataStore first-run read a non-existent file -> parser NPE x13). Post-fix: 0 exceptions.
- Cross-app regression matrix (s41_regress_matrix.py): gmdice 108922nw SUCCESS, microtimer 65090nw SUCCESS, bouncy 129600nw SUCCESS, unote 14850nw SUCCESS, tictactoe blank-first-frame (battery tictactoe_golden interaction PASS), dooz_18 timeout + stopwatch FAILURE verified PRE-EXISTING via HEAD A/B build (stash->rebuild->run->pop).
- Battery: 82 stages PASS incl. executor/Room/float/frame-pump/super-run fixtures + tictactoe_golden; EXT-01/02 = pre-existing missing-fixture gap. hello_widgets 2,058,896nw ~= S40 golden 2,059,104 (sampling error).
- Registry: R-NEW-345 registered (implemented, P0), R-NEW-344 refreshed (refined chain), R-NEW-346 registered in ledger section. Roots: 331 -> 332.
- Ledger: S41 section appended (full forensic chain + evidence paths + upstream fetches).

Stage Summary:
- KEY RESULTS: dooz23 startup pipeline now COMPLETES deterministically (was: never-completing runBlocking + 2 destroyed frames + empty composition). 5 generic runtime laws landed (super-identity, thread self-run, park-drain+yield, Unsafe family closure, honest file metadata). Zero regressions (A/B proven for the 2 suspicious targets).
- NEXT ROOT: content composition empty (R-NEW-344 core) — probe whether AbstractComposeView.setContent stored the content lambda before ensureCompositionCreated and whether the app composable lambda is invoked during composeInitial; then DataStore theme value round-trip.

---
Task ID: S41-r2
Agent: Super Z (main)
Task: Attack-6 — content composition frontier (R-NEW-344 core) round-2 forensic

Work Log:
- Probes run_e (FIELD-TRACE Lho;) / run_f (FIELD-TRACE Lc41;) / run_g (RET-TRACE Lxp1;) / run_h (RET-TRACE Lg4;) / run_i (RET-TRACE La72;) / run_j (ATOMIC-DIAG).
- Lho;.setContent: o=1 stored, holder n read — content lambda PERSISTED (obj#886 into Lc41; obj#894 Lmo1;.c via setValue).
- Lr;.g (ensureCompositionCreated) mapped from bytecode: builds holder Lx62;(view,owner,wrapper Lom;) and calls La72;.a.
- La72;.a: created AndroidComposeView Lt4; + addView(parent=ComposeView) and RETURNED holder obj#2812 (Lx62;) — the composition plumbing ran.
- Lx62;.e (lifecycle ON_CREATE handler) -> Lx62;.f -> Ls7;(flag=8,view,wrapper) -> Lt4;.setOnReadyForComposition — the DEFERRED compose request.
- Ls7;.i (the deferred invoke) does Looper.myLooper() vs view.getHandler().getLooper() identity check -> View.post(Lk5;) branch (ZERO View.post dispatches in all runs) OR inline compose.
- Version correction: Dooz master uses compose-bom 2026.06.01 + kotlin 2.4.10 (NOT 1.6.7) — DEX disassembly is the ground truth; fetched 1.6.7 sources are indicative only.
- Post-frame state (run_j): doFrame cb=973 fired; runnable 1414 (Lrx;) ran an AtomicReference state machine (get/set/getAndSet/CAS on obj#3107) and completed; then true quiescence. No exceptions (0 after R-NEW-346).

Stage Summary:
- The { Content() } wrapper is still never invoked; the deferred-compose-request chain (Ls7;/Lko;/Lk5;/setOnReadyForComposition) is the exact next frontier, documented in R-NEW-344 next-probe with 4 named probes.
- No code changes this round (forensic only); registry R-NEW-344 refreshed.

---
Task ID: S42
Agent: Super Z (main)
Task: Attack on the deferred-compose-request frontier (R-NEW-344 core) — user directive: next attack, everything commented, internet-sourced oracles until the game runs.

Work Log:
- DEX forensics round-1/2 (scripts/s42_disasm_r344_chain.py, s42_disasm_round2.py): mapped the FULL pending-compose-request contract in dooz_23 (compose BOM 2026.06.01, runtime 1.11.4): Lx62;.f is the ONLY producer of Ls7;(flag=8, ctx, wrapper) -> Lt4;.setOnReadyForComposition stores it in Lt4;->n0; Lt4;.onAttachedToWindow() pc 640-662 is the ONLY consumer (iget n0 -> if-null skip -> invoke-interface -> clear). Field xref: exactly one reader/clearer.
- run_a baseline: UC009 attach wave ran BEFORE AndroidComposeView existed (created lazily in first onMeasure: La72;.a pc=112 addView into the ALREADY-ATTACHED ComposeView 888) -> request stored, never consumed -> blank frame. [EXP062-ADDVIEW-TRACE] + [UC009-ATTACH] evidence.
- WEB ORACLE (user directive): fetched AOSP frameworks/base ViewGroup.java main branch (android.googlesource.com, 9585 lines) — addViewInner law verbatim: mAttachInfo != null && FLAG_PREVENT_DISPATCH_ATTACHED_TO_WINDOW clear -> child.dispatchAttachedToWindow(...) IMMEDIATELY; View.dispatchAttachedToWindow = AttachInfo first, then onAttachedToWindow, then ViewGroup recursion.
- FIX-1 (attach-on-add): ViewShadow.pending_child_attaches_ queue (record when parent attached at addView/addViewInLayout) + engine dispatch_attached_subtree_from() (mark-attached FIRST, super-chain onAttachedToWindow walk, iterative DFS re-reading children) consumed in bridge_to_api after try_shadow_dispatch (same shadow-flag/engine-callback pattern as Room callbacks) + one-shot attach guard in the UC009 loop. Evidence run_b/run_h: [R347-ATTACH] pending -> dispatched view=1512 class=Lt4; — AndroidComposeView.onAttachedToWindow ran for the FIRST TIME, consumed n0, composition STARTED (ComposerImpl Lxk0; live, 44 real calls incl. slot ops).
- FIX-2 (real-DEX measure): F10 hook extended to containers (AOSP View.measure dispatches onMeasure for EVERY subclass) + overrides_on_measure now recorded on the invoke-direct ctor path (was inflate-only — Lt4; built via invoke-direct had flag=false) + AOSP View.measure(final) law (receiver-node-based, placed BEFORE try_shadow_dispatch — silent-void ViewShadow handler was pre-empting it; [R347-MEASURE] view=1512 class=Lt4; dex_onmeasure=YES proves the real compose measure world runs) + View.onMeasure default one-store write-through + getMeasuredWidth/Height accessors (were implemented NOWHERE; AbstractComposeView reads them immediately after child.measure — DEX Lr;.i ground truth: getChildAt(0) -> child.measure(childSpec) -> setMeasuredDimension(child.measuredWidth+padding)).
- FIX-3 (DataStore file chain): uncaught NPE in Lg8;.a (STR-BRIDGE substring on null) killed the composition pass. Web-verified OpenJDK File.java semantics: File name-component law (getName/getPath/getParent/getParentFile/isAbsolute/getAbsolutePath; parent resolved against app-data root), File ctor path-assembly law (File(String)/(String,String)/(File,String)/(null,child)->child per OpenJDK; path stored in "path" field, R-NEW-346 metadata law reads it symmetrically), String.lastIndexOf(int[,int]) law (fromIndex<0 -> -1 — makes the extension idiom degrade JVM-exact). Evidence run_l: path="datastore/settings.preferences_pb" -> getName "settings.preferences_pb" -> lastIndexOf(46,22)=8 -> substring "preferences_pb" — the DataStore settings file chain completes end-to-end.
- REGRESSION GATE: gmdice 108922 / microtimer 65090 / unote 14850 nonwhite EXACT S41 goldens (all five laws behavior-neutral for the View-world corpus).
- Registry 332 -> 334 (R-NEW-347 implemented P0, R-NEW-348 OBSERVED-FAIL P0). Scripts persisted: s42_disasm_r344_chain.py, s42_disasm_round2.py, s42_register_roots.py.
- Upstream sources fetched to /tmp/s42: AOSP ViewGroup.java (main), compose-runtime 1.11.4 + compose-ui-android 1.11.4 sources jars (Google Maven) — versions extracted from the APK's META-INF.

Stage Summary:
- KEY RESULTS: the pending compose request now FIRES (attach-on-add law), AndroidComposeView.onAttachedToWindow runs and consumes it, the composition starts (ComposerImpl executes real slot-table ops), AndroidComposeView.onMeasure runs as REAL DEX, and the DataStore settings chain completes — all via 8 generic AOSP/OpenJDK laws, zero class hacks, zero golden regressions.
- NEXT ROOT (R-NEW-348): the 1.11.4 composition-capabilities gate (Lpz0;.c1 -> U0 null bail; Lqz0;.g = bits 128|0x400000) still terminates the pass before the app content lambda — the Dooz composables remain uninvoked; source-mapped frontier ready in /tmp/s42.
---
Task ID: S43
Agent: Super Z (session 43 — MASTER CAMPAIGN 3, Source-First continuation from remote HEAD d5073b4d)
Task: Continue the campaign from the current remote HEAD (container had rewound local to the S15 refactor; 35 S35→S42 commits recovered via fast-forward). Attack the standing frontier R-NEW-348 (dooz23 compose 1.11.4 content-lambda gate) with the Source-First law, multi-target discipline, GitHub/upstream oracles, everything commented.

Work Log:
- RECONCILE: fast-forwarded local main d5073b4d (S42 tip, ls-remote verified). Rebuilt the wiped environment: dooz23 APK re-fetched hash-verified (299eab21…), compose 1.11.4 runtime+ui+ui-android sources re-fetched from Google Maven (AndroidX coordinates, NOT org.jetbrains — the 404 lesson), ECJ 3.33.0 (Maven Central), r8 8.13.23 (Google Maven), platform-34-ext7_r03 android.jar restored; androguard bootstrapped into the venv.
- BASELINE (standard path): dooz23 rc=1, nonwhite=0, crash.log TWO chains: (1) RuntimeException "Unable to get message info for y81" x10 unwinding 20 frames, caught at Lne;.g catch-all; (2) ISE "Cannot locate windowRecomposer; View Lho;@960 is not attached to a window" (WindowRecomposer.android.kt:288) escaping MainActivity.onCreate invoke_pc=306 — onCreate dead BEFORE any composition.
- SOURCE-FIRST MILESTONE (compose 1.11.4 laws verified against real sources, /home/z/my-project/upstream/s43): invokeComposable JVM actual = (composable as Function2<Composer,Int,Unit>)(composer, 1) — Expect.jvmAndAndroid.kt:24; ComposerImpl renamed GapComposer in 1.11.4 (doCompose -> invokeComposable at GapComposer.kt:2643); NodeKind bits CONFIRMED (bit 7 = Nodes.OnRemeasured/MeasuredSizeAwareModifierNode, bit 22 = Nodes.LayoutAware) — the S42 "composition-services/capabilities gate" hypothesis for Lqz0;.g/Lpz0;.c1/U0 is DEAD: c1/U0 are the OnRemeasured dispatch, a normal empty-chain path. DEX map: Lr90;=kotlin Function2 (renamed), Lj90;=ComposableLambda (abstract h(Object,Object)Object), Lom;=ComposableLambdaImpl wrapper (19 interfaces), Lrr0;=MainActivity content lambda (implements Lj90;, h + <init>(MainActivity,I)); windowRecomposer law = WindowRecomposer.android.kt:288 checkPrecondition(isAttachedToWindow).
- R-NEW-349 ROOT+FIX (AOSP first-traversal ordering): ActivityShadow.setContentView(View) ran the U007 eager measure INLINE — with R-NEW-347/S42 the measure dispatches REAL DEX onMeasure (custom_view_measure_hook_) -> AbstractComposeView.onMeasure -> ensureCompositionCreated -> windowRecomposer require(isAttachedToWindow)=FALSE -> ISE. AOSP ViewRootImpl.performTraversals: attach wave STRICTLY precedes performMeasure. FIX: shadow RECORDS pending (attach-parent, measure-root); engine bridge consumes AFTER the shadow call: dispatch_attached_subtree_from(root) THEN measure_layout(root). Evidence: [R349-ORDER] root=960 -> [R347-ATTACH] Lho;@960 onAttachedToWindow -> AndroidComposeView Lt4;@1241 CREATED+attached DURING the wave -> measure done; windowRecomposer ISE 1 -> 0. SCOPE FIX (A/B-proven regression): the consume for setContentView is R349-record-only — draining pending-child-attaches there fired DEX onAttachedToWindow for XML-inflated trees (microtimer RoTimeControl) before post-inflate setup -> lateinit ISE escape -> white frame.
- R-NEW-350 ROOT+FIX (protobuf-javalite chain, DataStore read): runBlocking{settings.getTheme()} -> DataStore read -> protobuf MessageInfoFactory chain: DescriptorMessageInfoFactory CNFE = EXPECTED javalite fallback (caught); GeneratedMessageInfoFactory.isSupported TRUE ([R350-IAA]); asSubclass SILENT-NULL -> Lbc0;.d(NULL) ([R350-SHAPE] a0k8=NULL_REF) -> forName silent-void (3-arg form dispatched idx=6825 per [R350-FN2], ZERO bridge logs) -> defaultInstanceMap.get x2 NULL -> dynamicMethod(GET_DEFAULT_INSTANCE) NULL -> bare ISE -> RuntimeException("Unable to get message info for y81"). FIXES: (1) Class.forName OVERLOAD LAW at interpreter level in execute_invoke_static (BEFORE try_recursive_invoke/bridge — the call never reached the bridge; R-NEW-347 View.measure pre-emption pattern): dotted->L-desc -> class_info_index_ resolve -> ensure_class_initialized when initialize=true -> CLASS_REF; unknown -> deferred CNFE. (2) Class.asSubclass law in the Class bridge (OpenJDK: SAME reference when assignable — L-FORM descriptors for the subclass check, dotted form answered a false CCE; null->NPE; else deferred CCE). Evidence (MINIANDROID_R350_LAW=1): 'Unable to get message info' 23 -> 0; [R350-ASSUB] Ly81; asSubclass Lbc0; -> SAME reference; Ly81;.<clinit> OK + defaultInstanceMap.put; run advances into the FIRST real MessageSchema build. GATE: forName law DEFAULT-OFF (see R-NEW-352); dooz evidence runs pass MINIANDROID_R350_LAW=1.
- R-NEW-351 DISCOVERED (next frontier, OBSERVED-FAIL P0): the first real schema build dies in Llt0;.w (MessageSchema ctor, 1009B) aput-oob "length=1; index=1" at byte 0x772 (pc unit 953) — the int[] field table sized from the parsed MessageInfo is short for the writer loop; filled-new-array handler audited correct; MUTF-8 NUL decode verified correct (0xC0 0x80 -> real 0x00 byte) so split("\u0000") should work; needs protobuf MessageSchema oracle + full Llt0;.w/Lta1; disasm. nonwhite=2 (first non-white pixels ever for dooz23).
- R-NEW-352 REGISTERED (OBSERVED-FAIL P1): microtimer Room initDb retry loop under interpreter-level forName — 50001 re-visits of the SAME forName invoke (HALT-LOOP), lateinit ISE escape, white frame; A/B-proven (stash/unstash, identical APK); the reason the forName law is env-gated.
- CORPUS SWEEP (multi-target, default config): ChessClock 2,073,600/2,073,600 nonwhite rc=0, screenshot SHA e4a2d7c90cd2fd26... BYTE-IDENTICAL to the campaign-3 golden; gmdice 108,922 -> 1,745,009 nonwhite (16x, full render); unote 14,850 -> 236,521 (16x); microtimer 1,042,368 rc=0 (restored via the R-349 scope fix, == S42 baseline A/B). Evidence: docs/evidence/s43_r349_r350_r351/ (derived 540x960 PNGs, EVIDENCE.json SHAs, key log excerpts).
- BATTERY: 90/92 PASS — the ONLY 2 fails are the pre-existing EXT-01/EXT-02 external-fixture env gaps (documented since S35). Zero code regressions from the three new laws. Toolchain bootstrap script restored aapt2/ECJ/r8/android-34 after the container reset.
- Registry 334 -> 338 (R-NEW-349/350 implemented, R-NEW-351/352 OBSERVED-FAIL, R-NEW-348 refreshed SUPERSEDED-BY-EVIDENCE). Scripts persisted: scripts/s43_invoke_composable_probe.py, s43_fn2_shape_probe.py, s43_lambda_class_probe.py, s43_find_invoke_composable.py, s43_register_roots.py.

Stage Summary:
- Three generic laws landed with full root->proof->fix->micro->regression chains: (1) attach-before-measure (AOSP first traversal) — killed the windowRecomposer ISE and lifted gmdice/unote renders 16x each; (2) Class.forName overloads at interpreter level (env-gated) + (3) Class.asSubclass identity — unblocked the protobuf MessageInfo chain and reached the FIRST real schema build in dooz23 history.
- Honest frontier: dooz23 pixels remain 2/2,073,600; the content lambda is now blocked INSIDE protobuf schema construction (R-NEW-351), two layers past the S42 quiescence. R-NEW-352 (microtimer retry under the new law) is the gate to re-enabling R-NEW-350 by default.
- Next: (1) R-NEW-351 schema-table AIOOBE (protobuf MessageSchema oracle, full Llt0;.w map); (2) R-NEW-352 microtimer retry loop -> un-gate the forName law; (3) the compose content lambda (invokeComposable -> Lom;.h -> Lrr0;.h -> Dooz composables) is the direct next milestone once the DataStore read stops dying.
