# MiniAndroid — App & Game Achievements

> **CANONICAL, ONE RECORD PER TITLE** (S84 law, 2026-09-23).
> This file is the single source of truth for what each app and
> game has PROVEN on MiniAndroid. Historical per-wave narrative
> moved to [ACHIEVEMENTS_WAVE_HISTORY.md](history/ACHIEVEMENTS_WAVE_HISTORY.md).
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

- Titles: **96** (61 games, 34 apps, 1 fixtures) — 50 added in S84
- VERIFIED: **29** · VERIFIED-INTERACTIVE: **9** · PARTIAL: **3** · BLOCKED: **1**
- Rendered: 68 · Interacted: 11 · State-change proven: 9
- Canonical screenshots: **96** (9 GIF + 23 JPG) — one per title, zero duplicates

---

### Halma

* **Package / identity:** `app.halma` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran → near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (games__app.halma_15__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### bim.app

* **Package / identity:** `bim.app` · type: game · version: 16
* **Source:** [https://github.com/j-jorge/bim/](https://github.com/j-jorge/bim/)
* **APK SHA256:** `82b5ba2e96dc551903b4b818a96ca8e46dfd31427ae422708b2aaaeada84b5a6`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/bim.app/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=1 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

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
* **Sessions:** S62+ · status: **VERIFIED** · rendering: L5 (L5)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [ch.logixisland.anuto.jpg](../docs/evidence/canonical/ch.logixisland.anuto.jpg) · SHA256 `f876a103e2eae2f1…`
* **Root cause:** see session report (S62-S65 spotlight reports) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Notes:** canonical harvested from docs/evidence/s62plus_spotlight/anuto_frame0_after_onDraw.png

### Astroloop

* **Package / identity:** `com.astroloop.game` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran → near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (games__com.astroloop.game_4__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### Tirailleur

* **Package / identity:** `com.bupkis.tirailleur` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran → near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (games__com.bupkis.tirailleur_13__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

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
* **APK SHA256:** `—`
* **Sessions:** S62/S74 · status: **VERIFIED** · rendering: L5 (L5)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [com.dozingcatsoftware.bouncy.jpg](../docs/evidence/canonical/com.dozingcatsoftware.bouncy.jpg) · SHA256 `5543ab86e0fb4e0f…`
* **Root cause:** see session report (S62-S65 spotlight reports) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Notes:** canonical harvested from docs/evidence/s74_ops/bouncy

### com.dozingcatsoftware.dodge

* **Package / identity:** `com.dozingcatsoftware.dodge` · type: game · version: 1.5.1
* **Source:** [https://github.com/dozingcat/dodge-android](https://github.com/dozingcat/dodge-android)
* **APK SHA256:** `a5687d1bad7b2927740a55b7b1df11efc81edcad03f0633ab5c2e5c58b120541`
* **Sessions:** S84 · status: **VERIFIED-INTERACTIVE** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=false · rendered=true · interacted=true · state_changed=true
* **Canonical screenshot:** [com.dozingcatsoftware.dodge.gif](../docs/evidence/canonical/com.dozingcatsoftware.dodge.gif) · SHA256 `3ca88c8da8a90bc3…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Notes:** S84 NEW title. rc_obs=1 errors=4 frames=8/8 click: probed=7 state_changed=6. unique_colors=52 entropy=1.685 resources(dex/classes)=?

### Firestrike

* **Package / identity:** `com.eightsines.firestrike.opensource` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran → near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (games__com.eightsines.firestrike.opensource_2000__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

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

* **Package / identity:** `com.galaxyrio.sudokusolver` · type: game · version: 2.1.0
* **Source:** [https://github.com/Galaxy-rio/SudokuYou](https://github.com/Galaxy-rio/SudokuYou)
* **APK SHA256:** `b211e022ce0c7001e42d8ae82fa0dcd671e071bc5f78103f0f8e0f3939158d3a`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/com.galaxyrio.sudokusolver/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=9 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

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
* **Sessions:** S83 · status: **VERIFIED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
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

### TicTacToe Deluxe (دوز)

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

### com.octbit.rutmath

* **Package / identity:** `com.octbit.rutmath` · type: game · version: 0.2.5
* **Source:** [https://github.com/przemarbor/RUTMath](https://github.com/przemarbor/RUTMath)
* **APK SHA256:** `43a05b440c782bf8d16f28bf6e41d726246ca74cae3670e6a1784ce81b982539`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/com.octbit.rutmath/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=13 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.qwde.ccm

* **Package / identity:** `com.qwde.ccm` · type: game · version: first
* **Source:** [https://gitlab.com/andsild/collective-club-maze](https://gitlab.com/andsild/collective-club-maze)
* **APK SHA256:** `dd57ead2dc7671e4a658864ba48003e5bd434d2719703ebdd870a8c0b5217edb`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/com.qwde.ccm/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=2 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

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

* **Package / identity:** `com.sanskritbasics.memory` · type: game · version: 3.4
* **Source:** [https://github.com/sanskritbscs/memory](https://github.com/sanskritbscs/memory)
* **APK SHA256:** `830798a6e70653d64fdf74a8f33beed448ffb2b22ca0736adf7cf6a07289e83c`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/com.sanskritbasics.memory/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=15 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.serwylo.retrowars

* **Package / identity:** `com.serwylo.retrowars` · type: game · version: 0.32.5
* **Source:** [https://github.com/retrowars/retrowars](https://github.com/retrowars/retrowars)
* **APK SHA256:** `8886269ac43e8f2f7f884fa1db8e2e7c1694db6cbc26311fe2323cef845eb3ec`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/com.serwylo.retrowars/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=7 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.sidhant.bubbleshooter

* **Package / identity:** `com.sidhant.bubbleshooter` · type: game · version: 1.0.1
* **Source:** [https://github.com/sidhant947/BubbleShooter](https://github.com/sidhant947/BubbleShooter)
* **APK SHA256:** `4f238534c4107070699ffc8c912ce54a0a6ba81aeb7a6666dad481746d468262`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none (rc=0) · issue: —
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** full app-specific behavior beyond click probe
* **Last success / first divergence:** 8/8 frames captured, click pass executed → none
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.sidhant.puzzle

* **Package / identity:** `com.sidhant.puzzle` · type: game · version: 2.0.3
* **Source:** [https://github.com/sidhant947/puzzle](https://github.com/sidhant947/puzzle)
* **APK SHA256:** `950bc52c96a4c042fcefb7e6c2aa9851221346dc22d500a642ec1d770a7b0888`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none (rc=0) · issue: —
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** full app-specific behavior beyond click probe
* **Last success / first divergence:** 8/8 frames captured, click pass executed → none
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### Queens

* **Package / identity:** `com.sidhant.queens` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran → near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (games__com.sidhant.queens_93__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

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

### com.willie.mancala

* **Package / identity:** `com.willie.mancala` · type: game · version: 1.2
* **Source:** [https://github.com/Willie169/mancala-android](https://github.com/Willie169/mancala-android)
* **APK SHA256:** `827e9850e1eaf784e4b4dd4a3df7f11dfb323c61ada944cde96395bca56b4b41`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/com.willie.mancala/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=15 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### Mines (premy)

* **Package / identity:** `cos.premy.mines` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `18faef7028457f4d123ac8d781f3ecdbf9e29b451468d5d6a348df28e8842aa7`
* **Sessions:** S83 · status: **VERIFIED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [cos.premy.mines.jpg](../docs/evidence/canonical/cos.premy.mines.jpg) · SHA256 `f73b3c57ca712dd2…`
* **Root cause:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** graphics completeness beyond L3
* **Notes:** S83 real-screenshot campaign evidence (games__cos.premy.mines_16__L2_GRAPHICALLY_INCOMPLETE.jpg)

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
* **Sessions:** S62+ · status: **VERIFIED** · rendering: L5 (L5)
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
* **Sessions:** S84 · status: **VERIFIED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=true · state_changed=false
* **Canonical screenshot:** [de.georgsieber.ballbreak.jpg](../docs/evidence/canonical/de.georgsieber.ballbreak.jpg) · SHA256 `b3c8930369dfe0b7…`
* **Root cause:** none (rc=0) · issue: —
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED
* **Remaining:** full app-specific behavior beyond click probe
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=2 state_changed=0. unique_colors=25 entropy=0.096 resources(dex/classes)=?

### Solitaire (tobiasbielefeld)

* **Package / identity:** `de.tobiasbielefeld.solitaire` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran → near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (games__de.tobiasbielefeld.solitaire_71__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

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
* **Root cause:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran → near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (games__eu.veldsoft.no.thanks_1__L1_NONBLANK.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

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
* **Root cause:** none (rc=0) · issue: —
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** full app-specific behavior beyond click probe
* **Last success / first divergence:** 8/8 frames captured, click pass executed → none
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=1 entropy=-0.0 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

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

### Dooz (tic-tac-toe)

* **Package / identity:** `io.github.yamin8000.dooz` · type: game · version: —
* **Source:** F-Droid io.github.yamin8000.dooz
* **APK SHA256:** `d81292cd346dcb23b04488bca400ca95af0f6eaa4aefefd31f847fe535cbdc17`
* **Sessions:** S66/S83 · status: **VERIFIED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [io.github.yamin8000.dooz.jpg](../docs/evidence/canonical/io.github.yamin8000.dooz.jpg) · SHA256 `cd1370525d4c2c4e…`
* **Root cause:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** graphics completeness beyond L3
* **Notes:** S83 real-screenshot campaign evidence (games__dooz__L2_GRAPHICALLY_INCOMPLETE.jpg)

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

### jwtc.android.chess

* **Package / identity:** `jwtc.android.chess` · type: game · version: 10.6.0
* **Source:** [https://github.com/jcarolus/android-chess](https://github.com/jcarolus/android-chess)
* **APK SHA256:** `3245b9ec35f6c1df771c418ac91ec792b5e056fb37e1d391e607b614f1a283b4`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/jwtc.android.chess/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=7 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### net.tigr.navyfleetbattle

* **Package / identity:** `net.tigr.navyfleetbattle` · type: game · version: 1.3.4
* **Source:** [https://github.com/tigrino/navy-fleet-battle](https://github.com/tigrino/navy-fleet-battle)
* **APK SHA256:** `a2eed1a574bc01ed2b8b004b22832d8baa5f936a154f68e0737dcef9c2fe7ca5`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none (rc=0) · issue: —
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** full app-specific behavior beyond click probe
* **Last success / first divergence:** 8/8 frames captured, click pass executed → none
* **Notes:** S84 NEW title. rc_obs=0 errors=3 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### OPMT (One More Time…)

* **Package / identity:** `one.scarecrow.games.OPMT` · type: game · version: —
* **Source:** [https://github.com/scarecrowgames/OneMoreTimePuzzleGame](https://github.com/scarecrowgames/OneMoreTimePuzzleGame)
* **APK SHA256:** `—`
* **Sessions:** S65/S74 · status: **PARTIAL** · rendering: L5 (L5)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** [one.scarecrow.games.OPMT.jpg](../docs/evidence/canonical/one.scarecrow.games.OPMT.jpg) · SHA256 `17aa411b313a5aa2…`
* **Root cause:** see session report (S62-S65 spotlight reports) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Last success / first divergence:** see S65/S74 report → see session report
* **Notes:** canonical harvested from docs/evidence/visual_forensics/s65_reval/opmt/game_partial_full.png

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

* **Package / identity:** `org.lufebe16.pysolfc` · type: game · version: 3.6.1
* **Source:** [https://github.com/shlomif/PySolFC](https://github.com/shlomif/PySolFC)
* **APK SHA256:** `abe8a22ddab2029fd78489527dc60f201bf9be37a27283e41619b4b40d6158e2`
* **Sessions:** S84 · status: **BLOCKED** · rendering: L-1 (NO-FRAME)
* **Execution evidence:** launched=false · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** engine boot → first uncaught in-flight exception (see run/s84/org.lufebe16.pysolfc/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=1 frames=0/8 click: probed=-1 state_changed=-1. unique_colors=None entropy=None resources(dex/classes)=?

### org.opensurge2d.surgeengine

* **Package / identity:** `org.opensurge2d.surgeengine` · type: game · version: 6.1.3.0-fdroid
* **Source:** [https://github.com/alemart/opensurge](https://github.com/alemart/opensurge)
* **APK SHA256:** `c1020c5a1e594b2189816ac39f657e827b9a4d22d199d72228ed7e276d70be77`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope). · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/org.opensurge2d.surgeengine/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=1 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### Battleship (SECUSO)

* **Package / identity:** `org.secuso.privacyfriendlybattleship` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran → near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (games__org.secuso.privacyfriendlybattleship_101__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

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

### ru.wohlsoft.thextech.fdroid

* **Package / identity:** `ru.wohlsoft.thextech.fdroid` · type: game · version: 1.3.7.3
* **Source:** [https://github.com/Wohlstand/TheXTech](https://github.com/Wohlstand/TheXTech)
* **APK SHA256:** `768aaa9ad0a08d8dc5640e70f298d688e593b9627b96e9f9cdbacdb487268edd`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=false · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. |  · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed → first uncaught in-flight exception (see run/s84/ru.wohlsoft.thextech.fdroid/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=0 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### Tarok

* **Package / identity:** `si.palcka.tarok` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran → near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (games__si.palcka.tarok_203__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### xyz.deepdaikon.quinb

* **Package / identity:** `xyz.deepdaikon.quinb` · type: game · version: 1.2.5
* **Source:** [https://gitlab.com/deepdaikon/Quinb/tree/HEAD](https://gitlab.com/deepdaikon/Quinb/tree/HEAD)
* **APK SHA256:** `bd720d019b85bac7aa08013bf2b50f331d76d736bfe681753a43c8215e002d69`
* **Sessions:** S84 · status: **OBSERVED** · rendering: L2 (GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=true · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** none (rc=0) · issue: —
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** full app-specific behavior beyond click probe
* **Last success / first divergence:** 8/8 frames captured, click pass executed → none
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

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

### NewsBlur

* **Package / identity:** `com.newsblur` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 HIGH · status: **OBSERVED** · rendering: L2 (L2_GRAPHICALLY_INCOMPLETE)
* **Execution evidence:** launched=true · rendered=false · interacted=false · state_changed=false
* **Canonical screenshot:** — (no visual — see divergence) · SHA256 `…`
* **Root cause:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep) · issue: [root-cause registry](../docs/evidence/ROOT_CAUSE_REGISTRY.md)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran → near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (high__com.newsblur_289__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

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

