/*
 * MiniAndroid Runtime v0.1 - Android Resource System
 * EXP-006: Android Resource and Layout Foundation
 * 
 * Implements minimal Android resource loading required for HelloWorld APK.
 * Supports:
 *   - resources.arsc detection and basic parsing
 *   - XML resource files (strings.xml, layouts)
 *   - Resource ID resolution
 *   - LayoutInflater for basic View creation
 * 
 * Golden Debug Protocol Compliant:
 * - No fake resource loading
 * - Every parsed resource must be traced
 * - Missing resource types must be reported
 */

#ifndef MINIANDROID_RESOURCE_PARSER_H
#define MINIANDROID_RESOURCE_PARSER_H

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <cstdint>
#include <optional>
#include <sstream>
#include <fstream>
#include <algorithm>

#include "../../third_party/nlohmann_json/include/nlohmann/json.hpp"
#include "runtime/object_model.h"  // Required for LayoutInflater

namespace miniandroid {
namespace resources {

using json = nlohmann::json;

// ============================================================================
// Error Reporting (Task #9)
// ============================================================================

enum class ResourceError {
    NONE = 0,
    FILE_NOT_FOUND,
    PARSE_ERROR,
    UNSUPPORTED_RESOURCE_TYPE,
    RESOURCE_NOT_FOUND,
    INVALID_RESOURCE_ID,
    XML_PARSE_ERROR,
    ARSC_CORRUPTED,
    STRING_TABLE_ERROR
};

struct UnsupportedResourceReport {
    std::string resource_type;
    std::string resource_name;
    std::string reason;
    std::string severity;  // "warning", "error", "info"
    
    json to_json() const {
        return {
            {"resource_type", resource_type},
            {"resource_name", resource_name},
            {"reason", reason},
            {"severity", severity}
        };
    }
};

class FailureReporter {
public:
    void report_unsupported(const std::string& type, const std::string& name, 
                           const std::string& reason, const std::string& severity = "warning") {
        UnsupportedResourceReport report{type, name, reason, severity};
        unsupported_resources_.push_back(report);
        
        if (severity == "error") {
            error_count_++;
        } else if (severity == "warning") {
            warning_count_++;
        }
    }
    
    void report_error(ResourceError error, const std::string& details) {
        errors_.push_back({static_cast<int>(error), details});
        error_count_++;
    }
    
    const std::vector<UnsupportedResourceReport>& get_unsupported() const { 
        return unsupported_resources_; 
    }
    
    const std::vector<std::pair<int, std::string>>& get_errors() const { 
        return errors_; 
    }
    
    int get_error_count() const { return error_count_; }
    int get_warning_count() const { return warning_count_; }
    bool has_errors() const { return error_count_ > 0; }
    
    json to_json() const {
        json j;
        j["unsupported_resources"] = json::array();
        for (const auto& report : unsupported_resources_) {
            j["unsupported_resources"].push_back(report.to_json());
        }
        j["errors"] = json::array();
        for (const auto& err : errors_) {
            j["errors"].push_back({
                {"error_code", err.first},
                {"details", err.second}
            });
        }
        j["error_count"] = error_count_;
        j["warning_count"] = warning_count_;
        j["has_critical_errors"] = has_errors();
        return j;
    }

private:
    std::vector<UnsupportedResourceReport> unsupported_resources_;
    std::vector<std::pair<int, std::string>> errors_;
    int error_count_ = 0;
    int warning_count_ = 0;
};

// ============================================================================
// Resource Types (Task #1)
// ============================================================================

// Android resource types we support
enum class ResourceType {
    UNKNOWN = 0,
    STRING,         // strings.xml
    LAYOUT,         // layout XML files
    DRAWABLE,       // images (not fully supported)
    MIPMAP,         // mipmap resources (not supported)
    COLOR,          // color values (basic support)
    DIMEN,          // dimension values (basic support)
    ID,             // ID resources
    STYLE,          // style resources (not supported)
    ATTR,           // attributes (not supported)
    RAW             // raw files
};

std::string resource_type_to_string(ResourceType type);
ResourceType string_to_resource_type(const std::string& str);

// Resource ID structure (0x7fPPTTII where PP=package, TT=type, II=entry)
struct ResourceId {
    uint32_t raw_id = 0;
    uint8_t package = 0;
    uint8_t type = 0;
    uint16_t entry = 0;
    
