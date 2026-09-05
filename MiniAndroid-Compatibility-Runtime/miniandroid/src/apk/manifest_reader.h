/*
 * MiniAndroid Runtime v0.1 - Manifest Reader (AXML Parser)
 * EXP-001: HelloWorld Loader
 * 
 * Parses Android's binary XML format used in AndroidManifest.xml
 */

#ifndef MINIANDROID_MANIFEST_READER_H
#define MINIANDROID_MANIFEST_READER_H

#include <string>
#include <vector>
#include <map>
#include <cstdint>

namespace miniandroid {
namespace apk {

// AXML token types
enum class AxmlToken : uint16_t {
    // EXP-037 PHASE A Week 3 (BLOCKER-006 FIX):
    // The previous token table was wrong. Real AXML chunk types per AOSP
    // frameworks/base/libs/androidfw/include/androidfw/ResourceTypes.h:
    //   RES_XML_TYPE              = 0x0003  (outer wrapper of every AXML file)
    //   RES_STRING_POOL_TYPE      = 0x0001  (string table)
    //   RES_XML_RESOURCE_MAP_TYPE = 0x0180  (resource ID map)
    //   RES_XML_START_NAMESPACE   = 0x0100
    //   RES_XML_END_NAMESPACE     = 0x0101
    //   RES_XML_START_ELEMENT     = 0x0102
    //   RES_XML_END_ELEMENT       = 0x0103
    //   RES_XML_CDATA_TYPE        = 0x0104
    //
    // The previous code invented START_DOCUMENT=0x0000 / END_DOCUMENT=0x0001
    // and the header check required type==0x0000. No real AXML file ever has
    // type=0x0000 — that corresponds to no chunk at all. END_DOCUMENT=0x0001
    // was even worse: 0x0001 is RES_STRING_POOL_TYPE, so the switch statement
    // was silently no-op-ing the string pool (and the positional default-case
    // fallback happened to handle it correctly by accident).
    RES_XML_TYPE              = 0x0003,  // Outer AXML file header
    STRING_POOL               = 0x0001,  // String table chunk
    RESOURCE_MAP              = 0x0180,  // Resource ID map chunk
    START_NAMESPACE           = 0x0100,
    END_NAMESPACE             = 0x0101,
    START_ELEMENT             = 0x0102,
    END_ELEMENT               = 0x0103,
    CDATA                     = 0x0104
};

// AXML resource values
enum class AxmlDataType : uint8_t {
    NULL_TYPE = 0,
    STRING = 1,
    INTEGER = 2,
    FLOAT = 3,
    BINARY = 4,
    ATTRIBUTE = 5,
    REFERENCE = 6,
    ATTRIBUTE_INT = 16,
    STRING_INT = 17,
    INT = 18,
    FLOAT_INT = 19,
    INT_HEX = 20,
    INT_BOOLEAN = 21
};

// Parsed manifest information
struct ManifestInfo {
    // Package identification
    std::string package_name;
    std::string version_name;
    int version_code = 0;
    
    // SDK versions
    std::string min_sdk_version;
    std::string target_sdk_version;
    
    // Main activity (from intent filter)
    std::string main_activity;       // Short form (.MainActivity)
    std::string main_activity_full;  // Full form (com.example.MainActivity)
    
    // All activities found
    struct ActivityInfo {
        std::string name;
        bool is_main_activity = false;
        bool is_launcher = false;
    };
    std::vector<ActivityInfo> activities;
    
    // Permissions
    std::vector<std::string> permissions;
    
    // Uses features
    std::vector<std::string> uses_features;
    
    // Application info
    std::string application_label;
    std::string application_name;  // EXP-093/F005: android:name attribute
    bool has_application = false;
    
