# MiniAndroid Agent State

## Current Experiment
EXP-057 — Final Login-Path Forensic + Sustained Autonomous Execution

## Current Commit
ae31f08 — EXP-057: Login path reached! getIntent heap_ fix + invoke-virtual return fix

## Status: LOGIN PATH REACHED ✅

## Baseline Metrics (EXP-057 final)
- Unique methods: 501
- HALT: 0
- Instructions: 66,010
- CLASS_INIT: 56
- EXCEPTION: 10

## Login Path Progress
- getIntent() → non-null Intent (intent_id=1122) ✅
- isClientActivated() → returns 1 (currentUser is null) ✅
- getFragmentStack() → returns NULL_REF ✅
- List.isEmpty() → returns false (0) ✅
- getClientNotActivatedFragment() → ENTERED ✅ (returns obj_id=1300)
- LoginActivity.loadCurrentState() → ENTERED ✅
- addFragmentToStack() → CALLED ✅
- Fragment lifecycle → NOT YET (next blocker)

## Key Fixes Applied (EXP-057)
1. ShadowRegistry.set_heap() now calls init(heap) on all registered shadows
2. invoke-virtual handler now sets last_invoke_return_ = return_val after recursive invoke

## Reproducibility
3 independent runs: all identical (501 methods, 66010 instructions, 0 HALT)

## Next Blocker
Fragment lifecycle (onCreate, onCreateView) — addFragmentToStack is called
but Fragment lifecycle methods are not yet reached.

## Key Files
- src/dex/dalvik_engine.cpp — interpreter + bridge_to_api
- src/framework/shadow_registry.h — set_heap fix
- src/framework/android_shadows.cpp — getIntent fix
- docs/EXP057_REPORT.md — final report

## Resume Instructions
1. Build: `cd miniandroid && bash build_exp042.sh`
2. Run: `./build_exp042/miniandroid_exp042 download/exp038_telegram/Telegram.apk run/exp057`
3. Read this file + worklog.md for context
4. Check run/exp057/ for investigation artifacts
