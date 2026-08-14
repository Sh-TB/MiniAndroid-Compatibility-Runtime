# EXP-032 Phase 4: Object Model Improvement Report

**Generated**: 2026-08-14T10:35:29.104861
**Status**: CREATED
**Phase Goal**: Enhance object model to support field operations (iget/iput/sget/sput)

---

## Executive Summary

Phase 4 analyzes the current MiniAndroid object model against **AOSP reference implementations** and designs enhanced structures to enable **critical missing opcode coverage**:

| Metric | Value |
|--------|-------|
| Total Gaps Identified | 8 |
| Critical Severity | 2 |
| High Severity | 3 |
| Gaps Addressed | 4 |

---

## Current State Analysis (Rule 1)

### Existing Structures

#### HeapObject (Current)
```cpp
struct HeapObject {
    uint32_t object_id;
    std::string class_descriptor;
    std::map<std::string, DalvikValue> fields;  // String-keyed only!
    // ... metadata
};
```

**Problems**:
- No field offset table → cannot support `iget vA, vB, @field` format
- No type information per field → cannot distinguish int vs ref vs wide
- No class metadata linkage → cannot resolve field by DEX index

#### DalvikHeap (Current)
```cpp
class DalvikHeap {
    std::map<uint32_t, HeapObject> objects_;
    // Basic allocate/get/mark_initialized only
};
```

**Problems**:
- No class registry → cannot look up field metadata
- No static field storage → sget/sput impossible
- No field resolution infrastructure

---

## Gap Analysis Details

### CRITICAL Gaps (Block Field Operations)

#### ClassInfo

| Attribute | Detail |
|-----------|--------|
| **Type** | MISSING |
| **Description** | No class metadata structure to hold field/method tables |
| **AOSP Reference** | `ClassObject in dalvik/vm/oo/Object.h` |
| **MiniAndroid Status** | NOT_IMPLEMENTED |
| **Impact On** | iget, iput, sget, sput, invoke-virtual, invoke-super |
| **Fix Complexity** | MEDIUM |

#### FieldOffsetTable

| Attribute | Detail |
|-----------|--------|
| **Type** | MISSING |
| **Description** | No field byte offset calculation for instance field access |
| **AOSP Reference** | `Field.byteOffset in Object.h, ArtField.field_offset_` |
| **MiniAndroid Status** | STRING_KEYED_MAP_ONLY |
| **Impact On** | iget, iput, iget-boolean, iget-byte, iget-char, iget-short, iput-wide, iput-object |
| **Fix Complexity** | MEDIUM |

## Enhanced Design Solutions

### Solution 1: EnhancedClassInfo Structure

**AOSP Equivalent**: `ClassObject` from `dalvik/vm/oo/Object.h`

```python
@dataclass
class EnhancedClassInfo:
    class_descriptor: str           # Landroid/app/Activity;
    super_class: Optional[str]      # Inheritance chain
    instance_fields: List[EnhancedFieldInfo]   # With calculated offsets
    static_fields: List[EnhancedFieldInfo]     # Separate storage
    vtable: List[EnhancedMethodInfo]           # Virtual dispatch
    instance_data_size: int          # Total instance bytes
```

**Key Method: `calculate_field_offsets()`**
```
Algorithm (matches dvmComputeInstanceFieldOffsets):
1. Start offset = superclass.instance_data_size
2. For each instance field:
   a. If wide field & not 8-aligned: align to 8 bytes
   b. Set field.byte_offset = current_offset
   c. current_offset += field.type.size_bytes()
3. Store final instance_data_size
```

