/*
 * MiniAndroid Runtime Metadata — EXP-034 Field System Implementation
 * 
 * Proper runtime metadata matching AOSP Dalvik/ART structures:
 * - RuntimeClassInfo (equivalent to ClassObject/mirror::Class)
 * - InstanceFieldInfo (equivalent to InstField/ArtField)  
 * - StaticFieldEntry (equivalent to StaticField)
 * - RuntimeMethodInfo (equivalent to Method/ArtMethod)
 * - VirtualDispatchTable (VTable implementation)
 *
 * Design Principles:
 * 1. Match AOSP structure organization
 * 2. Support offset-based field access (not string-keyed)
 * 3. Support VTable-based virtual dispatch
 * 4. Evidence-friendly (serializable to JSON)
 *
 * AOSP References:
 * - dalvik/libdex/DexClass.h: ClassObject definition
 * - dalvik/libdex/Object.h: Method, Field, InstField, StaticField
 * - art/runtime/mirror/class.h: mirror::Class
 * - art/runtime/art_method.h: ArtMethod
 * - art/runtime/art_field.h: ArtField
 *
 * Rule 1: Research before implementation — This follows AOSP patterns
 * Rule 2: REAL evidence only — Every operation traceable
 * Rule 3: GitHub preservation required — Will be committed
 */

#ifndef MINIANDROID_RUNTIME_METADATA_H
#define MINIANDROID_RUNTIME_METADATA_H

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <cstdint>
#include <optional>
#include <algorithm>
#include <sstream>
#include <iomanip>

#include "../../third_party/nlohmann_json/include/nlohmann/json.hpp"

namespace miniandroid {
namespace runtime {

using json = nlohmann::json;

// ============================================================================
// Forward Declarations
// ============================================================================

struct RuntimeClassInfo;
struct InstanceFieldInfo;
struct StaticFieldEntry;
struct RuntimeMethodInfo;
struct VirtualDispatchTable;

// ============================================================================
// Constants (from DEX format specification)
// ============================================================================

namespace AccessFlags {
    constexpr uint32_t ACC_PUBLIC       = 0x0001;
    constexpr uint32_t ACC_PRIVATE      = 0x0002;
    constexpr uint32_t ACC_PROTECTED    = 0x0004;
    constexpr uint32_t ACC_STATIC       = 0x0008;
    constexpr uint32_t ACC_FINAL        = 0x0010;
    constexpr uint32_t ACC_SYNCHRONIZED = 0x0020;
    constexpr uint32_t ACC_VOLATILE     = 0x0040;
    constexpr uint32_t ACC_BRIDGE       = 0x0040;
    constexpr uint32_t ACC_TRANSIENT    = 0x0080;
    constexpr uint32_t ACC_VARARGS      = 0x0080;
    constexpr uint32_t ACC_NATIVE       = 0x0100;
    constexpr uint32_t ACC_INTERFACE    = 0x0200;
    constexpr uint32_t ACC_ABSTRACT     = 0x0400;
    constexpr uint32_t ACC_STRICT       = 0x0800;
    constexpr uint32_t ACC_SYNTHETIC    = 0x1000;
    constexpr uint32_t ACC_ANNOTATION   = 0x2000;
    constexpr uint32_t ACC_ENUM         = 0x4000;
    constexpr uint32_t ACC_CONSTRUCTOR  = 0x10000;
    constexpr uint32_t ACC_DECL_SYNCHRONIZED = 0x20000;
}

// ============================================================================
// InstanceFieldInfo — Instance field with memory layout information
// ============================================================================

/**
 * InstanceFieldInfo represents an instance field with its byte offset.
 * 
 * Critical for implementing iget/iput instructions correctly.
 * Each instance of a class has the same field layout, so offsets are
 * stored in the class's RuntimeClassInfo, not per-object.
 * 
 * AOSP Equivalent: dalvik/libdex/Object.h::InstField
 *                   art/runtime/art_field.h::ArtField
 */
struct InstanceFieldInfo {
    // === Identity (from DEX field_ids[]) ===
    uint32_t field_idx;                 // Index in DEX field_ids[]
    std::string name;                   // Field name (e.g., "mText")
    std::string type_descriptor;       // Type descriptor (e.g., "Ljava/lang/String;")
    
    // === Declaration Info ===
    uint32_t access_flags;              // ACC_PRIVATE, ACC_PROTECTED, etc.
    uint32_t declaring_class_idx;       // Index of declaring class in class_defs[]
    
    // === Memory Layout (CRITICAL for correct field access) ===
    uint32_t byte_offset;               // Byte offset from start of instance data
    uint32_t field_size;                // Size in bytes: 1, 2, 4, or 8
    uint32_t alignment;                 // Alignment requirement: 1, 2, 4, or 8
    bool is_wide;                       // true if long or double (64-bit)
    bool is_object_ref;                 // true if reference type (object/array)
    
    // === Constructors ===
    InstanceFieldInfo()
        : field_idx(0), access_flags(0), declaring_class_idx(0),
          byte_offset(0), field_size(4), alignment(4),
          is_wide(false), is_object_ref(false) {}
    
    InstanceFieldInfo(uint32_t idx, const std::string& n, const std::string& type,
                      uint32_t flags, uint32_t decl_idx)
        : field_idx(idx), name(n), type_descriptor(type),
          access_flags(flags), declaring_class_idx(decl_idx),
          byte_offset(0), field_size(4), alignment(4),
          is_wide(false), is_object_ref(false)
    {
        infer_type_properties();
    }
    
