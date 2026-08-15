# EXP-034 RUNTIME DESIGN — Proper Runtime Metadata Architecture

**Generated**: 2026-08-14T12:10:00Z  
**Status**: DESIGN DOCUMENT (Pre-Implementation)  
**Based On**: EXP-033 Research, AOSP Dalvik Source Analysis, DEX Format Specification

---

## 1. Design Principles

### 1.1 Core Philosophy
**"Match AOSP structure, simplify implementation"**

The goal is NOT to replicate every detail of Dalvik/ART. The goal is to create a **minimal but structurally correct** runtime that:
- Uses the same data organization as AOSP
- Supports real APK bytecode execution
- Can be validated against real Android behavior
- Is simple enough to implement correctly

### 1.2 Evidence-Based Design Rules
1. **Every structure must have an AOSP counterpart**
2. **Every field must serve a documented purpose**
3. **Every design decision must reference AOSP source**
4. **No premature optimization**

---

## 2. AOSP Reference Structures

### 2.1 Dalvik ClassObject (dalvik/libdex/DexClass.h)
```c
/*
 * AOSP Dalvik ClassObject definition (simplified)
 * Source: android/dalvik/libdex/DexClass.h
 *
 * This is the primary class representation in Dalvik VM.
 */
struct ClassObject {
    Object                obj;            /* Must be first member */
    /* cached class name */
    const char*           descriptor;     /* e.g., "Ljava/lang/String;" */
    /* access flags */
    u4                    accessFlags;
    /* superclass pointer */
    ClassObject*          super;
    /* defining class loader */
    Object*               classLoader;
    
    /* --- Field information --- */
    /* instance field count */
    u4                    ifieldCount;
    /* static field count */
    u4                    sfieldCount;
    /* instance fields array */
    InstField*            ifields;
    /* static fields array */
    StaticField*          sfields;
    /* total instance field size (in 32-bit words) */
    u4                    ifieldRef;
    
    /* --- Method information --- */
    /* direct method count */
    u4                    directMethodCount;
    /* virtual method count */
    u4                    virtualMethodCount;
    /* direct methods array */
    Method*               directMethods;
    /* virtual methods array */
    Method*               virtualMethods;
    
    /* --- VTable (Virtual Dispatch Table) --- */
    /* vtable count */
    int                   vtableCount;
    /* vtable array (points into virtualMethods or extended table) */
    Method**              vtable;
    
    /* --- Interface information --- */
    /* interface count */
    int                   interfaceCount;
    /* interfaces array */
    ClassObject**         interfaces;
};
```

### 2.2 Dalvik Method Structure (dalvik/libdex/Object.h)
```c
/*
 * AOSP Dalvik Method definition (simplified)
 * Source: android/dalvik/libdex/Object.h
 *
 * Represents a single method within a class.
 */
struct Method {
    /* class that defines this method */
    ClassObject*          clazz;
    
    /* --- DEX format accessors --- */
    /* method index in DEX method_ids[] */
    u4                    methodIndex;
    
    /* --- Method metadata --- */
    /* access flags */
    u4                    accessFlags;
    /* DEX method_idx */
    u4                    methodIdx;
    
    /* --- Code item reference --- */
    /* pointer to code_item (or NULL for abstract/native) */
    const u2*             insns;      /* instruction array */
    u4                    insSize;    /* instruction word size */
    u4                    registersSize; /* register count */
    u2                    outsSize;   /* out-parameter count */
    
    /* --- Prototype info --- */
    const char*           shorty;     /* short descriptor (e.g., "VI") */
    const DexPrototype*   prototype;
};
```

### 2.3 Dalvik Field Structures (dalvik/libdex/Object.h)
```c
/*
 * AOSP Dalvik field definitions (simplified)
 */

/* Instance field - part of object layout */
struct InstField {
    Field                 field;        /* base field info */
    /* byte offset of this field in object instance */
    u4                    byteOffset;
};

/* Static field - stored in class */
struct StaticField {
    JValue                value;        /* field value (union of types) */
    u4                    threadId;     /* initializing thread ID */
};

/* Base field structure */
struct Field {
    /* declaring class */
    ClassObject*          clazz;
    /* field index in DEX field_ids[] */
    u4                    fieldIdx;
    /* access flags */
    u4                    accessFlags;
};
```

