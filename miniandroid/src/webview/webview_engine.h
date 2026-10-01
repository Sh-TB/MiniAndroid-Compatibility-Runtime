// S109 WEBVIEW-ENGINE — the HTML5 execution subsystem.
//
// SEMANTIC LAW (Android WebView.java + WHATWG HTML):
// * WebView.loadUrl/loadData deliver a DOCUMENT to a rendering engine that
//   parses HTML into a live DOM, executes scripts (inline during parse,
//   external src= in order), exposes DOM/canvas/timers/storage to JS, and
//   paints the composed page into the view's surface. Input events flow
//   Android → WebView → DOM event listeners.
// * This engine is that missing subsystem for MiniAndroid: a REAL
//   JavaScript engine (QuickJS, ES2020) + real HTML parser + live DOM +
//   Canvas2D raster (canvas2d.h) + timers/rAF event loop + localStorage +
//   pointer/key event dispatch. No package-name gates, no app special
//   cases: every WebView-family node in any APK routes here.
// * Event loop law: JS timers and requestAnimationFrame are driven by the
//   runtime's frame pump (Choreographer vsync ticks); rAF callbacks run
//   before the frame composites, receiving the frame timestamp (ms).
#pragma once
#include "canvas2d.h"
#include "html_dom.h"
#include <map>
#include <memory>
#include <string>
#include <vector>

namespace miniandroid { namespace webview {

class WebViewEngine {
public:
    explicit WebViewEngine(uint32_t view_id);
    ~WebViewEngine();
    WebViewEngine(const WebViewEngine&) = delete;
    WebViewEngine& operator=(const WebViewEngine&) = delete;

    // Load a document (URL recorded for relative resolution; body = HTML).
    // External <script src>/<link>/assets resolve through the APK.
    bool load_document(const std::string& url, const std::string& html,
                       const std::string& apk_path);

    // ── ADDITIONAL-AUDIT P1-11: WebView.evaluateJavascript law ───────
    // Android WebView.evaluateJavascript(script, callback): the script
    // evaluates in the PAGE's global scope (full DOM/canvas/timer access,
    // same realm as the document's own scripts); the callback receives the
    // result JSON-ENCODED ("null" for undefined and for script exceptions).
    // Returns false only when the evaluation could not run (exception);
    // json_out carries the callback payload either way. Async work the
    // script schedules drains through the S118 JOB-PUMP law (bounded).
    bool evaluate_javascript(const std::string& script, std::string* json_out,
                             std::string* error_out = nullptr);

    // Frame pump: fire due timers, then run pending rAF callbacks.
    void tick(double frame_ms);
    bool needs_frames() const;

    // Composite DOM + canvases into dst (w*h*4 bytes RGBA, row stride 4w).
    void render(uint8_t* dst, int w, int h);

    // Input (view-local coordinates). Returns whether a listener ran.
    bool pointer_event(int x, int y, const std::string& type);
    bool key_event(const std::string& key, const std::string& type,
                   const std::string& action);

    uint32_t view_id() const { return view_id_; }
    const std::string& document_url() const { return url_; }

    // per-engine provenance counters (evidence standard)
    struct Stats {
        size_t scripts_executed = 0;
        size_t dom_nodes = 0;
        size_t draw_calls = 0;
        size_t raf_frames = 0;
        size_t timers_fired = 0;
        size_t events_dispatched = 0;
        size_t events_registered = 0;
        size_t js_errors = 0;
        double script_ms = 0;
    };
    const Stats& stats() const { return stats_; }

public:
    struct Impl;   // defined in webview_engine.cpp (namespace-scope free
                   // functions/thunks need access)
private:
    std::unique_ptr<Impl> impl_;
    uint32_t view_id_;
    std::string url_;
    Stats stats_;
};

// Registry: WebView ViewNode id → engine. The F-085 WebView content law
// routes loadUrl/loadData here; the render walk and frame pump query it.
class WebViewRegistry {
public:
    static WebViewRegistry& instance();
    std::shared_ptr<WebViewEngine> create(uint32_t view_id);
    std::shared_ptr<WebViewEngine> find(uint32_t view_id);
    void tick_all(double frame_ms);
    bool any_needs_frames() const;
    std::vector<std::shared_ptr<WebViewEngine>> all() const;

private:
    std::map<uint32_t, std::shared_ptr<WebViewEngine>> engines_;
};

}} // namespace miniandroid::webview
