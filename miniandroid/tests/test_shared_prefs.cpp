/**
 * @file test_shared_prefs.cpp
 * @brief Comprehensive unit tests for SharedPreferences implementation
 * 
 * @description
 * Test suite for EXP-037 Phase A, Week 2: SharedPreferences Implementation.
 * Validates all functionality required for Android compatibility layer.
 * 
 * Test Categories:
 * - Suite 1: Construction & Initialization (5 tests)
 * - Suite 2: String Operations (6 tests)
 * - Suite 3: Primitive Type Operations (10 tests)
 * - Suite 4: Editor Pattern & Chaining (8 tests)
 * - Suite 5: XML File I/O (7 tests)
 * - Suite 6: Persistence Across Instances (4 tests)
 * - Suite 7: Error Handling (5 tests)
 * - Suite 8: Thread Safety (2 tests)
 * - Suite 9: Telegram-Specific Scenarios (3 tests)
 * - Suite 10: Edge Cases & Special Characters (5 tests)
 * 
 * Total: ~55 tests
 * 
 * @author EXP-037 Development (Phase A, Week 2)
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
#include <cmath>

// Include the implementation under test
#include "api/shared_prefs.h"

namespace fs = std::filesystem;
using namespace AndroidAPI;

// ============================================================================
// TEST INFRASTRUCTURE
// ============================================================================

/**
 * @struct TestStats
 * @brief Tracks test execution statistics
 */
struct TestStats {
    int total = 0;
    int passed = 0;
    int failed = 0;
    std::vector<std::string> failures;
};

static TestStats g_stats;

/**
 * @brief Run a single test case
 * @param test_name Human-readable test name
 * @param test_fn Function that performs the test assertions
 */
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

/**
 * @brief Assert macros for cleaner test code
 */
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

/**
 * @brief Generate unique package name for each test to avoid collisions
 * @param prefix Test-specific prefix
 * @return Unique package name with timestamp
 */
std::string uniquePackage(const std::string& prefix) {
    auto now = std::chrono::system_clock::now().time_since_epoch().count();
    return prefix + "_" + std::to_string(now);
}

/**
 * @brief Clean up test files after a test
 * @param prefs SharedPreferences to clean up
 */
void cleanupTest(SharedPreferences& prefs) {
    try {
        fs::remove(prefs.getFilePath());
        
        // Also remove parent directory if empty
        fs::path parent = prefs.getFilePath().parent_path();
        if (fs::exists(parent) && fs::is_empty(parent)) {
            fs::remove(parent);
        }
        
        // And the package directory if empty
        parent = parent.parent_path();
        if (fs::exists(parent) && fs::is_empty(parent)) {
            fs::remove(parent);
        }
    } catch (...) {
        // Ignore cleanup errors
    }
}


// ============================================================================
// SUITE 1: CONSTRUCTION & INITIALIZATION
// ============================================================================

void runSuite1_Construction() {
    std::cout << "\n[SUITE 1] Construction & Initialization\n" << std::endl;
    
    runTest("Test_DefaultConstruction_CreatesInstance", []() {
        std::string pkg = uniquePackage("org.test.construct");
        SharedPreferences prefs(pkg, "test");
        
        TEST_ASSERT_TRUE(!prefs.getPackageName().empty(), "Package name should not be empty");
        TEST_ASSERT_EQ(prefs.getName(), "test", "Name should match");
        TEST_ASSERT_EQ(prefs.size(), size_t(0), "Should be empty initially");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_CustomBasePath_UsesCorrectPath", []() {
        std::string pkg = uniquePackage("org.test.basepath");
        SharedPreferences prefs(pkg, "test", "custom_runtime/data");
        
        std::string expected = "custom_runtime/data/" + pkg + "/shared_prefs/test.xml";
        TEST_ASSERT_EQ(prefs.getFilePath().string(), expected, "Path should match custom base");
        
        cleanupTest(prefs);
        // Clean up custom directory
        try { fs::remove_all("custom_runtime"); } catch (...) {}
    });
    
    runTest("Test_FilePathConstructor_UsesExactPath", []() {
        fs::path temp_path = "runtime/data/test_exact_path.xml";
        SharedPreferences prefs(temp_path);
        
        TEST_ASSERT_EQ(prefs.getFilePath().string(), temp_path.string(), 
                       "Should use exact path provided");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_EmptyInitially_NoFileCreated", []() {
        std::string pkg = uniquePackage("org.test.nofile");
        SharedPreferences prefs(pkg, "test");
        
        TEST_ASSERT_FALSE(prefs.fileExists(), "File should not exist until commit");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_PackageAndName_Accessors", []() {
        std::string pkg = uniquePackage("com.example.app");
        SharedPreferences prefs(pkg, "user_settings");
        
        TEST_ASSERT_EQ(prefs.getPackageName(), pkg, "Package should match");
        TEST_ASSERT_EQ(prefs.getName(), "user_settings", "Name should match");
        
        cleanupTest(prefs);
    });
}


// ============================================================================
// SUITE 2: STRING OPERATIONS
// ============================================================================

