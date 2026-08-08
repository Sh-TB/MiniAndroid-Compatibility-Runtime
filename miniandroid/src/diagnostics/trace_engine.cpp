/*
 * MiniAndroid Runtime v0.1 - Trace Engine Implementation
 * EXP-001: HelloWorld Loader
 */

#include "trace_engine.h"
#include <filesystem>
#include <algorithm>

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

} // namespace diagnostics
} // namespace miniandroid
