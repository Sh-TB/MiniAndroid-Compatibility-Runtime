# MiniAndroid vs Dalvik (AOSP) Architecture Comparison

**Document:** EXP-033 - Architecture Gap Analysis  
**Date:** 2025-01-XX  
**Scope:** Complete Dalvik VM subsystem comparison  

---

## Executive Summary

This document provides a detailed architectural comparison between the **AOSP Dalvik Virtual Machine** and the **MiniAndroid Runtime v0.2** current implementation. The analysis identifies gaps in 10 major component areas, rates their severity, and estimates implementation complexity.

| Metric | Value |
|--------|-------|
| Total Components Analyzed | 10 |
| Critical Gaps (🔴) | 4 |
| High Gaps (🟡) | 4 |
| Medium Gaps (🟢) | 2 |
| Low Gaps (⚪) | 0 |

---

## Comparison Table

### 1. Register VM

| Aspect | Dalvik (AOSP) | MiniAndroid (Current) | Gap Severity | Implementation Complexity |
|--------|---------------|----------------------|--------------|--------------------------|
| **Number of Registers** | 65536 theoretically, but method-specific: `registers_size` from DEX code_item (typically 16-256) | Configurable via `DexRegisterFile::initialize(count)` - supports any size | 🟢 MEDIUM | EASY |
| **Register Types** | Typed by usage: int, float, wide (long/double = 2 regs), reference | `DalvikValue` union supports INT32, INT64, FLOAT32, FLOAT64, OBJECT_REF, etc. | 🟢 MEDIUM | EASY |
| **Parameter Registers (pN)** | Last `ins_size` registers are aliases p0..pN mapping to v[M]..v[M+N] | Implemented: `param_start_ = count - ins_count`, `write_p()` / `read_p()` methods | ⚪ LOW | DONE |
| **Register File Structure** | Contiguous array of `u4` values in `StackFrame` | `std::vector<DalvikValue> registers_` with tracking via `written_` set | 🟡 HIGH | MEDIUM |
| **Wide Register Handling** | Long/double occupy vN and vN+1 (convention, not enforced) | `INT64` and `FLOAT64` types exist but no adjacent-register enforcement | 🟡 HIGH | MEDIUM |
| **Uninitialized Detection** | Register can be "uninitialized" - verifier tracks this | `DalvikType::UNINITIALIZED` and `REGISTER_UNSET` exist | 🟢 MEDIUM | DONE |

#### Dalvik Reference (AOSP)
```c
// From vm/interp/Stack.h
struct StackFrame {
    u4* fp;           // frame pointer (points to v0)
    const Method* method;
    u4* returnAddr;
    // ... register file is fp[0] .. fp[registers_size-1]
};
```

#### MiniAndroid Current (dalvik_engine.h:202-255)
```cpp
class DexRegisterFile {
    std::vector<DalvikValue> registers_;
    uint32_t size_ = 0;
    uint32_t ins_count_ = 0;
    uint32_t param_start_ = 0;  // Where p-registers start
    std::set<uint8_t> written_;   // Track which regs were written
};
```

#### Gap Analysis
The register VM is **partially complete**. The basic structure exists but lacks:
- Proper wide-value register pair management
- Verification that wide values don't overlap other registers
- Optimized register access patterns (direct array vs vector)

---

### 2. Stack Frame / Call Frame

| Aspect | Dalvik (AOSP) | MiniAndroid (Current) | Gap Severity | Implementation Complexity |
|--------|---------------|----------------------|--------------|--------------------------|
| **Frame Layout** | `[args][locals][saved frame ptr][method ptr][return addr]` - tightly packed | Struct-based with named fields, not memory-layout compatible | 🔴 CRITICAL | HARD |
| **Return Address Handling** | Stored as pointer into bytecode array + saved PC | `uint32_t return_address = 0xFFFFFFFF` (placeholder) | 🟡 HIGH | MEDIUM |
| **Method\* Pointer Storage** | `const Method* method` - full method metadata | String-based: `class_name`, `method_name`, `method_descriptor` | 🔴 CRITICAL | HARD |
| **Frame Size Limits** | Limited by stack size (usually ~512KB for main thread) | No limit enforced; uses std::stack<StackFrame> | 🟡 HIGH | EASY |
| **Saved State** | Previous FP, return PC, saved result register, synchronization state | Only stores `caller_pc`, `return_value`, status enum | 🟡 HIGH | MEDIUM |
| **Exception Frame Linkage** | Linked list of exception frames for try/catch | Status enum has `EXCEPTION_PENDING` but no handler table | 🔴 CRITICAL | VERY_HARD |

