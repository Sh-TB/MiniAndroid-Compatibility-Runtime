# EXP-036 REPORT — Real Android App Execution Pipeline Stabilization

**Date**: 2026-08-14  
**Experiment**: Execution Pipeline Stabilization  
**Status**: INFRASTRUCTURE COMPLETE, INTEGRATION PENDING  

---

## Executive Summary

EXP-036 created critical infrastructure components for reliable Android app execution:

1. **Execution Observatory** — Complete trace system for every operation
2. **Execution Guard** — Timeout and infinite loop protection
3. **Exception System** — Foundation for Dalvik exception handling
4. **API Dispatcher** — Scalable Android API call architecture
5. **Evidence Gate** — Blocking validator that rejects fake success

### Current Status

| Component | Status | Files |
|-----------|--------|-------|
| Execution Observatory | ✅ Complete | `execution_observatory.h/cpp` |
| Execution Guard | ✅ Complete | `execution_guard.h/cpp` |
| Exception System | ✅ Complete | `exception_system.h/cpp` |
| API Dispatcher | ✅ Complete | `api_dispatcher.h/cpp` |
| Evidence Gate Validator | ✅ Complete | `exp036_execution_validator.py` |
| Baseline Documentation | ✅ Complete | `EXP036_BASELINE.md` |

### Evidence Gate Verdict: REJECTED (Expected)

```
Total Tested: 6
Passed:       0
Failed:       6
Real Evidence: ❌ NO
Host Shortcut: ⚠️ YES (in previous runs)
```

**This is CORRECT behavior** — the gate should reject until real execution is integrated.

---

## Components Created

### 1. Execution Observatory (`execution_observatory.h/cpp`)

**Purpose**: Complete execution trace system

**Key Features**:
- Method entry/exit tracking with full register state
- Instruction-level tracing with before/after state
- Exception event recording
- API call logging with resolution status
- Timeout event capture
- JSON and human-readable report generation

**Data Structures**:
```cpp
struct InstructionRecord {
    uint32_t pc;
    uint16_t opcode;
    std::string opcode_name;
    std::vector<RegisterState> registers_before;
    std::vector<RegisterState> registers_after;
    ExecutionSource source;  // REAL_DALVIK_INTERPRETER or HOST_SHORTCUT
};

struct MethodExecutionRecord {
    std::string class_descriptor;
    std::string method_name;
    size_t total_instructions_executed;
    bool is_successful();  // Checks source + instructions > 0 + no exceptions
};
```

**Usage**:
```cpp
Observatory::ExecutionObservatory obs("session_123");
obs.start_session("app.apk");

size_t method_handle = obs.record_method_enter(
    "com.example.MainActivity", "onCreate", "()V", 
    pc, args, depth
);

// ... execute instructions ...
obs.record_instruction(method_handle, pc, opcode, name, 
                       regs_before, regs_after, success, error,
                       ExecutionSource::REAL_DALVIK_INTERPRETER);

obs.record_method_exit(method_handle, exit_pc, return_val, true);
obs.end_session();
obs.save_to_directory("run/exp036/traces");
```

---

### 2. Execution Guard (`execution_guard.h/cpp`)

**Purpose**: Prevent infinite loops and resource exhaustion

**Limits Configured**:
```cpp
struct ExecutionLimits {
    size_t max_instructions_per_method = 100000;  // 100K per method
    size_t max_total_instructions = 1000000;      // 1M total
    size_t max_call_depth = 256;                 // Recursion limit
    size_t max_methods = 10000;                   // Total methods
};
```

**Features**:
- Per-method instruction counting
- Total session instruction limiting
- Call depth tracking (prevents stack overflow)
- Method count limiting
- Detailed violation diagnostics
- Integration with observatory for timeout events

**Usage**:
```cpp
Guard::ExecutionGuard guard(limits, &observatory);

guard.enter_method("Activity", "onCreate", "()V");

while (executing) {
    if (!guard.check_instruction(pc, opcode, opcode_name)) {
        // Handle timeout - get diagnostic report
        std::cout << guard.get_last_violation_report();
        break;
    }
    // Execute instruction...
}

guard.exit_method();
```

---

### 3. Exception System (`exception_system.h/cpp`)

**Purpose**: Dalvik/Java-style exception handling foundation

**Exception Types Supported**:
```cpp
enum class DalvikExceptionType {
    NULL_POINTER,
    ARRAY_INDEX_OUT_OF_BOUNDS,
    ARITHMETIC,           // divide by zero
    CLASS_CAST,
    NEGATIVE_ARRAY_SIZE,
    ILLEGAL_ARGUMENT,
    ILLEGAL_STATE,
    NO_SUCH_METHOD,
    NO_SUCH_FIELD,
    ABSTRACT_METHOD,
    UNSUPPORTED_OPERATION,
    RUNTIME,
    VIRTUAL_MACHINE_ERROR,
    CUSTOM
};
```

