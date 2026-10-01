// S135 — VISUAL RUNTIME BOOT/TRACE LOGGER — canonical runtime event model.
//
// ONE RUNTIME EVENT BACKBONE (S135 §23): every runtime subsystem reports
// through TraceEngine::runtime_event() with this canonical schema. Sinks:
//   (1) terminal log   (default INFO/WARN/ERROR/FRONTIER; heavy events only
//                       under MINIANDROID_TRACE_VERBOSE=1)
//   (2) trace.jsonl    (streaming, machine-readable, one JSON object/line)
//   (3) ring buffer    (last N=512 events, exception-safe tail)
//   (4) stage machine  (BOOT→APK→DEX→CLASSINIT→LIFECYCLE→VIEWTREE→MEASURE→
//                       LAYOUT→DRAW→FRAME + FIRST-DIVERGENCE engine)
//   (5) visual overlay (diagnostics/trace_overlay — composed AFTER the
//                       authoritative frame; never an app pixel owner)
//   (6) evidence bundle(trace_summary.json / sha256.json / screenshot_metrics)
//
// Event vocabulary is CURATED (S135 §3): only events that have real
// emission points in this runtime are canonical here — no blind stubs.
#ifndef MINIANDROID_RUNTIME_EVENT_H
#define MINIANDROID_RUNTIME_EVENT_H

#include <cstdint>
#include <string>
#include <vector>

#include "../../third_party/nlohmann_json/include/nlohmann/json.hpp"

namespace miniandroid {
namespace diagnostics {

// ── Canonical event names (the only strings the overlay stage machine
//    understands; everything else is pass-through evidence) ──────────────
namespace ev {
    // boot / pipeline
    constexpr const char* RUN_START       = "RUN_START";
    constexpr const char* RUN_END         = "RUN_END";
    constexpr const char* APK_LOADED      = "APK_LOADED";
    constexpr const char* APK_LOAD_FAILURE= "APK_LOAD_FAILURE";
    constexpr const char* MANIFEST_PARSED = "MANIFEST_PARSED";
    constexpr const char* DEX_PARSED      = "DEX_PARSED";
    constexpr const char* DEX_FAILURE     = "DEX_FAILURE";
    constexpr const char* RUNTIME_READY   = "RUNTIME_READY";
    constexpr const char* CLASSES_LOADED  = "CLASSES_LOADED";
    // lifecycle (AOSP order)
    constexpr const char* APPLICATION_CREATE = "APPLICATION_CREATE";
    constexpr const char* ACTIVITY_RESOLVED  = "ACTIVITY_RESOLVED";
    constexpr const char* ACTIVITY_ATTACH    = "ACTIVITY_ATTACH";
    constexpr const char* ACTIVITY_CREATE    = "ACTIVITY_CREATE";
    constexpr const char* ACTIVITY_START     = "ACTIVITY_START";
    constexpr const char* ACTIVITY_RESUME    = "ACTIVITY_RESUME";
    constexpr const char* ACTIVITY_PAUSE     = "ACTIVITY_PAUSE";
    constexpr const char* ACTIVITY_STOP      = "ACTIVITY_STOP";
    constexpr const char* ACTIVITY_DESTROY   = "ACTIVITY_DESTROY";
    constexpr const char* LIFECYCLE_STATE    = "LIFECYCLE_STATE";
    // view pipeline
    constexpr const char* CONTENT_VIEW_SET  = "SET_CONTENT_VIEW";
    constexpr const char* VIEWTREE_CREATED  = "VIEWTREE_CREATED";
    constexpr const char* MEASURE_START     = "MEASURE_START";
    constexpr const char* MEASURE_END       = "MEASURE_END";
    constexpr const char* LAYOUT_START      = "LAYOUT_START";
    constexpr const char* LAYOUT_END        = "LAYOUT_END";
    constexpr const char* DRAW_START        = "DRAW_START";
    constexpr const char* DRAW_END          = "DRAW_END";
    constexpr const char* RENDER_START      = "RENDER_START";
    constexpr const char* RENDER_OK         = "RENDER_OK";
    constexpr const char* RENDER_FAIL       = "RENDER_FAIL";
    // frame / capture
    constexpr const char* FRAME_SUBMIT      = "FRAME_SUBMIT";
    constexpr const char* FRAME_CAPTURE     = "FRAME_CAPTURE";
    constexpr const char* FRAME_ANALYSIS    = "FRAME_ANALYSIS";
    // surfaces / GL / WebView / Compose / resources
    constexpr const char* SURFACE_CREATED   = "SURFACE_CREATED";
    constexpr const char* SURFACE_CHANGED   = "SURFACE_CHANGED";
    constexpr const char* GL_FRAME_PRESENT  = "GL_FRAME_PRESENT";
    constexpr const char* WEBVIEW_CREATED   = "WEBVIEW_CREATED";
    constexpr const char* NAVIGATION_START  = "NAVIGATION_START";
    constexpr const char* DOCUMENT_RECEIVED = "DOCUMENT_RECEIVED";
    constexpr const char* JS_EXECUTION      = "JS_EXECUTION";
    constexpr const char* COMPOSITOR_SUBMIT = "COMPOSITOR_SUBMIT";
    constexpr const char* COMPOSE_FRAME     = "COMPOSE_FRAME";
    constexpr const char* RESOURCE_RESOLVED = "RESOURCE_RESOLVED";
    constexpr const char* RESOURCE_DECODED  = "RESOURCE_DECODED";
    constexpr const char* RESOURCE_FAILURE  = "RESOURCE_FAILURE";
    // VM / failure frontier
    constexpr const char* EXCEPTION         = "EXCEPTION";
    constexpr const char* MISSING_API       = "MISSING_API";
    constexpr const char* NATIVE_CALL       = "NATIVE_CALL";
    constexpr const char* DISPATCH_FAILURE  = "DISPATCH_FAILURE";
    constexpr const char* CLASS_INIT_FAILURE= "CLASS_INIT_FAILURE";
    constexpr const char* SCHED_STALL       = "SCHED_STALL";
    constexpr const char* TRACE_MARK        = "TRACE_MARK";   // generic frontier marker
}

// ── Renderer families (S135 §14) ─────────────────────────────────────────
namespace rf {
    constexpr const char* CLASSIC_CANVAS = "CLASSIC_CANVAS";
    constexpr const char* SURFACE_VIEW   = "SURFACE_VIEW";
    constexpr const char* OPENGL_GLES    = "OPENGL_GLES";
    constexpr const char* COMPOSE        = "COMPOSE";
    constexpr const char* WEBVIEW        = "WEBVIEW";
    constexpr const char* LIBGDX         = "LIBGDX";
    constexpr const char* NATIVE         = "NATIVE";
    constexpr const char* UNKNOWN        = "UNKNOWN";
}

// Severity drives overlay color semantics (S135 §4):
//   GREEN=confirmed, YELLOW=started/pending, RED=failure/divergence,
//   BLUE=informational, PURPLE=renderer/provenance, GRAY=not reached.
enum class EventSev {
    CONFIRMED,   // stage/event completed with evidence
    PENDING,     // started, not yet confirmed (frontier candidate)
    FAILURE,     // exception / divergence / failure
    INFO,        // informational
    RENDERER,    // renderer/provenance observation
    NOT_REACHED, // canonical stage never started (assigned at finalize)
};

const char* event_sev_name(EventSev s);

// One canonical runtime event. Fields default empty (omitted in JSON) —
// never guessed (S135 §15/§16: descriptor authoritative; UNKNOWN not invented).
struct RuntimeEvent {
    uint64_t    seq = 0;
    uint64_t    timestamp_ms = 0;
    std::string run_id;
    std::string package;          // apk package name
    std::string activity;         // current activity class (best effort)
    std::string thread;           // "main" unless known otherwise
    std::string component;        // boot|activity|viewtree|render|surface|webview|compose|resource|vm|capture
    std::string event;            // canonical name (ev::*)
    std::string cls;              // source class (apk or runtime)
    std::string method;
    std::string descriptor;       // kept authoritative — no rename guessing
    std::string renderer_family;  // rf::*
    std::string state;            // state snapshot ("RESUMED", "1080x1920", ...)
    std::string provenance;       // source/provenance hint
    std::string result;           // OK|FAIL|PENDING|SKIPPED
    std::string exception;        // exception class + message
    uint64_t    parent_event = 0; // seq of parent event
    EventSev    sev = EventSev::INFO;

