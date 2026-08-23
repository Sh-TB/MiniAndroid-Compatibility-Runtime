# MiniAndroid Agent State — EXP-088+ Campaign

## Current Experiment
EXP-088+ — Long-horizon MiniAndroid generic compatibility campaign

## Current Commit (most recent state)
HEAD — Phase 1.2: Multi-DEX class injection (28557 Telegram classes injected)

## Status: 10 PROVEN, 1 IN PROGRESS (M boundary advanced)

### PROVEN (no change this round)
- A1 AXML inflation
- A2 measure/layout
- A5 text rendering (BitmapFont uninit FIXED in previous round)
- A4 drawable/image loading
- B1 valid PNG output
- B5 entry-point resolution
- B generic input/click
- B2 event deduplication
- C SQLite
- F Handler/Looper
- I multi-DEX audit

### IN PROGRESS (M boundary moved)
Phase M was BLOCKED on UserConfig.isClientActivated "class not in index".
After this round, the boundary has moved to:

```
LaunchActivity.onCreate (1330 instructions) ✅
→ handleIntent (15606 instructions) ✅
→ switchToAccount ✅
→ UserConfig.isClientActivated (CALLED, not "NOT FOUND") ✅
→ LoginActivity.loadCurrentState (class found, 260 methods) ✅
→ IntroActivity.<init> ✅
→ addDelegate (8 calls) ✅
→ ActionBarLayout.<init> (187 instructions) ✅
→ [next: PhoneView rendering / PhoneView transition]
```

### Root-cause fixes this round
1. **Multi-DEX class injection** (PRIMARY FIX):
   - `stage_parse_dex()` only parsed classes.dex (DEX 0) into `dex_report.classes`
   - Other DEX files (classes2..classesN) were loaded into `per_dex_raw_data_` but
     their classes were NEVER merged into `dex_report.classes` and `class_info_index_`
   - Only ONE class was injected on-demand (manifest activity class)
   - **FIX**: Added `DalvikExecutionEngine::inject_secondary_dex_classes()` method
     that parses each secondary DEX with `DexParser::parse_data()` and injects ALL
     classes into `dex_report_->classes` (via const_cast — same pattern as existing
     on-demand injection). Updates `class_info_index_` for O(1) lookup.
   - Called from inside `execute_apk_with_activity()` right after `dex_report_` is set.
   - For Telegram: **injected 28557 classes** from 4 secondary DEX files.

2. **ConcurrentHashMap bypass** (generic, supporting fix):
   - `Lj$/util/concurrent/ConcurrentHashMap;.e` (computeIfAbsent) loops forever
   - Without bypass, runtime hangs in `FastDateFormat.<clinit>` before reaching LoginActivity
   - **FIX**: Added `Lj$/util/concurrent/ConcurrentHashMap;` and
     `Ljava/util/concurrent/ConcurrentHashMap;` to the framework-bypass list in
     `try_recursive_invoke` (lines 1863-1897 and 1973-1982).
   - This is a GENERIC fix — any APK using desugared Java 8 collections benefits.

### Verified secondary findings
1. **`this` receiver propagation**: Already fixed in primary branch (EXP-061 FIX comment at line 6521-6538). Verified via Telegram's IntroActivity.<init> executing with correct receiver.
2. **Secondary DEX lazy injection**: Root cause confirmed and FIXED (see above).
3. **getInstance dispatch**: Same root cause as #2 — fixed by inject_secondary_dex_classes(). UserConfig.getInstance now executes (was "class not in index").

### Phase M boundary progression
**BEFORE this round:**
```
LaunchActivity.onCreate → UserConfig.isClientActivated → "class not in index" (BLOCKED)
```

**AFTER this round:**
```
LaunchActivity.onCreate (1330 instructions) ✅
→ handleIntent (15606 instructions) ✅
→ switchToAccount ✅
→ UserConfig.isClientActivated (CALLED, not "NOT FOUND") ✅
→ LoginActivity.loadCurrentState (class found, 260 methods) ✅
→ IntroActivity.<init> ✅
→ addDelegate (8 calls) ✅
→ ActionBarLayout.<init> (187 instructions) ✅
→ [next: PhoneView rendering / PhoneView transition]
```

## Resume Instructions (next round)

1. The campaign is NOT complete. M is IN PROGRESS (no longer BLOCKED).
2. **Exact next action**: Investigate what happens after IntroActivity is added to the
   fragment stack. The runtime needs to:
   - Actually call `IntroActivity.onFragmentCreate()` (currently only `addDelegate` is dispatched)
   - Then transition to `LoginActivity` (when the user clicks "Start Messaging")
   - Then render `PhoneView` (which requires layout_cache.json for Telegram's login layout —
     we already have `download/exp038_telegram/layout_cache.json` but it's not being loaded)
   - Then inject a phone number
   - Then mock `auth.sendCode`
3. Reproducer:
   ```
   cd miniandroid && ./build/miniandroid run -o /tmp/tg_test download/exp038_telegram/Telegram.apk
   grep -aE "EXP088-MD-INJECT|UserConfig|LoginActivity|IntroActivity" /tmp/tg_test.log
   ```
4. After M is PROVEN (full login chain works end-to-end), the campaign is complete.
5. Do NOT mark M as PROVEN unless the full chain works end-to-end.

## Build artifacts
- `/home/z/my-project/scripts/a4_build.sh` — builds all A4 + F + multi-DEX inject tests
- `/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/tests/exp088_multidex_inject_test.cpp` — multi-DEX inject regression test
- `/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/docs/compatibility/SECONDARY_FORENSICS_INTEGRATION.md` — secondary forensics integration doc

## Reproducibility
- Telegram: 3/3 reproducible runs (identical screenshot SHA `24956663322f4c73c55f30fc7e46dc63f7578102d1db08e9ae311c19d9e9d495`)
- All A4 tests pass: 4/4 + 4/4 + multi + simplestopwatch
- All Phase F tests pass: 23/23
- All multi-DEX inject tests pass: 2/2
- All regression tests pass: A1, B, B2, C, F, I — no regressions introduced
