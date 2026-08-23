/*
 * MiniAndroid Runtime v0.1 - Execution Engine
 * EXP-001: HelloWorld Loader
 * 
 * Main runtime engine that orchestrates APK loading, DEX parsing,
 * API stub execution, and rendering.
 */

#ifndef MINIANDROID_EXECUTION_ENGINE_H
#define MINIANDROID_EXECUTION_ENGINE_H

#include <string>
#include <vector>
#include <memory>
#include <map>
#include <functional>

#include "apk/apk_parser.h"
#include "dex/dex_parser.h"
#include "dex/dalvik_engine.h"  // EXP-031: Real Dalvik engine
#include "api/android_stubs.h"
#include "diagnostics/trace_engine.h"
// EXP-086 Phase 7 (B4 FIX): ShadowRegistry for Handler/Looper dispatch
#include "framework/shadow_registry.h"

namespace miniandroid {
namespace runtime {

// Execution mode selection (EXP-031)
enum class ExecutionMode {
    LEGACY,           // Old behavior - simulated lifecycle (for regression)
    REAL_DALVIK       // New path - real bytecode interpretation (default for EXP-031)
};

// Execution source tracking (EXP-031 Golden Debug Protocol)
enum class ExecutionSource {
    HOST_SHORTCUT,              // Legacy C++ direct call (fake lifecycle)
    REAL_DALVIK_INTERPRETER,    // Real DEX opcode execution
    UNKNOWN                     // Source not tracked (legacy data)
};

// Execution result status
enum class ExecutionStatus {
    SUCCESS,
    PARTIAL_SUCCESS,  // Some features worked
    FAILURE,
    CRASH
};

// Configuration for execution
struct ExecutionConfig {
    // Output settings
    std::string output_directory = "./run";
    
    // Rendering settings
    int screen_width = 1080;
    int screen_height = 1920;
    uint32_t background_color = 0xFFFFFFFF;  // White
    
    // Tracing settings
    bool verbose_logging = false;
    bool generate_screenshot = true;
    bool generate_reports = true;
    
    // EXP-031: Execution mode (CRITICAL - determines real vs fake path)
    ExecutionMode execution_mode = ExecutionMode::REAL_DALVIK;  // Default to REAL!
    
    // Legacy simulation settings (only used in LEGACY mode)
    bool simulate_lifecycle = true;
    std::string simulated_text = "";  // Empty = try to extract from APK
};

// Final result of execution
struct ExecutionResult {
    ExecutionStatus status = ExecutionStatus::FAILURE;
    std::string status_message;
    
    // Parsed data
    apk::ApkInfo apk_info;
    dex::DexReport dex_report;
    
    // Runtime objects
    std::shared_ptr<api::Activity> activity;
    std::shared_ptr<api::View> content_view;
    
    // Output files generated
    std::string screenshot_path;
    std::string report_path;
    
    // Metrics from diagnostics
    diagnostics::ExecutionMetrics metrics;
};

/**
 * Main Execution Engine
 * 
 * This is the core orchestrator that:
 * 1. Parses the APK file
 * 2. Extracts and parses DEX data
 * 3. Creates Android object instances
 * 4. Simulates lifecycle
 * 5. Renders output
 * 6. Generates reports
 */
class ExecutionEngine {
public:
    ExecutionEngine();
    ~ExecutionEngine();
    
    /**
     * Execute an APK file
     * @param path Path to .apk file
     * @param config Execution configuration
     * @return ExecutionResult with all details
     */
    ExecutionResult execute(const std::string& path, const ExecutionConfig& config = {});
    
    /**
     * Execute with default configuration
     */
    ExecutionResult execute(const std::string& path);
    
    /**
     * Get last error message
     */
    std::string get_last_error() const { return last_error_; }
    
    /**
     * Access trace engine for custom tracing
     */
    diagnostics::TraceEngine& get_trace_engine() { return trace_engine_; }

    // EXP-086 Phase 7 (B4 FIX): Allow caller to set ShadowRegistry
    // so Handler/Looper dispatch is wired up during execute_apk.
    void set_shadow_registry(framework::ShadowRegistry* reg) { shadow_registry_ = reg; }

private:
    // Pipeline stages
    bool stage_load_apk(const std::string& path, ExecutionResult& result);
    bool stage_parse_dex(ExecutionResult& result);
    bool stage_initialize_runtime(ExecutionResult& result, const ExecutionConfig& config);
    bool stage_load_classes(ExecutionResult& result);
    bool stage_execute_application(ExecutionResult& result, const ExecutionConfig& config);
    bool stage_render_frame(ExecutionResult& result, const ExecutionConfig& config);
    bool stage_capture_output(ExecutionResult& result, const ExecutionConfig& config);
    bool stage_generate_reports(ExecutionResult& result, const ExecutionConfig& config);
    
    // Helper methods
    void setup_api_tracing();
    std::shared_ptr<api::View> create_hello_world_view(const ExecutionConfig& config);
    std::shared_ptr<api::View> create_view_from_layout(const dex::DexReport& report);
    std::shared_ptr<api::View> create_view_from_dalvik_result(
        const dalvik::DalvikExecutionResult& dalvik_result,
        const dex::DexReport& dex_report
    );  // EXP-031: Real execution view creation
    
    // EXP-031: Mode-specific execution paths
    bool stage_execute_application_real_dalvik(ExecutionResult& result, const ExecutionConfig& config);
    bool stage_execute_application_legacy(ExecutionResult& result, const ExecutionConfig& config);
    
    // Error handling
    void set_error(const std::string& error) { last_error_ = error; }
    
    // Components
    apk::ApkParser apk_parser_;
    dex::DexParser dex_parser_;
    dalvik::DalvikExecutionEngine dalvik_engine_;  // EXP-031: Real executor
    diagnostics::TraceEngine trace_engine_;
    // EXP-086 Phase 7 (B4 FIX): Shadow registry for Handler/Looper dispatch
    framework::ShadowRegistry* shadow_registry_ = nullptr;
    
    // State
    std::vector<uint8_t> framebuffer_;
    std::string last_error_;
};

} // namespace runtime
} // namespace miniandroid

#endif // MINIANDROID_EXECUTION_ENGINE_H
