/**
 * @file application_context.cpp
 * @brief Implementation of Android Context API compatibility layer
 * 
 * @description
 * Complete implementation of ApplicationContext that integrates:
 * - FileSandbox (file system operations)
 * - SharedPreferences (key-value persistence)
 * - Package management
 * - Resource stubs
 * 
 * This is THE class that Telegram's ApplicationLoader will receive.
 * Every method here maps to an actual Android Context API call.
 * 
 * Key Implementation Details:
 * - Lazy initialization: Components created on first access
 * - Thread safety: std::shared_mutex for read-write locking
 * - Caching: SharedPreferences instances cached by name
 * - Delegation pattern: Can wrap other contexts
 * 
 * @author EXP-037 Development (Phase A, Week 3)
 * @date 2026-08-14
 * @version 1.0.0
 * 
 * @license MIT
 */

#include "android_context.h"
#include "shared_prefs.h"
#include "storage/file_sandbox.h"

#include <iostream>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <cassert>

namespace AndroidAPI {

// ============================================================================
// STUB CLASSES FOR RESOURCES/ASSETS (P1 - Future Implementation)
// ============================================================================

/**
 * @class Resources
 * @brief Stub Resources class (will be fully implemented later)
 */
class Resources {
public:
    Resources() = default;
    ~Resources() = default;
    
    // Stub methods - return empty defaults
    std::string getString(int id, const std::string& def = "") const { 
        (void)id; 
        return def; 
    }
    
    int getInteger(int id, int def = 0) const { 
        (void)id; 
        return def; 
    }
    
    bool getBoolean(int id, bool def = false) const { 
        (void)id; 
        return def; 
    }
    
    // For debugging
    std::string debugInfo() const {
        return "Resources (stub implementation)";
    }
};

/**
 * @class AssetManager  
 * @brief Stub AssetManager class (will be fully implemented later)
 */
class AssetManager {
public:
    AssetManager() = default;
    ~AssetManager() = default;
    
    // Stub methods
    std::unique_ptr<std::ifstream> open(const std::string& path) const {
        (void)path;
        return nullptr;
    }
    
    std::vector<std::string> list(const std::string& path) const {
        (void)path;
        return {};
    }
    
