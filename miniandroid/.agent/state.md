# EXP-088 Campaign State

**Last updated:** 2026-08-23T05:35:00Z
**HEAD:** a9434de

## Phase Status

| Phase | Status | Evidence |
|---|---|---|
| A1 (AXML inflation) | PROVEN | ViewShadow tree created from layout_cache.json |
| A2 (measure/layout) | PROVEN | MATCH_PARENT/WRAP_CONTENT, 20736 non-white pixels |
| A5 (text rendering) | PROVEN | BitmapFont glyphs, headingcalculator 5880 dark text pixels |
| A4 (drawables/images) | IN_PROGRESS | Layout cache now resolves drawable src paths; ImageButton tag mapping added; image_drawable_path captured in ViewShadow; renderer extracts PNG from APK. Full pixel decode still pending. |
| B (generic input/click) | IN_PROGRESS | dispatch_click wired after onCreate; full proof needs Calculator APK |
| B2 (event dedup) | NOT_STARTED | Needs B proof first |
| C (SQLite) | NOT_STARTED | Independent track |
| F (Handler/Looper) | NOT_STARTED | Infrastructure wired in EXP-086 |
| I (multi-DEX audit) | NOT_STARTED | |
| M (Telegram login) | LOCKED | Depends on B+B2 |

## Exact Next Action
1. Test simplestopwatch rendering with the fixed layout cache (3 ImageButtons with PNG paths)
2. If PNG decode works in renderer, mark A4 PROVEN
3. Move to Phase B (generic click dispatch proof with headingcalculator)
4. Then Phase C (SQLite micro test)

## Known Issues
- simplestopwatch takes >60s to execute (deep DEX execution)
- gmdice sometimes segfaults during rendering (intermittent)
- Telegram has no layout cache (uses obfuscated res/ paths)
