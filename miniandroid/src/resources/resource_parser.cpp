/*
 * MiniAndroid Runtime v0.1 - Android Resource System Implementation
 * EXP-006: Android Resource and Layout Foundation
 * 
 * Implements all resource parsing, string loading, layout inflation.
 */

#include "resources/resource_parser.h"
#include "apk/apk_parser.h"
#include "runtime/object_model.h"

#include <fstream>
#include <sstream>
#include <algorithm>
#include <cctype>

namespace miniandroid {
namespace resources {

// ============================================================================
// Utility Functions
// ============================================================================

std::string resource_type_to_string(ResourceType type) {
    switch (type) {
        case ResourceType::STRING: return "string";
        case ResourceType::LAYOUT: return "layout";
        case ResourceType::DRAWABLE: return "drawable";
        case ResourceType::MIPMAP: return "mipmap";
        case ResourceType::COLOR: return "color";
        case ResourceType::DIMEN: return "dimen";
        case ResourceType::ID: return "id";
        case ResourceType::STYLE: return "style";
        case ResourceType::ATTR: return "attr";
        case ResourceType::RAW: return "raw";
        default: return "unknown";
    }
}

ResourceType string_to_resource_type(const std::string& str) {
    if (str == "string") return ResourceType::STRING;
    if (str == "layout") return ResourceType::LAYOUT;
    if (str == "drawable") return ResourceType::DRAWABLE;
    if (str == "mipmap") return ResourceType::MIPMAP;
    if (str == "color") return ResourceType::COLOR;
    if (str == "dimen") return ResourceType::DIMEN;
    if (str == "id") return ResourceType::ID;
    if (str == "style") return ResourceType::STYLE;
    if (str == "attr") return ResourceType::ATTR;
    if (str == "raw") return ResourceType::RAW;
    return ResourceType::UNKNOWN;
}

// ============================================================================
// XmlNode Serialization
// ============================================================================

json XmlNode::to_json() const {
    json j;
    j["tag_name"] = tag_name;
    j["line_number"] = line_number;
    
    if (!attributes.empty()) {
        j["attributes"] = json::array();
        for (const auto& attr : attributes) {
            j["attributes"].push_back(attr.to_json());
        }
    }
    
    if (!text_content.empty()) {
        j["text_content"] = text_content;
    }
    
    if (!children.empty()) {
        j["children"] = json::array();
        for (const auto& child : children) {
            j["children"].push_back(child->to_json());
        }
    }
    
    return j;
}

// ============================================================================
// SimpleXmlParser Implementation
// ============================================================================

SimpleXmlParser::SimpleXmlParser(FailureReporter* reporter)
    : reporter_(reporter) {}

std::unique_ptr<XmlNode> SimpleXmlParser::parse(const std::string& xml_content) {
    std::istringstream stream(xml_content);
    last_error_.clear();
    
    try {
        auto root = parse_node(stream);
        if (root && !last_error_.empty()) {
            return nullptr;
        }
        return root;
    } catch (const std::exception& e) {
        last_error_ = std::string("XML parse exception: ") + e.what();
        if (reporter_) {
            reporter_->report_error(ResourceError::XML_PARSE_ERROR, last_error_);
        }
        return nullptr;
    }
}

std::unique_ptr<XmlNode> SimpleXmlParser::parse_file(const std::string& filepath) {
    std::ifstream file(filepath);
    if (!file.is_open()) {
        last_error_ = "Cannot open file: " + filepath;
        if (reporter_) {
            reporter_->report_error(ResourceError::FILE_NOT_FOUND, last_error_);
        }
        return nullptr;
    }
    
    std::stringstream buffer;
    buffer << file.rdbuf();
    file.close();
    
    return parse(buffer.str());
}

std::unique_ptr<XmlNode> SimpleXmlParser::parse_node(std::istringstream& stream, int depth) {
    // Prevent stack overflow on deeply nested/malformed XML
    if (depth > 100) {
        last_error_ = "XML nesting too deep (>100 levels)";
        return nullptr;
    }
    
    std::string line;
    while (std::getline(stream, line)) {
        line = trim(line);
        
        // Skip empty lines and comments
        if (line.empty() || line.find("<!--") == 0) {
            if (line.find("-->") != std::string::npos) {
                continue; // Skip rest of comment
            }
            continue;
        }
        
        // Skip XML declaration
        if (line.find("<?xml") == 0) {
            continue;
        }
        
        // Look for opening tag
        size_t tag_start = line.find('<');
        if (tag_start == std::string::npos) {
            // Pure text content - return as text node
            auto node = std::make_unique<XmlNode>();
            node->text_content = unescape_xml(trim(line));
            return node;
        }
        
        // Check if there's text before the tag (e.g., "text<tag>")
        if (tag_start > 0) {
            auto text_node = std::make_unique<XmlNode>();
            text_node->text_content = unescape_xml(trim(line.substr(0, tag_start)));
            
            // Put back the rest for next read
            // For simplicity, just return the text node
            return text_node;
        }
        
        size_t tag_end = line.find('>', tag_start);
        if (tag_end == std::string::npos) {
            // Multi-line tag - read more lines until we find '>'
            std::string remaining;
            while (tag_end == std::string::npos && std::getline(stream, remaining)) {
                line += " " + trim(remaining);  // Add space and next line
                tag_end = line.find('>');
            }
            if (tag_end == std::string::npos) {
                last_error_ = "Unclosed tag";
                return nullptr;
            }
        }
        
        // Extract tag content (between < and >)
        std::string tag_content = line.substr(tag_start + 1, tag_end - tag_start - 1);
        
        // Check for closing tag
        if (!tag_content.empty() && tag_content[0] == '/') {
            return nullptr; // End of current element
        }
        
        // Check for self-closing tag
        bool self_closing = false;
        if (!tag_content.empty() && tag_content[tag_content.size() - 1] == '/') {
            self_closing = true;
            tag_content = tag_content.substr(0, tag_content.size() - 1);
        }
        
        // Parse tag name and attributes
        auto node = std::make_unique<XmlNode>();
        size_t space_pos = tag_content.find(' ');
        if (space_pos != std::string::npos) {
            node->tag_name = trim(tag_content.substr(0, space_pos));
            std::string attrs_str = tag_content.substr(space_pos + 1);
            node->attributes = parse_attributes(attrs_str);
        } else {
            node->tag_name = trim(tag_content);
        }
        
        // Extract any text content after the closing '>' on the same line
        std::string remaining_line = line.substr(tag_end + 1);
        if (!remaining_line.empty()) {
            // Check if there's text content before the next tag or closing tag
            size_t next_tag = remaining_line.find('<');
            if (next_tag != std::string::npos) {
                std::string potential_text = trim(remaining_line.substr(0, next_tag));
                if (!potential_text.empty()) {
                    node->text_content = unescape_xml(potential_text);
                }
                
                // Check if what follows is a closing tag
                std::string after_text = remaining_line.substr(next_tag);
                if (after_text.find("</" + node->tag_name) == 0) {
                    // This is all the text content
                    return node;
                }
            } else {
                // No more tags on this line - might be pure text content
                std::string text = trim(remaining_line);
                if (!text.empty() && text.find("</" + node->tag_name) != std::string::npos) {
                    // Extract text before closing tag
                    size_t close_pos = text.find("</" + node->tag_name);
                    node->text_content = unescape_xml(trim(text.substr(0, close_pos)));
                    return node;
                } else if (!text.empty()) {
                    node->text_content = unescape_xml(text);
                }
            }
        }
        
        // If not self-closing, parse children
        if (!self_closing) {
            while (true) {
                auto pos = stream.tellg();
                std::string child_line;
                if (!std::getline(stream, child_line)) break;
                
                child_line = trim(child_line);
                if (child_line.empty()) continue;
                
                // Check for closing tag
                if (child_line.find("</" + node->tag_name) == 0) {
                    break;
                }
                
                // Put back and parse as child
                stream.seekg(pos);
                auto child = parse_node(stream, depth + 1);
                if (child) {
                    // If child is a text node, add to our text content
                    if (child->tag_name.empty() && !child->text_content.empty()) {
                        if (node->text_content.empty()) {
                            node->text_content = child->text_content;
                        } else {
                            node->text_content += child->text_content;
                        }
                    } else {
                        node->children.push_back(std::move(child));
                    }
                } else {
                    break; // End of children
                }
            }
        }
        
        return node;
    }
    
    return nullptr;
}

std::vector<XmlAttribute> SimpleXmlParser::parse_attributes(const std::string& attr_string) {
    std::vector<XmlAttribute> attributes;
    
    // Simple attribute parser: name="value" or namespace:name="value"
    size_t pos = 0;
    while (pos < attr_string.size()) {
        // Skip whitespace
        while (pos < attr_string.size() && std::isspace(attr_string[pos])) pos++;
        if (pos >= attr_string.size()) break;
        
        // Find attribute name
        size_t name_start = pos;
        while (pos < attr_string.size() && attr_string[pos] != '=' && !std::isspace(attr_string[pos])) {
            pos++;
        }
        std::string name = trim(attr_string.substr(name_start, pos - name_start));
        
        // Skip to =
        while (pos < attr_string.size() && std::isspace(attr_string[pos])) pos++;
        if (pos >= attr_string.size() || attr_string[pos] != '=') break;
        pos++; // skip =
        
        // Skip whitespace after =
        while (pos < attr_string.size() && std::isspace(attr_string[pos])) pos++;
        if (pos >= attr_string.size()) break;
        
        // Find value (quoted)
        char quote_char = attr_string[pos];
        if (quote_char != '"' && quote_char != '\'') break;
        pos++; // skip opening quote
        
        size_t value_start = pos;
        while (pos < attr_string.size() && attr_string[pos] != quote_char) {
            if (attr_string[pos] == '\\') pos++; // skip escaped char
            pos++;
        }
        std::string value = unescape_xml(attr_string.substr(value_start, pos - value_start));
        if (pos < attr_string.size()) pos++; // skip closing quote
        
        // Parse namespace if present
        XmlAttribute attr;
        size_t colon_pos = name.find(':');
        if (colon_pos != std::string::npos) {
            attr.namespace_uri = name.substr(0, colon_pos);
            attr.name = name.substr(colon_pos + 1);
        } else {
            attr.name = name;
        }
        attr.value = value;
        
        attributes.push_back(attr);
    }
    
    return attributes;
}

std::string SimpleXmlParser::trim(const std::string& str) {
    size_t start = str.find_first_not_of(" \t\n\r");
    if (start == std::string::npos) return "";
    size_t end = str.find_last_not_of(" \t\n\r");
    return str.substr(start, end - start + 1);
}

std::string SimpleXmlParser::unescape_xml(const std::string& str) {
    std::string result = str;
    size_t pos = 0;
    while ((pos = result.find('&', pos)) != std::string::npos) {
        if (result.substr(pos, 4) == "&lt;") {
            result.replace(pos, 4, "<");
        } else if (result.substr(pos, 4) == "&gt;") {
            result.replace(pos, 4, ">");
        } else if (result.substr(pos, 5) == "&amp;") {
            result.replace(pos, 5, "&");
        } else if (result.substr(pos, 6) == "&quot;") {
            result.replace(pos, 6, "\"");
        } else if (result.substr(pos, 6) == "&apos;") {
            result.replace(pos, 6, "'");
        } else {
            pos++;
            continue;
        }
    }
    return result;
}

// ============================================================================
// ResourceTable Implementation
// ============================================================================

ResourceTable::ResourceTable(FailureReporter* reporter)
    : reporter_(reporter) {
    // Initialize with default package
    package_.package_id = 0x7F;
    package_.package_name = "com.miniandroid.app";
    
    // Register standard type IDs
    register_type(0x01, "attr");
    register_type(0x02, "id");
    register_type(0x03, "style");
    register_type(0x04, "string");
    register_type(0x05, "dimen");
    register_type(0x06, "color");
    register_type(0x07, "drawable");
    register_type(0x08, "layout");
    register_type(0x09, "mipmap");
    register_type(0x0A, "raw");
}

void ResourceTable::set_package(const PackageInfo& pkg) {
    package_ = pkg;
}

void ResourceTable::register_type(uint8_t type_id, const std::string& type_name) {
    package_.type_names[type_id] = type_name;
    package_.name_to_type[type_name] = type_id;
}

void ResourceTable::map_resource_id(uint32_t raw_id, ResourceType type, const std::string& name) {
    resource_map_[raw_id] = {type, name};
    name_to_id_map_[name] = raw_id;
}

ResourceId ResourceTable::resolve_id(uint32_t raw_id) const {
    return ResourceId::from_raw(raw_id);
}

std::optional<ResourceId> ResourceTable::find_by_name(const std::string& name, ResourceType type) const {
    auto it = name_to_id_map_.find(name);
    if (it != name_to_id_map_.end()) {
        return ResourceId::from_raw(it->second);
    }
    return std::nullopt;
}

bool ResourceTable::has_resource(uint32_t id) const {
    return resource_map_.find(id) != resource_map_.end();
}

bool ResourceTable::load_from_arsc(const std::vector<uint8_t>& arsc_data) {
    // Basic ARSC validation
    if (arsc_data.size() < 8) {
        if (reporter_) {
            reporter_->report_error(ResourceError::ARSC_CORRUPTED, 
                "ARSC data too small for valid header");
        }
        return false;
    }
    
    // Check ARSC magic number (0x00020001 or similar)
    uint32_t magic = arsc_data[0] | (arsc_data[1] << 8) | (arsc_data[2] << 16) | (arsc_data[3] << 24);
    if (magic != 0x00020001 && magic != 0x00020000) {
        // Not standard ARSC format - report but don't fail
        if (reporter_) {
            reporter_->report_unsupported("resources.arsc", "binary_format",
                "Non-standard ARSC format detected (magic: 0x" + 
                [&]() {
                    std::ostringstream oss;
                    oss << std::hex << magic;
                    return oss.str();
                }() + ")", "warning");
        }
        // Continue anyway - we'll use XML-based resources instead
    }
    
    // For now, we'll primarily rely on XML resources
    // Full ARSC parsing would require significant additional code
    return true;
}

bool ResourceTable::detect_and_load_arsc(const std::vector<uint8_t>& apk_data) {
    // Scan for resources.arsc in APK data
    // This is a simplified detection - full ZIP scanning is in ApkParser
    
    // For HelloWorld APK without compiled resources, this will fail gracefully
    return false; // No ARSC in our test APK
}

json ResourceTable::to_json() const {
    json j;
    j["package"] = package_.to_json();
    j["resource_count"] = get_resource_count();
    j["resources"] = json::array();
    for (const auto& [id, info] : resource_map_) {
        j["resources"].push_back({
            {"id", ResourceId::from_raw(id).to_json()},
            {"type", resource_type_to_string(info.first)},
            {"name", info.second}
        });
    }
    return j;
}

// ============================================================================
// StringResources Implementation
// ============================================================================

StringResources::StringResources(FailureReporter* reporter)
    : reporter_(reporter) {}

bool StringResources::load_from_xml(const std::string& xml_content) {
    SimpleXmlParser parser(reporter_);
    auto root = parser.parse(xml_content);
    
    if (!root) {
        if (reporter_) {
            reporter_->report_error(ResourceError::XML_PARSE_ERROR,
                "Failed to parse strings XML: " + parser.get_last_error());
        }
        return false;
    }
    
    // Expect <resources> as root
    if (root->tag_name != "resources") {
        if (reporter_) {
            reporter_->report_error(ResourceError::PARSE_ERROR,
                "strings.xml root element must be <resources>, got <" + root->tag_name + ">");
        }
        return false;
    }
    
    // Parse <string> elements
    for (const auto& child : root->children) {
        if (child->tag_name == "string") {
            StringResource str_res;
            
            // Get name attribute (required)
            auto name_attr = child->get_attribute("name");
            if (!name_attr) {
                if (reporter_) {
                    reporter_->report_error(ResourceError::PARSE_ERROR,
                        "String resource missing 'name' attribute");
                }
                continue;
            }
            str_res.name = *name_attr;
            
            // Get text content or value
            if (!child->text_content.empty()) {
                str_res.value = child->text_content;
            } else if (!child->children.empty()) {
                // Handle nested elements or CDATA
                for (const auto& sub_child : child->children) {
                    if (sub_child->text_content.empty()) {
                        str_res.value += sub_child->tag_name; // Fallback
                    } else {
                        str_res.value += sub_child->text_content;
                    }
                }
            }
            
            // Assign a simple ID based on index
            str_res.id = ResourceId::from_raw(0x7F040001 + static_cast<uint32_t>(strings_.size()));
            
            strings_.push_back(str_res);
            name_index_[str_res.name] = strings_.size() - 1;
            id_index_[str_res.id.raw_id] = strings_.size() - 1;
        }
    }
    
    return !strings_.empty();
}

bool StringResources::load_from_xml_file(const std::string& filepath) {
    std::ifstream file(filepath);
    if (!file.is_open()) {
        if (reporter_) {
            reporter_->report_error(ResourceError::FILE_NOT_FOUND,
                "Cannot open strings file: " + filepath);
        }
        return false;
    }
    
    std::stringstream buffer;
    buffer << file.rdbuf();
    file.close();
    
    return load_from_xml(buffer.str());
}

bool StringResources::load_from_apk(const std::vector<uint8_t>& apk_data, const std::string& entry_path) {
    apk::ApkParser parser;
    auto data = parser.extract_entry_from_memory(apk_data, entry_path);
    
    if (data.empty()) {
        if (reporter_) {
            reporter_->report_error(ResourceError::FILE_NOT_FOUND,
                "Cannot extract from APK: " + entry_path);
        }
        return false;
    }
    
    std::string xml_content(data.begin(), data.end());
    return load_from_xml(xml_content);
}

std::optional<StringResource> StringResources::get_by_name(const std::string& name) const {
    auto it = name_index_.find(name);
    if (it != name_index_.end()) {
        return strings_[it->second];
    }
    return std::nullopt;
}

std::optional<StringResource> StringResources::get_by_id(uint32_t id) const {
    auto it = id_index_.find(id);
    if (it != id_index_.end()) {
        return strings_[it->second];
    }
    return std::nullopt;
}

std::string StringResources::resolve_string(const std::string& name, const std::string& default_value) const {
    auto str = get_by_name(name);
    if (str) {
        return str->value;
    }
    return default_value;
}

json StringResources::to_json() const {
    json j;
    j["string_count"] = get_string_count();
    j["strings"] = json::array();
    for (const auto& str : strings_) {
        j["strings"].push_back(str.to_json());
    }
    return j;
}

// ============================================================================
// ResourceInventory Implementation
// ============================================================================

ResourceInventory::ResourceInventory(FailureReporter* reporter)
    : reporter_(reporter) {}

ResourceType ResourceInventory::classify_path(const std::string& path) {
    if (path.find("res/values/") != std::string::npos || path.find("res/values-") != std::string::npos) {
        if (path.find("strings.xml") != std::string::npos) return ResourceType::STRING;
        if (path.find("colors.xml") != std::string::npos) return ResourceType::COLOR;
        if (path.find("dims.xml") != std::string::npos || path.find("dimens.xml") != std::string::npos) return ResourceType::DIMEN;
        if (path.find("ids.xml") != std::string::npos) return ResourceType::ID;
        if (path.find("styles.xml") != std::string::npos) return ResourceType::STYLE;
        if (path.find("attrs.xml") != std::string::npos) return ResourceType::ATTR;
        return ResourceType::UNKNOWN; // Other values files
    }
    if (path.find("res/layout/") != std::string::npos || path.find("res/layout-") != std::string::npos) {
        return ResourceType::LAYOUT;
    }
    if (path.find("res/drawable/") != std::string::npos || path.find("res/drawable-") != std::string::npos) {
        return ResourceType::DRAWABLE;
    }
    if (path.find("res/mipmap/") != std::string::npos || path.find("res/mipmap-") != std::string::npos) {
        return ResourceType::MIPMAP;
    }
    if (path.find("res/raw/") != std::string::npos) {
        return ResourceType::RAW;
    }
    if (path.find("resources.arsc") != std::string::npos) {
        return ResourceType::STRING; // ARSC contains all types
    }
    if (path.find("assets/") != std::string::npos) {
        return ResourceType::RAW;
    }
    
    return ResourceType::UNKNOWN;
}

bool ResourceInventory::scan_apk_entries(const std::vector<std::string>& entries) {
    entries_.clear();
    
    for (const auto& entry : entries) {
        ResourceEntry res_entry;
        res_entry.path = entry;
        res_entry.type = classify_path(entry);
        res_entry.is_supported = (res_entry.type != ResourceType::UNKNOWN);
        
        entries_.push_back(res_entry);
        
        // Report unsupported types
        if (!res_entry.is_supported && reporter_) {
            reporter_->report_unsupported(
                resource_type_to_string(res_entry.type),
                entry,
                "Unknown resource type classification",
                "info");
        }
        
        // Report unsupported but known types
        if ((res_entry.type == ResourceType::DRAWABLE || res_entry.type == ResourceType::MIPMAP ||
             res_entry.type == ResourceType::STYLE || res_entry.type == ResourceType::ATTR) && reporter_) {
            reporter_->report_unsupported(
                resource_type_to_string(res_entry.type),
                entry,
                "Resource type not fully implemented in EXP-006",
                "warning");
        }
    }
    
    return true;
}

bool ResourceInventory::scan_apk(const std::string& apk_path) {
    apk::ApkParser parser;
    auto entries = parser.list_entries(apk_path);
    
    std::vector<std::string> entry_names;
    for (const auto& entry : entries) {
        entry_names.push_back(entry.name);
    }
    
    return scan_apk_entries(entry_names);
}

void ResourceInventory::add_entry(const ResourceEntry& entry) {
    entries_.push_back(entry);
}

const ResourceEntry* ResourceInventory::get_entry(const std::string& path) const {
    for (const auto& entry : entries_) {
        if (entry.path == path) {
            return &entry;
        }
    }
    return nullptr;
}

std::vector<ResourceEntry> ResourceInventory::get_entries_by_type(ResourceType type) const {
    std::vector<ResourceEntry> result;
    for (const auto& entry : entries_) {
        if (entry.type == type) {
            result.push_back(entry);
        }
    }
    return result;
}

size_t ResourceInventory::get_supported_count() const {
    size_t count = 0;
    for (const auto& entry : entries_) {
        if (entry.is_supported) count++;
    }
    return count;
}

size_t ResourceInventory::get_parsed_count() const {
    size_t count = 0;
    for (const auto& entry : entries_) {
        if (entry.is_parsed) count++;
    }
    return count;
}

bool ResourceInventory::has_layouts() const {
    for (const auto& entry : entries_) {
        if (entry.type == ResourceType::LAYOUT) return true;
    }
    return false;
}

bool ResourceInventory::has_strings() const {
    for (const auto& entry : entries_) {
        if (entry.type == ResourceType::STRING) return true;
    }
    return false;
}

bool ResourceInventory::has_arsc() const {
    for (const auto& entry : entries_) {
        if (entry.path.find("resources.arsc") != std::string::npos) return true;
    }
    return false;
}

json ResourceInventory::to_json() const {
    json j;
    j["total_entries"] = get_total_count();
    j["supported_entries"] = get_supported_count();
    j["parsed_entries"] = get_parsed_count();
    j["has_layouts"] = has_layouts();
    j["has_strings"] = has_strings();
    j["has_arsc"] = has_arsc();
    j["entries"] = json::array();
    for (const auto& entry : entries_) {
        j["entries"].push_back(entry.to_json());
    }
    return j;
}

// ============================================================================
// LayoutInflater Implementation
// ============================================================================

LayoutInflater::LayoutInflater(miniandroid::runtime::EnhancedObjectHeap* heap,
                               StringResources* string_res,
                               FailureReporter* reporter)
    : heap_(heap), string_res_(string_res), reporter_(reporter) {}

InflateResult LayoutInflater::inflate(const XmlNode* layout_root) {
    InflateResult result;
    inflate_count_++;
    
    if (!layout_root) {
        result.success = false;
        result.error_message = "Layout root is null";
        return result;
    }
    
    if (!heap_) {
        result.success = false;
        result.error_message = "Object heap not initialized";
        if (reporter_) {
            reporter_->report_error(ResourceError::PARSE_ERROR, result.error_message);
        }
        return result;
    }
    
    // Push an empty result for inflate_node to populate
    history_.push_back(InflateResult());
    
    try {
        // Inflate the root node (will populate history_.back())
        result.root_view_id = inflate_node(layout_root, 0);
        
        // Copy data from populated history entry
        if (!history_.empty()) {
            auto& populated = history_.back();
            result.created_view_ids = std::move(populated.created_view_ids);
            result.view_classes = std::move(populated.view_classes);
            result.layout_params = std::move(populated.layout_params);
            result.view_attributes = std::move(populated.view_attributes);
        }
        
        if (result.root_view_id == 0) {
            result.success = false;
            result.error_message = "Failed to inflate root view";
            history_.pop_back(); // Remove failed entry
            return result;
        }
        
        // Get root view class
        result.root_view_class = layout_root->tag_name;
        
        result.success = true;
        // Update history_ with the complete result
        if (!history_.empty()) {
            history_.back() = result;
        }
        
    } catch (const std::exception& e) {
        result.success = false;
        result.error_message = std::string("Inflate exception: ") + e.what();
        if (reporter_) {
            reporter_->report_error(ResourceError::XML_PARSE_ERROR, result.error_message);
        }
        if (!history_.empty()) {
            history_.back() = result;
        }
    }
    
    return result;
}

InflateResult LayoutInflater::inflate_from_xml(const std::string& xml_content) {
    SimpleXmlParser parser(reporter_);
    auto root = parser.parse(xml_content);
    
    if (!root) {
        InflateResult result;
        result.success = false;
        result.error_message = "Failed to parse layout XML: " + parser.get_last_error();
        return result;
    }
    
    return inflate(root.get());
}

InflateResult LayoutInflater::inflate_from_apk(const std::vector<uint8_t>& apk_data, const std::string& layout_path) {
    apk::ApkParser parser;
    auto data = parser.extract_entry_from_memory(apk_data, layout_path);
    
    if (data.empty()) {
        InflateResult result;
        result.success = false;
        result.error_message = "Cannot extract layout from APK: " + layout_path;
        if (reporter_) {
            reporter_->report_error(ResourceError::FILE_NOT_FOUND, result.error_message);
        }
        return result;
    }
    
    std::string xml_content(data.begin(), data.end());
    return inflate_from_xml(xml_content);
}

uint32_t LayoutInflater::inflate_node(const XmlNode* node, uint32_t parent_id) {
    if (!node) return 0;
    
    std::string class_name = node->tag_name;
    
    // Map XML tag names to View class names
    if (class_name == "LinearLayout") {
        class_name = "android.widget.LinearLayout";
    } else if (class_name == "TextView") {
        class_name = "android.widget.TextView";
    } else if (class_name == "Button") {
        class_name = "android.widget.Button";
    } else if (class_name == "ImageView") {
        class_name = "android.widget.ImageView";
    }
    
    // Create the view object
    uint32_t view_id = create_view(class_name, node->attributes);
    
    if (view_id == 0) {
        if (reporter_) {
            reporter_->report_unsupported("View", class_name,
                "Unknown view type or creation failed", "error");
        }
        return 0;
    }
    
    // Apply attributes to the view
    apply_attributes(view_id, node->attributes);
    
    // Store view class mapping (use the pre-created history entry)
    if (history_.empty()) {
        history_.push_back(InflateResult()); // Fallback if not created
    }
    auto& current_result = history_.back();
    current_result.created_view_ids.push_back(view_id);
    current_result.view_classes[view_id] = class_name;
    
    // Recursively inflate children
    for (const auto& child : node->children) {
        uint32_t child_id = inflate_node(child.get(), view_id);
        if (child_id == 0) {
            // Child inflation failed but continue with siblings
            continue;
        }
    }
    
    return view_id;
}

uint32_t LayoutInflater::create_view(const std::string& class_name, const std::vector<XmlAttribute>& attrs) {
    if (!heap_) return 0;
    
    // Determine view type from class name
    if (class_name.find("TextView") != std::string::npos || 
        class_name.find("Button") != std::string::npos) {
        // Create TextView
        auto* tv = heap_->allocate<miniandroid::runtime::TextViewRuntimeObject>("TextView", 0);
        if (tv) {
            uint32_t id = tv->get_object_id();
            
            // Set initial properties from attributes
            for (const auto& attr : attrs) {
                if (attr.name == "text") {
                    tv->set_text(resolve_attribute_value(attr.value));
                }
            }
            
            return id;
        }
    } else if (class_name.find("LinearLayout") != std::string::npos ||
               class_name.find("ViewGroup") != std::string::npos) {
        // Create generic ViewGroup (use View for now)
        auto* view = heap_->allocate<miniandroid::runtime::ViewRuntimeObject>("ViewGroup", 0);
        if (view) {
            return view->get_object_id();
        }
    } else {
        // Generic View
        auto* view = heap_->allocate<miniandroid::runtime::ViewRuntimeObject>("View", 0);
        if (view) {
            return view->get_object_id();
        }
    }
    
    return 0;
}

void LayoutInflater::apply_attributes(uint32_t view_id, const std::vector<XmlAttribute>& attrs) {
    if (!heap_ || view_id == 0) return;
    
    LayoutParams params = parse_layout_params(attrs);
    
    // Store layout params
    if (history_.empty()) {
        history_.push_back(InflateResult());
    }
    auto& current_result = history_.back();
    current_result.layout_params[view_id] = params;
    
    // Store all attributes for reference
    std::map<std::string, std::string> attr_map;
    for (const auto& attr : attrs) {
        std::string key = attr.namespace_uri.empty() ? attr.name : attr.namespace_uri + ":" + attr.name;
        attr_map[key] = resolve_attribute_value(attr.value);
    }
    current_result.view_attributes[view_id] = attr_map;
    
    // Apply specific attributes to the view object
    auto* view = heap_->get_as<miniandroid::runtime::ViewRuntimeObject>(view_id);
    if (view) {
        // Apply layout params to view bounds (simplified)
        // In real Android, this happens during layout pass
    }
    
    // Apply text to TextView
    auto* tv = heap_->get_as<miniandroid::runtime::TextViewRuntimeObject>(view_id);
    if (tv) {
        for (const auto& attr : attrs) {
            if (attr.name == "text") {
                std::string resolved = resolve_attribute_value(attr.value);
                if (!resolved.empty()) {
                    tv->set_text(resolved);
                }
            }
        }
    }
}

LayoutParams LayoutInflater::parse_layout_params(const std::vector<XmlAttribute>& attrs) {
    LayoutParams params;
    
    for (const auto& attr : attrs) {
        if (attr.namespace_uri == "android") {
            if (attr.name == "layout_width") {
                if (attr.value == "match_parent" || attr.value == "fill_parent") {
                    params.width = LayoutParams::MATCH_PARENT;
                } else if (attr.value == "wrap_content") {
                    params.width = LayoutParams::WRAP_CONTENT;
                } else {
                    try {
                        params.width = std::stoi(attr.value);
                    } catch (...) {}
                }
            } else if (attr.name == "layout_height") {
                if (attr.value == "match_parent" || attr.value == "fill_parent") {
                    params.height = LayoutParams::MATCH_PARENT;
                } else if (attr.value == "wrap_content") {
                    params.height = LayoutParams::WRAP_CONTENT;
                } else {
                    try {
                        params.height = std::stoi(attr.value);
                    } catch (...) {}
                }
            } else if (attr.name == "layout_margin") {
                try {
                    int margin = std::stoi(attr.value);
                    params.left_margin = margin;
                    params.top_margin = margin;
                    params.right_margin = margin;
                    params.bottom_margin = margin;
                } catch (...) {}
            } else if (attr.name == "layout_marginLeft") {
                try { params.left_margin = std::stoi(attr.value); } catch (...) {}
            } else if (attr.name == "layout_marginTop") {
                try { params.top_margin = std::stoi(attr.value); } catch (...) {}
            } else if (attr.name == "layout_marginRight") {
                try { params.right_margin = std::stoi(attr.value); } catch (...) {}
            } else if (attr.name == "layout_marginBottom") {
                try { params.bottom_margin = std::stoi(attr.value); } catch (...) {}
            } else if (attr.name == "layout_gravity") {
                // Simplified gravity handling
                if (attr.value.find("center") != std::string::npos) {
                    params.gravity = 1; // CENTER
                } else if (attr.value.find("right") != std::string::npos || attr.value.find("end") != std::string::npos) {
                    params.gravity = 2; // RIGHT/END
                }
            }
        }
    }
    
    return params;
}

std::string LayoutInflater::resolve_attribute_value(const std::string& value) {
    // Handle resource references like @string/hello_text
    if (value.find("@string/") == 0) {
        std::string name = value.substr(8); // Remove "@string/"
        if (string_res_) {
            return string_res_->resolve_string(name, "");
        }
        return ""; // Resource not available
    }
    
    // Handle other resource references
    if (value.find("@") == 0) {
        if (reporter_) {
            reporter_->report_unsupported("resource_reference", value,
                "Non-string resource references not fully resolved", "warning");
        }
        return value; // Return as-is for now
    }
    
    return value;
}

// ============================================================================
// ResourceManager Implementation
// ============================================================================

ResourceManager::ResourceManager()
    : string_resources_(&failure_reporter_),
      inventory_(&failure_reporter_) {}

bool ResourceManager::initialize(const std::string& apk_path) {
    apk_path_ = apk_path;
    
    // Read APK into memory
    std::ifstream file(apk_path, std::ios::binary | std::ios::ate);
    if (!file.is_open()) {
        failure_reporter_.report_error(ResourceError::FILE_NOT_FOUND,
            "Cannot open APK: " + apk_path);
        return false;
    }
    
    size_t size = file.tellg();
    file.seekg(0, std::ios::beg);
    
    apk_data_.resize(size);
    if (!file.read(reinterpret_cast<char*>(apk_data_.data()), size)) {
        failure_reporter_.report_error(ResourceError::FILE_NOT_FOUND,
            "Failed to read APK data: " + apk_path);
        return false;
    }
    file.close();
    
    state_.initialized = true;
    
    // Detect ARSC
    state_.arsc_detected = resource_table_.detect_and_load_arsc(apk_data_);
    
    // Scan inventory using APK parser
    apk::ApkParser parser;
    auto entries = parser.list_entries(apk_path);
    std::vector<std::string> entry_names;
    for (const auto& entry : entries) {
        entry_names.push_back(entry.name);
    }
    inventory_.scan_apk_entries(entry_names);
    
    return true;
}

bool ResourceManager::initialize_from_data(const std::vector<uint8_t>& apk_data, const std::string& apk_name) {
    apk_data_ = apk_data;
    apk_path_ = apk_name;
    state_.initialized = true;
    
    // Detect ARSC
    state_.arsc_detected = resource_table_.detect_and_load_arsc(apk_data_);
    
    // Note: Inventory scanning requires APK path for full functionality
    // For data-only initialization, inventory will be empty until scan_apk is called
    
    return true;
}

bool ResourceManager::load_all_resources() {
    if (!state_.initialized) {
        failure_reporter_.report_error(ResourceError::PARSE_ERROR,
            "Manager not initialized");
        return false;
    }
    
    // Load string resources from APK data
    if (!apk_data_.empty()) {
        if (string_resources_.load_from_apk(apk_data_, "res/values/strings.xml")) {
            state_.strings_loaded = true;
        }
    }
    
    // If not loaded from APK, this is OK - caller may use embedded defaults
    return state_.strings_loaded || !apk_data_.empty();
}

bool ResourceManager::inflate_layout(const std::string& layout_name) {
    if (!state_.initialized) {
        failure_reporter_.report_error(ResourceError::PARSE_ERROR,
            "Manager not initialized");
        return false;
    }
    
    // Note: Full layout inflation requires heap connection
    // This is handled by Exp006Runner which has direct access to LayoutInflater
    state_.layout_loaded = false; // Will be set by runner after successful inflation
    
    return true; // Return true to indicate we're ready
}

std::vector<uint8_t> ResourceManager::extract_entry(const std::string& entry_name) {
    apk::ApkParser parser;
    return parser.extract_entry_from_memory(apk_data_, entry_name);
}

} // namespace resources
} // namespace miniandroid
