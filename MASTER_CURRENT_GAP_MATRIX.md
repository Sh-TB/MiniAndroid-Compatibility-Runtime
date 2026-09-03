# MASTER_CURRENT_GAP_MATRIX — UNIFIED_011.3

Identity rule (§5/§7): findings are identified by **finding subject + target subsystem +
source + provenance**. RESULT numbers are NOT global IDs and are never used as keys
(different Agents reused overlapping RESULT numbers; e.g. two distinct "RESULT_012"
findings exist in historical reports — both are separately identified below by subject).

Every row: verified at the 011.3 head by fresh execution or fresh source inspection
during this campaign. Repro unless stated:
`python3 scripts/u011_test_matrix.py --binary build/miniandroid --apk-dir <cache>`
(fixture builds: `tests/unified0112_filled_new_array_test.cpp`,
`tests/unified0113_typed_catch_test.cpp`).

## Counts (calculated from the matrix below — not copied from any report)

```text
RAW_FINDINGS:        41   (agent-discovery sets + campaign audits + this campaign's new findings)
DISTINCT_FINDINGS:   38   (after merging 3 duplicates)
DUPLICATES:           3
ALREADY_FIXED:       17   (fixed in earlier campaigns, verified working at this HEAD)
NOT_REPRODUCED:       2
NOT_REACHABLE:        2
CONFIRMED_OPEN:       9
FIXED:                7   (fixed BY this campaign)
DEFERRED:             9
BLOCKED:              4
```

## A. DEX interpreter semantics (§7 inventory)

