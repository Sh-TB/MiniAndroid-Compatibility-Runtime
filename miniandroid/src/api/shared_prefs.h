/**
 * @file shared_prefs.h
 * @brief Android SharedPreferences compatibility layer for MiniAndroid runtime
 * 
 * @description
 * Implements persistent key-value storage using XML files, compatible with
 * Android's SharedPreferences API. This is THE critical component for session
 * persistence - Telegram uses it to store login state, user ID, and other
 * session data that must survive process restarts.
 * 
 * Key Features:
 * - Android-compatible XML format (can read real Android shared_prefs)
 * - All primitive types: String, Int, Long, Float, Boolean, Set<String>
 * - Editor pattern with commit() (synchronous) and apply() (async)
 * - Thread-safe operations with mutex protection
 * - Integration with FileSandbox for path management
 * 
 * XML Format (Android-compatible):
 * @code
 * <?xml version='1.0' encoding='utf-8' standalone='yes' ?>
 * <map>
 *     <string name="logged_in_key">true</string>
 *     <int name="user_id" value="123456789" />
 *     <long name="login_time" value="1692012345678" />
 *     <float name="some_float" value="3.14" />
 *     <boolean name="notifications" value="true" />
 *     <set name="tags">
 *         <string>work</string>
 *         <string>personal</string>
 *     </set>
 * </map>
 * @endcode
 * 
 * Usage Example:
 * @code
 * // Get preferences (creates/opens XML file)
 * SharedPreferences prefs("org.telegram.messenger", "mainconfig");
 * 
 * // Read values with defaults
 * bool loggedIn = prefs.getBoolean("logged_in_key", false);
 * int userId = prefs.getInt("user_id", -1);
 * 
 * // Modify using Editor pattern
 * prefs.edit()
 *      .putString("phone_hash", "abc123")
 *      .putLong("login_time", System.currentTimeMillis())
 *      .putBoolean("logged_in_key", true)
 *      .commit();  // Synchronous write to disk
 * @endcode
 * 
 * @author EXP-037 Development (Phase A, Week 2)
 * @date 2026-08-14
 * @version 1.0.0
 * 
 * @license MIT
 * 
 * @see FileSandbox - Provides directory structure for storage
 * @see https://developer.android.com/reference/android/content/SharedPreferences
 */

#ifndef SHARED_PREFS_H
#define SHARED_PREFS_H

#include <string>
#include <vector>
#include <map>
#include <set>
#include <memory>
#include <fstream>
#include <sstream>
#include <mutex>
#include <functional>
#include <filesystem>
#include <variant>
#include <optional>
#include <atomic>
#include <shared_mutex>

namespace fs = std::filesystem;

/**
 * @namespace AndroidAPI
 * @brief Android framework API compatibility layer
 */
namespace AndroidAPI {

// ============================================================================
// DATA TYPES
// ============================================================================

/**
 * @enum PrefType
 * @brief Supported preference value types (matches Android SharedPreferences)
 */
enum class PrefType : uint8_t {
    STRING = 0,       ///< std::string
    INT,              ///< int32_t
    LONG,             ///< int64_t
    FLOAT,            ///< float
    BOOLEAN,          ///< bool
    STRING_SET        ///< std::set<std::string>
};

/**
 * @union PrefValue
 * @brief Variant type holding any supported preference value
 */
struct PrefValue {
    PrefType type;
    
    // Using variant for type-safe storage
    std::variant<
        std::string,           // STRING
        int32_t,               // INT
        int64_t,               // LONG
        float,                 // FLOAT
        bool,                  // BOOLEAN
        std::set<std::string>  // STRING_SET
    > data;

    // Default constructor
    PrefValue() : type(PrefType::STRING), data(std::string("")) {}
    
