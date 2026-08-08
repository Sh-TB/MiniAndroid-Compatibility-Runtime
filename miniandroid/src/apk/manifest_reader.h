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
    START_DOCUMENT = 0x0000,
    END_DOCUMENT = 0x0001,
    START_NAMESPACE = 0x0100,
    END_NAMESPACE = 0x0101,
    START_ELEMENT = 0x0102,
    END_ELEMENT = 0x0103,
    CDATA = 0x0104
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
#pragma pack(push, 1)
struct AxmlStartNamespace {
    AxmlChunkHeader chunk;
    uint32_t prefix_index;
    uint32_t uri_index;
};
#pragma pack(pop)

// End namespace element
#pragma pack(push, 1)
struct AxmlEndNamespace {
    AxmlChunkHeader chunk;
    uint32_t prefix_index;
    uint32_t uri_index;
};
#pragma pack(pop)

// Start element
#pragma pack(push, 1)
struct AxmlStartElement {
    AxmlChunkHeader chunk;
    uint32_t namespace_index;
    uint32_t name_index;
    uint16_t attribute_count;
    uint16_t class_attribute_index;
    uint32_t attribute_ids_offset;
    // Followed by attributes
};
#pragma pack(pop)

// End element
#pragma pack(push, 1)
struct AxmlEndElement {
    AxmlChunkHeader chunk;
    uint32_t namespace_index;
    uint32_t name_index;
};
#pragma pack(pop)

// Attribute data
#pragma pack(push, 1)
struct AxmlAttribute {
    uint32_t namespace_index;
    uint32_t name_index;
    uint32_t value_string_index;
    uint32_t value_type;
    uint32_t value_data;
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
    size_t decode_string_length(const uint8_t* data, size_t offset, size_t& out_length, bool utf8);
    
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
    bool activity_has_main_action_ = false;
    bool activity_has_launcher_category_ = false;
    
    bool verbose_ = false;
};

} // namespace apk
} // namespace miniandroid

#endif // MINIANDROID_MANIFEST_READER_H