#### Dalvik Reference (AOSP)
```c
// Simplified AOSP StackFrame
typedef struct StackFrame {
    u4* fp;                    // base of core frame
    const Method* method;      // method we're executing
    u4* returnAddr;            // to return to
    struct Frame* prev;        // previous frame (for exceptions)
    u2  currentPc;             // current program counter
    bool fromCode;             // came from compiled code?
    // ... more fields for JNI, precision, etc.
} Frame;
```

#### MiniAndroid Current (dalvik_engine.h:301-354)
```cpp
struct StackFrame {
    uint32_t frame_id;
    std::string class_name;
    std::string method_name;
    std::string method_descriptor;
    std::string source_file;
    
    uint32_t return_address = 0xFFFFFFFF;
    uint32_t caller_pc = 0;
    DalvikValue return_value;
    
    DexRegisterFile registers;
    
    uint32_t code_offset = 0;
    uint32_t bytecode_length = 0;
    uint32_t registers_size = 0;
    uint32_t ins_size = 0;
    uint32_t outs_size = 0;
    
    Clock::time_point enter_time;
    Clock::time_point exit_time;
    double duration_ms = 0;
    
    enum class Status { ACTIVE, RETURNED, EXCEPTION_PENDING, HALTED } status;
};
```

#### Gap Analysis
The StackFrame is a **significant gap area**:
- Uses string identifiers instead of Method pointers (prevents efficient dispatch)
- No exception frame linkage for try/catch blocks
- Missing JNI transition support
- Timing/debug fields are useful for research but add overhead

---

### 3. Heap Management

| Aspect | Dalvik (AOSP) | MiniAndroid (Current) | Gap Severity | Implementation Complexity |
|--------|---------------|----------------------|--------------|--------------------------|
| **Object Allocation** | `dvmMalloc()` with size class, alignment, heap limits | `DalvikHeap::allocate()` creates HeapObject in map | 🟡 HIGH | MEDIUM |
| **GC Integration** | Mark-sweep or concurrent GC; root scanning from stacks/registers | **No GC implementation** - objects never freed | 🔴 CRITICAL | VERY_HARD |
| **Object ID System** | Direct pointer (32/64-bit address) | Sequential `uint32_t object_id` starting at 1 | 🟢 MEDIUM | EASY |
| **Memory Layout** | Contiguous heap with bump allocation per thread | `std::map<uint32_t, HeapObject>` - scattered | 🟡 HIGH | HARD |
| **Allocation Tracking** | Allocation tracking for debugger/profiler | `allocation_log_` with JSON entries | 🟢 MEDIUM | DONE |
| **Large Object Space** | Separate space for arrays > 12KB | Not implemented | ⚪ LOW | MEDIUM |
| **Object Alignment** | 8-byte aligned (or 16-byte for some configs) | No alignment (map-based storage) | 🟡 HIGH | EASY |

#### Dalvik Reference (AOSP)
```c
// From vm/alloc/Alloc.h
struct Heap {
    HeapSource *heapSource;       // manages multiple heaps
    size_t maximumSize;           // -Xmx equivalent
    size_t startSize;             // -Xms equivalent
    size_t allocBytes;            // bytes allocated since GC
    size_t bytesAllocated;        // total bytes ever allocated
    Object *liveBits;             // mark bits for GC
    // ... GC structures, card table, etc.
};

Object* dvmMalloc(size_t size, int flags);
void dvmFreeObject(Object *obj);
```

#### MiniAndroid Current (dalvik_engine.h:422-480)
```cpp
class DalvikHeap {
    std::map<uint32_t, HeapObject> objects_;
    uint32_t next_id_ = 1;
    uint64_t alloc_sequence_ = 0;
    std::vector<json> allocation_log_;

public:
    uint32_t allocate(const std::string& class_desc, uint32_t pc, uint32_t frame_id);
    HeapObject* get(uint32_t id);
    void mark_initialized(uint32_t id);
    void bind_api_object(uint32_t id, std::shared_ptr<api::AndroidObject> api_obj);
};
```

