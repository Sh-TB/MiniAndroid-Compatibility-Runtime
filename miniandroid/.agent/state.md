# EXP-088 Campaign State

**Last updated:** 2026-08-23T05:45:00Z
**HEAD:** 6f5e786

## Phase Status

| Phase | Status | Evidence |
|---|---|---|
| A1 (AXML inflation) | PROVEN | ViewShadow tree created from layout_cache.json |
| A2 (measure/layout) | PROVEN | MATCH_PARENT/WRAP_CONTENT, 20736 non-white pixels |
| A5 (text rendering) | PROVEN | BitmapFont glyphs, headingcalculator 5880 dark text pixels |
| B1 (PNG output) | PROVEN | PIL-decodable PNG with valid CRCs |
| B5 (entry-point resolution) | PROVEN | 7/7 APKs enter onCreate |
| A4 (drawables/images) | IN_PROGRESS | Layout cache resolves drawable src paths (lock.png, settings.png, menu.png). ImageButton tag mapping added. image_drawable_path captured in ViewShadow. Renderer extracts PNG from APK. Full pixel decode NOT yet verified due to intermittent segfault in rendering. |
| B (generic input/click) | IN_PROGRESS | dispatch_click wired after onCreate |
| B2 (event dedup) | NOT_STARTED | |
| C (SQLite) | NOT_STARTED | |
| F (Handler/Looper) | NOT_STARTED | |
| I (multi-DEX audit) | NOT_STARTED | |
| M (Telegram login) | LOCKED | |

## Exact Next Action
1. Fix intermittent segfault in rendering lambda (likely stack depth or dangling reference)
2. Verify simplestopwatch renders with ImageButton placeholders
3. Move to Phase B (generic click dispatch proof)
4. Then Phase C (SQLite micro test)

## Key Fixes This Turn
- Fixed Path scope bug in layout_cache_generator.py (local `from pathlib import Path` shadowed module import)
- Added ImageButton/TableLayout/TableRow tag mapping
- Added `src` attribute capture in inflate_view_tree for drawable path resolution
- Added isinstance() checks in resolve_resource_ref for ARSC boolean returns
- Added try/except in resolve_tree_attrs to prevent silent crashes
- Fixed resource ID matching to use filename stem (not exact path) for config-specific layouts

## Known Issues
- gmdice and simplestopwatch runs sometimes segfault during rendering
- The segfault is intermittent — sometimes produces valid PNG, sometimes crashes
- Root cause likely: recursive std::function lambda in stage_render_frame accessing freed ViewShadow nodes
- simplestopwatch execution takes >60s due to deep DEX class loading
