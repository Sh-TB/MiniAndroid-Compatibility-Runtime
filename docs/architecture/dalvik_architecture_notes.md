# Dalvik Virtual Machine Architecture - Technical Research Notes

**Document:** EXP-033 Dalvik Architecture Research  
**Project:** MiniAndroid  
**Purpose:** Deep technical reference for Dalvik VM implementation

---

## Table of Contents

1. [Dalvik Bytecode Execution Model](#1-dalvik-bytecode-execution-model)
2. [Register Frame Model](#2-register-frame-model)
3. [Method Invocation Flow](#3-method-invocation-flow)
4. [Object Representation in Dalvik](#4-object-representation-in-dalvik)
5. [Field Resolution](#5-field-resolution)
6. [Virtual Dispatch Mechanism](#6-virtual-dispatch-mechanism)
7. [Key AOSP Source References](#7-key-aosp-source-references)

---

## 1. Dalvik Bytecode Execution Model

### 1.1 Register-Based Architecture Overview

Unlike the Java Virtual Machine (JVM) which uses a **stack-based** execution model, Dalvik employs a **register-based** virtual machine design. This fundamental architectural choice has significant implications for bytecode density and execution efficiency.

In a stack-based VM, operations implicitly pop operands from and push results to an operand stack:

```
JVM Stack-Based Example:
  iload_1       # Push local variable 1 to stack
  iload_2       # Push local variable 2 to stack  
  iadd          # Pop two values, add, push result
  istore_3      # Pop result to local variable 3
```

In contrast, Dalvik's register-based model explicitly names source and destination registers:

```
Dalvik Register-Based Equivalent:
  add-int v3, v1, v2   # v3 = v1 + v2 (explicit register naming)
```

This approach yields approximately **30% better code density** on average because register operands are encoded directly in instructions rather than requiring separate load/store operations.

### 1.2 Register Types: v-registers vs p-registers

Dalvik distinguishes between two conceptual views of the same physical register frame:

#### Virtual Registers (vNN)

Virtual registers are numbered from **v0** upward and represent the programmer-visible register namespace within a method. When examining DEX bytecode disassembly, you will always see v-register notation.

```
Example method with 5 registers:
  .registers 5
  
  const-string v0, "Hello"    # v0 = string reference
  const/4      v1, 5          # v1 = integer value 5
  move         v2, v0         # v2 = v0 (copy)
  # v3, v4 available for temporary use
```

#### Parameter Registers (pNN)

Parameter registers are an **aliasing view** into the upper portion of the register frame for non-static methods. They provide convenient access to method arguments:

- **p0** = `this` reference (for instance methods)
- **p1** = first explicit parameter
- **p2** = second explicit parameter
- etc.

The mapping formula is: `pN = v(registerCount - parameterCount + N)`

```
Method: void foo(int a, int b) with .registers 5
  
  Physical layout:  [v0] [v1] [v2] [v3] [v4]
                     ^    ^    ^
                     |    |    +-- p2 (= b, 2nd param)
                     |    +------- p1 (= a, 1st param)
                     +------------ p0 (= this)
  
  v0, v1 are "locals" - available for temporary computations
  v2/v3/v4 overlap with p0/p1/p2
```

For **static methods**, there is no `this` parameter, so mapping shifts:
- **p0** = first explicit parameter
- **p1** = second explicit parameter

### 1.3 Instruction Format Taxonomy

Dalvik defines multiple instruction formats optimized for different operand counts and sizes. Each format name encodes the number of code units (16-bit halfwords) it occupies.

| Format | Size (code units) | Description |
|--------|-------------------|-------------|
| **10x** | 1 | No operands (e.g., `return-void`) |
| **12x** | 1 | Two 4-bit register operands (e.g., `move vA, vB`) |
| **11n** | 1 | 4-bit reg + 4-bit signed literal (e.g., `const/4 vA, #+B`) |
| **11x** | 1 | Single 8-bit register (e.g., `move-result vAA`) |
| **10t** | 1 | 8-bit branch offset (e.g., `goto +AA`) |
| **20t** | 2 | 16-bit branch offset (e.g., `goto/16 +AAAA`) |
| **20bc** | 2 | 8-bit reg + 16-bit constant pool index |
| **22x** | 2 | Two 8-bit registers (e.g., `move/from16 vAA, vBBBB`) |
| **21s** | 2 | 8-bit reg + 16-bit signed literal (e.g., `const/16 vAA, #+BBBB`) |
| **21h** | 2 | 8-bit reg + high 16 bits of literal |
| **21c** | 2 | 8-bit reg + 16-bit constant index |
| **23x** | 2 | Three 8-bit registers (e.g., `cmpg-float vAA, vBB, vCC`) |
| **22b** | 2 | 8-bit reg + 8-bit reg + 8-bit lit |
| **22t** | 2 | Two 8-bit regs + 8-bit branch offset |
| **22s** | 2 | Two 8-bit regs + 16-bit signed lit (#BBBB) |
| **22c** | 2 | Two 8-bit regs + 16-bit constant index |
| **22cs** | 2 | Two 8-bit regs + 16-bit field offset |
| **30t** | 3 | 32-bit branch offset (e.g., `goto/32 +AAAAAAAA`) |
| **31i** | 3 | 8-bit reg + 32-bit literal (e.g., `const vAA, #+BBBBBBBB`) |
| **31c** | 3 | 8-bit reg + 32-bit constant index |
| **31t** | 3 | 8-bit reg + 32-bit branch target |
| **32x** | 3 | Two 16-bit registers (e.g., `move/16 vAAAA, vBBBB`) |
| **35c** | 3 | Method call: 5 regs + method index |
| **35ms** | 3 | Method call: 5 regs + vtable offset |
| **35mi** | 3 | Interface call: 5 regs + interface method index |
| **3rc** | 3 | Range method call: range + method index |
| **3rms** | 3 | Range method call: range + vtable offset |
| **3rmi** | 3 | Range interface call: range + interface index |
| **45cc** | 4 | invoke-object-init-range variant |
| **51l** | 5 | 8-bit reg + 64-bit literal (e.g., `const-wide vAA, #+BBBBBBBBBBBBBBBB`) |

### 1.4 Instruction Encoding Details

Each instruction occupies an integral number of **16-bit code units**. The opcode byte is always in the low 8 bits of the first code unit, with register identifiers typically packed into the remaining bits.

**Format 12x encoding (single code unit):**

```
Bit layout: [AAAA | BBBB | OOOO_OOOO]
            ^     ^     ^
            |     |     +-- Opcode (8 bits)
            |     +-------- Source/Dest register vB (4 bits)
            +-------------- Destination/Source register vA (4 bits)
```

**Format 35c encoding (invoke instruction):**

```
Code Unit 0: [ARGG | OOOO_OOOO]   G=arg count (4 bits), Opcode (8 bits)
Code Unit 1: [CCCC | CCCC | CCCC | CCCC]   Method reference index (16 bits)
Code Unit 2: [EEEE | DDDD | CCCC | BBBB]   Registers {D,C,B,A} (4 bits each)
```

The 35c format can specify up to 5 register arguments inline. For methods with more arguments, the **3rc (range)** format specifies a contiguous range of registers:

```
Format 3rc:
Code Unit 0: [AAAA | OOOO_OOOO]   A=arg count, Opcode
Code Unit 1: [CCCC | CCCC | CCCC | CCCC]   Method reference index  
Code Unit 2: [---- | ---- | BBBB | BBBB]   First register in range (16 bits)
```

### 1.5 Program Counter (PC) Advancement

The Program Counter tracks the current execution position within a method's bytecode array. Key characteristics:

- PC is measured in **16-bit code units**, not bytes
- Each instruction advances PC by its format-defined size (1-5 code units)
- Exception handler offsets are relative to PC at instruction start
- The PC can be read via the `move-exception` related mechanisms

```
PC Progression Example:
  
  Address  Instruction           Size   Next PC
  ------   -------------------   ----   -------
  0000:    const/4 v0, 5         1      0002
  0002:    add-int v1, v0, v0    1      0004
  0004:    const-string v2, ...  2      0006
  0006:    return-object v2      1      (end)
```

### 1.6 Endian Handling

DEX files use **little-endian** byte ordering throughout. This aligns with the dominant mobile processor architectures (ARM, x86):

- Multi-byte integers in class definitions: little-endian
- Instruction code units: little-endian
- Constant pool entries: little-endian
- String data: UTF-8 (byte-oriented, no endian concerns)

When running on big-endian architectures (rare for Android), the runtime must perform byte-swapping during DEX loading or during interpretation.

---

## 2. Register Frame Model

### 2.1 Overview of Method Frame Layout

Every executing method in Dalvik has an associated **register frame** (also called a "frame" or "activation record"). This frame contains all registers used by the method plus additional space for method invocation.

```
Complete Frame Structure:
+----------------------------------+
|          ins[] (in-regs)         |  <-- Parameters passed TO this method
|          (size = insSize)        |
+----------------------------------+
|         locals[]                 |  <-- Local variables + parameters (aliased)
|    (size = registers - insSize)  |
+----------------------------------+
|                                  |
|          outs[]                  |  <-- Space for args when THIS method calls another
|    (size = outsSize)             |
|                                  |
+----------------------------------+
```

### 2.2 The ins[] Region

The **ins[]** region holds incoming parameter values. For a non-static method with N word-sized parameters:

```
ins[0] = this reference (object pointer)
ins[1] = first method parameter
ins[2] = second method parameter
...
ins[N] = Nth method parameter
```

Long and double values occupy **two consecutive ins[] slots**. The ins[] region overlaps with the upper portion of the logical register space visible to the method.

**Frame initialization on method entry:**
1. Caller places arguments in ITS outs[] region
2. On method transfer, values are copied from caller's outs[] to callee's ins[]
3. The callee now accesses these as pN registers (which alias v-registers)

### 2.3 The locals[] Region

The **locals[]** region comprises the remainder of the method's declared registers that are not used for incoming parameters:

```
Total registers declared: R
Number of ins registers:  P
locals[] size:           R - P

Register mapping:
  locals[0] = v0
  locals[1] = v1
  ...
  locals[R-P-1] = v(R-P-1)
  ins[0] = v(R-P)      (= p0 for instance methods)
  ins[1] = v(R-P+1)    (= p1)
  ...
  ins[P-1] = v(R-1)    (= p(P-1))
```

### 2.4 The outs[] Region - Critical for Method Calls

The **outs[]** region is perhaps the most architecturally significant part of the Dalvik frame model. It provides pre-allocated space for passing arguments to methods invoked by the current method.

**Why outs[] exists:**
- Dalvik frames are allocated on a contiguous stack-like structure
- When method A calls method B, B's arguments must be placed somewhere accessible to B
- Rather than pushing arguments onto a separate stack, A writes to its own outs[] area
- On method transfer, the runtime uses A's outs[] as B's ins[] source

**Size calculation:**
```
outsSize = max(args required by any method this method invokes)
```

This is computed during DEX verification/optimization by analyzing all invoke instructions in the method.

### 2.5 Complete Frame Size Calculation

The total memory required for a method's frame:

```
frameSize = sizeof(FrameHeader) 
          + (registers * sizeof(u4))    // ins[] + locals[]
          + (outsSize * sizeof(u4))     // outs[] area
          + (optional method pointer)
          + (optional return PC/storage)
```

Where `u4` is an unsigned 32-bit value (all Dalvik registers hold 32-bit values; 64-bit long/double pairs occupy two consecutive registers).

### 2.6 Visual Example: Frame Setup During Invocation

Consider method `Foo.bar(int x)` calling `Helper.process(String s, int y)`:

```
BEFORE invoke (inside Foo.bar):
+--------------------------------------------------+
| Foo.bar's Frame                                   |
|                                                    |
| ins[]:  [this][x]              <- bar's params     |
| locals:[temp1][temp2]          <- bar's locals     |
| outs:   [s_ref][y_val][][...]  <- space for process|
+--------------------------------------------------+
           ^      ^
           |      +-- will become process's ins[1]
           +--------- will become process's ins[0]

AFTER invoke (inside Helper.process):
+--------------------------------------------------+
| Helper.process's Frame                            |
|                                                    |
| ins[]:  [s_ref][y_val]          <- copied from outs|
| locals: [local1][local2]...      <- process's locals|
| outs:   [][][][]...              <- for process's calls|
+--------------------------------------------------+
```

---

## 3. Method Invocation Flow

### 3.1 The Method* Structure

Before understanding invocation, we must understand what a "method" represents internally. The `Method` structure (conceptually defined) contains:

```
struct Method {
    ClassObject*     clazz;        // Class defining this method
    u4               accessFlags;  // PUBLIC, PRIVATE, STATIC, etc.
    u2               methodIndex;  // Index in class's method array
    u2               registersSize; // Frame register count
    u2               outsSize;     // outs[] size
    u2               insSize;      // Parameter word count
    
    // Code location
    const u2*        insns;        // Start of bytecode (in code units)
    u4               insnsSize;    // Bytecode length in code units
    
    // Resolution caches (populated at runtime)
    Method*          nativeFunc;   // For native methods
    u2               methodIndex;  // Index into vtable (if virtual)
};
```

### 3.2 invoke-virtual: Dynamic Dispatch

`invoke-virtual` is the most common invocation type, used for normal virtual method calls where the actual target depends on the runtime type of the object.

**Bytecode format (35c):**
```
invoke-virtual {vC, vD, vE, vF, vG}, method@BBBB
```

**Resolution algorithm:**

```
1. EXTRACT object reference from first register (vC, the "this")
2. VERIFY object != null (throw NullPointerException if null)
3. FETCH object->clazz (the object's actual ClassObject*)
4. LOOK UP method@BBBB in class's vtable using method index
5. The vtable entry contains the final Method* to execute
6. TRANSFER control to resolved method with argument registers
```

**VTable lookup detail:**
- The method reference encodes a **virtual method table index**
- Each class maintains a vtable inherited from parent + own virtual methods
- Overridden methods replace parent entries at the same index
- New methods append to the end

```
Class hierarchy example:

Object:
  vtable[0] = Object.hashCode()
  vtable[1] = Object.toString()
  vtable[2] = Object.equals()

MyClass extends Object, overrides toString():
  vtable[0] = Object.hashCode()        (inherited)
  vtable[1] = MyClass.toString()        (OVERRIDDEN)
  vtable[2] = Object.equals()           (inherited)
  vtable[3] = MyClass.newMethod()       (new virtual)
```

### 3.3 invoke-direct: Direct (Non-Virtual) Calls

`invoke-direct` is used for:
- **Constructor invocations** (`<init>` methods)
- **Private method calls** (methods with `private` access flag)
- Invocations where the target is known at compile time

**Key characteristic:** No vtable lookup occurs. The method is resolved against the **declared class** of the reference, not the runtime type of the object.

```
invoke-direct {vA, ...}, Constructor@BBBB

Resolution:
1. Extract this from vA
2. Verify non-null
3. Resolve method directly from referenced class (no vtable)
4. Verify access permissions (must be private or <init>)
5. Transfer control
```

**Security implication:** `invoke-direct` to `<init>` is the **only** valid way to construct objects. Calling `<init>` twice on the same object is verified as illegal.

### 3.4 invoke-static: Class Methods

`invoke-static` invokes methods that belong to a class rather than an instance. There is no `this` parameter.

**Bytecode format:**
```
invoke-static {vC, vD, ...}, method@BBBB
```

**Resolution:**
1. Resolve method reference to Method* via class's direct method table
2. Verify method has STATIC access flag
3. Transfer control (no null check needed - no this pointer)

**Static binding:** Static methods cannot be overridden (though they can be hidden), so resolution is straightforward.

### 3.5 invoke-super: Parent Class Dispatch

`invoke-super` is used to invoke the **parent class's** implementation of a virtual method, bypassing any override in the current class.

```
class Parent {
    void foo() { /* Parent implementation */ }
}

class Child extends Parent {
    void foo() {
        invoke-super Child.foo();  // Calls Parent.foo(), not Child.foo()
    }
}
```

**Resolution algorithm:**
1. Get current method's class (the class containing the invoke-super instruction)
2. Get that class's **parent** class
3. Look up the method in the **parent's** vtable
4. Invoke the parent's implementation

This is essential for proper inheritance patterns, especially when subclasses need to extend rather than fully replace superclass behavior.

### 3.6 invoke-interface: Interface Dispatch

Interface method dispatch is more complex than virtual dispatch because a class can implement multiple interfaces, and interface methods don't slot neatly into a single vtable.

**Bytecode format:**
```
invoke-interface {vC, vD, vE, vF, vG}, method@BBBB
```

**Resolution algorithm:**
1. Extract object from first register (this)
2. Verify non-null
3. Get object's actual class
4. Search class's **interface dispatch table (iftable/ifitern)**
5. Find matching interface method implementation
6. Invoke resolved method

**Interface table structure:**
Each class maintains an iftable mapping interface indices to actual method implementations:

```
struct InterfaceEntry {
    ClassObject*    interfaceClass;  // The interface being implemented
    Method**        methodTable;     // Array of method implementations
};
```

The search requires matching both the interface type AND the method index within that interface.

### 3.7 Return Value Handling

Return values are passed through a dedicated mechanism:

**Return instructions:**
- `return-void` - No return value
- `return vAA` - Return 32-bit value from register
- `return-wide vAA` - Return 64-bit value from register pair
- `return-object vAA` - Return object reference

**Return value transfer:**
1. Executing method places return value in special "result register"
2. Control returns to caller
3. Caller executes `move-result*` to copy result to its register

```
Caller:                          Callee:
  invoke-virtual {...}, foo       
  move-result v0       <---------- return-object vX
  ; v0 now holds result              
```

---

## 4. Object Representation in Dalvik

### 4.1 Object Header Layout

Every heap-allocated object in Dalvik begins with a standard header. Understanding this layout is crucial for garbage collection, synchronization, and type checking.

```
Object Memory Layout (simplified):
+---------------------------+
| ClassObject* clazz        |  (4 bytes) Pointer to object's class
| u4         lockword       |  (4 bytes) Monitor lock / GC state
+---------------------------+
| Instance field data...     |  (variable size)
| - Fields declared in this |
|   class, then super, etc. |
+---------------------------+
```

**Component details:**

**ClassObject* clazz:**
- Identifies the object's type at runtime
- Used for instanceof checks, virtual dispatch, field offset calculation
- Immutable after object creation
- Points to the class's ClassObject in the heap

**Lock word:**
- Multiple purposes depending on state:
  - Thin lock: Contains thread ID + recursion count (for uncontended locking)
  - Fat lock: Pointer to Monitor object (for contended/wait scenarios)
  - GC mark bit: Set during garbage collection tracing
  - Hash code: May cache System.identityHashCode()

### 4.2 Heap Allocation Process

Object allocation follows this sequence:

```
Allocation Algorithm:
1. CALCULATE size = sizeof(Object header) + total instance field size
2. ALLOCATE from heap (bump-pointer in TLAB or full heap alloc)
3. INITIALIZE header:
   - clazz = class pointer
   - lockword = 0 (unlocked, unmarked)
4. CONSTRUCT instance data:
   - Zero-initialize all fields (JLS guarantee)
   - If <init> exists, it will set meaningful values later
5. RETURN object reference (essentially a heap address + tag)
```

**TLAB (Thread-Local Allocation Buffer) optimization:**
- Each thread gets a small chunk of pre-allocated heap space
- Most allocations are just a pointer bump (extremely fast)
- Only need global synchronization when TLAB exhausts

### 4.3 Object References as 32-Bit Identifiers

In Dalvik, object references are **32-bit values** that serve as handles to heap objects:

```
Reference properties:
- Size: Always 32 bits (one register)
- Value: Typically direct pointer to object header
- Null: Represented as zero (0x00000000)
- Not subject to GC movement (or updated if copying collector)
```

**Note on ART vs Dalvik:** ART (Android Runtime) introduced compressed references (32-bit refs in 64-bit processes), but original Dalvik used plain pointers on 32-bit systems.

### 4.4 Array Object Representation

Arrays are objects with special internal structure:

```
ArrayObject Layout:
+---------------------------+
| ClassObject* clazz        |  -> Array class (e.g., "[I" for int[])
| u4         lockword       |   
+---------------------------+
| u4         length         |  Number of elements
+---------------------------+
| Element[0]                |  First element
| Element[1]                |  Second element
| ...                       |
| Element[length-1]         |  Last element
+---------------------------+
```

**Array class naming convention:**
- `[I` - int[]
- `[Ljava/lang/String;` - String[]
- `[[B` - byte[][]
- `[Z` - boolean[]

**Element storage:**
- Primitive arrays store values directly
- Object arrays store references (4 bytes each)
- Elements are contiguous in memory for cache efficiency

### 4.5 String Object Special Handling

Strings have unique representation due to their importance and immutability:

```
StringObject Layout:
+---------------------------+
| ClassObject* clazz        |  -> java/lang/String class
| u4         lockword       |
+---------------------------+
| u4         instanceData   |  (varies by implementation)
| ...                        |
+---------------------------+
| Object*    charArray      |  -> Internal char[] with actual characters
| u4         offset          |  Start position in charArray
| u4         count           |  Number of characters
| u4         hashCode        |  Cached hash (0 = not computed)
+---------------------------+
```

**Key characteristics:**
- **Immutable**: Once created, character content never changes
- **May share backing array**: Substrings can share parent's charArray with different offset/count
- **Interned strings**: Maintained in global string pool for deduplication
- **Hash caching**: identityHashCode computed once and stored

---

## 5. Field Resolution

### 5.1 Instance Fields vs Static Fields

Dalvik distinguishes between two categories of fields:

| Aspect | Instance Field (ifield) | Static Field (sfield) |
|--------|-------------------------|----------------------|
| Storage | Within each object | In ClassObject's static field area |
| Access | Requires object reference | Requires class reference |
| Lifetime | As long as object exists | As long as class is loaded |
| Bytecode | iget/iput | sget/sput |

### 5.2 Instance Field Access: iget/iput

**iget bytecode format (22c):**
```
iget vA, vB, field@CCCC

vA  = destination register (will receive field value)
vB  = object reference register (source object)
CCCC = field index in class's ifield table
```

**iput bytecode format (22c):**
```
iput vA, vB, field@CCCC

vA  = source register (value to store)
vB  = object reference register (target object)
CCCC = field index in class's ifield table
```

**Execution semantics:**
```
iget operation:
1. Load object reference from vB
2. Verify object != null (NullPointerException if null)
3. Resolve field@CCCC to InstField descriptor
4. Calculate offset: object_base + field_offset
5. Load value from calculated address
6. Store value in vA

iput operation:
1. Load object reference from vB
2. Verify object != null
3. Resolve field@CCCC to InstField descriptor
4. Calculate offset: object_base + field_offset
5. Load value from vA
6. Store value to calculated address
```

### 5.3 Static Field Access: sget/sput

**sget bytecode format (21c):**
```
sget vAA, field@BBBBBB

vAA   = destination register
BBBBBB = field index in class's sfield table (16-bit index)
```

**sput bytecode format (21c):**
```
sput vAA, field@BBBBBB

vAA   = source register
BBBBBB = field index
```

**Execution semantics:**
```
sget operation:
1. Resolve field@BBBBBB to StaticField descriptor
2. Locate static storage: field->field->clazz->sfields[field_index]
3. Load value from static field storage
4. Store in vAA

sput operation:
1. Resolve field@BBBBBB to StaticField descriptor
2. Locate static storage
3. Load value from vAA
4. Store to static field location
```

### 5.4 Field Offset Calculation

Field offsets are determined during class loading and linking:

```
Offset assignment algorithm (simplified):
1. START with offset = sizeof(Object header) (typically 8 bytes)
2. FOR each class in inheritance order (Object first, child last):
     a. FOR each declared instance field (in declaration order):
        - Assign current_offset to field
        - Advance offset by field_size (4 bytes for refs/int/float, 8 for long/double)
        - Insert padding for alignment if needed
3. RECORD final offset in InstField.byteOffset
```

**Memory layout example:**
```
class Parent {
    int x;      // offset 8
    double y;   // offset 16 (aligned to 8-byte boundary)
}

class Child extends Parent {
    int z;      // offset 24
    Object ref; // offset 28
}

Child object layout:
[+0]  ClassObject*
[+4]  lockword
[+8]  x (int)
[+16] y (double)
[+24] z (int)
[+28] ref (Object reference)
Total instance size: 32 bytes
```

### 5.5 InstField and StaticField Structures

**InstField (instance field descriptor):**
```
struct InstField {
    Field         field;        // Common field metadata (name, type, etc.)
    u4            byteOffset;   // Offset from object start
};
```

**StaticField (static field descriptor):**
```
struct StaticField {
    Field         field;        // Common field metadata  
    u4            value;        // Storage for the field's value (32-bit)
};
// For 64-bit fields (long/double), two StaticField slots are used
```

**Common Field structure:**
```
struct Field {
    ClassObject*  clazz;        // Declaring class
    const char*   name;         // Field name (UTF-8)
    ClassObject*  type;         // Field type class
    u4            accessFlags;  // PUBLIC, PROTECTED, FINAL, etc.
};
```

### 5.6 Field ID to Offset Mapping

The DEX file's field ID is a compound identifier:

```
FieldId in DEX:
struct FieldId {
    u2  classIdx;   // Index into type_ids for declaring class
    u2  typeIdx;    // Index into type_ids for field type
    u4  nameIdx;    // Index into string_ids for field name
};
```

**Resolution process (first access):**
1. Use field_id to look up declaring class, type, and name
2. Search class's ifield/sfield list for matching name+type
3. Cache resolved field pointer for subsequent accesses
4. Return cached result on future executions (fast path)

---

## 6. Virtual Dispatch Mechanism

### 6.1 VTable (Virtual Method Table) Concept

The VTable is central to Dalvik's polymorphic method dispatch. Every class maintains a vtable - an array of function pointers (Method*) for all virtual methods available to instances of that class.

```
VTable Properties:
- Inherited from parent class (with modifications)
- Entries ordered consistently across hierarchy
- Overridden methods REPLACE parent entries at same index
- New virtual methods APPEND to end
- Size grows monotonically down hierarchy
```

### 6.2 VTable Construction During Class Initialization

VTable construction occurs when a class is first loaded/linked:

```
BuildVTable(ClassObject* clazz):
1. IF clazz has superclass:
     a. Copy entire parent's vtable as starting point
     b. Set initial vtableCount = parent's vtableCount
   ELSE:
     a. Create empty vtable
     b. Set vtableCount = 0
   
2. FOR each virtual method declared in clazz:
     a. SEARCH existing vtable for method with same signature
     b. IF found (overriding parent method):
        - REPLACE vtable[index] with clazz's method
     ELSE (new virtual method):
        - APPEND to end of vtable
        - Increment vtableCount
        
3. STORE completed vtable in clazz->vtable
```

### 6.3 invoke-virtual Dispatch Algorithm (Detailed)

The complete dispatch process for `invoke-virtual`:

```
PSEUDOCODE for invoke-virtual {regs}, method@BBBB:

INPUT:
  - regs[]: Array of argument registers
  - methodRef: Reference to target method (encoded in instruction)

STEP 1: Extract 'this' pointer
  thisObject = regs[0]  // First register in invoke list
  
STEP 2: Null check
  IF thisObject == NULL:
      THROW NullPointerException
      RETURN
      
STEP 3: Get actual class
  actualClass = thisObject->clazz  // From object header
  
STEP 4: Resolve method reference to vtable index
  // This may involve:
  // - Looking up method in DEX method_id table
  // - Finding matching entry in vtable
  // - Caching the vtable index for future calls
  vtableIndex = resolveVirtualMethodIndex(methodRef, actualClass)
  
STEP 5: VTable lookup
  targetMethod = actualClass->vtable[vtableIndex]
  
STEP 6: Invoke
  CALL_METHOD(targetMethod, regs[], argCount)
```

### 6.4 Interface Dispatch Differences

Interface dispatch differs significantly from virtual dispatch:

**Challenge:** A class can implement multiple interfaces. An interface method doesn't have a fixed vtable index across all implementing classes.

**Solution: Interface Table (iftable)**

```
Interface Table Structure:
struct IfTable {
    InterfaceEntry entries[count];
};

struct InterfaceEntry {
    ClassObject*    interfaceClass;   // The interface
    Method**        methodArray;      // Implementation methods for this interface
};
```

**invoke-interface dispatch:**
```
1. Get thisObject from registers
2. Null check
3. Get actualClass = thisObject->clazz
4. Search iftable for entry matching target interface
5. Within that entry's methodArray, find method at interface method index
6. Call resolved method
```

**Performance note:** Interface dispatch is historically slower than virtual dispatch due to the two-level search (find interface, then find method). Some implementations cache recent interface dispatches.

### 6.5 Method Override Resolution

When a subclass overrides a superclass method:

```
class Animal {
    void makeSound() { /* generic */ }  // vtable[N]
}

class Cat extends Animal {
    @Override
    void makeSound() { /* meow */ }    // Replaces vtable[N]
}

class Dog extends Animal {
    @Override
    void makeSound() { /* woof */ }    // Replaces vtable[N]
}
```

**Dispatch behavior:**
```java
Animal a = new Cat();
a.makeSound();  // invoke-virtual -> Cat's vtable -> Cat.makeSound()

Animal b = new Dog();
b.makeSound();  // invoke-virtual -> Dog's vtable -> Dog.makeSound()
```

The vtable ensures correct override selection without conditional logic at each call site - the indirection through the object's class handle everything.

### 6.6 Final Methods and Devirtualization

Methods marked `final` cannot be overridden, enabling optimization:

```
class Optimizable {
    final int compute() { return 42; }
}

// Compiler/runtime MAY transform:
invoke-virtual {v0}, Optimizable.compute
// Into direct call (bond to exact method at compile/link time):
invoke-direct style dispatch to Optimizable.compute
```

**Benefits:**
- Eliminates vtable indirection
- Enables inlining
- Better branch prediction

---

## 7. Key AOSP Source References

### 7.1 Core Interpreter Files

| File | Purpose |
|------|---------|
| `dalvik/vm/Interp.c` | Main interpreter loop (portable C implementation) |
| `dalvik/vm/mterp/` | Architecture-specific assembly interpreters |
| `dalvik/vm/mterp/arm/` | ARM assembly interpreter (most common target) |
| `dalvik/vm/mterp/x86/` | x86 assembly interpreter |
| `dalvik/vm/mterp/out/` | Generated interpreter common code |

### 7.2 Object Model Files

| File | Purpose |
|------|---------|
| `dalvik/vm/oo/Object.h` | Core object/data structure definitions |
| `dalvik/vm/oo/oo.cpp` | Object allocation and manipulation |
| `dalvik/vm/oo/Class.h` | ClassObject structure definition |
| `dalvik/vm/oo/Class.cpp` | Class loading and initialization |

### 7.3 Resolution Files

| File | Purpose |
|------|---------|
| `dalvik/vm/Resolve.c` | Field and method resolution logic |
| `dalvik/vm/oo/Resolve.h` | Resolution API declarations |

### 7.4 Verification Files

| File | Purpose |
|------|---------|
| `dalvik/vm/Check.cpp` | Bytecode verification |
| `dalvik/vm/Verify.c` | DEX verification subsystem |

### 7.5 Key Structures to Study

```
// From Object.h (conceptual)
typedef struct Object {
    ClassObject*    clazz;
    u4              lock;
} Object;

// From Interp.c (conceptual)
typedef struct StackSaveArea {
    u4*             prevFrame;
    u4*             savedPc;
    Method*         method;
    u4              returnAddr;
} StackSaveArea;

// Execution state maintained per thread
typedef struct Thread {
    u4*             curFrame;      // Current method's frame base
    interpState     interpState;   // Interpreter registers
    // ...
} Thread;
```

---

## Appendix A: Quick Reference - Common Opcodes

### Data Movement
| Opcode | Format | Operation |
|--------|--------|-----------|
| `move` | 12x | vA = vB |
| `move/from16` | 22x | vAA = vBBBB |
| `move/16` | 32x | vAAAA = vBBBB |
| `move-wide` | 12x | vA:vA+1 = vB:vB+1 |
| `move-object` | 12x | vA = vB (reference) |
| `move-result` | 11x | vAA = last invoke return value |
| `move-result-object` | 11x | vAA = last invoke return (ref) |
| `move-result-wide` | 11x | vAA:vAA+1 = last invoke return (wide) |
| `move-exception` | 11x | vAA = pending exception |

### Constants
| Opcode | Format | Operation |
|--------|--------|-----------|
| `const/4` | 11n | vA = sign_extend(#literal4) |
| `const/16` | 21s | vA = sign_extend(#literal16) |
| `const` | 31i | vA = #literal32 |
| `const/high16` | 21h | vA = #literal16 << 16 |
| `const-wide/16` | 21s | vA:vA1 = sign_extend(#literal16) |
| `const-wide/32` | 31i | vA:vA1 = #literal32 |
| `const-wide` | 51l | vA:vA1 = #literal64 |
| `const-wide/high16` | 21h | vA:vA1 = #literal16 << 48 |
| `const-class` | 21c | vA = class_object_for(type) |
| `const-string` | 21c | vA = string_reference_for(id) |

### Invocation
| Opcode | Format | Operation |
|--------|--------|-----------|
| `invoke-virtual` | 35c/3rc | Call virtual method |
| `invoke-super` | 35c/3rc | Call superclass method |
| `invoke-direct` | 35c/3rc | Call private/<init> method |
| `invoke-static` | 35c/3rc | Call static method |
| `invoke-interface` | 35c/3rc | Call interface method |

### Field Access
| Opcode | Format | Operation |
|--------|--------|-----------|
| `iget` | 22c | vA = vB.field (32-bit) |
| `iget-wide` | 22c | vA:vA1 = vB.field (64-bit) |
| `iget-object` | 22c | vA = vB.field (ref) |
| `iget-boolean` | 22c | vA = vB.field (boolean) |
| `iget-byte` | 22c | vA = vB.field (byte) |
| `iget-char` | 22c | vA = vB.field (char) |
| `iget-short` | 22c | vA = vB.field (short) |
| `iput` | 22c | vB.field = vA (32-bit) |
| `iput-wide` | 22c | vB.field = vA:vA1 (64-bit) |
| `iput-object` | 22c | vB.field = vA (ref) |
| `sget` | 21c | vA = static_field (32-bit) |
| `sget-wide` | 21c | vA:vA1 = static_field (64-bit) |
| `sget-object` | 21c | vA = static_field (ref) |
| `sput` | 21c | static_field = vA (32-bit) |
| `sput-object` | 21c | static_field = vA (ref) |

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **DEX** | Dalvik Executable format - the compiled bytecode container |
| **Code Unit** | 16-bit unit used for measuring instruction sizes and PC positions |
| **VTable** | Virtual Method Table - array of method pointers for dynamic dispatch |
| **IFTable** | Interface Table - maps interfaces to their implementations |
| **Frame** | Activation record containing registers for a method invocation |
| **ins[]** | Input registers - method parameters within a frame |
| **locals[]** | Local variable registers within a frame |
| **outs[]** | Output registers - space for passing arguments to called methods |
| **ClassObject** | Runtime representation of a Java/Dalvik class |
| **Method*** | Pointer to a method's runtime structure |
| **Thin Lock** | Compact lock representation in object header (no contention) |
| **Fat Lock** | Full Monitor object for contended locks |
| **TLAB** | Thread-Local Allocation Buffer for fast object allocation |

---

*Document Version: 1.0*  
*Created for MiniAndroid EXP-033*  
*Technical Reference Only - Not Production Documentation*
