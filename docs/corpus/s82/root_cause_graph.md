# S82 Root-Cause Fanout Graph

## F-NEW-156 — onCreate APP-BOUNDARY-UNWIND family

- status: registered
- fanout (35): GAME-001, GAME-002, GAME-003, GAME-005, GAME-006, GAME-007, GAME-009, GAME-012, GAME-014, GAME-017, GAME-019, GAME-020, GAME-023, GAME-025, GAME-034, GAME-046, GAME-047, GAME-048, GAME-050, GAME-052, APP-001, APP-002, APP-003, APP-004, APP-005, APP-006, APP-008, APP-013, APP-014, APP-029, APP-046, APP-079, APP-089, MAND-001, MAND-002

## F-NEW-157 — libGDX AndroidGraphics.createGLSurfaceView NPE (EGL/GLSurfaceView frontier)

- status: registered
- fanout (1): MAND-001

## VF-NEW-001 — VF-DIALOG-ITEMS (fixed S81; dialog path gated upstream)

- status: registered
- fanout (2): GAME-014, GAME-021

## VF-NEW-002 — VF-PLACEHOLDER-GARBLE (fixed S81; AFTER-state holds on real titles)

- status: registered
- fanout (2): GAME-014 (unote/unote ladder), APP (muellerma stopwatch — service family face)

## VF-NEW-003 — IMAGE_DECODED_VS_RENDERED_GAP chain

- status: registered
- fanout (40): GAME-001, GAME-002, GAME-003, GAME-004, GAME-005, GAME-006, GAME-007, GAME-008, GAME-009, GAME-012, GAME-014, GAME-015, GAME-016, GAME-017, GAME-018, GAME-020, GAME-023, GAME-025, GAME-034, GAME-046, GAME-047, GAME-048, GAME-050, GAME-052, APP-001, APP-002, APP-003, APP-004, APP-005, APP-006, APP-007, APP-008, APP-013, APP-014, APP-029, APP-046, APP-079, APP-089, MAND-001, MAND-002

## F-NEW-158 — PROGRAMMATIC-BACKGROUND-DROP (setBackground(Drawable)/setBackgroundResource(resid) silently ignored; image_resource_id clobber)

- status: ROOT_CAUSED_FIXED (S82-GFX; fixture ladder L0/L4 evidence + regression 26/26 + pixel goldens 24/24)
- fanout (4): l0_solid fixture, l4_xmldrawables fixture, GAME-004, PROGRAMMATIC-UI titles across corpus (static families B/C/D/E — see graphics_families.json)

## F-NEW-159 — NULL-FRAMEWORK-RECEIVER NPE family (LocaleList.toLanguageTags / WindowInsetsController.setSystemBarsAppearance on null refs → onCreate APP BOUNDARY unwind; F-NEW-156 sub-cluster)

- status: OPEN (S82-GFX fanout probe ×2 titles re-traced: MAND-002, APP-001 family; exact traces in run/s82gfx/fanout/*.log)
- fanout (3): MAND-002, APP-001, subset of F-NEW-156's 35

