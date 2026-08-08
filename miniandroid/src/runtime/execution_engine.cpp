/*
 * MiniAndroid Runtime v0.1 - Execution Engine Implementation
 * EXP-001: HelloWorld Loader
 */

#include "execution_engine.h"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <chrono>

namespace miniandroid {
namespace runtime {

namespace fs = std::filesystem;

ExecutionEngine::ExecutionEngine() {
}

ExecutionEngine::~ExecutionEngine() {
}

ExecutionResult ExecutionEngine::execute(const std::string& path) {
    return execute(path, ExecutionConfig{});
}

ExecutionResult ExecutionEngine::execute(const std::string& path, const ExecutionConfig& config) {
    ExecutionResult result;
    
    // Start tracing session
    trace_engine_.start_session();
    // Note: verbose logging handled by individual parsers
    
    diagnostics::ScopedTimer timer(trace_engine_, "TotalExecution");
    
    // Execute pipeline stages
    bool success = true;
    
    success &= stage_load_apk(path, result);
    if (success) success &= stage_parse_dex(result);
    if (success) success &= stage_initialize_runtime(result, config);
    if (success) success &= stage_load_classes(result);
    if (success) success &= stage_execute_application(result, config);
    if (success) success &= stage_render_frame(result, config);
    if (success) success &= stage_capture_output(result, config);
    
    // Always try to generate reports
    stage_generate_reports(result, config);
    
    // Determine final status
    if (success && result.status == ExecutionStatus::SUCCESS) {
        result.status_message = "Execution completed successfully";
    } else if (result.metrics.errors_count > 0) {
        result.status = ExecutionStatus::FAILURE;
        result.status_message = "Execution failed with errors";
    } else {
        result.status = ExecutionStatus::PARTIAL_SUCCESS;
        result.status_message = "Partial execution completed";
    }
    
    // Copy metrics
    result.metrics = trace_engine_.get_metrics();
    
    // End session
    trace_engine_.end_session();
    
    return result;
}

bool ExecutionEngine::stage_load_apk(const std::string& path, ExecutionResult& result) {
    trace_engine_.info("ExecutionEngine", "stage_load_apk", "Loading APK: " + path);
    
    apk_parser_.set_verbose(true);  // Always verbose for now
    
    result.apk_info = apk_parser_.parse(path);
    
    if (!result.apk_info.is_valid) {
        set_error("APK parsing failed: " + result.apk_info.validation_error);
        trace_engine_.record_error("PARSE_ERROR", result.apk_info.validation_error,
                                   "ApkParser", "parse");
        return false;
    }
    
    trace_engine_.info("ExecutionEngine", "stage_load_apk",
                       "Package: " + result.apk_info.package_name +
                       ", Main Activity: " + result.apk_info.main_activity);
    
    return true;
}

bool ExecutionEngine::stage_parse_dex( ExecutionResult& result) {
    trace_engine_.info("ExecutionEngine", "stage_parse_dex", "Parsing DEX files");
    
    if (result.apk_info.dex_files.empty()) {
        trace_engine_.warning("ExecutionEngine", "stage_parse_dex", 
                              "No DEX files found in APK");
        // Continue anyway - might be native-only
        return true;
    }
    
    // Parse first DEX file (classes.dex)
    std::string dex_path = result.apk_info.apk_path;  // Will extract from APK
    
    // Extract classes.dex from APK
    auto dex_data = apk_parser_.extract_entry(dex_path, "classes.dex");
    
    if (dex_data.empty()) {
        set_error("Failed to extract classes.dex from APK");
        trace_engine_.record_error("DEX_ERROR", "Cannot extract classes.dex",
                                   "DexParser", "parse");
        return false;
    }
    
    result.dex_report = dex_parser_.parse_data(dex_data, "classes.dex");
    
    if (!result.dex_report.is_valid) {
        set_error("DEX parsing failed: " + result.dex_report.validation_error);
        trace_engine_.record_error("PARSE_ERROR", result.dex_report.validation_error,
                                   "DexParser", "parse");
        return false;
    }
    
    trace_engine_.info("ExecutionEngine", "stage_parse_dex",
                       "Parsed " + std::to_string(result.dex_report.classes_count) +
                       " classes, " + std::to_string(result.dex_report.methods_count) +
                       " methods");
    
    return true;
}

bool ExecutionEngine::stage_initialize_runtime(ExecutionResult& result, const ExecutionConfig& config) {
    trace_engine_.info("ExecutionEngine", "stage_initialize_runtime", "Initializing runtime");
    
    // Allocate framebuffer
    size_t buffer_size = static_cast<size_t>(config.screen_width * config.screen_height * 4);  // RGBA
    framebuffer_.resize(buffer_size, 0xFF);  // Initialize to white-ish
    
    // Clear framebuffer with background color
    uint8_t r = (config.background_color >> 16) & 0xFF;
    uint8_t g = (config.background_color >> 8) & 0xFF;
    uint8_t b = config.background_color & 0xFF;
    uint8_t a = (config.background_color >> 24) & 0xFF;
    
    for (size_t i = 0; i < buffer_size; i += 4) {
        framebuffer_[i] = r;
        framebuffer_[i+1] = g;
        framebuffer_[i+2] = b;
        framebuffer_[i+3] = a;
    }
    
    setup_api_tracing();
    
    trace_engine_.info("ExecutionEngine", "stage_initialize_runtime",
                       "Framebuffer allocated: " + std::to_string(config.screen_width) + 
                       "x" + std::to_string(config.screen_height));
    
    return true;
}

bool ExecutionEngine::stage_load_classes(ExecutionResult& result) {
    trace_engine_.info("ExecutionEngine", "stage_load_classes", "Loading class definitions");
    
    // In v0.1, we don't actually load real classes - we use stubs
    // This stage would be expanded in future versions
    
    if (result.dex_report.classes.empty()) {
        trace_engine_.warning("ExecutionEngine", "stage_load_classes",
                              "No classes in DEX report");
    } else {
        // Log class information
        for (const auto& cls : result.dex_report.classes) {
            trace_engine_.debug("ExecutionEngine", "stage_load_classes",
                               "Found class: " + cls.name + 
                               " extends " + cls.superclass_name +
                               " (" + std::to_string(cls.all_methods().size()) + " methods)");
        }
    }
    
    return true;
}

bool ExecutionEngine::stage_execute_application(ExecutionResult& result, const ExecutionConfig& config) {
    trace_engine_.info("ExecutionEngine", "stage_execute_application", "Executing application lifecycle");
    
    // Create Activity instance
    result.activity = std::make_shared<api::Activity>();
    result.activity->set_package_name(result.apk_info.package_name);
    
    // Simulate lifecycle if configured
    if (config.simulate_lifecycle) {
        // Create content view
        if (config.simulated_text.empty()) {
            // Try to create from what we know about the app
            result.content_view = create_view_from_layout(result.dex_report);
        } else {
            result.content_view = create_hello_world_view(config);
        }
        
        // Set content view on activity
        if (result.content_view) {
            result.activity->setContentView(result.content_view);
        }
        
        // Execute lifecycle methods (these will be traced)
        api::Bundle* null_bundle = nullptr;
        result.activity->onCreate(null_bundle);
        result.activity->onStart();
        result.activity->onResume();
    }
    
    result.status = ExecutionStatus::SUCCESS;
    
    trace_engine_.info("ExecutionEngine", "stage_execute_application",
                       "Lifecycle simulation complete");
    
    return true;
}

bool ExecutionEngine::stage_render_frame( ExecutionResult& result, const ExecutionConfig& config) {
    trace_engine_.info("ExecutionEngine", "stage_render_frame", "Rendering frame");
    
    if (!result.content_view) {
        trace_engine_.warning("ExecutionEngine", "stage_render_frame", "No content view to render");
        return true;  // Not fatal
    }
    
    // Create canvas with framebuffer
    api::Canvas canvas(framebuffer_.data(), config.screen_width, config.screen_height);
    
    // Measure and layout
    int width_spec = config.screen_width;  // EXACTLY mode
    int height_spec = config.screen_height;
    
    result.content_view->measure(width_spec, height_spec);
    result.content_view->layout(0, 0, config.screen_width, config.screen_height);
    
    // Draw
    result.content_view->draw(canvas);
    
    trace_engine_.increment_frame_count();
    
    trace_engine_.info("ExecutionEngine", "stage_render_frame", "Frame rendered successfully");
    
    return true;
}

bool ExecutionEngine::stage_capture_output( ExecutionResult& result, const ExecutionConfig& config) {
    trace_engine_.info("ExecutionEngine", "stage_capture_output", "Capturing output");
    
    if (!config.generate_screenshot) {
        trace_engine_.info("ExecutionEngine", "stage_capture_output", "Screenshot generation disabled");
        return true;
    }
    
    // Ensure output directory exists
    fs::create_directories(config.output_directory);
    
    // Generate screenshot filename
    std::string screenshot_path = config.output_directory + "/screenshot.png";
    result.screenshot_path = screenshot_path;
    
    // Write raw RGBA data as PPM (simple format, can convert later)
    // For production, would use libpng or stb_image_write
    std::string ppm_path = config.output_directory + "/screenshot.ppm";
    std::ofstream ppm_file(ppm_path, std::ios::binary);
    
    if (ppm_file.is_open()) {
        ppm_file << "P6\n" << config.screen_width << " " << config.screen_height << "\n255\n";
        
        for (size_t i = 0; i < framebuffer_.size(); i += 4) {
            ppm_file.put(framebuffer_[i]);     // R
            ppm_file.put(framebuffer_[i+1]);   // G
            ppm_file.put(framebuffer_[i+2]);   // B
            // Skip Alpha for PPM
        }
        
        ppm_file.close();
        
        // Log screenshot info
        trace_engine_.log_screenshot(ppm_path, config.screen_width, config.screen_height,
                                     framebuffer_.size());
        
        // Also create a simple PNG placeholder note
        std::string note_path = config.output_directory + "/screenshot_note.txt";
        std::ofstream note(note_path);
        note << "Screenshot saved as PPM: " << ppm_path << "\n";
        note << "Resolution: " << config.screen_width << "x" << config.screen_height << "\n";
        note << "Convert to PNG using: convert " << ppm_path << " screenshot.png\n";
        note.close();
        
        trace_engine_.info("ExecutionEngine", "stage_capture_output",
                          "Screenshot saved to: " + ppm_path);
    } else {
        set_error("Failed to write screenshot file");
        trace_engine_.record_error("IO_ERROR", "Cannot write screenshot file",
                                   "ExecutionEngine", "stage_capture_output");
        return false;
    }
    
    return true;
}

bool ExecutionEngine::stage_generate_reports( ExecutionResult& result, const ExecutionConfig& config) {
    trace_engine_.info("ExecutionEngine", "stage_generate_reports", "Generating reports");
    
    if (!config.generate_reports) {
        return true;
    }
    
    // Write all report files
    std::string status_str = (result.status == ExecutionStatus::SUCCESS) ? "SUCCESS" : "FAILURE";
    
    bool written = trace_engine_.write_reports(
        config.output_directory,
        result.apk_info.package_name.empty() ? "UnknownApp" : result.apk_info.package_name,
        status_str,
        result.apk_info.apk_path
    );
    
    if (written) {
        result.report_path = config.output_directory + "/report.md";
        trace_engine_.info("ExecutionEngine", "stage_generate_reports",
                          "Reports generated in: " + config.output_directory);
    }
    
    return written;
}

void ExecutionEngine::setup_api_tracing() {
    // The trace engine is already set up
    // In a full implementation, we'd connect API stubs to this tracer
}

std::shared_ptr<api::View> ExecutionEngine::create_hello_world_view(const ExecutionConfig& config) {
    trace_engine_.info("ExecutionEngine", "create_hello_world_view", "Creating HelloWorld view");
    
    // Create a simple TextView with "Hello MiniAndroid"
    auto text_view = std::make_shared<api::TextView>();
    text_view->setText("Hello MiniAndroid");
    text_view->setTextColor(0xFF000000);  // Black text
    text_view->setTextSize(48.0f);
    text_view->setId(1);  // Give it an ID
    
    // Position it (centered roughly)
    int x = config.screen_width / 4;
    int y = config.screen_height / 3;
    int w = config.screen_width / 2;
    int h = 100;
    
    text_view->layout(x, y, x + w, y + h);
    
    return text_view;
}

std::shared_ptr<api::View> ExecutionEngine::create_view_from_layout(const dex::DexReport& report) {
    trace_engine_.info("ExecutionEngine", "create_view_from_layout", "Creating view from DEX analysis");
    
    // Look for clues about what the app displays
    // This is heuristic-based for v0.1
    
    std::string display_text = "Hello MiniAndroid";  // Default
    
    // Search for string constants that might be displayed
    for (const auto& str : report.strings) {
        // Look for common patterns like "Hello", text that looks like UI strings
        if (str.find("Hello") != std::string::npos ||
            str.find("hello") != std::string::npos ||
            str.length() > 5 && str.length() < 100 &&
            std::all_of(str.begin(), str.end(), [](char c) { 
                return std::isalnum(c) || std::isspace(c); 
            })) {
            display_text = str;
            break;
        }
    }
    
    // Create default hello world view
    ExecutionConfig default_config;
    default_config.simulated_text = display_text;
    return create_hello_world_view(default_config);
}

} // namespace runtime
} // namespace miniandroid
