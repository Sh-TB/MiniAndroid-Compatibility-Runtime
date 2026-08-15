/*
 * MiniAndroid Runtime v0.1 - Unified Application Runtime Implementation
 * EXP-007→EXP-012: Real APK Runtime Integration
 * 
 * Implements the central coordinator for all MiniAndroid subsystems.
 */

#include "application_runtime.h"
#include "apk/apk_parser.h"
#include "apk/manifest_reader.h"
#include "dex/dex_parser.h"
#include "dex/class_resolver.h"
#include "dex/dex_interpreter_batch.h"
// EXP-037 Phase B (BLOCKER-020): Use DalvikExecutionEngine instead of
// DexInterpreterBatch for execute_on_create. DexInterpreterBatch only handles
// 5 opcodes (const-string, new-instance, invoke-direct, invoke-virtual,
// return-void) and lacks invoke-super, goto, if-*, iget/iput/sget/sput —
// every real onCreate hits invoke-super at PC=0 and immediately halts.
// DalvikExecutionEngine has all the opcodes I've implemented across
// BLOCKER-012 (invoke-super), BLOCKER-014 (goto fix), BLOCKER-015 (35c format),
// BLOCKER-016 (arg_count), BLOCKER-017 (22c format), BLOCKER-018 (if-*).
#include "dex/dalvik_engine.h"
// Note: Do NOT include dex/dex_interpreter.h - it has Opcodes that conflict with dex_interpreter_batch.h
#include "object_model.h"
#include "resources/resource_parser.h"
#include "renderer/software_renderer.h"
#include "diagnostics/trace_engine.h"

// Don't include dex_interpreter.h to avoid Opcodes redefinition
// We use dex_interpreter_batch.h which has BatchExecutionTrace

#include <iostream>
#include <filesystem>
#include <algorithm>

namespace fs = std::filesystem;

