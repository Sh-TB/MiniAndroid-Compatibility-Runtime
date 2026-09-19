# S62+ — Open-Source APK Spotlight: 2 NEW source-first builds executed; F-110 lever implemented (57.8×); 6 generic laws

Date: 2026-09-19 (S62+ continuation). All runs on this machine (2 CPU).
RECON ground truth at session start: local HEAD b0271429 (S58) was BEHIND
origin/main; fast-forwarded to 7cf1f02f (S62-PUSH-VERIFY) before any work.
No new campaign/branch/roadmap; mission = increase the count of REAL
open-source APKs executed launch→UI→(input→state→render).

## 1. NEW open-source APKs — source-first, built from source, executed

### 1a. anuto (ch.logixisland.anuto) — GPLv2, Java, zero external deps

```text
Repository      https://github.com/mjaun/android-anuto @ 33ed89e382c8e05c83ed4e92a00871107144a437
Build           aapt2 compile+link (res/ + binary manifest) → ECJ -source 8
                (android-34 stubs) → D8 → deterministic zip
APK SHA256      8794573d9d82bde2ee1ccb47f1ad15c4b426fd3cdf00dec77645cecf6452a444
Build input fix manifest lacked package= (AGP8 namespace-in-gradle style);
                staged copy got package="ch.logixisland.anuto" from build.gradle
Run             ./miniandroid run --execution-mode real-dalvik --max-seconds 180
Result          rc=0; REAL AnutoApplication bound (onCreate OK ins=14751);
                GameActivity.onCreate ran real DEX chain (theme, setContentView,
                GameLoop.start, EntityStore/Enemy/EnemyProperties, map load);
                GameView (custom <view class=...>) CONSTRUCTED via the G11
                (Context,AttributeSet) ctor law; REAL GameView.onDraw dispatched
                → [C013-ONDRAW] dispatched=YES ops=2 → app-driven frame
                (drawColor BLACK — app's own background law); 2,073,600 non-white
                px. Screenshot: anuto_frame0_after_onDraw.png SHA 11a38a5a…
Input           --tap 540,960 → target=774 (GameView) → onTouch DOWN dispatched
                to REAL app DEX (consumed=true — app code returns true);
                UP dispatched (app returns false for UP) → screenToGame →
                TowerSelector.selectTowerAt executed in real DEX.
3-run det       11a38a5aeeff45a6 ×3
L-level         L5 PROVEN (real UI: app-defined View subclass drawing through
                real DEX onDraw into the framebuffer) + input→handler→state
                dispatched. Honest: NOT L6-visible — sprites need the
                canvas bitmap-draw family (recorded next frontier); frame
                diff after tap = 0 because selection ink lives in bitmaps.
```

### 1b. OpenSudoku (cz.romario.opensudoku) — GPLv3, Java, zero external deps

```text
Repository      https://github.com/romario333/opensudoku @ d19146495f669ce34ba929b6eff5cc4a7be595cf
Build           aapt2 compile+link → ECJ → D8 (Ant layout src/+res/+manifest)
APK SHA256      712b4a41f28f9e67d706d1b3771d716ef97dcf4d36823a0bf3356419f1b16d5b
Run             ./miniandroid run --execution-mode real-dalvik --max-seconds 60
Result          rc=0, Errors: 0; FolderListActivity (ListActivity) real onCreate;
                real view tree: LinearLayout root → ListView 1080x1876 →
                Button text="Get more puzzles online" at layout position;
                2,029,440 non-white px. App's REAL SQLite chain ran as DEX
                (DatabaseHelper.onCreate → SQLiteDatabase.execSQL chain,
                SQLiteQueryBuilder.getFolderList). Screenshot:
                opensudoku_frame0_folderlist.png SHA a4b96b95…
Input           --click-count 3 → 3/3 CLICK dispatched to REAL app DEX
                listener FolderListActivity$1 (anonymous inner-class
                OnClickListener; UI-EVENT result=DISPATCHED). Handler body =
                startActivity(ACTION_VIEW http…) — honest no-op in a headless
                runtime (external-intent law), so diff_px=0.
3-run det       11671b9c439b2e10 ×3
L-level         L5 PROVEN (real UI + visible text rendered) + input
                dispatched to real handlers. Honest: ListView rows empty
                (SQLite query data path = typed-zero), no pixel-transition
                state change from the external-intent button.
```

