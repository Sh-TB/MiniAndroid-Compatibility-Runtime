/**
 * @file android_context.h
 * @brief Android Context API compatibility layer for MiniAndroid runtime
 * 
 * @description
 * Implements the Android Context abstract class that is the foundation of all
 * Android application interaction. Every Android app starts by obtaining a Context,
 * and Telegram's ApplicationLoader.onCreate() immediately calls:
 * 
 * - context.getSharedPreferences() → Session persistence (NOW WORKING)
 * - context.getFilesDir() → File storage (NOW WORKING)
 * - context.getCacheDir() → Cache access (NOW WORKING)
 * - context.getPackageName() → Package identification (NOW WORKING)
 * - context.getResources() → Resource access (STUBBED)
 * 
 * Class Hierarchy (matches Android):
 * @code
 * Context (abstract interface)
 *     ↓
 * ContextWrapper (base implementation with delegation)
 *     ↓
 * Application (concrete, represents the app itself)
 *     ↓
 * ApplicationLoader (Telegram's class, loaded from DEX in future)
 * @endcode
 * 
 * Key Design Decisions:
 * 1. Composition over inheritance - wraps FileSandbox + SharedPreferences
 * 2. Thread-safe - uses shared_mutex for read-heavy workloads
 * 3. Lazy initialization - directories created on first access
 * 4. Minimal stubs - only implement what Telegram actually calls
 * 
 * Usage Example (how Telegram will use this):
 * @code
 * // In ApplicationLoader.onCreate():
 * Context context = Runtime.getContext("org.telegram.messenger");
 * 
 * // Get preferences (session persistence)
 * SharedPreferences prefs = context.getSharedPreferences("mainconfig", 0);
 * boolean loggedIn = prefs.getBoolean("logged_in_key", false);
 * 
 * // Access files
 * File filesDir = context.getFilesDir();
 * File cacheDir = context.getCacheDir();
 * 
 * // Get package info
 * String pkgName = context.getPackageName();
 * Resources res = context.getResources();
 * @endcode
 * 
 * @author EXP-037 Development (Phase A, Week 3)
 * @date 2026-08-14
 * @version 1.0.0
 * 
 * @license MIT
 * 
 * @see https://developer.android.com/reference/android/content/Context
 * @see FileSandbox - Provides file system abstraction
 * @see SharedPreferences - Provides key-value persistence
 */

#ifndef ANDROID_CONTEXT_H
#define ANDROID_CONTEXT_H

#include <string>
#include <memory>
#include <vector>
#include <map>
#include <filesystem>
#include <functional>
#include <shared_mutex>
#include <variant>

// Forward declarations for components we wrap
namespace Storage {
    class FileSandbox;
}

namespace AndroidAPI {
    class SharedPreferences;
}

namespace fs = std::filesystem;

/**
 * @namespace AndroidAPI
 * @brief Android framework API compatibility layer
 */
namespace AndroidAPI {

// ============================================================================
// FORWARD DECLARATIONS
// ============================================================================

class Resources;
class AssetManager;
class PackageManager;

// ============================================================================
// CONTEXT CONFIGURATION
// ============================================================================

/**
 * @struct ContextConfig
 * @brief Configuration options for Context creation
 */
struct ContextConfig {
    std::string base_path;              ///< Base directory (default: "runtime/data")
    bool auto_create_dirs;             ///< Auto-create dirs on access (default: true)
    bool strict_mode;                  ///< Throw on errors vs return defaults
    
    ContextConfig()
        : base_path("runtime/data")
        , auto_create_dirs(true)
        , strict_mode(false) {}
};

// ============================================================================
// ABSTRACT CONTEXT INTERFACE
// ============================================================================

/**
 * @class Context
 * @brief Abstract interface matching Android's Context class
 * 
 * @description
 * Defines the contract that all Context implementations must follow.
 * This mirrors Android's android.content.Context abstract class.
 * 
 * Only methods that Telegram actually uses are included here.
 * Additional methods can be added as needed for other apps.
 * 
 * Thread Safety:
 * All implementations must be thread-safe.
 */
class Context {
public:
    virtual ~Context() = default;
    
    // ========================================================================
    // PREFERENCES ACCESS (P0 - CRITICAL FOR TELEGRAM)
    // ========================================================================
    
