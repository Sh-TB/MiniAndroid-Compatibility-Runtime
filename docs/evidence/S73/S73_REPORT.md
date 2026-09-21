# S73 REPORT — GitHub Execution Tracking + Historical APK Evidence + Autonomous Snake Gameplay

Session: S73 · Date: 2026-09-21 · Base: S72-W4 HEAD `e25c0371` (pushed this session)
Constitution: CONSTITUTION_V2.md (binding). Binary: rebuilt from HEAD sources
(container reset had wiped `build/`; rebuild verified: dooz ×3 byte-identical
`0e334abe1b10b592`, snake W4 recipe re-verified byte-identical
`1a419545419deb3a` — the rebuild is faithful to the committed state).

## 1. GitHub tracking

* Issues found (pre-existing): 9 (#1–#8 closed Telegram experiment records,
  #9 MASTER-ROADMAP open).
* Issues reused: 0 (no [EXEC] issues existed; the Telegram experiment issues
  are referenced as history from #16 rather than duplicated).
* Issues created: **14 canonical [EXEC] issues** (#10–#23), exactly one per
  tracked application, each with the execution-ladder template.
* Duplicates avoided: inventory + title search performed before creation
  (PART J); zero duplicates created.
* Labels created: `execution, apk, runtime, rendering, input, state-change,
  screenshot, gameplay, autonomous-gameplay, differential, regression,
  blocked, p0, p1, p2` (15; existing conventions like `evidence` reused).
* Issue states: CLOSED (completed-state documented): #10 HelloWorld,
  #11 TicTacToe, #12 ConnectFour. OPEN (honest unfinished): #13 Snake
  (closing review at this commit), #14 Dooz (BLOCKED), #15 Unote,
  #16 Telegram, #17 GMDice, #18 MicroTimer, #19 FishRings, #20 TriPeaks
  (BLOCKED), #21 Bouncy, #22 Stopwatch (BLOCKED by design), #23 OPMT.
* Dated evidence comments posted on #13–#23 (PART A6/D).

## 2. Application matrix (S73 current-HEAD re-execution, canonical recipe
real-dalvik 9 frames @1500ms unless noted)

| Application | Package | Historical claim | Current status | Launch | UI | Render | Screenshot | Input | State change | 3-run | Issue | Blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HelloWorld | com.appliberated.helloworldselfaware | golden control target | DONE | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | #10 | — |
| TicTacToe | com.emmanuelmess.tictactoe | 9-click chain, win ×3 | DONE | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | #11 | — |
| ConnectFour | (golden fixture) | agent-playable 24-step | DONE | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | #12 | — |
| AndroidGameSnake | zhangman.github.snake | screenshot-proven (W4) | OBSERVED+autonomous | ✓ | ✓ | ✓ | ✓ | ✓ autonomous | ✓ | ✓ 3/3 | #13 | — (restart path open) |
| Dooz v23 | io.github.yamin8000.dooz | 23472 px + det ×3 | BLOCKED (+ metric reclassified) | ✓ | ✗ | engine-default only | ✗ | ✗ | ✗ | ✓ | #14 | F-146, F-147 (F-145 frontier) |
| Unote | app.varlorg.unote | themed UI recovered | PARTIAL | ✓ | ✓ | 231120 px | ✓ | unprobed | — | ✓ | #15 | ladder open |
| Telegram | org.telegram.messenger | checkpoint M (EXP-064..071) | PARTIAL (historical) | ✓ | ✓ login UI | ✓ | ✓ | ✓ | ✓ (page) | historical | #16 | init budget; not re-run at HEAD |
| GMDice | de.duenndns.gmdice | battery + tap goldens | PARTIAL | ✓ | ✓ | 182628 px | ✓ | historical | historical | ✓ | #17 | ladder open |
| MicroTimer | dubrowgn.microtimer | L7 keypad→display | PARTIAL | ✓ | ✓ | 1041437 px | ✓ | historical | historical | ✓ | #18 | ladder open |
| FishRings | eu.veldsoft.fish.rings | S10 + F-142 board | PARTIAL | ✓ | ✓ | 2073360 px board (frames 4–8) | ✓ | historical | historical | ✓ | #19 | ladder open |
| TriPeaks | eu.veldsoft.tri.peaks | S7 lobby; R-NEW-388 | BLOCKED (visual) | ✓ | lobby | 205638 px lobby | PARTIAL | historical | — | ✓ | #20 | R-NEW-388; OBJECT-IDENTITY |
| Bouncy | com.dozingcatsoftware.bouncy | L6 two-state clicks | PARTIAL | ✓ | ✓ | 2073600 px | ✓ | historical | historical | ✓ | #21 | L7 loop open |
| Stopwatch | com.github.muellerma.stopwatch | service-only manifest | BLOCKED (by design) | n/a | n/a | engine-default face | — | n/a | n/a | ✓ | #22 | no launchable Activity (F-143 family) |
| OPMT | one.scarecrow.games.OPMT | S6 chain | PARTIAL | ✓ | ✓ | 213286 px | ✓ | historical | historical | ✓ | #23 | app-own IOOBE (OBJECT-IDENTITY) |

Current-HEAD pixel evidence (final frame, canonical recipe): unote 231120
(sha 2928a026c4a88a14), bouncy 2073600 (108618ac7c58083b), gmdice 182628
(a011e9e9eee2cb42), microtimer 1041437 (e4869001e3638d69), fishrings board
2073360 (19af37b69965fc48; splash 0 px frames 0–3 then board frames 4–8),
opmt 213286 (60e5611daaf01e58), tripeaks 205638 (834928fd671a9560),
tictactoe 0 (blank-class face under launch-only recipe — consistent with
the S51-era L4 record; the golden validator proves the game separately),
dooz 23472 / stopwatch 23472 (both = engine-default black region, sha
0e334abe1b10b592 — see §5), snake launch 116230 (407020eadd2aa4cd).

## 3. Snake — autonomous gameplay (PART C)

* Launch: real APK `snake_v1.0_vc1.apk` (sha256 54cf48a9…), real Activity,
  real ConstraintLayout UI (F-148 geometry), real SnakePanelView.
* START: real tap (98,839)@frame1 → CLICK → reStartGame → Thread self-run
  (F-150 laws) → observed movement law: 1 cell/frame, tap@k effective at
  frame k+1, head = grown cell, reverse turns rejected by the APP.
* Autonomous controller: iterative closed-loop driver
  (scripts/s73_snake_controller.py). Vision = rendered-frame pixels ONLY;
  actuator = scheduled taps through the canonical TouchDispatcher DOWN/UP
  pipeline (F-117 scheduled-input extension `--tap x,y@frame`; legacy form
  bit-identical — verified against stored W4 evidence). 4 decision
  iterations → GOALS_MET.
* Moves: 88 head-advance frames; 22 accepted direction turns (≥20 goal);
  game-over: none during the session.
* Food capture: frame 34 — snake grew 3→4 (snake-cell pixels 3042→6084),
  food respawned (0,0)→(9,0) in the same render (growth-based capture
  detection; the food teleports in the capture render).
* Engineered probes (C4, real taps): reverse-rejection OBSERVED (LEFT tap
  while moving RIGHT rejected; heads continued (15,10)→(18,10)); wall/wrap
  law discovered: head (19,10)→(0,10) WRAPS (no wall death); self-collision
  game-over OBSERVED (head re-entry into occupied (5,10), panel switches to
  game-over surface 1,868,783 px); restart via START after game-over NOT
  OBSERVED (honest open; possibly Dialog-based restart path — not exercised).
* Frames: run_01 keeps all 90 PNGs; runs 02/03 keep key frames + full
  per-frame SHA records (determinism_proof.json).
* GIF: snake_autoplay.gif (39,073 bytes, sha in screenshot_metrics.json) —
  composed ONLY from real run_01 output frames (50% NEAREST scale,
  64-color quantize, 250 ms/frame — documented transform).
* Trace: gameplay_trace.json per run (C5 schema: run_id, frame, file,
  input, observed_snake, observed_food, head, direction, state_hash,
  screenshot_sha256, event).
* 3-run reproducibility: **3/3 IDENTICAL** — three independent full runs of
  the identical 23-tap schedule; per-frame PNG sha equality across all 90
  frames (determinism_proof.json).
* SHA256: per-frame in gameplay_trace.json + SHA256SUMS per run; key-frame
  metrics in screenshot_metrics.json (B3 gate: resolution 1080×1920,
  non-background, entropy, luminance, dominant colors, content bounds).
* No game-state injection, no fake screenshot, no renderer bypass: the
  controller's only actuator is taps; all state knowledge is pixel-extracted.

## 4. Generic laws discovered

No NEW F-numbers this session. Two honest runtime deltas, both documented:

1. **F-117 EXTENSION (runtime input capability, not a new law)** —
   `--tap x,y@frame` (scheduled-input cadence: a tap fires after frame `k`
   renders; real users tap BETWEEN frames). Legacy form (no `@`) keeps the
   exact old law (tap k at frame k) — verified byte-identical against
   stored W4 evidence. Implementation: execution_engine.h/cpp + main.cpp;
   all-or-none validation; regression-clean (fixtures 25/25, corpus re-run).
2. **Engine-default black surface FINDING (open lead, no law claimed)** —
   dooz AND Stopwatch (no launchable Activity) render byte-identical
   frames: 23,472 pure-black pixels in a (0,0)–(489,47) rectangle. The
   painter is not yet root-caused (canvas-shadow default-paint context is
   a candidate; upstream evidence pending). Recorded in #14/#22; queued.

Registry: unchanged at 396 roots (F-146/F-147/F-145 statuses unchanged;
the wrap/game-over/restart observations are APP-specific laws of the snake
game, recorded in its issue, not generic registry entries).

## 5. Dooz (PART E)

* F-146 (`g8.a@569 → ur.e(J)` null receiver): **UNCHANGED / OPEN**.
* F-147 (`onCreate@228 → ViewGroup.getChildAt` on null): **UNCHANGED / OPEN**.
* F-145 (screenshot/UI surface): **UNCHANGED / OPEN** — and sharpened by the
  reclassification below.
* F-141: remains CLOSED (not reopened).
* **Reclassification (B4 audit, dated in #14):** the "23472 px real content"
  metric from S72-W3/W4 is 23,472 pure-black pixels forming a (0,0)–(489,47)
  rectangle — byte-identical to the frame rendered for Stopwatch, an app
  with NO launchable Activity. The surface is therefore an ENGINE-DEFAULT
  black region, not dooz content. dooz's own UI surface remains unrendered;
  its visual status reverts to engine-default-only. Determinism facts
  (×3 byte-identical) stand; the INTERPRETATION is corrected. No old file
  rewritten — the correction lives in the issue comment + this report.

## 6. Regression

* Fixtures (25 pinned foundation APKs, current binary): **25/25 rc=0,
  f141-throws = 0 across the board** (run/s73_fixtures/).
* Corpus (10 canonical APKs + snake, current binary, canonical recipe):
  completed; per-app pixel faces recorded in §2 (all match stored records
  where stored records exist; tictactoe blank-class face consistent with
  its S51-era record; dooz/stopwatch faces reclassified per §5).
* Determinism: dooz ×3 byte-identical (0e334abe1b10b592); snake autonomous
  session 3/3 IDENTICAL (90/90 frames each); snake W4 legacy recipe
  re-verified byte-identical (1a419545419deb3a).
* Zero regressions observed. Exact numbers above; no bare "PASS".

## 7. Git state

* HEAD: e25c0371 at session start (== origin/main after the S73 pre-push).
* Branch: main.
* Working tree: dirty → cleaned by the S73 commits (see below).
* Commits created: 1 (S73 campaign commit; SHA recorded in the closing
  comment of #13).
* Commits pending push: 0 after this session's push (18 pre-existing
  pending commits + the S73 commit pushed and remote-verified).
* Remote HEAD: verified equal to local HEAD after push (ls-remote check).
* Push result: **PUSHED AND VERIFIED** (credentials were provided this
  session via env var only; token never written to any tracked file;
  secret-guard PASS at push time).
* Secret scan: secret guard PASS (no credential-shaped strings in the
  working tree at push time); the PAT was used from an ephemeral
  environment variable only.