    static ResourceId from_raw(uint32_t raw) {
        ResourceId id;
        id.raw_id = raw;
        id.package = (raw >> 24) & 0xFF;
        id.type = (raw >> 16) & 0xFF;
        id.entry = raw & 0xFFFF;
        return id;
    }
    
    bool is_valid() const { return raw_id != 0; }
    
    json to_json() const {
        return {
            {"raw_id", raw_id},
            {"hex", "0x" + [&]() {
                std::ostringstream oss;
                oss << std::hex << std::setw(8) << std::setfill('0') << raw_id;
                return oss.str();
            }()},
            {"package", package},
            {"type", type},
            {"entry", entry}
        };
    }
};

// ============================================================================
// Package Information (Task #1)
// ============================================================================

struct PackageInfo {
    uint32_t package_id = 0x7F;  // Default app package ID
    std::string package_name;
    std::map<uint8_t, std::string> type_names;  // type ID -> name
    std::map<std::string, uint8_t> name_to_type;  // name -> type ID
    
    json to_json() const {
        json j;
        j["package_id"] = package_id;
        j["package_name"] = package_name;
        j["types"] = json::object();
        for (const auto& [id, name] : type_names) {
            j["types"][name] = id;
        }
        return j;
    }
};

// ============================================================================
// String Resource (Task #2)
// ============================================================================

struct StringResource {
    std::string name;
    std::string value;
    ResourceId id;
    
    json to_json() const {
        return {
            {"name", name},
            {"value", value},
            {"id", id.to_json()}
        };
    }
};

// ============================================================================
// Simple XML Parser for Android Resources (Tasks #2, #4)
// ============================================================================

struct XmlAttribute {
    std::string namespace_uri;
    std::string name;
    std::string value;
    
    json to_json() const {
        return {
            {"namespace", namespace_uri},
            {"name", name},
            {"value", value}
        };
    }
};

struct XmlNode {
    std::string tag_name;
    std::vector<XmlAttribute> attributes;
    std::vector<std::unique_ptr<XmlNode>> children;
    std::string text_content;  // For text nodes
    int line_number = 0;
    
    bool is_text_node() const { return !tag_name.empty() && children.empty(); }
    
    // Helper to get attribute value
    std::optional<std::string> get_attribute(const std::string& name) const {
        for (const auto& attr : attributes) {
            if (attr.name == name) {
                return attr.value;
            }
        }
        return std::nullopt;
    }
    
    // Helper to get attribute with namespace (e.g., "android:id")
    std::optional<std::string> get_attribute_ns(const std::string& ns, const std::string& name) const {
        for (const auto& attr : attributes) {
            if (attr.namespace_uri == ns && attr.name == name) {
                return attr.value;
            }
        }
        return std::nullopt;
    }
    
    json to_json() const;
};

class SimpleXmlParser {
public:
    explicit SimpleXmlParser(FailureReporter* reporter = nullptr);
    
    std::unique_ptr<XmlNode> parse(const std::string& xml_content);
    std::unique_ptr<XmlNode> parse_file(const std::string& filepath);
    
    std::string get_last_error() const { return last_error_; }

private:
    std::unique_ptr<XmlNode> parse_node(std::istringstream& stream, int depth = 0);
    std::vector<XmlAttribute> parse_attributes(const std::string& attr_string);
    std::string trim(const std::string& str);
    std::string unescape_xml(const std::string& str);
    
    std::string last_error_;
    FailureReporter* reporter_;
};

// ============================================================================
// Resource Table (Task #1)
// ============================================================================

class ResourceTable {
public:
    explicit ResourceTable(FailureReporter* reporter = nullptr);
    
    // Load from various sources
    bool load_from_arsc(const std::vector<uint8_t>& arsc_data);
    bool detect_and_load_arsc(const std::vector<uint8_t>& apk_data);
    
    // Package management
    void set_package(const PackageInfo& pkg);
    const PackageInfo& get_package() const { return package_; }
    
    // Type registration
    void register_type(uint8_t type_id, const std::string& type_name);
    
