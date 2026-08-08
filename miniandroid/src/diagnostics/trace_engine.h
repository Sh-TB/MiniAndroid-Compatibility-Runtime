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
#include <fstream>
#include <sstream>
#include <chrono>
#include <iomanip>
#include <memory>
#include <cstdint>

// Include JSON library (nlohmann/json)
#include <nlohmann/json.hpp>

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

private:
    std::string session_id_;
    std::vector<TraceEntry> traces_;
    std::vector<ErrorRecord> errors_;
    std::vector<ScreenshotRecord> screenshots_;
    ExecutionMetrics metrics_;
    
    bool session_active_ = false;
    
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
