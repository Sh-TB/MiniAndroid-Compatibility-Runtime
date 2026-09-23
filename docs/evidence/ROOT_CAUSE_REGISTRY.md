# Root-Cause Registry — S84 fan-out families

> **ONE family = ONE root-cause record.** Every blocked/partial title in
> [ACHIEVEMENTS.md](../ACHIEVEMENTS.md) references an ID here instead of
> duplicating an investigation. A/B proofs, fan-out counts and first
> divergence signatures are recorded per family. (S84 §7 user law.)

## F-NEW-160 — Class.forName framework bridge — **FIXED (S84)**

- **Signature:** `[R350-FORNAME] "android.os.Build$VERSION" → ClassNotFoundException`
  although the framework class exists on every device and the engine seeds
  its statics (`SDK_INT=34`, `RELEASE=14`).
- **Root cause:** the R350-FORNAME law resolved names against the APK DEX
  class index only; framework classes were unreachable by forName.
- **Fix:** framework bridge for the pure-data `Build` family
  (`Build`, `Build$VERSION`, `Build$VERSION_CODES`) — resolved as Class
  objects; member access rides the normal shadow paths
  (`miniandroid/src/dex/dalvik_engine.cpp`, S84 comment block).
- **A/B proof:** 9/50 S84 titles hit the CNFE pre-fix; post-fix the CNFE
  lines are gone; battery 26/26 + golden ladder 10/10 unchanged.
- **A/B regression guard (foehnix.widget):** bridging instantiable
  artifacts (`dalvik.system.CloseGuard`) pushed the app into a
  `Class.getMethod`/`Method.invoke` recursion storm (L2→L0 frame-drop
  cascade) — so instantiable classes STAY on the caught-CNFE path that
  real apps handle gracefully. The bridge is deliberately minimal.


## F-NEW-164..170 — SurfaceView real-surface chain + draw-law closures — **FIXED (S86)**

- **Ground truth (upstream source read, user directive):** `github.com/dozingcat/dodge-android`
  (GPLv3) — `FieldView extends SurfaceView implements SurfaceHolder.Callback`,
  `drawField()` = `surfaceHolder.lockCanvas(null)` → black field rect + goal
  zones + per-bullet colored circles → `unlockCanvasAndPost`, driven by a
  game thread (`while(running){field.tick(); drawField(); sleepUntilNextFrame();}`).
  The S84 Dodge GIF showed menu+about only — the FIELD never painted.
- **F-NEW-164 SurfaceView/SurfaceHolder real-surface law** — `getHolder()`
  returns a per-view holder object (`svHolder`/`svOwner` heap-field pairing);
  `lockCanvas` allocates a REAL Canvas bound to the view (`svTarget`) and
  opens a surface op capture; `unlockCanvasAndPost` POSTS the op list
  (`CanvasShadow::surface_ops_`); `addCallback` records the Callback; the
  render stage dispatches `surfaceCreated`/`surfaceChanged` lazily
  (`dispatch_surface_view_lifecycle`, GLSurfaceView-law mirror) and composites
  the last posted buffer at the view bounds (`CanvasShadow::replay_surface`).
- **F-NEW-165 Deque family** — `java.util.LinkedList` end-access
  (`getLast/getFirst/peek*/poll*/removeFirst/removeLast/push/pop/offer*/addFirst/addLast`)
  was unimplemented → `FrameRateManager.nanosToWaitUntilNextFrame` NPE'd on a
  null `Long` unbox and the GAME THREAD died at APP BOUNDARY before frame 1.
- **F-NEW-166 Display family** — `WindowManager.getDefaultDisplay` (AOSP:
  never null), `Display.getMetrics(out)` (device-profile fill 2.625/420dpi/
  1080x1920), `Display.getRotation` (ROTATION_0), `Display.getSize(out)`.
  Ground truth: FieldView ctor `getDefaultDisplay().getMetrics(...)` NPE +
  `AndroidUtils.getDeviceRotation` `Integer.intValue` NPE.
