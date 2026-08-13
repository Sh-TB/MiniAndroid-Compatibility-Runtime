# EXP-031: Baseline Documentation — Pre-Integration State

**Phase:** PHASE 0 — SAFETY AUDIT AND BASELINE FREEZE  
**Date:** 2026-08-14  
**Purpose:** Document current execution path BEFORE connecting DalvikEngine  
**Status:** ⚠️ **FAKE LIFECYCLE DETECTED**

---

## Executive Summary

MiniAndroid currently achieves "successful execution" through **simulated lifecycle events**, NOT real Dalvik bytecode interpretation. This baseline document captures the exact state before integration so we can prove the transformation.

### Critical Finding

```
CURRENT STATE:
APK → Parse → ⚠️ FAKE onCreate() → Render → "SUCCESS" ❌

TARGET STATE:
APK → Parse → DalvikEngine → Real Opcodes → Real onCreate() → Render → "SUCCESS" ✅
```

---

## 1. Current Execution Path (DETAILED)

### 1.1 Entry Point Flow

```
┌─────────────────────────────────────────────────────────────┐
│  main.cpp::main() [Line 228]                                │
│    ↓                                                        │
│  Parse CLI arguments (--output, --text, --width, etc.)      │
│    ↓                                                        │
│  cmd_run(apk_path, config) [Line 186]                       │
│    ↓                                                        │
│  ExecutionEngine::execute(apk_path, config) [Line 28]       │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Pipeline Stages (ExecutionEngine::execute)

| Stage | Function | Line | Status | Notes |
|-------|----------|------|--------|-------|
| 1 | `stage_load_apk()` | 71 | ✅ WORKING | Parses APK with ApkParser |
| 2 | `stage_parse_dex()` | 92 | ✅ WORKING | Extracts classes.dex, parses DEX |
| 3 | `stage_initialize_runtime()` | 132 | ✅ WORKING | Allocates framebuffer |
| 4 | `stage_load_classes()` | 161 | ⚠️ STUB | Logs only, no real class loading |
| **5** | **`stage_execute_application()`** | **183** | **❌ FAKE** | **SIMULATES lifecycle!** |
| 6 | `stage_render_frame()` | 220 | ✅ WORKING | Renders to framebuffer |
| 7 | `stage_capture_output()` | 248 | ✅ WORKING | Writes PPM screenshot |
| 8 | `stage_generate_reports()` | 304 | ✅ WORKING | Generates reports |

---

## 2. THE PROBLEM: Fake Lifecycle (Stage 5)

### 2.1 Location

**File:** `src/runtime/execution_engine.cpp`  
**Function:** `ExecutionEngine::stage_execute_application()`  
**Lines:** 183-218

### 2.2 What It Does (WRONG)

```cpp
// Line 187: Creates Activity WITHOUT DEX class loading
result.activity = std::make_shared<api::Activity>();  // ❌ HOST_SHORTCUT