    // Parameterized constructors for each type
    PrefValue(PrefType t, const std::string& v) : type(t), data(v) {}
    PrefValue(PrefType t, int32_t v) : type(t), data(v) {}
    PrefValue(PrefType t, int64_t v) : type(t), data(v) {}
    PrefValue(PrefType t, float v) : type(t), data(v) {}
    PrefValue(PrefType t, bool v) : type(t), data(v) {}
    PrefValue(PrefType t, const std::set<std::string>& v) : type(t), data(v) {}
    
    // Static factory methods
    static PrefValue fromString(const std::string& v) { return PrefValue(PrefType::STRING, v); }
    static PrefValue fromInt(int32_t v) { return PrefValue(PrefType::INT, v); }
    static PrefValue fromLong(int64_t v) { return PrefValue(PrefType::LONG, v); }
    static PrefValue fromFloat(float v) { return PrefValue(PrefType::FLOAT, v); }
    static PrefValue fromBoolean(bool v) { return PrefValue(PrefType::BOOLEAN, v); }
    static PrefValue fromStringSet(const std::set<std::string>& v) { return PrefValue(PrefType::STRING_SET, v); }

    // Accessors with type checking
    std::string asString() const { return std::get<std::string>(data); }
    int32_t asInt() const { return std::get<int32_t>(data); }
    int64_t asLong() const { return std::get<int64_t>(data); }
    float asFloat() const { return std::get<float>(data); }
    bool asBoolean() const { return std::get<bool>(data); }
    std::set<std::string> asStringSet() const { return std::get<std::set<std::string>>(data); }
    
    bool isType(PrefType t) const { return type == t; }
};

/**
 * @enum PrefsError
 * @brief Error codes for SharedPreferences operations
 */
enum class PrefsError : uint8_t {
    NONE = 0,              ///< No error
    FILE_NOT_FOUND,        ///< Preferences file doesn't exist yet
    PARSE_ERROR,           ///< XML parsing failed
    WRITE_ERROR,           ///< Failed to write to disk
    TYPE_MISMATCH,         ///< Requested type doesn't match stored type
    KEY_NOT_FOUND,         ///< Key doesn't exist in preferences
    NOT_INITIALIZED,       ///< Preferences not initialized
    FILE_CORRUPTED,        ///< File exists but content is invalid
    LOCK_TIMEOUT,          ///< Failed to acquire mutex lock
    UNKNOWN                ///< Unknown error
};

/**
 * @struct PrefsResult
 * @brief Result wrapper with error handling (Rust-inspired Result pattern)
 */
template<typename T>
struct PrefsResult {
    T value;
    PrefsError error;
    bool ok;
    
    static PrefsResult success(T v) { return {v, PrefsError::NONE, true}; }
    static PrefsResult failure(PrefsError e) { return {T{}, e, false}; }
    
    operator bool() const { return ok; }
};

// ============================================================================
// FORWARD DECLARATIONS
// ============================================================================

class SharedPreferences;
class SharedPreferencesEditor;

// ============================================================================
// CALLBACK TYPES
// ============================================================================

/**
 * @typedef OnSharedPreferenceChangeListener
 * @brief Callback interface for preference changes (Android-compatible)
 */
using OnSharedPreferenceChangeListener = std::function<void(
    SharedPreferences* prefs,
    const std::string& key
)>;

// ============================================================================
// SHARED PREFERENCES EDITOR
// ============================================================================

/**
 * @class SharedPreferencesEditor
 * @brief Builder pattern editor for batch modifications
 * 
 * @description
 * Implements Android's SharedPreferences.Editor pattern.
 * All modifications are buffered and written atomically on commit()/apply().
 * 
 * Thread Safety:
 * - Each Editor instance should be used from a single thread
 * - commit() acquires the parent's write lock
 * - apply() queues an async write operation
 * 
 * @code
 * // Example usage
 * prefs.edit()
 *      .putString("key1", "value1")
 *      .putInt("key2", 42)
 *      .putBoolean("key3", true)
 *      .remove("old_key")
 *      .commit();  // Returns true if sync write succeeded
 * @endcode
 */
class SharedPreferencesEditor {
public:
    /**
     * @brief Destructor - does NOT auto-commit (must call commit/apply explicitly)
     */
    ~SharedPreferencesEditor() = default;
    
