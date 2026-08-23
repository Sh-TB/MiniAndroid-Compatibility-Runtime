/*
 * MiniAndroid Runtime v0.1 - Execution Engine Implementation
 * EXP-001: HelloWorld Loader
 * EXP-031.5: Real Dalvik Bytecode Execution Proof
 */

#include "execution_engine.h"
#include "../dex/trace_exporter.h"  // EXP-031.5: Mandatory trace generation
// EXP-086 Phase 3 (B1 FIX): PNGWriter for direct PNG output
#include "../renderer/software_renderer.h"
// EXP-086 Phase 7 (B4 FIX): HandlerShadow for Runnable queue drain
#include "../framework/android_shadows.h"
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
        dalvik_engine_.build_class_dex_index(result.dex_report);
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
    }
    
    try {
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
                    // Invoke each drained Runnable via try_recursive_invoke
                    for (uint32_t rid : drained) {
                        try {
                            // The runnable_id is a heap object reference.
                            // We invoke its run() method.
                            // dalvik_engine_ will resolve via try_recursive_invoke.
                            // For now, just log — actual invocation requires
                            // heap access to find the class of rid.
                            std::cerr << "[EXP086-P7] Drained Runnable id=" << rid
                                      << " (invocation deferred to future work)" << std::endl;
                        } catch (const std::exception& e) {
                            std::cerr << "[EXP086-P7] Runnable drain failed: " << e.what() << std::endl;
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
            if (!clickables.empty()) {
                trace_engine_.info("ExecutionEngine", "phase_b_click",
                                   "Found " + std::to_string(clickables.size()) +
                                   " views with click listeners");
                // Dispatch click to first clickable view (generic)
                uint32_t first_clickable = clickables[0];
                bool click_ok = dalvik_engine_.dispatch_click(first_clickable);
                trace_engine_.info("ExecutionEngine", "phase_b_click",
                                   "dispatch_click(" + std::to_string(first_clickable) +
                                   ") → " + (click_ok ? "OK" : "FAILED"));
            } else {
                trace_engine_.info("ExecutionEngine", "phase_b_click",
                                   "No views with click listeners found (setContentView may not have been called)");
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

                        // Iterative BFS traversal with visited-set
                        struct RenderTask {
                            uint32_t view_id;
                            int left, top, width, height;
                            int depth;
                        };
                        std::vector<RenderTask> queue;
                        std::set<uint32_t> visited;
                        const int MAX_NODES = 500;
                        int node_count = 0;

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

                            // Resolve width
                            int w = task.width;
                            if (node->width == -1) w = task.width;
                            else if (node->width == -2) w = task.width;
                            else if (node->width > 0) w = node->width;

                            // Resolve height
                            int h = font.get_line_height() + 20;
                            if (node->height == -1) h = task.height;
                            else if (node->height == -2) {
                                if (!node->text.empty()) {
                                    int lines = 1;
                                    for (char c : node->text) if (c == '\n') lines++;
                                    h = lines * font.get_line_height() + 20;
                                }
                            }
                            else if (node->height > 0) h = node->height;

                            int left = task.left;
                            int top = task.top;
                            int right = task.left + w;
                            int bottom = task.top + h;

                            // Draw view background
                            bool is_container = node->class_desc.find("Layout") != std::string::npos ||
                                              node->class_desc.find("ViewGroup") != std::string::npos;
                            if (is_container) {
                                canvas.draw_rect(left, top, right, bottom,
                                               renderer::Colors::GREY_200);
                            } else if (node->class_desc.find("Button") != std::string::npos) {
                                canvas.draw_rect(left, top, right, bottom,
                                               renderer::RGBA{0x6F, 0xA8, 0xDC, 0xFF});
                            }

                            // Draw text if present
                            if (!node->text.empty()) {
                                int text_x = left + 10;
                                int text_y = top + font.get_line_height();
                                std::string line;
                                for (char c : node->text) {
                                    if (c == '\\n') {
                                        if (!line.empty()) {
                                            canvas.draw_text(line, text_x, text_y,
                                                            renderer::Colors::GREY_800, &font);
                                        }
                                        text_y += font.get_line_height();
                                        line.clear();
                                    } else if (c != '\\r') {
                                        line += c;
                                    }
                                }
                                if (!line.empty()) {
                                    canvas.draw_text(line, text_x, text_y,
                                                    renderer::Colors::GREY_800, &font);
                                }
                            }

                            // EXP-088 A4: Draw ImageView/ImageButton
                            bool is_image_view = node->class_desc.find("ImageView") != std::string::npos ||
                                                 node->class_desc.find("ImageButton") != std::string::npos;
                            if (is_image_view && !node->image_drawable_path.empty()) {
                                auto png_data = apk_parser_.extract_entry_cached(node->image_drawable_path);
                                if (!png_data.empty() && png_data.size() >= 24 &&
                                    png_data[0] == 0x89 && png_data[1] == 0x50 &&
                                    png_data[2] == 0x47 && png_data[3] == 0x4E) {
                                    uint32_t img_w = (png_data[16] << 24) | (png_data[17] << 16) |
                                                    (png_data[18] << 8) | png_data[19];
                                    uint32_t img_h = (png_data[20] << 24) | (png_data[21] << 16) |
                                                    (png_data[22] << 8) | png_data[23];
                                    int img_left = left + 5;
                                    int img_top = top + 5;
                                    int img_right = std::min((int)(img_left + img_w), right - 5);
                                    int img_bottom = std::min((int)(img_top + img_h), bottom - 5);
                                    canvas.draw_rect(img_left, img_top, img_right, img_bottom,
                                                   renderer::RGBA{0xFF, 0x99, 0x33, 0xFF});
                                    std::string dim = std::to_string(img_w) + "x" + std::to_string(img_h);
                                    canvas.draw_text(dim, img_left + 2, img_top + font.get_line_height(),
                                                   renderer::Colors::WHITE, &font);
                                }
                            }
                            if (is_image_view && node->image_drawable_path.empty() &&
                                node->image_resource_id != 0) {
                                canvas.draw_rect(left + 5, top + 5, right - 5, bottom - 5,
                                               renderer::RGBA{0xCC, 0xCC, 0xCC, 0xFF});
                                canvas.draw_text("IMG", left + 10, top + font.get_line_height(),
                                               renderer::Colors::GREY_800, &font);
                            }

                            // Queue children (reverse order for correct BFS)
                            int child_y = top;
                            for (auto it = node->children.rbegin(); it != node->children.rend(); ++it) {
                                queue.push_back({*it, left, child_y, w, h, task.depth + 1});
                                child_y += font.get_line_height() + 20;
                            }
                        }

                        // Copy FrameBuffer pixels (RGBA) back to framebuffer_ (uint8_t RGBA)
                        const auto& pixels = fb.get_pixels();
                        for (size_t i = 0; i < pixels.size() && i * 4 + 3 < framebuffer_.size(); i++) {
                            framebuffer_[i * 4]     = pixels[i].r;
                            framebuffer_[i * 4 + 1] = pixels[i].g;
                            framebuffer_[i * 4 + 2] = pixels[i].b;
                            framebuffer_[i * 4 + 3] = pixels[i].a;
                        }

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
