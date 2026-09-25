# S103 — MAXIMUM EXTRACTION / TEST EVERYTHING (campaign evidence record)

Zero production changes. Every claim below has execution evidence in
`run/s103/` unless marked code-level. 3-run rule applied to key findings.

## U-001 CLASS IDENTITY — VERIFIED (runtime, 3/3 deterministic)

- Fresh ballbreak run (current tree): androidx Toolbar inflates under its REAL
  descriptor `Landroidx/appcompat/widget/Toolbar;`; dex superclass chain
  dispatches (`Toolbar → ViewGroup`); real dex <init> runs (Toolbar$LayoutParams
  addView observed).
- POSITIVE instanceof + check-cast proof: `ActionBarOverlayLayout.pullChildren`
  → `findViewById(action_bar=0x7f080028, receiver=cf) → FOUND view_id=232` →
  `ToolbarWidgetWrapper.<init>` executes with the real Toolbar receiver
  (`getContext` dispatched via Toolbar→ViewGroup chain) — the instanceof passed
  and the check-cast succeeded (log lines 1288-1310, u001_ballbreak.log).
- OLD bug stays dead: zero occurrences of the S101-era ISE "out of Toolbar".
- NEW FIRST DIVERGENCE (deeper in the same chain):
  `WindowDecorActionBar.init pc=0 → findViewById(decor_content_parent=0x7f080054,
  search_root=70) → NOT FOUND`, `pc=15 findViewById(action_bar=0x7f080028,
  search_root=70) → NOT FOUND` → `getDecorToolbar(null)` → ISE
  "Can't make a decor toolbar out of **null**" → APP BOUNDARY unwind.
  Root: the sub-decor subtree (where the Toolbar lives) is NOT linked under the
  window DecorView root used by WindowDecorActionBar. Same run contains both
  subtrees: receiver=cf finds view 232; root=70 does not.
  3/3 runs: ISE x2 each, screenshots byte-identical (fe797c19...).
- N-001 COLLISION CORPUS (scripts/s103/dex_typescan.py — opcode-LOW-byte
  corrected, ground-truth-validated against getDecorToolbar):
  22/59 corpus APKs execute instance-of/check-cast on exactly the classes the
  inflater maps away (AppCompatTextView/Button/CheckBox/... → platform,
  FloatingActionButton → ImageView, MaterialButton → Button).
  Highest: privacyfriendly2048 (21x AppCompatButton, 69x AppCompatCheckBox
  instanceof), battleship (Toolbar x7 + FAB x10 cast sites).
  Sites recorded per APK in run/s103/u001_typescan.json.
- Engine-semantics divergence (code-level): inflated AppCompat* views carry
  platform descriptors → `is_subclass_of` instanceof answers FALSE where real
  Android (AppCompatViewInflater substitution) answers TRUE; check-cast is
  deliberately optimistic (dalvik_engine.cpp:13505) → no CCE divergence but an
  instanceof/cast inconsistency. Runtime observation pending apps reaching
  those sites (their first divergences are earlier).

## U-002 THEME / NULL-PRODUCER FAMILY — VERIFIED (runtime)

- obtainStyledAttributes producer (S101 law) holds: `F-NEW-175 obtainStyledAttributes
  attrs=127 theme-backed` + real attr values consumed (windowMinWidthMajor=124...),
  createSubDecor 5x getBoolean + recycle consumed without NPE; chain advanced
  two stages past the S101 getDimensionPixelSize NPE site. TypedArray VALUE
  correctness beyond non-null NOT independently verified this campaign.
- Null-producer family fan-out (fresh S102 log sweep, scripts/s103 sweep):
  **30/61 titles** carry "on a null object reference" crash evidence — the
  single biggest failure family. Top null receivers: Field.get x5,
  MarginLayoutParams.getMarginStart x5, Object.getClass x4, Rect.set x3,
  WindowInsets.inset x3, Window.getCallback x1 (S83 law exists), CoordinatorLayout
  anchor family x2+2.
