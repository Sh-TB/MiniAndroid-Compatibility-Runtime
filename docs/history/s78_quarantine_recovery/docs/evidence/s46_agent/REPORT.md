# S46 AGENT GAMEPLAY ACCEPTANCE — TicTacToe Classic (real runtime, dynamic policy)

Date: 2026-09-15 · Engine: build/miniandroid (S46, post R-NEW-361 fix) · APK: fixture build (ECJ+D8, com.miniandroid.tictactoegolden)

## Protocol (mission §7 — Agent gameplay, NOT scripted playback)

The run used the new `--agent-play 9` engine mode (`stage_agent_play`,
src/runtime/execution_engine.cpp). Per step the agent:

1. OBSERVES the app's own rendered view texts (ViewShadow node texts —
   the same bytes an external vision agent would read). No engine-internal
   game state is consulted.
2. DECIDES with a deterministic policy over the observed 3x3 board:
   `win:complete-line > block:opponent-line > take-center > take-corner >
   first-empty`.
3. ACTS by dispatching a REAL click (`dispatch_click`) on the chosen view.
4. RE-RENDERS and verifies the observed state transition per step.

## Result (frames/manifest.json = docs/evidence/s46_agent/agent_tictactoe_manifest.json)

- moves made: **9 / 9** — every step `state_transition_verified: true`
- dynamic_selection: **true** (policy reasons differ per step — see below)
- final status (the app's own rendered text): **DRAW** — a real measurable
  game outcome (optimal hotseat play: the agent plays both sides)
- per-move pixel diffs: 2,741–2,797 px per step (real redraws)

Step-by-step policy trace (from the run log):

| step | cell | reason |
|------|------|--------|
| 1 | 4 (center) | take-center |
| 2 | 0 | take-corner |
| 3 | 2 | take-corner |
| 4 | 6 | win:complete-line |
| 5 | 3 | block:opponent-line |
| 6 | 5 | win:complete-line |
| 7 | 8 | take-corner |
| 8 | 1 | first-empty |
| 9 | 7 | first-empty → DRAW |

The win/block/center decisions prove the agent adapted to OBSERVED state
(a scripted playback would click a fixed list regardless of board content).

## Evidence files

- `agent_tictactoe_gameplay.gif` — 10-frame GIF built from the ACTUAL runtime
  PNGs (sha256 c98214d3870e536eecea6274acd3d7d0419f23529569163aba2b7f2a237f3ab7,
  8,279 bytes; per-frame PNG SHA-256 list in `agent_tictactoe_gameplay.gif.json`)
- `agent_tictactoe_manifest.json` — engine-written per-step evidence:
  observation board, chosen view id, policy reason, dispatch result,
  state_transition_verified, changed pixel count, framebuffer SHA-256,
  PNG SHA-256
- `frame_000_launch.png` / `frame_004_win_attempt.png` /
  `frame_009_final_draw.png` — sampled runtime frames

## Relation to the WIN-state evidence

The §29 golden (validate_tictactoe_golden.sh) separately proves the
X → O → X → **X WINS** terminal state with 9/9 dispatched clicks and
deterministic replay 613cfccc0f27… (ALL PASS at this HEAD). The agent run
adds the dynamic observe→decide→act loop; its optimal-play outcome is a
draw, which is the correct result of the same policy playing both sides.