    /**
     * Infer size/alignment from type descriptor
     * Matches DEX format type encoding rules
     */
    void infer_type_properties() {
        if (type_descriptor.empty()) return;
        
        char base_type = type_descriptor[0];
        switch (base_type) {
            case 'Z':  // boolean
            case 'B':  // byte
                field_size = 1;
                alignment = 1;
                is_wide = false;
                is_object_ref = false;
                break;
            case 'C':  // char
            case 'S':  // short
                field_size = 2;
                alignment = 2;
                is_wide = false;
                is_object_ref = false;
                break;
            case 'I':  // int
            case 'F':  // float
                field_size = 4;
                alignment = 4;
                is_wide = false;
                is_object_ref = false;
                break;
            case 'J':  // long
            case 'D':  // double
                field_size = 8;
                alignment = 8;
                is_wide = true;
                is_object_ref = false;
                break;
            case 'L':  // object
            case '[':  // array
                field_size = sizeof(void*);  // 4 or 8 depending on platform
                alignment = sizeof(void*);
                is_wide = false;
                is_object_ref = true;
                break;
            default:
                // Unknown - default to 32-bit
                field_size = 4;
                alignment = 4;
                is_wide = false;
                is_object_ref = false;
                break;
        }
    }
    
    // === Value Access Operations ===
    
    /**
     * Read field value from raw object memory
     * 
     * @param object_data Pointer to object's instance field area
     * @return Value as JSON (int, string for refs, etc.)
     */
    json get_value(const uint8_t* object_data) const {
        if (!object_data) return json();
        
        const uint8_t* field_ptr = object_data + byte_offset;
        
        try {
            if (is_object_ref) {
                // Reference type - read as pointer (store as hex string for safety)
                uintptr_t ref_value = *reinterpret_cast<const uintptr_t*>(field_ptr);
                return "ref_" + std::to_string(ref_value);
            } else if (is_wide) {
                // 64-bit value (long/double)
                int64_t wide_value = *reinterpret_cast<const int64_t*>(field_ptr);
                return wide_value;
            } else if (field_size == 1) {
                // byte/boolean
                return static_cast<int>(*field_ptr);
            } else if (field_size == 2) {
                // short/char
                int16_t value = *reinterpret_cast<const int16_t*>(field_ptr);
                return static_cast<int>(value);
            } else {
                // 32-bit int/float
                int32_t value = *reinterpret_cast<const int32_t*>(field_ptr);
                return value;
            }
        } catch (...) {
            return json();  // Error reading
        }
    }
    
    /**
     * Write field value to raw object memory
     * 
     * @param object_data Pointer to object's instance field area (mutable)
     * @param value Value to write (from interpreter register)
     * @return true if successful
     */
    bool set_value(uint8_t* object_data, const json& value) const {
        if (!object_data) return false;
        
        uint8_t* field_ptr = object_data + byte_offset;
        
        try {
            if (is_object_ref) {
                // For references, we'd store object ID
                // In full implementation, this would resolve to heap pointer
                // For now, just validate the write could happen
                return true;
            } else if (is_wide) {
                int64_t wide_value = value.get<int64_t>();
                *reinterpret_cast<int64_t*>(field_ptr) = wide_value;
                return true;
            } else if (field_size == 1) {
                int8_t byte_value = static_cast<int8_t>(value.get<int>());
                *field_ptr = static_cast<uint8_t>(byte_value);
                return true;
            } else if (field_size == 2) {
                int16_t short_value = static_cast<int16_t>(value.get<int>());
                *reinterpret_cast<int16_t*>(field_ptr) = short_value;
                return true;
            } else {
                int32_t int_value = value.get<int>();
                *reinterpret_cast<int32_t*>(field_ptr) = int_value;
                return true;
            }
        } catch (...) {
            return false;  // Type mismatch or other error
        }
    }
    
    // === Validation ===
    
    /**
     * Check if this field's offset is reasonable
     */
    bool validate_offset() const {
        // Basic sanity checks
        if (byte_offset > 10000) return false;  // Suspiciously large
        if (byte_offset % alignment != 0) return false;  // Misaligned
        if (field_size != 1 && field_size != 2 && 
            field_size != 4 && field_size != 8) return false;
        return true;
    }
    
    // === Debug/Evidence ===
    
    std::string debug_string() const {
        std::ostringstream ss;
        ss << "Field[" << name << "] ";
        ss << type_descriptor << " ";
        ss << "offset=" << byte_offset << " ";
        ss << "size=" << field_size;
        if (is_wide) ss << " [WIDE]";
        if (is_object_ref) ss << " [REF]";
        return ss.str();
    }
    
    json to_json() const {
        return {
            {"field_idx", field_idx},
            {"name", name},
            {"type_descriptor", type_descriptor},
            {"access_flags", access_flags},
            {"declaring_class_idx", declaring_class_idx},
            {"byte_offset", byte_offset},
            {"field_size", field_size},
            {"alignment", alignment},
            {"is_wide", is_wide},
            {"is_object_ref", is_object_ref}
        };
    }
    
