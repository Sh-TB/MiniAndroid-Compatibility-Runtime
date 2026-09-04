/*
 * MiniAndroid Runtime v0.4 - EXP-019 Android Application Runtime Integration Batch
 * 
 * Connects DEX interpreter, API dispatcher, object model, resource system and renderer
 * into a real Android application runtime.
 * 
 * Data Source: database/api_priority.json (EXP-017)
 * 
 * 7 Phases:
 * Phase 1: Real Resource Pipeline (Context.getResources, Resources.getString, getIdentifier)
 * Phase 2: View Tree from DEX (setContentView, LayoutInflater, findViewById)
 * Phase 3: Button and Event System (Button, setOnClickListener, interface dispatch)
 * Phase 4: Activity Lifecycle Real Mode (remove direct simulation, use runtime dispatch)
 * Phase 5: Intent System (Intent constructor, putExtra/getExtra, startActivity)
 * Phase 6: Golden Corpus Test (20+ APKs)
 * Phase 7: Strict Validation (--strict-real mode)
 * 
 * Golden Debug Protocol Compliant
 * Evidence-first development
 */

#ifndef MINIANDROID_RUNTIME_INTEGRATION_EXP019_H
#define MINIANDROID_RUNTIME_INTEGRATION_EXP019_H

#include "application_runtime.h"
#include "../dex/dex_interpreter_exp018.h"
#include "../resources/resource_parser.h"
#include <unordered_map>
#include <functional>
#include <variant>
#include <mutex>

namespace miniandroid {
namespace runtime {

using json = nlohmann::json;
using namespace dex;

// ============================================================================
// EXP-019 Configuration
// ============================================================================

struct Exp019Config : RuntimeConfig {
    // Phase 1: Resource settings
    bool enable_real_resources = true;
    bool trace_resource_calls = true;
    
    // Phase 2: View tree settings
    bool enable_view_tree_from_dex = true;
    bool auto_register_view_ids = true;
    
    // Phase 3: Event system settings
    bool enable_event_system = true;
    bool enable_interface_dispatch = true;
    
    // Phase 4: Lifecycle settings
    bool real_lifecycle_mode = false;  // --strict-real enables this
    bool dispatch_lifecycle_via_dex = true;
    
    // Phase 5: Intent settings
    bool enable_intent_system = true;
    
    // Phase 7: Strict validation
    bool strict_real_mode = false;  // --strict-real flag
    
    // API priority database path
    std::string api_priority_path = "run/database/api_priority.json";
};

// ============================================================================
// Phase 1: Resource Runtime Trace (Evidence: run/resource_runtime_trace.json)
// ============================================================================

enum class ResourceCallType {
    GET_RESOURCES,       // Context.getResources()
    GET_STRING,          // Resources.getString(int)
    GET_IDENTIFIER,      // Resources.getIdentifier(String, String, String)
    GET_TEXT,            // Resources.getText(int)
    GET_DIMENSION,       // Resources.getDimension(int)
    GET_COLOR,           // Resources.getColor(int)
    GET_DRAWABLE,        // Resources.getDrawable(int)
    GET_LAYOUT,          // Resources.getLayout(int)
    OPEN_RAW_RESOURCE,   // Resources.openRawResource(int)
    UNKNOWN_RESOURCE_CALL
};

std::string resource_call_type_to_string(ResourceCallType type);

struct ResourceCallRecord {
    uint64_t sequence = 0;
    std::string timestamp;
    
    // What was called
    ResourceCallType call_type;
    std::string method_name;
    
    // Arguments
    std::variant<int32_t, std::string> primary_arg;  // resource ID or name
    std::string def_type;  // for getIdentifier
    std::string def_package;  // for getIdentifier
    
    // Resolution result
    bool resolved = false;
    std::string resolved_value;
    int32_t resolved_id = 0;
    
    // Source tracking
    bool called_from_dex = false;
    uint32_t caller_pc = 0;
    std::string caller_method;
    
    // Performance
    double resolution_time_ms = 0;
    
    json to_json() const;
};

struct ResourceRuntimeTrace {
    std::string experiment_id = "EXP-019";
    std::string timestamp;
    
    // Statistics
    uint64_t total_resource_calls = 0;
    std::map<ResourceCallType, uint64_t> calls_by_type;
    uint64_t successful_resolutions = 0;
    uint64_t failed_resolutions = 0;
    
    // All records
    std::vector<ResourceCallRecord> calls;
    
