/**
 * @file file_sandbox.h
 * @brief Persistent file storage sandbox for MiniAndroid runtime
 * 
 * @description
 * Implements Android-compatible file system abstraction for Windows.
 * Creates and manages the directory structure that mirrors Android's
 * /data/data/<package>/ layout, adapted for Windows filesystem.
 * 
 * Directory Structure (mirrors Android):
 * 
 * runtime/data/
 * └── <package_name>/
 *     ├── files/           # Context.getFilesDir()
 *     ├── cache/           # Context.getCacheDir()
 *     ├── databases/       # SQLiteDatabase storage
 *     ├── shared_prefs/    # SharedPreferences XML files
 *     └── lib/             # Native libraries (.dll on Windows)
 * 
 * @author EXP-037 Development (Phase A, Week 1)
 * @date 2026-08-14
 * @version 1.0.0
 * 
 * @license MIT
 */

#ifndef FILE_SANDBOX_H
#define FILE_SANDBOX_H

#include <string>
#include <vector>
#include <filesystem>
#include <fstream>
#include <map>
#include <memory>
#include <system_error>

namespace fs = std::filesystem;

/**
 * @namespace Storage
 * @brief File system storage components for MiniAndroid
 */
namespace Storage {

// ============================================================================
// ENUMERATIONS
// ============================================================================

/**
 * @enum SandboxDirectory
 * @brief Types of sandbox directories available
 */
enum class SandboxDirectory : uint8_t {
    FILES = 0,          ///< Application private files (getFilesDir)
    CACHE,              ///< Cache files (getCacheDir)
    DATABASES,          ///< SQLite databases
    SHARED_PREFS,       ///< SharedPreferences XML files
    LIB,                ///< Native libraries (.dll on Windows)
    EXTERNAL,           ///< External storage (if available)
    ROOT                ///< Package root directory
};

/**
 * @enum SandboxError
 * @brief Error codes for sandbox operations
 */
enum class SandboxError : uint8_t {
    NONE = 0,            ///< No error
    NOT_INITIALIZED,     ///< Sandbox not initialized
    DIRECTORY_CREATE_FAILED,  ///< Failed to create directory
    PATH_TOO_LONG,       ///< Path exceeds OS limits
    PERMISSION_DENIED,   ///< Access denied
    NOT_FOUND,           ///< Path doesn't exist
    ALREADY_EXISTS,      ///< Already exists (for create operations)
    INVALID_PACKAGE_NAME, ///< Invalid package name format
    DISK_FULL,           ///< No space left on device
    UNKNOWN              ///< Unknown error
};

// ============================================================================
// DATA STRUCTURES
// ============================================================================

/**
 * @struct SandboxConfig
 * @brief Configuration for sandbox initialization
 */
struct SandboxConfig {
    std::string root_path;        ///< Base path for all sandboxes (default: "runtime/data")
    bool auto_create;             ///< Auto-create directories on access (default: true)
    bool strict_mode;             ///< Fail on errors vs graceful degradation (default: false)
    
    /**
     * @brief Default constructor with sensible defaults
     */
    SandboxConfig() 
        : root_path("runtime/data")
        , auto_create(true)
        , strict_mode(false) {}
    
    /**
     * @brief Constructor with custom root path
     */
    explicit SandboxConfig(const std::string& root)
        : root_path(root)
        , auto_create(true)
        , strict_mode(false) {}
};

/**
 * @struct SandboxPathInfo
 * @brief Information about a sandbox path
 */
struct SandboxPathInfo {
    fs::path path;               ///< Full path to directory
    bool exists;                 ///< Whether directory currently exists
    uint64_t size_bytes;         ///< Total size in bytes (0 if not exists or not calculated)
    uint32_t file_count;         ///< Number of files in directory
    bool readable;               ///< Whether directory is readable
    bool writable;               ///< Whether directory is writable
    
    SandboxPathInfo() 
        : exists(false), size_bytes(0), file_count(0), 
          readable(false), writable(false) {}
};

/**
 * @struct FileInfo
 * @brief Information about a single file in the sandbox
 */
struct FileInfo {
    std::string name;            ///< File name (without path)
    fs::path full_path;          ///< Complete file path
    uint64_t size_bytes;         ///< File size in bytes
    std::time_t modified_time;   ///< Last modification time
    bool is_readable;            ///< Whether file can be read
    bool is_writable;            ///< Whether file can be written
    
