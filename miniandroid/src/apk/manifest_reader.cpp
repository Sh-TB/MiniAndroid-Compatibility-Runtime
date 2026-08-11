/*
 * MiniAndroid Runtime v0.1 - Manifest Reader Implementation
 * EXP-001: HelloWorld Loader
 */

#include "manifest_reader.h"

#include <cstring>
#include <iostream>
#include <algorithm>

namespace miniandroid {
namespace apk {

// AXML magic number
constexpr uint32_t AXML_MAGIC = 0x00080003;

// String pool flags
constexpr uint32_t STRING_POOL_UTF8_FLAG = 0x00000100;

ManifestReader::ManifestReader() : verbose_(false), depth_(0) {
}

ManifestReader::~ManifestReader() {
}

ManifestInfo ManifestReader::parse(const std::vector<uint8_t>& data) {
    result_ = ManifestInfo();
    strings_.clear();
    resource_ids_.clear();
    namespace_stack_.clear();
    depth_ = 0;
    in_activity_ = false;
    
    if (data.empty()) {
        result_.error_message = "Empty manifest data";
        result_.parse_success = false;
        return result_;
    }
    
    const uint8_t* ptr = data.data();
    size_t size = data.size();
    
    // Check if this is plain XML (not binary AXML)
    // Plain XML starts with '<?' or '<', while AXML starts with 0x00080003
    bool is_plain_xml = false;
    if (size >= 2 && (ptr[0] == '<')) {
        is_plain_xml = true;
        log("Detected plain XML format");
    } else if (size >= 4) {
        uint32_t magic = *reinterpret_cast<const uint32_t*>(ptr);
        if (magic != AXML_MAGIC) {
            // Not AXML magic - check if it looks like text
            if (ptr[0] == '<' || (size >= 5 && strncmp(reinterpret_cast<const char*>(ptr), "<?xml", 5) == 0)) {
                is_plain_xml = true;
                log("Detected plain XML format (fallback)");
            }
        }
    }
    
    // Parse plain XML if detected
    if (is_plain_xml) {
        return parse_plain_xml(data);
    }
    
    // Otherwise parse as binary AXML
    if (size < sizeof(AxmlHeader)) {
        result_.error_message = "Data too small for AXML header";
        result_.parse_success = false;
        return result_;
    }
    
    // Parse main header
    if (!parse_header(ptr, size)) {
        result_.parse_success = false;
        return result_;
    }
    
    // Parse chunks
    size_t offset = sizeof(AxmlHeader);
    
    while (offset < size) {
        if (offset + sizeof(AxmlChunkHeader) > size) {
            break;
        }
        
        const AxmlChunkHeader* chunk = reinterpret_cast<const AxmlChunkHeader*>(ptr + offset);
        
        if (chunk->size < sizeof(AxmlChunkHeader) || offset + chunk->size > size) {
            log("Invalid chunk size at offset " + std::to_string(offset));
            break;
        }
        
        switch (static_cast<AxmlToken>(chunk->type)) {
            case AxmlToken::START_DOCUMENT:
                log("Start document");
                break;
                
            case AxmlToken::END_DOCUMENT:
                log("End document");
                break;
                
            case AxmlToken::START_NAMESPACE:
            case AxmlToken::END_NAMESPACE:
            case AxmlToken::START_ELEMENT:
            case AxmlToken::END_ELEMENT:
            case AxmlToken::CDATA:
                parse_element(ptr, size, offset);
                break;
                
            default:
                // Check for string pool or resource IDs by position
                if (offset == sizeof(AxmlHeader)) {
                    // First chunk should be string pool
                    if (!parse_string_pool(ptr + offset, chunk->size)) {
                        log("Failed to parse string pool");
                    }
                } else if (!strings_.empty() && resource_ids_.empty()) {
                    // Might be resource IDs
                    parse_resource_ids(ptr + offset, chunk->size);
                }
                break;
        }
        
        offset += chunk->size;
    }
    
    result_.parse_success = true;
    log("Manifest parsing complete. Package: " + result_.package_name);
    
    return result_;
}

bool ManifestReader::parse_header(const uint8_t* data, size_t size) {
    const AxmlHeader* header = reinterpret_cast<const AxmlHeader*>(data);
    
    if (header->magic != AXML_MAGIC) {
        result_.error_message = "Invalid AXML magic number";
        log(result_.error_message);
        return false;
    }
    
    if (header->header.type != static_cast<uint16_t>(AxmlToken::START_DOCUMENT)) {
        result_.error_message = "Invalid AXML header type";
        log(result_.error_message);
        return false;
    }
    
    log("AXML header valid, document size: " + std::to_string(header->header.size));
    return true;
}

bool ManifestReader::parse_string_pool(const uint8_t* chunk, size_t size) {
    if (size < sizeof(AxmlStringPoolHeader)) {
        return false;
    }
    
    const AxmlStringPoolHeader* sp_header = reinterpret_cast<const AxmlStringPoolHeader*>(chunk);
    
    uint32_t string_count = sp_header->string_count;
    bool is_utf8 = (sp_header->flags & STRING_POOL_UTF8_FLAG) != 0;
    
    log("String pool: " + std::to_string(string_count) + " strings, UTF8=" + 
        (is_utf8 ? "true" : "false"));
    
    strings_.reserve(string_count);
    
    // Strings start after the header
    const uint8_t* strings_start = chunk + sp_header->strings_start;
    const uint8_t* strings_end = chunk + size;
    
    size_t offset = 0;
    
    for (uint32_t i = 0; i < string_count && (strings_start + offset) < strings_end; i++) {
        size_t str_length = 0;
        size_t bytes_consumed = decode_string_length(strings_start, offset, str_length, is_utf8);
        offset += bytes_consumed;
        
        if ((strings_start + offset + str_length) > strings_end) {
            log("String " + std::to_string(i) + " extends beyond pool");
            break;
        }
        
        if (is_utf8) {
            std::string str(reinterpret_cast<const char*>(strings_start + offset), str_length);
            strings_.push_back(str);
        } else {
            // UTF-16 - convert to UTF-8 (simplified)
            std::string utf8_str;
            const char16_t* utf16_ptr = reinterpret_cast<const char16_t*>(strings_start + offset);
            for (size_t j = 0; j < str_length; j++) {
                char16_t c = utf16_ptr[j];
                if (c < 0x80) {
                    utf8_str += static_cast<char>(c);
                } else if (c < 0x800) {
                    utf8_str += static_cast<char>(0xC0 | (c >> 6));
                    utf8_str += static_cast<char>(0x80 | (c & 0x3F));
                } else {
                    utf8_str += static_cast<char>(0xE0 | (c >> 12));
                    utf8_str += static_cast<char>(0x80 | ((c >> 6) & 0x3F));
                    utf8_str += static_cast<char>(0x80 | (c & 0x3F));
                }
            }
            strings_.push_back(utf8_str);
        }
        
        offset += is_utf8 ? str_length : str_length * 2;
        
        // Skip null terminator(s)
        if (is_utf8) {
            offset++;  // 1 byte null terminator
        } else {
            offset += 2;  // 2 byte null terminator
        }
        
        // Align to 4 bytes
        while (offset % 4 != 0) {
            offset++;
        }
    }
    
    log("Parsed " + std::to_string(strings_.size()) + " strings from pool");
    return true;
}

bool ManifestReader::parse_resource_ids(const uint8_t* chunk, size_t size) {
    if (size < sizeof(AxmlResourceIdsHeader)) {
        return false;
    }
    
    const AxmlResourceIdsHeader* res_header = reinterpret_cast<const AxmlResourceIdsHeader*>(chunk);
    
    size_t id_count = (size - sizeof(AxmlResourceIdsHeader)) / sizeof(uint32_t);
    resource_ids_.resize(id_count);
    
    std::memcpy(resource_ids_.data(), chunk + sizeof(AxmlResourceIdsHeader), 
                id_count * sizeof(uint32_t));
    
    log("Parsed " + std::to_string(id_count) + " resource IDs");
    return true;
}

bool ManifestReader::parse_element(const uint8_t* data, size_t size, size_t& offset) {
    if (offset + sizeof(AxmlChunkHeader) > size) {
        return false;
    }
    
    const AxmlChunkHeader* chunk = reinterpret_cast<const AxmlChunkHeader*>(data + offset);
    AxmlToken token_type = static_cast<AxmlToken>(chunk->type);
    
    switch (token_type) {
        case AxmlToken::START_NAMESPACE: {
            if (offset + sizeof(AxmlStartNamespace) > size) return false;
            
            const AxmlStartNamespace* ns = reinterpret_cast<const AxmlStartNamespace*>(data + offset);
            std::string prefix = get_string(ns->prefix_index);
            std::string uri = get_string(ns->uri_index);
            
            push_namespace(prefix, uri);
            log("NS Start: " + prefix + " = " + uri);
            break;
        }
        
        case AxmlToken::END_NAMESPACE: {
            if (offset + sizeof(AxmlEndNamespace) > size) return false;
            
            const AxmlEndNamespace* ns = reinterpret_cast<const AxmlEndNamespace*>(data + offset);
            std::string prefix = get_string(ns->prefix_index);
            
            pop_namespace();
            log("NS End: " + prefix);
            break;
        }
        
        case AxmlToken::START_ELEMENT: {
            if (offset + sizeof(AxmlStartElement) > size) return false;
            
            const AxmlStartElement* elem = reinterpret_cast<const AxmlStartElement*>(data + offset);
            
            std::string ns = resolve_namespace(elem->namespace_index);
            std::string name = get_string(elem->name_index);
            
            // Parse attributes
            std::vector<AxmlAttribute> attrs(elem->attribute_count);
            size_t attr_offset = offset + sizeof(AxmlStartElement) + 
                                 (elem->attribute_ids_offset ? 0 : elem->attribute_count * sizeof(uint32_t));
            
            // Attributes follow the element structure
            const uint8_t* attr_ptr = data + offset + sizeof(AxmlStartElement);
            
            // Skip attribute resource IDs if present
            if (elem->attribute_count > 0) {
                attr_ptr += elem->attribute_count * sizeof(uint32_t);  // Resource IDs
            }
            
            for (uint16_t i = 0; i < elem->attribute_count; i++) {
                if (attr_ptr + sizeof(AxmlAttribute) <= data + size) {
                    std::memcpy(&attrs[i], attr_ptr, sizeof(AxmlAttribute));
                    attr_ptr += sizeof(AxmlAttribute);
                }
            }
            
            process_start_element(ns, name, attrs);
            depth_++;
            break;
        }
        
        case AxmlToken::END_ELEMENT: {
            if (offset + sizeof(AxmlEndElement) > size) return false;
            
            const AxmlEndElement* elem = reinterpret_cast<const AxmlEndElement*>(data + offset);
            
            std::string ns = resolve_namespace(elem->namespace_index);
            std::string name = get_string(elem->name_index);
            
            process_end_element(ns, name);
            depth_--;
            break;
        }
        
        case AxmlToken::CDATA: {
            // CDATA section - skip for now
            log("CDATA section found");
            break;
        }
        
        default:
            log("Unknown token type: " + std::to_string(chunk->type));
            break;
    }
    
    return true;
}

std::string ManifestReader::get_string(size_t index) const {
    if (index < strings_.size()) {
        return strings_[index];
    }
    return "";  // Empty string for invalid index
}

size_t ManifestReader::decode_string_length(const uint8_t* data, size_t offset, 
                                            size_t& out_length, bool utf8) {
    if (utf8) {
        // UTF-8: length is 1 or 2 bytes
        uint8_t first = data[offset];
        if ((first & 0x80) == 0) {
            out_length = first;
            return 1;
        } else {
            uint16_t len = (first & 0x7F) | (static_cast<uint16_t>(data[offset + 1]) << 7);
            out_length = len;
            return 2;
        }
    } else {
        // UTF-16: length is 1 or 2 bytes (gives character count)
        uint8_t first = data[offset];
        if ((first & 0x80) == 0) {
            out_length = first;
            return 1;
        } else {
            uint16_t len = (first & 0x7F) | (static_cast<uint16_t>(data[offset + 1]) << 7);
            out_length = len;
            return 2;
        }
    }
}

void ManifestReader::push_namespace(const std::string& prefix, const std::string& uri) {
    if (namespace_stack_.empty()) {
        namespace_stack_.push_back({{prefix, uri}});
    } else {
        namespace_stack_.back()[prefix] = uri;
        namespace_stack_.push_back(namespace_stack_.back());
    }
}

void ManifestReader::pop_namespace() {
    if (!namespace_stack_.empty()) {
        namespace_stack_.pop_back();
    }
}

std::string ManifestReader::resolve_namespace(uint32_t ns_index) const {
    if (ns_index == 0xFFFFFFFF) {
        return "";  // No namespace
    }
    return get_string(ns_index);
}

void ManifestReader::process_start_element(const std::string& ns, const std::string& name,
                                           const std::vector<AxmlAttribute>& attrs) {
    std::string full_path = std::string(depth_ * 2, ' ') + (ns.empty() ? "" : ns + ":") + name;
    log("Element: " + full_path);
    
    // Handle manifest element
    if (name == "manifest") {
        result_.package_name = get_attribute_value(attrs, "package");
        result_.version_name = get_attribute_value(attrs, "versionName");
        result_.version_code = get_attribute_int(attrs, "versionCode");
        result_.has_application = true;
        log("Package: " + result_.package_name);
    }
    
    // Handle uses-sdk element
    if (name == "uses-sdk") {
        result_.min_sdk_version = get_attribute_value(attrs, "minSdkVersion");
        result_.target_sdk_version = get_attribute_value(attrs, "targetSdkVersion");
        log("SDK: min=" + result_.min_sdk_version + ", target=" + result_.target_sdk_version);
    }
    
    // Handle application element
    if (name == "application") {
        result_.application_label = get_attribute_value(attrs, "label");
        log("Application label: " + result_.application_label);
    }
    
    // Handle activity element
    if (name == "activity") {
        current_activity_name_ = get_attribute_value(attrs, "name");
        activity_has_main_action_ = false;
        activity_has_launcher_category_ = false;
        in_activity_ = true;
        
        ManifestInfo::ActivityInfo act_info;
        act_info.name = current_activity_name_;
        result_.activities.push_back(act_info);
        
        log("Activity: " + current_activity_name_);
    }
    
    // Handle intent-filter elements inside activity
    if (in_activity_) {
        if (name == "action") {
            std::string action_name = get_attribute_value(attrs, "name");
            if (action_name == "android.intent.action.MAIN" || action_name == "MAIN") {
                activity_has_main_action_ = true;
                log("Found MAIN action");
            }
        }
        
        if (name == "category") {
            std::string category_name = get_attribute_value(attrs, "name");
            if (category_name == "android.intent.category.LAUNCHER" || category_name == "LAUNCHER") {
                activity_has_launcher_category_ = true;
                log("Found LAUNCHER category");
            }
        }
    }
    
    // Handle permission elements
    if (name == "uses-permission") {
        std::string perm = get_attribute_value(attrs, "name");
        if (!perm.empty()) {
            result_.permissions.push_back(perm);
            log("Permission: " + perm);
        }
    }
    
    // Handle uses-feature elements
    if (name == "uses-feature") {
        std::string feature = get_attribute_value(attrs, "name");
        if (!feature.empty()) {
            result_.uses_features.push_back(feature);
        }
    }
}

void ManifestReader::process_end_element(const std::string& ns, const std::string& name) {
    // When closing an activity, check if it's the main launcher
    if (name == "activity" && in_activity_) {
        if (activity_has_main_action_ && activity_has_launcher_category_) {
            result_.main_activity = current_activity_name_;
            
            // Convert to full class name if needed
            if (!current_activity_name_.empty()) {
                if (current_activity_name_[0] == '.') {
                    result_.main_activity_full = result_.package_name + current_activity_name_;
                } else if (current_activity_name_.find('.') == std::string::npos) {
                    result_.main_activity_full = result_.package_name + "." + current_activity_name_;
                } else {
                    result_.main_activity_full = current_activity_name_;
                }
            }
            
            // Mark as main activity in activities list
            for (auto& act : result_.activities) {
                if (act.name == current_activity_name_) {
                    act.is_main_activity = true;
                    act.is_launcher = true;
                    break;
                }
            }
            
            log("Main Activity: " + result_.main_activity + " (" + result_.main_activity_full + ")");
        }
        
        in_activity_ = false;
        current_activity_name_.clear();
    }
}

std::string ManifestReader::get_attribute_value(const std::vector<AxmlAttribute>& attrs,
                                                 const std::string& name) const {
    for (const auto& attr : attrs) {
        std::string attr_name = get_string(attr.name_index);
        
        // Try with and without android: prefix
        if (attr_name == name || attr_name == "android:" + name) {
            if (attr.value_type == static_cast<uint32_t>(AxmlDataType::STRING)) {
                return get_string(attr.value_string_index);
            } else if (attr.value_type == static_cast<uint32_t>(AxmlDataType::REFERENCE)) {
                return "@0x" + int_to_hex(attr.value_data);
            } else if (attr.value_type == static_cast<uint32_t>(AxmlDataType::INT) ||
                       attr.value_type == static_cast<uint32_t>(AxmlDataType::ATTRIBUTE_INT)) {
                return std::to_string(static_cast<int32_t>(attr.value_data));
            }
        }
    }
    return "";
}

int ManifestReader::get_attribute_int(const std::vector<AxmlAttribute>& attrs,
                                       const std::string& name) const {
    std::string value = get_attribute_value(attrs, name);
    if (!value.empty()) {
        try {
            return std::stoi(value);
        } catch (...) {
            return 0;
        }
    }
    return 0;
}

void ManifestReader::log(const std::string& message) {
    if (verbose_) {
        std::cerr << "[ManifestReader] " << message << std::endl;
    }
}

std::string ManifestReader::int_to_hex(uint32_t value) {
    const char* hex_digits = "0123456789abcdef";
    std::string result(8, '0');
    for (int i = 7; i >= 0; i--) {
        result[i] = hex_digits[value & 0xF];
        value >>= 4;
    }
    return result;
}

ManifestInfo ManifestReader::parse_plain_xml(const std::vector<uint8_t>& data) {
    // Convert to string
    std::string xml_content(data.begin(), data.end());
    log("Parsing plain XML manifest, size: " + std::to_string(xml_content.size()));
    
    // Simple state machine parser for AndroidManifest.xml
    // This handles basic structure: manifest -> application -> activity
    
    enum class XmlState {
        ROOT,
        MANIFEST,
        APPLICATION,
        ACTIVITY,
        INTENT_FILTER,
        ACTION,
        CATEGORY,
        UNKNOWN
    };
    
    std::vector<XmlState> state_stack;
    state_stack.push_back(XmlState::ROOT);
    
    size_t pos = 0;
    while (pos < xml_content.size()) {
        // Find next tag
        size_t tag_start = xml_content.find('<', pos);
        if (tag_start == std::string::npos) break;
        
        size_t tag_end = xml_content.find('>', tag_start);
        if (tag_end == std::string::npos) break;
        
        std::string tag = xml_content.substr(tag_start, tag_end - tag_start + 1);
        pos = tag_end + 1;
        
        // Check for end tag
        if (tag.find("</") == 0) {
            // End tag
            if (!state_stack.empty()) {
                state_stack.pop_back();
            }
            if (state_stack.back() == XmlState::ACTIVITY) {
                in_activity_ = false;
            }
            continue;
        }
        
        // Check for self-closing or start tag
        bool self_closing = (tag.find("/>") != std::string::npos);
        
        // Extract tag name
        std::string tag_name;
        size_t name_start = tag.find_first_not_of("< \t");
        if (name_start != std::string::npos) {
            size_t name_end = tag.find_first_of(" \t/>", name_start);
            if (name_end != std::string::npos) {
                tag_name = tag.substr(name_start, name_end - name_start);
            } else {
                tag_name = tag.substr(name_start);
            }
        }
        
        // Extract attributes
        auto extract_attr = [&](const std::string& attr) -> std::string {
            std::string search = attr + "=\"";
            size_t attr_pos = tag.find(search);
            if (attr_pos != std::string::npos) {
                size_t val_start = attr_pos + search.length();
                size_t val_end = tag.find('"', val_start);
                if (val_end != std::string::npos) {
                    return tag.substr(val_start, val_end - val_start);
                }
            }
            return "";
        };
        
        // Handle different elements
        if (tag_name == "manifest") {
            state_stack.push_back(XmlState::MANIFEST);
            result_.package_name = extract_attr("package");
            std::string ver_code = extract_attr("android:versionCode");
            if (!ver_code.empty()) {
                try { result_.version_code = std::stoi(ver_code); } catch (...) {}
            }
            result_.version_name = extract_attr("android:versionName");
            log("Found manifest, package: " + result_.package_name);
            
        } else if (tag_name == "application") {
            state_stack.push_back(XmlState::APPLICATION);
            result_.application_label = extract_attr("android:label");
            log("Found application");
            
        } else if (tag_name == "activity") {
            state_stack.push_back(XmlState::ACTIVITY);
            in_activity_ = true;
            current_activity_name_ = extract_attr("android:name");
            activity_has_main_action_ = false;
            activity_has_launcher_category_ = false;
            
            ManifestInfo::ActivityInfo act;
            act.name = current_activity_name_;
            result_.activities.push_back(act);
            log("Found activity: " + current_activity_name_);
            
        } else if (tag_name == "intent-filter" && in_activity_) {
            state_stack.push_back(XmlState::INTENT_FILTER);
            
        } else if (tag_name == "action" && in_activity_) {
            std::string action_name = extract_attr("android:name");
            if (action_name == "android.intent.action.MAIN") {
                activity_has_main_action_ = true;
                log("Found MAIN action");
            }
            
        } else if (tag_name == "category" && in_activity_) {
            std::string category_name = extract_attr("android:name");
            if (category_name == "android.intent.category.LAUNCHER") {
                activity_has_launcher_category_ = true;
                log("Found LAUNCHER category");
            }
        }
        
        // Check for main activity after processing category
        if (tag_name == "category" && activity_has_main_action_ && activity_has_launcher_category_) {
            if (!current_activity_name_.empty()) {
                result_.main_activity = current_activity_name_;
                
                // Build fully qualified name
                if (!current_activity_name_.empty() && current_activity_name_[0] == '.') {
                    result_.main_activity_full = result_.package_name + current_activity_name_;
                } else {
                    result_.main_activity_full = current_activity_name_;
                }
                
                // Mark as launcher activity
                for (auto& act : result_.activities) {
                    if (act.name == current_activity_name_) {
                        act.is_main_activity = true;
                        act.is_launcher = true;
                        break;
                    }
                }
                
                log("Main Activity identified: " + result_.main_activity_full);
            }
        }
        
        // Pop state if self-closing
        if (self_closing && !state_stack.empty() && state_stack.back() != XmlState::ROOT) {
            if (state_stack.back() == XmlState::ACTIVITY) {
                in_activity_ = false;
            }
            state_stack.pop_back();
        }
    }
    
    result_.parse_success = true;
    log("Plain XML manifest parsing complete. Package: " + result_.package_name + 
        ", Main Activity: " + result_.main_activity_full);
    
    return result_;
}

} // namespace apk
} // namespace miniandroid
