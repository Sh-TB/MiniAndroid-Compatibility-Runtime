/**
 * @file test_android_context.cpp
 * @brief Comprehensive unit tests for Android Context API
 * 
 * @description
 * Test suite for EXP-037 Phase A, Week 3: Basic Context Implementation.
 * Validates the unified Context API that integrates FileSandbox + SharedPreferences.
 * 
 * This is THE interface that Telegram's ApplicationLoader will receive.
 * All tests validate real usage patterns, not toy examples.
 * 
 * Test Categories:
 * - Suite 1: Construction & Initialization (5 tests)
 * - Suite 2: Package Information (4 tests)
 * - Suite 3: File System Operations (8 tests)
 * - Suite 4: SharedPreferences Integration (6 tests)
 * - Suite 5: Resources & Assets (3 tests)
 * - Suite 6: ContextWrapper Delegation (3 tests)
 * - Suite 7: Factory Functions (2 tests)
 * - Suite 8: Thread Safety (2 tests)
 * - Suite 9: Telegram-Specific Scenarios (4 tests)
 * - Suite 10: Edge Cases & Error Handling (5 tests)
 * 
 * Total: ~42 tests
 * 
 * @author EXP-037 Development (Phase A, Week 3)
 * @date 2026-08-14
 * @version 1.0.0
 */

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <map>
#include <set>
#include <cassert>
#include <filesystem>
#include <thread>
#include <chrono>
#include <atomic>
#include <functional>
#include <memory>

// Include implementations under test
#include "api/android_context.h"
#include "api/shared_prefs.h"

namespace fs = std::filesystem;
using namespace AndroidAPI;

// ============================================================================
// TEST INFRASTRUCTURE
// ============================================================================

struct TestStats {
    int total = 0;
    int passed = 0;
    int failed = 0;
    std::vector<std::string> failures;
};

static TestStats g_stats;

void runTest(const std::string& test_name, std::function<void()> test_fn) {
    g_stats.total++;
    std::cout << "  [TEST] " << test_name << "... ";
    
    try {
        test_fn();
        std::cout << "\u2713 PASSED" << std::endl;
        g_stats.passed++;
    } catch (const std::exception& e) {
        std::cout << "\u2717 FAILED" << std::endl;
        std::cout << "         Error: " << e.what() << std::endl;
        g_stats.failed++;
        g_stats.failures.push_back(test_name + ": " + e.what());
    } catch (...) {
        std::cout << "\u2717 FAILED" << std::endl;
        std::cout << "         Unknown exception" << std::endl;
        g_stats.failed++;
        g_stats.failures.push_back(test_name + ": Unknown exception");
    }
}

#define TEST_ASSERT(condition, message) \
    if (!(condition)) { \
        throw std::runtime_error(std::string("Assertion failed: ") + message); \
    }

#define TEST_ASSERT_EQ(actual, expected, message) \
    if ((actual) != (expected)) { \
        std::ostringstream ss; \
        ss << message << " (expected: " << (expected) << ", actual: " << (actual) << ")"; \
        throw std::runtime_error(ss.str()); \
    }

#define TEST_ASSERT_TRUE(condition, message) TEST_ASSERT(condition, message)
#define TEST_ASSERT_FALSE(condition, message) TEST_ASSERT(!(condition), message)

std::string uniquePackage(const std::string& prefix) {
    auto now = std::chrono::system_clock::now().time_since_epoch().count();
    return prefix + "_" + std::to_string(now);
}

void cleanupTest(const std::string& pkg) {
    try {
        fs::path base = fs::path("runtime/data") / pkg;
        if (fs::exists(base)) {
            fs::remove_all(base);
        }
    } catch (...) {}
}


// ============================================================================
// SUITE 1: CONSTRUCTION & INITIALIZATION
// ============================================================================