| Canonical ID | Finding | Provenance | Source | Current HEAD | Reproduced | Real APK | Duplicate | Already Fixed | Needs Fix | Test | Final Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DEX-FNA-35C | filled-new-array 35c arg_count read from opcode nibble `(pc>>4)&0xF` (const 2); G never read | Agent EXP-093 finding + UNIFIED_011.2 audit M3; EXP071 "✓ verified" claim REJECTED (presence-only) | dalvik_engine.cpp:5504 (pre-fix) | fixed @2f05134: A=(>>12), G=(>>8), C..F=cu2 | YES — fixture old-code 4/5 FAIL | Telegram varargs (Object…), any D8 varargs APK | no | yes (2f05134) | no | unified0112_filled_new_array_test 5/5 | FIXED+REGRESSION_TESTED |
| DEX-AGET-OOB-LIVELOCK | aget confirmed-OOB warn-and-continue → dooz LM1/i;.f livelock (78 s, 1.2 M instr) | UNIFIED_011.2 run logs | ARRAY_GET_CASE (pre-fix) | fixed @2f05134: confirmed OOB throws AIOOBE (SYNTH-EXC); arr_len==0 keeps legacy path | YES — dooz 78 s→0.8 s | dooz; any loop over arrays | no | yes (2f05134) | no | matrix dooz row + [SYNTH-EXC] log | FIXED+REGRESSION_TESTED |
| DEX-CATCH-TYPED | Typed catch handlers decoded but discarded (`(void)type_idx` in find_catch_handler_for_pc AND THROW handler); only catch-all ever fired | 011.2 audit; §18 | dalvik_engine.cpp:6301/5926 (pre-fix) | **FIXED (011.3)**: is_exception_subtype (DEX chain + built-in java.lang/io/util hierarchy); first subtype match wins, catch-all fallback, in BOTH lookup paths | YES — typed_catch_test cases 1/2/5 (old code FAILs them) | any app with typed catch (Signal init paths, Telegram catch-alls proven firing) | no | no | no | unified0113_typed_catch_test 8/8 | FIXED+REGRESSION_TESTED |
| DEX-THROW-NO-HANDLER | THROW with no handler = skip-and-continue (silently executed code after throw) | EXP-071 approximation | dalvik_engine.cpp:5885 (pre-fix) | **FIXED (011.3)**: frame unwind + caller-side try search; if uncaught anywhere → caller continues (documented compatibility tail — see DEX-EXC-TAIL) | YES — typed_catch_test case 6 | any real throw site | no | no | no | typed_catch_test 8/8 | FIXED+REGRESSION_TESTED |
| DEX-EXC-PROPAGATE | Exception unwinding a callee frame was silently dropped at the invoke site (no caller try-table search) | 011.2 audit note | try_recursive_invoke restore block | **FIXED (011.3)**: EXC-PROPAGATE searches caller try table at invoke pc; handler → jump with pending_exception_ (move-exception works); post-switch pc redirect defeats invoke `pc_+=len` clobber | YES — typed_catch_test case 7 | Telegram ConnectionsManager/LocaleController catch-alls PROVEN firing in run logs | no | no | no | typed_catch_test case 7 | FIXED+REGRESSION_TESTED |
| DEX-EXC-TAIL | Uncaught-anywhere exception previously killed the whole run when propagated (011.3 intermediate state: Telegram golden regressed to eb16ab5c) | **NEW 011.3** (found by telegram A/B during campaign) | try_recursive_invoke uncaught branch | **FIXED (011.3)**: uncaught tail = caller continues with null return (compatibility). Rationale: engine raises ARTIFACT exceptions (LruCache maxSize=0 IAE — real Android never throws there); full unwind killed onCreate | YES — telegram run: 088ea640 regression then restore | Telegram (golden preserved), all matrix apps | no | no | no | typed_catch_test case 8 + telegram golden 3/3 | FIXED (policy documented) |
| DEX-APUT-BOUNDS | APUT auto-grows `__array_length__` past end (no OOB) | 011.2 audit | ARRAY_PUT_CASE | **FIXED (UNIFIED_014)**: confirmed-length arrays enforce AOSP HandleAPut (null→NPE; idx<0\|\|idx>=len→AIOOBE "length=…; index=…"; store-only-after-checks; length immutable); unknown-length gate = legacy store+grow (aget parity); non-OBJECT_REF/heap-missing unchanged | YES — unified014_aput_bounds_test: old 4/6 FAIL (run/unified014_aput/before_fix_FAIL.txt), new 6/6; corpus A/B all 5 APKs byte-identical old→new (ssw golden 2a12587a ×3) | dooz/array loops; any aput-OOB path | no | no | no | unified014_aput_bounds_test 6/6 | FIXED+REGRESSION_TESTED |
| DEX-WIDE-ARITH | long/double arithmetic, cmp-long/-double, cmpl/cmpg, rsub, shifts, neg/not, lit8/LIT16, const-wide/32, packed/sparse-switch, fill-array-data, array-length, register nibbles | EXP-052/054/055/058/060 campaigns | dalvik_engine.cpp | present at HEAD | prior fixtures | Telegram timestamps (long) run 3/3 deterministic | no | yes | no | prior campaign fixtures | INTEGRATED |
| DEX-INVOKE-WIDE | invoke-{static,virtual,direct,super,interface} wide-arg merging; proto resolution per-DEX | EXP-058/079/082, EXP-095 CM-019 | execute_invoke_* | present | prior (runOnUIThread, LayoutHelper) | Telegram/AndroidX | no | yes | no | prior fixtures + matrix | INTEGRATED |
| DEX-IGET-IPUT-WIDTH | iget/iput variant width semantics (boolean/byte/char/short/wide/object) | EXP-062 | execute_iget/execute_iput | present | prior | corpus-wide | no | yes | no | matrix | INTEGRATED |
| DEX-REPEAT-CALL | repeat-call state leakage | EXP-088 multidex_inject | execute_method_internal reset | addressed (injection idempotence) | no | — | no | yes | no | prior | INTEGRATED |
| DEX-MULTIDEX-MAP | multi-DEX class/method ownership + cross-DEX resolution | EXP-088 Phase 1.2 inject_secondary_dex_classes; EXP-066 | dex engine | present (Telegram 5-DEX works; WhatsApp 12-DEX parses) | partial | Telegram (5 DEX) 3/3 golden | no | yes | no | telegram golden + whatsapp run | INTEGRATED (WhatsApp entry chain = separate row APP-WA-ENTRY) |
| DEX-EXC-TYPEDFRAME | synthetic exception/unwind correct continuation (method-frame return restoration) | 011.2 SYNTH-EXC + 011.3 | raise_synthetic_exception | present; fixture-proven | YES | dooz progress | no | yes (011.3 extends) | no | typed_catch_test | INTEGRATED |
| DEX-MONITOR-VOLATILE | monitor-enter/exit + volatile treatment | §7 inventory | interpreter | monitor = compatibility no-op (no threads), volatile n/a single-thread | by source inspection | none demonstrated | no | partial | no | — | LOW_IMPACT/DEFERRED |