- Producer audit (code-level): getDeclaredField ALWAYS succeeds (allocates a
  Field even for nonexistent names — libcore throws NoSuchFieldException);
  getField (public/inherited) NOT implemented → default stub null → the
  Field.get NPE killing 5 real titles.

## U-003 HANDLER — VERIFIED (runtime, 3/3); queue ORDER diverges; FL-004 root-cause claim DISPROVEN

- Probe fixture (fixtures/maxext_probe, APK SHA 4c5e6d65... pre-rebuild;
  re-built with order probes for runs 2-3):
  H1 Looper.getMainLooper() = nonnull; H2 new Handler(mainLooper) OK.
  H3 posted runnable EXECUTED (marker RAN); H4 postAtFrontOfQueue runnable
  EXECUTED (marker RAN). The source comment "recorded as a no-op" is stale —
  a looper pump drains posts before first onResume.
- H6 order-final = "-PF" in 2/2 runs of v2: posted runs BEFORE front-posted.
  ART law: front-of-queue must run first (FP). postAtFrontOfQueue is
  currently treated as a tail enqueue → ORDER DIVERGENCE (E4, deterministic).
- FL-004 ("postAtFrontOfQueue missing = root cause") DISPROVEN: the callbacks
  DO execute; only front-semantics diverge.

## U-004 View.getWidth — REPORT HYPOTHESIS DISPROVEN; real root = setFrame non-materialization

- W1 new View: w=0 mw=0 — CORRECT (AOSP getWidth = mRight - mLeft, no frame yet).
- W2 after measure(EXACTLY 200,100): mw=0 — DIVERGENCE (measured dimension not
  stored; expect 200).
- W3 after layout(10,20,210,120): **w=0 h=0 — DIVERGENCE**: the frame never
  lands (expect 200x100). The "0 is semantically correct" defense FAILS here:
  layout() did not materialize mLeft/mRight/mTop/mBottom. Root = setFrame /
  layout bookkeeping for directly-laid-out views, NOT the getWidth getter.
- W4 GONE + layout: w=0 (same root; vis=8 correct). W5 zero-frame: 0 correct.
- Upstream: AOSP View.java getWidth()/setFrame laws; parent-layout propagation
  works differently (real apps render — W3 exposes the direct-layout subset).

## U-005 REFLECTION Field.get — 8 LIVE DIVERGENCES (probe fixture, 3/3 deterministic)

| case | result | ART law |
|------|--------|---------|
| R1 static int get(null) | null | 42 |
| R2 static Object get(null) | null | nonnull |
| R3 static final get(null) | null | "const-value" |
| R4 instance get(this) | null | 7 |
| R5 instance get(null) | NO-THROW | NPE |
| R6 getDeclaredField(missing) | NO-THROW | NoSuchFieldException |
| R7 getField(inherited) | NPE (null Field) | 99 |
| R8 Field.set static | silent no-op (42 != 43) | 43 |
| R9 getModifiers (instance) | 9 (PUBLIC|STATIC hardcoded) | 1 |
| R10 getField(missing) | null Field | NoSuchFieldException |
| R11 boxed static Integer | 0 (pre-init default) | 1234 |

- Root law: FIELD IDENTITY FRAGMENTATION — the reflection Field bridge reads
  static_field_storage_/heap keys that do not match the keys the interpreter's
  sput/iput wrote (R1-R4, R8, R11), plus a missing getField implementation and
  missing existence checks (R5-R7, R10). Mirror evidence: dalvik_engine.cpp
  getDeclaredField block (28582+) and Field.get block (29686+).

## U-006 COMPOSE CHAIN — first divergence = R8 MERGED-LAMBDA BRANCH DISPATCH (same field-identity root)

- Fresh solitaire run: S102 laws held (ComponentActivity constructed; compose
  classes initialized; ComposeView.setContent reached onMeasure).
- Chain: onCreate → ComponentActivity.setContentView → AbstractComposeView.onMeasure
  → ensureCompositionCreated → resolveParentCompositionContext →
  WindowRecomposer_androidKt.getWindowRecomposer → SynchronizedLazyImpl.getValue
  → LocalDensity$1.invoke → noLocalProvidedFor("LocalDensity") → ISE →
  APP BOUNDARY unwind (u006_solitaire.log lines 764-806).