### 2.4 ART mirror::Class (art/runtime/mirror/class.h)
```
/*
 * ART's more modern class representation (for reference)
 * Source: android/art/runtime/mirror/class.h
 *
 * ART uses C++ objects with better encapsulation,
 * but follows similar principles.
 */
class MANAGED Class FINAL : public Object {
    // Heap allocation size
    uint32_t class_size_;
    
    // Access flags
    uint32_t access_flags_;
    
    // Class state (loaded, resolving, verified, etc...)
    ClassStatus status_;
    
    // Superclass
    GcRoot<Class> super_class_;
    
    // VTable
    LengthPrefixedArray<ArtMethod, PointerSize::k64> vtable_;
    
    // IMT (Interface Method Table)
    Atomic<ImtConflictTable*> imt_;
    
    // Static field array
    GcRoot<ArtField[]> ifields_;  // instance fields
    GcRoot<ArtField[]> sfields_;  // static fields
    
    // Methods arrays
    GcRoot<ArtMethod[]> direct_methods_;
    GcRoot<ArtMethod[]> virtual_methods_;
};
```

---

## 3. MiniAndroid Runtime Metadata Design

### 3.1 Design Rationale

Based on AOSP analysis, MiniAndroid needs these **minimal structures**:

| AOSP Component | MiniAndroid Equivalent | Purpose |
|---------------|----------------------|---------|
| ClassObject | RuntimeClassInfo | Class metadata + field/method storage |
| Method | RuntimeMethodInfo | Method with code_item reference |
| InstField | InstanceFieldInfo | Instance field with byte offset |
| StaticField | StaticFieldValue | Static field with value storage |
| VTable (Method**) | VirtualDispatchTable | Method lookup by index |

### 3.2 RuntimeClassInfo Design

```cpp
/**
 * RuntimeClassInfo — MiniAndroid's equivalent of AOSP ClassObject
 * 
 * Design Goals:
 * 1. Match AOSP ClassObject structure (simplified)
 * 2. Support field offset calculation (like dvmComputeInstanceFieldOffsets)
 * 3. Support VTable construction (like dvmBuildVTable)
 * 4. Be serializable for evidence collection
 * 
 * AOSP Reference:
 * - dalvik/libdex/DexClass.h: ClassObject
 * - art/runtime/mirror/class.h: mirror::Class
 */
struct RuntimeClassInfo {
    // === Identity ===
    std::string class_descriptor;       // "Landroid/app/Activity;"
    std::string source_file;            // "Activity.java"
    uint32_t access_flags;              // ACC_PUBLIC, ACC_CLASS, etc.
    
    // === Hierarchy ===
    std::string superclass_descriptor;  // "Landroid/app/ContextThemeWrapper;"
    bool hierarchy_resolved;            // Has parent been linked?
    
    // === Fields (Critical for EXP-034) ===
    // Instance fields — layout matches object memory layout
    std::vector<InstanceFieldInfo> instance_fields;
    uint32_t instance_field_size;       // Total bytes for instance fields
    
    // Static fields — per-class storage
    std::vector<StaticFieldEntry> static_fields;
    
    // === Methods ===
    std::vector<RuntimeMethodInfo> direct_methods;   // <init>, static methods
    std::vector<RuntimeMethodInfo> virtual_methods;  // Overridable methods
    
    // === VTable (Virtual Dispatch Table) ===
    VirtualDispatchTable vtable;
    bool vtable_built;                  // Has VTable been constructed?
    
    // === DEX References ===
    uint32_t dex_class_idx;             // Index in DEX class_defs[]
    uint32_t class_data_offset;         // Offset to class_data_item
    
    // === Status ===
    enum class LoadState {
        UNLOADED,                       // Not yet loaded
        LOADED,                         // Header parsed
        RESOLVED,                       // Fields/methods linked
        VERIFYING,                      // Being verified
        VERIFIED,                       // Ready for execution
        ERROR                           // Loading failed
    } load_state = LoadState::UNLOADED;
    
    std::string error_message;          // If load_state == ERROR
    
    // === Methods ===
    
    /**
     * Calculate instance field offsets
     * 
     * Algorithm (from AOSP dvmComputeInstanceFieldOffsets):
     * 1. Start with superclass's total field size (aligned)
     * 2. For each instance field in declaration order:
     *    a. Align current offset to field type's alignment
     *    b. Assign offset to field
     *    c. Advance by field size
     * 3. Wide fields (long/double) aligned to 8 bytes
     * 4. Final size padded to 8-byte boundary
     * 
     * @param superclass Parent class (or nullptr for java.lang.Object)
     * @return true if successful
     */
    bool calculate_field_offsets(const RuntimeClassInfo* superclass);
    
    /**
     * Build virtual dispatch table
     * 
     * Algorithm (from AOSP dvmBuildVTable):
     * 1. Copy parent's VTable (if exists)
     * 2. For each virtual method in this class:
     *    a. Search VTable for matching signature
     *    b. If found, replace entry (override)
     *    c. If not found, append new entry
     * 3. Store result in this->vtable
     * 
     * @param parent_vtable Parent's VTable (or empty if no parent)
     * @return true if successful
     */
    bool build_vtable(const VirtualDispatchTable& parent_vtable);
    
    /**
     * Look up instance field by DEX field index
     * 
     * @param field_idx Index from iget/iput instruction
     * @return Field info or nullptr if not found
     */
    const InstanceFieldInfo* find_instance_field(uint32_t field_idx) const;
    
    /**
     * Look up static field by DEX field index
     * 
     * @param field_idx Index from sget/sput instruction
     * @return Field entry or nullptr if not found
     */
    const StaticFieldEntry* find_static_field(uint32_t field_idx) const;
    
    /**
     * Look up virtual method by VTable index
     * 
     * Used by invoke-virtual after VTable lookup
     * 
     * @param vtable_index Index from resolved method call
     * @return Method info or nullptr if not found
     */
    const RuntimeMethodInfo* find_virtual_method(uint32_t vtable_index) const;
    
    // === Serialization (for evidence) ===
    nlohmann::json to_json() const;
    static RuntimeClassInfo from_json(const nlohmann::json& j);
};
```