## B. Resources / ARSC / AXML (§9)

| Canonical ID | Finding | Provenance | Source | Current HEAD | Reproduced | Real APK | Duplicate | Already Fixed | Needs Fix | Test | Final Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RES-SRC-IMG-MISMATCH | LayoutInflater wrote `src_drawable_path`; renderer read only `image_drawable_path` → dead state | 011.2 audit M5; §13 | layout_inflater.cpp:661 vs execution_engine.cpp:1382 | fixed @73e1946 (render fallback) | YES — ssw icons | simplestopwatch, any XML-src ImageView | no | yes | no | exp_graphics_image_e2e | FIXED (011.2)+REGRESSION_TESTED |
| RES-DRAWABLE-PATHS-DEAD | `resource_drawable_paths_` read in 2 places, populated nowhere (EXP-067 delivery incomplete) | 011.2 audit M4 | dalvik_engine.cpp:4303/10770 | fixed @73e1946 (populate, density-ranked) | YES | runtime setImageResource chain | no | yes | no | [IMG-RES-RENDER] log | FIXED (011.2) |
| RES-STRING-ARSC | @string/ARSC/res_config/string-pool/type-matched find_id | UNIFIED_007/009 | resource runtime | present | YES (gmdice/ssw strings) | corpus-wide | no | yes | no | matrix | INTEGRATED |
| RES-DENSITY | density-qualified drawable lookup (drawable-*dpi) | 011.2 fix | populate_resource_drawable_paths rank | present (NEW 011.2) | YES (ssw picked hdpi) | all APKs | no | yes | no | ssw after-frame | INTEGRATED |
| RES-OBFUSCATED | obfuscated res names (unote/headingcalc fall to default screen) | status_011_1 blockers | ARSC parser | present limitation | not reproduced this run (those APKs unchanged) | unote, headingcalculator | no | no | yes | — | CONFIRMED_OPEN (next-candidate campaign item §35.7) |
| RES-CONFLATION | resource/background/image ID conflation | §9 directive item | axml/layout_inflater | background→src distinct paths verified for ssw (background vs android:src) | YES (ssw renders both) | ssw | no | yes | no | ssw frames | INTEGRATED |
| RES-TYPEDARRAY-THEME | TypedArray / Theme.style inheritance | §9 directive item | resource runtime | partial (styles flat-resolved) | not reproduced | none blocking corpus | no | no | optional | — | DEFERRED |
| RES-RAWS | raw resources / res/0s.xml-style files / obfuscated file names | §9 | arsc/axml | res/0s-style names parsed via entry list | partial | none blocking | no | no | optional | — | DEFERRED |

## C. Image pipeline (§10/§12/§13/§14)

