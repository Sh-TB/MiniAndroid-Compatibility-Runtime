/*
 * MiniAndroid Runtime v0.1 - DEX Parser
 * EXP-001: HelloWorld Loader
 * 
 * Parses DEX (Dalvik Executable) format files from APKs.
 * Extracts class, method, field, and string information.
 */

#ifndef MINIANDROID_DEX_PARSER_H
#define MINIANDROID_DEX_PARSER_H

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <cstdint>
#include <functional>
#include <optional>

namespace miniandroid {
namespace dex {

// DEX magic numbers
constexpr const char* DEX_MAGIC_035 = "dex\n035\0";
constexpr const char* DEX_MAGIC_036 = "dex\n036\0";
constexpr const char* DEX_MAGIC_037 = "dex\n037\0";
constexpr const char* DEX_MAGIC_038 = "dex\n038\0";
constexpr const char* DEX_MAGIC_039 = "dex\n039\0";

// DEX error codes
enum class DexError {
    NONE = 0,
    INVALID_MAGIC,
    CHECKSUM_MISMATCH,
    SIGNATURE_MISMATCH,
    FILE_TOO_SMALL,
    ENDIAN_TAG_INVALID,
    UNSUPPORTED_VERSION,
    PARSE_ERROR
};

// DEX File Header (70 bytes)
#pragma pack(push, 1)
struct DexHeader {
    uint8_t magic[8];            // "dex\n035\0"
    uint32_t checksum;           // Adler32 checksum
    uint8_t signature[20];       // SHA-1 hash
    uint32_t file_size;          // Total file size
    uint32_t header_size;        // 0x70
    uint32_t endian_tag;         // 0x12345678
    uint32_t link_size;
    uint32_t link_off;
    uint32_t map_off;
    uint32_t string_ids_size;
    uint32_t string_ids_off;
    uint32_t type_ids_size;
    uint32_t type_ids_off;
    uint32_t proto_ids_size;
    uint32_t proto_ids_off;
    uint32_t field_ids_size;
    uint32_t field_ids_off;
    uint32_t method_ids_size;
    uint32_t method_ids_off;
    uint32_t class_defs_size;
    uint32_t class_defs_off;
    uint32_t data_size;
    uint32_t data_off;
};
#pragma pack(pop)

// String ID (4 bytes each - just an offset)
struct DexStringId {
    uint32_t string_data_off;     // Offset to string_data_item
};

// Type ID (4 bytes each)
struct DexTypeId {
    uint32_t descriptor_idx;      // Index into string_ids
};

// Prototype ID (12 bytes each)
struct DexProtoId {
    uint32_t shorty_idx;          // Short descriptor index
    uint32_t return_type_idx;     // Return type index
    uint32_t parameters_off;      // Offset to type_list or 0
};

// Field ID (8 bytes each)
struct DexFieldId {
    uint16_t class_idx;           // Defining class
    uint16_t type_idx;            // Field type
    uint32_t name_idx;            // Field name
};

// Method ID (8 bytes each)
struct DexMethodId {
    uint16_t class_idx;           // Defining class
    uint16_t proto_idx;           // Method prototype
    uint32_t name_idx;            // Method name
};

// Class definition (32 bytes each)
struct DexClassDef {
    uint32_t class_idx;           // Class type
    uint32_t access_flags;        // Access flags (PUBLIC, FINAL, etc.)
    uint32_t superclass_idx;      // Superclass or NO_INDEX
    uint32_t interfaces_off;      // Interfaces
    uint32_t source_file_idx;     // Source filename
    uint32_t annotations_off;     // Annotations
    uint32_t class_data_off;      // Class data (encoded)
    uint32_t static_values_off;   // Static values
};

// Class data item header
struct DexClassDataHeader {
    uint32_t static_fields_size;
    uint32_t instance_fields_size;
    uint32_t direct_methods_size;
    uint32_t virtual_methods_size;
};

// Encoded field/method structures
struct DexEncodedField {
    uint32_t field_idx_diff;
    uint32_t access_flags;
};

struct DexEncodedMethod {
    uint32_t method_idx_diff;
    uint32_t access_flags;
    uint32_t code_off;            // Offset to code_item or 0 (abstract/native)
};

// Code item structure
struct DexCodeItem {
    uint16_t registers_size;
    uint16_t ins_size;
    uint16_t outs_size;
    uint16_t tries_size;
    uint32_t debug_info_off;
    uint32_t insns_size;          // Instruction count (2-byte units)
    // Followed by insns[insns_size]
    // Optionally followed by tries[] and handler_list
};

// Parsed class information
struct MethodInfo {
    std::string name;
    std::string descriptor;       // e.g., "(Ljava/lang/String;)V"
    std::string shorty;           // Short form of descriptor
    std::string return_type;
    std::vector<std::string> parameters;
    std::string defining_class;   // Class that defines this method
    