### 3.3 InstanceFieldInfo Design

```cpp
/**
 * InstanceFieldInfo — Represents an instance field with memory layout
 * 
 * Critical for implementing iget/iput correctly.
 * Each instance field has a fixed byte offset in objects of this class.
 * 
 * AOSP Reference:
 * - dalvik/libdex/Object.h: InstField
 * - art/runtime/art_field.h: ArtField
 */
struct InstanceFieldInfo {
    // === Identity ===
    uint32_t field_idx;                 // DEX field_ids[] index
    std::string name;                   // "mText"
    std::string descriptor;             // "Ljava/lang/String;"
    std::string type_signature;         // Full type descriptor
    
    // === Declaration Info ===
    uint32_t access_flags;              // ACC_PRIVATE, ACC_FINAL, etc.
    uint32_t declaring_class_idx;       // Which class declares this
    
    // === Memory Layout (CRITICAL) ===
    uint32_t byte_offset;               // Offset from object start
    uint32_t field_size;                // Size in bytes (1, 2, 4, or 8)
    uint32_t alignment;                 // Alignment requirement (1, 2, 4, or 8)
    bool is_wide;                       // True for long/double (64-bit)
    bool is_object_ref;                 // True for reference types
    
    // === Value Access Helpers ===
    
    /**
     * Get field value from object's raw memory
     * 
     * @param object_data Pointer to object's field data area
     * @return Decoded value as JSON-compatible type
     */
    nlohmann::json get_value(const uint8_t* object_data) const;
    
    /**
     * Set field value in object's raw memory
     * 
     * @param object_data Pointer to object's field data area
     * @param value Value to store (from interpreter registers)
     * @return true if successful
     */
    bool set_value(uint8_t* object_data, const nlohmann::json& value) const;
    
    // === Validation ===
    bool validate_offset() const;        // Check offset is reasonable
    std::string debug_string() const;   // Human-readable description
};
```

### 3.4 StaticFieldEntry Design