    // Missing resources detected
    std::vector<std::string> missing_resource_ids;
    std::vector<std::string> missing_resource_names;
    
    json to_json() const;
};

// ============================================================================
// Phase 2: View Runtime Trace (Evidence: run/view_runtime_trace.json)
// ============================================================================

enum class ViewOperationType {
    SET_CONTENT_VIEW,     // Activity.setContentView(int/layout)
    FIND_VIEW_BY_ID,      // View.findViewById(int)
    CREATE_VIEW,          // LayoutInflater.createView()
    INFLATE_LAYOUT,       // LayoutInflater.inflate()
    SET_ON_CLICK_LISTENER, // View.setOnClickListener()
    SET_TEXT,             // TextView.setText()
    SET_VISIBILITY,       // View.setVisibility()
    SET_ENABLED,          // View.setEnabled()
    CLICK_EVENT,          // Simulated click event
    UNKNOWN_VIEW_OP
};

std::string view_operation_type_to_string(ViewOperationType type);

struct ViewOperationRecord {
    uint64_t sequence = 0;
    std::string timestamp;
    
    ViewOperationType operation_type;
    std::string operation_name;
    
    // Target view
    uint32_t view_id = 0;
    std::string view_class;
    std::optional<int32_t> android_id;  // R.id.XXX value
    
    // Arguments
    std::map<std::string, std::variant<int32_t, std::string, bool>> arguments;
    
    // Result
    bool success = false;
    std::string result_description;
    uint32_t result_view_id = 0;  // For findViewById
    
    // Source
    bool from_dex = false;
    uint32_t caller_pc = 0;
    
    json to_json() const;
};

struct ViewIdRegistryEntry {
    int32_t android_id = 0;       // R.id.XXX value
    uint32_t internal_id = 0;     // Our object heap ID
    std::string view_class;
    std::string id_name;           // "button1", "textView1", etc.
    uint32_t parent_id = 0;
    bool is_clickable = false;
    
    json to_json() const;
};

struct ViewRuntimeTrace {
    std::string experiment_id = "EXP-019";
    std::string timestamp;
    
    // View ID registry (critical for findViewById)
    std::map<int32_t, ViewIdRegistryEntry> view_id_registry;
    std::map<uint32_t, int32_t> internal_to_android_id;
    
    // Operations log
    std::vector<ViewOperationRecord> operations;
    
    // Statistics
    uint64_t total_operations = 0;
    std::map<ViewOperationType, uint64_t> ops_by_type;
    uint64_t successful_finds = 0;
    uint64_t failed_finds = 0;
    
    // Current content view
    uint32_t content_view_id = 0;
    std::string current_layout_name;
    
    json to_json() const;
};

// ============================================================================
// Phase 3: Event Dispatch Trace (Evidence: run/event_dispatch_trace.json)
// ============================================================================

enum class EventType {
    CLICK,
    LONG_CLICK,
    TOUCH,
    KEY_PRESS,
    FOCUS_CHANGE,
    UNKNOWN_EVENT
};

std::string event_type_to_string(EventType type);

struct InputEvent {
    EventType type;
    uint32_t target_view_id = 0;
    int32_t target_android_id = 0;
    
    // Event data
    float x = 0;
    float y = 0;
    int32_t key_code = 0;
    bool consumed = false;
    
    json to_json() const;
};

struct EventDispatchRecord {
    uint64_t sequence = 0;
    std::string timestamp;
    
    InputEvent event;
    
    // Dispatch path
    bool dispatched = false;
    std::string dispatch_path;  // "INTERFACE_DISPATCH", "DIRECT_CALL", "NO_HANDLER"
    
    // Listener info
    bool has_listener = false;
    std::string listener_interface;
    std::string listener_method;
    uint32_t listener_object_id = 0;
    
    // Execution result
    bool handler_executed = false;
    std::string execution_result;
    
    json to_json() const;
};

struct EventDispatchTrace {
    std::string experiment_id = "EXP-019";
    std::string timestamp;
    
    std::vector<EventDispatchRecord> events;
    
    // Registered listeners
    struct ListenerRegistration {
        uint32_t view_id;
        std::string interface_name;
        uint32_t listener_object_id;
        bool active;
    };
    std::vector<ListenerRegistration> registered_listeners;
    
    // Statistics
    uint64_t total_events = 0;
    uint64_t dispatched_events = 0;
    uint64_t handled_events = 0;
    uint64_t unhandled_events = 0;
    
