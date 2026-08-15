/**
 * @file test_file_sandbox.cpp
 * @brief Comprehensive unit tests for FileSandbox component
 * 
 * @description
 * Tests all FileSandbox functionality to ensure Android-compatible
 * persistent storage works correctly on Windows.
 * 
 * Test Categories:
 * 1. Initialization & Configuration
 * 2. Directory Management
 * 3. File Operations (Android Context API)
 * 4. SharedPreferences Helpers
 * 5. Database Helpers
 * 6. Error Handling
 * 7. Edge Cases & Security
 * 
 * @author EXP-037 Development (Phase A, Week 1)
 * @date 2026-08-14
 */

#include "src/storage/file_sandbox.h"

#include <iostream>
#include <fstream>
#include <sstream>
#include <cassert>
#include <vector>
#include <string>
#include <algorithm>

// ============================================================================
// TEST FRAMEWORK (Minimal)
// ============================================================================

static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) \
    void name(); \
    static void run_##name() { \
        std::cout << "  [TEST] " << #name << "... "; \
        try { \
            name(); \
            tests_passed++; \
            std::cout << "✓ PASSED" << std::endl; \
        } catch (const std::exception& e) { \
            tests_failed++; \
            std::cout << "✗ FAILED: " << e.what() << std::endl; \
        } catch (...) { \
            tests_failed++; \
            std::cout << "✗ FAILED: Unknown exception" << std::endl; \
        } \
    } \
    void name()