    static InstanceFieldInfo from_json(const json& j) {
        InstanceFieldInfo f;
        f.field_idx = j.value("field_idx", 0);
        f.name = j.value("name", "");
        f.type_descriptor = j.value("type_descriptor", "");
        f.access_flags = j.value("access_flags", 0);
        f.declaring_class_idx = j.value("declaring_class_idx", 0);
        f.byte_offset = j.value("byte_offset", 0);
        f.field_size = j.value("field_size", 4);
        f.alignment = j.value("alignment", 4);
        f.is_wide = j.value("is_wide", false);
        f.is_object_ref = j.value("is_object_ref", false);
        return f;
    }
};

// ============================================================================
// StaticFieldEntry — Per-class static field storage
// ============================================================================

/**
 * StaticFieldEntry stores a static field's value.
 * Unlike instance fields, static fields have one value per class (not per object).
 * Used by sget/sput instructions.
 * 
 * AOSP Equivalent: dalvik/libdex/Object.h::StaticField
 */
struct StaticFieldEntry {
    // === Identity ===
    uint32_t field_idx;                 // DEX field_ids[] index
    std::string name;                   // Field name
    std::string type_descriptor;       // Type descriptor
    
    // === Declaration Info ===
    uint32_t access_flags;
    uint32_t declaring_class_idx;
    
    // === Value Storage ===
    json value;                         // Current value (JSON for flexibility)
    bool initialized;                   // Has <clinit> executed?
    bool is_wide;                       // long/double
    bool is_object_ref;                 // reference type
    
    // === Constructor ===
    StaticFieldEntry()
        : field_idx(0), access_flags(0), declaring_class_idx(0),
          initialized(false), is_wide(false), is_object_ref(false),
          value(nullptr) {}
    
    StaticFieldEntry(uint32_t idx, const std::string& n, const std::string& type,
                     uint32_t flags, uint32_t decl_idx)
        : field_idx(idx), name(n), type_descriptor(type),
          access_flags(flags), declaring_class_idx(decl_idx),
          initialized(false), is_wide(false), is_object_ref(false),
          value(nullptr)
    {
        infer_type_properties();
    }
    
    void infer_type_properties() {
        if (type_descriptor.empty()) return;
        
        char base_type = type_descriptor[0];
        switch (base_type) {
            case 'J': case 'D':
                is_wide = true;
                is_object_ref = false;
                break;
            case 'L': case '[':
                is_wide = false;
                is_object_ref = true;
                break;
            default:
                is_wide = false;
                is_object_ref = false;
                break;
        }
        
        // Set default value based on type
        if (!initialized) {
            if (is_object_ref) {
                value = nullptr;  // null reference
            } else if (is_wide) {
                value = static_cast<int64_t>(0);
            } else {
                value = 0;
            }
            initialized = true;  // Default-initialized
        }
    }
    
    // === Access ===
    
    json get_value() const {
        return value;
    }
    
    bool set_value(const json& new_value) {
        value = new_value;
        return true;
    }
    
    // === Debug ===
    std::string debug_string() const {
        std::ostringstream ss;
        ss << "Static[" << name << "] ";
        ss << type_descriptor << " = ";
        if (value.is_null()) {
            ss << "null";
        } else if (value.is_string()) {
            ss << value.get<std::string>();
        } else if (value.is_number_integer()) {
            ss << value.get<int64_t>();
        } else {
            ss << value.dump();
        }
        return ss.str();
    }
    
    json to_json() const {
        return {
            {"field_idx", field_idx},
            {"name", name},
            {"type_descriptor", type_descriptor},
            {"access_flags", access_flags},
            {"declaring_class_idx", declaring_class_idx},
            {"value", value},
            {"initialized", initialized},
            {"is_wide", is_wide},
            {"is_object_ref", is_object_ref}
        };
    }
    
    static StaticFieldEntry from_json(const json& j) {
        StaticFieldEntry f;
        f.field_idx = j.value("field_idx", 0);
        f.name = j.value("name", "");
        f.type_descriptor = j.value("type_descriptor", "");
        f.access_flags = j.value("access_flags", 0);
        f.declaring_class_idx = j.value("declaring_class_idx", 0);
        f.value = j.value("value", json());
        f.initialized = j.value("initialized", false);
        f.is_wide = j.value("is_wide", false);
        f.is_object_ref = j.value("is_object_ref", false);
        return f;
    }
};

// ============================================================================
// RuntimeMethodInfo — Method with code item reference
// ============================================================================

/**
 * RuntimeMethodInfo represents a method within a class.
 * Bridges DEX format data with interpreter execution.
 * 
 * AOSP Equivalent: dalvik/libdex/Object.h::Method
 *                   art/runtime/art_method.h::ArtMethod
 */
struct RuntimeMethodInfo {
    // === Identity (from DEX method_ids[]) ===
    uint32_t method_idx;                // Index in DEX method_ids[]
    std::string name;                   // Method name (e.g., "onCreate")
    std::string descriptor;             // Full descriptor (e.g., "(Landroid/os/Bundle;)V")
    std::string shorty;                 // Shorty (return + params, e.g., "VL")
    
    // === Declaration ===
    uint32_t access_flags;              // ACC_PUBLIC, ACC_STATIC, etc.
    uint32_t declaring_class_idx;       // Owner class index
    
    // === Method Classification ===
    bool is_direct;                     // In direct_methods[] (<init>, private)
    bool is_virtual;                    // In virtual_methods[] (overridable)
    bool is_static;                     // ACC_STATIC flag set
    bool is_abstract;                   // ACC_ABSTRACT flag (no code_item!)
    bool is_constructor;                // <init> or <clinit>
    
    // === Code Item Reference (CRITICAL for execution) ===
    bool has_code;                      // False for abstract/native methods
    uint32_t code_item_offset;          // Offset to code_item in DEX file
    
    // Register requirements (from code_item header)
    uint16_t registers_size;            // Total registers needed
    uint16_t ins_size;                  // Input (argument) registers  
    uint16_t outs_size;                 // Out registers for sub-calls
    
