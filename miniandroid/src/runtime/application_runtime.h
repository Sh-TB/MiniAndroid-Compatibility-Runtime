/*
 * MiniAndroid Runtime v0.1 - Unified Application Runtime
 * EXP-007→EXP-012: Real APK Runtime Integration
 * 
 * Creates the central ApplicationRuntime that coordinates ALL subsystems:
 * APK → Manifest → DEX → ClassResolver → Interpreter → ObjectHeap 
 * → ResourceManager → LayoutInflater → ViewTree → Renderer → Diagnostics
 * 
 * Golden Debug Protocol Compliant:
 * - Evidence before assumptions
 * - No fake success
 * - Every state transition logged
 * - Explicit failure reporting
 */

#ifndef MINIANDROID_APPLICATION_RUNTIME_H
#define MINIANDROID_APPLICATION_RUNTIME_H

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <cstdint>
#include <chrono>
#include <functional>
#include <sstream>
#include <iomanip>
#include <fstream>

#include "../../third_party/nlohmann_json/include/nlohmann/json.hpp"

// Forward declarations for all subsystems
namespace miniandroid {
    namespace apk {
        class ApkParser;
        struct ApkInfo;
        struct ManifestInfo;
    }
    namespace dex {
        class DexParser;
        class ClassResolver;
        class DexInterpreter;
        struct DexReport;
        struct ExecutionTrace;
        struct EntryPoint;
        struct BatchExecutionTrace;  // From dex_interpreter_batch.h
    }
    namespace runtime {
        class EnhancedObjectHeap;
        class ActivityRuntimeObject;
    }
    namespace resources {
        class ResourceManager;
        class LayoutInflater;
        struct InflateResult;
    }
    namespace renderer {
        class RenderPipeline;
        class FrameBuffer;
        struct LayoutNode;
    }
    namespace diagnostics {
        class TraceEngine;
    }
    // EXP-051: Android framework shadow registry.
    namespace framework {
        class ShadowRegistry;
        class DalvikHeapAdapter;
        class ThreadShadow;
        class LooperShadow;
        class HandlerShadow;
        class ActivityShadow;
        class IntentShadow;
        class ViewShadow;
        class ArchTaskExecutorShadow;  // EXP-052
        class CollectionShadow;  // EXP-054
    }
}

// ============================================================================
// Runtime Configuration (must be defined before ApplicationRuntime)
// ============================================================================

struct RuntimeConfig {
    std::string output_dir = "run";
    bool verbose = false;
    bool save_screenshot = true;
    std::string screenshot_path = "run/screenshot.png";
    int framebuffer_width = 480;
    int framebuffer_height = 800;
    uint32_t max_instructions = 5000000;
    bool stop_on_unimplemented = false;
    bool generate_evidence = true;
    
    nlohmann::json to_json() const {
        return {
            {"output_dir", output_dir},
            {"verbose", verbose},
            {"save_screenshot", save_screenshot},
            {"screenshot_path", screenshot_path},
            {"framebuffer_width", framebuffer_width},
            {"framebuffer_height", framebuffer_height},
            {"max_instructions", max_instructions},
            {"stop_on_unimplemented", stop_on_unimplemented},
            {"generate_evidence", generate_evidence}
        };
    }
};

namespace miniandroid {
namespace runtime {

using json = nlohmann::json;

// ============================================================================
// Runtime State Machine (PHASE A, Task 3)
// ============================================================================

enum class RuntimeState {
    CREATED,                // Initial state
    APK_LOADED,             // APK file parsed
    MANIFEST_RESOLVED,      // AndroidManifest.xml processed
    DEX_LOADED,              // classes.dex parsed
    ACTIVITY_RESOLVED,      // Launcher activity identified
    ACTIVITY_CREATED,        // Activity object instantiated
    ACTIVITY_STARTED,        // onStart() called
    ACTIVITY_RESUMED,        // onResume() called
    CONTENT_LOADED,          // setContentView() processed
    LAYOUT_READY,            // View tree measured and laid out
    FRAME_RENDERED,          // Framebuffer rendered
    COMPLETED,               // Full pipeline complete
    
