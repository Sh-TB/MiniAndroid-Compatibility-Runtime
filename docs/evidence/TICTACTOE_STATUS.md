# TICTACTOE_STATUS — §29 "must not be forgotten" record (revalidated)

Campaign: REUSE-FIRST FULL COMPATIBILITY + RESEARCH-TO-CODE
Revalidation date: 2026-09-05 · Local HEAD at revalidation: `9e7c0e9b`
(introduced at `de5f370e` "ONE COMPLETE APK — tictactoe_golden
end-to-end"; revalidated at every campaign HEAD since, including this one)

## Status: PASS — real interaction, real state machine, deterministic

This is NOT a first-frame-only claim. The validation drives NINE real
click events through the runtime's input dispatch into the real DEX
listeners and checks the semantic and pixel state after every frame.

## What the validator proves (this campaign's run)

`miniandroid/tests/fixtures/tictactoe_golden/validate_tictactoe_golden.sh`
— **ALL PASS (8 groups), zero skipped**:

1. **Load**: fixture APK built by the real toolchain (ECJ + D8), APK
   SHA256 `87b8a2558631e9f22bfc7fe0b795a653dd5562cff12658aa66084fcf94f46c58`.
2. **Board visible**: frames manifest produced; board surfaces rendered
   (buttons fill the frame).
3. **Input → state change (real DEX listeners)**: 9/9 clicks dispatched;
   10 frames recorded; frame0 status `'X to move'`; frame1 status
   `'O to move'` with exactly one X placed; frame7 status `'X WINS'`;
   final board 4 X + 3 O marks.
4. **Pixels follow state**: marks exactly in cells 2..8 (cells 0/1 empty),
   every mark region has real glyph ink (>100 px each).
5. **End-of-game freeze**: frames 8/9 byte-identical (no further state
   mutation after the win).
6. **Deterministic replay**: run B — all 10 frames byte-identical
   (manifest hash `0d339d847f91…` prefix, full value recorded in
   `docs/evidence/tictactoe_golden/frames_manifest.json`).

## §29 minimum goal vs achieved

| Required | Achieved |
|---|---|
| boot → board visible | YES (frame0, board surfaces rendered) |
| click a cell → board changes | YES (9 clicks, marks appear cell by cell) |
| second screenshot differs from first | YES (10 distinct frames, manifest diffs) |
| deterministic replay | YES (all frames byte-identical across runs) |
| win/draw path visible | YES ('X WINS' at frame7, frozen afterwards) |

## Evidence files

- `docs/evidence/tictactoe_golden/frames_manifest.json` — per-frame hashes
- `docs/evidence/tictactoe_golden/board_launch.png`, `board_x_wins.png`,
  `launch_vs_xwins.png` — runtime-produced frames
- `miniandroid/tests/fixtures/tictactoe_golden/validate_tictactoe_golden.sh`
  — the executable spec (zero-skip law)

## Regression state at this HEAD

- helloworld_golden 18/18 PASS; semantic battery 96/96; MUTF-8 battery
  7/7. No regression: frame hashes unchanged by this campaign's code
  changes (MUTF-8 primitive + switch/arg discriminators are additive).
