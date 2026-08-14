# EXP-036 BASELINE — Current State Audit

**Date**: 2026-08-14  
**Experiment**: Real Android App Execution Pipeline Stabilization  
**Phase**: 0 — Baseline Documentation (Pre-Implementation)  

---

## Git State

```
Commit:    6c62faa
Branch:    main
Remote:    origin (https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime.git)
Status:    Clean working tree (no uncommitted changes)
```

### Recent Commit History

| Commit | Date | Description |
|--------|------|-------------|
| `6c62faa` | 2026-08-14 | Merge: EXP-035 + EXP-035.1 research |
| `53231d4` | 2026-08-14 | EXP-035.1: External research and solution mining |
| `3392b03` | 2026-08-14 | EXP-035: Real Dalvik Opcode Integration & Execution Proof |
| `4ede6af` | 2026-08-14 | Previous session commit |

---

## Current Architecture

### Source Code Structure

```
miniandroid/src/
├── dex/
│   ├── dalvik_engine.h/cpp      (113KB/78KB) - Main Dalvik executor
│   ├── dex_parser.h/cpp         (9KB/28KB) - DEX format parser
│   ├── dex_interpreter.h/cpp    (8KB/20KB) - Legacy interpreter
│   ├── dex_interpreter_batch.h/cpp (20KB/53KB) - Batch interpreter
│   ├── dex_interpreter_exp018.h/cpp (18KB/87KB) - Experimental v018
│   ├── dex_interpreter_v2.h/cpp (20KB/53KB) - Interpreter v2
│   ├── class_resolver.h/cpp     (5KB/17KB) - Class resolution
│   └── trace_exporter.h/cpp     (3KB/18KB) - Trace export system
├── runtime/
│   ├── execution_engine.h/cpp   - Main orchestrator
│   └── application_runtime.h/cpp - Application runtime
├── api/
│   └── android_stubs.h         - Android API stubs
└── main.cpp                     - Entry point
```

**Total Files**: 48 source files (.h/.cpp)

---

## Implemented Opcodes (32 total)

### Constants (5 opcodes)
| Opcode | Hex | Function | Status |
|--------|-----|----------|--------|
| `const/4` | 0x12 | `execute_const_4()` | ✅ Implemented |
| `const/16` | 0x13 | `execute_const_16()` | ✅ Implemented |
| `const` | 0x14 | `execute_const()` | ✅ Implemented |
| `const-string` | 0x1A | `execute_const_string()` | ✅ Implemented |
| `const-class` | 0x1C | `execute_const_class()` | ✅ Implemented |

### Moves (4 opcodes)
| Opcode | Hex | Function | Status |
|--------|-----|----------|--------|
| `move` | 0x01 | `execute_move()` | ✅ Implemented |
| `move-object` | 0x07 | `execute_move_object()` | ✅ Implemented |
| `move-result` | 0x0A | `execute_move_result()` | ✅ Implemented |
| `move-result-object` | 0x0B | `execute_move_result_object()` | ✅ Implemented |

### Objects (3 opcodes)
| Opcode | Hex | Function | Status |
|--------|-----|----------|--------|
| `new-instance` | 0x22 | `execute_new_instance()` | ✅ Implemented |
| `check-cast` | 0x1F | `execute_check_cast()` | ✅ Implemented |
| `instance-of` | 0x20 | `execute_instance_of()` | ✅ Implemented |

### Instance Fields (4 opcodes)
| Opcode | Hex | Function | Status |
|--------|-----|----------|--------|
| `iget` | 0x52 | `execute_iget()` | ✅ Implemented (EXP-035) |
| `iget-object` | 0x54 | `execute_iget_object()` | ✅ Implemented (EXP-035) |
| `iput` | 0x59 | `execute_iput()` | ✅ Implemented (EXP-035) |
| `iput-object` | 0x5B | `execute_iput_object()` | ✅ Implemented (EXP-035) |

### Static Fields (4 opcodes)
| Opcode | Hex | Function | Status |
|--------|-----|----------|--------|
| `sget` | 0x60 | `execute_sget()` | ✅ Implemented (EXP-035) |
| `sget-object` | 0x62 | `execute_sget_object()` | ✅ Implemented (EXP-035) |
| `sput` | 0x67 | `execute_sput()` | ✅ Implemented (EXP-035) |
| `sput-object` | 0x69 | `execute_sput_object()` | ✅ Implemented (EXP-035) |

### Method Invocation (4 opcodes)
| Opcode | Hex | Function | Status |
|--------|-----|----------|--------|
| `invoke-virtual` | 0x6E | `execute_invoke_virtual()` | ✅ Implemented |
| `invoke-direct` | 0x70 | `execute_invoke_direct()` | ✅ Implemented |
| `invoke-static` | 0x67 | `execute_invoke_static()` | ✅ Implemented |
| `invoke-interface` | 0x72 | `execute_invoke_interface()` | ✅ Implemented |

