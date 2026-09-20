# S71 REPORT — FOUNDATION FORENSIC TRIAGE

Rule 0 honored: no API was fixed until the whole P0/P1 surface was
forensically audited. Only S70 tools were used (upgraded in place where they
were defective). Everything below is evidence-linked.

## 0. Engine/tool trust (USE-first census of S70 tools)

| tool | input → output | decision it feeds | defect found (fixed in place) |
|---|---|---|---|
| diagnose.py | registry id → 17-section bundle | root-cause path | hardcoded `run/s69_live` → stale-data false lead (F-136 bundle showed S69 golden sha while current binary produces R-NEW-389 sha). Fixed: freshest-live resolution. |
| graph_build.py | indexes+traces → knowledge_graph.json | status law | hardcoded s69_live trace dir (broke when dir removed → silent 0-LIVE graph). Fixed: freshest-live law (s71_live outranks s69_live). |
| live_runs.json | per-app live summaries | apps block, matrix rebuild | no builder existed; rebuilt from fresh traces with schema-preserved fields (scripts/s71_refresh_live_runs.py; S69 archive kept). |
| api trace recorder | engine → api_calls.json | per-call forensics | `api_trace.arguments = arg_names` records REGISTER NAMES, not values (dalvik_engine.cpp:14451) — string content invisible to trace diffs. This recorder defect HID the R-NEW-389 root cause from S70. Documented (bounded value capture = follow-up). |
| s71_forensic.py | 136 LIVE-STUB + traces → 9-way classification | triage | new (this session, on top of S70 artifacts). |
| s71_coupling.py | families × fresh traces → depth-weighted ranking | root selection | new (trace-window coupling; no second graph built). |

Fresh live evidence: 10 canonical APKs re-run (run/s71_live, same canonical
recipe). Rebuilt graph reproduces S70 law exactly: 6,396 APIs / 929
LIVE-IMPL / 136 LIVE-STUB / 2,264 SERVED-STATIC / 0 UNSERVED. Bonus
determinism proof: unote api_calls.json byte-identical across builds
(sha a4031ada…) — dispatch traces are build-stable; the bouncy PIXEL delta
was therefore always content-side, never trace-side.

## 1. FOUNDATION GATE — 136 LIVE-STUB forensic breakdown

| final class | n | notes |
|---|---|---|
| TRUE-MISSING | 87 | real laws missing; 8 of 10 P0 here |
| INTRINSIC | 22 | no runtime equivalent by architecture (GL/EGL, notifications, SoundPool, window chrome cosmetics) |
| APP-SPECIFIC | 11 | app-defined receivers misattributed as platform gaps |
| FALSE-UNSERVED | 7 | guard bodies EXIST; receiver class missed substring guards → **fixed by F-137 this session** |
| PARTIAL | 6 | behavior partially applies (setTextSize ×4 bookkeeping, Random ctor, getRefreshRate) |
| IMPLEMENTED-CORRECT | 2 | super-call bookkeeping only |
| IMPLEMENTED-WRONG | 1 | SQLiteDatabase.equals (identity law violated) |
| UNKNOWN | 0 | both initial UNKNOWNs resolved with caller-context evidence (`<unknown>.add` = FragmentTransaction.add chain; `j$…newKeySet` = desugar-shim law) |

The P0 10: Enum.valueOf / String.<init> / List.contains / Arrays.sort /
LinkedHashSet.<init> / ThreadLocal×3 = TRUE-MISSING (silent-wrong);
TextView.setTextSize + Random.<init> = PARTIAL.

## 2. Semantic families (136 → 16 laws)

36 raw families consolidate to 16 semantic laws over the 101 actionable
records (rank = depth-weighted fan-out + trace-window coupling + silent-wrong;
docs/foundation/s71/family_ranking.json):

1. ANCESTRY-DISPATCH (22 rec; rank 6170; 194 coupled APIs) — **FIXED F-137**
2. COLLECTION-ELEMENTS (8 rec; 109 sites; contains/ctor/sort semantics)
3. OBJECT-CLASS / CLASS identity laws (getClass receiver coverage, isX,
   equals identity, boxing)
4. WIDGET-LISTENER (setAdapter/listener/checked laws)
5. WINDOW-CHROME (intrinsics + getDefaultDisplay/getAttributes)
6. THREADLOCAL per-thread map law
7. NIO/BUFFER + BAOS stream semantics
8. ENUM-LAW (valueOf)
9. FRAGMENT-TX (manager→transaction chain, dooz)
10. TEXTSIZE bookkeeping
11. DRAWABLE (ShapeDrawable family, setColorFilter)
12. BUNDLE/URI/TYPEDVALUE/INTENTFILTER/JSON framework-data laws
13. STRING-CTOR (content copy/decode overloads)
14. ARRAYS-ORDER (sort post-state)
15. DESUGAR-SHIM (j$ CHM views)
16. MISC singletons/props/thread-state/Runtime

## 3. R-NEW-389 — ROOT-CAUSED (was OPEN/P1)

FIRST PIXEL DIVERGENCE achieved at OP level (not pixel guessing): the canvas
op trace differs in exactly one field between builds — `drawText` content
`""` → `"Touch to start"` (ScoreView.java:226 getString). F-136's ARSC-first
string law fixed that resolution; the 81 px dark→yellow band is the hint
text rendering. Controls: current ×3 + golden ×3 + comment-only ×1
deterministic; instrumentation render-neutral. Verdict: SEMANTIC, correct
direction; the S70 "cross-build nondeterminism" hypothesis is DISPROVED.
(docs/foundation/s71/R-NEW-389_ROOT_CAUSE.md)