- **F-NEW-167 Activity.getPreferences** — AOSP law
  `getPreferences(mode) == getSharedPreferences(getLocalClassName(), mode)`;
  ground truth `DodgeMain.bestLevel()` SP null NPE.
- **F-NEW-168 draw-subtree visibility law** — AOSP `View.draw(Canvas,
  ViewGroup, long)` gates the ENTIRE body (background, onDraw AND
  dispatchDraw) on `(mViewFlags & VISIBILITY_MASK) == VISIBLE`;
  INVISIBLE(4) now prunes the subtree (GONE-only pruning kept Dodge's
  VISIBLE menu buttons painting over the live field). f06 leaf golden
  unchanged (all-white, pixel-identical).
- **F-NEW-169 RectF/Rect object draw + ctor law** — `Canvas.drawRect(RectF,
  Paint)` recorded (0,0,0,0) (only the 4-float overload was modeled) and the
  `RectF.<init>` never stored left/top/right/bottom heap fields; both laws
  added (op-trace evidence: correct colors, all-zero geometry → real
  geometry after).
- **F-NEW-170 View dimension queries** — `getWidth/getHeight/
  getMeasuredWidth/getMeasuredHeight` answered 0 (unbridged); now answer the
  ViewNode's measured geometry (UNIFIED_007 measure/layout). Dodge sizes
  EVERYTHING from `getWidth()`.
- **A/B proof (Dodge 1.5.1, SHA `a5687d1b…` = S84 pin):** pre: rc=1, 2-frame
  GIF (menu+about), field white; post: rc=0, 14 distinct frames — black
  field, semi-transparent red start zone (128,0,0) / green end zone
  (0,128,0), blue dodger, colored bullet swarm moving. Canonical GIF
  replaced (SHA `5a648a24…`), registry L3 VERIFIED-INTERACTIVE.
- **Regression:** battery 26/26 rc=0 + golden graphics ladder 10/10 +
  S83-B2 2/2, zero pixel drift on goldens.

## F-NEW-163 / F-NEW-163b — Context-family Resources + Resources.getSystem — **FIXED (S85)**

- **Signature:** `[SYNTH-EXC] f141-null-recv: NullPointerException (Attempt to invoke
  virtual method 'Landroid/content/res/Resources;.getDisplayMetrics' on a null object
  reference) method=Lnet/sourceforge/solitaire_cg/SolitaireView;.<init> pc=23` →
  APP-BOUNDARY unwind out of `SolitaireCG.onCreate`.
- **Root cause (163):** the P0.2 `getResources()` law matched only class-NAME
  substrings (`Context|Activity|View`). App subclasses of the Context family
  (`Solitaire extends Application`, custom `Application`/`Service` subclasses) matched
  none, so `getResources()` answered null. AOSP law: EVERY Context-family instance
  answers `getResources()`.
- **Root cause (163b):** `Resources.getSystem()` (static) was unimplemented → null.
  SolitaireCG overrides `SolitaireView.getResources()` and its body calls
  `Resources.getSystem()`; AOSP law: never null (shared system Resources).
- **Fix:** hierarchy-walk fallback over the Context roots
  (`Context/Activity/Application/Service/ContentProvider/ContextThemeWrapper`) via
  `is_subclass_of` before the singleton is denied + `Resources.getSystem()` static
  law answering the same Resources singleton
  (`miniandroid/src/dex/dalvik_engine.cpp`, S85 comment blocks).
- **A/B proof (S85):** solitaire_cg rc 1→0, exceptions 0, 9 frames, L2 UI;
  battery 26/26 + golden ladder 10/10 + S83-B2 ladder 2/2 unchanged.