#### Gap Analysis
Heap management is a **critical gap**:
- No garbage collection means memory leaks are guaranteed
- Map-based storage prevents pointer arithmetic on object fields
- No generational or concurrent collection support
- The sequential ID system works for debugging but isn't compatible with real DEX semantics

---

### 4. Object Header

| Aspect | Dalvik (AOSP) | MiniAndroid (Current) | Gap Severity | Implementation Complexity |
|--------|---------------|----------------------|--------------|--------------------------|
| **Header Fields** | `ClassObject* clazz`, lock word, monitor ID, hash code | `object_id`, `class_descriptor`, `readable_class`, `initialized` flag | 🔴 CRITICAL | HARD |
| **Header Size** | 8-16 bytes (depending on architecture/alignment) | ~100+ bytes (strings, maps, shared_ptr) | 🟡 HIGH | HARD |
| **ClassObject\* Placement** | First word of every object header | Stored as string `class_descriptor` | 🔴 CRITICAL | HARD |
| **Lock/Synchronization Word** | Thin lock (inline) or fat lock (monitor pointer) | **Not implemented** | 🔴 CRITICAL | VERY_HARD |
| **Hash Code Field** | Cached identity hash code (or derived from address) | Not implemented | ⚪ LOW | EASY |
| **Array Length** | For arrays: length field after header | No array type distinction | 🟡 HIGH | MEDIUM |

#### Dalvik Reference (AOSP)
```c
// From vm/oo/Object.h
struct Object {
    ClassObject* clazz;     // MUST be first field for casts
    Lock lock;              // thin/fat lock word
    
    /* Fields below depend on object type */
    /* Array: u4 length; then elements */
    /* Normal: instance fields from ClassObject.fieldOffsets */
};
// sizeof(Object) typically 8-16 bytes
```

#### MiniAndroid Current (dalvik_engine.h:360-420)
```cpp
struct HeapObject {
    uint32_t object_id = 0;
    std::string class_descriptor;      // Landroid/widget/TextView;
    std::string readable_class;        // android.widget.TextView
    
    bool initialized = false;
    uint64_t creation_sequence = 0;
    uint32_t creator_pc = 0;
    uint32_t creator_frame_id = 0;
    
    std::map<std::string, DalvikValue> fields;  // Name -> value
    std::shared_ptr<api::AndroidObject> api_object;  // Bridge to stubs
};
```

#### Gap Analysis
Object header is the **most critical structural gap**:
- Real Dalvik uses pointer-based headers enabling fast instanceof checks
- Synchronization primitives are completely missing
- String-based class lookup is O(n) instead of O(1) pointer dereference
- Field storage as map<string, value> is extremely inefficient vs offset-based

---

### 5. Class Metadata (ClassObject Equivalent)

| Aspect | Dalvik (AOSP) | MiniAndroid (Current) | Gap Severity | Implementation Complexity |
|--------|---------------|----------------------|--------------|--------------------------|
| **Field Table Organization** | `InstField* ifields[]` with precomputed offsets; `StaticField* sfields[]` | `std::map<std::string, FieldMetadata>` - name-keyed only | 🟡 HIGH | MEDIUM |
| **Method Table Organization** | `Method directMethods[]`, `Method virtualMethods[]` | `std::map<std::string, MethodMetadata>` - name-keyed only | 🟡 HIGH | MEDIUM |
| **Static Field Storage** | Inline in ClassObject after vtable | In `FieldMetadata` struct but no separate static storage | 🟡 HIGH | MEDIUM |
| **VTable Pointer** | `Method** vtable` - array of virtual method pointers | **Not implemented** | 🔴 CRITICAL | HARD |
| **Superclass Linkage** | `ClassObject* super` - direct parent pointer | `std::string parent_class_` - string name only | 🟡 HIGH | EASY |
| **Interface Table (iftable)** | `InterfaceEntry* iftable[]` for interface dispatch | **Not implemented** | 🔴 CRITICAL | HARD |
| **Virtual Method Count** | `int virtualMethodCount` for vtable sizing | No concept of virtual vs direct method count | 🟡 HIGH | MEDIUM |