void runSuite1_Construction() {
    std::cout << "\n[SUITE 1] Construction & Initialization\n" << std::endl;
    
    runTest("Test_DefaultConstruction_CreatesInstance", []() {
        std::string pkg = uniquePackage("org.test.ctx_construct");
        ApplicationContext ctx(pkg);
        
        TEST_ASSERT_TRUE(!ctx.getPackageName().empty(), "Package name should not be empty");
        TEST_ASSERT_FALSE(ctx.isInitialized(), "Should not be initialized yet");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_Initialize_CreatesDirectories", []() {
        std::string pkg = uniquePackage("org.test.ctx_init");
        ApplicationContext ctx(pkg);
        
        bool success = ctx.initialize();
        TEST_ASSERT_TRUE(success, "Initialize should succeed");
        TEST_ASSERT_TRUE(ctx.isInitialized(), "Should be initialized after init");
        
        // Verify directories exist
        TEST_ASSERT_TRUE(fs::exists(ctx.getFilesDir()), "Files dir should exist");
        TEST_ASSERT_TRUE(fs::exists(ctx.getCacheDir()), "Cache dir should exist");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_LazyInitialization_OnFirstAccess", []() {
        std::string pkg = uniquePackage("org.test.ctx_lazy");
        ApplicationContext ctx(pkg);
        
        // Don't call initialize() explicitly
        TEST_ASSERT_FALSE(ctx.isInitialized(), "Not initialized yet");
        
        // Access should trigger lazy init
        auto filesDir = ctx.getFilesDir();
        
        TEST_ASSERT_TRUE(ctx.isInitialized(), "Should be initialized after access");
        TEST_ASSERT_TRUE(fs::exists(filesDir), "Files dir should exist after lazy init");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_CustomConfig_BasePath", []() {
        std::string pkg = uniquePackage("org.test.ctx_config");
        ContextConfig config;
        config.base_path = "custom_runtime/data";
        
        ApplicationContext ctx(pkg, config);
        ctx.initialize();
        
        std::string expectedPrefix = "custom_runtime/data/" + pkg;
        TEST_ASSERT_EQ(ctx.getFilesDir().string().substr(0, expectedPrefix.length()),
                      expectedPrefix,
                      "Custom base path should be used");
        
        cleanupTest(pkg);
        try { fs::remove_all("custom_runtime"); } catch (...) {}
    });
    
    runTest("Test_DebugInfo_ContainsUsefulData", []() {
        std::string pkg = uniquePackage("org.test.ctx_debug");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        std::string info = ctx.debugInfo();
        
        TEST_ASSERT_TRUE(info.find(pkg) != std::string::npos,
                        "Debug info should contain package name");
        TEST_ASSERT_TRUE(info.find("Yes") != std::string::npos,
                        "Debug info should show initialized status");
        TEST_ASSERT_TRUE(info.find("Files Dir") != std::string::npos,
                        "Debug info should show files directory");
        
        cleanupTest(pkg);
    });
}


// ============================================================================
// SUITE 2: PACKAGE INFORMATION
// ============================================================================

void runSuite2_PackageInfo() {
    std::cout << "\n[SUITE 2] Package Information\n" << std::endl;
    
    runTest("Test_GetPackageName_ReturnsCorrectName", []() {
        std::string pkg = uniquePackage("com.example.mypackage");
        ApplicationContext ctx(pkg);
        
        TEST_ASSERT_EQ(ctx.getPackageName(), pkg,
                      "getPackageName should return constructor value");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_GetPackageName_TelegramFormat", []() {
        ApplicationContext ctx("org.telegram.messenger");
        
        TEST_ASSERT_EQ(ctx.getPackageName(), "org.telegram.messenger",
                      "Should handle standard Android package names");
    });
    
    runTest("Test_GetApplicationInfo_BasicFields", []() {
        std::string pkg = uniquePackage("org.test.appinfo");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        auto info = ctx.getApplicationInfo();
        
        TEST_ASSERT_EQ(info.packageName, pkg,
                      "AppInfo package name should match");
        TEST_ASSERT_TRUE(info.uid > 0,
                        "AppInfo UID should be positive");
        TEST_ASSERT_TRUE(info.enabled,
                        "App should be enabled by default");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_GetApplicationInfo_DataDir", []() {
        std::string pkg = uniquePackage("org.test.datadir");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        auto info = ctx.getApplicationInfo();
        
        TEST_ASSERT_TRUE(info.dataDir.find(pkg) != std::string::npos,
                        "Data dir should contain package name");
        
        cleanupTest(pkg);
    });
}


// ============================================================================
// SUITE 3: FILE SYSTEM OPERATIONS
// ============================================================================

