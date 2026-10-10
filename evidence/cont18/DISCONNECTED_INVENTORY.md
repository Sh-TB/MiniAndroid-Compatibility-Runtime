# CONT-18 WAVE A — Disconnected/Unused Findings Inventory

- binary: aed46450c103f2ea (HEAD e99c2fbd, 5 anchors x3 zero-drift)
- registry total: 566; non-terminal (disconnected): 320
- class counts: {"A": 35, "B": 49, "C": 38, "D": 109, "E": 88, "F": 1}

| class | meaning |
|---|---|
| A | IMPLEMENTED-UNCLOSED: fix landed, closure chain never completed |
| B | ROOT-PROVEN-NO-FIX: root verified correct, no fix attached |
| C | EVIDENCE-CAPTURED-PENDING: evidence/classification done, fix not attempted |
| D | PARTIAL-REMAINING: partial fix, remaining scope abandoned |
| E | UNPROVEN-RESEARCH: unproven or researched-not-implemented |
| F | BLOCKED-OTHER |

## P0/P1 disconnected findings (the abandonment front line)

| prio | id | cls | status | title |
|---|---|---|---|---|
| P0 | F-NEW-179 | A | IMPLEMENTED | Per-frame canonical pump for Compose/WebView/Choreographer (item 21 P0-8) |
| P0 | F-NEW-199 | A | IMPLEMENTED | DEEP-AUDIT P0-2: ArchTaskExecutorShadow::dispatch treats executeOnDiskIO(Runnable) as effectively no-op — back |
| P0 | F-NEW-215 | A | IMPLEMENTED | DEEP-AUDIT (new campaign §6) CLASS-INIT HONESTY LAW: failed <clinit> left the class silently INITIALIZED — ens |
| P0 | F-NEW-216 | A | IMPLEMENTED | ENUM-CONSTANT NAME LAW (kOrdinals): the table carried a FICTIONAL member TimeUnit.NANOS (that name belongs to  |
| P0 | F-NEW-218 | A | IMPLEMENTED | CLASS-TOKEN BACKING VALIDATION LAW: execute_instance_of's F-105c arm dereferenced CLASS_REF.ref_id as a heap i |
| P0 | F-NEW-219 | A | IMPLEMENTED | REFLECTION METHOD-FAMILY LAW: Class.getMethod/getDeclaredMethod minted a Method record for ANY name (F-029 min |
| P0 | F-NEW-220 | A | IMPLEMENTED | CONTENT-PARENT REUSE LAW (F-NEW-197-B first leg): the F165-CONTENT anchor materialized a PARALLEL android.R.id |
| P0 | F-NEW-222 | A | IMPLEMENTED | COLLECTIONS EMPTY-FACTORY LAW: Collections.emptyMap()/emptySet() had NO handler — the bridge fallback answered |
| P0 | F-NEW-223 | A | IMPLEMENTED | VIRTUAL EXTERNAL-STORAGE VOLUME + HONEST FILE CREATION LAW: android.os.Environment had NO handler (getExternal |
| P0 | F-NEW-225 | A | IMPLEMENTED | GENERIC-TYPE + FRAMEWORK-REFLECTION FAMILY (4 sub-laws): (225a) Field.getGenericType() unbridged → null → Gson |
| P0 | F-NEW-226 | A | IMPLEMENTED | VIEW PAINT IDENTITY LAW: TextView.getPaint() unbridged → NULL → TextPaint.measureText NPE at ssw MyChrono.setF |
| P0 | R-NEW-300 | A | IMPLEMENTED |  |
| P0 | R-NEW-345 | A | IMPLEMENTED | runBlocking/BlockingCoroutine joinBlocking livelock — kotlinx event-loop state machine + worker threads never  |
| P0 | R-NEW-347 | A | IMPLEMENTED | dooz23 first-frame chain (compose BOM 2026.06.01 / runtime 1.11.4): AndroidComposeView never attached, never D |
| P0 | R-NEW-349 | A | IMPLEMENTED | dooz23 onCreate death: eager measure inside setContentView(View) dispatched real DEX AbstractComposeView.onMea |
| P0 | R-NEW-350 | A | IMPLEMENTED | protobuf-javalite MessageInfo chain dead: 3-arg Class.forName(String,Z,ClassLoader) silently void + Class.asSu |
| P0 | R-NEW-056 | B | VERIFIED-CORRECT |  |
| P0 | R-NEW-058 | B | VERIFIED-CORRECT |  |
| P0 | R-NEW-063 | B | VERIFIED-CORRECT |  |
| P0 | R-NEW-081 | B | VERIFIED-CORRECT |  |
| P0 | F-NEW-157 | C | OBSERVED-FAIL | libGDX AndroidGraphics.createGLSurfaceView NPE (EGL/GLSurfaceView frontier): app-boundary unwind at MainActivi |
| P0 | F-NEW-169 | C | OBSERVED-FAIL |  |
| P0 | F-NEW-208 | C | PENDING | SUCCESS-PATH SP-1+SFC-1/2: build the success corpus + per-title success signature — every title with real L4 e |
| P0 | F-NEW-209 | C | PENDING | SUCCESS-PATH SP-2/3/12 + SFC-3/4/5: prove the common successful chain (APK->manifest->Application->Activity->W |
| P0 | F-NEW-156 | D | PARTIAL | Fresh-corpus onCreate APP BOUNDARY unwind family: first-run NPE inside app onCreate (before/at setContentView) |
| P0 | F-NEW-172 | D | PARTIAL | F-NEW-172 |
| P0 | F-NEW-197 | D | PARTIAL | V10 five-app gate white/black frontier (fresh census attribution): Dame (blidraughts), Droidify, OpenCalculato |
| P0 | R-NEW-001 | D | PARTIAL |  |
| P0 | R-NEW-061 | D | PARTIAL |  |
| P0 | R-NEW-242 | D | PARTIAL |  |
| P0 | R-NEW-246 | D | PARTIAL |  |
| P0 | R-NEW-256 | D | PARTIAL |  |
| P0 | R-NEW-259 | D | PARTIAL |  |
| P0 | R-NEW-260 | D | PARTIAL |  |
| P0 | R-NEW-279 | D | PARTIAL |  |
| P0 | R-NEW-285 | D | PARTIAL |  |
| P1 | F-104 | A | IMPLEMENTED | F-104 (S58): io/state law family — FileInputStream/FileReader sandbox ctor law + "file:" stream keys in cached |
| P1 | F-NEW-163 | A | IMPLEMENTED | S135 VISUAL RUNTIME BOOT/TRACE LOGGER — dual-path observability (machine trace.jsonl + semantic overlay trace_ |
| P1 | F-NEW-189 | A | IMPLEMENTED | Gate data-root freshness law discovered and documented (simplestopwatch SharedPreferences persistence) |
| P1 | F-NEW-200 | A | IMPLEMENTED | DEEP-AUDIT P0-3: forbid STUBBED+return-true+SUCCESS transitions — required state vocabulary EXECUTED / EXECUTE |
| P1 | F-NEW-201 | A | IMPLEMENTED | DEEP-AUDIT P0-4 (extended proofs beyond F-NEW-183): the one canonical content parent per live window must surv |
| P1 | F-NEW-202 | A | IMPLEMENTED | DEEP-AUDIT P1-5: HandlerShadow::settle advances virtual time by an extremely large amount — prove normal scree |
| P1 | F-NEW-203 | A | IMPLEMENTED | DEEP-AUDIT P1-6: ArchTaskExecutorShadow::isMainThread / ThreadShadow::currentThread / LooperShadow convert ide |
| P1 | F-NEW-224 | A | IMPLEMENTED | ONE CANONICAL DESCRIPTOR NORMALIZATION LAW: the four spellings (Landroidx/foo/Bar; / androidx.foo.Bar / androi |
| P1 | F-NEW-227 | A | IMPLEMENTED | PAINT.MEASURETEXT LAW: Paint/TextPaint.measureText had NO handler for any overload — every text-metrics probe  |
| P1 | R-NEW-402 | A | IMPLEMENTED | S81 visual audit instrument: status ladder EXECUTED ≠ VISUALLY COMPATIBLE (L0 LOADED_ONLY … L5 VISUALLY_VERIFI |
| P1 | R-NEW-428 | A | IMPLEMENTED | View.scrollTo/scrollBy fire onScrollChanged hook (AOSP View law) |
| P1 | R-NEW-430 | A | IMPLEMENTED | computeScroll dispatch per frame in the draw walk (AOSP ViewGroup draw law) |
| P1 | R-NEW-431 | A | IMPLEMENTED | View.setChecked/toggle/isChecked + onCheckedChanged hook |
| P1 | R-NEW-433 | A | IMPLEMENTED | View listener family storage (OnScrollChangeListener/OnCheckedChangeListener/OnItemClickListener/OnItemLongCli |
| P1 | R-NEW-435 | A | IMPLEMENTED | ViewPropertyAnimator record + settle-on-start |
| P1 | R-NEW-436 | A | IMPLEMENTED | Scroll-clip walk law: scrolling-ancestor fully-outside skip + RenderTask clip fields |
| P1 | R-NEW-454 | A | IMPLEMENTED | Browser DOM/URL surface family missing for module-class pages: URLSearchParams (30+ z.ai bundle sites), docume |
| P1 | R-NEW-455 | A | IMPLEMENTED | Browser resource-forensics instrumentation missing (S133 §4/§5/§31): no per-resource table, no stage traces, n |
| P1 | R-NEW-003 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-009 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-011 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-012 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-013 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-014 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-026 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-027 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-028 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-033 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-052 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-053 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-057 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-059 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-060 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-065 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-077 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-135 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-139 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-174 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-187 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-188 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-194 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-195 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-197 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-198 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-199 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-208 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-254 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-272 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-275 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-276 | B | VERIFIED-CORRECT |  |
| P1 | R-NEW-451 | B | VERIFIED | <img> replaced-element law missing: DOM <img> had no fetch, no box, no paint (only JS new Image()/CSS backgrou |
| P1 | R-NEW-452 | B | VERIFIED | Inline SVG BASIC-SHAPES law missing (SVG2 §10.3/§10.4): paint_svg_content painted only <path>/<use> — <circle> |
| P1 | R-NEW-453 | B | VERIFIED | Canvas attribute intrinsic-size law missing (WHATWG HTML §4.12.4): parsed <canvas width= height=> kept a 1x1 b |
| P1 | F-138 | C | REGISTERED | ScoreView hint HUD geometry — bitmap-font text drawn at (0,0) (legacy text path, text_size=0) |
| P1 | F-143 | C | OPEN | Service launch/lifecycle family: Service.onCreate/onStartCommand/startForegroundService (stopwatch = service-o |
| P1 | F-145 | C | OPEN | Final screenshot capture surface does not follow the top-of-stack window (multi-activity apps capture the spla |
| P1 | F-147 | C | OPEN | dooz: ViewGroup.getChildAt(I) on null receiver at MainActivity.onCreate pc=228 (v10 null — likely a findViewBy |
| P1 | F-NEW-161 | C | OBSERVED-FAIL | chessclock_29: NPE "Uri.toString on null receiver" at ChessClock.setUpGame pc=321 → APP-BOUNDARY unwind. getIn |
| P1 | F-NEW-168 | C | OBSERVED-FAIL | WhatsApp next faces (F-NEW-156 chain continues): (a) androidx FragmentManager host law — 'FragmentManager has  |
| P1 | F-NEW-198 | C | PENDING | DEEP-AUDIT P0-1: ApplicationRuntime legacy rendering path — prove by call graph + runtime trace that no real A |
| P1 | F-NEW-205 | C | PENDING | DEEP-AUDIT P1-8: view_tree_lifecycle_owner installation must be window-canonical — owner lookup from Compose/A |
| P1 | F-NEW-206 | C | PENDING | DEEP-AUDIT P1-9: cross-check the traversal order against AOSP ViewRootImpl — attach -> measure -> layout -> pr |
| P1 | F-NEW-207 | C | PENDING | DEEP-AUDIT P1-10: final visual gate — never accept status bar/navigation bar/placeholder pixels/diagnostic ove |
| P1 | F-NEW-210 | C | PENDING | SUCCESS-PATH SP-4/5/6/7/8: authority-accounting audits — renderer-family selection must use only runtime seman |
| P1 | F-NEW-211 | C | PENDING | SUCCESS-PATH SP-9/10: investigate the successful apps' upstream source (TicTacToe Classic, Simple Stopwatch, b |
| P1 | F-NEW-212 | C | PENDING | SUCCESS-PATH SP-11 + SFC-9: high-fan-out missing-laws search — once the successful path is known, inspect fail |
| P1 | F-NEW-213 | C | PENDING | SUCCESS-PATH SP-13 + SFC-6/7: SUCCESS-PATH REPORT (A working titles examined; B exact renderer family of each; |
| P1 | F-NEW-217 | C | PENDING | kotlinx-coroutines virtual-concurrency frontier: MutexImpl.unlock F084 spin (50,001 visits, bytecode_size=66)  |
| P1 | F-NEW-221 | C | OBSERVED | R8-MERGED CLASS CONSTRUCTOR/DISPATCH MISMATCH: LA/h; is a horizontal class merge (field `a` mode int + packed- |
| P1 | F-NEW-229 | C | OBSERVED | CL MATCH_PARENT SPEC LAW: a ConstraintLayout child with width/height=MATCH_PARENT and NO anchors on that axis  |
| P1 | F-NEW-250 | C | CLASSIFIED | kotlinx.serialization reflective serializer chain (serializerOrNull -> Companion/INSTANCE reflection -> @Seria |
| P1 | F-NEW-256 | C | CLASSIFIED | Compose real-content frontier — REFINED CONT-10: scope re-invocation WORKS (W5 'zero reinvocation' corrected); |
| P1 | R-NEW-331 | C | OBSERVED-FAIL |  |
| P1 | R-NEW-381 | C | OBSERVED-FAIL | Dooz v23 first-frame content — S61 face: the Compose draw path is now WIRED (F-108 R8-rename law: identity via |
| P1 | R-NEW-395 | C | USED_BY_EXECUTION | java.security.AccessController.doPrivileged law: dispatch the action's run() and return its result (libcore Ac |
| P1 | R-NEW-396 | C | USED_BY_EXECUTION | Class.getDeclaredFields on synthetic (non-DEX) classes answers the known declared-field subset (Lsun/misc/Unsa |
| P1 | R-NEW-397 | C | USED_BY_EXECUTION | java.util.Collections EMPTY_SET/EMPTY_LIST/EMPTY_MAP static-final singletons + Empty-family read contract (Ope |
| P1 | R-NEW-398 | C | USED_BY_EXECUTION | Platform-text-pipeline routing for non-ASCII strings + CJK fallback face (AOSP fonts.xml fallback chain) |
| P1 | R-NEW-399 | C | USED_BY_EXECUTION | AOSP ViewGroup child-dispatch law: touch targets are bounds-checked per CHILD; ancestor bounds never gate the  |
| P1 | R-NEW-400 | C | USED_BY_EXECUTION | AOSP MediaPlayer object law: create() → non-null PREPARED player; start/pause/stop/release/reset per the state |
| P1 | F-NEW-162 | D | PARTIAL | C013-CUSTOMVIEW inline placeholder contaminates visible frames and can stand in for unimplemented renderer fam |
| P1 | F-NEW-166 | D | PARTIAL | WhatsApp_next_face (F-NEW-156 family): onCreate dies BEFORE any setContentView — NPE 'INVOKE_RETURN must not b |
| P1 | F-NEW-230 | D | PARTIAL | GOLDEN PROVENANCE/CONFIG GAP: four banked golden SHAs are not reproducible at HEAD with default configs — ssw  |
| P1 | R-NEW-002 | D | PARTIAL |  |
| P1 | R-NEW-004 | D | PARTIAL |  |
| P1 | R-NEW-005 | D | PARTIAL |  |
| P1 | R-NEW-006 | D | PARTIAL |  |
| P1 | R-NEW-015 | D | PARTIAL |  |
| P1 | R-NEW-017 | D | PARTIAL |  |
| P1 | R-NEW-024 | D | PARTIAL |  |
| P1 | R-NEW-034 | D | PARTIAL |  |
| P1 | R-NEW-062 | D | PARTIAL |  |
| P1 | R-NEW-127 | D | PARTIAL |  |
| P1 | R-NEW-173 | D | PARTIAL |  |
| P1 | R-NEW-223 | D | PARTIAL |  |
| P1 | R-NEW-258 | D | PARTIAL |  |
| P1 | R-NEW-261 | D | PARTIAL |  |
| P1 | R-NEW-340 | D | PARTIAL-FIX |  |
| P1 | R-NEW-441 | D | PARTIAL | SlidingUpPanelLayout runtime-state family: View.getLeft/getTop/getRight/getBottom had NO bridge (umano dimChil |
| P1 | R-NEW-281 | E | UNPROVEN |  |
| P1 | R-NEW-283 | E | UNPROVEN |  |
| P1 | R-NEW-284 | E | UNPROVEN |  |
