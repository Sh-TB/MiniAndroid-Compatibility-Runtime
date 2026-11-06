# ISSUE 524: Coder 3 | Achievement 16 — S157: four corpus PARTIALs re-judged (simplestopwatch + simplekeyboard now SUCCESS EXIT=0), the #523 filed gaps CLOSED (opencalculator keypad taps DISPATCH to real buttons; microtimer clicks land with visual deltas), 5 new AOSP layout laws, bouncy golden BYTE-EXACT — 33 counted items

# Coder 3 | Achievement 16 — S157: four corpus PARTIALs re-judged (simplestopwatch + simplekeyboard now SUCCESS EXIT=0), the #523 filed gaps CLOSED (opencalculator keypad taps DISPATCH to real buttons; microtimer clicks land with visual deltas), 5 new AOSP layout laws, bouncy golden BYTE-EXACT — 33 counted items

> Chain: #508 (A11) · #511 (A12) · #513 (A13) · #516 (A14) · #523 (A15) · case files #401–#424.
> Governing law: **no fake success** — every verdict below re-runnable with the exact recipes in §0.
> Session start state: S156 (`d50dca1d2189830f` aggregate + 5 pins EXACT) re-verified before any change.

---

## 0) VERIFICATION RECIPES (one command each; pass/fail stated)

**R1 — simplestopwatch_26 (was PARTIAL, now SUCCESS):**
```bash
./miniandroid/build/miniandroid run --execution-mode real-dalvik --frames 6 \
  --frame-delay 300 --width 1080 --height 1920 \
  -o /tmp/r1 upload/canonical_apks_restored/omegacentauri.mobi.simplestopwatch_26.apk
```
PASS = `report.md` says **SUCCESS** ✅, process EXIT=0, and the log carries
`[S157-CONTENT-FRAME] materialized android.R.id.content node=…`. Falsifier:
any `APP BOUNDARY unwind` from `ShowTime.setTheme`.

**R2 — simplekeyboard_145 (was PARTIAL, now SUCCESS):**
```bash
./miniandroid/build/miniandroid run --execution-mode real-dalvik --frames 6 \
  --frame-delay 300 --width 1080 --height 1920 \
  -o /tmp/r2 upload/canonical_apks_restored/rkr.simplekeyboard.inputmethod_145.apk
```
PASS = **SUCCESS** ✅ EXIT=0 with
`[S157-LISTVIEW] getListView MATERIALIZED` + `[S157-DECOR]` window-chain lines.
Falsifier: `ViewParent.getParent on null` NPE at `SettingsActivity.onCreate`.