    FileInfo() 
        : size_bytes(0), modified_time(0), 
          is_readable(false), is_writable(false) {}
};

// ============================================================================
// MAIN CLASS: FileSandbox
// ============================================================================

/**
 * @class FileSandbox
 * @brief Manages persistent file storage for an Android package
 * 
 * This class provides Android Context file API compatibility:
 * - getFilesDir() → files/ directory
 * - getCacheDir() → cache/ directory
 * - getSharedPreferences() path → shared_prefs/ directory
 * - openFileInput() / openFileOutput() → files/ directory operations
 * 
 * Thread Safety: Basic thread safety via mutex for directory creation.
 * File operations should use external synchronization if needed.
 * 
 * Usage Example:
 * @code
 * // Create sandbox for Telegram
 * Storage::FileSandbox telegram_sandbox("org.telegram.messenger");
 * 
 * // Initialize (creates directory structure)
 * telegram_sandbox.initialize();
 * 
 * // Get paths (auto-creates if configured)
 * fs::path files_dir = telegram_sandbox.getDirectory(SandboxDirectory::FILES);
 * fs::path cache_dir = telegram_sandbox.getDirectory(SandboxDirectory::CACHE);
 * 
 * // Check what we have
 * Storage::SandboxPathInfo info = telegram_sandbox.getPathInfo(SandboxDirectory::FILES);
 * std::cout << "Files dir exists: " << info.exists << std::endl;
 * std::cout << "File count: " << info.file_count << std::endl;
 * @endcode
 */
class FileSandbox {
private:
    // ========================================================================
    // PRIVATE MEMBERS
    // ========================================================================
    
    std::string package_name_;      ///< Android package name (e.g., "org.telegram.messenger")
    fs::path root_path_;           ///< Root of this sandbox (<root>/<package>)
    fs::path package_root_;        ///< Full path to package directory
    SandboxConfig config_;         ///< Configuration settings
    bool initialized_;              ///< Whether initialize() was called successfully
    
    // Cache for path information (optional optimization)
    mutable std::map<SandboxDirectory, fs::path> directory_cache_;
    
    // ========================================================================
    // PRIVATE METHODS
    // ========================================================================
    
    /**
     * @brief Validate package name format
     * 
     * Android package names must match: [a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+
     * Examples: "org.telegram.messenger", "com.example.app"
     * 
     * @param name Package name to validate
     * @return true if valid, false otherwise
     */
    bool isValidPackageName(const std::string& name) const;
    
    /**
     * @brief Sanitize a path component to prevent traversal attacks
     * 
     * Removes "..", ".", leading/trailing slashes, etc.
     * 
     * @param component Path component to sanitize
     * @return Sanitized string safe for path construction
     */
    std::string sanitizePathComponent(const std::string& component) const;
    
    /**
     * @brief Get the subdirectory name for a SandboxDirectory type
     * 
     * @param dir Directory type enum value
     * @return Subdirectory name string (e.g., "files", "cache", etc.)
     */
    std::string getDirectoryName(SandboxDirectory dir) const;
    
    /**
     * @brief Build full path for a directory type
     * 
     * Constructs: <root_path>/<package_name>/<subdirectory>
     * 
     * @param dir Directory type
     * @return Full filesystem path
     */
    fs::path buildPath(SandboxDirectory dir) const;
    
    /**
     * @brief Ensure a directory exists, creating it if necessary
     * 
     * @param path Directory path to ensure
     * @param create_parents Also create parent directories
     * @return SandboxError::NONE on success, error code otherwise
     */
    SandboxError ensureDirectoryExists(const fs::path& path, bool create_parents = true);
    
    /**
     * @brief Calculate directory statistics
     * 
     * @param path Directory to analyze
     * @param[out] info Structure to fill with data
     */
    void calculateDirectoryInfo(const fs::path& path, SandboxPathInfo& info) const;

public:
    // ========================================================================
    // CONSTRUCTORS & DESTRUCTOR
    // ========================================================================
    
    /**
     * @brief Default constructor (must call initialize() later)
     */
    FileSandbox();
    
    /**
     * @brief Construct with package name (uses default config)
     * 
     * @param package_name Android-style package name
     */
    explicit FileSandbox(const std::string& package_name);
    
    /**
     * @brief Construct with package name and custom config
     * 
     * @param package_name Android-style package name
     * @param config Configuration settings
     */
    FileSandbox(const std::string& package_name, const SandboxConfig& config);
    
    /**
     * @brief Destructor (does not delete files, just cleanup)
     */
    ~FileSandbox();
    
