# EXP-048 Progress Summary

**Date:** 2026-08-17
**Commit:** 31a9113

## Execution Metrics

| Metric | EXP-047 (baseline) | EXP-048 (current) | Change |
|--------|-------------------|-------------------|--------|
| Unique methods | 189 | 189 | — |
| JNI calls | 5 | 5 | — |
| SharedPreferences API calls | 0 | 128 | +128 |
| HALT-LOOP | 0 | 0 | — |
| HALT-GOTO | 0 | 0 | — |
| Memory peak | 440 MB | 440 MB | stable |
| Result | SUCCESS | SUCCESS | — |

## Key Fixes

### 1. invoke-interface Handler Fixed (CRITICAL)
**Root cause:** The invoke-interface handler was NOT calling bridge_to_api. It only logged the call and returned void, silently ignoring ALL interface method calls.

**Fix:** invoke-interface now:
1. Extracts args from 35c format (argc from high nibble)
2. Tries try_recursive_invoke first
3. Falls through to bridge_to_api if no DEX implementation found

**Impact:** 128 SharedPreferences API calls now reach bridge_to_api:
- 68 × getBoolean, 36 × getInt, 8 × getString, 8 × getLong, 3 × contains
- 5 × getSharedPreferences (creates per-name objects with XML loading)

### 2. Persistent SharedPreferences Implemented
- getSharedPreferences(name, mode) creates per-name heap objects
- XML file loading from runtime/data/org.telegram.messenger/shared_prefs/
- All getters: getString, getBoolean, getInt, getLong, contains
- All setters: putString, putBoolean, putInt, putLong, putFloat
- Editor pattern: edit(), commit(), apply() with XML persistence
- Android-compatible XML format

### 3. Native Method Analysis
- 462 native methods across 5 DEX files
- 44 P0 (startup path) native methods
- JNI bridge with 12 registered stubs
- 5 native_getCurrentTime calls dispatched via HOST_COMPATIBILITY_STUB

## Checkpoints

| Checkpoint | Status | Evidence |
|-----------|--------|----------|
| A: LaunchActivity entered | ✅ | METHOD-IN log |
| B: LaunchActivity completed | ✅ | Result: SUCCESS |
| C: Application initialized | ✅ | postInitApplication reaches deep |
| D: UserConfig initialized | ✅ | UserConfig.getInstance, loadConfig |
| E: SharedPreferences read | ✅ | 128 API calls (getBoolean, getInt, etc.) |
| F: NativeLoader reached | ✅ | NativeLoader.initNativeLibs |
| G: First native dispatched | ✅ | native_getCurrentTime × 5 |
| H: SharedPreferences written | ❌ | edit/commit not called in this path |
| I: Login UI state | ❌ | Not yet reached |

## Next Blockers

1. **SharedPreferences write path** — SharedConfig.loadConfig only reads, doesn't write.
   Need to find code path that calls edit().putString().commit() to prove persistence.
2. **More native methods** — Only native_getCurrentTime is dispatched. Need deeper execution
   to reach native_init, native_setJava, etc.
3. **Login UI** — LaunchActivity.onCreate completes but doesn't reach Login View creation.