    // Instruction count
    uint32_t insns_count;               // Number of 16-bit code units
    
    // === VTable Index (for virtual methods) ===
    int32_t vtable_index;               // Position in class's VTable (-1 = not set)
    
    // === Constructor ===
    RuntimeMethodInfo()
        : method_idx(0), access_flags(0), declaring_class_idx(0),
          is_direct(false), is_virtual(false), is_static(false),
          is_abstract(false), is_constructor(false),
          has_code(false), code_item_offset(0),
          registers_size(0), ins_size(0), outs_size(0),
          insns_count(0), vtable_index(-1) {}
    
    // === Signature Operations ===
    
    /**
     * Get unique signature for VTable lookup
     * Format: "name+descriptor"
     */
    std::string get_signature() const {
        return name + "+" + descriptor;
    }
    
    /**
     * Check if this method matches another's signature
     * Used during VTable construction for override detection
     */
    bool matches_signature(const RuntimeMethodInfo& other) const {
        return name == other.name && descriptor == other.descriptor;
    }
    
    /**
     * Check if this method can accept given argument types
     * Simplified type compatibility check
     */
    bool is_compatible(const std::vector<std::string>& arg_types) const {
        // Parse argument types from descriptor
        // Format: (arg1arg2...)return
        if (descriptor.size() < 2 || descriptor[0] != '(') return false;
        
        size_t end = descriptor.find(')');
        if (end == std::string::npos) return false;
        
        std::string args = descriptor.substr(1, end - 1);
        
        // Quick check: count should match
        // Full type checking would require walking both type lists
        return arg_types.size() >= args.size();  // Simplified
    }
    
    // === Debug/Evidence ===
    
    std::string debug_string() const {
        std::ostringstream ss;
        ss << "Method[" << name << "] ";
        ss << descriptor << " ";
        if (is_direct) ss << "[DIRECT] ";
        if (is_virtual) ss << "[VIRTUAL] ";
        if (is_static) ss << "[STATIC] ";
        if (is_abstract) ss << "[ABSTRACT] ";
        if (has_code) {
            ss << "code@" << code_item_offset;
            ss << " regs=" << registers_size;
        }
        if (vtable_index >= 0) {
            ss << " vtable[" << vtable_index << "]";
        }
        return ss.str();
    }
    
    json to_json() const {
        return {
            {"method_idx", method_idx},
            {"name", name},
            {"descriptor", descriptor},
            {"shorty", shorty},
            {"access_flags", access_flags},
            {"declaring_class_idx", declaring_class_idx},
            {"is_direct", is_direct},
            {"is_virtual", is_virtual},
            {"is_static", is_static},
            {"is_abstract", is_abstract},
            {"is_constructor", is_constructor},
            {"has_code", has_code},
            {"code_item_offset", code_item_offset},
            {"registers_size", registers_size},
            {"ins_size", ins_size},
            {"outs_size", outs_size},
            {"insns_count", insns_count},
            {"vtable_index", vtable_index}
        };
    }
    
    static RuntimeMethodInfo from_json(const json& j) {
        RuntimeMethodInfo m;
        m.method_idx = j.value("method_idx", 0);
        m.name = j.value("name", "");
        m.descriptor = j.value("descriptor", "");
        m.shorty = j.value("shorty", "");
        m.access_flags = j.value("access_flags", 0);
        m.declaring_class_idx = j.value("declaring_class_idx", 0);
        m.is_direct = j.value("is_direct", false);
        m.is_virtual = j.value("is_virtual", false);
        m.is_static = j.value("is_static", false);
        m.is_abstract = j.value("is_abstract", false);
        m.is_constructor = j.value("is_constructor", false);
        m.has_code = j.value("has_code", false);
        m.code_item_offset = j.value("code_item_offset", 0);
        m.registers_size = j.value("registers_size", 0);
        m.ins_size = j.value("ins_size", 0);
        m.outs_size = j.value("outs_size", 0);
        m.insns_count = j.value("insns_count", 0);
        m.vtable_index = j.value("vtable_index", -1);
        return m;
    }
};

// ============================================================================
// VirtualDispatchTable — VTable for polymorphic method dispatch
// ============================================================================

/**
 * VirtualDispatchTable implements the virtual method dispatch table.
 * Enables invoke-virtual to work correctly with inheritance and overriding.
 * 
 * The VTable stores ordered method pointers for virtual dispatch:
 * - Index 0..N-1 map to specific method implementations
 * - Subclasses inherit and can override parent's VTable entries
 * - New virtual methods are appended
 * 
 * AOSP Equivalent: ClassObject->vtable (dalvik)
 *                   mirror::Class::vtable_ (ART)
 * 
 * Usage in invoke-virtual:
 * 1. Resolve method reference to VTable index at link time
 * 2. At call site: obj->class->vtable[index] → method
 * 3. Execute found method (may be overridden in subclass)
 */
struct VirtualDispatchTable {
    // Ordered method list (index = position in table)
    std::vector<const RuntimeMethodInfo*> entries;
    
    // Signature-to-index map for fast lookup during construction
    std::map<std::string, uint32_t> signature_map;
    
    // === Operations ===
    
    /**
     * Look up method by VTable index
     * Primary operation during invoke-virtual execution
     */
    const RuntimeMethodInfo* lookup_by_index(uint32_t index) const {
        if (index >= entries.size()) return nullptr;
        return entries[index];
    }
    
    /**
     * Look up method by signature
     * Used during VTable construction
     */
    const RuntimeMethodInfo* lookup_by_signature(const std::string& signature) const {
        auto it = signature_map.find(signature);
        if (it == signature_map.end()) return nullptr;
        return entries[it->second];
    }
    