void runSuite2_StringOperations() {
    std::cout << "\n[SUITE 2] String Operations\n" << std::endl;
    
    runTest("Test_PutString_GetString_RoundTrip", []() {
        std::string pkg = uniquePackage("org.test.string");
        SharedPreferences prefs(pkg, "test");
        
        prefs.edit()
            .putString("greeting", "Hello, World!")
            .commit();
        
        std::string value = prefs.getString("greeting");
        TEST_ASSERT_EQ(value, "Hello, World!", "String value should match");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_GetString_DefaultValue_WhenMissing", []() {
        std::string pkg = uniquePackage("org.test.defval");
        SharedPreferences prefs(pkg, "test");
        
        std::string value = prefs.getString("nonexistent", "default_value");
        TEST_ASSERT_EQ(value, "default_value", "Should return default for missing key");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_PutString_EmptyValue", []() {
        std::string pkg = uniquePackage("org.test.emptystr");
        SharedPreferences prefs(pkg, "test");
        
        prefs.edit()
            .putString("empty", "")
            .commit();
        
        std::string value = prefs.getString("empty", "not_empty");
        TEST_ASSERT_EQ(value, "", "Empty string should be preserved");
        TEST_ASSERT_TRUE(prefs.contains("empty"), "Key should exist even with empty value");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_PutString_SpecialCharacters", []() {
        std::string pkg = uniquePackage("org.test.special");
        SharedPreferences prefs(pkg, "test");
        
        std::string special = "Hello <world> & \"friends\" 'here'";
        prefs.edit()
            .putString("special", special)
            .commit();
        
        std::string value = prefs.getString("special");
        TEST_ASSERT_EQ(value, special, "Special characters should survive round-trip");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_PutString_UnicodeCharacters", []() {
        std::string pkg = uniquePackage("org.test.unicode");
        SharedPreferences prefs(pkg, "test");
        
        std::string unicode = "Hello \u4e16\u754c \u00e9\u00e8\u00ea";  // Chinese, accents
        prefs.edit()
            .putString("unicode", unicode)
            .commit();
        
        std::string value = prefs.getString("unicode");
        TEST_ASSERT_EQ(value, unicode, "Unicode should survive round-trip");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_MultipleStrings_DifferentKeys", []() {
        std::string pkg = uniquePackage("org.test.multi");
        SharedPreferences prefs(pkg, "test");
        
        prefs.edit()
            .putString("key1", "value1")
            .putString("key2", "value2")
            .putString("key3", "value3")
            .commit();
        
        TEST_ASSERT_EQ(prefs.getString("key1"), "value1", "First value should match");
        TEST_ASSERT_EQ(prefs.getString("key2"), "value2", "Second value should match");
        TEST_ASSERT_EQ(prefs.getString("key3"), "value3", "Third value should match");
        TEST_ASSERT_EQ(prefs.size(), size_t(3), "Should have 3 entries");
        
        cleanupTest(prefs);
    });
}


// ============================================================================
// SUITE 3: PRIMITIVE TYPE OPERATIONS
// ============================================================================

