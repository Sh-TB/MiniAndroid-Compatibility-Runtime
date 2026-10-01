/*
 * MiniAndroid Runtime v0.1 - Trace Engine Implementation
 * EXP-001: HelloWorld Loader
 */

#include "trace_engine.h"
#include <filesystem>
#include <algorithm>
#include <cstdlib>
#include <unistd.h>
#include <iostream>

namespace miniandroid {
namespace diagnostics {

// Forward declaration for helper function
std::string format_bytes(size_t bytes);

using json = nlohmann::json;
namespace fs = std::filesystem;

TraceEngine::TraceEngine() : session_active_(false) {
}

TraceEngine::~TraceEngine() {
    if (session_active_) {
        end_session();
    }
}

void TraceEngine::start_session(const std::string& session_id) {
    clear();
    
    if (session_id.empty()) {
        session_id_ = generate_session_id();
    } else {
        session_id_ = session_id;
    }
    
    session_active_ = true;
    metrics_.start_time_ms = get_timestamp_ms();
    
    info("TraceEngine", "start_session", "Session started: " + session_id_);
}

void TraceEngine::end_session() {
    if (session_active_) {
        metrics_.end_time_ms = get_timestamp_ms();
        metrics_.duration_ms = metrics_.end_time_ms - metrics_.start_time_ms;
        
        info("TraceEngine", "end_session", "Session ended. Duration: " + 
             std::to_string(metrics_.duration_ms) + "ms");
        
        session_active_ = false;
    }
}

void TraceEngine::trace(const std::string& category, LogLevel level,
                         const std::string& source_class, const std::string& method,
                         const std::string& message,
                         const std::vector<std::string>& args) {
    if (!session_active_) return;
    
    TraceEntry entry;
    entry.timestamp_ms = get_timestamp_ms();
    entry.category = category;
    entry.level = level;
    entry.source_class = source_class;
    entry.source_method = method;
    entry.message = message;
    entry.args = args;
    
    traces_.push_back(entry);
    
    // Update metrics
    if (category == "API") {
        metrics_.api_calls_count++;
    }
    
    switch (level) {
        case LogLevel::WARNING:
            metrics_.warnings_count++;
            break;
        case LogLevel::ERROR:
        case LogLevel::FATAL:
            metrics_.errors_count++;
            break;
        default:
            break;
    }
}

void TraceEngine::debug(const std::string& cls, const std::string& method, const std::string& msg) {
    trace("DEBUG", LogLevel::DEBUG, cls, method, msg);
}

void TraceEngine::info(const std::string& cls, const std::string& method, const std::string& msg) {
    trace("SYSTEM", LogLevel::INFO, cls, method, msg);
}

void TraceEngine::warning(const std::string& cls, const std::string& method, const std::string& msg) {
    trace("SYSTEM", LogLevel::WARNING, cls, method, msg);
}

void TraceEngine::error(const std::string& cls, const std::string& method, const std::string& msg) {
    trace("SYSTEM", LogLevel::ERROR, cls, method, msg);
}

void TraceEngine::fatal(const std::string& cls, const std::string& method, const std::string& msg) {
    trace("SYSTEM", LogLevel::FATAL, cls, method, msg);
}

void TraceEngine::record_error(const std::string& type, const std::string& message,
                                const std::string& context_class,
                                const std::string& context_method,
                                bool is_fatal) {
    ErrorRecord err;
    err.timestamp_ms = get_timestamp_ms();
    err.error_type = type;
    err.error_message = message;
    err.context_class = context_class;
    err.context_method = context_method;
    err.is_fatal = is_fatal;
    
    errors_.push_back(err);
    
    // Also log as trace
    LogLevel level = is_fatal ? LogLevel::FATAL : LogLevel::ERROR;
    trace("ERROR", level, context_class.empty() ? "Unknown" : context_class,
          context_method.empty() ? "Unknown" : context_method,
          "[" + type + "] " + message);

    // S135: every recorded error is ALSO a canonical runtime event — one
    // backbone, zero duplicate wiring. UNIMPLEMENTED* types surface as
    // MISSING_API (S135 §16); everything else as EXCEPTION (§17 VM lane).
    RuntimeEvent e;
    e.event = (type.rfind("UNIMPLEMENTED", 0) == 0) ? ev::MISSING_API
                                                    : ev::EXCEPTION;
    e.component = (e.event == ev::MISSING_API) ? "api" : "vm";
    e.sev = EventSev::FAILURE;
    e.cls = context_class;
    e.method = context_method;
    e.exception = "[" + type + "] " + message;
    e.result = "FAIL";
    e.state = is_fatal ? "fatal" : "nonfatal";
    runtime_event(std::move(e));
}

void TraceEngine::log_screenshot(const std::string& path, int width, int height, size_t size) {
    ScreenshotRecord ss;
    ss.file_path = path;
    ss.width = width;
    ss.height = height;
    ss.file_size_bytes = size;
    ss.timestamp_ms = get_timestamp_ms();
    
    screenshots_.push_back(ss);
    
    info("TraceEngine", "log_screenshot", 
         "Screenshot captured: " + path + " (" + std::to_string(width) + "x" + 
         std::to_string(height) + ", " + std::to_string(size) + " bytes)");

    // S135: authoritative-frame capture is a canonical FRAME_CAPTURE event.
    RuntimeEvent e = make_event(ev::FRAME_CAPTURE, EventSev::CONFIRMED,
                                "capture",
                                std::to_string(width) + "x" + std::to_string(height),
                                "OK");
    e.extra = {{"path", path}, {"bytes", size}};
    runtime_event(std::move(e));
}

json TraceEngine::generate_api_trace_json() const {
    json root;
    
    root["session_id"] = session_id_;
    root["generated_at"] = format_timestamp(get_timestamp_ms());
    root["total_calls"] = traces_.size();
    
    json calls = json::array();
    for (const auto& trace : traces_) {
        calls.push_back(trace.to_json());
    }
    root["calls"] = calls;
    
    return root;
}

std::string TraceEngine::generate_crash_log() const {
    std::ostringstream oss;
    
    oss << "MiniAndroid Crash/Error Log\n";
    oss << "============================\n\n";
    oss << "Session: " << session_id_ << "\n";
    oss << "Generated: " << format_timestamp(get_timestamp_ms()) << "\n";
    oss << "Total Errors: " << errors_.size() << "\n\n";
    
    if (errors_.empty()) {
        oss << "[No errors recorded]\n";
    } else {
        for (size_t i = 0; i < errors_.size(); i++) {
            const auto& err = errors_[i];
            
            oss << "--- Error #" << (i + 1) << " ---\n";
            oss << "Type: " << err.error_type << "\n";
            oss << "Message: " << err.error_message << "\n";
            oss << "Context: " << err.context_class << "." << err.context_method << "\n";
            oss << "Fatal: " << (err.is_fatal ? "YES" : "NO") << "\n";
            oss << "Timestamp: " << format_timestamp(err.timestamp_ms) << "\n\n";
        }
    }
    
    return oss.str();
}

std::string TraceEngine::generate_markdown_report(const std::string& app_name,
                                                   const std::string& status,
                                                   const std::string& apk_path) const {
    std::ostringstream oss;
    
    oss << "# MiniAndroid Execution Report\n\n";
    
    // Header section
    oss << "## Application\n\n";
    oss << "- **APK:** `" << apk_path << "`\n";
    oss << "- **Package:** `" << app_name << "`\n";
    oss << "- **Status:** ";
    if (status == "SUCCESS") {
        oss << "**SUCCESS** ✅\n";
    } else {
        oss << "**FAILURE** ❌\n";
    }
    oss << "\n";
    
    // Metrics
    oss << "## Metrics\n\n";
    oss << "| Metric | Value |\n";
    oss << "|--------|-------|\n";
    oss << "| APIs Called | " << metrics_.api_calls_count << " |\n";
    oss << "| Frames Rendered | " << metrics_.frames_rendered << " |\n";
    oss << "| Execution Time | " << metrics_.duration_ms << "ms |\n";
    oss << "| Memory Peak | " << format_bytes(metrics_.memory_peak_bytes) << " |\n";
    oss << "| Errors | " << metrics_.errors_count << " |\n";
    oss << "| Warnings | " << metrics_.warnings_count << " |\n";
    oss << "\n";
    
    // API Call Summary
    auto class_summary = get_call_summary_by_class();
    
    oss << "## API Trace Summary\n\n";
    oss << "| Class | Calls |\n";
    oss << "|-------|-------|\n";
    
    for (const auto& [cls, count] : class_summary) {
        oss << "| `" << cls << "` | " << count << " |\n";
    }
    oss << "\n";
    
    // Detailed call breakdown (top methods)
    auto method_summary = get_call_summary_by_method();
    
    oss << "## Top Method Calls\n\n";
    oss << "| Method | Calls |\n";
    oss << "|--------|-------|\n";
    
    // Sort by count
    std::vector<std::pair<std::string, size_t>> sorted_methods(
        method_summary.begin(), method_summary.end());
    std::sort(sorted_methods.begin(), sorted_methods.end(),
              [](const auto& a, const auto& b) { return a.second > b.second; });
    
    int max_show = std::min(static_cast<int>(sorted_methods.size()), 20);
    for (int i = 0; i < max_show; i++) {
        oss << "| `" << sorted_methods[i].first << "` | " << sorted_methods[i].second << " |\n";
    }
    oss << "\n";
    
    // Errors/Warnings
    if (!errors_.empty()) {
        oss << "## Errors & Issues\n\n";
        
        for (const auto& err : errors_) {
            oss << "### " << err.error_type << "\n\n";
            oss << "- **Message:** " << err.error_message << "\n";
            oss << "- **Location:** `" << err.context_class << "." << err.context_method << "`\n";
            oss << "- **Fatal:** " << (err.is_fatal ? "Yes" : "No") << "\n\n";
        }
    }
    
    // Screenshots
    if (!screenshots_.empty()) {
        oss << "## Screenshots\n\n";
        for (const auto& ss : screenshots_) {
            oss << "### Output Frame\n\n";
            oss << "- **File:** `" << ss.file_path << "`\n";
            oss << "- **Resolution:** " << ss.width << "x" << ss.height << "\n";
            oss << "- **Size:** " << format_bytes(ss.file_size_bytes) << "\n\n";
            oss << "![Screenshot](" << ss.file_path << ")\n\n";
        }
    }
    
    // Session info
    oss << "## Session Info\n\n";
    oss << "- **Session ID:** `" << session_id_ << "`\n";
    oss << "- **Generated:** " << format_timestamp(get_timestamp_ms()) << "\n";
    
    return oss.str();
}

bool TraceEngine::write_reports(const std::string& output_dir,
                                 const std::string& app_name,
                                 const std::string& status,
                                 const std::string& apk_path) {
    try {
        // Create output directory if it doesn't exist
        fs::create_directories(output_dir);
        
        // Write api_trace.json
        json api_trace = generate_api_trace_json();
        std::ofstream api_file(output_dir + "/api_trace.json");
        api_file << api_trace.dump(2);
        api_file.close();
        
        // Write crash.log
        std::ofstream crash_file(output_dir + "/crash.log");
        crash_file << generate_crash_log();
        crash_file.close();
        
        // Write report.md
        std::ofstream report_file(output_dir + "/report.md");
        report_file << generate_markdown_report(app_name, status, apk_path);
        report_file.close();
        
        info("TraceEngine", "write_reports", "Reports written to: " + output_dir);
        
        return true;
    } catch (const std::exception& e) {
        error("TraceEngine", "write_reports", std::string("Failed to write reports: ") + e.what());
        return false;
    }
}

void TraceEngine::clear() {
    traces_.clear();
    errors_.clear();
    screenshots_.clear();
    metrics_ = ExecutionMetrics();
    session_id_.clear();
    session_active_ = false;
}

std::map<std::string, size_t> TraceEngine::get_call_summary_by_class() const {
    std::map<std::string, size_t> summary;
    
    for (const auto& trace : traces_) {
        summary[trace.source_class]++;
    }
    
    return summary;
}

std::map<std::string, size_t> TraceEngine::get_call_summary_by_method() const {
    std::map<std::string, size_t> summary;
    
    for (const auto& trace : traces_) {
        std::string full_method = trace.source_class + "." + trace.source_method;
        summary[full_method]++;
    }
    
    return summary;
}

uint64_t TraceEngine::get_timestamp_ms() {
    return static_cast<uint64_t>(
        std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()
        ).count()
    );
}

std::string TraceEngine::generate_session_id() {
    auto now = std::chrono::system_clock::now();
    auto time_t_now = std::chrono::system_clock::to_time_t(now);
    
    std::ostringstream oss;
    oss << "EXP-001-";
    oss << std::put_time(std::gmtime(&time_t_now), "%Y%m%d-%H%M%S");
    oss << "-" << std::setw(4) << std::setfill('0') 
        << (std::chrono::high_resolution_clock::now().time_since_epoch().count() % 10000);
    
    return oss.str();
}

std::string TraceEngine::format_timestamp(uint64_t ts) {
    auto time_point = std::chrono::system_clock::time_point(
        std::chrono::milliseconds(ts)
    );
    auto time_t_val = std::chrono::system_clock::to_time_t(time_point);
    
    std::ostringstream oss;
    oss << std::put_time(std::gmtime(&time_t_val), "%Y-%m-%d %H:%M:%S UTC");
    return oss.str();
}

std::string format_bytes(size_t bytes) {
    const char* suffixes[] = {"B", "KB", "MB", "GB"};
    int suffix_index = 0;
    double size = static_cast<double>(bytes);
    
    while (size >= 1024 && suffix_index < 3) {
        size /= 1024;
        suffix_index++;
    }
    
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(2) << size << " " << suffixes[suffix_index];
    return oss.str();
}

// ═════════════════════════════════════════════════════════════════════════
// S135 — VISUAL RUNTIME BOOT/TRACE LOGGER — backbone implementation
// ONE RUNTIME EVENT BACKBONE, six sinks (see runtime_event.h header doc).
// ═════════════════════════════════════════════════════════════════════════

const char* event_sev_name(EventSev s) {
    switch (s) {
        case EventSev::CONFIRMED:  return "CONFIRMED";
        case EventSev::PENDING:    return "PENDING";
        case EventSev::FAILURE:    return "FAILURE";
        case EventSev::INFO:       return "INFO";
        case EventSev::RENDERER:   return "RENDERER";
        case EventSev::NOT_REACHED:return "NOT_REACHED";
    }
    return "INFO";
}

namespace {

// Event → canonical stage auto-mapping (the boot contract). Returns the
// stage the event advances, or "" when the event is stage-neutral.
const char* stage_for_event(const std::string& e) {
    // BOOT
    if (e == ev::RUN_START) return stage::BOOT;
    // APK
    if (e == ev::APK_LOADED || e == ev::MANIFEST_PARSED) return stage::APK;
    if (e == ev::APK_LOAD_FAILURE) return stage::APK;
    // DEX
    if (e == ev::DEX_PARSED) return stage::DEX;
    if (e == ev::DEX_FAILURE) return stage::DEX;
    // CLASS-INIT
    if (e == ev::CLASSES_LOADED) return stage::CLASSINIT;
    if (e == ev::CLASS_INIT_FAILURE) return stage::CLASSINIT;
    // LIFECYCLE
    if (e == ev::ACTIVITY_RESUME) return stage::LIFECYCLE;
    if (e == ev::LIFECYCLE_STATE) return stage::LIFECYCLE;
    // VIEWTREE
    if (e == ev::VIEWTREE_CREATED) return stage::VIEWTREE;
    // MEASURE / LAYOUT / DRAW
    if (e == ev::MEASURE_START || e == ev::MEASURE_END) return stage::MEASURE;
    if (e == ev::LAYOUT_START || e == ev::LAYOUT_END) return stage::LAYOUT;
    if (e == ev::DRAW_START || e == ev::DRAW_END) return stage::DRAW;
    if (e == ev::RENDER_OK) return stage::DRAW;   // full render pass completed
    if (e == ev::RENDER_FAIL) return stage::DRAW;
    // FRAME
    if (e == ev::FRAME_SUBMIT || e == ev::FRAME_CAPTURE) return stage::FRAME;
    return "";
}

EventSev sev_for_stage_event(const std::string& e, EventSev in) {
    // *_START events mean "started, not yet confirmed" unless the caller
    // says worse. Failure events stay FAILURE.
    if (in == EventSev::FAILURE) return EventSev::FAILURE;
    const bool is_start =
        e == ev::MEASURE_START || e == ev::LAYOUT_START || e == ev::DRAW_START ||
        e == ev::RENDER_START;
    const bool is_end =
        e == ev::MEASURE_END || e == ev::LAYOUT_END || e == ev::DRAW_END ||
        e == ev::RENDER_OK || e == ev::FRAME_CAPTURE || e == ev::APK_LOADED ||
        e == ev::MANIFEST_PARSED || e == ev::DEX_PARSED ||
        e == ev::CLASSES_LOADED || e == ev::ACTIVITY_RESUME ||
        e == ev::VIEWTREE_CREATED;
    if (is_end && in == EventSev::INFO) return EventSev::CONFIRMED;
    if (is_start && in == EventSev::INFO) return EventSev::PENDING;
    return in;
}

} // anonymous namespace

void TraceEngine::boot_trace_begin(const std::string& output_dir,
                                   const std::string& apk_path) {
    // Env contract (S135 §22/§26):
    //   MINIANDROID_BOOT_TRACE=1      → machine sinks (JSONL + summary)
    //   MINIANDROID_TRACE_UI=1        → visual overlay sink at capture
    //   MINIANDROID_TRACE_VERBOSE=1   → heavy/verbose terminal events
    //   MINIANDROID_TRACE_BUFFER=N    → ring buffer capacity (default 512)
    auto env_flag = [](const char* k) {
        const char* v = std::getenv(k);
        return v && (v[0] == '1' || v[0] == 't' || v[0] == 'T' ||
                     v[0] == 'y' || v[0] == 'Y');
    };
    boot_trace_enabled_ = env_flag("MINIANDROID_BOOT_TRACE");
    trace_ui_           = env_flag("MINIANDROID_TRACE_UI");
    trace_verbose_      = env_flag("MINIANDROID_TRACE_VERBOSE");
    if (const char* b = std::getenv("MINIANDROID_TRACE_BUFFER")) {
        const long n = std::strtol(b, nullptr, 10);
        if (n >= 16 && n <= 1000000) rt_cap_ = static_cast<size_t>(n);
    }

    // run_id: monotonic, collision-free within the process lifetime.
    static uint64_t s_run_counter = 0;
    ++s_run_counter;
    run_id_ = std::to_string(static_cast<long long>(get_timestamp_ms())) +
              "-" + std::to_string(s_run_counter);
    rt_t0_ms_ = get_timestamp_ms();

    if (boot_trace_enabled_ && !output_dir.empty()) {
        std::error_code ec;
        fs::create_directories(output_dir, ec);
        rt_jsonl_.open(output_dir + "/trace.jsonl", std::ios::out | std::ios::trunc);
    }

    RuntimeEvent e0;
    e0.event = ev::RUN_START;
    e0.component = "boot";
    e0.sev = EventSev::PENDING;
    e0.state = "apk=" + apk_path;
    e0.result = "PENDING";
    e0.extra = {
        {"boot_trace", boot_trace_enabled_},
        {"trace_ui", trace_ui_},
        {"buffer_cap", rt_cap_},
        {"pid", static_cast<int64_t>(::getpid())},
    };
    runtime_event(std::move(e0));
}

RuntimeEvent TraceEngine::make_event(const char* event_name, EventSev sev,
                                     const char* component,
                                     const std::string& state,
                                     const std::string& result) const {
    RuntimeEvent e;
    e.event = event_name ? event_name : ev::TRACE_MARK;
    e.sev = sev;
    e.component = component ? component : "";
    e.state = state;
    e.result = result.empty() ? (sev == EventSev::FAILURE ? "FAIL" : "OK")
                              : result;
    e.run_id = run_id_;
    e.package = package_label_;
    e.activity = activity_label_;
    e.renderer_family = renderer_family_;
    return e;
}

void TraceEngine::runtime_event(RuntimeEvent ev_in) {
    // 1) identity sinks
    ev_in.seq = ++rt_seq_;
    ev_in.timestamp_ms = get_timestamp_ms();
    ++rt_total_;
    if (ev_in.run_id.empty())   ev_in.run_id = run_id_;
    if (ev_in.package.empty())  ev_in.package = package_label_;
    if (ev_in.activity.empty()) ev_in.activity = activity_label_;
    if (ev_in.renderer_family.empty())
        ev_in.renderer_family = renderer_family_;
    if (ev_in.thread.empty())   ev_in.thread = "main";

    // 2) ring buffer sink (exception-safe tail — S135 §11)
    rt_events_.push_back(ev_in);
    while (rt_events_.size() > rt_cap_) rt_events_.pop_front();

    // 3) JSONL streaming sink
    if (rt_jsonl_.is_open()) {
        rt_jsonl_ << ev_in.to_json().dump() << "\n";
        rt_jsonl_.flush();
    }

    // 4) terminal sink (default INFO/WARN/ERROR/FRONTIER; verbose = all)
    //    Compact, grep-able, no duplication of the existing [TAG] prints.
    const bool noteworthy =
        ev_in.sev == EventSev::FAILURE || ev_in.sev == EventSev::PENDING;
    if (boot_trace_enabled_ && (trace_verbose_ || noteworthy ||
                                ev_in.event == ev::FRAME_ANALYSIS)) {
        std::ostringstream oss;
        oss << "[TRACE] " << ev_in.seq << " " << ev_in.event;
        if (!ev_in.state.empty())    oss << " state=" << ev_in.state;
        if (!ev_in.result.empty())   oss << " result=" << ev_in.result;
        if (!ev_in.exception.empty()) oss << " exc=" << ev_in.exception;
        if (!ev_in.cls.empty())      oss << " cls=" << ev_in.cls;
        if (!ev_in.method.empty())   oss << " m=" << ev_in.method;
        if (!ev_in.renderer_family.empty())
            oss << " rf=" << ev_in.renderer_family;
        if (ev_in.sev == EventSev::FAILURE) oss << " [FRONTIER]";
        std::cerr << oss.str() << std::endl;
    }

    // 5) stage machine sink — auto-advance the canonical boot contract
    const char* st = stage_for_event(ev_in.event);
    if (st && *st) {
        const EventSev s2 = sev_for_stage_event(ev_in.event, ev_in.sev);
        std::string detail = ev_in.state;
        if (!ev_in.method.empty())
            detail += (detail.empty() ? "" : " | ") + ev_in.cls + "." + ev_in.method;
        mark_stage(st, s2, detail);
    }
    // RENDER_START formally opens the three render sub-stages (S135 §3):
    // measure → layout → draw are PENDING until the composed frame confirms.
    // (No detail here — the confirming event's state becomes the detail.)
    if (ev_in.event == ev::RENDER_START) {
        mark_stage(stage::MEASURE, EventSev::PENDING, "");
        mark_stage(stage::LAYOUT, EventSev::PENDING, "");
        mark_stage(stage::DRAW, EventSev::PENDING, "");
    }

    // 6) FAILURE events attach as divergence evidence immediately (§12:
    //    recorded as evidence — the FINAL first-divergence verdict is
    //    derived from stage states at finalize; exceptions never masquerade
    //    as the divergence by themselves).
    if (ev_in.sev == EventSev::FAILURE && first_divergence_.is_null()) {
        // provisional divergence evidence (final verdict computed at
        // finalize from the stage machine; this is the earliest signal)
        first_divergence_candidate_ = {
            {"stage", st && *st ? nlohmann::json(st) : nlohmann::json(nullptr)},
            {"event", ev_in.event},
            {"seq", ev_in.seq},
            {"exception", ev_in.exception},
            {"state", ev_in.state},
            {"cls", ev_in.cls},
            {"method", ev_in.method},
        };
    }
}

void TraceEngine::mark_stage(const std::string& stage, EventSev sev,
                             const std::string& detail) {
    // State escalation law: CONFIRMED is sticky except when a later FAILURE
    // legitimately demotes it (a stage can confirm then fail on re-render).
    auto it = stage_states_.find(stage);
    if (it == stage_states_.end()) {
        stage_states_[stage] = sev;
    } else {
        // precedence: FAILURE > CONFIRMED > PENDING
        const EventSev cur = it->second;
        if (sev == EventSev::FAILURE ||
            (sev == EventSev::CONFIRMED && cur == EventSev::PENDING) ||
            cur == EventSev::NOT_REACHED) {
            it->second = sev;
        }
    }
    if (!detail.empty()) stage_details_[stage] = detail;   // last writer wins

    // Walk-through confirmation law (S135 §12): the canonical order IS the
    // AOSP execution contract — a stage that CONFIRMED proves every earlier
    // stage that had STARTED (PENDING) actually completed (their explicit
    // confirmation event just never fired — e.g. BOOT's RUN_START, or the
    // measure/layout legs of one render pass). NOT_REACHED earlier stages
    // are NOT promoted: an unstarted lifecycle is real evidence.
    if (sev == EventSev::CONFIRMED) {
        bool seen = false;
        for (const auto& sname : stage::canonical_order()) {
            if (sname == stage) { seen = true; break; }
            auto pit = stage_states_.find(sname);
            if (pit != stage_states_.end() && pit->second == EventSev::PENDING)
                pit->second = EventSev::CONFIRMED;
        }
        (void)seen;
    }
}

void TraceEngine::record_frame_analysis(int w, int h, uint32_t dominant_color,
                                        double dominant_pct,
                                        size_t unique_colors,
                                        size_t non_default_px,
                                        const std::string& verdict,
                                        const std::string& sha_hex) {
    frame_analysis_ = {
        {"size", std::to_string(w) + "x" + std::to_string(h)},
        {"width", w}, {"height", h},
        {"dominant_color", (nlohmann::json) {
            ("#" + ([](uint32_t c) {
                std::ostringstream o; o << std::hex << std::setw(6)
                << std::setfill('0') << c; return o.str(); })(dominant_color))},
        },
        {"dominant_pct", dominant_pct},
        {"unique_colors", unique_colors},
        {"non_default_pixels", non_default_px},
        {"verdict", verdict},
        {"screenshot_sha256", sha_hex},
    };
    RuntimeEvent e = make_event(ev::FRAME_ANALYSIS, EventSev::INFO, "capture",
                                verdict, "OK");
    e.extra = frame_analysis_;
    runtime_event(std::move(e));
}

void TraceEngine::set_renderer_family(const std::string& family,
                                      const std::string& evidence) {
    if (renderer_family_ == family) return;
    renderer_family_ = family;
    RuntimeEvent e = make_event(ev::TRACE_MARK, EventSev::RENDERER,
                                "render", family, "OK");
    e.provenance = evidence.empty() ? "renderer-family" : evidence;
    runtime_event(std::move(e));
}

void TraceEngine::set_first_divergence(const std::string& stage,
                                       const std::string& expected,
                                       const std::string& actual,
                                       const std::string& evidence) {
    if (!first_divergence_.is_null()) return;  // FIRST one wins (§12)
    first_divergence_ = {
        {"stage", stage},
        {"expected", expected},
        {"actual", actual},
        {"evidence", evidence},
        {"seq", rt_seq_},
    };
}

nlohmann::json TraceEngine::boot_trace_finalize(const std::string& output_dir) {
    using s_ev = EventSev;
    // ── FIRST-DIVERGENCE derivation from the canonical stage machine ────
    // Law (S135 §12): FIRST_DIVERGENCE = first stage (canonical order)
    // whose state is not CONFIRMED while the boot walk had already started
    // (some earlier stage CONFIRMED/PENDING/FAILURE). LAST_EXCEPTION is
    // reported separately — never conflated.
    const auto& order = stage::canonical_order();
    nlohmann::json stages = nlohmann::json::array();
    std::string last_success, divergence_stage, next_required;
    // Derivation law (S135 §12, two passes):
    //   Pass 1: a stage whose state is FAILURE is authoritative — the FIRST
    //           failure in canonical order is the divergence point (a later
    //           CONFIRMED stage does not erase the failure: the machine
    //           recorded the walk passing through a broken leg).
    //   Pass 2 (no failure): the first stage that is not CONFIRMED while
    //           earlier stages confirmed = where the walk stopped.
    std::string first_failure_stage;
    for (const auto& sname : order) {
        EventSev st = s_ev::NOT_REACHED;
        auto it = stage_states_.find(sname);
        if (it != stage_states_.end()) st = it->second;
        if (st == s_ev::FAILURE) { first_failure_stage = sname; break; }
    }
    for (const auto& sname : order) {
        EventSev st = s_ev::NOT_REACHED;
        auto it = stage_states_.find(sname);
        if (it != stage_states_.end()) st = it->second;
        stages.push_back({
            {"stage", sname},
            {"state", event_sev_name(st)},
            {"detail", stage_detail(sname)},
        });
        if (!divergence_stage.empty()) continue;
        if (st == s_ev::CONFIRMED) { last_success = sname; continue; }
        if (!first_failure_stage.empty()) {
            // skip ahead: divergence handled below by the failure stage
            continue;
        }
        divergence_stage = sname;   // first non-confirmed = walk stopped here
    }
    if (!first_failure_stage.empty() && divergence_stage.empty())
        divergence_stage = first_failure_stage;
    // next required stage: the one after the divergence (canonical successor)
    if (!divergence_stage.empty()) {
        for (size_t i = 0; i + 1 < order.size(); ++i) {
            if (order[i] == divergence_stage) { next_required = order[i + 1]; break; }
        }
    }

    if (first_divergence_.is_null() && !divergence_stage.empty()) {
        // derive from the stage machine (authoritative §12 path)
        std::string actual = stage_detail(divergence_stage);
        if (actual.empty())
            actual = std::string("stage ") + event_sev_name(
                stage_states_.count(divergence_stage)
                    ? stage_states_[divergence_stage] : s_ev::NOT_REACHED);
        first_divergence_ = {
            {"stage", divergence_stage},
            {"expected", divergence_stage + " confirmed (boot contract)"},
            {"actual", actual.empty() ? "not reached / not confirmed" : actual},
            {"last_successful_stage", last_success},
            {"next_required_stage", next_required},
            {"source", "stage-machine-derivation"},
        };
    } else if (!first_divergence_.is_null()) {
        // caller-provided divergence keeps its fields; enrich the chain
        // fields the caller could not know at emit time.
        if (!first_divergence_.contains("last_successful_stage"))
            first_divergence_["last_successful_stage"] = last_success;
        if (!first_divergence_.contains("next_required_stage"))
            first_divergence_["next_required_stage"] = next_required;
        if (!first_divergence_.contains("source"))
            first_divergence_["source"] = "explicit-evidence";
    }
    // Attach the earliest failure candidate as evidence (distinct from the
    // verdict — FIRST_DIVERGENCE != LAST_EXCEPTION, §12). When no stage
    // divergence exists the candidate travels under its own key and NEVER
    // fabricates a non-null first_divergence object.
    nlohmann::json last_exception = nullptr;
    for (auto it = rt_events_.rbegin(); it != rt_events_.rend(); ++it) {
        if (it->sev == EventSev::FAILURE) {
            last_exception = it->to_json();
            break;
        }
    }
    if (!first_divergence_.is_null() && !first_divergence_candidate_.is_null())
        first_divergence_["first_failure_event"] = first_divergence_candidate_;

    // ── events tail (last 32, §11) ──────────────────────────────────────
    nlohmann::json tail = nlohmann::json::array();
    const size_t kTail = 32;
    const size_t n = rt_events_.size();
    const size_t skip = n > kTail ? n - kTail : 0;
    for (size_t i = skip; i < n; ++i) tail.push_back(rt_events_[i].to_json());

    // severity census
    std::map<std::string, size_t> sev_census;
    for (const auto& e : rt_events_) sev_census[event_sev_name(e.sev)]++;

    const uint64_t dur = get_timestamp_ms() -
                         (rt_t0_ms_ ? rt_t0_ms_ : metrics_.start_time_ms);
    nlohmann::json summary = {
        {"schema", "miniandroid.boot_trace/1.0"},
        {"instrument", "S135 VISUAL RUNTIME BOOT/TRACE LOGGER"},
        {"run_id", run_id_},
        {"session_id", session_id_},
        {"apk_package", package_label_},
        {"activity", activity_label_},
        {"lifecycle", lifecycle_label_},
        {"renderer_family", renderer_family_.empty() ? rf::UNKNOWN
                                                     : renderer_family_},
        {"duration_ms", dur},
        {"events_total", rt_total_},
        {"events_retained", rt_events_.size()},
        {"severity_census", sev_census},
        {"stages", stages},
        {"first_divergence", first_divergence_.is_null()
                             ? nullptr : first_divergence_},
        {"first_failure_event", first_divergence_.is_null() &&
                                !first_divergence_candidate_.is_null()
                                ? first_divergence_candidate_ : nullptr},
        {"last_exception", last_exception},
        {"frame_analysis", frame_analysis_.is_null() ? nullptr
                                                     : frame_analysis_},
        {"last_events", tail},
    };

    if (boot_trace_enabled_ && !output_dir.empty()) {
        std::error_code ec;
        fs::create_directories(output_dir, ec);
        std::ofstream f(output_dir + "/trace_summary.json");
        if (f) { f << summary.dump(2) << std::endl; }
        if (rt_jsonl_.is_open()) {
            rt_jsonl_ << nlohmann::json{
                {"seq", ++rt_seq_}, {"ts_ms", get_timestamp_ms()},
                {"run_id", run_id_}, {"event", ev::RUN_END},
                {"component", "boot"},
                {"sev", summary["first_divergence"].is_null()
                        ? "CONFIRMED" : "FAILURE"},
                {"state", summary["first_divergence"].is_null()
                          ? "run complete" : "diverged"},
            }.dump() << "\n";
            rt_jsonl_.close();
        }
    }
    return summary;
}

} // namespace diagnostics
} // namespace miniandroid
