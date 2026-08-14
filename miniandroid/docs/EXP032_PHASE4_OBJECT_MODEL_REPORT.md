# EXP-032 Phase 4: Object Model Improvement Report

**Generated**: 2026-08-14  
**Status**: ✅ COMPLETE  
**Output**: `database/exp032_object_model_gap.json`

---

## Executive Summary

This phase analyzes MiniAndroid's current object model against AOSP Dalvik/ART reference architecture and produces a detailed improvement specification. The analysis reveals **3 critical gaps** that block implementation of field operation opcodes (iget/iput/sget/sput).

### Key Findings

| Category | Current Status | AOSP Reference | Gap Severity |
|----------|---------------|----------------|--------------|
| **Field Offset Table** | ❌ Missing | `ClassObject->fieldOffsets` | 🔴 CRITICAL |
| **VTable** | ❌ Missing | `ClassObject->vtable` | 🔴 CRITICAL |
| **Static Field Storage** | ⚠️ Partial | `ClassObject->sfields` | 🔴 CRITICAL |
| **Interface Table** | ❌ Missing | `ClassObject->iftable` | 🟠 HIGH |
| **Monitor Lock** | ❌ Missing | `Object.lock` | 🟠 HIGH |

---

## 1. Current Object Model Analysis

### 1.1 Existing Components

MiniAndroid has a foundational object model with these components:

#### RuntimeObject (`src/runtime/object_model.h`)
```cpp
class RuntimeObject {
    uint32_t object_id_;
    std::string runtime_class_;
    std::string class_descriptor_;
    ObjectLifetime lifetime_;        // ALLOCATED → ACTIVE → FINALIZING → COLLECTED
    uint64_t creation_timestamp_;
    uint32_t creator_pc_;
};
```
**Strengths**: Clean lifetime management, identity tracking, JSON serialization  
**Weaknesses**: No monitor lock, no hash code, no type-check cache

#### HeapObject (`src/dex/dalvik_engine.h`)
```cpp
struct HeapObject {
    uint32_t object_id;
    std::string class_descriptor;
    std::map<std::string, DalvikValue> fields;  // Name-based lookup
    std::shared_ptr<api::AndroidObject> api_object;
};
```
**Strengths**: Simple field storage, API bridge support  
**Weaknesses**: Name-based field access (slow), no offset table, no VTable pointer

#### ClassMetadata (`src/runtime/object_model.h`)
```cpp
class ClassMetadata {
    std::map<std::string, MethodMetadata> methods_;
    std::map<std::string, FieldMetadata> fields_;
    std::string parent_class_;
};
```
**Strengths**: Method/field metadata storage, inheritance tracking  
**Weaknesses**: No VTable, no field offsets, no static field values

#### DalvikHeap (`src/dex/dalvik_engine.h`)
```cpp
class DalvikHeap {
    std::map<uint32_t, HeapObject> objects_;
    uint32_t next_id_;
    json allocation_log_;
};
```
**Strengths**: Allocation logging, ID-based lookup  
**Weaknesses**: No GC, no memory limit, no compaction

---

## 2. AOSP Reference Architecture

### 2.1 Dalvik ClassObject Structure

From `dalvik/vm/oo/ClassObject.h`:

```
┌─────────────────────────────────────────────────────────────┐
│                    ClassObject Layout                        │
├─────────────────────────────────────────────────────────────┤
│  [Object Header]                                            │
│    ├── clazz: ClassObject*     (self-reference)             │
│    └── lock: u32               (monitor lock word)          │
├─────────────────────────────────────────────────────────────┤
│  [Class Identity]                                            │
│    ├── descriptor: const char*   ("Landroid/app/Activity;") │
│    └── accessFlags: u4          (PUBLIC, FINAL, etc.)       │
├─────────────────────────────────────────────────────────────┤
│  [Hierarchy]                                                 │
│    ├── super: ClassObject*      (parent class)              │
│    └── objectSize: size_t       (instance byte size)        │
├─────────────────────────────────────────────────────────────┤
│  [VTable - CRITICAL for invoke-virtual]                      │
│    ├── vtable: Method**         (sorted virtual methods)     │
│    └── vtableCount: u4          (number of entries)         │
├─────────────────────────────────────────────────────────────┤
│  [Instance Fields - CRITICAL for iget/iput]                  │
│    ├── ifields: InstField*      (field definitions)         │
│    ├── ifieldCount: u4          (field count)                │
│    └── fieldOffsets: u4*        (byte offsets from obj start)│
├─────────────────────────────────────────────────────────────┤
│  [Static Fields - CRITICAL for sget/sput]                    │
│    ├── sfields: StaticField*    (static field definitions)  │
│    └── sfieldCount: u4          (static field count)        │
├─────────────────────────────────────────────────────────────┤
│  [Methods]                                                   │
│    ├── directMethods: Method*    (ctors, private, static)    │
│    ├── virtualMethods: Method*   (overridable methods)      │
│    └── methodCount: u4           (total methods)            │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 ART mirror::Object Structure

From `runtime/art_object.h`:

```
┌─────────────────────────────────────────┐
│         mirror::Object (ART)            │
├─────────────────────────────────────────┤
│  klass_: HeapReference<Class>  (offset 0)│
│  monitor_: uint32_t            (offset 4)│
│  ebh_state_: uint32_t          (offset 8)│
└─────────────────────────────────────────┘
         ↓ (instance fields follow)
┌─────────────────────────────────────────┐
│  Instance fields at known offsets...    │
│  (determined by klass_->GetFieldOffset) │
└─────────────────────────────────────────┘
```

---

## 3. Critical Gap Analysis

### 3.1 🔴 GAP #1: Field Offset Table (Blocks iget/iput)

**AOSP Reference**: `ClassObject->fieldOffsets (u4*)`  
**Current Status**: ❌ Completely Missing  
**Impact**: Cannot efficiently implement `iget`, `iput`, `iget-object`, `iput-object`

#### Problem
Current implementation uses name-based field lookup:
```cpp
// SLOW: O(log n) string comparison per field access
DalvikValue HeapObject::get_field(const std::string& name) {
    auto it = fields.find(name);  // map<string, DalvikValue>
    return (it != fields.end()) ? it->second : DalvikValue::make_uninit();
}
```

#### Solution: Offset-Based Field Access
```cpp
// FAST: O(1) array indexing using pre-computed offsets
struct ImprovedHeapObject {
    ClassInfo* clazz;                          // Pointer to class metadata
    uint8_t data[];                            // Flexible array for instance data
    
    DalvikValue read_field(uint32_t byte_offset, FieldType type) {
        return *reinterpret_cast<DalvikValue*>(data + byte_offset);
    }
    
    void write_field(uint32_t byte_offset, const DalvikValue& value, FieldType type) {
        *reinterpret_cast<DalvikValue*>(data + byte_offset) = value;
    }
};

// ClassInfo provides offset table
struct ClassInfo {
    std::vector<FieldInfo> instance_fields;
    std::map<std::string, uint32_t> field_offsets;  // name → byte_offset
    