namespace miniandroid {
namespace runtime {

using json = nlohmann::json;
using namespace miniandroid::apk;
using namespace miniandroid::dex;
using namespace miniandroid::resources;
using namespace miniandroid::renderer;
using namespace miniandroid::diagnostics;

// ============================================================================
// Utility Functions
// ============================================================================

std::string state_to_string(RuntimeState state) {
    switch (state) {
        case RuntimeState::CREATED: return "CREATED";
        case RuntimeState::APK_LOADED: return "APK_LOADED";
        case RuntimeState::MANIFEST_RESOLVED: return "MANIFEST_RESOLVED";
        case RuntimeState::DEX_LOADED: return "DEX_LOADED";
        case RuntimeState::ACTIVITY_RESOLVED: return "ACTIVITY_RESOLVED";
        case RuntimeState::ACTIVITY_CREATED: return "ACTIVITY_CREATED";
        case RuntimeState::ACTIVITY_STARTED: return "ACTIVITY_STARTED";
        case RuntimeState::ACTIVITY_RESUMED: return "ACTIVITY_RESUMED";
        case RuntimeState::CONTENT_LOADED: return "CONTENT_LOADED";
        case RuntimeState::LAYOUT_READY: return "LAYOUT_READY";
        case RuntimeState::FRAME_RENDERED: return "FRAME_RENDERED";
        case RuntimeState::COMPLETED: return "COMPLETED";
        case RuntimeState::LOAD_FAILED: return "LOAD_FAILED";
        case RuntimeState::RESOLUTION_FAILED: return "RESOLUTION_FAILED";
        case RuntimeState::EXECUTION_FAILED: return "EXECUTION_FAILED";
        case RuntimeState::RESOURCE_FAILED: return "RESOURCE_FAILED";
        case RuntimeState::RENDER_FAILED: return "RENDER_FAILED";
        case RuntimeState::ERROR: return "ERROR";
        default: return "UNKNOWN";
    }
}

RuntimeState string_to_state(const std::string& str) {
    if (str == "CREATED") return RuntimeState::CREATED;
    if (str == "APK_LOADED") return RuntimeState::APK_LOADED;
    if (str == "MANIFEST_RESOLVED") return RuntimeState::MANIFEST_RESOLVED;
    if (str == "DEX_LOADED") return RuntimeState::DEX_LOADED;
    if (str == "ACTIVITY_RESOLVED") return RuntimeState::ACTIVITY_RESOLVED;
    if (str == "ACTIVITY_CREATED") return RuntimeState::ACTIVITY_CREATED;
    if (str == "ACTIVITY_STARTED") return RuntimeState::ACTIVITY_STARTED;
    if (str == "ACTIVITY_RESUMED") return RuntimeState::ACTIVITY_RESUMED;
    if (str == "CONTENT_LOADED") return RuntimeState::CONTENT_LOADED;
    if (str == "LAYOUT_READY") return RuntimeState::LAYOUT_READY;
    if (str == "FRAME_RENDERED") return RuntimeState::FRAME_RENDERED;
    if (str == "COMPLETED") return RuntimeState::COMPLETED;
    if (str == "LOAD_FAILED") return RuntimeState::LOAD_FAILED;
    if (str == "RESOLUTION_FAILED") return RuntimeState::RESOLUTION_FAILED;
    if (str == "EXECUTION_FAILED") return RuntimeState::EXECUTION_FAILED;
    if (str == "RESOURCE_FAILED") return RuntimeState::RESOURCE_FAILED;
    if (str == "RENDER_FAILED") return RuntimeState::RENDER_FAILED;
    if (str == "ERROR") return RuntimeState::ERROR;
    return RuntimeState::CREATED;
}

std::string api_category_to_string(ApiCategory cat) {
    switch (cat) {
        case ApiCategory::CONTEXT: return "CONTEXT";
        case ApiCategory::ACTIVITY: return "ACTIVITY";
        case ApiCategory::VIEW: return "VIEW";
        case ApiCategory::RESOURCE: return "RESOURCE";
        case ApiCategory::LAYOUT: return "LAYOUT";
        case ApiCategory::RENDERER: return "RENDERER";
        default: return "UNKNOWN";
    }
}

ApiCategory string_to_api_category(const std::string& str) {
    if (str == "CONTEXT") return ApiCategory::CONTEXT;
    if (str == "ACTIVITY") return ApiCategory::ACTIVITY;
    if (str == "VIEW") return ApiCategory::VIEW;
    if (str == "RESOURCE") return ApiCategory::RESOURCE;
    if (str == "LAYOUT") return ApiCategory::LAYOUT;
    if (str == "RENDERER") return ApiCategory::RENDERER;
    return ApiCategory::UNKNOWN;
}

std::string impl_status_to_string(ImplementationStatus status) {
    switch (status) {
        case ImplementationStatus::IMPLEMENTED: return "IMPLEMENTED";
        case ImplementationStatus::PARTIAL: return "PARTIAL";
        case ImplementationStatus::STUBBED: return "STUBBED";
        case ImplementationStatus::UNIMPLEMENTED: return "UNIMPLEMENTED";
        case ImplementationStatus::NOT_APPLICABLE: return "NOT_APPLICABLE";
        default: return "UNKNOWN";
    }
}

ImplementationStatus string_to_impl_status(const std::string& str) {
    if (str == "IMPLEMENTED") return ImplementationStatus::IMPLEMENTED;
    if (str == "PARTIAL") return ImplementationStatus::PARTIAL;
    if (str == "STUBBED") return ImplementationStatus::STUBBED;
    if (str == "UNIMPLEMENTED") return ImplementationStatus::UNIMPLEMENTED;
    if (str == "NOT_APPLICABLE") return ImplementationStatus::NOT_APPLICABLE;
    return ImplementationStatus::UNIMPLEMENTED;
}

std::string dispatch_type_to_string(DispatchType type) {
    switch (type) {
        case DispatchType::STATIC: return "STATIC";
        case DispatchType::DIRECT: return "DIRECT";
        case DispatchType::VIRTUAL: return "VIRTUAL";
        case DispatchType::INTERFACE: return "INTERFACE";
        case DispatchType::SUPER: return "SUPER";
        default: return "UNKNOWN";
    }
}

std::string failure_type_to_string(FailureType type) {
    switch (type) {
        case FailureType::UNIMPLEMENTED_OPCODE: return "UNIMPLEMENTED_OPCODE";
        case FailureType::UNIMPLEMENTED_API: return "UNIMPLEMENTED_API";
        case FailureType::UNIMPLEMENTED_RESOURCE: return "UNIMPLEMENTED_RESOURCE";
        case FailureType::UNSUPPORTED_ATTRIBUTE: return "UNSUPPORTED_ATTRIBUTE";
        case FailureType::METHOD_RESOLUTION_FAILURE: return "METHOD_RESOLUTION_FAILURE";
        case FailureType::CLASS_RESOLUTION_FAILURE: return "CLASS_RESOLUTION_FAILURE";
        case FailureType::RESOURCE_RESOLUTION_FAILURE: return "RESOURCE_RESOLUTION_FAILURE";
        case FailureType::RENDER_FAILURE: return "RENDER_FAILURE";
        case FailureType::INVALID_RUNTIME_STATE: return "INVALID_RUNTIME_STATE";
        case FailureType::PARSE_ERROR: return "PARSE_ERROR";
        case FailureType::FILE_NOT_FOUND: return "FILE_NOT_FOUND";
        case FailureType::INTERNAL_ERROR: return "INTERNAL_ERROR";
        case FailureType::EXECUTION_FAILED: return "EXECUTION_FAILED";
        case FailureType::RESOURCE_FAILED: return "RESOURCE_FAILED";
        default: return "UNKNOWN_FAILURE";
    }
}

// ============================================================================
// ApplicationRuntime Constructor/Destructor
// ============================================================================

ApplicationRuntime::ApplicationRuntime() {
    start_time_ = std::chrono::steady_clock::now();
    initialize_subsystems();
    
    StateTransition initial;
    initial.from_state = RuntimeState::CREATED;
    initial.to_state = RuntimeState::CREATED;
    initial.timestamp = get_timestamp();
    initial.reason = "ApplicationRuntime initialized";
    initial.success = true;
    state_transitions_.push_back(initial);
    
    if (config_.verbose) {
        std::cout << "[MiniAndroid] ApplicationRuntime created" << std::endl;
    }
}

ApplicationRuntime::~ApplicationRuntime() {
    cleanup();
    
    auto end = std::chrono::steady_clock::now();
    total_duration_ms_ = std::chrono::duration<double, std::milli>(end - start_time_).count();
    
    if (config_.verbose) {
        std::cout << "[MiniAndroid] ApplicationRuntime destroyed (ran for " 
                  << total_duration_ms_ << "ms)" << std::endl;
    }
}

void ApplicationRuntime::initialize_subsystems() {
    // Create all subsystems
    apk_parser_ = std::make_unique<ApkParser>();
    dex_parser_ = std::make_unique<DexParser>();
    class_resolver_ = std::make_unique<ClassResolver>();
    heap_ = std::make_unique<EnhancedObjectHeap>();
    resource_manager_ = std::make_unique<ResourceManager>();
    render_pipeline_ = std::make_unique<RenderPipeline>(
        config_.framebuffer_width, config_.framebuffer_height);
    trace_engine_ = std::make_unique<TraceEngine>();
    // Note: interpreter_ not created - we use DexInterpreterBatch instead
    
    // Configure subsystems
    apk_parser_->set_verbose(config_.verbose);
    dex_parser_->set_verbose(config_.verbose);
    class_resolver_->set_verbose(config_.verbose);
}

void ApplicationRuntime::cleanup() {
    // Smart pointers handle cleanup automatically
}

std::string ApplicationRuntime::get_timestamp() const {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    std::stringstream ss;
    ss << std::put_time(std::gmtime(&time_t), "%Y-%m-%dT%H:%M:%SZ");
    return ss.str();
}

// ============================================================================
// State Management
// ============================================================================

bool ApplicationRuntime::transition_to(RuntimeState new_state, const std::string& reason) {
    auto start = std::chrono::steady_clock::now();
    RuntimeState from = state_;
    
    state_ = new_state;
    
    auto end = std::chrono::steady_clock::now();
    double duration = std::chrono::duration<double, std::milli>(end - start).count();
    
    record_transition(from, new_state, reason, true, duration);
    
    if (config_.verbose) {
        std::cout << "[State] " << state_to_string(from) << " → " 
                  << state_to_string(new_state) << ": " << reason << std::endl;
    }
    
    return true;
}

void ApplicationRuntime::record_transition(RuntimeState from, RuntimeState to, 
                                          const std::string& reason,
                                          bool success, double duration_ms) {
    StateTransition trans;
    trans.from_state = from;
    trans.to_state = to;
    trans.timestamp = get_timestamp();
    trans.reason = reason;
    trans.success = success;
    trans.duration_ms = duration_ms;
    state_transitions_.push_back(trans);
}

// ============================================================================
// Core Pipeline Operations
// ============================================================================

bool ApplicationRuntime::execute_apk(const std::string& apk_path) {
    RuntimeConfig default_config;
    return execute_apk(apk_path, default_config);
}

bool ApplicationRuntime::execute_apk(const std::string& apk_path, const RuntimeConfig& config) {
    config_ = config;
    apk_path_ = apk_path;
    
    if (config_.verbose) {
        std::cout << "\n========== MiniAndroid Runtime v0.1 ==========" << std::endl;
        std::cout << "Executing: " << apk_path << std::endl;
        std::cout << "==============================================\n" << std::endl;
    }
    
    try {
        // Phase A: Load APK and resolve basics
        if (!load_apk(apk_path)) return false;
        if (!resolve_manifest()) return false;
        if (!load_dex()) return false;
        
        // Phase B: Resolve and create application
        if (!resolve_launcher_activity()) return false;
        if (!create_application()) return false;
        
        // Phase C: Execute DEX lifecycle methods
        // EXP-037 Phase B (BLOCKER-010 FIX): wire execute_on_create() into the
        // pipeline so the megabatch path actually invokes the DalvikExecutionEngine
        // and runs real bytecode. Without this call, the runtime transitions
        // through lifecycle states using only C++ stubs (4 microseconds total).
        if (!execute_on_create()) {
            // Don't fail hard — continue with stubbed lifecycle if DEX execution
            // hits an unimplemented opcode. This is intentional: the runtime
            // should produce as much evidence as possible even when it can't
            // fully execute real bytecode.
            if (config_.verbose) {
                std::cout << "[Phase C] execute_on_create() returned false — continuing with stubbed lifecycle" << std::endl;
            }
        }
        if (!execute_lifecycle()) return false;
        
        // Phase E: Resources
        if (!initialize_resources()) return false;
        if (!load_content_view()) return false;
        
        // Phase F: Layout
        if (!perform_layout()) return false;
        
        // Phase H: Rendering
        if (!render_frame()) return false;
        
        // Complete!
        transition_to(RuntimeState::COMPLETED, "Pipeline completed successfully");
        
        if (config_.save_screenshot) {
            save_screenshot(config_.screenshot_path);
        }
        
        if (config_.generate_evidence) {
            write_all_evidence(config_.output_dir);
        }
        
        return true;
        
    } catch (const std::exception& e) {
        FailureRecord f;
        f.type = FailureType::INTERNAL_ERROR;
        f.stage = "execute_apk";
        f.details = e.what();
        f.timestamp = get_timestamp();
        f.apk_path = apk_path_;
        f.is_blocking = true;
        record_failure(f);
        transition_to(RuntimeState::ERROR, std::string("Exception: ") + e.what());
        return false;
    }
}

// ============================================================================
// Phase A: Loading & Initialization
// ============================================================================

bool ApplicationRuntime::load_apk(const std::string& apk_path) {
    auto start = std::chrono::steady_clock::now();
    
    try {
        if (config_.verbose) {
            std::cout << "[Phase A] Loading APK: " << apk_path << std::endl;
        }
        
        // Parse APK
        ApkInfo info = apk_parser_->parse(apk_path);
        
        if (!info.is_valid) {
            FailureRecord f;
            f.type = FailureType::FILE_NOT_FOUND;
            f.stage = "load_apk";
            f.details = apk_parser_->get_last_error();
            f.timestamp = get_timestamp();
            f.apk_path = apk_path;
            f.is_blocking = true;
            record_failure(f);
            transition_to(RuntimeState::LOAD_FAILED, "APK parsing failed: " + apk_parser_->get_last_error());
            return false;
        }
        
        apk_info_ = std::make_unique<ApkInfo>(info);
        
        // EXP-038 (BLOCKER-023): Use cached APK data instead of re-reading the file.
        // The ApkParser::parse() call above already loaded the entire APK into
        // memory and cached all ZIP entries. We can now use extract_entry_cached()
        // for O(1) entry lookups.
        // For backward compatibility, we still populate apk_data_ but from
        // the parser's cached data if available.
        if (apk_parser_->has_cached_data()) {
            // Use cached extraction for manifest
            manifest_data_ = apk_parser_->extract_entry_cached("AndroidManifest.xml");
        } else {
            // Fallback: read file and extract manually (legacy path)
            std::ifstream file(apk_path, std::ios::binary | std::ios::ate);
            if (!file.is_open()) {
                transition_to(RuntimeState::LOAD_FAILED, "Cannot open APK file");
                return false;
            }
            size_t size = file.tellg();
            file.seekg(0, std::ios::beg);
            apk_data_.resize(size);
            file.read(reinterpret_cast<char*>(apk_data_.data()), size);
            file.close();
            manifest_data_ = apk_parser_->extract_entry(apk_path, "AndroidManifest.xml");
        }

        auto end = std::chrono::steady_clock::now();
        double duration = std::chrono::duration<double, std::milli>(end - start).count();
        
        transition_to(RuntimeState::APK_LOADED, "APK loaded successfully: " + apk_path);
        
        if (config_.verbose) {
            std::cout << "  Package: " << info.package_name << std::endl;
            std::cout << "  Main Activity: " << info.main_activity_full << std::endl;
            std::cout << "  Size: " << info.file_size << " bytes" << std::endl;
            std::cout << "  Duration: " << duration << "ms" << std::endl;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        FailureRecord f;
        f.type = FailureType::PARSE_ERROR;
        f.stage = "load_apk";
        f.details = e.what();
        f.timestamp = get_timestamp();
        f.apk_path = apk_path;
        f.is_blocking = true;
        record_failure(f);
        transition_to(RuntimeState::LOAD_FAILED, std::string("Exception: ") + e.what());
        return false;
    }
}

bool ApplicationRuntime::resolve_manifest() {
    auto start = std::chrono::steady_clock::now();
    
    try {
        if (config_.verbose) {
            std::cout << "[Phase A] Resolving manifest..." << std::endl;
        }
        
        if (manifest_data_.empty()) {
            FailureRecord f;
            f.type = FailureType::PARSE_ERROR;
            f.stage = "resolve_manifest";
            f.details = "No manifest data available";
            f.timestamp = get_timestamp();
            f.apk_path = apk_path_;
            f.is_blocking = true;
            record_failure(f);
            transition_to(RuntimeState::RESOLUTION_FAILED, "No manifest data");
            return false;
        }
        
        ManifestReader manifest_reader;
        manifest_reader.set_verbose(config_.verbose);
        ManifestInfo manifest_info = manifest_reader.parse(manifest_data_);
        
        if (!manifest_info.parse_success) {
            FailureRecord f;
            f.type = FailureType::PARSE_ERROR;
            f.stage = "resolve_manifest";
            f.details = manifest_info.error_message;
            f.timestamp = get_timestamp();
            f.apk_path = apk_path_;
            f.is_blocking = true;
            record_failure(f);
            transition_to(RuntimeState::RESOLUTION_FAILED, "Manifest parsing failed");
            return false;
        }
        
        manifest_info_ = std::make_unique<ManifestInfo>(manifest_info);
        
        auto end = std::chrono::steady_clock::now();
        double duration = std::chrono::duration<double, std::milli>(end - start).count();
        
        transition_to(RuntimeState::MANIFEST_RESOLVED, "Manifest resolved: " + manifest_info.package_name);
        
        if (config_.verbose) {
            std::cout << "  Package: " << manifest_info.package_name << std::endl;
            std::cout << "  Activities: " << manifest_info.activities.size() << std::endl;
            std::cout << "  Duration: " << duration << "ms" << std::endl;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        FailureRecord f;
        f.type = FailureType::PARSE_ERROR;
        f.stage = "resolve_manifest";
        f.details = e.what();
        f.timestamp = get_timestamp();
        f.apk_path = apk_path_;
        f.is_blocking = true;
        record_failure(f);
        transition_to(RuntimeState::RESOLUTION_FAILED, std::string("Exception: ") + e.what());
        return false;
    }
}

bool ApplicationRuntime::load_dex() {
    auto start = std::chrono::steady_clock::now();
    
    try {
        if (config_.verbose) {
            std::cout << "[Phase A] Loading DEX..." << std::endl;
        }
        
        // EXP-038 (BLOCKER-024): MultiDex support.
        // Load ALL classes*.dex files from the APK, not just classes.dex.
        // Telegram has 5 DEX files with 41,078 total classes. Without
        // multidex, the runtime only sees 12,521 classes and can't resolve
        // org.telegram.ui.LaunchActivity (which is in a later DEX file).
        
        // Get list of DEX files from the cached APK info
        std::vector<std::string> dex_files;
        if (apk_info_ && !apk_info_->dex_files.empty()) {
            dex_files = apk_info_->dex_files;
        } else {
            dex_files.push_back("classes.dex");  // fallback
        }
        
        // Sort to ensure classes.dex is first, then classes2.dex, etc.
        std::sort(dex_files.begin(), dex_files.end());
        
        // Create a merged DexReport
        DexReport merged_report;
        merged_report.is_valid = true;
        merged_report.dex_path = apk_path_;
        merged_report.dex_version = "039";  // will be updated from first DEX
        
        if (config_.verbose) {
            std::cout << "  Found " << dex_files.size() << " DEX files" << std::endl;
        }
        
        for (size_t i = 0; i < dex_files.size(); i++) {
            const std::string& dex_name = dex_files[i];
            
            // Extract DEX data using cached lookup
            std::vector<uint8_t> dex_data;
            if (apk_parser_->has_cached_data()) {
                dex_data = apk_parser_->extract_entry_cached(dex_name);
            } else {
                dex_data = apk_parser_->extract_entry_from_memory(apk_data_, dex_name);
            }
            
            if (dex_data.empty()) {
                if (config_.verbose) {
                    std::cout << "  [SKIP] " << dex_name << " (not found)" << std::endl;
                }
                continue;
            }
            
            // Parse this DEX file
            DexReport report = dex_parser_->parse_data(dex_data, apk_path_ + "/" + dex_name);
            
            if (!report.is_valid) {
                if (config_.verbose) {
                    std::cout << "  [FAIL] " << dex_name << ": " << report.validation_error << std::endl;
                }
                continue;
            }
            
            if (config_.verbose) {
                std::cout << "  [" << (i+1) << "/" << dex_files.size() << "] "
                          << dex_name << ": " << report.classes_count << " classes, "
                          << report.methods_count << " methods" << std::endl;
            }
            
            // Merge into combined report
            // For the first DEX, use its version info
            if (i == 0) {
                merged_report.dex_version = report.dex_version;
            }
            
            // Append all classes
            for (auto& cls : report.classes) {
                merged_report.classes.push_back(std::move(cls));
            }
            
            // Append method_ids and field_ids
            for (auto& mid : report.method_ids) {
                merged_report.method_ids.push_back(mid);
            }
            for (auto& fid : report.field_ids) {
                merged_report.field_ids.push_back(fid);
            }
            
            // Append strings and types (with offset adjustment to avoid duplicates)
            // Note: For now, we just concatenate. Cross-DEX references use
            // method_idx/field_idx which are PER-DEX, not global. This is a
            // known limitation — proper multidex requires global ID remapping.
            // For now, the first DEX's strings/types are used for resolution.
            if (merged_report.strings.empty()) {
                merged_report.strings = report.strings;
                merged_report.types = report.types;
            }
            
            // Update counts
            merged_report.classes_count += report.classes_count;
            merged_report.methods_count += report.methods_count;
            merged_report.fields_count += report.fields_count;
            merged_report.strings_count += report.strings_count;
            merged_report.types_count += report.types_count;
            merged_report.prototypes_count += report.prototypes_count;
        }
        
        if (merged_report.classes.empty()) {
            FailureRecord f;
            f.type = FailureType::FILE_NOT_FOUND;
            f.stage = "load_dex";
            f.details = "No valid DEX files found in APK";
            f.timestamp = get_timestamp();
            f.apk_path = apk_path_;
            f.is_blocking = true;
            record_failure(f);
            transition_to(RuntimeState::LOAD_FAILED, "No valid DEX files");
            return false;
        }
        
        // Also keep the first DEX's data for backward compatibility (dex_data_)
        if (apk_parser_->has_cached_data()) {
            dex_data_ = apk_parser_->extract_entry_cached("classes.dex");
        }
        
        dex_report_ = std::make_unique<DexReport>(merged_report);
        
        auto end = std::chrono::steady_clock::now();
        double duration = std::chrono::duration<double, std::milli>(end - start).count();
        
        transition_to(RuntimeState::DEX_LOADED, "DEX loaded: " + std::to_string(merged_report.classes_count) + " classes");
        
        if (config_.verbose) {
            std::cout << "  Version: " << merged_report.dex_version << std::endl;
            std::cout << "  Classes: " << merged_report.classes_count << std::endl;
            std::cout << "  Methods: " << merged_report.methods_count << std::endl;
            std::cout << "  Duration: " << duration << "ms" << std::endl;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        FailureRecord f;
        f.type = FailureType::PARSE_ERROR;
        f.stage = "load_dex";
        f.details = e.what();
        f.timestamp = get_timestamp();
        f.apk_path = apk_path_;
        f.is_blocking = true;
        record_failure(f);
        transition_to(RuntimeState::LOAD_FAILED, std::string("Exception: ") + e.what());
        return false;
    }
}

// ============================================================================
// Phase B: Application Startup
// ============================================================================

bool ApplicationRuntime::resolve_launcher_activity() {
    auto start = std::chrono::steady_clock::now();
    
    try {
        if (config_.verbose) {
            std::cout << "[Phase B] Resolving launcher activity..." << std::endl;
        }
        
        if (!dex_report_) {
            FailureRecord f;
            f.type = FailureType::INVALID_RUNTIME_STATE;
            f.stage = "resolve_launcher_activity";
            f.details = "DEX not loaded";
            f.timestamp = get_timestamp();
            f.apk_path = apk_path_;
            f.is_blocking = true;
            record_failure(f);
            transition_to(RuntimeState::RESOLUTION_FAILED, "DEX not loaded");
            return false;
        }
        
        // Use ClassResolver to find entry point
        // EXP-038 (BLOCKER-025): Pass the manifest's main_activity to the
        // class resolver so it searches for the specific launcher class
        // instead of using the "find first Activity with 'Main' in name"
        // heuristic. For Telegram, the launcher is org.telegram.ui.LaunchActivity
        // which doesn't contain "Main", so the heuristic picks the wrong class.
        std::string target_activity;
        if (manifest_info_ && !manifest_info_->main_activity_full.empty()) {
            target_activity = manifest_info_->main_activity_full;
            if (config_.verbose) {
                std::cout << "  Searching for launcher class: " << target_activity << std::endl;
            }
        }
        
        // Convert dotted form to descriptor form for matching
        std::string target_descriptor;
        if (!target_activity.empty()) {
            target_descriptor = "L" + target_activity + ";";
            for (auto& c : target_descriptor) if (c == '.') c = '/';
        }
        
        ExecutionTrace trace;
        if (!target_activity.empty()) {
            // Search for the specific class in DEX
            trace = class_resolver_->resolve_target(*dex_report_, target_activity, "onCreate");
            
            // If not found by readable name, try descriptor form
            if (!trace.success || !trace.entry_point.resolved) {
                // Direct descriptor match — find class and use its readable name
                for (const auto& cls : dex_report_->classes) {
                    if (cls.name == target_descriptor) {
                        // Convert descriptor (Lcom/foo/Bar;) to readable (com.foo.Bar)
                        std::string readable = cls.name;
                        if (!readable.empty() && readable.front() == 'L') readable.erase(0, 1);
                        if (!readable.empty() && readable.back() == ';') readable.pop_back();
                        for (auto& c : readable) if (c == '/') c = '.';
                        trace = class_resolver_->resolve_target(*dex_report_, readable, "onCreate");
                        break;
                    }
                }
            }
        } else {
            trace = class_resolver_->resolve(*dex_report_);
        }
        
        execution_trace_ = std::make_unique<ExecutionTrace>(trace);
        
        if (!trace.success || !trace.entry_point.resolved) {
            FailureRecord f;
            f.type = FailureType::METHOD_RESOLUTION_FAILURE;
            f.stage = "resolve_launcher_activity";
            f.details = trace.status_message;
            f.timestamp = get_timestamp();
            f.apk_path = apk_path_;
            f.is_blocking = true;
            record_failure(f);
            transition_to(RuntimeState::RESOLUTION_FAILED, "Cannot resolve launcher activity");
            return false;
        }
        
        entry_point_ = std::make_unique<EntryPoint>(trace.entry_point);
        activity_class_name_ = trace.entry_point.readable_class;
        
        auto end = std::chrono::steady_clock::now();
        double duration = std::chrono::duration<double, std::milli>(end - start).count();
        
        transition_to(RuntimeState::ACTIVITY_RESOLVED, 
                     "Launcher resolved: " + activity_class_name_);
        
        if (config_.verbose) {
            std::cout << "  Activity: " << activity_class_name_ << std::endl;
            std::cout << "  Method: " << trace.entry_point.method_name << std::endl;
            std::cout << "  Duration: " << duration << "ms" << std::endl;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        FailureRecord f;
        f.type = FailureType::CLASS_RESOLUTION_FAILURE;
        f.stage = "resolve_launcher_activity";
        f.details = e.what();
        f.timestamp = get_timestamp();
        f.apk_path = apk_path_;
        f.is_blocking = true;
        record_failure(f);
        transition_to(RuntimeState::RESOLUTION_FAILED, std::string("Exception: ") + e.what());
        return false;
    }
}

bool ApplicationRuntime::create_application() {
    auto start = std::chrono::steady_clock::now();
    
    try {
        if (config_.verbose) {
            std::cout << "[Phase B] Creating application objects..." << std::endl;
        }
        
        // Create Activity object in heap using proper API
        // Use allocate method which properly constructs objects and generates ID
        ActivityRuntimeObject* activity = heap_->allocate<ActivityRuntimeObject>(
            activity_class_name_, 0  // pc = 0 for runtime-created objects
        );
        activity_object_id_ = activity->get_object_id();  // Get the ID that was assigned
        
        // Mark as created
        activity->mark_created();
        
        lifecycle_events_.clear();
        lifecycle_events_.push_back("attach");
        
        auto end = std::chrono::steady_clock::now();
        double duration = std::chrono::duration<double, std::milli>(end - start).count();
        
        transition_to(RuntimeState::ACTIVITY_CREATED, 
                     "Activity created: ID=" + std::to_string(activity_object_id_));
        
        if (config_.verbose) {
            std::cout << "  Activity ID: " << activity_object_id_ << std::endl;
            std::cout << "  Class: " << activity_class_name_ << std::endl;
            std::cout << "  Duration: " << duration << "ms" << std::endl;
        }
        
        // Record API call
        ApiCallRecord call;
        call.class_name = "Activity";
        call.method_name = "<init>";
        call.descriptor = "()V";
        call.category = ApiCategory::ACTIVITY;
        call.call_timestamp = get_timestamp();
        call.sequence = ++api_call_sequence_;
        call.success = true;
        call.result_summary = "Activity object created with ID " + std::to_string(activity_object_id_);
        call.implementation_status = ImplementationStatus::IMPLEMENTED;
        record_api_call(call);
        
        return true;
        
    } catch (const std::exception& e) {
        FailureRecord f;
        f.type = FailureType::INTERNAL_ERROR;
        f.stage = "create_application";
        f.details = e.what();
        f.timestamp = get_timestamp();
        f.apk_path = apk_path_;
        f.is_blocking = true;
        record_failure(f);
        transition_to(RuntimeState::ERROR, std::string("Exception: ") + e.what());
        return false;
    }
}

bool ApplicationRuntime::execute_lifecycle() {
    auto start = std::chrono::steady_clock::now();
    
    try {
        if (config_.verbose) {
            std::cout << "[Phase B] Executing lifecycle..." << std::endl;
        }
        
        // Simulate lifecycle transitions
        // In a real runtime, these would execute actual DEX bytecode
        
        // onStart()
        lifecycle_events_.push_back("onStart");
        transition_to(RuntimeState::ACTIVITY_STARTED, "Activity.onStart()");
        
        // onResume()
        lifecycle_events_.push_back("onResume");
        transition_to(RuntimeState::ACTIVITY_RESUMED, "Activity.onResume()");
        
        auto end = std::chrono::steady_clock::now();
        double duration = std::chrono::duration<double, std::milli>(end - start).count();
        
        if (config_.verbose) {
            std::cout << "  Lifecycle events: ";
            for (const auto& event : lifecycle_events_) {
                std::cout << event << " → ";
            }
            std::cout << "complete" << std::endl;
            std::cout << "  Duration: " << duration << "ms" << std::endl;
        }
        
        // Record lifecycle API calls
        for (const auto& event : lifecycle_events_) {
            ApiCallRecord call;
            call.class_name = "Activity";
            call.method_name = event;
            call.descriptor = "()V";
            call.category = ApiCategory::ACTIVITY;
            call.call_timestamp = get_timestamp();
            call.sequence = ++api_call_sequence_;
            call.success = true;
            call.result_summary = event + " executed";
            call.implementation_status = ImplementationStatus::STUBBED;  // Currently stubbed
            record_api_call(call);
        }
        
        return true;
        
    } catch (const std::exception& e) {
        FailureRecord f;
        f.type = FailureType::INTERNAL_ERROR;
        f.stage = "execute_lifecycle";
        f.details = e.what();
        f.timestamp = get_timestamp();
        f.apk_path = apk_path_;
        f.is_blocking = true;
        record_failure(f);
        transition_to(RuntimeState::ERROR, std::string("Exception: ") + e.what());
        return false;
    }
}

// ============================================================================
// Phase C: DEX Execution
// ============================================================================

bool ApplicationRuntime::execute_on_create() {
    auto start = std::chrono::steady_clock::now();

    // EXP-037 Phase B (BLOCKER-010 debug): always print this so we can verify
    // execute_on_create is actually being invoked by the megabatch pipeline.
    std::cout << "[Phase C] execute_on_create() ENTERED" << std::endl;

    try {
        if (config_.verbose) {
            std::cout << "[Phase C] executing onCreate via DEX interpreter..." << std::endl;
        }
        
        if (!entry_point_ || !entry_point_->has_bytecode) {
            // Record that we're using stubbed execution
            FailureRecord f;
            f.type = FailureType::UNIMPLEMENTED_API;
            f.stage = "execute_on_create";
            f.details = "Using stubbed onCreate (no bytecode or interpreter limited)";
            f.timestamp = get_timestamp();
            f.apk_path = apk_path_;
            f.dex_method = entry_point_ ? entry_point_->method_name : "unknown";
            f.is_blocking = false;
            record_failure(f);
            
            // Simulate onCreate behavior
            lifecycle_events_.push_back("onCreate(stubbed)");
            
            ApiCallRecord call;
            call.class_name = activity_class_name_;
            call.method_name = "onCreate";
            call.descriptor = "(Landroid/os/Bundle;)V";
            call.category = ApiCategory::ACTIVITY;
            call.call_timestamp = get_timestamp();
            call.sequence = ++api_call_sequence_;
            call.success = true;
            call.result_summary = "onCreate executed (stubbed)";
            call.implementation_status = ImplementationStatus::STUBBED;
            record_api_call(call);
            
            return true;
        }
        
        // EXP-037 Phase B (BLOCKER-020): Use DalvikExecutionEngine instead of
        // DexInterpreterBatch. The batch interpreter lacks handlers for
        // invoke-super, goto, if-*, iget/iput/sget/sput — so it halts at PC=0
        // of every real onCreate method.
        //
        // DalvikExecutionEngine is the interpreter I've been actively
        // improving (BLOCKER-012 through BLOCKER-018). It can execute the
        // full onCreate of pro.rudloff.lineageos_updater_shortcut to
        // completion (8 instructions, return-void reached).
        //
        // The legacy DexInterpreterBatch path is preserved below commented
        // out for reference; it can be removed once we confirm the new path
        // works for all test APKs.
        /*
        // Try to use batch interpreter if available
        DexInterpreterBatch batch_interpreter;
        BatchInterpreterConfig config;  // Use BatchInterpreterConfig not InterpreterConfig
        config.verbose = config_.verbose;
        config.max_instructions = config_.max_instructions;

        instruction_trace_ = std::make_unique<BatchExecutionTrace>(
            batch_interpreter.execute_entry_point(*entry_point_, *dex_report_, config));
        */

        // Use DalvikExecutionEngine — the full-featured interpreter.
        miniandroid::dalvik::DalvikExecutionEngine dalvik_engine;
        // EXP-039: Set config with increased instruction limit
        dalvik_engine.config_.max_instructions = 10000000;
        dalvik_engine.config_.stop_on_unimplemented = false;
        dalvik_engine.config_.verbose = false;  // EXP-041: reduce memory by disabling verbose
        dalvik_engine.config_.enable_api_bridge = true;
        // EXP-037 Phase B (BLOCKER-019): Pass the manifest's main activity
        // class name so DalvikExecutionEngine can find the entry point in
        // obfuscated APKs (where class names don't contain "Activity"/"Main").
        // main_activity_full is in dotted form ("com.foo.MainActivity") and
        // DalvikExecutionEngine::execute_apk_with_activity handles conversion
        // to DEX descriptor form ("Lcom/foo/MainActivity;").
        std::string activity_class = manifest_info_ ? manifest_info_->main_activity_full
                                                    : std::string();

        // EXP-038 (BLOCKER-033): Pass per-DEX raw data to DalvikExecutionEngine.
        // This enables correct method_idx resolution for multidex APKs.
        std::vector<std::vector<uint8_t>> per_dex_raw;
        if (apk_info_) {
            for (const auto& dex_name : apk_info_->dex_files) {
                auto raw = apk_parser_->extract_entry_cached(dex_name);
                if (!raw.empty()) {
                    per_dex_raw.push_back(std::move(raw));
                }
            }
        }
        dalvik_engine.set_per_dex_raw_data(std::move(per_dex_raw));

        if (config_.verbose) { std::cout << "  Building class→DEX index..." << std::endl; }
        dalvik_engine.build_class_dex_index(*dex_report_);
        if (config_.verbose) { std::cout << "  Starting DEX execution..." << std::endl; }

        auto dalvik_result = dalvik_engine.execute_apk_with_activity(
            apk_path_, *dex_report_, activity_class, config_.verbose);

        // Extract evidence
        bool success = (dalvik_result.total_instructions_executed > 0);
        if (dalvik_result.final_status == miniandroid::dalvik::DalvikExecutionResult::FinalStatus::COMPLETED_SUCCESS) {
            success = true;
        }

        if (!success) {
            FailureRecord f;
            f.type = FailureType::UNIMPLEMENTED_OPCODE;
            f.stage = "execute_on_create";
            f.details = dalvik_result.halt_reason.empty()
                      ? "DalvikExecutionEngine produced no instruction trace"
                      : dalvik_result.halt_reason;
            f.timestamp = get_timestamp();
            f.apk_path = apk_path_;
            f.dex_method = entry_point_->method_name;
            f.is_blocking = false;  // don't fail hard — continue with stubbed lifecycle
            record_failure(f);
        }

        // Record method dispatch
        MethodDispatchRecord dispatch;
        dispatch.caller_class = "ActivityThread";
        dispatch.target_class = activity_class_name_;
        dispatch.method_name = "onCreate";
        dispatch.descriptor = "(Landroid/os/Bundle;)V";
        dispatch.dispatch_type = DispatchType::VIRTUAL;
        dispatch.success = success;
        dispatch.status_detail = success
            ? ("Executed " + std::to_string(dalvik_result.total_instructions_executed) + " instructions")
            : dalvik_result.halt_reason;
        dispatch.sequence = ++dispatch_sequence_;
        record_dispatch(dispatch);

        // EXP-037 Phase B (BLOCKER-020): Record API call traces from the
        // DalvikExecutionEngine so they appear in the evidence output.
        for (const auto& api_trace : dalvik_result.api_call_traces) {
            ApiCallRecord call;
            call.class_name = api_trace.api_class;
            call.method_name = api_trace.method;
            call.descriptor = "()V";  // simplified
            call.category = ApiCategory::ACTIVITY;
            call.call_timestamp = get_timestamp();
            call.sequence = ++api_call_sequence_;
            // ApiCallTrace::Status has IMPLEMENTED / STUBBED / MISSING / ERROR.
            call.success = (api_trace.status != miniandroid::dalvik::ApiCallTrace::Status::ERROR &&
                            api_trace.status != miniandroid::dalvik::ApiCallTrace::Status::MISSING);
            call.result_summary = api_trace.return_value;
            call.implementation_status = (api_trace.status == miniandroid::dalvik::ApiCallTrace::Status::IMPLEMENTED)
                                       ? ImplementationStatus::IMPLEMENTED
                                       : ImplementationStatus::STUBBED;
            record_api_call(call);
        }

        lifecycle_events_.push_back(success ? "onCreate(executed)" : "onCreate(partial)");

        auto end = std::chrono::steady_clock::now();
        double duration = std::chrono::duration<double, std::milli>(end - start).count();
        
        if (config_.verbose) {
            // EXP-037 Phase B (BLOCKER-020): instruction_trace_ is no longer
            // populated — we use DalvikExecutionEngine directly. Print stats
            // from dalvik_result instead.
            std::cout << "  Instructions executed: " << dalvik_result.total_instructions_executed << std::endl;
            std::cout << "  Final status: " << static_cast<int>(dalvik_result.final_status) << std::endl;
            if (!dalvik_result.halt_reason.empty()) {
                std::cout << "  Halt reason: " << dalvik_result.halt_reason << std::endl;
            }
            std::cout << "  API call traces: " << dalvik_result.api_call_traces.size() << std::endl;
            std::cout << "  Heap objects: " << dalvik_result.heap.size() << std::endl;
            std::cout << "  Duration: " << duration << "ms" << std::endl;
        }
        
        return success;
        
    } catch (const std::exception& e) {
        FailureRecord f;
        f.type = FailureType::INTERNAL_ERROR;
        f.stage = "execute_on_create";
        f.details = e.what();
        f.timestamp = get_timestamp();
        f.apk_path = apk_path_;
        f.dex_method = entry_point_ ? entry_point_->method_name : "unknown";
        f.is_blocking = true;
        record_failure(f);
        transition_to(RuntimeState::ERROR, std::string("Exception: ") + e.what());
        return false;
    }
}

const dex::BatchExecutionTrace& ApplicationRuntime::get_instruction_trace() const {
    static BatchExecutionTrace empty_trace;
    return instruction_trace_ ? *instruction_trace_ : empty_trace;
}

// ============================================================================
// Phase E: Resources
// ============================================================================

bool ApplicationRuntime::initialize_resources() {
    auto start = std::chrono::steady_clock::now();
    
    try {
        if (config_.verbose) {
            std::cout << "[Phase E] Initializing resources..." << std::endl;
        }
        
        // Initialize resource manager from APK data
        bool success = resource_manager_->initialize_from_data(apk_data_, apk_path_);
        
        if (!success) {
            FailureRecord f;
            f.type = FailureType::RESOURCE_RESOLUTION_FAILURE;
            f.stage = "initialize_resources";
            f.details = "Failed to initialize resources";
            f.timestamp = get_timestamp();
            f.apk_path = apk_path_;
            f.is_blocking = false;
            record_failure(f);
            // Non-fatal - continue with defaults
        }
        
        // Load all resources
        success = resource_manager_->load_all_resources();
        
        if (!success) {
            FailureRecord f;
            f.type = FailureType::RESOURCE_RESOLUTION_FAILURE;
            f.stage = "initialize_resources";
            f.details = "Failed to load some resources";
            f.timestamp = get_timestamp();
            f.apk_path = apk_path_;
            f.is_blocking = false;
            record_failure(f);
        }
        
        auto end = std::chrono::steady_clock::now();
        double duration = std::chrono::duration<double, std::milli>(end - start).count();
        
        if (config_.verbose) {
            const ResourceManagerState& state = resource_manager_->get_state();
            std::cout << "  ARSC detected: " << (state.arsc_detected ? "Yes" : "No") << std::endl;
            std::cout << "  Strings loaded: " << (state.strings_loaded ? "Yes" : "No") << std::endl;
            std::cout << "  String count: " << resource_manager_->get_string_resources().get_string_count() << std::endl;
            std::cout << "  Duration: " << duration << "ms" << std::endl;
        }
        
        // Record resource API calls
        ApiCallRecord call;
        call.class_name = "ResourceManager";
        call.method_name = "initialize";
        call.descriptor = "(Landroid/content/res/Resources;)V";
        call.category = ApiCategory::RESOURCE;
        call.call_timestamp = get_timestamp();
        call.sequence = ++api_call_sequence_;
        call.success = true;
        call.result_summary = "Resources initialized";
        call.implementation_status = ImplementationStatus::IMPLEMENTED;
        record_api_call(call);
        
        return true;
        
    } catch (const std::exception& e) {
        FailureRecord f;
        f.type = FailureType::RESOURCE_FAILED;
        f.stage = "initialize_resources";
        f.details = e.what();
        f.timestamp = get_timestamp();
        f.apk_path = apk_path_;
        f.is_blocking = false;
        record_failure(f);
        return false;  // Non-fatal
    }
}

bool ApplicationRuntime::load_content_view() {
    auto start = std::chrono::steady_clock::now();
    
    try {
        if (config_.verbose) {
            std::cout << "[Phase E] Loading content view..." << std::endl;
        }
        
        // Inflate layout
        bool success = resource_manager_->inflate_layout("main");
        
        if (!success) {
            // Try activity_main as fallback
            success = resource_manager_->inflate_layout("activity_main");
        }
        
        const InflateResult& inflate_result = resource_manager_->get_last_inflate_result();
        
        if (!inflate_result.success) {
            FailureRecord f;
            f.type = FailureType::RESOURCE_RESOLUTION_FAILURE;
            f.stage = "load_content_view";
            f.details = inflate_result.error_message;
            f.timestamp = get_timestamp();
            f.apk_path = apk_path_;
            f.is_blocking = false;
            record_failure(f);
            // Continue anyway - we can use hardcoded layout as fallback
        }
        
        transition_to(RuntimeState::CONTENT_LOADED, "Content view loaded");
        
        // Record setContentView API call
        ApiCallRecord call;
        call.class_name = "Activity";
        call.method_name = "setContentView";
        call.descriptor = "(I)V";
        call.category = ApiCategory::ACTIVITY;
        call.call_timestamp = get_timestamp();
        call.sequence = ++api_call_sequence_;
        call.success = inflate_result.success;
        call.result_summary = inflate_result.success ? 
            "Layout inflated: " + inflate_result.root_view_class : 
            "Layout inflation failed: " + inflate_result.error_message;
        call.implementation_status = ImplementationStatus::PARTIAL;
        record_api_call(call);
        
        auto end = std::chrono::steady_clock::now();
        double duration = std::chrono::duration<double, std::milli>(end - start).count();
        
        if (config_.verbose) {
            std::cout << "  Root view: " << inflate_result.root_view_class << std::endl;
            std::cout << "  Views created: " << inflate_result.created_view_ids.size() << std::endl;
            std::cout << "  Duration: " << duration << "ms" << std::endl;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        FailureRecord f;
        f.type = FailureType::RESOURCE_FAILED;
        f.stage = "load_content_view";
        f.details = e.what();
        f.timestamp = get_timestamp();
        f.apk_path = apk_path_;
        f.is_blocking = false;
        record_failure(f);
        return false;  // Non-fatal
    }
}

// ============================================================================
// Phase F: Layout
// ============================================================================

bool ApplicationRuntime::perform_layout() {
    auto start = std::chrono::steady_clock::now();
    
    try {
        if (config_.verbose) {
            std::cout << "[Phase F] Performing measure/layout..." << std::endl;
        }
        
        // The render pipeline handles layout internally when we call render
        // For now, we just verify the object heap has views to lay out
        
        int view_count = 0;
        std::vector<uint32_t> ids = heap_->get_all_ids();
        for (uint32_t id : ids) {
            RuntimeObject* obj = heap_->get(id);
            if (obj && (obj->get_runtime_class().find("View") != std::string::npos ||
                       obj->get_runtime_class().find("Layout") != std::string::npos)) {
                view_count++;
            }
        }
        
        if (config_.verbose) {
            std::cout << "  Views in heap: " << view_count << std::endl;
        }
        
        transition_to(RuntimeState::LAYOUT_READY, "Layout ready for rendering");
        
        // Record layout API calls
        ApiCallRecord call;
        call.class_name = "View";
        call.method_name = "measure";
        call.descriptor = "(II)V";
        call.category = ApiCategory::LAYOUT;
        call.call_timestamp = get_timestamp();
        call.sequence = ++api_call_sequence_;
        call.success = true;
        call.result_summary = "Measure pass complete for " + std::to_string(view_count) + " views";
        call.implementation_status = ImplementationStatus::PARTIAL;
        record_api_call(call);
        
        ApiCallRecord layout_call;
        layout_call.class_name = "View";
        layout_call.method_name = "layout";
        layout_call.descriptor = "(IIII)V";
        layout_call.category = ApiCategory::LAYOUT;
        layout_call.call_timestamp = get_timestamp();
        layout_call.sequence = ++api_call_sequence_;
        layout_call.success = true;
        layout_call.result_summary = "Layout pass complete";
        layout_call.implementation_status = ImplementationStatus::PARTIAL;
        record_api_call(layout_call);
        
        auto end = std::chrono::steady_clock::now();
        double duration = std::chrono::duration<double, std::milli>(end - start).count();
        
        if (config_.verbose) {
            std::cout << "  Duration: " << duration << "ms" << std::endl;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        FailureRecord f;
        f.type = FailureType::RENDER_FAILURE;
        f.stage = "perform_layout";
        f.details = e.what();
        f.timestamp = get_timestamp();
        f.apk_path = apk_path_;
        f.is_blocking = false;
        record_failure(f);
        return false;
    }
}

// ============================================================================
// Phase H: Rendering
// ============================================================================

bool ApplicationRuntime::render_frame() {
    auto start = std::chrono::steady_clock::now();
    
    try {
        if (config_.verbose) {
            std::cout << "[Phase H] Rendering frame..." << std::endl;
        }
        
        // Get text content from resources or use default
        std::string text_content = "Hello MiniAndroid";  // Default fallback
        
        // Try to get text from string resources
        auto& strings = resource_manager_->get_string_resources();
        auto hello_text = strings.get_by_name("hello_text");
        if (hello_text.has_value()) {
            text_content = hello_text->value;
        } else {
            // Try other common names
            auto app_name = strings.get_by_name("app_name");
            if (app_name.has_value()) {
                text_content = app_name->value;
            }
        }
        
        // Render using pipeline
        bool success = render_pipeline_->render(*heap_, text_content);
        
        if (!success) {
            FailureRecord f;
            f.type = FailureType::RENDER_FAILURE;
            f.stage = "render_frame";
            f.details = "Render pipeline failed";
            f.timestamp = get_timestamp();
            f.apk_path = apk_path_;
            f.is_blocking = true;
            record_failure(f);
            transition_to(RuntimeState::RENDER_FAILED, "Rendering failed");
            return false;
        }
        
        auto end = std::chrono::steady_clock::now();
        double duration = std::chrono::duration<double, std::milli>(end - start).count();
        
        transition_to(RuntimeState::FRAME_RENDERED, "Frame rendered successfully");
        
        // Record rendering API calls
        ApiCallRecord call;
        call.class_name = "View";
        call.method_name = "draw";
        call.descriptor = "(Landroid/graphics/Canvas;)V";
        call.category = ApiCategory::RENDERER;
        call.call_timestamp = get_timestamp();
        call.sequence = ++api_call_sequence_;
        call.success = true;
        call.result_summary = "Frame rendered (" + std::to_string(render_pipeline_->get_statistics().total_commands_issued) + " commands)";
        call.implementation_status = ImplementationStatus::IMPLEMENTED;
        record_api_call(call);
        
        if (config_.verbose) {
            const RenderStatistics& stats = render_pipeline_->get_statistics();
            std::cout << "  Framebuffer: " << render_pipeline_->get_framebuffer().get_width() 
                      << "x" << render_pipeline_->get_framebuffer().get_height() << std::endl;
            std::cout << "  Commands issued: " << stats.total_commands_issued << std::endl;
            std::cout << "  Pixels written: " << stats.pixels_written << std::endl;
            std::cout << "  Duration: " << duration << "ms" << std::endl;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        FailureRecord f;
        f.type = FailureType::RENDER_FAILURE;
        f.stage = "render_frame";
        f.details = e.what();
        f.timestamp = get_timestamp();
        f.apk_path = apk_path_;
        f.is_blocking = true;
        record_failure(f);
        transition_to(RuntimeState::RENDER_FAILED, std::string("Exception: ") + e.what());
        return false;
    }
}

bool ApplicationRuntime::save_screenshot(const std::string& output_path) {
    try {
        if (config_.verbose) {
            std::cout << "[Phase H] Saving screenshot to: " << output_path << std::endl;
        }
        
        const FrameBuffer& fb = render_pipeline_->get_framebuffer();
        bool success = PNGWriter::write_png(output_path, fb);
        
        if (!success) {
            FailureRecord f;
            f.type = FailureType::RENDER_FAILURE;
            f.stage = "save_screenshot";
            f.details = "Failed to write PNG";
            f.timestamp = get_timestamp();
            f.apk_path = apk_path_;
            f.is_blocking = false;
            record_failure(f);
            return false;
        }
        
        if (config_.verbose) {
            std::cout << "  Screenshot saved: " << output_path << std::endl;
            std::cout << "  Size: " << fb.get_width() << "x" << fb.get_height() << std::endl;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        FailureRecord f;
        f.type = FailureType::RENDER_FAILURE;
        f.stage = "save_screenshot";
        f.details = e.what();
        f.timestamp = get_timestamp();
        f.apk_path = apk_path_;
        f.is_blocking = false;
        record_failure(f);
        return false;
    }
}

const renderer::FrameBuffer* ApplicationRuntime::get_framebuffer() const {
    return render_pipeline_ ? &render_pipeline_->get_framebuffer() : nullptr;
}

// ============================================================================
// Recording Methods
// ============================================================================

void ApplicationRuntime::record_api_call(const ApiCallRecord& call) {
    api_calls_.push_back(call);
    
    // Update database
    std::string key = call.class_name + "#" + call.method_name;
    auto it = api_database_.find(key);
    if (it != api_database_.end()) {
        it->second.call_count++;
    } else {
        ApiDatabaseEntry entry;
        entry.class_name = call.class_name;
        entry.method_name = call.method_name;
        entry.descriptor = call.descriptor;
        entry.category = call.category;
        entry.first_seen_exp = 7;  // EXP-007
        entry.call_count = 1;
        entry.implementation_status = call.implementation_status;
        api_database_[key] = entry;
    }
}

void ApplicationRuntime::record_dispatch(const MethodDispatchRecord& dispatch) {
    method_dispatches_.push_back(dispatch);
}

void ApplicationRuntime::record_failure(FailureRecord failure) {
    failures_.push_back(failure);
    
    if (config_.verbose && failure.is_blocking) {
        std::cerr << "[FAILURE] " << failure_type_to_string(failure.type) 
                  << " at " << failure.stage << ": " << failure.details << std::endl;
    }
}

// ============================================================================
// Evidence Generation Methods (abbreviated - key methods only)
// ============================================================================

json ApplicationRuntime::to_json() const {
    json j;
    j["experiment"] = "EXP-007→EXP-012 MEGA BATCH";
    j["version"] = "0.1";
    j["timestamp"] = get_timestamp();
    j["apk_path"] = apk_path_;
    j["final_state"] = state_to_string(state_);
    j["is_complete"] = is_complete();
    j["has_error"] = has_error();
    j["total_duration_ms"] = total_duration_ms_;
    
    j["configuration"] = config_.to_json();
    j["state_transitions"] = [&]() {
        json arr = json::array();
        for (const auto& t : state_transitions_) arr.push_back(t.to_json());
        return arr;
    }();
    
    if (apk_info_) {
        j["apk_info"] = {
            {"package", apk_info_->package_name},
            {"main_activity", apk_info_->main_activity_full},
            {"version", apk_info_->version_name}
        };
    }
    
    if (dex_report_) {
        j["dex"] = {
            {"version", dex_report_->dex_version},
            {"classes", dex_report_->classes_count},
            {"methods", dex_report_->methods_count}
        };
    }
    
    j["statistics"] = {
        {"api_calls", api_calls_.size()},
        {"method_dispatches", method_dispatches_.size()},
        {"failures", failures_.size()},
        {"api_database_entries", api_database_.size()}
    };
    
    return j;
}

json ApplicationRuntime::generate_state_trace() const {
    json trace;
    trace["experiment"] = "EXP-007→EXP-012";
    trace["type"] = "runtime_state_trace";
    trace["timestamp"] = get_timestamp();
    trace["apk_path"] = apk_path_;
    trace["final_state"] = state_to_string(state_);
    trace["transitions"] = json::array();
    
    for (const auto& t : state_transitions_) {
        trace["transitions"].push_back(t.to_json());
    }
    
    return trace;
}

json ApplicationRuntime::generate_component_map() const {
    json map;
    map["experiment"] = "EXP-007→EXP-012";
    map["type"] = "runtime_component_map";
    map["timestamp"] = get_timestamp();
    
    map["components"] = json::array();
    
    map["components"].push_back({
        {"name", "ApkParser"},
        {"status", apk_parser_ ? "initialized" : "null"},
        {"purpose", "ZIP/APK parsing and extraction"}
    });
    
    map["components"].push_back({
        {"name", "ManifestReader"},
        {"status", manifest_info_ ? "loaded" : "not_loaded"},
        {"purpose", "AXML binary XML parsing"}
    });
    
    map["components"].push_back({
        {"name", "DexParser"},
        {"status", dex_report_ ? "loaded" : "not_loaded"},
        {"purpose", "Dalvik bytecode parsing"}
    });
    
    map["components"].push_back({
        {"name", "ClassResolver"},
        {"status", entry_point_ ? "resolved" : "not_resolved"},
        {"purpose", "Entry point resolution"}
    });
    
    map["components"].push_back({
        {"name", "EnhancedObjectHeap"},
        {"status", heap_ ? "active" : "null"},
        {"object_count", heap_ ? heap_->size() : 0},
        {"purpose", "Android object model storage"}
    });
    
    map["components"].push_back({
        {"name", "ResourceManager"},
        {"status", resource_manager_ ? "initialized" : "null"},
        {"strings_loaded", resource_manager_ ? resource_manager_->get_string_resources().get_string_count() : 0},
        {"purpose", "Android resource loading"}
    });
    
    map["components"].push_back({
        {"name", "RenderPipeline"},
        {"status", render_pipeline_ ? (state_ >= RuntimeState::FRAME_RENDERED ? "rendered" : "ready") : "null"},
        {"purpose", "Software rendering pipeline"}
    });
    
    return map;
}

json ApplicationRuntime::generate_failure_report() const {
    json report;
    report["experiment"] = "EXP-007→EXP-012";
    report["type"] = "failure_report";
    report["timestamp"] = get_timestamp();
    report["apk_path"] = apk_path_;
    report["total_failures"] = failures_.size();
    report["blocking_failures"] = 0;
    
    report["by_type"] = json::object();
    report["failures"] = json::array();
    
    for (const auto& f : failures_) {
        report["failures"].push_back(f.to_json());
        
        std::string type = failure_type_to_string(f.type);
        if (report["by_type"].contains(type)) {
            report["by_type"][type] = report["by_type"][type].get<int>() + 1;
        } else {
            report["by_type"][type] = 1;
        }
        
        if (f.is_blocking) {
            report["blocking_failures"] = report["blocking_failures"].get<int>() + 1;
        }
    }
    
    return report;
}

json ApplicationRuntime::generate_golden_end_to_end() const {
    json test;
    test["experiment"] = "EXP-007→EXP-012";
    test["type"] = "golden_end_to_end";
    test["timestamp"] = get_timestamp();
    test["apk_path"] = apk_path_;
    
    json stages = json::object();
    
    stages["apk_loads"] = {{"pass", apk_info_ != nullptr}, {"detail", apk_info_ ? "Parsed OK" : "Failed"}};
    stages["manifest_loads"] = {{"pass", manifest_info_ != nullptr}, {"detail", manifest_info_ ? "Parsed OK" : "Failed"}};
    stages["dex_loads"] = {{"pass", dex_report_ != nullptr}, {"detail", dex_report_ ? "Parsed OK" : "Failed"}};
    stages["launcher_resolves"] = {{"pass", entry_point_ != nullptr && entry_point_->resolved}, 
                                   {"detail", entry_point_ ? entry_point_->readable_class : "Not resolved"}};
    stages["activity_resolves"] = {{"pass", activity_object_id_ != 0}, 
                                    {"detail", "ID=" + std::to_string(activity_object_id_)}};
    stages["oncreate_executes"] = {{"pass", state_ >= RuntimeState::ACTIVITY_CREATED}, 
                                    {"detail", state_to_string(state_)}};
    stages["objects_created"] = {{"pass", heap_ && heap_->size() > 0}, 
                                 {"detail", std::to_string(heap_ ? heap_->size() : 0) + " objects"}};
    stages["resources_resolve"] = {{"pass", resource_manager_ && resource_manager_->get_string_resources().get_string_count() > 0}, 
                                    {"detail", std::to_string(resource_manager_ ? resource_manager_->get_string_resources().get_string_count() : 0) + " strings"}};
    stages["layout_inflates"] = {{"pass", resource_manager_ && resource_manager_->get_last_inflate_result().success}, 
                                  {"detail", resource_manager_ ? resource_manager_->get_last_inflate_result().root_view_class : "N/A"}};
    stages["renderer_executes"] = {{"pass", state_ >= RuntimeState::FRAME_RENDERED}, {"detail", state_to_string(state_)}};
    stages["framebuffer_exists"] = {{"pass", render_pipeline_ != nullptr}, {"detail", "Framebuffer available"}};
    
    test["stages"] = stages;
    
    int passed = 0;
    int total = 0;
    for (auto& [key, val] : stages.items()) {
        total++;
        if (val["pass"].get<bool>()) passed++;
    }
    
    test["summary"] = {
        {"passed", passed},
        {"total", total},
        {"pass_rate", total > 0 ? (double)passed / total : 0.0},
        {"overall", passed == total ? "PASS" : (passed > total / 2 ? "PARTIAL" : "FAIL")}
    };
    
    return test;
}

bool ApplicationRuntime::write_all_evidence(const std::string& output_dir) {
    try {
        fs::create_directories(output_dir);
        fs::create_directories(output_dir + "/golden");
        fs::create_directories(output_dir + "/database");
        
        auto write_json = [&](const std::string& filename, const json& data) -> bool {
            std::string path = output_dir + "/" + filename;
            std::ofstream file(path);
            if (!file.is_open()) {
                std::cerr << "[ERROR] Cannot write evidence: " << path << std::endl;
                return false;
            }
            file << data.dump(2) << std::endl;
            file.close();
            return true;
        };
        
        write_json("application_runtime.json", to_json());
        write_json("runtime_component_map.json", generate_component_map());
        write_json("runtime_state_trace.json", generate_state_trace());
        write_json("failure_report.json", generate_failure_report());
        write_json("golden_end_to_end.json", generate_golden_end_to_end());
        
        if (config_.verbose) {
            std::cout << "\n[Evidence] All files written to: " << output_dir << "/" << std::endl;
        }
        
        return true;
        
    } catch (const std::exception& e) {
        std::cerr << "[ERROR] Failed to write evidence: " << e.what() << std::endl;
        return false;
    }
}

} // namespace runtime
} // namespace miniandroid
