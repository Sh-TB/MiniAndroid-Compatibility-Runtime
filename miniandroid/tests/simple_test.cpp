/*
 * MiniAndroid Runtime v0.1 - Simple Test (No GTest dependency)
 * EXP-001: HelloWorld Loader
 */

#include <iostream>
#include <cassert>

// Include headers we want to test
#include "apk/apk_parser.h"
#include "dex/dex_parser.h"
#include "api/android_stubs.h"
#include "diagnostics/trace_engine.h"

using namespace miniandroid;

void test_api_stubs() {
    std::cout << "[TEST] Testing API Stubs..." << std::endl;
    
    // Test Bundle
    api::Bundle bundle;
    bundle.putString("key1", "value1");
    bundle.putInt("key2", 42);
    
    assert(bundle.getString("key1") == "value1");
    assert(bundle.getInt("key2") == 42);
    assert(bundle.getInt("nonexistent", 10) == 10);
    assert(bundle.isEmpty() == false);
    
    std::cout << "  [PASS] Bundle operations" << std::endl;
    
    // Test TextView
    api::TextView text_view;
    text_view.setText("Hello World");
    text_view.setTextColor(0xFF000000);
    text_view.setTextSize(24.0f);
    
    assert(text_view.getText() == "Hello World");
    
    std::cout << "  [PASS] TextView operations" << std::endl;
    
    // Test Activity
    api::Activity activity;
    activity.set_package_name("com.test.app");
    
    assert(activity.getPackageName() == "com.test.app");
    
    std::cout << "  [PASS] Activity operations" << std::endl;
}

void test_trace_engine() {
    std::cout << "[TEST] Testing Trace Engine..." << std::endl;
    
    diagnostics::TraceEngine engine;
    
    engine.start_session("test-session-001");
    
    engine.info("TestClass", "testMethod", "Test info message");
    engine.debug("TestClass", "testMethod", "Debug message");
    engine.warning("TestClass", "testMethod", "Warning message");
    engine.error("TestClass", "testMethod", "Error message");
    
    engine.record_error("TEST_ERROR", "This is a test error", 
                        "TestClass", "testMethod", false);
    
    engine.increment_frame_count();
    engine.increment_frame_count();
    
    auto& metrics = engine.get_metrics();
    assert(engine.get_traces().size() >= 4);  // At least our trace calls
    assert(metrics.frames_rendered == 2);
    assert(metrics.errors_count >= 1);
    
    auto class_summary = engine.get_call_summary_by_class();
    assert(!class_summary.empty());
    
    auto method_summary = engine.get_call_summary_by_method();
    assert(!method_summary.empty());
    
    // Generate reports
    std::string report = engine.generate_markdown_report("com.test.app", "SUCCESS", "/path/to/test.apk");
    assert(report.find("MiniAndroid Execution Report") != std::string::npos);
    assert(report.find("SUCCESS") != std::string::npos);
    
    nlohmann::json api_trace = engine.generate_api_trace_json();
    assert(api_trace["session_id"] == "test-session-001");
    assert(api_trace["total_calls"] >= 4);
    
    std::string crash_log = engine.generate_crash_log();
    assert(crash_log.find("TEST_ERROR") != std::string::npos);
    
    engine.end_session();
    
    std::cout << "  [PASS] Trace Engine operations" << std::endl;
}

void test_paint_and_canvas() {
    std::cout << "[TEST] Testing Paint & Canvas..." << std::endl;
    
    // Create framebuffer
    int width = 100;
    int height = 100;
    std::vector<uint8_t> buffer(width * height * 4, 0x00);  // Black
    
    // Create canvas
    api::Canvas canvas(buffer.data(), width, height);
    
    // Fill with white
    canvas.drawColor(0xFFFFFFFF);
    
    // Check that buffer is now white (at least first pixel)
    assert(buffer[0] == 0xFF);  // R
    assert(buffer[1] == 0xFF);  // G
    assert(buffer[2] == 0xFF);  // B
    assert(buffer[3] == 0xFF);  // A
    
    // Draw text area
    api::Paint paint;
    paint.setColor(0xFF000000);  // Black
    paint.setTextSize(16.0f);
    
    canvas.drawText("Test", 10.0f, 50.0f, paint);
    
    // Draw rect
    canvas.drawRect(5.0f, 5.0f, 20.0f, 20.0f, paint);
    
    std::cout << "  [PASS] Paint & Canvas operations" << std::endl;
}

void test_view_hierarchy() {
    std::cout << "[TEST] Testing View Hierarchy..." << std::endl;
    
    // Create view group
    auto root = std::make_shared<api::ViewGroup>();
    
    // Add child views
    auto text1 = std::make_shared<api::TextView>();
    text1->setText("Text 1");
    text1->setId(1);
    
    auto text2 = std::make_shared<api::TextView>();
    text2->setText("Text 2");
    text2->setId(2);
    
    root->addView(text1);
    root->addView(text2);
    
    assert(root->getChildCount() == 2);
    assert(root->getChildAt(0) == text1);
    assert(root->getChildAt(1) == text2);
    
    // Remove view
    root->removeView(text1);
    assert(root->getChildCount() == 1);
    
    std::cout << "  [PASS] View hierarchy operations" << std::endl;
}

int main() {
    std::cout << "=========================================" << std::endl;
    std::cout << "MiniAndroid Runtime v0.1 - Unit Tests" << std::endl;
    std::cout << "EXP-001: HelloWorld Loader" << std::endl;
    std::cout << "=========================================\n" << std::endl;
    
    int passed = 0;
    int failed = 0;
    
    try {
        test_api_stubs();
        passed++;
    } catch (const std::exception& e) {
        std::cerr << "  [FAIL] API Stubs: " << e.what() << std::endl;
        failed++;
    }
    
    try {
        test_trace_engine();
        passed++;
    } catch (const std::exception& e) {
        std::cerr << "  [FAIL] Trace Engine: " << e.what() << std::endl;
        failed++;
    }
    
    try {
        test_paint_and_canvas();
        passed++;
    } catch (const std::exception& e) {
        std::cerr << "  [FAIL] Paint/Canvas: " << e.what() << std::endl;
        failed++;
    }
    
    try {
        test_view_hierarchy();
        passed++;
    } catch (const std::exception& e) {
        std::cerr << "  [FAIL] View Hierarchy: " << e.what() << std::endl;
        failed++;
    }
    
    std::cout << "\n=========================================" << std::endl;
    std::cout << "Test Results: " << passed << " passed, " << failed << " failed" << std::endl;
    std::cout << "=========================================" << std::endl;
    
    return failed > 0 ? 1 : 0;
}