**Try/Catch Table Support**:
```cpp
struct TryCatchEntry {
    uint32_t try_start_pc;
    uint32_t try_end_pc;
    uint32_t handler_pc;
    std::string exception_type;
    
    bool covers_pc(uint32_t pc) const;
    bool can_catch(const std::string& exc_type) const;
};
```

**Exception Manager State Machine**:
```
NO_EXCEPTION → THROWN → BEING_HANDLED → HANDLED
                              ↓
                          UNHANDLED (propagates up)
```

**Factory Functions**:
```cpp
auto exc = Exceptions::Factory::null_pointer(msg, cls, method, pc);
auto exc = Exceptions::Factory::array_index_oob(msg, index, size);
auto exc = Exceptions::Factory::arithmetic_div_zero();
auto exc = Exceptions::Factory::class_cast(from, to);
```

---

### 4. API Dispatcher (`api_dispatcher.h/cpp`)

**Purpose**: Scalable Android API call handling architecture

**Architecture**:
```
Dalvik invoke → ApiDispatcher.dispatch()
                    ↓
              Resolver Chain (priority ordered)
                    ↓
              [ActivityResolver] → handles Activity.* calls
              [ViewResolver]     → handles View.* calls
              [TextViewResolver] → handles TextView.* calls
              [LogResolver]      → handles Log.* calls
              [ObjectResolver]   → handles Object.* calls
              [StringResolver]   → handles String.* calls
              [ClassResolver]    → handles Class.* calls
              [BundleResolver]   → handles Bundle.* calls
                    ↓
              Default Stub (if no resolver matches)
```

**Built-in Resolvers**:

| Resolver | Priority | APIs Handled | Evidence Produced |
|----------|----------|--------------|------------------|
| ActivityResolver | 90 | onCreate, onStart, onResume, setContentView | ✅ LIFECYCLE EVIDENCE |
| TextViewResolver | 70 | setText, getText | ✅ UI EVIDENCE |
| LogResolver | 95 | v, d, i, w, e, println | ✅ LOG OUTPUT |
| ViewResolver | 80 | <init>, setId, getId, setOnClickListener | UI tracking |
| BundleResolver | 85 | getInt, getString, putInt, putString | Data tracking |

**API Result Types**:
```cpp
ApiResult::ok(value)           // Found and executed successfully
ApiResult::fail(error)         // Found but threw exception
ApiResult::stub(note)          // Missing - returns default
ApiResult::missing_critical(reason) // Missing - causes failure
```

**Coverage Tracking**:
```cpp
dispatcher.generate_coverage_report()
// Returns:
// - Total API calls
// - Success/fail/stub counts
// - Critical missing APIs list
// - Coverage percentage
```

---

### 5. Evidence Gate Validator (`exp036_execution_validator.py`)

**Purpose**: MANDATORY validator that rejects fake success

**Required Checks (ALL must pass)**:
1. ✅ APK file exists
2. ✅ DEX extracted/parsed
3. ✅ Bytecode available
4. ✅ Interpreter executed
5. ✅ **REAL_DALVIK_INTERPRETER source tag present**
6. ✅ No HOST_SHORTCUT detected
7. ✅ No timeout occurred
8. ✅ Evidence files created
9. ✅ Trace non-empty (instructions > 0)

**Verdict Logic**:
```python
if all_checks_pass and has_real_evidence and no_host_shortcut:
    verdict = "ACCEPTED"
else:
    verdict = "REJECTED"  # No fake success allowed!
```

**Output**:
- `validation_report.json` — Machine-readable results
- Console output — Human-readable summary
- Exit code 0 = PASS, 1 = FAIL

---

## Current Blockers (Why Evidence Gate Rejects)

### Blocker 1: New Components Not Integrated
**Problem**: Observatory, Guard, Exception System, Dispatcher are created but not wired into `dalvik_engine.cpp`
**Solution**: Integrate into main execution loop in next phase

### Blocker 2: No Real Execution Since Last Session
**Problem**: Previous execution traces show HOST_SHORTCUT or zero instructions
**Solution**: Run MiniAndroid with new integrated components

### Blocker 3: Missing Opcodes Prevent Full Execution
**Problem**: Arrays, arithmetic, type conversions not implemented
**Impact**: Most real apps need these opcodes
**Priority**: Add minimum viable set for simple Activity

---

## Architecture Diagram (After EXP-036)