- APK-bytecode proof (primary evidence): `LocalDensity$1` is an R8-merged lambda
  class — 30 static INSTANCE fields, 1 instance selector field (6-insn <init>),
  `invoke` = packed-switch at pc=3 with 29 branches (keys 0..28) covering the
  default lambdas of LocalViewConfiguration...LocalDensity PLUS the
  AndroidUiDispatcher.CurrentThread block (Looper/Choreographer/ThreadLocal/
  EventLoop/BlockingCoroutine, pc=114-212). getWindowRecomposer pc=76/88 reads
  `AndroidUiDispatcher.Main$delegate` (SynchronizedLazyImpl obj 324) — the
  DISPATCHER branch should run; the engine executed the LocalDensity branch
  (selector field iput/iget never met). NOT a missing LocalDensity provider.
- Downstream dependencies (inside getWindowRecomposer, next frontier after the
  selector law): View.setTag (pooling container), ViewModelProvider.get,
  LifecycleOwner.getLifecycle, View.getHandler, HandlerContext, BroadcastFrameClock,
  Recomposer.<init>, LazyStandaloneCoroutine, addOnAttachStateChangeListener.

## U-007 ARSC OFFSET16 / COMPACT — UNSUPPORTED + MISPARSE-RISK; 0 measured exposure

- AOSP law pinned (fetched ResourceTypes.h, run/s103/upstream_ResourceTypes.h):
  ResTable_type.flags FLAG_SPARSE=0x01 / FLAG_OFFSET16=0x02 (off16==0xffff →
  NO_ENTRY else off*4); ResTable_entry.FLAG_COMPACT=0x0008 (value packed
  inline, no trailing Res_value); ResStringPool UTF8_FLAG=1<<8.
- Engine (arsc_parser.cpp): SPARSE supported (sparse-entry branch matches AOSP
  off<<2 law); OFFSET16 NOT handled (dense branch reads u32 unconditionally →
  u16-pair table misparses); COMPACT NOT handled (entry walker expects
  trailing Res_value). No flag check exists for either.
- Corpus measurement (scripts/s103/arsc_flagscan.py, scanner validated on
  ballbreak: 152 types, 809 complex, 3327 simple): 54 APKs scanned →
  OFFSET16: 0 APKs; COMPACT: 0 APKs; SPARSE: 0 APKs. UTF-8 pools: common
  (supported). Classification: UNSUPPORTED + MISPARSE-RISK,
  NOT-REQUIRED-IN-APK-PATH today (F-Droid/aapt2-built corpus).

## U-008 CDEX — UNSUPPORTED (explicit clean rejection) + NOT-REQUIRED-IN-APK-PATH

- Loader law (dex_parser.cpp:135): accepts magic 035/036/037/038/039,
  header_size must be 0x70, endian tag 0x12345678.
- Execution evidence: synthetic fixture (cdex001\0 magic swapped into the probe
  APK, run/s103/maxext_cdex.apk) → `PARSE_ERROR: Invalid DEX magic:
  6364657830303100`, status FAILURE, 0 frames. No misparse, honest rejection.
- Corpus: 119/119 dexes standard dex magic (dexfamilyscan) → CDEX never
  appears in the APK path (it is ART on-device output). 10 multidex APKs
  (max 3 dexes); 10 near-ID-limit dexes (max 64,422 method ids — u32 counts
  in the parser, safe); jumbo const-string 0x1b used 3,617x corpus-wide
  (engine walks all 66 dexes without desync → supported); invoke-polymorphic
  (0xfa/fb) and invoke-custom (0xfc/fd): 0 occurrences (R8-desugared corpus).

## PART C — FALSE LEADS / SYSTEM BOUNDARIES

- FL-004 Handler.postAtFrontOfQueue as root: DISPROVEN (posts execute; only
  front-ordering diverges — see U-003).