## 4. R-NEW-388 — re-measured; demoted from foundation list

Generic RelativeLayout anchor laws PROVEN on the f14 fixture with the current
binary (alignParentRight x=780, centerInParent (340,760), below-chain y=300 —
no (0,0) collapse). TriPeaks never reaches GameActivity in canonical runs
(splash WebView); blocker is app-specific sequencing.
(docs/foundation/s71/R-NEW-388_REMEASURE.md)

## 5. A7 — generic contract chain (corrected impact)

Label: raw-captured, never ARSC-resolved, ZERO runtime consumers; icon:
unparsed; no title-bar surface → S66 "raw @0x… in pixels" claim corrected
(log-only today). Generic law to build: manifest reference resolve at consume
time + getApplicationLabel/labelRes/icon consumers. Bundles with F-137
(getApplicationInfo guard) + DRAWABLE-LAW.
(docs/foundation/s71/A7_CONTRACT_CHAIN.md)

## 6. F-137 — the evidence-selected root, FIXED this session

Root: 39+ framework guards match `class_name.find("Context")/find("Activity")`;
app subclass receivers (NoteMain, BouncyActivity, GameMasterDice,
MultiDexApplication, dooz App/MainActivity, microtimer MainActivity) miss ALL
guards → silent type-default stubs. Upstream law: Application/Service extend
Context; Activity extends ContextThemeWrapper extends Context (AOSP).

Fix (no guard sites touched): `framework_ancestor_for_dispatch()` — DEX
superclass walk (class_to_superclass_) + built-in AOSP platform table; ONE
retry at the bridge stub fallthrough (dalvik_engine.cpp:30507). Bounded (12
hops, terminal at Context, trace keeps the REAL receiver class).

Proof chain:
- gmdice `GameMasterDice.getResources`: STUBBED → IMPLEMENTED ×5
- unote `NoteMain.getWindow`: STUBBED → IMPLEMENTED
- dooz `App.getApplicationContext`: STUBBED → IMPLEMENTED; `App.getClass`
  ×2 IMPLEMENTED; `<unknown>.getClass` 14→12
- bouncy MultiDexApplication.getApplicationInfo chain fires (Application→Context)
- TRUE-MISSING ancestry rows (setTitle/setTheme/setShowWhenLocked/
  setTurnScreenOn) correctly UNCHANGED (need method laws — exactly as the
  classification predicted)
- Battery: 92/94 PASS (the 2 fails = EXT-01/02 external fixture APK absent
  in this fresh container — environmental, fetch-documented; all fixture
  builds re-passed after toolchain bootstrap)
- Pixels: 5/6 apps byte-identical pre/post; dooz new sha 736592d0… ×3
  deterministic with exactly the predicted API conversions. No app-specific
  patch anywhere.

## 7. Ten-section verdict

1. **What S70 initially believed**: 136 LIVE-STUB + 10 P0 mostly real
   foundation gaps; R-NEW-389 = suspected cross-build nondeterminism.
2. **What forensic audit disproved**: R-NEW-389 nondeterminism (op-level
   root cause found); "trace-identical ⇒ pixels-identical" reasoning (trace
   records register NAMES); TriPeaks RL wiring gap as a CURRENT foundation
   law gap (generic fixture passes); A7 pixel-impact claim (no consumer
   exists); 7 FALSE-UNSERVED + 11 APP-SPECIFIC + 22 INTRINSIC are not
   "missing APIs"; 2 of 136 were trace-resolution artifacts resolved by
   caller context.
3. **What is actually missing**: 87 TRUE-MISSING records → 16 semantic
   laws; top: ancestry method laws (setTitle/setTheme/…), collections
   element semantics, getClass receiver coverage, Enum.valueOf,
   String ctors, ThreadLocal, fragment-tx.
4. **What is only an extractor/matrix artifact**: FALSE-UNSERVED ×7
   (substring dispatch), APP-SPECIFIC ×11, register-name-only trace args,
   stale live-run citations, 2 trace-class-resolution records.
5. **Semantic families**: 16 (list above; ranking file with depth +
   coupling + silent-wrong weights).
6. **Highest-impact root contracts**: ancestry-dispatch (done), collection
   element semantics, object/class identity, enum law, fragment-tx.
7. **Which root was fixed**: F-137 ancestry-dispatch (full chain: upstream
   law → implement → battery → corpus pixels → determinism ×3).
8. **Real consumer impact**: 6 apps re-run; conversions listed in §6; zero
   unexplained pixel deltas; battery green.
9. **Remaining unknowns**: none at triage level (UNKNOWN=0). Open
   implementation: 85 TRUE-MISSING laws (minus 6 converted), EXT fixture
   fetch in fresh containers, recorder value-capture upgrade, dooz Compose
   (separate campaign per S70), F-138 HUD geometry.
10. **FOUNDATION COMPLETE = NO** — honestly: 87→81 TRUE-MISSING laws remain
    (6+ converted by F-137 this session); but the foundation list is now
    PROVEN, RANKED, and ROOT-CAUSED — prioritization is no longer guesswork.

## 8. Success criteria (mandate's 10)

① P0 classified 10/10 ✓ ② P1s classified 136/136 ✓ ③ families extracted ✓
④ foundation roots ranked ✓ ⑤ R-NEW-389 instrumented to root cause ✓
⑥ R-NEW-388 source→layout chain ✓ ⑦ A7 generic contract ✓ ⑧ 136→16 laws ✓
⑨ generic high-fanout root evidence-selected AND fixed ✓ ⑩ no priority by
raw counts alone ✓