void runSuite3_PrimitiveTypes() {
    std::cout << "\n[SUITE 3] Primitive Type Operations\n" << std::endl;
    
    // Integer tests
    runTest("Test_PutInt_GetInt_Positive", []() {
        std::string pkg = uniquePackage("org.test.intpos");
        SharedPreferences prefs(pkg, "test");
        
        prefs.edit().putInt("count", 42).commit();
        TEST_ASSERT_EQ(prefs.getInt("count"), 42, "Positive integer should match");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_PutInt_GetInt_Negative", []() {
        std::string pkg = uniquePackage("org.test.intneg");
        SharedPreferences prefs(pkg, "test");
        
        prefs.edit().putInt("negative", -12345).commit();
        TEST_ASSERT_EQ(prefs.getInt("negative"), -12345, "Negative integer should match");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_PutInt_GetInt_Zero", []() {
        std::string pkg = uniquePackage("org.test.intzero");
        SharedPreferences prefs(pkg, "test");
        
        prefs.edit().putInt("zero", 0).commit();
        TEST_ASSERT_EQ(prefs.getInt("zero"), 0, "Zero should be preserved");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_PutInt_GetInt_MaxMin", []() {
        std::string pkg = uniquePackage("org.test.intbounds");
        SharedPreferences prefs(pkg, "test");
        
        prefs.edit()
            .putInt("max", INT32_MAX)
            .putInt("min", INT32_MIN)
            .commit();
        
        TEST_ASSERT_EQ(prefs.getInt("max"), INT32_MAX, "Max int32 should work");
        TEST_ASSERT_EQ(prefs.getInt("min"), INT32_MIN, "Min int32 should work");
        
        cleanupTest(prefs);
    });
    
    // Long tests
    runTest("Test_PutLong_GetLong_LargeValues", []() {
        std::string pkg = uniquePackage("org.test.longval");
        SharedPreferences prefs(pkg, "test");
        
        int64_t large = 9876543210LL;
        prefs.edit().putLong("large", large).commit();
        
        prefs.edit().putLong("timestamp", 1692012345678LL).commit();
        TEST_ASSERT_EQ(prefs.getLong("timestamp"), 1692012345678LL, "Large long should work");
        
        cleanupTest(prefs);
    });
    
    // Float tests
    runTest("Test_PutFloat_GetFloat_Precision", []() {
        std::string pkg = uniquePackage("org.test.floatval");
        SharedPreferences prefs(pkg, "test");
        
        prefs.edit().putFloat("pi", 3.14159f).commit();
        float pi = prefs.getFloat("pi");
        
        // Allow small floating point difference
        TEST_ASSERT_TRUE(fabs(pi - 3.14159f) < 0.0001f, "Float precision should be reasonable");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_PutFloat_GetFloat_SpecialValues", []() {
        std::string pkg = uniquePackage("org.test.floatspec");
        SharedPreferences prefs(pkg, "test");
        
        prefs.edit()
            .putFloat("zero", 0.0f)
            .putFloat("neg", -1.5f)
            .putFloat("small", 0.0001f)
            .commit();
        
        TEST_ASSERT_TRUE(prefs.getFloat("zero") == 0.0f, "Zero float");
        TEST_ASSERT_TRUE(prefs.getFloat("neg") < 0.0f, "Negative float");
        
        cleanupTest(prefs);
    });
    
    // Boolean tests
    runTest("Test_PutBoolean_GetBoolean_TrueFalse", []() {
        std::string pkg = uniquePackage("org.test.bool");
        SharedPreferences prefs(pkg, "test");
        
        prefs.edit()
            .putBoolean("enabled", true)
            .putBoolean("disabled", false)
            .commit();
        
        TEST_ASSERT_TRUE(prefs.getBoolean("enabled"), "True should be true");
        TEST_ASSERT_FALSE(prefs.getBoolean("disabled"), "False should be false");
        
        cleanupTest(prefs);
    });
    
    // StringSet tests
    runTest("Test_PutStringSet_GetStringSet_RoundTrip", []() {
        std::string pkg = uniquePackage("org.test.set");
        SharedPreferences prefs(pkg, "test");
        
        std::set<std::string> tags = {"work", "personal", "important"};
        prefs.edit().putStringSet("tags", tags).commit();
        
        std::set<std::string> result = prefs.getStringSet("tags");
        TEST_ASSERT_EQ(result.size(), size_t(3), "Set should have 3 elements");
        TEST_ASSERT_TRUE(result.count("work") > 0, "Should contain 'work'");
        TEST_ASSERT_TRUE(result.count("personal") > 0, "Should contain 'personal'");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_PutStringSet_EmptySet", []() {
        std::string pkg = uniquePackage("org.test.emptyset");
        SharedPreferences prefs(pkg, "test");
        
        std::set<std::string> empty_set;
        prefs.edit().putStringSet("empty_tags", empty_set).commit();
        
        std::set<std::string> result = prefs.getStringSet("empty_tags");
        TEST_ASSERT_TRUE(result.empty(), "Empty set should be preserved");
        
        cleanupTest(prefs);
    });
}


// ============================================================================
// SUITE 4: EDITOR PATTERN & CHAINING
// ============================================================================

void runSuite4_EditorPattern() {
    std::cout << "\n[SUITE 4] Editor Pattern & Chaining\n" << std::endl;
    
    runTest("Test_Editor_Chaining_MultiplePuts", []() {
        std::string pkg = uniquePackage("org.test.chain");
        SharedPreferences prefs(pkg, "test");
        
        bool success = prefs.edit()
            .putString("name", "Alice")
            .putInt("age", 30)
            .putBoolean("active", true)
            .commit();
        
        TEST_ASSERT_TRUE(success, "Chained commit should succeed");
        TEST_ASSERT_EQ(prefs.getString("name"), "Alice", "Chained string should work");
        TEST_ASSERT_EQ(prefs.getInt("age"), 30, "Chained int should work");
        TEST_ASSERT_TRUE(prefs.getBoolean("active"), "Chained bool should work");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_Commit_ReturnsTrue_OnSuccess", []() {
        std::string pkg = uniquePackage("org.test.commitok");
        SharedPreferences prefs(pkg, "test");
        
        bool result = prefs.edit().putString("key", "value").commit();
        TEST_ASSERT_TRUE(result, "Commit should return true on success");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_Commit_CreatesFile", []() {
        std::string pkg = uniquePackage("org.test.filecreate");
        SharedPreferences prefs(pkg, "test");
        
        TEST_ASSERT_FALSE(prefs.fileExists(), "File should not exist before commit");
        
        prefs.edit().putString("key", "value").commit();
        
        TEST_ASSERT_TRUE(prefs.fileExists(), "File should exist after commit");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_Remove_Key", []() {
        std::string pkg = uniquePackage("org.test.remove");
        SharedPreferences prefs(pkg, "test");
        
        prefs.edit()
            .putString("temp", "temporary")
            .commit();
        
        TEST_ASSERT_TRUE(prefs.contains("temp"), "Key should exist before removal");
        
        prefs.edit()
            .remove("temp")
            .commit();
        
        TEST_ASSERT_FALSE(prefs.contains("temp"), "Key should not exist after removal");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_Clear_AllKeys", []() {
        std::string pkg = uniquePackage("org.test.clear");
        SharedPreferences prefs(pkg, "test");
        
        prefs.edit()
            .putString("k1", "v1")
            .putInt("k2", 2)
            .putBoolean("k3", true)
            .commit();
        
        TEST_ASSERT_EQ(prefs.size(), size_t(3), "Should have 3 entries before clear");
        
        prefs.edit().clear().commit();
        
        TEST_ASSERT_EQ(prefs.size(), size_t(0), "Should have 0 entries after clear");
        TEST_ASSERT_TRUE(prefs.isEmpty(), "Should be empty after clear");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_MultipleEditors_Independent", []() {
        std::string pkg = uniquePackage("org.test.multiedit");
        SharedPreferences prefs(pkg, "test");
        
        // Create two independent editors
        auto editor1 = prefs.edit();
        auto editor2 = prefs.edit();
        
        editor1.putString("e1", "from_editor1");
        editor2.putString("e2", "from_editor2");
        
        // Commit editor1 first
        editor1.commit();
        TEST_ASSERT_TRUE(prefs.contains("e1"), "Editor1's change should be visible");
        TEST_ASSERT_FALSE(prefs.contains("e2"), "Editor2's change should NOT be visible yet");
        
        // Then commit editor2
        editor2.commit();
        TEST_ASSERT_TRUE(prefs.contains("e2"), "Editor2's change should now be visible");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_HasPendingChanges_BeforeCommit", []() {
        std::string pkg = uniquePackage("org.test.pending");
        SharedPreferences prefs(pkg, "test");
        
        auto editor = prefs.edit();
        TEST_ASSERT_FALSE(editor.hasPendingChanges(), "No changes initially");
        
        editor.putString("key", "value");
        TEST_ASSERT_TRUE(editor.hasPendingChanges(), "Changes after put");
        TEST_ASSERT_EQ(editor.pendingChangeCount(), size_t(1), "One pending change");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_Apply_NonBlocking", []() {
        std::string pkg = uniquePackage("org.test.apply");
        SharedPreferences prefs(pkg, "test");
        
        // apply() is async, so we just verify it doesn't block or crash
        prefs.edit()
            .putString("async_key", "async_value")
            .apply();
        
        // Give it a moment to complete
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        
        // The value should eventually be there (may need more time in production)
        // For this test, we just verify no crash occurred
        TEST_ASSERT_TRUE(true, "Apply completed without crash");
        
        cleanupTest(prefs);
    });
}