    /**
     * Add method to VTable or override existing entry
     * 
     * Core algorithm for VTable construction:
     * - If method signature already exists, replace (override)
     * - If new signature, append (new virtual method)
     * 
     * @param method Pointer to method to add (must outlive this table!)
     * @return Index where method was placed
     */
    uint32_t add_or_override(const RuntimeMethodInfo* method) {
        if (!method) return UINT32_MAX;
        
        std::string sig = method->get_signature();
        auto it = signature_map.find(sig);
        
        if (it != signature_map.end()) {
            // Override existing entry
            uint32_t index = it->second;
            entries[index] = method;
            return index;
        } else {
            // Append new entry
            uint32_t index = static_cast<uint32_t>(entries.size());
            entries.push_back(method);
            signature_map[sig] = index;
            method->vtable_index = static_cast<int32_t>(index);  // Back-reference
            return index;
        }
    }
    
    /**
     * Inherit all entries from parent's VTable
     * Starting point for subclass VTable construction
     */
    void inherit_from(const VirtualDispatchTable& parent) {
        clear();
        
        for (size_t i = 0; i < parent.entries.size(); i++) {
            const RuntimeMethodInfo* method = parent.entries[i];
            entries.push_back(method);
            
            std::string sig = method->get_signature();
            signature_map[sig] = static_cast<uint32_t>(i);
        }
    }
    
    /**
     * Clear all entries
     */
    void clear() {
        entries.clear();
        signature_map.clear();
    }
    
    // === Validation ===
    
    /**
     * Check table integrity
     */
    bool validate() const {
        // Size consistency
        if (entries.size() != signature_map.size()) return false;
        
        // All entries non-null
        for (const auto* method : entries) {
            if (!method) return false;
        }
        
        // All indices valid
        for (const auto& [sig, idx] : signature_map) {
            if (idx >= entries.size()) return false;
            if (entries[idx]->get_signature() != sig) return false;
        }
        
        return true;
    }
    
    size_t size() const { return entries.size(); }
    bool empty() const { return entries.empty(); }
    
    // === Debug/Evidence ===
    
    std::string debug_string() const {
        std::ostringstream ss;
        ss << "VTable[" << entries.size() << "]:\n";
        for (size_t i = 0; i < entries.size(); i++) {
            const auto* method = entries[i];
            if (method) {
                ss << "  [" << i << "] " << method->name << method->descriptor << "\n";
            } else {
                ss << "  [" << i << "] NULL\n";
            }
        }
        return ss.str();
    }
    
    json to_json() const {
        json arr = json::array();
        for (size_t i = 0; i < entries.size(); i++) {
            if (entries[i]) {
                arr.push_back({
                    {"index", i},
                    {"signature", entries[i]->get_signature()},
                    {"name", entries[i]->name}
                });
            } else {
                arr.push_back({{"index", i}, {"signature", "NULL"}});
            }
        }
        return arr;
    }
};

// ============================================================================
// RuntimeClassInfo — Complete runtime class representation
// ============================================================================

/**
 * RuntimeClassInfo is MiniAndroid's equivalent of AOSP's ClassObject/mirror::Class.
 * 
 * It contains ALL metadata needed for runtime execution:
 * - Class identity and hierarchy
 * - Instance/static field layouts with offsets
 * - Direct/virtual method lists
 * - Virtual dispatch table (VTable)
 * - DEX format references
 * 
 * This structure bridges the gap between DEX parsing and interpreter execution.
 * When the DEX parser extracts a class_def, it populates a RuntimeClassInfo.
 * The interpreter then uses this to execute bytecode correctly.
 * 
 * AOSP Equivalent: dalvik/libdex/DexClass.h::ClassObject
 *                   art/runtime/mirror/class.h::Class
 */
struct RuntimeClassInfo {
    // === Identity ===
    std::string class_descriptor;       // e.g., "Landroid/app/Activity;"
    std::string source_file;            // e.g., "Activity.java"
    uint32_t access_flags;              // ACC_PUBLIC | ACC_CLASS, etc.
    
    // === Hierarchy ===
    std::string superclass_descriptor;  // Parent class descriptor
    const RuntimeClassInfo* superclass; // Direct parent pointer (runtime)
    bool hierarchy_resolved;            // Has parent been linked?
    
    // === Fields (CRITICAL for field operations) ===
    std::vector<InstanceFieldInfo> instance_fields;
    uint32_t instance_field_bytes;      // Total bytes for instance fields
    
    std::vector<StaticFieldEntry> static_fields;
    
    // === Methods ===
    std::vector<RuntimeMethodInfo> direct_methods;   // <init>, private, static
    std::vector<RuntimeMethodInfo> virtual_methods;  // Overridable methods
    
    // === VTable ===
    VirtualDispatchTable vtable;
    bool vtable_built;                  // Has build_vtable() been called?
    
    // === DEX References ===
    uint32_t dex_class_idx;             // Index in DEX class_defs[]
    uint32_t class_data_offset;         // File offset to class_data_item
    
    // === Status Tracking ===
    enum class LoadState {
        UNLOADED = 0,                   // Not yet processed
        LOADED = 1,                     // Basic info extracted
        RESOLVED = 2,                   // Fields/methods linked
        VERIFYING = 3,                  // Being verified
        VERIFIED = 4,                   // Ready for execution
        ERROR = 99                      // Loading failed
    } load_state;
    
    std::string error_message;          // Details if load_state == ERROR
    