## 2. F-110 lever IMPLEMENTED + 5 companion laws — measured A/B

### F-110a: result-snapshot deferral (the measured 57.8× lever)

ROOT CAUSE (gprof on a 25s anuto startup run, 387,639,677
pair<string,string> copies = __do_uninit_copy #3 flat-profile entry):
`execute_method_internal` assigned `result.call_stack = call_stack_;
result.heap = heap_;` at EVERY method exit — a full deep copy of the
entire heap + call stack — and execute_method_internal is RECURSIVE, so
each of the N nested exits performed an O(heap) copy that its parent
immediately overwrote. O(N × heap_size) quadratic.

FIX: outermost-only snapshot (`if (call_stack_.empty())`). The outermost
exit is the last write in every nesting chain → final result content
byte-identical; nested copies removed.

A/B (same APK, same 25s wall budget, default env):

| metric | before | after F-110a |
|---|---|---|
| instructions executed | 128,076 | 7,400,000+ (PROGRESS counter) |
| rate | ~5.1K/s | ~296K/s (**57.8×**) |
| RSS at budget stop | 41 MB | 335 MB (reached far deeper) |

This is the F-110 lever S62 registered as "per-invoke constants +
DalvikValue copy cost" — the gprof root cause turned out to be the
result-snapshot copy amplifying every register/field string copy. Honest:
57.8× is THIS workload's startup face (quadratic → linear); dooz v23
composition (627 cold class inits, ~700K instructions) benefits from the
same removal but its own frontier re-measurement is future work.

### F-110b: THREAD-SLEEP YIELD LAW (R-NEW-345 companion)

Thread.sleep(ms) inside a run-to-completion drained thread body
(park_drain_last_depth_ ≥ 1) is a deterministic yield point: the virtual
clock advances (M3 FIX-M3-014 law, same as SystemClock.sleep) and the
body's frame chain suspends at the drain boundary. Upstream law: sleep
suspends THIS thread; the app's main thread must proceed. First hit:
anuto GameLoop.run — while(running){cycle; sleep(TICK)} spun to the 50K
loop-visit cap and the F084 deferred VirtualMachineError destroyed
onCreate (APP BOUNDARY unwind). Evidence: [SLEEP-YIELD] ... at
GameLoop.run in the l5 run.

### F-110c: ArrayList insert/remove laws (drain law)

The heap-backed array[N] convention handled add(E)/get/size/isEmpty/clear
but had NO remove(int) and treated add(int,E) as add(E) (the 3-arg
overload's index was taken for the element). Upstream java.util.ArrayList
semantics implemented: add(int,E) shift-right insert; remove(int)
shift-left remove returning the removed element + IndexOutOfBoundsException
(deferred, containment law) on OOB; remove(Object) first-occurrence
boolean. First hit: anuto MessageQueue.processMessages —
`while(!isEmpty && due) { remove(0); execute(); }` could never drain
(head never left the queue → infinite loop + 2.1GB heap balloon from
re-executed load messages).

### F-110d: CURRENT-THREAD IDENTITY LAW

Thread.currentThread() returned the main singleton unconditionally. AOSP:
it returns the thread EXECUTING the code. While a drained body runs, the
engine now sets active_drained_thread_ (save/restore, nested-safe) and
currentThread() returns that heap object. First hit: anuto
GameLoop.isThreadChangeNeeded gates every GameEngine.post through
`Thread.currentThread() != mGameThread` — with the main singleton
returned, loadMap re-posted itself forever and the queue never drained.
Evidence: [THREAD-ID] currentThread -> obj=785 (drained-body identity).

### F-110e: touch-target law + MotionEvent family

- view_touchable now includes touch_listener_id: AOSP
  View.dispatchTouchEvent runs the mOnTouchListener gate BEFORE
  clickability; a plain non-clickable view with setOnTouchListener IS a
  touch target (anuto GameView was tap-dead: target=0 at its own coords).
- DOWN/UP dispatch to OnTouchListener.onTouch(View,MotionEvent)Z via the
  new dispatch_touch_listener; consumed = the listener's boolean return;
  a consumed DOWN owns the gesture (no pressed/long-press/PerformClick —
  upstream law).
- MotionEvent heap materialization (__action__/__x__/__y__) + bridge
  getters getAction/getActionMasked/getX/getY.
- Framework static INT constant table (sget law): MotionEvent.ACTION_DOWN
  =0, UP=1, MOVE=2, CANCEL=3, OUTSIDE=4, POINTER_DOWN=5, POINTER_UP=6,
  MASK=255 (AOSP values; non-zero constants could never compare true via
  the typed-zero default).

Evidence (tap3 run): [UI-EVENT] event=TOUCH action=0 view_object=774
listener_class=Lch/logixisland/anuto/view/game/GameView;
result=DISPATCHED consumed=true → the app's own onTouch ran, called
screenToGame + TowerSelector.selectTowerAt in real DEX, and returned true
(DOWN); UP dispatched with the app's false return.

## 3. Two more generic laws from the build+inflate faces

### F-111: LayoutInflater `<view class=...>` namespace law

AOSP LayoutInflater.createViewFromTag reads the custom-view class via
getAttributeValue(null, "class") — NO namespace. The AXML parser gives
no-namespace attributes ns=""; the inflater's el.attr("class") defaulted
to ns="android" and MISSED — `<view class="ch.logixisland.anuto.view.game.GameView">`
degraded to a generic Landroid/view/View; and the G11 DEX-constructor law
never fired (the game board was a hollow placeholder). Fix: namespace-
agnostic lookup (attr(n, "")). Reused unchanged by OpenSudoku's build
(no custom views there) and any future app with the `<view class>` form.

### F-112: manifest Application buildClassName law

AOSP PackageParser.buildClassName: leading '.' joins the manifest package;
a name with no dot also joins; otherwise as-is. application_name was
taken raw and its descriptor normalizer turned ".AnutoApplication" into
"L/AnutoApplication;" → "not present in DEX" → default Application
fallback → the app's real Application.onCreate never ran (no sInstance;
the custom-view ctor depending on it would NPE). The same three-branch law
already existed for the main activity name; now applied to <application>
android:name too. Evidence: [R341-APP] instantiating Application
Lch/logixisland/anuto/AnutoApplication; ... onCreate OK ins=14751.

## 4. Regression + determinism

- Battery: BATTERY GATE ALL PASS (96 stages) at this HEAD, including
  helloworld_golden 26 checks, tictactoe_golden, G06 tap 3-run
  determinism, G07 lifecycle, G08 navigation, EXT-01/EXT-02 external
  goldens. (First battery run in this fresh environment failed 32
  fixture-build stages — root cause: /home/z/my-project/tools/ was NOT
  bootstrapped in this container; restored via the documented
  scripts/build/bootstrap_toolchain.sh, after which all stages PASS.
  No engine-caused regression. EXT fixtures re-fetched from the
  documented frozen URLs: APK SHA 009b4671… matches the record.)
- 3-run determinism: anuto 11a38a5aeeff45a6 ×3; opensudoku
  11671b9c439b2e10 ×3.

## 5. Run commands (reproduce)

```text
# build APKs (source-first; tools bootstrapped into ./tools)
TOOLS=$PWD/tools bash scripts/build/build_fixture_apk.sh \
    <staged-src-dir> <out.apk>
# execute
./miniandroid/build/miniandroid run --execution-mode real-dalvik \
    --max-seconds 180 [-o OUT] [--tap 540,960 | --click-count 3] APK
```

## 6. Honest frontier (recorded, not hidden)

1. Canvas bitmap-draw family (decodeResource→Bitmap→Matrix→drawBitmap
   replay): anuto sprites render as background-only today; its selection
   ink/UI fragments also need platform-<fragment> inflation. Both are the
   recorded next generic frontiers for L6-visible on custom-view games.
2. App-SQLite data path (OpenSudoku ListView rows) — the execSQL chain
   runs but query results are typed-zero; a data-backed adapter would
   lift rows to visible state.
3. dooz v23 composition re-measurement under F-110a (the 57.8× lever
   changes the S62 composition-volume budget estimate; not re-run yet).