    // Raw data access
    bool parse_success = false;
    std::string error_message;
};

// AXML chunk header
#pragma pack(push, 1)
struct AxmlChunkHeader {
    uint16_t type;
    uint16_t header_size;
    uint32_t size;  // Including header
};
#pragma pack(pop)

// AXML header
#pragma pack(push, 1)
struct AxmlHeader {
    uint32_t magic;          // 0x00080003
    AxmlChunkHeader header;
};
#pragma pack(pop)

// String pool header
#pragma pack(push, 1)
struct AxmlStringPoolHeader {
    AxmlChunkHeader chunk;
    uint32_t string_count;
    uint32_t style_count;
    uint32_t flags;
    uint32_t strings_start;
    uint32_t styles_start;
};
#pragma pack(pop)

// Resource ID array header
#pragma pack(push, 1)
struct AxmlResourceIdsHeader {
    AxmlChunkHeader chunk;
    // Followed by uint32_t ids[]
};
#pragma pack(pop)

// Start namespace element
// EXP-037 PHASE A Week 3 (BLOCKER-006 FIX):
// Per AOSP frameworks/base/libs/androidfw/include/androidfw/ResourceTypes.h,
// ResXMLTree_node extends ResChunk_header with two extra fields:
//   uint32_t lineNumber;
//   uint32_t comment;
// All XML element chunk types (namespace/element/cdata) inherit these
// fields. The previous code omitted them, causing every field after the
// chunk_header to be read from the wrong offset (off-by-8).
#pragma pack(push, 1)
struct AxmlStartNamespace {
    AxmlChunkHeader chunk;     // 8 bytes (offset 0)
    uint32_t lineNumber;       // 4 bytes (offset 8)  — was MISSING
    uint32_t comment;          // 4 bytes (offset 12) — was MISSING
    uint32_t prefix_index;    // 4 bytes (offset 16)
    uint32_t uri_index;        // 4 bytes (offset 20)
};
#pragma pack(pop)

// End namespace element
#pragma pack(push, 1)
struct AxmlEndNamespace {
    AxmlChunkHeader chunk;     // 8 bytes
    uint32_t lineNumber;       // 4 bytes — was MISSING
    uint32_t comment;          // 4 bytes — was MISSING
    uint32_t prefix_index;
    uint32_t uri_index;
};
#pragma pack(pop)

// Start element
// AOSP ResXMLTree_attrExt layout (44-byte total struct, but headerSize in
// the chunk header is 16 — only ResXMLTree_node part is counted as the
// "header" by AAPT2; the attrExt-specific fields are part of the body).
#pragma pack(push, 1)
struct AxmlStartElement {
    AxmlChunkHeader chunk;            // 8 bytes (offset 0)
    uint32_t lineNumber;              // 4 bytes (offset 8)  — was MISSING
    uint32_t comment;                 // 4 bytes (offset 12) — was MISSING
    uint32_t namespace_index;        // 4 bytes (offset 16)
    uint32_t name_index;             // 4 bytes (offset 20)
    uint16_t attribute_start;        // 2 bytes (offset 24) — was MISSING
    uint16_t attribute_size;         // 2 bytes (offset 26) — was MISSING
    uint16_t attribute_count;        // 2 bytes (offset 28)
    uint16_t id_attribute_index;     // 2 bytes (offset 30) — was class_attribute_index
    uint16_t class_attribute_index;  // 2 bytes (offset 32)
    uint16_t style_attribute_index;   // 2 bytes (offset 34) — was MISSING
};
#pragma pack(pop)

// End element
#pragma pack(push, 1)
struct AxmlEndElement {
    AxmlChunkHeader chunk;     // 8 bytes
    uint32_t lineNumber;       // 4 bytes — was MISSING
    uint32_t comment;          // 4 bytes — was MISSING
    uint32_t namespace_index;
    uint32_t name_index;
};
#pragma pack(pop)

// Attribute data
// EXP-037 PHASE A Week 3 (BLOCKER-006 FIX):
// Per AOSP ResourceTypes.h, ResXMLTree_attribute is:
//   ns(4) + name(4) + rawValue(4) + Res_value{size(2)+res0(1)+dataType(1)+data(4)}
// The previous struct read Res_value's first 4 bytes as a single u32
// "value_type", which conflated size, res0, and dataType. The actual
// dataType is in the HIGH byte (byte 3) of that u32 when read as LE.
// Code that checks `value_type == AxmlDataType::STRING` therefore never
// matched, because the comparison was against the low 8 bits (size=8)
// not the high 8 bits (dataType=1 for STRING).
#pragma pack(push, 1)
struct AxmlAttribute {
    uint32_t namespace_index;        // 4 bytes (offset 0)
    uint32_t name_index;              // 4 bytes (offset 4)
    uint32_t value_string_index;     // 4 bytes (offset 8) — rawValue, string index or -1
    uint16_t value_size;             // 2 bytes (offset 12) — size of Res_value (always 8)
    uint8_t  value_res0;             // 1 byte  (offset 14) — always 0
    uint8_t  value_data_type;        // 1 byte  (offset 15) — Res_value dataType
    uint32_t value_data;              // 4 bytes (offset 16) — Res_value data
};
#pragma pack(pop)

/**
 * Binary XML (AXML) Parser for AndroidManifest.xml
 * 
 * Android uses a custom binary XML format in APKs to save space and
 * improve parsing speed. This class decodes that format.
 */
class ManifestReader {
public:
    ManifestReader();
    ~ManifestReader();
    
