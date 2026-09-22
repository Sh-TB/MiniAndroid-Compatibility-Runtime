# S82 Root-Cause Fanout Graph (§41)

One fix -> exactly which titles must regression (§19/§34).

## F-NEW-156 — onCreate APP-BOUNDARY-UNWIND family
- status: OBSERVED-FAIL family (S81)
- fanout (35 titles): GAME-001, GAME-002, GAME-003, GAME-005, GAME-006, GAME-007, GAME-009, GAME-012, GAME-014, GAME-017, GAME-019, GAME-020, GAME-023, GAME-025, GAME-034, GAME-046, GAME-047, GAME-048, GAME-050, GAME-052, APP-001, APP-002, APP-003, APP-004, APP-005, APP-006, APP-008, APP-013, APP-014, APP-029, APP-046, APP-079, APP-089, MAND-001, MAND-002

## F-NEW-157 — libGDX AndroidGraphics.createGLSurfaceView NPE (EGL/GLSurfaceView frontier)
- status: OBSERVED-FAIL (P0)
- fanout (1 titles): MAND-001

## VF-NEW-001 — VF-DIALOG-ITEMS (fixed S81; dialog path gated upstream)
- status: FIXED (S81) — title-level retests recorded
- fanout (2 titles): GAME-014, GAME-021

## VF-NEW-002 — VF-PLACEHOLDER-GARBLE (fixed S81; AFTER-state holds on real titles)
- status: FIXED (S81) — title-level retests recorded
- fanout (2 titles): GAME-014 (unote/unote ladder), APP (muellerma stopwatch — service family face)

## VF-NEW-003 — IMAGE_DECODED_VS_RENDERED_GAP chain
- status: FIXED (S81) — title-level retests recorded
- fanout (40 titles): GAME-001, GAME-002, GAME-003, GAME-004, GAME-005, GAME-006, GAME-007, GAME-008, GAME-009, GAME-012, GAME-014, GAME-015, GAME-016, GAME-017, GAME-018, GAME-020, GAME-023, GAME-025, GAME-034, GAME-046, GAME-047, GAME-048, GAME-050, GAME-052, APP-001, APP-002, APP-003, APP-004, APP-005, APP-006, APP-007, APP-008, APP-013, APP-014, APP-029, APP-046, APP-079, APP-089, MAND-001, MAND-002