    // Resource ID mapping
    void map_resource_id(uint32_t raw_id, ResourceType type, const std::string& name);
    ResourceId resolve_id(uint32_t raw_id) const;
    std::optional<ResourceId> find_by_name(const std::string& name, ResourceType type) const;
    
    // Query methods
    bool has_resource(uint32_t id) const;
    size_t get_resource_count() const { return resource_map_.size(); }
    
    json to_json() const;

private:
    PackageInfo package_;
    std::map<uint32_t, std::pair<ResourceType, std::string>> resource_map_;
    std::map<std::string, uint32_t> name_to_id_map_;
    FailureReporter* reporter_;
};

// ============================================================================
// String Resource Table (Task #2)
// ============================================================================

class StringResources {
public:
    explicit StringResources(FailureReporter* reporter = nullptr);
    
    // Load from strings.xml
    bool load_from_xml(const std::string& xml_content);
    bool load_from_xml_file(const std::string& filepath);
    bool load_from_apk(const std::vector<uint8_t>& apk_data, const std::string& entry_path);
    
    // String lookup
    std::optional<StringResource> get_by_name(const std::string& name) const;
    std::optional<StringResource> get_by_id(uint32_t id) const;
    std::string resolve_string(const std::string& name, const std::string& default_value = "") const;
    
    // Query
    size_t get_string_count() const { return strings_.size(); }
    const std::vector<StringResource>& get_all_strings() const { return strings_; }
    
    json to_json() const;

private:
    std::vector<StringResource> strings_;
    std::map<std::string, size_t> name_index_;
    std::map<uint32_t, size_t> id_index_;
    FailureReporter* reporter_;
    ResourceTable* resource_table_ = nullptr;
};

// ============================================================================
// APK Resource Inventory (Task #3)
// ============================================================================

struct ResourceEntry {
    std::string path;
    size_t size = 0;
    ResourceType type;
    bool is_parsed = false;
    bool is_supported = true;
    
    json to_json() const {
        return {
            {"path", path},
            {"size", size},
            {"type", resource_type_to_string(type)},
            {"is_parsed", is_parsed},
            {"is_supported", is_supported}
        };
    }
};

class ResourceInventory {
public:
    explicit ResourceInventory(FailureReporter* reporter = nullptr);
    
    // Scan APK contents
    bool scan_apk_entries(const std::vector<std::string>& entries);
    bool scan_apk(const std::string& apk_path);
    
    // Entry management
    void add_entry(const ResourceEntry& entry);
    const ResourceEntry* get_entry(const std::string& path) const;
    std::vector<ResourceEntry> get_entries_by_type(ResourceType type) const;
    
    // Query
    size_t get_total_count() const { return entries_.size(); }
    size_t get_supported_count() const;
    size_t get_parsed_count() const;
    bool has_layouts() const;
    bool has_strings() const;
    bool has_arsc() const;
    
    json to_json() const;

private:
    ResourceType classify_path(const std::string& path);
    std::vector<ResourceEntry> entries_;
    FailureReporter* reporter_;
};

// ============================================================================
// LayoutInflater (Task #4)
// ============================================================================

struct LayoutParams {
    int width = -2;   // WRAP_CONTENT by default
    int height = -2;  // WRAP_CONTENT by default
    int left_margin = 0;
    int top_margin = 0;
    int right_margin = 0;
    int bottom_margin = 0;
    int gravity = 0;
    
    enum { MATCH_PARENT = -1, WRAP_CONTENT = -2 };
    
    json to_json() const {
        return {
            {"width", width == -1 ? "MATCH_PARENT" : width == -2 ? "WRAP_CONTENT" : std::to_string(width)},
            {"height", height == -1 ? "MATCH_PARENT" : height == -2 ? "WRAP_CONTENT" : std::to_string(height)},
            {"margins", {left_margin, top_margin, right_margin, bottom_margin}}
        };
    }
};

struct InflateResult {
    bool success = false;
    uint32_t root_view_id = 0;
    std::string root_view_class;
    std::vector<uint32_t> created_view_ids;
    std::map<uint32_t, std::string> view_classes;
    std::map<uint32_t, LayoutParams> layout_params;
    std::map<uint32_t, std::map<std::string, std::string>> view_attributes;
    std::string error_message;
    