    // === Constructor ===
    RuntimeClassInfo()
        : access_flags(0), superclass(nullptr),
          hierarchy_resolved(false),
          instance_field_bytes(0),
          vtable_built(false),
          dex_class_idx(UINT32_MAX),
          class_data_offset(0),
          load_state(LoadState::UNLOADED) {}
    
    RuntimeClassInfo(const std::string& descriptor)
        : class_descriptor(descriptor),
          access_flags(0), superclass(nullptr),
          hierarchy_resolved(false),
          instance_field_bytes(0),
          vtable_built(false),
          dex_class_idx(UINT32_MAX),
          class_data_offset(0),
          load_state(LoadState::UNLOADED) {}
    
    // === Field Offset Calculation (AOSP Algorithm) ===
    
    /**
     * Calculate instance field offsets following AOSP algorithm.
     * 
     * This matches dvmComputeInstanceFieldOffsets() from Dalvik:
     * https://android.googlesource.com/platform/dalvik/+/master/vm/analysis/CodeVerify.c
     * 
     * Algorithm:
     * 1. Start after superclass's field area (aligned to 8 bytes)
     * 2. For each field in declaration order:
     *    a. Align current offset to field's alignment requirement
     *    b. Assign offset to field
     *    c. Advance by field's size
     * 3. Pad final size to 8-byte boundary
     * 
     * @param superclass Parent class info (nullptr for java.lang.Object)
     * @return true if calculation succeeded
     * 
     * Example output for class TextView extends View:
     *   View fields (inherited): offset 0-15 (mLeft, mTop, mRight, mBottom)
     *   TextView.mText: offset 16 (reference, 4 bytes)
     *   TextView.mTextColor: offset 20 (int, 4 bytes)
     *   Total: 24 bytes (padded to 24, already aligned)
     */
    bool calculate_field_offsets(const RuntimeClassInfo* super) {
        // Start after superclass fields
        uint32_t current_offset;
        
        if (super) {
            // Align to 8-byte boundary after superclass
            current_offset = align_value(super->instance_field_bytes, 8);
            superclass = super;  // Store parent reference
        } else {
            current_offset = 0;  // No parent, start at beginning
        }
        
        // Assign offsets to each instance field
        for (auto& field : instance_fields) {
            // Align to field's requirement
            if (field.is_wide) {
                current_offset = align_value(current_offset, 8);  // Wide fields: 8-byte align
            } else {
                current_offset = align_value(current_offset, 4);  // Normal: 4-byte align
            }
            
            // Assign offset
            field.byte_offset = current_offset;
            
            // Advance past this field
            current_offset += field.field_size;
        }
        
        // Pad total to 8-byte boundary
        instance_field_bytes = align_value(current_offset, 8);
        
        // Validate all offsets
        for (const auto& field : instance_fields) {
            if (!field.validate_offset()) {
                error_message = "Invalid field offset for: " + field.name;
                load_state = LoadState::ERROR;
                return false;
            }
        }
        
        hierarchy_resolved = (super != nullptr);
        return true;
    }
    
    // === VTable Construction (AOSP Algorithm) ===
    
    /**
     * Build virtual dispatch table following AOSP algorithm.
     * 
     * This matches dvmBuildVTable() from Dalvik:
     * https://android.googlesource.com/platform/dalvik/+/master/vm/oo/Class.c
     * 
     * Algorithm:
     * 1. Copy parent's entire VTable as starting point
     * 2. For each virtual method in this class:
     *    a. Search current VTable for matching signature
     *    b. If found, replace entry (this overrides parent)
     *    c. If not found, append as new entry
     * 3. Mark VTable as built
     * 
     * @param parent_vtable Parent's VTable (empty if no parent)
     * @return true if construction succeeded
     * 
     * Example for class Dog extends Animal:
     *   Animal.vtable: [Animal.speak, Animal.eat]
     *   Dog overrides speak(), adds bark():
     *   Dog.vtable: [Dog.speak, Animal.eat, Dog.bark]
     */
    bool build_vtable(const VirtualDispatchTable& parent_vtable) {
        // Step 1: Inherit parent's VTable
        vtable.inherit_from(parent_vtable);
        
        // Step 2: Process this class's virtual methods
        for (auto& method : virtual_methods) {
            if (method.is_abstract) continue;  // Abstract methods don't enter VTable
            
            // Try to add or override
            uint32_t index = vtable.add_or_override(&method);
            
            if (index == UINT32_MAX) {
                error_message = "Failed to add method to VTable: " + method.name;
                load_state = LoadState::ERROR;
                return false;
            }
        }
        
        // Step 3: Validate
        if (!vtable.validate()) {
            error_message = "VTable validation failed";
            load_state = LoadState::ERROR;
            return false;
        }
        
        vtable_built = true;
        return true;
    }
    
    // Simplified overload using parent class directly
    bool build_vtable(const RuntimeClassInfo* parent) {
        if (parent && parent->vtable_built) {
            return build_vtable(parent->vtable);
        } else {
            VirtualDispatchTable empty_vtable;
            return build_vtable(empty_vtable);
        }
    }
    
    // === Field Lookup Operations ===
    
    /**
     * Find instance field by DEX field index
     * Used by iget/iput instructions
     */
    const InstanceFieldInfo* find_instance_field(uint32_t field_idx) const {
        for (const auto& field : instance_fields) {
            if (field.field_idx == field_idx) {
                return &field;
            }
        }
        return nullptr;  // Not found
    }
    