    // Prevent copying (manage resources uniquely)
    FileSandbox(const FileSandbox&) = delete;
    FileSandbox& operator=(const FileSandbox&) = delete;
    
    // Allow moving
    FileSandbox(FileSandbox&& other) noexcept;
    FileSandbox& operator=(FileSandbox&& other) noexcept;
    
    // ========================================================================
    // INITIALIZATION
    // ========================================================================
    
    /**
     * @brief Initialize the sandbox (create directory structure)
     * 
     * Must be called before using other methods (unless auto_create is enabled).
     * Creates the complete directory tree:
     * <root>/<package>/{files,cache,databases,shared_prefs,lib}
     * 
     * @return true if successful (or already initialized), false on error
     */
    bool initialize();
    
    /**
     * @brief Check if sandbox has been initialized
     * 
     * @return true if initialize() was called successfully
     */
    bool isInitialized() const { return initialized_; }
    
    /**
     * @brief Get the package name this sandbox manages
     * 
     * @return Package name string
     */
    const std::string& getPackageName() const { return package_name_; }
    
    // ========================================================================
    // DIRECTORY ACCESS (Android Context API Compatibility)
    // ========================================================================
    
    /**
     * @brief Get path to a specific sandbox directory
     * 
     * Maps to Android's:
     * - SandboxDirectory::FILES → Context.getFilesDir()
     * - SandboxDirectory::CACHE → Context.getCacheDir()
     * - SandboxDirectory::SHARED_PREFS → SharedPreferences storage location
     * - SandboxDirectory::DATABASES → SQLiteDatabase storage
     * 
     * If auto_create is enabled, directory is created automatically.
     * 
     * @param dir Type of directory to get
     * @return Full path to the requested directory
     * @throws std::runtime_error if strict_mode and directory creation fails
     */
    fs::path getDirectory(SandboxDirectory dir);
    
    /**
     * @brief Get path to files directory (Android: Context.getFilesDir())
     * 
     * Convenience method for SandboxDirectory::FILES
     * 
     * @return Path to files/ directory
     */
    fs::path getFilesDir() { return getDirectory(SandboxDirectory::FILES); }
    
    /**
     * @brief Get path to cache directory (Android: Context.getCacheDir())
     * 
     * Convenience method for SandboxDirectory::CACHE
     * 
     * @return Path to cache/ directory
     */
    fs::path getCacheDir() { return getDirectory(SandboxDirectory::CACHE); }
    
    /**
     * @brief Get path to databases directory
     * 
     * Convenience method for SandboxDirectory::DATABASES
     * 
     * @return Path to databases/ directory
     */
    fs::path getDatabasesDir() { return getDirectory(SandboxDirectory::DATABASES); }
    
    /**
     * @brief Get path to shared preferences directory
     * 
     * Convenience method for SandboxDirectory::SHARED_PREFS
     * 
     * @return Path to shared_prefs/ directory
     */
    fs::path getSharedPrefsDir() { return getDirectory(SandboxDirectory::SHARED_PREFS); }
    
    /**
     * @brief Get path to native libraries directory
     * 
     * On Windows, this would contain .dll files instead of .so
     * 
     * @return Path to lib/ directory
     */
    fs::path getLibDir() { return getDirectory(SandboxDirectory::LIB); }
    
    // ========================================================================
    // PATH INFORMATION
    // ========================================================================
    
    /**
     * @brief Get detailed information about a sandbox directory
     * 
     * @param dir Directory type to query
     * @return SandboxPathInfo structure with details
     */
    SandboxPathInfo getPathInfo(SandboxDirectory dir);
    
    /**
     * @brief Get detailed information about the package root
     * 
     * @return SandboxPathInfo for entire package directory
     */
    SandboxPathInfo getPackageInfo();
    
    /**
     * @brief Check if a specific directory exists
     * 
     * @param dir Directory type to check
     * @return true if directory exists on disk
     */
    bool directoryExists(SandboxDirectory dir);
    
    /**
     * @brief Get total size of all sandbox directories combined
     * 
     * @return Total size in bytes across all subdirectories
     */
    uint64_t getTotalSize();
    
    // ========================================================================
    // FILE OPERATIONS (Android Context API Compatibility)
    // ========================================================================
    
    /**
     * @brief Open a file for reading (Android: Context.openFileInput())
     * 
     * Opens file from files/ directory in read-only mode.
     * 
     * @param name Filename (not full path, just name)
     * @return Input stream to the file, or empty stream if error
     */
    std::ifstream openFileInput(const std::string& name);
    
