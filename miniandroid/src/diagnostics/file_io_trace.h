// IAPK CAMPAIGN — file-IO provenance instrument (header-only).
//
// Records the runtime's file operations with provenance (op / path /
// result / caller / subsystem) so installed-app runs can prove WHERE the
// app's bytes actually go and come from:
//
//   OPEN READ WRITE STAT LIST EXISTS MKDIR CREATE DELETE RENAME
//
// Env-gated: MINIANDROID_FILE_IO=<out.jsonl> enables it. Bounded by law
// (max 4000 events — focused trace, not a firehose; counters always keep
// the totals). Zero cost when unset (one bool check).
//
// Output JSONL, one record per op:
//   {"seq":N,"op":"OPEN","path":"...","result":"SUCCESS"|"FAILURE",
//    "subsystem":"...","caller":"Class.method","package":"..."}
// plus a final summary line {"summary":{op:count,...},"failures":N,...}
#ifndef MINIANDROID_FILE_IO_TRACE_H
#define MINIANDROID_FILE_IO_TRACE_H

#include <cstdlib>
#include <fstream>
#include <map>
#include <mutex>
#include <string>
#include <vector>

namespace miniandroid {
namespace diagnostics {

class FileIoTrace {
public:
    static FileIoTrace& instance() {
        static FileIoTrace inst;
        return inst;
    }

    // Reads MINIANDROID_FILE_IO=<out.jsonl>.
    void begin() {
        const char* p = std::getenv("MINIANDROID_FILE_IO");
        if (p && *p) {
            std::lock_guard<std::mutex> lk(mu_);
            enabled_ = true;
            out_path_ = p;
        }
    }

    bool enabled() const {
        return enabled_;
    }

    // One record per traced file operation. Cheap no-op when disabled.
    void record(const std::string& op, const std::string& path, bool ok,
                const std::string& subsystem, const std::string& caller) {
        if (!enabled_) return;
        std::lock_guard<std::mutex> lk(mu_);
        counters_[op]++;
        total_ops_++;
        if (!ok) failures_++;
        if (events_.size() >= kMaxEvents) {
            dropped_++;
            return;
        }
        events_.push_back({seq_++, op, path, ok, subsystem, caller});
    }

    // Write the JSONL trace + summary. Safe to call multiple times
    // (one-shot: cleared after the first successful write).
    void finalize(const std::string& running_package) {
        if (!enabled_) return;
        std::lock_guard<std::mutex> lk(mu_);
        std::ofstream f(out_path_, std::ios::binary);
        if (f) {
            for (const auto& e : events_) {
                f << "{\"seq\":" << e.seq
                  << ",\"op\":\"" << e.op
                  << "\",\"path\":\"" << json_escape(e.path)
                  << "\",\"result\":\"" << (e.ok ? "SUCCESS" : "FAILURE")
                  << "\",\"subsystem\":\"" << json_escape(e.subsystem)
                  << "\",\"caller\":\"" << json_escape(e.caller)
                  << "\",\"package\":\"" << json_escape(running_package)
                  << "\"}\n";
            }
            f << "{\"summary\":{\"total_ops\":" << total_ops_
              << ",\"failures\":" << failures_
              << ",\"events_emitted\":" << events_.size()
              << ",\"events_dropped\":" << dropped_
              << ",\"package\":\"" << json_escape(running_package) << "\"";
            for (const auto& [op, n] : counters_)
                f << ",\"" << op << "\":" << n;
            f << "}}\n";
        }
        enabled_ = false;
        events_.clear();
    }

    size_t total_ops() const { return total_ops_; }

private:
    struct Event {
        uint64_t seq;
        std::string op;
        std::string path;
        bool ok;
        std::string subsystem;
        std::string caller;
    };

    static std::string json_escape(const std::string& s) {
        std::string out;
        for (char c : s) {
            switch (c) {
                case '"': out += "\\\""; break;
                case '\\': out += "\\\\"; break;
                case '\n': out += "\\n"; break;
                case '\r': out += "\\r"; break;
                case '\t': out += "\\t"; break;
                default:
                    if (static_cast<unsigned char>(c) < 0x20) {
                        char b[8]; snprintf(b, sizeof(b), "\\u%04x", c);
                        out += b;
                    } else out += c;
            }
        }
        return out;
    }

    static constexpr size_t kMaxEvents = 4000;

    std::mutex mu_;
    bool enabled_ = false;
    std::string out_path_;
    std::vector<Event> events_;
    std::map<std::string, size_t> counters_;
    uint64_t seq_ = 0;
    uint64_t total_ops_ = 0;
    uint64_t failures_ = 0;
    uint64_t dropped_ = 0;
};

}  // namespace diagnostics
}  // namespace miniandroid

#endif  // MINIANDROID_FILE_IO_TRACE_H
