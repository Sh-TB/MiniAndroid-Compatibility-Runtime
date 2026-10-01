/*
 * MiniAndroid Runtime v0.1 - Diagnostics / Trace Engine
 * EXP-001: HelloWorld Loader
 * 
 * Comprehensive tracing, logging, and report generation system.
 */

#ifndef MINIANDROID_TRACE_ENGINE_H
#define MINIANDROID_TRACE_ENGINE_H

#include <string>
#include <vector>
#include <map>
#include <deque>
#include <fstream>
#include <sstream>
#include <chrono>
#include <iomanip>
#include <memory>
#include <cstdint>

// Include JSON library (nlohmann/json)
#include <nlohmann/json.hpp>

// S135: canonical runtime event model (ONE RUNTIME EVENT BACKBONE)
#include "runtime_event.h"

namespace miniandroid {
namespace diagnostics {

// Log levels
enum class LogLevel {
    DEBUG,
    INFO,
    WARNING,
    ERROR,
    FATAL
};

// Trace entry structure
struct TraceEntry {
    uint64_t timestamp_ms;
    std::string category;        // "API", "RENDER", "PARSE", "SYSTEM"
    LogLevel level;
    std::string source_class;
    std::string source_method;
    std::string message;
    std::vector<std::string> args;
    
    // Convert to JSON
    nlohmann::json to_json() const {
        nlohmann::json j;
        j["timestamp"] = timestamp_ms;
        j["category"] = category;
        j["level"] = log_level_to_string(level);
        j["class"] = source_class;
        j["method"] = source_method;
        j["message"] = message;
        if (!args.empty()) {
            j["args"] = args;
        }
        return j;
    }

private:
    static const char* log_level_to_string(LogLevel l) {
        switch (l) {
            case LogLevel::DEBUG:    return "DEBUG";
            case LogLevel::INFO:     return "INFO";
            case LogLevel::WARNING:  return "WARNING";
            case LogLevel::ERROR:    return "ERROR";
            case LogLevel::FATAL:    return "FATAL";
            default:                 return "UNKNOWN";
        }
    }
};

// Error/exception record
struct ErrorRecord {
    uint64_t timestamp_ms;
    std::string error_type;       // "UNIMPLEMENTED_API", "PARSE_ERROR", etc.
    std::string error_message;
    std::string context_class;
    std::string context_method;
    bool is_fatal;
    
    nlohmann::json to_json() const {
        nlohmann::json j;
        j["timestamp"] = timestamp_ms;
        j["type"] = error_type;
        j["message"] = error_message;
        j["context"]["class"] = context_class;
        j["context"]["method"] = context_method;
        j["fatal"] = is_fatal;
        return j;
    }
};

// Screenshot record
struct ScreenshotRecord {
    std::string file_path;
    int width;
    int height;
    size_t file_size_bytes;
    uint64_t timestamp_ms;
    
    nlohmann::json to_json() const {
        nlohmann::json j;
        j["file_path"] = file_path;
        j["width"] = width;
        j["height"] = height;
        j["size_bytes"] = file_size_bytes;
        j["timestamp"] = timestamp_ms;
        return j;
    }
};

// Execution metrics
struct ExecutionMetrics {
    uint64_t start_time_ms = 0;
    uint64_t end_time_ms = 0;
    uint64_t duration_ms = 0;
    
    size_t api_calls_count = 0;
    size_t frames_rendered = 0;
    size_t errors_count = 0;
    size_t warnings_count = 0;
    
    // Memory metrics (if available)
    size_t memory_peak_bytes = 0;
    size_t memory_current_bytes = 0;
    
    nlohmann::json to_json() const {
        nlohmann::json j;
        j["start_time"] = start_time_ms;
        j["end_time"] = end_time_ms;
        j["duration_ms"] = duration_ms;
        j["api_calls"] = api_calls_count;
        j["frames_rendered"] = frames_rendered;
        j["errors"] = errors_count;
        j["warnings"] = warnings_count;
        j["memory_peak_bytes"] = memory_peak_bytes;
        j["memory_current_bytes"] = memory_current_bytes;
        return j;
    }
};

/**
 * Main trace engine class
 * 
 * Collects all execution data and generates comprehensive reports.
 */
class TraceEngine {
public:
    TraceEngine();
    ~TraceEngine();
    
    /**
     * Start a new tracing session
     */
    void start_session(const std::string& session_id = "");
    
    /**
     * End current session
     */
    void end_session();
    
    /**
     * Get session ID
     */
    std::string get_session_id() const { return session_id_; }
    