| Canonical ID | Finding | Provenance | Source | Current HEAD | Reproduced | Real APK | Duplicate | Already Fixed | Needs Fix | Test | Final Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| IMG-E2E-CHAIN | RESOURCE→ARSC→path→decoder→Bitmap→ViewShadow→ImageView→Canvas→framebuffer→PNG full chain | §11 E2E | exp_graphics_image_e2e | **PASS end-to-end** (011.2) + re-verified with pipeline renderer (011.3) | YES — ssw | ssw + XML-src apps | no | yes | no | exp_graphics_image_e2e + u0113 evidence | INTEGRATED |
| IMG-GETDRAWABLE-STUB | `Resources.getDrawable` returns stub string | EXP-067 | dalvik_engine.cpp:10760 | present | source inspection | rarely-hit path | no | no | optional | — | LOW_IMPACT |
| IMG-BITMAPFACTORY | `BitmapFactory.decodeResource` not an API entry (decoders exist) | 011.2 audit | source scan | absent as API | source inspection | runtime-bitmap apps | no | no | yes (needs IMG-HEAP-MODEL) | — | DEFERRED (with IMG-HEAP-MODEL) |
| IMG-SETIMAGE-DISCARD | setImageBitmap/setImageDrawable/setImageURI discard state ("no decode yet" comment) | 011.2 audit | android_shadows.cpp:1331 | present (marks-only) | source inspection | runtime-bitmap apps | no | no | yes (same prereq) | — | DEFERRED |
| IMG-HEAP-MODEL | Bitmap heap model: decode→bitmap object→heap identity→View state→renderer access (§14) | 011.2 final report open gap | heap/renderer | absent | by design audit | runtime-bitmap apps (WhatsApp avatars) | no | no | yes | — | CONFIRMED_OPEN (high-value §35.3) |
| IMG-FAB | ImageView render check misses FloatingActionButton (string class-name match) | 011.2 audit | execution_engine is_image_view | present | source inspection | FAB apps | no | no | yes (trivial) | — | DEFERRED (trivial, no real target yet) |
| IMG-PNG | PNG RGB/RGBA/palette/tRNS/bit-depths/Adam7 | CAMPAIGN-010 libpng lineage | PNGDecoder (libpng-backed) | present | prior 7,036-image differential + 12/12 fixture | corpus | no | yes | no | exp088_a4_png_decoder_test 12/12 | INTEGRATED |
| IMG-WEBP-JPEG | WebP + JPEG decode | EXP-097 | libwebp/libjpeg | linked + reachable from render dispatch | magic-branch exercised when assets present | Telegram avatars | no | yes | no | ssw PNG branch + magic detect | INTEGRATED |
| IMG-VECTOR-NINE | VectorDrawable / StateList / NinePatch decode | 011.2 audit | decoder set | placeholder path ("IMG?" + grey box) | by design | some apps | no | no | yes | — | CONFIRMED_OPEN (§35.13/14) |
| IMG-LOTTIE | Lottie (RLottie) animation | EXP-097/098 | rlottie linked | present (SMS screen) | prior | Telegram | no | yes | no | exp097 evidence | INTEGRATED |

## D. Graphics / render / interaction (§15/§22/§23/§27)

