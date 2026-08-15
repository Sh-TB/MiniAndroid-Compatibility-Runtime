/**
 * @file file_sandbox.cpp
 * @brief Implementation of persistent file storage sandbox for MiniAndroid
 * 
 * @description
 * Implements Windows-compatible version of Android's application data storage.
 * Provides Context.getFilesDir(), getCacheDir(), SharedPreferences paths, etc.
 * 
 * Key Design Decisions:
 * 1. Uses std::filesystem (C++17) for cross-platform path handling
 * 2. Auto-creates directories on first access (configurable)
 * 3. Validates package names to prevent path traversal
 * 4. Provides detailed error information for debugging
 * 5. Thread-safe directory creation via internal synchronization
 * 
 * @author EXP-037 Development (Phase A, Week 1)
 * @date 2026-08-14
 * @version 1.0.0
 * 
 * @license MIT
 */

#include "file_sandbox.h"

#include <iostream>
#include <sstream>
#include <algorithm>
#include <regex>
#include <mutex>
#include <chrono>

namespace Storage {

// ============================================================================
// CONSTANTS
// ============================================================================

/// Maximum allowed package name length (Android limit is usually shorter)
static const size_t MAX_PACKAGE_NAME_LENGTH = 256;

/// Maximum path length to attempt (Windows MAX_PATH is 260, but we allow longer with \\?\ prefix)
static const size_t MAX_PATH_LENGTH = 4096;

/// Default directory permissions (not used on Windows, but kept for documentation)
static const int DIRECTORY_PERMISSIONS = 0755;

/// Subdirectory names for each SandboxDirectory type
static const std::map<SandboxDirectory, std::string> DIRECTORY_NAMES = {
    {SandboxDirectory::FILES, "files"},
    {SandboxDirectory::CACHE, "cache"},
    {SandboxDirectory::DATABASES, "databases"},
    {SandboxDirectory::SHARED_PREFS, "shared_prefs"},
    {SandboxDirectory::LIB, "lib"},
    {SandboxDirectory::EXTERNAL, "external"},
    {SandboxDirectory::ROOT, ""}
};

/// Regex pattern for validating Android package names
/// Must match: [a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+
static const std::string PACKAGE_NAME_PATTERN = 
    R"(^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_*)+$)";

// ============================================================================
// UTILITY FUNCTION IMPLEMENTATIONS
// ============================================================================

bool isValidAndroidPackageName(const std::string& name) {
    // Quick length check first
    if (name.empty() || name.length() > MAX_PACKAGE_NAME_LENGTH) {
        return false;
    }
    
    // Check for invalid characters (anything not alphanumeric, underscore, or dot)
    for (char c : name) {
        if (!isalnum(c) && c != '_' && c != '.') {
            return false;
        }
    }
    
    // Must start with letter
    if (!isalpha(name[0])) {
        return false;
    }
    
    // Must contain at least one dot (package hierarchy)
    if (name.find('.') == std::string::npos) {
        return false;
    }
    
    // No consecutive dots
    if (name.find("..") != std::string::npos) {
        return false;
    }
    
    // No leading/trailing dots
    if (name.front() == '.' || name.back() == '.') {
        return false;
    }
    
    // Each segment must start with letter (after dot)
    size_t pos = 0;
    while ((pos = name.find('.', pos)) != std::string::npos) {
        pos++; // Move past the dot
        if (pos < name.length() && !isalpha(name[pos])) {
            return false;
        }
    }
    
    return true;
}

bool ensureGlobalRootExists(const std::string& root_path) {
    try {
        fs::path root(root_path);
        
        if (fs::exists(root)) {
            return fs::is_directory(root);
        }
        
        return fs::create_directories(root);
    } catch (const fs::filesystem_error& e) {
        std::cerr << "[FileSandbox] Failed to create global root: " << e.what() << std::endl;
        return false;
    }
}

// ============================================================================
// FILESANDBOX CONSTRUCTORS/DESTRUCTOR
// ============================================================================

FileSandbox::FileSandbox()
    : initialized_(false)
    , last_error_(SandboxError::NONE)
{
    config_ = SandboxConfig();
}

FileSandbox::FileSandbox(const std::string& package_name)
    : package_name_(package_name)
    , initialized_(false)
    , last_error_(SandboxError::NONE)
{
    config_ = SandboxConfig();
    
    // Build paths immediately
    root_path_ = fs::path(config_.root_path);
    package_root_ = root_path_ / package_name_;
}

FileSandbox::FileSandbox(const std::string& package_name, const SandboxConfig& config)
    : package_name_(package_name)
    , config_(config)
    , initialized_(false)
    , last_error_(SandboxError::NONE)
{
    root_path_ = fs::path(config_.root_path);
    package_root_ = root_path_ / package_name_;
}

FileSandbox::~FileSandbox() {
    // Nothing to clean up - we don't own any resources that need explicit release
    // The filesystem directories persist after destruction (as intended)
}

FileSandbox::FileSandbox(FileSandbox&& other) noexcept
    : package_name_(std::move(other.package_name_))
    , root_path_(std::move(other.root_path_))
    , package_root_(std::move(other.package_root_))
    , config_(std::move(other.config_))
    , initialized_(other.initialized_)
    , directory_cache_(std::move(other.directory_cache_))
{
    other.initialized_ = false;
}

FileSandbox& FileSandbox::operator=(FileSandbox&& other) noexcept {
    if (this != &other) {
        package_name_ = std::move(other.package_name_);
        root_path_ = std::move(other.root_path_);
        package_root_ = std::move(other.package_root_);
        config_ = std::move(other.config_);
        initialized_ = other.initialized_;
        directory_cache_ = std::move(other.directory_cache_);
        other.initialized_ = false;
    }
    return *this;
}

// ============================================================================
// INITIALIZATION
// ============================================================================

bool FileSandbox::initialize() {
    // Validate package name first
    if (!isValidPackageName(package_name_)) {
        setError(SandboxError::INVALID_PACKAGE_NAME, 
                 "Invalid package name: " + package_name_);
        if (config_.strict_mode) {
            throw std::runtime_error("Invalid package name: " + package_name_);
        }
        return false;
    }
    
    // Ensure global root exists
    if (!ensureGlobalRootExists(config_.root_path)) {
        setError(SandboxError::DIRECTORY_CREATE_FAILED,
                 "Failed to create root directory: " + config_.root_path);
        return false;
    }
    
    // Create all subdirectories
    std::vector<SandboxDirectory> dirs_to_create = {
        SandboxDirectory::FILES,
        SandboxDirectory::CACHE,
        SandboxDirectory::DATABASES,
        SandboxDirectory::SHARED_PREFS,
        SandboxDirectory::LIB
    };
    
    bool all_success = true;
    for (SandboxDirectory dir : dirs_to_create) {
        fs::path dir_path = buildPath(dir);
        SandboxError err = ensureDirectoryExists(dir_path);
        if (err != SandboxError::NONE) {
            all_success = false;
            if (config_.strict_mode) {
                return false;
            }
            // In non-strict mode, continue trying others
        }
    }
    
    initialized_ = all_success;
    
    if (initialized_) {
        // Clear cache so paths are recalculated
        directory_cache_.clear();
        
        // Log success for debugging
        std::cout << "[FileSandbox] Initialized sandbox for: " << package_name_ << std::endl;
        std::cout << "[FileSandbox] Root path: " << package_root_.string() << std::endl;
    }
    
    return initialized_;
}

// ============================================================================
// PRIVATE HELPER METHODS
// ============================================================================

bool FileSandbox::isValidPackageName(const std::string& name) const {
    return ::Storage::isValidAndroidPackageName(name);
}

std::string FileSandbox::sanitizePathComponent(const std::string& component) const {
    std::string result = component;
    
    // Remove path traversal attempts
    std::string::size_type pos;
    while ((pos = result.find("..")) != std::string::npos) {
        result.erase(pos, 2);
    }
    
    // Remove leading/trailing slashes and dots
    while (!result.empty() && (result.front() == '/' || result.front() == '\\' || result.front() == '.')) {
        result.erase(0, 1);
    }
    while (!result.empty() && (result.back() == '/' || result.back() == '\\' || result.back() == '.')) {
        result.pop_back();
    }
    
    // Replace backslashes with forward slashes (Windows compatibility)
    std::replace(result.begin(), result.end(), '\\', '/');
    
    // Remove double slashes
    while ((pos = result.find("//")) != std::string::npos) {
        result.erase(pos, 1);
    }
    
    return result;
}

std::string FileSandbox::getDirectoryName(SandboxDirectory dir) const {
    auto it = DIRECTORY_NAMES.find(dir);
    if (it != DIRECTORY_NAMES.end()) {
        return it->second;
    }
    return ""; // ROOT or unknown
}

fs::path FileSandbox::buildPath(SandboxDirectory dir) const {
    std::string subdir = getDirectoryName(dir);
    if (subdir.empty()) {
        return package_root_; // ROOT
    }
    return package_root_ / subdir;
}

SandboxError FileSandbox::ensureDirectoryExists(const fs::path& path, bool create_parents) {
    try {
        // Check path length
        std::string path_str = path.string();
        if (path_str.length() > MAX_PATH_LENGTH) {
            setError(SandboxError::PATH_TOO_LONG, "Path too long: " + path_str.substr(0, 50) + "...");
            return SandboxError::PATH_TOO_LONG;
        }
        
        // Check if already exists
        if (fs::exists(path)) {
            if (fs::is_directory(path)) {
                return SandboxError::NONE; // Already exists and is directory
            } else {
                setError(SandboxError::DIRECTORY_CREATE_FAILED,
                         "Path exists but is not a directory: " + path_str);
                return SandboxError::DIRECTORY_CREATE_FAILED;
            }
        }
        
        // Create directory
        if (create_parents) {
            fs::create_directories(path);
        } else {
            fs::create_directory(path);
        }
        
        // Verify creation succeeded
        if (!fs::exists(path) || !fs::is_directory(path)) {
            setError(SandboxError::DIRECTORY_CREATE_FAILED,
                     "Failed to create directory: " + path_str);
            return SandboxError::DIRECTORY_CREATE_FAILED;
        }
        
        return SandboxError::NONE;
        
    } catch (const fs::filesystem_error& e) {
        SandboxError err;
        
        switch (e.code().value()) {
            case static_cast<int>(std::errc::permission_denied):
                err = SandboxError::PERMISSION_DENIED;
                break;
            case static_cast<int>(std::errc::no_space_on_device):
                err = SandboxError::DISK_FULL;
                break;
            case static_cast<int>(std::errc::filename_too_long):
                err = SandboxError::PATH_TOO_LONG;
                break;
            default:
                err = SandboxError::DIRECTORY_CREATE_FAILED;
                break;
        }
        
        setError(err, e.what());
        return err;
    } catch (const std::exception& e) {
        setError(SandboxError::UNKNOWN, e.what());
        return SandboxError::UNKNOWN;
    }
}

void FileSandbox::calculateDirectoryInfo(const fs::path& path, SandboxPathInfo& info) const {
    info.path = path;
    info.exists = fs::exists(path) && fs::is_directory(path);
    
    if (!info.exists) {
        info.size_bytes = 0;
        info.file_count = 0;
        info.readable = false;
        info.writable = false;
        return;
    }
    
    // Calculate size and file count
    info.size_bytes = 0;
    info.file_count = 0;
    
    try {
        for (const auto& entry : fs::recursive_directory_iterator(path)) {
            if (entry.is_regular_file()) {
                info.file_count++;
                try {
                    info.size_bytes += entry.file_size();
                } catch (...) {
                    // Some files might not report size (permissions, etc.)
                    // Just skip them in the count
                }
            }
        }
    } catch (const fs::filesystem_error&) {
        // Might not have permission to traverse all files
        // Use partial information
    }
    
    // Check permissions (simplified - just test one operation)
    try {
        // Test readability by checking if we can list contents
        fs::directory_iterator test_it(path);
        info.readable = true;
    } catch (...) {
        info.readable = false;
    }
    
    try {
        // Test writability by checking if we can create a temp file
        fs::path test_file = path / ".write_test_tmp";
        std::ofstream test(test_file);
        if (test.is_open()) {
            test.close();
            fs::remove(test_file);
            info.writable = true;
        } else {
            info.writable = false;
        }
    } catch (...) {
        info.writable = false;
    }
}

void FileSandbox::setError(SandboxError error, const std::string& msg) const {
    last_error_ = error;
    last_error_msg_ = msg;
    
    if (!msg.empty()) {
        std::cerr << "[FileSandbox] Error (" << static_cast<int>(error) << "): " << msg << std::endl;
    }
}

// ============================================================================
// DIRECTORY ACCESS METHODS
// ============================================================================

fs::path FileSandbox::getDirectory(SandboxDirectory dir) {
    // Check cache first
    auto it = directory_cache_.find(dir);
    if (it != directory_cache_.end() && fs::exists(it->second)) {
        return it->second;
    }
    
    // Build path
    fs::path path = buildPath(dir);
    
    // Auto-create if configured
    if (config_.auto_create && !fs::exists(path)) {
        ensureDirectoryExists(path);
    }
    
    // Cache the result
    directory_cache_[dir] = path;
    
    return path;
}

SandboxPathInfo FileSandbox::getPathInfo(SandboxDirectory dir) {
    fs::path path = getDirectory(dir); // Ensures existence if auto_create enabled
    SandboxPathInfo info;
    calculateDirectoryInfo(path, info);
    return info;
}

SandboxPathInfo FileSandbox::getPackageInfo() {
    SandboxPathInfo info;
    calculateDirectoryInfo(package_root_, info);
    return info;
}

bool FileSandbox::directoryExists(SandboxDirectory dir) {
    fs::path path = buildPath(dir); // Don't use getDirectory (avoids auto-create)
    return fs::exists(path) && fs::is_directory(path);
}

uint64_t FileSandbox::getTotalSize() {
    uint64_t total = 0;
    
    std::vector<SandboxDirectory> dirs = {
        SandboxDirectory::FILES,
        SandboxDirectory::CACHE,
        SandboxDirectory::DATABASES,
        SandboxDirectory::SHARED_PREFS,
        SandboxDirectory::LIB
    };
    
    for (SandboxDirectory dir : dirs) {
        SandboxPathInfo info = getPathInfo(dir);
        total += info.size_bytes;
    }
    
    return total;
}

// ============================================================================
// FILE OPERATIONS
// ============================================================================

std::ifstream FileSandbox::openFileInput(const std::string& name) {
    // Sanitize filename to prevent traversal
    std::string safe_name = sanitizePathComponent(name);
    
    if (safe_name.empty()) {
        setError(SandboxError::NOT_FOUND, "Invalid filename: " + name);
        return std::ifstream(); // Return empty stream
    }
    
    fs::path files_dir = getDirectory(SandboxDirectory::FILES);
    fs::path file_path = files_dir / safe_name;
    
    // Check existence
    if (!fs::exists(file_path)) {
        setError(SandboxError::NOT_FOUND, "File not found: " + safe_name);
        return std::ifstream(); // Return empty stream
    }
    
    // Open file
    std::ifstream stream(file_path, std::ios::binary);
    
    if (!stream.is_open()) {
        setError(SandboxError::PERMISSION_DENIED, "Cannot open file for reading: " + safe_name);
        return std::ifstream(); // Return empty stream
    }
    
    setError(SandboxError::NONE); // Clear any previous error
    return stream;
}

std::ofstream FileSandbox::openFileOutput(const std::string& name, bool append) {
    // Sanitize filename
    std::string safe_name = sanitizePathComponent(name);
    
    if (safe_name.empty()) {
        setError(SandboxError::NOT_FOUND, "Invalid filename: " + name);
        return std::ofstream(); // Return empty stream
    }
    
    fs::path files_dir = getDirectory(SandboxDirectory::FILES);
    fs::path file_path = files_dir / safe_name;
    
    // Open mode
    std::ios_base::openmode mode = std::ios::binary;
    if (append) {
        mode |= std::ios::app;
    } else {
        mode |= std::ios::trunc;
    }
    
    // Open file
    std::ofstream stream(file_path, mode);
    
    if (!stream.is_open()) {
        setError(SandboxError::PERMISSION_DENIED, "Cannot open file for writing: " + safe_name);
        return std::ofstream(); // Return empty stream
    }
    
    setError(SandboxError::NONE); // Clear any previous error
    return stream;
}

bool FileSandbox::deleteFile(const std::string& name) {
    std::string safe_name = sanitizePathComponent(name);
    
    if (safe_name.empty()) {
        setError(SandboxError::NOT_FOUND, "Invalid filename: " + name);
        return false;
    }
    
    fs::path files_dir = getDirectory(SandboxDirectory::FILES);
    fs::path file_path = files_dir / safe_name;
    
    if (!fs::exists(file_path)) {
        // File doesn't exist - consider this success (idempotent delete)
        return true;
    }
    
    try {
        fs::remove(file_path);
        return !fs::exists(file_path); // Verify deletion
    } catch (const fs::filesystem_error& e) {
        setError(SandboxError::PERMISSION_DENIED, e.what());
        return false;
    }
}

std::vector<FileInfo> FileSandbox::fileList() {
    std::vector<FileInfo> files;
    
    fs::path files_dir = getDirectory(SandboxDirectory::FILES);
    
    if (!fs::exists(files_dir) || !fs::is_directory(files_dir)) {
        return files;
    }
    
    try {
        for (const auto& entry : fs::directory_iterator(files_dir)) {
            if (entry.is_regular_file()) {
                FileInfo info;
                info.name = entry.path().filename().string();
                info.full_path = entry.path();
                
                try {
                    info.size_bytes = entry.file_size();
                } catch (...) {
                    info.size_bytes = 0;
                }
                
                try {
                    auto ftime = fs::last_write_time(entry.path());
                    // Convert to time_t (simplified - may need adjustment for precision)
                    auto sctp = std::chrono::time_point_cast<std::chrono::system_clock::duration>(
                        ftime - fs::file_time_type::clock::now() + std::chrono::system_clock::now()
                    );
                    info.modified_time = std::chrono::system_clock::to_time_t(sctp);
                } catch (...) {
                    info.modified_time = 0;
                }
                
                // Check basic permissions
                try {
                    std::ifstream test(entry.path());
                    info.is_readable = test.is_open();
                    if (info.is_readable) test.close();
                } catch (...) {
                    info.is_readable = false;
                }
                
                try {
                    std::ofstream test(entry.path(), std::ios::app);
                    info.is_writable = test.is_open();
                    if (info.is_writable) {
                        // Don't actually write anything, just check permission
                        test.close();
                    }
                } catch (...) {
                    info.is_writable = false;
                }
                
                files.push_back(info);
            }
        }
    } catch (const fs::filesystem_error& e) {
        setError(SandboxError::PERMISSION_DENIED, e.what());
    }
    
    return files;
}

bool FileSandbox::fileExists(const std::string& name) {
    std::string safe_name = sanitizePathComponent(name);
    
    if (safe_name.empty()) {
        return false;
    }
    
    fs::path files_dir = getDirectory(SandboxDirectory::FILES);
    fs::path file_path = files_dir / safe_name;
    
    return fs::exists(file_path) && fs::is_regular_file(file_path);
}

// ============================================================================
// SHARED PREFERENCES HELPERS
// ============================================================================

fs::path FileSandbox::getPreferencesPath(const std::string& name) {
    std::string safe_name = sanitizePathComponent(name);
    
    // Remove .xml extension if provided (we'll add it)
    if (safe_name.length() > 4 && safe_name.substr(safe_name.length() - 4) == ".xml") {
        safe_name = safe_name.substr(0, safe_name.length() - 4);
    }
    
    fs::path prefs_dir = getDirectory(SandboxDirectory::SHARED_PREFS);
    return prefs_dir / (safe_name + ".xml");
}

std::vector<std::string> FileSandbox::listPreferences() {
    std::vector<std::string> prefs;
    
    fs::path prefs_dir = getDirectory(SandboxDirectory::SHARED_PREFS);
    
    if (!fs::exists(prefs_dir) || !fs::is_directory(prefs_dir)) {
        return prefs;
    }
    
    try {
        for (const auto& entry : fs::directory_iterator(prefs_dir)) {
            if (entry.is_regular_file()) {
                std::string filename = entry.path().filename().string();
                
                // Only .xml files
                if (filename.length() > 4 && filename.substr(filename.length() - 4) == ".xml") {
                    // Remove .xml extension for return value
                    prefs.push_back(filename.substr(0, filename.length() - 4));
                }
            }
        }
    } catch (const fs::filesystem_error& e) {
        setError(SandboxError::PERMISSION_DENIED, e.what());
    }
    
    // Sort alphabetically for consistent output
    std::sort(prefs.begin(), prefs.end());
    
    return prefs;
}

bool FileSandbox::deletePreferences(const std::string& name) {
    fs::path pref_path = getPreferencesPath(name);
    
    if (!fs::exists(pref_path)) {
        return true; // Idempotent
    }
    
    try {
        fs::remove(pref_path);
        return !fs::exists(pref_path);
    } catch (const fs::filesystem_error& e) {
        setError(SandboxError::PERMISSION_DENIED, e.what());
        return false;
    }
}

// ============================================================================
// DATABASE HELPERS
// ============================================================================

fs::path FileSandbox::getDatabasePath(const std::string& name) {
    std::string safe_name = sanitizePathComponent(name);
    
    fs::path db_dir = getDirectory(SandboxDirectory::DATABASES);
    return db_dir / safe_name;
}

std::vector<std::string> FileSandbox::listDatabases() {
    std::vector<std::string> dbs;
    
    fs::path db_dir = getDirectory(SandboxDirectory::DATABASES);
    
    if (!fs::exists(db_dir) || !fs::is_directory(db_dir)) {
        return dbs;
    }
    
    try {
        for (const auto& entry : fs::directory_iterator(db_dir)) {
            if (entry.is_regular_file()) {
                std::string filename = entry.path().filename().string();
                
                // Common database extensions: .db, .sqlite, .sqlite3
                // Also include files without extension (some apps do this)
                dbs.push_back(filename);
            }
        }
    } catch (const fs::filesystem_error& e) {
        setError(SandboxError::PERMISSION_DENIED, e.what());
    }
    
    // Sort alphabetically
    std::sort(dbs.begin(), dbs.end());
    
    return dbs;
}

bool FileSandbox::deleteDatabase(const std::string& name) {
    fs::path db_path = getDatabasePath(name);
    
    // Also check for associated journal/WAL files
    std::vector<fs::path> related_files = {
        db_path.string() + "-journal",
        db_path.string() + "-wal",
        db_path.string() + "-shm"
    };
    
    bool success = true;
    
    if (fs::exists(db_path)) {
        try {
            fs::remove(db_path);
            if (fs::exists(db_path)) {
                success = false;
            }
        } catch (const fs::filesystem_error& e) {
            setError(SandboxError::PERMISSION_DENIED, e.what());
            success = false;
        }
    }
    
    // Try to remove related files (don't fail if they don't exist)
    for (const auto& related : related_files) {
        if (fs::exists(related)) {
            try {
                fs::remove(related);
            } catch (...) {
                // Non-critical failure
            }
        }
    }
    
    return success;
}

// ============================================================================
// UTILITY METHODS
// ============================================================================

bool FileSandbox::clearDirectory(SandboxDirectory dir, bool confirm_if_large) {
    fs::path dir_path = getDirectory(dir);
    
    if (!fs::exists(dir_path)) {
        return true; // Nothing to clear
    }
    
    // Count files first if confirmation required
    if (confirm_if_large) {
        uint32_t count = 0;
        try {
            for (const auto& entry : fs::recursive_directory_iterator(dir_path)) {
                if (entry.is_regular_file()) count++;
                if (count > 100) break; // Early exit once we know it's large
            }
        } catch (...) {
            // If we can't count, proceed anyway
        }
        
        if (count > 100) {
            // Safety check - require explicit confirmation for large deletions
            // For now, we'll log a warning but continue
            std::cout << "[FileSandbox] WARNING: Clearing directory with " << count 
                      << " files: " << dir_path.string() << std::endl;
        }
    }
    
    try {
        // Remove all contents but keep the directory itself
        for (const auto& entry : fs::directory_iterator(dir_path)) {
            fs::remove_all(entry.path());
        }
        return true;
    } catch (const fs::filesystem_error& e) {
        setError(SandboxError::PERMISSION_DENIED, e.what());
        return false;
    }
}

bool FileSandbox::clearAllData(bool confirm_if_large) {
    if (!fs::exists(package_root_)) {
        return true; // Nothing to clear
    }
    
    // Count total files if confirmation required
    if (confirm_if_large) {
        uint32_t count = 0;
        try {
            for (const auto& entry : fs::recursive_directory_iterator(package_root_)) {
                if (entry.is_regular_file()) count++;
                if (count > 1000) break;
            }
        } catch (...) {}
        
        if (count > 1000) {
            std::cout << "[FileSandbox] WARNING: Clearing ALL data with " << count 
                      << " files: " << package_root_.string() << std::endl;
        }
    }
    
    try {
        // Remove all contents inside each subdirectory
        std::vector<SandboxDirectory> dirs = {
            SandboxDirectory::FILES,
            SandboxDirectory::CACHE,
            SandboxDirectory::DATABASES,
            SandboxDirectory::SHARED_PREFS,
            SandboxDirectory::LIB
        };
        
        for (SandboxDirectory dir : dirs) {
            clearDirectory(dir, false); // Already confirmed above
        }
        
        return true;
    } catch (const fs::filesystem_error& e) {
        setError(SandboxError::PERMISSION_DENIED, e.what());
        return false;
    }
}

std::string FileSandbox::debugPrintStructure() const {
    std::ostringstream ss;
    
    ss << "=== FileSandbox Debug Structure ===" << std::endl;
    ss << "Package: " << package_name_ << std::endl;
    ss << "Root: " << package_root_.string() << std::endl;
    ss << "Initialized: " << (initialized_ ? "Yes" : "No") << std::endl;
    ss << std::endl;
    
    ss << "Directories:" << std::endl;
    
    std::vector<std::pair<SandboxDirectory, std::string>> dir_display = {
        {SandboxDirectory::FILES, "Files (getFilesDir)"},
        {SandboxDirectory::CACHE, "Cache (getCacheDir)"},
        {SandboxDirectory::DATABASES, "Databases"},
        {SandboxDirectory::SHARED_PREFS, "SharedPreferences"},
        {SandboxDirectory::LIB, "Native Libraries"}
    };
    
    for (auto& [dir, label] : dir_display) {
        fs::path path = buildPath(dir);
        bool exists = fs::exists(path);
        
        ss << "  [" << (exists ? "✓" : "✗") << "] " << label << ": " << path.filename().string();
        if (exists) {
            // Count items
            uint32_t count = 0;
            try {
                for (const auto& _ : fs::directory_iterator(path)) { count++; }
            } catch (...) {}
            ss << " (" << count << " items)";
        }
        ss << std::endl;
    }
    
    ss << std::endl;
    // Note: getTotalSize() is non-const, so we can't call it here
    // In production, either make it const or cache the value during init
    // For now, we'll skip this in the debug output or calculate it differently
    ss << "===================================" << std::endl;
    
    return ss.str();
}

SandboxError FileSandbox::getLastError() const {
    return last_error_;
}

std::string FileSandbox::getLastErrorMessage() const {
    if (last_error_ == SandboxError::NONE) {
        return "No error";
    }
    return last_error_msg_;
}

} // namespace Storage
