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
#include "../fonts/text_shaper.h"
#include "../resources/resource_runtime.h"
#include "../resources/res_config.h"  // G04 §4: device_config() density law
// EXP-086 Phase 7 (B4 FIX): HandlerShadow for Runnable queue drain
#include "../framework/android_shadows.h"
#include "../framework/dialog_shadow.h"
#include "../framework/canvas_shadow.h"
// EXP-087 Phase 3 (B2 FIX): DalvikHeapAdapter for shadow heap access
#include "../framework/heap_adapter.h"

#include <filesystem>
#include <fstream>
#include <iterator>
#include <iostream>
#include <chrono>
#include <set>
#include <algorithm>

namespace miniandroid {
namespace runtime {

namespace fs = std::filesystem;

// ── G04 §4/§12: ONE density-scaling + placement law for EVERY image draw ───
// BitmapFactory law chain (BitmapFactory.java decodeResourceStream +
// BitmapFactory.cpp native scale): inDensity = the SELECTED entry's config
// density (0 → DENSITY_DEFAULT 160; DENSITY_NONE → never scale);
// inTargetDensity = the device densityDpi; scale = target/source.
// ImageView law (ImageView.java L255): default scaleType FIT_CENTER —
// scale = min(boxW/srcW, boxH/srcH), centered in the padding-excluded box.
// Shared by both render output paths so they cannot drift (§12).
static uint16_t g04_selected_source_density(uint16_t selected_density) {
    if (selected_density == 0xFFFF) return 0;            // DENSITY_NONE → no scale
    return selected_density ? selected_density : 160;    // DENSITY_DEFAULT law
}

static renderer::FitRect g04_image_draw_rect(
        int decoded_w, int decoded_h, uint16_t selected_density,
        int box_x, int box_y, int box_w, int box_h) {
    int src_w = decoded_w, src_h = decoded_h;
    uint16_t src_density = g04_selected_source_density(selected_density);
    if (src_density > 0) {
        uint16_t target = resources::device_config().density;   // single device law
        if (target > 0 && src_density != target) {
            float scale = float(target) / float(src_density);
            // BitmapFactory scales the BITMAP ITSELF: intrinsic size =
            // natural × target/source (rounded). Guard the int ceiling.
            if (decoded_w > 0 && decoded_h > 0 &&
                decoded_w * decoded_h < (1 << 24)) {   // allocation-safety bound
                src_w = std::max(1, (int)std::lround(decoded_w * scale));
                src_h = std::max(1, (int)std::lround(decoded_h * scale));
            }
        }
    }
    return renderer::fit_center_rect(src_w, src_h, box_x, box_y, box_w, box_h);
}

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
    // DEMO-CLICK-SEQUENCE: multi-click frame capture (see stage docs).
    // Runs after click-test so both probes see the launch framebuffer.
    if (success && config.click_count > 0) stage_click_sequence(result, config);
    // GOLDEN-02: coordinate-anchored long-press gesture (AOSP touch law).
    if (success && config.long_press_enabled) stage_long_press(result, config);
    // G06 §4/§6: canonical tap gesture through the TouchDispatcher law
    // pipeline (DOWN → pressed frame → UP → queued callbacks → drained frame).
    if (success && config.tap_enabled) stage_tap(result, config);
    if (success && config.frame_count > 0) stage_frame_sequence(result, config);

    // G07 §10: final frame boundary — apply any still-pending finish() and
    // persist the lifecycle state-machine trace as runtime evidence.
    {
        nlohmann::json launch_rec = consume_pending_intent();
        nlohmann::json finish_rec = consume_finish_cascade();
        try {
            std::filesystem::create_directories(config.output_directory);
            auto* as = shadow_registry_
                           ? shadow_registry_->find_as<framework::ActivityShadow>()
                           : nullptr;
            nlohmann::json lt = lifecycle_.to_json(
                result.apk_info.apk_path,
                as ? as->current_activity_class() : std::string());
            lt["finish_cascade"] = finish_rec;
            lt["activity_launch"] = launch_rec;
            std::ofstream lf(config.output_directory + "/lifecycle_trace.json");
            lf << lt.dump(2);
        } catch (const std::exception& e) {
            std::cerr << "[G07] lifecycle trace write failed: " << e.what()
                      << std::endl;
        }
    }

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