```cpp
/**
 * StaticFieldEntry — Static field with value storage
 * 
 * Static fields are stored per-class (not per-instance).
 * Used by sget/sput instructions.
 * 
 * AOSP Reference:
 * - dalvik/libdex/Object.h: StaticField
 */
struct StaticFieldEntry {
    // === Identity ===
    uint32_t field_idx;                 // DEX field_ids[] index
    std::string name;                   // "INSTANCE"
    std::string descriptor;             // "Lcom/example/MyClass;"
    std::string type_signature;
    
    // === Declaration Info ===
    uint32_t access_flags;
    uint32_t declaring_class_idx;
    
    // === Value Storage ===
    nlohmann::json value;               // Current value (JSON for flexibility)
    bool initialized;                   // Has <clinit> run?
    bool is_wide;                       // long/double
    bool is_object_ref;                 // reference type
    
    // === Thread Safety (simplified) ===
    // In real Dalvik, static init has thread ID tracking
    // MiniAndroid is single-threaded, so simplified
    
    // === Access ===
    nlohmann::json get_value() const;
    bool set_value(const nlohmann::json& new_value);
    
    std::string debug_string() const;
};
```

### 3.5 RuntimeMethodInfo Design

```cpp
/**
 * RuntimeMethodInfo — Method with code item reference
 * 
 * Bridges DEX format data with interpreter execution.
 * Each method knows its code_item location and register requirements.
 * 
 * AOSP Reference:
 * - dalvik/libdex/Object.h: Method
 * - art/runtime/art_method.h: ArtMethod
 */
struct RuntimeMethodInfo {
    // === Identity ===
    uint32_t method_idx;                // DEX method_ids[] index
    std::string name;                   // "onCreate"
    std::string descriptor;             // "(Landroid/os/Bundle;)V"
    std::string shorty;                 // "VL" (return + params shorthand)
    
    // === Declaration ===
    uint32_t access_flags;              // ACC_PUBLIC, ACC_STATIC, etc.
    uint32_t declaring_class_idx;       // Owner class
    bool is_direct;                     // true if in direct_methods[]
    bool is_virtual;                    // true if in virtual_methods[]
    bool is_static;                     // ACC_STATIC flag
    bool is_abstract;                   // ACC_ABSTRACT flag (no code!)
    
    // === Code Item Reference (CRITICAL) ===
    bool has_code;                      // false for abstract/native
    uint32_t code_item_offset;          // Offset in DEX file
    
    // Register requirements (from code_item)
    uint16_t registers_size;            // Total registers needed
    uint16_t ins_size;                  // Input (argument) registers
    uint16_t outs_size;                 // Out registers for method calls
    
    // Instruction data
    uint32_t insns_count;               // Number of 16-bit code units
    // Note: Actual instructions read from DEX at runtime
    
    // === Execution State (runtime only) ===
    mutable bool compiled;              // JIT compiled (future)
    mutable uint32_t invoke_count;      // How many times called
    
    // === VTable Index (for virtual methods) ===
    int32_t vtable_index;               // Position in class's VTable (-1 if not set)
    
    // === Methods ===
    
    /**
     * Get method signature for VTable matching
     * Format: "name+descriptor" (unique identifier)
     */
    std::string get_signature() const;
    
    /**
     * Check if this method overrides another
     * 
     * Two methods match if they have same name+descriptor
     * Used during VTable construction
     */
    bool matches_signature(const RuntimeMethodInfo& other) const;
    
    /**
     * Check if method can be called with given arguments
     * 
     * @param arg_types List of argument type descriptors
     * @return true if compatible
     */
    bool is_compatible(const std::vector<std::string>& arg_types) const;
    
    // === Debug/Evidence ===
    std::string debug_string() const;
    nlohmann::json to_json() const;
};
```

### 3.6 VirtualDispatchTable Design