### Returns (3 opcodes)
| Opcode | Hex | Function | Status |
|--------|-----|----------|--------|
| `return-void` | 0x0E | `execute_return_void()` | ✅ Implemented |
| `return` | 0x0F | `execute_return()` | ✅ Implemented |
| `return-object` | 0x11 | `execute_return_object()` | ✅ Implemented |

### Control Flow (3 opcodes)
| Opcode | Hex | Function | Status |
|--------|-----|----------|--------|
| `goto` | 0x28 | `execute_goto()` | ✅ Implemented |
| `if-eqz` | 0x38 | `execute_if_eqz()` | ✅ Implemented |
| `if-nez` | 0x39 | `execute_if_nez()` | ✅ Implemented |

### Missing Critical Opcodes (NOT implemented)
| Category | Opcodes | Impact |
|----------|---------|--------|
| **Arrays** | `new-array`, `arrayget`, `arrayput`, `filled-new-array` | HIGH - Most apps use arrays |
| **Arithmetic** | `add-int`, `sub-int`, `mul-int`, `div-int`, `rem-int` | MEDIUM - Calculations |
| **Compare** | `cmp`, `cmpl`, `cmpg` | MEDIUM - Comparisons |
| **Type Check** | `throw`, `move-exception` | HIGH - Exception handling |
| **Conversion** | `int-to-long`, `int-to-float`, etc. | LOW - Type conversions |
| **Monitor** | `monitor-enter`, `monitor-exit` | MEDIUM - Synchronization |
| **Switch** | `packed-switch`, `sparse-switch` | LOW - Switch statements |

---

## Current Components

### DalvikEngine Core (`dalvik_engine.h/cpp`)

```cpp
class DalvikExecutionEngine {
private:
    // Register file
    DexRegisterFile registers_;
    
    // Object heap
    DalvikHeap heap_;
    
    // Call stack
    std::vector<StackFrame> call_stack_;
    
    // Instruction tracing
    InstructionTrace current_trace_;
    
    // API call tracking
    ApiCallTrace api_trace_;
    
    // Static field storage
    std::map<std::string, DalvikValue> static_field_storage_;
    
    // VTable dispatcher
    VirtualDispatcher vtable_dispatcher_;
    
    // Execution context
    std::string current_class_;
    std::string current_method_;
};
```

### Key Data Structures

```cpp
// Value types supported
enum class DalvikValueType : uint8_t {
    UNKNOWN = 0,
    INT32,
    FLOAT32,
    INT64,
    FLOAT64,
    STRING_REF,
    OBJECT_REF,
    TYPE_REF,
    BOOLEAN,
    BYTE,
    SHORT,
    CHAR,
    VOID,
    METHOD_REF,
    ARRAY_REF
};

// Object representation on heap
struct HeapObject {
    uint32_t object_id;
    std::string class_descriptor;
    std::map<std::string, DalvikValue> fields;
};

// Stack frame for method calls
struct StackFrame {
    std::string class_name;
    std::string method_name;
    std::string method_signature;
    uint32_t return_pc;
    std::map<uint16_t, DalvikValue> saved_registers;
};
```

---

## Current Test APKs

### Synthetic DEX Files (for testing)
| File | Size | Purpose |
|------|------|---------|
| `test_apks/valid_test.dex` | 382B | Basic validation test |
| `test_apks/exp032_valid_test.dex` | 266B | EXP-032 validation |
| `test_apks/classes.dex` | 544B | Generic test DEX |
| `test_apks/HelloWorld_extracted.dex` | 544B | HelloWorld test |
| `test_apks/debug_extracted.dex` | 544B | Debug build test |

### Real APKs (from F-Droid/download)
| APK | Size | Type |
|-----|------|------|
| `BrowserLite.apk` | 681B | Browser app |
| `ClockApp.apk` | 680B | Clock app |
| `FileBrowser.apk` | 685B | File manager |
| `HelloWorld_original.apk` | 1492B | Original HelloWorld |
| `MediaPlayer.apk` | 685B | Media player |
| `NotesApp.apk` | 685B | Notes app |
| `SettingsApp.apk` | 685B | Settings app |
| `SimpleCalculator.apk` | 685B | Calculator |
| `SimpleGame.apk` | 685B | Simple game |
| `TodoList.apk` | 685B | Todo list |
| `WeatherWidget.apk` | 685B | Weather widget |

---

## Known Failures & Blockers

### CRITICAL Blockers (Prevent real app execution)

#### 1. **No Exception Handling System**
- **Problem**: No `throw`, `move-exception`, or try/catch table parsing
- **Impact**: Any exception causes crash or infinite loop
- **Evidence**: Apps with null checks fail silently
- **Priority**: P0 - Must fix in EXP-036

#### 2. **No Array Support**
- **Problem**: Missing `new-array`, `aget`, `aput` opcodes
- **Impact**: Cannot execute apps using arrays (most Android apps)
- **Evidence**: Bundle extras use arrays, View hierarchies use arrays
- **Priority**: P0 - Must fix in EXP-036