// Lines 191-210: SIMULATES lifecycle
if (config.simulate_lifecycle) {
    // Creates fake view from heuristics
    result.content_view = create_view_from_layout(result.dex_report);  // ❌ HOST_SHORTCUT
    
    // Calls lifecycle directly - NO DEX involved!
    result.activity->setContentView(result.content_view);   // ❌ HOST_SHORTCUT
    result.activity->onCreate(null_bundle);                  // ❌ HOST_SHORTCUT
    result.activity->onStart();                              // ❌ HOST_SHORTCUT
    result.activity->onResume();                             // ❌ HOST_SHORTCUT
}
```

### 2.3 Evidence of Falsification

| Check | Result | Evidence |
|-------|--------|----------|
| Opcode trace exists? | ❌ NO | No `opcode_trace.json` with instructions |
| Method body executed? | ❌ NO | `method.bytecode` never read by executor |
| PC advanced? | ❌ NO | Program Counter doesn't exist in this path |
| ExecutionSource? | ❌ MISSING | All events lack source attribution |
| DEX offset? | ❌ UNKNOWN | No bytecode address in lifecycle events |

---

## 3. Shortcut Functions Identified

### 3.1 `create_hello_world_view()` 
**Location:** execution_engine.cpp:335  
**Type:** HOST_SHORTCUT  
**Purpose:** Creates hardcoded TextView without DEX

```cpp
auto text_view = std::make_shared<api::TextView>();
text_view->setText("Hello MiniAndroid");  // Hardcoded!
```

### 3.2 `create_view_from_layout()`
**Location:** execution_engine.cpp:356  
**Type:** HOST_SHORTCUT  
**Purpose:** Heuristic view creation from string constants

```cpp
// Searches DEX strings for display text (NOT real layout inflation)
for (const auto& str : report.strings) {
    if (str.find("Hello") != std::string::npos) {
        display_text = str;  // Guesswork!
        break;
    }
}
```

---

## 4. DalvikEngine Status (EXP-030 Build)

### 4.1 What Exists

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| Header | `src/dex/dalvik_engine.h` | 890 | ✅ Complete |
| Implementation | `src/dex/dalvik_engine.cpp` | 1328 | ✅ Complete |
| **Total** | | **2218** | **✅ Compiled into binary** |

### 4.2 Components Built

- **DalvikValue** — 15-type value system (INT32, OBJECT_REF, etc.)
- **DexRegisterFile** — v0-vN + p0-pN register file
- **DalvikHeap** — Object allocation with unique IDs
- **CallStack/StackFrame** — Method invocation tracking
- **InstructionTrace** — Per-opcode evidence capture
- **ApiCallTrace** — Android API call logging
- **DalvikExecutionResult** — Complete results container

### 4.3 Entry Points Available

```cpp
// Main APK execution
DalvikExecutionResult execute_apk(
    const std::string& apk_path,
    const dex::DexReport& dex_report,
    bool verbose
);

// Individual method execution
DalvikExecutionResult execute_method(
    const dex::MethodInfo& method,
    const dex::DexReport& dex_report,
    const std::vector<DalvikValue>& args,
    bool verbose
);
```

### 4.4 Connection Status

```
┌─────────────────────────────────────────┐
│  ExecutionEngine.cpp                    │
│                                         │
│  ┌───────────────────────────┐         │
│  │ stage_execute_application │         │
│  │                           │         │
│  │  ⚠️ Currently calls:      │         │
│  │  api::Activity->onCreate()│ ← FAKE  │
│  │                           │         │
│  │  ✅ Should call:          │         │
│  │  dalvik_engine_.execute() │ ← REAL  │
│  └───────────┬───────────────┘         │
│              │ NOT CONNECTED           │
│              ▼                         │
│  ┌───────────────────────────┐         │
│  │  DalvikEngine (ORPHANED)  │         │
│  │  - Built and compiled     │         │
│  │  - Has 25+ opcodes       │         │
│  │  - NEVER CALLED           │         │
│  └───────────────────────────┘         │
└─────────────────────────────────────────┘
```

---

## 5. Current Configuration

### 5.1 ExecutionConfig (execution_engine.h:35-52)

```cpp
struct ExecutionConfig {
    std::string output_directory = "./run";
    int screen_width = 1080;
    int screen_height = 1920;
    uint32_t background_color = 0xFFFFFFFF;
    bool verbose_logging = false;
    bool generate_screenshot = true;
    bool generate_reports = true;
    
    // ⚠️ PROBLEM: No execution mode switch!
    bool simulate_lifecycle = true;  // Always enabled!
    std::string simulated_text = "";
};
```

### 5.2 Missing Features for Integration

| Feature | Current | Required |
|---------|---------|----------|
| Execution mode switch | ❌ None | `--execution-mode=legacy\|real-dalvik` |
| ExecutionSource tracking | ❌ Missing | Enum: HOST_SHORTCUT vs REAL_DALVIK_INTERPRETER |
| DalvikEngine member | ❌ Not in ExecutionEngine | Add as member variable |
| Mode-aware pipeline | ❌ Single path | Branch on mode |

---

## 6. Diagnostic Emitters

### 6.1 TraceEngine (Internal)
- **File:** `src/diagnostics/trace_engine.h/cpp`
- **Status:** Active, used by all stages
- **Problem:** Doesn't track ExecutionSource

### 6.2 State Machine (External Validator)
- **File:** `tools/exp029_state_machine.py`
- **Status:** Runs post-execution
- **Problem:** Validates output, can't detect fake vs real

### 6.3 EXP-030 Validator
- **File:** `tools/exp030_real_dalvik_validator.py`
- **Status:** Built but engine not called
- **Result:** All APKs show BYTECODE_LOADED with 0 opcodes

---

## 7. Baseline Metrics

### 7.1 EXP-030 Validation Results

```
Total APKs Tested: 12
Depth Achieved: BYTECODE_LOADED (all)
Opcodes Executed: 0 (engine exists but not called)
Registers Modified: false
Objects Allocated: 0
API Calls from DEX: 0

