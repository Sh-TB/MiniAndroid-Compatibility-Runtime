# G06–G08 INITIAL AUDIT — FOUNDATION VERIFICATION + CAPABILITY MATRIX

Recorded 2026-09-06 at campaign start. Rule 0.1 vocabulary only.

## 1. Current HEAD

```text
HEAD: 67812290 (main, clean working tree)
origin/main: 67812290 — SYNCED (10 unpushed G04+G05 commits pushed this
session, verified 0 ahead / 0 behind via ls-remote)
Prior-campaign evidence published this session:
  Issue #8 comment (G04+G05 closure) →
  https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/8#issuecomment-5558532580
```

## 2. Current battery at 67812290

31 stages ALL PASS — reproduced after a full sandbox wipe (runtime rebuilt
from scratch; fixtures re-frozen SHA-exact):

| Stage | Result |
|---|---|
| semantic long/cmp/conv 14 · switch parse-neg 25 · pass3 bridge 57 (96/96) | PASS |
| MUTF-8 14/14 · resource-config 48/48 · resource core law 42/42 | PASS |
| resource hostile 18/18 · LinearLayout/MeasureSpec law 24/24 | PASS |
| G04 hostile 24/24 · encoded-value law 18/18 | PASS |
| helloworld_golden (26) · tictactoe_golden (8) | PASS |
| EXT-01 typography 9/9 · EXT-02 interaction 12/12 | PASS |
| density-matrix oracle 11/11 · corpus fetch+runs 3/3 | PASS |

## 3–7. G01–G05 status at current HEAD (frozen-hash reproduction)

| Layer | Evidence at 67812290 | Status |
|---|---|---|
| G01 typography | EXT-01 golden 9/9; 3-run byte-identical `142238fd92b69e11` (frozen G48 hash) | verified |
| G02 interaction | EXT-02 long-press 12/12; frame_001 `e242ac1e9c8cc224` (frozen GOLDEN-02 hash); 500ms law + UP suppression intact | verified |
| G03 resources | 48/48 config · 42/42 core · 18/18 hostile · 18/18 encoded-value · 96/96 bridge | verified |
| G04 drawable/image | density oracle 11/11; 3-run byte-identical `351340a7a92e645c` (frozen); hostile 24/24 | verified |
| G05 layout/measure | LinearLayout/MeasureSpec law 24/24; helloworld 26/26; tictactoe 8/8; corpus 3/3 | verified |

## 8–9. Residuals found at current HEAD

| ID | Finding | Disposition |
|---|---|---|
| FIND-G06AUDIT-001 | `build/resource_trace` is a separate make target; after a clean checkout the battery's density-oracle stage (27) fails on the missing binary until `make resource_trace` runs — an environment/restore gap, not a runtime defect (pixel-law and determinism checks all PASS once built) | NON-BLOCKING — battery hygiene fix queued: battery now builds resource_trace itself |
| FIND-G06AUDIT-002 | `run_test_battery.sh` used `--skip-build` in the prior session's evidence; rebuild-from-clean now proven green (this audit) | NON-BLOCKING — evidence, no change needed |

No G01–G05 correctness defects found. None block G06–G08.

## 10. G06–G08 capability matrix (source audit at 67812290)

### G06 — state + input + interaction

| Capability | Present? | Anchor |
|---|---|---|
| hit_test(x,y) → topmost touch target (CLICKABLE or LONG_CLICKABLE law, visibility gating) | YES | view_renderer.cpp L583–608 |
| click dispatch through real DEX (dispatch_click / by-class) | YES | dalvik_engine.cpp |
| long-press: 500ms law, UP-click suppression (mHasPerformedLongPress) | YES (GOLDEN-02) | execution_engine.cpp stage_long_press |
| ViewNode state fields: clickable/enabled/visibility V0/I4/G8 | fields exist | android_shadows.h L547–549 |
| **generic MotionEvent pipeline (DOWN→MOVE→UP→CANCEL)** | **NO — tap = direct performClick, no DOWN first** | FIND-G06-001 |
| **pressed state (PFLAG_PREPRESSED@TAP_TIMEOUT → setPressed → drawableStateChanged)** | **NO** | FIND-G06-002 |
| **enabled gating in touch pipeline (disabled ⇒ onTouchEvent returns false)** | **NO — hit_test ignores enabled** | FIND-G06-003 |
| **state-list drawable switching (input → state → render)** | **NO** | FIND-G06-002 |
| focus / focusable / selected state machine | **NO** | FIND-G06-004 |

### G07 — lifecycle + main thread + frames

| Capability | Present? | Anchor |
|---|---|---|
| onCreate via real DEX interpreter; pipeline state machine CREATED→…→FRAME_RENDERED→COMPLETED with transition log | YES | application_runtime.cpp L770+, execution_engine.cpp |
| Handler queue + virtual clock; postDelayed; drain points; --frames advance; Runnable run() via DEX | YES (EXP-086/088/090) | execution_engine.cpp L569–600 |
| **runtime-driven onPause/onStop/onDestroy (finish() cascade)** | **NO — stubs only log; ActivityShadow.finish() sets DESTROYED, runtime never reacts** | FIND-G07-001 |
| **foreground/background transitions on Activity switch** | **NO** | FIND-G07-001 |
| explicit PROCESS_CREATED→…→DESTROYED lifecycle record | **NO** | FIND-G07-002 |
| sleep-based sync used? | NO (virtual Looper clock — correct model already) | — |

