/*
 * MiniAndroid Runtime v0.1 - APK Parser
 * EXP-001: HelloWorld Loader
 * 
 * Handles ZIP-based APK file parsing and extraction.
 */

#ifndef MINIANDROID_APK_PARSER_H
#define MINIANDROID_APK_PARSER_H

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <cstdint>
#include <functional>

namespace miniandroid {
namespace apk {

// ZIP/APK error codes
enum class ApkError {
    NONE = 0,
    FILE_NOT_FOUND,
    FILE_TOO_SMALL,
    INVALID_ZIP,
    NO_MANIFEST,
    NO_DEX,
    CORRUPTED_FILE,
    UNSUPPORTED_FORMAT
};

// APK information structure (output of parser)
struct ApkInfo {
    // Basic info
    std::string apk_name;
    std::string apk_path;
    size_t file_size = 0;
    
    // Package info from manifest
    std::string package_name;
    std::string version_name;
    int version_code = 0;
    std::string min_sdk_version;
    std::string target_sdk_version;
    
    // Main activity
    std::string main_activity;
    std::string main_activity_full;

    // EXP-093/F005: Custom Application class from manifest
    std::string application_name;
    
    // Permissions
    std::vector<std::string> permissions;
    
    // Contents
    std::vector<std::string> dex_files;
    std::vector<std::string> native_libraries;
    std::vector<std::string> resource_files;
    
    // All entries in ZIP
    std::vector<std::string> all_entries;
    
    // Validation
    bool is_valid = false;
    std::string validation_error;
};

// ZIP local file header structure (simplified)
#pragma pack(push, 1)
struct ZipLocalFileHeader {
    uint32_t signature;        // 0x04034b50 "PK\x03\x04"
    uint16_t version_needed;
    uint16_t flags;
    uint16_t compression_method;
    uint16_t last_mod_time;
    uint16_t last_mod_date;
    uint32_t crc32;
    uint32_t compressed_size;
    uint32_t uncompressed_size;
    uint16_t file_name_length;
    uint16_t extra_field_length;
};
#pragma pack(pop)

// ZIP central directory entry (simplified)
#pragma pack(push, 1)
struct ZipCentralDirEntry {
    uint32_t signature;        // 0x02014b50 "PK\x01\x02"
    uint16_t version_made_by;
    uint16_t version_needed;
    uint16_t flags;
    uint16_t compression_method;
    uint16_t last_mod_time;
    uint16_t last_mod_date;
    uint32_t crc32;
    uint32_t compressed_size;
    uint32_t uncompressed_size;
    uint16_t file_name_length;
    uint16_t extra_field_length;
    uint16_t file_comment_length;
    uint16_t disk_number_start;
    uint16_t internal_file_attributes;
    uint32_t external_file_attributes;
    uint32_t relative_offset_local_header;
};
#pragma pack(pop)

// End of central directory record
#pragma pack(push, 1)
struct ZipEndOfCentralDir {
    uint32_t signature;        // 0x06054b50 "PK\x05\x06"
    uint16_t disk_number;
    uint16_t disk_with_central_dir;
    uint16_t num_entries_on_disk;
    uint16_t num_entries_central_dir;
    uint32_t central_dir_size;
    uint32_t central_dir_offset;
    uint16_t comment_length;
};
#pragma pack(pop)

// Entry in ZIP archive
struct ZipEntry {
    std::string name;
    uint32_t compressed_size = 0;
    uint32_t uncompressed_size = 0;
    uint16_t compression_method = 0;
    uint32_t crc32 = 0;
    uint32_t offset = 0;  // Offset to local file header
    bool is_directory = false;
};

// Callback for progress reporting
using ProgressCallback = std::function<void(const std::string& stage, int percent)>;

/**
 * Main APK Parser class
 * 
 * Usage:
 *   ApkParser parser;
 *   auto result = parser.parse("HelloWorld.apk");
 *   if (result.is_valid) { ... }
 */
class ApkParser {
public:
    ApkParser();
    ~ApkParser();
    
