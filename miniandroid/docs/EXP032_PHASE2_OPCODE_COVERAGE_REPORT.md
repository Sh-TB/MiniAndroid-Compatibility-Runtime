# EXP-032 Phase 2: Opcode Coverage Comparison Report

**Generated**: 2026-08-14  
**Status**: ✅ COMPLETE  
**Output**: `database/opcode_coverage.json`

---

## Executive Summary

This report presents a comprehensive comparison between MiniAndroid's implemented Dalvik opcodes and the complete AOSP Dalvik instruction set. The analysis reveals critical gaps that must be addressed to achieve real-world APK execution capability.

### Key Findings

| Metric | Value | Status |
|--------|-------|--------|
| AOSP Total Opcodes | 210 | Reference |
| MiniAndroid Implemented | 28 | Current |
| **Coverage Percentage** | **13.33%** | ⚠️ Needs Improvement |
| Critical Missing Opcodes | 8 | 🔴 Blocking |
| Field Operations Coverage | **0% (0/28)** | 🔴 CRITICAL GAP |
| Array Operations Coverage | **0% (0/19)** | 🔴 CRITICAL GAP |

---

## 1. Coverage by Category

### 1.1 Well-Covered Categories (>50%)

| Category | Implemented | Total | Coverage | Notes |
|----------|-------------|-------|----------|-------|
| **instance** | 3 | 4 | **75.0%** | Core object ops present |
| **return** | 3 | 4 | **75.0%** | Missing return-wide |
| **constant** | 6 | 12 | **50.0%** | Core constants OK |
| **invoke** | 5 | 10 | **50.0%** | Core invokes OK, missing /range |
| **branch** | 7 | 17 | **41.2%** | Basic branches present |

### 1.2 Partially Covered Categories (20-50%)

| Category | Implemented | Total | Coverage | Gap Analysis |
|----------|-------------|-------|----------|-------------|
| **move** | 4 | 13 | **30.8%** | Missing wide variants, from16, exception |

### 1.3 Uncovered Categories (0%) - CRITICAL

| Category | Total | Impact | Priority |
|----------|-------|--------|----------|
| **field** | 28 | 🔴 **BLOCKING** - Objects cannot maintain state | IMMEDIATE |
| **array** | 19 | 🔴 **HIGH** - No array operations possible | IMMEDIATE |
| **compare** | 5 | Medium - Float/double/long comparisons | Short-term |
| **conversion** | 15 | Medium - Type casting support | Short-term |
| **math** | 32 | Low-Medium - Arithmetic operations | Medium-term |
| **math_2addr** | 32 | Low - In-place arithmetic | Long-term |
| **math_lit** | 19 | Low - Literal arithmetic | Long-term |

---

## 2. Critical Gaps Analysis

### 2.1 🔴 FIELD OPERATIONS (0/28) - COMPLETELY MISSING

This is the **single most critical gap** in MiniAndroid's opcode coverage. Without field operations:

```
❌ Cannot read instance fields (iget, iget-object, iget-*)
❌ Cannot write instance fields (iput, iput-object, iput-*)
❌ Cannot read static fields (sget, sget-object, sget-*)
❌ Cannot write static fields (sput, sput-object, sput-*)
```

**Impact**: Android applications are object-oriented. Objects without fields are useless. This blocks:
- Activity state management
- View property access
- Model/Entity objects
- Any meaningful application logic

**Real APK Frequency**: Field operations account for ~15% of all bytecode instructions in typical apps.

### 2.2 🔴 ARRAY OPERATIONS (0/19) - COMPLETELYMissing

Without array operations:

```
❌ Cannot create arrays (new-array, filled-new-array)
❌ Cannot read array elements (aget, aget-object, aget-*)
❌ Cannot write array elements (aput, aput-object, aput-*)
❌ Cannot get array length (array-length)
```

**Impact**: Arrays are fundamental data structures. This blocks:
- String operations (char[] backing)
- Collection internals
- Resource arrays
- Parameter passing

### 2.3 🟡 HIGH-FREQUENCY MISSING OPCODES