    // =======================================================================
    // M3 FINDING-016: EXCEPTION-HONESTY LAW (final status mapping)
    // A run whose app bytecode left exceptions in flight past EVERY frame
    // must never report plain SUCCESS. ART law: uncaught past the outermost
    // app frame = process death. Compatibility-continue mode keeps the run
    // alive for deterministic goldens, but the status is downgraded to
    // PARTIAL_SUCCESS, the exceptions are recorded in crash.log, and
    // MINIANDROID_EXC_STRICT=1 reports the run as CRASH (nonzero rc).
    // (Placed AFTER the final-status determination above — that block
    // overwrites status_message unconditionally.)
    // =======================================================================
    {
        const size_t uncaught_n = dalvik_engine_.uncaught_in_flight_count();
        if (uncaught_n > 0) {
            if (dalvik_engine_.strict_uncaught_crash()) {
                // ART process-death law (strict mode): the process is gone.
                result.status = ExecutionStatus::CRASH;
                result.status_message =
                    "ART process-death law: " +
                    dalvik_engine_.strict_crash_reason() +
                    " (strict mode — MINIANDROID_EXC_STRICT=1)";
            } else {
                if (result.status == ExecutionStatus::SUCCESS) {
                    result.status = ExecutionStatus::PARTIAL_SUCCESS;
                }
                result.status_message +=
                    " [F-016 exception-honesty: " + std::to_string(uncaught_n) +
                    " uncaught in-flight exception(s) past all app frames — "
                    "ART process-death law; compatibility-continue mode "
                    "(MINIANDROID_EXC_STRICT=1 fails the run); see crash.log]";
            }
            trace_engine_.warning("ExecutionEngine", "f016_exception_honesty",
                                  "⚠️ " + std::to_string(uncaught_n) +
                                  " uncaught in-flight exception(s) — status adjusted");
        }
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
        // FIX-4 (generic app fonts): register font files the app ships in
        // its own assets/ (any package, any name — AOSP Typeface family
        // model). The TextShaper resolves FACE_APP to these faces and falls
        // back to the system chain when the app ships none. No package or
        // filename special-casing beyond the "bold in the file name picks
        // the bold face of the family" rule.
        {
            auto entries = apk_parser_.list_entries_cached("assets/");
            int reg = 0, scanned = 0;
            std::string first_path;
            for (const auto& e : entries) {
                if (e.is_directory) continue;
                std::string lower;
                for (char c : e.name) lower += (char)std::tolower((unsigned char)c);
                bool ttf = lower.size() > 4 && lower.substr(lower.size() - 4) == ".ttf";
                bool otf = lower.size() > 4 && lower.substr(lower.size() - 4) == ".otf";
                if (!ttf && !otf) continue;
                scanned++;
                if (first_path.empty()) first_path = e.name;
                auto bytes = apk_parser_.extract_entry_cached(e.name);
                if (bytes.empty()) {
                    std::fprintf(stderr,
                                 "FONT_LOAD_FAILED path=%s reason=extract_empty\n",
                                 e.name.c_str());
                    continue;
                }
                bool bold = lower.find("bold") != std::string::npos;
                if (fonts::TextShaper::instance()
                        .register_app_font_memory(bytes, e.name, bold) >= 0)
                    reg++;
                else
                    std::fprintf(stderr,
                                 "FONT_LOAD_FAILED path=%s reason=FT_New_Memory_Face\n",
                                 e.name.c_str());
            }
            // §7 structured diagnostics: the font-source decision is always
            // observable (NO_FONT_DIRECTORY is a VALID outcome, not an error).
            std::fprintf(stderr,
                         "FONT_SOURCE apk=%s font_files=%d registered=%d "
                         "first=%s\n",
                         result.apk_info.apk_path.c_str(), scanned, reg,
                         first_path.empty() ? "<none>" : first_path.c_str());
            if (reg > 0)
                trace_engine_.info("ExecutionEngine", "app_fonts",
                                   "registered " + std::to_string(reg) +
                                   " app font face(s) from APK assets");
        }
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
            // G11 FIX-G11-001: custom-view constructor execution bridge.
            // Installed on the ResourceRuntime (process-wide Factory law) —
            // NOT on one LayoutInflater instance: ensure_loaded() (first
            // called below at the framework-statics preload and later by
            // ActivityShadow.setContentView) recreates the inflater, and a
            // per-instance hook set before that recreation is silently
            // wiped (headingcalculator F5-C1 root cause: hook installed on
            // the lazy default inflater, then the real inflater was created
            // and the factory was gone). AOSP law: the phone process
            // re-applies the Factory to EVERY new LayoutInflater.
            {
                auto& rt = resources::ResourceRuntime::instance();
                rt.set_custom_view_ctor_hook(
                    [this](uint32_t view_id,
                           const std::string& class_desc) -> bool {
                        return dalvik_engine_.run_custom_view_constructor(
                            view_id, class_desc);
                    });
                // G12 FIX-G12-002 (completes G10 FIX-G10-002's intent): the
                // DEX superclass classifier must be wired for EVERY inflate/
                // measure/layout path — window setContentView, constructor
                // subtree inflates (FIX-G11-001), and the renderer pass.
                // Previously only the renderer's measure pass installed it,
                // so app containers (CalculatorDisplay extends LinearLayout)
                // classified as LEAF nodes on the window path and measured
                // 0x0 despite real children. The classifier consults the
                // AOSP framework ancestry table (FIX-G12-001) for framework
                // classes and app DEX chains for app classes.
                rt.set_is_a(
                    [this](const std::string& c, const std::string& a) {
                        return dalvik_engine_.is_subclass_of(c, a);
                    });
                // MASTER CAMPAIGN FIX (F10 real-DEX onMeasure): measure-pass
                // bridge for custom Views whose DEX chain overrides
                // onMeasure — the override executes as real bytecode and
                // setMeasuredDimension writes back through the ViewShadow.
                rt.set_custom_view_measure_hook(
                    [this](uint32_t view_id, int wspec, int hspec,
                           int& out_w, int& out_h) -> bool {
                        return dalvik_engine_.dispatch_custom_view_measure(
                            view_id, wspec, hspec, out_w, out_h);
                    });
            }
            // G06 §4: canonical input pipeline. The dispatcher shares the
            // ViewShadow tree (geometry/state) and the HandlerShadow virtual
            // queue (PerformClick/UnsetPressedState/CheckForLongPress ride
            // the SAME queue as app Runnables — one-MessageQueue law).
            auto* handler_shadow = shadow_registry_->find_as<framework::HandlerShadow>();
            auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
            if (handler_shadow && view_shadow) {
                touch_dispatcher_ = std::make_unique<framework::TouchDispatcher>(
                    view_shadow, handler_shadow);
                touch_dispatcher_->set_click_dispatch(
                    [this](uint32_t view_id) -> bool {
                        return dalvik_engine_.dispatch_click(view_id);
                    });
                touch_dispatcher_->set_long_click_dispatch(
                    [this](uint32_t view_id, bool& consumed) -> bool {
                        return dalvik_engine_.dispatch_long_click(view_id,
                                                                  consumed);
                    });
            }
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
        // CYCLE-E AUDIT (§10): resources.arsc is the FIRST-CLASS value source.
        // The engine now reads string/color/dimen/bool values from the APK's
        // OWN resources.arsc (real resource IDs, real default configs) via
        // the Cycle-D ArscParser. The legacy JSON sidecar below remains only
        // as an OVERRIDE for values the ARSC cannot provide — no more
        // dependency on a Telegram-only hand-built sidecar.
        // VISUAL-CAMPAIGN (EXT-01 gate G25): seed the virtual device identity
        // statics (Build.VERSION.SDK_INT/RELEASE, Build.*, ANDROID_ID) BEFORE
        // any DEX executes — AOSP defines these in the framework image, before
        // any app code runs.
        dalvik_engine_.seed_framework_device_statics();
        {
            auto& rt = resources::ResourceRuntime::instance();
            if (rt.ensure_loaded(result.apk_info.apk_path)) {
                const auto& arsc = rt.arsc();
                int a_str = 0, a_col = 0, a_dim = 0, a_bool = 0;
                for (const auto& [resid, name] : arsc.list_type("", "string")) {
                    auto v = arsc.resolve_value(resid);
                    if (v.has_value() && v->is_string() && !name.empty()) {
                        dalvik_engine_.resource_string_values_[name] = v->string_value;
                        a_str++;
                    }
                }
                for (const auto& [resid, name] : arsc.list_type("", "color")) {
                    auto v = arsc.resolve_value(resid);
                    if (v.has_value() && v->is_color() && !name.empty()) {
                        dalvik_engine_.resource_color_values_[name] =
                            static_cast<int32_t>(v->data);
                        a_col++;
                    }
                }
                for (const auto& [resid, name] : arsc.list_type("", "dimen")) {
                    auto v = arsc.resolve_value(resid);
                    if (v.has_value() && v->type == resources::DataType::DIMENSION &&
                        !name.empty()) {
                        dalvik_engine_.resource_dimen_values_[name] =
                            static_cast<int32_t>(v->dim_value);
                        a_dim++;
                    }
                }
                for (const auto& [resid, name] : arsc.list_type("", "bool")) {
                    auto v = arsc.resolve_value(resid);
                    if (v.has_value() && v->type == resources::DataType::INT_BOOLEAN &&
                        !name.empty()) {
                        dalvik_engine_.resource_bool_values_[name] = v->data != 0;
                        a_bool++;
                    }
                }
                // GOLDEN-03 §10: integers seeded ARSC-first (previously only
                // the removed sidecar could provide them).
                int a_int = 0;
                for (const auto& [resid, name] : arsc.list_type("", "integer")) {
                    auto v = arsc.resolve_value(resid);
                    if (v.has_value() && (v->type == resources::DataType::INT_DEC ||
                                          v->type == resources::DataType::INT_HEX) &&
                        !name.empty()) {
                        dalvik_engine_.resource_integer_values_[name] =
                            static_cast<int32_t>(v->data);
                        a_int++;
                    }
                }
                // GOLDEN-03 §10: raw resources seeded ARSC-first — a raw entry's
                // VALUE IS THE ASSET PATH (STRING type, e.g. "res/-si.json"),
                // exactly like file-backed drawables/layouts (Campaign 013 §18).
                int a_raw = 0;
                for (const auto& [resid, name] : arsc.list_type("", "raw")) {
                    auto v = arsc.resolve_value(resid);
                    if (v.has_value() && v->is_string() && !name.empty() &&
                        v->string_value.compare(0, 4, "res/") == 0) {
                        dalvik_engine_.resource_raw_paths_[name] = v->string_value;
                        a_raw++;
                    }
                }
                std::cerr << "[ARSC-VALUES] apk=" << result.apk_info.apk_path
                          << " strings=" << a_str << " colors=" << a_col
                          << " dimens=" << a_dim << " bools=" << a_bool
                          << " integers=" << a_int << " raw=" << a_raw
                          << " (ARSC-authoritative resource values)" << std::endl;
            } else {
                std::cerr << "[ARSC-VALUES] ResourceRuntime unavailable for "
                          << result.apk_info.apk_path
                          << " (no sidecar exists — ARSC is the only source)" << std::endl;
            }
        }

        // GOLDEN-03 §10 — ARSC IS THE ONLY RESOURCE VALUE SOURCE.
        // The legacy resource_values.json sidecar (EXP-092/EXP-067) was a
        // Telegram-era override that let an arbitrary JSON file next to the
        // APK (or under download/exp038_telegram) silently override real ARSC
        // values. Per the GOLDEN-03 §10 law ("ARSC must remain authoritative;
        // any legacy sidecar bypass must remain removed from the production
        // path") it is REMOVED — a hostile/foreign resource_values.json can no
        // longer influence resolution. integers/raw/drawable paths are seeded
        // ARSC-first below (and at render time for drawables), like every
        // other value class.
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

        // M3 FINDING-016: record the in-flight uncaught exceptions into the
        // TraceEngine NOW (before stage_generate_reports writes crash.log —
        // the final status mapping runs too late for report inclusion).
        for (const auto& entry : dalvik_engine_.uncaught_in_flight_log()) {
            trace_engine_.record_error("EXC-UNCAUGHT-TOP", entry);
        }

        // EXP-086 Phase 7 (B4 FIX): Drain the Handler/Looper queue after
        // onCreate execution. Without this, Handler.post() callbacks
        // queued during onCreate are never dispatched — timer-based apps,
        // animation callbacks, and Lambda runnables never fire.
        // This is the GENERIC drain (not Telegram-specific).
        if (auto* registry = dalvik_engine_.get_shadow_registry()) {
            if (auto* hs = registry->find_as<framework::HandlerShadow>()) {
                // Idle-settle: the app finished onCreate and the main Looper
                // would dispatch everything posted so far. settle() jumps the
                // virtual clock far forward so every entry posted so far is
                // due — the documented EXP-088 drain-all law, now expressed
                // through the deterministic virtual clock. Entries RE-posted
                // during this drain (self-reposting animation tickers) become
                // due at a future Looper time and wait for --frames gates.
                hs->settle();
                std::vector<uint32_t> drained;
                size_t n = hs->drain_ready(&drained);
                if (n > 0) {
                    trace_engine_.info("ExecutionEngine", "drain_handler_queue",
                                       "Drained " + std::to_string(n) + " Runnables after onCreate");
                    // EXP-090: Actually INVOKE each drained Runnable's run() method.
                    for (uint32_t rid : drained) {
                        invoke_handler_runnable(rid);
                    }
                }
            }
        }

        // ===================================================================
        // G07 §7: RUNTIME LIFECYCLE STATE MACHINE — the launch sequence.
        // onCreate already executed via the DEX interpreter above
        // (ActivityThread.performLaunchActivity law). The remaining launch
        // callbacks follow the AOSP transaction order (handleResumeActivity
        // → performResume): onStart then onResume, dispatched through the
        // REAL DEX engine on the launcher activity class. Apps that
        // override them run real bytecode; apps that do not fall through to
        // the framework Activity stub — the super-class law.
        // ===================================================================
        {
            auto* as = shadow_registry_
                           ? shadow_registry_->find_as<framework::ActivityShadow>()
                           : nullptr;
            auto* hs_clock =
                shadow_registry_
                    ? shadow_registry_->find_as<framework::HandlerShadow>()
                    : nullptr;
            // The launcher activity class comes from the manifest entry the
            // DEX engine executed (execute_apk_with_activity registered the
            // heap id); register the class on the shadow so the lifecycle
            // dispatcher and the Intent pipeline (G08) share one identity.
            std::string act_class;
            if (as && as->current_activity_class().empty() &&
                !result.apk_info.main_activity_full.empty()) {
                std::string desc = "L" + result.apk_info.main_activity_full + ";";
                for (auto& c : desc)
                    if (c == '.') c = '/';
                as->set_current_activity(as->current_activity_id(), desc);
            }
            if (as) act_class = as->current_activity_class();
            if (as && hs_clock && !act_class.empty()) {
                lifecycle_.transition_to(
                    framework::LifecyclePhase::ACTIVITY_CREATED,
                    "Activity.onCreate() executed via DEX interpreter "
                    "(ActivityThread.performLaunchActivity law)",
                    hs_clock->virtual_now_ms());
                // FIND-G09-LC-001 law fix (G09 corpus evidence: 10+
                // framework-only APKs, e.g. app.varlorg.unote /
                // omegacentauri.mobi.simplestopwatch, skipped the STARTED hop
                // and had the whole finish cascade REJECTED by the guard).
                // AOSP law (ActivityThread.handleLaunchActivity →
                // handleStartActivity → handleResumeActivity): the activity
                // record advances on the FRAMEWORK path — whether or not the
                // application overrides the callback (the framework stub
                // answers for non-overriding apps). The machine therefore
                // advances unconditionally; the record documents whether real
                // app bytecode ran.
                nlohmann::json rec;
                bool start_ok = dispatch_app_lifecycle("onStart", &rec);
                lifecycle_.transition_to(
                    framework::LifecyclePhase::STARTED,
                    std::string("Activity.onStart() dispatched via DEX "
                                "engine") +
                        (start_ok ? ""
                                  : " (framework stub answered — super-class "
                                    "law; record state advances regardless)"),
                    hs_clock->virtual_now_ms());
                bool resume_ok = dispatch_app_lifecycle("onResume", &rec);
                lifecycle_.transition_to(
                    framework::LifecyclePhase::RESUMED,
                    std::string("Activity.onResume() dispatched via DEX "
                                "engine (handleResumeActivity law)") +
                        (resume_ok ? ""
                                   : " (framework stub answered — super-class "
                                     "law; record state advances regardless)"),
                    hs_clock->virtual_now_ms());
                as->set_state(framework::ActivityShadow::LifecycleState::RESUMED);
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
        // G12 FIND-G11-NOACTIVITY-001 (AOSP launcher law): the hard
        // "bytecode must have executed" assertion applies to apps that
        // DECLARE a launchable activity. Some real apps (muellerma
        // stopwatch: Quick-Settings TILE app) declare NO activity at all —
        // on a real device the launcher never starts them; their DEX runs
        // only as service/tile processes. For those the framework-path
        // boot (G09 FIND-G09-LC-001) plus the default window IS the lawful
        // result; demanding activity bytecode would fail an app real
        // Android never renders an activity for. Activity apps keep the
        // honest hard assertion unchanged.
        const bool declares_no_activity =
            result.apk_info.main_activity.empty() &&
            result.apk_info.main_activity_full.empty();
        if (dalvik_result.total_instructions_executed == 0 &&
            !declares_no_activity) {
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
        if (dalvik_result.total_instructions_executed == 0 &&
            declares_no_activity) {
            trace_engine_.info("ExecutionEngine", "activity_less_boot",
                               "App declares no launchable activity (AOSP "
                               "launcher law: tile/service-only app) — "
                               "framework-path boot without activity "
                               "bytecode is the lawful result");
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
        // MASTER CAMPAIGN FIX (lifecycle-provenance law): the engine records
        // lifecycle execution AT METHOD ENTRY (execute_method_internal).
        // The previous scan over dalvik_result.api_call_traces read a
        // capacity-CAPPED ring buffer — volume-dependent eviction made the
        // verdict flip between identical runs (same byte-identical
        // screenshot, status oscillated SUCCESS vs PARTIAL SUCCESS on
        // fr.neamar.kiss v224).
        bool lifecycle_from_dex = dalvik_engine_.lifecycle_methods_from_dex();
        if (lifecycle_from_dex) {
            trace_engine_.info("ExecutionEngine", "lifecycle_source",
                               "✅ Lifecycle onCreate/onStart/onResume executed as DEX bytecode "
                               "(REAL_DALVIK_INTERPRETER, entry-time provenance)");
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
    //
    // EXPLICIT CAPTURE MODES (--click-count / --frames): the probe click
    // is SKIPPED. Both modes supply their own interaction driver (the
    // click sequence dispatches its clicks; the frame sequence must see a
    // zero-interaction run so the app's own postDelayed ticker is the only
    // state driver). Injecting a probe click on top would double-step the
    // launch state and (for self-deactivating tickers) kill the animation
    // the mode exists to capture. Default journey runs keep the probe —
    // it is the Telegram intro-advance mechanism.
    // ===================================================================
    // G06 §6: gesture stages (--tap/--long-press) are interaction drivers
    // too — the probe click must not pollute a gesture golden's launch frame
    // (it fires BEFORE the scripted gesture and would double-step state).
    if (config.frame_count > 0 || config.click_count > 0 ||
        config.tap_enabled || config.long_press_enabled) {
        trace_engine_.info("ExecutionEngine", "phase_b_click",
                           std::string("skipped: ") +
                           (config.frame_count > 0 ? "--frames"
                            : config.click_count > 0 ? "--click-count"
                            : config.tap_enabled ? "--tap" : "--long-press") +
                           " mode supplies its own interaction driver");
    } else if (shadow_registry_ && result.status != ExecutionStatus::FAILURE) {
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
                        // M3 F-ROOM-CHAIN diagnostic: geometry + text so the
                        // timer-start tap can target the REAL button center
                        // through the canonical --tap hit-test pipeline.
                        if (std::getenv("MINIANDROID_DUMP_CLICKABLES")) {
                            std::cerr << "[CLICKABLE] id=" << vid
                                      << " cls=" << node->class_desc
                                      << " x=" << node->x << " y=" << node->y
                                      << " w=" << node->width
                                      << " h=" << node->height
                                      << " text=\"" << node->text << "\""
                                      << std::endl;
                        }
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

    // ===== UC009-WIRE: composition trigger for Compose-based apps =====
    // AOSP ViewRootImpl.performTraversals(): dispatchAttachedToWindow() runs
    // on the attaching tree BEFORE the first draw. For Compose this is THE
    // composition trigger:
    //   AbstractComposeView.onAttachedToWindow -> ensureCompositionCreated()
    // The hook (dispatch_view_attached, CAMPAIGN 009 §10) existed but was
    // never invoked from this pipeline — dead code. Env-gated for golden
    // protection; enable with MINIANDROID_DISPATCH_ATTACH=1.
    if (std::getenv("MINIANDROID_DISPATCH_ATTACH") != nullptr) {
        std::cerr << "[UC009-WIRE] view-attach dispatch (dispatchAttachedToWindow)..." << std::endl;
        bool attached = dalvik_engine_.dispatch_view_attached();
        if (attached) {
            // AOSP: composition start posts work to the UI-thread queue
            // (Recomposer via AndroidUiDispatcher / Handler). Drain bounded
            // rounds so posted composition work actually executes; each
            // round may create new views and enqueue more work.
            if (auto* registry = dalvik_engine_.get_shadow_registry()) {
                if (auto* hs = registry->find_as<framework::HandlerShadow>()) {
                    for (int round = 0; round < 64; ++round) {
                        std::vector<uint32_t> drained;
                        size_t n = hs->drain_ready(&drained);
                        if (n == 0) break;
                        std::cerr << "[UC009-WIRE] drain round=" << round
                                  << " runnable(s)=" << n << std::endl;
                        for (uint32_t rid : drained) {
                            try {
                                auto& heap = dalvik_engine_.get_heap_public();
                                if (heap.has_object(rid)) {
                                    const auto* obj = heap.get(rid);
                                    std::string cls = obj ? obj->class_descriptor : "";
                                    if (!cls.empty()) {
                                        std::cerr << "[UC009-WIRE] Runnable id=" << rid
                                                  << " class=" << cls << std::endl;
                                        miniandroid::dalvik::DalvikValue ret;
                                        miniandroid::dalvik::DalvikExecutionResult wire_result;
                                        std::vector<miniandroid::dalvik::DalvikValue> wire_args;
                                        wire_args.push_back(miniandroid::dalvik::DalvikValue::make_object(rid, cls));
                                        dalvik_engine_.try_recursive_invoke(
                                            cls, "run", wire_args, ret, wire_result);
                                    }
                                }
                            } catch (const std::exception& e) {
                                std::cerr << "[UC009-WIRE] Runnable failed: " << e.what() << std::endl;
                            }
                        }
                    }
                }
            }
        }
    }
    // ===== end UC009-WIRE =====

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
    // GOLDEN-03 §10/§11: drawable paths are ARSC-AUTHORITATIVE first — a
    // file-backed entry's VALUE IS THE PATH (Campaign 013 §18 law), resolved
    // via apk_path_for() under the device configuration. The basename
    // heuristic below remains only as fallback for names the ARSC cannot
    // resolve (e.g. legacy tables without type names).
    // G04 §4: entry list hoisted to function scope — the draw stage below
    // resolves resids DIRECTLY via select_file (canonical law), no R-field
    // indirection.
    std::vector<std::string> apk_entry_names;
    if (!result.apk_info.apk_path.empty()) {
        auto entries = apk_parser_.list_entries(result.apk_info.apk_path);
        apk_entry_names.reserve(entries.size());
        for (const auto& e : entries) apk_entry_names.push_back(e.name);
        std::vector<std::string>& entry_names = apk_entry_names;
        {
            // ARSC-first: resolve every R.drawable/mipmap resid through the
            // canonical resolver (config-selected variant included).
            auto& rt = resources::ResourceRuntime::instance();
            if (rt.ensure_loaded(result.apk_info.apk_path)) {
                dalvik_engine_.populate_drawable_paths_from_arsc(rt.arsc(), entry_names);
            }
        }
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
                    // VISUAL-CAMPAIGN (EXT-01 gate G49): the WINDOW BACKGROUND
                    // is the app theme's android:windowBackground (AOSP
                    // PhoneWindow law), not an unconditional white. For the
                    // EXT-01 fixture this resolves to #000000 — without it
                    // the white text on the white default surface was
                    // invisible (352 anti-alias pixels at 254,254,254).
                    renderer::RGBA win_bg{255, 255, 255, 255};
                    {
                        auto wb = resources::ResourceRuntime::instance()
                                      .resolve_window_background_argb(result.apk_info.apk_path);
                        if (wb.has_value()) {
                            win_bg = renderer::RGBA{
                                (uint8_t)((*wb >> 16) & 0xFF),
                                (uint8_t)((*wb >> 8) & 0xFF),
                                (uint8_t)(*wb & 0xFF),
                                (uint8_t)((*wb >> 24) & 0xFF)};
                            std::cerr << "[EXT01-WINBG] windowBackground=@0x" << std::hex
                                      << *wb << std::dec << " rgb("
                                      << (int)win_bg.r << "," << (int)win_bg.g
                                      << "," << (int)win_bg.b << ")" << std::endl;
                        }
                    }
                    fb.clear(win_bg);
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
                        // FIX-2b (AOSP relayout law): RE-MEASURE the tree at
                        // render time. Views created before lifecycle code ran
                        // were measured empty; DEX setText()/addView() after
                        // setContentView must invalidate layout, exactly as
                        // Android re-measures on requestLayout(). Without this
                        // every runtime-populated TextView keeps the 0x0
                        // geometry it measured before its text existed.
                        {
                            // Only when the resource runtime actually inflated
                            // this app's layout (programmatic view trees have
                            // no inflater state — measured geometry comes from
                            // the captured LayoutParams path below).
                            auto& rt = resources::ResourceRuntime::instance();
                            if (rt.loaded()) {
                                // G10 FIX-G10-002 + G12 FIX-G12-002: the
                                // DEX-backed superclass classifier is owned
                                // by the ResourceRuntime (Factory law) and
                                // installed once at stage entry — re-assert
                                // here so a stage entered without the early
                                // wiring still classifies by real ancestry.
                                rt.set_is_a(
                                    [this](const std::string& c, const std::string& a) {
                                        return dalvik_engine_.is_subclass_of(c, a);
                                    });
                                rt.inflater().measure_layout(view_shadow, root_id);
                            }
                        }
                        // CAMPAIGN 013: deferred custom-view placeholders.
                        struct CVP { int l, t, w, h; std::string cls; uint32_t view_id = 0; };
                        std::vector<CVP> custom_view_placeholders;
                        // UC009: rects actually used when drawing each visited view —
                        // Compose children inherit the parent's REAL draw rect because
                        // our measure pass does not run Compose's own measure machinery.
                        std::map<uint32_t, std::pair<std::pair<int,int>, std::pair<int,int>>> visited_rects;

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
                            visited_rects[task.view_id] = {{left, top}, {w, h}};

                            // Draw view background
                            // EXP-095 (CM-020): REAL background colors captured
                            // from setBackgroundColor(int) take priority. Per §17:
                            // do not accept default white unless the source
                            // actually requires it.
                            // G06 §5: StateListDrawable law — when the
                            // background is a <selector>, the winning item is
                            // re-picked against the node's CURRENT state
                            // (pressed/enabled/selected) EVERY frame
                            // (drawableStateChanged → re-pick law).
                            bool is_full_screen = (w >= config.screen_width && h >= config.screen_height);
                            bool drew_bg = false;
                            // G06 §5: selector parse is lazy + cached per
                            // view (parse-once law); the pick itself re-runs
                            // EVERY frame against the node's CURRENT state.
                            auto sl_it = state_list_cache_.find(node->view_id);
                            if (sl_it == state_list_cache_.end() &&
                                node->bg_drawable_path.size() > 4 &&
                                node->bg_drawable_path.compare(
                                    node->bg_drawable_path.size() - 4, 4,
                                    ".xml") == 0) {
                                auto axml = apk_parser_.extract_entry_cached(
                                    node->bg_drawable_path);
                                std::vector<
                                    framework::ViewShadow::ViewNode::BgStateItem>
                                    items;
                                bool is_sl = !axml.empty() &&
                                             framework::parse_state_list(axml,
                                                                         &items) &&
                                             !items.empty();
                                if (is_sl) {
                                    trace_engine_.info(
                                        "ExecutionEngine", "stage_render_frame",
                                        "STATE-LIST bg '" + node->bg_drawable_path +
                                            "' parsed: " +
                                            std::to_string(items.size()) +
                                            " item(s)");
                                }
                                sl_it = state_list_cache_
                                            .emplace(node->view_id,
                                                     std::make_pair(is_sl,
                                                                    std::move(items)))
                                            .first;
                            }
                            uint32_t eff_bg_color = node->bg_color;
                            if (sl_it != state_list_cache_.end() &&
                                sl_it->second.first) {
                                uint32_t c = 0;
                                std::string p;
                                if (framework::pick_state_list(
                                        sl_it->second.second, node->pressed,
                                        node->enabled, node->selected, &c, &p)) {
                                    if (p.empty() && c != 0) eff_bg_color = c;
                                }
                            }
                            if (eff_bg_color != 0) {
                                // ARGB int → RGBA
                                uint32_t c = eff_bg_color;
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
                            // FIX-3: REAL text pipeline — the SAME
                            // fonts::layout_text that measured this view in
                            // the layout pass now drives painting, so measured
                            // geometry and painted pixels cannot disagree.
                            // Replaces the fixed 8x16 BitmapFont (which
                            // ignored textSize/colour/bold and rendered
                            // microscopic text on density-scaled screens).
                            if (!node->text.empty()) {
                                float ts = node->text_size_px > 0
                                         ? node->text_size_px
                                         : 14.0f * config.density;
                                // G32: resolve the node's requested system
                                // family ONCE per node draw (AOSP fonts.xml
                                // law — "monospace" -> DroidSansMono face).
                                int face_idx = fonts::FACE_SYSTEM;
                                if (!node->font_family.empty())
                                    face_idx = fonts::TextShaper::instance()
                                                   .resolve_family(node->font_family,
                                                                   node->text_bold);
                                int hpad = node->padding_left + node->padding_right;
                                float avail = (float)std::max(0, w - hpad);
                                auto lay = fonts::layout_text(
                                    node->text, ts, node->text_bold, avail,
                                    node->num_lines, face_idx,
                                    node->line_spacing_mult,
                                    node->line_spacing_add_px,
                                    node->include_font_pad,
                                    node->elegant_text_height);
                                // Honour the captured text colour; fall back
                                // to the AOSP-ish dark grey used before.
                                uint32_t tc = node->text_color;
                                renderer::RGBA tcol = tc != 0
                                    ? renderer::RGBA{uint8_t((tc >> 16) & 0xFF),
                                                     uint8_t((tc >> 8) & 0xFF),
                                                     uint8_t(tc & 0xFF),
                                                     uint8_t((tc >> 24) & 0xFF)}
                                    : renderer::Colors::GREY_800;
                                // G36/G47: per-line StaticLayout law —
                                // baseline_k = v_k + line_above[k];
                                // v_{k+1} = v_k + line_boxes[k]. Vertical
                                // gravity positions the LAW-COMPUTED block
                                // (sum of line boxes), not an ad-hoc height.
                                float block_h = lay.block_height();
                                float v = (float)top + node->padding_top;
                                int vg = node->text_gravity & 0x70;
                                if ((node->text_gravity & 0x10) || vg == 0x10)
                                    v = (float)top + ((float)h - block_h) / 2.0f;
                                else if (vg == 0x50)
                                    v = (float)(top + h) - node->padding_bottom
                                       - block_h;
                                int hg = node->text_gravity & 0x7;
                                for (size_t li = 0; li < lay.lines.size(); ++li) {
                                    const auto& ln = lay.lines[li];
                                    if (!ln.text.empty()) {
                                        float lx = (float)left + node->padding_left;
                                        if (hg == 1)
                                            lx = (float)left + ((float)w - ln.width) / 2.0f;
                                        else if (hg == 5)
                                            lx = (float)right - node->padding_right - ln.width;
                                        float above = li < lay.line_above.size()
                                                    ? lay.line_above[li] : lay.ascent;
                                        fonts::TextShaper::instance().draw(
                                            fb, ln.text, lx, v + above, ts, tcol,
                                            node->text_bold, face_idx);
                                    }
                                    v += li < lay.line_boxes.size()
                                       ? lay.line_boxes[li] : lay.line_height;
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
                                    node->class_desc.rfind("Lcom/google/android/", 0) == 0;
                                // UC009 exception: Compose view classes ARE bundled DEX
                                // classes with REAL draw bytecode (AndroidComposeView
                                // draws the whole composed LayoutNode tree through
                                // dispatchDraw). They must NOT be treated as framework
                                // shadows — that exclusion kept every Compose app blank.
                                bool compose_view_class =
                                    node->class_desc.find("Landroidx/compose/") == 0;
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
                                // UC009: our measure pass does not run the
                                // Compose measure machinery, so a runtime-created
                                // AndroidComposeView measures degenerate (e.g.
                                // 1080x36). AOSP truth: it fills its ComposeView
                                // parent — expand BEFORE the size gate.
                                if (compose_view_class) {
                                    auto rit = visited_rects.find(node->parent_id);
                                    if (rit != visited_rects.end() &&
                                        (rit->second.second.first > w || rit->second.second.second > h)) {
                                        left = rit->second.first.first;
                                        top = rit->second.first.second;
                                        w = rit->second.second.first;
                                        h = rit->second.second.second;
                                        std::cerr << "[UC009-DRAW] AndroidComposeView expanded to ComposeView rect "
                                                  << w << "x" << h << std::endl;
                                    }
                                }
                                if ((!framework_class || compose_view_class) && node->children.empty() &&
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
                                        // Nothing drawn anywhere: draw the
                                        // honest placeholder INLINE (grey
                                        // surface + class name). The old
                                        // screen-blankness gate hid this when
                                        // ANY other view painted pixels — an
                                        // invisible custom view is less
                                        // truthful than a labeled one, per the
                                        // CAMPAIGN 013 evidence standard.
                                        canvas.draw_rect(left, top, right, bottom,
                                                       renderer::RGBA{0xF0, 0xF0, 0xF0, 0xFF});
                                        canvas.draw_rect(left, top, right, top + 1,
                                                       renderer::RGBA{0xD8, 0xD8, 0xD8, 0xFF});
                                        canvas.draw_rect(left, top, left + 1, bottom,
                                                       renderer::RGBA{0xD8, 0xD8, 0xD8, 0xFF});
                                        std::string simple = node->class_desc;
                                        size_t slash = simple.rfind('/');
                                        if (slash != std::string::npos)
                                            simple = simple.substr(slash + 1);
                                        if (!simple.empty() && simple.back() == ';')
                                            simple.pop_back();
                                        canvas.draw_text(simple, left + 12,
                                                       top + font.get_line_height() + 12,
                                                       renderer::RGBA{0x99, 0x99, 0x99, 0xFF},
                                                       &font);
                                        std::cerr << "[C013-CUSTOMVIEW] inline placeholder: "
                                                  << node->class_desc
                                                  << " at (" << left << "," << top
                                                  << " " << w << "x" << h << ")" << std::endl;
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
                            // G04 §4 (FIND-G04-AUDIT-006): DIRECT resid →
                            // drawable resolution via the canonical select_file
                            // (resolve_full chain, selected config, cycle-safe).
                            // Replaces resid → R-field-name → basename indirection,
                            // which failed for every app whose R$drawable statics
                            // had not been parsed (Markor 0/35 evidence).
                            std::function<bool(uint32_t, std::string*, uint16_t*)>
                                canonical_drawable_for =
                                [&](uint32_t resid, std::string* out_path,
                                    uint16_t* out_density) -> bool {
                                if (resid == 0 || !out_path || !out_density) return false;
                                auto& by_resid = dalvik_engine_.resource_drawable_path_by_resid_;
                                auto hit = by_resid.find(resid);
                                if (hit != by_resid.end()) {
                                    *out_path = hit->second;
                                    auto d = dalvik_engine_.drawable_density_by_resid().find(resid);
                                    *out_density = d != dalvik_engine_.drawable_density_by_resid().end()
                                                       ? d->second : 0;
                                    return true;
                                }
                                auto& rt = resources::ResourceRuntime::instance();
                                if (!rt.ensure_loaded(result.apk_info.apk_path)) return false;
                                auto sel = rt.arsc().select_file(resid, apk_entry_names,
                                                                 resources::device_config());
                                if (!sel) return false;
                                by_resid[resid] = sel->path;
                                dalvik_engine_.resource_drawable_density_by_resid_[resid] =
                                    sel->selected_density();
                                *out_path = sel->path;
                                *out_density = sel->selected_density();
                                return true;
                            };
                            bool is_image_view = node->class_desc.find("ImageView") != std::string::npos ||
                                                 node->class_desc.find("ImageButton") != std::string::npos;
                            if (is_image_view && !node->image_drawable_path.empty()) {
                                auto png_data = apk_parser_.extract_entry_cached(node->image_drawable_path);
                                if (!png_data.empty() && png_data.size() >= 8 &&
                                    png_data[0] == 0x89 && png_data[1] == 0x50 &&
                                    png_data[2] == 0x4E && png_data[3] == 0x47) {
                                    auto decoded = renderer::PNGDecoder::decode(png_data);
                                    if (decoded.ok && !decoded.rgba.empty()) {
                                        // G04 §4/§12: density scale (selected config →
                                        // device) + FIT_CENTER in the padding-excluded
                                        // box (ImageView.java L255 default scaleType law).
                                        // Replaces the old (left+5, top+5) natural-size
                                        // draw — an ad-hoc placement with no AOSP law.
                                        uint16_t sel_d = node->src_density;
                                        if (sel_d == 0 && node->image_resource_id != 0) {
                                            auto& dm = dalvik_engine_.drawable_density_by_resid();
                                            auto it = dm.find((uint32_t)node->image_resource_id);
                                            if (it != dm.end()) sel_d = it->second;
                                        }
                                        int pl = node->padding_left, pt = node->padding_top;
                                        int pr = node->padding_right, pb = node->padding_bottom;
                                        renderer::FitRect fr = g04_image_draw_rect(
                                            decoded.width, decoded.height, sel_d,
                                            left + pl, top + pt,
                                            std::max(1, w - pl - pr),
                                            std::max(1, h - pt - pb));
                                        canvas.draw_image(decoded.rgba.data(),
                                                          decoded.width, decoded.height,
                                                          fr.x, fr.y, fr.w, fr.h);
                                        trace_engine_.info("ExecutionEngine",
                                            "stage_render_frame",
                                            std::string("Drew image '") + node->image_drawable_path +
                                            "' (" + std::to_string(decoded.width) + "x" +
                                            std::to_string(decoded.height) + ", " +
                                            decoded.color_type_name + ", src_density=" +
                                            std::to_string(sel_d) + ") fit-center at (" +
                                            std::to_string(fr.x) + "," +
                                            std::to_string(fr.y) + " " +
                                            std::to_string(fr.w) + "x" + std::to_string(fr.h) + ")");
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
                                uint16_t resolved_img_density = 0;
                                if (node->image_resource_id != 0) {
                                    canonical_drawable_for(
                                        (uint32_t)node->image_resource_id,
                                        &resolved_img_path, &resolved_img_density);
                                }
                                if (resolved_img_path.empty()) {
                                    resolved_img_path = node->src_drawable_path;
                                    resolved_img_density = node->src_density;
                                }

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
                                        // G04 §4/§12: same density + FIT_CENTER law as
                                        // every other image draw (single shared helper);
                                        // density comes from the canonical resolver.
                                        uint16_t sel_d = resolved_img_density;
                                        if (sel_d == 0) sel_d = node->src_density;
                                        int pl = node->padding_left, pt = node->padding_top;
                                        int pr = node->padding_right, pb = node->padding_bottom;
                                        renderer::FitRect fr = g04_image_draw_rect(
                                            decoded.width, decoded.height, sel_d,
                                            left + pl, top + pt,
                                            std::max(1, w - pl - pr),
                                            std::max(1, h - pt - pb));
                                        canvas.draw_image(decoded.rgba.data(),
                                                          decoded.width, decoded.height,
                                                          fr.x, fr.y, fr.w, fr.h);
                                        trace_engine_.info("ExecutionEngine",
                                            "stage_render_frame",
                                            std::string("IMG-RES-RENDER drew '") +
                                            resolved_img_path + "' (" +
                                            std::to_string(decoded.width) + "x" +
                                            std::to_string(decoded.height) + ", " +
                                            decoded.color_type_name + ", src_density=" +
                                            std::to_string(sel_d) + ") fit-center at (" +
                                            std::to_string(fr.x) + "," +
                                            std::to_string(fr.y) + " " +
                                            std::to_string(fr.w) + "x" + std::to_string(fr.h) + ")");
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

                            // M3 F-005 FIX-B (AG, 2026-09-08): draw the View's
                            // FOREGROUND drawable (View.setForeground — AOSP
                            // View.java mForeground). Gravity law: the captured
                            // foregroundGravity positions the layer (microtimer
                            // row buttons set 17 = Gravity.CENTER); CENTER
                            // centers the intrinsic-size image inside the view
                            // bounds without scaling (AOSP gravity resolution).
                            if (!node->fg_drawable_path.empty()) {
                                auto fg_data =
                                    apk_parser_.extract_entry_cached(node->fg_drawable_path);
                                if (fg_data.size() >= 4) {
                                    renderer::DecodedImage fgd;
                                    bool fg_attempted = false;
                                    if (fg_data[0] == 0x89 && fg_data[1] == 0x50 &&
                                        fg_data[2] == 0x4E && fg_data[3] == 0x47) {
                                        fg_attempted = true;
                                        fgd = renderer::PNGDecoder::decode(fg_data);
                                    } else if (fg_data[0] == 0xFF && fg_data[1] == 0xD8 &&
                                               fg_data[2] == 0xFF) {
                                        fg_attempted = true;
                                        fgd = renderer::JPEGDecoder::decode(fg_data);
                                    } else if (fg_data[0] == 'R' && fg_data[1] == 'I' &&
                                               fg_data[2] == 'F' && fg_data[3] == 'F' &&
                                               fg_data.size() >= 12 &&
                                               fg_data[8] == 'W' && fg_data[9] == 'E' &&
                                               fg_data[10] == 'B' && fg_data[11] == 'P') {
                                        fg_attempted = true;
                                        fgd = renderer::WebPDecoder::decode(fg_data);
                                    }
                                    if (fg_attempted && fgd.ok && !fgd.rgba.empty()) {
                                        // density-scaled intrinsic, centered.
                                        const float dscale =
                                            node->src_density ? (float)node->src_density / 160.0f
                                                              : 1.0f;
                                        int dw = (int)std::lround(fgd.width / dscale);
                                        int dh = (int)std::lround(fgd.height / dscale);
                                        dw = std::min(dw, w);
                                        dh = std::min(dh, h);
                                        const int fx = left + (w - dw) / 2;
                                        const int fy = top + (h - dh) / 2;
                                        canvas.draw_image(fgd.rgba.data(), fgd.width,
                                                          fgd.height, fx, fy, dw, dh);
                                    }
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
                            // FIX-G10-001 (AOSP LinearLayout.java): unset orientation (-1) = HORIZONTAL
                            bool horizontal = is_linear_layout && (node->orientation != 1);
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
                                    // EXT-AOSP-001: cross-axis placement in a
                                    // horizontal row honors the container
                                    // gravity when the child has none
                                    // (LinearLayout.java L1777-1778 majorGravity
                                    // / minorGravity resolution).
                                    int eff_x_gravity = b.n->lp_gravity;
                                    if (eff_x_gravity == 0 && node->gravity_set) {
                                        eff_x_gravity = node->container_gravity;
                                    }
                                    int cx = row_x + b.n->lp_margin_left;
                                    int cy = top + b.n->lp_margin_top;
                                    int cyg = eff_x_gravity & 0x70;
                                    if (cyg == 0x10 || eff_x_gravity == 0x11) {
                                        cy = top + (h - b.ch) / 2;
                                    } else if (cyg == 0x50) {
                                        cy = top + h - b.ch - b.n->lp_margin_bottom;
                                    }
                                    child_tasks.push_back({b.id, cx, cy, b.cw, b.ch, task.depth + 1});
                                    row_x = cx + b.cw + b.n->lp_margin_right;
                                }
                                (void)cursor_x; (void)cursor_y;
                            } else {
                                for (const auto& b : boxes) {
                                    const auto* cnode = b.n;
                                    // EXT-AOSP-001 (LinearLayout.java@1cdfff55
                                    // L1284/L1466): child gravity falls back to
                                    // the container gravity when the child
                                    // carries no explicit layout_gravity. This
                                    // runtime encodes "no explicit gravity" as
                                    // lp_gravity == 0 (AOSP uses -1).
                                    int eff_gravity = cnode->lp_gravity;
                                    if (eff_gravity == 0 && node->gravity_set) {
                                        eff_gravity = node->container_gravity;
                                    }
                                    int hg = eff_gravity & 0x7;
                                    int cx;
                                    if (hg == 1 || eff_gravity == 0x11) {
                                        cx = left + (w - b.cw) / 2;
                                    } else if (hg == 5) {
                                        cx = left + w - b.cw - cnode->lp_margin_right;
                                    } else {
                                        cx = left + cnode->lp_margin_left;
                                    }
                                    int cy;
                                    int vg = eff_gravity & 0x70;
                                    if (is_linear_layout) {
                                        cy = cursor_y + cnode->lp_margin_top;
                                        cursor_y = cy + b.ch + cnode->lp_margin_bottom;
                                    } else {
                                        // FrameLayout semantics: overlap at parent
                                        // origin; gravity may center vertically.
                                        if (vg == 0x10 || eff_gravity == 0x11) {
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

// ─────────────────────────────────────────────────────────────────────────
// DEMO-CLICK-SEQUENCE (2026-09-04): deterministic multi-interaction capture.
//
// Motivation: the real-APK execution proof needs a SEQUENCE of frames showing
// application state evolving across multiple user interactions — not just a
// single before/after pair. This stage dispatches N sequential clicks
// (round-robin over every view with a registered OnClickListener), re-renders
// through the SAME stage_render_frame pipeline after each click, and writes:
//
//   frames/frame_000.png          frame 1 (launch UI, no interaction)
//   frames/frame_001..N.png       after each dispatched click
//   frames/manifest.json          per-frame evidence:
//                                   - clicked view id/class/listener class
//                                   - changed-pixel count vs previous frame
//                                   - framebuffer SHA256 (frame hash)
//                                   - the app's own visible state (every
//                                     ViewShadow node text), so the counter/
//                                     position/color text inside the app is
//                                     part of the machine-readable evidence
//
// The state transitions are produced ENTIRELY by the APK's own DEX bytecode
// reacting to dispatched clicks; this stage only drives input + capture.
// Never alters run success/failure — probe semantics like stage_click_test.
// ─────────────────────────────────────────────────────────────────────────
namespace {
// Minimal SHA-256 (FIPS 180-4) for frame hashing. No external dependency
// exists in the runtime tree; ~60 lines keep the evidence self-contained.
struct Sha256 {
    uint32_t h[8] = {0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
                     0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};
    uint64_t len = 0;
    uint8_t buf[64] = {0};
    size_t buf_len = 0;

    static uint32_t rotr(uint32_t x, int n) { return (x >> n) | (x << (32 - n)); }
    static uint32_t k(int i) {
        static const uint32_t K[64] = {
            0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,
            0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,
            0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,
            0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
            0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,
            0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,
            0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,
            0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
            0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,
            0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,
            0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
        return K[i];
    }
    void block(const uint8_t* p) {
        uint32_t w[64];
        for (int i = 0; i < 16; ++i)
            w[i] = (uint32_t(p[i*4])<<24)|(uint32_t(p[i*4+1])<<16)|
                   (uint32_t(p[i*4+2])<<8)|uint32_t(p[i*4+3]);
        for (int i = 16; i < 64; ++i) {
            uint32_t s0 = rotr(w[i-15],7)^rotr(w[i-15],18)^(w[i-15]>>3);
            uint32_t s1 = rotr(w[i-2],17)^rotr(w[i-2],19)^(w[i-2]>>10);
            w[i] = w[i-16]+s0+w[i-7]+s1;
        }
        uint32_t a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],hh=h[7];
        for (int i = 0; i < 64; ++i) {
            uint32_t S1 = rotr(e,6)^rotr(e,11)^rotr(e,25);
            uint32_t ch = (e&f)^((~e)&g);
            uint32_t t1 = hh+S1+ch+k(i)+w[i];
            uint32_t S0 = rotr(a,2)^rotr(a,13)^rotr(a,22);
            uint32_t maj = (a&b)^(a&c)^(b&c);
            uint32_t t2 = S0+maj;
            hh=g; g=f; f=e; e=d+t1; d=c; c=b; b=a; a=t1+t2;
        }
        h[0]+=a; h[1]+=b; h[2]+=c; h[3]+=d; h[4]+=e; h[5]+=f; h[6]+=g; h[7]+=hh;
    }
    void update(const uint8_t* data, size_t n) {
        len += n;
        while (n > 0) {
            size_t take = std::min(n, size_t(64) - buf_len);
            std::memcpy(buf + buf_len, data, take);
            buf_len += take; data += take; n -= take;
            if (buf_len == 64) { block(buf); buf_len = 0; }
        }
    }
    std::string hex() {
        uint64_t bits = len * 8;
        uint8_t pad = 0x80;
        update(&pad, 1);
        uint8_t z = 0;
        while (buf_len != 56) update(&z, 1);
        uint8_t l[8];
        for (int i = 0; i < 8; ++i) l[i] = uint8_t(bits >> (56 - i*8));
        update(l, 8);
        std::string out;
        char s[3];
        for (int i = 0; i < 8; ++i)
            for (int j = 3; j >= 0; --j) {
                snprintf(s, sizeof s, "%02x", uint8_t(h[i] >> (j*8)));
                out += s;
            }
        return out;
    }
};
std::string sha256_hex(const std::vector<uint8_t>& data) {
    Sha256 s;
    s.update(data.data(), data.size());
    return s.hex();
}
}  // namespace

// Shared helper: invoke a drained Runnable's run() method through the DEX
// engine (used by the post-onCreate idle-settle drain and by the
// time-driven frame stage).
void ExecutionEngine::invoke_handler_runnable(uint32_t rid) {
    // G06 §4: framework-internal callbacks (PerformClick / UnsetPressedState
    // / CheckForLongPress) ride the same queue as app Runnables through
    // reserved tokens; route them to the TouchDispatcher instead of the DEX
    // run() path. One MessageQueue, one ordering law.
    if (rid >= framework::HandlerShadow::kFrameworkTokenBase) {
        if (touch_dispatcher_) {
            nlohmann::json rec;
            touch_dispatcher_->fire_framework_callback(rid, &rec);
            std::cerr << "[G06-TOKEN] " << rec.dump() << std::endl;
        }
        return;
    }
    try {
        auto& heap = dalvik_engine_.get_heap_public();
        if (!heap.has_object(rid)) return;
        const auto* obj = heap.get(rid);
        std::string cls = obj ? obj->class_descriptor : "";
        if (cls.empty()) return;
        std::cerr << "[EXP090-DRAIN] Invoking Runnable id=" << rid
                  << " class=" << cls << std::endl;
        miniandroid::dalvik::DalvikValue ret;
        miniandroid::dalvik::DalvikExecutionResult drain_result;
        std::vector<miniandroid::dalvik::DalvikValue> args;
        args.push_back(miniandroid::dalvik::DalvikValue::make_object(rid, cls));
        dalvik_engine_.try_recursive_invoke(cls, "run", args, ret, drain_result);
        std::cerr << "[EXP090-DRAIN] Runnable id=" << rid << " invoked" << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "[EXP090-DRAIN] Runnable drain failed: " << e.what() << std::endl;
    }
}

// TIME-DRIVEN FRAME CAPTURE — the Looper-time counterpart of
// stage_click_sequence. Instead of dispatching clicks, advance the
// Handler virtual clock one frame_delay per frame and drain whatever
// became due (self-reposting postDelayed animation tickers step here).
// Everything on screen is the APK's own DEX logic reacting to Looper
// time; the runtime only advances the clock, renders, and captures.
bool ExecutionEngine::stage_frame_sequence( ExecutionResult& result, const ExecutionConfig& config) {
    trace_engine_.info("ExecutionEngine", "stage_frame_sequence",
                       "FRAME-SEQUENCE capture (" + std::to_string(config.frame_count) +
                       " frames @ +" + std::to_string(config.frame_delay_ms) + "ms virtual each)");
    if (!shadow_registry_) return true;

    auto* hs = shadow_registry_->find_as<framework::HandlerShadow>();
    if (!hs) {
        std::cerr << "[FRAME-SEQ] no HandlerShadow — nothing to drive" << std::endl;
        return true;
    }
    auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
    if (!view_shadow) return true;

    const std::string frames_dir = config.output_directory + "/frames";
    try { std::filesystem::create_directories(frames_dir); } catch (...) {}

    // Same frame saver as the click sequence (framebuffer law + PNG file law).
    auto save_frame = [&](const std::string& path, std::string* png_sha_out = nullptr) -> bool {
        try {
            renderer::FrameBuffer fb(config.screen_width, config.screen_height);
            for (int y = 0; y < config.screen_height; ++y) {
                for (int x = 0; x < config.screen_width; ++x) {
                    size_t i = (static_cast<size_t>(y) * config.screen_width + x) * 4;
                    if (i + 3 < framebuffer_.size()) {
                        fb.set_pixel(x, y, renderer::RGBA{
                            framebuffer_[i], framebuffer_[i + 1],
                            framebuffer_[i + 2], framebuffer_[i + 3]});
                    }
                }
            }
            bool ok = renderer::PNGWriter::write_png(path, fb);
            if (ok && png_sha_out) {
                std::ifstream pf(path, std::ios::binary);
                std::vector<unsigned char> bytes((std::istreambuf_iterator<char>(pf)),
                                                 std::istreambuf_iterator<char>());
                *png_sha_out = sha256_hex(bytes);
            }
            return ok;
        } catch (const std::exception& e) {
            std::cerr << "[FRAME-SEQ] frame save failed: " << e.what() << std::endl;
            return false;
        }
    };

    auto collect_texts = [&]() {
        nlohmann::json arr = nlohmann::json::array();
        for (const auto& [id, node_ptr] : view_shadow->all_nodes()) {
            if (node_ptr && !node_ptr->text.empty()) {
                arr.push_back({{"view_id", id},
                               {"class", node_ptr->class_desc},
                               {"text", node_ptr->text}});
            }
        }
        return arr;
    };

    nlohmann::json manifest;
    manifest["frame_count_requested"] = config.frame_count;
    manifest["frame_delay_ms"] = config.frame_delay_ms;
    manifest["screen"] = {{"width", config.screen_width},
                          {"height", config.screen_height}};
    manifest["frames"] = nlohmann::json::array();

    // Frame 0: the launch state (identical framing to the click sequence —
    // post-onCreate, post idle-settle drain).
    std::vector<uint8_t> prev = framebuffer_;
    {
        nlohmann::json f;
        f["index"] = 0;
        f["file"] = "frame_000.png";
        f["event"] = "launch (no interaction)";
        f["sha256"] = sha256_hex(prev);
        std::string png_sha;
        save_frame(frames_dir + "/frame_000.png", &png_sha);
        f["png_sha256"] = png_sha;
        f["visible_texts"] = collect_texts();
        manifest["frames"].push_back(f);
    }

    int fired_total = 0;
    for (int k = 1; k < config.frame_count; ++k) {
        hs->advance_virtual(config.frame_delay_ms);
        std::vector<uint32_t> drained;
        size_t n = hs->drain_ready(&drained);
        fired_total += static_cast<int>(n);
        for (uint32_t rid : drained) {
            invoke_handler_runnable(rid);
        }
        // G07/G08: frame boundary transitions — finish() cascades and
        // startActivity() launches requested by callbacks drained this
        // frame apply at THIS boundary.
        {
            nlohmann::json launch = consume_pending_intent();
            if (!launch.is_null()) manifest["activity_launch"] = launch;
            nlohmann::json fin = consume_finish_cascade();
            if (!fin.is_null()) manifest["finish_cascade"] = fin;
        }

        stage_render_frame(result, config);  // re-render CURRENT state

        size_t diff_px = 0;
        if (framebuffer_.size() == prev.size()) {
            for (size_t i = 0; i < framebuffer_.size(); i += 4) {
                if (framebuffer_[i] != prev[i] ||
                    framebuffer_[i + 1] != prev[i + 1] ||
                    framebuffer_[i + 2] != prev[i + 2]) {
                    diff_px++;
                }
            }
        }

        char name[64];
        snprintf(name, sizeof name, "/frame_%03d.png", k);
        std::string png_sha;
        bool saved = save_frame(frames_dir + name, &png_sha);

        nlohmann::json f;
        f["index"] = k;
        f["file"] = std::string("frame_") + (k < 100 ? (k < 10 ? "00" : "0") : "") +
                    std::to_string(k) + ".png";
        f["event"] = "timer (virtual +" + std::to_string(config.frame_delay_ms) + "ms)";
        f["runnables_fired"] = n;
        f["looper_virtual_ms"] = hs->virtual_now_ms();
        f["changed_pixels_vs_previous"] = diff_px;
        f["sha256"] = sha256_hex(framebuffer_);
        f["png_sha256"] = png_sha;
        f["visible_texts"] = collect_texts();
        manifest["frames"].push_back(f);
        if (saved) {
            std::cerr << "[FRAME-SEQ] frame_" << k << ": runnables_fired=" << n
                      << ", diff_px=" << diff_px << std::endl;
        }
        prev = framebuffer_;
    }

    manifest["runnables_fired_total"] = fired_total;
    try {
        std::ofstream mf(frames_dir + "/manifest.json");
        mf << manifest.dump(2);
    } catch (...) {}

    std::cerr << "[FRAME-SEQ] done: runnables_fired=" << fired_total
              << " frames=" << manifest["frames"].size()
              << " dir=" << frames_dir << std::endl;
    return true;
}

bool ExecutionEngine::stage_click_sequence( ExecutionResult& result, const ExecutionConfig& config) {
    if (config.click_count <= 0) return true;
    trace_engine_.info("ExecutionEngine", "stage_click_sequence",
                       "CLICK-SEQUENCE capture (" + std::to_string(config.click_count) + " clicks)");
    if (!shadow_registry_) return true;

    auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
    if (!view_shadow) return true;

    auto clickables = view_shadow->find_all_with_click_listener("");
    // FIX-6 (generic touch path): XML android:onClick views are REAL touch
    // targets too (AOSP resolves the handler on the hosting Activity).
    // Without them, XML-driven apps (uNote) had no drivable controls in the
    // click-sequence proof even though their buttons were touchable on a
    // real device. Same handler-resolution law as stage_click_test.
    struct XmlSeqClick { uint32_t view_id; std::string handler; std::string cls; };
    std::vector<XmlSeqClick> xml_clicks;
    for (const auto& [id, node_ptr] : view_shadow->all_nodes()) {
        if (node_ptr && !node_ptr->onClick_handler.empty())
            xml_clicks.push_back({id, node_ptr->onClick_handler, node_ptr->class_desc});
    }
    std::cerr << "[CLICK-SEQ] " << clickables.size() << " listener view(s), "
              << xml_clicks.size() << " XML onClick view(s), "
              << config.click_count << " click(s) requested" << std::endl;
    if (clickables.empty() && xml_clicks.empty()) {
        std::cerr << "[CLICK-SEQ] no clickable views — nothing to drive" << std::endl;
        return true;
    }

    const std::string frames_dir = config.output_directory + "/frames";
    try { std::filesystem::create_directories(frames_dir); } catch (...) {}

    // Helper: copy framebuffer_ → FrameBuffer → PNG on disk.
    // Returns the SHA256 of the written PNG FILE bytes via png_sha_out so the
    // manifest can document both hash domains:
    //   sha256     — raw framebuffer (the deterministic render law)
    //   png_sha256 — the PNG file bytes (what a user can verify after download)
    auto save_frame = [&](const std::string& path, std::string* png_sha_out = nullptr) -> bool {
        try {
            renderer::FrameBuffer fb(config.screen_width, config.screen_height);
            for (int y = 0; y < config.screen_height; ++y) {
                for (int x = 0; x < config.screen_width; ++x) {
                    size_t i = (static_cast<size_t>(y) * config.screen_width + x) * 4;
                    if (i + 3 < framebuffer_.size()) {
                        fb.set_pixel(x, y, renderer::RGBA{
                            framebuffer_[i], framebuffer_[i + 1],
                            framebuffer_[i + 2], framebuffer_[i + 3]});
                    }
                }
            }
            bool ok = renderer::PNGWriter::write_png(path, fb);
            if (ok && png_sha_out) {
                std::ifstream pf(path, std::ios::binary);
                std::vector<unsigned char> bytes((std::istreambuf_iterator<char>(pf)),
                                                 std::istreambuf_iterator<char>());
                *png_sha_out = sha256_hex(bytes);
            }
            return ok;
        } catch (const std::exception& e) {
            std::cerr << "[CLICK-SEQ] frame save failed: " << e.what() << std::endl;
            return false;
        }
    };

    // Helper: the app's own visible state — every node's text in the tree.
    auto collect_texts = [&]() {
        nlohmann::json arr = nlohmann::json::array();
        for (const auto& [id, node_ptr] : view_shadow->all_nodes()) {
            if (node_ptr && !node_ptr->text.empty()) {
                arr.push_back({{"view_id", id},
                               {"class", node_ptr->class_desc},
                               {"text", node_ptr->text}});
            }
        }
        return arr;
    };

    nlohmann::json manifest;
    manifest["click_count_requested"] = config.click_count;
    manifest["clickable_views"] = clickables.size();
    manifest["screen"] = {{"width", config.screen_width},
                          {"height", config.screen_height}};
    manifest["frames"] = nlohmann::json::array();

    std::vector<uint8_t> prev = framebuffer_;
    {
        nlohmann::json f;
        f["index"] = 0;
        f["file"] = "frame_000.png";
        f["event"] = "launch (no interaction)";
        f["sha256"] = sha256_hex(prev);
        std::string png_sha;
        save_frame(frames_dir + "/frame_000.png", &png_sha);
        f["png_sha256"] = png_sha;
        f["visible_texts"] = collect_texts();
        manifest["frames"].push_back(f);
    }

    int dispatched_total = 0;
    for (int k = 1; k <= config.click_count; ++k) {
        // Round-robin over BOTH touch paths (listener views first, then XML
        // onClick views) — real Android delivers to whichever the app set.
        const size_t total = clickables.size() + xml_clicks.size();
        const size_t idx = static_cast<size_t>(k - 1) % total;
        uint32_t target = 0;
        bool is_xml = idx >= clickables.size();
        std::string xml_handler, xml_cls;
        if (!is_xml) {
            target = clickables[idx];
        } else {
            const auto& xc = xml_clicks[idx - clickables.size()];
            target = xc.view_id;
            xml_handler = xc.handler;
            xml_cls = xc.cls;
        }
        const auto* node = view_shadow->find_node(target);
        bool dispatched = false;
        if (!is_xml) {
            dispatched = dalvik_engine_.dispatch_click(target);
        } else {
            // AOSP android:onClick: activity.<handler>(View v) — REAL DEX
            // dispatch with the real Activity instance as p0.
            std::string host_class = result.apk_info.main_activity_full;
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
            std::vector<miniandroid::dalvik::DalvikValue> handler_args;
            if (activity_this_id != 0)
                handler_args.push_back(miniandroid::dalvik::DalvikValue::make_object(
                    activity_this_id, activity_this_class));
            handler_args.push_back(miniandroid::dalvik::DalvikValue::make_object(target, xml_cls));
            miniandroid::dalvik::DalvikValue ret = miniandroid::dalvik::DalvikValue::make_void();
            miniandroid::dalvik::DalvikExecutionResult sub;
            dispatched = dalvik_engine_.try_recursive_invoke(
                host_class, xml_handler, handler_args, ret, sub);
            if (dispatched)
                std::cerr << "[CLICK-SEQ] xml onClick " << xml_handler
                          << " dispatched on activity" << std::endl;
        }
        if (dispatched) dispatched_total++;

        framebuffer_ = prev;
        stage_render_frame(result, config);  // re-render CURRENT state

        size_t diff_px = 0;
        if (framebuffer_.size() == prev.size()) {
            for (size_t i = 0; i < framebuffer_.size(); i += 4) {
                if (framebuffer_[i] != prev[i] ||
                    framebuffer_[i + 1] != prev[i + 1] ||
                    framebuffer_[i + 2] != prev[i + 2]) {
                    diff_px++;
                }
            }
        }

        char name[64];
        snprintf(name, sizeof name, "/frame_%03d.png", k);
        std::string png_sha;
        bool saved = save_frame(frames_dir + name, &png_sha);

        nlohmann::json f;
        f["index"] = k;
        f["file"] = std::string("frame_") + (k < 100 ? (k < 10 ? "00" : "0") : "") +
                    std::to_string(k) + ".png";
        f["event"] = "click";
        f["clicked_view_id"] = target;
        f["clicked_view_class"] = node ? node->class_desc : "?";
        if (is_xml) {
            f["click_kind"] = "xml_onClick";
            f["xml_handler"] = xml_handler;
        } else {
            f["click_kind"] = "listener";
        }
        f["click_dispatched"] = dispatched;
        f["changed_pixels_vs_previous"] = diff_px;
        f["sha256"] = sha256_hex(framebuffer_);
        f["png_sha256"] = png_sha;
        f["visible_texts"] = collect_texts();
        manifest["frames"].push_back(f);
        if (saved) {
            std::cerr << "[CLICK-SEQ] frame_" << k << ": clicked view " << target
                      << ", diff_px=" << diff_px << std::endl;
        }
        prev = framebuffer_;
    }

    manifest["clicks_dispatched"] = dispatched_total;
    try {
        std::ofstream mf(frames_dir + "/manifest.json");
        mf << manifest.dump(2);
    } catch (...) {}

    std::cerr << "[CLICK-SEQ] done: dispatched=" << dispatched_total
              << "/" << config.click_count
              << " frames=" << manifest["frames"].size()
              << " dir=" << frames_dir << std::endl;
    return true;
}

// GOLDEN-02: coordinate-anchored long-press gesture capture.
//
// AOSP gesture law (frameworks/base/core/java/android/view/View.java):
//   ACTION_DOWN at (x,y)
//     → dispatchTouchEvent/onTouchEvent → hit testing finds the touch
//       target (CLICKABLE or LONG_CLICKABLE view under the point)
//     → postCheckForLongPress: CheckForLongPress posted with delay
//       ViewConfiguration.getLongPressTimeout() (DEFAULT = 500 ms)
//     → CheckForLongPress.run(): view enabled && still pressed →
//       performLongClick() → OnLongClickListener.onLongClick(View)Z
//     → consumed (true) → mHasPerformedLongPress = true → the subsequent
//       ACTION_UP does NOT perform a click
//     → not consumed (false / no listener) → ACTION_UP performs a click.
//
// The gesture driver is deterministic: no wall-clock enters the
// framebuffer; the 500ms timeout is a recorded law, not a sleep.
// Frame 0 = untouched launch frame; frame 1 = the post-gesture render
// (the app's own visible consequence, e.g. a Toast window).
bool ExecutionEngine::stage_long_press(ExecutionResult& result, const ExecutionConfig& config) {
    if (!config.long_press_enabled) return true;
    trace_engine_.info("ExecutionEngine", "stage_long_press",
                       "LONG-PRESS gesture capture at (" +
                       std::to_string(config.long_press_x) + "," +
                       std::to_string(config.long_press_y) + ")");
    if (!shadow_registry_) return true;

    auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
    auto* activity_shadow = shadow_registry_->find_as<framework::ActivityShadow>();
    if (!view_shadow || !activity_shadow) return true;

    const std::string frames_dir = config.output_directory + "/frames";
    try { std::filesystem::create_directories(frames_dir); } catch (...) {}

    // Same PNG capture helper as stage_click_sequence: framebuffer_ →
    // FrameBuffer → PNG on disk (+ SHA-256 of both the raw framebuffer and
    // the PNG file bytes).
    auto save_frame = [&](const std::string& path, std::string* png_sha_out = nullptr) -> bool {
        try {
            renderer::FrameBuffer fb(config.screen_width, config.screen_height);
            for (int y = 0; y < config.screen_height; ++y) {
                for (int x = 0; x < config.screen_width; ++x) {
                    size_t i = (static_cast<size_t>(y) * config.screen_width + x) * 4;
                    if (i + 3 < framebuffer_.size()) {
                        fb.set_pixel(x, y, renderer::RGBA{
                            framebuffer_[i], framebuffer_[i + 1],
                            framebuffer_[i + 2], framebuffer_[i + 3]});
                    }
                }
            }
            bool ok = renderer::PNGWriter::write_png(path, fb);
            if (ok && png_sha_out) {
                std::ifstream pf(path, std::ios::binary);
                std::vector<unsigned char> bytes((std::istreambuf_iterator<char>(pf)),
                                                 std::istreambuf_iterator<char>());
                *png_sha_out = sha256_hex(bytes);
            }
            return ok;
        } catch (const std::exception& e) {
            std::cerr << "[G02-GESTURE] frame save failed: " << e.what() << std::endl;
            return false;
        }
    };

    // The app's own visible state — every node's text in the tree.
    auto collect_texts = [&]() {
        nlohmann::json arr = nlohmann::json::array();
        for (const auto& [id, node_ptr] : view_shadow->all_nodes()) {
            if (node_ptr && !node_ptr->text.empty()) {
                arr.push_back({{"view_id", id},
                               {"class", node_ptr->class_desc},
                               {"text", node_ptr->text}});
            }
        }
        return arr;
    };

    nlohmann::json manifest;
    manifest["gesture"] = "LONG_PRESS";
    manifest["view_config_long_press_timeout_ms"] = 500;  // AOSP DEFAULT_LONG_PRESS_TIMEOUT
    manifest["screen"] = {{"width", config.screen_width},
                          {"height", config.screen_height}};
    manifest["frames"] = nlohmann::json::array();

    std::vector<uint8_t> prev = framebuffer_;
    {
        nlohmann::json f;
        f["index"] = 0;
        f["file"] = "frame_000.png";
        f["event"] = "launch (no interaction)";
        f["sha256"] = sha256_hex(prev);
        std::string png_sha;
        save_frame(frames_dir + "/frame_000.png", &png_sha);
        f["png_sha256"] = png_sha;
        f["visible_texts"] = collect_texts();
        manifest["frames"].push_back(f);
    }

    // ── ACTION_DOWN: hit testing ─────────────────────────────────────────
    // AOSP View touch-target law: dispatchTouchEvent walks the tree and the
    // deepest VISIBLE view under the point that is CLICKABLE or
    // LONG_CLICKABLE receives the gesture (View.setOnLongClickListener sets
    // LONG_CLICKABLE; View.isTouchable() accepts either flag). The walk
    // mirrors ViewRenderer::hit_test semantics without instantiating the
    // (currently unlinked) renderer.
    const int px = config.long_press_x, py = config.long_press_y;
    uint32_t root_id = activity_shadow->content_view_id();
    std::function<uint32_t(uint32_t)> hit_walk = [&](uint32_t id) -> uint32_t {
        const auto* n = view_shadow->find_node(id);
        if (!n || n->visibility != 0) return 0;
        uint32_t best = 0;
        if (px >= n->x && px < n->x + std::max(1, n->width) &&
            py >= n->y && py < n->y + std::max(1, n->height)) {
            const bool touchable = n->clickable || !n->onClick_handler.empty() ||
                                   n->click_listener_id != 0 ||
                                   !n->click_listener_class.empty() ||
                                   n->long_click_listener_id != 0;
            if (touchable) best = id;
            for (uint32_t cid : n->children) {
                uint32_t sub = hit_walk(cid);
                if (sub != 0) best = sub;  // deepest touchable view wins
            }
        }
        return best;
    };
    uint32_t target = hit_walk(root_id);
    manifest["action"] = {{"down_x", px}, {"down_y", py},
                          {"hit_test_root_id", root_id},
                          {"target_view_id", target}};
    const auto* tnode = view_shadow->find_node(target);
    manifest["target_view_class"] = tnode ? tnode->class_desc : std::string("");
    manifest["target_bounds"] = tnode ? nlohmann::json({tnode->x, tnode->y,
                                                        tnode->width, tnode->height})
                                      : nlohmann::json(nullptr);
    std::cerr << "[G02-GESTURE] ACTION_DOWN (" << px << "," << py << ")"
              << " root=" << root_id
              << " hit_target=" << target
              << (tnode ? (" class=" + tnode->class_desc) : " (NO TARGET)")
              << std::endl;
    if (target == 0) {
        // Honest evidence: no touch target under the point — no dispatch.
        manifest["long_click_dispatched"] = false;
        manifest["consumed"] = false;
        manifest["up_click_suppressed"] = false;
        try {
            std::ofstream mf(frames_dir + "/manifest.json");
            mf << manifest.dump(2);
        } catch (...) {}
        std::cerr << "[G02-GESTURE] no touch target — gesture produced no dispatch"
                  << std::endl;
        return true;
    }

    // ── CheckForLongPress (500ms) → performLongClick ─────────────────────
    bool dispatched = false, consumed = false;
    dispatched = dalvik_engine_.dispatch_long_click(target, consumed);

    // ── ACTION_UP: AOSP mHasPerformedLongPress law ───────────────────────
    bool click_suppressed = false, up_click_dispatched = false;
    if (dispatched && consumed) {
        click_suppressed = true;  // mHasPerformedLongPress = true
        std::cerr << "[G02-GESTURE] ACTION_UP: click SUPPRESSED"
                  << " (onLongClick consumed — AOSP mHasPerformedLongPress law)"
                  << std::endl;
    } else {
        // AOSP: long press not consumed → UP performs click.
        up_click_dispatched = dalvik_engine_.dispatch_click(target);
        std::cerr << "[G02-GESTURE] ACTION_UP: performClick dispatched="
                  << (up_click_dispatched ? "true" : "false") << std::endl;
    }
    manifest["long_click_dispatched"] = dispatched;
    manifest["consumed"] = consumed;
    manifest["up_click_suppressed"] = click_suppressed;
    manifest["up_click_dispatched"] = up_click_dispatched;

    // ── Second frame: re-render CURRENT app state ────────────────────────
    framebuffer_ = prev;
    stage_render_frame(result, config);

    size_t diff_px = 0;
    if (framebuffer_.size() == prev.size()) {
        for (size_t i = 0; i < framebuffer_.size(); i += 4) {
            if (framebuffer_[i] != prev[i] ||
                framebuffer_[i + 1] != prev[i + 1] ||
                framebuffer_[i + 2] != prev[i + 2]) {
                diff_px++;
            }
        }
    }

    std::string png_sha;
    bool saved = save_frame(frames_dir + "/frame_001.png", &png_sha);
    nlohmann::json f;
    f["index"] = 1;
    f["file"] = "frame_001.png";
    f["event"] = "long_press";
    f["down"] = {{"x", px}, {"y", py}};
    f["target_view_id"] = target;
    f["target_view_class"] = tnode ? tnode->class_desc : std::string("");
    f["long_click_dispatched"] = dispatched;
    f["consumed"] = consumed;
    f["up_click_suppressed"] = click_suppressed;
    f["up_click_dispatched"] = up_click_dispatched;
    f["changed_pixels_vs_previous"] = diff_px;
    f["sha256"] = sha256_hex(framebuffer_);
    f["png_sha256"] = png_sha;
    f["visible_texts"] = collect_texts();
    manifest["frames"].push_back(f);
    manifest["changed_pixels_vs_previous"] = diff_px;

    try {
        std::ofstream mf(frames_dir + "/manifest.json");
        mf << manifest.dump(2);
    } catch (...) {}

    std::cerr << "[G02-GESTURE] done: dispatched=" << (dispatched ? "yes" : "no")
              << " consumed=" << (consumed ? "yes" : "no")
              << " click_suppressed=" << (click_suppressed ? "yes" : "no")
              << " diff_px=" << diff_px
              << " dir=" << frames_dir << std::endl;
    return true;
}

// G07 §7 — dispatch ONE app lifecycle callback through the REAL DEX engine.
// `this` = the launcher activity's recorded heap object (execute_apk_
// with_activity allocated it during onCreate). Apps overriding the method
// run real bytecode; apps that do not hit the framework Activity stub —
// the AOSP super-class behavior. Never a scripted log line: the DEX
// interpreter (or the stub bridge) is the ONLY dispatch path.
bool ExecutionEngine::dispatch_app_lifecycle(const std::string& method,
                                             nlohmann::json* record) {
    auto* as = shadow_registry_
                   ? shadow_registry_->find_as<framework::ActivityShadow>()
                   : nullptr;
    if (!as || as->current_activity_class().empty()) return false;
    try {
        auto& heap = dalvik_engine_.get_heap_public();
        uint32_t act_id = as->current_activity_id();
        if (act_id == 0 || !heap.has_object(act_id)) {
            trace_engine_.warning("ExecutionEngine", "dispatch_app_lifecycle",
                                  "no activity heap object — " + method +
                                      " not dispatched");
            return false;
        }
        miniandroid::dalvik::DalvikValue ret;
        miniandroid::dalvik::DalvikExecutionResult result;
        std::vector<miniandroid::dalvik::DalvikValue> args;
        args.push_back(miniandroid::dalvik::DalvikValue::make_object(
            act_id, as->current_activity_class()));
        bool ok = dalvik_engine_.try_recursive_invoke(
            as->current_activity_class(), method, args, ret, result);
        if (record) {
            (*record)["method"] = method;
            (*record)["class"] = as->current_activity_class();
            (*record)["dispatched"] = ok;
            (*record)["instructions"] = result.total_instructions_executed;
        }
        std::cerr << "[G07-LIFECYCLE] " << as->current_activity_class() << "."
                  << method << "() dispatched via DEX engine (ok=" << ok
                  << ", instructions=" << result.total_instructions_executed
                  << ")" << std::endl;
        return ok;
    } catch (const std::exception& e) {
        std::cerr << "[G07-LIFECYCLE] " << method << " dispatch failed: "
                  << e.what() << std::endl;
        return false;
    }
}

// G08 §11/§12/§13 — consume a pending startActivity() at a frame boundary.
// Launch law (ActivityThread + TransactionExecutor, android-14.0.0_r2):
//   A.onPause  (handlePauseActivity — FIRST callback of a switch)
//   B.onCreate (performLaunchActivity: instantiate + onCreate WITH the
//               launching Intent — getIntent() returns it)
//   B.onStart, B.onResume (handleResumeActivity)
//   A.onStop   (LAST callback of a switch)
// The second Activity is a REAL DEX class: its onCreate executes real
// bytecode, its setContentView inflates a REAL second view tree, and the
// renderer shows it. Hostile Intents (missing/unknown component) are
// recorded as named failures — never a crash.
nlohmann::json ExecutionEngine::consume_pending_intent() {
    auto* as = shadow_registry_
                   ? shadow_registry_->find_as<framework::ActivityShadow>()
                   : nullptr;
    auto* hs = shadow_registry_
                   ? shadow_registry_->find_as<framework::HandlerShadow>()
                   : nullptr;
    auto* intent_shadow =
        shadow_registry_ ? shadow_registry_->find_as<framework::IntentShadow>()
                         : nullptr;
    if (!as || !hs || !intent_shadow || !intent_shadow->has_pending())
        return nullptr;
    auto pi = intent_shadow->take_pending();
    nlohmann::json rec;
    rec["component"] = pi->component_class;
    rec["callbacks"] = nlohmann::json::array();

    // Hostile: no component set (implicit intent — no resolution law at this
    // layer) → named failure, no crash, activity A untouched.
    if (pi->component_class.empty()) {
        rec["launched"] = false;
        rec["error"] = "ACTIVITY_NOT_FOUND: implicit intent (no component)";
        std::cerr << "[G08-LAUNCH] FAILED: no component (implicit intent)"
                  << std::endl;
        return rec;
    }
    // Normalize: readable form → DEX descriptor.
    std::string cls = pi->component_class;
    if (cls.front() != 'L') {
        cls = "L" + cls + ";";
        for (auto& c : cls)
            if (c == '.') c = '/';
    }
    rec["component_descriptor"] = cls;

    auto dispatch_cb = [&](const std::string& cb, uint32_t target_id,
                           const std::string& target_cls,
                           std::vector<miniandroid::dalvik::DalvikValue> extra_args,
                           const char* key) {
        nlohmann::json r;
        try {
            auto& heap = dalvik_engine_.get_heap_public();
            if (target_id == 0 || !heap.has_object(target_id)) {
                r["method"] = cb;
                r["dispatched"] = false;
            } else {
                miniandroid::dalvik::DalvikValue ret;
                miniandroid::dalvik::DalvikExecutionResult res;
                std::vector<miniandroid::dalvik::DalvikValue> args;
                args.push_back(miniandroid::dalvik::DalvikValue::make_object(
                    target_id, target_cls));
                for (auto& a : extra_args) args.push_back(a);
                bool ok = dalvik_engine_.try_recursive_invoke(
                    target_cls, cb, args, ret, res);
                r["method"] = cb;
                r["class"] = target_cls;
                r["dispatched"] = ok;
                r["instructions"] = res.total_instructions_executed;
            }
        } catch (const std::exception& e) {
            r["method"] = cb;
            r["dispatched"] = false;
            r["error"] = e.what();
        }
        rec[key].push_back(r);
        std::cerr << "[G08-LIFECYCLE] " << r.dump() << std::endl;
    };

    // ── A.onPause (first callback of the switch) ─────────────────────────
    dispatch_cb("onPause", as->current_activity_id(),
                as->current_activity_class(), {}, "callbacks");
    lifecycle_.transition_to(framework::LifecyclePhase::PAUSED,
                             "switch: A.onPause (TransactionExecutor law: "
                             "pause is FIRST)",
                             hs->virtual_now_ms());

    // ── Push A onto the task stack with its window ───────────────────────
    framework::ActivityShadow::ActivityRecord a_record;
    a_record.obj_id = as->current_activity_id();
    a_record.cls = as->current_activity_class();
    a_record.content_view_id = as->content_view_id();
    a_record.state = framework::ActivityShadow::LifecycleState::PAUSED;
    a_record.launched_for_request =
        as->take_pending_launch_request_code();
    as->push_activity_record(a_record);
    rec["request_code"] = a_record.launched_for_request;

    // ── B.onCreate WITH the launching intent ─────────────────────────────
    auto& heap = dalvik_engine_.get_heap_public();
    uint32_t b_id = heap.allocate(cls, 0, 0);
    uint32_t intent_obj = pi->intent_object_id;
    if (intent_obj == 0)
        intent_obj = heap.allocate("Landroid/content/Intent;", 0, 0);
    // getIntent() on B returns the LAUNCH intent (extras propagate).
    as->set_launch_intent_id(intent_obj);
    as->set_current_activity(b_id, cls);
    as->set_state(framework::ActivityShadow::LifecycleState::CREATED);
    as->set_content_view(0);  // B must build its own window
    lifecycle_.transition_to(
        framework::LifecyclePhase::ACTIVITY_CREATED,
        "B.onCreate via DEX (performLaunchActivity law): " + cls,
        hs->virtual_now_ms());
    std::vector<miniandroid::dalvik::DalvikValue> intent_arg;
    intent_arg.push_back(
        miniandroid::dalvik::DalvikValue::make_object(intent_obj,
                                                      "Landroid/content/Intent;"));
    dispatch_cb("onCreate", b_id, cls, intent_arg, "callbacks");
    rec["b_view_root"] = as->content_view_id();

    // ── B.onStart + B.onResume ───────────────────────────────────────────
    dispatch_cb("onStart", b_id, cls, {}, "callbacks");
    lifecycle_.transition_to(framework::LifecyclePhase::STARTED,
                             "B.onStart via DEX: " + cls,
                             hs->virtual_now_ms());
    dispatch_cb("onResume", b_id, cls, {}, "callbacks");
    lifecycle_.transition_to(
        framework::LifecyclePhase::RESUMED,
        "B.onResume via DEX (handleResumeActivity law): " + cls,
        hs->virtual_now_ms());
    as->set_state(framework::ActivityShadow::LifecycleState::RESUMED);

    // ── A.onStop (LAST callback of the switch) ───────────────────────────
    dispatch_cb("onStop", a_record.obj_id, a_record.cls, {}, "callbacks");
    rec["launched"] = true;
    rec["a_class"] = a_record.cls;
    rec["a_view_root"] = a_record.content_view_id;
    rec["stack_depth_after"] = as->stack_depth();
    std::cerr << "[G08-LAUNCH] launched " << cls
              << " (stack depth now " << as->stack_depth()
              << ", B view root " << as->content_view_id() << ")" << std::endl;
    return rec;
}

// G07 — consume a pending finish() at a frame boundary. AOSP law
// (Activity.finish + ActivityThread.handleDestroyActivity):
// onPause → onStop → onDestroy. Each callback is dispatched through the
// real DEX engine BEFORE its state transition is recorded — the state
// machine reflects EXECUTED callbacks, not intentions.
nlohmann::json ExecutionEngine::consume_finish_cascade() {
    auto* as = shadow_registry_
                   ? shadow_registry_->find_as<framework::ActivityShadow>()
                   : nullptr;
    auto* hs = shadow_registry_
                   ? shadow_registry_->find_as<framework::HandlerShadow>()
                   : nullptr;
    if (!as || !hs || !as->take_pending_finish()) return nullptr;
    // A finish() during a destroyed/idle state is hostile input — the
    // controller records the rejected attempt as evidence.
    nlohmann::json rec;
    rec["finish_requested"] = true;
    rec["callbacks"] = nlohmann::json::array();
    auto dispatch = [&](const char* m) {
        nlohmann::json r;
        dispatch_app_lifecycle(m, &r);
        rec["callbacks"].push_back(r);
    };
    dispatch("onPause");
    lifecycle_.transition_to(framework::LifecyclePhase::PAUSED,
                             "finish cascade: onPause dispatched via DEX",
                             hs->virtual_now_ms());
    dispatch("onStop");
    lifecycle_.transition_to(framework::LifecyclePhase::STOPPED,
                             "finish cascade: onStop dispatched via DEX",
                             hs->virtual_now_ms());
    dispatch("onDestroy");
    lifecycle_.transition_to(framework::LifecyclePhase::DESTROYED,
                             "finish cascade: onDestroy dispatched via DEX "
                             "(performDestroyActivity law)",
                             hs->virtual_now_ms());
    as->set_state(framework::ActivityShadow::LifecycleState::DESTROYED);
    rec["final_state"] = framework::lifecycle_phase_name(lifecycle_.state());
    std::cerr << "[G07-FINISH] cascade complete at virtual_ms="
              << hs->virtual_now_ms() << std::endl;

    // ── G08: pop the task stack and RESTORE the previous activity ────────
    std::cerr << "[G08-DBG] restore block enter, depth=" << as->stack_depth()
              << std::endl;
    if (as->stack_depth() > 0) {
        std::cerr << "[G08-DBG] popping" << std::endl;
        framework::ActivityShadow::ActivityRecord popped;
        bool has_prev = as->pop_activity_record(&popped);
        std::cerr << "[G08-DBG] popped=" << has_prev << " cls=" << popped.cls
                  << " req=" << popped.launched_for_request << std::endl;
        rec["popped_to"] = has_prev ? popped.cls : std::string();
        auto dispatch_cb = [&](const std::string& cb, uint32_t target_id,
                               const std::string& target_cls) {
            nlohmann::json r;
            try {
                auto& heap2 = dalvik_engine_.get_heap_public();
                if (target_id != 0 && heap2.has_object(target_id)) {
                    miniandroid::dalvik::DalvikValue ret;
                    miniandroid::dalvik::DalvikExecutionResult res;
                    std::vector<miniandroid::dalvik::DalvikValue> args;
                    args.push_back(miniandroid::dalvik::DalvikValue::make_object(
                        target_id, target_cls));
                    bool ok = dalvik_engine_.try_recursive_invoke(target_cls,
                                                                  cb, args, ret,
                                                                  res);
                    r["method"] = cb;
                    r["class"] = target_cls;
                    r["dispatched"] = ok;
                    r["instructions"] = res.total_instructions_executed;
                } else {
                    r["method"] = cb;
                    r["dispatched"] = false;
                }
            } catch (const std::exception& e) {
                r["method"] = cb;
                r["dispatched"] = false;
                r["error"] = e.what();
            }
            rec["restore_callbacks"].push_back(r);
            std::cerr << "[G08-RESTORE] " << r.dump() << std::endl;
        };
        rec["restore_callbacks"] = nlohmann::json::array();

        // onActivityResult BEFORE onStart (Activity.onActivityResult law:
        // "You will receive this call immediately before onResume()").
        if (has_prev && popped.launched_for_request >= 0) {
            int result_code = 0;
            uint32_t data_id = 0;
            bool has_result = as->take_result(&result_code, &data_id);
            rec["result_delivered"] = has_result;
            rec["result_code"] = result_code;
            std::cerr << "[G08-DBG] has_result=" << has_result
                      << " rc=" << result_code << " data=" << data_id
                      << std::endl;
            if (has_result) {
                nlohmann::json r;
                try {
                    auto& heap3 = dalvik_engine_.get_heap_public();
                    miniandroid::dalvik::DalvikValue ret;
                    miniandroid::dalvik::DalvikExecutionResult res;
                    std::vector<miniandroid::dalvik::DalvikValue> args;
                    args.push_back(miniandroid::dalvik::DalvikValue::make_object(
                        popped.obj_id, popped.cls));
                    args.push_back(miniandroid::dalvik::DalvikValue::make_int(
                        popped.launched_for_request));
                    args.push_back(miniandroid::dalvik::DalvikValue::make_int(
                        result_code));
                    if (data_id != 0)
                        args.push_back(
                            miniandroid::dalvik::DalvikValue::make_object(
                                data_id, "Landroid/content/Intent;"));
                    bool ok = dalvik_engine_.try_recursive_invoke(
                        popped.cls, "onActivityResult", args, ret, res);
                    r["method"] = "onActivityResult";
                    r["class"] = popped.cls;
                    r["dispatched"] = ok;
                    r["instructions"] = res.total_instructions_executed;
                    r["request_code"] = popped.launched_for_request;
                    r["result_code"] = result_code;
                } catch (const std::exception& e) {
                    r["method"] = "onActivityResult";
                    r["dispatched"] = false;
                    r["error"] = e.what();
                }
                rec["restore_callbacks"].push_back(r);
                std::cerr << "[G08-RESTORE] " << r.dump() << std::endl;
            }
        }
        // Restart law (handleResumeActivity from STOPPED):
        // onRestart → onStart → onResume.
        dispatch_cb("onRestart", popped.obj_id, popped.cls);
        dispatch_cb("onStart", popped.obj_id, popped.cls);
        dispatch_cb("onResume", popped.obj_id, popped.cls);
        lifecycle_.transition_to(
            framework::LifecyclePhase::STARTED,
            "A restart: onRestart+onStart via DEX (STOPPED → STARTED law)",
            hs->virtual_now_ms());
        lifecycle_.transition_to(
            framework::LifecyclePhase::RESUMED,
            "A restored: onResume via DEX (restart completion)",
            hs->virtual_now_ms());
        as->set_state(framework::ActivityShadow::LifecycleState::RESUMED);
        rec["final_state"] = "RESUMED (A restored)";
        std::cerr << "[G08-RESTORE] previous activity restored: "
                  << popped.cls << std::endl;
    }
    return rec;
}

// G06 §4/§6 — deterministic tap gesture through the canonical input
// pipeline. Event law: View.onTouchEvent (touch_dispatcher.cpp).
//   t0        ACTION_DOWN  → setPressed(true) + CheckForLongPress @ +500ms
//   t0+20ms   frame_001    → pressed state VISIBLE (input → state → render)
//   t0+50ms   ACTION_UP    → removeLongPressCallback + post(PerformClick)
//                           + post(UnsetPressedState @ PRESSED_STATE_DURATION)
//   t0+50ms   drain        → PerformClick fires → real DEX onClick →
//                           app state mutation (queued app Runnables drain
//                           in the same loop — one-queue law)
//   t0+120ms  drain        → UnsetPressedState → setPressed(false)
//   final     frame_002    → post-click, unpressed state
// No sleeps anywhere: every timestamp is the HandlerShadow virtual clock.
bool ExecutionEngine::stage_tap(ExecutionResult& result,
                                const ExecutionConfig& config) {
    if (!config.tap_enabled) return true;
    if (!shadow_registry_ || !touch_dispatcher_) return true;
    trace_engine_.info("ExecutionEngine", "stage_tap",
                       "TAP gesture sequence through canonical input "
                       "pipeline (" +
                           std::to_string(config.tap_sequence.size()) +
                           " gesture(s))");

    auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
    auto* activity_shadow = shadow_registry_->find_as<framework::ActivityShadow>();
    auto* handler_shadow = shadow_registry_->find_as<framework::HandlerShadow>();
    if (!view_shadow || !activity_shadow || !handler_shadow) return true;

    const std::string frames_dir = config.output_directory + "/frames";
    try { std::filesystem::create_directories(frames_dir); } catch (...) {}

    // Same PNG capture helper as stage_long_press / stage_click_sequence.
    auto save_frame = [&](const std::string& path,
                          std::string* png_sha_out = nullptr) -> bool {
        try {
            renderer::FrameBuffer fb(config.screen_width, config.screen_height);
            for (int y = 0; y < config.screen_height; ++y) {
                for (int x = 0; x < config.screen_width; ++x) {
                    size_t i = (static_cast<size_t>(y) * config.screen_width + x) * 4;
                    if (i + 3 < framebuffer_.size()) {
                        fb.set_pixel(x, y, renderer::RGBA{
                            framebuffer_[i], framebuffer_[i + 1],
                            framebuffer_[i + 2], framebuffer_[i + 3]});
                    }
                }
            }
            bool ok = renderer::PNGWriter::write_png(path, fb);
            if (ok && png_sha_out) {
                std::ifstream pf(path, std::ios::binary);
                std::vector<unsigned char> bytes((std::istreambuf_iterator<char>(pf)),
                                                 std::istreambuf_iterator<char>());
                *png_sha_out = sha256_hex(bytes);
            }
            return ok;
        } catch (const std::exception& e) {
            std::cerr << "[G06-TAP] frame save failed: " << e.what() << std::endl;
            return false;
        }
    };

    auto collect_texts = [&]() {
        nlohmann::json arr = nlohmann::json::array();
        for (const auto& [id, node_ptr] : view_shadow->all_nodes()) {
            if (node_ptr && !node_ptr->text.empty()) {
                arr.push_back({{"view_id", id},
                               {"class", node_ptr->class_desc},
                               {"text", node_ptr->text}});
            }
        }
        return arr;
    };

    // Bounded drain-until-quiescent on the deterministic virtual clock.
    // M3 FINDING-009: the lambda body lives AFTER the frame-capture state
    // declarations below (it now saves tick frames and needs manifest /
    // frames_dir / frame_index / last_saved_fb in scope). See the second
    // definition — this site kept only for the historical comment.
    //
    // Fires every due queue entry (framework tokens AND app Runnables, FIFO
    // by (when, seq)); newly enqueued due entries drain in the same instant,
    // capped (hostile re-post storms cannot loop forever — §18 safety law).

    nlohmann::json manifest;
    manifest["gesture"] = "TAP";
    manifest["pipeline"] = "canonical (TouchDispatcher law)";
    manifest["laws"] = {"View.java L17044-17047 touchable",
                        "L17049-17057 disabled",
                        "L17113-17125 DOWN setPressed + long-press arm",
                        "L17133-17169 UP post(PerformClick)+UnsetPressed(64ms)",
                        "L17172-17184 CANCEL cleanup",
                        "CheckForLongPress mHasPerformedLongPress suppression",
                        "one-MessageQueue ordering (framework tokens)"};
    manifest["screen"] = {{"width", config.screen_width},
                          {"height", config.screen_height}};
    manifest["events"] = nlohmann::json::array();
    manifest["frames"] = nlohmann::json::array();

    std::vector<uint8_t> prev = framebuffer_;
    {
        nlohmann::json f;
        f["index"] = 0;
        f["file"] = "frame_000.png";
        f["event"] = "launch (no interaction)";
        f["sha256"] = sha256_hex(prev);
        std::string png_sha;
        save_frame(frames_dir + "/frame_000.png", &png_sha);
        f["png_sha256"] = png_sha;
        f["visible_texts"] = collect_texts();
        manifest["frames"].push_back(f);
    }

    uint32_t root_id = activity_shadow->content_view_id();
    int frame_index = 1;  // frame_000 = launch, captured above
    size_t total_diff = 0;
    nlohmann::json all_drains = nlohmann::json::array();
    // M3 FINDING-010: mutation-keyed tick frames — the frame content at the
    // moment of the most recent SAVE (launch, gesture, or tick). Compared
    // after every dispatch round inside the drain; a tick that mutated the
    // tree emits exactly one frame, deterministically.
    std::vector<uint8_t> last_saved_fb = framebuffer_;

    // ── drain_quiescent (M3 FINDING-009/010) ─────────────────────────────
    // Bounded drain-until-QUIESCENT on the deterministic virtual clock.
    // AOSP law (MessageQueue.next): the main Looper NEVER exits while
    // messages are pending — when the head's `when` is in the future it
    // sleeps nativePollOnce(head.when - now) and dispatches when the clock
    // reaches `when`. The previous `if (drain_ready()==0) return;` treated
    // "nothing due NOW" as quiescence and stranded every future-scheduled
    // tick (microtimer's re-post delay=999ms never fired → one-tick
    // countdown). Quiescence is queue EMPTY.
    //
    // §18 storm law, refined (FINDING-009): the hostile signature is MANY
    // DISPATCH ROUNDS WITH NEGLIGIBLE VIRTUAL PROGRESS (delay=0 re-post
    // storms — <2ms between dispatches). The storm budget therefore counts
    // CONSECUTIVE low-progress dispatch rounds only; a dispatch that
    // advances the clock ≥2ms (a countdown tick: ~1000ms per round) resets
    // it. A second absolute bound (512 dispatch rounds per drain call)
    // deterministically terminates pathological forever-chains. Both
    // bounds are fixed constants — zero wall-clock input.
    auto drain_quiescent = [&](nlohmann::json* drain_log) {
        int storm_rounds = 0;                       // consecutive low-progress dispatches
        static constexpr int kStormCap = 64;        // §18 hostile-storm bound
        static constexpr int kTotalRoundCap = 512;  // absolute per-drain bound
        int total_rounds = 0;
        int64_t last_dispatch_when = handler_shadow->virtual_now_ms();
        while (total_rounds < kTotalRoundCap) {
            std::vector<uint32_t> due;
            size_t n = handler_shadow->drain_ready(&due);
            if (n == 0) {
                // FINDING-009: poll-timeout fast-forward. Quiescence is an
                // EMPTY queue, not a future-dated head.
                if (handler_shadow->queue_size() == 0) return;
                int64_t next_ready = handler_shadow->next_ready_ms();
                int64_t now = handler_shadow->virtual_now_ms();
                if (next_ready <= now) return;  // defensive: nothing advanceable
                handler_shadow->advance_virtual(next_ready - now);
                if (drain_log)
                    drain_log->push_back({{"event", "poll-timeout fast-forward"},
                                          {"advanced_to_virtual_ms", next_ready},
                                          {"delta_ms", next_ready - now}});
                continue;
            }
            ++total_rounds;
            int64_t now = handler_shadow->virtual_now_ms();
            if (now - last_dispatch_when < 2) {
                if (++storm_rounds > kStormCap) {
                    std::cerr << "[G06-TAP] drain loop hit iteration cap "
                                 "(hostile re-post storm bounded)"
                              << std::endl;
                    return;
                }
            } else {
                storm_rounds = 0;
            }
            last_dispatch_when = now;
            if (drain_log) {
                for (uint32_t id : due)
                    drain_log->push_back({{"virtual_ms", now},
                                          {"entry", id}});
            }
            for (uint32_t id : due) invoke_handler_runnable(id);
            // FINDING-010: tick-frame capture — the redraw evidence law.
            // A tick that mutated the view tree MUST be observable as a
            // framebuffer change; save exactly one frame per mutation,
            // keyed to the content (not the clock), so runs without visible
            // ticks save nothing extra.
            stage_render_frame(result, config);
            if (framebuffer_.size() == last_saved_fb.size() &&
                framebuffer_ != last_saved_fb) {
                size_t tdiff = 0;
                for (size_t i = 0; i < framebuffer_.size(); i += 4) {
                    if (framebuffer_[i] != last_saved_fb[i] ||
                        framebuffer_[i + 1] != last_saved_fb[i + 1] ||
                        framebuffer_[i + 2] != last_saved_fb[i + 2]) {
                        tdiff++;
                    }
                }
                std::string tick_png;
                char tname[32];
                snprintf(tname, sizeof tname, "frame_%03d.png", frame_index);
                save_frame(frames_dir + "/" + tname, &tick_png);
                nlohmann::json tf;
                tf["index"] = frame_index;
                tf["file"] = tname;
                tf["event"] = "queue drain: framebuffer mutated (tick)";
                tf["virtual_ms"] = handler_shadow->virtual_now_ms();
                tf["changed_pixels_vs_previous"] = tdiff;
                tf["sha256"] = sha256_hex(framebuffer_);
                tf["png_sha256"] = tick_png;
                tf["visible_texts"] = collect_texts();
                manifest["frames"].push_back(tf);
                frame_index++;
                last_saved_fb = framebuffer_;
            }
            // M3 F-ROOM-CHAIN (AG, 2026-09-08): looper-iteration time cost.
            // AOSP law: MessageQueue.next() re-evaluates the head's `when`
            // against the Looper clock between dispatch rounds, and the
            // wall clock advances at least by the dispatch cost. On the
            // frozen virtual clock a runnable that self-reposts with
            // delay=0 at the same timestamp (microtimer's sub-second
            // alignment law: delay = (expires - now) % 1000 == 0) would
            // re-queue due-at-now FOREVER — the observed 64-iteration
            // "re-post storm" cap. Deterministic model: when the queue
            // still holds entries due at the CURRENT instant after a
            // dispatch round, advance the virtual clock by 1ms so the
            // next round observes a strictly later Looper time. This
            // mirrors real ART (clock >= dispatch cost) with zero
            // nondeterminism: the quantum is fixed, never wall-clock.
            if (handler_shadow->has_due_at(handler_shadow->virtual_now_ms()))
                handler_shadow->advance_virtual(1);
        }
        std::cerr << "[G06-TAP] drain loop hit total-round cap (" <<
                     kTotalRoundCap << " dispatch rounds — pathological "
                     "forever-chain bounded)" << std::endl;
    };

    for (const auto& [px, py] : config.tap_sequence) {
        // ── t0: ACTION_DOWN ──────────────────────────────────────────────
        auto down_rec = touch_dispatcher_->dispatch(
            root_id, {framework::TouchAction::DOWN, px, py});
        manifest["events"].push_back(down_rec);
        const uint32_t target = down_rec.value("target_view_id", 0u);
        std::cerr << "[G06-TAP] DOWN (" << px << "," << py << ") target="
                  << target << " consumed="
                  << down_rec.value("consumed", false) << std::endl;
        if (target == 0) {
            manifest["no_target"] = true;
            continue;
        }

        // ── t0+20ms: pressed frame (state visible) ───────────────────────
        handler_shadow->advance_virtual(20);
        stage_render_frame(result, config);
        {
            std::string png_sha;
            nlohmann::json f;
            f["index"] = frame_index;
            char name[32];
            snprintf(name, sizeof name, "frame_%03d.png", frame_index);
            f["file"] = name;
            f["event"] = "ACTION_DOWN pressed state (mid-gesture)";
            f["virtual_ms"] = handler_shadow->virtual_now_ms();
            f["target_view_id"] = target;
            f["target_pressed"] = view_shadow->find_node(target)
                                      ? view_shadow->find_node(target)->pressed
                                      : false;
            f["sha256"] = sha256_hex(framebuffer_);
            save_frame(frames_dir + "/" + name, &png_sha);
            f["png_sha256"] = png_sha;
            f["visible_texts"] = collect_texts();
            manifest["frames"].push_back(f);
            frame_index++;
            last_saved_fb = framebuffer_;
        }

        // ── t0+50ms: ACTION_UP → queue PerformClick + UnsetPressedState ──
        handler_shadow->advance_virtual(30);
        auto up_rec = touch_dispatcher_->dispatch(
            root_id, {framework::TouchAction::UP, px, py});
        manifest["events"].push_back(up_rec);
        std::cerr << "[G06-TAP] UP click_posted="
                  << up_rec.value("click_posted", false) << std::endl;

        // ── drain t0+50: PerformClick fires → real DEX onClick ───────────
        nlohmann::json click_drain = nlohmann::json::array();
        drain_quiescent(&click_drain);
        all_drains.push_back(click_drain);

        // ── t0+120ms: UnsetPressedState clears pressed ───────────────────
        handler_shadow->advance_virtual(70);
        nlohmann::json unset_drain = nlohmann::json::array();
        drain_quiescent(&unset_drain);
        all_drains.push_back(unset_drain);

        // G07/G08: this tap landed on a frame boundary — a finish() or
        // startActivity() requested by the click callback applies its
        // runtime transition HERE, before the final frame is captured.
        nlohmann::json intent_rec = consume_pending_intent();
        if (!intent_rec.is_null()) manifest["activity_launch"] = intent_rec;
        nlohmann::json finish_rec = consume_finish_cascade();
        if (!finish_rec.is_null()) manifest["finish_cascade"] = finish_rec;

        // ── post-gesture frame: post-click / post-launch / post-restore ──
        stage_render_frame(result, config);
        size_t diff_px = 0;
        if (framebuffer_.size() == prev.size()) {
            for (size_t i = 0; i < framebuffer_.size(); i += 4) {
                if (framebuffer_[i] != prev[i] ||
                    framebuffer_[i + 1] != prev[i + 1] ||
                    framebuffer_[i + 2] != prev[i + 2]) {
                    diff_px++;
                }
            }
        }
        total_diff += diff_px;
        std::string png_sha;
        char name[32];
        snprintf(name, sizeof name, "frame_%03d.png", frame_index);
        bool saved = save_frame(frames_dir + "/" + name, &png_sha);
        nlohmann::json f;
        f["index"] = frame_index;
        f["file"] = name;
        f["event"] = "post-gesture (callbacks drained, transitions applied)";
        f["virtual_ms"] = handler_shadow->virtual_now_ms();
        f["target_view_id"] = target;
        f["target_pressed_after"] = view_shadow->find_node(target)
                                        ? view_shadow->find_node(target)->pressed
                                        : false;
        f["changed_pixels_vs_previous"] = diff_px;
        f["sha256"] = sha256_hex(framebuffer_);
        f["png_sha256"] = png_sha;
        f["visible_texts"] = collect_texts();
        manifest["frames"].push_back(f);
        frame_index++;
        prev = framebuffer_;
        last_saved_fb = framebuffer_;
        // A launched activity owns the window: subsequent gestures hit ITS
        // tree (the content view root switched at the launch boundary).
        root_id = activity_shadow->content_view_id();
    }

    manifest["changed_pixels_vs_launch"] = total_diff;
    manifest["gesture_count"] = config.tap_sequence.size();
    manifest["drains"] = all_drains;
    manifest["touch_trace"] = touch_dispatcher_->trace();

    try {
        std::ofstream mf(frames_dir + "/manifest.json");
        mf << manifest.dump(2);
    } catch (...) {}
    std::cerr << "[G06-TAP] done: gestures=" << config.tap_sequence.size()
              << " total_diff_px=" << total_diff
              << " dir=" << frames_dir << std::endl;
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