    uint32_t get_field_offset(const std::string& name) const {
        auto it = field_offsets.find(name);
        return (it != field_offsets.end()) ? it->second : UINT32_MAX;
    }
};
```

#### Opcode Implementation Pattern (iget)
```cpp
case Opcode::IGET_OBJECT: {  // 0x54
    // Decode operands
    uint8_t vA = (insn >> 8) & 0xF;    // result register
    uint8_t vB = insn >> 12;           // object register
    uint16_t field_idx = next_unit;    // field reference index
    
    // Get object reference
    DalvikValue obj_ref = registers.read_v(vB);
    if (obj_ref.type == DalvikType::NULL_REF) {
        throw DalvikException("NullPointerException: iget-object on null");
    }
    
    // Dereference to heap object
    HeapObject* heap_obj = dalvik_heap.get(obj_ref.object_id);
    if (!heap_obj) throw DalvikException("Invalid object reference");
    
    // Resolve field offset from class info
    ClassInfo* cls = class_resolver.resolve(heap_obj->class_descriptor);
    FieldInfo field = dex_parser.get_field(field_idx);
    uint32_t offset = cls->get_field_offset(field.name);
    
    if (offset == UINT32_MAX) {
        throw DalvikException("NoSuchFieldError: " + field.name);
    }
    
    // Read field value using OFFSET (not name!)
    DalvikValue value = heap_obj->read_field(offset, field.type);
    registers.write_v(vA, value);
    
    break;
}
```

---

### 3.2 🔴 GAP #2: VTable (Affects invoke-virtual)

**AOSP Reference**: `ClassObject->vtable (Method**)`  
**Current Status**: ❌ Completely Missing  
**Impact**: Virtual method dispatch is slow/incorrect

#### What is a VTable?
A **Virtual Method Table** is an array of function pointers (or method indices) used for dynamic dispatch. Each class has its own VTable that:

1. Inherits parent's VTable entries
2. Overrides entries for methods it redefines
3. Appends new virtual methods at the end

```
Example VTable for TextView (extends View extends Object):

Index | Method                  | Source Class
------|------------------------|-------------
0     | getClass()             | java.lang.Object
1     | hashCode()             | java.lang.Object
2     | equals(Object)         | java.lang.Object
...   | ...                    | ...
10    | getVisibility()        | android.view.View
11    | setVisibility(int)     | android.view.View
12    | getText()              | android.widget.TextView  ← Override!
13    | setText(CharSequence)  | android.widget.TextView  ← New!
```

#### Solution: Build VTable During Class Resolution
```cpp
struct ClassInfo {
    struct VTableEntry {
        MethodInfo* method;       // Method implementation
        std::string method_name; // For debugging
        ClassInfo* declaring_class; // Where this impl comes from
    };
    
    std::vector<VTableEntry> vtable;
    
    void build_vtable() {
        // Start with parent's vtable
        if (super_class) {
            vtable = super_class->vtable;  // Copy parent's entries
        }
        
        // Override with this class's virtual methods
        for (auto& method : virtual_methods) {
            bool found = false;
            for (size_t i = 0; i < vtable.size(); i++) {
                if (vtable[i].method_name == method.name &&
                    has_same_signature(vtable[i].method, &method)) {
                    // Override existing entry
                    vtable[i] = {&method, method.name, this};
                    found = true;
                    break;
                }
            }
            
            if (!found) {
                // Append new virtual method
                vtable.push_back({&method, method.name, this});
            }
        }
    }
    
    MethodInfo* resolve_virtual(uint32_t vtable_index) {
        if (vtable_index < vtable.size()) {
            return vtable[vtable_index].method;
        }
        return nullptr;
    }
};
```

---

### 3.3 🔴 GAP #3: Static Field Storage (Blocks sget/sput)

**AOSP Reference**: `ClassObject->svalues (u4[] or JValue[])`  
**Current Status**: ⚠️ Metadata exists but no runtime storage  
**Impact**: Cannot store/retrieve static field values

#### Problem
Static fields belong to the **class**, not to any instance. They need class-level storage.

#### Solution: Add Static Field Storage to ClassInfo
```cpp
struct ClassInfo {
    // Static field DEFINITIONS (from DEX)
    std::vector<FieldInfo> static_fields;
    
    // Static field VALUES (runtime storage)
    std::map<std::string, DalvikValue> static_field_values;
    
    void init_static_fields() {
        for (const auto& field : static_fields) {
            // Initialize to default values
            DalvikValue default_val = get_default_value(field.type);
            static_field_values[field.name] = default_val;
        }
    }
    