    /**
     * Parse binary manifest data
     * @param data Raw bytes of AndroidManifest.xml from APK
     * @return ManifestInfo structure with parsed data
     */
    ManifestInfo parse(const std::vector<uint8_t>& data);
    
    /**
     * Get raw string pool (for debugging)
     */
    const std::vector<std::string>& get_strings() const { return strings_; }
    
    /**
     * Set verbose logging
     */
    void set_verbose(bool verbose) { verbose_ = verbose; }

private:
    // Parsing methods
    bool parse_header(const uint8_t* data, size_t size);
    bool parse_string_pool(const uint8_t* chunk, size_t size);
    bool parse_resource_ids(const uint8_t* chunk, size_t size);
    bool parse_element(const uint8_t* data, size_t size, size_t& offset);
    
    // String pool helpers
    std::string get_string(size_t index) const;
    // (decode_string_length removed — FIND-REUSE-004 moved pool entry
    //  decoding into resources/string_pool.cpp, AOSP decodeLength law)
    
    // Namespace tracking
    void push_namespace(const std::string& prefix, const std::string& uri);
    void pop_namespace();
    std::string resolve_namespace(uint32_t ns_index) const;
    
    // Element processing
    void process_start_element(const std::string& ns, const std::string& name,
                               const std::vector<AxmlAttribute>& attrs);
    void process_end_element(const std::string& ns, const std::string& name);
    
    // Attribute helpers
    std::string get_attribute_value(const std::vector<AxmlAttribute>& attrs, 
                                    const std::string& name) const;
    int get_attribute_int(const std::vector<AxmlAttribute>& attrs,
                          const std::string& name) const;
    
    // Logging
    void log(const std::string& message);
    
    // Utility helpers
    static std::string int_to_hex(uint32_t value);
    
    // Plain XML parser for non-binary manifests
    ManifestInfo parse_plain_xml(const std::vector<uint8_t>& data);
    
    // State
    std::vector<std::string> strings_;
    std::vector<uint32_t> resource_ids_;
    
    // Namespace stack: {prefix -> uri}
    std::vector<std::map<std::string, std::string>> namespace_stack_;
    
    // Current parsing state
    ManifestInfo result_;
    int depth_ = 0;
    bool in_activity_ = false;
    std::string current_activity_name_;
    std::string current_activity_target_;  // EXP-038: targetActivity for activity-alias
    bool activity_has_main_action_ = false;
    bool activity_has_launcher_category_ = false;
    
    bool verbose_ = false;
};

} // namespace apk
} // namespace miniandroid

#endif // MINIANDROID_MANIFEST_READER_H