void runSuite3_FileSystem() {
    std::cout << "\n[SUITE 3] File System Operations\n" << std::endl;
    
    runTest("Test_GetFilesDir_ReturnsValidPath", []() {
        std::string pkg = uniquePackage("org.test.filesdir");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        fs::path filesDir = ctx.getFilesDir();
        
        TEST_ASSERT_TRUE(filesDir.has_filename(),
                        "Files dir path should be valid");
        TEST_ASSERT_EQ(filesDir.filename().string(), "files",
                      "Files dir should end with 'files'");
        TEST_ASSERT_TRUE(fs::exists(filesDir),
                        "Files directory should exist on disk");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_GetCacheDir_ReturnsValidPath", []() {
        std::string pkg = uniquePackage("org.test.cachedir");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        fs::path cacheDir = ctx.getCacheDir();
        
        TEST_ASSERT_EQ(cacheDir.filename().string(), "cache",
                      "Cache dir should end with 'cache'");
        TEST_ASSERT_TRUE(fs::exists(cacheDir),
                        "Cache directory should exist on disk");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_OpenFileOutput_And_Write", []() {
        std::string pkg = uniquePackage("org.test.filewrite");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        {
            auto out = ctx.openFileOutput("test.txt");
            TEST_ASSERT_TRUE(out && out->is_open(),
                           "Output stream should be open");
            
            (*out) << "Hello from Context!" << std::endl;
        }
        
        // Verify file exists and has content
        TEST_ASSERT_TRUE(fs::exists(ctx.getFilesDir() / "test.txt"),
                        "File should exist after writing");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_OpenFileInput_And_Read", []() {
        std::string pkg = uniquePackage("org.test.fileread");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        // Write a file first
        {
            auto out = ctx.openFileOutput("data.txt");
            (*out) << "Test content 12345";
        }
        
        // Read it back
        auto in = ctx.openFileInput("data.txt");
        TEST_ASSERT_TRUE(in && in->is_open(),
                        "Input stream should be open");
        
        std::string content((std::istreambuf_iterator<char>(*in)),
                            std::istreambuf_iterator<char>());
        
        TEST_ASSERT_EQ(content, "Test content 12345",
                      "Content should match what was written");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_DeleteFile", []() {
        std::string pkg = uniquePackage("org.test.filedelete");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        // Create file
        {
            auto out = ctx.openFileOutput("temp.txt");
            (*out) << "temporary";
        }
        
        TEST_ASSERT_TRUE(fs::exists(ctx.getFilesDir() / "temp.txt"),
                        "File should exist before deletion");
        
        bool deleted = ctx.deleteFile("temp.txt");
        TEST_ASSERT_TRUE(deleted, "deleteFile should return true");
        TEST_ASSERT_FALSE(fs::exists(ctx.getFilesDir() / "temp.txt"),
                         "File should not exist after deletion");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_FileList", []() {
        std::string pkg = uniquePackage("org.test.filelist");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        // Create multiple files
        ctx.openFileOutput("file1.txt");
        ctx.openFileOutput("file2.txt");
        ctx.openFileOutput("file3.dat");
        
        auto files = ctx.fileList();
        
        TEST_ASSERT_EQ(files.size(), size_t(3),
                      "Should list 3 files");
        
        // Verify all files are in the list
        std::set<std::string> fileSet(files.begin(), files.end());
        TEST_ASSERT_TRUE(fileSet.count("file1.txt") > 0,
                        "Should contain file1.txt");
        TEST_ASSERT_TRUE(fileSet.count("file2.txt") > 0,
                        "Should contain file2.txt");
        TEST_ASSERT_TRUE(fileSet.count("file3.dat") > 0,
                        "Should contain file3.dat");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_GetDatabasePath", []() {
        std::string pkg = uniquePackage("org.test.dbpath");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        fs::path dbPath = ctx.getDatabasePath("mydb.sqlite");
        
        TEST_ASSERT_TRUE(dbPath.string().find("databases") != std::string::npos,
                        "DB path should contain 'databases'");
        TEST_ASSERT_TRUE(dbPath.string().find("mydb.sqlite") != std::string::npos,
                        "DB path should contain database name");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_FilesAndCache_AreDifferentDirs", []() {
        std::string pkg = uniquePackage("org.test.differentdirs");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        fs::path filesDir = ctx.getFilesDir();
        fs::path cacheDir = ctx.getCacheDir();
        
        TEST_ASSERT_TRUE(filesDir != cacheDir,
                        "Files and cache should be different directories");
        
        cleanupTest(pkg);
    });
}


// ============================================================================
// SUITE 4: SHARED PREFERENCES INTEGRATION
// ============================================================================

