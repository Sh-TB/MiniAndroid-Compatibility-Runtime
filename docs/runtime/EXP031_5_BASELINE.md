# EXP-031.5 BASELINE — Real Dalvik Bytecode Execution Proof

**Date**: 2026-08-14  
**Previous Experiment**: EXP-031 (Real Dalvik Engine Integration)  
**Git Commit**: `c435cc8`  
**Binary**: `build/miniandroid` (23,953,136 bytes)

---

## Executive Summary

This baseline captures the state of MiniAndroid **before** EXP-031.5 validation begins.

### Current Status: PARTIALLY INTEGRATED

| Component | Status | Evidence |
|-----------|--------|----------|
| ExecutionMode enum | ✅ IMPLEMENTED | `execution_engine.h:28-31` |
| CLI flag parsing | ✅ WORKING | `--execution-mode=legacy\|real-dalvik` |
| DalvikEngine integration | ✅ CONNECTED | Called from `stage_execute_application_real_dalvik()` |
| ExecutionSource tracking | ✅ DEFINED | `HOST_SHORTCUT`, `REAL_DALVIK_INTERPRETER` |
| Real bytecode execution | ❌ UNPROVEN | No evidence of opcodes actually executed |
| Instruction traces | ❌ MISSING | No trace files generated |
| Runtime assertions | ❌ ABSENT | Silent fallback possible |

---

## What Currently Works

### 1. Mode Switching (VERIFIED)
```bash
# Legacy mode - uses HOST_SHORTCUT path
./build/miniandroid run --execution-mode=legacy HelloWorld.apk
# Result: SUCCESS ✅ (but fake lifecycle)

# Real-Dalvik mode - calls DalvikEngine
./build/miniandroid run --execution-mode=real-dalvik HelloWorld.apk  
# Result: SUCCESS ⚠️ (calls engine but may not execute real bytecode)
```

### 2. Pipeline Architecture
```
APK → Parse → DEX → [MODE SWITCH] → Render → Output
                    ├─ LEGACY ──→ stage_execute_application_legacy()
                    └─ REAL ───→ stage_execute_application_real_dalvik()
                                       └─ dalvik_engine_.execute_apk()
```

### 3. DalvikEngine Capabilities (from EXP-030)
- **25+ opcodes implemented**: const, move, invoke-*, return, new-instance, etc.
- **Full register machine**: DexRegisterFile with read/write
- **Object heap**: DalvikHeap with allocation tracking
- **Call stack**: StackFrame management
- **API bridge**: Android stub integration

---

## What Is NOT Yet Proven

### Critical Gaps

#### Gap #1: No Opcode Execution Evidence
**Problem**: We don't know if `ExecuteInstruction()` is ever called.

**Evidence Required**:
- `opcode_trace.json` with actual PC advances
- `instruction_traces[]` array populated
- `total_instructions_executed > 0`

**Current State**: UNKNOWN

#### Gap #2: DEX Bytecode Extraction
**Problem**: DEX parser may not populate `method.bytecode` arrays.

**Impact**: DalvikEngine receives empty bytecode → no instructions to execute.

**Location to Check**: `dex_parser.cpp` - method bytecode extraction

#### Gap #3: Silent Fallback to HOST_SHORTCUT
**Problem**: If DalvikEngine executes 0 instructions, code falls back:
```cpp
// execution_engine.cpp:244
if (dalvik_result.total_instructions_executed > 0) {
    // Real path
} else {
    // ⚠️ SILENT FALLBACK TO FAKE!
    result.content_view = create_hello_world_view(config);
}
```

**Risk**: Reports SUCCESS without any real execution.

#### Gap #4: Lifecycle Not From DEX
**Problem**: Even in REAL_DALVIK mode, lifecycle calls may come from C++:
```cpp
// execution_engine.cpp:262-269
if (!lifecycle_from_dex) {
    // These are HOST_SHORTCUT calls!
    result.activity->onCreate(null_bundle);
    result.activity->onStart();
    result.activity->onResume();
}
```

---

## Known Blockers

| ID | Severity | Description | Impact |
|----|----------|-------------|--------|
| B001 | CRITICAL | DEX parser may not extract method bytecode | Empty instruction streams |
| B002 | HIGH | Class resolver disconnected from execution | Method resolution fails |
| B003 | MEDIUM | API bridge incomplete | Complex APKs fail |
| B004 | HIGH | No assertion if ExecuteInstruction never called | Silent fake success |

---

## Baseline Test Results

### Legacy Mode Test
```
Command: ./build/miniandroid run --execution-mode=legacy test_apks/HelloWorld.apk
Result:  SUCCESS ✅
Mode:    HOST_SHORTCUT (simulated lifecycle)
Frames:  1
Errors:  0
Warnings: 0
```

### Real-Dalvik Mode Test
```
Command: ./build/miniandroid run --execution-mode=real-dalvik test_apks/HelloWorld.apk
Result:  SUCCESS ✅
Mode:    REAL_DALVIK_INTERPRETER (called)
Frames:  1
Errors:  0
Warnings: 1  ← Something suspicious!
```

**⚠️ Warning in real mode needs investigation!**

---

## Success Criteria for EXP-031.5

Before this experiment passes, ALL of these must be true:

### Mandatory Evidence
- [ ] `dalvik_result.total_instructions_executed > 0`
- [ ] `opcode_trace.json` exists with entries
- [ ] PC address advances through code_item
- [ ] Register values change according to instructions
- [ ] At least one `invoke-*` opcode executed
- [ ] At least one object allocated on heap
- [ ] Lifecycle event generated from DEX trace (not C++ call)
- [ ] Zero `HOST_SHORTCUT` involvement in lifecycle

### Forbidden Conditions
- [ ] NO simulated success without opcode evidence
- [ ] NO lifecycle shortcut when REAL_DALVIK mode selected
- [ ] NO manually injected state transitions
- [ ] NO "PASS" without `REAL_DALVIK_INTERPRETER` source

---

## Next Steps (PHASES 1-12)

See EXP-031.5 specification for detailed phase requirements:

1. **PHASE 1**: Audit and verify real execution path
2. **PHASE 2**: Implement mandatory trace system
3. **PHASE 3**: Remove all false success conditions
4. **PHASE 4**: Create minimal deterministic test APKs
5. **PHASE 5**: Validate core opcodes (20+)
6. **PHASE 6**: Validate object model (heap/dispatch)
7. **PHASE 7**: Execute real APKs in real-dalvik mode only
8. **PHASE 8**: Validate success criteria checklist
9. **PHASE 9**: Implement failure intelligence system
10. **PHASE 10**: Generate legacy vs real comparison report
11. **PHASE 11**: Write final documentation
12. **PHASE 12**: GitHub commit and push

---

## Golden Debug Protocol Reminder

> **"This APK ran because MiniAndroid executed its bytecode, NOT because the framework pretended it ran."**

Every claim must have artifacts:
- Opcode traces with PC addresses
- Register snapshots before/after
- Method dispatch records
- Heap allocation logs
- ExecutionSource = `REAL_DALVIK_INTERPRETER`

---

*Baseline captured at experiment start. All changes after this point are part of EXP-031.5.*