    // ------------------------------------------------------------------------
    // PUT OPERATIONS (return *this for chaining)
    // ------------------------------------------------------------------------
    
    /**
     * @brief Store a string value
     * @param key Preference key
     * @param value String value to store
     * @return Reference to this Editor for chaining
     */
    SharedPreferencesEditor& putString(const std::string& key, const std::string& value);
    
    /**
     * @brief Store a string value (move semantics)
     * @param key Preference key
     * @param value String value to move
     * @return Reference to this Editor for chaining
     */
    SharedPreferencesEditor& putString(const std::string& key, std::string&& value);
    
    /**
     * @brief Store an integer value
     * @param key Preference key
     * @param value Integer value to store
     * @return Reference to this Editor for chaining
     */
    SharedPreferencesEditor& putInt(const std::string& key, int32_t value);
    
    /**
     * @brief Store a long integer value
     * @param key Preference key
     * @param value Long value to store
     * @return Reference to this Editor for chaining
     */
    SharedPreferencesEditor& putLong(const std::string& key, int64_t value);
    
    /**
     * @brief Store a float value
     * @param key Preference key
     * @param value Float value to store
     * @return Reference to this Editor for chaining
     */
    SharedPreferencesEditor& putFloat(const std::string& key, float value);
    
    /**
     * @brief Store a boolean value
     * @param key Preference key
     * @param value Boolean value to store
     * @return Reference to this Editor for chaining
     */
    SharedPreferencesEditor& putBoolean(const std::string& key, bool value);
    
    /**
     * @brief Store a set of strings
     * @param key Preference key
     * @param values Set of strings to store
     * @return Reference to this Editor for chaining
     */
    SharedPreferencesEditor& putStringSet(const std::string& key, const std::set<std::string>& values);
    
    // ------------------------------------------------------------------------
    // REMOVAL OPERATIONS
    // ------------------------------------------------------------------------
    
    /**
     * @brief Remove a single key from preferences
     * @param key Key to remove
     * @return Reference to this Editor for chaining
     */
    SharedPreferencesEditor& remove(const std::string& key);
    
    /**
     * @brief Remove all preferences
     * @return Reference to this Editor for chaining
     */
    SharedPreferencesEditor& clear();
    
    // ------------------------------------------------------------------------
    // COMMIT OPERATIONS
    // ------------------------------------------------------------------------
    
    /**
     * @brief Synchronously write changes to disk
     * @return true if write succeeded and no errors occurred
     * 
     * @description
     * Atomically writes all pending changes to the XML file.
     * Acquires write lock during operation.
     * Triggers registered listeners after successful commit.
     */
    bool commit();
    
    /**
     * @brief Asynchronously write changes to disk
     * @description
     * Queues the write operation for background execution.
     * Changes are guaranteed to be written eventually.
     * In this implementation, uses a simple async mechanism.
     */
    void apply();
    
    // ------------------------------------------------------------------------
    // QUERY OPERATIONS
    // ------------------------------------------------------------------------
    
    /**
     * @brief Check if there are pending modifications
     * @return true if any put/remove/clear has been called
     */
    bool hasPendingChanges() const;
    
    /**
     * @brief Get count of pending modifications
     * @return Number of keys that will be modified on commit
     */
    size_t pendingChangeCount() const;

private:
    // Private constructor - only SharedPreferences can create editors
    friend class SharedPreferences;
    
    /**
     * @brief Construct an editor for the given preferences
     * @param prefs Parent SharedPreferences instance
     */
    explicit SharedPreferencesEditor(SharedPreferences* prefs);
    