    /**
     * @brief Get SharedPreferences instance (Android: Context.getSharedPreferences())
     * 
     * @param name Preferences file name (without .xml extension)
     * @param mode Access mode (currently ignored, always private)
     * @return Pointer to SharedPreferences instance (never null)
     * 
     * @description
     * This is THE most critical method for session persistence.
     * Telegram calls this in ApplicationLoader.onCreate() to check login state.
     * 
     * Implementation must:
     * - Return existing instance if already created
     * - Create new instance if first access
     * - Cache instances for performance
     * - Be thread-safe
     */
    virtual std::shared_ptr<SharedPreferences> getSharedPreferences(
        const std::string& name, 
        int mode = 0) = 0;
    
    // ========================================================================
    // FILE SYSTEM ACCESS (P0 - CRITICAL FOR TELEGRAM)
    // ========================================================================
    
    /**
     * @brief Get files directory (Android: Context.getFilesDir())
     * 
     * @return Path to app-private files directory
     * 
     * Returns: runtime/data/<package>/files/
     */
    virtual fs::path getFilesDir() const = 0;
    
    /**
     * @brief Get cache directory (Android: Context.getCacheDir())
     * 
     * @return Path to app-private cache directory
     * 
     * Returns: runtime/data/<package>/cache/
     */
    virtual fs::path getCacheDir() const = 0;
    
    /**
     * @brief Get databases directory (Android: Context.getDatabasePath())
     * 
     * @param name Database file name
     * @return Full path to database file
     * 
     * Returns: runtime/data/<package>/databases/<name>
     */
    virtual fs::path getDatabasePath(const std::string& name) const = 0;
    
    /**
     * @brief Open file for reading (Android: Context.openFileInput())
     * 
     * @param name File name relative to files dir
     * @return Input stream to file, or nullptr if not found
     */
    virtual std::unique_ptr<std::ifstream> openFileInput(const std::string& name) const = 0;
    
    /**
     * @brief Open file for writing (Android: Context.openFileOutput())
     * 
     * @param name File name relative to files dir
     * @param mode Write mode (append, truncate, etc.)
     * @return Output stream to file
     */
    virtual std::unique_ptr<std::ofstream> openFileOutput(
        const std::string& name, 
        int mode = 0) const = 0;
    
    /**
     * @brief Delete file from files directory (Android: Context.deleteFile())
     * 
     * @param name File name to delete
     * @return true if deletion succeeded
     */
    virtual bool deleteFile(const std::string& name) = 0;
    
    /**
     * @brief List files in files directory (Android: Context.fileList())
     * 
     * @return Vector of file names
     */
    virtual std::vector<std::string> fileList() const = 0;

    // ========================================================================
    // PACKAGE INFORMATION (P0 - CRITICAL FOR TELEGRAM)
    // ========================================================================
    
    /**
     * @brief Get package name (Android: Context.getPackageName())
     * 
     * @return Package name string (e.g., "org.telegram.messenger")
     */
    virtual std::string getPackageName() const = 0;
    
    /**
     * @brief Get application info (Android: Context.getApplicationInfo())
     * 
     * @return Application info structure (simplified)
     */
    virtual struct ApplicationInfo getApplicationInfo() const = 0;

    // ========================================================================
    // RESOURCES ACCESS (P1 - STUBBED FOR NOW)
    // ========================================================================
    
    /**
     * @brief Get Resources instance (Android: Context.getResources())
     * 
     * @return Pointer to Resources object (may be minimal stub)
     * 
     * @note Currently returns a stub. Real implementation needed when
     *       Telegram accesses strings.xml, drawables, etc.
     */
    virtual std::shared_ptr<Resources> getResources() const = 0;
    
    /**
     * @brief Get AssetManager (Android: Context.getAssets())
     * 
     * @return Pointer to AssetManager instance
     */
    virtual std::shared_ptr<AssetManager> getAssets() const = 0;
    
    /**
     * @brief Get string resource (Android: Context.getString())
     * 
     * @param resourceId Resource ID (R.string.xxx)
     * @param defaultValue Default value if resource not found
     * @return String value, or default if not found
     */
    virtual std::string getString(int resourceId, const std::string& defaultValue = "") const = 0;

    // ========================================================================
    // CLASS LOADING (P1 - FUTURE)
    // ========================================================================
    
    /**
     * @brief Load class by name (Android: Context.getClassLoader().loadClass())
     * 
     * @param className Fully qualified class name
     * @return Class reference (future: DEX-loaded class)
     */
    virtual void* loadClass(const std::string& className) = 0;

    // ========================================================================
    // LIFECYCLE & STATE (P1 - FUTURE)
    // ========================================================================
    
