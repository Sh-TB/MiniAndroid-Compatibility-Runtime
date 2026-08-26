/*
 * MiniAndroid Runtime v0.1 - APK Parser Implementation
 * EXP-001: HelloWorld Loader
 */

#include "apk_parser.h"
#include "manifest_reader.h"

#include <fstream>
#include <sstream>
#include <iostream>
#include <algorithm>
#include <cstring>

// For zlib decompression
#include <zlib.h>

namespace miniandroid {
namespace apk {

// Constants
constexpr uint32_t ZIP_LOCAL_FILE_HEADER_SIG = 0x04034b50;
constexpr uint32_t ZIP_CENTRAL_DIR_SIG = 0x02014b50;
constexpr uint32_t ZIP_END_OF_CENTRAL_DIR_SIG = 0x06054b50;
constexpr size_t MIN_APK_SIZE = 100;  // Minimum valid APK size
constexpr size_t MAX_APK_SIZE = 512 * 1024 * 1024;  // 512MB max

ApkParser::ApkParser() : verbose_(false) {
}

ApkParser::~ApkParser() {
}

ApkInfo ApkParser::parse(const std::string& path) {
    return parse(path, nullptr);
}

ApkInfo ApkParser::parse(const std::string& path, ProgressCallback callback) {
    ApkInfo info;
    info.apk_path = path;
    info.apk_name = extract_filename(path);
    
    if (callback) callback("Validating APK", 10);
    
    // Step 1: Validate the file
    auto validation_error = validate(path);
    if (validation_error != ApkError::NONE) {
        info.is_valid = false;
        info.validation_error = get_last_error();
        return info;
    }
    
    if (callback) callback("Reading APK data", 20);
    
    // Step 2: Read entire file to memory
    std::vector<uint8_t> data;
    if (!read_file_to_memory(path, data)) {
        info.is_valid = false;
        return info;
    }
    
    info.file_size = data.size();
    
    return parse_apk_data(data, path);
}

std::vector<uint8_t> ApkParser::extract_entry(const std::string& apk_path, const std::string& entry_name) {
    std::vector<uint8_t> apk_data;
    if (!read_file_to_memory(apk_path, apk_data)) {
        return {};
    }
    return extract_entry_from_memory(apk_data, entry_name);
}

std::vector<uint8_t> ApkParser::extract_entry_from_memory(const std::vector<uint8_t>& apk_data, 
                                                          const std::string& entry_name) {
    // Find the entry
    auto entries = list_entries_from_data(apk_data);
    
    for (const auto& entry : entries) {
        if (entry.name == entry_name) {
            // Read local file header at entry offset
            ZipLocalFileHeader header;
            size_t offset = entry.offset;
            
            if (offset + sizeof(header) > apk_data.size()) {
                last_error_ = "Invalid local file header offset";
                return {};
            }
            
            std::memcpy(&header, &apk_data[offset], sizeof(header));
            
            // Validate signature
            if (header.signature != ZIP_LOCAL_FILE_HEADER_SIG) {
                last_error_ = "Invalid local file header signature";
                return {};
            }
            
            // Skip past header + name + extra field to get to data
            size_t data_offset = offset + sizeof(header) + 
                                 header.file_name_length + 
                                 header.extra_field_length;
            
            // Extract compressed data
            std::vector<uint8_t> compressed_data(header.compressed_size);
            if (data_offset + header.compressed_size > apk_data.size()) {
                last_error_ = "Compressed data exceeds file bounds";
                return {};
            }
            
            std::memcpy(compressed_data.data(), &apk_data[data_offset], header.compressed_size);
            
            // Decompress if needed
            return decompress_data(compressed_data, 
                                   header.compressed_size, 
                                   header.uncompressed_size,
                                   header.compression_method);
        }
    }
    
    last_error_ = "Entry not found: " + entry_name;
    return {};
}

// EXP-038 (BLOCKER-023): Cached extraction — O(1) lookup instead of O(n) re-parse.
// Uses cached_apk_data_ and cached_entries_ populated during parse_apk_data().
std::vector<uint8_t> ApkParser::extract_entry_cached(const std::string& entry_name) {
    if (cached_apk_data_.empty()) {
        last_error_ = "No cached APK data — parse() must be called first";
        return {};
    }
    
    auto it = cached_entries_.find(entry_name);
    if (it == cached_entries_.end()) {
        last_error_ = "Entry not found in cache: " + entry_name;
        return {};
    }
    
    const ZipEntry& entry = it->second;
    const std::vector<uint8_t>& apk_data = cached_apk_data_;
    
    // Read local file header at entry offset
    ZipLocalFileHeader header;
    size_t offset = entry.offset;
    
    if (offset + sizeof(header) > apk_data.size()) {
        last_error_ = "Invalid local file header offset";
        return {};
    }
    
    std::memcpy(&header, &apk_data[offset], sizeof(header));
    
    if (header.signature != ZIP_LOCAL_FILE_HEADER_SIG) {
        last_error_ = "Invalid local file header signature";
        return {};
    }
    
    // Skip past header + name + extra field to get to data
    size_t data_offset = offset + sizeof(header) + 
                         header.file_name_length + 
                         header.extra_field_length;
    
    if (data_offset + header.compressed_size > apk_data.size()) {
        last_error_ = "Compressed data exceeds file bounds";
        return {};
    }
    
    // Extract compressed data
    std::vector<uint8_t> compressed_data(header.compressed_size);
    std::memcpy(compressed_data.data(), &apk_data[data_offset], header.compressed_size);
    
    // Decompress if needed
    return decompress_data(compressed_data, 
                           header.compressed_size, 
                           header.uncompressed_size,
                           header.compression_method);
}

std::vector<ZipEntry> ApkParser::list_entries(const std::string& path) {
    std::vector<uint8_t> data;
    if (!read_file_to_memory(path, data)) {
        return {};
    }
    return list_entries_from_data(data);
}

ApkError ApkParser::validate(const std::string& path) {
    // Check file exists
    std::ifstream file(path, std::ios::binary | std::ios::ate);
    if (!file.is_open()) {
        last_error_ = "File not found: " + path;
        return ApkError::FILE_NOT_FOUND;
    }
    
    auto size = file.tellg();
    file.close();
    
    // Check minimum size
    if (size < MIN_APK_SIZE) {
        last_error_ = "File too small to be a valid APK (" + std::to_string(size) + " bytes)";
        return ApkError::FILE_TOO_SMALL;
    }
    
    // Check maximum size
    if (size > MAX_APK_SIZE) {
        last_error_ = "File exceeds maximum APK size (512MB)";
        return ApkError::UNSUPPORTED_FORMAT;
    }
    
    // Verify ZIP magic bytes
    std::vector<uint8_t> magic(4);
    file.open(path, std::ios::binary);
    file.read(reinterpret_cast<char*>(magic.data()), 4);
    file.close();
    
    if (magic[0] != 0x50 || magic[1] != 0x4B || magic[2] != 0x03 || magic[3] != 0x04) {
        last_error_ = "Invalid ZIP magic bytes - not a valid APK/ZIP file";
        return ApkError::INVALID_ZIP;
    }
    
    log("APK validation passed: " + path);
    return ApkError::NONE;
}

bool ApkParser::read_file_to_memory(const std::string& path, std::vector<uint8_t>& buffer) {
    std::ifstream file(path, std::ios::binary | std::ios::ate);
    if (!file.is_open()) {
        last_error_ = "Cannot open file: " + path;
        return false;
    }
    
    auto size = file.tellg();
    file.seekg(0, std::ios::beg);
    
    buffer.resize(static_cast<size_t>(size));
    if (!file.read(reinterpret_cast<char*>(buffer.data()), size)) {
        last_error_ = "Failed to read file contents";
        return false;
    }
    
    return true;
}

ApkInfo ApkParser::parse_apk_data(const std::vector<uint8_t>& data, const std::string& path) {
    ApkInfo info;
    info.apk_path = path;
    info.apk_name = extract_filename(path);
    info.file_size = data.size();
    
    // Parse ZIP entries
    std::vector<ZipEntry> entries;
    size_t eocd_offset = 0;
    
    if (!find_end_of_central_dir(data, eocd_offset)) {
        info.is_valid = false;
        info.validation_error = "Cannot find end of central directory";
        return info;
    }
    
    if (!parse_central_directory(data, eocd_offset, entries)) {
        info.is_valid = false;
        info.validation_error = "Cannot parse central directory";
        return info;
    }
    
    // EXP-038 (BLOCKER-023): Cache the APK data and parsed entries for
    // fast O(1) lookup by extract_entry_cached(). Without this cache,
    // every extract_entry_from_memory() call re-parses the entire central
    // directory (11,531 entries for Telegram → extreme slowness).
    cached_apk_data_ = data;
    cached_entries_.clear();
    for (const auto& entry : entries) {
        cached_entries_[entry.name] = entry;
    }
    log("Cached " + std::to_string(cached_entries_.size()) + " ZIP entries for fast lookup");
    
    // Categorize entries
    for (const auto& entry : entries) {
        info.all_entries.push_back(entry.name);
        
        // Check for required files
        if (entry.name == "AndroidManifest.xml") {
            info.resource_files.push_back(entry.name);
        }
        else if (entry.name == "classes.dex" || 
                 (entry.name.find("classes") == 0 && entry.name.find(".dex") != std::string::npos)) {
            info.dex_files.push_back(entry.name);
        }
        else if (entry.name.find("lib/") == 0 && entry.name.find(".so") != std::string::npos) {
            info.native_libraries.push_back(entry.name);
        }
        
        // Track directories
        if (!entry.name.empty() && entry.name.back() == '/') {
            // It's a directory, skip for most purposes
        }
    }
    
    // EXP-038 (BLOCKER-024): Cache DEX file list for multidex loading.
    cached_dex_files_ = info.dex_files;
    log("Found " + std::to_string(cached_dex_files_.size()) + " DEX files: ");
    for (const auto& dex : cached_dex_files_) {
        log("  - " + dex);
    }
    
    // Validate required entries exist
    bool has_manifest = false;
    bool has_dex = !info.dex_files.empty();
    
    for (const auto& entry : entries) {
        if (entry.name == "AndroidManifest.xml") {
            has_manifest = true;
        }
    }
    
    if (!has_manifest) {
        info.validation_error = "APK missing AndroidManifest.xml";
        info.is_valid = false;
        return info;
    }
    
    if (!has_dex) {
        log("Warning: APK contains no DEX files (native-only?)");
    }
    
    // Extract and parse manifest
    log("Extracting AndroidManifest.xml...");
    auto manifest_data = extract_entry_from_memory(data, "AndroidManifest.xml");
    
    if (!manifest_data.empty()) {
        analyze_manifest(manifest_data, info);
    } else {
        log("Warning: Could not extract AndroidManifest.xml");
    }
    
    info.is_valid = true;
    log("APK parsing complete: " + info.package_name + " (" + std::to_string(entries.size()) + " entries)");
    
    return info;
}

bool ApkParser::find_end_of_central_dir(const std::vector<uint8_t>& data, size_t& eocd_offset) {
    // EOCD can have variable-length comment, search backwards
    // EOCD is at least 22 bytes without comment
    size_t min_eocd_size = 22;
    
    if (data.size() < min_eocd_size) {
        last_error_ = "File too small for EOCD";
        return false;
    }
    
    // Search from end, but not more than 65535 bytes back (max comment length)
    size_t search_start = (data.size() > 65557) ? data.size() - 65557 : 0;
    
    for (size_t i = data.size() - min_eocd_size; i >= search_start; i--) {
        if (i + 4 > data.size()) continue;
        
        uint32_t sig;
        std::memcpy(&sig, &data[i], 4);
        
        if (sig == ZIP_END_OF_CENTRAL_DIR_SIG) {
            eocd_offset = i;
            log("Found EOCD at offset " + std::to_string(i));
            return true;
        }
    }
    
    last_error_ = "End of central directory signature not found";
    return false;
}

bool ApkParser::parse_central_directory(const std::vector<uint8_t>& data, size_t eocd_offset,
                                        std::vector<ZipEntry>& entries) {
    // Parse EOCD to get central directory location
    ZipEndOfCentralDir eocd;
    if (eocd_offset + sizeof(eocd) > data.size()) {
        last_error_ = "EOCD extends beyond file";
        return false;
    }
    
    std::memcpy(&eocd, &data[eocd_offset], sizeof(eocd));
    
    if (eocd.signature != ZIP_END_OF_CENTRAL_DIR_SIG) {
        last_error_ = "Invalid EOCD signature";
        return false;
    }
    
    size_t cd_offset = eocd.central_dir_offset;
    uint16_t num_entries = eocd.num_entries_central_dir;
    
    log("Central Directory: " + std::to_string(num_entries) + " entries at offset " + std::to_string(cd_offset));
    
    // Parse each central directory entry
    size_t pos = cd_offset;
    for (uint16_t i = 0; i < num_entries; i++) {
        if (pos + sizeof(ZipCentralDirEntry) > data.size()) {
            last_error_ = "Central directory entry extends beyond file";
            return false;
        }
        
        ZipCentralDirEntry cde;
        std::memcpy(&cde, &data[pos], sizeof(cde));
        
        if (cde.signature != ZIP_CENTRAL_DIR_SIG) {
            last_error_ = "Invalid central directory entry signature at entry " + std::to_string(i);
            return false;
        }
        
        ZipEntry entry;
        entry.compressed_size = cde.compressed_size;
        entry.uncompressed_size = cde.uncompressed_size;
        entry.compression_method = cde.compression_method;
        entry.crc32 = cde.crc32;
        entry.offset = cde.relative_offset_local_header;
        
        // Read filename
        size_t name_start = pos + sizeof(ZipCentralDirEntry);
        if (name_start + cde.file_name_length <= data.size()) {
            entry.name = std::string(reinterpret_cast<const char*>(&data[name_start]), cde.file_name_length);
        }
        
        entry.is_directory = !entry.name.empty() && entry.name.back() == '/';
        
        entries.push_back(entry);
        
        // Move to next entry
        pos += sizeof(ZipCentralDirEntry) + cde.file_name_length + cde.extra_field_length + cde.file_comment_length;
    }
    
    return true;
}

bool ApkParser::parse_local_file_header(const std::vector<uint8_t>& data, size_t offset, ZipEntry& entry) {
    if (offset + sizeof(ZipLocalFileHeader) > data.size()) {
        return false;
    }
    
    ZipLocalFileHeader lfh;
    std::memcpy(&lfh, &data[offset], sizeof(lfh));
    
    if (lfh.signature != ZIP_LOCAL_FILE_HEADER_SIG) {
        return false;
    }
    
    entry.compressed_size = lfh.compressed_size;
    entry.uncompressed_size = lfh.uncompressed_size;
    entry.compression_method = lfh.compression_method;
    entry.crc32 = lfh.crc32;
    
    // Read filename
    size_t name_start = offset + sizeof(ZipLocalFileHeader);
    if (name_start + lfh.file_name_length <= data.size()) {
        entry.name = std::string(reinterpret_cast<const char*>(&data[name_start]), lfh.file_name_length);
    }
    
    entry.is_directory = !entry.name.empty() && entry.name.back() == '/';
    
    return true;
}

std::vector<uint8_t> ApkParser::decompress_data(const std::vector<uint8_t>& compressed,
                                                 uint32_t compressed_size,
                                                 uint32_t uncompressed_size,
                                                 uint16_t method) {
    if (method == 0) {
        // Stored (no compression)
        return compressed;
    }
    
    if (method == 8) {
        // Deflate compression
        std::vector<uint8_t> result(uncompressed_size);
        
        z_stream strm = {};
        strm.next_in = const_cast<Bytef*>(compressed.data());
        strm.avail_in = compressed_size;
        strm.next_out = result.data();
        strm.avail_out = uncompressed_size;
        
        // Initialize with raw deflate (no zlib/gzip header)
        if (inflateInit2(&strm, -MAX_WBITS) != Z_OK) {
            last_error_ = "Failed to initialize zlib";
            return {};
        }
        
        int ret = inflate(&strm, Z_FINISH);
        inflateEnd(&strm);
        
        if (ret != Z_STREAM_END) {
            last_error_ = "Deflate decompression failed";
            return {};
        }
        
        return result;
    }
    
    last_error_ = "Unsupported compression method: " + std::to_string(method);
    return {};
}

void ApkParser::analyze_manifest(const std::vector<uint8_t>& manifest_data, ApkInfo& info) {
    ManifestReader reader;
    auto manifest_info = reader.parse(manifest_data);
    
    info.package_name = manifest_info.package_name;
    info.version_name = manifest_info.version_name;
    info.version_code = manifest_info.version_code;
    info.min_sdk_version = manifest_info.min_sdk_version;
    info.target_sdk_version = manifest_info.target_sdk_version;
    info.main_activity = manifest_info.main_activity;
    info.main_activity_full = manifest_info.main_activity_full;
    info.application_name = manifest_info.application_name;  // EXP-093/F005
    info.permissions = manifest_info.permissions;
}

void ApkParser::log(const std::string& message) {
    if (verbose_) {
        std::cerr << "[ApkParser] " << message << std::endl;
    }
}

// Helper function to extract filename from path
std::string ApkParser::extract_filename(const std::string& path) {
    size_t pos = path.find_last_of("/\\");
    if (pos != std::string::npos) {
        return path.substr(pos + 1);
    }
    return path;
}

// Additional helper to list entries from memory (used internally)
std::vector<ZipEntry> ApkParser::list_entries_from_data(const std::vector<uint8_t>& data) {
    std::vector<ZipEntry> entries;
    size_t eocd_offset = 0;
    
    if (!find_end_of_central_dir(data, eocd_offset)) {
        return entries;
    }
    
    parse_central_directory(data, eocd_offset, entries);
    return entries;
}

} // namespace apk
} // namespace miniandroid