**R3 — opencalculator tap dispatch (the #523 §4.4 item-31 gap):**
```bash
./miniandroid/build/miniandroid run --execution-mode real-dalvik --frames 12 \
  --frame-delay 300 --width 1080 --height 1920 \
  --tap 130,1400@8 --tap 540,1400@9 --tap 950,1400@10 \
  -o /tmp/r3 upload/opencalculator_53.apk
```
PASS = three `[F117-TAP] … target=898|900|901` lines (the REAL keypad Buttons
"1","3","−"), each followed by
`[G06-TOKEN] {"callback":"PerformClick","click_dispatched":true,…}` and
`[UI-EVENT] event=XML_CLICK handler=keyDigitPadMappingToDisplay … result=DISPATCHED`.
Falsifier: any `target=762` (the SlidingUpPanelLayout fallback) or
`size=(0x0)` in the `[EXP092-RENDER]` dump for a keypad Button.

**R4 — microtimer click chain (the #523 §4.4 item-32 gap):**
```bash
./miniandroid/build/miniandroid run --execution-mode real-dalvik --frames 6 \
  --frame-delay 300 --width 1080 --height 1920 \
  --tap 200,1700@3 --tap 540,1700@4 \
  -o /tmp/r4 upload/canonical_apks/dubrowgn.microtimer_8.apk
```
PASS = `[F117-TAP] … target=142|143` +
`[UI-EVENT] event=CLICK … result=DISPATCHED listener=Lk/d;` +
`>1` distinct frame SHA-256s in `frames/` (the filed "zero visual delta
across 25 frames" is gone — this probe shows 3 distinct states).

**R5 — the regression gate (bouncy golden must not move):**
```bash
./miniandroid/build/miniandroid run --execution-mode real-dalvik --frames 30 \
  --frame-delay 200 --width 1080 --height 1920 \
  --tap 519,609@15 --tap 540,1600@20 --tap 540,1600@21 \
  -o /tmp/r5 work/apks/bouncy_43.apk
(cd /tmp/r5/frames && sha256sum frame_*.png | sha256sum)
```
PASS = aggregate `d50dca1d2189830f` (the S139/S156 canonical), EXIT=0.
**Measured this session: EXACT** — all five S157 render-path laws are
render-neutral for the pinball tree.

**R6 — tictactoe_3 (improved, honestly bounded):** same probe as §1.3 —
report flips to **SUCCESS** status (7 frames rendered; the earlier
`GLSurfaceView20` NoSuchMethodException chain is gone); EXIT=1 remains and is
honest (§5).

---

## 1) THE FOUR CORPUS RE-JUDGEMENTS (root cause → law → file/function route)

### 1.1 simplestopwatch_26 — PARTIAL → **SUCCESS EXIT=0**

- **Symptom:** `ShowTime.setTheme pc=134` NPE'd
  (`ViewGroup.getChildAt on null`) → APP BOUNDARY unwind after a rendered
  first frame.
- **Root cause (bytecode-level):** the app does
  `(ViewGroup) findViewById(android.R.id.content)` and dereferences it. The
  ActivityShadow findViewById law searched the ViewShadow tree and answered
  `handled_null()` — PhoneWindow's content-parent frame DID NOT EXIST in the
  shadow tree, so the "never null on a live window" AOSP contract was
  violated.
- **New law S157-A (one-stable content frame):**
  `ViewShadow::ensure_content_frame(uint32_t app_root_id)` —
  `src/framework/android_shadows.{h,cpp}`. Three-step resolution
  (remembered identity → existing 0x01020002 node parenting the root →
  materialize `FrameLayout` with `android_view_id=0x01020002`, adopt the app
  root as child 0, preserve the old window edge). Render-safe by
  construction: `effective_content_root_()` keeps answering
  `content_view_id_`, so down-walks (render/tap) never traverse the new
  ancestor — only `getParent()` up-walks complete, exactly as AOSP.
- **New law S157-B (Activity-side delegation):**
  `ActivityShadow.dispatch findViewById` — `src/framework/android_shadows.cpp`
  (after the registry search) delegates `target_id==0x01020002` to the same
  content-frame law instead of `handled_null()`.

### 1.2 simplekeyboard_145 — PARTIAL → **SUCCESS EXIT=0**

- **Symptom:** `SettingsActivity.onCreate pc=17` NPE'd
  (`ViewParent.getParent on null`) — the app walks
  `getListView().getParent().getParent()` to mount its preference list.
- **Root cause:** `PreferenceActivity`/`ListActivity` had **no
  `getListView` handler** — the ancestry re-dispatch
  (`[S71-ANCESTRY] … for .getListView`) answered null; and the framework-
  boundary onCreate dispatch (`[F-NEW-471-RES-GAP]`) never inflates
  `list_content`, so no ListView existed at `android.R.id.list`.
- **New law S157-C (getListView contract):** `ActivityShadow.dispatch
  getListView` — ONE stable ListView node per activity instance
  (`activity_list_view_nodes_` map), mounted under the content frame at
  `android.R.id.list` (0x0102000b), real runtime class
  `Landroid/widget/ListView;`. Works even when `content_view_id_==0`
  (framework-boundary onCreate) because S157-A now materializes the
  frame+DecorView chain with a 0 root.
- **New law S157-D (window-chain completion):** the content frame is never
  an orphan — when it has no parent, a DecorView stand-in (`FrameLayout`,
  cast-safe) is materialized above it (AOSP PhoneWindow law: DecorView →
  mContentParent → content view).

### 1.3 tictactoe_3 — FAILURE → **SUCCESS status** (bounded, §5)

- **Symptom:** `AndroidGraphics.preserveEGLContextOnPause` reflected
  `GLSurfaceView20.setPreserveEGLContextOnPause` → `NoSuchMethodException`
  (F-NEW-219) → the app's catch path called `Gdx.app.log` on a null
  `Gdx.app` → NPE → APP BOUNDARY unwind.
- **Root cause:** the F-NEW-219 DEX walk stops at the first framework
  superclass (`Landroid/opengl/GLSurfaceView;` — not in the app DEX), so a
  method the platform shadow implements was reported absent.
- **New law S157-E (reflect-family):**
  `ShadowRegistry::class_implements_method(cls, method)` +
  a shadow-claims walk in the F-NEW-219 NOT-RESOLVED arm —
  `src/framework/shadow_registry.h`, `src/dex/dalvik_engine.cpp`. A hit mints
  the Method record; `Method.invoke` then dispatches through the normal
  shadow path (GLSurfaceViewShadow stores `glPreserve`). Evidence line:
  `[S157-REFLECT-FAMILY] getMethod …GLSurfaceView20;.setPreserveEGLContextOnPause resolved via shadow family of Landroid/opengl/GLSurfaceView;`.
- **Result:** report = SUCCESS, 7 frames rendered. The remaining EXIT=1 is
  the F-016 honesty law (one uncaught exception past app frames) — §5.

### 1.4 muellerma stopwatch_6 — PARTIAL, re-classed SERVICE-ONLY (filed)

- **Root cause (not an engine bug):** the APK manifest declares **NO
  activity and no launcher intent-filter** — components are
  `StopwatchApp` (Application), `StopwatchService` (foreground service),
  `StopwatchTile` (TileService), androidx.startup provider. There is no
  window to render by design; `final_state=PROCESS_CREATED` is the correct
  boot outcome for a launcher-style law.
- **Filed follow-up:** a "no-launcher-activity boot law" (drive
  Application → Service.onStartCommand → TileService.onStartListening/onClick
  contracts; treat the foreground NOTIFICATION as the authoritative app
  content) is the S158 candidate. Not faked as SUCCESS.

---

## 2) THE #523 FILED INTERACTION GAPS — BOTH CLOSED

### 2.1 opencalculator v53 (item 31: "keypad renders but coordinate taps don't dispatch")

- **Root cause (three layers, all measured):**
  1. `ContentFrameLayout → ConstraintLayout` children carry match-constraint
     sizes (0dp) → 0x0 boxes cascaded through
     `SlidingUpPanelLayout → TableLayout → TableRow → every Button`
     (`[EXP092-RENDER] size=(0x0)` for all 27 keypad buttons).
  2. The engine had **no TableLayout/TableRow layout law**.
  3. The draw walk computed real boxes but wrote them nowhere —
     `TouchDispatcher::node_at` rejected every button at the 0x0 containment
     test → `target=762` (panel fallback) for every tap.
- **New laws:**
  - **S157-F (un-measured child fill, measured path):** a child with no
    real measure result is resolved by its LayoutParams against the parent's
    box (MATCH/match-constraint FILL, WRAP_CONTENT measures content) —
    `src/runtime/execution_engine.cpp` draw-walk measured push.
  - **S157-G (ConstraintLayout MatchConstraint, heuristic path):** 0dp
    children resolve to the parent's inner box.
  - **S157-H (TableLayout law):** rows split the table's inner height
    equally (keypad contract).
  - **S157-I (TableRow law):** cells split the row width equally
    (stretchAllColumns law — matches the rendered ~259/225px cells).
  - **S157-J (hit-box sync):** the draw pass syncs the computed absolute box
    back into the ViewShadow node when the node carries no measured geometry
    (AOSP performTraversals: touch targets are the laid-out views, never
    un-measured placeholders) — idempotent per frame, render-neutral.
- **Result (R3):** buttons now measure 259x255/256 at their grid slots
  (`[EXP092-RENDER] node=894 … size=(259x256)`); taps hit the REAL buttons
  (898="1", 900="3", 901="−") with `click_dispatched:true` ×3 and the app's
  own XML handler `keyDigitPadMappingToDisplay` DISPATCHED.

### 2.2 microtimer v8 (item 32: "listeners register yet taps produce ZERO visual delta")

- **Re-probe with S157 laws:** `[F117-TAP] target=142|143` →
  `[UI-EVENT] event=CLICK … result=DISPATCHED listener=Lk/d;` ×2 →
  **3 distinct frame SHA-256s** across the 6-frame probe (the byte-identical
  streak is gone). The gap's first half (hit-test) is closed by S157-J; the
  observed display refresh now shows real deltas.

---

## 3) REGRESSION + DETERMINISM GATES

- **R5 bouncy golden:** aggregate `d50dca1d2189830f` **EXACT** on the new
  binary (EXIT=0). All five S157 laws are render-neutral for the pinball.
- **S139 re-verification at session start (before any change):** canonical
  30-frame recipe ×3 — all three runs EXIT=0/SUCCESS with the frame-set
  aggregate `d50dca1d2189830f` ×3 (byte-identical across runs); the 29-native
  dlsym census re-confirmed (World/Body/Fixture/Shape/RevoluteJoint family
  through the APK's OWN `libgdx-box2d.so`).

## 4) THE 33-ITEM SESSION INVENTORY

| # | item | verdict |
|---|------|---------|
| 1 | Session-start state re-verified (git tree 12,401 paths, build, PAT) | VERIFIED |
| 2 | S139 canonical ×3 re-run, aggregate `d50dca1d…` ×3 byte-exact | EXACT |
| 3 | 29-distinct-native dlsym census re-confirmed | VERIFIED |
| 4 | simplestopwatch root cause: findViewById(android.R.id.content) null | ROOT-CAUSED |
| 5 | S157-A content-frame law (`ViewShadow::ensure_content_frame`) | IMPLEMENTED |
| 6 | S157-B Activity findViewById 0x01020002 delegation | IMPLEMENTED |
| 7 | simplestopwatch_26 FAILURE → **SUCCESS EXIT=0** | VERIFIED |
| 8 | simplekeyboard root cause: getListView null (no law) | ROOT-CAUSED |
| 9 | S157-C getListView law (stable ListView @android.R.id.list) | IMPLEMENTED |
| 10 | S157-D window-chain completion (DecorView stand-in) | IMPLEMENTED |
| 11 | S157-C2 getListView with 0 content root (framework-boundary onCreate) | IMPLEMENTED |
| 12 | simplekeyboard_145 FAILURE → **SUCCESS EXIT=0** | VERIFIED |
| 13 | tictactoe root cause: F-NEW-219 DEX walk stops at framework superclass | ROOT-CAUSED |
| 14 | S157-E reflect-family law (ShadowRegistry::class_implements_method + walk) | IMPLEMENTED |
| 15 | tictactoe_3 FAILURE → SUCCESS status, 7 frames (bounded, §5) | VERIFIED |
| 16 | tictactoe filed remainder: libgdx.so dlopen SIGSEGV + AssetManager.load null-string NPE | FILED |
| 17 | muellerma stopwatch_6 re-classed SERVICE-ONLY (no activity in manifest) | FILED w/ component map |
| 18 | opencalculator root cause: 0x0 cascade (ConstraintLayout + Table/TableRow) | ROOT-CAUSED |
| 19 | S157-F un-measured child fill (measured path) | IMPLEMENTED |
| 20 | S157-G ConstraintLayout MatchConstraint (heuristic path) | IMPLEMENTED |
| 21 | S157-H TableLayout equal-row law | IMPLEMENTED |
| 22 | S157-I TableRow equal-cell law | IMPLEMENTED |
| 23 | S157-J hit-box sync (render box → node → hit-test) | IMPLEMENTED |
| 24 | opencalculator taps → REAL buttons 898/900/901, click_dispatched ×3 | VERIFIED |
| 25 | opencalculator XML_CLICK keyDigitPadMappingToDisplay DISPATCHED (#523 item-31 CLOSED) | VERIFIED |
| 26 | opencalculator filed remainder: x/d.onLayout NPE (Lx/d;.r on null) + G1/d.g Pattern.matcher(null) — display text not yet mutated | FILED |
| 27 | microtimer re-probe: hit-test + 10 real listeners re-confirmed | VERIFIED |
| 28 | microtimer CLICK DISPATCHED (Lk/d) ×2 + 3 distinct frame SHAs (#523 item-32 CLOSED) | VERIFIED |
| 29 | R5 regression gate: bouncy golden `d50dca1d…` EXACT on the new binary | EXACT |
| 30 | Corpus re-judgement table updated (4 PARTIAL rows re-tested with full recipes) | DONE |
| 31 | `p2_census.py` region-diff event tool reused across the probes | DONE |
| 32 | Dashboard #492 PATCHed (chain, statistics, per-app %) | DONE |
| 33 | No fake success: §5 lists everything this session does NOT claim | STATED |

## 5) WHAT THIS ACHIEVEMENT DOES NOT CLAIM

- **tictactoe_3 is not claimed full-playable.** The report says SUCCESS and
  the boot chain is clean, but EXIT=1 remains: the APK's own `libgdx.so`
  dlopen faults (SIGSEGV inside the loader — pre-existing FIX-TTT marker)
  and `AssetManager.load` later NPEs on a null asset string. Honest state:
  frame-captured, bounded; next wave owns the libgdx loader.
- **opencalculator is not claimed E5.** Taps dispatch and the app's own
  handler runs, but the display text does not yet mutate: the app's own
  obfuscated `x/d.onLayout` NPEs (`Lx/d;.r` on null, every frame, pre-dating
  taps) and `G1/d.g` hits `Pattern.matcher(null)` (a resource-backed string
  answered null) inside the formatting chain. Both are FILED with evidence
  lines, not hidden.
- **muellerma stopwatch_6 is not claimed SUCCESS** — a service-only app
  cannot render a window; the S158 boot-law candidate is filed.
- **No bouncy regression is claimed-by-assertion** — R5 is byte-exact and
  re-runnable.

> Coder 3 — four corpus rows re-judged, two #523 filed gaps closed, five new
> AOSP laws landed render-neutral. Verification recipes above; reject with
> stderr if any face regresses.