    json to_json() const {
        json j;
        j["success"] = success;
        j["root_view_id"] = root_view_id;
        j["root_view_class"] = root_view_class;
        j["created_view_ids"] = created_view_ids;
        j["view_classes"] = json::object();
        for (const auto& [id, cls] : view_classes) {
            j["view_classes"][std::to_string(id)] = cls;
        }
        j["layout_params"] = json::object();
        for (const auto& [id, params] : layout_params) {
            j["layout_params"][std::to_string(id)] = params.to_json();
        }
        j["view_attributes"] = json::object();
        for (const auto& [id, attrs] : view_attributes) {
            j["view_attributes"][std::to_string(id)] = attrs;
        }
        if (!error_message.empty()) {
            j["error_message"] = error_message;
        }
        return j;
    }
};

class LayoutInflater {
public:
    explicit LayoutInflater(miniandroid::runtime::EnhancedObjectHeap* heap, 
                           StringResources* string_res,
                           FailureReporter* reporter = nullptr);
    
    // Inflate layout from XML
    InflateResult inflate(const XmlNode* layout_root);
    InflateResult inflate_from_xml(const std::string& xml_content);
    InflateResult inflate_from_apk(const std::vector<uint8_t>& apk_data, const std::string& layout_path);
    
    // View creation helpers
    uint32_t create_view(const std::string& class_name, const std::vector<XmlAttribute>& attrs);
    void apply_attributes(uint32_t view_id, const std::vector<XmlAttribute>& attrs);
    
    // Configuration
    void set_default_package(const std::string& pkg) { default_package_ = pkg; }
    
    // Statistics
    int get_inflate_count() const { return inflate_count_; }
    const std::vector<InflateResult>& get_history() const { return history_; }

private:
    uint32_t inflate_node(const XmlNode* node, uint32_t parent_id = 0);
    LayoutParams parse_layout_params(const std::vector<XmlAttribute>& attrs);
    std::string resolve_attribute_value(const std::string& value);
    
    miniandroid::runtime::EnhancedObjectHeap* heap_;
    StringResources* string_res_;
    FailureReporter* reporter_;
    std::string default_package_ = "com.miniandroid.helloworld";
    int inflate_count_ = 0;
    std::vector<InflateResult> history_;
};

// ============================================================================
// ResourceManager - Main Coordinator (All Tasks)
// ============================================================================

struct ResourceManagerState {
    bool initialized = false;
    bool arsc_detected = false;
    bool strings_loaded = false;
    bool layout_loaded = false;
    bool inflated = false;
    bool rendered = false;
    
    json to_json() const {
        return {
            {"initialized", initialized},
            {"arsc_detected", arsc_detected},
            {"strings_loaded", strings_loaded},
            {"layout_loaded", layout_loaded},
            {"inflated", inflated},
            {"rendered", rendered}
        };
    }
};

class ResourceManager {
public:
    explicit ResourceManager();
    
    // Initialize with APK
    bool initialize(const std::string& apk_path);
    bool initialize_from_data(const std::vector<uint8_t>& apk_data, const std::string& apk_name);
    
    // Resource accessors
    ResourceTable& get_resource_table() { return resource_table_; }
    StringResources& get_string_resources() { return string_resources_; }
    ResourceInventory& get_inventory() { return inventory_; }
    FailureReporter& get_failure_reporter() { return failure_reporter_; }
    
    // High-level operations
    bool load_all_resources();
    bool inflate_layout(const std::string& layout_name = "main");
    
    // Get last inflate result
    const InflateResult& get_last_inflate_result() const { return last_inflate_result_; }
    
    // State
    const ResourceManagerState& get_state() const { return state_; }
    
    // APK data access
    const std::vector<uint8_t>& get_apk_data() const { return apk_data_; }
    std::vector<uint8_t> extract_entry(const std::string& entry_name);

private:
    std::string apk_path_;
    std::vector<uint8_t> apk_data_;
    ResourceTable resource_table_;
    StringResources string_resources_;
    ResourceInventory inventory_;
    FailureReporter failure_reporter_;
    LayoutInflater* layout_inflater_ = nullptr;
    ResourceManagerState state_;
    InflateResult last_inflate_result_;
};

} // namespace resources
} // namespace miniandroid

#endif // MINIANDROID_RESOURCE_PARSER_H