    // Failure states
    LOAD_FAILED,
    RESOLUTION_FAILED,
    EXECUTION_FAILED,
    RESOURCE_FAILED,
    RENDER_FAILED,
    ERROR                    // Generic error
};

std::string state_to_string(RuntimeState state);
RuntimeState string_to_state(const std::string& str);

struct StateTransition {
    RuntimeState from_state;
    RuntimeState to_state;
    std::string timestamp;
    std::string reason;
    bool success = true;
    double duration_ms = 0;
    
    json to_json() const {
        return {
            {"from", state_to_string(from_state)},
            {"to", state_to_string(to_state)},
            {"timestamp", timestamp},
            {"reason", reason},
            {"success", success},
            {"duration_ms", duration_ms}
        };
    }
};

// ============================================================================
// API Call Record (PHASE D, Task 10)
// ============================================================================

enum class ApiCategory {
    CONTEXT,
    ACTIVITY,
    VIEW,
    RESOURCE,
    LAYOUT,
    RENDERER,
    UNKNOWN
};

std::string api_category_to_string(ApiCategory cat);
ApiCategory string_to_api_category(const std::string& str);

enum class ImplementationStatus {
    IMPLEMENTED,
    PARTIAL,
    STUBBED,
    UNIMPLEMENTED,
    NOT_APPLICABLE
};

std::string impl_status_to_string(ImplementationStatus status);
ImplementationStatus string_to_impl_status(const std::string& str);

struct ApiCallRecord {
    std::string class_name;
    std::string method_name;
    std::string descriptor;
    ApiCategory category;
    std::string call_timestamp;
    uint64_t sequence = 0;
    bool success = false;
    std::string result_summary;
    ImplementationStatus implementation_status = ImplementationStatus::UNIMPLEMENTED;
    
    json to_json() const {
        return {
            {"class", class_name},
            {"method", method_name},
            {"descriptor", descriptor},
            {"category", api_category_to_string(category)},
            {"timestamp", call_timestamp},
            {"sequence", sequence},
            {"success", success},
            {"result", result_summary},
            {"implementation_status", impl_status_to_string(implementation_status)}
        };
    }
};

struct ApiDatabaseEntry {
    std::string class_name;
    std::string method_name;
    std::string descriptor;
    ApiCategory category;
    int first_seen_exp = 0;
    int call_count = 0;
    ImplementationStatus implementation_status = ImplementationStatus::UNIMPLEMENTED;
    int priority = 3;  // P0=0, P1=1, P2=2, P3=3
    
    json to_json() const {
        return {
            {"class", class_name},
            {"method", method_name},
            {"descriptor", descriptor},
            {"category", api_category_to_string(category)},
            {"first_seen_exp", first_seen_exp},
            {"call_count", call_count},
            {"implementation_status", impl_status_to_string(implementation_status)},
            {"priority", priority}
        };
    }
};

// ============================================================================
// Method Dispatch Record (PHASE C, Task 8)
// ============================================================================

enum class DispatchType {
    STATIC,
    DIRECT,
    VIRTUAL,
    INTERFACE,
    SUPER,
    UNKNOWN_DISPATCH
};

std::string dispatch_type_to_string(DispatchType type);

struct MethodDispatchRecord {
    std::string caller_class;
    std::string target_class;
    std::string method_name;
    std::string descriptor;
    DispatchType dispatch_type;
    bool success = false;
    std::string status_detail;
    uint64_t sequence = 0;
    
