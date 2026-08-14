/*
 * MiniAndroid Runtime v0.1 - DEX Parser Implementation
 * EXP-001: HelloWorld Loader
 */

#include "dex_parser.h"

#include <fstream>
#include <iostream>
#include <sstream>
#include <cstring>
#include <algorithm>

// For Adler32 checksum
#include <zlib.h>

namespace miniandroid {
namespace dex {

DexParser::DexParser() : verbose_(false), current_data_(nullptr), current_size_(0) {
}

DexParser::~DexParser() {
}

DexReport DexParser::parse(const std::string& path) {
    // Read file
    std::ifstream file(path, std::ios::binary | std::ios::ate);
    if (!file.is_open()) {
        DexReport report;
        report.is_valid = false;
        report.validation_error = "Cannot open DEX file: " + path;
        return report;
    }
    
    auto size = file.tellg();
    file.seekg(0, std::ios::beg);
    
    std::vector<uint8_t> data(static_cast<size_t>(size));
    if (!file.read(reinterpret_cast<char*>(data.data()), size)) {
        DexReport report;
        report.is_valid = false;
        report.validation_error = "Failed to read DEX file";
        return report;
    }
    
    DexReport report = parse_data(data, path);
    report.dex_path = path;
    
    return report;
}

DexReport DexParser::parse_data(const std::vector<uint8_t>& data, const std::string& source) {
    if (data.empty()) {
        DexReport report;
        report.is_valid = false;
        report.validation_error = "Empty DEX data";
        return report;
    }
    
    return parse_raw(data.data(), data.size(), source);
}

DexReport DexParser::parse_raw(const uint8_t* data, size_t size, const std::string& source) {
    DexReport report;
    report.dex_path = source;
    
    // Reset state
    strings_.clear();
    types_.clear();
    protos_.clear();
    methods_.clear();
    fields_.clear();
    current_data_ = data;
    current_size_ = size;
    
    // Minimum check
    if (size < sizeof(DexHeader)) {
        report.is_valid = false;
        report.validation_error = "Data too small for DEX header";
        return report;
    }
    
    // Parse header
    std::memcpy(&report.header, data, sizeof(DexHeader));
    
    // Validate header
    auto validation_error = validate_header(report.header);
    if (validation_error != DexError::NONE) {
        report.is_valid = false;
        report.validation_error = last_error_;
        return report;
    }
    
    // Extract version
    report.dex_version = std::string(reinterpret_cast<const char*>(report.header.magic + 4), 3);
    log("DEX version: " + report.dex_version);
    
    // Verify checksum (warning only)
    if (!verify_checksum(data, size, report.header)) {
        log("Warning: Checksum mismatch (file may be modified)");
    }
    
    // Verify signature (warning only)
    if (!verify_signature(data, size, report.header)) {
        log("Warning: Signature mismatch");
    }
    
    // Parse all sections
    bool success = true;
    
    success &= parse_string_pool(data, report);
    success &= parse_types(data, report);
    success &= parse_prototypes(data, report);
    success &= parse_fields(data, report);
    success &= parse_methods(data, report);
    success &= parse_class_defs(data, report);
    
    report.is_valid = success;
    
    if (success) {
        log("DEX parsing complete: " + std::to_string(report.classes_count) + " classes, " +
            std::to_string(report.methods_count) + " methods");
    } else {
        report.validation_error = "Error during DEX parsing";
    }
    
    return report;
}

DexError DexParser::validate_header(const DexHeader& header) {
    // Check magic
    if (std::memcmp(header.magic, DEX_MAGIC_035, 8) != 0 &&
        std::memcmp(header.magic, DEX_MAGIC_036, 8) != 0 &&
        std::memcmp(header.magic, DEX_MAGIC_037, 8) != 0 &&
        std::memcmp(header.magic, DEX_MAGIC_038, 8) != 0 &&
        std::memcmp(header.magic, DEX_MAGIC_039, 8) != 0) {
        
        char magic_hex[17];
        for (int i = 0; i < 8; i++) {
            snprintf(magic_hex + i*2, 3, "%02x", header.magic[i]);
        }
        magic_hex[16] = '\0';
        
        last_error_ = "Invalid DEX magic: " + std::string(magic_hex);
        return DexError::INVALID_MAGIC;
    }
    
    // Check header size
    if (header.header_size != 0x70) {
        last_error_ = "Invalid header size: " + std::to_string(header.header_size);
        return DexError::PARSE_ERROR;
    }
    
    // Check endian tag
    if (header.endian_tag != 0x12345678) {
        last_error_ = "Invalid endian tag (wrong endianness?)";
        return DexError::ENDIAN_TAG_INVALID;
    }
    
    // Check file size consistency
    if (header.file_size > current_size_) {
        last_error_ = "File size in header exceeds actual data";
        return DexError::FILE_TOO_SMALL;
    }
    
    return DexError::NONE;
}

bool DexParser::verify_checksum(const uint8_t* data, size_t size, const DexHeader& header) {
    // Checksum covers everything except the checksum field itself
    // and is stored at offset 8, covering bytes 12 to end
    
    if (size < 12) return false;
    
    uLong adler = adler32(0L, Z_NULL, 0);
    adler = adler32(adler, data + 12, static_cast<uInt>(size - 12));
    
    return (static_cast<uint32_t>(adler) == header.checksum);
}

bool DexParser::verify_signature(const uint8_t* data, size_t size, const DexHeader& header) {
    // SHA-1 hash covers everything except signature field
    // Signature is at offset 32, 20 bytes long
    
    if (size < 52) return false;
    
    // Note: Full SHA-1 implementation would go here
    // For now, we just verify the field exists
    return true;  // Skip full verification for v0.1
}

bool DexParser::parse_string_pool(const uint8_t* data, DexReport& report) {
    if (report.header.string_ids_size == 0) {
        log("No strings in DEX");
        return true;
    }
    
    // Read string IDs (array of offsets)
    std::vector<DexStringId> string_ids(report.header.string_ids_size);
    size_t ids_offset = report.header.string_ids_off;
    
    if (ids_offset + string_ids.size() * sizeof(DexStringId) > current_size_) {
        last_error_ = "String IDs extend beyond file";
        return false;
    }
    
    std::memcpy(string_ids.data(), data + ids_offset, 
                string_ids.size() * sizeof(DexStringId));
    
    // Read each string
    strings_.reserve(string_ids.size());
    
    for (const auto& str_id : string_ids) {
        if (str_id.string_data_off >= current_size_) {
            strings_.push_back("<invalid offset>");
            continue;
        }
        
        std::string str = read_dex_string(data, str_id.string_data_off);
        strings_.push_back(str);
    }
    
    report.strings_count = static_cast<uint32_t>(strings_.size());
    report.strings = strings_;
    
    log("Parsed " + std::to_string(strings_.size()) + " strings");
    return true;
}

bool DexParser::parse_types(const uint8_t* data, DexReport& report) {
    if (report.header.type_ids_size == 0) {
        log("No types in DEX");
        return true;
    }
    
    // Read type IDs (array of string indices)
    std::vector<DexTypeId> type_ids(report.header.type_ids_size);
    size_t ids_offset = report.header.type_ids_off;
    
    if (ids_offset + type_ids.size() * sizeof(DexTypeId) > current_size_) {
        last_error_ = "Type IDs extend beyond file";
        return false;
    }
    
    std::memcpy(type_ids.data(), data + ids_offset,
                type_ids.size() * sizeof(DexTypeId));
    
    // Convert to type descriptors
    types_.reserve(type_ids.size());
    
    for (const auto& type_id : type_ids) {
        std::string type = get_string(type_id.descriptor_idx);
        types_.push_back(type);
    }
    
    report.types_count = static_cast<uint32_t>(types_.size());
    report.types = types_;  // Copy types to report for interpreter use
    
    log("Parsed " + std::to_string(types_.size()) + " types");
    return true;
}

bool DexParser::parse_prototypes(const uint8_t* data, DexReport& report) {
    if (report.header.proto_ids_size == 0) {
        return true;
    }
    
    std::vector<DexProtoId> proto_ids(report.header.proto_ids_size);
    size_t protos_offset = report.header.proto_ids_off;
    
    if (protos_offset + proto_ids.size() * sizeof(DexProtoId) > current_size_) {
        last_error_ = "Proto IDs extend beyond file";
        return false;
    }
    
    std::memcpy(proto_ids.data(), data + protos_offset,
                proto_ids.size() * sizeof(DexProtoId));
    
    protos_ = proto_ids;
    report.prototypes_count = static_cast<uint32_t>(proto_ids.size());
    
    log("Parsed " + std::to_string(proto_ids.size()) + " prototypes");
    return true;
}

bool DexParser::parse_fields(const uint8_t* data, DexReport& report) {
    if (report.header.field_ids_size == 0) {
        return true;
    }
    
    std::vector<DexFieldId> field_ids(report.header.field_ids_size);
    size_t fields_offset = report.header.field_ids_off;
    
    if (fields_offset + field_ids.size() * sizeof(DexFieldId) > current_size_) {
        last_error_ = "Field IDs extend beyond file";
        return false;
    }
    
    std::memcpy(field_ids.data(), data + fields_offset,
                field_ids.size() * sizeof(DexFieldId));
    
    fields_ = field_ids;
    report.fields_count = static_cast<uint32_t>(field_ids.size());
    
    log("Parsed " + std::to_string(field_ids.size()) + " fields");
    return true;
}

bool DexParser::parse_methods(const uint8_t* data, DexReport& report) {
    if (report.header.method_ids_size == 0) {
        return true;
    }
    
    std::vector<DexMethodId> method_ids(report.header.method_ids_size);
    size_t methods_offset = report.header.method_ids_off;
    
    if (methods_offset + method_ids.size() * sizeof(DexMethodId) > current_size_) {
        last_error_ = "Method IDs extend beyond file";
        return false;
    }
    
    std::memcpy(method_ids.data(), data + methods_offset,
                method_ids.size() * sizeof(DexMethodId));
    
    methods_ = method_ids;
    report.methods_count = static_cast<uint32_t>(method_ids.size());
    
    log("Parsed " + std::to_string(method_ids.size()) + " method IDs");
    return true;
}

bool DexParser::parse_class_defs(const uint8_t* data, DexReport& report) {
    if (report.header.class_defs_size == 0) {
        log("No class definitions in DEX");
        return true;
    }
    
    std::vector<DexClassDef> class_defs(report.header.class_defs_size);
    size_t defs_offset = report.header.class_defs_off;
    
    // ====================================================================
    // EXP-031.6 DEBUG: Trace class_def parsing
    // ====================================================================
    log("=== EXP-031.6 CLASS_DEF PARSING ===");
    log("class_defs_size: " + std::to_string(report.header.class_defs_size));
    log("class_defs_off: 0x" + std::to_string(defs_offset));
    log("file_size: 0x" + std::to_string(current_size_));
    
    if (defs_offset + class_defs.size() * sizeof(DexClassDef) > current_size_) {
        last_error_ = "Class definitions extend beyond file";
        log("ERROR: Class defs extend beyond file!");
        return false;
    }
    
    log("Reading " + std::to_string(class_defs.size()) + " class_defs (" + 
        std::to_string(sizeof(DexClassDef)) + " bytes each)...");
    
    std::memcpy(class_defs.data(), data + defs_offset,
                class_defs.size() * sizeof(DexClassDef));
    
    // Parse each class
    report.classes.reserve(class_defs.size());
    
    for (size_t i = 0; i < class_defs.size(); i++) {
        const auto& class_def = class_defs[i];
        ClassInfo info;
        
        // ====================================================================
        // EXP-031.6 DEBUG: Log raw class_def fields
        // ====================================================================
        log("CLASS_DEF[" + std::to_string(i) + "] @ offset 0x" + 
            std::to_string(defs_offset + i * sizeof(DexClassDef)) + ":");
        log("  class_idx: " + std::to_string(class_def.class_idx) + 
            " (max valid: " + std::to_string(report.header.type_ids_size) + ")");
        log("  access_flags: 0x" + std::to_string(class_def.access_flags));
        log("  superclass_idx: " + std::to_string(class_def.superclass_idx));
        log("  class_data_off: 0x" + std::to_string(class_def.class_data_off));
        
        // Get class name from type index
        info.name = get_type(class_def.class_idx);
        log("  → Resolved name: [" + info.name + "]");
        
        // Get superclass name
        if (class_def.superclass_idx != 0xFFFFFFFF) {
            info.superclass_name = get_type(class_def.superclass_idx);
        }
        
        // Source file
        if (class_def.source_file_idx != 0xFFFFFFFF) {
            info.source_file = get_string(class_def.source_file_idx);
        }
        
        info.access_flags = class_def.access_flags;
        
        // Parse class data (fields and methods)
        if (class_def.class_data_off != 0 && class_def.class_data_off < current_size_) {
            log("  → Parsing class_data at 0x" + std::to_string(class_def.class_data_off));
            parse_class_data(data, class_def, info);
        } else {
            log("  → NO class_data (off=0x" + std::to_string(class_def.class_data_off) + 
                ", size=0x" + std::to_string(current_size_) + ")");
        }
        
        report.classes.push_back(info);
        
        log("  → Result: " + std::to_string(info.direct_methods.size()) + " direct methods, " +
            std::to_string(info.virtual_methods.size()) + " virtual methods");
    }
    
    log("=== END CLASS_DEF PARSING ===");
    
    report.classes_count = static_cast<uint32_t>(report.classes.size());
    
    log("Parsed " + std::to_string(report.classes.size()) + " classes");
    return true;
}

bool DexParser::parse_class_data(const uint8_t* data, const DexClassDef& class_def, ClassInfo& info) {
    size_t offset = class_def.class_data_off;
    
    // ====================================================================
    // EXP-031.6 DEBUG: Trace class_data parsing
    // ====================================================================
    log("  === EXP-031.6 CLASS_DATA PARSING @ 0x" + std::to_string(offset) + " ===");
    
    if (offset >= current_size_) {
        log("  ERROR: offset beyond file end!");
        return false;
    }
    
    // Show first 32 bytes at class_data location for debugging
    {
        std::string hex_dump;
        size_t show_bytes = std::min((size_t)32, current_size_ - offset);
        for (size_t i = 0; i < show_bytes; i++) {
            char buf[4];
            snprintf(buf, sizeof(buf), "%02x ", data[offset + i]);
            hex_dump += buf;
        }
        log("  First bytes: " + hex_dump);
    }
    
    // Read encoded header using ULEB128
    auto read_uleb128 = [&data, &offset, this](uint32_t& value, const char* field_name) -> bool {
        if (offset >= current_size_) {
            log("  ULEB128 ERROR at " + std::string(field_name) + ": offset beyond end");
            return false;
        }
        
        value = 0;
        int shift = 0;
        uint8_t byte;
        size_t start_offset = offset;
        
        do {
            if (offset >= current_size_) {
                log("  ULEB128 TRUNCATE at " + std::string(field_name));
                return false;
            }
            byte = data[offset++];
            value |= static_cast<uint32_t>(byte & 0x7F) << shift;
            shift += 7;
        } while (byte & 0x80);
        
        log("  ULEB128[" + std::string(field_name) + "] @ 0x" + std::to_string(start_offset) + 
            " = " + std::to_string(value));
        return true;
    };
    
    DexClassDataHeader header;
    if (!read_uleb128(header.static_fields_size, "static_fields_size")) return false;
    if (!read_uleb128(header.instance_fields_size, "instance_fields_size")) return false;
    if (!read_uleb128(header.direct_methods_size, "direct_methods_size")) return false;
    if (!read_uleb128(header.virtual_methods_size, "virtual_methods_size")) return false;
    
    log("  → Header: static=" + std::to_string(header.static_fields_size) +
        ", instance=" + std::to_string(header.instance_fields_size) +
        ", direct=" + std::to_string(header.direct_methods_size) +
        ", virtual=" + std::to_string(header.virtual_methods_size));
    
    // Read static fields
    uint32_t field_idx = 0;
    for (uint32_t i = 0; i < header.static_fields_size; i++) {
        DexEncodedField encoded_field;
        if (!read_uleb128(encoded_field.field_idx_diff, "sf_field_diff")) break;
        if (!read_uleb128(encoded_field.access_flags, "sf_access_flags")) break;
        
        field_idx += encoded_field.field_idx_diff;
        
        FieldInfo fi;
        if (field_idx < fields_.size()) {
            fi.name = get_string(fields_[field_idx].name_idx);
            fi.type = get_type(fields_[field_idx].type_idx);
            fi.defining_class = get_type(fields_[field_idx].class_idx);
        }
        fi.is_static = true;
        fi.access_flags = encoded_field.access_flags;
        
        info.static_fields.push_back(fi);
    }
    
    // Read instance fields
    field_idx = 0;
    for (uint32_t i = 0; i < header.instance_fields_size; i++) {
        DexEncodedField encoded_field;
        if (!read_uleb128(encoded_field.field_idx_diff, "if_field_diff")) break;
        if (!read_uleb128(encoded_field.access_flags, "if_access_flags")) break;
        
        field_idx += encoded_field.field_idx_diff;
        
        FieldInfo fi;
        if (field_idx < fields_.size()) {
            fi.name = get_string(fields_[field_idx].name_idx);
            fi.type = get_type(fields_[field_idx].type_idx);
            fi.defining_class = get_type(fields_[field_idx].class_idx);
        }
        fi.is_static = false;
        fi.access_flags = encoded_field.access_flags;
        
        info.instance_fields.push_back(fi);
    }
    
    // Read direct methods
    uint32_t method_idx = 0;
    for (uint32_t i = 0; i < header.direct_methods_size; i++) {
        DexEncodedMethod encoded_method;
        log("  → Direct method[" + std::to_string(i) + "]:");
        if (!read_uleb128(encoded_method.method_idx_diff, "dm_method_diff")) break;
        if (!read_uleb128(encoded_method.access_flags, "dm_access_flags")) break;
        if (!read_uleb128(encoded_method.code_off, "dm_code_off")) break;
        
        method_idx += encoded_method.method_idx_diff;
        
        MethodInfo mi;
        if (method_idx < methods_.size()) {
            mi.name = get_string(methods_[method_idx].name_idx);
            
            // Get prototype
            if (methods_[method_idx].proto_idx < protos_.size()) {
                const auto& proto = protos_[methods_[method_idx].proto_idx];
                mi.shorty = get_string(proto.shorty_idx);
                mi.return_type = get_type(proto.return_type_idx);
                
                // Parse parameters
                if (proto.parameters_off != 0 && proto.parameters_off < current_size_) {
                    // Type list starts with size
                    uint32_t list_size;
                    std::memcpy(&list_size, data + proto.parameters_off, sizeof(uint32_t));
                    
                    for (uint32_t p = 0; p < list_size; p++) {
                        uint16_t type_idx;
                        size_t param_off = proto.parameters_off + sizeof(uint32_t) + p * sizeof(uint16_t);
                        if (param_off + sizeof(uint16_t) <= current_size_) {
                            std::memcpy(&type_idx, data + param_off, sizeof(uint16_t));
                            mi.parameters.push_back(get_type(type_idx));
                        }
                    }
                }
            }
            
            // Build descriptor
            mi.descriptor = "(";
            for (const auto& param : mi.parameters) {
                mi.descriptor += param;
            }
            mi.descriptor += ")" + mi.return_type;
            
            mi.defining_class = get_type(methods_[method_idx].class_idx);
        }
        
        mi.is_constructor = (mi.name == "<init>" || mi.name == "<clinit>");
        mi.is_static = (encoded_method.access_flags & 0x0008) != 0;  // ACC_STATIC
        mi.is_native = (encoded_method.access_flags & 0x0100) != 0;   // ACC_NATIVE
        mi.is_abstract = (encoded_method.access_flags & 0x0400) != 0; // ACC_ABSTRACT
        mi.access_flags = encoded_method.access_flags;
        
        // Parse code item if present
        if (encoded_method.code_off != 0 && !mi.is_native && !mi.is_abstract) {
            parse_code_item(data, encoded_method.code_off, mi);
        }
        
        info.direct_methods.push_back(mi);
    }
    
    // Read virtual methods
    method_idx = 0;
    for (uint32_t i = 0; i < header.virtual_methods_size; i++) {
        DexEncodedMethod encoded_method;
        log("  → Virtual method[" + std::to_string(i) + "]:");
        if (!read_uleb128(encoded_method.method_idx_diff, "vm_method_diff")) break;
        if (!read_uleb128(encoded_method.access_flags, "vm_access_flags")) break;
        if (!read_uleb128(encoded_method.code_off, "vm_code_off")) break;
        
        method_idx += encoded_method.method_idx_diff;
        
        MethodInfo mi;
        if (method_idx < methods_.size()) {
            mi.name = get_string(methods_[method_idx].name_idx);
            
            if (methods_[method_idx].proto_idx < protos_.size()) {
                const auto& proto = protos_[methods_[method_idx].proto_idx];
                mi.shorty = get_string(proto.shorty_idx);
                mi.return_type = get_type(proto.return_type_idx);
                
                if (proto.parameters_off != 0 && proto.parameters_off < current_size_) {
                    uint32_t list_size;
                    std::memcpy(&list_size, data + proto.parameters_off, sizeof(uint32_t));
                    
                    for (uint32_t p = 0; p < list_size; p++) {
                        uint16_t type_idx;
                        size_t param_off = proto.parameters_off + sizeof(uint32_t) + p * sizeof(uint16_t);
                        if (param_off + sizeof(uint16_t) <= current_size_) {
                            std::memcpy(&type_idx, data + param_off, sizeof(uint16_t));
                            mi.parameters.push_back(get_type(type_idx));
                        }
                    }
                }
            }
            
            mi.descriptor = "(";
            for (const auto& param : mi.parameters) {
                mi.descriptor += param;
            }
            mi.descriptor += ")" + mi.return_type;
            
            mi.defining_class = get_type(methods_[method_idx].class_idx);
        }
        
        mi.is_constructor = (mi.name == "<init>");
        mi.is_static = (encoded_method.access_flags & 0x0008) != 0;
        mi.is_native = (encoded_method.access_flags & 0x0100) != 0;
        mi.is_abstract = (encoded_method.access_flags & 0x0400) != 0;
        mi.access_flags = encoded_method.access_flags;
        
        if (encoded_method.code_off != 0 && !mi.is_native && !mi.is_abstract) {
            parse_code_item(data, encoded_method.code_off, mi);
        }
        
        info.virtual_methods.push_back(mi);
    }
    
    return true;
}

std::string DexParser::read_dex_string(const uint8_t* data, uint32_t offset) {
    if (offset >= current_size_) {
        return "<out of bounds>";
    }
    
    // MUTF-8 encoded string with ULEB128 length prefix
    size_t pos = offset;
    
    // Read ULEB128 length
    uint32_t length = 0;
    int shift = 0;
    uint8_t byte;
    
    do {
        if (pos >= current_size_) return "<error>";
        byte = data[pos++];
        length |= static_cast<uint32_t>(byte & 0x7F) << shift;
        shift += 7;
    } while (byte & 0x80);
    
    // Skip 1 or 2 bytes of high-byte content (for MUTF-8)
    if ((byte & 0x80) != 0) {
        pos++;  // Additional byte for lengths > 127
    }
    
    // Read string characters
    if (pos + length > current_size_) {
        return "<truncated>";
    }
    
    std::string result(reinterpret_cast<const char*>(data + pos), length);
    return result;
}

std::string DexParser::get_string(uint32_t index) const {
    if (index < strings_.size()) {
        return strings_[index];
    }
    return "<invalid string idx:" + std::to_string(index) + ">";
}

std::string DexParser::get_type(uint32_t index) const {
    if (index < types_.size()) {
        return types_[index];
    }
    return "<invalid type idx:" + std::to_string(index) + ">";
}

bool DexParser::parse_code_item(const uint8_t* data, uint32_t offset, MethodInfo& method) {
    // ====================================================================
    // EXP-031.6 DEBUG: Trace code_item extraction
    // ====================================================================
    log("  === EXP-031.6 CODE_ITEM @ 0x" + std::to_string(offset) + " for " + method.name + " ===");
    
    if (offset + sizeof(DexCodeItem) > current_size_) {
        log("  ERROR: code_item header extends beyond file (off=0x" + std::to_string(offset) + 
            ", need=0x" + std::to_string(sizeof(DexCodeItem)) + 
            ", have=0x" + std::to_string(current_size_) + ")");
        return false;
    }
    
    DexCodeItem code_item;
    std::memcpy(&code_item, data + offset, sizeof(DexCodeItem));
    
    method.code_offset = offset;
    
    log("  registers_size: " + std::to_string(code_item.registers_size));
    log("  ins_size: " + std::to_string(code_item.ins_size));
    log("  outs_size: " + std::to_string(code_item.outs_size));
    log("  tries_size: " + std::to_string(code_item.tries_size));
    log("  debug_info_off: 0x" + std::to_string(code_item.debug_info_off));
    log("  insns_size: " + std::to_string(code_item.insns_size) + " ← KEY FIELD!");
    
    // Copy bytecode instructions
    if (code_item.insns_size > 0 && 
        offset + sizeof(DexCodeItem) + code_item.insns_size * sizeof(uint16_t) <= current_size_) {
        
        method.bytecode.resize(code_item.insns_size);
        std::memcpy(method.bytecode.data(),
                   data + offset + sizeof(DexCodeItem),
                   code_item.insns_size * sizeof(uint16_t));
        
        log("  ✅ EXTRACTED " + std::to_string(code_item.insns_size) + " INSTRUCTIONS!");
        
        // Show first few opcodes
        std::string first_insns;
        size_t show_count = std::min((size_t)5, method.bytecode.size());
        for (size_t i = 0; i < show_count; i++) {
            char buf[16];
            snprintf(buf, sizeof(buf), "%04x ", method.bytecode[i]);
            first_insns += buf;
        }
        log("  First opcodes: " + first_insns);
        
    } else {
        if (code_item.insns_size == 0) {
            log("  ⚠️ insns_size = 0 (empty method body)");
        } else {
            log("  ❌ Instructions extend beyond file! insns_size=" + std::to_string(code_item.insns_size));
        }
    }
    
    return true;
}

void DexParser::log(const std::string& message) {
    if (verbose_) {
        std::cerr << "[DexParser] " << message << std::endl;
    }
}

// ClassInfo helper implementations
std::vector<MethodInfo> ClassInfo::all_methods() const {
    std::vector<MethodInfo> all;
    all.insert(all.end(), direct_methods.begin(), direct_methods.end());
    all.insert(all.end(), virtual_methods.begin(), virtual_methods.end());
    return all;
}

std::vector<MethodInfo> ClassInfo::get_method(const std::string& name) const {
    std::vector<MethodInfo> results;
    
    for (const auto& m : direct_methods) {
        if (m.name == name) results.push_back(m);
    }
    for (const auto& m : virtual_methods) {
        if (m.name == name) results.push_back(m);
    }
    
    return results;
}

std::optional<MethodInfo> ClassInfo::get_constructor() const {
    for (const auto& m : direct_methods) {
        if (m.name == "<init>") {
            return m;
        }
    }
    return std::nullopt;
}

} // namespace dex
} // namespace miniandroid