- **S85 near-blank gate (EVID-CLASS-S85):** the S85 audit hardening
  (`scripts/s81_visual_audit.py` level_of) now classifies the engine-default
  shell class (white framebuffer + small black status region, nonbg_ratio≈0.011,
  content SHA eb16ab5c…) as L1-NEARBLANK-GATE — it can no longer pass L2 via its
  status-bar pixels. All S85-era claims re-judged; 72 records honestly demoted to
  OBSERVED (S54 blank-gate law). The remaining VERIFIED/INTERACTIVE counts are
  content-verified.

## F-NEW-161 — Compose UI runtime internals — **OPEN (fan-out ≈ 24 titles)**

- **Signature chain:** `kotlin.reflect.jvm.internal.ReflectionFactoryImpl`
  forName CNFE (**caught, faithful** — kotlin-reflect is optional on
  devices too) → later compose-runtime NPEs (null `Iterator.hasNext` in
  the recomposition chain, null `View.getWidth` in compose layout,
  `IllegalStateException` in `setContent`) → ART process-death law
  PARTIAL.
- **Why not fixed here:** compose recomposition is an S83-GFX-BASE P4
  scope family (measure/layout semantics on top of the software raster
  base), not a one-law fix; recorded as the pinned frontier with per-title
  first-divergence signatures in `run/s84/<pkg>/obs_obs.log`.
- **Fan-out list (S84):** com.justdeax.composeStopwatch,
  com.vayunmathur.clock, com.vayunmathur.games.alchemist,
  com.ma.tehro, com.hfut.schedule, me.timeto.app, me.river.nightbell,
  com.hegocre.nextcloudpasswords, com.kompact, com.octbit.rutmath,
  com.galaxyrio.sudokusolver, com.sanskritbasics.memory,
  com.serwylo.retrowars, com.willie.mancala, com.sidhant.puzzle-family
  variants, de.seemoo.at_tracking_detection, com.bupkis.tirailleur-class
  titles and others — every `rc=1` S84 run with compose frames in its log.

## F-NEW-162 — androidx generated-adapter forName family — **OPEN (12 titles)**

- **Signature:** `androidx.savedstate.Recreator_LifecycleAdapter`
  deferred CNFE (verified NOT packaged in the APKs — the adapter is an
  optional build-time artifact, so the CNFE itself is faithful; the gap
  is that the app's fallback path still ends in deferred unwind
  PARTIAL).
- **Same family:** `androidx.activity.ComponentActivity$$ExternalSyntheticLambda`
  and datastore-preferences protobuf generated classes
  (me.river.nightbell).
- **Next action:** implement the androidx fallback semantics
  (reflective-lookup-with-catch) as one semantic shadow — expected to
  clean the deferred-unwind PARTIAL of all 12 consumers at once.

## EVID-CLASS-S84 — shared near-blank evidence class — **CAUGHT + QUARANTINED**

- **Signature:** 16 S83 evidence JPGs byte-identical (f817c243…), plus
  ×2 classes (boxcars/no-thanks, ball2box/blackjack) — apps whose
  8-frame campaign run renders a status-bar-only framebuffer
  (2–3 unique colors).
- **Detection:** the S84 validator (R5 content-hash duplicate check) —
  exactly the class of fake-by-repetition the user's canonical law
  targets.
- **Disposition:** all members demoted to OBSERVED (no canonical
  artifact, log references only); near-blank frames are not visual
  evidence per the S54 gate law. Real-UI evidence for dooz restored from
  the s83b sweep (content-verified distinct).
- **Rule going forward:** no campaign ships a screenshot whose content
  hash equals another title's — the validator enforces this on every
  wave.

## Engine laws landed in S84 (summary)

| Law | Status | Proof |
|---|---|---|
| F-NEW-160 forName framework bridge (Build family) | FIXED | 9-title CNFE eliminated; battery 26/26; ladder 10/10; foehnix A/B guard |
| F-NEW-161 compose internals | OPEN (P4 scope) | ~24-title fan-out with first-divergence signatures |
| F-NEW-162 androidx adapter fallback | OPEN | 12-title fan-out, verified packaging state |
| EVID-CLASS-S84 evidence quarantine | ENFORCED | validator R5 + 20-title demotion |