    SharedPreferences* m_prefs;              ///< Parent preferences
    std::map<std::string, PrefValue> m_puts;  ///< Pending puts (empty = remove)
    std::set<std::string> m_removes;          ///< Pending removes
    bool m_clear_all;                         ///< Clear flag
    
    /// Track which keys have been modified (for listeners)
    std::set<std::string> m_modified_keys;
};

// ============================================================================
// SHARED PREFERENCES
// ============================================================================

/**
 * @class SharedPreferences
 * @brief Persistent key-value storage backed by XML files
 * 
 * @description
 * Main class implementing Android's SharedPreferences interface.
 * Provides methods for reading/writing persistent key-value pairs.
 * 
 * Lifecycle:
 * 1. Construct with package name and preferences name
 * 2. Call getSharedPreferences() or use directly
 * 3. Read values with getXxx(key, default)
 * 4. Write values via edit().putXxx().commit()
 * 5. Destroy when done (auto-saves if needed)
 * 
 * Thread Safety:
 * - All read operations are protected by shared (read) lock
 * - All write operations are protected by exclusive (write) lock
 * - Multiple concurrent readers allowed
 * - Only one writer at a time
 * 
 * Memory Model:
 * - On construction: reads XML file into memory map
 * - All reads come from memory (fast)
 * - commit() writes memory map back to XML
 * - apply() schedules async commit
 * 
 * @code
 * // Basic usage
 * SharedPreferences prefs("org.telegram.messenger", "mainconfig");
 * 
 * // Read with defaults
 * std::string token = prefs.getString("auth_token", "");
 * bool loggedIn = prefs.getBoolean("logged_in", false);
 * 
 * // Write using editor
 * if (prefs.edit().putString("new_key", "value").commit()) {
 *     std::cout << "Saved successfully!" << std::endl;
 * }
 * @endcode
 */
class SharedPreferences {
public:
    // ------------------------------------------------------------------------
    // CONSTRUCTION / DESTRUCTION
    // ------------------------------------------------------------------------
    
    /**
     * @brief Construct SharedPreferences for given package and name
     * @param package_name Android package name (e.g., "org.telegram.messenger")
     * @param prefs_name Name of preferences file (without .xml extension)
     * @param base_path Base directory for storage (default: "runtime/data")
     * 
     * @description
     * Creates or opens a SharedPreferences instance.
     * If the XML file exists, it's loaded into memory.
     * If not, an empty preferences set is created.
     * The file will be created on first commit().
     */
    SharedPreferences(
        const std::string& package_name,
        const std::string& prefs_name,
        const std::string& base_path = "runtime/data"
    );
    
    /**
     * @brief Construct with explicit file path
     * @param xml_file Full path to the XML file
     * 
     * @description
     * Alternative constructor for testing or special cases.
     * Uses exact path provided without package/name derivation.
     */
    explicit SharedPreferences(const fs::path& xml_file);
    
    /**
     * @brief Destructor
     * @description
     * Note: Does NOT auto-commit pending changes.
     * Caller must explicitly call commit() to persist changes.
     */
    ~SharedPreferences() = default;
    
    // Prevent copying (would break thread safety)
    SharedPreferences(const SharedPreferences&) = delete;
    SharedPreferences& operator=(const SharedPreferences&) = delete;
    
    // Allow moving
    SharedPreferences(SharedPreferences&&) noexcept = default;
    SharedPreferences& operator=(SharedPreferences&&) noexcept = default;

    // ------------------------------------------------------------------------
    // READ OPERATIONS (thread-safe)
    // ------------------------------------------------------------------------
    
    /**
     * @brief Get a string value
     * @param key Preference key
     * @param def_value Default value if key not found or wrong type
     * @return Stored value or default
     */
    std::string getString(const std::string& key, const std::string& def_value = "") const;
    
    /**
     * @brief Get an integer value (32-bit)
     * @param key Preference key
     * @param def_value Default value if key not found or wrong type
     * @return Stored value or default
     */
    int32_t getInt(const std::string& key, int32_t def_value = 0) const;
    