    json to_json() const;
};

// ============================================================================
// Phase 4: Lifecycle Real Mode Trace (Evidence: run/lifecycle_real_trace.json)
// ============================================================================

enum class LifecycleEvent {
    APPLICATION_ON_CREATE,
    ACTIVITY_ON_CREATE,
    ACTIVITY_ON_START,
    ACTIVITY_ON_RESUME,
    ACTIVITY_ON_PAUSE,
    ACTIVITY_ON_STOP,
    ACTIVITY_ON_DESTROY,
    ACTIVITY_ON_RESTART,
    SAVE_INSTANCE_STATE,
    RESTORE_INSTANCE_STATE
};

std::string lifecycle_event_to_string(LifecycleEvent event);

using json = nlohmann::json;

struct LifecycleDispatchRecord {
    uint64_t sequence = 0;
    std::string timestamp;
    
    LifecycleEvent event;
    std::string event_name;
    
    // Dispatch mode
    bool real_dispatch = false;  // True = via runtime, False = simulated
    std::string dispatch_source;  // "RUNTIME_DISPATCH", "SIMULATED", "DEX_CALLBACK"
    
    // DEX connection
    bool has_dex_handler = false;
    std::string dex_class;
    std::string dex_method;
    bool dex_executed = false;
    uint32_t dex_pc_start = 0;
    uint32_t dex_instructions_executed = 0;
    
    // Result
    bool success = false;
    std::string error_message;
    double duration_ms = 0;
    
    json to_json() const;
};

struct LifecycleRealTrace {
    std::string experiment_id = "EXP-019";
    std::string timestamp;
    
    // Mode
    bool strict_real_mode = false;
    bool real_dispatch_enabled = false;
    
    // All lifecycle events in order
    std::vector<LifecycleDispatchRecord> events;
    
    // Current state
    std::string current_activity_state;
    
    // Validation
    std::vector<std::string> simulation_violations;
    bool all_real_dispatch = true;
    
    json to_json() const;
};

// ============================================================================
// Phase 5: Intent Trace (Evidence: run/intent_trace.json)
// ============================================================================

struct IntentExtra {
    std::string key;
    std::variant<int32_t, std::string, double, bool> value;
    std::string type_name;  // "int", "String", "double", "boolean"
    
    json to_json() const;
};

struct IntentRecord {
    uint64_t sequence = 0;
    std::string timestamp;
    
    std::string action;  // ACTION_MAIN, ACTION_VIEW, etc.
    std::string component;  // "com.example/.MainActivity"
    std::vector<IntentExtra> extras;
    int flags = 0;
    
    // Operations
    enum class Operation {
        CREATED,
        EXTRA_ADDED,
        EXTRA_RETRIEVED,
        START_ACTIVITY_CALLED,
        RESOLVED
    } operation;
    
    // startActivity result
    bool activity_started = false;
    std::string target_activity;
    
    json to_json() const;
};

struct IntentTrace {
    std::string experiment_id = "EXP-019";
    std::string timestamp;
    
    std::vector<IntentRecord> intents;
    
    // Active intents (not yet delivered)
    std::vector<uint64_t> pending_intents;
    
    // Statistics
    uint64_t total_created = 0;
    uint64_t start_activity_calls = 0;
    uint64_t successful_starts = 0;
    
    json to_json() const;
};

// ============================================================================
// Phase 7: Strict Validation Record (Evidence: run/strict_runtime_validation.json)
// ============================================================================

enum class ViolationType {
    HARDCODED_TEXT,
    DIRECT_CPP_OBJECT_INJECTION,
    FAKE_LIFECYCLE,
    MISSING_EVIDENCE,
    UNVERIFIED_API_CALL,
    SIMULATED_BEHAVIOR,
    RESOURCE_BYPASS
};

std::string violation_type_to_string(ViolationType type);

struct ViolationRecord {
    ViolationType violation_type;
    std::string description;
    std::string location;  // File:line or method name
    std::string timestamp;
    bool is_blocking = false;  // Would fail in --strict-real mode
    
    json to_json() const;
};

struct StrictValidationResult {
    std::string experiment_id = "EXP-019";
    std::string timestamp;
    bool strict_mode_enabled = false;
    
    // Results
    bool passed = true;
    std::vector<ViolationRecord> violations;
    
    // Summary by type
    std::map<ViolationType, uint64_t> violations_by_type;
    uint64_t blocking_violations = 0;
    uint64_t non_blocking_violations = 0;
    