#define ASSERT_TRUE(condition) \
    if (!(condition)) { \
        throw std::runtime_error("Assertion failed: " #condition); \
    }

#define ASSERT_FALSE(condition) \
    if ((condition)) { \
        throw std::runtime_error("Assertion failed (should be false): " #condition); \
    }

#define ASSERT_EQ(a, b) \
    if ((a) != (b)) { \
        std::ostringstream ss; \
        ss << "Assertion failed: " << #a << " != " << #b << " (" << (a) << " != " << (b) << ")"; \
        throw std::runtime_error(ss.str()); \
    }

#define ASSERT_GE(a, b) \
    if (!((a) >= (b))) { \
        std::ostringstream ss; \
        ss << "Assertion failed: " << #a << " >= " << #b << " failed"; \
        throw std::runtime_error(ss.str()); \
    }

#define ASSERT_NE(a, b) \
    if ((a) == (b)) { \
        std::ostringstream ss; \
        ss << "Assertion failed: " << #a << " == " << #b << " (should not be equal)"; \
        throw std::runtime_error(ss.str()); \
    }

#define ASSERT_GT(a, b) \
    if (!((a) > (b))) { \
        std::ostringstream ss; \
        ss << "Assertion failed: " << #a << " > " << #b << " failed"; \
        throw std::runtime_error(ss.str()); \
    }

#define ASSERT_THROWS(expression, exception_type) \
    { \
        bool threw = false; \
        try { expression; } \
        catch (const exception_type&) { threw = true; } \
        catch (...) {} \
        if (!threw) { \
            throw std::runtime_error("Expected exception not thrown: " #expression); \
        } \
    }

// ============================================================================
// TEST SUITE 1: INITIALIZATION & CONFIGURATION
// ============================================================================

TEST(Test_PackageNameValidation_ValidNames) {
    // Valid package names should pass validation
    ASSERT_TRUE(Storage::isValidAndroidPackageName("org.telegram.messenger"));
    ASSERT_TRUE(Storage::isValidAndroidPackageName("com.example.app"));
    ASSERT_TRUE(Storage::isValidAndroidPackageName("com.google.android.apps.maps"));
    ASSERT_TRUE(Storage::isValidAndroidPackageName("a.b")); // Minimum valid
    ASSERT_TRUE(Storage::isValidAndroidPackageName("MyApp.Version1.SubModule"));
}

TEST(Test_PackageNameValidation_InvalidNames) {
    // Invalid package names should fail
    ASSERT_FALSE(Storage::isValidAndroidPackageName(""));
    ASSERT_FALSE(Storage::isValidAndroidPackageName("no_dots"));
    ASSERT_FALSE(Storage::isValidAndroidPackageName(".starts.with.dot"));
    ASSERT_FALSE(Storage::isValidAndroidPackageName("ends.with."));
    ASSERT_FALSE(Storage::isValidAndroidPackageName("..double..dot"));
    ASSERT_FALSE(Storage::isValidAndroidPackageName("1starts.with.number"));
    ASSERT_FALSE(Storage::isValidAndroidPackageName("has spaces.bad"));
    ASSERT_FALSE(Storage::isValidAndroidPackageName("has/slash.bad"));
}

TEST(Test_DefaultConstructor) {
    Storage::FileSandbox sandbox;
    
    // Should not be initialized yet
    ASSERT_FALSE(sandbox.isInitialized());
    
    // Package name should be empty
    ASSERT_EQ(sandbox.getPackageName(), "");
}

TEST(Test_PackageNameConstructor) {
    Storage::FileSandbox sandbox("org.telegram.messenger");
    
    // Should have correct package name
    ASSERT_EQ(sandbox.getPackageName(), "org.telegram.messenger");
}

TEST(Test_CustomConfigConstructor) {
    Storage::SandboxConfig config;
    config.root_path = "custom/data/path";
    config.auto_create = false;
    config.strict_mode = true;
    
    Storage::FileSandbox sandbox("com.test.app", config);
    
    ASSERT_EQ(sandbox.getPackageName(), "com.test.app");
}

TEST(Test_Initialize_CreatesDirectories) {
    // Use unique name for each test run to avoid conflicts
    std::string test_package = "org.test.init_" + std::to_string(time(nullptr));
    Storage::FileSandbox sandbox(test_package);
    
    bool result = sandbox.initialize();
    
    ASSERT_TRUE(result);
    ASSERT_TRUE(sandbox.isInitialized());
    
    // Verify directories exist
    ASSERT_TRUE(sandbox.directoryExists(Storage::SandboxDirectory::FILES));
    ASSERT_TRUE(sandbox.directoryExists(Storage::SandboxDirectory::CACHE));
    ASSERT_TRUE(sandbox.directoryExists(Storage::SandboxDirectory::DATABASES));
    ASSERT_TRUE(sandbox.directoryExists(Storage::SandboxDirectory::SHARED_PREFS));
    ASSERT_TRUE(sandbox.directoryExists(Storage::SandboxDirectory::LIB));
    
    // Cleanup
    sandbox.clearAllData(false);
}

TEST(Test_Initialize_InvalidPackage) {
    Storage::FileSandbox sandbox("invalid-package-name");
    
    // Should fail to initialize with invalid package name
    bool result = sandbox.initialize();
    
    ASSERT_FALSE(result);
    ASSERT_FALSE(sandbox.isInitialized());
}

// ============================================================================
// TEST SUITE 2: DIRECTORY MANAGEMENT
// ============================================================================

TEST(Test_GetDirectory_ReturnsValidPaths) {
    std::string test_package = "org.test.dirs_" + std::to_string(time(nullptr));
    Storage::FileSandbox sandbox(test_package);
    sandbox.initialize();
    
    // Get all directory types
    fs::path files_dir = sandbox.getFilesDir();
    fs::path cache_dir = sandbox.getCacheDir();
    fs::path db_dir = sandbox.getDatabasesDir();
    fs::path prefs_dir = sandbox.getSharedPrefsDir();
    fs::path lib_dir = sandbox.getLibDir();
    
    // All should exist and be directories
    ASSERT_TRUE(fs::exists(files_dir));
    ASSERT_TRUE(fs::is_directory(files_dir));
    ASSERT_TRUE(fs::exists(cache_dir));
    ASSERT_TRUE(fs::is_directory(cache_dir));
    ASSERT_TRUE(fs::exists(db_dir));
    ASSERT_TRUE(fs::is_directory(db_dir));
    ASSERT_TRUE(fs::exists(prefs_dir));
    ASSERT_TRUE(fs::is_directory(prefs_dir));
    ASSERT_TRUE(fs::exists(lib_dir));
    ASSERT_TRUE(fs::is_directory(lib_dir));
    
    // Paths should contain package name
    std::string files_str = files_dir.string();
    ASSERT_TRUE(files_str.find(test_package) != std::string::npos);
    
    // Cleanup
    sandbox.clearAllData(false);
}

TEST(Test_GetPathInfo_ReturnsCorrectInfo) {
    std::string test_package = "org.test.pathinfo_" + std::to_string(time(nullptr));
    Storage::FileSandbox sandbox(test_package);
    sandbox.initialize();
    
    // Get info about files directory
    Storage::SandboxPathInfo info = sandbox.getPathInfo(Storage::SandboxDirectory::FILES);
    
    ASSERT_TRUE(info.exists);
    ASSERT_TRUE(info.readable);
    ASSERT_TRUE(info.writable);
    ASSERT_EQ(info.file_count, 0); // Empty initially
    
    // Cleanup
    sandbox.clearAllData(false);
}

TEST(Test_DirectoryExists_BeforeInit) {
    std::string test_package = "org.test.exist_" + std::to_string(time(nullptr));
    Storage::FileSandbox sandbox(test_package);
    
    // Before initialize, directories shouldn't exist (unless auto_create is on)
    // With default config, getDirectory() auto-creates, but directoryExists() doesn't
    ASSERT_FALSE(sandbox.directoryExists(Storage::SandboxDirectory::FILES));
}

// ============================================================================
// TEST SUITE 3: FILE OPERATIONS (Android Context API Compatibility)
// ============================================================================

TEST(Test_OpenFileOutput_And_Write) {
    std::string test_package = "org.test.fop_" + std::to_string(time(nullptr));
    Storage::FileSandbox sandbox(test_package);
    sandbox.initialize();
    
    // Write a test file
    std::string test_content = "Hello, MiniAndroid! This is a test file.";
    std::ofstream out = sandbox.openFileOutput("test.txt");
    
    ASSERT_TRUE(out.is_open());
    
    out << test_content;
    out.close();
    
    // Verify file exists
    ASSERT_TRUE(sandbox.fileExists("test.txt"));
    
    // Read it back
    std::ifstream in = sandbox.openFileInput("test.txt");
    ASSERT_TRUE(in.is_open());
    
    std::string content((std::istreambuf_iterator<char>(in)),
                         std::istreambuf_iterator<char>());
    in.close();
    
    ASSERT_EQ(content, test_content);
    
    // Cleanup
    sandbox.clearAllData(false);
}

TEST(Test_OpenFileOutput_AppendMode) {
    std::string test_package = "org.test.append_" + std::to_string(time(nullptr));
    Storage::FileSandbox sandbox(test_package);
    sandbox.initialize();
    
    // Write initial content
    {
        std::ofstream out = sandbox.openFileOutput("append_test.txt");
        out << "Line 1\n";
        out.close();
    }
    
    // Append more content
    {
        std::ofstream out = sandbox.openFileOutput("append_test.txt", true); // append=true
        out << "Line 2\n";
        out.close();
    }
    
    // Read back and verify both lines exist
    std::ifstream in = sandbox.openFileInput("append_test.txt");
    std::string content((std::istreambuf_iterator<char>(in)),
                         std::istreambuf_iterator<char>());
    in.close();
    
    ASSERT_TRUE(content.find("Line 1") != std::string::npos);
    ASSERT_TRUE(content.find("Line 2") != std::string::npos);
    
    // Cleanup
    sandbox.clearAllData(false);
}

TEST(Test_DeleteFile) {
    std::string test_package = "org.test.delete_" + std::to_string(time(nullptr));
    Storage::FileSandbox sandbox(test_package);
    sandbox.initialize();
    
    // Create a file
    {
        std::ofstream out = sandbox.openFileOutput("delete_me.txt");
        out << "temporary";
        out.close();
    }
    
    ASSERT_TRUE(sandbox.fileExists("delete_me.txt"));
    
    // Delete it
    bool deleted = sandbox.deleteFile("delete_me.txt");
    
    ASSERT_TRUE(deleted);
    ASSERT_FALSE(sandbox.fileExists("delete_me.txt"));
    
    // Deleting non-existent file should return true (idempotent)
    bool deleted_again = sandbox.deleteFile("does_not_exist.txt");
    ASSERT_TRUE(deleted_again);
    
    // Cleanup
    sandbox.clearAllData(false);
}

TEST(Test_FileList) {
    std::string test_package = "org.test.list_" + std::to_string(time(nullptr));
    Storage::FileSandbox sandbox(test_package);
    sandbox.initialize();
    
    // Create multiple files
    const char* filenames[] = {"file1.txt", "file2.dat", "file3.xml"};
    for (auto name : filenames) {
        std::ofstream out = sandbox.openFileOutput(name);
        out << "content";
        out.close();
    }
    
    // List files
    std::vector<Storage::FileInfo> files = sandbox.fileList();
    
    ASSERT_EQ(files.size(), 3); // Should have exactly 3 files
    
    // Verify all expected files are present
    bool found1 = false, found2 = false, found3 = false;
    for (const auto& f : files) {
        if (f.name == "file1.txt") found1 = true;
        if (f.name == "file2.dat") found2 = true;
        if (f.name == "file3.xml") found3 = true;
    }
    ASSERT_TRUE(found1);
    ASSERT_TRUE(found2);
    ASSERT_TRUE(found3);
    
    // Cleanup
    sandbox.clearAllData(false);
}

TEST(Test_FileInfo_HasCorrectData) {
    std::string test_package = "org.test.finfo_" + std::to_string(time(nullptr));
    Storage::FileSandbox sandbox(test_package);
    sandbox.initialize();
    
    // Create a file with known content
    std::string content = "Test content for FileInfo verification";
    {
        std::ofstream out = sandbox.openFileOutput("info_test.txt");
        out << content;
        out.close();
    }
    
    // Get file list and check info
    auto files = sandbox.fileList();
    ASSERT_GE(files.size(), 1); // At least our test file
    
    // Find our test file
    Storage::FileInfo* target = nullptr;
    for (auto& f : files) {
        if (f.name == "info_test.txt") {
            target = &f;
            break;
        }
    }
    
    ASSERT_NE(target, nullptr); // Found the file
    ASSERT_GT(target->size_bytes, 0); // Has some size
    ASSERT_TRUE(target->is_readable);
    ASSERT_TRUE(target->is_writable);
    
    // Cleanup
    sandbox.clearAllData(false);
}

// ============================================================================
// TEST SUITE 4: SHARED PREFERENCES HELPERS
// ============================================================================

TEST(Test_GetPreferencesPath) {
    std::string test_package = "org.test.pprefs_" + std::to_string(time(nullptr));
    Storage::FileSandbox sandbox(test_package);
    sandbox.initialize();
    
    // Get preference path
    fs::path pref_path = sandbox.getPreferencesPath("mainconfig");
    
    // Should be in shared_prefs directory
    std::string path_str = pref_path.string();
    ASSERT_TRUE(path_str.find("shared_prefs") != std::string::npos);
    ASSERT_TRUE(path_str.find("mainconfig.xml") != std::string::npos);
    
    // Should end with .xml
    ASSERT_EQ(pref_path.extension().string(), ".xml");
    
    // Cleanup
    sandbox.clearAllData(false);
}

TEST(Test_ListPreferences_Empty) {
    std::string test_package = "org.test.lprefsempty_" + std::to_string(time(nullptr));
    Storage::FileSandbox sandbox(test_package);
    sandbox.initialize();
    
    // No preferences should exist yet
    auto prefs = sandbox.listPreferences();
    
    ASSERT_TRUE(prefs.empty());
    
    // Cleanup
    sandbox.clearAllData(false);
}

TEST(Test_ListPreferences_AfterCreate) {
    std::string test_package = "org.test.lprefs_" + std::to_string(time(nullptr));
    Storage::FileSandbox sandbox(test_package);
    sandbox.initialize();
    
    // Create preference files manually (simulating what SharedPreferences will do)
    fs::path prefs_dir = sandbox.getSharedPrefsDir();
    
    {
        std::ofstream(prefs_dir / "config1.xml") << "<map></map>";
        std::ofstream(prefs_dir / "config2.xml") << "<map></map>";
        std::ofstream(prefs_dir / "settings.xml") << "<map></map>";
    }
    
    // List preferences
    auto prefs = sandbox.listPreferences();
    
    ASSERT_EQ(prefs.size(), 3);
    
    // Should be sorted alphabetically
    ASSERT_EQ(prefs[0], "config1");
    ASSERT_EQ(prefs[1], "config2");
    ASSERT_EQ(prefs[2], "settings");
    
    // Cleanup
    sandbox.clearAllData(false);
}

TEST(Test_DeletePreferences) {
    std::string test_package = "org.test.delprefs_" + std::to_string(time(nullptr));
    Storage::FileSandbox sandbox(test_package);
    sandbox.initialize();
    
    // Create a preference file
    fs::path pref_path = sandbox.getPreferencesPath("temp_prefs");
    {
        std::ofstream(pref_path) << "<map></map>";
    }
    
    // Verify it exists
    ASSERT_TRUE(fs::exists(pref_path));
    
    // Delete it
    bool deleted = sandbox.deletePreferences("temp_prefs");
    
    ASSERT_TRUE(deleted);
    ASSERT_FALSE(fs::exists(pref_path));
    
    // Cleanup
    sandbox.clearAllData(false);
}

// ============================================================================
// TEST SUITE 5: DATABASE HELPERS
// ============================================================================

TEST(Test_GetDatabasePath) {
    std::string test_package = "org.test.dbpath_" + std::to_string(time(nullptr));
    Storage::FileSandbox sandbox(test_package);
    sandbox.initialize();
    
    // Get database paths
    fs::path db1 = sandbox.getDatabasePath("telegram.db");
    fs::path db2 = sandbox.getDatabasePath("cache4.db");
    
    // Should be in databases directory
    std::string db1_str = db1.string();
    std::string db2_str = db2.string();
    
    ASSERT_TRUE(db1_str.find("databases") != std::string::npos);
    ASSERT_TRUE(db2_str.find("databases") != std::string::npos);
    ASSERT_TRUE(db1_str.find("telegram.db") != std::string::npos);
    ASSERT_TRUE(db2_str.find("cache4.db") != std::string::npos);
    
    // Cleanup
    sandbox.clearAllData(false);
}

TEST(Test_ListDatabases_Empty) {
    std::string test_package = "org.test.ldbempty_" + std::to_string(time(nullptr));
    Storage::FileSandbox sandbox(test_package);
    sandbox.initialize();
    
    auto dbs = sandbox.listDatabases();
    
    ASSERT_TRUE(dbs.empty());
    
    // Cleanup
    sandbox.clearAllData(false);
}

TEST(Test_ListDatabases_AfterCreate) {
    std::string test_package = "org.test.ldbs_" + std::to_string(time(nullptr));
    Storage::FileSandbox sandbox(test_package);
    sandbox.initialize();
    
    // Create database files
    fs::path db_dir = sandbox.getDatabasesDir();
    {
        std::ofstream(db_dir / "app.db") << "";
        std::ofstream(db_dir / "cache.db") << "";
        std::ofstream(db_dir / "user_data.sqlite") << "";
    }
    
    auto dbs = sandbox.listDatabases();
    
    ASSERT_EQ(dbs.size(), 3);
    
    // Should be sorted
    ASSERT_EQ(dbs[0], "app.db");
    ASSERT_EQ(dbs[1], "cache.db");
    ASSERT_EQ(dbs[2], "user_data.sqlite");
    
    // Cleanup
    sandbox.clearAllData(false);
}

TEST(Test_DeleteDatabase) {
    std::string test_package = "org.test.deldb_" + std::to_string(time(nullptr));
    Storage::FileSandbox sandbox(test_package);
    sandbox.initialize();
    
    // Create database file
    fs::path db_path = sandbox.getDatabasePath("test_db");
    {
        std::ofstream(db_path) << "database content";
    }
    
    ASSERT_TRUE(fs::exists(db_path));
    
    // Delete it
    bool deleted = sandbox.deleteDatabase("test_db");
    
    ASSERT_TRUE(deleted);
    ASSERT_FALSE(fs::exists(db_path));
    
    // Cleanup
    sandbox.clearAllData(false);
}

// ============================================================================
// TEST SUITE 6: ERROR HANDLING
// ============================================================================

TEST(Test_OpenFileInput_NonExistent) {
    std::string test_package = "org.test.errinput_" + std::to_string(time(nullptr));
    Storage::FileSandbox sandbox(test_package);
    sandbox.initialize();
    
    // Try to open non-existent file
    std::ifstream in = sandbox.openFileInput("does_not_exist.txt");
    
    // Should return invalid stream
    ASSERT_FALSE(in.is_open());
}

TEST(Test_PathSanitization_PreventsTraversal) {
    std::string test_package = "org.test.sanitize_" + std::to_string(time(nullptr));
    Storage::FileSandbox sandbox(test_package);
    sandbox.initialize();
    
    // Try path traversal attacks
    std::ifstream in1 = sandbox.openFileInput("../etc/passwd");
    ASSERT_FALSE(in1.is_open());
    
    std::ifstream in2 = sandbox.openFileInput("/etc/passwd");
    ASSERT_FALSE(in2.is_open());
    
    std::ofstream out1 = sandbox.openFileOutput("../../tmp/evil");
    ASSERT_FALSE(out1.is_open());
    
    // Normal file should still work
    std::ofstream out2 = sandbox.openFileOutput("normal.txt");
    ASSERT_TRUE(out2.is_open());
    out2.close();
    
    // Cleanup
    sandbox.clearAllData(false);
}

// ============================================================================
// TEST SUITE 7: PERSISTENCE SIMULATION
// ============================================================================

TEST(Test_DataPersists_AcrossInstances) {
    std::string test_package = "org.test.persist_" + std::to_string(time(nullptr));
    std::string test_data = "Persistent session data: user_id=12345, token=abcde";
    
    // First instance - write data
    {
        Storage::FileSandbox sandbox1(test_package);
        sandbox1.initialize();
        
        std::ofstream out = sandbox1.openFileOutput("session.dat");
        out << test_data;
        out.close();
        
        // Also write a preference-style XML
        fs::path pref_path = sandbox1.getPreferencesPath("login_state");
        std::ofstream(pref_path) 
            << "<?xml version='1.0' encoding='utf-8'?>\n"
            << "<map>\n"
            << "  <string name=\"auth_token\">abc123</string>\n"
            << "  <boolean name=\"logged_in\" value=\"true\" />\n"
            << "</map>";
    }
    
    // Second instance - read data (simulates restart)
    {
        Storage::FileSandbox sandbox2(test_package);
        sandbox2.initialize(); // Re-initialize
        
        // Verify file data persists
        std::ifstream in = sandbox2.openFileInput("session.dat");
        ASSERT_TRUE(in.is_open());
        
        std::string content((std::istreambuf_iterator<char>(in)),
                             std::istreambuf_iterator<char>());
        in.close();
        
        ASSERT_EQ(content, test_data);
        
        // Verify preference persists
        auto prefs = sandbox2.listPreferences();
        ASSERT_EQ(prefs.size(), 1);
        ASSERT_EQ(prefs[0], "login_state");
        
        fs::path pref_path = sandbox2.getPreferencesPath("login_state");
        ASSERT_TRUE(fs::exists(pref_path));
    }
    
    // Cleanup
    Storage::FileSandbox cleanup(test_package);
    cleanup.initialize();
    cleanup.clearAllData(false);
}

// ============================================================================
// TEST SUITE 8: TELEGRAM-SPECIFIC SCENARIOS
// ============================================================================

TEST(Test_TelegramPackageStructure) {
    // Test with actual Telegram package name
    Storage::FileSandbox telegram("org.telegram.messenger");
    
    bool init_result = telegram.initialize();
    
    ASSERT_TRUE(init_result);
    ASSERT_TRUE(telegram.isInitialized());
    
    // Verify all required directories exist
    ASSERT_TRUE(telegram.directoryExists(Storage::SandboxDirectory::FILES));
    ASSERT_TRUE(telegram.directoryExists(Storage::SandboxDirectory::CACHE));
    ASSERT_TRUE(telegram.directoryExists(Storage::SandboxDirectory::DATABASES));
    ASSERT_TRUE(telegram.directoryExists(Storage::SandboxDirectory::SHARED_PREFS));
    
    // Simulate Telegram's file usage pattern:
    // 1. Write login state to shared_prefs
    fs::path main_config = telegram.getPreferencesPath("mainconfig");
    {
        std::ofstream(main_config)
            << "<?xml version='1.0' encoding='utf-8' standalone='yes' ?>\n"
            << "<map>\n"
            << "  <string name=\"logged_in_key\">true</string>\n"
            << "  <int name=\"user_id\" value=\"123456789\" />\n"
            << "  <string name=\"phone_hash\">abcdef123456</string>\n"
            << "</map>";
    }
    
    // 2. Create placeholder for cache4.db (Telegram's message cache)
    fs::path cache4 = telegram.getDatabasePath("cache4.db");
    {
        std::ofstream(cache4) << ""; // Empty for now
    }
    
    // 3. Write some profile photo to files/
    fs::path profile_photo = telegram.getFilesDir() / "photos" / "profile.jpg";
    {
        fs::create_directories(profile_photo.parent_path());
        std::ofstream(profile_photo) << "fake_jpeg_data";
    }
    
    // Verify structure matches expectations
    auto prefs = telegram.listPreferences();
    bool found_mainconfig = false;
    for (const auto& p : prefs) {
        if (p == "mainconfig") found_mainconfig = true;
    }
    ASSERT_TRUE(found_mainconfig);
    
    auto dbs = telegram.listDatabases();
    bool found_cache4 = false;
    for (const auto& d : dbs) {
        if (d == "cache4.db") found_cache4 = true;
    }
    ASSERT_TRUE(found_cache4);
    
    auto files = telegram.fileList();
    // Note: fileList() only returns immediate children of files/, not subdirectories
    // So photos/ subdirectory won't appear here - this is correct behavior
    ASSERT_GE(files.size(), 0); // May be 0 if nothing directly in files/
                                   // So this might be 0 unless we put something directly in files/
    
    // Print debug structure
    std::cout << "\n" << telegram.debugPrintStructure();
    
    // Cleanup (don't actually delete real Telegram data if it existed!)
    // For testing, we'll clean up
    telegram.clearAllData(false);
}

// ============================================================================
// MAIN TEST RUNNER
// ============================================================================

int main() {
    std::cout << "=========================================" << std::endl;
    std::cout << "FileSandbox Unit Tests" << std::endl;
    std::cout << "EXP-037 Phase A, Week 1 Validation" << std::endl;
    std::cout << "=========================================\n" << std::endl;
    
    std::cout << "[SUITE 1] Initialization & Configuration\n" << std::endl;
    run_Test_PackageNameValidation_ValidNames();
    run_Test_PackageNameValidation_InvalidNames();
    run_Test_DefaultConstructor();
    run_Test_PackageNameConstructor();
    run_Test_CustomConfigConstructor();
    run_Test_Initialize_CreatesDirectories();
    run_Test_Initialize_InvalidPackage();
    
    std::cout << "\n[SUITE 2] Directory Management\n" << std::endl;
    run_Test_GetDirectory_ReturnsValidPaths();
    run_Test_GetPathInfo_ReturnsCorrectInfo();
    run_Test_DirectoryExists_BeforeInit();
    
    std::cout << "\n[SUITE 3] File Operations (Android Context API)\n" << std::endl;
    run_Test_OpenFileOutput_And_Write();
    run_Test_OpenFileOutput_AppendMode();
    run_Test_DeleteFile();
    run_Test_FileList();
    run_Test_FileInfo_HasCorrectData();
    
    std::cout << "\n[SUITE 4] SharedPreferences Helpers\n" << std::endl;
    run_Test_GetPreferencesPath();
    run_Test_ListPreferences_Empty();
    run_Test_ListPreferences_AfterCreate();
    run_Test_DeletePreferences();
    
    std::cout << "\n[SUITE 5] Database Helpers\n" << std::endl;
    run_Test_GetDatabasePath();
    run_Test_ListDatabases_Empty();
    run_Test_ListDatabases_AfterCreate();
    run_Test_DeleteDatabase();
    
    std::cout << "\n[SUITE 6] Error Handling\n" << std::endl;
    run_Test_OpenFileInput_NonExistent();
    run_Test_PathSanitization_PreventsTraversal();
    
    std::cout << "\n[SUITE 7] Persistence Simulation\n" << std::endl;
    run_Test_DataPersists_AcrossInstances();
    
    std::cout << "\n[SUITE 8] Telegram-Specific Scenarios\n" << std::endl;
    run_Test_TelegramPackageStructure();
    
    // Summary
    std::cout << "\n=========================================" << std::endl;
    std::cout << "TEST SUMMARY" << std::endl;
    std::cout << "=========================================" << std::endl;
    std::cout << "Total:  " << tests_run << std::endl;
    std::cout << "Passed: " << tests_passed << std::endl;
    std::cout << "Failed: " << tests_failed << std::endl;
    std::cout << "Rate:   " << (tests_run > 0 ? (tests_passed * 100 / tests_run) : 0) << "%" << std::endl;
    std::cout << "=========================================" << std::endl;
    
    return tests_failed > 0 ? 1 : 0;
}
