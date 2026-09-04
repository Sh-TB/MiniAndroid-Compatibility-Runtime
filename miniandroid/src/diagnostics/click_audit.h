// UNIFIED_002 — EXP-100: env-gated click/chain audit writer (DIAGNOSTIC).
//
// Purpose: close the evidence-preservation gap found in the UNIFIED_000
// consolidation (AUTOMATIC_CLICK_ANALYSIS.md): phase_b_click dispatched
// clicks but per-click target data existed only on stderr, which was not
// persisted. This header lets both execution_engine.cpp (phase_b_click,
// candidate enumeration, stop condition) and dalvik_engine.cpp
// (dispatch_click / dispatch_click_by_class) append structured JSON Lines
// records to a file.
//
// SAFETY / CLASSIFICATION:
//   - DIAGNOSTIC ONLY. Enabled exclusively when the environment variable
//     MINIANDROID_CLICK_AUDIT contains a writable file path.
//   - When the variable is unset/empty (default) this code performs ONE
//     getenv call per record and writes nothing — zero behavior change.
//   - No runtime semantics are altered: no DEX, bridge, or renderer code
//     path depends on these records.
#pragma once

#include <atomic>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <fstream>
#include <string>

namespace miniandroid {
namespace diagnostics {

// Append one pre-formatted JSON line to the audit file (env-gated).
inline void audit_append(const std::string& json_line) {
    const char* path = std::getenv("MINIANDROID_CLICK_AUDIT");
    if (path == nullptr || path[0] == '\0') return;  // default: disabled
    std::ofstream f(path, std::ios::app);
    if (f.is_open()) f << json_line << "\n";
}

// Millisecond-resolution ISO-8601 local timestamp.
inline std::string iso_now() {
    using namespace std::chrono;
    auto now = system_clock::now();
    std::time_t t = system_clock::to_time_t(now);
    struct tm tm_buf;
#if defined(_WIN32)
    localtime_s(&tm_buf, &t);   // Win32 secure variant (POSIX localtime_r unavailable)
#else
    localtime_r(&t, &tm_buf);
#endif
    char buf[40];
    std::strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%S", &tm_buf);
    auto ms = duration_cast<milliseconds>(now.time_since_epoch()).count() % 1000;
    char out[64];
    std::snprintf(out, sizeof(out), "%s.%03lldZ", buf, static_cast<long long>(ms));
    return std::string(out);
}

// Monotonic per-process click counter (shared by all dispatch sites).
inline std::atomic<uint64_t>& click_counter() {
    static std::atomic<uint64_t> ctr{0};
    return ctr;
}

// Minimal JSON string escaping (control chars, quote, backslash).
inline std::string jesc(const std::string& s) {
    std::string out;
    out.reserve(s.size() + 8);
    char b[8];
    for (char c : s) {
        switch (c) {
            case '"':  out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n";  break;
            case '\r': out += "\\r";  break;
            case '\t': out += "\\t";  break;
            default:
                if (static_cast<unsigned char>(c) < 0x20) {
                    std::snprintf(b, sizeof(b), "\\u%04x", c);
                    out += b;
                } else {
                    out += c;
                }
        }
    }
    return out;
}

}  // namespace diagnostics
}  // namespace miniandroid