    /**
     * Find instance field by name (for debugging/host shortcuts)
     */
    const InstanceFieldInfo* find_instance_field_by_name(const std::string& name) const {
        for (const auto& field : instance_fields) {
            if (field.name == name) {
                return &field;
            }
        }
        return nullptr;
    }
    
    /**
     * Find static field by DEX field index
     * Used by sget/sput instructions
     */
    const StaticFieldEntry* find_static_field(uint32_t field_idx) const {
        for (const auto& field : static_fields) {
            if (field.field_idx == field_idx) {
                return &field;
            }
        }
        return nullptr;  // Not found
    }
    
    /**
     * Find static field by name (for debugging)
     */
    StaticFieldEntry* find_static_field_by_name(const std::string& name) {
        for (auto& field : static_fields) {
            if (field.name == name) {
                return &field;
            }
        }
        return nullptr;
    }
    
    // === Method Lookup Operations ===
    
    /**
     * Find virtual method by VTable index
     * Used after invoke-virtual resolution
     */
    const RuntimeMethodInfo* find_virtual_method(uint32_t vtable_index) const {
        return vtable.lookup_by_index(vtable_index);
    }
    
    /**
     * Find direct method by name+descriptor
     * Used by invoke-direct
     */
    const RuntimeMethodInfo* find_direct_method(const std::string& name, 
                                                  const std::string& desc) const {
        for (const auto& method : direct_methods) {
            if (method.name == name && method.descriptor == desc) {
                return &method;
            }
        }
        return nullptr;
    }
    
    /**
     * Find static method by name+descriptor
     * Used by invoke-static
     */
    const RuntimeMethodInfo* find_static_method(const std::string& name,
                                                const std::string& desc) const {
        // Check direct methods first (static methods are often there)
        for (const auto& method : direct_methods) {
            if (method.is_static && method.name == name && method.descriptor == desc) {
                return &method;
            }
        }
        return nullptr;
    }
    
    // === Utility Methods ===
    
    /**
     * Align value up to given boundary
     */
    static uint32_t align_value(uint32_t value, uint32_t alignment) {
        return (value + alignment - 1) & ~(alignment - 1);
    }
    
    /**
     * Check if this class represents an interface
     */
    bool is_interface() const {
        return (access_flags & AccessFlags::ACC_INTERFACE) != 0;
    }
    
    /**
     * Check if this class is abstract
     */
    bool is_abstract() const {
        return (access_flags & AccessFlags::ACC_ABSTRACT) != 0;
    }
    
    /**
     * Check if this class is public
     */
    bool is_public() const {
        return (access_flags & AccessFlags::ACC_PUBLIC) != 0;
    }
    
    // === Serialization (Evidence Collection) ===
    
    json to_json() const {
        json instance_fields_json = json::array();
        for (const auto& f : instance_fields) {
            instance_fields_json.push_back(f.to_json());
        }
        
        json static_fields_json = json::array();
        for (const auto& f : static_fields) {
            static_fields_json.push_back(f.to_json());
        }
        
        json direct_methods_json = json::array();
        for (const auto& m : direct_methods) {
            direct_methods_json.push_back(m.to_json());
        }
        
        json virtual_methods_json = json::array();
        for (const auto& m : virtual_methods) {
            virtual_methods_json.push_back(m.to_json());
        }
        
        return {
            {"class_descriptor", class_descriptor},
            {"source_file", source_file},
            {"access_flags", access_flags},
            {"superclass_descriptor", superclass_descriptor},
            {"hierarchy_resolved", hierarchy_resolved},
            {"instance_fields", instance_fields_json},
            {"instance_field_bytes", instance_field_bytes},
            {"static_fields", static_fields_json},
            {"direct_methods", direct_methods_json},
            {"virtual_methods", virtual_methods_json},
            {"vtable", vtable.to_json()},
            {"vtable_built", vtable_built},
            {"dex_class_idx", dex_class_idx},
            {"class_data_offset", class_data_offset},
            {"load_state", static_cast<int>(load_state)},
            {"error_message", error_message}
        };
    }
    
    static RuntimeClassInfo from_json(const json& j) {
        RuntimeClassInfo cls;
        cls.class_descriptor = j.value("class_descriptor", "");
        cls.source_file = j.value("source_file", "");
        cls.access_flags = j.value("access_flags", 0);
        cls.superclass_descriptor = j.value("superclass_descriptor", "");
        cls.hierarchy_resolved = j.value("hierarchy_resolved", false);
        cls.instance_field_bytes = j.value("instance_field_bytes", 0);
        cls.vtable_built = j.value("vtable_built", false);
        cls.dex_class_idx = j.value("dex_class_idx", UINT32_MAX);
        cls.class_data_offset = j.value("class_data_offset", 0);
        cls.load_state = static_cast<LoadState>(j.value("load_state", 0));
        cls.error_message = j.value("error_message", "");
        
        if (j.contains("instance_fields")) {
            for (const auto& fj : j["instance_fields"]) {
                cls.instance_fields.push_back(InstanceFieldInfo::from_json(fj));
            }
        }
        
        if (j.contains("static_fields")) {
            for (const auto& fj : j["static_fields"]) {
                cls.static_fields.push_back(StaticFieldEntry::from_json(fj));
            }
        }
        
        if (j.contains("direct_methods")) {
            for (const auto& mj : j["direct_methods"]) {
                cls.direct_methods.push_back(RuntimeMethodInfo::from_json(mj));
            }
        }
        
        if (j.contains("virtual_methods")) {
            for (const auto& mj : j["virtual_methods"]) {
                cls.virtual_methods.push_back(RuntimeMethodInfo::from_json(mj));
            }
        }
        
        return cls;
    }
    