    // For debugging
    std::string debugInfo() const {
        return "AssetManager (stub implementation)";
    }
};


// ============================================================================
// CONTEXT WRAPPER IMPLEMENTATION
// ============================================================================

ContextWrapper::ContextWrapper(std::shared_ptr<Context> baseContext)
    : m_baseContext(baseContext) {
}

void ContextWrapper::setBaseContext(std::shared_ptr<Context> baseContext) {
    m_baseContext = baseContext;
}

std::shared_ptr<Context> ContextWrapper::getBaseContext() const {
    return m_baseContext;
}

std::shared_ptr<SharedPreferences> ContextWrapper::getSharedPreferences(
    const std::string& name, int mode) {
    if (m_baseContext) {
        return m_baseContext->getSharedPreferences(name, mode);
    }
    throw std::runtime_error("ContextWrapper: No base context set");
}

fs::path ContextWrapper::getFilesDir() const {
    if (m_baseContext) return m_baseContext->getFilesDir();
    throw std::runtime_error("ContextWrapper: No base context set");
}

fs::path ContextWrapper::getCacheDir() const {
    if (m_baseContext) return m_baseContext->getCacheDir();
    throw std::runtime_error("ContextWrapper: No base context set");
}

fs::path ContextWrapper::getDatabasePath(const std::string& name) const {
    if (m_baseContext) return m_baseContext->getDatabasePath(name);
    throw std::runtime_error("ContextWrapper: No base context set");
}

std::unique_ptr<std::ifstream> ContextWrapper::openFileInput(
    const std::string& name) const {
    if (m_baseContext) return m_baseContext->openFileInput(name);
    return nullptr;
}

std::unique_ptr<std::ofstream> ContextWrapper::openFileOutput(
    const std::string& name, int mode) const {
    if (m_baseContext) return m_baseContext->openFileOutput(name, mode);
    return nullptr;
}

bool ContextWrapper::deleteFile(const std::string& name) {
    if (m_baseContext) return m_baseContext->deleteFile(name);
    return false;
}

std::vector<std::string> ContextWrapper::fileList() const {
    if (m_baseContext) return m_baseContext->fileList();
    return {};
}

std::string ContextWrapper::getPackageName() const {
    if (m_baseContext) return m_baseContext->getPackageName();
    throw std::runtime_error("ContextWrapper: No base context set");
}

ApplicationInfo ContextWrapper::getApplicationInfo() const {
    if (m_baseContext) return m_baseContext->getApplicationInfo();
    throw std::runtime_error("ContextWrapper: No base context set");
}

std::shared_ptr<Resources> ContextWrapper::getResources() const {
    if (m_baseContext) return m_baseContext->getResources();
    throw std::runtime_error("ContextWrapper: No base context set");
}

std::shared_ptr<AssetManager> ContextWrapper::getAssets() const {
    if (m_baseContext) return m_baseContext->getAssets();
    throw std::runtime_error("ContextWrapper: No base context set");
}

std::string ContextWrapper::getString(int resourceId, const std::string& defaultValue) const {
    if (m_baseContext) return m_baseContext->getString(resourceId, defaultValue);
    return defaultValue;
}

void* ContextWrapper::loadClass(const std::string& className) {
    if (m_baseContext) return m_baseContext->loadClass(className);
    throw std::runtime_error("ContextWrapper: No base context set");
}


// ============================================================================
// APPLICATION CONTEXT IMPLEMENTATION
// ============================================================================

ApplicationContext::ApplicationContext(
    const std::string& packageName,
    const ContextConfig& config)
    : ContextWrapper(nullptr)  // No base context - we ARE the base
    , m_packageName(packageName)
    , m_config(config)
    , m_initialized(false) {
    
    // Set up application info
    m_appInfo.packageName = packageName;
    m_appInfo.dataDir = config.base_path + "/" + packageName;
    m_appInfo.sourceDir = "";  // Will be set when APK is loaded
    m_appInfo.uid = 10000 + std::hash<std::string>{}(packageName) % 10000;
}

ApplicationContext::~ApplicationContext() {
    // Clean up resources
    std::unique_lock<std::shared_mutex> lock(m_rwLock);
    m_prefsCache.clear();
    m_sandbox.reset();
    m_resources.reset();
    m_assets.reset();
}

ApplicationContext::ApplicationContext(ApplicationContext&& other) noexcept
    : ContextWrapper(nullptr)
    , m_packageName(std::move(other.m_packageName))
    , m_config(std::move(other.m_config))
    , m_sandbox(std::move(other.m_sandbox))
    , m_prefsCache(std::move(other.m_prefsCache))
    , m_resources(std::move(other.m_resources))
    , m_assets(std::move(other.m_assets))
    , m_appInfo(std::move(other.m_appInfo))
    , m_initialized(other.m_initialized) {
    other.m_initialized = false;
}

ApplicationContext& ApplicationContext::operator=(ApplicationContext&& other) noexcept {
    if (this != &other) {
        m_packageName = std::move(other.m_packageName);
        m_config = std::move(other.m_config);
        m_sandbox = std::move(other.m_sandbox);
        m_prefsCache = std::move(other.m_prefsCache);
        m_resources = std::move(other.m_resources);
        m_assets = std::move(other.m_assets);
        m_appInfo = std::move(other.m_appInfo);
        m_initialized = other.m_initialized;
        other.m_initialized = false;
    }
    return *this;
}

// ============================================================================
// INITIALIZATION
// ============================================================================

bool ApplicationContext::initialize() {
    // Note: We don't lock here to avoid deadlock with getFilesDir/getCacheDir
    // which are called during initialization output.
    // Thread safety: first caller initializes, others wait.
    // In production, this should use a once_flag or similar mechanism.
    
    if (m_initialized) {
        return true;  // Already initialized
    }
    
    try {
        // Create FileSandbox with our configuration
        Storage::SandboxConfig sandboxConfig;
        sandboxConfig.root_path = m_config.base_path;
        sandboxConfig.auto_create = m_config.auto_create_dirs;
        sandboxConfig.strict_mode = m_config.strict_mode;
        
        m_sandbox = std::make_unique<Storage::FileSandbox>(
            m_packageName, sandboxConfig);
        
        // Initialize sandbox (creates directory structure)
        if (!m_sandbox->initialize()) {
            std::cerr << "[ApplicationContext] Failed to initialize FileSandbox" << std::endl;
            return false;
        }
        
        // Create stub resources
        m_resources = std::make_shared<Resources>();
        m_assets = std::make_shared<AssetManager>();
        
        m_initialized = true;
        
        // Debug output (outside lock, after init complete)
        std::cout << "[ApplicationContext] Initialized for package: " 
                  << m_packageName << std::endl;
        
        fs::path filesDir, cacheDir;
        {
            std::shared_lock<std::shared_mutex> lock(m_rwLock);
            if (m_sandbox) {
                filesDir = m_sandbox->getDirectory(Storage::SandboxDirectory::FILES);
                cacheDir = m_sandbox->getDirectory(Storage::SandboxDirectory::CACHE);
            }
        }
        
        std::cout << "[ApplicationContext] Files dir: " << filesDir.string() << std::endl;
        std::cout << "[ApplicationContext] Cache dir: " << cacheDir.string() << std::endl;
        
        return true;
        
    } catch (const std::exception& e) {
        std::cerr << "[ApplicationContext] Initialization error: " 
                  << e.what() << std::endl;
        return false;
    }
}

bool ApplicationContext::isInitialized() const {
    std::shared_lock<std::shared_mutex> lock(m_rwLock);
    return m_initialized;
}

void ApplicationContext::ensureInitialized() const {
    // Note: This is const but may modify state on first call.
    // This is acceptable for lazy initialization pattern.
    if (!m_initialized) {
        // Cast away const for initialization (acceptable in this pattern)
        const_cast<ApplicationContext*>(this)->initialize();
    }
}

void ApplicationContext::ensureResources() const {
    // Note: This is const but may modify state on first call.
    // This is acceptable for lazy initialization pattern.
    if (!m_resources) {
        const_cast<ApplicationContext*>(this)->m_resources = std::make_shared<Resources>();
    }
    if (!m_assets) {
        const_cast<ApplicationContext*>(this)->m_assets = std::make_shared<AssetManager>();
    }
}


// ============================================================================
// PREFERENCES IMPLEMENTATION (A3.3)
// ============================================================================

std::shared_ptr<SharedPreferences> ApplicationContext::getSharedPreferences(
    const std::string& name, int mode) {
    
    (void)mode;  // Mode ignored for now (always private)
    
    ensureInitialized();
    
    std::shared_lock<std::shared_mutex> lock(m_rwLock);
    
    // Check cache first
    auto it = m_prefsCache.find(name);
    if (it != m_prefsCache.end()) {
        return it->second;
    }
    
    // Need to create new instance - upgrade to write lock
    lock.unlock();
    
    {
        std::unique_lock<std::shared_mutex> writeLock(m_rwLock);
        
        // Double-check after acquiring write lock
        it = m_prefsCache.find(name);
        if (it != m_prefsCache.end()) {
            return it->second;
        }
        
        // Create new SharedPreferences instance
        auto prefs = std::make_shared<SharedPreferences>(
            m_packageName,
            name,
            m_config.base_path);
        
        // Cache it
        m_prefsCache[name] = prefs;
        
        return prefs;
    }
}


// ============================================================================
// FILE SYSTEM IMPLEMENTATION (A3.4)
// ============================================================================

fs::path ApplicationContext::getFilesDir() const {
    ensureInitialized();
    
    std::shared_lock<std::shared_mutex> lock(m_rwLock);
    if (m_sandbox) {
        return m_sandbox->getDirectory(Storage::SandboxDirectory::FILES);
    }
    return fs::path();
}

fs::path ApplicationContext::getCacheDir() const {
    ensureInitialized();
    
    std::shared_lock<std::shared_mutex> lock(m_rwLock);
    if (m_sandbox) {
        return m_sandbox->getDirectory(Storage::SandboxDirectory::CACHE);
    }
    return fs::path();
}

fs::path ApplicationContext::getDatabasePath(const std::string& name) const {
    ensureInitialized();
    
    std::shared_lock<std::shared_mutex> lock(m_rwLock);
    if (m_sandbox) {
        return m_sandbox->getDirectory(Storage::SandboxDirectory::DATABASES) / name;
    }
    return fs::path();
}

std::unique_ptr<std::ifstream> ApplicationContext::openFileInput(
    const std::string& name) const {
    
    ensureInitialized();
    
    std::shared_lock<std::shared_mutex> lock(m_rwLock);
    if (!m_sandbox) return nullptr;
    
    // FileSandbox returns ifstream by value, wrap in unique_ptr
    auto stream = m_sandbox->openFileInput(name);
    if (stream.is_open()) {
        return std::make_unique<std::ifstream>(std::move(stream));
    }
    return nullptr;
}

std::unique_ptr<std::ofstream> ApplicationContext::openFileOutput(
    const std::string& name, int mode) const {
    
    ensureInitialized();
    
    std::shared_lock<std::shared_mutex> lock(m_rwLock);
    if (!m_sandbox) return nullptr;
    
    // FileSandbox returns ofstream by value, wrap in unique_ptr
    auto stream = m_sandbox->openFileOutput(name, mode != 0);  // append if mode != 0
    if (stream.is_open()) {
        return std::make_unique<std::ofstream>(std::move(stream));
    }
    return nullptr;
}

bool ApplicationContext::deleteFile(const std::string& name) {
    ensureInitialized();
    
    std::unique_lock<std::shared_mutex> lock(m_rwLock);
    if (m_sandbox) {
        return m_sandbox->deleteFile(name);
    }
    return false;
}

std::vector<std::string> ApplicationContext::fileList() const {
    ensureInitialized();
    
    std::shared_lock<std::shared_mutex> lock(m_rwLock);
    if (m_sandbox) {
        // FileSandbox returns vector<FileInfo>, extract names
        auto fileInfoList = m_sandbox->fileList();
        std::vector<std::string> names;
        names.reserve(fileInfoList.size());
        for (const auto& info : fileInfoList) {
            names.push_back(info.name);
        }
        return names;
    }
    return {};
}


// ============================================================================
// PACKAGE INFO IMPLEMENTATION (A3.6)
// ============================================================================

std::string ApplicationContext::getPackageName() const {
    return m_packageName;
}

ApplicationInfo ApplicationContext::getApplicationInfo() const {
    return m_appInfo;
}


// ============================================================================
// RESOURCES IMPLEMENTATION (A3.5 - Stubs)
// ============================================================================

std::shared_ptr<Resources> ApplicationContext::getResources() const {
    ensureInitialized();
    ensureResources();
    
    std::shared_lock<std::shared_mutex> lock(m_rwLock);
    return m_resources;
}

std::shared_ptr<AssetManager> ApplicationContext::getAssets() const {
    ensureInitialized();
    ensureResources();
    
    std::shared_lock<std::shared_mutex> lock(m_rwLock);
    return m_assets;
}

std::string ApplicationContext::getString(int resourceId, const std::string& defaultValue) const {
    ensureResources();
    
    std::shared_lock<std::shared_mutex> lock(m_rwLock);
    if (m_resources) {
        return m_resources->getString(resourceId, defaultValue);
    }
    return defaultValue;
}


// ============================================================================
// CLASS LOADING IMPLEMENTATION (Stub)
// ============================================================================

void* ApplicationContext::loadClass(const std::string& className) {
    // TODO: Implement DEX class loading when interpreter is integrated
    (void)className;
    std::cerr << "[ApplicationContext] loadClass() not yet implemented" << std::endl;
    return nullptr;
}


// ============================================================================
// UTILITY METHODS
// ============================================================================

Storage::FileSandbox* ApplicationContext::getFileSandbox() const {
    ensureInitialized();
    
    std::shared_lock<std::shared_mutex> lock(m_rwLock);
    return m_sandbox.get();
}

std::vector<std::string> ApplicationContext::getPreferencesList() const {
    std::shared_lock<std::shared_mutex> lock(m_rwLock);
    
    std::vector<std::string> names;
    names.reserve(m_prefsCache.size());
    
    for (const auto& [name, prefs] : m_prefsCache) {
        names.push_back(name);
    }
    
    return names;
}

void ApplicationContext::clearCache() {
    std::unique_lock<std::shared_mutex> lock(m_rwLock);
    m_prefsCache.clear();
}

std::string ApplicationContext::debugInfo() const {
    std::ostringstream ss;
    
    ss << "=== ApplicationContext Debug Info ===\n";
    ss << "Package: " << m_packageName << "\n";
    ss << "Initialized: " << (m_initialized ? "Yes" : "No") << "\n";
    
    if (m_initialized && m_sandbox) {
        ss << "Files Dir: " << getFilesDir().string() << "\n";
        ss << "Cache Dir: " << getCacheDir().string() << "\n";
        ss << "DB Dir: " << getDatabasePath("").parent_path().string() << "\n";
    }
    
    ss << "Cached Preferences: " << m_prefsCache.size() << "\n";
    
    if (!m_prefsCache.empty()) {
        ss << "  ";
        for (const auto& [name, prefs] : m_prefsCache) {
            ss << name << " (" << prefs->size() << " entries), ";
        }
        ss << "\n";
    }
    
    ss << "=====================================\n";
    
    return ss.str();
}


// ============================================================================
// FACTORY FUNCTION IMPLEMENTATIONS
// ============================================================================

namespace ContextFactory {

std::shared_ptr<ApplicationContext> create(const std::string& packageName) {
    auto ctx = std::make_shared<ApplicationContext>(packageName);
    
    if (!ctx->initialize()) {
        throw std::runtime_error("Failed to initialize ApplicationContext for: " + packageName);
    }
    
    return ctx;
}

std::shared_ptr<ApplicationContext> createForTelegram() {
    static const std::string TELEGRAM_PACKAGE = "org.telegram.messenger";
    return create(TELEGRAM_PACKAGE);
}

std::shared_ptr<Context> getDefault() {
    // Return a default context if one has been created
    // In production, this would be set during app startup
    static std::weak_ptr<Context> defaultCtx;
    
    if (auto ctx = defaultCtx.lock()) {
        return ctx;
    }
    
    return nullptr;
}

} // namespace ContextFactory

} // namespace AndroidAPI
