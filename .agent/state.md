# MiniAndroid Project State

**Last updated:** 2026-08-16 (EXP-043 cycle complete)
**Latest commit:** 2bbcf34 (EXP-043 Phase 4: Pre-populate applicationContext)

## Telegram Execution Stage

| Layer | Status |
|-------|--------|
| APK parsing | DONE |
| Manifest resolution | DONE |
| MultiDex loading | DONE (5 DEX, 41078 classes) |
| Per-DEX method resolution | DONE (BLOCKER-033 fixed) |
| Dalvik opcode coverage | DONE (all if-* and goto values corrected to AOSP canonical) |
| Recursive method invocation | DONE (BLOCKER-034 fixed) |
| Memory architecture | DONE (peak RSS 440 MB, ring buffers) |
| Android framework stubs | PARTIAL (30+ P0/P1 APIs implemented in bridge_to_api) |
| Pre-populated static fields | DONE (applicationContext + Activity this) |
| JNI runtime | NOT STARTED (inventory taken: 462 native methods, 376 Java_* exports) |
| Native .so loading | NOT STARTED |
| UI rendering | NOT STARTED |

## Current Achievement

**LaunchActivity.onCreate COMPLETES SUCCESSFULLY** (exit code 0, Result: SUCCESS).

- 42 unique methods reached including:
  - LaunchActivity.onCreate (1330 instructions)
  - Theme.createChatResources (2441 instructions)
  - Theme.createCommonResources (753 instructions)
  - Theme.createDialogsResources (878 instructions)
  - ApplicationLoader.postInitApplication (266 instructions)
  - All Kotlin Intrinsics methods (checkNotNullParameter, throwParameterIsNullNPE, etc.)
  - AndroidUtilities.dp, isTablet, bold, checkDisplaySize, etc.
  - RLottieDrawable.recycle, recycleResources, checkChoreographer, etc.

## Active Blocker

`ApplicationLoader.postInitApplication` exits prematurely at PC=8 (goto/32)
because D8 uses `if-ltz` (op=0x39) for null checks, but our engine implements
standard AOSP `if-ltz` semantics (branch if < 0). When `applicationContext`
is a non-null OBJECT_REF, `if-ltz` treats it as 0, so the null check fails
and the method returns early.

**Fix needed:** D8-specific if-ltz handling that distinguishes null checks
(if-ltz on OBJECT_REF → branch if non-null) from numeric comparisons
(if-ltz on INT32 → branch if < 0).

## Solved Blockers (EXP-043)

| ID | Description | Commit |
|----|-------------|--------|
| goto opcode values | GOTO=0x27, GOTO_16=0x28, GOTO_32=0x29 (were swapped) | a730c27 |
| if-* opcode values | All 12 if-* opcodes corrected to AOSP canonical | a730c27 |
| cmp-* opcode values | CMPL_FLOAT=0x2c through CMP_LONG=0x30 (were off-by-1) | a730c27 |
| if-*z handlers | Each if-*z now has its own handler (was all dispatching to if-eqz) | a730c27 |
| goto/32 byte order | D8 emits 2-code-unit goto/32 with 16-bit offset (not 3-unit 32-bit) | a5dc072 |
| Intrinsics loop | if-* and goto fixes eliminated the createParameterIsNullExceptionMessage loop | a730c27 |
| Pre-populated applicationContext | ApplicationLoader.applicationContext set before onCreate | 2bbcf34 |

## Key Evidence Files

- `miniandroid/docs/EXP043_STUB_DEBT.md` — 6 documented stubs
- `miniandroid/docs/EXP043_JNI_DISTANCE.md` — JNI distance analysis (not reached yet)
- `miniandroid/docs/EXP043_TELEGRAM_SOURCE_MAP.md` — Telegram source compatibility map
- `miniandroid/docs/EXP043_LOOP_DETECTOR_TESTS.md` — Loop detector validation
- `miniandroid/run/exp043_auto/EXP043_REPORT.md` — Automated execution report
- `miniandroid/docs/exp042/EXP042_MEMORY_ANALYSIS.md` — Memory architecture
- `miniandroid/docs/exp042/TELEGRAM_EXECUTION_PATH.md` — Execution path tracing
- `miniandroid/docs/exp042/JNI_INVENTORY.md` — 462 native methods
- `miniandroid/docs/exp042/NATIVE_LIBRARIES.md` — libtmessages.49.so analysis

## Solved Blockers (chronological, most recent first)

| ID | Date | Description | Commit |
|----|------|-------------|--------|
| EXP-042 Phase 2 | 2026-08-16 | Return-opcode bounds check + iget/iput/sget/sput never-return-false | d48d479 |
| EXP-042 Phase 1 | 2026-08-16 | Memory ring buffers + per-frame loop detector | d48d479 |
| BLOCKER-037 | 2026-08-15 | halted_on_return_ leak across recursive calls | b5e02ca |
| BLOCKER-036 | 2026-08-15 | goto/16 and goto/32 format handling | ecfd785 |
| BLOCKER-035 | 2026-08-15 | Correct class→DEX ownership mapping | 98ec49e |
| BLOCKER-034 | 2026-08-15 | Recursive DEX method invocation (309 → 10001 instructions) | 63f8e62 |
| BLOCKER-033 | 2026-08-15 | Per-DEX method resolution via raw DEX bytes | 00d6fc4 |
| BLOCKER-032 | 2026-08-15 | const/high16 (0x15) opcode | d7f9291 |
| BLOCKER-031 | 2026-08-15 | Array opcodes (new-array, aget, aput) | d7f9291 |
| BLOCKER-030 | 2026-08-15 | invoke-*/range opcodes | d7f9291 |
| BLOCKER-029 | 2026-08-15 | if-eqz/if-nez opcode values off by 1 | d7f9291 |
| BLOCKER-028 | 2026-08-15 | 35 new arithmetic opcodes | d7f9291 |
| BLOCKER-027 | 2026-08-15 | sput-boolean and sget/sput variants | d7f9291 |
| BLOCKER-026 | 2026-08-15 | move-object/from16 (0x08) | d7f9291 |
| BLOCKER-025 | 2026-08-15 | Launcher resolution via manifest | d7f9291 |
| BLOCKER-024 | 2026-08-15 | MultiDex support | d7f9291 |
| BLOCKER-023 | 2026-08-15 | APK parser caching | 133ec32 |
| BLOCKER-022 | 2026-08-15 | activity-alias tracking | 133ec32 |

## Architectural Discoveries

- Per-DEX method_idx resolution is mandatory for multidex APKs (BLOCKER-033)
- `static thread_local` state across recursive method calls is dangerous
  (BLOCKER-036 + EXP-042 Phase 2 bug)
- `iget`/`iput` error paths MUST advance pc_ — returning false causes
  infinite loops at every field access on uninitialized `this`
- Loop detector threshold of 50 000 per-frame allows legitimate loops
  while catching real `while(true)` busy-waits

## Key Evidence Files

- `miniandroid/docs/exp042/EXP042_MEMORY_ANALYSIS.md`
- `miniandroid/docs/exp042/TELEGRAM_EXECUTION_PATH.md`
- `miniandroid/docs/exp042/EXP042_TELEGRAM_COMPATIBILITY_MAP.md`
- `miniandroid/docs/exp042/JNI_INVENTORY.md`
- `miniandroid/docs/exp042/NATIVE_LIBRARIES.md`
- `miniandroid/run/exp042_auto/EXP042_REPORT.md`
- `miniandroid/docs/EXP038_TELEGRAM_BLOCKERS.md`
