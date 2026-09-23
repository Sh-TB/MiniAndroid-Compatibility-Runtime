# MiniAndroid — App & Game Achievements

> **CANONICAL, ONE RECORD PER TITLE** (S84 law, 2026-09-23).
> This file is the single source of truth for what each app and
> game has PROVEN on MiniAndroid. Historical per-wave narrative
> moved to [ACHIEVEMENTS_WAVE_HISTORY.md](history/ACHIEVEMENTS_WAVE_HISTORY.md).
>
> **Navigation hub (S90):** [docs/achievements/INDEX.md](achievements/INDEX.md)
> → [GAMES_WITH_GIFS.md](achievements/GAMES_WITH_GIFS.md) ·
> [APPS_EXECUTED.md](achievements/APPS_EXECUTED.md) ·
> [ASSET_MANIFEST.json](achievements/ASSET_MANIFEST.json)
>
> Chain (no broken links):
> `Title → Source → APK+SHA → Execution session → Achievement →
>  ONE canonical screenshot → root-cause issue → README summary`
>
> Validate: `python3 tools/verify_canonical_evidence.py` ·
> machine source: `docs/evidence/canonical/registry.json`

## Status vocabulary

| Status | Meaning |
|---|---|
| VERIFIED | launched + rendered real frames at the recorded session |
| VERIFIED-INTERACTIVE | + real click dispatched and rendered state change captured (GIF) |
| PARTIAL | rendered frames but a first-divergence blocks deeper behavior (root cause recorded) |
| OBSERVED | frames captured, level below render threshold |
| BLOCKED | no usable frame; root cause recorded |

## Rendering levels

L0 recognized → L1 manifest → L2 DEX → L3 lifecycle → L4 UI machinery → L5 meaningful frame (non-blank real UI) → L6 real input → L7 input→state change → L8 multiple interactions → L9 app-specific behavior → L10 close/reopen persistence. The screenshot-gate law (S54) applies: blank/placeholder frames are NEVER evidence.

## Totals (generated from registry.json — not hand-written)

- Titles: **148** (87 games, 60 apps, 1 fixtures) — 33 added in S84
- VERIFIED: **34** · VERIFIED-INTERACTIVE: **12** · PARTIAL: **2** · BLOCKED: **0**
- Rendered: 129 · Interacted: 13 · State-change proven: 12
- Canonical screenshots: **148** (12 GIF + 24 JPG) — one per title, zero duplicates

---

### Halma

* **Package / identity:** `app.halma` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S87-source-probe · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** S87 re-probe vc15: 8 frames, near-blank class → com.badlogic.gdx.backends.android.AndroidInput.onResume on null receiver (F-NEW-157 libGDX/EGL frontier family)
* **Notes:** S87 re-probe at HEAD; upstream Crazy-Marvin/Halma (libGDX game — gated by the documented GL frontier)

### bim.app

* **Package / identity:** `bim.app` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) → none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### ca.rmen.nounours