### G08 — multi-Activity + Intent

| Capability | Present? | Anchor |
|---|---|---|
| IntentShadow: setClass/setClassName/setComponent, putExtra/get…Extra (string/int/bool), flags, package | YES | android_shadows.h L330–380 |
| startActivity records pending intent | YES | android_shadows.cpp L1030–1053 |
| **pending-intent consumption → second Activity instantiation** | **NO — has_pending_intent()/take_pending_intent_target_class() are DEAD CODE (zero callers)** | FIND-G08-001 |
| **Activity stack (push/pop), back navigation, finish()-driven pop** | **NO** | FIND-G08-002 |
| **A PAUSED → B CREATED/STARTED/RESUMED transition with exact callback order** | **NO** | FIND-G08-003 |
| **result delivery (setResult / startActivityForResult / onActivityResult-before-onResume law)** | **NO** | FIND-G08-004 |

## 11. AOSP laws required for G06–G08 (android-14.0.0_r2)

| Law | Source anchor |
|---|---|
| `clickable = (CLICKABLE|LONG_CLICKABLE) && ENABLED`; disabled view's onTouchEvent returns false (no press, no click) | View.java onTouchEvent |
| Tap: DOWN posts CheckForTap @ TAP_TIMEOUT(100ms) → setPressed(true) → drawableStateChanged; UP posts PerformClick runnable (state updates run before click callback) | View.java onTouchEvent + PerformClick |
| Long-press: CheckForLongPress @ LONG_PRESS_TIMEOUT(500ms); performed ⇒ UP suppressed | View.java checkForLongClick (already ported GOLDEN-02) |
| CANCEL: setPressed(false) + removeTapCallback + removeLongPressCallback | View.java onTouchEvent ACTION_CANCEL |
| drawableStateChanged → Drawable.setState(PRESSED_ENABLED_STATE_SET / EMPTY_STATE_SET) | View.java + DrawableContainer |
| ViewGroup dispatchTouchEvent: onInterceptTouchEvent, reverse-order child dispatch | ViewGroup.java dispatchTouchEvent |
| Choreographer/Handler frame law: one frame = drain due tasks then draw | Choreographer.doFrame; Handler Looper |
| ActivityThread: performLaunchActivity(onCreate)→handleResumeActivity; handlePauseActivity; handleStopActivity; handleDestroyActivity; finish() drives destroy | ActivityThread.java |
| Launch order law: A.onPause → B.onCreate → B.onStart → B.onResume → A.onStop | ActivityThread + ActivityTestCase contracts |
| onActivityResult is delivered immediately BEFORE onResume on re-start | Activity.java.onActivityResult doc + Instrumentation |
| finish() cascade: PAUSED→STOPPED→DESTROYED; back == finish of top | Activity.finish + ActivityThread.handleDestroyActivity |
| setResult/Intent result roundtrip via ActivityRecord | Activity.java setResult/getCallingActivity |

## 12. External APK corpus plan

Frozen (kept): EXT-01 HelloWorldSelfAware `009b4671…cc41` · EXT-02..04 corpus
(SimpleStopwatch/gmdice/MicroTimer, hash-verified) · EXT-05 KISS `da6ab0b1…98c9`
· EXT-06 Fossify Notes `5a56e0e3…bced` (NOT APPLICABLE — Compose) · EXT-07
Markor `3f9f260d…84b9` · EXT-FIX density-matrix (per-build SHA).

New for G06–G08 (frozen with URL/version/package/SHA-256/SDK/capability):

| ID | Candidate | Role | Note |
|---|---|---|---|
| EXT-08 | org.connectbot (F-Droid, classic Views) | real multi-Activity (HostList→Console), explicit Intents, back | fetch-attempt recorded; if unreachable ⇒ documented BLOCKED fetch |
| G06-FIX | project fixture via REAL toolchain (aapt2 2.20-14304508 + ECJ + D8 — same path as density-matrix) | tap/long-press/cancel, enabled/disabled, state-list pressed color, focus | real DEX click handlers; no AppCompat |
| G08-FIX | project fixture via REAL toolchain | 2 Activities, explicit Intent, string/int extras, setResult+finish, startActivityForResult/onActivityResult, back | real DEX bytecode navigation — no screen-swapping shortcut |

Corpus honesty rule unchanged: fixtures are real APKs built by the real
Android toolchain (provenance = build log + in-repo sources); the RUNTIME
contains zero fixture-specific branches.

## 13. Proposed gate structure (battery expansion)

```
[G01] typography golden · [G02] interaction golden · [G03] resource battery
[G04] density oracle   · [G05] measure/weight law  · [G06] input pipeline law
      + EXT tap golden (input→state→render)
[G07] lifecycle law battery (order, finish cascade, frame boundary, replay)
[G08] multi-activity law battery (intent resolution, transition order,
      extras, result, back)
[cross] interaction→render + A→B→back goldens · [hostile] input/lifecycle/
      intent/runtime · [replay] 3-run determinism · [corpus] full corpus
```

## 14. Campaign implementation order (focused commits)

C1 G06 input pipeline law + enabled gating + pressed/state-list
C2 G06 fixtures + tap golden (3-run determinism)
C3 G07 lifecycle state machine + finish cascade + frame-boundary law
C4 G08 Activity stack + Intent launch + transitions + result/back
C5 G08 navigation golden + result golden
C6 hostile battery extension (input/lifecycle/intent)
C7 battery named gates + regression run + final report A–P + GitHub evidence
