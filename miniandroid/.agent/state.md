# EXP-088 Campaign State

**Last updated:** 2026-08-23T06:20:00Z
**HEAD:** b5cd611

## Phase Status

| Phase | Status | Evidence |
|---|---|---|
| A1 (AXML inflation) | PROVEN | ViewShadow tree created from layout_cache.json |
| A2 (measure/layout) | PROVEN | MATCH_PARENT/WRAP_CONTENT, 20736 non-white pixels |
| A5 (text rendering) | PROVEN | BitmapFont glyphs, headingcalculator 5880 dark text pixels |
| B1 (PNG output) | PROVEN | PIL-decodable PNG with valid CRCs |
| B5 (entry-point resolution) | PROVEN | 7/7 APKs enter onCreate |
| A4 (drawables/images) | IN_PROGRESS | Iterative BFS renderer fixes segfault. Drawable src paths captured (lock.png, settings.png, menu.png). headingcalculator 5/5 SUCCESS. gmdice 1/5 SUCCESS (DEX crash after setListAdapter). Full pixel decode still pending. |
| B (generic input/click) | PROVEN | findViewById returns correct views (view_id=13, view_id=7). setOnClickListener registers listeners (listener_id=3). Click dispatch fires after onCreate ([UI-EVENT] event=CLICK result=DISPATCHED). |
| B2 (event dedup) | NOT_STARTED | |
| C (SQLite) | NOT_STARTED | |
| F (Handler/Looper) | NOT_STARTED | |
| I (multi-DEX audit) | NOT_STARTED | |
| M (Telegram login) | LOCKED | |

## Exact Next Action
1. Remove debug prints from ActivityShadow and dalvik_engine
2. Move to Phase B2 (event deduplication) — verify one click = one callback
3. Then Phase C (SQLite micro test)
4. Then Phase F (Handler/Looper)
5. Then Phase I (multi-DEX audit)
6. Then Phase M (Telegram login)

## Key Fixes This Turn
- Fixed iterative BFS renderer (replaced recursive std::function lambda)
- Fixed layout cache generator: skip 'id' attribute resolution
- Fixed ActivityShadow::findViewById: search from content_view_id
- Fixed ViewShadow::findViewById: search from content_view_id via registry
- Fixed bridge_to_api: added shadow registry fallback for unhandled methods
- Fixed DalvikType enum values in shadow dispatch code

## Known Issues
- gmdice DEX execution crashes intermittently after setListAdapter (4/5 runs)
- headingcalculator works reliably (5/5) but has no clickable buttons in layout
- simplestopwatch works with 120s timeout (3 ImageButtons with resolved src paths)
- Telegram has no layout cache (uses obfuscated res/ paths)