    json to_json() const;
};

// ============================================================================
// Main EXP-019 Runtime Integration Class
// ============================================================================

/**
 * EXP-019 Runtime Integration Layer
 * 
 * This class connects ALL subsystems together with real Android semantics:
 * 
 * Phase 1 - Resource Pipeline:
 *   - Intercepts getResources(), getString(), getIdentifier() from DEX
 *   - Routes through real ResourceManager
 *   - Records all resource access patterns
 * 
 * Phase 2 - View Tree:
 *   - setContentView() triggers LayoutInflater
 *   - Creates real View objects in ObjectHeap
 *   - Registers IDs for findViewById()
 * 
 * Phase 3 - Events:
 *   - setOnClickListener() registers interface callbacks
 *   - Click events dispatch through invoke-interface
 *   - Full event pipeline traced
 * 
 * Phase 4 - Lifecycle:
 *   - Application.onCreate() → Activity.onCreate() chain
 *   - All lifecycle methods dispatched via DEX interpreter
 *   - No C++ direct lifecycle simulation
 * 
 * Phase 5 - Intents:
 *   - Intent objects with extras support
 *   - startActivity() navigation
 */
class RuntimeIntegrationExp019 {
public:
    RuntimeIntegrationExp019();
    ~RuntimeIntegrationExp019();
    
    // ========================================================================
    // Initialization
    // ========================================================================
    
    /**
     * Initialize with existing application runtime
     */
    bool initialize(ApplicationRuntime* runtime, const Exp019Config& config = Exp019Config{});
    
    /**
     * Load API priority database for intelligent stubbing decisions
     */
    bool load_api_priority_database(const std::string& path);
    
    // ========================================================================
    // Phase 1: Resource Pipeline
    // ========================================================================
    
    /**
     * Handle Context.getResources() call from DEX
     * Returns a Resources object reference
     */
    Value handle_get_resources(uint32_t pc, const std::string& caller_method);
    
    /**
     * Handle Resources.getString(int id) call from DEX
     */
    Value handle_get_string(int32_t resource_id, uint32_t pc, const std::string& caller_method);
    
    /**
     * Handle Resources.getIdentifier(String name, String defType, String defPackage)
     */
    Value handle_get_identifier(const std::string& name, const std::string& def_type, 
                                const std::string& def_package, uint32_t pc);
    
    /**
     * Generic resource method dispatcher
     */
    Value dispatch_resource_call(ResourceCallType call_type, 
                                  const std::vector<Value>& args,
                                  uint32_t pc,
                                  const std::string& caller_method);
    
    // Resource trace accessors
    const ResourceRuntimeTrace& get_resource_trace() const { return resource_trace_; }
    
    // ========================================================================
    // Phase 2: View Tree from DEX
    // ========================================================================
    
    /**
     * Handle Activity.setContentView(int layoutResID) or setContentView(View)
     */
    bool handle_set_content_view(const Value& layout_arg, uint32_t pc, const std::string& caller_method);
    
    /**
     * Handle View.findViewById(int id)
     */
    Value handle_find_view_by_id(int32_t id, uint32_t pc, const std::string& caller_method);
    
    /**
     * Register a view ID mapping (called during inflation)
     */
    void register_view_id(int32_t android_id, uint32_t internal_id, 
                          const std::string& view_class, const std::string& id_name = "");
    
    /**
     * Get view by Android ID from registry
     */
    Value get_view_by_android_id(int32_t android_id) const;
    
    // View trace accessors
    const ViewRuntimeTrace& get_view_trace() const { return view_trace_; }
    const ViewIdRegistryEntry* lookup_view_id(int32_t android_id) const;
    
    // ========================================================================
    // Phase 3: Button and Event System
    // ========================================================================
    
    /**
     * Handle Button creation
     */
    Value create_button_object(const std::vector<resources::XmlAttribute>& attrs, uint32_t pc);
    
    /**
     * Handle View.setOnClickListener(OnClickListener listener)
     */
    bool handle_set_on_click_listener(uint32_t view_id, Value listener_object, uint32_t pc);
    
    /**
     * Dispatch a click event to a view
     */
    bool dispatch_click_event(uint32_t view_id, float x, float y);
    
    /**
     * Dispatch click event by Android ID
     */
    bool dispatch_click_event_by_id(int32_t android_id, float x = 0, float y = 0);
    
    // Event trace accessors
    const EventDispatchTrace& get_event_trace() const { return event_trace_; }
    
    // ========================================================================
    // Phase 4: Activity Lifecycle Real Mode
    // ========================================================================
    