    json to_json() const {
        return {
            {"caller", caller_class},
            {"target", target_class},
            {"method", method_name},
            {"descriptor", descriptor},
            {"dispatch_type", dispatch_type_to_string(dispatch_type)},
            {"success", success},
            {"detail", status_detail},
            {"sequence", sequence}
        };
    }
};

// ============================================================================
// Failure Classification (PHASE I, Task 25)
// ============================================================================

enum class FailureType {
    UNIMPLEMENTED_OPCODE,
    UNIMPLEMENTED_API,
    UNIMPLEMENTED_RESOURCE,
    UNSUPPORTED_ATTRIBUTE,
    METHOD_RESOLUTION_FAILURE,
    CLASS_RESOLUTION_FAILURE,
    RESOURCE_RESOLUTION_FAILURE,
    RENDER_FAILURE,
    INVALID_RUNTIME_STATE,
    PARSE_ERROR,
    FILE_NOT_FOUND,
    INTERNAL_ERROR,
    EXECUTION_FAILED,      // Added for lifecycle execution failures
    RESOURCE_FAILED,        // Added for resource system failures
    UNKNOWN_FAILURE
};

std::string failure_type_to_string(FailureType type);

struct FailureRecord {
    FailureType type;
    std::string stage;           // Which phase failed
    std::string details;
    std::string timestamp;
    std::string apk_path;
    std::string dex_method;      // Method where failure occurred
    uint32_t pc = 0;             // Program counter
    std::string opcode;           // Opcode that caused failure
    bool is_blocking = false;     // Does this prevent continuation?
    
    json to_json() const {
        return {
            {"type", failure_type_to_string(type)},
            {"stage", stage},
            {"details", details},
            {"timestamp", timestamp},
            {"apk_path", apk_path},
            {"dex_method", dex_method},
            {"pc", pc},
            {"opcode", opcode},
            {"is_blocking", is_blocking}
        };
    }
};

// ============================================================================
// Crash Checkpoint (PHASE I, Task 26)
// ============================================================================

struct CrashCheckpoint {
    std::string timestamp;
    RuntimeState state;
    std::string apk_path;
    std::string current_method;
    uint32_t pc = 0;
    std::string last_opcode;
    
    // Register state snapshot
    json register_state;
    
    // Object heap snapshot (summary)
    json object_state_summary;
    
    // Error details
    std::string error_type;
    std::string error_message;
    std::vector<FailureRecord> recent_failures;
    
    json to_json() const {
        return {
            {"timestamp", timestamp},
            {"state", state_to_string(state)},
            {"apk_path", apk_path},
            {"current_method", current_method},
            {"pc", pc},
            {"last_opcode", last_opcode},
            {"register_state", register_state},
            {"object_state", object_state_summary},
            {"error_type", error_type},
            {"error_message", error_message},
            {"recent_failures", [&]() {
                json arr = json::array();
                for (const auto& f : recent_failures) arr.push_back(f.to_json());
                return arr;
            }()}
        };
    }
};

// ============================================================================
// Main Application Runtime Class (PHASE A, Task 1)
// ============================================================================

class ApplicationRuntime {
public:
    ApplicationRuntime();
    ~ApplicationRuntime();
    
    // ========================================================================
    // Core Pipeline Operations
    // ========================================================================
    
    /**
     * Load and execute an APK through the complete pipeline
     * @param apk_path Path to APK file
     * @return true if pipeline completed successfully
     */
    bool execute_apk(const std::string& apk_path);
    
    /**
     * Execute with custom configuration
     */
    bool execute_apk(const std::string& apk_path, const RuntimeConfig& config);
    
    // ========================================================================
    // Phase A: Loading & Initialization
    // ========================================================================
    
    /** Load APK file (CREATED → APK_LOADED) */
    bool load_apk(const std::string& apk_path);
    
    /** Resolve manifest (APK_LOADED → MANIFEST_RESOLVED) */
    bool resolve_manifest();
    
    /** Parse DEX (MANIFEST_RESOLVED → DEX_LOADED) */
    bool load_dex();
    
    // ========================================================================
    // Phase B: Application Startup
    // ========================================================================
    