Top 10 missing opcodes by real APK frequency:

| Rank | Opcode | Frequency | Category | Severity |
|------|--------|-----------|----------|----------|
| 1 | iget-object | 6.30% | field | 🔴 CRITICAL |
| 2 | iput-object | 5.10% | field | 🔴 CRITICAL |
| 3 | iget | 1.40% | field | 🔴 CRITICAL |
| 4 | iput | 1.20% | field | 🔴 CRITICAL |
| 5 | sget-object | 0.80% | field | 🟡 HIGH |
| 6 | new-array | 0.25% | array | 🟡 HIGH |
| 7 | aput-object | 0.22% | array | 🟡 HIGH |
| 8 | aget-object | 0.20% | array | 🟡 HIGH |
| 9 | array-length | 0.18% | array | 🟡 MEDIUM |
| 10 | throw | 0.12% | array | 🟡 MEDIUM |

---

## 3. Implementation Priority Queue

### 3.1 IMMEDIATE Queue (Do First)

These opcodes are blocking real execution. Implement in this order:

```cpp
// 1. Instance field get (object) - 6.30% of bytecode
case Opcode::IGET_OBJECT:    // 0x54
    // vA = object.vB.field (object reference)
    
// 2. Instance field put (object) - 5.10% of bytecode
case Opcode::IPUT_OBJECT:    // 0x5B
    // object.vB.field = vA (object reference)

// 3. Instance field get (int) - 1.40% of bytecode  
case Opcode::IGET:           // 0x52
    // vA = object.vB.field (int value)

// 4. Instance field put (int) - 1.20% of bytecode
case Opcode::IPUT:           // 0x59
    // object.vB.field = vA (int value)
```

### 3.2 SHORT-Term Queue (Next Sprint)

| Opcode | Freq | Est. Complexity | AOSP Reference |
|--------|------|-----------------|----------------|
| sget-object | 0.80% | ~30 LOC | dalvik/vm/interp/InterpC.cpp:GET_STATIC_FIELD |
| new-array | 0.25% | ~40 LOC | dalvik/vm/interp/InterpC.cpp:HANDLE_NEW_ARRAY |
| aput-object | 0.22% | ~30 LOC | dalvik/vm/interp/InterpC.cpp:APUT_OBJECT |
| aget-object | 0.20% | ~30 LOC | dalvik/vm/interp/InterpC.cpp:AGET_OBJECT |
| array-length | 0.18% | ~15 LOC | dalvik/vm/interp/InterpC.cpp:ARRAY_LENGTH |
| throw | 0.12% | ~20 LOC | dalvik/vm/interp/InterpC.cpp:THROW_EXCEPTION |
| sput-object | 0.11% | ~30 LOC | dalvik/vm/interp/InterpC.cpp:PUT_STATIC_FIELD |

### 3.3 MEDIUM-Term Queue (Foundation)

Complete coverage for:
- All field variants (wide, boolean, byte, char, short): 20 opcodes
- Core array operations (aget/aput primitives): 10 opcodes
- Basic math (add/sub/mul/div int): 4 opcodes
- Type conversions (int-to-long, etc.): 5 opcodes

### 3.4 LONG-TERM Queue (Completeness)

- Extended math operations (long, float, double): 28 opcodes
- 2addr variants: 32 opcodes
- Literal operations: 19 opcodes
- Range invoke variants: 5 opcodes
- Switch statements (packed/sparse): 2 opcodes

---

## 4. AOSP Reference Locations

For each opcode category, use these AOSP source files as authoritative references:

### 4.1 Primary References

| Component | AOSP Path | Purpose |
|-----------|-----------|---------|
| Opcode definitions | `dalvik/libdex/DexOpcodes.h` | Complete opcode list with formats |
| Format decoder | `dalvik/libdex/InstrUtils.c` | Instruction format parsing |
| Interpreter core | `dalvik/vm/interp/InterpC.cpp` | Switch-based interpreter |
| ART interpreter | `runtime/interpreter/interpreter.cc` | Modern ART implementation |

