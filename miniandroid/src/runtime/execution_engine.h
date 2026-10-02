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
#include "renderer/software_renderer.h"  // S95: VectorRefResolver for image_ref_resolver()
// EXP-086 Phase 7 (B4 FIX): ShadowRegistry for Handler/Looper dispatch
#include "framework/shadow_registry.h"
// EXP-087 Phase 3 (B2 FIX): DalvikHeapAdapter for shadow heap access
#include "framework/heap_adapter.h"
// G06 §4: canonical input pipeline (TouchDispatcher) + StateListDrawable law
#include "framework/touch_dispatcher.h"
#include "framework/state_list.h"
#include "framework/lifecycle_controller.h"

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
    // FIX-3: density (px per dp) for default text sizing — must mirror the
    // DeviceMetrics the LayoutInflater measures with (420dpi bucket default).
    float density = 2.625f;
    
    // Tracing settings
    bool verbose_logging = false;
    bool generate_screenshot = true;
    // S67 FOUNDATION (§1 evidence pipeline): dump the live ViewShadow tree to
    // <output>/view_tree.json after the final capture. This is the canonical
    // view→pixel provenance artifact (x/y/w/h/class/text/visibility per node)
    // and was previously only reachable through the legacy EXP-061 flow.
    bool dump_view_tree = false;
    // S69 SOURCE-LINKED CAMPAIGN (§2B API graph / §13 API coverage matrix):
    // dump the engine's ApiCallTrace ring (every invoke bridged to the
    // framework during the main DEX execution — class, method, descriptor,
    // status IMPLEMENTED/STUBBED/MISSING/ERROR) to <output>/api_calls.json.
    // This is the LIVE dispatch surface — ground truth that pairs with the
    // static served-API extraction in tools/architecture/.
    bool dump_api_trace = false;
    // UNIFIED_011.2 CLICK-TEST (§10/§11): generic touch probe. After the first
    // frame is captured, dispatch a real click on every view with a registered
    // listener, re-render, and record which clicks change pixels (L9→L12:
    // touch accepted → callback executed → state changed → second frame).
    bool click_test = false;
    // S60 (R-NEW-380): wall-clock soft budget for the DEX dispatch (seconds;
    // 0 = disabled). Graceful stop identical to the instruction budget —
    // the end-of-run evidence pipeline (screenshot/trace/report) still runs.
    uint64_t max_wall_seconds = 0;

    // F-107b2 (S61): per-instruction trace caps. Mirrors the dalvik Config
    // fields; mapped in stage_execute_application_real_dalvik. trace_cap=0
    // (default) disables the per-instruction trace machinery (forensic
    // artifact, not primary evidence) — opt in via MINIANDROID_TRACE_CAP.
    size_t trace_cap = 0;
    size_t api_call_trace_cap = 5000;
    // DEMO-CLICK-SEQUENCE (2026-09-04): deterministic multi-interaction capture.
    // When > 0, dispatch this many sequential clicks (round-robin over all
    // clickable views), re-render through the SAME pipeline after each click,
    // and save every frame as frames/frame_<NNN>.png plus a frames/manifest.json
    // recording the click target, pixel diff vs the previous frame, framebuffer
    // SHA256, and the app's own visible state text (ViewShadow node texts).
    // This is the runtime mechanism behind the real-APK execution proof: the
    // state transitions in the evidence GIF come from the app's own DEX logic
    // reacting to dispatched clicks, not from any host-side animation.
    int click_count = 0;
    // TIME-DRIVEN FRAME CAPTURE (2026-09-04): when > 0, run a virtual-clock
    // frame loop: advance the Handler/Looper virtual clock by frame_delay_ms
    // per frame, drain the Handler queue (firing every Runnable whose
    // postDelayed time has arrived — including self-reposting animation
    // tickers), re-render through the SAME pipeline, and save one PNG per
    // step into frames/ plus manifest.json entries. The state transitions
    // come from the APK's own DEX logic reacting to Looper time — no clicks,
    // no host-side animation. Mutually exclusive with click_count.
    int frame_count = 0;
    int frame_delay_ms = 300;
    // GOLDEN-02: coordinate-anchored long-press gesture (AOSP View touch law).
    // After the launch frame: hit_test(x,y) → target view → DOWN →
    // ViewConfiguration.getLongPressTimeout() (500ms) → CheckForLongPress →
    // performLongClick → dispatch_long_click. The listener's boolean return
    // is the AOSP "handled" value: true → mHasPerformedLongPress → the UP
    // click is SUPPRESSED; false (or no listener) → UP performs a click.
    // The post-interaction frame is captured with the same pipeline as
    // click-sequence frames (frames/longpress manifest + PNG + SHA-256).
    bool long_press_enabled = false;
    int long_press_x = 0;
    int long_press_y = 0;
    // G06 §4/§6: canonical tap gesture through the TouchDispatcher law
    // pipeline. DOWN at t0 (pressed frame captured), UP at t0+50ms virtual,
    // queued PerformClick + UnsetPressedState drained before the final frame.
    // G08: REPEATABLE — each --tap appends to the sequence, enabling
    // A→B→back navigation proofs in one deterministic run.
    bool tap_enabled = false;
    std::vector<std::pair<int, int>> tap_sequence;
    // S73 F-117 extension: per-tap fire frame for `--tap x,y@frame` (real
    // user input cadence: fingers tap at Looper times BETWEEN frames).
    // EMPTY = legacy law exactly (tap k fires at frame k). When non-empty,
    // size MUST equal tap_sequence.size() (all-or-none, enforced in main).
    std::vector<int> tap_at_frames;
    // S129 (R-NEW-425/426): generic swipe/drag gesture — canonical AOSP
    // cadence DOWN → N MOVEs (16ms virtual apart — 60Hz, linear interpolation) →
    // UP, all through the TouchDispatcher law pipeline. Drives the MOVE
    // delivery law (VelocityTracker.addMovement / GestureDetector.onScroll
    // streams) and scroll containers. `--swipe x1,y1,x2,y2[@frame]`;
    // fires ONCE at frame == swipe_at_frame (default 2).
    bool swipe_enabled = false;
    int swipe_x1 = 0, swipe_y1 = 0, swipe_x2 = 0, swipe_y2 = 0;
    int swipe_at_frame = 2;
    int swipe_steps = 12;
    bool generate_reports = true;
    
    // EXP-031: Execution mode (CRITICAL - determines real vs fake path)
    ExecutionMode execution_mode = ExecutionMode::REAL_DALVIK;  // Default to REAL!
    
    // Legacy simulation settings (only used in LEGACY mode)
    bool simulate_lifecycle = true;
    std::string simulated_text = "";  // Empty = try to extract from APK

    // M3 FINDING-012: per-invocation app-data root (Android's
    // /data/data/<pkg> analog). Empty = keep the process default
    // ("runtime/data", CWD-relative, back-compat) or the
    // MINIANDROID_DATA_ROOT env override. Drivers that need hermetic or
    // stateful-replay control (determinism gates, persistence goldens,
    // battery corpus runs) MUST set this explicitly per run.
    std::string data_root = "";
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

    // S95 L-S95-ADAPTIVE-1: app-resource resolver handed to the renderer's
    // vector/adaptive-icon decoder. The renderer has no ResTable; the engine
    // resolves references through the ARSC (colors) and the APK zip
    // (drawable/mipmap files at the canonical density selection).
    renderer::VectorRefResolver image_ref_resolver();

