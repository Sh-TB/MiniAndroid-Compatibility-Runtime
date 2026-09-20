# S72 WAVE 4 — NEW REAL GAME (AndroidGameSnake) → MEANINGFUL SCREENSHOT

Session: S72-W4 · Binary base: build/miniandroid @ W3 (a3f09ef2) + F-148/F-149/F-150
Constitution: CONSTITUTION_V2.md (binding; §-references below)

## 0. Constitution-impact re-test (user directive: measure the 185 rules' effect)

Fresh evidence on the UNCHANGED W3 binary (10 canonical APKs, canonical recipe,
`scripts/s72_w4_corpus.sh`): **10/10 pixel-identical to W3, dooz det ×3
BYTE-IDENTICAL** — the W3 state reproduces exactly (§18/§20: fresh runs confirm
stored baselines; nothing rotted). Constitution-era improvement vs the W1
pre-constitution dashboard (real, re-measured in S72-W1→W3):

| App | W1 (pre-constitution) | W4 (post F-141..F-147) | Δ |
|-----|----------------------|------------------------|---|
| dooz | 197 px (blank) | 23472 px + det ×3 | +118x (F-141 family) |
| unote | 11.4% garbage-backed | 231120 px real theme | recovered honestly (F-141f) |
| fishrings | 0 px board | 2073360 px real board | +real UI (F-142) |
| gmdice / microtimer / tripeaks / opmt | 8.8–50.2% | stable pixel-SAME | stable |

Old-app deltas the new laws caused in W4: **zero unexplained** (see §4).

## 1. Target game (evidence-based selection, §RULE brief #1)

```text
TARGET_GAME      AndroidGameSnake (贪吃蛇 grid snake)
SOURCE           github.com/zhangman523/AndroidGameSnake @ b4968c39
LICENSE          Apache-2.0
BUILD_METHOD     aapt2 8.13.2 / ECJ 3.33.0 / D8 (r8 8.13.23) — canonical recipe;
                 compile-stubs: android.support.v7.app.AppCompatActivity (=
                 Activity semantics, OPMT S65 law) + android.support.annotation.Nullable;
                 staged res (siggen law): AppTheme parent → platform Material.Light +
                 app-local color attrs + 30 ConstraintLayout attr ids
APK_PATH         upload/s72_w4_apks/snake_v1.0_vc1.apk (sha256 54cf48a9…, 22 entries)
PACKAGE          zhangman.github.snake
MAIN_ACTIVITY    zhangman.github.snake.MainActivity (extends AppCompatActivity)
INPUT_MODEL      5 Buttons (left/right/top/bottom/start) → View.OnClickListener →
                 SnakePanelView.setSnakeDirection / reStartGame
STATE_MODEL      20×20 grid; List<GridPosition> snake + header + length + direction +
                 isEndGame; GameMainThread (Thread subclass) loop: move → collision →
                 refresh → tail → postInvalidate → sleep(1000/8)
RENDER_MODEL     SnakePanelView.onDraw: drawColor(WHITE) + 400 stroke rects + 400
                 fill rects (GRID white / FOOD blue / SNAKE #FF4081)
KNOWN_DEPS       com.android.support appcompat-v7 (compile-stub), constraint-layout
                 (staged attrs + F-148 engine law), AlertDialog family (supported)
EXPECTED_BLOCKERS→ FOUND: ConstraintLayout gap (F-148), DisplayMetrics/applyDimension
                 gap (F-149), Thread game-loop family dead (F-150)
```

Selection rationale: NOT a duplicate architecture — TicTacToe/ConnectFour are
static grid+click; this is the **real-time game-loop family** (app-own Thread +
sleep + postInvalidate + collision state machine), highest knowledge value per
the survey (S63/S64/S65 deferred-by-facts reused; snake candidates with libGDX/
Kotlin/Flutter excluded by build-signature probes: super-snake=libGDX,
MangoSnake=Kotlin, sidhant947=Flutter).

## 2. The three laws closed (SOURCE → UPSTREAM → LAW → FIX → TEST)

### F-148 (P0) — ConstraintLayout anchor family
- First divergence: every child measured 0-wide, stacked at x=0 (view_tree.json).
- Fix: layout_inflater.cpp — parse 12 anchor attrs + 2 bias attrs; per-axis
  topological CL measure branch (MATCH_CONSTRAINT spread, bias 0.5, margins on
  the anchored side, parent-padding-box anchors, AOSP (0,0) fallback); layout
  phase replays cached edges (RL replay contract).
- Real-APK proof: snake_view EXACTLY(1080)×780; TOP (441,801) centered; LEFT
  (122,940)/RIGHT (760,940); BOTTOM (441,1398) = span 799 × bias 0.5 EXACT.

### F-149 (P0) — Resources.getDisplayMetrics + TypedValue.applyDimension + device-density unity
- First divergence: `[DEX-MEASURE] SnakePanelView.onMeasure -> 0x0` (dp2px = 0).
- Three stacked silent gaps (§038): getDisplayMetrics unimplemented (silent
  null); DisplayMetrics singleton pre-populated density=1.0 CONTRADICTING the
  inflater's 2.625 authority (silent cross-component divergence); no
  applyDimension DEX bridge.
- Fix: dalvik_engine.cpp — getDisplayMetrics answers the singleton with the
  device law (density 2.625/DENSITY_420, scaledDensity 2.625, 1080×1920,
  xdpi/ydpi 420); applyDimension exact AOSP switch over the metrics heap
  fields; singleton population aligned.