    /**
     * @brief Open a file for writing (Android: Context.openFileOutput())
     * 
     * Opens/creates file in files/ directory in write mode.
     * 
     * @param name Filename (not full path, just name)
     * @param append If true, append to existing file; otherwise overwrite
     * @return Output stream to the file, or empty stream if error
     */
    std::ofstream openFileOutput(const std::string& name, bool append = false);
    
    /**
     * @brief Delete a file from the files directory
     * 
     * @param name Filename to delete
     * @return true if deleted successfully (or didn't exist)
     */
    bool deleteFile(const std::string& name);
    
    /**
     * @brief List all files in the files directory
     * 
     * @return Vector of FileInfo structures
     */
    std::vector<FileInfo> fileList();
    
    /**
     * @brief Check if a file exists in the files directory
     * 
     * @param name Filename to check
     * @return true if file exists
     */
    bool fileExists(const std::string& name);
    
    // ========================================================================
    // SHARED PREFERENCES HELPERS
    // ========================================================================
    
    /**
     * @brief Get path to a SharedPreferences XML file
     * 
     * Constructs path: <shared_prefs>/<name>.xml
     * 
     * @param name Preference file name (without .xml extension)
     * @return Full path to the preferences XML file
     */
    fs::path getPreferencesPath(const std::string& name);
    
    /**
     * @brief List all existing SharedPreferences files
     * 
     * @return Vector of preference file names (without .xml extension)
     */
    std::vector<std::string> listPreferences();
    
    /**
     * @brief Delete a SharedPreferences file
     * 
     * @param name Preference file name (without .xml extension)
     * @return true if deleted successfully
     */
    bool deletePreferences(const std::string& name);
    
    // ========================================================================
    // DATABASE HELPERS
    // ========================================================================
    
    /**
     * @brief Get path to a database file
     * 
     * Constructs path: <databases>/<name>
     * 
     * @param name Database filename (e.g., "telegram.db", "cache4.db")
     * @return Full path to database file
     */
    fs::path getDatabasePath(const std::string& name);
    
    /**
     * @brief List all existing database files
     * 
     * @return Vector of database filenames
     */
    std::vector<std::string> listDatabases();
    
    /**
     * @brief Delete a database file
     * 
     * @param name Database filename to delete
     * @return true if deleted successfully
     */
    bool deleteDatabase(const std::string& name);
    
    // ========================================================================
    // UTILITY METHODS
    // ========================================================================
    
    /**
     * @brief Clear all contents of a directory (but keep directory itself)
     * 
     * @param dir Directory type to clear
     * @param confirm_if_large If >100 files, require confirmation (returns false)
     * @return true if cleared successfully
     */
    bool clearDirectory(SandboxDirectory dir, bool confirm_if_large = true);
    
    /**
     * @brief Clear ALL sandbox data (destructive!)
     * 
     * Deletes everything inside the package directory.
     * Use with caution!
     * 
     * @param confirm_if_large If >1000 files total, require confirmation
     * @return true if cleared successfully
     */
    bool clearAllData(bool confirm_if_large = true);
    
    /**
     * @brief Export sandbox structure as JSON-like string (for debugging)
     * 
     * @return Human-readable representation of sandbox contents
     */
    std::string debugPrintStructure() const;
    
    /**
     * @brief Get the last error that occurred
     * 
     * @return Last error code
     */
    SandboxError getLastError() const;
    
    /**
     * @brief Get human-readable error message for last error
     * 
     * @return Error description string
     */
    std::string getLastErrorMessage() const;

private:
    mutable SandboxError last_error_;      ///< Most recent error code
    mutable std::string last_error_msg_;  ///< Human-readable error message
    
    /**
     * @brief Set the last error state
     */
    void setError(SandboxError error, const std::string& msg = "") const;
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * @brief Validate if a string is a valid Android package name
 * 
 * @param name String to validate
 * @return true if matches Android package naming conventions
 */
bool isValidAndroidPackageName(const std::string& name);

/**
 * @brief Create the default global sandbox root if it doesn't exist
 * 
 * Creates "runtime/data/" directory (or custom path).
 * 
 * @param root_path Base path to create
 * @return true if exists or was created successfully
 */
bool ensureGlobalRootExists(const std::string& root_path = "runtime/data");

} // namespace Storage

#endif // FILE_SANDBOX_H