    DalvikValue sget(const std::string& field_name) {
        auto it = static_field_values.find(field_name);
        if (it == static_field_values.end()) {
            throw DalvikException("NoSuchFieldError: " + field_name);
        }
        return it->second;
    }
    
    void sput(const std::string& field_name, const DalvikValue& value) {
        auto it = static_field_values.find(field_name);
        if (it == static_field_values.end()) {
            throw DalvikException("NoSuchFieldError: " + field_name);
        }
        // Type check would go here in production
        it->second = value;
    }
    
private:
    DalvikValue get_default_value(const std::string& descriptor) {
        if (descriptor == "I" || descriptor == "Z" || 
            descriptor == "S" || descriptor == "B" ||
            descriptor == "C" || descriptor == "J" ||
            descriptor == "F" || descriptor == "D") {
            return DalvikValue::make_int(0);  // Numeric default
        } else if (descriptor.startsWith("L") || descriptor.startsWith("[")) {
            return DalvikValue::make_null();  // Reference default
        }
        return DalvikValue::make_uninit();
    }
};
```

---

## 4. Improved Architecture Specification

### 4.1 Enhanced ClassInfo Design

```cpp
// EXP-032 Phase 4: AOSP-Aligned ClassInfo Specification
class ClassInfo {
public:
    // ===== IDENTITY =====
    std::string descriptor;           // "Landroid/widget/TextView;"
    std::string source_file;          // "TextView.java"
    uint32_t access_flags;            // ACC_PUBLIC | ACC_FINAL
    uint32_t dex_class_def_idx;       // Index in DEX class_defs[]
    
    // ===== HIERARCHY =====
    ClassInfo* super_class;           // Parent class (nullptr for Object)
    std::vector<ClassInfo*> interfaces; // Implemented interfaces
    
    // ===== INSTANCE LAYOUT =====
    size_t object_instance_size;      // Total bytes per instance
    std::vector<FieldInfo> instance_fields;
    std::map<std::string, uint32_t> field_offsets; // name → byte_offset
    
    // ===== STATIC STORAGE =====
    std::vector<FieldInfo> static_fields;
    std::map<std::string, DalvikValue> static_field_values;
    
    // ===== METHODS =====
    std::vector<MethodInfo> direct_methods;  // Constructors, private, static
    std::vector<MethodInfo> virtual_methods; // Overridable methods
    
    // ===== VTABLE =====
    struct VTableEntry {
        MethodInfo* method;
        std::string name;
        std::string signature;
        ClassInfo* declaring_class;
    };
    std::vector<VTableEntry> vtable;
    
    // ===== RESOLUTION STATE =====
    enum class Status { UNRESOLVED, RESOLVED, VERIFYING, VERIFIED };
    Status status = Status::UNRESOLVED;
    
    // ===== OPERATIONS =====
    void build_vtable();
    void init_static_fields();
    uint32_t get_field_offset(const std::string& name) const;
    DalvikValue get_static_field(const std::string& name) const;
    void set_static_field(const std::string& name, const DalvikValue& val);
    MethodInfo* resolve_virtual(uint32_t vtable_index) const;
    bool is_instance_of(ClassInfo* target) const;
    
    // ===== SERIALIZATION =====
    json to_json() const;
};
```

### 4.2 Enhanced HeapObject Design

```cpp
// EXP-032 Phase 4: AOSP-Aligned HeapObject Specification
struct HeapObject {
    // ===== OBJECT HEADER (matches AOSP layout) =====
    ClassInfo* clazz;                 // Class pointer (like Object.clazz)
    uint32_t monitor_word;            // Monitor lock (stub)
    
    // ===== IDENTITY =====
    uint32_t object_id;
    uint64_t allocation_timestamp;
    uint32_t creator_pc;
    uint32_t creator_frame_id;
    