    /** Resolve launcher activity from manifest (DEX_LOADED → ACTIVITY_RESOLVED) */
    bool resolve_launcher_activity();
    
    /** Create application and activity objects (ACTIVITY_RESOLVED → ACTIVITY_CREATED) */
    bool create_application();
    
    /** Execute activity lifecycle (ACTIVITY_CREATED → ACTIVITY_RESUMED) */
    bool execute_lifecycle();
    
    // ========================================================================
    // Phase C: DEX Execution
    // ========================================================================
    
    /** Connect lifecycle to DEX interpreter */
    bool execute_on_create();
    
    /** Get DEX instruction trace */
    const dex::BatchExecutionTrace& get_instruction_trace() const;
    
    // ========================================================================
    // Phase E: Resources
    // ========================================================================
    
    /** Initialize resource system */
    bool initialize_resources();
    
    /** Load content view (calls setContentView equivalent) */
    bool load_content_view();
    
    // ========================================================================
    // Phase F: Layout
    // ========================================================================
    
    /** Perform measure and layout pass */
    bool perform_layout();
    
    // ========================================================================
    // Phase H: Rendering
    // ========================================================================
    
    /** Render frame to framebuffer */
    bool render_frame();
    
    /** Save screenshot to PNG */
    bool save_screenshot(const std::string& output_path);
    
    // ========================================================================
    // State & Accessors
    // ========================================================================
    
    RuntimeState get_state() const { return state_; }
    std::string get_state_string() const { return state_to_string(state_); }
    bool has_error() const { return state_ >= RuntimeState::LOAD_FAILED; }
    bool is_complete() const { return state_ == RuntimeState::COMPLETED; }
    
    /** Get current APK path */
    const std::string& get_apk_path() const { return apk_path_; }
    
    /** Get APK info */
    const apk::ApkInfo* get_apk_info() const { return apk_info_.get(); }
    
    /** Get manifest info */
    const apk::ManifestInfo* get_manifest_info() const { return manifest_info_.get(); }
    
    /** Get DEX report */
    const dex::DexReport* get_dex_report() const { return dex_report_.get(); }
    
    /** Get execution trace */
    const dex::ExecutionTrace* get_execution_trace() const { return execution_trace_.get(); }
    
    /** Get entry point */
    const dex::EntryPoint* get_entry_point() const { return entry_point_.get(); }
    
    /** Get object heap */
    EnhancedObjectHeap* get_object_heap() { return heap_.get(); }
    const EnhancedObjectHeap* get_object_heap() const { return heap_.get(); }
    
    /** Get resource manager */
    resources::ResourceManager* get_resource_manager() { return resource_manager_.get(); }
    const resources::ResourceManager* get_resource_manager() const { return resource_manager_.get(); }
    
    /** Get render pipeline */
    renderer::RenderPipeline* get_render_pipeline() { return render_pipeline_.get(); }
    const renderer::FrameBuffer* get_framebuffer() const;
    
    // ========================================================================
    // Evidence & Diagnostics (PHASE I)
    // ========================================================================
    
    /** Get all state transitions */
    const std::vector<StateTransition>& get_state_transitions() const { return state_transitions_; }
    
    /** Get all API calls */
    const std::vector<ApiCallRecord>& get_api_calls() const { return api_calls_; }
    
    /** Get method dispatch records */
    const std::vector<MethodDispatchRecord>& get_method_dispatches() const { return method_dispatches_; }
    
    /** Get failures */
    const std::vector<FailureRecord>& get_failures() const { return failures_; }
    
    /** Get API database */
    const std::map<std::string, ApiDatabaseEntry>& get_api_database() const { return api_database_; }
    
    /** Record an API call */
    void record_api_call(const ApiCallRecord& call);
    
    /** Record a method dispatch */
    void record_dispatch(const MethodDispatchRecord& dispatch);
    
    /** Record a failure */
    void record_failure(FailureRecord failure);
    