    // Parse APK file and extract metadata
    ApkInfo parse(const std::string& path);
    
    // Parse with progress callback
    ApkInfo parse(const std::string& path, ProgressCallback callback);
    
    // Extract a specific entry from the APK
    std::vector<uint8_t> extract_entry(const std::string& apk_path, const std::string& entry_name);
    
    // Extract to memory using pre-loaded data
    std::vector<uint8_t> extract_entry_from_memory(const std::vector<uint8_t>& apk_data, const std::string& entry_name);

    // EXP-038 (BLOCKER-023): Extract using cached APK data.
    // After parse() is called, the APK data and central directory entries
    // are cached. This method uses the cache for O(1) entry lookup instead
    // of re-parsing the entire central directory on every extraction.
    // Returns empty vector if entry not found or if parse() was never called.
    std::vector<uint8_t> extract_entry_cached(const std::string& entry_name);
    
    // EXP-038 (BLOCKER-023): Check if cached APK data is available.
    bool has_cached_data() const { return !cached_apk_data_.empty(); }
    
    // EXP-038 (BLOCKER-024): Get list of DEX files found during parse.
    const std::vector<std::string>& get_cached_dex_files() const { return cached_dex_files_; }
    
    // List all entries in APK
    std::vector<ZipEntry> list_entries(const std::string& path);
    
    // Validate APK structure
    ApkError validate(const std::string& path);
    
    // Get last error message
    std::string get_last_error() const { return last_error_; }
    
    // Set verbose logging
    void set_verbose(bool verbose) { verbose_ = verbose; }

private:
    // Internal methods
    bool read_file_to_memory(const std::string& path, std::vector<uint8_t>& buffer);
    ApkInfo parse_apk_data(const std::vector<uint8_t>& data, const std::string& path);
    
    // ZIP parsing
    bool find_end_of_central_dir(const std::vector<uint8_t>& data, size_t& eocd_offset);
    bool parse_central_directory(const std::vector<uint8_t>& data, size_t eocd_offset, 
                                 std::vector<ZipEntry>& entries);
    bool parse_local_file_header(const std::vector<uint8_t>& data, size_t offset, ZipEntry& entry);
    
    // Data extraction (with zlib decompression)
    std::vector<uint8_t> decompress_data(const std::vector<uint8_t>& compressed, 
                                         uint32_t compressed_size, 
                                         uint32_t uncompressed_size,
                                         uint16_t method);
    
    // EXP-094 (CM-021): central-directory-driven extraction — used by both
    // extract_entry_from_memory and extract_entry_cached. Reads the local
    // file header ONLY for the data offset (file_name_length + extra_field_length
    // may differ between LFH and CDE per APPNOTE.TXT §4.4.10/§4.4.11). The
    // sizes/method/crc come from the ZipEntry (already populated from the
    // central directory, which is the authoritative source).
    std::vector<uint8_t> extract_entry_using_central_dir_(
        const std::vector<uint8_t>& apk_data, const ZipEntry& entry);
    
    // Manifest analysis (delegates to manifest_reader)
    void analyze_manifest(const std::vector<uint8_t>& manifest_data, ApkInfo& info);
    
    // Helper methods
    static std::string extract_filename(const std::string& path);
    std::vector<ZipEntry> list_entries_from_data(const std::vector<uint8_t>& data);
    
    // Logging
    void log(const std::string& message);
    
    std::string last_error_;
    bool verbose_ = false;

    // EXP-038 (BLOCKER-023): Cached APK data for fast entry extraction.
    // After parse() is called, the entire APK file data is kept in memory
    // and the central directory entries are cached in a map for O(1) lookup.
    // This avoids re-parsing 11,531 ZIP entries on every extract_entry call.
    std::vector<uint8_t> cached_apk_data_;
    std::map<std::string, ZipEntry> cached_entries_;
    std::vector<std::string> cached_dex_files_;  // EXP-038 (BLOCKER-024)
};

} // namespace apk
} // namespace miniandroid

#endif // MINIANDROID_APK_PARSER_H