    /**
     * @brief Get a long integer value (64-bit)
     * @param key Preference key
     * @param def_value Default value if key not found or wrong type
     * @return Stored value or default
     */
    int64_t getLong(const std::string& key, int64_t def_value = 0) const;
    
    /**
     * @brief Get a float value
     * @param key Preference key
     * @param def_value Default value if key not found or wrong type
     * @return Stored value or default
     */
    float getFloat(const std::string& key, float def_value = 0.0f) const;
    
    /**
     * @brief Get a boolean value
     * @param key Preference key
     * @param def_value Default value if key not found or wrong type
     * @return Stored value or default
     */
    bool getBoolean(const std::string& key, bool def_value = false) const;
    
    /**
     * @brief Get a set of strings
     * @param key Preference key
     * @param def_value Default value if key not found or wrong type
     * @return Stored value or default
     */
    std::set<std::string> getStringSet(
        const std::string& key, 
        const std::set<std::string>& def_value = {}
    ) const;
    
    // ------------------------------------------------------------------------
    // QUERY OPERATIONS (thread-safe)
    // ------------------------------------------------------------------------
    
    /**
     * @brief Check if a key exists in preferences
     * @param key Key to check
     * @return true if key exists
     */
    bool contains(const std::string& key) const;
    
    /**
     * @brief Get all keys in preferences
     * @return Set of all key names
     */
    std::set<std::string> getAllKeys() const;
    
    /**
     * @brief Get all preferences as a map
     * @return Map of key -> PrefValue pairs (copy)
     */
    std::map<std::string, PrefValue> getAll() const;
    
    /**
     * @brief Get total number of preferences
     * @return Count of stored key-value pairs
     */
    size_t size() const;
    
    /**
     * @brief Check if preferences is empty
     * @return true if no preferences stored
     */
    bool isEmpty() const;
    
    // ------------------------------------------------------------------------
    // EDITOR OPERATIONS
    // ------------------------------------------------------------------------
    
    /**
     * @brief Create an Editor for modifying these preferences
     * @return New Editor instance for batch modifications
     * 
     * @description
     * Each call returns a new, independent Editor.
     * Multiple Editors can exist simultaneously.
     * Last commit() wins (last-write-wins semantics).
     */
    SharedPreferencesEditor edit();

    // ------------------------------------------------------------------------
    // LISTENER REGISTRATION
    // ------------------------------------------------------------------------
    
    /**
     * @brief Register a change listener
     * @param listener Callback function
     * @description
     * Listener is called after any successful commit().
     * Called with the SharedPreferences instance and changed key.
     */
    void registerOnSharedPreferenceChangeListener(OnSharedPreferenceChangeListener listener);
    
    /**
     * @brief Unregister a change listener
     * @param listener Previously registered callback
     */
    void unregisterOnSharedPreferenceChangeListener(OnSharedPreferenceChangeListener listener);

    // ------------------------------------------------------------------------
    // FILE OPERATIONS
    // ------------------------------------------------------------------------
    
    /**
     * @brief Force reload from disk (discard uncommitted memory changes)
     * @return true if reload succeeded
     */
    bool reload();
    
    /**
     * @brief Get the underlying file path
     * @return Path to the XML file
     */
    fs::path getFilePath() const;
    
    /**
     * @brief Get the package name
     * @return Package name this preferences belongs to
     */
    std::string getPackageName() const;
    
    /**
     * @brief Get the preferences name
     * @return Name of this preferences set
     */
    std::string getName() const;
    
    /**
     * @brief Check if the backing file exists on disk
     * @return true if XML file exists
     */
    bool fileExists() const;
    
    /**
     * @brief Delete the backing file from disk
     * @return true if deletion succeeded
     * @warning This is irreversible!
     */
    bool deleteFile();
    
    // ------------------------------------------------------------------------
    // DEBUG / DIAGNOSTICS
    // ------------------------------------------------------------------------
    