private:
    // Pipeline stages
    bool stage_load_apk(const std::string& path, ExecutionResult& result);
    bool stage_parse_dex(ExecutionResult& result);
    bool stage_initialize_runtime(ExecutionResult& result, const ExecutionConfig& config);
    bool stage_load_classes(ExecutionResult& result);
    bool stage_execute_application(ExecutionResult& result, const ExecutionConfig& config);
    bool stage_render_frame(ExecutionResult& result, const ExecutionConfig& config);
    // F-NEW-198: final_pass=true skips the R-NEW-340 compose pump (the
    // end-of-window re-capture must not advance app state; it records it).
    bool stage_capture_output(ExecutionResult& result, const ExecutionConfig& config,
                              bool final_pass = false);
    // UNIFIED_011.2 CLICK-TEST: generic post-first-frame interaction probe.
    bool stage_click_test(ExecutionResult& result, const ExecutionConfig& config);
    bool stage_click_sequence(ExecutionResult& result, const ExecutionConfig& config);
    bool stage_frame_sequence(ExecutionResult& result, const ExecutionConfig& config);
    bool stage_long_press(ExecutionResult& result, const ExecutionConfig& config);
    // G06 §4/§6: deterministic tap gesture through the canonical input
    // pipeline (DOWN → pressed frame → UP → queued PerformClick →
    // UnsetPressedState → drained frame). Frames + touch trace manifest.
    bool stage_tap(ExecutionResult& result, const ExecutionConfig& config);
    void invoke_handler_runnable(uint32_t runnable_id);
    // F-050: Choreographer frame pump — invoke a posted FrameCallback's
    // REAL DEX doFrame(J)V at the deterministic virtual frame time (the
    // vsync law that resumes Compose withFrameNanos continuations).
    void invoke_choreographer_do_frame(uint32_t callback_id,
                                       const std::string& callback_class,
                                       int64_t frame_time_nanos);
    // F-050: bounded launch-frame pump — fire pending frame callbacks,
    // drain the resumption work they post (one MessageQueue law), repeat
    // until quiescent or the deterministic bound. Returns frames fired.
    int pump_compose_frames(int max_frames);
    // G07 §7: lifecycle state machine + real-DEX lifecycle dispatch.
    bool dispatch_app_lifecycle(const std::string& method,
                                nlohmann::json* record);
    // Consumes a pending finish() at a frame boundary: onPause → onStop →
    // onDestroy through real DEX (AOSP ActivityThread cascade). Returns a
    // JSON record (null when nothing pending).
    nlohmann::json consume_finish_cascade();
    // G08: consumes a pending startActivity() at a frame boundary —
    // A.onPause → B.onCreate(intent) → B.onStart → B.onResume → A.onStop
    // (TransactionExecutor law) with REAL DEX on both activities.
    nlohmann::json consume_pending_intent();
    // S83-GFX-BASE §25: GLSurfaceView frame pass — after the view-tree
    // render, every GLSurfaceView node with a renderer runs its REAL
    // renderer callbacks (onSurfaceCreated/Changed/DrawFrame via DEX) into
    // the PortableGL software context, and the PGL frame is presented
    // (blitted) into the window framebuffer region of that view.
    bool stage_gl_surfaces(ExecutionResult& result, const ExecutionConfig& config);
    // S83-GFX-BASE: original render body (stage_render_frame wraps it with
    // the GL surface pass so every frame path composites GL surfaces).
    bool stage_render_frame_impl(ExecutionResult& result, const ExecutionConfig& config);

    // R-NEW-440b (S132): ONE render/input root law. AOSP ViewRootImpl
    // renders and hit-tests the hierarchy under android.R.id.content.
    // ActivityShadow.content_view_id() is unset (0) when the appcompat
    // delegate installs content via Window.setContentView + content.addView
    // (R005-DECOR + S83-CONTENT path) — the S83 content-parent node
    // (android_view_id == 0x01020002) is then the root for the draw walk
    // AND the touch dispatcher (same law, same root).
    uint32_t effective_content_root_() const;

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
    // EXP-087 Phase 3 (B2 FIX): Heap adapter for shadow heap access
    std::unique_ptr<framework::DalvikHeapAdapter> heap_adapter_;
    // G06 §4: canonical input dispatcher (owns the gesture state machine;
    // framework callbacks ride the SAME HandlerShadow queue as app
    // Runnables via kFrameworkTokenBase tokens).
    std::unique_ptr<framework::TouchDispatcher> touch_dispatcher_;
    // G06 §5: per-view state-list parse cache (parse-once, pick-per-frame).
    // value.first = is a selector; value.second = parsed items.
    std::map<uint32_t,
             std::pair<bool, std::vector<framework::ViewShadow::ViewNode::BgStateItem>>>
        state_list_cache_;
    // G07 §7/§10: runtime lifecycle state machine (real transitions only).
    framework::LifecycleController lifecycle_;
    
    // State
    std::vector<uint8_t> framebuffer_;
    std::string last_error_;

