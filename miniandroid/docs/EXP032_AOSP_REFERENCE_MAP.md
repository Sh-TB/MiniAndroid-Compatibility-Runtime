# EXP-032: AOSP Reference-Driven MiniAndroid Acceleration

## AOSP Reference Map — Component Mapping & Implementation Priority

**Created**: 2026-08-14 (EXP-032 Phase 0)  
**Purpose**: Map every MiniAndroid component to its AOSP reference, identify gaps, prioritize implementation  
**Status**: RESEARCH COMPLETE — Ready for implementation phases

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [DEX Format Components](#1-dex-format-components)
3. [Dalvik Interpreter Components](#2-dalvik-interpreter-components)
4. [Runtime Object Model](#3-runtime-object-model)
5. [Android Framework Compatibility](#4-android-framework-compatibility)
6. [Execution Pipeline](#5-execution-pipeline)
7. [Missing Features Matrix](#6-missing-features-matrix)
8. [Implementation Priority Queue](#7-implementation-priority-queue)
9. [AOSP Source Locations Index](#8-aosp-source-locations-index)
10. [Golden Debug Rules for AOSP Integration](#9-golden-debug-rules-for-aosp-integration)

---

## Executive Summary

### Current State
MiniAndroid is a **research-grade C++17 Android APK execution runtime** with:
- ✅ Full DEX format parser (all versions 035-039)
- ✅ 25+ Dalvik opcodes implemented
- ✅ Register-based VM architecture (DalvikEngine)
- ✅ Basic Android framework stubs
- ❌ **Critical Gap**: Interpreter receives zero instructions from real DEX files

### Mission
Use **AOSP (Android Open Source Project)** as specification/test/debug reference to:
1. Validate DEX parsing against real-world DEX files
2. Verify opcode semantics match Dalvik behavior
3. Fix the code_item extraction pipeline break
4. Achieve real bytecode execution from real APKs

### Key Insight
We don't need to copy AOSP code. We need to use AOSP as:
- **Specification reference**: "How does Dalvik handle invoke-virtual?"
- **Behavior reference**: "What registers does const/4 modify?"
- **Test reference**: "Does our output match dexdump?"
- **Debugging reference**: "Where does AOSP's code_item extraction happen?"

---

## 1. DEX Format Components

### 1.1 DEX Header Parsing

| Field | MiniAndroid | AOSP Reference | Status | Notes |
|-------|-------------|----------------|--------|-------|
| `magic[8]` | `DexHeader.magic` | `art/libdexfile/dex/dex_file.h::Header` | ✅ Complete | All versions supported |
| `checksum` | `DexHeader.checksum` | Same + Adler32 verification | ✅ Complete | Verified |
| `signature[20]` | `DexHeader.signature` | SHA-1 hash | ✅ Complete | Verified |
| `file_size` | `DexHeader.file_size` | Size validation | ✅ Complete | |
| `header_size` | `DexHeader.header_size` | Fixed 0x70 | ✅ Complete | |
| `endian_tag` | `DexHeader.endian_tag` | 0x12345678 check | ✅ Complete | |
| `string_ids_size/off` | Parsed correctly | `string_ids_[]` array | ✅ Complete | |
| `type_ids_size/off` | Parsed correctly | `type_ids_[]` array | ✅ Complete | |
| `proto_ids_size/off` | Parsed correctly | `proto_ids_[]` array | ✅ Complete | |
| `field_ids_size/off` | Parsed correctly | `field_ids_[]` array | ✅ Complete | |
| `method_ids_size/off` | Parsed correctly | `method_ids_[]` array | ✅ Complete | |
| `class_defs_size/off` | Parsed correctly | `class_defs_[]` array | ✅ Complete | |
| `data_size/off` | Stored but not validated | Data section bounds | ⚠️ Partial | Could add validation |

**AOSP Source Location**:
```
art/libdexfile/dex/dex_file.h      // Header struct definition
art/libdexfile/dex/dex_file.cc     // Header parsing & validation
dalvik/libdex/DexFile.cpp          // Original Dalvik parser (legacy)
dalvik/libdex/DexProto.cpp         // Proto ID handling
```

**Missing Feature**: None critical. Header parsing is solid.

---

### 1.2 String Pool (string_ids)

| Aspect | MiniAndroid | AOSP Reference | Status | Priority |
|--------|-------------|----------------|--------|----------|
| MUTF-8 decoding | `read_mutf8_string()` | `DexFile::GetStringMUTF8()` | ✅ Working | - |
| String data offset resolution | `DexStringId.string_data_off` | `GetStringData()` | ✅ Working | - |
| ULEB128 length prefix | Handled in read | `ReadUnsignedLeb128()` | ✅ Working | - |
| Cache after first read | `strings_[]` vector | `StringsCache()` | ✅ Working | - |

**AOSP Source Location**:
```
art/libdexfile/dex/utf.h           // MUTF-8 utilities
art/libdexfile/dex/string_access.h // String data accessors
```

**Missing Feature**: None.

---

### 1.3 Type IDs (type_ids)

| Aspect | MiniAndroid | AOSP Reference | Status | Priority |
|--------|-------------|----------------|--------|----------|
| Descriptor indexing | `DexTypeId.descriptor_idx` | `GetTypeDescriptor()` | ✅ Working | - |
| Type name resolution | `get_type(index)` | `StringByTypeIdx()` | ✅ Working | - |
| Primitive type mapping | Implicit via descriptor | `kPrimitive...` constants | ⚠️ Implicit | Low |

**AOSP Source Location**:
```
art/libdexfile/dex/primitive.h     // Type constants
art/libdexfile/dex/type_list.h     // Type list iteration
```

---

### 1.4 Prototype IDs (proto_ids)

| Aspect | MiniAndroid | AOSP Reference | Status | Priority |
|--------|-------------|----------------|--------|----------|
| Shorty extraction | `DexProtoId.shorty_idx` | `GetShorty()` | ✅ Working | - |
| Return type | `DexProtoId.return_type_idx` | `GetReturnType()` | ✅ Working | - |
| Parameters list | `parse_descriptor_params()` | `ParameterIterator` | ✅ Working | - |
| TypeList offset | `parameters_off` handling | `GetParameterTypeList()` | ✅ Working | - |

**AOSP Source Location**:
```
art/libdexfile/dex/proto_accessor.h // Proto iteration
art/runtime/proto_primitives.h      // Proto utilities
```

---

### 1.5 Method IDs (method_ids)

| Aspect | MiniAndroid | AOSP Reference | Status | Priority |
|--------|-------------|----------------|--------|----------|
| Class index | `DexMethodId.class_idx` | `GetMethodDeclaringClass()` | ✅ Working | - |
| Name index | `DexMethodId.name_idx` | `GetMethodName()` | ✅ Working | - |
| Proto index | `DexMethodId.proto_idx` | `GetMethodPrototype()` | ✅ Working | - |
| Method signature building | Manual string concat | `PrettyMethod()` | ✅ Working | - |

**AOSP Source Location**:
```
art/libdexfile/dex/method_id.h      // Method ID struct
art/runtime/art_method.h            // ArtMethod (runtime representation)
```

---

### 1.6 Class Definitions (class_defs)

| Aspect | MiniAndroid | AOSP Reference | Status | Priority |
|--------|-------------|----------------|--------|----------|
| Class type index | `DexClassDef.class_idx` | `GetClassDescriptor()` | ✅ Working | - |
| Access flags | `DexClassDef.access_flags` | Bitmask validation | ✅ Working | - |
| Superclass | `DexClassDef.superclass_idx` | `GetSuperclass()` | ✅ Working | - |
| Interfaces | `interfaces_off` | `GetInterfacesList()` | ⚠️ Stored only | Medium |
| Source file | `source_file_idx` | `GetSourceFile()` | ✅ Working | - |
| **class_data_off** | **Stored but extraction broken** | **`GetClassData()`** | **❌ BROKEN** | **P0** |
| static_values_off | Not fully utilized | `GetStaticValues()` | ⚠️ Partial | Medium |

**⚠️ CRITICAL FINDING**: The `class_data_off` → class_data_item → code_item chain is where the pipeline breaks.

**AOSP Source Location**:
```
art/libdexfile/dex/class_accessor.h    // Class data iteration
art/runtime/class_linker.h             // Class linking & verification
dalvik/libdex/DexClassList.cpp         // Legacy class def parser
```

---

### 1.7 Class Data Item (THE CRITICAL PATH)

This is where **EXP-031.6 identified the break**.

| Aspect | MiniAndroid | AOSP Reference | Status | Priority |
|--------|-------------|----------------|--------|----------|
| ULEB128 header decoding | `parse_class_data()` | `ReadClassDataHead()` | ⚠️ Needs audit | **P0** |
| static_fields_size | Read but not validated | Cross-check with field_ids | ⚠️ Needs audit | **P0** |
| instance_fields_size | Read but not validated | Cross-check with field_ids | ⚠️ Needs audit | **P0** |
| direct_methods_size | Read but not validated | Key for constructors | ⚠️ Needs audit | **P0** |
| virtual_methods_size | Read but not validated | Key for overrides | ⚠️ Needs audit | **P0** |
| EncodedField parsing | `DexEncodedField` | `ClassDataItemIterator` | ⚠️ Needs audit | **P0** |
| **EncodedMethod.code_off** | **Read but NOT followed to code_item** | **`GetCodeItemOffset()`** | **❌ BROKEN** | **P0** |
| **code_item extraction** | **`parse_code_item()` exists but returns empty** | **`GetCodeItem()`** | **❌ BROKEN** | **P0** |
| **insns[] population** | **Empty vector in MethodInfo.bytecode** | **`insns_[]` array** | **❌ EMPTY** | **P0** |

**AOSP Source Location** (CRITICAL FOR DEBUGGING):
```
// PRIMARY REFERENCE - How AOSP extracts code_item:
art/libdexfile/dex/code_item_access.h   // Code item accessors
art/libdexfile/dex/invoke_type.h        // Invoke type resolution

// CLASS DATA ITERATION - How AOSP walks methods:
art/runtime/class_linker.cc             // LinkCode() method (~line 1500)
                                        // This is WHERE code_item gets attached to Method

// SPECIFIC FUNCTION TO STUDY:
void ClassLinker::LinkCode(ArtMethod* method, const void* quick_code, uint32_t method_size) {
    // This shows how code_item becomes executable
}

// CODE ITEM STRUCTURE VALIDATION:
art/compiler/dex/quick/dex_file_to_method_compiler.h  // Code item layout
external/dexdump/dexdump.c                            // dexdump output format
```

**ROOT CAUSE HYPOTHESIS** (from EXP-031.6):
```cpp
// In dex_parser.cpp, parse_class_data():
// The function reads EncodedMethod correctly BUT:
// 1. code_off is stored in MethodInfo.code_offset
// 2. parse_code_item(data, offset, method) is called
// 3. INSIDE parse_code_item(): something goes wrong
// 4. Result: method.bytecode is EMPTY (size == 0)
//
// NEEDS: Step-by-step comparison against AOSP's GetCodeItem()
```

---

### 1.8 Code Item Structure (THE TARGET)

| Field | MiniAndroid (`DexCodeItem`) | AOSP (`CodeItem`) | Status | Validation Needed |
|-------|----------------------------|-------------------|--------|-------------------|
| `registers_size` | uint16_t | uint16_t | ✅ Defined | Compare values |
| `ins_size` | uint16_t | uint16_t | ✅ Defined | Compare values |
| `outs_size` | uint16_t | uint16_t | ✅ Defined | Compare values |
| `tries_size` | uint16_t | uint16_t | ✅ Defined | Usually 0 for simple methods |
| `debug_info_off` | uint32_t | uint32_t | ✅ Defined | Skip for now |
| **`insns_size`** | **uint32_t** | **uint32_t** | **✅ Defined** | **MUST BE > 0** |
| **`insns[]`** | **vector<uint16_t>** | **uint16_t[]** | **❌ EMPTY** | **THIS IS THE BUG** |

**AOSP Code Item Layout** (from `art/libdexfile/dex/code_item_access.h`):
```cpp
struct CodeItem {
    uint16_t registers_size_;
    uint16_t ins_size_;
    uint16_t outs_size_;
    uint16_t tries_size_;
    uint32_t debug_info_off_;
    uint32_t insns_size_;          // In 2-byte code units
    uint16_t insns_[1];           // Variable-length instruction array
    // Followed optionally by: tries[], handler_list[]
};
```

**VALIDATION TEST**: For HelloWorld.dex `onCreate()`:
- Expected: `insns_size >= 4` (at minimum: iget, invoke-virtual, return-void)
- Actual (MiniAndroid): `insns_size = 0` or `bytecode.empty()`
- Action: Compare byte-by-byte against `dexdump -d HelloWorld.dex`

---

## 2. Dalvik Interpreter Components

### 2.1 Opcode Coverage Matrix

#### Constants Category (11 opcodes)

| Opcode | Hex | MiniAndroid | AOSP Behavior | Test Status | Priority |
|--------|-----|-------------|---------------|-------------|----------|
| `nop` | 0x00 | ✅ Implemented | No-op | ⚠️ Synthetic only | - |
| `const/4` | 0x12 | ✅ Implemented | vAA <- #+BBBB | ⚠️ Synthetic only | - |
| `const/16` | 0x13 | ✅ Implemented | vAA <- #+BBBBBBBB | ⚠️ Synthetic only | - |
| `const` | 0x14 | ✅ Implemented | vAA <- #+BBBBBBBB | ⚠️ Synthetic only | - |
| `const/high16` | 0x15 | ✅ Implemented | vAA <- #+BBBB0000 | ⚠️ Synthetic only | - |
| `const-wide` | 0x16 | ✅ Implemented | vAA:vAA+1 <- 64-bit | ⚠️ Synthetic only | - |
| `const-wide/16` | 0x17 | ✅ Implemented | Sign-extended 16-bit | ⚠️ Synthetic only | - |
| `const-wide/32` | 0x18 | ✅ Implemented | Sign-extended 32-bit | ⚠️ Synthetic only | - |
| `const-string` | 0x1a | ✅ Implemented | Resolve string ref | ⚠️ Synthetic only | - |
| `const-string/jumbo` | 0x1b | ✅ Implemented | Large string pool idx | ⚠️ Synthetic only | - |
| `const-class` | 0x1c | ✅ Implemented | Resolve class ref | ⚠️ Synthetic only | - |

**AOSP Reference**:
```
art/runtimeinterpreter.cc              // Main interpreter loop
art/runtimequick_entrypoints_cc       // Quick entry points
artcompilerdexlocal_optimizations.cc  // Constant folding
dalvikvminterpInterpC-portstd.cpp     // Original Dalvik C interpreter
dalvikvminterpInterpCppportstd.cpp    // C++ version
```

#### Move Category (11 opcodes)

| Opcode | Hex | MiniAndroid | AOSP Behavior | Test Status | Priority |
|--------|-----|-------------|---------------|-------------|----------|
| `move` | 0x01 | ✅ Implemented | vA <- vB | ⚠️ Synthetic only | - |
| `move/from16` | 0x02 | ✅ Implemented | vAA <- vBBBB | ⚠️ Synthetic only | - |
| `move/16` | 0x03 | ✅ Implemented | vAAAA <- vBBBB | ⚠️ Synthetic only | - |
| `move-wide` | 0x04 | ✅ Implemented | 64-bit move | ⚠️ Synthetic only | - |
| `move-object` | 0x05 | ✅ Implemented | Ref move | ⚠️ Synthetic only | - |
| `move-object/from16` | 0x06 | ✅ Implemented | Wide ref move | ⚠️ Synthetic only | - |
| `move-object/16` | 0x07 | ✅ Implemented | Full ref move | ⚠️ Synthetic only | - |
| `move-result` | 0x0a | ✅ Implemented | Return value -> vA | ⚠️ Synthetic only | - |
| `move-result-object` | 0x0b | ✅ Implemented | Ref return -> vA | ⚠️ Synthetic only | - |
| `move-result-wide` | 0x0c | ✅ Implemented | 64-bit return | ⚠️ Synthetic only | - |
| `move-exception` | 0x0d | ✅ Implemented | Exception -> vA | ⚠️ Synthetic only | - |

#### Return Category (4 opcodes)

| Opcode | Hex | MiniAndroid | AOSP Behavior | Test Status | Priority |
|--------|-----|-------------|---------------|-------------|----------|
| `return-void` | 0x0e | ✅ Implemented | Return no value | ⚠️ Synthetic only | - |
| `return` | 0x0f | ✅ Implemented | Return int vA | ⚠️ Synthetic only | - |
| `return-wide` | 0x10 | ✅ Implemented | Return 64-bit | ⚠️ Synthetic only | - |
| `return-object` | 0x11 | ✅ Implemented | Return ref vA | ⚠️ Synthetic only | - |

#### Invoke Category (5 opcodes)

| Opcode | Hex | MiniAndroid | AOSP Behavior | Test Status | Priority |
|--------|-----|-------------|---------------|-------------|----------|
| `invoke-virtual` | 0x6e | ✅ Implemented | Virtual dispatch | ⚠️ Synthetic only | HIGH |
| `invoke-super` | 0x6f | ✅ Implemented | Super call | ⚠️ Synthetic only | MEDIUM |
| `invoke-direct` | 0x70 | ✅ Implemented | Direct/constructor | ⚠️ Synthetic only | HIGH |
| `invoke-static` | 0x71 | ✅ Implemented | Static dispatch | ⚠️ Synthetic only | HIGH |
| `invoke-interface` | 0x72 | ✅ Implemented | Interface dispatch | ⚠️ Synthetic only | LOW |

**AOSP Invoke Resolution** (CRITICAL FOR REAL EXECUTION):
```
art/runtimeentrypoints_cc            // ArtMethod::Invoke()
artruntimeobject_lock.h             // Locking during invoke
artinterpreterenter_from_interpreter.cc  // Interpreter entry
artruntimeinterpreter_switch_impl.cc     // Implementation switch

// VTABLE LOOKUP (for invoke-virtual):
artruntimeart_field.h               // GcRoot mirror::Class*
artruntimeart_method.h              // vtable_[] array
artruntimeobject_array.h            // PointerArray for vtable
```

#### Control Flow Category (7 opcodes)

| Opcode | Hex | MiniAndroid | AOSP Behavior | Test Status | Priority |
|--------|-----|-------------|---------------|-------------|----------|
| `goto` | 0x28 | ✅ Implemented | Unconditional branch | ⚠️ Synthetic only | - |
| `goto/16` | 0x29 | ✅ Implemented | 16-bit offset | ⚠️ Synthetic only | - |
| `goto/32` | 0x2a | ✅ Implemented | 32-bit offset | ⚠️ Synthetic only | - |
| `if-eqz` | 0x38 | ✅ Implemented | Branch if vA == 0 | ⚠️ Synthetic only | - |
| `if-nez` | 0x39 | ✅ Implemented | Branch if vA != 0 | ⚠️ Synthetic only | - |
| `if-eq` | 0x39 | ✅ Implemented | Branch if vA == vB | ⚠️ Synthetic only | - |
| `if-ne` | 0x3a | ✅ Implemented | Branch if vA != vB | ⚠️ Synthetic only | - |

#### MISSING Critical Opcodes (P0 Blockers)

| Opcode | Hex | Purpose | Why Critical | AOSP Reference | Est. Complexity |
|--------|-----|---------|--------------|----------------|-----------------|
| `iget` | 0x52 | Instance field read | Activity.mContentParent | `iget_instance_field()` | Medium |
| `iget-wide` | 0x53 | 64-bit instance field | Bundle fields | Same | Medium |
| `iget-object` | 0x54 | Instance ref field | View references | Same | Medium |
| `iget-boolean` | 0x55 | Boolean field | Flags | Same | Easy |
| `iget-byte` | 0x56 | Byte field | Rarely used | Same | Easy |
| `iget-char` | 0x57 | Char field | Rarely used | Same | Easy |
| `iget-short` | 0x58 | Short field | Rarely used | Same | Easy |
| `iput` | 0x59 | Instance field write | Setting fields | `iput_instance_field()` | Medium |
| `iput-wide` | 0x5a | 64-bit field write | Bundle fields | Same | Medium |
| `iput-object` | 0x5b | Ref field write | View assignment | Same | Medium |
| `sget` | 0x60 | Static field read | Log.TAG, etc. | `sget_static_field()` | Medium |
| `sput` | 0x62 | Static field write | Static state | Same | Medium |
| `new-instance` | 0x22 | Allocate object | Activity(), View() | `AllocObject()` | High |
| `aget` | 0x44 | Array element read | Resource arrays | Easy | Easy |
| `aput` | 0x45 | Array element write | Rarely needed | Easy | Easy |
| `array-length` | 0x23 | Get array size | Validation | Easy | Easy |
| `filled-new-array` | 0x24 | Create filled array | Rare | Medium | Medium |
| `fill-array-data` | 0x26 | Fill from table | Switch/data tables | Medium | Medium |
| `if-lez` | 0x3d | Branch if <= 0 | Loops | Easy | Easy |
| `if-gtz` | 0x3e | Branch if > 0 | Loops | Easy | Easy |
| `if-ltz` | 0x3f | Branch if < 0 | Loops | Easy | Easy |
| `if-gez` | 0x40 | Branch if >= 0 | Loops | Easy | Easy |
| `packed-switch` | 0x2b | Dense switch | Try-catch | Medium | Hard |
| `sparse-switch` | 0x2c | Sparse switch | Try-catch | Medium | Hard |
| `cmpl-float` | 0x2d | Float compare | Comparisons | Easy | Easy |
| `cmpg-float` | 0x2e | Float compare (NaN) | Comparisons | Easy | Easy |
| `cmpl-double` | 0x2f | Double compare | Comparisons | Easy | Easy |
| `add-int/lit8` | 0xd0 | Add literal | Arithmetic | Easy | Easy |
| `sub-int/lit8` | 0xd1 | Subtract literal | Arithmetic | Easy | Easy |
| `mul-int/lit8` | 0xd2 | Multiply literal | Arithmetic | Easy | Easy |
| `div-int/lit8` | 0xd3 | Divide literal | Arithmetic | Easy | Easy |
| `rem-int/lit8` | 0xd4 | Remainder literal | Arithmetic | Easy | Easy |
| `and-int/lit8` | 0xd5 | AND literal | Bit ops | Easy | Easy |
| `or-int/lit8` | 0xd6 | OR literal | Bit ops | Easy | Easy |
| `xor-int/lit8` | 0xd7 | XOR literal | Bit ops | Easy | Easy |

**Total Missing**: ~35 opcodes (out of ~220 total Dalvik opcodes)  
**Coverage**: ~42 / 220 ≈ **19%** (up from previous estimate of 11%)

---

### 2.2 Register Machine Architecture

| Component | MiniAndroid | AOSP Equivalent | Status | Gap Analysis |
|-----------|-------------|-----------------|--------|--------------|
| Register file | `DexRegisterFile` | `ShadowFrame` or registers | ✅ Good | Missing wide register pairing |
| Value types | `DalvikValue` (15 types) | `JValue` union | ✅ Good | Missing NaN/Inf float handling |
| PC tracking | `uint32_t pc_` | `art::ArtMethod::DexInstructionIter` | ✅ Good | Need instruction width calculation |
| Call stack | `std::stack<StackFrame>` | `ManagedStack` | ✅ Good | Missing frame depth limits |
| Method context | `StackFrame` struct | `ShadowFrame` | ✅ Good | Missing line number tracking |
| Heap objects | `HeapObject` struct | `mirror::Object` | ⚠️ Basic | No GC, no compaction |
| Object references | `uint32_t object_id` | `GcRoot<mirror::Object>` | ⚠️ Basic | No weak refs, no soft refs |

**AOSP Reference**:
```
art/runtime/shadow_frame.h           // ShadowFrame (register frame)
art/runtimeframe.h                   // Stack frame layout
artruntimehandle_scope.h             // Handle scope (GC roots)
artruntimegc_root.h                  // Root types
artruntimemirrorobject.h            // mirror::Object hierarchy
```

---

## 3. Runtime Object Model

### 3.1 Android Object Representations

| Android Class | MiniAndroid Stub | AOSP Source | Methods Implemented | Methods Missing |
|---------------|------------------|-------------|---------------------|-----------------|
| `android.app.Activity` | `api::Activity` | frameworks/base/core/java/android/app/Activity.java | 11 (lifecycle + basic) | 50+ (intents, fragments, menus, etc.) |
| `android.os.Bundle` | `api::Bundle` | frameworks/base/core/java/android/os/Bundle.java | 8 (basic get/put) | 20+ (parcelable, typed arrays) |
| `android.content.Context` | `api::Context` | frameworks/base/core/java/android/content/Context.java | 3 (package, resources) | 30+ (content resolver, prefs, etc.) |
| `android.view.View` | `api::View` | frameworks/base/core/java/android/view/View.java | 8 (draw, measure, layout) | 100+ (touch, focus, animation, etc.) |
| `android.view.ViewGroup` | `api::ViewGroup` | frameworks/base/core/java/android/view/ViewGroup.java | 4 (add/remove child) | 50+ (layout params, touch dispatch) |
| `android.widget.TextView` | `api::TextView` | frameworks/base/core/java/android/widget/TextView.java | 5 (text, color, size) | 80+ (spans, auto-size, input) |
| `android.graphics.Canvas` | `api::Canvas` | frameworks/base/core/java/android/graphics/Canvas.java | 4 (color, text, rect) | 40+ (paths, bitmap, matrix) |
| `android.graphics.Paint` | `api::Paint` | frameworks/base/core/java/android/graphics/Paint.java | 5 (color, size, style) | 30+ (shader, mask filter, etc.) |

**Total API Surface**: ~48 methods implemented out of ~400+ in real Android (**~12% coverage**)

### 3.2 Object Model Improvements Needed (PHASE 4 Target)

| Feature | Current State | AOSP Reference | Priority | Effort |
|---------|---------------|----------------|----------|--------|
| **VTable** | Not implemented | `Class::vtable_[]` array | **P0** | High |
| **Interface ITable** | Not implemented | `Class::iftable_[]` | P1 | Medium |
| **Static field storage** | Not implemented | `Class::SFields_[]` | **P0** | Medium |
| **Instance field storage** | Basic map | `Object::fields_[]` | **P0** | Medium |
| **Superclass chain** | Single level | `Class::super_class_` | P1 | Low |
| **Method override resolution** | Not implemented | `VTable lookup` | **P0** | High |
| **Object identity** | Integer ID | `Monitor::IdentityHash()` | P2 | Low |
| **Type checking** | Name comparison | `Class::IsSubClass()` | P1 | Medium |

**AOSP Object Model Reference**:
```
art/runtime/mirror/class.h          // Class object layout
art/runtime/mirror/object.h         // Base object layout
art/runtime/mirror/method.h         // Method object
art/runtime/mirror/field.h          // Field object
art/runtime/object_utils.h          // Object utilities
art/runtime/class_linker.cc         // Class loading & linking
```

---

## 4. Android Framework Compatibility

### 4.1 API Frequency Analysis (from existing databases)

Based on `database/exp027_real_api_frequency.json`:

| Rank | API Call | Frequency | MiniAndroid Status | Priority |
|------|----------|-----------|-------------------|----------|
| 1 | `Activity.onCreate()` | 100% | ✅ Stub exists | P0 (already done) |
| 2 | `Activity.setContentView()` | 95% | ✅ Stub exists | P0 (already done) |
| 3 | `TextView.setText()` | 85% | ✅ Stub exists | P0 (already done) |
| 4 | `View.findViewById()` | 70% | ✅ Stub exists | P1 (needs ID resolution) |
| 5 | `Bundle.getString()` | 60% | ✅ Stub exists | P1 (needs intent integration) |
| 6 | `Log.d()/i()/w()/e()` | 55% | ❌ Not implemented | P1 (easy win) |
| 7 | `Resources.getString()` | 45% | ⚠️ Partial | P1 (R.class mapping) |
| 8 | `View.setOnClickListener()` | 40% | ❌ Not implemented | P2 (event system) |
| 9 | `Toast.makeText()` | 35% | ❌ Not implemented | P2 (UI feedback) |
| 10 | `Intent.putExtra()` | 30% | ❌ Not implemented | P2 (navigation) |

### 4.2 Android Manifest Handling

| Feature | MiniAndroid | AOSP Reference | Status | Priority |
|---------|-------------|----------------|--------|----------|
| Package name | Extracted | `PackageParser.parsePackage()` | ✅ Working | - |
| Activity declaration | Extracted | `PackageParser.parseActivity()` | ✅ Working | - |
| Intent filters | Basic | `IntentInfo` parsing | ⚠️ Partial | P2 |
| Permissions | Listed | `PermissionGroup` | ⚠️ Listed only | P3 |
| Uses-sdk | Min/target SDK | `UsesSdk` | ✅ Working | - |
| Application attributes | Basic | `ApplicationInfo` | ⚠️ Partial | P2 |

**AOSP Reference**:
```
frameworks/base/core/java/android/content/pm/PackageParser.java
frameworks/base/core/java/android/content/pm/PackageUserState.java
frameworks/base/core/java/android/content/pm/ApplicationInfo.java
frameworks/base/core/java/android/content/pm/ActivityInfo.java
```

---

## 5. Execution Pipeline

### 5.1 Pipeline Stage Mapping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MINIANDROID PIPELINE                                  │
├─────────────┬───────────────────────────────────┬───────────────────────────┤
│   Stage     │        MiniAndroid                │      AOSP Equivalent      │
├─────────────┼───────────────────────────────────┼───────────────────────────┤
│ 1. APK Load │ ApkParser::parse()                │ AssetManager::openApk()   │
│             │ ZIP extraction                    │ ZipFileRO                 │
├─────────────┼───────────────────────────────────┼───────────────────────────┤
│ 2. DEX Parse│ DexParser::parse()               │ OatFileAssistant::OpenDex │
│             │ Manual struct reading             │ DexFileLoader::Open()     │
├─────────────┼───────────────────────────────────┼───────────────────────────┤
│ 3. Class    │ ClassResolver::find_entry_point() │ ClassLinker::DefineClass │
│    Resolve  │ String matching                   │ DexCache lookups          │
├─────────────┼───────────────────────────────────┼───────────────────────────┤
│ 4. Code     │ parse_code_item() [BROKEN]        │ ClassLinker::LinkCode()   │
│    Extract  │ Returns empty bytecode             │ Links Dex to ArtMethod    │
├─────────────┼───────────────────────────────────┼───────────────────────────┤
│ 5. Execute  │ DalvikEngine::ExecuteMethod()     │ InterpretDexCmd()         │
│             │ Switch on opcode                  │ Thread::Current()->       │
│             │                                   │   GetInterpreterHandler() │
├─────────────┼───────────────────────────────────┼───────────────────────────┤
│ 6. Render   │ SoftwareRenderer::render()        │ SurfaceFlinger + HWComposer│
│             │ PPM pixel buffer                  │ GPU composition           │
└─────────────┴───────────────────────────────────┴───────────────────────────┘
```

### 5.2 THE BREAKING POINT (Stage 4)

```
STAGE 4 DETAIL — Where Pipeline Fails:

MiniAndroid Path:
  class_def → class_data_off → parse_class_data()
                                    ↓
                          EncodedMethod { method_idx_diff, access_flags, code_off }
                                    ↓
                          parse_code_item(data, code_off, method)
                                    ↓
                          [MYSTERIOUS FAILURE]
                                    ↓
                          method.bytecode = {}  ← EMPTY!

AOSP Path (for comparison):
  class_def → ClassAccessor → ClassDataItemIterator
                                    ↓
                          GetCodeItemOffset()
                                    ↓
                          GetCodeItem() → const CodeItem*
                                    ↓
                          insns_[], insns_size_ populated
                                    ↓
                          LinkCode(art_method, code_item, size)
                                    ↓
                          art_method->SetEntryPointFromInterpreter()
                                    ↓
                          READY FOR EXECUTION!
```

**DEBUGGING ACTION ITEMS**:
1. Log raw bytes at `code_off` offset before calling `parse_code_item()`
2. Compare byte layout against `dexdump -c` output
3. Verify ULEB128 decoding didn't corrupt position
4. Check if `code_off` is 0 (abstract/native method)
5. Validate `insns_size` is read as uint32_t (not truncated)

---

## 6. Missing Features Matrix

### 6.1 By Priority Level

#### P0 — Blocking Real Execution

| Feature | Component | AOSP Reference | Est. Effort | Dependency |
|---------|-----------|----------------|-------------|------------|
| **code_item extraction fix** | dex_parser | `GetCodeItem()` | 1-2 days | None |
| **iget/iput opcodes** | dalvik_engine | Field access handlers | 2-3 days | code_item fix |
| **sget/sput opcodes** | dalvik_engine | Static field handlers | 1-2 days | code_item fix |
| **new-instance opcode** | dalvik_engine | Object allocation | 2-3 days | Object model |
| **VTable implementation** | object_model | `Class::vtable_[]` | 3-4 days | None |
| **Instance field storage** | dalvik_heap | `Object::fields_[]` | 1-2 days | new-instance |
| **Static field storage** | class_info | `Class::SFields_[]` | 1 day | None |

#### P1 — Required for Real Apps

| Feature | Component | AOSP Reference | Est. Effort | Dependency |
|---------|-----------|----------------|-------------|------------|
| Array opcodes (aget/aput) | dalvik_engine | Array handlers | 1-2 days | None |
| invoke-virtual VTable lookup | dalvik_engine | Virtual dispatch | 2-3 days | VTable |
| Log.* API stubs | android_stubs | `android.util.Log` | 0.5 day | None |
| R.class resource mapping | resource_parser | R.java generation | 2-3 days | aapt tool |
| Exception handling (basic) | dalvik_engine | Try/catch blocks | 3-4 days | None |
| Interface dispatch | dalvik_engine | ITable lookup | 2-3 days | ITable |

#### P2 — Nice to Have

| Feature | Component | AOSP Reference | Est. Effort | Dependency |
|---------|-----------|----------------|-------------|------------|
| Event/touch system | api stubs | View.OnClickListener | 5-7 days | None |
| Intent navigation | api stubs | Activity.startActivity() | 3-5 days | None |
| Fragment support | api stubs | FragmentManager | 7-10 days | None |
| Multi-dex support | dex_parser | classes2.dex loading | 2-3 days | None |
| JNI bridge | runtime | JNIEnv functions | 10+ days | None |

#### P3 — Future Work

| Feature | Component | AOSP Reference | Est. Effort | Notes |
|---------|-----------|----------------|-------------|-------|
| Garbage Collector | runtime | ConcurrentCopying GC | 14+ days | Complex |
| JIT Compiler | compiler | JIT/Meta compiler | 21+ days | Very complex |
| Optimization passes | compiler | OptimizingCompiler | 14+ days | Complex |
| ProGuard support | tools | R8 shrinker | 7+ days | Tooling |
| Full ART compatibility | runtime | All of ART | 60+ days | Long-term goal |

---

## 7. Implementation Priority Queue

### Immediate (This Week)

```
┌─────────────────────────────────────────────────────────────────┐
│  QUEUE POSITION 1: FIX code_item EXTRACTION                     │
│  ─────────────────────────────────────────────────────────────  │
│  File: src/dex/dex_parser.cpp                                   │
│  Function: parse_code_item()                                    │
│  Task: Compare against AOSP GetCodeItem() byte-by-byte          │
│  Evidence: insns_size > 0, bytecode non-empty                   │
│  Test: HelloWorld.dex onCreate() must have instructions         │
│  AOSP Ref: art/libdexfile/dex/code_item_access.h               │
├─────────────────────────────────────────────────────────────────┤
│  QUEUE POSITION 2: IMPLEMENT iget/iput OPCODES                  │
│  ─────────────────────────────────────────────────────────────  │
│  File: src/dex/dalvik_engine.cpp                               │
│  Function: ExecuteInstruction() case statements                 │
│  Task: Add handlers for 0x52-0x58 (iget), 0x59-0x5b (iput)    │
│  Evidence: Field read/write in trace                           │
│  Test: Access Activity.mContentParent field                     │
│  AOSP Ref: art/runtime/entrypoints_quick_cc                    │
├─────────────────────────────────────────────────────────────────┤
│  QUEUE POSITION 3: IMPLEMENT sget/sput OPCODES                  │
│  ─────────────────────────────────────────────────────────────  │
│  File: src/dex/dalvik_engine.cpp                               │
│  Task: Add handlers for 0x60-0x62 (sget), 0x62-0x63 (sput)    │
│  Evidence: Static field access in trace                         │
│  Test: Read Log.TAG constant                                   │
│  AOSP Ref: art/runtime/entrypoints_quick_cc                    │
└─────────────────────────────────────────────────────────────────┘
```

### Short Term (Next 2 Weeks)

```
┌─────────────────────────────────────────────────────────────────┐
│  QUEUE POSITION 4: IMPLEMENT new-instance OPCODE                │
│  ─────────────────────────────────────────────────────────────  │
│  Task: Object allocation on heap                                │
│  Dependency: Object model improvements                          │
│  AOSP Ref: art/runtime/class_linker.cc AllocObject()           │
├─────────────────────────────────────────────────────────────────┤
│  QUEUE POSITION 5: BUILD VTABLE                                 │
│  ─────────────────────────────────────────────────────────────  │
│  Task: Virtual method dispatch table per class                  │
│  AOSP Ref: art/runtime/mirror/class.h vtable_[]                │
├─────────────────────────────────────────────────────────────────┤
│  QUEUE POSITION 6: REAL APK VALIDATION (PHASE 1)                │
│  ─────────────────────────────────────────────────────────────  │
│  Task: Test against 10+ real APKs                               │
│  Output: database/exp032_real_dex_validation.json              │
│  Evidence: Every test has PASS/FAIL with logs                   │
└─────────────────────────────────────────────────────────────────┘
```

### Medium Term (Next Month)

```
┌─────────────────────────────────────────────────────────────────┐
│  QUEUE POSITION 7: OPCODE COVERAGE COMPARISON (PHASE 2)         │
│  ─────────────────────────────────────────────────────────────  │
│  Output: database/opcode_coverage.json                         │
│  Task: Document each opcode vs AOSP behavior                   │
├─────────────────────────────────────────────────────────────────┤
│  QUEUE POSITION 8: REAL METHOD EXECUTION PROOF (PHASE 3)       │
│  ─────────────────────────────────────────────────────────────  │
│  Evidence: APK SHA256 → DEX SHA256 → Class → Method → PC →    │
│           Opcode → Registers Before → Registers After          │
├─────────────────────────────────────────────────────────────────┤
│  QUEUE POSITION 9: API COMPATIBILITY DATABASE (PHASE 5)         │
│  ─────────────────────────────────────────────────────────────  │
│  Task: Frequency-based priority for API implementation          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. AOSP Source Locations Index

### Primary References (Most Useful)

| Location | Purpose | URL (AOSP GitHub) |
|----------|---------|-------------------|
| `art/libdexfile/dex/` | DEX format definitions | `platform/art/libdexfile/dex/` |
| `art/libdexfile/dex/code_item_access.h` | **Code item extraction** | *CRITICAL* |
| `art/libdexfile/dex/class_accessor.h` | Class data iteration | *CRITICAL* |
| `art/runtime/class_linker.cc` | Class loading & linking | *CRITICAL* |
| `art/runtime/interpreter/` | Interpreter implementation | *HIGH PRIORITY* |
| `art/runtime/art_method.h` | Method representation | *HIGH PRIORITY* |
| `art/runtime/mirror/class.h` | Class object | *HIGH PRIORITY* |
| `art/runtime/mirror/object.h` | Base object | *MEDIUM* |

### Secondary References (Specific Topics)

| Topic | Location | Use Case |
|-------|----------|----------|
| Opcode semantics | `art/runtime/fixed_up_call.h` | Quick entry points |
| Invoke resolution | `art/runtime/entrypoints_cc` | Method invocation |
| Field access | `art/runtime/field_helper.h` | iget/iput behavior |
| Object allocation | `art/runtime/object_allocator.h` | new-instance |
| String handling | `art/runtime/string_allocation.h` | const-string |
| Array operations | `art/runtime/array_slice.h` | aget/aput |
| Exception handling | `art/runtime/exception_handler.h` | try/catch |
| Register machine | `art/runtime/shadow_frame.h` | Frame layout |
| Garbage collection | `art/runtime/gc/` | Future reference |

### Legacy Dalvik References (Historical)

| Location | Notes |
|----------|-------|
| `dalvik/vm/interp/` | Original C interpreter |
| `dalvik/vm/interp/InterpCpp-portstd.cpp` | C++ port |
| `dalvik/libdex/` | Original DEX parser |
| `dalvik/vm/Object.h` | Original object model |

### Tools for Validation

| Tool | Location | Purpose |
|------|----------|---------|
| `dexdump` | `system/dexdump/` | Disassemble DEX files |
| `dexlist` | `system/dexlist/` | List all methods |
| `oatdump` | `art/oatdump/` | Dump OAT/DEX combined |
| `hprofconv` | `cmdline/hprofconv/` | Heap analysis |
| `dmtracedump` | `tools/dmtracedump/` | Trace visualization |

---

## 9. Golden Debug Rules for AOSP Integration

### Rule 1: Never Assume — Always Verify

```
❌ BAD: "The code_item should be at this offset"
✅ GOOD: "Log raw bytes at offset, compare to dexdump output"

MANDATORY EVIDENCE:
- Raw hex dump at suspicious offsets
- Side-by-side comparison with dexdump
- Byte count matches expected structure size
```

### Rule 2: Search AOSP Before Implementing

```
Before writing any opcode handler:

1. Find AOSP implementation: grep -r "OP_IGET" art/runtime/
2. Read the handler logic completely
3. Note edge cases (null checks, type checks, exceptions)
4. Implement simplified version for MiniAndroid
5. Add comment: "// Based on AOSP art/runtime/entrypoints_quick_cc:1234"
```

### Rule 3: Every PASS Requires Evidence

```
❌ INVALID PASS:
  "Test passed" (no supporting data)

✅ VALID PASS:
  {
    "test": "code_item_extraction",
    "status": "PASS",
    "evidence": {
      "apk_sha256": "abc123...",
      "dex_sha256": "def456...",
      "class": "Lcom/example/MainActivity;",
      "method": "onCreate:(Landroid/os/Bundle;)V",
      "code_offset": "0x00000134",
      "insns_size": 12,
      "bytecode": [0x6e20, 0x0123, ...],
      "first_opcode": "invoke-super",
      "register_count": 5,
      "validation": "matches dexdump -d output"
    }
  }
```

### Rule 4: Classify Every Blocker

```
When stuck:

{
  "blocker_id": "BLOCKER-032-001",
  "description": "code_item extraction returns empty bytecode",
  "component": "dex_parser.cpp:parse_code_item()",
  "symptoms": ["insns_size == 0", "bytecode.empty()"],
  "hypothesis": "ULEB128 decoding corrupts file position",
  "aosp_reference": "art/libdexfile/dex/class_accessor.h:Line 87",
  "reproduction_steps": [
    "Parse HelloWorld.dex",
    "Find MainActivity class",
    "Extract onCreate() method",
    "Check method.bytecode.size()"
  ],
  "attempted_fixes": [],
  "next_action": "Add logging before/after ULEB128 decode"
}
```

### Rule 5: Prefer Proven Behavior Over Assumptions

```
Priority order for truth:

1. ✅ AOSP source code (what Google actually does)
2. ✅ dexdump output (what real DEX contains)
3. ✅ Real APK execution traces (what actually happens)
4. ⚠️ DEX format spec (theoretical - may have edge cases)
5. ❌ Our assumptions (unverified - dangerous)
6. ❌ ChatGPT/Copilot suggestions (may hallucinate)
```

### Rule 6: Minimal Reproduction Always

```
Before debugging complex issue:

1. Create minimal DEX with ONE method
2. That method has ONE instruction (e.g., return-void)
3. Parse that DEX
4. Does code_item extract correctly?

If YES: Issue is in complex interaction
If NO: Issue is in fundamental parsing

This saves hours of debugging time.
```

---

## Appendix A: Quick Reference Commands

### AOSP Code Search (online)

```bash
# Search AOSP source:
https://cs.android.com/?q=GetCodeItem+file:art

# Specific file:
https://cs.android.com/android/platform/superproject/main/+/main:art/libdexfile/dex/code_item_access.h

# Opcode handler search:
https://cs.android.com/?q=OP_IGET+art/runtime
```

### Local Validation Commands

```bash
# Disassemble HelloWorld.dex (requires Android SDK):
dexdump -d miniandroid/test_apks/classes.dex > /tmp/hello_world_disasm.txt

# Show headers:
dexdump -f miniandroid/test_apks/classes.dex

# Show all code items:
dexdump -c miniandroid/test_apks/classes.dex

# If dexdump unavailable, use our own parser with verbose:
./build/miniandroid --verbose --dex-only test_apks/classes.dex
```

### Testing Checklist

```bash
# After any code_item fix, verify ALL of these:

[ ] HelloWorld.dex parses without error
[ ] MainActivity class found
[ ] <init>() constructor extracted (may be empty for trivial ctor)
[ ] onCreate() method extracted
[ ] onCreate().insns_size > 0
[ ] onCreate().bytecode[0] != 0x0000 (not nop, unless really nop)
[ ] First opcode decodes to known instruction
[ ] Register count matches dexdump output
[ ] Instruction count matches dexdump output
```

---

## Appendix B: Glossary

| Term | Definition | AOSP Location |
|------|------------|---------------|
| **DEX** | Dalvik Executable format | `art/libdexfile/dex/dex_file.h` |
| **code_item** | Contains method bytecode | `art/libdexfile/dex/code_item_access.h` |
| **class_data_item** | Encoded class contents | `art/libdexfile/dex/class_accessor.h` |
| **insns[]** | Instruction array (2-byte units) | `CodeItem::insns_[]` |
| **VTable** | Virtual method dispatch table | `mirror::Class::vtable_[]` |
| **ITable** | Interface method table | `mirror::Class::iftable_[]` |
| **ShadowFrame** | Interpreter register frame | `art/runtime/shadow_frame.h` |
| **ArtMethod** | Runtime method representation | `art/runtime/art_method.h` |
| **DexCache** | Per-class DEX lookup cache | `art/runtime/dex_cache.h` |
| **OAT** | Compiled ELF format (ART) | `runtime/oat.h` |
| **Quick Code** | Compiled machine code | `ArtMethod::entrypoint_from_quick_compiled_code_` |

---

## Document Status

| Attribute | Value |
|-----------|-------|
| **Version** | 1.0 |
| **Created** | 2026-08-14 |
| **Experiment** | EXP-032 Phase 0 |
| **Author** | AI Agent (Super Z) |
| **Reviewer** | Pending human review |
| **Status** | ✅ COMPLETE — Ready for Phase 1 |
| **Next Action** | Begin DEX Parser Validation Against Real APKs |

---

*"Use AOSP as your north star, but build your own path."*
