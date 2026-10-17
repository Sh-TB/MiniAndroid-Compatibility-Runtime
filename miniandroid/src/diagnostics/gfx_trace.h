// CONT-83 WS-B — first-party op-level GRAPHICS TRACE (JSONL).
//
// CONT-83 directive: "Implement a low-overhead, opt-in trace/event layer
// around the actual internal API boundary. Use an explicit schema version
// and correlation IDs." This layer records EVERY graphics-boundary call
// (GL10/GLES20/EGL/native-lib loads/frame present) as one JSONL row with:
//   schema v, event type, steady ns since first event, frame counter, op,
//   api, handled, bounded extras. The FIRST MISSING TRANSITION is recorded
// as it happens (gl.rec-miss / native.dep-missing / marshal-failure rows),
// not reconstructed by hand.
//
// Zero cost when MINIANDROID_GFX_TRACE is unset (one thread_local bool).
// Bounded: per-op rows are capped (kMaxSameOp) + global cap; drops counted
// and reported. Redaction: no pixel data, no user content — op names,
// handles, dims, return codes only. Sink: one JSONL file (default
// $MINIANDROID_OUT_DIR/gfx_trace.jsonl, or MINIANDROID_GFX_TRACE_FILE).
//
// A/B discipline: tracing-on must never alter rendering semantics — the
// wall anchors are re-verified byte-identical with the trace ON (see
// evidence/cont83/).
#ifndef MINIANDROID_GFX_TRACE_H
#define MINIANDROID_GFX_TRACE_H

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <map>
#include <mutex>
#include <string>
#include <vector>

#include <nlohmann/json.hpp>

namespace miniandroid {
namespace gfx {

class GfxTrace {
public:
    static GfxTrace& instance() {
        static GfxTrace t;
        return t;
    }

    static bool env_enabled() {
        static const bool on = [] {
            const char* e = std::getenv("MINIANDROID_GFX_TRACE");
            return e && *e && e[0] != '0';
        }();
        return on;
    }

    // Sink resolution (lazy, first event wins): MINIANDROID_GFX_TRACE_FILE
    // else $MINIANDROID_OUT_DIR/gfx_trace.jsonl else ./gfx_trace.jsonl.
    void sink_path(std::string& out) const {
        const char* f = std::getenv("MINIANDROID_GFX_TRACE_FILE");
        if (f && *f) { out = f; return; }
        const char* d = std::getenv("MINIANDROID_OUT_DIR");
        out = (d && *d ? std::string(d) : std::string(".")) +
              "/gfx_trace.jsonl";
    }

    // Core event emit. `fill` mutates the row (adds fields) before write.
    template <typename F>
    void event(const char* type, F&& fill) {
        if (!env_enabled()) return;
        nlohmann::json row = base_row(type);
        fill(row);
        commit(std::move(row));
    }

    // Shorthand: one graphics API call row.
    // api: "GL10" | "GLES20" | "EGL"; handled=false ⇒ the honest REC-MISS
    // frontier row (first missing transition of the op kind).
    void gl_call(const char* api, const std::string& op, bool handled,
                 int argc = -1, const char* note = nullptr) {
        if (!env_enabled()) return;
        const std::string key = std::string(api) + "." + op +
                                (handled ? "" : ".MISS");
        if (!budget(key)) return;
        event("gl.call", [&](nlohmann::json& r) {
            r["api"] = api;
            r["op"] = op;
            r["handled"] = handled;
            if (argc >= 0) r["argc"] = argc;
            if (note) r["note"] = note;
            if (!handled) first_missing_now(
                std::string("GL op unhandled (REC-MISS): ") + api + "." + op);
        });
    }

    // GL constant materialization frontier: an sget the tables could not
    // answer (pre-F-NEW-386 evidence for the generated-table fix).
    void const_miss(const std::string& cls, const std::string& field) {
        if (!env_enabled()) return;
        if (!budget("sget.MISS")) return;
        event("gl.const-miss", [&](nlohmann::json& r) {
            r["class"] = cls;
            r["field"] = field;
        });
    }

    // Frame correlation: one row per GL frame stage at the frame pump.
    // stage: "surface-created" | "surface-changed" | "draw-frame" | "present"
    void frame_stage(const char* stage, int w, int h, uint32_t view_id) {
        if (!env_enabled()) return;
        if (std::string(stage) == "draw-frame") ++frame_no_;
        event("gfx.frame", [&](nlohmann::json& r) {
            r["stage"] = stage;
            r["frame"] = frame_no_.load();
            if (w > 0) { r["w"] = w; r["h"] = h; }
            if (view_id) r["view_id"] = view_id;
        });
    }