public:
    // ═══════════════════════════════════════════════════════════════════
    // FINAL CAMPAIGN item 21 (P0-2/3/5/6/7): FRAME-TRUTH CENSUS.
    // One per-frame ledger of WHAT the authoritative render actually did.
    // Filled by stage_render_frame, consumed by stage_capture_output's
    // pixel-ownership verdict + trace_summary. No verdict may claim
    // REAL_APP_CONTENT without the correlated proof this ledger carries.
    // ═══════════════════════════════════════════════════════════════════
    struct FrameRenderCensus {
        bool auth_root_valid = false;        // P0-6: authoritative root resolved + node found
        bool measure_ran = false;            // P0-6: a measure pass ran
        bool layout_ran = false;             // P0-6: a layout pass ran
        bool draw_walk_ran = false;          // P0-6: >= 1 node visited by the draw walk
        uint64_t app_draw_ops = 0;           // P0-6: real app-owned canvas ops (bg/onDraw/text/images)
        bool dialog_content_rendered = false;// P0-6: a showing dialog painted app content
        bool synthetic_suppressed = false;   // P0-3: synthetic api::View path refused in REAL_DALVIK
        bool render_exception = false;       // P0-3: real draw walk threw; framebuffer discarded
        bool no_root = false;                // P0-2: zero authoritative window content reachable
        bool budget_exhausted = false;       // P0-7: node/depth budget hit — frame is PARTIAL
        int  nodes_visited = 0;              // P0-7 census
        int  nodes_skipped_depth = 0;        // P0-7 census
        int  depth_max = 0;                  // P0-7 census
        uint64_t unreachable_children = 0;   // P0-7: queue entries stranded by the node budget
        std::string layout_source;           // P1-2 census: "inflater" | "programmatic"
        // ── SECONDARY CAMPAIGN V1/V2 (authoritative verdict hardening) ──
        // V2: a real APK's setContentView(res) that produced NO root is
        // RESOURCE_INFLATION_FAILED — never a silent synthetic default
        // screen. Set from the ActivityShadow inflate outcome each frame.
        bool inflation_failed = false;
        // V1/V7: the laid-out rect of the AUTHORITATIVE content root.
        // Verdict law: REAL_APP_CONTENT requires app-owned pixels INSIDE
        // these bounds; non-dominant pixels OUTSIDE them are window chrome
        // (status bar / nav / decor bands) and can never masquerade as app
        // content. Invalid when no root resolved.
        bool content_bounds_valid = false;
        int  content_l = 0, content_t = 0, content_r = 0, content_b = 0;
        // P0-5: diagnostic regions recorded, NEVER painted into the
        // authoritative frame (l,t,r,b in screen coordinates).
        struct DiagRegion { int l, t, r, b; std::string kind; std::string detail; };
        std::vector<DiagRegion> diag_regions;
        // F-NEW-232 LAUNCH-FRAME DEFERRED-UI OBSERVABILITY: a plain run
        // freezes at the launch frame (F-NEW-197/F-115b law — an idle Looper
        // cannot observe its own future). When the pump quiesces while the
        // MessageQueue still holds FUTURE-due entries (Timer.schedule /
        // postDelayed), this frame is a PROVISIONAL launch face — downstream
        // verdicts (and humans) must not read a blank/flat face here as the
        // app's settled state without a time-driven (--frames) cross-check.
        bool deferred_ui_pending = false;
        int  deferred_queue_size = 0;
        long long deferred_earliest_ready_ms = 0;
        // F-NEW-233: the final frame verdict + earliest missing proof stage,
        // persisted on the census so the post-final-status message law can
        // annotate the run message (the capture-side message gets wiped by
        // the final-status overwrite).
        std::string verdict;
        std::string first_missing_stage;
        void reset() { *this = FrameRenderCensus{}; }
        bool app_content_proof() const {
            return auth_root_valid && draw_walk_ran && app_draw_ops > 0;
        }
    };
    FrameRenderCensus frame_census_;
    // P0-6: pre-walk framebuffer snapshot — pixels identical to this baseline
    // after the walk were NOT produced by this draw pass (system chrome /
    // pipeline fills) and can never masquerade as app content.
    std::vector<uint8_t> frame_baseline_;
};

} // namespace runtime
} // namespace miniandroid

#endif // MINIANDROID_EXECUTION_ENGINE_H
