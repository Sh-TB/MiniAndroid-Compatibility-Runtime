# MiniAndroid Agent State

## Current Experiment
EXP-057 — Final Login-Path Forensic + Sustained Autonomous Execution

## Current Commit
cdc5c08 — EXP-056: getIntent() null fix + CollectionShadow null handling

## Baseline Metrics (EXP-056)
- Unique methods: 442
- HALT: 0
- Instructions: 60,437
- CLASS_INIT: 52
- EXCEPTION: 10

## Current Blocker
getFragmentStack() returns NULL_REF → isEmpty() on null → execution jumps to checkLayout (PC 970) instead of reaching getClientNotActivatedFragment (PC 719).

## Key Files
- src/dex/dalvik_engine.cpp — interpreter + bridge_to_api
- src/framework/android_shadows.cpp — shadow implementations
- src/runtime/application_runtime.cpp — runtime wiring
- docs/EXP056_REPORT.md — prior experiment report

## Resume Instructions
1. Build: `cd miniandroid && bash build_exp042.sh`
2. Run: `./build_exp042/miniandroid_exp042 download/exp038_telegram/Telegram.apk run/exp057`
3. Read this file + worklog.md for context
4. Check run/exp057/ for investigation artifacts