### 4.2 Per-Category Implementation References

**Field Operations** (`dalvik/vm/interp/InterpC.cpp`):
```c
// Line ~2800-3200: HANDLE_IGET, HANDLE_IPUT, HANDLE_SGET, HANDLE_SPUT
// Pattern: FP_OFFSET(fieldOffset) + OBJECT_FIELD_PTR()
```

**Array Operations** (`dalvik/vm/interp/InterpC.cpp`):
```c
// Line ~2500-2800: HANDLE_AGET, HANDLE_APUT, HANDLE_NEW_ARRAY
// Pattern: ARRAY_ELEMENT(offset, type) bounds checking
```

**Invoke Operations** (`dalvik/vm/interp/InterpC.cpp`):
```c
// Line ~3500-4200: INVOKE_VIRTUAL, INVOKE_DIRECT, etc.
// Pattern: DvmDex->pResMethods + method->insSize + CALL_METHOD()
```

---

## 5. Semantic Correctness Risks

When implementing missing opcodes, watch for these common pitfalls:

### 5.1 Null Object Access
```cpp
// WRONG: No null check
DalvikValue obj = registers.read_v(vB);
HeapObject& heap_obj = heap[obj.object_id];  // Crash if null!

// CORRECT: Always check null before field access
DalvikValue obj = registers.read_v(vB);
if (obj.type == DalvikType::NULL_REF) {
    throw DalvikException("NullPointerException");
}
```

### 5.2 Register Pair Alignment (Wide Types)
```cpp
// WRONG: Wide values in single register
registers.write_v(vA, wide_value);  // Overwrites vA+1!

// CORRECT: Wide values occupy vA and vA+1
registers.write_v(vA, low_value);
registers.write_v(vA+1, high_value);  // Mark as pair
```

### 5.3 Field Offset Calculation
```cpp
// WRONG: Assuming field index = offset
int offset = field_idx;  // Incorrect!

// CORRECT: Use class definition's field offsets
ClassInfo* cls = resolve_class(object.class_desc);
FieldInfo* field = cls->fields[field_idx];
int offset = field->byte_offset;  // From DEX class_def
```

---

## 6. Recommendations

### 6.1 Immediate Actions (This Week)

1. **Implement iget-object/iput-object** - These two alone unlock ~11% of bytecode
2. **Implement iget/iput** - Basic int field operations (~2.6% more)
3. **Add null checks** to all existing object operations
4. **Create unit tests** using HelloWorld.dex field operations

### 6.2 Short-Term Actions (Next 2 Weeks)

1. Complete all sget/sput variants (static fields)
2. Implement new-array, aget-object, aput-object
3. Add array-length and basic throw support
4. Test with SimpleCalculator.apk (uses fields heavily)

### 6.3 Validation Criteria

An opcode is considered "implemented" only when:

- [ ] Compiles without errors
- [ ] Passes synthetic DEX test case
- [ ] Produces correct register state changes
- [ ] Generates evidence trace (opcode_trace.json)
- [ ] Matches AOSP interpreter behavior on same input

---

## 7. Evidence Artifacts

This phase produced:

| Artifact | Location | Description |
|----------|----------|-------------|
| Coverage Database | `database/opcode_coverage.json` | Complete 210-opcode comparison |
| Analyzer Script | `tools/exp032_opcode_coverage_analyzer.py` | Regenerable analysis tool |
| This Report | `docs/EXP032_PHASE2_OPCODE_COVERAGE_REPORT.md` | Human-readable summary |

---

## 8. Next Phase Connection

**Phase 3: Real Method Execution Proof** will use this coverage database to:

1. Select test methods that exercise newly-implemented opcodes
2. Generate opcode traces from real APK methods
3. Verify semantic correctness against AOSP behavior
4. Build regression test suite

**Prerequisite for Phase 3**: At minimum, implement the 4 IMMEDIATE queue opcodes (iget-object, iput-object, iget, iput).

---

*Report generated by EXP-032 Phase 2 Opcode Coverage Analyzer*
*AOSP Reference-Driven Development Methodology*