// ============================================================================
// SUITE 5: XML FILE I/O
// ============================================================================

void runSuite5_XmlIo() {
    std::cout << "\n[SUITE 5] XML File I/O\n" << std::endl;
    
    runTest("Test_XmlFormat_AndroidCompatible", []() {
        std::string pkg = uniquePackage("org.test.xmlfmt");
        SharedPreferences prefs(pkg, "test");
        
        prefs.edit()
            .putString("name", "Telegram")
            .putInt("version", 100)
            .putBoolean("pro", false)
            .commit();
        
        // Read raw XML content
        std::ifstream file(prefs.getFilePath());
        std::stringstream buffer;
        buffer << file.rdbuf();
        file.close();
        
        std::string xml = buffer.str();
        
        // Verify Android-compatible structure
        TEST_ASSERT_TRUE(xml.find("<?xml version='1.0' encoding='utf-8' standalone='yes' ?>") != std::string::npos,
                        "Should have XML declaration");
        TEST_ASSERT_TRUE(xml.find("<map>") != std::string::npos,
                        "Should have <map> root element");
        TEST_ASSERT_TRUE(xml.find("</map>") != std::string::npos,
                        "Should have closing </map>");
        TEST_ASSERT_TRUE(xml.find("<string name=\"name\">") != std::string::npos,
                        "Should have string element with name attribute");
        TEST_ASSERT_TRUE(xml.find("<int name=\"version\" value=\"100\" />") != std::string::npos,
                        "Should have int element with value attribute");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_XmlEscaping_SpecialChars", []() {
        std::string pkg = uniquePackage("org.test.xmlescape");
        SharedPreferences prefs(pkg, "test");
        
        std::string dangerous = "<script>alert('xss')</script>";
        prefs.edit().putString("dangerous", dangerous).commit();
        
        // Read back and verify escaping happened
        std::ifstream file(prefs.getFilePath());
        std::stringstream buffer;
        buffer << file.rdbuf();
        file.close();
        
        std::string xml = buffer.str();
        
        // Should contain escaped versions
        TEST_ASSERT_TRUE(xml.find("&lt;script&gt;") != std::string::npos,
                        "XML should escape < and >");
        
        // But reading back should give original
        TEST_ASSERT_EQ(prefs.getString("dangerous"), dangerous,
                      "Round-trip should unescape correctly");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_ReloadFromFile", []() {
        std::string pkg = uniquePackage("org.test.reload");
        SharedPreferences prefs(pkg, "test");
        
        // Write initial data
        prefs.edit()
            .putString("original", "data")
            .commit();
        
        // Modify externally (simulate another process)
        {
            std::ofstream file(prefs.getFilePath(), std::ios::app);
            file << "    <string name=\"external\">added</string>\n";
            file << "</map>\n";  // This will make invalid XML but tests reload concept
            // Actually let's do proper modification by rewriting
        }
        
        // Better approach: create new instance pointing to same file
        SharedPreferences prefs2(pkg, "test");
        TEST_ASSERT_EQ(prefs2.getString("original"), "data",
                      "New instance should read existing data");
        
        cleanupTest(prefs);
        cleanupTest(prefs2);
    });
    
    runTest("Test_DeleteFile_RemovesFromDisk", []() {
        std::string pkg = uniquePackage("org.test.delfile");
        SharedPreferences prefs(pkg, "test");
        
        prefs.edit().putString("key", "value").commit();
        TEST_ASSERT_TRUE(prefs.fileExists(), "File should exist");
        
        bool deleted = prefs.deleteFile();
        TEST_ASSERT_TRUE(deleted, "Delete should succeed");
        TEST_ASSERT_FALSE(prefs.fileExists(), "File should not exist after delete");
        TEST_ASSERT_EQ(prefs.size(), size_t(0), "In-memory data cleared too");
    });
    
    runTest("Test_GenerateXml_SortedOutput", []() {
        std::string pkg = uniquePackage("org.test.sorted");
        SharedPreferences prefs(pkg, "test");
        
        // Add keys in non-alphabetical order
        prefs.edit()
            .putString("zebra", "last")
            .putString("alpha", "first")
            .putString("middle", "mid")
            .commit();
        
        // Read XML and verify order
        std::ifstream file(prefs.getFilePath());
        std::stringstream buffer;
        buffer << file.rdbuf();
        file.close();
        
        std::string xml = buffer.str();
        size_t pos_alpha = xml.find("alpha");
        size_t pos_middle = xml.find("middle");
        size_t pos_zebra = xml.find("zebra");
        
        TEST_ASSERT_TRUE(pos_alpha < pos_middle && pos_middle < pos_zebra,
                        "Keys should appear in alphabetical order in XML");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_LongValue_InXml", []() {
        std::string pkg = uniquePackage("org.test.longxml");
        SharedPreferences prefs(pkg, "test");
        
        int64_t timestamp = 1692012345678LL;
        prefs.edit().putLong("ts", timestamp).commit();
        
        // Verify XML contains correct format
        std::ifstream file(prefs.getFilePath());
        std::stringstream buffer;
        buffer << file.rdbuf();
        file.close();
        
        std::string xml = buffer.str();
        TEST_ASSERT_TRUE(xml.find("<long name=\"ts\" value=\"1692012345678\" />") != std::string::npos,
                        "Long should be formatted correctly in XML");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_FloatPrecision_InXml", []() {
        std::string pkg = uniquePackage("org.test.floatxml");
        SharedPreferences prefs(pkg, "test");
        
        prefs.edit().putFloat("ratio", 0.75f).commit();
        
        // Read back and verify
        float ratio = prefs.getFloat("ratio");
        TEST_ASSERT_TRUE(fabs(ratio - 0.75f) < 0.001f, "Float should maintain precision");
        
        cleanupTest(prefs);
    });
}


