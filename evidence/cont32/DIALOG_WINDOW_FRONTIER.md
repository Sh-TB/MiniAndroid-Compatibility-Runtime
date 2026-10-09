# CONT-32 — Dialog Window Frontier: F-NEW-290 Root-Cause, Fix, Probe, and
# the AndroidCompositionLocals CNFE Verdict

Wave: CONT-32 (user directive: ادامه). Predecessor: evidence/cont31
(COMPOSESTOPWATCH_FRONTIER.md, which pinned this wave's targets). This wave:
(1) decoded and root-caused the "Dialog has no window" ISE face to its engine
law, (2) fixed it generically as F-NEW-290 with a probe-proven ×3 record,
(3) verdicted the AndroidCompositionLocals_androidKt CNFE as FAITHFUL engine
behavior (class genuinely absent from the R8-minified APK), (4) full
zero-drift regression gate.

## 0. RESUMABLE STATE BLOCK

| item | value |
|---|---|
| HEAD at wave start | 2fd055b7 (tmp-artifacts auto-commit) over pushed 8dcb5285 (CONT-31) |
| pre-wave binary | 9bdd61328d0f01d9 (byte-stable == CONT-31 record) |
| post-fix binary | **c280b243f880e7e6** |
| target APK | tmp/cont31_apks/composeStopwatch_1009011.apk (sha256 dbf937ebbe7c0b3d…) |
| pre-fix run (this binary) | run/cont32/csw_r1: rc=1, ISE "Dialog has no window" ×31 |
| post-fix runs | run/cont32/csw_post_r1..r3: ISE ×0, frame 5c4a0172628849ba (unchanged) |
| probe | fixtures/fnew290_probe → run/cont32/f290_pre, f290_pre2, f290_post_r1..r3 |
| regression | run/cont32/regression + scripts/cont32_regression.sh (parts run foreground) |

## 1. THE FACE (pre-fix, binary 9bdd61328d0f01d9)

composeStopwatch ×3 deterministic: rc=1, screenshot `5c4a0172628849ba`
(DEFAULT_BACKGROUND_ONLY), `IllegalStateException: "Dialog has no window"` at
`Lea;.r pc=2` (depth 53) ×31/run, caught by catch-alls in `Lx30;.n` (multiple
try ranges), re-thrown until propagated. The face appeared after F-NEW-289
eliminated the LiveData main-thread ISE — the app now reaches the dialog-show
path that never executed before.

## 2. DECODE (androguard, tmp/cont32/disasm2.txt)

- `Lea;r(Ljava/lang/String;)V` = kotlin's `error(String)` intrinsic:
  `new IllegalStateException(msg); throw` (pc 0-2).
- `Lis;` = androidx.compose.ui.window.DialogWrapper, super `Lpj;`
  (Compose ComponentDialog), super-super **`Landroid/app/Dialog;`**.
- `Lpj;.<init>` pc 0-1: `Dialog.<init>(new ContextThemeWrapper(ctx, style), 0)`
  — the [F166-BASECTX] ContextThemeWrapper (receiver 7220) and the
  [DIALOG] new Builder window (obj 7219 = the Lis; instance itself) in the log.
- `Lis;.<init>` pc 13-16: `window = Dialog.getWindow(); if (window == null)`
  → pc 113-115: `const-string "Dialog has no window"; invoke-static Lea;.r`.
  Downstream pc 21-25: `lp = window.getAttributes(); lp.type = <flags>;
  window.setAttributes(lp)` — a null getAttributes is an instant NPE.

## 3. ROOT CAUSE (engine dispatch chain)

1. `Dialog.getWindow()` is invoke-virtual; the engine bridges with the
   RUNTIME class (`Lis;`) — R8-renamed, no "Dialog" substring.
2. `DialogShadow::handles_class` gates on platform names only
   (AlertDialog$Builder / AlertDialog; / Dialog; / DialogFragment; / Toast;) —
   the shadow is NEVER ASKED for `Lis;`.
3. The call reaches the generic bridge; the S71 ancestry walk
   (`framework_ancestor_for_dispatch`) hops Lis;→Lpj;→Dialog and
   kPlatformSuper maps `Landroid/app/Dialog; → Landroid/content/Context;`;
   no Context guard answers getWindow → the STUBBED default returns
   **null** (reference proto).
4. DialogWrapper's `?:` null-check fires → kotlin `error(...)` → ISE ×31.

**AOSP law violated**: android.app.Dialog's constructor binds `mContext` and
`mWindow = new PhoneWindow(context)` BEFORE any subclass ctor body runs —
`getWindow()`/`getContext()` NEVER answer null afterwards, for ANY Dialog
receiver, renamed or not (the receiver-identity principle of S134-F134A
applied to the Dialog family).

## 4. F-NEW-290 — ROOT_CAUSED_FIXED (minimal generic fix)

- **Bridge law** (dalvik_engine.cpp, after the S134-F134A Activity getWindow
  arm): `getWindow`/`getContext` on a receiver whose class chain reaches
  `Landroid/app/Dialog;` (is_subclass_of walk — no name-based dispatch) is
  dispatched to the DialogShadow under the PLATFORM class name.
- **DialogShadow** gains `getWindow` (mints ONE Window heap object per
  DialogWindow, stable for the dialog lifetime) and `getContext` (the
  ctor-bound mContext, recorded at `<init>` arg 0).
- **Window attribute law** (bridge, after P1.2 setFlags): `getAttributes`
  answers a per-receiver cached `WindowManager$LayoutParams`
  (`window_layout_params_` map — every Window carries its OWN LayoutParams);
  setAttributes/setBackgroundDrawableResource/setGravity/addFlags absorb;
  `requestFeature` answers true (pre-content law).

No package checks, no app logic, no exception suppression, no forced
rendering. The existing R-005 activity-decor law is untouched.

## 5. PROBE — fixtures/fnew290_probe (real aapt2/ECJ/D8, w4 script)

A Dialog subclass ctor consuming `getWindow()` immediately — the androidx
DialogWrapper shape. **Probe hygiene find**: the first draft's class name
`MainActivity$WrapperDialog` CONTAINED the substring "Activity" and the S134
find("Activity") arm answered the singleton Window — masking the null
(DLG-WINDOW PASS pre-fix). Caught BEFORE any engine build; the activity was
renamed to `Main` so the dialog chain name carries no "Activity". The engine
was never built against the polluted probe.

| row | asserts | pre-fix (f290_pre2) | post-fix ×3 |
|---|---|---|---|
| DLG-WINDOW | getWindow() != null right after super | **FAIL** (divergence isolated) | PASS |
| DLG-ATTRS | getAttributes() != null | (gated) | PASS |
| DLG-SETATTRS | lp.type write + setAttributes | (gated) | PASS |
| DLG-REQFEAT | requestFeature(NO_TITLE) == true | (gated) | PASS |
| DLG-CTX | getContext() != null | (gated) | PASS |
| DLG-WSET | bg/gravity/flags absorbed | (gated) | PASS |
| DLG-STABLE | second getWindow() == first (identity) | (gated) | PASS |
| SUMMARY | | FAIL 0/1 | **PASS 7/0 ×3** |

Post-fix battery record: `PROBE fnew290 rc=1 PASS=56 FAIL=0`.

## 6. TARGET APP AFTER THE FIX — honestly PARTIAL

composeStopwatch ×3 on binary c280b243f880e7e6:

| run | rc | screenshot | "Dialog has no window" | verdict |
|---|---|---|---|---|
| csw_post_r1 | 1 | 5c4a0172628849ba | **0** (was 31) | DEFAULT_BACKGROUND_ONLY |
| csw_post_r2 | 1 | 5c4a0172628849ba | **0** | DEFAULT_BACKGROUND_ONLY |
| csw_post_r3 | 1 | 5c4a0172628849ba | **0** | DEFAULT_BACKGROUND_ONLY |

- The DialogWrapper ctor chain now COMPLETES: the C013-HIER superclass-chain
  law routes getWindow/getContext/setTitle/setCanceledOnTouchOutside;
  [F290-DIALOG] mints window obj=7238 once; getAttributes serves the ctor's
  type-write; getDecorView/setContentView absorb per existing laws.
- The frame is UNCHANGED — the divergence MOVED onward, as required by
  honesty: `Lh4;` (the Compose-backed custom view) still dispatches onDraw
  with **ops=0**; no content-pixel claims.
- Deferred faces unchanged and honestly recorded (§7).

## 7. ANDROIDCOMPOSITIONLOCALS CNFE — VERDICT: FAITHFUL (not a bug)

CONT-31 flagged `S102-CLASSLOADER: ClassNotFoundException
(androidx.compose.ui.platform.AndroidCompositionLocals_androidKt)` at
`Lah0;.<clinit>` pc=14 as "a REAL androidx class name worth a dedicated
look". Look taken:

- The string census finds the name ONCE — as a `loadClass` constant.
- **The class is NOT in the APK DEX**: 0 classes under
  `Landroidx/compose/ui/platform/*` exist at all — R8 fully renamed/
  repackaged the compose classes (all the short `Lxx;` names).
- `Lah0;.<clinit>` reflectively loads the CANONICAL name and IMMEDIATELY
  catches the CNFE (deferred handler; the catch path continues the clinit).

This is a faithful REPRODUCTION of ART behavior on the same APK: a
`loadClass` of a genuinely-absent class throws CNFE, the app catches it and
falls back. **No engine defect** — recorded as an honest observation, not a
root. (Same verdict family as the R350-FORNAME kotlin.reflect CNFE.)

## 8. OTHER DEFERRED FACES (recorded, not chased this wave)

- `STREAM-OPEN` DataStore ENOENT with a MANGLED path:
  `runtime/data/data/data/.../runtime/data/runtime/data/...` — repeated
  prefix segments suggest a path-join bug in the sandbox resolver; the
  ENOENT is deferred/handled so the app tolerates it. Worth a future wave.
- `STR-BRIDGE` StringIndexOutOfBoundsException (length=0; begin=0; end=2) at
  `Lwv;.p pc=26` — uncaught/deferred; next-wave candidate.

## 9. REGRESSION GATE — ZERO DRIFT at c280b243f880e7e6

scripts/cont32_regression.sh (probe builds + anchors foreground; the binary
CHANGED this wave so the full gate ran):

| gate | result |
|---|---|
| anchors ×3 ×8 apps | dooz d602648e8e401895, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8, gmdice f3b483fe7b7cf51b, opencalc a976d2f9fb675cb3, tttdeluxe af6094295ecb50e3, flappycow 13cf47464d9787f4, g2048 59ca1526611c4622 — **24/24 BYTE-IDENTICAL MATCH** |
| probe battery | fcol 140/0, f259 49/0, f259g 84/7 (known-honest F259-L row), f266 42/0, f268 96/0, fnew253 147/0, fnew286 10/0, fnew289 28/0, fnew252 56/0 — **== CONT-28..31 records EXACTLY** |
| new probe | fnew290 **56/0** |
| Track B control | Simple Calculator ×3 rc=0 `7960bce447ac6d8f` — FULL SUCCESS retained |

## 10. STATUS WORDS

- F-NEW-290: **ROOT_CAUSED_FIXED / TESTED / OBSERVED** (probe PRE/POST ×3 +
  target ISE elimination ×3 + zero-drift regression).
- composeStopwatch rendering: **PARTIAL** — the Dialog-window face is closed;
  the app's next frontier is the ops=0 face with the deferred CNFEs
  re-verified as faithful; the STR-BRIDGE SIOOBE and the mangled DataStore
  path are the named next candidates.
- Registry: 598 → **599** (F-NEW-290 added; dedup-checked against 290-free).

## 11. NEXT RESUMABLE CHECKPOINT

1. The `Lwv;.p` STR-BRIDGE StringIndexOutOfBounds (length=0) — decode the
   consumer and the empty-string producer (the CONT-4 poison-source method
   applies: MINIANDROID_CONT4_SOLVER_DIAG prints the engine call chain).
2. The mangled DataStore path join (`runtime/data/data/data/...` repetition).
3. Standing: F-NEW-288 (TextUnit value-class spin, Track A P0) and Simple
   Calculator input-pump (Track B).