- Proof: SnakePanelView measures **1080×780 = 20 × 15dp × 2.625 EXACTLY**
  (the AOSP first-measure value); buttons 197×118 = 75×45dp EXACTLY.

### F-150 (P0) — Thread game-loop family
- First divergence: `[F084-HALT] GameMainThread.run visited 50001×, op 0x71
  (invoke-static)` — the loop never slept → VirtualMachineError poisoned
  onCreate (APP BOUNDARY unwind).
- Four stacked gaps (each root-caused separately, §041 multi-root):
  1. ThreadShadow no-op family answered `sleep` handled_void, SHADOWING the
     real sleep law (removed; the real law advances/registers).
  2. javac compiles unqualified `sleep`/`start` against the SUBCLASS
     descriptor (`invoke-static GameMainThread;->sleep(J)V` — DEX method_ids
     ground truth) → literal `class_name == Thread` guards never matched →
     `is_thread_receiver()` walks the DEX superclass chain (3 sites).
  3. pending_starts_ drained only inside park drains → never at frames.
  4. a body that yielded at sleep had NO resume point (died after slice 1).
- Fix: stage_frame_sequence drains pending starts + due yielded bodies at
  every frame boundary (bounded 4/8); ThreadShadow yielded-registry
  (thread → {target, wake_at}); sleep inside drained bodies records
  wake = now + ms and yields WITHOUT advancing the shared clock (the frame
  boundary owns the clock); main-thread quiescence keeps the M3 advance law.
- Proof: 2 ticks/frame EXACT (125ms sleep @ 250ms frame-delay); direction taps
  steer the snake cell-by-cell; the app's own reverse-guard (illegal turn
  ignored) observed live; game state per frame = snake cells + food cell.

## 3. Real-app proof chain (§165/§169) — INPUT → STATE → RENDER → SCREENSHOT

```text
launch → frame_000 (buttons + panel, 116230 px)
tap START (98,839) @frame1 → CLICK → reStartGame → Thread.start (self-run law)
        → tick: snake [(10,10),(11,10)], food (0,0) blue
taps BOTTOM×2, RIGHT, TOP×2, LEFT @frames 2-7 → setSnakeDirection state chain
        → snake turns/moves 2 cells/frame (sleep law EXACT), reverse-guards hold
frame_013 final: snake [(7,10),(8,10),(9,10)] + food (0,0), 122314 px
```
Screenshot metrics (final frame, each of 3 runs): resolution 1080×1920;
non-white 122314; luminance 248.87; entropy 0.3679 bits; dominant colors
#ffffff 1951286 / #6fa8dc (buttons) 110282 / **#ff4081 (snake) 4563** /
#212121 (text) 3682 / **#0000ff (food) 1521**; content bounds [0,0,956,1512];
PNG sha256 958031dc…; pixel sha **1a419545419deb3a** ×3.
Evidence: docs/evidence/s72_w4_snake/ (4 annotated frames + APK + SHA256SUMS).

The screenshot is app-provenance (§14): every pixel comes from the APK's own
DEX onDraw (801 canvas ops replayed per frame — C013-ONDRAW) + inflater
rendering of the app's own layout; no image injection, no hardcoded frame.

## 4. Regression (§117-123)

- Corpus (10 canonical APKs, post-F148/149/150 binary): **10/10 pixel-SAME**
  vs W3; dooz det ×3 BYTE-IDENTICAL (23472 px — F-146/F-147 unchanged).
- Fixtures (25 pinned APKs): **25/25 rc=0, pixel-SAME vs W3**; zero
  f141-throws; EXT-01/02 environmental unchanged.
- Honest delta record: the F-150 sleep de-noop changes NO corpus pixel
  (verified 10/10) — the only sleep-loop app in the corpus is the new target.

## 5. Status vocabulary (§RULE brief #10-11)

- TARGET GAME chain: LAUNCHED / INPUT TESTED / STATE OBSERVED / RENDERED /
  **SCREENSHOT-PROVEN** (×3 byte-identical, metrics + SHAs above).
- F-148/F-149/F-150: ROOT-CAUSED-FIXED (P0 ×3, each with real-APK proof).
- F-146/F-147 (dooz, P1): re-probed on the current binary — **unchanged**
  (same first divergences g8.a pc=569 / onCreate pc=228; 23472 px). OPEN,
  next-wave queue. NOT folded into this wave's success (§RULE brief #7).
- F-145 (screenshot surface, P1): still OPEN (dooz/stopwatch splash capture).
- F-143/F-144: unchanged.

## 6. FOUNDATION STATUS (§32)

**NOT COMPLETE** — frontier moved materially: the modern-layout family
(ConstraintLayout subset) + device-density unity + the Thread game-loop family
are now law-backed with real-APK proofs and zero regressions. Remaining known
open roots: F-145/F-146/F-147 (P1) + the documented F-148 subset boundaries
(chains/Guideline/RATIO/RTL) + F-150 deviation notes.

## 7. Registry delta

393 → **396** (F-148, F-149, F-150 ROOT-CAUSED-FIXED). Tooling added:
scripts/s72_w4_{build_snake.sh,corpus.sh,fixtures.sh,measure.py,snake_proof.py,
disasm2.py,registry.py}; tools/exp042_disasm.py method-table corruption fixed
(`methods[method_idx]` line) + APK-arg support.