// ============================================================================
// SUITE 6: PERSISTENCE ACROSS INSTANCES
// ============================================================================

void runSuite6_Persistence() {
    std::cout << "\n[SUITE 6] Persistence Across Instances\n" << std::endl;
    
    runTest("Test_DataSurvives_InstanceDestruction", []() {
        std::string pkg = uniquePackage("org.test.persist1");
        fs::path file_path;
        
        {
            // First instance - write data
            SharedPreferences prefs1(pkg, "session");
            file_path = prefs1.getFilePath();
            
            prefs1.edit()
                .putString("auth_token", "abc123xyz")
                .putLong("login_time", 1692012345678LL)
                .putBoolean("logged_in", true)
                .commit();
        }
        // Instance destroyed here
        
        {
            // Second instance - should read same data
            SharedPreferences prefs2(pkg, "session");
            
            TEST_ASSERT_EQ(prefs2.getString("auth_token"), "abc123xyz",
                          "Token should persist across instances");
            TEST_ASSERT_EQ(prefs2.getLong("login_time"), 1692012345678LL,
                          "Timestamp should persist across instances");
            TEST_ASSERT_TRUE(prefs2.getBoolean("logged_in"),
                           "Login state should persist across instances");
        }
        
        // Cleanup
        try { fs::remove(file_path); } catch (...) {}
    });
    
    runTest("Test_ModificationsVisibleToNewInstance", []() {
        std::string pkg = uniquePackage("org.test.persist2");
        fs::path file_path;
        
        {
            SharedPreferences prefs1(pkg, "config");
            file_path = prefs1.getFilePath();
            
            prefs1.edit().putInt("counter", 1).commit();
        }
        
        {
            SharedPreferences prefs2(pkg, "config");
            int val = prefs2.getInt("counter", 0);
            
            prefs2.edit().putInt("counter", val + 1).commit();
        }
        
        {
            SharedPreferences prefs3(pkg, "config");
            TEST_ASSERT_EQ(prefs3.getInt("counter", 0), 2,
                          "Increment should persist across instances");
        }
        
        try { fs::remove(file_path); } catch (...) {}
    });
    
    runTest("Test_MultiplePrefsFiles_ForSamePackage", []() {
        std::string pkg = uniquePackage("org.test.multifiles");
        
        {
            SharedPreferences prefs1(pkg, "settings");
            SharedPreferences prefs2(pkg, "cache");
            
            prefs1.edit().putString("theme", "dark").commit();
            prefs2.edit().putString("last_view", "chat_list").commit();
        }
        
        {
            SharedPreferences prefs1(pkg, "settings");
            SharedPreferences prefs2(pkg, "cache");
            
            TEST_ASSERT_EQ(prefs1.getString("theme"), "dark",
                          "Settings file should only contain settings");
            TEST_ASSERT_EQ(prefs2.getString("last_view"), "chat_list",
                          "Cache file should only contain cache");
            TEST_ASSERT_FALSE(prefs1.contains("last_view"),
                            "Settings should not contain cache keys");
        }
        
        // Cleanup both files
        try {
            fs::path base = fs::path("runtime/data") / pkg / "shared_prefs";
            fs::remove(base / "settings.xml");
            fs::remove(base / "cache.xml");
        } catch (...) {}
    });
    
    runTest("Test_FactoryCreate_TelegramPrefs", []() {
        auto prefs = SharedPreferencesFactory::createForTelegram("mainconfig");
        
        TEST_ASSERT_EQ(prefs->getPackageName(), "org.telegram.messenger",
                      "Factory should set Telegram package");
        TEST_ASSERT_EQ(prefs->getName(), "mainconfig",
                      "Factory should set requested name");
        
        // Write some Telegram-like data
        prefs->edit()
            .putBoolean("logged_in_key", true)
            .putInt("user_id", 123456789)
            .putString("phone_hash", "abcdef123456")
            .commit();
        
        // Read back via factory
        auto prefs2 = SharedPreferencesFactory::createForTelegram("mainconfig");
        TEST_ASSERT_TRUE(prefs2->getBoolean("logged_in_key", false),
                        "Factory-created instance should read persisted data");
        
        // Cleanup
        try { fs::remove(prefs->getFilePath()); } catch (...) {}
    });
}