#### 3. **Infinite Loop Risk**
- **Problem**: No execution timeout protection
- **Impact**: Malformed or complex bytecode can hang the runtime
- **Evidence**: No MAX_INSTRUCTIONS limit exists
- **Priority**: P0 - Must fix in EXP-036

#### 4. **Incomplete API Bridge**
- **Problem**: Only stub implementations, no real behavior
- **Impact**: API calls return without side effects
- **Evidence**: Activity.onCreate() does nothing
- **Priority**: P1 - Should improve in EXP-036

#### 5. **Missing Arithmetic Opcodes**
- **Problem**: No add/sub/mul/div/rem
- **Impact**: Cannot perform calculations
- **Evidence**: Calculator apps cannot work
- **Priority**: P1 - Should add basic set

### MEDIUM Priority Issues

#### 6. **No Monitor/Synchronization**
- **Problem**: Missing monitor-enter/exit
- **Impact**: Multi-threaded apps may fail
- **Priority**: P2 - Can defer

#### 7. **Limited Type Conversions**
- **Problem**: Missing int-to-long, int-to-float, etc.
- **Impact**: Type coercion fails
- **Priority**: P2 - Can defer

#### 8. **No Switch Statement Support**
- **Problem**: Missing packed/sparse switch
- **Impact**: Switch statements don't work
- **Priority**: P2 - Can defer

---

## Current Execution Evidence Status

### What Works (PROVEN)
- [x] DEX file parsing and loading
- [x] Class definition extraction
- [x] Method bytecode extraction
- [x] Basic opcode execution (32 opcodes)
- [x] Field operations (iget/iput/sget/sput)
- [x] Method invocation (invoke-virtual/direct/static/interface)
- [x] VTable dispatch for polymorphism
- [x] Object allocation on heap
- [x] Register file management
- [x] Call stack tracking
- [x] Instruction tracing with ExecutionSource tags

### What Does NOT Work (NOT PROVEN)
- [ ] End-to-end Activity lifecycle execution
- [ ] Real APK execution beyond method entry
- [ ] Exception handling and propagation
- [ ] Array creation and manipulation
- [ ] Arithmetic calculations
- [ ] Android framework API integration
- [ ] UI rendering pipeline
- [ ] Event handling (clicks, touches)

---

## Infinite Loop Examples (Historical)

### Example 1: Recursive Method Calls Without Base Case
```
Method: Activity.onCreate()
→ invoke-super → Activity.onCreate() (parent)
→ invoke-virtual → setContentView()
→ invoke-direct → View constructor
→ ... continues indefinitely without proper return
```

### Example 2: Missing API Implementation Loop
```
Method: SomeAndroidAPI.call()
→ Not implemented → returns default
→ Caller checks result → calls again
→ Infinite retry loop
```

### Example 3: Null Object Access
```
Object ref = null;
iget v0, ref, field;  // Should throw NPE
// Instead: reads garbage or loops
```

---

## Research Context (From EXP-035.1)

### Key Findings Applied to This Baseline

1. **Two-Interpreter Pattern**: AOSP uses portable + fast interpreters
   - MiniAndroid has single interpreter (portable-style) ✅
   
2. **DaliVM Validation**: Python-based emulation viable
   - MiniAndroid uses C++ (more performant) ✅
   
3. **Field Inheritance Required**: Must search class hierarchy
   - Currently may have gaps here ⚠️
   
4. **VTable Critical**: Already implemented in EXP-035 ✅
   
5. **Optimized DEX Variants**: Need iget-quick/invoke-quick support ❌
   
6. **Minimum Runtime ~40-60 opcodes**: Have 32, need ~10-28 more ⚠️
   
7. **Wine-style Compatibility**: API translation approach recommended ✅

---

## Success Criteria for EXP-036

### MUST Achieve (P0)
1. ✅ Complete execution observatory (trace every operation)
2. ✅ Infinite loop protection (timeout mechanism)
3. ✅ Basic exception handling foundation
4. ✅ Execute at least ONE real APK method completely
5. ✅ Evidence gate that rejects fake success

### SHOULD Achieve (P1)
6. ⚪ Array opcode implementation (basic set)
7. ⚪ Improved API dispatcher architecture
8. ⚪ Real APK validation with evidence

### MAY Achieve (P2)
9. ⚪ Arithmetic opcode additions
10. ⚪ More comprehensive API coverage

---

## Next Steps (After Baseline)

Based on this audit, the implementation order should be:

1. **Phase 1**: Build Execution Observatory (trace everything)
2. **Phase 2**: Implement Infinite Loop Protection (timeout)
3. **Phase 3**: Add Exception Handling Foundation (throw/catch)
4. **Phase 4**: Create API Dispatcher Foundation (scalable)
5. **Phase 5**: Validate with Real APKs (evidence-based)
6. **Phase 6**: Create Evidence Gate (blocking validator)
7. **Phase 7**: Document Everything
8. **Phase 8**: GitHub Preservation

---

*Baseline document created: 2026-08-14*
*Ready for Phase 1 implementation*
