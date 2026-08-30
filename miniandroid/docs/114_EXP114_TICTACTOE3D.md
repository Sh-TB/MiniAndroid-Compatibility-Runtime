# DOC 114 — EXP-114: Tic-Tac-Toe with REAL 3D Software Rendering

Campaign: UNIFIED_005 · Date: 2026-08-28 · Commit: d6b4020
Owner priority: «یدونه بازی که حداقل 3D کمی داشته باشه لود کنی»

## 1. Claim (evidence-grade)

PROVEN (16/16 checks PASS, exit 0): the runtime renders a playable tic-tac-toe
board with REAL 3D graphics — full pinhole-perspective projection, per-box
painter depth sorting, per-face backface culling in view space, Lambert shading
from transformed normals, and depth fog. The 3D claim is machine-verified: six
frames at yaw 0..300 degrees have six DISTINCT pixel hashes (a fake "3D" sprite
would be rotation-invariant); the AI game reaches a terminal state with a
detected winning triple, and the win cells are rendered RAISED and brighter.

## 2. Why this is REAL 3D (and machine-proven so)

1. Geometry: every visual element is a solid in model space — platform tiles,
   9 cell slabs, X pieces = two crossed extruded bars (10 faces each),
   O pieces = 14-segment extruded ring (70 faces).
2. Transform chain: model → rotate_y(yaw) → rotate_x(pitch) → translate(z+dist)
   → perspective divide (focal 1050) → 1080x1920 framebuffer.
3. Occlusion: per-box centroid depth sort (far→near) + backface culling
   (view-space normal z >= 0 → culled). 1680 faces / 6.79M pixels filled.
4. Verification: rotation strip exp114_rot_000..300.png — 6 distinct FNV pixel
   hashes; board pixel-hash changes after every AI move (9/9 distinct states).

## 3. The game (real logic, not a canned replay)

- Perfect minimax for X. O plays perfect minimax EXCEPT a seeded-random first
  reply (mt19937(114)) — perfect-vs-perfect always draws; the seeded
  imperfection makes a decisive result reproducible so the win-state graphics
  are exercised. This is recorded openly in the JSON report (ai_policy).
- Result this seed: X wins on column 1 (cells 1-4-7) in 7 moves; every move
  recorded in tictactoe3d_report.json with per-move screenshots.

## 4. Bugs found & fixed during the task (buffer rule)

1. rotate_x sign inverted → first render looked at the board from BELOW.
2. Painter's big-face failure: one huge platform top face occluded far cells
   (dark rectangle over the top row) → platform re-tiled 6x6; per-box sort
   then correct (tiled sub-slabs sort farther than cells above them).
3. X-bar and O-ring face winding inverted → culling hid the visible sides;
   rewound all quads counter-clockwise-from-outside (quad_face derives normals
   from winding: cross(b-a, d-a)).
4. Letter-spacing: 8x16 glyph advance mushed adjacent glyphs → +scale px gap.

## 5. Source & artifacts

- src/games/tictactoe3d.h (header-only: game + 3D renderer)
- tools/exp114_tictactoe3d_demo.cpp (harness)
- run_exp005/ttt3d/: exp114_intro.png, exp114_move_01..07.png, exp114_final.png,
  exp114_rot_000..300.png (6), tictactoe3d_report.json (16 checks PASS)

## 6. Honesty boundaries

- 3x3 board, no textures, no GPU — software rasterizer only (that is the point:
  the runtime's own renderer does the 3D).
- "3D کمی" satisfied by true perspective geometry, NOT by skew/scale tricks.
- The O imperfection is a deliberate, disclosed seed choice for decisive
  graphics; the minimax itself is standard and X's play is perfect.