    bool is_constructor = false;
    bool is_static = false;
    bool is_native = false;
    bool is_abstract = false;
    
    uint32_t access_flags = 0;
    uint32_t code_offset = 0;     // 0 if abstract/native

    // EXP-058: Store code_item header fields. Previously these were
    // read from the DEX but NOT stored in MethodInfo, causing callers
    // to hardcode registers_size=16 which is WRONG for methods with
    // different register counts (e.g., onCreate has registers_size=17).
    uint16_t registers_size = 0;
    uint16_t ins_size = 0;
    uint16_t outs_size = 0;

    // Bytecode (if available)
    std::vector<uint16_t> bytecode;

    // EXP-052: Exception-handling diagnostic state.
    //
    // Real DEX methods have an optional tries[] + encoded_catch_handler_list
    // section AFTER the insns[] array (when tries_size > 0). The runtime
    // does NOT yet implement exception handling — but we capture the raw
    // bytes here so the THROW handler can at least log whether the current
    // method has a try table, and (eventually) decode it to find a
    // matching catch handler.
    //
    // tries_size = number of try_item entries (each is 8 bytes:
    //   u32 start_addr, u16 insn_count, u16 handler_off).
    // tries_data  = raw bytes of the tries[] array + the
    //   encoded_catch_handler_list that follows it. The handler list
    //   uses ULEB128-encoded sizes and offsets — we keep the raw bytes
    //   and decode on demand.
    //
    // When tries_size == 0, the method has no try/catch handlers — any
    // throw inside it must propagate to the caller.
    uint16_t tries_size = 0;
    std::vector<uint8_t> tries_data;
};

// Parsed field information
struct FieldInfo {
    std::string name;
    std::string type;
    std::string defining_class;
    
    bool is_static = false;
    uint32_t access_flags = 0;
};

// Parsed class information
struct ClassInfo {
    std::string name;             // e.g., "Lcom/example/MainActivity;"
    std::string source_file;
    std::string superclass_name;
    
    uint32_t access_flags = 0;
    
    // Contents
    std::vector<FieldInfo> static_fields;
    std::vector<FieldInfo> instance_fields;
    std::vector<MethodInfo> direct_methods;   // Static + constructors + private
    std::vector<MethodInfo> virtual_methods;  // Everything else
    
    // Interface names
    std::vector<std::string> interfaces;
    
    // Helper methods
    std::vector<MethodInfo> all_methods() const;
    std::vector<MethodInfo> get_method(const std::string& name) const;
    std::optional<MethodInfo> get_constructor() const;
};

// Complete DEX report
struct DexReport {
    // Version info
    std::string dex_version;
    std::string dex_path;
    
    // Counts
    uint32_t strings_count = 0;
    uint32_t types_count = 0;
    uint32_t prototypes_count = 0;
    uint32_t fields_count = 0;
    uint32_t methods_count = 0;
    uint32_t classes_count = 0;
    
    // All strings (useful for debugging)
    std::vector<std::string> strings;
    
    // All types (for opcode resolution)
    std::vector<std::string> types;
    
    // EXP-037 Phase B (BLOCKER-002 + BLOCKER-003 FIX):
    // Previously, DexParser parsed method_ids[] and field_ids[] into private
    // vectors (methods_ and fields_) but never exposed them on DexReport.
    // The dalvik_engine then fabricated lookup code that referenced
    // nonexistent DexReport::methods / DexReport::fields members, breaking
    // the build (BLOCKER-001). Now we expose the raw ID tables so the
    // interpreter can resolve method_idx → {class_idx, proto_idx, name_idx}
    // and field_idx → {class_idx, type_idx, name_idx} properly. The string
    // and type lookup is done via the already-populated `strings` and
    // `types` vectors above.
    std::vector<DexMethodId> method_ids;   // method_ids[] table from DEX header
    std::vector<DexFieldId>  field_ids;     // field_ids[]  table from DEX header
    
    // All classes with full details
    std::vector<ClassInfo> classes;
    
    // Validation
    bool is_valid = false;
    std::string validation_error;
    
    // Raw header for debugging
    DexHeader header;

    // EXP-037 Phase B (BLOCKER-002): Resolve method_idx → method name.
    // Returns "<bad_idx:N>" if out of range.
    std::string get_method_name(uint32_t method_idx) const {
        if (method_idx >= method_ids.size()) return "<bad_method_idx:" + std::to_string(method_idx) + ">";
        uint32_t name_idx = method_ids[method_idx].name_idx;
        if (name_idx >= strings.size()) return "<bad_name_idx:" + std::to_string(name_idx) + ">";
        return strings[name_idx];
    }