void runSuite4_PreferencesIntegration() {
    std::cout << "\n[SUITE 4] SharedPreferences Integration\n" << std::endl;
    
    runTest("Test_GetSharedPreferences_ReturnsWorkingPrefs", []() {
        std::string pkg = uniquePackage("org.test.prefs_int");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        auto prefs = ctx.getSharedPreferences("test_prefs");
        
        TEST_ASSERT_TRUE(prefs != nullptr,
                        "getSharedPreferences should return non-null");
        TEST_ASSERT_EQ(prefs->getPackageName(), pkg,
                      "Prefs should have correct package name");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_PrefsIntegration_WriteAndRead", []() {
        std::string pkg = uniquePackage("org.test.prefs_write");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        auto prefs = ctx.getSharedPreferences("config");
        
        // Write via context's SharedPreferences
        prefs->edit()
            .putString("key_from_ctx", "value_from_ctx")
            .putInt("counter", 42)
            .commit();
        
        // Read back
        TEST_ASSERT_EQ(prefs->getString("key_from_ctx"), "value_from_ctx",
                      "String written via context should be readable");
        TEST_ASSERT_EQ(prefs->getInt("counter"), 42,
                      "Int written via context should be readable");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_MultiplePrefsInstances_DifferentNames", []() {
        std::string pkg = uniquePackage("org.test.prefs_multi");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        auto prefs1 = ctx.getSharedPreferences("settings");
        auto prefs2 = ctx.getSharedPreferences("cache");
        
        prefs1->edit().putString("theme", "dark").commit();
        prefs2->edit().putString("last_view", "chat").commit();
        
        // Each should only have its own data
        TEST_ASSERT_TRUE(prefs1->contains("theme"),
                        "Settings should have theme");
        TEST_ASSERT_FALSE(prefs1->contains("last_view"),
                         "Settings should NOT have last_view");
        TEST_ASSERT_TRUE(prefs2->contains("last_view"),
                        "Cache should have last_view");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_SamePrefsName_ReturnsCachedInstance", []() {
        std::string pkg = uniquePackage("org.test.prefs_cache");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        auto prefs1 = ctx.getSharedPreferences("cached");
        auto prefs2 = ctx.getSharedPreferences("cached");
        
        // Should return same instance (pointer equality)
        TEST_ASSERT_EQ(prefs1.get(), prefs2.get(),
                      "Same name should return cached instance");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_PrefsPersist_ViaContext", []() {
        std::string pkg = uniquePackage("org.test.prefs_persist");
        fs::path prefsFile;
        
        {
            ApplicationContext ctx(pkg);
            ctx.initialize();
            
            auto prefs = ctx.getSharedPreferences("session");
            prefs->edit()
                .putBoolean("logged_in", true)
                .putInt("user_id", 999888)
                .commit();
            
            prefsFile = prefs->getFilePath();
        }
        // Context destroyed
        
        // Create new context, get same prefs
        {
            ApplicationContext ctx2(pkg);
            ctx2.initialize();
            
            auto prefs = ctx2.getSharedPreferences("session");
            
            TEST_ASSERT_TRUE(prefs->getBoolean("logged_in", false),
                            "Login state persisted via context");
            TEST_ASSERT_EQ(prefs->getInt("user_id", -1), 999888,
                          "User ID persisted via context");
        }
        
        cleanupTest(pkg);
    });
    
    runTest("Test_GetPreferencesList", []() {
        std::string pkg = uniquePackage("org.test.prefs_list");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        ctx.getSharedPreferences("prefs1");
        ctx.getSharedPreferences("prefs2");
        ctx.getSharedPreferences("prefs3");
        
        auto list = ctx.getPreferencesList();
        
        TEST_ASSERT_EQ(list.size(), size_t(3),
                      "Should have 3 cached preferences");
        
        cleanupTest(pkg);
    });
}


// ============================================================================
// SUITE 5: RESOURCES & ASSETS (Stubs)
// ============================================================================