#### Dalvik Reference (AOSP)
```c
// From vm/oo/Object.h (simplified)
struct ClassObject {
    Object obj;                        // First field IS-A Object
    ClassObject* super;                // superclass
    /* descriptor, loader, accessFlags... */
    
    // Field tables
    u4 ifieldCount;                    // # instance fields
    InstField* ifields;                // instance field descriptors + offsets
    u4 sfieldCount;                    // # static fields  
    StaticField* sfields;              // static field values (storage!)
    
    // Method tables
    u4 directMethodCount;
    Method* directMethods;             // <init>, private, static
    u4 virtualMethodCount;
    Method* virtualMethods;            // overridable methods
    
    // VTable
    int vtableCount;
    Method** vtable;                   // built during linking
    
    // Interface table
    int iftableCount;
    InterfaceEntry* iftable;           // {interfaceClass, method[]}
    
    // More: sourceFile, objectSize, refOffsets, ...
};
```

#### MiniAndroid Current (object_model.h:91-187)
```cpp
class ClassMetadata {
    std::string class_name_;
    std::string parent_class_;         // String, not pointer
    std::string descriptor_;
    
    std::map<std::string, MethodMetadata> methods_;
    std::vector<std::string> method_list_;
    
    std::map<std::string, FieldMetadata> fields_;
    std::vector<std::string> field_list_;
    
public:
    void add_method(const MethodMetadata& method);
    void add_field(const FieldMetadata& field);
    bool has_parent() const;
    bool is_derived_from(const std::string& base_class) const;
};
```

#### Gap Analysis
Class metadata is a **major gap area**:
- VTable is completely absent - this breaks polymorphism
- Interface table (iftable) means interface calls cannot work correctly
- Static field storage doesn't actually hold values
- String-based inheritance lookup prevents efficient type checking

---

### 6. Field Table

| Aspect | Dalvik (AOSP) | MiniAndroid (Current) | Gap Severity | Implementation Complexity |
|--------|---------------|----------------------|--------------|--------------------------|
| **Instance Fields (ifields)** | `InstField[]` with `byteOffset` precomputed at link time | `FieldMetadata` in map, no offsets | 🟡 HIGH | MEDIUM |
| **Static Fields (sfields)** | `StaticField[]` with actual value storage inline | Same map, marked `is_static=true` but no value storage | 🟡 HIGH | MEDIUM |
| **Field Offset Calculation** | Computed during class linking considering superclass layout | **Not computed** - fields accessed by name | 🔴 CRITICAL | HARD |
| **Access by Index** | `IFIELD_OFFSET(cls, idx)` macro - O(1) | Access by name via map lookup - O(log n) | 🟡 HIGH | MEDIUM |
| **Field Types** | Full type info: primitive width, reference kind | Type stored as descriptor string | 🟢 MEDIUM | EASY |
| **32/64-bit Alignment** | Long/double aligned to 8-byte boundary | No alignment consideration | 🟡 HIGH | EASY |

#### Dalvik Reference (AOSP)
```c
// Instance field descriptor
struct InstField {
    Field field;          // {name, signature, accessFlags}
    u4 byteOffset;        // Offset from object start (computed!)
};

// Static field with VALUE storage
struct StaticField {
    Field field;
    JValue value;         // Union holding actual field value
};

// Access macros
#define OBJECT_FIELD(obj, offset) (*(u4*)((u1*)(obj) + (offset)))
#define IFIELD_OFFSET(cls, idx) ((cls)->ifields[(idx)].byteOffset)
```

#### MiniAndroid Current (object_model.h:75-89)
```cpp
struct FieldMetadata {
    std::string name;
    std::string type;           // e.g., "Ljava/lang/String;", "I", "Z"
    bool is_static = false;
    bool is_public = true;
    
    json to_json() const;
};
// Note: No offset, no value storage, no width info
```

And in HeapObject (dalvik_engine.h:371):
```cpp
std::map<std::string, DalvikValue> fields;  // Runtime field storage
```

#### Gap Analysis
Field table gaps impact **performance and correctness**:
- Without precomputed offsets, iget/iput opcodes must do map lookups
- Static fields have no persistent storage across accesses
- Field alignment issues could cause problems on strict architectures
- No distinction between field declaration and field storage location

---