    /**
     * @brief Check if this is the main process (Android: Context.isMainProcess())
     */
    virtual bool isMainProcess() const { return true; }
};

// ============================================================================
// APPLICATION INFO STRUCTURE
// ============================================================================

/**
 * @struct ApplicationInfo
 * @brief Simplified version of Android's ApplicationInfo
 */
struct ApplicationInfo {
    std::string packageName;          ///< Package name
    std::string sourceDir;            ///< Source directory (APK path)
    std::string dataDir;              ///< Data directory
    int uid;                          ///< User ID
    int targetSdkVersion;             ///< Target SDK version
    int flags;                        ///< Various flags
    bool enabled;                     ///< Is application enabled
    
    ApplicationInfo() 
        : uid(0)
        , targetSdkVersion(30)  // Android 11 default
        , flags(0)
        , enabled(true) {}
};

// ============================================================================
// CONTEXT WRAPPER BASE CLASS
// ============================================================================

/**
 * @class ContextWrapper
 * @brief Base implementation of Context with delegation support
 * 
 * @description
 * Implements common functionality and provides delegation pattern.
 * This matches Android's android.content.ContextWrapper.
 * 
 * Subclasses can override specific methods or delegate to wrapped context.
 */
class ContextWrapper : public Context {
public:
    /**
     * @brief Construct wrapper with optional delegate
     * @param baseContext Context to delegate to (can be null)
     */
    explicit ContextWrapper(std::shared_ptr<Context> baseContext = nullptr);
    
    virtual ~ContextWrapper() = default;
    
    // Set/get the base context for delegation
    void setBaseContext(std::shared_ptr<Context> baseContext);
    std::shared_ptr<Context> getBaseContext() const;
    
    // Default implementations (override in subclasses)
    std::shared_ptr<SharedPreferences> getSharedPreferences(
        const std::string& name, 
        int mode = 0) override;
        
    fs::path getFilesDir() const override;
    fs::path getCacheDir() const override;
    fs::path getDatabasePath(const std::string& name) const override;
    std::unique_ptr<std::ifstream> openFileInput(const std::string& name) const override;
    std::unique_ptr<std::ofstream> openFileOutput(const std::string& name, int mode = 0) const override;
    bool deleteFile(const std::string& name) override;
    std::vector<std::string> fileList() const override;
    
    std::string getPackageName() const override;
    ApplicationInfo getApplicationInfo() const override;
    
    std::shared_ptr<Resources> getResources() const override;
    std::shared_ptr<AssetManager> getAssets() const override;
    std::string getString(int resourceId, const std::string& defaultValue = "") const override;
    
    void* loadClass(const std::string& className) override;

protected:
    std::shared_ptr<Context> m_baseContext;  ///< Delegate context
};

// ============================================================================
// APPLICATION CONTEXT (MAIN IMPLEMENTATION)
// ============================================================================

/**
 * @class ApplicationContext
 * @brief Concrete Context implementation representing an Android Application
 * 
 * @description
 * This is the primary Context implementation that MiniAndroid uses.
 * It integrates:
 * - FileSandbox for file system operations
 * - SharedPreferences for key-value persistence
 * - Package information management
 * 
 * When Telegram runs, its ApplicationLoader will receive an instance of this class.
 * 
 * Lifecycle:
 * 1. Create with package name
 * 2. Call initialize() (or auto-init on first use)
 * 3. Use throughout application lifetime
 * 4. Destroy when app shuts down
 * 
 * Example:
 * @code
 * // Create context for Telegram
 * ApplicationContext telegramCtx("org.telegram.messenger");
 * 
 * // Now ready for Telegram to use
 * auto prefs = telegramCtx.getSharedPreferences("mainconfig", 0);
 * bool isLoggedIn = prefs->getBoolean("logged_in_key", false);
 * @endcode
 */
class ApplicationContext : public ContextWrapper {
public:
    // ========================================================================
    // CONSTRUCTION
    // ========================================================================
    
    /**
     * @brief Construct ApplicationContext for given package
     * @param packageName Android package name (e.g., "org.telegram.messenger")
     * @param config Optional configuration overrides
     */
    explicit ApplicationContext(
        const std::string& packageName,
        const ContextConfig& config = ContextConfig());
    
    /**
     * @brief Destructor - cleans up resources
     */
    ~ApplicationContext() override;
    
    // Prevent copying (singleton-like per package)
    ApplicationContext(const ApplicationContext&) = delete;
    ApplicationContext& operator=(const ApplicationContext&) = delete;
    
    // Allow moving
    ApplicationContext(ApplicationContext&& other) noexcept;
    ApplicationContext& operator=(ApplicationContext&& other) noexcept;
    