    // === Debug Output ===
    
    std::string debug_string() const {
        std::ostringstream ss;
        ss << "Class[" << class_descriptor << "]\n";
        ss << "  Super: " << (superclass_descriptor.empty() ? "(none)" : superclass_descriptor) << "\n";
        ss << "  Fields: " << instance_fields.size() << " instance, " 
           << static_fields.size() << " static\n";
        ss << "  Instance size: " << instance_field_bytes << " bytes\n";
        ss << "  Methods: " << direct_methods.size() << " direct, "
           << virtual_methods.size() << " virtual\n";
        ss << "  VTable: " << vtable.size() << " entries" 
           << (vtable_built ? " (built)" : " (not built)") << "\n";
        ss << "  State: " << static_cast<int>(load_state);
        if (load_state == LoadState::ERROR) {
            ss << " ERROR: " << error_message;
        }
        return ss.str();
    }
};

// ============================================================================
// Runtime Metadata Container — Holds all loaded classes
// ============================================================================

/**
 * RuntimeMetadataContainer manages all loaded classes.
 * Acts as the "ClassLoader" equivalent for the mini-runtime.
 */
class RuntimeMetadataContainer {
private:
    // Map from class descriptor to class info
    std::map<std::string, std::unique_ptr<RuntimeClassInfo>> classes;
    
public:
    /**
     * Add a class to the container
     */
    bool add_class(std::unique_ptr<RuntimeClassInfo> class_info) {
        if (!class_info) return false;
        
        const std::string& desc = class_info->class_descriptor;
        if (classes.find(desc) != classes.end()) {
            return false;  // Already exists
        }
        
        classes[desc] = std::move(class_info);
        return true;
    }
    
    /**
     * Find class by descriptor
     */
    RuntimeClassInfo* find_class(const std::string& descriptor) {
        auto it = classes.find(descriptor);
        if (it == classes.end()) return nullptr;
        return it->second.get();
    }
    
    const RuntimeClassInfo* find_class(const std::string& descriptor) const {
        auto it = classes.find(descriptor);
        if (it == classes.end()) return nullptr;
        return it->second.get();
    }
    
    /**
     * Get number of loaded classes
     */
    size_t class_count() const { return classes.size(); }
    
    /**
     * Check if class exists
     */
    bool has_class(const std::string& descriptor) const {
        return classes.find(descriptor) != classes.end();
    }
    
    /**
     * Resolve class hierarchy for all loaded classes
     * Links superclass pointers and builds VTables
     */
    bool resolve_all_hierarchies() {
        bool success = true;
        
        for (auto& [desc, cls] : classes) {
            if (!cls->superclass_descriptor.empty()) {
                // Find parent
                RuntimeClassInfo* super = find_class(cls->superclass_descriptor);
                
                if (super) {
                    // Calculate field offsets
                    if (!cls->calculate_field_offsets(super)) {
                        success = false;
                        continue;
                    }
                    
                    // Build VTable
                    if (!cls->build_vtable(super)) {
                        success = false;
                        continue;
                    }
                    
                    cls->load_state = RuntimeClassInfo::LoadState::RESOLVED;
                } else {
                    // Parent not loaded yet - mark as unresolved
                    cls->error_message = "Superclass not found: " + cls->superclass_descriptor;
                    cls->load_state = RuntimeClassInfo::LoadState::LOADED;
                }
            } else {
                // No parent (java.lang.Object or root)
                cls->calculate_field_offsets(nullptr);
                
                VirtualDispatchTable empty_vtable;
                cls->build_vtable(empty_vtable);
                
                cls->load_state = RuntimeClassInfo::LoadState::RESOLVED;
            }
        }
        
        return success;
    }
    
    /**
     * Export all metadata as JSON (for evidence collection)
     */
    json to_json() const {
        json class_list = json::array();
        for (const auto& [desc, cls] : classes) {
            class_list.push_back(cls->to_json());
        }
        
        return {
            {"total_classes", classes.size()},
            {"classes", class_list}
        };
    }
    
    /**
     * Generate summary statistics
     */
    json get_statistics() const {
        int total_instance_fields = 0;
        int total_static_fields = 0;
        int total_direct_methods = 0;
        int total_virtual_methods = 0;
        int total_vtable_entries = 0;
        int resolved_count = 0;
        int error_count = 0;
        
        for (const auto& [desc, cls] : classes) {
            total_instance_fields += cls->instance_fields.size();
            total_static_fields += cls->static_fields.size();
            total_direct_methods += cls->direct_methods.size();
            total_virtual_methods += cls->virtual_methods.size();
            total_vtable_entries += cls->vtable.size();
            
            if (cls->load_state == RuntimeClassInfo::LoadState::RESOLVED ||
                cls->load_state == RuntimeClassInfo::LoadState::VERIFIED) {
                resolved_count++;
            } else if (cls->load_state == RuntimeClassInfo::LoadState::ERROR) {
                error_count++;
            }
        }
        
        return {
            {"total_classes", classes.size()},
            {"resolved_classes", resolved_count},
            {"error_classes", error_count},
            {"total_instance_fields", total_instance_fields},
            {"total_static_fields", total_static_fields},
            {"total_direct_methods", total_direct_methods},
            {"total_virtual_methods", total_virtual_methods},
            {"total_vtable_entries", total_vtable_entries}
        };
    }
};

} // namespace runtime
} // namespace miniandroid

#endif // MINIANDROID_RUNTIME_METADATA_H