### 7. Method Table

| Aspect | Dalvik (AOSP) | MiniAndroid (Current) | Gap Severity | Implementation Complexity |
|--------|---------------|----------------------|--------------|--------------------------|
| **Direct Methods** | `<init>`, private methods, static constructors | Supported via `is_constructor`, `is_static` flags | 🟢 MEDIUM | DONE |
| **Virtual Methods** | Overridable methods in vtable | `is_virtual = true` flag but no vtable entry | 🟡 HIGH | MEDIUM |
| **Static Methods** | Marked ACC_STATIC, stored in directMethods | `is_static` flag exists | 🟢 MEDIUM | DONE |
| **Abstract/Native Markers** | ACC_ABSTRACT, ACC_NATIVE flags | **Not implemented** | 🟡 HIGH | EASY |
| **Code Item Pointers** | `const u2* insns` - pointer to DEX bytecode | No code item linkage (resolved at invoke time) | 🔴 CRITICAL | HARD |
| **Method Index** | Position in method[] array for quick opcodes | No indexing system | 🟡 HIGH | MEDIUM |
| **Method Size/Registers** | `registersSize`, `outsSize`, `insSize` from code_item | Stored in StackFrame, not in MethodMetadata | 🟡 HIGH | EASY |

#### Dalvik Reference (AOSP)
```c
struct Method {
    ClassObject* clazz;
    u4 accessFlags;
    u4 methodIndex;                  // index in class method array
    
    // Shorty & descriptor
    const char* shorty;              // prototype shortcut
    const DexMethodId* dexMethodId;  // DEX reference
    
    // Code
    const DexCode* dexCode;          // DEX code_item (registers, insns...)
    const u2* insns;                 // instruction array (cached ptr)
    
    // Arguments
    u4 registersSize;                // from code_item
    u4 outsSize;
    u4 insSize;
    
    // JNI (for native methods)
    void* nativeFunc;
    bool jniArgInfo;
};
```

#### MiniAndroid Current (object_model.h:57-73)
```cpp
struct MethodMetadata {
    std::string name;
    std::string descriptor;          // e.g., "(Ljava/lang/String;)V"
    bool is_constructor = false;
    bool is_virtual = true;
    bool is_static = false;
    
    json to_json() const;
};
```

#### Gap Analysis
Method table is **incomplete for execution**:
- No linkage between MethodMetadata and actual bytecode
- Cannot execute methods without external resolution
- Abstract/native markers needed for proper method handling
- Missing register size info prevents proper frame setup

---

### 8. Virtual Dispatch

| Aspect | Dalvik (AOSP) | MiniAndroid (Current) | Gap Severity | Implementation Complexity |
|--------|---------------|----------------------|--------------|--------------------------|
| **VTable Construction Algorithm** | Build during class linking: copy parent vtable, override/add new | **Not implemented** | 🔴 CRITICAL | HARD |
| **Method Resolution Order** | C3 linearization or depth-first (Java spec) | Simple string comparison | 🔴 CRITICAL | HARD |
| **Interface Dispatch (iftable)** | Two-level: find interface entry, then method index within | Falls back to API bridge stub | 🔴 CRITICAL | VERY_HARD |
| **invoke-super Handling** | Use caller's class vtable, not object's actual class | Treated same as invoke-direct | 🟡 HIGH | MEDIUM |
| **Quick Opcode Caching** | Method indices cached after first resolution | No caching | ⚪ LOW | MEDIUM |
| **Conflict Resolution** | Ambiguous interface methods → IncompatibleClassChangeError | Not detected | 🟡 HIGH | HARD |

#### Dalvik Reference (AOSP)
```c
// VTable construction (simplified)
void dvmLinkClass(ClassObject* clazz) {
    if (clazz->super) {
        // Copy parent's vtable
        memcpy(vtable, clazz->super->vtable, 
               clazz->super->vtableCount * sizeof(Method*));
        vtableCount = clazz->super->vtableCount;
    }
    
    // Override with our virtual methods
    for (int i = 0; i < clazz->virtualMethodCount; i++) {
        Method* method = &clazz->virtualMethods[i];
        int vtableIndex = findOverrideIndex(clazz, method);
        if (vtableIndex >= 0) {
            vtable[vtableIndex] = method;  // Override
        } else {
            vtable[vtableCount++] = method;  // Add new
        }
    }
}

// Virtual dispatch
static inline Method* dvmFindVirtualMethod(Object* obj, u4 methodIdx) {
    return obj->clazz->vtable[methodIdx];
}
```