    /**
     * Add a trace entry
     */
    void trace(const std::string& category, LogLevel level,
               const std::string& source_class, const std::string& method,
               const std::string& message,
               const std::vector<std::string>& args = {});
    
    // Convenience methods for common log levels
    void debug(const std::string& cls, const std::string& method, const std::string& msg);
    void info(const std::string& cls, const std::string& method, const std::string& msg);
    void warning(const std::string& cls, const std::string& method, const std::string& msg);
    void error(const std::string& cls, const std::string& method, const std::string& msg);
    void fatal(const std::string& cls, const std::string& method, const std::string& msg);
    
    /**
     * Record an error/exception
     */
    void record_error(const std::string& type, const std::string& message,
                      const std::string& context_class = "", 
                      const std::string& context_method = "",
                      bool is_fatal = false);
    
    /**
     * Record a screenshot capture
     */
    void log_screenshot(const std::string& path, int width, int height, size_t size);
    
    /**
     * Increment frame counter
     */
    void increment_frame_count() { metrics_.frames_rendered++; }
    
    /**
     * Set/get metrics
     */
    ExecutionMetrics& get_metrics() { return metrics_; }
    const ExecutionMetrics& get_metrics() const { return metrics_; }
    
    /**
     * Get all traces
     */
    const std::vector<TraceEntry>& get_traces() const { return traces_; }
    
    /**
     * Get all errors
     */
    const std::vector<ErrorRecord>& get_errors() const { return errors_; }
    
    /**
     * Get screenshot records
     */
    const std::vector<ScreenshotRecord>& get_screenshots() const { return screenshots_; }
    
    /**
     * Generate API trace JSON
     */
    nlohmann::json generate_api_trace_json() const;
    
    /**
     * Generate crash/error log
     */
    std::string generate_crash_log() const;
    
    /**
     * Generate Markdown report
     */
    std::string generate_markdown_report(const std::string& app_name, 
                                          const std::string& status,
                                          const std::string& apk_path) const;
    
    /**
     * Write all output files to directory
     */
    bool write_reports(const std::string& output_dir,
                       const std::string& app_name,
                       const std::string& status,
                       const std::string& apk_path);
    
    /**
     * Clear all collected data
     */
    void clear();
    
    /**
     * Get call count summary by class
     */
    std::map<std::string, size_t> get_call_summary_by_class() const;
    
    /**
     * Get call count summary by method
     */
    std::map<std::string, size_t> get_call_summary_by_method() const;

    // ═══════════════════════════════════════════════════════════════════
    // S135 — RUNTIME EVENT BACKBONE (ONE backbone, many sinks)
    // ═══════════════════════════════════════════════════════════════════

    // Begin the boot-trace session for one run. output_dir receives:
    //   trace.jsonl (streaming) — enabled via MINIANDROID_BOOT_TRACE=1 or
    //   the trace enabled flag below. run_id is generated here.
    void boot_trace_begin(const std::string& output_dir,
                          const std::string& apk_path);

    // THE canonical entry point. Dispatches to every active sink:
    // ring buffer, JSONL stream, terminal log, stage machine.
    void runtime_event(RuntimeEvent ev);

    // Convenience factory: minimal event with severity + state/result.
    RuntimeEvent make_event(const char* event_name, EventSev sev,
                            const char* component,
                            const std::string& state = "",
                            const std::string& result = "") const;

    // Stage-machine updates. mark_stage maps boot-contract stages to
    // CONFIRMED/PENDING/FAILURE and records detail evidence.
    void mark_stage(const std::string& stage, EventSev sev,
                    const std::string& detail = "");

    // Frame analysis record (dominant color / unique colors / non-default
    // pixels / verdict). Drives DEFAULT_BACKGROUND_ONLY vs REAL_APP_CONTENT.
    void record_frame_analysis(int w, int h, uint32_t dominant_color,
                               double dominant_pct, size_t unique_colors,
                               size_t non_default_px,
                               const std::string& verdict,
                               const std::string& sha_hex);

    // FINAL CAMPAIGN item 21 (P0-6): merge the frame-truth census (render
    // correlation ledger + pixel ownership) into frame_analysis_. Carried
    // into trace_summary.json + the FRAME_ANALYSIS event so no consumer can
    // see a verdict without the correlated proof behind it.
    void record_frame_census(const nlohmann::json& census);

    // Renderer family observation (PURPLE provenance lane).
    void set_renderer_family(const std::string& family,
                             const std::string& evidence);

    // First divergence: recorded ONCE (first one wins — §12), with the
    // expected-vs-actual chain. Exceptions attach separately; the engine
    // NEVER collapses FIRST_DIVERGENCE into LAST_EXCEPTION.
    void set_first_divergence(const std::string& stage,
                              const std::string& expected,
                              const std::string& actual,
                              const std::string& evidence);