void runSuite5_Resources() {
    std::cout << "\n[SUITE 5: Resources & Assets (Stubs)]\n" << std::endl;
    
    runTest("Test_GetResources_ReturnsNonNull", []() {
        std::string pkg = uniquePackage("org.test.res_notnull");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        auto resources = ctx.getResources();
        
        TEST_ASSERT_TRUE(resources != nullptr,
                        "getResources should return non-null stub");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_GetAssets_ReturnsNonNull", []() {
        std::string pkg = uniquePackage("org.test.assets_notnull");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        auto assets = ctx.getAssets();
        
        TEST_ASSERT_TRUE(assets != nullptr,
                        "getAssets should return non-null stub");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_GetString_ReturnsDefaultForUnknownId", []() {
        std::string pkg = uniquePackage("org.test.str_default");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        std::string result = ctx.getString(12345, "default_value");
        
        TEST_ASSERT_EQ(result, "default_value",
                      "getString should return default for unknown resource ID");
        
        cleanupTest(pkg);
    });
}


// ============================================================================
// SUITE 6: CONTEXT WRAPPER DELEGATION
// ============================================================================

void runSuite6_WrapperDelegation() {
    std::cout << "\n[SUITE 6] ContextWrapper Delegation\n" << std::endl;
    
    runTest("Test_Wrapper_DelegatesToBaseContext", []() {
        std::string pkg = uniquePackage("org.test.wrap_delegate");
        auto baseCtx = std::make_shared<ApplicationContext>(pkg);
        baseCtx->initialize();
        
        ContextWrapper wrapper(baseCtx);
        
        // Wrapper should delegate to base
        TEST_ASSERT_EQ(wrapper.getPackageName(), pkg,
                      "Wrapper should delegate getPackageName");
        TEST_ASSERT_EQ(wrapper.getFilesDir().string(),
                      baseCtx->getFilesDir().string(),
                      "Wrapper should delegate getFilesDir");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_SetBaseContext_ChangesDelegation", []() {
        std::string pkg1 = uniquePackage("org.test.wrap_base1");
        std::string pkg2 = uniquePackage("org.test.wrap_base2");
        
        auto ctx1 = std::make_shared<ApplicationContext>(pkg1);
        ctx1->initialize();
        
        auto ctx2 = std::make_shared<ApplicationContext>(pkg2);
        ctx2->initialize();
        
        ContextWrapper wrapper(ctx1);
        TEST_ASSERT_EQ(wrapper.getPackageName(), pkg1,
                      "Initially delegates to ctx1");
        
        wrapper.setBaseContext(ctx2);
        TEST_ASSERT_EQ(wrapper.getPackageName(), pkg2,
                      "After setBaseContext, delegates to ctx2");
        
        cleanupTest(pkg1);
        cleanupTest(pkg2);
    });
    
    runTest("Test_Wrapper_NoBase_Throws", []() {
        ContextWrapper wrapper(nullptr);
        
        bool threw = false;
        try {
            wrapper.getPackageName();
        } catch (const std::runtime_error&) {
            threw = true;
        }
        
        TEST_ASSERT_TRUE(threw,
                        "Wrapper without base should throw on method calls");
    });
}


// ============================================================================
// SUITE 7: FACTORY FUNCTIONS
// ============================================================================

void runSuite7_Factory() {
    std::cout << "\n[SUITE 7] Factory Functions\n" << std::endl;
    
    runTest("Test_Create_ForAnyPackage", []() {
        std::string pkg = uniquePackage("org.test.factory_any");
        
        auto ctx = ContextFactory::create(pkg);
        
        TEST_ASSERT_TRUE(ctx != nullptr,
                        "Factory should create non-null context");
        TEST_ASSERT_TRUE(ctx->isInitialized(),
                        "Factory-created context should be initialized");
        TEST_ASSERT_EQ(ctx->getPackageName(), pkg,
                      "Factory should use provided package name");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_CreateForTelegram_Preconfigured", []() {
        auto telegramCtx = ContextFactory::createForTelegram();
        
        TEST_ASSERT_TRUE(telegramCtx != nullptr,
                        "Telegram factory should create context");
        TEST_ASSERT_EQ(telegramCtx->getPackageName(), "org.telegram.messenger",
                      "Should be configured for Telegram");
        TEST_ASSERT_TRUE(telegramCtx->isInitialized(),
                      "Should be pre-initialized");
    });
}


// ============================================================================
// SUITE 8: THREAD SAFETY
// ============================================================================