    /**
     * @brief Print contents to stdout (for debugging)
     * @param verbose Include extra details
     */
    void debugPrint(bool verbose = false) const;
    
    /**
     * @brief Validate XML integrity
     * @return true if file parses correctly
     */
    bool validate() const;
    
    /**
     * @brief Get last error message
     * @return Human-readable error description
     */
    std::string getLastError() const;

private:
    // ------------------------------------------------------------------------
    // PRIVATE MEMBERS
    // ------------------------------------------------------------------------
    
    std::string m_package_name;                     ///< Package name
    std::string m_name;                             ///< Preferences name
    fs::path m_file_path;                           ///< Full path to XML file
    
    mutable std::shared_mutex m_rw_lock;            ///< Read-write lock for thread safety
    std::map<std::string, PrefValue> m_data;        ///< In-memory preference store
    std::vector<OnSharedPreferenceChangeListener> m_listeners;  ///< Change listeners
    mutable std::string m_last_error;               ///< Last error message

    // ------------------------------------------------------------------------
    // PRIVATE METHODS (called by Editor friend)
    // ------------------------------------------------------------------------
    
    friend class SharedPreferencesEditor;
    
    /**
     * @brief Apply editor changes to this preferences instance
     * @param editor The editor whose changes to apply
     * @return true if apply succeeded
     */
    bool applyEditorChanges(const SharedPreferencesEditor& editor);
    
    /**
     * @brief Notify listeners of changes
     * @param keys Set of keys that were modified
     */
    void notifyListeners(const std::set<std::string>& keys);

    // ------------------------------------------------------------------------
    // XML I/O METHODS
    // ------------------------------------------------------------------------
    
    /**
     * @brief Load preferences from XML file
     * @return true if load succeeded
     */
    bool loadFromFile();
    
    /**
     * @brief Save preferences to XML file
     * @return true if save succeeded
     */
    bool saveToFile();
    
    /**
     * @brief Parse XML content into m_data map
     * @param content XML string content
     * @return true if parse succeeded
     */
    bool parseXml(const std::string& content);
    
    /**
     * @brief Generate XML content from m_data map
     * @return XML string
     */
    std::string generateXml() const;
    
    /**
     * @brief Escape XML special characters
     * @param input Raw string
     * @return Escaped string safe for XML
     */
    static std::string escapeXml(const std::string& input);
    
    /**
     * @brief Unescape XML entities
     * @input Escaped XML string
     * @return Unescaped original string
     */
    static std::string unescapeXml(const std::string& input);
};

// ============================================================================
// FACTORY / UTILITY FUNCTIONS
// ============================================================================

/**
 * @namespace SharedPreferencesFactory
 * @brief Factory methods for creating SharedPreferences instances
 */
namespace SharedPreferencesFactory {

    /**
     * @brief Create SharedPreferences with default settings
     * @param package_name Android package name
     * @param prefs_name Preferences name
     * @return Shared pointer to SharedPreferences
     */
    std::shared_ptr<SharedPreferences> create(
        const std::string& package_name,
        const std::string& prefs_name
    );
    
    /**
     * @brief Create SharedPreferences for Telegram app
     * @param prefs_name Preferences name (e.g., "mainconfig")
     * @return Shared pointer configured for org.telegram.messenger
     */
    std::shared_ptr<SharedPreferences> createForTelegram(
        const std::string& prefs_name = "mainconfig"
    );
    
    /**
     * @brief List all existing preferences files for a package
     * @param package_name Package to query
     * @return Vector of preferences names
     */
    std::vector<std::string> listPreferences(const std::string& package_name);
    
    /**
     * @brief Delete all preferences for a package
     * @param package_name Package to clear
     * @return Number of files deleted
     */
    size_t deleteAllPreferences(const std::string& package_name);

} // namespace SharedPreferencesFactory

} // namespace AndroidAPI

#endif // SHARED_PREFS_H