    // ===== LIFETIME =====
    enum class State { ALLOCATED, INITIALIZED, FINALIZABLE, COLLECTED };
    State state = State::ALLOCATED;
    
    // ===== INSTANCE DATA =====
    // Using byte array with offset-based access (AOSP compatible)
    std::vector<uint8_t> instance_data;  // Raw instance bytes
    
    // ===== API BRIDGE =====
    std::shared_ptr<api::AndroidObject> api_object;
    
    // ===== OPERATIONS =====
    template<typename T>
    T read_field(uint32_t byte_offset) {
        if (byte_offset + sizeof(T) <= instance_data.size()) {
            return *reinterpret_cast<T*>(instance_data.data() + byte_offset);
        }
        return T{};
    }
    
    template<typename T>
    void write_field(uint32_t byte_offset, T value) {
        if (byte_offset + sizeof(T) <= instance_data.size()) {
            *reinterpret_cast<T*>(instance_data.data() + byte_offset) = value;
        }
    }
    
    // Convenience wrappers using DalvikValue
    DalvikValue read_dalvik_field(uint32_t offset, const std::string& type_desc);
    void write_dalvik_field(uint32_t offset, const DalvikValue& value);
    
    // ===== SERIALIZATION =====
    json to_json() const;
};
```

### 4.3 Enhanced DalvikHeap Design

```cpp
// EXP-032 Phase 4: AOSP-Aligned DalvikHeap Specification
class DalvikHeap {
public:
    // ===== CONFIGURATION =====
    size_t max_heap_bytes = 0;        // 0 = unlimited
    size_t current_allocation = 0;
    
    // ===== ALLOCATION =====
    uint32_t allocate_object(ClassInfo* cls, uint32_t pc, uint32_t frame_id);
    uint32_t allocate_array(ClassInfo* elem_cls, size_t length, ...);
    
    // ===== ACCESS =====
    HeapObject* get(uint32_t object_id);
    const HeapObject* get(uint32_t object_id) const;
    
    // ===== LIFETIME =====
    void mark_initialized(uint32_t id);
    void release(uint32_t id);         // Manual "GC"
    
    // ===== MONITORING =====
    size_t size() const;
    json dump() const;
    json get_allocation_log() const;
    std::vector<uint32_t> get_all_ids() const;
    
private:
    std::map<uint32_t, HeapObject> objects_;
    uint32_t next_id_ = 1;
    uint64_t alloc_sequence_ = 0;
    json allocation_log_;
};
```

---

## 5. Implementation Priority Queue

### 5.1 IMMEDIATE (This Sprint)

These changes unblock the critical opcodes identified in Phase 2:

| Task | Lines of Code | Unblocks |
|------|--------------|----------|
| Add `field_offsets` to ClassInfo | ~50 LOC | iget, iput (all variants) |
| Add `static_field_values` to ClassInfo | ~40 LOC | sget, sput (all variants) |
| Create basic VTable structure | ~80 LOC | invoke-virtual speed |
| Implement `iget-object` opcode | ~30 LOC | 6.3% of real bytecode |
| Implement `iput-object` opcode | ~30 LOC | 5.1% of real bytecode |

**Total Estimated Effort**: ~230 LOC over 2-3 days

### 5.2 SHORT-Term (Next Sprint)

| Task | Lines of Code | Benefit |
|------|--------------|---------|
| Interface table support | ~100 LOC | invoke-interface correctness |
| Monitor lock stub | ~30 LOC | synchronized keyword |
| Heap memory limit | ~20 LOC | OOM detection |
| Array allocation support | ~60 LOC | new-array opcode |

### 5.3 MEDIUM-Term (Future Phases)

| Task | Lines of Code | Benefit |
|------|--------------|---------|
| Reference counting GC | ~200 LOC | Memory safety |
| Hash code caching | ~15 LOC | Performance |
| Generational allocator | ~500+ LOC | Production readiness |

---

## 6. Migration Strategy

### 6.1 Backward Compatibility

The improved object model must maintain compatibility with:

1. **Existing DalvikEngine** - Register file format unchanged
2. **Existing API stubs** - api::AndroidObject bridge preserved
3. **Existing trace format** - JSON output extended, not broken
4. **Existing test cases** - All EXP-031.6 tests must still pass

### 6.2 Incremental Adoption

```
Phase 4a: Add new ClassInfo alongside existing ClassMetadata
Phase 4b: Migrate DalvikHeap to use ClassInfo
Phase 4c: Update HeapObject with offset table
Phase 4d: Implement field operation opcodes
Phase 4e: Remove old ClassMetadata (once fully migrated)
```

---

## 7. Testing Strategy

### 7.1 Unit Tests for New Components

```cpp
TEST(ClassInfoTest, FieldOffsetCalculation) {
    ClassInfo cls;
    cls.descriptor = "Ltest/Point;";
    cls.instance_fields = {
        {"x", "I", false},  // int x at offset 0
        {"y", "I", false},  // int y at offset 4
    };
    cls.build_field_offsets();
    
    EXPECT_EQ(cls.get_field_offset("x"), 0);
    EXPECT_EQ(cls.get_field_offset("y"), 4);
    EXPECT_EQ(cls.get_field_offset("z"), UINT32_MAX);  // Not found
}

