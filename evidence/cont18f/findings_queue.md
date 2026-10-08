# FINDINGS QUEUE (generated — do not edit by hand)

Source: root_registry.json (578 rows). Regenerate: `python3 scripts/findings_queue.py`.

Queued (actionable): **255**   Terminal (closed/rejected/superseded/not-applicable): **323**

Queued by priority: {"P3": 105, "P2": 65, "P1": 53, "P0": 32}

## Top 40 of the queue

| # | id | pri | status | layer | title |
|--:|----|-----|--------|-------|-------|
| 1 | F-NEW-156 | P0 | OBSERVED-FAIL | — | Fresh-corpus onCreate APP BOUNDARY unwind family: first-run NPE inside app onCreate (before/at setContentView) |
| 2 | F-NEW-157 | P0 | OBSERVED-FAIL | — | libGDX AndroidGraphics.createGLSurfaceView NPE (EGL/GLSurfaceView frontier): app-boundary unwind at MainActivi |
| 3 | F-NEW-169 | P0 | OBSERVED-FAIL | — |  |
| 4 | F-NEW-265 | P0 | CLASSIFIED | dex/exceptions + compose/measure | DOOZ FIRST DIVERGENCE RE-ROOTED (supersedes the W6 'canvas bridge never constructed' reading as a downstream c |
| 5 | F-NEW-172 | P0 | PARTIAL | DEX interpreter / array + loop seman | F-NEW-172 |
| 6 | F-NEW-197 | P0 | PARTIAL | white-screen family | V10 five-app gate white/black frontier (fresh census attribution): Dame (blidraughts), Droidify, OpenCalculato |
| 7 | R-NEW-001 | P0 | PARTIAL | — | (title backfilled CONT-17) R-NEW-001 — live re-verified at HEAD, see evidence |
| 8 | R-NEW-061 | P0 | PARTIAL | — | (title backfilled CONT-17) R-NEW-061 — live re-verified at HEAD, see evidence |
| 9 | R-NEW-242 | P0 | PARTIAL | — | (title backfilled CONT-17) R-NEW-242 — live re-verified at HEAD, see evidence |
| 10 | R-NEW-246 | P0 | PARTIAL | — | (title backfilled CONT-17) R-NEW-246 — live re-verified at HEAD, see evidence |
| 11 | R-NEW-256 | P0 | PARTIAL | — | R-NEW-256: composition constructs deep into Material3 (1.13M trace lines, M13); state→tree law partial |
| 12 | R-NEW-259 | P0 | PARTIAL | — | (title backfilled CONT-17) R-NEW-259 — live re-verified at HEAD, see evidence |
| 13 | R-NEW-260 | P0 | PARTIAL | — | (title backfilled CONT-17) R-NEW-260 — live re-verified at HEAD, see evidence |
| 14 | R-NEW-279 | P0 | PARTIAL | — | (title backfilled CONT-17) R-NEW-279 — live re-verified at HEAD, see evidence |
| 15 | R-NEW-285 | P0 | PARTIAL | — | (title backfilled CONT-17) R-NEW-285 — live re-verified at HEAD, see evidence |
| 16 | F-NEW-179 | P0 | IMPLEMENTED | renderer/frame-pump | Per-frame canonical pump for Compose/WebView/Choreographer (item 21 P0-8) |
| 17 | F-NEW-199 | P0 | IMPLEMENTED | runtime/arch-task-executor | DEEP-AUDIT P0-2: ArchTaskExecutorShadow::dispatch treats executeOnDiskIO(Runnable) as effectively no-op — back |
| 18 | F-NEW-215 | P0 | IMPLEMENTED | dex/class-initialization | DEEP-AUDIT (new campaign §6) CLASS-INIT HONESTY LAW: failed <clinit> left the class silently INITIALIZED — ens |
| 19 | F-NEW-216 | P0 | IMPLEMENTED | framework/enum-constant-identity | ENUM-CONSTANT NAME LAW (kOrdinals): the table carried a FICTIONAL member TimeUnit.NANOS (that name belongs to  |
| 20 | F-NEW-218 | P0 | IMPLEMENTED | dex/class-token-identity | CLASS-TOKEN BACKING VALIDATION LAW: execute_instance_of's F-105c arm dereferenced CLASS_REF.ref_id as a heap i |
| 21 | F-NEW-219 | P0 | IMPLEMENTED | runtime/reflection-method-family | REFLECTION METHOD-FAMILY LAW: Class.getMethod/getDeclaredMethod minted a Method record for ANY name (F-029 min |
| 22 | F-NEW-220 | P0 | IMPLEMENTED | runtime/window-content-anchor | CONTENT-PARENT REUSE LAW (F-NEW-197-B first leg): the F165-CONTENT anchor materialized a PARALLEL android.R.id |
| 23 | F-NEW-222 | P0 | IMPLEMENTED | framework/collections-empty-factory | COLLECTIONS EMPTY-FACTORY LAW: Collections.emptyMap()/emptySet() had NO handler — the bridge fallback answered |
| 24 | F-NEW-223 | P0 | IMPLEMENTED | storage/external-volume | VIRTUAL EXTERNAL-STORAGE VOLUME + HONEST FILE CREATION LAW: android.os.Environment had NO handler (getExternal |
| 25 | F-NEW-225 | P0 | IMPLEMENTED | reflection/generic-type-identity | GENERIC-TYPE + FRAMEWORK-REFLECTION FAMILY (4 sub-laws): (225a) Field.getGenericType() unbridged → null → Gson |
| 26 | F-NEW-226 | P0 | IMPLEMENTED | framework/view-paint-identity | VIEW PAINT IDENTITY LAW: TextView.getPaint() unbridged → NULL → TextPaint.measureText NPE at ssw MyChrono.setF |
| 27 | F-NEW-264 | P0 | IMPLEMENTED | dex/exceptions | EXCEPTION-INTEGRITY DELIVERY LAW: move-exception must deliver the REAL in-flight java.lang.Throwable object (A |
| 28 | R-NEW-300 | P0 | IMPLEMENTED | — | R-NEW-300: S22 [M3-19-CYCLE] LB1/a;.B re-entered (depth=17) stubbed the runner's coroutineScope start; [S22] g |
| 29 | R-NEW-345 | P0 | IMPLEMENTED | — | runBlocking/BlockingCoroutine joinBlocking livelock — kotlinx event-loop state machine + worker threads never  |
| 30 | R-NEW-347 | P0 | IMPLEMENTED | — | dooz23 first-frame chain (compose BOM 2026.06.01 / runtime 1.11.4): AndroidComposeView never attached, never D |
| 31 | R-NEW-349 | P0 | IMPLEMENTED | — | dooz23 onCreate death: eager measure inside setContentView(View) dispatched real DEX AbstractComposeView.onMea |
| 32 | R-NEW-350 | P0 | IMPLEMENTED | — | protobuf-javalite MessageInfo chain dead: 3-arg Class.forName(String,Z,ClassLoader) silently void + Class.asSu |
| 33 | F-143 | P1 | OPEN | — | Service launch/lifecycle family: Service.onCreate/onStartCommand/startForegroundService (stopwatch = service-o |
| 34 | F-145 | P1 | OPEN | — | Final screenshot capture surface does not follow the top-of-stack window (multi-activity apps capture the spla |
| 35 | F-147 | P1 | OPEN | — | dooz: ViewGroup.getChildAt(I) on null receiver at MainActivity.onCreate pc=228 (v10 null — likely a findViewBy |
| 36 | F-138 | P1 | REGISTERED | — | ScoreView hint HUD geometry — bitmap-font text drawn at (0,0) (legacy text path, text_size=0) |
| 37 | F-NEW-161 | P1 | OBSERVED-FAIL | dex/api | chessclock_29: NPE "Uri.toString on null receiver" at ChessClock.setUpGame pc=321 → APP-BOUNDARY unwind. getIn |
| 38 | F-NEW-217 | P1 | CLASSIFIED | runtime/virtual-concurrency | kotlinx-coroutines virtual-concurrency frontier: MutexImpl.unlock F084 spin (50,001 visits, bytecode_size=66)  |
| 39 | F-NEW-221 | P1 | OBSERVED | dex/r8-merged-class-identity | R8-MERGED CLASS CONSTRUCTOR/DISPATCH MISMATCH: LA/h; is a horizontal class merge (field `a` mode int + packed- |
| 40 | F-NEW-229 | P1 | OBSERVED | layout/constraintlayout-match-parent | CL MATCH_PARENT SPEC LAW: a ConstraintLayout child with width/height=MATCH_PARENT and NO anchors on that axis  |