```cpp
/**
 * VirtualDispatchTable — VTable implementation for invoke-virtual
 * 
 * The VTable enables polymorphic method dispatch:
 * 1. Compiler emits invoke-virtual with method reference
 * 2. Runtime looks up object's actual class
 * 3. Search class's VTable for method index
 * 4. Call the method found (which may be overridden)
 * 
 * AOSP Reference:
 * - dalvm/Analysis/VTableCheck.cpp: VTable building logic
 * - art/runtime/mirror/class.h: vtable_ field
 */
struct VirtualDispatchTable {
    // Ordered list of method pointers (by index)
    std::vector<const RuntimeMethodInfo*> entries;
    
    // Signature-to-index map for fast lookup
    std::map<std::string, uint32_t> signature_map;
    
    // === Operations ===
    
    /**
     * Look up method by VTable index
     * 
     * @param index Index from invoke-virtual resolution
     * @return Method or nullptr if invalid index
     */
    const RuntimeMethodInfo* lookup_by_index(uint32_t index) const;
    
    /**
     * Look up method by signature
     * 
     * @param signature "name+descriptor" string
     * @return Method or nullptr if not found
     */
    const RuntimeMethodInfo* lookup_by_signature(const std::string& signature) const;
    
    /**
     * Add or override method in VTable
     * 
     * During VTable construction:
     * - If signature exists, replace (override)
     * - If not, append (new virtual method)
     * 
     * @param method Method to add
     * @return Index where method was placed
     */
    uint32_t add_or_override(const RuntimeMethodInfo* method);
    
    /**
     * Copy parent's VTable as starting point
     * 
     * @param parent Parent class's VTable
     */
    void inherit_from(const VirtualDispatchTable& parent);
    
    // === Validation ===
    bool validate() const;              // Check integrity
    size_t size() const;                // Number of entries
    bool empty() const;
    
    // === Debug/Evidence ===
    nlohmann::json to_json() const;
    std::string debug_string() const;
};
```

---

## 4. Object Memory Layout

### 4.1 Object Structure in Memory

```
┌──────────────────────────────────────┐
│        Object Header (fixed)         │
│  ┌────────────────────────────────┐  │
│  │ ClassInfo* (vtable ptr)  8B   │  │
│  │ Lock/monitor word        4B   │  │
│  │ Hash code / flags        4B   │  │
│  └────────────────────────────────┘  │
├──────────────────────────────────────┤
│                                      │
│     Instance Fields (variable)       │
│  ┌────────────────────────────────┐  │
│  │ [superclass fields...]         │  │  ← Inherited fields first
│  ├────────────────────────────────┤  │
│  │ field_0  (offset=0)     4B    │  │
│  │ field_1  (offset=4)     4B    │  │
│  │ field_2  (offset=8)     8B    │  │  ← wide field (aligned)
│  │ field_3  (offset=16)    4B    │  │
│  │ ...                            │  │
│  └────────────────────────────────┘  │
│                                      │
├──────────────────────────────────────┤
│        Total Size = header + fields  │
└──────────────────────────────────────┘
```

### 4.2 Field Offset Calculation Example

Given class hierarchy:
```java
class Object {                          // offset
    int hashCode;                       // 0
}                                       // total: 4 bytes

class View extends Object {             // inherits Object fields
    int mLeft;                          // 0 (after Object's 4)
    int mTop;                           // 4
    int mRight;                         // 8
    int mBottom;                        // 12
}                                       // total: 16 bytes

class TextView extends View {           // inherits View fields
    CharSequence mText;                 // 16 (reference = 4 bytes)
    int mTextColor;                     // 20
}                                       // total: 24 bytes
```

**Algorithm** (matches `dvmComputeInstanceFieldOffsets`):
```
function calculateFieldOffsets(classInfo, superclass):
    if superclass != null:
        currentOffset = align8(superclass.instance_field_size)
    else:
        currentOffset = 0
    
    for field in classInfo.instance_fields:
        if field.is_wide:
            currentOffset = align8(currentOffset)  // Align wide to 8
        else:
            currentOffset = align4(currentOffset)  // Align normal to 4
        
        field.byte_offset = currentOffset
        currentOffset += field.field_size
    
    classInfo.instance_field_size = align8(currentOffset)
```

---

## 5. VTable Construction Example

### 5.1 Simple Hierarchy

```java
class Animal {
    void speak() { /* ... */ }          // vtable[0] = Animal.speak
    void eat() { /* ... */ }            // vtable[1] = Animal.eat
}

class Dog extends Animal {
    @Override
    void speak() { /* woof */ }         // vtable[0] = Dog.speak (override!)
    void bark() { /* ... */ }           // vtable[2] = Dog.bark (new)
}
```