TEST(DalvikHeapTest, IputIgetObjectPattern) {
    // Allocate object
    uint32_t obj_id = heap.allocate(&point_class, 0, 0);
    
    // Set field via iput-object pattern
    HeapObject* obj = heap.get(obj_id);
    uint32_t offset = point_class.get_field_offset("x");
    obj->write_field(offset, DalvikValue::make_int(42));
    
    // Read back via iget-object pattern
    DalvikValue val = obj->read_field(offset);
    EXPECT_EQ(val.int_val, 42);
}

TEST(VTableTest, MethodOverride) {
    // Child overrides parent's method
    child_class.build_vtable();
    
    // Same index, different implementation
    EXPECT_EQ(child_class.vtable[OVERRIDE_INDEX].declaring_class, &child_class);
    EXPECT_EQ(child_class.vtable[INHERITED_INDEX].declaring_class, &parent_class);
}
```

### 7.2 Integration Tests with Real DEX

Use valid_test.dex methods from Phase 3:
- Verify `<init>` can set initial field values
- Verify `onCreate()` can read/write Activity fields
- Generate opcode traces showing field operations

---

## 8. Artifacts Generated

| Artifact | Location | Description |
|----------|----------|-------------|
| Gap Analysis Database | `database/exp032_object_model_gap.json` | Complete gap analysis with priorities |
| This Report | `docs/EXP032_PHASE4_OBJECT_MODEL_REPORT.md` | Human-readable specification |
| Analyzer Tool | `tools/exp032_object_model_analyzer.py` | Regenerable analysis tool |

---

## 9. Conclusions

### 9.1 What Was Accomplished

✅ Complete analysis of current object model vs AOSP architecture  
✅ Identified 3 critical gaps blocking field operation opcodes  
✅ Produced detailed specifications for ClassInfo/VTable/Heap improvements  
✅ Created implementation priority queue with effort estimates  
✅ Designed backward-compatible migration strategy  

### 9.2 What Changes Are Needed

**Immediate (unblocks ~14% of real bytecode)**:
1. Add field offset table to ClassInfo → enables iget/iput
2. Add static field storage to ClassInfo → enables sget/sput  
3. Create basic VTable structure → improves invoke-virtual

**Estimated Impact After Phase 4 Implementation**:
- Opcode coverage: 13.33% → ~25% (+11.67 percentage points)
- Real APK execution capability: SIGNIFICANTLY IMPROVED
- Evidence quality score: 30/100 → ~55/100

---

*Report generated by EXP-032 Phase 4 Object Model Improvement*
*AOSP Reference-Driven Development Methodology*