    // ========================================================================
    // Evidence Generation
    // ========================================================================
    
    /** Generate application runtime JSON evidence */
    json to_json() const;
    
    /** Generate runtime state trace */
    json generate_state_trace() const;
    
    /** Generate component map */
    json generate_component_map() const;
    
    /** Generate launcher resolution info */
    json generate_launcher_resolution() const;
    
    /** Generate application trace */
    json generate_application_trace() const;
    
    /** Generate lifecycle trace */
    json generate_lifecycle_trace() const;
    
    /** Generate DEX lifecycle trace */
    json generate_dex_lifecycle_trace() const;
    
    /** Generate method dispatch trace */
    json generate_method_dispatch_trace() const;
    
    /** Generate API usage report */
    json generate_api_usage_report() const;
    
    /** Generate ARSC trace */
    json generate_arsc_trace() const;
    
    /** Generate resource resolution trace */
    json generate_resource_resolution_trace() const;
    
    /** Generate layout attribute trace */
    json generate_layout_attribute_trace() const;
    
    /** Generate layout geometry */
    json generate_layout_geometry() const;
    
    /** Generate context API trace */
    json generate_context_api_trace() const;
    
    /** Generate activity API trace */
    json generate_activity_api_trace() const;
    
    /** Generate view API trace */
    json generate_view_api_trace() const;
    
    /** Generate render command trace */
    json generate_render_command_trace() const;
    
    /** Generate frame checksum */
    json generate_frame_checksum() const;
    
    /** Generate unified execution trace */
    json generate_execution_trace() const;
    
    /** Generate failure report */
    json generate_failure_report() const;
    
    /** Generate crash checkpoint */
    json generate_crash_checkpoint() const;
    
    /** Generate golden end-to-end test results */
    json generate_golden_end_to_end() const;
    
    /** Write all evidence files to directory */
    bool write_all_evidence(const std::string& output_dir);

    // ========================================================================
    // EXP-051: Shadow Registry Public API
    // ========================================================================

    /** Access the shadow registry (never null after construction). */
    framework::ShadowRegistry* get_shadow_registry() { return shadow_registry_.get(); }

    /** Drain pending Handler/Runnable queue. Returns the number of
     *  Runnables whose run() method the runtime should now invoke.
     *  Each drained Runnable's heap object_id is appended to out_ids. */
    size_t drain_handler_queue(std::vector<uint32_t>* out_ids);

    /** True if a startActivity(Intent) call is pending. */
    bool has_pending_intent() const;

    /** Take the pending Intent's target class (DEX descriptor).
     *  Returns empty string if no pending Intent or no component set.
     *  This is the only piece of Intent state the runtime needs to
     *  drive Activity transitions — the actual PendingIntent object
     *  stays inside the IntentShadow. */
    std::string take_pending_intent_target_class();

    /** Get the ActivityShadow's current content view id (0 if none). */
    uint32_t get_content_view_id() const;

    /** Record the current Activity on the ActivityShadow. Called by
     *  the runtime when an Activity is created. */
    void set_current_activity(uint32_t activity_obj_id,
                              const std::string& activity_class);

    /** Generate a shadow registry diagnostic report (for evidence). */
    json generate_shadow_report() const;
    
private:
    // ========================================================================
    // Internal State Management
    // ========================================================================
    
    bool transition_to(RuntimeState new_state, const std::string& reason);
    void record_transition(RuntimeState from, RuntimeState to, const std::string& reason, 
                          bool success, double duration_ms);
    
    std::string get_timestamp() const;
    void initialize_subsystems();
    void cleanup();
    
    // ========================================================================
    // Subsystem Pointers (owned)
    // ========================================================================
    