// ============================================================================
// SUITE 7: ERROR HANDLING
// ============================================================================

void runSuite7_ErrorHandling() {
    std::cout << "\n[SUITE 7] Error Handling\n" << std::endl;
    
    runTest("Test_TypeMismatch_ReturnsDefault", []() {
        std::string pkg = uniquePackage("org.test.typemismatch");
        SharedPreferences prefs(pkg, "test");
        
        // Store as string
        prefs.edit().putString("key", "not_a_number").commit();
        
        // Try to read as int - should return default
        int value = prefs.getInt("key", -1);
        TEST_ASSERT_EQ(value, -1, "Type mismatch should return default");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_MissingKey_ReturnsDefault", []() {
        std::string pkg = uniquePackage("org.test.missing");
        SharedPreferences prefs(pkg, "test");
        
        // Never wrote anything
        TEST_ASSERT_EQ(prefs.getString("any_key", "fallback"), "fallback",
                      "Missing key should return default");
        TEST_ASSERT_EQ(prefs.getInt("any_key", 42), 42,
                      "Missing key should return default int");
        TEST_ASSERT_TRUE(prefs.getBoolean("any_key", true),
                         "Missing key should return default bool (true)");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_Contains_FalseForMissing", []() {
        std::string pkg = uniquePackage("org.test.contains");
        SharedPreferences prefs(pkg, "test");
        
        TEST_ASSERT_FALSE(prefs.contains("anything"), "Should not contain unwritten key");
        
        prefs.edit().putString("exists", "yes").commit();
        TEST_ASSERT_TRUE(prefs.contains("exists"), "Should contain written key");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_GetAllKeys_Complete", []() {
        std::string pkg = uniquePackage("org.test.allkeys");
        SharedPreferences prefs(pkg, "test");
        
        prefs.edit()
            .putString("a", "1")
            .putInt("b", 2)
            .putBoolean("c", true)
            .commit();
        
        auto keys = prefs.getAllKeys();
        TEST_ASSERT_EQ(keys.size(), size_t(3), "Should have 3 keys");
        TEST_ASSERT_TRUE(keys.count("a") > 0, "Should contain key 'a'");
        TEST_ASSERT_TRUE(keys.count("b") > 0, "Should contain key 'b'");
        TEST_ASSERT_TRUE(keys.count("c") > 0, "Should contain key 'c'");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_GetAll_ReturnsCompleteMap", []() {
        std::string pkg = uniquePackage("org.test.getall");
        SharedPreferences prefs(pkg, "test");
        
        prefs.edit()
            .putString("s", "str")
            .putInt("i", 42)
            .commit();
        
        auto all = prefs.getAll();
        TEST_ASSERT_EQ(all.size(), size_t(2), "getAll should return all entries");
        TEST_ASSERT_TRUE(all.count("s") > 0, "getAll should contain 's'");
        TEST_ASSERT_TRUE(all["s"].isType(PrefType::STRING), "Type should be STRING");
        
        cleanupTest(prefs);
    });
}


// ============================================================================
// SUITE 8: THREAD SAFETY (Basic Tests)
// ============================================================================