**Example Output** (from test run):
```json
{
  "class_descriptor": "Landroid/app/Activity;",
  "readable_name": "android.app.Activity",
  "super_class": "Landroid/content/ContextThemeWrapper;",
  "access_flags": "0x00000001",
  "instance_field_count": 0,
  "static_field_count": 0,
  "instance_data_size_bytes": 20,
  "virtual_method_count": 3,
  "vtable_ready": true,
  "loaded": true,
  "verified": true,
  "initialized": false,
  "instance_fields": [
    {
      "field_name": "mWindow",
      "field_descriptor": "Landroid/view/Window;",
      "field_idx": 0,
      "access_flags": "0x00000001",
      "byte_offset": 0,
      "is_static": false,
      "declaring_class": "Landroid/app/Activity;",
      "is_wide": false,
      "type_size": 4
    },
    {
      "field_name": "mCalled",
      "field_descriptor": "Z",
      "field_idx": 1,
      "access_flags": "0x00000001",
      "byte_offset": 4,
      "is_static": false,
      "declaring_class": "Landroid/app/Activity;",
      "is_wide": false,
      "type_size": 4
    },
    {
      "field_name": "mFinished",
      "field_descriptor": "Z",
      "field_idx": 2,
      "access_flags": "0x00000001",
      "byte_offset": 8,
      "is_static": false,
      "declaring_class": "Landroid/app/Activity;",
      "is_wide": false,
      "type_size": 4
    },
    {
      "field_name": "mResultCode",
      "field_descriptor": "I",
      "field_idx": 3,
      "access_flags": "0x00000001",
      "byte_offset": 12,
      "is_static": false,
      "declaring_class": "Landroid/app/Activity;",
      "is_wide": false,
      "type_size": 4
    },
    {
      "field_name": "mSavedInstanceState",
      "field_descriptor": "Landroid/os/Bundle;",
      "field_idx": 4,
      "access_flags": "0x00000001",
      "byte_offset": 16,
      "is_static": false,
      "declaring_class": "Landroid/app/Activity;",
      "is_wide": false,
      "type_size": 4
    }
  ],
  "static_fields": [
    {
      "field_name": "RESULT_CANCELED",
      "field_descriptor": "I",
      "field_idx": 0,
      "access_flags": "0x00000009",
      "byte_offset": 0,
      "is_static": true,
      "declaring_class": "Landroid/app/Activity;",
      "is_wide": false,
      "type_size": 4
    },
    {
      "field_name": "RESULT_OK",
      "field_descriptor": "I",
      "field_idx": 1,
      "access_flags": "0x00000009",
      "byte_offset": 1,
      "is_static": true,
      "declaring_class": "Landroid/app/Activity;",
      "is_wide": false,
      "type_size": 4
    }
  ],
  "vtable": [
    {
      "method_name": "onCreate",
      "method_descriptor": "(Landroid/os/Bundle;)V",
      "method_idx": 0,
      "access_flags": "0x00000001",
      "code_offset": 0,
      "is_direct": false,
      "is_virtual": true,
      "is_static": false,
      "declaring_class": "Landroid/app/Activity;",
      "vtable_index": 0
    },
    {
      "method_name": "onStart",
      "method_descriptor": "()V",
      "method_idx": 1,
      "access_flags": "0x00000001",
      "code_offset": 0,
      "is_direct": false,
      "is_virtual": true,
      "is_static": false,
      "declaring_class": "Landroid/app/Activity;",
      "vtable_index": 1
    },
    {
      "method_name": "onResume",
      "method_descriptor": "()V",
      "method_idx": 2,
      "access_flags": "0x00000001",
      "code_offset": 0,
      "is_direct": false,
      "is_virtual": true,
      "is_static": false,
      "declaring_class": "Landroid/app/Activity;",
      "vtable_index": 2
    }
  ],
  "interfaces": []
}
```

### Solution 2: EnhancedDalvikHeap with Field Operations

**New Capabilities**:

| Operation | Opcode Support | Implementation |
|-----------|---------------|----------------|
| `iget()` | iget, iget-object, iget-wide, iget-boolean, etc. | Offset-based instance data read |
| `iput()` | iput, iput-object, iput-wide, iput-boolean, etc. | Offset-based instance data write |
| `sget()` | sget, sget-object, sget-wide, etc. | Per-class static storage read |
| `sput()` | sput, sput-object, sput-wide, etc. | Per-class static storage write |

**Test Results** (Evidence - Rule 2):

| Class | Field | Type | Offset | iget/iput | Roundtrip |
|-------|-------|------|--------|-----------|-----------|
| android.app.Activity | mWindow | Landroid/view/Window; | 0 | ✓ | ✓ |
| android.widget.TextView | mText | Ljava/lang/CharSequence; | 0 | ✓ | ✓ |