* **Package / identity:** `ca.rmen.nounours` · type: game · version: 3.5.8
* **Source:** [https://github.com/caarmen/nounours-android](https://github.com/caarmen/nounours-android)
* **APK SHA256:** `0e7da7b17b63d727fb2a3a75e0576e1a42e286ebc8fb73b368da5518a728c682`
* **Sessions:** S84 · status: **VERIFIED-INTERACTIVE** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=false · rendered=true · interacted=true · state_changed=true
* **Canonical screenshot:** [ca.rmen.nounours.gif](../docs/evidence/canonical/ca.rmen.nounours.gif) · SHA256 `24a19ed30eda6be3…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Notes:** S84 NEW title. rc_obs=1 errors=1 frames=8/8 click: probed=1 state_changed=1. unique_colors=2 entropy=0.918 resources(dex/classes)=?

### Anuto TD

* **Package / identity:** `ch.logixisland.anuto` · type: game · version: —
* **Source:** [https://github.com/jogishop/AnutoTD](https://github.com/jogishop/AnutoTD)
* **APK SHA256:** `—`
* **Sessions:** S62+ / S85-sweep(shell at HEAD re-run; S-era canonical retained) · status: **VERIFIED** · rendering: L5 (L5)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [ch.logixisland.anuto.jpg](../docs/evidence/canonical/ch.logixisland.anuto.jpg) · SHA256 `f876a103e2eae2f1…`
* **Root cause:** see session report (S62-S65 spotlight reports) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Notes:** canonical harvested from docs/evidence/s62plus_spotlight/anuto_frame0_after_onDraw.png

### com.ahorcado

* **Package / identity:** `com.ahorcado` · type: game · version: 1.5.1
* **Source:** [https://github.com/Webierta/ahorcandroid](https://github.com/Webierta/ahorcandroid)
* **APK SHA256:** `7f4df3878508804bd0d15df2bdd29cb7f70377182b2e8c069c060024e547e2d5`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Landroid/security/NetworkSecurityPolicy;.isCleartextT
* **Notes:** S85 NEW-50 (game); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Astroloop

* **Package / identity:** `com.astroloop.game` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) → none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Tirailleur

* **Package / identity:** `com.bupkis.tirailleur` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) → none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.clavierhaus.gnubg

* **Package / identity:** `com.clavierhaus.gnubg` · type: game · version: 1.0.2
* **Source:** [https://github.com/clavierhaus/gnubg-android](https://github.com/clavierhaus/gnubg-android)
* **APK SHA256:** `a951da343ca91f10512d888802123cb040c4be72dc3d3eb58ce8ddfab80d78ff`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L1 (NONBLANK)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/com.clavierhaus.gnubg/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=32 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.034 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### Vector Pinball (bouncy)

* **Package / identity:** `com.dozingcatsoftware.bouncy` · type: game · version: —
* **Source:** [https://github.com/dozingcatsoftware/Bouncy](https://github.com/dozingcatsoftware/Bouncy)
* **APK SHA256:** `ffda0d9cb0b1b2aa58be9559dda891c4fa24391bc481d297a8e3d96c31f62721`
* **Sessions:** S62+ / S85-sweep · status: **VERIFIED-INTERACTIVE** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=true · state_changed=true
* **Canonical screenshot:** [com.dozingcatsoftware.bouncy.gif](../docs/evidence/canonical/com.dozingcatsoftware.bouncy.gif) · SHA256 `d96b48d7e8667b5b…`
* **Root cause:** none — interaction proven at current HEAD · issue: —
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** graphics completeness beyond L3
* **Notes:** S85 sweep: probed=12 state_changed=10

### com.dozingcatsoftware.dodge

* **Package / identity:** `com.dozingcatsoftware.dodge` · type: game · version: 1.5.1
* **Source:** [https://github.com/dozingcat/dodge-android](https://github.com/dozingcat/dodge-android)
* **APK SHA256:** `a5687d1bad7b2927740a55b7b1df11efc81edcad03f0633ab5c2e5c58b120541`
* **Sessions:** S84/S86 · status: **VERIFIED-INTERACTIVE** · rendering: L3 (L3_STRUCT_CANDIDATE)
* **Execution evidence:** launched=true · rendered=true · interacted=true · state_changed=true
* **Canonical screenshot:** [com.dozingcatsoftware.dodge.gif](../docs/evidence/canonical/com.dozingcatsoftware.dodge.gif) · SHA256 `5a648a244bec1bb1…`
* **Root cause:** S86 root-cause chain (upstream source-read driven): the game field NEVER rendered in the S84 GIF (frame0=menu, frame1=about white). Root causes fixed this wave, all A/B-proven: F-NEW-164 SurfaceView/SurfaceHolder.lockCanvas real-surface law (FieldView extends SurfaceView, drawField() = lockCanvas->drawRect(black)+zones+bullets->unlockCanvasAndPost); F-NEW-165 java.util.LinkedList Deque end-access family (FrameRateManager.previousFrameTimestamps.getLast() NPE killed the game thread at APP BOUNDARY); F-NEW-166 WindowManager.getDefaultDisplay/Display.getMetrics/getRotation (FieldView ctor Display.getMetrics NPE); F-NEW-167 Activity.getPreferences == getSharedPreferences(getLocalClassName(), mode) (bestLevel() SP NPE); F-NEW-168 AOSP draw-subtree law: View.draw(Canvas,ViewGroup,long) gates dispatchDraw on VISIBLE — INVISIBLE(4) prunes the subtree (menuView INVISIBLE kept button children painting); F-NEW-169 Canvas.drawRect(RectF,Paint) object overload + RectF ctor field law (rect recorded (0,0,0,0)); F-NEW-170 View.getWidth/getHeight dimension query laws (drawField sizes all geometry from getWidth(); was 0 -> all-zero draw ops). Game now renders the real Dodge design from upstream source: black field, semi-transparent red start zone, green end zone, blue dodger circle, per-bullet random bright colors. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED/SCREENSHOT_CAPTURED
* **Remaining:** dodger steering (touch/tilt navigation) + collision/death animation proof
* **Notes:** S86 canonical GIF: 14 frames (menu + 13 live gameplay), tap New Game at (537,935), bullets move/dodger visible, L3 struct-candidate. Upstream ground truth: github.com/dozingcat/dodge-android (GPLv3) FieldView.java read this wave; APK re-downloaded SHA256 a5687d1bad7b2927740a55b7b1df11efc81edcad03f0633ab5c2e5c58b120541 = S84 pin (v1.5.1, vc10).

### FireStrike

* **Package / identity:** `com.eightsines.firestrike.opensource` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) → none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### TicTacToe Classic

* **Package / identity:** `com.emmanuelmess.tictactoe` · type: game · version: —
* **Source:** F-Droid com.emmanuelmess.tictactoe
* **APK SHA256:** `16510d7cb5dbcf7db049762728bd3e38911c3117b1f090129caee11e2b098f6e`
* **Sessions:** S83 · status: **VERIFIED-INTERACTIVE** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=true · state_changed=true
* **Canonical screenshot:** [com.emmanuelmess.tictactoe.gif](../docs/evidence/canonical/com.emmanuelmess.tictactoe.gif) · SHA256 `b6811a17d271d5dc…`
* **Root cause:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** graphics completeness beyond L3
* **Notes:** S83 real-screenshot campaign evidence (games__tictactoeclassic__L2_GRAPHICALLY_INCOMPLETE.jpg)

### com.galaxyrio.sudokusolver

* **Package / identity:** `com.galaxyrio.sudokusolver` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S87-source-probe · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** S87 re-probe vc6: 8 frames, near-blank class → kotlin.reflect.jvm.internal.ReflectionFactoryImpl CNFE (R350-FORNAME family) + Field.get null in Ld31; (open)
* **Notes:** S87 re-probe at HEAD; upstream Galaxy-rio/SudokuYou (Kotlin app; kotlin-reflect stdlib init needs the FORNAME bridge extended beyond the Build family)

### com.games.boardgames.aeonsend

* **Package / identity:** `com.games.boardgames.aeonsend` · type: game · version: 1.0
* **Source:** [https://github.com/JanSvoboda/aeonsend-randomizer](https://github.com/JanSvoboda/aeonsend-randomizer)
* **APK SHA256:** `9dbd85782b534a58c8112faa58e9229fc47e1af101a5dc9b36205bbe22910a57`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L0 (LOADED_ONLY)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none — clean run at current HEAD · issue: —
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L0 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Lcom/games/boardgames/aeonsend/database/DatabaseHandl
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.github.m374lx.alexvsbus

* **Package / identity:** `com.github.m374lx.alexvsbus` · type: game · version: 2025.06.16.0
* **Source:** [https://github.com/M374LX/alexvsbus](https://github.com/M374LX/alexvsbus)
* **APK SHA256:** `ecec13afdae16e9f7c362673c74c2915839a95b48adc8c74e77fb8fb2d709e89`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none — clean run at current HEAD · issue: —
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.helddertierwelt.mentalmath

* **Package / identity:** `com.helddertierwelt.mentalmath` · type: game · version: 27
* **Source:** [https://codeberg.org/Mental-Math/MentalMath](https://codeberg.org/Mental-Math/MentalMath)
* **APK SHA256:** `68af653d1dc0b1841374100462163c12a36fe5c9afe4b187bd1a0400fe546dc7`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L1 (NONBLANK)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/com.helddertierwelt.mentalmath/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=32 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.034 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### Balance the Ball

* **Package / identity:** `com.jeffliu.balancetheball` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `6180534b151e4d50365b21483f3719e32f207a42675dee20227de449c875c1e2`
* **Sessions:** S83 / S85-sweep(shell at HEAD re-run; S-era canonical retained) · status: **VERIFIED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [com.jeffliu.balancetheball.jpg](../docs/evidence/canonical/com.jeffliu.balancetheball.jpg) · SHA256 `bfb8f34224084ad4…`
* **Root cause:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** graphics completeness beyond L3
* **Notes:** S83 real-screenshot campaign evidence (games__com.jeffliu.balancetheball_4__L2_GRAPHICALLY_INCOMPLETE.jpg)

### com.kaeruct.raumballer

* **Package / identity:** `com.kaeruct.raumballer` · type: game · version: 1.2
* **Source:** [https://github.com/KaeruCT/RaumBaller](https://github.com/KaeruCT/RaumBaller)
* **APK SHA256:** `e0eb9a7dfbd82162c44e25d0294b89f6f811396cce7691a969443bd271658bc1`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L0 (LOADED_ONLY)
* **Execution evidence:** launched=false · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/com.kaeruct.raumballer/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=1 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=1 entropy=-0.0 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.kingalex.kingpong

* **Package / identity:** `com.kingalex.kingpong` · type: game · version: 1.1.2
* **Source:** [https://github.com/KingAlexGilbert/king-pong](https://github.com/KingAlexGilbert/king-pong)
* **APK SHA256:** `9545a66697a83c25957767b7f9adb296d71fd57e30365dc742225104feb70b66`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L0 (LOADED_ONLY)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none (rc=0) · issue: —
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** full app-specific behavior beyond click probe
* **Last success / first divergence:** 8/8 frames captured, click pass executed → none
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=1 entropy=-0.0 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### 2048

* **Package / identity:** `com.miniandroid.g2048` · type: game · version: —
* **Source:** in-house (games/2048)
* **APK SHA256:** `1b1c602a5f0a27231ebcdcfdc632a96c82f6fb74aaae7d80130ac63ab185d278`
* **Sessions:** S80/S83 · status: **VERIFIED-INTERACTIVE** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=true · state_changed=true
* **Canonical screenshot:** [com.miniandroid.g2048.gif](../docs/evidence/canonical/com.miniandroid.g2048.gif) · SHA256 `d613d30fce792406…`
* **Root cause:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** graphics completeness beyond L3
* **Notes:** S83 real-screenshot campaign evidence (games__g2048_v1.0_vc1__L2_GRAPHICALLY_INCOMPLETE.jpg)

### MiniCraft (House Builder)

* **Package / identity:** `com.miniandroid.minicraft` · type: game · version: 1.0
* **Source:** in-house (games/minicraft) — companion to Snake Deluxe / Mini Tetris / 2048 / TicTacToe Deluxe
* **APK SHA256:** `77b9629ee111b968ccc9dbd4507eab3564a0a7a6e26dcacbe28f99de189c3a90`
* **Sessions:** S86 · status: **VERIFIED-INTERACTIVE** · rendering: L3 (L3_STRUCT_CANDIDATE)
* **Execution evidence:** launched=true · rendered=true · interacted=true · state_changed=true
* **Canonical screenshot:** [com.miniandroid.minicraft.gif](../docs/evidence/canonical/com.miniandroid.minicraft.gif) · SHA256 `3fbca3e4b1a1662b…`
* **Root cause:** none — built on the proven in-house pattern (static state law + real Canvas.onDraw + button clicks); renders first try at current HEAD with the S86 engine laws · issue: —
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED/SCREENSHOT_CAPTURED
* **Remaining:** freeform multi-story building + world save/restore
* **Notes:** S86 user-requested house-building game. 2D block sandbox: LCG terrain (grass/dirt/stone), build cursor walked with the direction pad, BRICK cycles material (brick/plank/roof/glass/door), PLACE/DIG edit the world, DEMO auto-builds a brick cottage (gabled roof + timber ring + glass window + door). Canonical GIF: 16 frames — terrain, 5 real placements, material cycle, DEMO house build, 2 digs; stats strip mutates (Blocks/Dug).

### Snake Deluxe

* **Package / identity:** `com.miniandroid.snakedeluxe` · type: game · version: —
* **Source:** in-house (games/snake-deluxe)
* **APK SHA256:** `—`
* **Sessions:** S80/S83 · status: **VERIFIED-INTERACTIVE** · rendering: L3 (L3_STRUCT_CANDIDATE)
* **Execution evidence:** launched=true · rendered=true · interacted=true · state_changed=true
* **Canonical screenshot:** [com.miniandroid.snakedeluxe.gif](../docs/evidence/canonical/com.miniandroid.snakedeluxe.gif) · SHA256 `f2dd621c662526fa…`
* **Root cause:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** graphics completeness beyond L3
* **Notes:** S83 real-screenshot campaign evidence (games__snake_deluxe_v1.0_vc1__L3_STRUCT_CANDIDATE.jpg)

### Mini Tetris

* **Package / identity:** `com.miniandroid.tetris` · type: game · version: —
* **Source:** in-house (games/mini-tetris)
* **APK SHA256:** `cb2818dfe6c6cadb651348ddaf4c91c57bea5ecc134f215d25fb5ffdffdf8644`
* **Sessions:** S80/S83 · status: **VERIFIED-INTERACTIVE** · rendering: L3 (L3_STRUCT_CANDIDATE)
* **Execution evidence:** launched=true · rendered=true · interacted=true · state_changed=true
* **Canonical screenshot:** [com.miniandroid.tetris.gif](../docs/evidence/canonical/com.miniandroid.tetris.gif) · SHA256 `927d966a5a7397a8…`
* **Root cause:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** graphics completeness beyond L3
* **Notes:** S83 real-screenshot campaign evidence (games__tetris_v1.0_vc1__L3_STRUCT_CANDIDATE.jpg)

### TicTacToe Deluxe

* **Package / identity:** `com.miniandroid.tictactoedeluxe` · type: game · version: —
* **Source:** in-house (games/tictactoe-deluxe)
* **APK SHA256:** `—`
* **Sessions:** S83 NEW · status: **VERIFIED-INTERACTIVE** · rendering: L3 (L3_STRUCT_CANDIDATE)
* **Execution evidence:** launched=true · rendered=true · interacted=true · state_changed=true
* **Canonical screenshot:** [com.miniandroid.tictactoedeluxe.gif](../docs/evidence/canonical/com.miniandroid.tictactoedeluxe.gif) · SHA256 `ade32b621e90fb27…`
* **Root cause:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** graphics completeness beyond L3
* **Notes:** S83 real-screenshot campaign evidence (games__tictactoe_deluxe_v1.0_vc1__L3_STRUCT_CANDIDATE.jpg)

### com.mufradat.africaquiz

* **Package / identity:** `com.mufradat.africaquiz` · type: game · version: 1.0
* **Source:** [https://codeberg.org/Mufradat/africa-quiz](https://codeberg.org/Mufradat/africa-quiz)
* **APK SHA256:** `649282d36bd5c237acfc7354d1d3af66fac198706880cf7353903dd47260ad12`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L1 → [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (androidx.savedstate.Recreator_LifecycleAdapter) method=Landroidx/lifecycle/Lifecycling;
* **Notes:** S85 NEW-50 (game); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.octbit.rutmath

* **Package / identity:** `com.octbit.rutmath` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) → none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.qwde.ccm

* **Package / identity:** `com.qwde.ccm` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) → none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Boxcars

* **Package / identity:** `com.rocket9labs.boxcars` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L1 (L1_NONBLANK)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran → near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (games__com.rocket9labs.boxcars_104090__L1_NONBLANK.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### com.sanskritbasics.memory

* **Package / identity:** `com.sanskritbasics.memory` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) → none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.serwylo.babydots

* **Package / identity:** `com.serwylo.babydots` · type: game · version: 1.10.0
* **Source:** [https://github.com/babydots/babydots](https://github.com/babydots/babydots)
* **APK SHA256:** `582d536d0aa435b5be64b04337b33750372192e49cf55ccbe39369770eabbedd`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none — clean run at current HEAD · issue: —
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L1 → [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (kotlin.reflect.jvm.internal.ReflectionFactoryImpl) method=Lkotlin/jvm/internal/Reflecti
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0; probed=1; engine_state_changed=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### RetroWars

* **Package / identity:** `com.serwylo.retrowars` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) → none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.sidhant.bubbleshooter

* **Package / identity:** `com.sidhant.bubbleshooter` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S87-source-probe · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** S87 re-probe vc23: 8 frames, rc=0, no exceptions → silent near-blank: zero exceptions, zero render nodes, Enum.ordinal REC-MISS ×18 (unlocalized — needs deeper trace)
* **Notes:** S87 re-probe at HEAD; upstream sidhant947/BubbleShooter (SurfaceView-family game; lifecycle completes but nothing inflates — honest open)

### com.sidhant.puzzle

* **Package / identity:** `com.sidhant.puzzle` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) → none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Queens

* **Package / identity:** `com.sidhant.queens` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) → none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Ball2Box

* **Package / identity:** `com.simondalvai.ball2box` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L0 (L0_LOADED_ONLY)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran → near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (games__com.simondalvai.ball2box_69__L0_LOADED_ONLY.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### com.smorgasbork.hotdeath

* **Package / identity:** `com.smorgasbork.hotdeath` · type: game · version: 1.0.11
* **Source:** [https://github.com/jpriebe/hotdeath](https://github.com/jpriebe/hotdeath)
* **APK SHA256:** `8e6c19ead1795fa5b0f62090f3a56efa4be16e4b3e33f151af707f5eb5e5c620`
* **Sessions:** S84 · status: **VERIFIED-INTERACTIVE** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=true · state_changed=true
* **Canonical screenshot:** [com.smorgasbork.hotdeath.gif](../docs/evidence/canonical/com.smorgasbork.hotdeath.gif) · SHA256 `d6fdff53adfaa6fa…`
* **Root cause:** none (rc=0) · issue: —
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** full app-specific behavior beyond click probe
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=6 state_changed=3. unique_colors=4 entropy=0.982 resources(dex/classes)=?

### com.towerillusion.abdal

* **Package / identity:** `com.towerillusion.abdal` · type: game · version: 1.0.0
* **Source:** [https://github.com/towerillusionii/Abstract-Dots-and-Lines](https://github.com/towerillusionii/Abstract-Dots-and-Lines)
* **APK SHA256:** `50be6be690faaa59348bef4bd2e48067f7c3aee624a6fea31188c71f9045296c`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Landroid/content/res/AssetManager;.open' on a null ob
* **Notes:** S85 NEW-50 (game); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.trianguloy.adnihilation

* **Package / identity:** `com.trianguloy.adnihilation` · type: game · version: 1.0
* **Source:** [https://github.com/TrianguloY/Adnihilation](https://github.com/TrianguloY/Adnihilation)
* **APK SHA256:** `ae531b495cc39b210fc13ef74e7e5e663f8fde658a3535e3b964675f8c417d80`
* **Sessions:** S85 · status: **VERIFIED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [com.trianguloy.adnihilation.jpg](../docs/evidence/canonical/com.trianguloy.adnihilation.jpg) · SHA256 `541a877382de1031…`
* **Root cause:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** state-change evidence
* **Notes:** S85 NEW-50 (game); rc_obs=1; frames=8; rc_click=1; probed=1; engine_state_changed=0

### com.vayunmathur.games.alchemist

* **Package / identity:** `com.vayunmathur.games.alchemist` · type: game · version: v2.6.5
* **Source:** [https://github.com/vayun-mathur/Modern-Apps](https://github.com/vayun-mathur/Modern-Apps)
* **APK SHA256:** `88a0ac6f06e9c57f25977ebcfd49081d2e909137619b5359246e5bd1411c74f1`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L1 (NONBLANK)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/com.vayunmathur.games.alchemist/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=15 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.034 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### Solitaire (vayunmathur)

* **Package / identity:** `com.vayunmathur.games.solitaire` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran → near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (games__com.vayunmathur.games.solitaire_20260804__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### com.vovagorodok.blichess

* **Package / identity:** `com.vovagorodok.blichess` · type: game · version: 8.0.0+ble2.5.1
* **Source:** [https://github.com/vovagorodok/blichess/](https://github.com/vovagorodok/blichess/)
* **APK SHA256:** `3ae86223a70439511f32ffe7489de6050b430dd9692d7a45ae6506933dddc69d`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L1 (NONBLANK)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/com.vovagorodok.blichess/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=2 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.034 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.vovagorodok.blidraughts

* **Package / identity:** `com.vovagorodok.blidraughts` · type: game · version: 2.3.0+ble2.5.1
* **Source:** [https://github.com/vovagorodok/blidraughts/](https://github.com/vovagorodok/blidraughts/)
* **APK SHA256:** `f7f4582fa24607d87c304c3acaca0cc150fa311da22e469cd15150c73d20ba2d`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L1 (NONBLANK)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/com.vovagorodok.blidraughts/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=2 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.034 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### Mancala

* **Package / identity:** `com.willie.mancala` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) → none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Mines (premy)

* **Package / identity:** `cos.premy.mines` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `18faef7028457f4d123ac8d781f3ecdbf9e29b451468d5d6a348df28e8842aa7`
* **Sessions:** S85-sweep · status: **VERIFIED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [cos.premy.mines.jpg](../docs/evidence/canonical/cos.premy.mines.jpg) · SHA256 `f73b3c57ca712dd2…`
* **Root cause:** VERIFIED · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** interaction + canonical artifact harvest
* **Notes:** S85 sweep promotion: prior VERIFIED → L2 render

### Blackjack

* **Package / identity:** `crypto.o0o0o0o0o.games.blackjack` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L0 (L0_LOADED_ONLY)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran → near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (games__crypto.o0o0o0o0o.games.blackjack_4__L0_LOADED_ONLY.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### OpenSudoku

* **Package / identity:** `cz.romario.opensudoku` · type: game · version: —
* **Source:** [https://github.com/romario333/opensudoku](https://github.com/romario333/opensudoku)
* **APK SHA256:** `—`
* **Sessions:** S62+ / S85-sweep(shell at HEAD re-run; S-era canonical retained) · status: **VERIFIED** · rendering: L5 (L5)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [cz.romario.opensudoku.jpg](../docs/evidence/canonical/cz.romario.opensudoku.jpg) · SHA256 `1478e902a245a829…`
* **Root cause:** see session report (S62-S65 spotlight reports) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Notes:** canonical harvested from docs/evidence/s62plus_spotlight/opensudoku_frame0_folderlist.png

### de.georgsieber.ballbreak

* **Package / identity:** `de.georgsieber.ballbreak` · type: game · version: 1.8.1
* **Source:** [https://github.com/schorschii/ballBreak-Android](https://github.com/schorschii/ballBreak-Android)
* **APK SHA256:** `e6e9f37293d3aaacda7163f997d17e538962acde7a991f6325f9dd72b45ffe02`
* **Sessions:** S84 / S85-sweep(shell at HEAD re-run; S-era canonical retained) · status: **VERIFIED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [de.georgsieber.ballbreak.jpg](../docs/evidence/canonical/de.georgsieber.ballbreak.jpg) · SHA256 `b3c8930369dfe0b7…`
* **Root cause:** none (rc=0) · issue: —
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED
* **Remaining:** full app-specific behavior beyond click probe
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=2 state_changed=0. unique_colors=25 entropy=0.096 resources(dex/classes)=?

### Solitaire (Bielefeld)

* **Package / identity:** `de.tobiasbielefeld.solitaire` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S87-source-probe · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** S87 re-probe vc71: 8 frames, near-blank class → Context.getResources on null receiver + Window.getCallback NPE inside android/support v7 chain (f141 family, open)
* **Notes:** S87 re-probe at HEAD; upstream TobiasBielefeld/Simple-Solitaire read (GameActivity statics need a live Context before the support shadow answers)

### dev.lonami.klooni

* **Package / identity:** `dev.lonami.klooni` · type: game · version: 0.8.6
* **Source:** [https://codeberg.org/Lonami/Klooni1010](https://codeberg.org/Lonami/Klooni1010)
* **APK SHA256:** `55641cdb5dba7f30c1d229cf8a34f390a8ff6b3f60cdff9b45d277919f33ce24`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Lcom/badlogic/gdx/backends/android/AndroidInput;.onRe
* **Notes:** S85 NEW-50 (game); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### eu.quelltext.counting

* **Package / identity:** `eu.quelltext.counting` · type: game · version: 1.3
* **Source:** [https://gitlab.com/niccokunzmann/12345](https://gitlab.com/niccokunzmann/12345)
* **APK SHA256:** `98fe65f21ff8e51918b94e80d25d99d52f5527d24a69dcd8dd9ca1a5da9b7a02`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L0 (LOADED_ONLY)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none — clean run at current HEAD · issue: —
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L0 → none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Memory

* **Package / identity:** `eu.quelltext.memory` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `4dd3957983e3c3f38c673f898d9659d5e0251f97137bab5254eafdcdbc9fa27c`
* **Sessions:** S83 · status: **VERIFIED** · rendering: L0 (L0_LOADED_ONLY)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** [eu.quelltext.memory.jpg](../docs/evidence/canonical/eu.quelltext.memory.jpg) · SHA256 `1f36d707ec9f685c…`
* **Root cause:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** graphics completeness beyond L3
* **Notes:** S83 real-screenshot campaign evidence (games__eu.quelltext.memory_7__L0_LOADED_ONLY.jpg)

### Fish Rings

* **Package / identity:** `eu.veldsoft.fish.rings` · type: game · version: —
* **Source:** [https://github.com/VelbazhdSoftwareLLC/FishRingsForAndroid](https://github.com/VelbazhdSoftwareLLC/FishRingsForAndroid)
* **APK SHA256:** `—`
* **Sessions:** S65 · status: **VERIFIED** · rendering: L10 (L10)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [eu.veldsoft.fish.rings.jpg](../docs/evidence/canonical/eu.veldsoft.fish.rings.jpg) · SHA256 `28c952a6e1657b02…`
* **Root cause:** see session report (S62-S65 spotlight reports) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Notes:** canonical harvested from docs/evidence/visual_forensics/s65_reval/fishrings/after_tap3_full.png

### FreeKlondike

* **Package / identity:** `eu.veldsoft.free.klondike` · type: game · version: —
* **Source:** [https://github.com/VelbazhdSoftwareLLC/FreeKlondike](https://github.com/VelbazhdSoftwareLLC/FreeKlondike)
* **APK SHA256:** `—`
* **Sessions:** S64 · status: **VERIFIED** · rendering: L10 (L10)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [eu.veldsoft.free.klondike.jpg](../docs/evidence/canonical/eu.veldsoft.free.klondike.jpg) · SHA256 `7dd689bf2d692980…`
* **Root cause:** see session report (S62-S65 spotlight reports) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Notes:** canonical harvested from docs/evidence/s64_spotlight/fk_game_deal_response.png

### No Thanks!

* **Package / identity:** `eu.veldsoft.no.thanks` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L1 (L1_NONBLANK)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-171 (APXACT depth underflow) + F-NEW-172 (FragmentActivity super-chain) + F-NEW-173 (ViewConfiguration object) + F-NEW-174 (beneath finisher) — all A/B-proven at S87 HEAD; remaining: savedstate adapter + TypedArray null · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** S87: SplashActivity inflates ConstraintLayout→WebView tree (was silent depth-underflow blank) → androidx.savedstate.Recreator_LifecycleAdapter CNFE (Lifecycling.generatedConstructor) + TypedArray.getIndexCount on null obtainStyledAttributes result (open)
* **Notes:** S87 source-first probe (vc1); upstream VelbazhdSoftwareLLC/No-Thanks-for-Android (veldsoft control: 3 sibling titles already render)

### TriPeaks

* **Package / identity:** `eu.veldsoft.tri.peaks` · type: game · version: —
* **Source:** [https://github.com/VelbazhdSoftwareLLC/TriPeaks](https://github.com/VelbazhdSoftwareLLC/TriPeaks)
* **APK SHA256:** `—`
* **Sessions:** S65 · status: **PARTIAL** · rendering: L10 (L10)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [eu.veldsoft.tri.peaks.jpg](../docs/evidence/canonical/eu.veldsoft.tri.peaks.jpg) · SHA256 `8e1d41a151898010…`
* **Root cause:** see session report (S62-S65 spotlight reports) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Last success / first divergence:** see S65 report → see session report
* **Notes:** canonical harvested from docs/evidence/visual_forensics/s65_reval/tripeaks/board_full.png

### io.github.divverent.aaaaxy

* **Package / identity:** `io.github.divverent.aaaaxy` · type: game · version: 1.7.239+20260804.4198.805e2a0b
* **Source:** [https://github.com/divVerent/aaaaxy](https://github.com/divVerent/aaaaxy)
* **APK SHA256:** `976ebc08571af97dcefc5feee2479eed47f0cbfc12b320f393462dfb50f077f3`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none — clean run at current HEAD · issue: —
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Ljava/lang/String;.equals' on a null object reference
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### io.github.ebraminio.bouncy

* **Package / identity:** `io.github.ebraminio.bouncy` · type: game · version: 0.0.1
* **Source:** [https://github.com/ebraminio/bouncy](https://github.com/ebraminio/bouncy)
* **APK SHA256:** `a509db2afda544f6da9620eb473319b0a034c6ffc8b6536e2a8a7bcc0f407f54`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L0 (LOADED_ONLY)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none (rc=0) · issue: —
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** full app-specific behavior beyond click probe
* **Last success / first divergence:** 8/8 frames captured, click pass executed → none
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=1 entropy=-0.0 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### io.github.hathibelagal.mykanji

* **Package / identity:** `io.github.hathibelagal.mykanji` · type: game · version: 1.6
* **Source:** [https://github.com/hathibelagal-dev/MyKanji](https://github.com/hathibelagal-dev/MyKanji)
* **APK SHA256:** `b20274a0885d03ba6947f82975c90e8415a4174dded8409e4798f92cb3a763a1`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L0 (LOADED_ONLY)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-171 (APXACT depth underflow) + F-NEW-172 (FragmentActivity super-chain) + F-NEW-173 (ViewConfiguration object) + F-NEW-174 (beneath finisher) — all A/B-proven at S87 HEAD; remaining: WebView asset content · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** full app-specific behavior beyond click probe
* **Last success / first divergence:** S87: root view tree inflates (LinearLayout → full-screen WebView); was silent depth-underflow blank → WebView content blank — local asset HTML not rendered (F085 WebView path exercised; content pipeline open)
* **Notes:** S87 source-first probe (vc7, APK SHA matches pin b20274a0885d03ba…); upstream hathibelagal-dev/MyKanji — main UI is a WebView over local HTML (upstream source read)

### io.github.johnathan.minesweeper

* **Package / identity:** `io.github.johnathan.minesweeper` · type: game · version: 1.5
* **Source:** [https://github.com/john-athan/minesweeper](https://github.com/john-athan/minesweeper)
* **APK SHA256:** `3b52a2fd21c4b4184eed1a1d4a9944e89bb9e7f99bf37329f03bd5eca962942e`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L1 (NONBLANK)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/io.github.johnathan.minesweeper/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=32 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.034 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### io.github.rotundtapir.fivehundred

* **Package / identity:** `io.github.rotundtapir.fivehundred` · type: game · version: 0.6.5
* **Source:** [https://github.com/rotundtapir/500](https://github.com/rotundtapir/500)
* **APK SHA256:** `db215475793097c05098ef541939274d789be75ee41924477381e75637dc99ee`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L1 → [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (androidx.savedstate.Recreator_LifecycleAdapter) method=Landroidx/lifecycle/Lifecycling;
* **Notes:** S85 NEW-50 (game); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Dooz (tic-tac-toe)

* **Package / identity:** `io.github.yamin8000.dooz` · type: game · version: —
* **Source:** F-Droid io.github.yamin8000.dooz
* **APK SHA256:** `d81292cd346dcb23b04488bca400ca95af0f6eaa4aefefd31f847fe535cbdc17`
* **Sessions:** S66/S83 · status: **OBSERVED** · rendering: L1 (L1_NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** R-NEW-344 family (OPEN): compose WindowRecomposer context chain — app paints a near-blank loading shell (white + tiny header line); R-NEW-403 fixed the pre-frame keySet NPE, recomposer chain is the next dependency. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** graphics completeness beyond L3
* **Last success / first divergence:** full lifecycle + real frames (S83) → none recorded in S83 session
* **Notes:** S85 audit: the restored s83b evidence was a near-blank loading shell (99.9% white) — demoted per S54 gate; no honest UI claim at HEAD.

### io.itch.pirate_solitaire

* **Package / identity:** `io.itch.pirate_solitaire` · type: game · version: 1.3
* **Source:** [https://github.com/Pheonyxior/Pirate-Solitaire-Git-Repo/tree/master](https://github.com/Pheonyxior/Pirate-Solitaire-Git-Repo/tree/master)
* **APK SHA256:** `b9fbe6023d8696b62f334085378a3ae3bc8f979d4d12698ce6facaed36bb02f8`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L0 (LOADED_ONLY)
* **Execution evidence:** launched=false · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/io.itch.pirate_solitaire/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=1 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=1 entropy=-0.0 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### ir.hsn6.tpb

* **Package / identity:** `ir.hsn6.tpb` · type: game · version: 1.0.1
* **Source:** [https://github.com/HassanHeydariNasab/2-player-battle](https://github.com/HassanHeydariNasab/2-player-battle)
* **APK SHA256:** `37ffc01c030e3d24eb2e2129c8f91684ac5c97251ca0101f2759e57fbebe6c7f`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Chess (jwtc)

* **Package / identity:** `jwtc.android.chess` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S87-source-probe · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** S87 re-probe vc298: 8 frames, near-blank class → TypedArray.hasValue on null obtainStyledAttributes result + Field.get null in obfuscated Lk3/a;.<clinit> (open)
* **Notes:** S87 re-probe at HEAD; upstream jcarolus/android-chess read (classic View board game; ChessBoardView is a plain onDraw Canvas — renders once TypedArray/obtainStyledAttributes law lands)

### name.boyle.chris.sgtpuzzles

* **Package / identity:** `name.boyle.chris.sgtpuzzles` · type: game · version: 2025-09-12-1919-23762278-fdroid
* **Source:** [https://github.com/chrisboyle/sgtpuzzles](https://github.com/chrisboyle/sgtpuzzles)
* **APK SHA256:** `6b36d5537984523c57984a784156eb853a92c940fded286483687484f3d652e4`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none — clean run at current HEAD · issue: —
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### net.sourceforge.solitaire_cg

* **Package / identity:** `net.sourceforge.solitaire_cg` · type: game · version: 4.1
* **Source:** [https://sourceforge.net/p/solitairecg/code](https://sourceforge.net/p/solitairecg/code)
* **APK SHA256:** `—`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none — clean run at current HEAD · issue: —
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Landroid/content/res/Resources;.getDisplayMetrics' on
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Navy Fleet Battle

* **Package / identity:** `net.tigr.navyfleetbattle` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) → none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### OPMT (One More Time…)

* **Package / identity:** `one.scarecrow.games.OPMT` · type: game · version: —
* **Source:** [https://github.com/scarecrowgames/OneMoreTimePuzzleGame](https://github.com/scarecrowgames/OneMoreTimePuzzleGame)
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **VERIFIED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [one.scarecrow.games.OPMT.jpg](../docs/evidence/canonical/one.scarecrow.games.OPMT.jpg) · SHA256 `17aa411b313a5aa2…`
* **Root cause:** PARTIAL · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** interaction + canonical artifact harvest
* **Notes:** S85 sweep promotion: prior PARTIAL → L2 render

### org.andstatus.game2048

* **Package / identity:** `org.andstatus.game2048` · type: game · version: 1.16.2
* **Source:** [https://github.com/andstatus/game2048](https://github.com/andstatus/game2048)
* **APK SHA256:** `2d6707624623fe8857da271dcc19511ab52472ce1fee6ac23bc7f2ecf2e7eea9`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Ljava/lang/Object;.getClass' on a null object referen
* **Notes:** S85 NEW-50 (game); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.asafonov.accelerace

* **Package / identity:** `org.asafonov.accelerace` · type: game · version: 0.12
* **Source:** [https://github.com/asafonov/accelerace.apk](https://github.com/asafonov/accelerace.apk)
* **APK SHA256:** `fe705a1599e6ce0c86f6a288bc361c9ffb3f6885dcfcc0baacca1921fe7a5a9e`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L0 (LOADED_ONLY)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none — clean run at current HEAD · issue: —
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L0 → none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.bobstuff.bobball

* **Package / identity:** `org.bobstuff.bobball` · type: game · version: 1.17
* **Source:** [https://github.com/bobthekingofegypt/BobBall](https://github.com/bobthekingofegypt/BobBall)
* **APK SHA256:** `fd43009a7ffdfaf84963487e2b3502bef63775a4eedd60d7040da70e658b3241`
* **Sessions:** S84 · status: **VERIFIED-INTERACTIVE** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=true · state_changed=true
* **Canonical screenshot:** [org.bobstuff.bobball.gif](../docs/evidence/canonical/org.bobstuff.bobball.gif) · SHA256 `788ce033de1ae0c3…`
* **Root cause:** none (rc=0) · issue: —
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** full app-specific behavior beyond click probe
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=6 state_changed=6. unique_colors=57 entropy=0.672 resources(dex/classes)=?

### org.lufebe16.pysolfc

* **Package / identity:** `org.lufebe16.pysolfc` · type: game · version: 1.2.1
* **Source:** [https://f-droid.org/en/packages/org.lufebe16.pysolfc/](https://f-droid.org/en/packages/org.lufebe16.pysolfc/)
* **APK SHA256:** `5b8ba9abc4c11ba0ebcc75d663f2b472704c00840ab564631feb0c84feb45664`
* **Sessions:** S84/S85 · status: **OBSERVED** · rendering: L1 (L1_NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** Kivy bootstrap family (honest PARTIAL): Color.parseColor('') IAE in PythonActivity.setBackgroundColor (faithful AOSP IAE on empty string — app input), AssetManager.open null recv, String.startsWith null recv inside org.kivy chains; frames render past the exceptions. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** Kivy runtime bootstrap chain
* **Last success / first divergence:** obs 8 frames @L2 (S85) → [SYNTH-EXC] S67 Color.parseColor (deferred): Ljava/lang/IllegalArgumentException; (Unknown color: ) method=Lorg/kivy/android/PythonActivity;.setBackgroundColor 
* **Notes:** S84 BLOCKED verdict was a TRUNCATED APK (74.6MB > 48MB cap) — re-downloaded vc102130601; renders L2 frames with Kivy bootstrap exceptions (honest PARTIAL). | S85 near-blank gate: rendered frames are the engine-default shell class; Kivy chain does not paint real UI yet. | Vocabulary: OBSERVED = loaded/ran with near-blank frames (S84 law); Kivy exceptions recorded in run/s85 logs.

### org.mattvchandler.a2050

* **Package / identity:** `org.mattvchandler.a2050` · type: game · version: 1.0.10
* **Source:** [https://github.com/mattvchandler/2050](https://github.com/mattvchandler/2050)
* **APK SHA256:** `98a0e75e589c319093db56cf98bfa32d920b9436a9cbe7c30b32dcf7a4a6d284`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke interface method 'Ljava/util/Iterator;.hasNext' on a null object refe
* **Notes:** S85 NEW-50 (game); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.og8.a1tox

* **Package / identity:** `org.og8.a1tox` · type: game · version: 1.00
* **Source:** [https://gitlab.com/og8org/1tox](https://gitlab.com/og8org/1tox)
* **APK SHA256:** `34895a84a638d53bd5ed57d134511eee9468f5461cb0e41874a1968ac256e4c8`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L0 (LOADED_ONLY)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none — clean run at current HEAD · issue: —
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L0 → none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Surge Engine (OpenSurge)

* **Package / identity:** `org.opensurge2d.surgeengine` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) → none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.secuso.privacyfriendly2048

* **Package / identity:** `org.secuso.privacyfriendly2048` · type: game · version: 1.4.2
* **Source:** [https://github.com/SecUSo/privacy-friendly-2048](https://github.com/SecUSo/privacy-friendly-2048)
* **APK SHA256:** `02c799d3d582669daf2acf920093c68d2933f60aa937bb72fa2a805557233fe8`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-171 (APXACT depth underflow) + F-NEW-172 (FragmentActivity super-chain) + F-NEW-173 (ViewConfiguration object) + F-NEW-174 (beneath finisher) — all A/B-proven at S87 HEAD; remaining: Glide engine loop (open) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** S87: secuso tutorial screen painted (uniq 160, Skip button; was engine-default blank) → F084 interpreter halt: infinite loop PC=0x2 in com.bumptech.glide.load.engine… + com.bumptech.glide.GeneratedAppGlideModuleImpl CNFE (deferred)
* **Notes:** S87 source-first probe (vc100, APK SHA matches pin 02c799d3d582669d…); upstream SecUSo/privacy-friendly-2048 (same pfacore scaffold as dame)

### PFBattleship

* **Package / identity:** `org.secuso.privacyfriendlybattleship` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) → none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.secuso.privacyfriendlydame

* **Package / identity:** `org.secuso.privacyfriendlydame` · type: game · version: 1.3.4
* **Source:** [https://github.com/SecUSo/privacy-friendly-dame](https://github.com/SecUSo/privacy-friendly-dame)
* **APK SHA256:** `41727c0121fef8ab760f34c348b04ccef5a41269f9a0f32516c50529cecd2b33`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-171 (APXACT depth underflow) + F-NEW-172 (FragmentActivity super-chain) + F-NEW-173 (ViewConfiguration object) + F-NEW-174 (beneath finisher) — all A/B-proven at S87 HEAD; remaining: pager page text render · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** S87: Splash→TutorialActivity real navigation + U007 inflate (6 views) + Skip/Next buttons painted (uniq 213; was engine-default blank) → ViewPager adapter page content (TextView text, page icon) not painted — TEXT_PIXELS=0 at frame_007 (open)
* **Notes:** S87 source-first probe (vc101, APK SHA matches S85 pin 41727c0121fef8ab…); upstream SecUSo/privacy-friendly-dame read (BaseActivity→pfacore DrawerActivity; SplashActivity routes then finish()); S54 gate: no artifact until L2+

### org.secuso.privacyfriendlymemory

* **Package / identity:** `org.secuso.privacyfriendlymemory` · type: game · version: 1.1.3-google
* **Source:** [https://github.com/SecUSo/privacy-friendly-memo-game](https://github.com/SecUSo/privacy-friendly-memo-game)
* **APK SHA256:** `82f83d9ea572240acabe45bcff9809f724d26f474896b150dcfd49d84037d8c6`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none — clean run at current HEAD · issue: —
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.secuso.privacyfriendlysolitaire

* **Package / identity:** `org.secuso.privacyfriendlysolitaire` · type: game · version: 1.1
* **Source:** [https://github.com/SecUSo/privacy-friendly-solitaire](https://github.com/SecUSo/privacy-friendly-solitaire)
* **APK SHA256:** `b0e2adf991f949821fb28389b7c91ea2e1f743dc22c47a5738bc5980b66603ae`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none — clean run at current HEAD · issue: —
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.secuso.privacyfriendlysudoku

* **Package / identity:** `org.secuso.privacyfriendlysudoku` · type: game · version: 3.2.6
* **Source:** [https://github.com/SecUSo/privacy-friendly-sudoku](https://github.com/SecUSo/privacy-friendly-sudoku)
* **APK SHA256:** `1aff917f4ac9952bd956f2b19589787b015decc23b4c13268d19f1437c68b5b3`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none — clean run at current HEAD · issue: —
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org99managers.futsal_edition

* **Package / identity:** `org99managers.futsal_edition` · type: game · version: v0.8.5
* **Source:** [https://codeberg.org/dulvui/99managers-futsal-edition/](https://codeberg.org/dulvui/99managers-futsal-edition/)
* **APK SHA256:** `c9eeea657951f694067f125222dea62f5a7a5c88e44d9c4b2c75de5e5ae5aab1`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Landroid/content/res/AssetManager;.open' on a null ob
* **Notes:** S85 NEW-50 (game); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Guandan

* **Package / identity:** `page.codeberg.lanticy.guandan` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran → near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (games__page.codeberg.lanticy.guandan_7__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### TheXTech (SuperTux-like)

* **Package / identity:** `ru.wohlsoft.thextech.fdroid` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) → none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Tarok

* **Package / identity:** `si.palcka.tarok` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) → none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### x653.all_in_gold

* **Package / identity:** `x653.all_in_gold` · type: game · version: 1.2
* **Source:** [https://gitlab.com/x653/all_in_gold](https://gitlab.com/x653/all_in_gold)
* **APK SHA256:** `01f04f99173ead827a6669a2fcd0625331bc0a68bcfa8684b87d0990fa7f9bae`
* **Sessions:** S85 · status: **VERIFIED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [x653.all_in_gold.jpg](../docs/evidence/canonical/x653.all_in_gold.jpg) · SHA256 `658d0a2825cce720…`
* **Root cause:** none — clean run at current HEAD · issue: —
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** state-change evidence
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0

### xyz.deepdaikon.quinb

* **Package / identity:** `xyz.deepdaikon.quinb` · type: game · version: —
* **Source:** 
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** no prior root cause — rendered at current HEAD · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) → none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### uNote

* **Package / identity:** `app.varlorg.unote` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `be91103f0e7db44361de5e918d9130dab4ac137bab5bd946a0fd8dab88bc2cc0`
* **Sessions:** S83 · status: **VERIFIED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [app.varlorg.unote.jpg](../docs/evidence/canonical/app.varlorg.unote.jpg) · SHA256 `0926d80c165221c8…`
* **Root cause:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** graphics completeness beyond L3
* **Notes:** S83 real-screenshot campaign evidence (apps__app.varlorg.unote_30__L2_GRAPHICALLY_INCOMPLETE.jpg)

### at.techbee.jtx

* **Package / identity:** `at.techbee.jtx` · type: app · version: 2.17.00.ose
* **Source:** [https://github.com/TechbeeAT/jtxBoard](https://github.com/TechbeeAT/jtxBoard)
* **APK SHA256:** `92fbd67fd935b52bba9e04003e9d6dc8235bb5c66e48dcf77af41c0e660b0c9e`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none — clean run at current HEAD · issue: —
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Lnet/fortuna/ical4j/model/TimeZoneRegistryFactory;.cr
* **Notes:** S85 NEW-50 (app); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.aurora.store

* **Package / identity:** `com.aurora.store` · type: app · version: 4.8.4
* **Source:** [https://gitlab.com/AuroraOSS/AuroraStore](https://gitlab.com/AuroraOSS/AuroraStore)
* **APK SHA256:** `fd9c75d90d0f4a7c132b9b4a5a2cf1992a45e03b8d8ff988b7dcfbc0db2c4d11`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L1 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Ljava/lang/Object;.getClass' on a null object referen
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.beemdevelopment.aegis

* **Package / identity:** `com.beemdevelopment.aegis` · type: app · version: 3.4.3
* **Source:** [https://github.com/beemdevelopment/Aegis](https://github.com/beemdevelopment/Aegis)
* **APK SHA256:** `0eecec45de0da3ff1358004b51e2960d9178551643a6ed44f6496ea9ec999c19`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L1 → [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (kotlin.reflect.jvm.internal.ReflectionFactoryImpl) method=Lkotlin/jvm/internal/Reflecti
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### DeskClock

* **Package / identity:** `com.best.deskclock` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran → near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (apps__com.best.deskclock_2036__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### Bnyro Clock

* **Package / identity:** `com.bnyro.clock` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran → near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (apps__com.bnyro.clock_24__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### PMK-61 Calculator

* **Package / identity:** `com.cax.pmk` · type: app · version: —
* **Source:** [https://github.com/xvadim/pmk-android](https://github.com/xvadim/pmk-android)
* **APK SHA256:** `—`
* **Sessions:** S64 · status: **VERIFIED** · rendering: L6 (L6)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [com.cax.pmk.jpg](../docs/evidence/canonical/com.cax.pmk.jpg) · SHA256 `245ae472e4b390d1…`
* **Root cause:** see session report (S62-S65 spotlight reports) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Notes:** canonical harvested from docs/evidence/s64_spotlight/pmk_frame0_indicator.png

### Chess Clock

* **Package / identity:** `com.chessclock.android` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `5ca6f2c54c05efe7df72b209988037b97e37be0faae133624ec352057445fafa`
* **Sessions:** S83 · status: **VERIFIED** · rendering: L0 (L0_LOADED_ONLY)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** [com.chessclock.android.jpg](../docs/evidence/canonical/com.chessclock.android.jpg) · SHA256 `c3209486dd0ab332…`
* **Root cause:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** graphics completeness beyond L3
* **Notes:** S83 real-screenshot campaign evidence (apps__com.chessclock.android_29__L0_LOADED_ONLY.jpg)

### com.drdisagree.colorblendr

* **Package / identity:** `com.drdisagree.colorblendr` · type: app · version: v3.0.1
* **Source:** [https://github.com/Mahmud0808/ColorBlendr](https://github.com/Mahmud0808/ColorBlendr)
* **APK SHA256:** `a30ea8f14ea9d6349381fc2b6d537b19c137e4762dc58713da18a8af91700045`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Ljava/lang/String;.split' on a null object reference)
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.forrestguice.suntimeswidget

* **Package / identity:** `com.forrestguice.suntimeswidget` · type: app · version: 0.17.5
* **Source:** [https://github.com/forrestguice/SuntimesWidget](https://github.com/forrestguice/SuntimesWidget)
* **APK SHA256:** `bd0fbe51f684895d8e1778203875cd0850af5387ec036811c540b13ce3ec0a11`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none (rc=0) · issue: —
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** full app-specific behavior beyond click probe
* **Last success / first divergence:** 8/8 frames captured, click pass executed → none
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.fsck.k9

* **Package / identity:** `com.fsck.k9` · type: app · version: 23.0
* **Source:** [https://github.com/thunderbird/thunderbird-android](https://github.com/thunderbird/thunderbird-android)
* **APK SHA256:** `92cd3a81c7a8d066e517a50932fe85424de7752cb72e76032174d53ec36a2741`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (kotlin.reflect.jvm.internal.ReflectionFactoryImpl) method=Lkotlin/jvm/internal/Reflecti
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.gh4a

* **Package / identity:** `com.gh4a` · type: app · version: 4.6.15
* **Source:** [https://github.com/slapperwan/gh4a](https://github.com/slapperwan/gh4a)
* **APK SHA256:** `66711fd47c0c0e651bbe67c06f5c6f8864f1470cfa49fdc9a7f423e288e30e93`
* **Sessions:** S85 · status: **VERIFIED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [com.gh4a.jpg](../docs/evidence/canonical/com.gh4a.jpg) · SHA256 `29a8df4536d8222e…`
* **Root cause:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** state-change evidence
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1

### com.hegocre.nextcloudpasswords

* **Package / identity:** `com.hegocre.nextcloudpasswords` · type: app · version: 1.2.1
* **Source:** [https://github.com/hegocre/NextcloudPasswords](https://github.com/hegocre/NextcloudPasswords)
* **APK SHA256:** `b8ee43950d3fd8473a78e85494af0800f9f0ba50be49a1d55aff8362ab2d4b9c`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/com.hegocre.nextcloudpasswords/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=5 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.hfut.schedule

* **Package / identity:** `com.hfut.schedule` · type: app · version: 4.21.1
* **Source:** [https://github.com/Chiu-xaH/HFUT-Schedule](https://github.com/Chiu-xaH/HFUT-Schedule)
* **APK SHA256:** `bc2b586a58bd6eba4641c5509e9d2f1c55b32f952b5820295ecc08838a3534db`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L1 (NONBLANK)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/com.hfut.schedule/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=32 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.034 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.jherkenhoff.qalculate

* **Package / identity:** `com.jherkenhoff.qalculate` · type: app · version: 0.2.1
* **Source:** [https://github.com/jherkenhoff/qalculate-android](https://github.com/jherkenhoff/qalculate-android)
* **APK SHA256:** `31366f4dd3e750e56f6667af195d1a9d8b16e11fff4b967df759082f65d9b1dd`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L1 (NONBLANK)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/com.jherkenhoff.qalculate/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=32 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.007 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.justdeax.composeStopwatch

* **Package / identity:** `com.justdeax.composeStopwatch` · type: app · version: 1.9.1
* **Source:** [https://github.com/JustDeax/ComposeStopwatch](https://github.com/JustDeax/ComposeStopwatch)
* **APK SHA256:** `dbf937ebbe7c0b3d24c07fa0ede7cb53ea117f7071db3b61f1c96b7d257cda55`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L1 (NONBLANK)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/com.justdeax.composeStopwatch/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=5 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.034 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.kompact

* **Package / identity:** `com.kompact` · type: app · version: 2.0.0
* **Source:** [https://git.naxod.com/luca/Kompact](https://git.naxod.com/luca/Kompact)
* **APK SHA256:** `9aacd0015ccd9aadab99b986f3c6e94da608aca692d01f43a6ebff9e612bb236`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/com.kompact/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=11 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.kunzisoft.keepass.libre

* **Package / identity:** `com.kunzisoft.keepass.libre` · type: app · version: 4.5.4
* **Source:** [https://github.com/Kunzisoft/KeePassDX](https://github.com/Kunzisoft/KeePassDX)
* **APK SHA256:** `862f87a30baef06181f049adf7c460611605b25a807eaf3c25841a9dd84bed9e`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (kotlin.reflect.jvm.internal.ReflectionFactoryImpl) method=Lkotlin/jvm/internal/Reflecti
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.ma.tehro

* **Package / identity:** `com.ma.tehro` · type: app · version: 1.5.0
* **Source:** [https://github.com/mosayeb-a/tehran-metro](https://github.com/mosayeb-a/tehran-metro)
* **APK SHA256:** `f5dbd2a88dfe9e64f813728b62701e19974cf0acf1d85b8b17f7da47df9317dd`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L1 (NONBLANK)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/com.ma.tehro/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=3 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.007 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.maltaisn.notes.sync

* **Package / identity:** `com.maltaisn.notes.sync` · type: app · version: 1.6.2
* **Source:** [https://github.com/maltaisn/another-notes-app/](https://github.com/maltaisn/another-notes-app/)
* **APK SHA256:** `176deff1189734d014a8078d8221ae8b249ef1b042bd12837067265f1fb47d46`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (kotlin.reflect.jvm.internal.ReflectionFactoryImpl) method=Lx2/r;.<clinit> pc=3 → deferr
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### NewsBlur

* **Package / identity:** `com.newsblur` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S87-source-probe · status: **OBSERVED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** S87 re-probe vc289: 8 frames, near-blank class → Cursor.moveToNext on null (SQLiteDatabase query path) ×deferred + AtomicReferenceFieldUpdater REC-MISS storm (open)
* **Notes:** S87 re-probe at HEAD (text-heavy heavy app control); upstream samuelclay/NewsBlur; SQLite cursor law is the first divergence

### com.nononsenseapps.notepad

* **Package / identity:** `com.nononsenseapps.notepad` · type: app · version: 7.2.6
* **Source:** [https://github.com/spacecowboy/NotePad](https://github.com/spacecowboy/NotePad)
* **APK SHA256:** `ed44d7aff78498a598ac92e831c859649281c8cdbd4d0e17130cbdde80755114`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L0 (LOADED_ONLY)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L0 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke interface method 'Ljava/util/List;.contains' on a null object referen
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.sebiai.glyphport

* **Package / identity:** `com.sebiai.glyphport` · type: app · version: 2.0.3
* **Source:** [https://github.com/SebiAi/GlyphPort](https://github.com/SebiAi/GlyphPort)
* **APK SHA256:** `c95f8ca470b565fc3fff2249006ca4e70afbffa987140cf68ce22199afba8280`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L1 → [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (kotlin.reflect.jvm.internal.ReflectionFactoryImpl) method=Lw5/t;.<clinit> pc=3 → deferr
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.trianguloy.urlchecker

* **Package / identity:** `com.trianguloy.urlchecker` · type: app · version: 3.5
* **Source:** [https://github.com/TrianguloY/UrlChecker](https://github.com/TrianguloY/UrlChecker)
* **APK SHA256:** `ddcbf344519bff30db9550d16f37104150b816ed401f95370d551f183a9e5520`
* **Sessions:** S85 · status: **VERIFIED-INTERACTIVE** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=true · state_changed=true
* **Canonical screenshot:** [com.trianguloy.urlchecker.gif](../docs/evidence/canonical/com.trianguloy.urlchecker.gif) · SHA256 `ba1ae97c8e92dcf6…`
* **Root cause:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** compose/runtime init (see root cause)
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1; probed=6; engine_state_changed=6

### com.vagujhelyigergely.calculatorm3

* **Package / identity:** `com.vagujhelyigergely.calculatorm3` · type: app · version: 1.5.2
* **Source:** [https://github.com/gergelyvagujhelyi/CalculatorM3](https://github.com/gergelyvagujhelyi/CalculatorM3)
* **APK SHA256:** `b224f071f7d34f7682ff048ce469f1fc196a4a005143e763875e27690bd9d955`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L1 (NONBLANK)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. |  · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/com.vagujhelyigergely.calculatorm3/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=0 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.007 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.vayunmathur.clock

* **Package / identity:** `com.vayunmathur.clock` · type: app · version: v2.6.4
* **Source:** [https://github.com/vayun-mathur/Modern-Apps](https://github.com/vayun-mathur/Modern-Apps)
* **APK SHA256:** `143f8f74374864347a8f4ebcbc063d37b5a6ffb29c8f58b2c5d6ee302d7cf335`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/com.vayunmathur.clock/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=11 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### de.danoeh.antennapod

* **Package / identity:** `de.danoeh.antennapod` · type: app · version: 3.12.2
* **Source:** [https://github.com/AntennaPod/AntennaPod](https://github.com/AntennaPod/AntennaPod)
* **APK SHA256:** `3f43a4337a693cdb49141afe06cb596e88c796009ed77bff51e9444ce2d1ebfc`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (android.os.Looper) method=Lorg/greenrobot/eventbus/android/AndroidDependenciesDetector;
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### GameMasterDice

* **Package / identity:** `de.duenndns.gmdice` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `1621eda11b5dbc0c232b54c652d27aeab2f8a3c95be2c1f0632d6233b12d8a85`
* **Sessions:** S63/S83 · status: **VERIFIED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [de.duenndns.gmdice.jpg](../docs/evidence/canonical/de.duenndns.gmdice.jpg) · SHA256 `1f38135926fa07e4…`
* **Root cause:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** graphics completeness beyond L3
* **Notes:** S83 real-screenshot campaign evidence (apps__de.duenndns.gmdice_8__L2_GRAPHICALLY_INCOMPLETE.jpg)

### de.markusfisch.android.binaryeye

* **Package / identity:** `de.markusfisch.android.binaryeye` · type: app · version: 1.75.4
* **Source:** [https://github.com/markusfisch/BinaryEye](https://github.com/markusfisch/BinaryEye)
* **APK SHA256:** `428c26249c706bd79610d03a1a985dcc0efd9dd5469fc9be92c703459a4d5f93`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Landroid/content/res/TypedArray;.hasValue' on a null 
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### de.schildbach.wallet

* **Package / identity:** `de.schildbach.wallet` · type: app · version: 11.03
* **Source:** [https://gitlab.com/bitcoin-wallet/bitcoin-wallet](https://gitlab.com/bitcoin-wallet/bitcoin-wallet)
* **APK SHA256:** `bc6d078854a74281e2ad07d5a7bc5ff68a322a809eb1e0bade1e4549e8f00090`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Ljava/util/ServiceLoader;.iterator' on a null object 
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### de.seemoo.at_tracking_detection

* **Package / identity:** `de.seemoo.at_tracking_detection` · type: app · version: 3.1.2
* **Source:** [https://github.com/seemoo-lab/AirGuard](https://github.com/seemoo-lab/AirGuard)
* **APK SHA256:** `583fc839caff840e7735dfeb28dd5a586e1fec101661e38db7eebb5b120907d4`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/de.seemoo.at_tracking_detection/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=20 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### de.taz.android.app.free

* **Package / identity:** `de.taz.android.app.free` · type: app · version: 2.1.2
* **Source:** [https://github.com/die-tageszeitung/taz-neo](https://github.com/die-tageszeitung/taz-neo)
* **APK SHA256:** `86f14e1101e7f98952bc402234a7223e99a9defa100a4e12918ee3d88192e448`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/de.taz.android.app.free/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=32 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### dev.lexip.hecate

* **Package / identity:** `dev.lexip.hecate` · type: app · version: 2.5.1
* **Source:** [https://github.com/xLexip/Adaptive-Theme](https://github.com/xLexip/Adaptive-Theme)
* **APK SHA256:** `7e98bf1cf2a9e4a4466bb71989918309d75b9fbeed026b42f04ce77e9d272d40`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L1 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Ljava/lang/Object;.getClass' on a null object referen
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### MicroTimer

* **Package / identity:** `dubrowgn.microtimer` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `79c6f730f64886e7b6561c2eed1a4420201e6e44a53b635dbb14c0689fd19828`
* **Sessions:** S83 · status: **VERIFIED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [dubrowgn.microtimer.jpg](../docs/evidence/canonical/dubrowgn.microtimer.jpg) · SHA256 `060e42e488c0f17e…`
* **Root cause:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** graphics completeness beyond L3
* **Notes:** S83 real-screenshot campaign evidence (apps__dubrowgn.microtimer_8__L2_GRAPHICALLY_INCOMPLETE.jpg)

### eu.faircode.email

* **Package / identity:** `eu.faircode.email` · type: app · version: 1.2337
* **Source:** [https://github.com/M66B/FairEmail](https://github.com/M66B/FairEmail)
* **APK SHA256:** `1e59bd1d82ccdf0af90e7a29e7cb219eaa189031675b376578e7da8ec649e539`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Landroid/content/Context;.getFilesDir' on a null obje
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### foehnix.widget

* **Package / identity:** `foehnix.widget` · type: app · version: 4.0
* **Source:** [https://github.com/dzmanto/foehnix](https://github.com/dzmanto/foehnix)
* **APK SHA256:** `960913f40cefe5f4542554ef603305586b87ca0b03b25f28f09abeec7a9cf857`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none (rc=0) · issue: —
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** full app-specific behavior beyond click probe
* **Last success / first divergence:** 8/8 frames captured, click pass executed → none
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### fr.corenting.convertisseureurofranc

* **Package / identity:** `fr.corenting.convertisseureurofranc` · type: app · version: 2.19
* **Source:** [https://github.com/corenting/InflationCalculator](https://github.com/corenting/InflationCalculator)
* **APK SHA256:** `257295104823c97039995d60af839d5c4681a0d6840b00486fe674d78b0d1cfe`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/fr.corenting.convertisseureurofranc/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=32 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### io.github.aoc_normal

* **Package / identity:** `io.github.aoc_normal` · type: app · version: 1.0
* **Source:** [https://archive.softwareheritage.org/browse/origin/https://github.com/Raidenxd2/always_on_clock_normal/directory/](https://archive.softwareheritage.org/browse/origin/https://github.com/Raidenxd2/always_on_clock_normal/directory/)
* **APK SHA256:** `7d049e2276f0c1ae46775e1d8cc897fb57e700c64e071cf843198e9532d9a0dc`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L0 (LOADED_ONLY)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none (rc=0) · issue: —
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** full app-specific behavior beyond click probe
* **Last success / first divergence:** 8/8 frames captured, click pass executed → none
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=1 entropy=-0.0 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### Shopping List Calc

* **Package / identity:** `io.github.buildsbyben.shoppinglistcalc` · type: app · version: —
* **Source:** [https://github.com/buildsbyben/shopping-list-calc](https://github.com/buildsbyben/shopping-list-calc)
* **APK SHA256:** `—`
* **Sessions:** S64 · status: **VERIFIED** · rendering: L9 (L9)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [io.github.buildsbyben.shoppinglistcalc.jpg](../docs/evidence/canonical/io.github.buildsbyben.shoppinglistcalc.jpg) · SHA256 `57b3ca45c8ff83c6…`
* **Root cause:** see session report (S62-S65 spotlight reports) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Notes:** canonical harvested from docs/evidence/s64_spotlight/sc_after_click.png

### TimeLimit

* **Package / identity:** `io.timelimit.android.aosp.direct` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 HIGH · status: **OBSERVED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran → near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (high__io.timelimit.android.aosp.direct_231__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### it.niedermann.nextcloud.deck

* **Package / identity:** `it.niedermann.nextcloud.deck` · type: app · version: 1.26.3
* **Source:** [https://github.com/stefan-niedermann/nextcloud-deck](https://github.com/stefan-niedermann/nextcloud-deck)
* **APK SHA256:** `e7152b3062658082f5abdf7bdfdbb90c170155f557f598a799d0c9967dfaa6d5`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Ljava/util/concurrent/CompletableFuture;.thenAcceptAs
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### me.river.nightbell

* **Package / identity:** `me.river.nightbell` · type: app · version: 3.13.0
* **Source:** [https://github.com/riveerxd/nightbell](https://github.com/riveerxd/nightbell)
* **APK SHA256:** `e4972ad68a1550339edb71bab866bd32d045057c85349ee857954b107eed8fe1`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L1 (NONBLANK)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/me.river.nightbell/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=23 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.007 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### me.timeto.app

* **Package / identity:** `me.timeto.app` · type: app · version: 2026.09.19
* **Source:** [https://github.com/Medvedev91/timeto.me](https://github.com/Medvedev91/timeto.me)
* **APK SHA256:** `cff24d4b5043e2683c5de425662ad6723cce99aee55af35b142d496f4b762191`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L1 (NONBLANK)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/me.timeto.app/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=32 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.007 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### Simple Stopwatch

* **Package / identity:** `omegacentauri.mobi.simplestopwatch` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `b3ec1a5ec24ce53bf5c2322eaf79b00c52f021ed7a0ada9d58fae31dcffc83d2`
* **Sessions:** S64/S83 · status: **VERIFIED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [omegacentauri.mobi.simplestopwatch.jpg](../docs/evidence/canonical/omegacentauri.mobi.simplestopwatch.jpg) · SHA256 `60c1f2f03ca5d9c6…`
* **Root cause:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** graphics completeness beyond L3
* **Notes:** S83 real-screenshot campaign evidence (apps__omegacentauri.mobi.simplestopwatch_26__L2_GRAPHICALLY_INCOMPLETE.jpg)

### Notes (billthefarmer)

* **Package / identity:** `org.billthefarmer.notes` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `82cf8bc44c16374897665dabcd33e78715e801af48373b45b9c41e85e55e64ef`
* **Sessions:** S83 · status: **VERIFIED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [org.billthefarmer.notes.jpg](../docs/evidence/canonical/org.billthefarmer.notes.jpg) · SHA256 `c67b0f528032b839…`
* **Root cause:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** graphics completeness beyond L3
* **Notes:** S83 real-screenshot campaign evidence (apps__org.billthefarmer.notes_139__L2_GRAPHICALLY_INCOMPLETE.jpg)

### SigGen

* **Package / identity:** `org.billthefarmer.siggen` · type: app · version: —
* **Source:** [https://github.com/billthefarmer/sig-gen](https://github.com/billthefarmer/sig-gen)
* **APK SHA256:** `—`
* **Sessions:** S63 · status: **PARTIAL** · rendering: L5 (L5)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [org.billthefarmer.siggen.jpg](../docs/evidence/canonical/org.billthefarmer.siggen.jpg) · SHA256 `338c5a8687d371c2…`
* **Root cause:** see session report (S62-S65 spotlight reports) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Last success / first divergence:** see S63 report → see session report
* **Notes:** canonical harvested from docs/evidence/s63_spotlight/siggen_frame0.png

### Heading Calculator

* **Package / identity:** `org.debian.eugen.headingcalculator` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `274ec873098eea512e10aa6915d2a832a5a178a65ee7931bc101fe4832983f93`
* **Sessions:** S83 · status: **VERIFIED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [org.debian.eugen.headingcalculator.jpg](../docs/evidence/canonical/org.debian.eugen.headingcalculator.jpg) · SHA256 `4de2a3f8f8b8c429…`
* **Root cause:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** graphics completeness beyond L3
* **Notes:** S83 real-screenshot campaign evidence (apps__org.debian.eugen.headingcalculator_1__L2_GRAPHICALLY_INCOMPLETE.jpg)

### org.dystopia.email

* **Package / identity:** `org.dystopia.email` · type: app · version: 1.5.4
* **Source:** [https://framagit.org/dystopia-project/simple-email](https://framagit.org/dystopia-project/simple-email)
* **APK SHA256:** `e1545a2f2d3aab4b36c7f6ef6ac08a06fea37ac2de11415073cf7085917075b3`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Landroid/content/res/TypedArray;.hasValue' on a null 
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.fossify.clock

* **Package / identity:** `org.fossify.clock` · type: app · version: 1.6.0
* **Source:** [https://github.com/FossifyOrg/Clock](https://github.com/FossifyOrg/Clock)
* **APK SHA256:** `43cf9f0ec45f1f1ff2df47286622e5b8f3acedaeb07b7f7641b5243dbedca079`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (org.fossify.clock.App_LifecycleAdapter) method=Landroidx/lifecycle/y;.b pc=113 → deferr
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.fossify.gallery

* **Package / identity:** `org.fossify.gallery` · type: app · version: 1.13.1
* **Source:** [https://github.com/FossifyOrg/Gallery](https://github.com/FossifyOrg/Gallery)
* **APK SHA256:** `ae7e699599e81f70e2b82626bb1dfa883fe096cd938387133e123c116e5641d9`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] F084-HALT-RETURN (deferred): Ljava/lang/VirtualMachineError; (F084 interpreter halt in callee (no return value): Infinite loop at PC=0x7 in Loc/w;.r
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.fossify.notes

* **Package / identity:** `org.fossify.notes` · type: app · version: 1.7.0
* **Source:** [https://github.com/FossifyOrg/Notes](https://github.com/FossifyOrg/Notes)
* **APK SHA256:** `5a56e0e39cc488e1f3b947d3801006d3b7450ec73c67f03195c64c5fd3b6bced`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (kotlin.reflect.jvm.internal.ReflectionFactoryImpl) method=Lu4/w;.<clinit> pc=3 → deferr
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.nitri.opentopo

* **Package / identity:** `org.nitri.opentopo` · type: app · version: 1.38
* **Source:** [https://github.com/Pygmalion69/OpenTopoMapViewer](https://github.com/Pygmalion69/OpenTopoMapViewer)
* **APK SHA256:** `0fa0362afc6f8f0c95a43e9aa6dfa3e6891dca0755d043cbac08d63557c22da3`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/org.nitri.opentopo/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=19 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### org.secuso.privacyfriendlyactivitytracker

* **Package / identity:** `org.secuso.privacyfriendlyactivitytracker` · type: app · version: 3.1.2
* **Source:** [https://github.com/SecUSo/privacy-friendly-pedometer](https://github.com/SecUSo/privacy-friendly-pedometer)
* **APK SHA256:** `e4041cb724f97f4830ff0ae3e250cb5fd71a834bd72c4507f09cb7149fbf9047`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none — clean run at current HEAD · issue: —
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → none recorded
* **Notes:** S85 NEW-50 (app); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.secuso.privacyfriendlynotes

* **Package / identity:** `org.secuso.privacyfriendlynotes` · type: app · version: 2.2.2
* **Source:** [https://github.com/SecUSo/privacy-friendly-notes](https://github.com/SecUSo/privacy-friendly-notes)
* **APK SHA256:** `71e874f45fa4655f14296fce13791a82f994ea9bc26699f433383f0b4d334037`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none — clean run at current HEAD · issue: —
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → none recorded
* **Notes:** S85 NEW-50 (app); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.tasks

* **Package / identity:** `org.tasks` · type: app · version: 15.12
* **Source:** [https://github.com/tasks/tasks](https://github.com/tasks/tasks)
* **APK SHA256:** `ed972cc1cec3456a11992435a3fcf132d1311f1e8dfd27758265122fbc206ce0`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Ljava/util/logging/Logger;.setUseParentHandlers' on a
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Telegram

* **Package / identity:** `org.telegram.messenger.web` · type: app · version: 12.10.3 (vc70899)
* **Source:** [https://github.com/DrKLO/Telegram](https://github.com/DrKLO/Telegram)
* **APK SHA256:** `b6a13e876a8abfde867d8dcfed6ecc93198329aef8e5b860ae0ab7fc0c64beb8`
* **Sessions:** S85 (review: EXP-064..071 / MC4 / S74-ops / S85) · status: **OBSERVED** · rendering: L1 (L1_NONBLANK)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** Telegram app-init frontier (honest OBSERVED): multi-week native/TLS init chain; S85 divergence moved past S74 j$/stream + FragmentManager to ActionBarLayout.e0 List.isEmpty ×11 + ImageLoader cacheDirs File.isDirectory null ×9 (static-init chains not completed). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames render app shell only)
* **Remaining:** ImageLoader/ActionBarLayout static-init chains; native libs; TLS networking
* **Last success / first divergence:** launch + shell frames (S85) → ImageLoader.<init> pc=310 File.isDirectory null
* **Notes:** User-requested re-review at current HEAD: 10 frames L1 NONBLANK, rc=1, 29 deferred NPEs (ImageLoader cacheDirs File.isDirectory null ×9, ActionBarLayout List.isEmpty ×11). History: EXP-064..071 login UI + page transition; MC4 v12.10.1 parse/launch/themed-window; S74 v12.10.3 engine-default black. SHA matches S74 pin (b6a13e87…).

### org.y20k.transistor

* **Package / identity:** `org.y20k.transistor` · type: app · version: 4.3.9
* **Source:** [https://codeberg.org/y20k/transistor](https://codeberg.org/y20k/transistor)
* **APK SHA256:** `762f4fe86bca8a66e30a41d5ada92e5d76b2c6bddbbdc09ae505e595cf0a9da3`
* **Sessions:** S85 · status: **OBSERVED** · rendering: L1 (NONBLANK_NEARBLANK_GATE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented. · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 → [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Ljava/lang/Boolean;.booleanValue' on a null object re
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### P9 (tube42)

* **Package / identity:** `se.tube42.p9.android` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S81/S83 · status: **OBSERVED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran → near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (apps__se.tube42.p9.android_11__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### site.leos.apps.lespas

* **Package / identity:** `site.leos.apps.lespas` · type: app · version: 2.11.5
* **Source:** [https://github.com/scubajeff/lespas](https://github.com/scubajeff/lespas)
* **APK SHA256:** `be129b43f84752e4af2ea2475b68134fbf0bdab17ba5d65fe742e6621fffb640`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L1 (NONBLANK)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/site.leos.apps.lespas/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=14 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.034 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### tibarj.tranquilstopwatch

* **Package / identity:** `tibarj.tranquilstopwatch` · type: app · version: 1.12.1
* **Source:** [https://github.com/tibarj/tranquilstopwatch](https://github.com/tibarj/tranquilstopwatch)
* **APK SHA256:** `7bc31fae5cd2e9d815414dafb437f9a9a2fd21f4dc16d9929adc5fec962c5cb7`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=false · rendered=true · interacted=true · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED/INTERACTED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/tibarj.tranquilstopwatch/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=20 frames=8/8 click: probed=2 state_changed=0. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### TicTacToe3D self-aware fixture

* **Package / identity:** `org.miniandroid.helloworld` · type: fixture · version: —
* **Source:** [https://github.com/Applibered/HelloWorldSelfAware](https://github.com/Applibered/HelloWorldSelfAware)
* **APK SHA256:** `—`
* **Sessions:** S45 · status: **VERIFIED** · rendering: L6 (L6)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [org.miniandroid.helloworld.jpg](../docs/evidence/canonical/org.miniandroid.helloworld.jpg) · SHA256 `83720c1028f832d0…`
* **Root cause:** see session report (S62-S65 spotlight reports) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Notes:** canonical harvested from docs/evidence/external_hello_golden

