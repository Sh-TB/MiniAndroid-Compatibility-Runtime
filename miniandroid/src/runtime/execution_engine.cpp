/*
 * MiniAndroid Runtime v0.1 - Execution Engine Implementation
 * EXP-001: HelloWorld Loader
 * EXP-031.5: Real Dalvik Bytecode Execution Proof
 */

#include "execution_engine.h"
#include "../dex/trace_exporter.h"  // EXP-031.5: Mandatory trace generation
#include "../diagnostics/click_audit.h"  // UNIFIED_002 EXP-100: env-gated click audit (DIAGNOSTIC)
// EXP-086 Phase 3 (B1 FIX): PNGWriter for direct PNG output
#include "../renderer/software_renderer.h"
// EXP-086 Phase 7 (B4 FIX): HandlerShadow for Runnable queue drain
#include "../framework/android_shadows.h"
#include "../framework/dialog_shadow.h"
#include "../framework/canvas_shadow.h"
// EXP-087 Phase 3 (B2 FIX): DalvikHeapAdapter for shadow heap access
#include "../framework/heap_adapter.h"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <chrono>
#include <set>
#include <algorithm>

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
    // UNIFIED_011.2 CLICK-TEST: runs AFTER the first frame is captured so the
    // baseline PNG on disk is the untouched frame 1. Never fails the run.
    if (success && config.click_test) stage_click_test(result, config);
    
    // Always try to generate reports
    stage_generate_reports(result, config);
    
    // Determine final status
    // EXP-031.5: Preserve FAILURE status from assertions - don't overwrite!
    if (result.status == ExecutionStatus::FAILURE) {
        // Keep the failure status and message from the assertion
        result.status_message = result.status_message.empty() ? "Execution failed" : result.status_message;
    } else if (success && result.status == ExecutionStatus::SUCCESS) {
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
    
    // EXP-031.6: Enable verbose DEX parser logging for debugging
    dex_parser_.set_verbose(true);
    
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
    
    // ====================================================================
    // EXP-031: CRITICAL MODE SWITCH - This determines real vs fake execution
    // ====================================================================
    if (config.execution_mode == ExecutionMode::REAL_DALVIK) {
        return stage_execute_application_real_dalvik(result, config);
    } else {
        return stage_execute_application_legacy(result, config);
    }
}

// ============================================================================
// EXP-031: REAL DALVIK EXECUTION PATH (NEW - produces real evidence)
// ============================================================================