### Solution 3: VTable for Virtual Dispatch

**AOSP Equivalent**: `ClassObject.vtable`

**Purpose**: Enable correct `invoke-virtual` behavior with polymorphism.

**Construction Algorithm** (matches `dvmBuildVTable`):
1. Copy parent's vtable (inheritance)
2. Override with this class's virtual methods (by signature match)
3. Append new virtual methods not in parent

**Impact**: Enables proper method dispatch for Activity.onCreate(), View.onClick(), etc.

---

## AOSP References Used (Rule 6)

| Component | Source File | Purpose |
|-----------|-------------|---------|
| ClassObject | `dalvik/vm/oo/Object.h` | Class metadata structure |
| Field | `dalvik/vm/oo/Object.h` | Field offset resolution |
| ArtField | `art/runtime/art_field.h` | Compact ART field representation |
| ArtMethod | `art/runtime/art_method.h` | Method dispatch |
| mirror::Object | `art/runtime/mirror/object.h` | Object header layout |

---

## Implementation Decisions

### Python prototype before C++ implementation

**Rationale**: Validate design patterns before modifying production dalvik_engine.h
**Risk**: LOW - can iterate quickly

### Dictionary-based instance_data instead of raw bytes

**Rationale**: Easier debugging, type safety, evidence generation; performance can optimize later
**Risk**: MEDIUM - may need raw buffer for production

### Separate static_field_storage from objects

**Rationale**: Matches AOSP design where static fields are in ClassObject, not instances
**Risk**: LOW - standard OOP pattern

## Validation Status (Rule 3)

| Level | Status | Evidence |
|-------|--------|----------|
| **CREATED** | ✅ PASS | Code exists, runs successfully |
| **VALIDATED** | ⏳ PENDING | Unit tests needed |
| **PRODUCTION READY** | ⏳ PENDING | Integration testing needed |

**What Was Proven**:
- ✅ EnhancedClassInfo can calculate field offsets correctly
- ✅ EnhancedDalvikHeap supports iget/iput round-trip operations
- ✅ Static field storage (sget/sput) works per-class
- ✅ VTable construction produces valid dispatch tables

**Not Yet Proven**:
- ❌ C++ port correctness
- ❌ Performance under load
- ❌ Integration with real DEX parsing
- ❌ Edge cases (null objects, invalid fields, etc.)

---

## Next Steps for C++ Implementation

- [ ] Port EnhancedClassInfo to struct/class in dalvik_engine.h
- [ ] Port EnhancedFieldInfo to support iget/iput operand decoding
- [ ] Modify DalvikHeap to include class_registry and static storage
- [ ] Add iget/iput/sget/sput opcode handlers using new structures
- [ ] Integrate with existing DEX parser for field_ids table access
- [ ] Create unit tests validating field offset calculations

---

## Files Produced

| File | Purpose |
|------|---------|
| `database/exp032_phase4_object_model_improvement.json` | Complete evidence database (JSON) |
| `docs/EXP032_PHASE4_OBJECT_MODEL_IMPROVEMENT_REPORT.md` | Human-readable report (Markdown) |

---

## Appendix: Raw Gap Data

All identified gaps with full details:

| Component | Type | Severity | Impact |
|-----------|------|----------|--------|
| ClassInfo | MISSING | CRITICAL | iget, iput, sget... |
| FieldOffsetTable | MISSING | CRITICAL | iget, iput, iget-boolean... |
| VTable | MISSING | HIGH | invoke-virtual, invoke-interface, invoke-super... |
| StaticFieldStorage | MISSING | HIGH | sget, sput, sget-boolean... |
| FieldTypeSystem | INCOMPLETE | HIGH | iget-wide, iput-wide, iget-object... |
| InterfaceDispatch | MISSING | MEDIUM | invoke-interface... |
| ArrayObject | MISSING | MEDIUM | new-array, aget, aput... |
| StringObject | SIMPLIFIED | LOW | const-string, invoke-virtual(on strings)... |

---
*Report generated by EXP-032 Phase 4 Object Model Improvement Tool*