#### MiniAndroid Current (dalvik_engine.cpp:843-908)
```cpp
bool DalvikExecutionEngine::execute_invoke_virtual(uint32_t pc, InstructionTrace& trace,
                                                   DalvikExecutionResult& result) {
    // Parse 35c format...
    uint16_t method_idx = bytecode_[pc + 2];
    
    // NO VTABLE LOOKUP - simplified resolution
    std::string method_name = "<method:" + std::to_string(method_idx) + ">";
    std::string class_name = "<unknown>";
    
    if (dex_report_ && method_idx < dex_report_->methods_count) {
        method_name = "invoke_virtual_" + std::to_string(method_idx);
    }
    
    // Fall through to API bridge
    bridge_to_api(class_name, method_name, args, return_val, api_status);
}
```

#### Gap Analysis
Virtual dispatch is **the most critical missing piece**:
- Without VTable, polymorphic calls cannot work correctly
- Interface dispatch is completely non-functional
- invoke-super semantics are wrong
- This single gap makes most real Android apps impossible to run

---

### 9. Interpreter Loop

| Aspect | Dalvik (AOSP) | MiniAndroid (Current) | Gap Severity | Implementation Complexity |
|--------|---------------|----------------------|--------------|--------------------------|
| **Fetch-Decode-Execute Cycle** | Standard: fetch opcode, decode operands, execute, advance PC | Implemented correctly | ⚪ LOW | DONE |
| **Opcode Dispatch Mechanism** | Computed goto (GCC extension) or switch with labels | `switch(opcode)` statement | 🟢 MEDIUM | DONE |
| **Trace Generation Hooks** | Optional instrumentation via interpreter entry points | `InstructionTrace` generated each cycle | 🟢 MEDIUM | DONE (better than AOSP!) |
| **Exception Handling Integration** | Check pending exception after each instruction | Status enum exists but no exception propagation | 🔴 CRITICAL | HARD |
| **Return Value Handling** | Special `RESULT_REGISTER` (pseudoregister) | `DalvikValue return_value` in StackFrame | 🟢 MEDIUM | DONE |
| **Debugger Support** | Event hooks for step/breakpoint/watch | JSON trace output (good for post-mortem) | 🟢 MEDIUM | EASY |
| **Profile Counter** | Optional instruction counting for JIT hints | `instruction_sequence_` counter | ⚪ LOW | DONE |

#### Dalvik Reference (AOSP)
```c
// From mterp/out/InterpC-allstubs.c (simplified)
void dvmInterpret(Thread* self, const Method* method, JValue* pResult) {
    const u2* pc = method->insns;
    u4* fp = (u4*)self->curFrame;
    u2 inst;
    
    DEFINE_GOTO_TABLE(handlerTable);
    
    while (true) {
        inst = FETCH(0);
        GOTO_OPCODE(inst);  // Computed goto dispatch
        
        HANDLE_OPCODE(OP_CONST_4) (...);
        HANDLE_OPCODE(OP_INVOKE_VIRTUAL) (...);
        // ... 200+ opcodes
        HANDLE_OPCODE(OP_RETURN_VOID) (...);
    }
}
```

#### MiniAndroid Current (dalvik_engine.cpp:369-480)
```cpp
bool DalvikExecutionEngine::fetch_decode_execute(DalvikExecutionResult& result) {
    while (!halted_ && pc_ < bytecode_.size()) {
        InstructionTrace trace;
        trace.sequence = instruction_sequence_++;
        trace.pc_before = pc_;
        
        auto start = Clock::now();
        
        // Fetch opcode
        uint16_t opcode = fetch_opcode(pc_);
        
        // Capture register state before
        if (current_registers_) {
            trace.registers_before = current_registers_->get_snapshot();
        }
        
        // Decode and execute via switch
        switch (opcode) {
            case Opcode::CONST_4:
                success = execute_const_4(pc_, trace);
                break;
            case Opcode::INVOKE_VIRTUAL:
                success = execute_invoke_virtual(pc_, trace, result);
                break;
            // ... ~20 opcodes implemented
        }
        
        // Record trace
        result.instruction_traces.push_back(trace);
    }
}
```