    /**
     * Execute full application startup with real lifecycle dispatch
     * Application.onCreate() → Activity.onCreate() → onStart() → onResume()
     */
    bool execute_real_lifecycle();
    
    /**
     * Dispatch single lifecycle event via DEX
     */
    bool dispatch_lifecycle_event(LifecycleEvent event);
    
    /**
     * Enable/disable strict real mode (no simulation allowed)
     */
    void set_strict_real_mode(bool enabled);
    
    // Lifecycle trace accessors
    const LifecycleRealTrace& get_lifecycle_trace() const { return lifecycle_trace_; }
    
    // ========================================================================
    // Phase 5: Intent System
    // ========================================================================
    
    /**
     * Create new Intent object
     */
    Value create_intent(const std::string& action = "", const std::string& component = "");
    
    /**
     * Handle Intent.putExtra(String key, value)
     */
    bool intent_put_extra(uint64_t intent_seq, const std::string& key, 
                          const std::variant<int32_t, std::string, double, bool>& value);
    
    /**
     * Handle Intent.getXxxExtra(String key, defaultValue)
     */
    std::optional<std::variant<int32_t, std::string, double, bool>> 
    intent_get_extra(uint64_t intent_seq, const std::string& key);
    
    /**
     * Handle Activity.startActivity(Intent)
     */
    bool handle_start_activity(uint64_t intent_seq);
    
    // Intent trace accessors
    const IntentTrace& get_intent_trace() const { return intent_trace_; }
    
    // ========================================================================
    // Phase 6 & 7: Testing and Validation
    // ========================================================================
    
    /**
     * Run golden corpus test suite
     */
    json run_corpus_test(const std::string& apk_directory, int max_apks = 25);
    
    /**
     * Run strict validation check
     */
    StrictValidationResult run_strict_validation();
    
    /**
     * Generate comprehensive evidence report
     */
    json generate_full_report() const;
    
    /**
     * Write all evidence files
     */
    bool write_all_evidence(const std::string& output_dir);
    
private:
    // ========================================================================
    // Internal helpers
    // ========================================================================
    
    // Resource helpers
    ResourceCallRecord record_resource_call(ResourceCallType type, const std::string& method);
    void finalize_resource_record(ResourceCallRecord& record, bool success, const std::string& value = "");
    
    // View helpers  
    ViewOperationRecord record_view_operation(ViewOperationType type, const std::string& op_name);
    void finalize_view_record(ViewOperationRecord& record, bool success, const std::string& desc = "");
    
    // Event helpers
    EventDispatchRecord record_event_dispatch(InputEvent event);
    
    // Lifecycle helpers
    LifecycleDispatchRecord record_lifecycle_event(LifecycleEvent event);
    
    // Validation helpers
    void check_violation(ViolationType type, const std::string& description, 
                         const std::string& location, bool is_blocking = true);
    
    // State
    ApplicationRuntime* runtime_ = nullptr;
    Exp019Config config_;
    
    // Phase 1: Resource state
    ResourceRuntimeTrace resource_trace_;
    resources::ResourceManager* resource_manager_ = nullptr;
    Value resources_object_;  // Cached Resources object reference
    
    // Phase 2: View state
    ViewRuntimeTrace view_trace_;
    miniandroid::runtime::EnhancedObjectHeap* object_heap_ = nullptr;
    
    // Phase 3: Event state
    EventDispatchTrace event_trace_;
    std::map<uint32_t, uint32_t> view_click_listeners_;  // view_id -> listener_obj_id
    
    // Phase 4: Lifecycle state
    LifecycleRealTrace lifecycle_trace_;
    DexInterpreterExp018* interpreter_ = nullptr;
    
    // Phase 5: Intent state
    IntentTrace intent_trace_;
    std::map<uint64_t, IntentRecord> active_intents_;
    uint64_t next_intent_sequence_ = 1;
    
    // Phase 7: Validation state
    StrictValidationResult validation_result_;
    
    // API priority database
    json api_priority_db_;
    
    // Sequence counters
    uint64_t resource_call_sequence_ = 0;
    uint64_t view_op_sequence_ = 0;
    uint64_t event_sequence_ = 0;
    uint64_t lifecycle_sequence_ = 0;
    
    // Thread safety
    mutable std::mutex mutex_;
    
    // Utility
    std::string get_timestamp_iso8601() const;
};

} // namespace runtime
} // namespace miniandroid

#endif // MINIANDROID_RUNTIME_INTEGRATION_EXP019_H