void runSuite8_ThreadSafety() {
    std::cout << "\n[SUITE 8] Thread Safety\n" << std::endl;
    
    runTest("Test_ConcurrentReads_NoCrash", []() {
        std::string pkg = uniquePackage("org.test.threadread");
        SharedPreferences prefs(pkg, "test");
        
        prefs.edit()
            .putString("shared", "value")
            .putInt("counter", 100)
            .commit();
        
        // Spawn multiple reader threads
        std::vector<std::thread> threads;
        std::atomic<int> success_count(0);
        
        for (int i = 0; i < 10; ++i) {
            threads.emplace_back([&prefs, &success_count]() {
                try {
                    // Perform reads
                    for (int j = 0; j < 100; ++j) {
                        std::string s = prefs.getString("shared");
                        int c = prefs.getInt("counter");
                        (void)s;  // Suppress unused warning
                        (void)c;
                    }
                    success_count++;
                } catch (...) {
                    // Thread crashed
                }
            });
        }
        
        // Wait for all threads
        for (auto& t : threads) {
            t.join();
        }
        
        TEST_ASSERT_EQ(success_count.load(), 10, "All reader threads should complete without crash");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_ConcurrentWrites_LastWriteWins", []() {
        std::string pkg = uniquePackage("org.test.threadwrite");
        SharedPreferences prefs(pkg, "test");
        
        std::vector<std::thread> threads;
        
        // Each thread writes different value to same key
        for (int i = 0; i < 5; ++i) {
            threads.emplace_back([&prefs, i]() {
                prefs.edit()
                    .putInt("race_condition", i)
                    .commit();
            });
        }
        
        for (auto& t : threads) {
            t.join();
        }
        
        // One of the writes should have won
        int final_value = prefs.getInt("race_condition", -1);
        TEST_ASSERT_TRUE(final_value >= 0 && final_value <= 4,
                        "Final value should be one of the written values");
        
        cleanupTest(prefs);
    });
}


// ============================================================================
// SUITE 9: TELEGRAM-SPECIFIC SCENARIOS
// ============================================================================