```
┌─────────────────────────────────────────────────────────────┐
│                      MAIN.CPP                               │
│                   Entry Point / CLI                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│               EXECUTION_ENGINE.CPP                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ APK Parser  │→│ DEX Parser  │→│ Runtime Orchestrator │ │
│  └─────────────┘  └─────────────┘  └──────────┬──────────┘ │
└─────────────────────────────────────────────────────────────┘
                                                           │
┌─────────────────────────────────────────────────────────────▼┐
│                  DALVIK_ENGINE.CPP (EXP-036 Enhanced)        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              ExecutionObservatory                     │   │
│  │  • Method enter/exit tracking                        │   │
│  │  • Instruction-level tracing                         │   │
│  │  • Exception events                                  │   │
│  │  • API call logging                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                ExecutionGuard                          │   │
│  │  • MAX_INSTRUCTIONS_PER_METHOD = 100,000             │   │
│  │  • MAX_CALL_DEPTH = 256                              │   │
│  │  • Timeout detection & reporting                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              ExceptionManager                         │   │
│  │  • throw/catch state machine                         │   │
│  │  • Try/catch table parsing                          │   │
│  │  • Stack trace generation                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               ApiDispatcher                           │   │
│  │  • Activity lifecycle (onCreate, etc.)             │   │
│  │  • View operations                                 │   │
│  │  • Log output                                      │   │
│  │  • Object/String/Class core                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Opcode Switch Statement                   │   │
│  │  • 32+ opcodes already implemented                  │   │
│  │  • Each opcode produces trace record               │   │
│  │  • Source tagged as REAL_DALVIK_INTERPRETER         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Test Results (Evidence Gate Output)

### Validation Report Summary
```
Session: exp036_*
APKs Tested: 6
Passed: 0
Failed: 6
Pass Rate: 0.0%

Verdict: REJECTED (CORRECT - no real execution yet)
```

### Individual APK Results
All 6 test DEX/APK files failed validation because:
- No REAL_DALVIK_INTERPRETER source tags found
- Zero instructions executed in this session
- Previous sessions showed HOST_SHORTCUT patterns

**This is EXPECTED behavior** — the infrastructure is ready but not yet integrated.

---

## Files Created/Modified

### New Files (EXP-036)
| File | Size | Purpose |
|------|------|---------|
| `src/dex/execution_observatory.h` | ~15KB | Trace system header |
| `src/dex/execution_observatory.cpp` | ~20KB | Trace system implementation |
| `src/dex/execution_guard.h` | ~10KB | Timeout protection header |
| `src/dex/execution_guard.cpp` | ~12KB | Timeout protection implementation |
| `src/dex/exception_system.h` | ~15KB | Exception handling header |
| `src/dex/exception_system.cpp` | ~10KB | Exception handling implementation |
| `src/dex/api_dispatcher.h` | ~18KB | API dispatcher header |
| `src/dex/api_dispatcher.cpp` | ~25KB | API dispatcher implementation |
| `tools/exp036_execution_validator.py` | ~20KB | Evidence gate validator |
| `docs/exp036/EXP036_BASELINE.md` | ~12KB | Current state audit |

### Generated Files
| File | Purpose |
|------|---------|
| `run/exp036/validation_report.json` | Machine-readable validation results |

---

## Recommendations for Next Phase

### Immediate (Required for Evidence Gate PASS)

1. **Integrate Observatory into dalvik_engine.cpp**
   - Add `ExecutionObservatory` member to `DalvikExecutionEngine`
   - Call `record_method_enter()` at method start
   - Call `record_instruction()` for each opcode
   - Call `record_method_exit()` at method end
   - Tag all executions as `REAL_DALVIK_INTERPRETER`

2. **Integrate ExecutionGuard**
   - Add check before each instruction
   - Handle timeout gracefully with diagnostic output

3. **Integrate ExceptionManager**
   - Wrap opcode execution in try/catch
   - Implement basic `throw` opcode
   - Parse try/catch tables from DEX

4. **Integrate ApiDispatcher**
   - Route `invoke-*` through dispatcher
   - Generate lifecycle evidence for Activity.onCreate()

### Short-term (Improved Coverage)

5. **Add array opcodes** (`new-array`, `aget`, `aput`)
6. **Add basic arithmetic** (`add-int`, `sub-int`)
7. **Test with real APK that has simple Activity**

---

## Success Criteria Checklist

### For This Phase (INFRASTRUCTURE)
- [x] Execution Observatory designed and implemented
- [x] Execution Guard with timeout protection
- [x] Exception System foundation
- [x] API Dispatcher with resolvers
- [x] Evidence Gate validator created
- [x] Baseline documented
- [x] All components compile-ready
- [ ] Integrated into dalvik_engine (NEXT PHASE)
- [ ] Real execution evidence generated (NEXT PHASE)

### For Full Pass (After Integration)
- [ ] Evidence Gate returns ACCEPTED
- [ ] At least one APK shows REAL_DALVIK_INTERPRETER
- [ ] Instructions executed > 0
- [ ] Activity lifecycle reached (onCreate called)
- [ ] No HOST_SHORTCUT detected
- [ ] No timeouts in valid execution

---

*End of EXP-036 Report*
*Infrastructure complete, integration pending*