    // Cross-layer correlation ids (S135 §13): frame_id/view_id/resource_id/
    // task_id ... arbitrary but machine-readable.
    nlohmann::json extra;

    nlohmann::json to_json() const {
        nlohmann::json j;
        j["seq"] = seq;
        j["ts_ms"] = timestamp_ms;
        if (!run_id.empty())          j["run_id"] = run_id;
        if (!package.empty())         j["package"] = package;
        if (!activity.empty())        j["activity"] = activity;
        if (!thread.empty())          j["thread"] = thread;
        if (!component.empty())       j["component"] = component;
        j["event"] = event;
        if (!cls.empty())             j["class"] = cls;
        if (!method.empty())          j["method"] = method;
        if (!descriptor.empty())      j["descriptor"] = descriptor;
        if (!renderer_family.empty()) j["renderer_family"] = renderer_family;
        if (!state.empty())           j["state"] = state;
        if (!provenance.empty())      j["provenance"] = provenance;
        if (!result.empty())          j["result"] = result;
        if (!exception.empty())      j["exception"] = exception;
        if (parent_event != 0)        j["parent_event"] = parent_event;
        j["sev"] = event_sev_name(sev);
        if (!extra.is_null() && !extra.empty()) j["extra"] = extra;
        return j;
    }
};

// ── Canonical stage machine (S135 §12 FIRST-DIVERGENCE engine) ───────────
// The boot contract every APK run is expected to walk, in order:
//   BOOT → APK → DEX → CLASSINIT → LIFECYCLE → VIEWTREE → MEASURE →
//   LAYOUT → DRAW → FRAME
// EXPECTED chain (the §12 example): Activity → setContentView → measure →
// layout → draw → frame submit. The engine derives FIRST_DIVERGENCE from
// observed stage states — never from the last exception.
namespace stage {
    constexpr const char* BOOT      = "BOOT";
    constexpr const char* APK       = "APK";
    constexpr const char* DEX       = "DEX";
    constexpr const char* CLASSINIT = "CLASS-INIT";
    constexpr const char* LIFECYCLE = "LIFECYCLE";
    constexpr const char* VIEWTREE  = "VIEWTREE";
    constexpr const char* MEASURE   = "MEASURE";
    constexpr const char* LAYOUT    = "LAYOUT";
    constexpr const char* DRAW      = "DRAW";
    constexpr const char* FRAME     = "FRAME";
    // Canonical order — index order matters for divergence derivation.
    inline const std::vector<std::string>& canonical_order() {
        static const std::vector<std::string> kOrder = {
            BOOT, APK, DEX, CLASSINIT, LIFECYCLE,
            VIEWTREE, MEASURE, LAYOUT, DRAW, FRAME,
        };
        return kOrder;
    }
}

} // namespace diagnostics
} // namespace miniandroid

#endif // MINIANDROID_RUNTIME_EVENT_H