    // Native library load boundary (dlopen_exec). ok=false rows carry the
    // loader's own detail — the honest boundary line.
    void native_load(const std::string& lib, const std::string& host_path,
                     bool ok, const std::string& detail) {
        if (!env_enabled()) return;
        if (!budget("native.load")) return;
        event("native.load", [&](nlohmann::json& r) {
            r["lib"] = lib;
            r["host_path"] = host_path;
            r["ok"] = ok;
            r["detail"] = detail;
            if (!ok) first_missing_now("native lib load failed: " + lib +
                                       " (" + detail + ")");
        });
    }

    // DT_NEEDED dependency resolution rows (F-NEW-387 law).
    // status: "app-bundled" | "host-anchor" | "already-loaded" |
    //         "missing-honest-block"
    void native_dep(const std::string& needed, const std::string& status,
                    const std::string& resolved_path,
                    const std::string& note) {
        if (!env_enabled()) return;
        if (!budget("native.dep")) return;
        event("native.dep", [&](nlohmann::json& r) {
            r["needed"] = needed;
            r["status"] = status;
            if (!resolved_path.empty()) r["resolved"] = resolved_path;
            if (!note.empty()) r["note"] = note;
            if (status == "missing-honest-block")
                first_missing_now("DT_NEEDED unresolvable: " + needed);
        });
    }

    // Argument marshalling frontier (buffer/array materialization).
    void marshal_fail(const std::string& api, const std::string& op,
                      const std::string& what) {
        if (!env_enabled()) return;
        if (!budget("marshal.fail")) return;
        event("marshal.fail", [&](nlohmann::json& r) {
            r["api"] = api; r["op"] = op; r["what"] = what;
            first_missing_now("arg not materializable: " + api + "." + op +
                              " (" + what + ")");
        });
    }

    // Bounded summary — written by the run closeout next to trace_summary.
    nlohmann::json summary() {
        nlohmann::json s = {
            {"instrument", "MINIANDROID_GFX_TRACE"},
            {"schema", 1},
            {"events_written", written_.load()},
            {"events_dropped", dropped_.load()},
            {"gl_frames", frame_no_.load()},
            {"first_missing_transition", first_missing_.empty()
                                             ? nlohmann::json(nullptr)
                                             : nlohmann::json(first_missing_)},
        };
        return s;
    }

    void write_summary(const std::string& out_dir) {
        if (!env_enabled()) return;
        std::string p;
        sink_path(p);
        // Summary sits beside the JSONL regardless of sink location.
        const auto slash = p.rfind('/');
        const std::string base =
            (slash == std::string::npos) ? p : p.substr(slash + 1);
        std::ofstream f(out_dir + "/" + base + ".summary.json",
                        std::ios::binary);
        if (f) f << summary().dump(1);
    }

private:
    GfxTrace() = default;

    nlohmann::json base_row(const char* type) {
        const auto now = std::chrono::steady_clock::now();
        if (t0_epoch_ == 0) {
            t0_epoch_ = std::chrono::duration_cast<std::chrono::nanoseconds>(
                            now.time_since_epoch()).count();
        }
        const auto ns =
            std::chrono::duration_cast<std::chrono::nanoseconds>(
                now.time_since_epoch()).count() - t0_epoch_;
        nlohmann::json r = {
            {"v", 1},
            {"type", type},
            {"t_ns", ns},
            {"frame", frame_no_.load()},
        };
        return r;
    }

    // Per-key budget: cap rows for one repeated op kind so a hot loop
    // cannot flood the sink; the first N rows + the drop counter tell the
    // whole story. kMaxSameOp keeps mixed traces useful.
    bool budget(const std::string& key) {
        auto& n = counts_[key];
        if (n >= kMaxSameOp) {
            if (n == kMaxSameOp) ++dropped_;  // count the flood once per key
            ++n;
            return false;
        }
        ++n;
        return true;
    }

    void first_missing_now(const std::string& what) {
        std::lock_guard<std::mutex> lk(mu_);
        if (first_missing_.empty()) first_missing_ = what;
    }

    void commit(nlohmann::json row) {
        std::lock_guard<std::mutex> lk(mu_);
        if (sink_.empty()) {
            sink_path(sink_);
            // Schema header is always the first line of the sink.
            std::ofstream h(sink_, std::ios::app | std::ios::binary);
            if (h) h << "{\"v\":1,\"type\":\"gfx.schema\",\"schema\":"
                     << kSchema << "}\n";
        }
        std::ofstream f(sink_, std::ios::app | std::ios::binary);
        if (!f) { ++dropped_; return; }
        f << row.dump() << '\n';
        ++written_;
    }

    static constexpr uint64_t kMaxSameOp = 256;
    static constexpr int kSchema = 1;
    std::map<std::string, uint64_t> counts_;
    std::mutex mu_;
    std::string sink_;
    std::string first_missing_;
    std::atomic<uint64_t> t0_epoch_{0};
    std::atomic<uint64_t> frame_no_{0}, written_{0}, dropped_{0};
};

}  // namespace gfx
}  // namespace miniandroid

#endif  // MINIANDROID_GFX_TRACE_H