    // ========================================================================
    // INITIALIZATION
    // ========================================================================
    
    /**
     * @brief Initialize the context (create directories, etc.)
     * @return true if initialization succeeded
     * 
     * Called automatically on first access if not called explicitly.
     */
    bool initialize();
    
    /**
     * @brief Check if context has been initialized
     */
    bool isInitialized() const;
    
    // ========================================================================
    // OVERRIDES - PREFERENCES (delegates to SharedPreferences)
    // ========================================================================
    
    std::shared_ptr<SharedPreferences> getSharedPreferences(
        const std::string& name, 
        int mode = 0) override;
    
    // ========================================================================
    // OVERRIDES - FILE SYSTEM (delegates to FileSandbox)
    // ========================================================================
    
    fs::path getFilesDir() const override;
    fs::path getCacheDir() const override;
    fs::path getDatabasePath(const std::string& name) const override;
    std::unique_ptr<std::ifstream> openFileInput(const std::string& name) const override;
    std::unique_ptr<std::ofstream> openFileOutput(const std::string& name, int mode = 0) const override;
    bool deleteFile(const std::string& name) override;
    std::vector<std::string> fileList() const override;
    
    // ========================================================================
    // OVERRIDES - PACKAGE INFO
    // ========================================================================
    
    std::string getPackageName() const override;
    ApplicationInfo getApplicationInfo() const override;
    
    // ========================================================================
    // OVERRIDES - RESOURCES (stubbed)
    // ========================================================================
    
    std::shared_ptr<Resources> getResources() const override;
    std::shared_ptr<AssetManager> getAssets() const override;
    std::string getString(int resourceId, const std::string& defaultValue = "") const override;
    
    // ========================================================================
    // OVERRIDES - CLASS LOADING (stubbed)
    // ========================================================================
    
    void* loadClass(const std::string& className) override;
    
    // ========================================================================
    // ADDITIONAL UTILITY METHODS
    // ========================================================================
    
    /**
     * @brief Get direct access to underlying FileSandbox
     * @return Pointer to FileSandbox instance (never null after init)
     */
    Storage::FileSandbox* getFileSandbox() const;
    
    /**
     * @brief Get list of all cached SharedPreferences names
     * @return Vector of preference file names
     */
    std::vector<std::string> getPreferencesList() const;
    
    /**
     * @brief Clear all cached data (for testing/reset)
     */
    void clearCache();
    
    /**
     * @brief Get debug information about this context
     * @return Human-readable status string
     */
    std::string debugInfo() const;

private:
    // ========================================================================
    // PRIVATE MEMBERS
    // ========================================================================
    
    std::string m_packageName;                    ///< Package name
    ContextConfig m_config;                       ///< Configuration
    mutable std::shared_mutex m_rwLock;           ///< Read-write lock
    
    // Components (lazy initialized)
    std::unique_ptr<Storage::FileSandbox> m_sandbox;           ///< File sandbox
    mutable std::map<std::string, 
        std::shared_ptr<SharedPreferences>> m_prefsCache;      ///< Cached prefs
    std::shared_ptr<Resources> m_resources;         ///< Resources (stub)
    std::shared_ptr<AssetManager> m_assets;          ///< Assets (stub)
    
    ApplicationInfo m_appInfo;                      ///< App info
    
    bool m_initialized;                             ///< Init flag
    
    // ========================================================================
    // PRIVATE METHODS
    // ========================================================================
    
    /**
     * @brief Ensure context is initialized (called before operations)
     */
    void ensureInitialized() const;
    
    /**
     * @brief Create Resources stub if not exists
     */
    void ensureResources() const;
};

// ============================================================================
// FACTORY FUNCTIONS
// ============================================================================

/**
 * @namespace ContextFactory
 * @brief Factory methods for creating Context instances
 */
namespace ContextFactory {

    /**
     * @brief Create ApplicationContext for any package
     * @param packageName Android package name
     * @return Shared pointer to initialized context
     */
    std::shared_ptr<ApplicationContext> create(
        const std::string& packageName);
    
    /**
     * @brief Create pre-configured context for Telegram
     * @return Shared pointer configured for org.telegram.messenger
     * 
     * Convenience function - most common use case during development.
     */
    std::shared_ptr<ApplicationContext> createForTelegram();
    
    /**
     * @brief Get global/default context (if one exists)
     * @return Default context or null
     * 
     * Used when code needs "a context" but doesn't care which.
     */
    std::shared_ptr<Context> getDefault();

} // namespace ContextFactory

} // namespace AndroidAPI

#endif // ANDROID_CONTEXT_H