| Canonical ID | Finding | Provenance | Source | Current HEAD | Reproduced | Real APK | Duplicate | Already Fixed | Needs Fix | Test | Final Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GFX-CANVAS | Canvas save/restore/translate/clipRect/drawRect/drawBitmap/drawText/alpha/scale | §15 | software_renderer + api Canvas | subset present (STUB_DEBT documented) | ssw/gmdice frames | corpus | no | partial | yes (grow as real targets need) | matrix frames | INTEGRATED (subset) — remaining DEFERRED |
| GFX-GLES | GLES static GLES20 wiring; game reachability unknown | status_011_1 | gles bridge glue | not built; §16 rule: no real-APK GLES requirement demonstrated (corpus runs software) | no | none demonstrated | no | no | only on proven need | — | BLOCKED (per §16 — evidence-gated) |
| GFX-CLICK-DISPATCH | Touch → listener bytecode → state (dispatch) | 011.2 CLICK-TEST | dispatch_click + XML path | present | YES | gmdice, ssw | no | yes | no | click reports | INTEGRATED |
| GFX-FRAME2-RENDER | Click-test second frame re-rendered via ad-hoc content_view->draw() — bypassed the real pipeline; produced near-blank frames; pixel counts were redraw artifacts (gmdice "181,512 px", ssw "918,207 px" RECLASSIFIED) | **NEW 011.3** (visual oracle §23 exposed it) | stage_click_test probe | **FIXED (011.3)**: probe now calls stage_render_frame (identical pipeline/root selection as frame 1) | YES — before/after A/B in-campaign | gmdice, ssw, any click-probed app | no | no | no | u0113 click reports + oracle JSON | FIXED+REGRESSION_TESTED |
| GFX-FRAME2-THIS | XML android:onClick handlers executed with `this` = clicked View (activity heap object never passed) → instance fields hit wrong heap object → setText receiver_id=0, text="" → second frame unchanged | **NEW 011.3** ([EXP091-SETTEXT] view_id=0 evidence) | stage_click_test xml dispatch + ActivityShadow | **FIXED (011.3)**: activity heap id recorded (set_activity_heap_id) and passed as p0; handler chain reads REAL fields; re-render changes | YES — ssw Start→Stop/Lap 12,439 px oracle-verified | ssw + all XML-onClick apps | no | no | no | u0113_ssw_click3 + oracle JSON/PNG | FIXED+REGRESSION_TESTED |
| GFX-FRAME2-RUNTIMEVIEWS | gmdice roll flow mutates state but its UI (dialog/runtime-constructed views) never enters ViewShadow → true second-frame delta = 0 | **NEW 011.3** (honest re-measure after GFX-FRAME2-RENDER fix) | DiceCache.populate / dialog path | present limitation | YES (gmdice click report 0 px + dispatch chain logs) | gmdice (real game) | no | no | yes (runtime view construction model) | click_test_report.json | CONFIRMED_OPEN (§35.2 next blocker) |
| GFX-VISUAL-ORACLE | No quantitative before/after oracle (px/%, bbox) existed | §22/§23 directive | scripts/u0113_oracle_diff.py (NEW 011.3) | present | YES — gmdice + ssw JSONs | evidence tooling | no | no | no | run/u0113_oracle/*.json | INTEGRATED |
| GFX-SSW-REFLOW | ssw second frame renders correct Stop/Lap STATE but reflowed geometry (vertical vs horizontal buttons) vs frame-1 layout | **NEW 011.3** (honest observation) | render measure pass | present | YES (click_frame_0.png) | ssw | no | no | yes (measure re-run nuance) | oracle PNG | DEFERRED (cosmetic; state correctness proven) |

## E. Runtime APIs / app foundation (§8/§28/§29/§30)

| Canonical ID | Finding | Provenance | Source | Current HEAD | Reproduced | Real APK | Duplicate | Already Fixed | Needs Fix | Test | Final Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| API-CORE-STRINGS | substring/concat/parseInt/Long/Float/Double/StringBuilder/collections/isEmpty | §8 | api bridge + shadows | present (fixture-verified prior campaigns) | prior | corpus-wide | no | yes | no | prior fixtures | INTEGRATED |
| API-ASYNC | Handler/Looper/MessageQueue/Runnable/AsyncTask/HandlerThread/ThreadPoolExecutor/FutureTask | §29 | shadows + DispatchQueue evidence | present subset (Telegram runnables drain: [EXP090-DRAIN]) | YES (telegram logs) | Telegram | no | partial | grow on demand | telegram run | INTEGRATED (subset) |
| API-PREFS-SQLITE | SharedPreferences (real file save [PREFS] logs), SQLite | §8/§30 | shared_prefs + exp085 | present subset | YES ([PREFS] Saved default.xml 9 entries) | ssw | no | yes | no | exp085 phases | INTEGRATED |
| API-WINDOW-LIFECYCLE | Window/WindowManager/ViewRoot/permission callback/IME | §28 | ActivityShadow | partial (onCreate→resume path; IME absent) | partial | corpus | no | partial | on-demand | matrix | DEFERRED (no blocking target) |
| API-WEBVIEW | WebView absent → bgclock stops at L6 | 011.2 matrix | bridge | absent | YES (bgclock row) | bgclock | no | no | yes (large) | — | BLOCKED (large scope; documented boundary) |
| API-NETWORK | HttpURLConnection/ConnectivityManager | §30 | stubs | stub (no real network by design) | by design | Signal/WhatsApp boundaries | no | no | on-demand | — | NOT_REACHABLE (external boundary documented) |
| API-STORAGE-FILES | file APIs / AssetManager / raw resources / System.loadLibrary | §30 | file_sandbox + assets chain | present subset (BufferedReader asset chain EXP-071) | partial | Telegram fonts/assets | no | partial | on-demand | — | INTEGRATED (subset) |
| API-MEDIA-CAMERA-SENSORS | notifications/alarms/WorkManager/WebView/media/camera/sensors | §30 | stubs | stub | no | none in corpus first screens | no | no | on-demand | — | DEFERRED (no proven target need) |

## F. Real apps (§11/§19/§20/§21/§17/§22/§26/§31)

| Canonical ID | Finding | Provenance | Source | Current HEAD | Reproduced | Real APK | Duplicate | Already Fixed | Needs Fix | Test | Final Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| APP-TELEGRAM | deterministic baseline must be preserved (SHA + 3× + exit 0) | §21/§33 | u011_test_matrix | **PRESERVED (011.3)** — golden restored after DEX-EXC-TAIL regression; final matrix 3/3 `088ea640…` | YES | Telegram v12 12.10.1 | no | yes | no | matrix + BASELINE_MATCH | INTEGRATED |
| APP-WA-ENTRY | WhatsApp L1: 12-DEX app-shell entry chain (Application/Activity delegate creation in secondary DEX index) | 011.2 probe | run/real_whatsapp + logs | unchanged this campaign (audit-only; 12 DEX parse OK, 56K instr) | partial | WhatsApp | no | no | yes | real_whatsapp evidence | CONFIRMED_OPEN (§35.4) |
| APP-SIGNAL-INIT | Signal L2+: stub-heavy androidx/coroutines init exceeds probe window (280 s, no livelock) | 011.2 probe | signal run | unchanged this campaign | partial | Signal 8.24.2 | no | no | maybe (longer window + typed-catch now helps init paths) | — | CONFIRMED_OPEN (§35.5) |
| APP-DOOZ-COMPOSE | ComposeView inflates 0 children (Compose runtime gap) after livelock fix | 011.2 | dooz run log | unchanged (architecture-scale gap) | YES | dooz | no | no | yes (large) | — | BLOCKED (Compose runtime — §35.1) |
| APP-TICTACTOE-LIBGDX | tictactoe blank — libGDX framework dependency | 011.2 matrix | tictactoe run | unchanged | YES | tictactoe | no | no | yes | — | BLOCKED (libGDX backend) |
| APP-GMDICE-L13 | GMDice L12/L13: click→callback→state→second frame; visual correctness now measured honestly | §22 | click reports + oracle | dispatch+state PROVEN; second-frame content = 0 px (runtime views gap GFX-FRAME2-RUNTIMEVIEWS) | YES | gmdice | dup of GFX-FRAME2-RUNTIMEVIEWS | — | — | click_test_report.json | DUPLICATE (tracked via GFX-FRAME2-RUNTIMEVIEWS) |
| APP-SSW-STOPWATCH | ssw: full interaction chain PROVEN (Stop/Lap second frame) | §23 | u0113 evidence | working at HEAD | YES | simplestopwatch | no | yes (011.3) | no | oracle JSON | INTEGRATED |
| APP-CORPUS-DEFAULT | microtimer/unote/chessclock/headingcalc/notes/simplekeyboard/openlauncher fall to default shared screen (entry chain / ARSC obfuscation) | 011.2 matrix | corpus rows | unchanged | YES (default eb16ab5c rows) | corpus apps | no | no | yes | corpus reports | CONFIRMED_OPEN (grouped; §35.9) |
| APP-STOPWATCH-TRUNCATED | muellerma stopwatch = truncated APK (exit 1) — app defect, not engine | 011.2 | corpus row | unchanged | YES | stopwatch(muellerma) | no | n/a | no | — | NOT_REACHABLE (external boundary) |
| APP-TINY-REGISTRY | tinymusicplayer registry SHA stale vs F-Droid current | 011.2 audit M7 | APK_REGISTRY | unchanged (owner action) | YES | tinymusicplayer | no | n/a | no | — | DEFERRED (registry maintenance) |
| APP-WA-MATRIX-DUP | WhatsApp 12-DEX chain (duplicate ID used in two discovery sets) | §31 vs §19 | — | same finding as APP-WA-ENTRY | — | — | yes | — | — | — | DUPLICATE |
| APP-GLES-GAME-DUP | "real game needs GLES" vs GFX-GLES — same evidence-gated item | §16 vs §35 | — | same as GFX-GLES | — | — | yes | — | — | — | DUPLICATE |

## G. Tooling / process (§0/§3/§4/§34/§38)

| Canonical ID | Finding | Provenance | Source | Current HEAD | Reproduced | Real APK | Duplicate | Already Fixed | Needs Fix | Test | Final Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TOOL-HANDOFF-GAPS | status_011_1 TBD placeholder + untracked START_HERE/recovery in 011.1 package | 011.2 audit M1/M2 | status file + git | fixed @ae58a4d/43e024f | YES | — | no | yes | no | git show | FIXED (011.2) |
| TOOL-LOST-SUITE | 121/122 smali semantic fixture suite never integrated — lost work (the §0 failure mode) | **this campaign's §34 verification** | repo+history+12 recovery archives: absent | partially REVIVED as in-repo C++ semantic fixtures (fna 5/5, typed-catch 8/8 incl. the typed-exception class) | YES (fixtures run) | — | no | partial (revival) | no (declared lost + revived in-repo) | fixtures | FIXED (revival) — historical loss documented |
| TOOL-CLAIM-4A39F1B | `4a39f1b`/"176-176" claim absent from repository | §4 directive example | git cat-file + all refs + archives | documented REJECTED evidence | n/a | — | no | n/a | no | RECOVERED_11_1_TO_HEAD_DELTA §2 | NOT_REPRODUCED (claim rejected, preserved) |
| TOOL-URLS-STALE | registry download URLs stale (telegram.org redirect; tinymusicplayer/SHA drift) | 011.2 M7 | APK_REGISTRY | documented; Telegram re-fetched via official URL + SHA-verified | YES | — | no | partial | no (owner) | — | DEFERRED |
| TOOL-M8-SCRIPT-DISAGREE | u011_test_matrix expects corpus/dooz.apk etc. but downloader writes dooztictactoegvariant.apk — official scripts disagree | 011.2 M8 | scripts | worked around via verified symlinks; scripts untouched (behavior-preserving) | YES | — | no | partial | no (owner flag) | — | DEFERRED |
| TOOL-IMG-E2E-SYNTHETIC | §11 demands E2E with REAL APK asset (not synthetic) | directive §11 | exp_graphics_image_e2e | satisfied: real simplestopwatch APK assets (lock/settings/menu PNGs) | YES | ssw | no | yes | no | e2e README | INTEGRATED |

## Roll-up by required states (§6)

- **UNVALIDATED → 0** (every row has HEAD-state evidence this campaign)
- **REPRODUCED** rows: 24 distinct (fixture, matrix, oracle, or run-log evidence)
- **ALREADY_FIXED (earlier campaigns)**: 17
- **FIXED (this campaign)**: DEX-CATCH-TYPED, DEX-THROW-NO-HANDLER, DEX-EXC-PROPAGATE, DEX-EXC-TAIL, GFX-FRAME2-RENDER, GFX-FRAME2-THIS, TOOL-LOST-SUITE (revival)
- **CONFIRMED_OPEN (9)**: RES-OBFUSCATED, IMG-HEAP-MODEL, IMG-VECTOR-NINE, GFX-FRAME2-RUNTIMEVIEWS, APP-WA-ENTRY, APP-SIGNAL-INIT, APP-CORPUS-DEFAULT (grouped)
- **DEFERRED (9)**: DEX-APUT-BOUNDS, DEX-MONITOR-VOLATILE, RES-TYPEDARRAY-THEME, RES-RAWS, IMG-GETDRAWABLE-STUB→(LOW_IMPACT), IMG-BITMAPFACTORY, IMG-SETIMAGE-DISCARD, IMG-FAB, GFX-CANVAS-remainder, GFX-SSW-REFLOW, API-WINDOW-LIFECYCLE, API-MEDIA-CAMERA-SENSORS, APP-TINY-REGISTRY, TOOL-URLS-STALE, TOOL-M8-SCRIPT-DISAGREE (grouped where contiguous)
- **BLOCKED (4)**: GFX-GLES (evidence-gated §16), API-WEBVIEW, APP-DOOZ-COMPOSE, APP-TICTACTOE-LIBGDX
- **NOT_REPRODUCED (2)**: TOOL-CLAIM-4A39F1B (claim rejected), RES-OBFUSCATED-this-run (audited, not re-triggered)
- **NOT_REACHABLE (2)**: APP-STOPWATCH-TRUNCATED (defective APK), API-NETWORK (external boundary)
- **DUPLICATES (3)**: APP-GMDICE-L13→GFX-FRAME2-RUNTIMEVIEWS, APP-WA-MATRIX-DUP→APP-WA-ENTRY, APP-GLES-GAME-DUP→GFX-GLES