#### Gap Analysis
Interpreter loop is **surprisingly complete**:
- Core FDE cycle works correctly
- Good tracing infrastructure (better than stock AOSP for debugging)
- Main gaps: exception handling and incomplete opcode coverage (~20 of 200+)

---

### 10. Type System

| Aspect | Dalvik (AOSP) | MiniAndroid (Current) | Gap Severity | Implementation Complexity |
|--------|---------------|----------------------|--------------|--------------------------|
| **Primitive Types (ZBCSIJFD)** | Z=boolean, B=byte, C=char, S=short, I=int, J=long, F=float, D=double | All supported via `DalvikType` enum | 🟢 MEDIUM | DONE |
| **Reference Types (L-type)** | Lclassname; descriptor format | `OBJECT_REF`, `STRING_REF`, `CLASS_REF`, `NULL_REF` | 🟢 MEDIUM | DONE |
| **Array Types** | [I, [Ljava/lang/Object;, multi-dimensional | **Not implemented as distinct type** | 🟡 HIGH | MEDIUM |
| **Void Type** | V for return types only | `DalvikType::VOID_` exists | ⚪ LOW | DONE |
| **Wide Value Handling** | long/double use 2 consecutive registers (vN, vN+1) | INT64/FLOAT64 types exist but no pair enforcement | 🟡 HIGH | MEDIUM |
| **Type Checking** | `instanceof` opcode uses class hierarchy | Basic string comparison in `is_instance_of()` | 🟡 HIGH | MEDIUM |
| **Type Conversion** | i2l, l2f, f2d, etc. opcodes with precision rules | Some conversions may be missing | 🟡 HIGH | EASY |

#### Dalvik Reference (AOSP)
```c
// Primitive type widths
enum {
    PRIM_WIDTH_BOOLEAN = 1,
    PRIM_WIDTH_BYTE    = 1,
    PRIM_WIDTH_SHORT   = 2,
    PRIM_WIDTH_CHAR    = 2,
    PRIM_WIDTH_INT     = 4,
    PRIM_WIDTH_LONG    = 8,
    PRIM_WIDTH_FLOAT   = 4,
    PRIM_WIDTH_DOUBLE  = 8,
    PRIM_WIDTH_VOID    = 0,
    PRIM_WIDTH_OBJECT  = 4,  // reference = 4 bytes
};

// Wide type check
#define WIDE_TYPE(type) ((type) == PRIM_LONG || (type) == PRIM_DOUBLE)
```

#### MiniAndroid Current (dalvik_engine.h:103-200)
```cpp
enum class DalvikType {
    UNINITIALIZED,
    INT32,           // 4 bytes
    INT64,           // 8 bytes (wide)
    FLOAT32,         // 4 bytes
    FLOAT64,         // 8 bytes (wide)
    STRING_REF,
    CLASS_REF,
    OBJECT_REF,
    NULL_REF,
    BOOLEAN,         // 1 byte
    BYTE,            // 1 byte
    SHORT,           // 2 bytes
    CHAR,            // 2 bytes
    VOID_,
    REGISTER_UNSET
};

struct DalvikValue {
    DalvikType type = DalvikType::REGISTER_UNSET;
    union {
        int32_t int_val = 0;
        int64_t long_val;
        float float_val;
        double double_val;
        bool bool_val;
        int8_t byte_val;
        int16_t short_val;
        char char_val;
    };
    std::string string_val;
    std::string class_desc;
    uint32_t object_id = 0;
    uint32_t ref_id = 0;
    bool is_null = false;
};
```

#### Gap Analysis
Type system is **well-implemented**:
- All primitive types present with correct sizes
- Union-based value storage is correct approach
- Main gaps: array types and wide register pair enforcement

---

## Summary Statistics

### Gap Severity Distribution

```
CRITICAL (🔴) ████████████████████  40%  (4 components)
HIGH     (🟡) ██████████████████    40%  (4 components)
MEDIUM   (🟢) ██████████            20%  (2 components)
LOW      (⚪)                       0%   (0 components)
```

### Complexity Distribution

```
VERY_HARD ████                     15%  (2 items)
HARD      ██████████████           38%  (5 items)
MEDIUM    ██████████████████       46%  (6 items)
EASY      ██                        8%  (1 item)
```

### Components Ranked by Priority

| Priority | Component | Gap | Reason |
|----------|-----------|-----|--------|
| **1** | Virtual Dispatch (VTable) | 🔴 CRITICAL | Blocks all polymorphism |
| **2** | Object Header | 🔴 CRITICAL | Blocks fast type checks, sync |
| **3** | Exception Handling | 🔴 CRITICAL | Blocks try/catch/finally |
| **4** | Garbage Collection | 🔴 CRITICAL | Memory leaks inevitable |
| **5** | Class Metadata (iftable) | 🔴 CRITICAL | Blocks interface calls |
| **6** | Field Offsets | 🟡 HIGH | Performance, correctness |
| **7** | Method Code Linkage | 🟡 HIGH | Required for execution |
| **8** | Stack Frame Structure | 🟡 HIGH | Compatibility, performance |
| **9** | Heap Memory Layout | 🟡 HIGH | Performance |
| **10** | Wide Register Pairs | 🟡 HIGH | Correctness for long/double |

---

## Recommended Implementation Order

### Phase 1: Foundation (Weeks 1-4)
These changes enable everything else:

1. **Redesign Object Header** - Add ClassObject*, lock word
2. **Implement Field Offset Calculation** - Precompute at class load
3. **Add VTable Construction** - Copy-parent + override algorithm

### Phase 2: Execution (Weeks 5-8)
These make programs actually runnable:

4. **Link Methods to Bytecode** - Code items in MethodMetadata
5. **Implement invoke-virtual via VTable** - Real polymorphism
6. **Add Basic Exception Handling** - Try/catch frame chains

### Phase 3: Robustness (Weeks 9-12)
These make it production-quality:

7. **Interface Table (iftable)** - Full interface support
8. **Simple Mark-Sweep GC** - Even basic collection helps
9. **Contiguous Heap Layout** - Better cache behavior

### Phase 4: Polish (Ongoing)
10. **Wide Register Enforcement** - Catch bugs early
11. **Computed Goto Dispatch** - If GCC available
12. **JIT Hints / Profiling** - Future optimization path

---

## Appendix A: Opcode Coverage

| Category | AOSP Count | MiniAndroid Count | Coverage |
|----------|------------|-------------------|----------|
| Constants | 18 | 6 | 33% |
| Moves | 14 | 4 | 29% |
| Returns | 13 | 3 | 23% |
| Invokes | 7 | 4 | 57% |
| Fields | 28 | 0 | 0% |
| Objects | 17 | 3 | 18% |
| Arrays | 34 | 0 | 0% |
| Branches | 22 | 0 | 0% |
| Comparisons | 14 | 0 | 0% |
| Math | 42 | 0 | 0% |
| Casting | 6 | 2 | 33% |
| Synchronized | 4 | 0 | 0% |
| **Total** | **~220** | **~22** | **~10%** |

---

## Appendix B: File References

| Component | AOSP Source | MiniAndroid Source |
|-----------|-------------|-------------------|
| Register VM | `vm/interp/Stack.h` | `src/dex/dalvik_engine.h:202-255` |
| Stack Frame | `vm/interp/Stack.h` | `src/dex/dalvik_engine.h:301-354` |
| Heap | `vm/alloc/Alloc.h` | `src/dex/dalvik_engine.h:422-480` |
| Object Header | `vm/oo/Object.h` | `src/dex/dalvik_engine.h:360-420` |
| Class Metadata | `vm/oo/Class.h` | `src/runtime/object_model.h:91-187` |
| Field Table | `vm/oo/Class.h` | `src/runtime/object_model.h:75-89` |
| Method Table | `vm/oo/Class.h` | `src/runtime/object_model.h:57-73` |
| Virtual Dispatch | `vm/oo/Object.h` | `src/dex/dalvik_engine.cpp:843-908` |
| Interpreter Loop | `mterp/*` | `src/dex/dalvik_engine.cpp:369-480` |
| Type System | `vm/Common.h` | `src/dex/dalvik_engine.h:103-200` |

---

*Document generated for EXP-033 analysis. Based on MiniAndroid v0.2 source code review.*