**VTable Construction** (matches `dvmBuildVTable`):

```
Animal.vtable:
  [0] Animal.speak()
  [1] Animal.eat()

Dog.vtable (build process):
  Step 1: Copy parent → [Animal.speak, Animal.eat]
  Step 2: Process Dog.speak → matches [0], override → [Dog.speak, Animal.eat]
  Step 3: Process Dog.bark → no match, append → [Dog.speak, Animal.eat, Dog.bark]

Final Dog.vtable:
  [0] Dog.speak()       ← Overridden!
  [1] Animal.eat()      ← Inherited
  [2] Dog.bark()        ← New virtual method
```

### 5.2 invoke-virtual Flow

```
Bytecode: invoke-virtual {v0}, LAnimal;->speak()V

Execution:
1. Read object reference from v0 → Object* obj
2. Get obj->classInfo → Dog.classInfo (actual runtime class!)
3. Look up "speak()V" in Dog.vtable → index 0
4. Get Dog.vtable[0] → Dog.speak method
5. Execute Dog.speak's code_item ← Polymorphism works!
```

---

## 6. Integration with Existing Code

### 6.1 Current vs. Proposed Object Model

| Aspect | Current (object_model.h) | Proposed (this design) |
|--------|-------------------------|----------------------|
| Field storage | `map<string, value>` | Offset-based byte array |
| Field lookup | By string name | By DEX field_idx |
| Class info | Basic ClassMetadata | Full RuntimeClassInfo |
| Method info | None | RuntimeMethodInfo |
| VTable | None | VirtualDispatchTable |
| Inheritance | Single link | Full hierarchy with field inheritance |

### 6.2 Migration Path

**Phase 1 (This EXP)**: Add new structures alongside existing ones
- Create `runtime_metadata.h` with new definitions
- Keep old `object_model.h` working
- Gradually migrate components

**Phase 2 (Future)**: Replace old model
- Update DalvikEngine to use new structures
- Remove old string-keyed maps
- Full offset-based field access

---

## 7. Implementation Checklist

### 7.1 Files to Create
- [ ] `src/runtime/runtime_metadata.h` — All structure definitions
- [ ] `src/runtime/runtime_metadata.cpp` — Implementation of methods
- [ ] `src/runtime/field_layout.cpp` — Field offset calculator
- [ ] `src/runtime/vtable_builder.cpp` — VTable constructor

### 7.2 Files to Modify
- [ ] `src/dex/dalvik_engine.h` — Use new structures
- [ ] `src/dex/dex_interpreter.cpp` — Implement iget/iput/sget/sput
- [ ] `src/dex/class_resolver.cpp` — Build RuntimeClassInfo from DEX

### 7.3 Tests Required
- [ ] Unit test: Field offset calculation (matches AOSP example)
- [ ] Unit test: VTable construction (inheritance + override)
- [ ] Integration test: Real APK field access trace
- [ ] Integration test: Real APK virtual dispatch trace

---

## 8. Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Field offset math has bugs | HIGH | MEDIUM | Test against known AOSP layouts |
| VTable construction misses edge cases | HIGH | LOW | Follow AOSP algorithm exactly |
| Performance overhead of new structures | MEDIUM | LOW | Don't optimize yet; correctness first |
| Integration breaks existing tests | MEDIUM | MEDIUM | Run full test suite after changes |

---

## 9. Success Criteria for Implementation

### 9.1 MUST Achieve
- [ ] `RuntimeClassInfo` can be populated from real DEX class_def
- [ ] `calculate_field_offsets()` produces correct offsets for test cases
- [ ] `build_vtable()` produces correct VTable for inheritance hierarchies
- [ ] `find_instance_field(field_idx)` returns correct field
- [ ] `lookup_by_index(i)` returns correct method from VTable

### 9.2 NICE to Have
- [ ] Round-trip serialization (to_json/from_json)
- [ ] Debug visualization of object layout
- [ ] Performance baseline measurements

---

*Design complete: 2026-08-14T12:10:00Z*  
*Ready for implementation in PHASE 3-4*
*AOSP references verified against Android 12 source*