    std::unique_ptr<apk::ApkParser> apk_parser_;
    std::unique_ptr<dex::DexParser> dex_parser_;
    std::unique_ptr<dex::ClassResolver> class_resolver_;
    // Note: No dex::DexInterpreter - we use DexInterpreterBatch instead to avoid header conflicts
    std::unique_ptr<EnhancedObjectHeap> heap_;
    std::unique_ptr<resources::ResourceManager> resource_manager_;
    std::unique_ptr<renderer::RenderPipeline> render_pipeline_;
    std::unique_ptr<diagnostics::TraceEngine> trace_engine_;
    
    // ========================================================================
    // Data Objects (owned)
    // ========================================================================
    
    std::unique_ptr<apk::ApkInfo> apk_info_;
    std::unique_ptr<apk::ManifestInfo> manifest_info_;
    std::unique_ptr<dex::DexReport> dex_report_;
    std::unique_ptr<dex::ExecutionTrace> execution_trace_;
    std::unique_ptr<dex::EntryPoint> entry_point_;
    std::unique_ptr<dex::BatchExecutionTrace> instruction_trace_;
    
    // ========================================================================
    // Raw Data
    // ========================================================================
    
    std::string apk_path_;
    std::vector<uint8_t> apk_data_;
    std::vector<uint8_t> dex_data_;
    std::vector<uint8_t> manifest_data_;
    
    // ========================================================================
    // State
    // ========================================================================
    
    RuntimeState state_ = RuntimeState::CREATED;
    std::vector<StateTransition> state_transitions_;
    
    // ========================================================================
    // Records & Database
    // ========================================================================
    
    std::vector<ApiCallRecord> api_calls_;
    std::vector<MethodDispatchRecord> method_dispatches_;
    std::vector<FailureRecord> failures_;
    std::map<std::string, ApiDatabaseEntry> api_database_;  // key: "class#method"
    uint64_t api_call_sequence_ = 0;
    uint64_t dispatch_sequence_ = 0;
    
    // Configuration (using external RuntimeConfig struct)
    RuntimeConfig config_;
    
    // ========================================================================
    // Activity Tracking
    // ========================================================================
    
    uint32_t activity_object_id_ = 0;
    std::string activity_class_name_;
    std::vector<std::string> lifecycle_events_;

    // ========================================================================
    // EXP-051: Android Framework Shadow Registry
    // ========================================================================
    //
    // Owned by ApplicationRuntime so we can:
    //   * Register all default shadows at construction time.
    //   * Drain the HandlerShadow queue at well-defined points.
    //   * Read IntentShadow pending intents after Activity callbacks.
    //   * Dump stub-debt statistics for the EXP-051 report.
    //
    // The DalvikExecutionEngine gets a non-owning pointer to the registry
    // via set_shadow_registry() before execution begins.

    std::unique_ptr<framework::ShadowRegistry> shadow_registry_;
    std::unique_ptr<framework::DalvikHeapAdapter> heap_adapter_;
    // Cached pointers to specific shadows for direct access (no
    // dynamic_cast needed at drain points).
    framework::ThreadShadow*   shadow_thread_   = nullptr;
    framework::LooperShadow*    shadow_looper_   = nullptr;
    framework::HandlerShadow*   shadow_handler_  = nullptr;
    framework::ActivityShadow*  shadow_activity_ = nullptr;
    framework::IntentShadow*    shadow_intent_   = nullptr;
    framework::ViewShadow*      shadow_view_     = nullptr;
    framework::ArchTaskExecutorShadow* shadow_arch_task_ = nullptr;  // EXP-052
    framework::CollectionShadow* shadow_collection_ = nullptr;  // EXP-054

    // EXP-051: Initialize the shadow registry. Called once during
    // ApplicationRuntime construction. Wires the ThreadShadow and
    // LooperShadow together so they share the same main_thread_id.
    void initialize_shadow_registry();
    
    // ========================================================================
    // Timing
    // ========================================================================
    
    std::chrono::steady_clock::time_point start_time_;
    double total_duration_ms_ = 0;
};

} // namespace runtime
} // namespace miniandroid

#endif // MINIANDROID_APPLICATION_RUNTIME_H
