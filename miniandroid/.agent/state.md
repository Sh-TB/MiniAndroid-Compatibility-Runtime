# EXP-088 Campaign State

**Last updated:** 2026-08-23T05:15:00Z
**HEAD:** 2fe0b06

## Phase Status

| Phase | Status | Evidence |
|---|---|---|
| A1 (AXML inflation) | PROVEN | ViewShadow tree created from layout_cache.json, root_id=4 |
| A2 (measure/layout) | PROVEN | MATCH_PARENT/WRAP_CONTENT/exact px, 20736 non-white pixels |
| A5 (text rendering) | PROVEN | BitmapFont glyphs, headingcalculator 5880 dark text pixels |
| A4 (drawables/images) | IN_PROGRESS | ImageView placeholder rendering added; full PNG decode deferred |
| B (generic input/click) | IN_PROGRESS | dispatch_click wired after onCreate; full proof needs Calculator APK |
| B2 (event dedup) | NOT_STARTED | Needs B proof first |
| C (SQLite) | NOT_STARTED | Independent track |
| F (Handler/Looper) | NOT_STARTED | Infrastructure wired in EXP-086, no trigger yet |
| I (multi-DEX audit) | NOT_STARTED | |
| M (Telegram login) | LOCKED | Depends on B+B2 |

## Current Phase
A4 → B → B2

## Exact Next Action
1. Fix intermittent segfault in recursive rendering lambda
2. Create/run headingcalculator with per-APK layout cache to verify click dispatch
3. Implement Phase C (SQLite micro test) as independent track

## Files Changed
- miniandroid/src/runtime/execution_engine.cpp (A2+A5+A4+B rendering + click dispatch)
- miniandroid/src/framework/android_shadows.cpp (per-APK cache loading, ActivityShadow handles_class)
- miniandroid/src/framework/android_shadows.h (set_apk_path)
- miniandroid/tools/exp087_layout_cache_generator.py (layout cache tool)
- miniandroid/docs/exec-plans/active/EXP088.md (exec plan)

## Known Issues
- gmdice run sometimes segfaults during rendering (recursive lambda depth)
- headingcalculator layout cache has custom view classes not yet handled by renderer
- Telegram has no layout cache (0 layouts found — uses obfuscated res/ paths)