    // EXP-037 Phase B (BLOCKER-002): Resolve method_idx → declaring class type descriptor.
    std::string get_method_class(uint32_t method_idx) const {
        if (method_idx >= method_ids.size()) return "<bad_method_idx:" + std::to_string(method_idx) + ">";
        uint16_t class_idx = method_ids[method_idx].class_idx;
        if (class_idx >= types.size()) return "<bad_class_idx:" + std::to_string(class_idx) + ">";
        return types[class_idx];
    }

    // EXP-037 Phase B (BLOCKER-003): Resolve field_idx → field name.
    std::string get_field_name(uint32_t field_idx) const {
        if (field_idx >= field_ids.size()) return "<bad_field_idx:" + std::to_string(field_idx) + ">";
        uint32_t name_idx = field_ids[field_idx].name_idx;
        if (name_idx >= strings.size()) return "<bad_name_idx:" + std::to_string(name_idx) + ">";
        return strings[name_idx];
    }

    // EXP-037 Phase B (BLOCKER-003): Resolve field_idx → declaring class type descriptor.
    std::string get_field_class(uint32_t field_idx) const {
        if (field_idx >= field_ids.size()) return "<bad_field_idx:" + std::to_string(field_idx) + ">";
        uint16_t class_idx = field_ids[field_idx].class_idx;
        if (class_idx >= types.size()) return "<bad_class_idx:" + std::to_string(class_idx) + ">";
        return types[class_idx];
    }

    // EXP-037 Phase B (BLOCKER-003): Resolve field_idx → field type descriptor.
    std::string get_field_type(uint32_t field_idx) const {
        if (field_idx >= field_ids.size()) return "<bad_field_idx:" + std::to_string(field_idx) + ">";
        uint16_t type_idx = field_ids[field_idx].type_idx;
        if (type_idx >= types.size()) return "<bad_type_idx:" + std::to_string(type_idx) + ">";
        return types[type_idx];
    }
};

/**
 * Main DEX Parser Class
 * 
 * Usage:
 *   DexParser parser;
 *   auto report = parser.parse("classes.dex");
 *   if (report.is_valid) { ... }
 */
class DexParser {
public:
    DexParser();
    ~DexParser();
    
    /**
     * Parse a DEX file from disk
     */
    DexReport parse(const std::string& path);
    
    /**
     * Parse DEX data from memory
     */
    DexReport parse_data(const std::vector<uint8_t>& data, const std::string& source = "memory");
    
    /**
     * Parse DEX data from raw pointer
     */
    DexReport parse_raw(const uint8_t* data, size_t size, const std::string& source = "raw");
    
    /**
     * Get last error message
     */
    std::string get_last_error() const { return last_error_; }
    
    /**
     * Set verbose logging
     */
    void set_verbose(bool verbose) { verbose_ = verbose; }

private:
    // Validation
    DexError validate_header(const DexHeader& header);
    bool verify_checksum(const uint8_t* data, size_t size, const DexHeader& header);
    bool verify_signature(const uint8_t* data, size_t size, const DexHeader& header);
    
    // Parsing functions
    bool parse_string_pool(const uint8_t* data, DexReport& report);
    bool parse_types(const uint8_t* data, DexReport& report);
    bool parse_prototypes(const uint8_t* data, DexReport& report);
    bool parse_fields(const uint8_t* data, DexReport& report);
    bool parse_methods(const uint8_t* data, DexReport& report);
    bool parse_class_defs(const uint8_t* data, DexReport& report);
    bool parse_class_data(const uint8_t* data, const DexClassDef& class_def, ClassInfo& info);
    
    // String helpers
    std::string read_dex_string(const uint8_t* data, uint32_t offset);
    std::string read_mutf8_string(const uint8_t* data, uint32_t offset);
    std::string get_string(uint32_t index) const;
    std::string get_type(uint32_t index) const;
    
    // Type descriptor to readable name
    std::string descriptor_to_readable(const std::string& descriptor) const;
    std::string parse_descriptor_params(const std::string& desc, std::vector<std::string>& params) const;
    
    // Code parsing
    bool parse_code_item(const uint8_t* data, uint32_t offset, MethodInfo& method);
    
    // Utility
    void log(const std::string& message);
    
    // State
    std::vector<std::string> strings_;
    std::vector<std::string> types_;
    std::vector<DexProtoId> protos_;
    std::vector<DexMethodId> methods_;
    std::vector<DexFieldId> fields_;
    
    const uint8_t* current_data_ = nullptr;
    size_t current_size_ = 0;
    
    std::string last_error_;
    bool verbose_ = false;
};

} // namespace dex
} // namespace miniandroid

#endif // MINIANDROID_DEX_PARSER_H