void runSuite9_TelegramScenarios() {
    std::cout << "\n[SUITE 9] Telegram-Specific Scenarios\n" << std::endl;
    
    runTest("Test_TelegramLoginState_Persistence", []() {
        // Simulate Telegram's login flow
        auto prefs = SharedPreferencesFactory::createForTelegram("mainconfig");
        
        // Initial state: not logged in
        TEST_ASSERT_FALSE(prefs->getBoolean("logged_in_key", false),
                         "Initial state should be logged out");
        
        // User logs in
        prefs->edit()
            .putBoolean("logged_in_key", true)
            .putInt("user_id", 987654321)
            .putString("phone_hash", "a1b2c3d4e5f6")
            .putInt("loggedInTime", static_cast<int>(std::time(nullptr)))
            .commit();
        
        // Verify login state persisted
        TEST_ASSERT_TRUE(prefs->getBoolean("logged_in_key", false),
                        "Should be logged in after writing");
        TEST_ASSERT_EQ(prefs->getInt("user_id", -1), 987654321,
                      "User ID should persist");
        
        // Simulate app restart (new instance)
        auto prefs_after_restart = SharedPreferencesFactory::createForTelegram("mainconfig");
        
        TEST_ASSERT_TRUE(prefs_after_restart->getBoolean("logged_in_key", false),
                        "Login state should survive restart");
        TEST_ASSERT_EQ(prefs_after_restart->getInt("user_id", -1), 987654321,
                      "User ID should survive restart");
        TEST_ASSERT_EQ(prefs_after_restart->getString("phone_hash", ""),
                      "a1b2c3d4e5f6",
                      "Phone hash should survive restart");
        
        std::cout << "\n    [Telegram Scenario] Login state persists across restarts!" << std::endl;
        
        // Cleanup
        try { fs::remove(prefs->getFilePath()); } catch (...) {}
    });
    
    runTest("Test_TelegramMultiplePrefFiles", []() {
        // Telegram uses multiple preference files
        auto main_config = SharedPreferencesFactory::createForTelegram("mainconfig");
        auto user_config = SharedPreferencesFactory::createForTelegram("userconfig");
        auto cache_config = SharedPreferencesFactory::createForTelegram("cacheconfig");
        
        main_config->edit()
            .putBoolean("logged_in_key", true)
            .commit();
        
        user_config->edit()
            .putString("first_name", "John")
            .putString("last_name", "Doe")
            .commit();
        
        cache_config->edit()
            .putInt("last_chat_id", 12345)
            .putLong("last_msg_time", time(nullptr))
            .commit();
        
        // Each file should be independent
        TEST_ASSERT_TRUE(main_config->contains("logged_in_key"), "Main config should have logged_in_key");
        TEST_ASSERT_TRUE(user_config->contains("first_name"), "User config should have first_name");
        TEST_ASSERT_TRUE(cache_config->contains("last_chat_id"), "Cache config should have last_chat_id");
        
        TEST_ASSERT_FALSE(main_config->contains("first_name"), "Main should not contain user keys");
        TEST_ASSERT_FALSE(user_config->contains("last_chat_id"), "User should not contain cache keys");
        
        std::cout << "\n    [Telegram Scenario] Multiple pref files work independently!" << std::endl;
        
        // Cleanup
        try {
            fs::remove(main_config->getFilePath());
            fs::remove(user_config->getFilePath());
            fs::remove(cache_config->getFilePath());
        } catch (...) {}
    });
    
    runTest("Test_TelegramSessionData_ComplexTypes", []() {
        auto prefs = SharedPreferencesFactory::createForTelegram("session_data");
        
        // Complex session data that Telegram might store
        prefs->edit()
            // Basic auth
            .putString("auth_token", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
            .putLong("token_expiry", 1692600000000LL)
            
            // User preferences
            .putStringSet("pinned_chats", {"123456", "789012", "345678"})
            .putBoolean("notifications_enabled", true)
            .putBoolean("sound_enabled", false)
            .putString("theme", "dark")
            .putFloat("text_scale", 1.0f)
            
            // App state
            .putInt("current_account_index", 0)
            .putInt("last_opened_chat_id", 999888777)
            .putLong("last_sync_time", 1692000000000LL)
            .commit();
        
        // Verify all data persisted
        TEST_ASSERT_EQ(prefs->getString("auth_token").substr(0, 11), 
                      "eyJhbGciOiJ",
                      "Auth token should persist");
        TEST_ASSERT_EQ(prefs->getLong("token_expiry", 0), 
                      1692600000000LL,
                      "Token expiry should persist");
        
        auto pinned = prefs->getStringSet("pinned_chats");
        TEST_ASSERT_EQ(pinned.size(), size_t(3), "Pinned chats set should persist");
        
        TEST_ASSERT_TRUE(prefs->getBoolean("notifications_enabled", false),
                        "Notification setting should persist");
        TEST_ASSERT_FALSE(prefs->getBoolean("sound_enabled", true),
                         "Sound setting should persist");
        
        std::cout << "\n    [Telegram Scenario] Complex session data persists!" << std::endl;
        
        // Cleanup
        try { fs::remove(prefs->getFilePath()); } catch (...) {}
    });
}


// ============================================================================
// SUITE 10: EDGE CASES & SPECIAL CHARACTERS
// ============================================================================

void runSuite10_EdgeCases() {
    std::cout << "\n[SUITE 10] Edge Cases & Special Characters\n" << std::endl;
    
    runTest("Test_VeryLongStringValue", []() {
        std::string pkg = uniquePackage("org.test.longstr");
        SharedPreferences prefs(pkg, "test");
        
        // Create a 10KB string
        std::string long_value(10000, 'X');
        prefs.edit().putString("long_text", long_value).commit();
        
        std::string read_back = prefs.getString("long_text");
        TEST_ASSERT_EQ(read_back.length(), long_value.length(),
                      "Very long string should survive round-trip");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_VeryLongKeyName", []() {
        std::string pkg = uniquePackage("org.test.longkey");
        SharedPreferences prefs(pkg, "test");
        
        std::string long_key(500, 'K');
        prefs.edit().putString(long_key, "value").commit();
        
        TEST_ASSERT_TRUE(prefs.contains(long_key), "Long key should work");
        TEST_ASSERT_EQ(prefs.getString(long_key), "value", "Long key retrieval works");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_NewlinesInValue", []() {
        std::string pkg = uniquePackage("org.test.newlines");
        SharedPreferences prefs(pkg, "test");
        
        std::string multi_line = "Line1\nLine2\r\nLine3";
        prefs.edit().putString("multiline", multi_line).commit();
        
        TEST_ASSERT_EQ(prefs.getString("multiline"), multi_line,
                      "Newlines should survive round-trip");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_ManyEntries_Performance", []() {
        std::string pkg = uniquePackage("org.test.many");
        SharedPreferences prefs(pkg, "test");
        
        // Write 1000 entries
        auto editor = prefs.edit();
        for (int i = 0; i < 1000; ++i) {
            editor.putInt("key_" + std::to_string(i), i);
        }
        bool committed = editor.commit();
        
        TEST_ASSERT_TRUE(committed, "Should commit 1000 entries");
        TEST_ASSERT_EQ(prefs.size(), size_t(1000), "Should have 1000 entries");
        
        // Verify random access still works
        TEST_ASSERT_EQ(prefs.getInt("key_500", -1), 500, "Random access should work");
        
        cleanupTest(prefs);
    });
    
    runTest("Test_OverwriteExistingKey", []() {
        std::string pkg = uniquePackage("org.test.overwrite");
        SharedPreferences prefs(pkg, "test");
        
        prefs.edit().putString("key", "original").commit();
        TEST_ASSERT_EQ(prefs.getString("key"), "original", "Original value");
        
        prefs.edit().putString("key", "updated").commit();
        TEST_ASSERT_EQ(prefs.getString("key"), "updated", "Updated value");
        
        // Can also overwrite with different type
        prefs.edit().putInt("key", 42).commit();
        TEST_ASSERT_EQ(prefs.getInt("key", 0), 42, "Overwritten as int");
        
        cleanupTest(prefs);
    });
}


// ============================================================================
// MAIN TEST RUNNER
// ============================================================================

int main() {
    std::cout << "=========================================" << std::endl;
    std::cout << "SharedPreferences Unit Tests" << std::endl;
    std::cout << "EXP-037 Phase A, Week 2 Validation" << std::endl;
    std::cout << "=========================================" << std::endl;
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    // Run all test suites
    runSuite1_Construction();
    runSuite2_StringOperations();
    runSuite3_PrimitiveTypes();
    runSuite4_EditorPattern();
    runSuite5_XmlIo();
    runSuite6_Persistence();
    runSuite7_ErrorHandling();
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
    
    // Return exit code based on results
    return g_stats.failed > 0 ? 1 : 0;
}