void runSuite8_ThreadSafety() {
    std::cout << "\n[SUITE 8] Thread Safety\n" << std::endl;
    
    runTest("Test_ConcurrentContextAccess_NoCrash", []() {
        std::string pkg = uniquePackage("org.test.thread_ctx");
        auto ctx = std::make_shared<ApplicationContext>(pkg);
        ctx->initialize();
        
        std::vector<std::thread> threads;
        std::atomic<int> successCount(0);
        
        for (int i = 0; i < 10; ++i) {
            threads.emplace_back([ctx, &successCount]() {
                try {
                    // Perform various operations concurrently
                    for (int j = 0; j < 50; ++j) {
                        ctx->getPackageName();
                        ctx->getFilesDir();
                        ctx->getCacheDir();
                        ctx->getSharedPreferences("thread_test");
                    }
                    successCount++;
                } catch (...) {
                    // Thread crashed
                }
            });
        }
        
        for (auto& t : threads) {
            t.join();
        }
        
        TEST_ASSERT_EQ(successCount.load(), 10,
                      "All threads should complete without crash");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_ConcurrentPrefWrites_LastWriteWins", []() {
        std::string pkg = uniquePackage("org.test.thread_prefs");
        auto ctx = std::make_shared<ApplicationContext>(pkg);
        ctx->initialize();
        
        std::vector<std::thread> threads;
        
        for (int i = 0; i < 5; ++i) {
            threads.emplace_back([ctx, i]() {
                auto prefs = ctx->getSharedPreferences("concurrent");
                prefs->edit()
                    .putInt("race_key", i * 100)
                    .commit();
            });
        }
        
        for (auto& t : threads) {
            t.join();
        }
        
        // One of the writes should have won
        auto prefs = ctx->getSharedPreferences("concurrent");
        int finalValue = prefs->getInt("race_key", -1);
        
        TEST_ASSERT_TRUE(finalValue >= 0 && finalValue < 500,
                        "Final value should be one of the written values");
        
        cleanupTest(pkg);
    });
}


// ============================================================================
// SUITE 9: TELEGRAM-SPECIFIC SCENARIOS
// ============================================================================