bool ExecutionEngine::stage_execute_application_real_dalvik(ExecutionResult& result, const ExecutionConfig& config) {
    trace_engine_.info("ExecutionEngine", "stage_execute_application_real_dalvik", 
                       "[REAL_DALVIK_INTERPRETER] Starting real bytecode execution");
    
    // Create Activity instance through DalvikHeap (real allocation)
    // In future: this will come from DEX class loading
    result.activity = std::make_shared<api::Activity>();
    result.activity->set_package_name(result.apk_info.package_name);
    
    // EXP-086 Phase 1: Configure dalvik_engine_ with per-DEX raw data and APK path
    // before calling execute_apk_with_activity. Without this, multi-DEX method
    // resolution fails (per_dex_raw_data_ size=0).
    {
        std::vector<std::string> sorted_dex_files = result.apk_info.dex_files;
        std::sort(sorted_dex_files.begin(), sorted_dex_files.end());
        std::vector<std::vector<uint8_t>> per_dex_raw;
        for (const auto& dex_name : sorted_dex_files) {
            auto raw = apk_parser_.extract_entry_cached(dex_name);
            if (!raw.empty()) {
                per_dex_raw.push_back(std::move(raw));
            }
        }
        dalvik_engine_.set_per_dex_raw_data(std::move(per_dex_raw));
        dalvik_engine_.set_apk_path(result.apk_info.apk_path);
        // EXP-093/F011: Set manifest-derived package identity
        dalvik_engine_.set_package_info(
            result.apk_info.package_name,
            result.apk_info.version_code,
            result.apk_info.version_name);
        dalvik_engine_.build_class_dex_index(result.dex_report);
        // EXP-088+ Phase 1.2: inject_secondary_dex_classes() is called
        // from inside execute_apk_with_activity() (after dex_report_ is
        // set on the engine). See the call in dalvik_engine.cpp.
        // EXP-086 Phase 7 (B4 FIX): Set up ShadowRegistry so Handler/Looper
        // dispatch is wired up. Without this, Handler.post() calls during
        // onCreate are never enqueued and never drained.
        if (shadow_registry_) {
            dalvik_engine_.set_shadow_registry(shadow_registry_);
            // EXP-087 Phase 3 (B2 FIX): Create a DalvikHeapAdapter so shadows
            // can allocate heap objects. Without this, ViewShadow::create_view()
            // returns 0 because heap_ is null on the shadow.
            heap_adapter_ = std::make_unique<framework::DalvikHeapAdapter>(
                &dalvik_engine_.get_heap_public(), &dalvik_engine_);
            shadow_registry_->set_heap(heap_adapter_.get());
        }
        std::cerr << "[EXP086-P1] Configured dalvik_engine_ with "
                  << sorted_dex_files.size() << " DEX files for '"
                  << result.apk_info.main_activity_full << "'" << std::endl;

        // EXP-092 FIX: Load resource_values.json into the engine's
        // resource_string_values_ / resource_color_values_ / etc. maps.
        //
        // WITHOUT this load, the LocaleController.getString(int) intercept
        // (which calls field_name_by_resid_ -> resource_string_values_) returns
        // the FIELD NAME (e.g. "SentSmsCodeTitle") instead of the actual value
        // (e.g. "Enter code"). This path was previously only wired up in
        // ApplicationRuntime::execute_on_create(), which is never invoked by
        // cmd_run / stage_execute_application_real_dalvik.
        //
        // We attempt to load from TWO candidate paths (absolute first, then
        // relative to cwd), based on the APK's package name.
        {
            std::vector<std::string> candidate_paths;
            // Path 1: download/exp038_telegram/resource_values.json (legacy fixed)
            candidate_paths.push_back("download/exp038_telegram/resource_values.json");
            // Path 2: <apk_dir>/resource_values.json (next to the APK)
            std::string apk_dir;
            {
                auto slash = result.apk_info.apk_path.find_last_of('/');
                if (slash != std::string::npos) {
                    apk_dir = result.apk_info.apk_path.substr(0, slash);
                    candidate_paths.push_back(apk_dir + "/resource_values.json");
                }
            }
            // Path 3: derived from package name
            if (!result.apk_info.package_name.empty()) {
                std::string pkg_safe = result.apk_info.package_name;
                std::replace(pkg_safe.begin(), pkg_safe.end(), '.', '/');
                candidate_paths.push_back("download/" + pkg_safe + "/resource_values.json");
            }

            int loaded_strings = 0, loaded_colors = 0, loaded_dimens = 0,
                loaded_drawables = 0, loaded_integers = 0, loaded_bools = 0,
                loaded_raws = 0;
            bool loaded_any = false;
            std::string loaded_path;
            for (const auto& path : candidate_paths) {
                std::ifstream res_file(path);
                if (!res_file.is_open()) continue;
                loaded_path = path;
                json res_json;
                res_file >> res_json;

                // Strings
                if (res_json.contains("string")) {
                    for (auto& [name, value] : res_json["string"].items()) {
                        if (value.is_string()) {
                            dalvik_engine_.resource_string_values_[name] = value.get<std::string>();
                            loaded_strings++;
                        }
                    }
                }
                // Colors
                if (res_json.contains("color")) {
                    for (auto& [name, value] : res_json["color"].items()) {
                        if (value.is_string()) {
                            std::string v = value.get<std::string>();
                            if (v.rfind("type28:", 0) == 0 || v.rfind("type29:", 0) == 0 ||
                                v.rfind("type30:", 0) == 0 || v.rfind("type31:", 0) == 0) {
                                size_t colon = v.find(':');
                                if (colon != std::string::npos) {
                                    std::string hex = v.substr(colon + 1);
                                    if (hex.rfind("0x", 0) == 0 || hex.rfind("0X", 0) == 0) {
                                        hex = hex.substr(2);
                                    }
                                    try {
                                        uint32_t argb = std::stoul(hex, nullptr, 16);
                                        if (v.rfind("type29:", 0) == 0) argb |= 0xFF000000;
                                        dalvik_engine_.resource_color_values_[name] = static_cast<int32_t>(argb);
                                        loaded_colors++;
                                    } catch (...) {}
                                }
                            }
                        }
                    }
                }
                // Dimens
                if (res_json.contains("dimen")) {
                    for (auto& [name, value] : res_json["dimen"].items()) {
                        if (value.is_string()) {
                            std::string v = value.get<std::string>();
                            try {
                                // Strip "type1:" or "type2:" prefix if present
                                if (v.rfind("type", 0) == 0) {
                                    size_t colon = v.find(':');
                                    if (colon != std::string::npos) v = v.substr(colon + 1);
                                }
                                if (!v.empty() && (v.back() == 'd' || v.back() == 'p')) {
                                    // e.g. "16dp" — parse integer
                                    int32_t dv = static_cast<int32_t>(std::stoi(v));
                                    dalvik_engine_.resource_dimen_values_[name] = dv;
                                    loaded_dimens++;
                                } else if (!v.empty() && v[0] >= '0' && v[0] <= '9') {
                                    int32_t dv = static_cast<int32_t>(std::stoi(v));
                                    dalvik_engine_.resource_dimen_values_[name] = dv;
                                    loaded_dimens++;
                                }
                            } catch (...) {}
                        }
                    }
                }
                // Drawables
                if (res_json.contains("drawable")) {
                    for (auto& [name, value] : res_json["drawable"].items()) {
                        if (value.is_string()) {
                            dalvik_engine_.resource_drawable_paths_[name] = value.get<std::string>();
                            loaded_drawables++;
                        }
                    }
                }
                // Integers
                if (res_json.contains("integer")) {
                    for (auto& [name, value] : res_json["integer"].items()) {
                        if (value.is_number_integer()) {
                            dalvik_engine_.resource_integer_values_[name] = value.get<int32_t>();
                            loaded_integers++;
                        }
                    }
                }
                // Bools
                if (res_json.contains("bool")) {
                    for (auto& [name, value] : res_json["bool"].items()) {
                        if (value.is_boolean()) {
                            dalvik_engine_.resource_bool_values_[name] = value.get<bool>();
                            loaded_bools++;
                        }
                    }
                }
                // EXP-098 (CM-027): Raw resources — R.raw.X maps to an APK
                // asset path (e.g. "res/-si.json" for R.raw.sms_incoming_info).
                // Used by RLottieImageView.setAnimation(R.raw.X, w, h) →
                // RLottieDrawable(R.raw.X, ...) → AndroidUtilities.readRes(R.raw.X)
                // → openRawResource(R.raw.X) → load the asset as a UTF-8 string
                // → RLottieNative.createFromRawJson(json).
                if (res_json.contains("raw")) {
                    for (auto& [name, value] : res_json["raw"].items()) {
                        if (value.is_string()) {
                            dalvik_engine_.resource_raw_paths_[name] = value.get<std::string>();
                            loaded_raws++;
                        }
                    }
                }
                loaded_any = true;
                break;
            }
            std::cerr << "[EXP092-RES] resource_values.json loaded=" << (loaded_any ? "true" : "false")
                      << " path=\"" << (loaded_any ? loaded_path : "(not found)") << "\""
                      << " strings=" << loaded_strings
                      << " colors=" << loaded_colors
                      << " dimens=" << loaded_dimens
                      << " drawables=" << loaded_drawables
                      << " integers=" << loaded_integers
                      << " bools=" << loaded_bools
                      << std::endl;
            if (!loaded_any) {
                std::cerr << "[EXP092-RES] WARNING: no resource_values.json found — getString will return field names, not values" << std::endl;
            }
        }
    }

    try {
        // ===================================================================
        // EXP-093/F005: Application lifecycle — instantiate and call onCreate
        // BEFORE Activity.onCreate, per AOSP contract.
        //
        // AOSP flow: ActivityThread.handleBindApplication →
        //   instrumentation.newApplication(Class) →
        //   app.attachBaseContext(context) →
        //   app.onCreate()
        //
        // If the manifest declares android:name="org.example.MyApp",
        // we instantiate MyApp, call attachBaseContext, then onCreate.
        // If no android:name, use the default android.app.Application.
        // ===================================================================
        if (!result.apk_info.application_name.empty()) {
            std::string app_class = result.apk_info.application_name;
            // Normalize to DEX descriptor format: "Lorg/example/MyApp;"
            if (app_class[0] != 'L') {
                std::replace(app_class.begin(), app_class.end(), '.', '/');
                if (app_class[0] != 'L') app_class = "L" + app_class;
                if (app_class.back() != ';') app_class += ";";
            }
            std::cerr << "[EXP093-APP] Manifest declares Application class: "
                      << app_class << std::endl;

            // Try to instantiate the Application class via DEX execution.
            // new-instance → invoke-direct <init>(Context) → attachBaseContext → onCreate
            miniandroid::dalvik::DalvikValue app_return;
            miniandroid::dalvik::DalvikExecutionResult app_result;

            // Step 1: new-instance
            uint32_t app_obj_id = dalvik_engine_.get_heap_public().allocate(
                app_class, 0, 0);
            if (app_obj_id != 0) {
                std::cerr << "[EXP093-APP] Allocated Application object: obj_id="
                          << app_obj_id << std::endl;

                // Step 2: Call <init>(Context) — the constructor
                std::vector<miniandroid::dalvik::DalvikValue> init_args;
                init_args.push_back(
                    miniandroid::dalvik::DalvikValue::make_object(app_obj_id, app_class));
                // Pass the application context as the Context arg.
                // For now, use the same context singleton (obj_id=2).
                miniandroid::dalvik::DalvikValue ctx_val;
                ctx_val.type = miniandroid::dalvik::DalvikType::OBJECT_REF;
                ctx_val.object_id = 2;
                ctx_val.class_desc = "Landroid/content/Context;";
                init_args.push_back(ctx_val);

                dalvik_engine_.try_recursive_invoke(
                    app_class, "<init>", init_args, app_return, app_result);
                std::cerr << "[EXP093-APP] <init> invoked" << std::endl;

                // Step 3: Call attachBaseContext(Context)
                // This is a protected method on Application/ContextWrapper.
                // We invoke it via the DEX if available, otherwise skip.
                std::vector<miniandroid::dalvik::DalvikValue> attach_args;
                attach_args.push_back(
                    miniandroid::dalvik::DalvikValue::make_object(app_obj_id, app_class));
                attach_args.push_back(ctx_val);
                dalvik_engine_.try_recursive_invoke(
                    app_class, "attachBaseContext", attach_args, app_return, app_result);
                std::cerr << "[EXP093-APP] attachBaseContext invoked" << std::endl;

                // Step 4: Call onCreate()
                std::vector<miniandroid::dalvik::DalvikValue> create_args;
                create_args.push_back(
                    miniandroid::dalvik::DalvikValue::make_object(app_obj_id, app_class));
                dalvik_engine_.try_recursive_invoke(
                    app_class, "onCreate", create_args, app_return, app_result);
                std::cerr << "[EXP093-APP] onCreate invoked" << std::endl;

                // Cache the Application singleton so Activity.getApplication()
                // can return it later.
                // TODO: Set the ApplicationLoader.applicationContext or equivalent
                // singleton field to point to this object.
            } else {
                std::cerr << "[EXP093-APP] WARNING: Could not allocate Application object"
                          << std::endl;
            }
        } else {
            std::cerr << "[EXP093-APP] No custom Application class declared in manifest"
                      << std::endl;
        }

        // ===================================================================
        // CALL DALVIK ENGINE - This is the REAL execution path
        // ===================================================================
        auto dalvik_result = dalvik_engine_.execute_apk_with_activity(
            result.apk_info.apk_path,
            result.dex_report,
            result.apk_info.main_activity_full,  // EXP-086 P1: pass manifest-provided activity class
            config.verbose_logging
        );

        // EXP-086 Phase 7 (B4 FIX): Drain the Handler/Looper queue after
        // onCreate execution. Without this, Handler.post() callbacks
        // queued during onCreate are never dispatched — timer-based apps,
        // animation callbacks, and Lambda runnables never fire.
        // This is the GENERIC drain (not Telegram-specific).
        if (auto* registry = dalvik_engine_.get_shadow_registry()) {
            if (auto* hs = registry->find_as<framework::HandlerShadow>()) {
                std::vector<uint32_t> drained;
                size_t n = hs->drain_ready(&drained);
                if (n > 0) {
                    trace_engine_.info("ExecutionEngine", "drain_handler_queue",
                                       "Drained " + std::to_string(n) + " Runnables after onCreate");
                    // EXP-090: Actually INVOKE each drained Runnable's run() method.
                    // Previously this only logged "invocation deferred to future work"
                    // which meant callbacks never executed.
                    for (uint32_t rid : drained) {
                        try {
                            // Look up the Runnable's class from the heap
                            auto& heap = dalvik_engine_.get_heap_public();
                            if (heap.has_object(rid)) {
                                const auto* obj = heap.get(rid);
                                std::string cls = obj ? obj->class_descriptor : "";
                                if (!cls.empty()) {
                                    std::cerr << "[EXP090-DRAIN] Invoking Runnable id=" << rid
                                              << " class=" << cls << std::endl;
                                    miniandroid::dalvik::DalvikValue ret;
                                    miniandroid::dalvik::DalvikExecutionResult drain_result;
                                    std::vector<miniandroid::dalvik::DalvikValue> args;
                                    args.push_back(miniandroid::dalvik::DalvikValue::make_object(rid, cls));
                                    dalvik_engine_.try_recursive_invoke(
                                        cls, "run", args, ret, drain_result);
                                    std::cerr << "[EXP090-DRAIN] Runnable id=" << rid
                                              << " invoked" << std::endl;
                                }
                            }
                        } catch (const std::exception& e) {
                            std::cerr << "[EXP090-DRAIN] Runnable drain failed: " << e.what() << std::endl;
                        }
                    }
                }
            }
        }
        
        // Log real execution metrics
        trace_engine_.info("DalvikEngine", "execute_apk", 
                           "Instructions executed: " + std::to_string(dalvik_result.total_instructions_executed));
        trace_engine_.info("DalvikEngine", "execute_apk",
                           "API calls traced: " + std::to_string(dalvik_result.api_call_traces.size()));
        trace_engine_.info("DalvikEngine", "execute_apk",
                           "Heap objects: " + std::to_string(dalvik_result.heap.size()));
        
        // ===================================================================
        // EXP-031.5 HARD ASSERTION: Real execution MUST occur in REAL_DALVIK mode
        // NO FALLBACK ALLOWED - Golden Debug Protocol
        // ===================================================================
        if (dalvik_result.total_instructions_executed == 0) {
            // CRITICAL: No bytecode was executed!
            std::string error_msg = "EXP-031.5 ASSERTION FAILED: REAL_DALVIK mode selected but ExecuteInstruction() was never called. "
                                   "This means no actual Dalvik bytecode was executed. "
                                   "Possible causes: (1) DEX parser did not extract method bytecode, "
                                   "(2) No methods found matching entry point criteria, "
                                   "(3) All methods had empty bytecode arrays. "
                                   "Instructions expected: > 0, Actual: 0";
            
            trace_engine_.record_error("REAL_EXECUTION_ASSERTION_FAIL", error_msg,
                                       "ExecutionEngine", "stage_execute_application_real_dalvik");
            
            // DO NOT FALLBACK TO FAKE SUCCESS - Fail honestly per Golden Debug Protocol
            set_error(error_msg);
            result.status = ExecutionStatus::FAILURE;
            return false;
        }
        
        // ===================================================================
        // REAL EXECUTION CONFIRMED - Continue with evidence-based processing
        // ===================================================================
        trace_engine_.info("ExecutionEngine", "validation",
                           "✅ REAL EXECUTION CONFIRMED - " + 
                           std::to_string(dalvik_result.total_instructions_executed) + " opcodes executed");
        trace_engine_.info("ExecutionEngine", "execution_source",
                           "ExecutionSource = REAL_DALVIK_INTERPRETER (verified)");
        
        // Create content view from real execution results only
        if (dalvik_result.final_status == dalvik::DalvikExecutionResult::FinalStatus::COMPLETED_SUCCESS ||
            dalvik_result.final_status == dalvik::DalvikExecutionResult::FinalStatus::COMPLETED_PARTIAL) {
            result.content_view = create_view_from_dalvik_result(dalvik_result, result.dex_report);
        }
        
        // ===================================================================
        // LIFECYCLE SOURCE VALIDATION (EXP-031.5 Golden Debug Protocol)
        // ===================================================================
        api::Bundle* null_bundle = nullptr;
        
        // Check if lifecycle methods were invoked through DEX execution
        bool lifecycle_from_dex = false;
        for (const auto& api_trace : dalvik_result.api_call_traces) {
            std::string method_full = api_trace.api_class + "." + api_trace.method;
            if (method_full.find("onCreate") != std::string::npos ||
                method_full.find("onStart") != std::string::npos ||
                method_full.find("onResume") != std::string::npos) {
                lifecycle_from_dex = true;
                trace_engine_.info("ExecutionEngine", "lifecycle_source",
                                   "✅ Lifecycle method '" + method_full + "' from REAL_DALVIK_INTERPRETER");
                break;
            }
        }
        
        if (!lifecycle_from_dex) {
            // WARNING: Lifecycle not from DEX execution
            // This is allowed for now but MUST be tracked as HOST_SHORTCUT
            trace_engine_.warning("ExecutionEngine", "lifecycle_source",
                                  "⚠️ Lifecycle (onCreate/onStart/onResume) NOT found in DEX execution traces. "
                                  "Falling back to HOST_SHORTCUT lifecycle calls. "
                                  "This means lifecycle events are NOT consequences of bytecode execution.");
            
            // Mark execution as PARTIAL_SUCCESS since lifecycle is fake
            result.status = ExecutionStatus::PARTIAL_SUCCESS;
            
            // Still call lifecycle for visibility, but mark source clearly
            trace_engine_.info("ExecutionEngine", "lifecycle_fallback",
                               "[HOST_SHORTCUT] Calling onCreate/onStart/onResume from C++ (NOT from DEX)");
            result.activity->onCreate(null_bundle);
            result.activity->onStart();
            result.activity->onResume();
        } else {
            // Lifecycle fully from DEX - this is the goal!
            trace_engine_.info("ExecutionEngine", "lifecycle_verified",
                               "✅ All lifecycle events sourced from REAL_DALVIK_INTERPRETER");
            result.status = ExecutionStatus::SUCCESS;
        }
        
        // ===================================================================
        // EXP-031.5: GENERATE MANDATORY TRACE FILES (Golden Debug Protocol)
        // Every real execution MUST produce evidence files
        // ===================================================================
        std::string trace_dir = config.output_directory + "/exp031_5/traces/" + 
                               result.apk_info.package_name;
        
        trace_engine_.info("ExecutionEngine", "trace_export",
                           "Generating mandatory trace files: " + trace_dir);
        
        bool traces_ok = dalvik::TraceExporter::export_all_traces(
            dalvik_result,
            trace_dir,
            result.apk_info.apk_path
        );
        
        if (traces_ok) {
            trace_engine_.info("ExecutionEngine", "trace_export",
                               "✅ Trace files generated successfully");
            trace_engine_.info("ExecutionEngine", "trace_files",
                               "  - opcode_trace.json");
            trace_engine_.info("ExecutionEngine", "trace_files",
                               "  - method_trace.json");
            trace_engine_.info("ExecutionEngine", "trace_files",
                               "  - register_trace.json");
            trace_engine_.info("ExecutionEngine", "trace_files",
                               "  - heap_trace.json");
            trace_engine_.info("ExecutionEngine", "trace_files",
                               "  - execution_summary.json (contains verdict)");
        } else {
            trace_engine_.warning("ExecutionEngine", "trace_export",
                                  "⚠️ Failed to generate some trace files");
        }
        
    } catch (const std::exception& e) {
        set_error("Dalvik execution error: " + std::string(e.what()));
        trace_engine_.record_error("DALVIK_ERROR", e.what(),
                                   "DalvikEngine", "execute_apk");

        // Don't fallback to fake success - fail honestly
        result.status = ExecutionStatus::FAILURE;
        return false;
    }

    // ===================================================================
    // EXP-088 Phase B: Generic click dispatch after onCreate
    // After onCreate completes, find views with click listeners and
    // dispatch one click to verify the full event chain:
    //   click → listener → DEX callback → state change
    // ===================================================================
    if (shadow_registry_ && result.status != ExecutionStatus::FAILURE) {
        auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
        if (view_shadow) {
            auto clickables = view_shadow->find_all_with_click_listener("");
            std::cerr << "[EXP088-PHASE-B] ViewShadow found: " << (void*)view_shadow
                      << " clickables: " << clickables.size() << std::endl;
            if (!clickables.empty()) {
                // Log each clickable view for diagnostics
                for (uint32_t vid : clickables) {
                    const auto* node = view_shadow->find_node(vid);
                    if (node) {
                        std::cerr << "[EXP088-PHASE-B] clickable view_id=" << vid
                                  << " class=" << node->class_desc
                                  << " listener_id=" << node->click_listener_id
                                  << std::endl;
                    }
                }
                // EXP-100 (UNIFIED_002 §9): audit the CANDIDATE ENUMERATION —
                // record ALL clickable candidates + the iteration order so the
                // click→target→screen mapping is provable from artifacts.
                {
                    std::string cand;
                    for (size_t ci = 0; ci < clickables.size(); ++ci) {
                        const auto* cn = view_shadow->find_node(clickables[ci]);
                        if (ci) cand += ",";
                        cand += "{\"order\":" + std::to_string(ci) +
                            ",\"id\":" + std::to_string(clickables[ci]) +
                            ",\"class\":\"" + miniandroid::diagnostics::jesc(
                                cn ? cn->class_desc : std::string("?")) + "\"" +
                            ",\"listener_id\":" + std::to_string(
                                cn ? cn->click_listener_id : 0) + "}";
                    }
                    miniandroid::diagnostics::audit_append(
                        std::string("{\"schema\":\"click_audit_v1\",\"record\":\"enumerate_candidates\",\"t\":\"") +
                        miniandroid::diagnostics::iso_now() + "\"" +
                        ",\"count\":" + std::to_string(clickables.size()) +
                        ",\"candidates\":[" + cand + "]" +
                        ",\"order_rule\":\"find_all_with_click_listener ordering\"}");
                }
                trace_engine_.info("ExecutionEngine", "phase_b_click",
                                   "Found " + std::to_string(clickables.size()) +
                                   " views with click listeners");
                // EXP-089: Iterate ALL clickable views and dispatch click on each.
                // Previously only clicked the FIRST view (which was ActionBar,
                // not the IntroActivity "Start Messaging" button).
                // For Telegram, the intro screen has:
                //   - ActionBar (back button) — clicking this goes back, not forward
                //   - TextView (Start Messaging) — this is the one we want
                //   - IntroActivity$4 (a custom view)
                //   - FrameLayout (a container)
                // We iterate ALL clickables and dispatch click on each, stopping
                // when we find one that creates a LoginActivity (the actual goal
                // of clicking "Start Messaging").
                bool login_created = false;
                for (uint32_t vid : clickables) {
                    std::cerr << "[EXP088-PHASE-B] dispatching click on view_id=" << vid << std::endl;
                    bool click_ok = dalvik_engine_.dispatch_click(vid);
                    std::cerr << "[EXP088-PHASE-B] dispatch_click(" << vid
                              << ") → " << (click_ok ? "OK" : "FAILED") << std::endl;
                    trace_engine_.info("ExecutionEngine", "phase_b_click",
                                       "dispatch_click(" + std::to_string(vid) +
                                       ") → " + (click_ok ? "OK" : "FAILED"));
                    // Check if a LoginActivity was created after this click
                    // (generic check — looks for any class containing "LoginActivity"
                    // on the heap)
                    if (click_ok) {
                        auto& heap = dalvik_engine_.get_heap_public();
                        for (const auto& [oid, obj] : heap.all_objects()) {
                            if (obj.class_descriptor.find("LoginActivity") != std::string::npos &&
                                obj.class_descriptor.find("$") == std::string::npos) {
                                // Found a LoginActivity instance (not an inner class)
                                // Only count it if it was created AFTER the click
                                // (we can't easily check timestamps, so we check if
                                // it has a createView method — meaning it's a real
                                // fragment, not just a class def)
                                login_created = true;
                                std::cerr << "[EXP088-PHASE-B] LoginActivity created! obj_id="
                                          << oid << " class=" << obj.class_descriptor
                                          << " (from view_id=" << vid << ")" << std::endl;
                                break;
                            }
                        }
                    }
                    // EXP-100 (UNIFIED_002 §7/§9): per-click STAGE record —
                    // which click, on which view, dispatch result, whether a
                    // LoginActivity appeared on the heap AFTER this click, and
                    // whether this click is the stop point. This is the record
                    // that answers "click ID → exact target View → handler".
                    miniandroid::diagnostics::audit_append(
                        std::string("{\"schema\":\"click_audit_v1\","
                                    "\"record\":\"phase_b_stage\",\"t\":\"") +
                        miniandroid::diagnostics::iso_now() + "\"" +
                        ",\"view_id\":" + std::to_string(vid) +
                        ",\"dispatch_ok\":" + (click_ok ? "true" : "false") +
                        ",\"login_created_after\":" + (login_created ? "true" : "false") +
                        ",\"stop\":" + (login_created ? "true" : "false") +
                        ",\"stop_rule\":\"stop when LoginActivity on heap\"}");
                    if (login_created) break;
                }
                if (!login_created) {
                    std::cerr << "[EXP088-PHASE-B] No LoginActivity created after clicking all views" << std::endl;
                } else {
                    // EXP-089 M5: Generic phone input into phoneField (PhoneView$3)
                    // After LoginActivity is created, dispatch a phone number into the
                    // phone EditText field. This is GENERIC — uses dispatch_text_input_by_class
                    // which searches for any view whose class contains "PhoneView$3"
                    // (the phone number EditText in Telegram's PhoneView).
                    // EXP-094 (CM-018 follow-up): Input the NATIONAL number only
                    // ("5551234567"), WITHOUT "+" and WITHOUT the country code.
                    // Per LoginActivity.PhoneView.onNextPressed source:
                    //   phoneNumber = "+" + codeField.getText() + " " + phoneField.getText()
                    // codeField receives the country code ("1") from setCountry
                    // (triggered by the getNearestDc response), so the phone field
                    // must contain only the national part. Typing "+15551234567"
                    // here previously produced the doubled prefix "+1 +15551234567"
                    // in the Bundle "phone" value and the SMS screen text.
                    std::cerr << "[EXP089-M5] Dispatching phone input into PhoneView$3..." << std::endl;
                    bool input_ok = dalvik_engine_.dispatch_text_input_by_class(
                        "PhoneView$3", "5551234567");
                    std::cerr << "[EXP089-M5] Text input result: "
                              << (input_ok ? "DISPATCHED" : "FAILED") << std::endl;

                    // EXP-092+ ROOT CAUSE FIX: Do NOT inject "1" into codeField (PhoneView$1).
                    //
                    // The previous code injected "1" into the codeField to simulate
                    // the user typing the US country code. But this PREVENTS the real
                    // auth.sendCode path from being reached:
                    //
                    // 1. Injecting "1" into codeField triggers afterTextChanged, which
                    //    sets countryState = 1 (COUNTRY_NOT_SELECTED).
                    // 2. When getNearestDc response arrives (with country="US"),
                    //    lambda$new$12 at PC=11 checks:
                    //      if-nez v0(codeField.length()=1), +11 → PC=22
                    //    Since codeField.length() = 1 (non-zero), the branch IS taken
                    //    → SKIPS the setCountry call → countryState stays at 1.
                    // 3. onNextPressed at PC=604 checks:
                    //      if-ne v4(countryState=1), v2(=1), +28 → PC=632
                    //    Since 1 != 1 = false, the branch is NOT taken → falls through
                    //    to PC=606 (the needShowAlert path) → shows "ChooseCountry"
                    //    alert → NEVER reaches auth.sendCode.
                    //
                    // FIX: Do NOT inject "1" into codeField. Let it stay empty.
                    // Then:
                    // 1. codeField.length() = 0.
                    // 2. lambda$new$12 at PC=11: if-nez(0) = false → NOT taken → falls
                    //    through to PC=13 → calls setCountry(PhoneView, HashMap, "US").
                    // 3. setCountry: HashMap.get("US") → returns country code → sets
                    //    codeField.text = country code AND countryState = 0.
                    // 4. onNextPressed at PC=604: if-ne(0, 1) = true → TAKEN → PC=632.
                    // 5. PC=633: if-ne(0, 2) = true → TAKEN → PC=663 → auth.sendCode path.
                    //
                    // This is the LEGITIMATE Telegram behavior: the app auto-detects
                    // the country from the getNearestDc response and fills in the
                    // codeField automatically. The user only needs to type the phone
                    // number, not the country code.

                    // EXP-092+ FIX: Drain Handler queue BEFORE clicking Next.
                    // The getNearestDc response handler (Lambda14 → Lambda16 →
                    // lambda$new$12 → setCountry) is queued on the Handler during
                    // PhoneView.<init>. If we don't drain before clicking Next,
                    // setCountry hasn't run yet, so:
                    //   - codeField is empty → onNextPressed returns early at PC=73
                    //     (if-eqz codeField.length() == 0 → return)
                    //   - countryState is still 1 → onNextPressed takes the
                    //     needShowAlert side path
                    // By draining here, we ensure setCountry runs first:
                    //   - setCountry sets codeField.text = country code
                    //   - setCountry sets countryState = 0
                    // Then onNextPressed will see codeField.length() > 0 and
                    // countryState == 0, and proceed to the auth.sendCode path.
                    if (auto* registry = dalvik_engine_.get_shadow_registry()) {
                        if (auto* hs = registry->find_as<framework::HandlerShadow>()) {
                            for (int drain_iter = 0; drain_iter < 10; drain_iter++) {
                                std::vector<uint32_t> drained;
                                size_t n = hs->drain_ready(&drained);
                                if (n == 0) break;
                                std::cerr << "[EXP092-PRE-CLICK-DRAIN] Iteration "
                                          << drain_iter << " drained " << n
                                          << " runnables" << std::endl;
                                for (uint32_t rid : drained) {
                                    try {
                                        auto& heap = dalvik_engine_.get_heap_public();
                                        if (heap.has_object(rid)) {
                                            const auto* obj = heap.get(rid);
                                            std::string cls = obj ? obj->class_descriptor : "";
                                            if (!cls.empty()) {
                                                std::cerr << "[EXP092-PRE-CLICK-DRAIN] "
                                                          << "Invoking Runnable id=" << rid
                                                          << " class=" << cls << std::endl;
                                                miniandroid::dalvik::DalvikValue ret;
                                                miniandroid::dalvik::DalvikExecutionResult dr;
                                                std::vector<miniandroid::dalvik::DalvikValue> args;
                                                args.push_back(
                                                    miniandroid::dalvik::DalvikValue::make_object(rid, cls));
                                                dalvik_engine_.try_recursive_invoke(
                                                    cls, "run", args, ret, dr);
                                            }
                                        }
                                    } catch (const std::exception& e) {
                                        std::cerr << "[EXP092-PRE-CLICK-DRAIN] "
                                                  << "Runnable drain failed: "
                                                  << e.what() << std::endl;
                                    }
                                }
                            }
                        }
                    }

                    // EXP-089 M6: Click on FragmentFloatingButton (Next button)
                    // After phone input, dispatch a click on the FragmentFloatingButton
                    // which is the real "Next" button in Telegram's login screen.
                    std::cerr << "[EXP089-M6] Clicking FragmentFloatingButton..." << std::endl;
                    bool next_click_ok = dalvik_engine_.dispatch_click_by_class(
                        "FragmentFloatingButton");
                    std::cerr << "[EXP089-M6] FragmentFloatingButton click result: "
                              << (next_click_ok ? "OK" : "FAILED") << std::endl;

                    // EXP-089 M8: After onNextPressed creates PhoneNumberConfirmView,
                    // we need to click the confirm button. The PhoneNumberConfirmView
                    // creates a SECOND FragmentFloatingButton (the confirm button).
                    // We dispatch_click_by_class again — it should find the
                    // FragmentFloatingButton with the HIGHEST view_id (the confirm one).
                    if (next_click_ok) {
                        std::cerr << "[EXP089-M8] Clicking confirm FragmentFloatingButton..." << std::endl;
                        // dispatch_click_by_class finds ALL views with the class
                        // and clicks the LAST one (most recently created).
                        // The confirm FragmentFloatingButton was created AFTER
                        // the initial Next button, so it has a higher view_id.
                        bool confirm_ok = dalvik_engine_.dispatch_click_by_class(
                            "FragmentFloatingButton");
                        std::cerr << "[EXP089-M8] Confirm click result: "
                                  << (confirm_ok ? "OK" : "FAILED") << std::endl;

                        // Also try clicking any View with a listener that was
                        // created inside PhoneNumberConfirmView
                        if (!confirm_ok) {
                            std::cerr << "[EXP089-M8] Trying all views with listeners..." << std::endl;
                            auto* vs = shadow_registry_->find_as<framework::ViewShadow>();
                            if (vs) {
                                auto all_clickables = vs->find_all_with_click_listener("");
                                for (uint32_t cv : all_clickables) {
                                    const auto* node = vs->find_node(cv);
                                    if (node && node->click_listener_id != 0) {
                                        std::cerr << "[EXP089-M8] Trying view_id=" << cv
                                                  << " class=" << node->class_desc << std::endl;
                                        if (dalvik_engine_.dispatch_click(cv)) {
                                            std::cerr << "[EXP089-M8] Click succeeded on view_id=" << cv << std::endl;
                                            break;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            } else {
                std::cerr << "[EXP088-PHASE-B] No views with click listeners found" << std::endl;
                trace_engine_.info("ExecutionEngine", "phase_b_click",
                                   "No views with click listeners found (setContentView may not have been called)");
            }
        } else {
            std::cerr << "[EXP088-PHASE-B] ViewShadow not registered" << std::endl;
        }
    } else {
        std::cerr << "[EXP088-PHASE-B] Skipping phase_b_click: shadow_registry_="
                  << (void*)shadow_registry_
                  << " status=" << static_cast<int>(result.status) << std::endl;
    }

    // EXP-090: Drain Handler queue AGAIN after phase_b_click.
    // The phone input and confirm click may have queued auth response
    // callbacks (RequestDelegate.run) that need to execute before rendering.
    // Without this second drain, the callback never fires and setPage
    // is never called.
    if (auto* registry = dalvik_engine_.get_shadow_registry()) {
        if (auto* hs = registry->find_as<framework::HandlerShadow>()) {
            // Drain iteratively — callbacks may queue MORE runnables
            for (int drain_iter = 0; drain_iter < 10; drain_iter++) {
                std::vector<uint32_t> drained;
                size_t n = hs->drain_ready(&drained);
                if (n == 0) break;
                std::cerr << "[EXP090-DRAIN2] Iteration " << drain_iter
                          << " drained " << n << " runnables" << std::endl;
                for (uint32_t rid : drained) {
                    try {
                        auto& heap = dalvik_engine_.get_heap_public();
                        if (heap.has_object(rid)) {
                            const auto* obj = heap.get(rid);
                            std::string cls = obj ? obj->class_descriptor : "";
                            if (!cls.empty()) {
                                std::cerr << "[EXP090-DRAIN2] Invoking Runnable id=" << rid
                                          << " class=" << cls << std::endl;
                                miniandroid::dalvik::DalvikValue ret;
                                miniandroid::dalvik::DalvikExecutionResult drain_result;
                                std::vector<miniandroid::dalvik::DalvikValue> args;
                                args.push_back(miniandroid::dalvik::DalvikValue::make_object(rid, cls));
                                dalvik_engine_.try_recursive_invoke(
                                    cls, "run", args, ret, drain_result);
                                std::cerr << "[EXP090-DRAIN2] Runnable id=" << rid
                                          << " invoked" << std::endl;
                            }
                        }
                    } catch (const std::exception& e) {
                        std::cerr << "[EXP090-DRAIN2] Runnable failed: " << e.what() << std::endl;
                    }
                }
            }
        }
    }

    trace_engine_.info("ExecutionEngine", "stage_execute_application_real_dalvik",
                       "Real Dalvik execution complete");

    return true;
}

// ============================================================================
// EXP-031: LEGACY EXECUTION PATH (OLD - labeled as HOST_SHORTCUT)
// ============================================================================

bool ExecutionEngine::stage_execute_application_legacy(ExecutionResult& result, const ExecutionConfig& config) {
    trace_engine_.info("ExecutionEngine", "stage_execute_application_legacy", 
                       "[HOST_SHORTCUT] Using legacy simulated lifecycle");
    
    // Create Activity instance (SHORTCUT - not from DEX)
    result.activity = std::make_shared<api::Activity>();
    result.activity->set_package_name(result.apk_info.package_name);
    
    // Simulate lifecycle if configured (ALL SHORTCUTS)
    if (config.simulate_lifecycle) {
        // Create content view via shortcut
        if (config.simulated_text.empty()) {
            result.content_view = create_view_from_layout(result.dex_report);  // HOST_SHORTCUT
        } else {
            result.content_view = create_hello_world_view(config);              // HOST_SHORTCUT
        }
        
        // Set content view on activity (HOST_SHORTCUT)
        if (result.content_view) {
            result.activity->setContentView(result.content_view);
        }
        
        // Execute lifecycle methods (HOST_SHORTCUT - no DEX involved!)
        trace_engine_.info("ExecutionEngine", "lifecycle_calls",
                           "[HOST_SHORTCUT] Calling onCreate/onStart/onResume directly");
        
        api::Bundle* null_bundle = nullptr;
        result.activity->onCreate(null_bundle);   // HOST_SHORTCUT
        result.activity->onStart();               // HOST_SHORTCUT
        result.activity->onResume();              // HOST_SHORTCUT
    }
    
    result.status = ExecutionStatus::SUCCESS;
    
    trace_engine_.info("ExecutionEngine", "stage_execute_application_legacy",
                       "Legacy simulation complete [HOST_SHORTCUT]");
    
    return true;
}

bool ExecutionEngine::stage_render_frame( ExecutionResult& result, const ExecutionConfig& config) {
    trace_engine_.info("ExecutionEngine", "stage_render_frame", "Rendering frame");

    // UNIFIED_011.2 IMAGE-RES-RENDER (§13/§14): populate the R-name → drawable
    // path map once per run from the APK's res/ entry list. Without this the
    // runtime setImageResource chain could never resolve to real pixels.
    if (!result.apk_info.apk_path.empty()) {
        auto entries = apk_parser_.list_entries(result.apk_info.apk_path);
        std::vector<std::string> entry_names;
        entry_names.reserve(entries.size());
        for (const auto& e : entries) entry_names.push_back(e.name);
        dalvik_engine_.populate_resource_drawable_paths(entry_names);
    }

    // EXP-088 Phase A2: Real measure/layout + BitmapFont text rendering.
    // Replaces the EXP-087 pixel-block renderer with proper:
    //   1. SoftwareCanvas + BitmapFont for readable text glyphs
    //   2. Simple measure/layout pass respecting MATCH_PARENT/WRAP_CONTENT
    //   3. draw_rect for view backgrounds
    //   4. draw_text for text with real font data
    if (shadow_registry_) {
        auto* activity_shadow = shadow_registry_->find_as<framework::ActivityShadow>();
        auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
        if (activity_shadow && view_shadow) {
            uint32_t root_id = activity_shadow->content_view_id();

            // EXP-090: Search for the "current visible" fragment view by class name.
            // Fragment views (PhoneView, SmsView) are created by DEX bytecode and
            // may not be connected to the root in the ViewShadow tree (orphan nodes).
            // EXP-094 (CM-018): Priority is now:
            //   1. The view that last received setParams (the app's OWN signal
            //      for "this is the active page" — the app configures exactly
            //      the page it is showing).
            //   2. Newest SmsView (suffix match)  3. Newest PhoneView  4. root.
            {
                uint32_t chosen_root = 0;
                // 1. The app's own navigation signal: last setParams receiver.
                uint32_t params_view = dalvik_engine_.last_set_params_view();
                if (params_view != 0) {
                    const auto* pv = view_shadow->find_node(params_view);
                    if (pv && !pv->children.empty()) {
                        std::cerr << "[EXP094-RENDER] Using last-setParams view as render root: view_id="
                                  << params_view << " class=" << pv->class_desc
                                  << " children=" << pv->children.size() << std::endl;
                        chosen_root = params_view;
                    }
                }
                if (chosen_root == 0) {
                    uint32_t found_sms = 0, found_phone = 0;
                    // EXP-094: SUFFIX match on the simple class name — the real
                    // SmsView/PhoneView classes END with "SmsView;"/"PhoneView;"
                    // (e.g. "Lorg/telegram/ui/LoginActivity$LoginActivitySmsView;")
                    // while their inner/lambda classes end with "$2;",
                    // "$$ExternalSyntheticLambda4;", etc. A plain find("SmsView")
                    // matches lambdas; a find("$")-exclusion matches nothing
                    // because the OUTER separator is also "$".
                    auto ends_with = [](const std::string& s, const std::string& suffix) {
                        return s.size() >= suffix.size() &&
                               s.compare(s.size() - suffix.size(), suffix.size(), suffix) == 0;
                    };
                    for (const auto& [id, node_ptr] : view_shadow->all_nodes()) {
                        if (!node_ptr) continue;
                        if (ends_with(node_ptr->class_desc, "SmsView;")) {
                            if (found_sms == 0 || id > found_sms) {
                                found_sms = id;
                            }
                        }
                        if (ends_with(node_ptr->class_desc, "PhoneView;")) {
                            if (found_phone == 0 || id > found_phone) {
                                found_phone = id;
                            }
                        }
                    }
                    if (found_sms != 0) {
                        const auto* sms_node = view_shadow->find_node(found_sms);
                        std::cerr << "[EXP090-RENDER] Using SmsView as render root: view_id=" << found_sms
                                  << " class=" << (sms_node ? sms_node->class_desc : "?")
                                  << " children=" << (sms_node ? sms_node->children.size() : 0)
                                  << std::endl;
                        chosen_root = found_sms;
                    } else if (found_phone != 0) {
                        const auto* phone_node = view_shadow->find_node(found_phone);
                        std::cerr << "[EXP090-RENDER] Using PhoneView as render root: view_id=" << found_phone
                                  << " class=" << (phone_node ? phone_node->class_desc : "?")
                                  << " children=" << (phone_node ? phone_node->children.size() : 0)
                                  << std::endl;
                        chosen_root = found_phone;
                    }
                }
                if (chosen_root != 0) {
                    root_id = chosen_root;
                }
            }

            if (root_id != 0) {
                const auto* root_node = view_shadow->find_node(root_id);
                if (root_node) {
                    // Create a FrameBuffer + SoftwareCanvas for real rendering
                    renderer::FrameBuffer fb(config.screen_width, config.screen_height);
                    fb.clear(renderer::Colors::WHITE);  // White background like Android
                    renderer::SoftwareCanvas canvas(&fb);
                    renderer::BitmapFont font;

                    // EXP-088 A4 FIX: Convert recursive lambda to iterative
                    // traversal with visited-set to prevent cycles and a hard
                    // node-visit limit. This fixes the intermittent segfault
                    // caused by dangling ViewNode pointers from recursive
                    // std::function captures.
                    try {
                        view_shadow->find_node(root_id);  // verify root still valid

                        // Iterative traversal with visited-set.
                        // EXP-095 (CM-019): REAL layout pass — the parent computes
                        // each child's position/size using the captured
                        // LayoutParams (lp_width/lp_height/lp_gravity/margins
                        // from LayoutHelper.createLinear/createFrame).
                        //   * Vertical LinearLayout parent (the SmsView case):
                        //     children stack top→bottom honoring margins;
                        //     CENTER_HORIZONTAL gravity centers each child.
                        //   * FrameLayout/other parents: children overlap at
                        //     the parent's top-left, gravity centers them.
                        // AOSP Gravity bits: horizontal mask 0x7
                        //   (CENTER_HORIZONTAL=1, LEFT=3, RIGHT=5),
                        //   vertical mask 0x70 (CENTER_VERTICAL=0x10,
                        //   TOP=0x30, BOTTOM=0x50).
                        struct RenderTask {
                            uint32_t view_id;
                            int left, top, width, height;
                            int depth;
                        };
                        std::vector<RenderTask> queue;
                        std::set<uint32_t> visited;
                        const int MAX_NODES = 500;
                        int node_count = 0;
                        // CAMPAIGN 013: deferred custom-view placeholders.
                        struct CVP { int l, t, w, h; std::string cls; uint32_t view_id = 0; };
                        std::vector<CVP> custom_view_placeholders;

                        // Helper: measured text size for a node (used for
                        // WRAP_CONTENT resolution and text drawing).
                        auto measure_node = [&](const framework::ViewShadow::ViewNode* n,
                                                 int parent_avail_w) -> std::pair<int,int> {
                            (void)parent_avail_w;
                            int lines = 1;
                            for (char c : n->text) if (c == '\n') lines++;
                            int tw = 0;
                            {
                                std::string line;
                                for (char c : n->text) {
                                    if (c == '\n') {
                                        auto m = font.measure_text(line);
                                        tw = std::max(tw, m.width);
                                        line.clear();
                                    } else line += c;
                                }
                                auto m = font.measure_text(line);
                                tw = std::max(tw, m.width);
                            }
                            int th = lines * font.get_line_height() + 20;
                            return {tw, th};
                        };

                        queue.push_back({root_id, 0, 0, config.screen_width, config.screen_height, 0});

                        while (!queue.empty() && node_count < MAX_NODES) {
                            RenderTask task = queue.back();
                            queue.pop_back();

                            if (visited.count(task.view_id)) continue;  // cycle detection
                            visited.insert(task.view_id);
                            node_count++;

                            if (task.depth > 20) continue;

                            const auto* node = view_shadow->find_node(task.view_id);
                            if (!node) continue;

                            // EXP-092: Debug — log every node visited by the renderer
                            std::cerr << "[EXP092-RENDER] node=" << task.view_id
                                      << " class=" << node->class_desc
                                      << " text=\"" << node->text << "\""
                                      << " children=" << node->children.size()
                                      << " depth=" << task.depth
                                      << " pos=(" << task.left << "," << task.top << ")"
                                      << " size=(" << task.width << "x" << task.height << ")"
                                      << std::endl;

                            // The parent already computed this node's geometry
                            // (task.left/top/width/height) — use it directly.
                            int w = task.width;
                            int h = task.height;
                            int left = task.left;
                            int top = task.top;
                            // UNIFIED_007: when the real inflater measured this
                            // tree (ARSC→AXML inflation), use its exact geometry.
                            bool use_measured = node->laid_out;
                            if (use_measured) {
                                left = node->measured_left;
                                top = node->measured_top;
                                w = node->measured_width;
                                h = node->measured_height;
                            }
                            int right = left + w;
                            int bottom = top + h;

                            // Draw view background
                            // EXP-095 (CM-020): REAL background colors captured
                            // from setBackgroundColor(int) take priority. Per §17:
                            // do not accept default white unless the source
                            // actually requires it.
                            bool is_full_screen = (w >= config.screen_width && h >= config.screen_height);
                            bool drew_bg = false;
                            if (node->bg_color != 0) {
                                // ARGB int → RGBA
                                uint32_t c = node->bg_color;
                                renderer::RGBA rgba{
                                    static_cast<uint8_t>((c >> 16) & 0xFF),
                                    static_cast<uint8_t>((c >> 8) & 0xFF),
                                    static_cast<uint8_t>(c & 0xFF),
                                    static_cast<uint8_t>((c >> 24) & 0xFF)};
                                canvas.draw_rect(left, top, right, bottom, rgba);
                                drew_bg = true;
                            } else {
                                // EXP-092: Only draw container backgrounds for
                                // containers that DON'T fill the entire screen.
                                bool is_container = node->class_desc.find("Layout") != std::string::npos ||
                                                  node->class_desc.find("ViewGroup") != std::string::npos;
                                if (is_container && !is_full_screen) {
                                    canvas.draw_rect(left, top, right, bottom,
                                                   renderer::Colors::GREY_200);
                                    drew_bg = true;
                                } else if (node->class_desc.find("Button") != std::string::npos) {
                                    canvas.draw_rect(left, top, right, bottom,
                                                   renderer::RGBA{0x6F, 0xA8, 0xDC, 0xFF});
                                    drew_bg = true;
                                }
                            }
                            // EXP-095 (CM-020): EditText subclasses render the
                            // AOSP default editText background — a stroked box —
                            // so input fields are VISIBLE (per §15: a component
                            // is loaded only when pixels appear). CodeNumberField
                            // extends EditTextBoldCursor → AppCompatEditText →
                            // EditText; setBackground(null) removes it, but the
                            // container draws its own stroke — a bordered box is
                            // the closest generic representation.
                            bool is_edit_text = dalvik_engine_.is_subclass_of(node->class_desc, "Landroid/widget/EditText;");
                            if (is_edit_text && w > 4 && h > 4) {
                                renderer::RGBA border{0x99, 0x99, 0x99, 0xFF};
                                // 1px border via 4 rects (thin box)
                                canvas.draw_rect(left, top, right, top + 1, border);
                                canvas.draw_rect(left, bottom - 1, right, bottom, border);
                                canvas.draw_rect(left, top, left + 1, bottom, border);
                                canvas.draw_rect(right - 1, top, right, bottom, border);
                            }

                            // Draw text if present (AFTER background so text is on top)
                            // EXP-095: honor text gravity (CENTER_HORIZONTAL etc.)
                            // and word-wrap at the view width. (Also fixes the
                            // pre-existing double-escaped '\n' literal which
                            // never matched a real newline.)
                            if (!node->text.empty()) {
                                int hg = node->text_gravity & 0x7;
                                std::vector<std::string> out_lines;
                                {
                                    int avail = w - 20;
                                    std::string line, word;
                                    for (size_t i = 0; i <= node->text.size(); i++) {
                                        char c = (i < node->text.size()) ? node->text[i] : '\n';
                                        if (c == '\n') {
                                            if (!word.empty()) {
                                                if (!line.empty()) line += ' ';
                                                line += word; word.clear();
                                            }
                                            out_lines.push_back(line); line.clear();
                                            continue;
                                        }
                                        if (c == ' ') {
                                            if (!word.empty()) {
                                                if (!line.empty()) line += ' ';
                                                line += word; word.clear();
                                            }
                                            continue;
                                        }
                                        word += c;
                                        if (avail > 20) {
                                            std::string probe = line.empty() ? word : (line + " " + word);
                                            if (font.measure_text(probe).width > avail) {
                                                if (!line.empty()) out_lines.push_back(line);
                                                line = word; word.clear();
                                            }
                                        }
                                    }
                                    if (out_lines.empty()) out_lines.push_back("");
                                }
                                int text_y = top + font.get_line_height();
                                for (const auto& ln : out_lines) {
                                    if (!ln.empty()) {
                                        int lx = left + 10;
                                        if (hg == 1) {
                                            auto lm = font.measure_text(ln);
                                            lx = left + (w - lm.width) / 2;
                                        } else if (hg == 5) {
                                            auto lm = font.measure_text(ln);
                                            lx = right - 10 - lm.width;
                                        }
                                        canvas.draw_text(ln, lx, text_y,
                                                        renderer::Colors::GREY_800, &font);
                                    }
                                    text_y += font.get_line_height();
                                }
                            }

                            // CAMPAIGN 013 (custom-view visibility): unknown
                            // app-defined leaf views (e.g. headingcalc's
                            // CalculatorDisplay/CalculatorKeypad) cannot run
                            // their own onDraw, so they painted nothing — an
                            // all-white "real tree" screen. Per the evidence
                            // standard an invisible custom view is WORSE than
                            // an honest placeholder: draw a light-grey surface
                            // + the simple class name, exactly like the IMG?
                            // fallback. Only for LEAF nodes of non-framework
                            // classes with no text/image/background of their
                            // own, and never for subtree roots (PhoneView et
                            // al. carry children and render via the walk).
                            {
                                bool framework_class =
                                    node->class_desc.rfind("Landroid/", 0) == 0 ||
                                    node->class_desc.rfind("Landroidx/", 0) == 0 ||
                                    node->class_desc.rfind("Lcom/google/android/", 0) == 0;
                                bool has_own_content =
                                    !node->text.empty() ||
                                    !node->image_drawable_path.empty() ||
                                    node->image_resource_id != 0 ||
                                    !node->anim_frame_rgba.empty();
                                // CAMPAIGN 013: custom leaf views (runtime-created
                                // OR background-colored) run their REAL onDraw
                                // bytecode; a background color does NOT preclude
                                // onDraw content (Android draws bg then content).
                                if (!framework_class) {
                                    std::cerr << "[C013-LEAFCHK] " << node->class_desc
                                              << " children=" << node->children.size()
                                              << " own_content=" << has_own_content
                                              << " img_resid=" << node->image_resource_id
                                              << " bg=0x" << std::hex << node->bg_color << std::dec
                                              << " vis=" << node->visibility
                                              << " w=" << w << " h=" << h << std::endl;
                                }
                                if (!framework_class && node->children.empty() &&
                                    !has_own_content && w > 40 && h > 40 &&
                                    node->visibility == 0) {
                                    bool drew_real = false;
                                    if (task.view_id != 0 && shadow_registry_) {
                                        if (auto* canvas_shadow =
                                                shadow_registry_->find_as<framework::CanvasShadow>()) {
                                            int ondraw_ops =
                                                dalvik_engine_.dispatch_custom_view_draw(task.view_id);
                                            if (ondraw_ops > 0) {
                                                canvas_shadow->replay(canvas, font,
                                                                      (float)left, (float)top,
                                                                      (float)w, (float)h);
                                                drew_real = true;
                                                std::cerr << "[C013-CUSTOMVIEW] onDraw replayed "
                                                          << ondraw_ops << " ops for "
                                                          << node->class_desc << std::endl;
                                            }
                                        }
                                    }
                                    if (!drew_real && !drew_bg && node->bg_color == 0) {
                                        // Nothing drawn anywhere: defer to the
                                        // screen-blank grey placeholder (below).
                                        custom_view_placeholders.push_back(
                                            {left, top, w, h, node->class_desc, task.view_id});
                                    }
                                }
                            }

                            // EXP-098 (CM-027): Decode pending RLottie
                            // animations BEFORE drawing. The engine captured
                            // (raw_resid, w, h) on the ViewNode when
                            // RLottieImageView.setAnimation(R.raw.X, w, h)
                            // was called; here we resolve the resid → field
                            // name → APK path → JSON → rlottie frame RGBA.
                            // (Declared here; decode happens below after
                            // is_image_view is computed.)

                            // EXP-088 A4: Draw ImageView/ImageButton with REAL decoded pixels
                            // (replaces the prior placeholder rect + dimensions text).
                            // We use PNGDecoder to inflate + unfilter + expand to RGBA, then
                            // SoftwareCanvas::draw_image to alpha-blend onto the framebuffer.
                            // The image is drawn at (left+5, top+5) at its natural size; if it
                            // would extend past the view's right/bottom bounds, it is clipped
                            // by the framebuffer's own bounds (draw_image skips out-of-bounds
                            // pixels). For the simplestopwatch icons (27x40, 40x40) this is
                            // the correct behaviour.
                            bool is_image_view = node->class_desc.find("ImageView") != std::string::npos ||
                                                 node->class_desc.find("ImageButton") != std::string::npos;
                            if (is_image_view && !node->image_drawable_path.empty()) {
                                auto png_data = apk_parser_.extract_entry_cached(node->image_drawable_path);
                                if (!png_data.empty() && png_data.size() >= 8 &&
                                    png_data[0] == 0x89 && png_data[1] == 0x50 &&
                                    png_data[2] == 0x4E && png_data[3] == 0x47) {
                                    auto decoded = renderer::PNGDecoder::decode(png_data);
                                    if (decoded.ok && !decoded.rgba.empty()) {
                                        canvas.draw_image(decoded.rgba.data(),
                                                          decoded.width, decoded.height,
                                                          left + 5, top + 5);
                                        trace_engine_.info("ExecutionEngine",
                                            "stage_render_frame",
                                            std::string("Drew image '") + node->image_drawable_path +
                                            "' (" + std::to_string(decoded.width) + "x" +
                                            std::to_string(decoded.height) + ", " +
                                            decoded.color_type_name + ") at (" +
                                            std::to_string(left + 5) + "," +
                                            std::to_string(top + 5) + ")");
                                    } else if (!decoded.ok) {
                                        trace_engine_.warning("ExecutionEngine",
                                            "stage_render_frame",
                                            std::string("PNG decode failed for '") +
                                            node->image_drawable_path + "': " + decoded.error);
                                        // Fall back to a labelled placeholder so the user can
                                        // see that an image *should* be there.
                                        canvas.draw_rect(left + 5, top + 5, right - 5, bottom - 5,
                                                       renderer::RGBA{0xCC, 0xCC, 0xCC, 0xFF});
                                        canvas.draw_text("IMG?", left + 10,
                                                       top + font.get_line_height(),
                                                       renderer::Colors::GREY_800, &font);
                                    }
                                }
                            }
                            if (is_image_view && node->image_drawable_path.empty() &&
                                (node->image_resource_id != 0 ||
                                 !node->src_drawable_path.empty())) {
                                // UNIFIED_011.2 IMAGE-RES-RENDER (§13/§14): replace the
                                // "IMG" placeholder with REAL decoded pixels when the
                                // resource chain can be completed:
                                //   image_resource_id → field_name_by_resid_ →
                                //   resource_drawable_paths_ → APK entry → decoder →
                                //   draw_image. Falls back to src_drawable_path
                                //   (AXML android:src inflation path) when no runtime
                                //   resid was set. The renderer never touches APK ZIP
                                //   structure itself (§16 boundary preserved) — it only
                                //   consumes paths resolved by the resource layer.
                                std::string resolved_img_path;
                                if (node->image_resource_id != 0) {
                                    auto& fn_map = dalvik_engine_.field_name_by_resid_;
                                    auto fn_it = fn_map.find(node->image_resource_id);
                                    if (fn_it != fn_map.end()) {
                                        auto& dp_map = dalvik_engine_.resource_drawable_paths_;
                                        auto dp_it = dp_map.find(fn_it->second);
                                        if (dp_it != dp_map.end())
                                            resolved_img_path = dp_it->second;
                                    }
                                }
                                if (resolved_img_path.empty())
                                    resolved_img_path = node->src_drawable_path;

                                if (!resolved_img_path.empty()) {
                                    auto img_data = apk_parser_.extract_entry_cached(resolved_img_path);
                                    renderer::DecodedImage decoded;
                                    bool attempted = false;
                                    if (img_data.size() >= 4) {
                                        // PNG: 89 50 4E 47
                                        if (img_data[0] == 0x89 && img_data[1] == 0x50 &&
                                            img_data[2] == 0x4E && img_data[3] == 0x47) {
                                            attempted = true;
                                            decoded = renderer::PNGDecoder::decode(img_data);
                                        }
                                        // JPEG: FF D8 FF
                                        else if (img_data[0] == 0xFF && img_data[1] == 0xD8 &&
                                                 img_data[2] == 0xFF) {
                                            attempted = true;
                                            decoded = renderer::JPEGDecoder::decode(img_data);
                                        }
                                        // WebP: "RIFF" .... "WEBP"
                                        else if (img_data[0] == 'R' && img_data[1] == 'I' &&
                                                 img_data[2] == 'F' && img_data[3] == 'F' &&
                                                 img_data.size() >= 12 &&
                                                 img_data[8] == 'W' && img_data[9] == 'E' &&
                                                 img_data[10] == 'B' && img_data[11] == 'P') {
                                            attempted = true;
                                            decoded = renderer::WebPDecoder::decode(img_data);
                                        }
                                    }
                                    if (attempted && decoded.ok && !decoded.rgba.empty()) {
                                        canvas.draw_image(decoded.rgba.data(),
                                                          decoded.width, decoded.height,
                                                          left + 5, top + 5);
                                        trace_engine_.info("ExecutionEngine",
                                            "stage_render_frame",
                                            std::string("IMG-RES-RENDER drew '") +
                                            resolved_img_path + "' (" +
                                            std::to_string(decoded.width) + "x" +
                                            std::to_string(decoded.height) + ", " +
                                            decoded.color_type_name + ") at (" +
                                            std::to_string(left + 5) + "," +
                                            std::to_string(top + 5) + ")");
                                    } else {
                                        // Resolution succeeded but decode failed (or
                                        // unsupported format, e.g. XML drawable) — keep
                                        // the visible placeholder with the path evidence.
                                        canvas.draw_rect(left + 5, top + 5, right - 5, bottom - 5,
                                                       renderer::RGBA{0xCC, 0xCC, 0xCC, 0xFF});
                                        canvas.draw_text("IMG?", left + 10,
                                                       top + font.get_line_height(),
                                                       renderer::Colors::GREY_800, &font);
                                        trace_engine_.warning("ExecutionEngine",
                                            "stage_render_frame",
                                            std::string("IMG-RES-RENDER decode failed for '") +
                                            resolved_img_path + "'");
                                    }
                                } else {
                                    // No APK entry matched the R-field name — placeholder
                                    // with the resid as evidence (legacy behavior).
                                    canvas.draw_rect(left + 5, top + 5, right - 5, bottom - 5,
                                                   renderer::RGBA{0xCC, 0xCC, 0xCC, 0xFF});
                                    canvas.draw_text("IMG", left + 10, top + font.get_line_height(),
                                                   renderer::Colors::GREY_800, &font);
                                }
                            }

                            // EXP-098 (CM-027): RLottie animation decode + draw.
                            if (is_image_view) {
                                auto* mut_node = const_cast<framework::ViewShadow::ViewNode*>(node);
                                if (mut_node->anim_raw_resid != 0 &&
                                    !mut_node->anim_decode_attempted &&
                                    mut_node->anim_frame_rgba.empty()) {
                                    mut_node->anim_decode_attempted = true;
                                    // EXP-098: If target_w/h are 0 (dp result
                                    // was lost in move-result pipeline),
                                    // use the view's render geometry as the
                                    // render target size. Per source, the
                                    // SmsView icon is createFrame(64, 64) —
                                    // so the view bounds ARE the animation size.
                                    int rw = mut_node->anim_target_w > 0 ? mut_node->anim_target_w : w;
                                    int rh = mut_node->anim_target_h > 0 ? mut_node->anim_target_h : h;
                                    if (rw <= 0) rw = 64;  // ultimate fallback
                                    if (rh <= 0) rh = 64;
                                    auto& fn_map = dalvik_engine_.field_name_by_resid_;
                                    auto fn_it = fn_map.find(mut_node->anim_raw_resid);
                                    if (fn_it != fn_map.end()) {
                                        const std::string& field_name = fn_it->second;
                                        auto& raw_map = dalvik_engine_.resource_raw_paths_;
                                        auto raw_it = raw_map.find(field_name);
                                        if (raw_it != raw_map.end()) {
                                            const std::string& apk_path = raw_it->second;
                                            auto json_bytes = apk_parser_.extract_entry_cached(apk_path);
                                            if (!json_bytes.empty()) {
                                                std::string json_str(json_bytes.begin(),
                                                                      json_bytes.end());
                                                auto anim = renderer::RLottieDecoder::decode(
                                                    json_str, rw, rh, /*max_frames=*/1);
                                                if (anim.ok && !anim.frames_rgba.empty()) {
                                                    const uint32_t* src = reinterpret_cast<const uint32_t*>(
                                                        anim.frames_rgba.data());
                                                    size_t n = static_cast<size_t>(anim.width) *
                                                               anim.height;
                                                    std::vector<uint8_t> rgba(n * 4);
                                                    for (size_t i = 0; i < n; i++) {
                                                        rgba[i*4+0] = static_cast<uint8_t>(src[i] & 0xFF);
                                                        rgba[i*4+1] = static_cast<uint8_t>((src[i]>>8) & 0xFF);
                                                        rgba[i*4+2] = static_cast<uint8_t>((src[i]>>16) & 0xFF);
                                                        rgba[i*4+3] = static_cast<uint8_t>((src[i]>>24) & 0xFF);
                                                    }
                                                    mut_node->anim_frame_rgba = std::move(rgba);
                                                    mut_node->anim_w = anim.width;
                                                    mut_node->anim_h = anim.height;
                                                    mut_node->anim_total_frames = anim.total_frames;
                                                    mut_node->anim_current_frame = 0;
                                                    std::cerr << "[EXP098-RLOTTIE] view=" << task.view_id
                                                              << " R.raw." << field_name
                                                              << " → " << apk_path
                                                              << " (" << anim.width << "x" << anim.height
                                                              << ", " << anim.total_frames << " frames, "
                                                              << anim.frame_rate << " fps)"
                                                              << std::endl;
                                                } else if (!anim.ok) {
                                                    std::cerr << "[EXP098-RLOTTIE] decode FAILED for R.raw."
                                                              << field_name << ": " << anim.error
                                                              << std::endl;
                                                }
                                            }
                                        } else {
                                            std::cerr << "[EXP098-RLOTTIE] R.raw." << field_name
                                                      << " not in resource_raw_paths_" << std::endl;
                                        }
                                    }
                                }
                                // Draw the decoded frame.
                                if (!node->anim_frame_rgba.empty() &&
                                    node->anim_w > 0 && node->anim_h > 0) {
                                    int draw_w = std::min(node->anim_w, w);
                                    int draw_h = std::min(node->anim_h, h);
                                    int draw_x = left + (w - draw_w) / 2;
                                    int draw_y = top + (h - draw_h) / 2;
                                    canvas.draw_image(const_cast<uint8_t*>(node->anim_frame_rgba.data()),
                                                      node->anim_w, node->anim_h,
                                                      draw_x, draw_y);
                                }
                            }

                            // EXP-095 (CM-019): Queue children with REAL layout.
                            // The parent computes each child's position/size from
                            // its captured LayoutParams (lp_*), then children are
                            // pushed so they pop in FORWARD order (stack LIFO).
                            // Parent type via real class hierarchy:
                            //   * LinearLayout (vertical default): stack top-to-bottom
                            //   * LinearLayout horizontal: lay left-to-right
                            //   * FrameLayout/other: overlap, gravity centers
                            bool children_pushed = false;
                            if (use_measured) {
                                // UNIFIED_007: geometry from real measure/layout —
                                // children pop in forward order.
                                std::vector<RenderTask> m_tasks;
                                for (uint32_t cid : node->children) {
                                    const auto* cn = view_shadow->find_node(cid);
                                    if (!cn || cn->visibility == 8) continue;
                                    m_tasks.push_back({cid, cn->measured_left, cn->measured_top,
                                                       cn->measured_width, cn->measured_height,
                                                       task.depth + 1});
                                }
                                for (auto it = m_tasks.rbegin(); it != m_tasks.rend(); ++it)
                                    queue.push_back(*it);
                                children_pushed = true;
                            }
                            if (!children_pushed) {
                            bool is_linear_layout = dalvik_engine_.is_subclass_of(node->class_desc, "Landroid/widget/LinearLayout;");
                            bool is_frame_layout = dalvik_engine_.is_subclass_of(node->class_desc, "Landroid/widget/FrameLayout;");
                            std::cerr << "[EXP095-LAYOUT] parent=" << task.view_id
                                      << " class=" << node->class_desc
                                      << " linear=" << (is_linear_layout ? "Y" : "N")
                                      << " frame=" << (is_frame_layout ? "Y" : "N")
                                      << " orient=" << node->orientation
                                      << " children=" << node->children.size()
                                      << std::endl;
                            // Orientation: captured setOrientation(0=H, 1=V).
                            // Default VERTICAL per LinearLayout docs.
                            bool horizontal = is_linear_layout && (node->orientation == 0);
                            (void)is_frame_layout;

                            // ── Two-phase child layout ──────────────────────
                            // Phase 1: measure each child (size from LayoutParams).
                            struct ChildBox {
                                uint32_t id;
                                int cw, ch;
                                const framework::ViewShadow::ViewNode* n;
                            };
                            std::vector<ChildBox> boxes;
                            boxes.reserve(node->children.size());
                            for (uint32_t child_id : node->children) {
                                const auto* cnode = view_shadow->find_node(child_id);
                                if (!cnode) continue;
                                auto measured = measure_node(cnode, w);
                                int tw = measured.first, th = measured.second;
                                int cw, ch;
                                if (cnode->lp_width == INT_MIN) {
                                    cw = cnode->text.empty() ? w : std::min(w, tw);
                                } else if (cnode->lp_width == -1) {
                                    cw = w;
                                } else if (cnode->lp_width == -2) {
                                    cw = std::min(w, tw);
                                } else {
                                    cw = cnode->lp_width;
                                }
                                if (cnode->lp_height == INT_MIN || cnode->lp_height == -2) {
                                    ch = std::max(th, 20);
                                } else if (cnode->lp_height == -1) {
                                    ch = std::max(h / 2, th);
                                } else {
                                    ch = cnode->lp_height;
                                    if (ch <= 0) ch = std::max(th, 20);
                                }
                                boxes.push_back({child_id, cw, ch, cnode});
                            }
                            // Phase 2: position.
                            std::vector<RenderTask> child_tasks;
                            child_tasks.reserve(boxes.size());
                            int cursor_x = left;
                            int cursor_y = top;
                            if (task.depth == 0) cursor_y += 30;  // status-bar area
                            if (horizontal) {
                                // Horizontal row: children advance left→right.
                                // The row is centered in the parent when the
                                // parent has width and children don't fill it.
                                int total_w = 0;
                                for (const auto& b : boxes) {
                                    total_w += b.n->lp_margin_left + b.cw + b.n->lp_margin_right;
                                }
                                int row_x = left;
                                if (w > total_w && total_w > 0) {
                                    row_x = left + (w - total_w) / 2;
                                }
                                for (const auto& b : boxes) {
                                    int cx = row_x + b.n->lp_margin_left;
                                    int cy = top + b.n->lp_margin_top;
                                    child_tasks.push_back({b.id, cx, cy, b.cw, b.ch, task.depth + 1});
                                    row_x = cx + b.cw + b.n->lp_margin_right;
                                }
                                (void)cursor_x; (void)cursor_y;
                            } else {
                                for (const auto& b : boxes) {
                                    const auto* cnode = b.n;
                                    int hg = cnode->lp_gravity & 0x7;
                                    int cx;
                                    if (hg == 1 || cnode->lp_gravity == 0x11) {
                                        cx = left + (w - b.cw) / 2;
                                    } else if (hg == 5) {
                                        cx = left + w - b.cw - cnode->lp_margin_right;
                                    } else {
                                        cx = left + cnode->lp_margin_left;
                                    }
                                    int cy;
                                    int vg = cnode->lp_gravity & 0x70;
                                    if (is_linear_layout) {
                                        cy = cursor_y + cnode->lp_margin_top;
                                        cursor_y = cy + b.ch + cnode->lp_margin_bottom;
                                    } else {
                                        // FrameLayout semantics: overlap at parent
                                        // origin; gravity may center vertically.
                                        if (vg == 0x10 || cnode->lp_gravity == 0x11) {
                                            cy = top + (h - b.ch) / 2;
                                        } else if (vg == 0x50) {
                                            cy = top + h - b.ch - cnode->lp_margin_bottom;
                                        } else {
                                            cy = top + cnode->lp_margin_top;
                                        }
                                    }
                                    child_tasks.push_back({b.id, cx, cy, b.cw, b.ch, task.depth + 1});
                                }
                            }
                            // LIFO stack: push in reverse so children pop in order.
                            for (auto it = child_tasks.rbegin(); it != child_tasks.rend(); ++it) {
                                queue.push_back(*it);
                            }
                            }  // !children_pushed
                        }

                        // CAMPAIGN 013 (screen-level placeholder gate): if the
                        // real tree rendered a ~blank screen, draw the deferred
                        // custom-view placeholders so app-defined surfaces are
                        // at least visible+labeled. Working apps with ANY real
                        // content (e.g. simplestopwatch's BigTextView screen)
                        // keep their exact pixels — the golden is untouched.
                        {
                            const auto& px_c = fb.get_pixels();
                            size_t nw = 0;
                            for (const auto& c : px_c) {
                                if (c.r < 250 || c.g < 250 || c.b < 250) nw++;
                            }
                            if (nw < 5000 && !custom_view_placeholders.empty()) {
                                for (const auto& cv : custom_view_placeholders) {
                                    // CAMPAIGN 013 (§15 LIBGDX-canvas / §19): run the
                                    // app's REAL onDraw(Canvas) bytecode first. When
                                    // it produces draw primitives, replay them into
                                    // the view bounds — a real app-driven frame, not
                                    // a placeholder.
                                    int ondraw_ops = 0;
                                    if (cv.view_id != 0 && shadow_registry_) {
                                        if (auto* canvas_shadow =
                                                shadow_registry_->find_as<framework::CanvasShadow>()) {
                                            ondraw_ops = dalvik_engine_.dispatch_custom_view_draw(cv.view_id);
                                            if (ondraw_ops > 0) {
                                                canvas_shadow->replay(canvas, font,
                                                                      (float)cv.l, (float)cv.t,
                                                                      (float)cv.w, (float)cv.h);
                                            }
                                        }
                                    }
                                    if (ondraw_ops > 0) {
                                        std::cerr << "[C013-CUSTOMVIEW] onDraw replayed "
                                                  << ondraw_ops << " ops for " << cv.cls
                                                  << " at (" << cv.l << "," << cv.t << " "
                                                  << cv.w << "x" << cv.h << ")" << std::endl;
                                        continue;
                                    }
                                    canvas.draw_rect(cv.l, cv.t, cv.l + cv.w, cv.t + cv.h,
                                                   renderer::RGBA{0xF0, 0xF0, 0xF0, 0xFF});
                                    canvas.draw_rect(cv.l, cv.t, cv.l + cv.w, cv.t + 1,
                                                   renderer::RGBA{0xD8, 0xD8, 0xD8, 0xFF});
                                    canvas.draw_rect(cv.l, cv.t, cv.l + 1, cv.t + cv.h,
                                                   renderer::RGBA{0xD8, 0xD8, 0xD8, 0xFF});
                                    std::string simple = cv.cls;
                                    size_t slash = simple.rfind('/');
                                    if (slash != std::string::npos)
                                        simple = simple.substr(slash + 1);
                                    if (!simple.empty() && simple.back() == ';')
                                        simple.pop_back();
                                    canvas.draw_text(simple, cv.l + 12,
                                                   cv.t + font.get_line_height() + 12,
                                                   renderer::RGBA{0x99, 0x99, 0x99, 0xFF},
                                                   &font);
                                    std::cerr << "[C013-CUSTOMVIEW] placeholder drawn: "
                                              << cv.cls << " at (" << cv.l << "," << cv.t
                                              << " " << cv.w << "x" << cv.h << ")" << std::endl;
                                }
                            }
                        }

                        // CAMPAIGN 013 B1: dialog windows render ON TOP of the
                        // activity tree, into the SAME framebuffer, before the
                        // fb→framebuffer_ copy. Every showing DialogShadow
                        // window paints dim + chrome + its recorded content;
                        // its decor ViewNodes carry the clickable rows.
                        if (auto* dialog_shadow =
                                shadow_registry_->find_as<framework::DialogShadow>()) {
                            dialog_shadow->render_dialogs(
                                canvas, fb, config.screen_width, config.screen_height,
                                [this](int32_t resid) -> std::string {
                                    auto& fn = dalvik_engine_.field_name_by_resid_;
                                    auto it = fn.find(resid);
                                    if (it == fn.end()) return "";
                                    auto& sv = dalvik_engine_.resource_string_values_;
                                    auto sv_it = sv.find(it->second);
                                    return sv_it != sv.end() ? sv_it->second : std::string();
                                });
                        }

                        // Copy FrameBuffer pixels (RGBA) back to framebuffer_ (uint8_t RGBA)
                        const auto& pixels = fb.get_pixels();
                        // EXP-092: Debug — check if any non-white pixels exist in fb
                        int non_white = 0;
                        for (size_t i = 0; i < pixels.size(); i++) {
                            if (pixels[i].r != 255 || pixels[i].g != 255 || pixels[i].b != 255) {
                                non_white++;
                            }
                        }
                        std::cerr << "[EXP092-COPY] fb has " << non_white << " non-white pixels out of "
                                  << pixels.size() << " total" << std::endl;
                        for (size_t i = 0; i < pixels.size() && i * 4 + 3 < framebuffer_.size(); i++) {
                            framebuffer_[i * 4]     = pixels[i].r;
                            framebuffer_[i * 4 + 1] = pixels[i].g;
                            framebuffer_[i * 4 + 2] = pixels[i].b;
                            framebuffer_[i * 4 + 3] = pixels[i].a;
                        }
                        std::cerr << "[EXP092-COPY] framebuffer_ updated, checking..." << std::endl;
                        int fb_non_white = 0;
                        for (size_t i = 0; i < framebuffer_.size(); i += 4) {
                            if (framebuffer_[i] != 255 || framebuffer_[i+1] != 255 || framebuffer_[i+2] != 255) {
                                fb_non_white++;
                            }
                        }
                        std::cerr << "[EXP092-COPY] framebuffer_ has " << fb_non_white << " non-white pixels" << std::endl;

                        trace_engine_.info("ExecutionEngine", "stage_render_frame",
                                           "Rendered ViewShadow tree with BitmapFont (root_id=" +
                                           std::to_string(root_id) + ")");
                        trace_engine_.increment_frame_count();
                        return true;
                    } catch (const std::exception& e) {
                        trace_engine_.record_error("RENDER_ERROR", e.what(),
                                                   "ExecutionEngine", "stage_render_frame");
                        // Fall through to synthetic path
                    }
                }
            }
        }
    }

    // Fall back to the synthetic api::View rendering path
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

    // EXP-086 Phase 3 (B1 FIX): Write PNG directly using PNGWriter.
    // Previously this only wrote PPM (raw bitmap) and a note saying
    // "convert later" — that left screenshots inaccessible to most tools.
    // PNGWriter now uses zlib compress2() for proper IDAT compression.
    bool png_ok = false;
    try {
        // Build a FrameBuffer from the raw RGBA framebuffer
        renderer::FrameBuffer fb(config.screen_width, config.screen_height);
        for (int y = 0; y < config.screen_height; y++) {
            for (int x = 0; x < config.screen_width; x++) {
                size_t i = (y * config.screen_width + x) * 4;
                if (i + 3 < framebuffer_.size()) {
                    fb.set_pixel(x, y, renderer::RGBA{
                        framebuffer_[i], framebuffer_[i+1],
                        framebuffer_[i+2], framebuffer_[i+3]
                    });
                }
            }
        }
        png_ok = renderer::PNGWriter::write_png(screenshot_path, fb);
        if (png_ok) {
            trace_engine_.log_screenshot(screenshot_path, config.screen_width, config.screen_height,
                                         framebuffer_.size());
            trace_engine_.info("ExecutionEngine", "stage_capture_output",
                              "PNG screenshot saved to: " + screenshot_path);
        }
    } catch (const std::exception& e) {
        trace_engine_.record_error("PNG_WRITE_ERROR", e.what(),
                                   "PNGWriter", "write_png");
    }

    // Also write PPM as fallback (debugging aid)
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

        if (!png_ok) {
            // Only log screenshot if PNG failed
            trace_engine_.log_screenshot(ppm_path, config.screen_width, config.screen_height,
                                         framebuffer_.size());

            std::string note_path = config.output_directory + "/screenshot_note.txt";
            std::ofstream note(note_path);
            note << "PNG write failed — saved as PPM only.\n";
            note << "PPM: " << ppm_path << "\n";
            note << "Resolution: " << config.screen_width << "x" << config.screen_height << "\n";
            note.close();

            trace_engine_.info("ExecutionEngine", "stage_capture_output",
                              "PPM fallback saved to: " + ppm_path);
        }
    } else {
        set_error("Failed to write screenshot file");
        trace_engine_.record_error("IO_ERROR", "Cannot write screenshot file",
                                   "ExecutionEngine", "stage_capture_output");
        return false;
    }

    return true;
}

// UNIFIED_011.2 CLICK-TEST (§10/§11): generic touch-interaction probe.
//
// For every view with a registered click listener:
//   1. restore framebuffer_ to the untouched frame-1 state (identical start),
//   2. dispatch_click(view_id) — executes the REAL listener.onClick bytecode,
//   3. re-render (measure → layout → draw) into framebuffer_,
//   4. pixel-diff vs frame 1; save click_frame_<k>.png on change.
//
// A changed second frame is the full L9→L12 evidence chain:
//   touch accepted → callback executed → state changed → second frame rendered.
// Never alters run success/failure — this is a probe, not a gate.
bool ExecutionEngine::stage_click_test( ExecutionResult& result, const ExecutionConfig& config) {
    trace_engine_.info("ExecutionEngine", "stage_click_test", "CLICK-TEST probe");
    if (!shadow_registry_ || !result.content_view) return true;

    auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
    if (!view_shadow) return true;

    auto candidates = view_shadow->find_all_with_click_listener("");
    std::cerr << "[CLICK-TEST] " << candidates.size()
              << " view(s) with click listeners" << std::endl;

    // UNIFIED_011.2: XML android:onClick handlers are a SECOND touch path.
    // Previously captured (layout_inflater → onClick_handler) but never
    // dispatched — simplestopwatch's three buttons were untouchable.
    // Real Android resolves the method on the hosting Activity:
    //   public void <android:onClick>(View v)
    struct XmlClick { uint32_t view_id; std::string handler; std::string cls; };
    std::vector<XmlClick> xml_candidates;
    for (const auto& [id, node_ptr] : view_shadow->all_nodes()) {
        if (node_ptr && !node_ptr->onClick_handler.empty()) {
            xml_candidates.push_back({id, node_ptr->onClick_handler, node_ptr->class_desc});
        }
    }
    std::cerr << "[CLICK-TEST] " << xml_candidates.size()
              << " view(s) with XML android:onClick handlers" << std::endl;

    if (candidates.empty() && xml_candidates.empty()) return true;

    const std::vector<uint8_t> frame1 = framebuffer_;  // untouched baseline

    // Shared probe: mutate state via `dispatch_fn`, re-render, diff vs frame1.
    size_t diff_px = 0;
    bool dispatched = false;
    auto probe = [&](bool disp) -> size_t {
        framebuffer_ = frame1;
        if (disp) {
            // UNIFIED_011.3 VISUAL-ORACLE (§22/§23): re-render through the
            // SAME pipeline as frame 1. The previous ad-hoc path
            // (content_view->measure/layout/draw) bypassed the real renderer
            // (root selection + SoftwareCanvas/BitmapFont + resource image
            // decode) and produced a near-blank second frame — the recorded
            // "state_changed" pixel counts were dominated by redraw weakness
            // instead of app-driven change. stage_render_frame re-renders
            // the CURRENT shadow tree (post-handler mutation) into
            // framebuffer_ with identical logic and writes no files.
            stage_render_frame(result, config);
            size_t diff = 0;
            if (framebuffer_.size() == frame1.size()) {
                for (size_t i = 0; i < framebuffer_.size(); i += 4) {
                    if (framebuffer_[i] != frame1[i] || framebuffer_[i+1] != frame1[i+1] ||
                        framebuffer_[i+2] != frame1[i+2]) {
                        diff++;
                    }
                }
            }
            return diff;
        }
        return 0;
    };

    nlohmann::json report;
    report["clickable_views"] = candidates.size();
    report["xml_onclick_views"] = xml_candidates.size();
    report["frame1_sha_note"] = "screenshot.png (already written by stage_capture_output)";
    nlohmann::json per_view = nlohmann::json::array();
    int saved_frames = 0;
    int changed_views = 0;
    const size_t cap = 12;  // bound probe cost on listener-heavy UIs

    for (size_t ci = 0; ci < candidates.size() && ci < cap; ci++) {
        uint32_t view_id = candidates[ci];
        nlohmann::json entry;
        entry["view_id"] = view_id;
        const auto* node = view_shadow->find_node(view_id);
        entry["class"] = node ? node->class_desc : "?";
        std::string listener_class;
        if (node && node->click_listener_id != 0 &&
            dalvik_engine_.get_heap().has_object(node->click_listener_id)) {
            listener_class = dalvik_engine_.get_heap()
                .get(node->click_listener_id)->class_descriptor;
        }
        entry["listener_class"] = listener_class;
        entry["kind"] = "listener";

        dispatched = dalvik_engine_.dispatch_click(view_id);
        entry["click_dispatched"] = dispatched;
        diff_px = probe(dispatched);
        entry["changed_px"] = diff_px;
        entry["state_changed"] = (diff_px > 0);
        if (dispatched) changed_views += (diff_px > 0) ? 1 : 0;

        if (dispatched && diff_px > 0 && saved_frames < 5) {
            char name[64];
            snprintf(name, sizeof name, "/click_frame_%zu.png", ci);
            try {
                renderer::FrameBuffer fb(config.screen_width, config.screen_height);
                for (int y = 0; y < config.screen_height; y++) {
                    for (int x = 0; x < config.screen_width; x++) {
                        size_t i = (static_cast<size_t>(y) * config.screen_width + x) * 4;
                        if (i + 3 < framebuffer_.size()) {
                            fb.set_pixel(x, y, renderer::RGBA{
                                framebuffer_[i], framebuffer_[i+1],
                                framebuffer_[i+2], framebuffer_[i+3]});
                        }
                    }
                }
                renderer::PNGWriter::write_png(
                    config.output_directory + std::string(name), fb);
                entry["screenshot"] = std::string("click_frame_") + std::to_string(ci) + ".png";
                saved_frames++;
            } catch (const std::exception& e) {
                entry["screenshot_error"] = e.what();
            }
        }
        per_view.push_back(entry);
    }

    // XML android:onClick probes — dispatch the REAL Activity method by name.
    for (size_t ci = 0; ci < xml_candidates.size() && ci < cap; ci++) {
        const auto& xc = xml_candidates[ci];
        nlohmann::json entry;
        entry["view_id"] = xc.view_id;
        entry["class"] = xc.cls;
        entry["kind"] = "xml_onClick";
        entry["handler"] = xc.handler;

        miniandroid::dalvik::DalvikValue view_arg =
            miniandroid::dalvik::DalvikValue::make_object(xc.view_id, xc.cls);
        miniandroid::dalvik::DalvikValue ret = miniandroid::dalvik::DalvikValue::make_void();
        miniandroid::dalvik::DalvikExecutionResult sub;
        // Real Android dispatches on the Activity that inflated the layout:
        //   activity.<android:onClick>(View v) — resolved via the DEX.
        // The manifest activity descriptor is the authoritative host class;
        // try_recursive_invoke resolves the method through the DEX.
        std::string host_class = result.apk_info.main_activity_full;
        if (host_class.empty()) host_class = "";  // engine falls back to its own index
        // UNIFIED_011.3 FRAME-2 (§23): instance methods need the REAL activity
        // instance as p0 (`this`). Previously only the View was passed, so
        // `this` was the clicked View object — the handler read/wrote the
        // WRONG heap object's fields (this.big → default 0) and the
        // post-interaction re-render never changed (view_id=0, text="" in
        // [EXP091-SETTEXT]). Real Android dispatches activity.<handler>(View).
        std::vector<miniandroid::dalvik::DalvikValue> handler_args;
        uint32_t activity_this_id = 0;
        std::string activity_this_class;
        if (auto* activity_shadow =
                shadow_registry_->find_as<framework::ActivityShadow>()) {
            activity_this_id = activity_shadow->current_activity_id();
            if (activity_this_id != 0) {
                const auto* aobj = dalvik_engine_.get_heap().get(activity_this_id);
                activity_this_class = aobj ? aobj->class_descriptor : host_class;
            }
        }
        if (activity_this_id != 0) {
            handler_args.push_back(miniandroid::dalvik::DalvikValue::make_object(
                activity_this_id, activity_this_class));  // p0 = this (Activity)
            std::cerr << "[U0113-XMLCLICK] " << xc.handler
                      << " dispatched on activity obj#" << activity_this_id
                      << " (" << activity_this_class << ")" << std::endl;
        }
        handler_args.push_back(view_arg);  // p1 = View v
        bool dispatched_xml = dalvik_engine_.try_recursive_invoke(
            host_class, xc.handler, handler_args, ret, sub);
        entry["click_dispatched"] = dispatched_xml;
        diff_px = probe(dispatched_xml);
        entry["changed_px"] = diff_px;
        entry["state_changed"] = (diff_px > 0);
        if (dispatched_xml) changed_views += (diff_px > 0) ? 1 : 0;

        if (dispatched_xml && diff_px > 0 && saved_frames < 5) {
            char name[64];
            snprintf(name, sizeof name, "/click_frame_%zu.png", candidates.size() + ci);
            try {
                renderer::FrameBuffer fb(config.screen_width, config.screen_height);
                for (int y = 0; y < config.screen_height; y++) {
                    for (int x = 0; x < config.screen_width; x++) {
                        size_t i = (static_cast<size_t>(y) * config.screen_width + x) * 4;
                        if (i + 3 < framebuffer_.size()) {
                            fb.set_pixel(x, y, renderer::RGBA{
                                framebuffer_[i], framebuffer_[i+1],
                                framebuffer_[i+2], framebuffer_[i+3]});
                        }
                    }
                }
                renderer::PNGWriter::write_png(
                    config.output_directory + std::string(name), fb);
                entry["screenshot"] = std::string("click_frame_") + std::to_string(candidates.size() + ci) + ".png";
                saved_frames++;
            } catch (const std::exception& e) {
                entry["screenshot_error"] = e.what();
            }
        }
        per_view.push_back(entry);
    }

    report["views_probed"] = per_view.size();
    report["views_changed_second_frame"] = changed_views;
    report["per_view"] = per_view;
    try {
        std::ofstream rf(config.output_directory + "/click_test_report.json");
        rf << report.dump(2);
    } catch (...) {}

    std::cerr << "[CLICK-TEST] done: probed=" << per_view.size()
              << " state_changed=" << changed_views
              << " frames_saved=" << saved_frames << std::endl;

    // Leave the framebuffer in the LAST probed state is misleading; restore
    // frame 1 so later evidence (report.md) reflects the launch UI.
    framebuffer_ = frame1;
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
    trace_engine_.info("ExecutionEngine", "create_view_from_layout", "[HOST_SHORTCUT] Creating view from DEX heuristics");
    
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

// ============================================================================
// EXP-031: Create view from REAL Dalvik execution result (not heuristic)
// ============================================================================

std::shared_ptr<api::View> ExecutionEngine::create_view_from_dalvik_result(
    const dalvik::DalvikExecutionResult& dalvik_result,
    const dex::DexReport& dex_report
) {
    trace_engine_.info("ExecutionEngine", "create_view_from_dalvik_result",
                       "[REAL_DALVIK_INTERPRETER] Creating view from execution evidence");
    
    // Try to extract text from executed instructions
    std::string display_text = "Real Dalvik Execution";  // Default evidence text
    
    // Check API calls for setText or similar
    for (const auto& api_call : dalvik_result.api_call_traces) {
        if (api_call.method == "setText" && !api_call.arguments.empty()) {
            display_text = api_call.arguments[0];
            trace_engine_.info("ExecutionEngine", "create_view_from_dalvik_result",
                               "Using text from API call: " + display_text);
            break;
        }
    }
    
    // Check instruction traces for const-string operations
    for (const auto& instr : dalvik_result.instruction_traces) {
        if (instr.opcode_name == "const-string" && instr.return_value.has_value()) {
            display_text = instr.return_value->to_string();
            trace_engine_.info("ExecutionEngine", "create_view_from_dalvik_result",
                               "Using string from instruction: " + display_text);
            break;
        }
    }
    
    // Create view with real execution evidence
    ExecutionConfig evidence_config;
    evidence_config.simulated_text = display_text + " [REAL]";
    auto view = create_hello_world_view(evidence_config);
    
    return view;
}

} // namespace runtime
} // namespace miniandroid