    // Finalize: derive stage machine divergence, write trace_summary.json
    // (+ screenshot_metrics.json companion data) into output_dir.
    nlohmann::json boot_trace_finalize(const std::string& output_dir);

    // Sinks state ----------------------------------------------------------
    bool boot_trace_enabled() const { return boot_trace_enabled_; }
    bool trace_ui_enabled() const { return trace_ui_; }
    uint64_t rt_total() const { return rt_total_; }
    const std::string& run_id() const { return run_id_; }
    const std::deque<RuntimeEvent>& runtime_events() const { return rt_events_; }

    // Stage states for the overlay panel: name → severity.
    const std::map<std::string, EventSev>& stage_states() const { return stage_states_; }
    const std::map<std::string, std::string>& stage_details() const { return stage_details_; }
    const std::string& stage_detail(const std::string& stage) const {
        static const std::string kEmpty;
        auto it = stage_details_.find(stage);
        return it != stage_details_.end() ? it->second : kEmpty;
    }

    const std::string& current_renderer_family() const { return renderer_family_; }
    const nlohmann::json& first_divergence() const { return first_divergence_; }
    const nlohmann::json& frame_analysis() const { return frame_analysis_; }
    const std::string& last_event_name() const {
        // Returns by value via a member-backed static — the ternary below
        // mixes const char* and std::string, which materializes a temporary;
        // binding a temporary to a returned const& would dangle (S135 fix).
        static const std::string kNone{k_no_event_};
        return rt_events_.empty() ? kNone : rt_events_.back().event;
    }
    // Lifecycle label shown on the header ("RESUMED", "CREATED", ...)
    void set_lifecycle_label(const std::string& label) { lifecycle_label_ = label; }
    const std::string& lifecycle_label() const { return lifecycle_label_; }
    // Current activity label (best effort, for the header).
    void set_activity_label(const std::string& a) { activity_label_ = a; }
    const std::string& activity_label() const { return activity_label_; }
    void set_package_label(const std::string& p) { package_label_ = p; }
    const std::string& package_label() const { return package_label_; }

private:
    std::string session_id_;
    std::vector<TraceEntry> traces_;
    std::vector<ErrorRecord> errors_;
    std::vector<ScreenshotRecord> screenshots_;
    ExecutionMetrics metrics_;
    
    bool session_active_ = false;

    // ── S135 runtime event backbone sinks ────────────────────────────────
    bool boot_trace_enabled_ = false;      // MINIANDROID_BOOT_TRACE=1 / --trace
    bool trace_verbose_ = false;           // MINIANDROID_TRACE_VERBOSE=1
    bool trace_ui_ = false;                // MINIANDROID_TRACE_UI=1 / --trace-ui
    std::string run_id_;
    std::string package_label_;
    std::string activity_label_;
    std::string lifecycle_label_;
    std::string renderer_family_;
    std::deque<RuntimeEvent> rt_events_;   // ring buffer (configurable cap)
    size_t rt_cap_ = 512;
    uint64_t rt_seq_ = 0;
    uint64_t rt_total_ = 0;                // total events emitted (may exceed cap)
    std::ofstream rt_jsonl_;               // streaming JSONL sink
    std::map<std::string, EventSev> stage_states_;    // canonical stage machine
    std::map<std::string, std::string> stage_details_; // evidence per stage
    nlohmann::json first_divergence_;      // null until derived/observed
    nlohmann::json first_divergence_candidate_; // earliest FAILURE evidence (§12)
    nlohmann::json frame_analysis_;
    uint64_t rt_t0_ms_ = 0;

    static constexpr const char* k_no_event_ = "(none)";

    static uint64_t get_timestamp_ms();
    static std::string generate_session_id();
    static std::string format_timestamp(uint64_t ts);
};

/**
 * Scoped timer for measuring execution time
 */
class ScopedTimer {
public:
    ScopedTimer(TraceEngine& engine, const std::string& label)
        : engine_(engine), label_(label), start_(std::chrono::high_resolution_clock::now()) {}
    
    ~ScopedTimer() {
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start_);
        
        engine_.info("ScopedTimer", label_, "Completed in " + std::to_string(duration.count()) + "ms");
    }

private:
    TraceEngine& engine_;
    std::string label_;
    std::chrono::time_point<std::chrono::high_resolution_clock> start_;
};

} // namespace diagnostics
} // namespace miniandroid

#endif // MINIANDROID_TRACE_ENGINE_H