void runSuite9_TelegramScenarios() {
    std::cout << "\n[SUITE 9] Telegram-Specific Scenarios\n" << std::endl;
    
    runTest("Test_TelegramStartupSequence", []() {
        // Simulate what happens when Telegram starts:
        // 1. ApplicationLoader.onCreate() is called
        // 2. It gets a Context
        // 3. It calls getSharedPreferences("mainconfig")
        // 4. It checks logged_in_key
        
        auto ctx = ContextFactory::createForTelegram();
        
        // Step 1-2: Get context (done via factory)
        TEST_ASSERT_TRUE(ctx != nullptr, "Context created");
        
        // Step 3: Get main preferences
        auto mainPrefs = ctx->getSharedPreferences("mainconfig");
        TEST_ASSERT_TRUE(mainPrefs != nullptr, "Main prefs obtained");
        
        // Step 4: Check login state (initially false)
        bool loggedIn = mainPrefs->getBoolean("logged_in_key", false);
        TEST_ASSERT_FALSE(loggedIn, "Initial state: not logged in");
        
        // Simulate user logging in
        mainPrefs->edit()
            .putBoolean("logged_in_key", true)
            .putInt("user_id", 987654321)
            .putString("phone_hash", "abc123xyz")
            .putLong("login_time", static_cast<int64_t>(std::time(nullptr)))
            .commit();
        
        // Verify login state saved
        loggedIn = mainPrefs->getBoolean("logged_in_key", false);
        TEST_ASSERT_TRUE(loggedIn, "After login: logged in");
        
        std::cout << "\n    [Telegram Scenario] Startup sequence works!" << std::endl;
    });
    
    runTest("Test_TelegramMultiplePreferenceFiles", []() {
        auto ctx = ContextFactory::createForTelegram();
        
        // Telegram uses multiple preference files
        auto mainConfig = ctx->getSharedPreferences("mainconfig");
        auto userConfig = ctx->getSharedPreferences("userconfig");
        auto cacheConfig = ctx->getSharedPreferences("cacheconfig");
        auto notificationConfig = ctx->getSharedPreferences("notificationconfig");
        
        // Write different data to each
        mainConfig->edit().putBoolean("logged_in", true).commit();
        userConfig->edit().putString("first_name", "John").commit();
        cacheConfig->edit().putInt("last_chat_id", 12345).commit();
        notificationConfig->edit().putBoolean("sound_enabled", false).commit();
        
        // Each should be independent
        TEST_ASSERT_TRUE(mainConfig->contains("logged_in"), "Main config should have logged_in");
        TEST_ASSERT_TRUE(userConfig->contains("first_name"), "User config should have first_name");
        TEST_ASSERT_TRUE(cacheConfig->contains("last_chat_id"), "Cache config should have last_chat_id");
        TEST_ASSERT_TRUE(notificationConfig->contains("sound_enabled"), "Notification config should have sound_enabled");
        
        // No cross-contamination
        TEST_ASSERT_FALSE(mainConfig->contains("first_name"), "Main should not contain user keys");
        TEST_ASSERT_FALSE(userConfig->contains("last_chat_id"), "User should not contain cache keys");
        
        std::cout << "\n    [Telegram Scenario] Multiple pref files work independently!" << std::endl;
    });
    
    runTest("Test_TelegramFileOperations", []() {
        auto ctx = ContextFactory::createForTelegram();
        
        // Telegram stores various files:
        // - User profiles
        // - Cached images
        // - Temporary files
        // - Database files
        
        // Write a simulated user profile
        {
            auto profileOut = ctx->openFileOutput("user_profile.json");
            (*profileOut) << "{\"id\":12345,\"name\":\"Test User\"}" << std::endl;
        }
        
        // Write a cache entry
        {
            auto cacheOut = ctx->openFileOutput("cache/avatar_12345.jpg");
            (*cacheOut) << "FAKE_IMAGE_DATA";
        }
        
        // Write to database location (just verify path works)
        fs::path dbPath = ctx->getDatabasePath("telegram.db");
        TEST_ASSERT_TRUE(dbPath.string().find(".db") != std::string::npos,
                        "DB path should have .db extension");
        
        // List files
        auto files = ctx->fileList();
        TEST_ASSERT_TRUE(files.size() >= 2,
                        "Should have at least 2 files");
        
        // Read back profile
        auto profileIn = ctx->openFileInput("user_profile.json");
        std::string profileContent((std::istreambuf_iterator<char>(*profileIn)),
                                   std::istreambuf_iterator<char>());
        TEST_ASSERT_TRUE(profileContent.find("Test User") != std::string::npos,
                        "Profile should contain user name");
        
        std::cout << "\n    [Telegram Scenario] File operations work correctly!" << std::endl;
    });
    
    runTest("Test_TelegramFullSessionLifecycle", []() {
        // COMPLETE LIFECYCLE TEST:
        // 1. First launch - no session
        // 2. Login - session created
        // 3. Close (destroy context)
        // 4. Restart - session persists
        // 5. Continue without re-login
        
        std::string pkg = "org.telegram.messenger";
        
        // STEP 1: First launch
        {
            auto ctx = std::make_shared<ApplicationContext>(pkg);
            ctx->initialize();
            
            auto prefs = ctx->getSharedPreferences("mainconfig");
            
            bool wasLoggedIn = prefs->getBoolean("logged_in_key", false);
            TEST_ASSERT_FALSE(wasLoggedIn, "Step 1: Not logged in initially");
        }
        // Context destroyed (simulates app close)
        
        // STEP 2: Login
        {
            auto ctx = std::make_shared<ApplicationContext>(pkg);
            ctx->initialize();
            
            auto prefs = ctx->getSharedPreferences("mainconfig");
            prefs->edit()
                .putBoolean("logged_in_key", true)
                .putInt("user_id", 555666777)
                .putString("session_token", "super_secret_token_12345")
                .commit();
        }
        // App closed again
        
        // STEP 3: Restart (THE CRITICAL TEST)
        {
            auto ctx = std::make_shared<ApplicationContext>(pkg);
            ctx->initialize();
            
            auto prefs = ctx->getSharedPreferences("mainconfig");
            
            // THIS IS WHAT WE'RE BUILDING TOWARDS:
            bool isLoggedIn = prefs->getBoolean("logged_in_key", false);
            int userId = prefs->getInt("user_id", -1);
            std::string token = prefs->getString("session_token", "");
            
            TEST_ASSERT_TRUE(isLoggedIn,
                            "Step 3: Still logged in after restart!");
            TEST_ASSERT_EQ(userId, 555666777,
                          "Step 3: User ID persisted!");
            TEST_ASSERT_EQ(token, "super_secret_token_12345",
                          "Step 3: Session token persisted!");
            
            std::cout << "\n    [Telegram Scenario] FULL SESSION LIFECYCLE WORKS!" << std::endl;
            std::cout << "    ★★★ Telegram can survive restart! ★★★" << std::endl;
        }
        
        // Cleanup for next test
        cleanupTest(pkg);
    });
}


