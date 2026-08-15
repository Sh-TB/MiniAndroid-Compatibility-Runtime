# MiniAndroid Project State

**Last updated:** 2026-08-16 (EXP-043 cycle starting)
**Latest commit:** d48d479 (EXP-042: 7-phase Telegram reality acceleration cycle)

## Telegram Execution Stage

| Layer | Status |
|-------|--------|
| APK parsing | DONE |
| Manifest resolution | DONE |
| MultiDex loading | DONE (5 DEX, 41078 classes) |
| Per-DEX method resolution | DONE (BLOCKER-033 fixed) |
| Dalvik opcode coverage | DONE (0 missing opcodes) |
| Recursive method invocation | DONE (BLOCKER-034 fixed) |
| Memory architecture | DONE (peak RSS 439 MB at 400K+ insns) |
| Android framework stubs | PARTIAL (16 P0/P1 APIs implemented in bridge_to_api) |
| JNI runtime | NOT STARTED (inventory taken: 462 native methods, 376 Java_* exports) |
| Native .so loading | NOT STARTED |
| UI rendering | NOT STARTED |

## Active Blocker

`Intrinsics.createParameterIsNullExceptionMessage` loops at PC=0xf
(`op_at_pc=0x46` = `iget-object`) because the Kotlin NPE exception
builder reads an instance field from a null `this` reference. This
happens when `Intrinsics.checkNotNullParameter` is called with a null
argument inside `SavedStateRegistryController.performAttach`.

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