- FL-005 View.getWidth "NPE" diagnosis: DISPROVEN (no NPE involved; pre-layout
  0 is CORRECT; post-layout 0 is a setFrame bookkeeping bug — see U-004).
- FL-001 full emulators: nothing kernel-level needed — every divergence found
  this campaign is framework-semantics level (fields, frames, queues, resources).
- FL-002 full JVMs: borrowable surface = libcore reflection/Class laws
  (exactly the U-005 gap), not execution-engine replacement.
- FL-003 Skia/Cairo: unchanged; no graphics divergence surfaced this campaign.

## PART D — SECOND-ORDER MAP (what shares each root)

1. FIELD IDENTITY FRAGMENTATION → reflection Field.get/set static+instance,
   getField, NoSuchFieldException, merged-lambda selector dispatch (compose
   recomposer init), atomicfu fallback scan, DI frameworks, Kotlin metadata.
   Kills or blocks: solitaire (compose), memory, mancala, chess + latent in
   every R8-merged-lambda APK.
2. WINDOW-DECOR ↔ SUB-DECOR LINKAGE → decor findViewById producers,
   WindowDecorActionBar init, decor-toolbar family (5 titles), any
   decor.findViewById caller.
3. QUEUE ORDER (front-of-queue) → Choreographer sequencing, animation tick
   order, deferred UI work that assumes front semantics.
4. SETFRAME NON-MATERIALIZATION (direct-layout subset) → apps that layout()
   views directly then read getWidth/Height; measuredWidth storage.
5. ARSC OFFSET16/COMPACT + CDEX → latent only (0 exposure measured).

## PART E — SMALL CONCRETE PROBLEMS (exact symbols, no TODO inflation)

- execute_check_cast optimistic-pass vs instanceof is_subclass_of: identity
  inconsistency for the same object/type pair (dalvik_engine.cpp:13493/13556).
- Field bridge getModifiers hardcoded 9 (dalvik_engine.cpp:29725).
- getDeclaredFields returns unfiltered arrays (nonexistent names included).
- TypedArray hasValue/getBoolean/recycle REC-MISS noise from createSubDecor —
  answered via other paths; return-value correctness unverified.
- dump_method_v2.py:130 crashes on out-of-bounds string offsets (tool, not
  runtime; byte-order + bounds — S102 fix incomplete).
- View.measure does not persist measured dimensions (W2).
- arsc_parser has no ResTable_type.flags check for OFFSET16/COMPACT (silent
  misparse risk on future tables).

## COUNTS

- source searches / upstream fetches: 3 live fetches (ResourceTypes.h pinned)
  + local upstream trees (AOSP/OpenJDK references in-tree); repos inspected:
  AOSP frameworks/base (ResourceTypes), libcore reflection laws, androidx
  appcompat (getDecorToolbar), compose ui (WindowRecomposer), kotlinx.coroutines
  (BlockingCoroutine chain in merged lambda).
- exact symbols inspected: 40+ (listed above per U-item).
- MiniAndroid tests executed: 12 engine runs (ballbreak x3, probe v1, v2 x2,
  solitaire, cdex, +3 census/scans); 2 corpus scanners + 1 log sweep built.
- real APKs exercised: 3 (ballbreak, solitaire, probe fixture) + 59-corpus
  static scans (typescan, arsc, dexfamily).
- verified (runtime evidence): 6 U-items (U-001..U-006).
- verified (code-level only): U-007/U-008 engine-behavior claims + fixture
  execution for U-008 rejection.
- unverified: TypedArray value correctness; mapped-away-class instanceof at
  runtime (sites unreachable in current runs).
- rejected: FL-004 root-cause claim; FL-005 NPE diagnosis; "0 after layout is
  semantically correct"; "postAtFrontOfQueue is a no-op"; "LocalDensity
  provider missing"; S102-lemma "getField exists via getDeclaredField".
- new roots: field-identity fragmentation; sub-decor linkage; queue front-order;
  setFrame non-materialization (direct-layout subset).
- production changes: 0.