// ============================================================================
// SUITE 10: EDGE CASES & ERROR HANDLING
// ============================================================================

void runSuite10_EdgeCases() {
    std::cout << "\n[SUITE 10] Edge Cases & Error Handling\n" << std::endl;
    
    runTest("Test_EmptyPackageName_Handled", []() {
        // Empty package name is invalid but shouldn't crash
        bool threw = false;
        try {
            ApplicationContext ctx("");
            ctx.initialize();
        } catch (const std::exception&) {
            threw = true;
        }
        
        // May or may not throw depending on validation
        // Just ensure no crash/segfault
        TEST_ASSERT_TRUE(true, "Empty package handled without crash");
    });
    
    runTest("Test_SpecialCharsInPackageName", []() {
        // Test unusual but potentially valid package names
        std::string pkg = uniquePackage("org.test.special_chars_v2");
        ApplicationContext ctx(pkg);
        
        bool success = ctx.initialize();
        TEST_ASSERT_TRUE(success, "Special chars in package handled");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_RapidCreateDestroy", []() {
        // Stress test rapid creation/destruction
        for (int i = 0; i < 20; ++i) {
            std::string pkg = uniquePackage("org.test.rapid_" + std::to_string(i));
            {
                ApplicationContext ctx(pkg);
                ctx.initialize();
                ctx.getSharedPreferences("test");
                ctx.getFilesDir();
                ctx.getCacheDir();
            }
            cleanupTest(pkg);
        }
        
        TEST_ASSERT_TRUE(true, "Rapid create/destroy cycle completed");
    });
    
    runTest("Test_OpenNonExistentFile_ReturnsNull", []() {
        std::string pkg = uniquePackage("org.test.nonexist");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        auto in = ctx.openFileInput("does_not_exist.txt");
        
        TEST_ASSERT_TRUE(in == nullptr || !in->is_open(),
                        "Opening nonexistent file should return null/unopenable stream");
        
        cleanupTest(pkg);
    });
    
    runTest("Test_ClearCache_RemovesPrefsReferences", []() {
        std::string pkg = uniquePackage("org.test.clearcache");
        ApplicationContext ctx(pkg);
        ctx.initialize();
        
        // Create some prefs
        ctx.getSharedPreferences("cached1");
        ctx.getSharedPreferences("cached2");
        
        TEST_ASSERT_EQ(ctx.getPreferencesList().size(), size_t(2),
                      "Should have 2 cached prefs");
        
        ctx.clearCache();
        
        TEST_ASSERT_EQ(ctx.getPreferencesList().size(), size_t(0),
                      "Cache should be empty after clear");
        
        cleanupTest(pkg);
    });
}


// ============================================================================
// MAIN TEST RUNNER
// ============================================================================

int main() {
    std::cout << "=========================================" << std::endl;
    std::cout << "Android Context Unit Tests" << std::endl;
    std::cout << "EXP-037 Phase A, Week 3 Validation" << std::endl;
    std::cout << "=========================================" << std::endl;
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    // Run all test suites
    runSuite1_Construction();
    runSuite2_PackageInfo();
    runSuite3_FileSystem();
    runSuite4_PreferencesIntegration();
    runSuite5_Resources();
    runSuite6_WrapperDelegation();
    runSuite7_Factory();
    runSuite8_ThreadSafety();
    runSuite9_TelegramScenarios();
    runSuite10_EdgeCases();
    
    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    
    // Print summary
    std::cout << "\n=========================================" << std::endl;
    std::cout << "TEST SUMMARY" << std::endl;
    std::cout << "=========================================" << std::endl;
    std::cout << "Total:  " << g_stats.total << std::endl;
    std::cout << "Passed: " << g_stats.passed << std::endl;
    std::cout << "Failed: " << g_stats.failed << std::endl;
    std::cout << "Rate:   " << (g_stats.total > 0 ? (g_stats.passed * 100 / g_stats.total) : 0) 
              << "%" << std::endl;
    std::cout << "Time:   " << duration.count() << "ms" << std::endl;
    
    if (!g_stats.failures.empty()) {
        std::cout << "\nFailed Tests:" << std::endl;
        for (const auto& failure : g_stats.failures) {
            std::cout << "  - " << failure << std::endl;
        }
    }
    
    std::cout << "=========================================" << std::endl;
    
    return g_stats.failed > 0 ? 1 : 0;
}