Fake Success Rate: 100%
(All "successes" come from shortcuts, not real execution)
```

### 7.2 Binary Information

```
Binary: build/miniandroid
Size: 23.7 MB (+14% from EXP-030 DalvikEngine)
Contains: dalvik_engine.o (compiled but orphaned)
Compiler: g++ (Debian 14.2.0-19)
Standard: C++17
```

---

## 8. Integration Points (Where to Connect)

### 8.1 Primary Integration Point

**Location:** `ExecutionEngine::stage_execute_application()` (Line 183)

**Before (Current - FAKE):**
```cpp
bool ExecutionEngine::stage_execute_application(...) {
    result.activity = std::make_shared<api::Activity>();  // Shortcut
    result.activity->onCreate(null_bundle);                 // Fake
    // ...
}
```

**After (Target - REAL):**
```cpp
bool ExecutionEngine::stage_execute_application(...) {
    if (config.execution_mode == ExecutionMode::REAL_DALVIK) {
        // Route through DalvikEngine
        auto dalvik_result = dalvik_engine_.execute_apk(
            result.apk_info.apk_path,
            result.dex_report,
            config.verbose_logging
        );
        // Extract real Activity from heap...
    } else {
        // Legacy shortcut path (for regression comparison)
        legacy_execute_application_shortcut(result, config);
    }
}
```

### 8.2 Secondary Changes Needed

1. **Add include:** `#include "dex/dalvik_engine.h"` to execution_engine.h
2. **Add member:** `dalvik::DalvikExecutionEngine dalvik_engine_;`
3. **Add enum:** `enum class ExecutionMode { LEGACY, REAL_DALVIK };`
4. **Add config field:** `ExecutionMode execution_mode = ExecutionMode::LEGACY;`
5. **Parse CLI:** `--execution-mode=real-dalvik` flag in main.cpp

---

## 9. Risk Assessment

### 9.1 High-Risk Areas

| Area | Risk | Mitigation |
|------|------|------------|
| Breaking existing tests | Legacy mode may diverge | Keep LEGACY mode working |
| Performance regression | Real execution slower | Profile and optimize later |
| Missing opcodes | Some APKs may fail | Graceful fallback to STUBBED status |

### 9.2 Safety Measures

1. **Runtime mode switch** - Can revert to LEGACY instantly
2. **Backward compatibility** - Old behavior preserved
3. **Evidence requirement** - CI fails without opcode traces
4. **Gradual rollout** - Test with HelloWorld first

---

## 10. Success Criteria for EXP-031

### Must Achieve (Hard Requirements)

- [ ] DalvikEngine connected to execution path
- [ ] At least one APK executes REAL bytecode
- [ ] Opcode trace shows non-zero instruction count
- [ ] Lifecycle event has `source: "REAL_DALVIK_INTERPRETER"`
- [ ] Shortcut path explicitly labeled `HOST_SHORTCUT`
- [ ] CI blocks fake execution claims

### Should Achieve (Soft Requirements)

- [ ] 10+ APKs validated in REAL_DALVIK mode
- [ ] Comparison report generated (legacy vs real)
- [ ] VTable dispatch test passes
- [ ] Documentation complete

---

## 11. Artifacts Generated This Phase

| Artifact | Path | Purpose |
|----------|------|---------|
| Execution Map | `run/exp031/before_integration_map.json` | Machine-readable baseline |
| Baseline Doc | `docs/EXP031_BASELINE.md` | Human-readable analysis |
| This file | `docs/EXP031_BASELINE.md` | Reference document |

---

## 12. Next Phase (PHASE 1)

**Task:** Create Runtime Mode Switch

**Deliverables:**
- `ExecutionMode` enum (LEGACY, REAL_DALVIK)
- `--execution-mode=` CLI flag
- Config field for mode selection
- Conditional branching skeleton (don't remove old code yet)

---

*Baseline captured: 2026-08-14T00:30:00Z*  
*Ready for PHASE 1 integration work*
*Golden Debug Protocol: ACTIVE*
