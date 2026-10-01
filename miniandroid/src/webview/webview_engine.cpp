// S109 WEBVIEW-ENGINE — implementation. See webview_engine.h for laws.
#include "webview_engine.h"
#include "text_shaper.h"
#include "../resources/resource_runtime.h"
#include "../api/http_client.h"
#include "../third_party/nlohmann_json/include/nlohmann/json.hpp"
#include <openssl/evp.h>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstring>
#include <fstream>
#include <iostream>
#include <sstream>

extern "C" {
#include "../third_party/quickjs/quickjs.h"
}

#include "../../third_party/stb/stb_image.h"

namespace miniandroid { namespace webview {

static std::string lower_s(std::string s) {
    for (auto& c : s) c = char(::tolower((unsigned char)c));
    return s;
}
// S114 camelCase → kebab-case law for CSS property names (CSSOM §6.1:
// style.marginTop writes the margin-top slot). The old code stored the
// concatenated key ("margintop") — every JS game that positioned objects
// through style.marginLeft/marginTop/backgroundSize silently lost them.
static std::string css_key(const std::string& camel) {
    std::string out;
    out.reserve(camel.size() + 4);
    for (char ch : camel) {
        if (ch >= 'A' && ch <= 'Z') { out += '-'; out += char(ch - 'A' + 'a'); }
        else out += ch;
    }
    return out;
}
static std::string upper_s(std::string s) {
    for (auto& c : s) c = char(::toupper((unsigned char)c));
    return s;
}

// ── Image object (new Image()) ──────────────────────────────────────────
struct ImageObj {
    std::unique_ptr<renderer::FrameBuffer> fb;
    std::string src;
    bool complete = false;
    int natural_w = 0, natural_h = 0;
};

static DomNode* el_of(JSValueConst v);
static bool wv_trace();

// QuickJS law: plain C functions are not constructible — `new X()` throws
// "not a constructor". Native constructors must use JS_CFUNC_constructor.
static JSValue make_ctor(JSContext* ctx, JSCFunction f, const char* name, int len) {
    return JS_NewCFunction2(ctx, f, name, len, JS_CFUNC_constructor, 0);
}

// ── QuickJS class ids ───────────────────────────────────────────────────
static JSClassID kElementClass = 0;
static JSClassID kStyleClass = 0;
static JSClassID kCtx2DClass = 0;
static JSClassID kStorageClass = 0;
static JSClassID kPatternClass = 0;
static JSClassID kImageClass = 0;
static JSClassID kGradientClass = 0;

static void noop_finalizer(JSRuntime*, JSValue) {}

static void ctx2d_finalizer(JSRuntime*, JSValue val) {
    // Canvas2D is owned by the canvas DomNode (unique_ptr) — the JS object is
    // a non-owning view. Deleting here double-frees on GC. (S109 lesson.)
    (void)val;
}
static void image_finalizer(JSRuntime*, JSValue val) {
    // ImageObj is owned by Impl::owned_images (same non-owning-view law as
    // Canvas2D — a GC finalizer delete double-frees). (S109 lesson #2.)
    (void)val;
}

// forward
static renderer::FrameBuffer* canvas_bitmap_of(DomNode* n);

// ── engine impl ─────────────────────────────────────────────────────────
struct WebViewEngine::Impl {
    WebViewEngine* self = nullptr;
    JSRuntime* rt = nullptr;
    JSContext* ctx = nullptr;
    ParsedDocument doc;
    std::vector<CssRule> css_rules;
    std::map<std::string, std::string> custom_props;
    std::string apk_path;
    double viewport_w = 1080, viewport_h = 1920;

    std::map<DomNode*, JSValue> el_objs;
    JSValue window_obj = JS_UNDEFINED;
    JSValue document_obj = JS_UNDEFINED;
    JSValue storage_obj = JS_UNDEFINED;
    std::map<DomNode*, std::map<std::string, std::vector<JSValue>>> listeners;
    // S114: compiled inline event attributes (onclick= …), keyed by
    // (node, attr-name) hash — compile-once, invoked per dispatch
    std::map<uint64_t, JSValue> inline_handlers;

    struct Timer { double due_ms; double interval; JSValue func; bool repeated; };
    std::map<int, Timer> timers;
    std::map<int, std::vector<JSValue>> timer_args_;
    int next_timer_id = 1;
    std::vector<std::pair<JSValue, double>> raf_queue;
    double now_ms = 0;
    uint32_t rng_state = 0x9e3779b9;
    bool kv_dirty = false;

    std::map<std::string, std::string> kv;
    std::string kv_path;

    std::unique_ptr<renderer::FrameBuffer> surface;
    bool page_error = false;
    bool layout_dirty = true;
    bool painted_once = false;           // S118: first paint establishes the boxes

    // S118 FORCED SYNCHRONOUS LAYOUT law (HTML rendering §reflow):
    // getBoundingClientRect()/offsetWidth reads must reflect CURRENT layout.
    // Scripts that measure geometry from DOMContentLoaded (accelerace's
    // CarView) run before any paint — the old engine answered zero boxes
    // and every derived position was garbage. A geometry read before the
    // first paint runs the render pipeline once into a scratch buffer
    // (idempotent, deterministic) so the boxes exist.
    void sync_layout_if_needed() {
        if (painted_once || !self) return;
        int w = int(viewport_w), h = int(viewport_h);
        if (w <= 0 || h <= 0) return;
        std::vector<uint8_t> scratch(size_t(w) * size_t(h) * 4, 0);
        self->render(scratch.data(), w, h);
    }

    // ── S113 CSS layout/paint state ─────────────────────────────────────
    int css_viewport_w = -1;              // last width used for @media evaluation
    std::vector<CssRule> active_rules;    // media-filtered rules for the current viewport
    std::map<std::string, int> font_family_map;   // lowercased @font-face family → face idx
    struct CachedImg { int w = 0, h = 0; std::vector<renderer::RGBA> px; bool ok = false; };
    std::map<std::string, CachedImg> img_cache;

    // ── S133 RESOURCE FORENSICS ────────────────────────────────────────
    // One record per external resource fetch (script/style/font/image),
    // network OR asset — the browser resource table. Dumped to
    // $WV_DIAG_DIR/webview_resource_trace.json when WV_DIAG is set.
    struct ResourceRecord {
        int request_id = 0;
        std::string url;            // requested ref (as written / resolved)
        std::string final_url;      // post-redirect (network fetches)
        std::string type;           // script|style|font|image|other
        int status = 0;             // HTTP status, 200 = asset ok, 0 = failure
        size_t bytes = 0;
        std::string source;         // network|mininet-http|apk-asset|none
        std::string consumer;       // script-exec|stylesheet|font-face|img-src
        std::string error;          // non-empty => failure reason
        double ms = 0;
    };
    std::vector<ResourceRecord> resources;
    int next_request_id = 1;
    void record_resource(ResourceRecord r) {
        r.request_id = next_request_id++;
        resources.push_back(std::move(r));
        std::cerr << "[WV-RES] #" << resources.back().request_id
                  << " type=" << resources.back().type
                  << " status=" << resources.back().status
                  << " bytes=" << resources.back().bytes
                  << " src=" << resources.back().source
                  << " consumer=" << resources.back().consumer
                  << " url=" << resources.back().url.substr(0, 100)
                  << (resources.back().error.empty()
                          ? "" : (" ERR=" + resources.back().error))
                  << std::endl;
    }
    void dump_resource_trace() {
        const char* dir = getenv("WV_DIAG_DIR");
        if (!getenv("WV_DIAG") || !dir || !*dir) return;
        nlohmann::json j = nlohmann::json::array();
        for (auto& r : resources) {
            j.push_back({{"request_id", r.request_id}, {"url", r.url},
                         {"final_url", r.final_url}, {"type", r.type},
                         {"status", r.status}, {"bytes", r.bytes},
                         {"source", r.source}, {"consumer", r.consumer},
                         {"error", r.error}, {"ms", r.ms}});
        }
        std::string doc_url = self ? self->document_url() : "";
        nlohmann::json out = {{"document_url", doc_url},
                              {"resource_count", resources.size()},
                              {"resources", j}};
        std::string path = std::string(dir) + "/webview_resource_trace.json";
        std::ofstream f(path);
        if (f) { f << out.dump(1) << std::endl;
                 std::cerr << "[WV-DIAG] resource trace → " << path << std::endl; }
    }

    double now() const { return now_ms; }
    WebViewEngine::Stats stats;
    // createElement/parse ownership bridge: node ptr → owning unique_ptr until
    // adopted by a parent in the tree.
    std::vector<std::pair<DomNode*, std::unique_ptr<DomNode>>> orphans;
    std::vector<DomNode*> canvas_nodes;
    size_t sum_draw_calls() const {
        size_t s = 0;
        for (auto* n : canvas_nodes)
            if (n->canvas) s += n->canvas->draw_calls;
        return s;
    }
    std::vector<Pattern*> owned_patterns;
    std::vector<ImageObj*> owned_images;

    ~Impl() {
        dump_resource_trace();   // S133 resource forensics (gated: WV_DIAG)
        for (auto& [n, m] : listeners)
            for (auto& [t, v] : m)
                for (auto& f : v) JS_FreeValue(ctx, f);
        for (auto& [id, t] : timers) JS_FreeValue(ctx, t.func);
        for (auto& [f, ts] : raf_queue) JS_FreeValue(ctx, f);
        for (auto& [n, v] : el_objs) JS_FreeValue(ctx, v);
        for (auto* p : owned_patterns) delete p;
        for (auto* im : owned_images) delete im;
        // JS_FreeContext/JS_FreeRuntime at process exit re-enters GC
        // finalization over engine-owned C++ objects — a teardown-order
        // hazard that aborts. The engine's lifetime == process lifetime,
        // so the OS reclaims the JS heap: intentional leak-at-exit
        // (documented deviation, standard embedder practice).
        (void)window_obj; (void)document_obj; (void)storage_obj;
        (void)ctx; (void)rt;
    }

    static JS_BOOL interrupt_cb(JSRuntime*, void* opaque) {
        auto* dl = (std::chrono::steady_clock::time_point*)opaque;
        return std::chrono::steady_clock::now() > *dl ? 1 : 0;
    }
    void set_deadline(double seconds) {
        dl_ = std::chrono::steady_clock::now() +
              std::chrono::duration_cast<std::chrono::steady_clock::duration>(
                  std::chrono::duration<double>(seconds));
        JS_SetInterruptHandler(rt, interrupt_cb, &dl_);
    }

    void report_exception(const std::string& where) {
        JSValue exc = JS_GetException(ctx);
        stats.js_errors++;
        const char* msg = JS_ToCString(ctx, exc);
        std::cerr << "[WV-ERROR] " << where << ": " << (msg ? msg : "(exception)")
                  << std::endl;
        if (msg) JS_FreeCString(ctx, msg);
        // position info (QuickJS stores it when debug info is present)
        for (const char* prop : {"lineNumber", "columnNumber"}) {
            JSValue v = JS_GetPropertyStr(ctx, exc, prop);
            if (JS_IsNumber(v)) {
                double d = -1; JS_ToFloat64(ctx, &d, v);
                std::cerr << "[WV-ERROR]   " << prop << "=" << long(d) << std::endl;
            }
            JS_FreeValue(ctx, v);
        }
        JSValue stack = JS_GetPropertyStr(ctx, exc, "stack");
        if (!JS_IsUndefined(stack) && !JS_IsException(stack)) {
            const char* st = JS_ToCString(ctx, stack);
            if (st && *st) std::cerr << "[WV-ERROR] stack: " << st << std::endl;
            if (st) JS_FreeCString(ctx, st);
        }
        JS_FreeValue(ctx, stack);
        JS_FreeValue(ctx, exc);
    }

    bool exec_script(const std::string& code, const std::string& name,
                     bool is_module = false) {
        if (code.empty()) return false;
        set_deadline(20.0);  // hang guard: no infinite loop stalls the runtime
        auto t0 = std::chrono::steady_clock::now();
        // S133 ES-MODULE law (WHATWG HTML §4.12.21): type=module code parses
        // with module goals — import/export allowed, top-level `this` is
        // undefined, the module is evaluated through QuickJS's module system
        // (module loader resolves static and dynamic import() specifiers).
        int flags = is_module ? JS_EVAL_TYPE_MODULE : JS_EVAL_TYPE_GLOBAL;
        JSValue r = JS_Eval(ctx, code.c_str(), code.size(), name.c_str(), flags);
        stats.script_ms += std::chrono::duration<double, std::milli>(
            std::chrono::steady_clock::now() - t0).count();
        bool ok = !JS_IsException(r);
        JS_FreeValue(ctx, r);
        if (!ok) report_exception("script " + name);
        else stats.scripts_executed++;
        return ok;
    }

    // ── URL/asset law ──────────────────────────────────────────────────
    // S117: RFC 3986 §5.2.4 remove_dot_segments law. Real browsers resolve a
    // relative ref ("./style.css", "../img/x.png", "a//b.html") against the
    // document base URL and NORMALIZE dot segments before any fetch; the raw
    // string join produced entries like "assets/./style.css" that never match
    // the APK zip directory, silently dropping every external stylesheet and
    // script that used a "./"-prefixed href (org.asafonov.weather rendered a
    // blank window: CSS 9KB + JS 25KB both unreached). One choke point covers
    // every external ref family: scripts, stylesheets, images, @font-face.
    static std::string normalize_dot_segments(std::string p) {
        if (p.find("://") != std::string::npos) return p;              // scheme'd URL
        bool abs = !p.empty() && p[0] == '/';
        std::vector<std::string> out;
        size_t i = 0;
        while (i < p.size()) {
            size_t j = p.find('/', i);
            std::string seg = p.substr(i, (j == std::string::npos ? p.size() : j) - i);
            i = (j == std::string::npos) ? p.size() : j + 1;
            if (seg.empty() || seg == ".") continue;                    // drop "//", "."
            if (seg == "..") { if (!out.empty()) out.pop_back(); continue; }
            out.push_back(seg);
        }
        std::string r = abs ? "/" : "";
        for (size_t k = 0; k < out.size(); ++k) { if (k) r += "/"; r += out[k]; }
        return r;
    }
    std::string url_dir() const {
        std::string u = self->document_url();
        // S133 WEB-001 fan-out: an http(s) document base resolves relative
        // refs against its own directory (RFC 3986 §5.2 relative transform)
        // — NOT against the APK asset root.
        if (u.rfind("http://", 0) == 0 || u.rfind("https://", 0) == 0) {
            size_t slash = u.rfind('/');
            if (slash != std::string::npos && u.find("://", 0) + 2 < slash)
                return u.substr(0, slash + 1);
            return u;   // no path segment ("https://host") — base is the URL
        }
        if (u.rfind("assets/", 0) == 0) {
            size_t slash = u.rfind('/');
            if (slash != std::string::npos && slash >= 7) return u.substr(0, slash + 1);
        }
        return "assets/";
    }
    std::string resolve_url(const std::string& ref) const {
        if (ref.empty()) return ref;
        if (ref.rfind("file:///android_asset/", 0) == 0)
            return "assets/" + ref.substr(strlen("file:///android_asset/"));
        if (ref.rfind("http://", 0) == 0 || ref.rfind("https://", 0) == 0) return ref;
        // already-resolved asset-root form — idempotent (module names flow
        // through resolve_url multiple times: exec_script, loader, fetch)
        if (ref.rfind("assets/", 0) == 0) return ref;
        if (ref.rfind("//", 0) == 0) return "https:" + ref;   // scheme-relative law
        if (ref.rfind("/assets/", 0) == 0) return ref.substr(1);
        if (ref[0] == '/') {
            // Root-relative: against an http(s) base it's scheme+host+ref.
            std::string u = self->document_url();
            if (u.rfind("http://", 0) == 0 || u.rfind("https://", 0) == 0) {
                size_t host_end = u.find("://", 0);
                size_t path0 = u.find('/', host_end + 3);
                if (path0 == std::string::npos) return u + ref.substr(1);
                return u.substr(0, path0) + ref;
            }
            return "assets" + ref;   // app-root-relative
        }
        return url_dir() + ref;
    }
    // S133: classify an external ref by consumer context (resource table).
    static const char* resource_type_of(const char* consumer, const std::string& ref) {
        std::string low = ref;
        std::transform(low.begin(), low.end(), low.begin(),
                       [](unsigned char c) { return char(::tolower(c)); });
        if (consumer && std::string(consumer) == "font-face") return "font";
        if (consumer && std::string(consumer) == "stylesheet") return "style";
        if (consumer && (std::string(consumer) == "script-exec" ||
                         std::string(consumer) == "module-import")) return "script";
        if (low.find(".js") != std::string::npos || low.find(".mjs") != std::string::npos)
            return "script";
        if (low.find(".css") != std::string::npos) return "style";
        if (low.find(".png") != std::string::npos) return "image";
        if (low.find(".jpg") != std::string::npos || low.find(".jpeg") != std::string::npos ||
            low.find(".webp") != std::string::npos || low.find(".gif") != std::string::npos ||
            low.find(".svg") != std::string::npos || low.find(".ico") != std::string::npos)
            return "image";
        return "other";
    }
    // S133 NETWORK RESOURCE LAW: fetch_asset gains the network tier. An
    // http(s) ref (absolute, or relative against an http(s) document base)
    // fetches through mininet::http_get — the SAME S100 NET-001 substrate
    // WEB-001 uses for the top-level document. Asset refs keep the APK
    // path. Every fetch lands in the resource forensics table.
    std::vector<uint8_t> fetch_resource(const std::string& ref, const char* consumer) {
        ResourceRecord rec;
        rec.url = ref;
        rec.type = resource_type_of(consumer, ref);
        rec.consumer = consumer ? consumer : "other";
        std::string entry = resolve_url(ref);
        size_t q = entry.find_first_of("?#");
        std::string bare = q == std::string::npos ? entry : entry.substr(0, q);
        bool is_http = bare.rfind("http://", 0) == 0 || bare.rfind("https://", 0) == 0;
        std::vector<uint8_t> out;
        auto t0 = std::chrono::steady_clock::now();
        if (is_http) {
            mininet::HttpResponse hr = mininet::http_get(bare, 5, 20000);
            rec.ms = std::chrono::duration<double, std::milli>(
                         std::chrono::steady_clock::now() - t0).count();
            rec.final_url = hr.final_url;
            rec.status = hr.status;
            rec.source = "mininet-http";
            if (!hr.ok()) rec.error = hr.error.empty()
                ? ("http status " + std::to_string(hr.status)) : hr.error;
            else {
                out.assign(hr.body.begin(), hr.body.end());
                rec.bytes = out.size();
            }
        } else {
            entry = normalize_dot_segments(bare);
            if (!apk_path.empty() &&
                resources::ResourceRuntime::instance().ensure_loaded(apk_path)) {
                auto bytes =
                    resources::ResourceRuntime::instance().apk().extract_entry_cached(entry);
                rec.status = bytes.empty() ? 0 : 200;
                rec.source = bytes.empty() ? "none" : "apk-asset";
                if (bytes.empty()) rec.error = "asset missing: " + entry;
                else { out = std::move(bytes); rec.bytes = out.size(); }
            } else {
                rec.error = "no apk context";
            }
        }
        record_resource(std::move(rec));
        return out;
    }
    // Legacy asset-only path retained for non-resource lookups.
    std::vector<uint8_t> fetch_asset(const std::string& ref) {
        std::string entry = resolve_url(ref);
        size_t q = entry.find_first_of("?#");
        if (q != std::string::npos) entry.erase(q);
        entry = normalize_dot_segments(entry);   // S117 RFC 3986 §5.2.4 law
        if (apk_path.empty()) return {};
        if (!resources::ResourceRuntime::instance().ensure_loaded(apk_path)) return {};
        return resources::ResourceRuntime::instance().apk().extract_entry_cached(entry);
    }

    JSValue get_element_js(DomNode* n);
    void dispatch(DomNode* target, const std::string& type, JSValue ev);

    void load_persisted_kv() {
        if (kv_path.empty()) return;
        std::ifstream f(kv_path);
        if (!f) return;
        try {
            nlohmann::json j;
            f >> j;
            if (j.is_object())
                for (auto it = j.begin(); it != j.end(); ++it)
                    if (it.value().is_string()) kv[it.key()] = it.value().get<std::string>();
        } catch (...) {}
    }
    void persist_kv() {
        if (kv_path.empty()) return;
        try {
            nlohmann::json j = nlohmann::json::object();
            for (auto& [k, v] : kv) j[k] = v;
            std::ofstream f(kv_path);
            f << j.dump();
        } catch (...) {}
    }

    void setup_bindings();
    void run_scripts();
    // S118 JOB-PUMP law: async continuations live on the QuickJS job queue;
    // the embedder owns the loop. Bounded drain keeps 3-run determinism.
    int drain_pending_jobs(int bound) {
        if (!rt) return 0;
        JSContext* jx = nullptr;
        int n = 0;
        while (n < bound && JS_ExecutePendingJob(rt, &jx) > 0) ++n;
        return n;
    }
    void compute_layout();
    DomNode* body() const {
        // S113 law: the parser nests a real <html> element INSIDE the root
        // holder (the parse() root is a synthetic holder), so <body> is NOT
        // a direct child — search recursively (ROOT-051 find_body law).
        std::function<DomNode*(DomNode*)> find = [&](DomNode* n) -> DomNode* {
            for (auto& c : n->children) {
                if (c->tag == "body") return c.get();
                if (auto* r = find(c.get())) return r;
            }
            return nullptr;
        };
        if (auto* b = find(doc.root.get())) return b;
        return doc.root.get();
    }

private:
    std::chrono::steady_clock::time_point dl_;
};

// ── style object: exotic class with C++-map-backed properties ──────────
static int style_get_own_property(JSContext* ctx, JSPropertyDescriptor* desc,
                                  JSValueConst this_obj, JSAtom prop) {
    auto* n = (DomNode*)JS_GetOpaque(this_obj, kStyleClass);
    if (!n) return false;
    const char* name = JS_AtomToCString(ctx, prop);
    if (!name) return false;
    std::string key = css_key(name);
    JS_FreeCString(ctx, name);
    if (key == "cssText") {
        if (desc) {
            std::string css;
            for (auto& kv : n->style) css += kv.first + ":" + kv.second + ";";
            desc->flags = JS_PROP_WRITABLE;
            desc->value = JS_NewString(ctx, css.c_str());
        }
        return true;
    }
    auto it = n->style.find(key);
    if (it == n->style.end()) return false;
    if (desc) {
        desc->flags = JS_PROP_WRITABLE;
        desc->value = JS_NewString(ctx, it->second.c_str());
    }
    return true;
}
static int style_define_own_property(JSContext* ctx, JSValueConst this_obj,
                                     JSAtom prop, JSValueConst val,
                                     JSValueConst getter, JSValueConst setter, int flags) {
    auto* n = (DomNode*)JS_GetOpaque(this_obj, kStyleClass);
    if (!n) return true;
    // tagged-int atoms (array-index writes) serialize as digit strings via
    // JS_AtomToCString — route them to the default path (public API has no
    // JS_AtomIsTaggedInt; the digit heuristic is exact for index atoms).
    {
        const char* raw = JS_AtomToCString(ctx, prop);
        if (raw) {
            bool is_index = raw[0] >= '0' && raw[0] <= '9';
            JS_FreeCString(ctx, raw);
            if (is_index) return false;
        }
    }
    const char* name = JS_AtomToCString(ctx, prop);
    if (!name) return true;
    std::string key = css_key(name);
    JS_FreeCString(ctx, name);
    // C-defined methods and internal slots take the DEFAULT path — swallowing
    // them broke the object invariants (setProperty vanished, GC abort).
    if (key == "setproperty" || key == "removeproperty" || key == "csstext" ||
        key.rfind("__", 0) == 0)
        return false;
    if (JS_VALUE_GET_TAG(val) != JS_TAG_STRING) return false;  // only CSS strings
    const char* v = JS_ToCString(ctx, val);
    if (v) {
        n->style[key] = v;
        n->inline_keys.insert(key);   // S114: JS writes outrank stylesheet rules
        if (key == "display") n->display_none = (std::string(v) == "none");
        JS_FreeCString(ctx, v);
        return true;
    }
    return false;
}
static void register_js_classes(JSRuntime* rt);
static JSValue grad_addColorStop(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv);
// ── classList: real object with add/remove/toggle/contains/item ─────────
static void classlist_read(DomNode* n, std::vector<std::string>& out) {
    auto it = n->attrs.find("class");
    if (it == n->attrs.end()) return;
    std::istringstream ss(it->second);
    std::string tok;
    while (ss >> tok) out.push_back(tok);
}
static void classlist_write(DomNode* n, const std::vector<std::string>& toks) {
    std::string v;
    for (auto& t : toks) { if (!v.empty()) v += ' '; v += t; }
    if (v.empty()) n->attrs.erase("class"); else n->attrs["class"] = v;
}
static JSValue cl_add(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    if (wv_trace()) std::cerr << "[WV-T] classList.add" << std::endl;
    auto* n = (DomNode*)JS_GetOpaque(this_v, kElementClass);
    if (n) {
        std::vector<std::string> toks; classlist_read(n, toks);
        for (int i = 0; i < argc; ++i) {
            const char* s = JS_ToCString(ctx, argv[i]);
            if (s) {
                if (std::find(toks.begin(), toks.end(), s) == toks.end()) toks.push_back(s);
                JS_FreeCString(ctx, s);
            }
        }
        classlist_write(n, toks);
    }
    return JS_UNDEFINED;
}
static JSValue cl_remove(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    if (wv_trace()) std::cerr << "[WV-T] classList.remove" << std::endl;
    auto* n = (DomNode*)JS_GetOpaque(this_v, kElementClass);
    if (n) {
        std::vector<std::string> toks; classlist_read(n, toks);
        for (int i = 0; i < argc; ++i) {
            const char* s = JS_ToCString(ctx, argv[i]);
            if (s) {
                toks.erase(std::remove(toks.begin(), toks.end(), s), toks.end());
                JS_FreeCString(ctx, s);
            }
        }
        classlist_write(n, toks);
    }
    return JS_UNDEFINED;
}
static JSValue cl_toggle(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* n = (DomNode*)JS_GetOpaque(this_v, kElementClass);
    bool now_on = false;
    if (n && argc >= 1) {
        const char* s = JS_ToCString(ctx, argv[0]);
        if (s) {
            std::vector<std::string> toks; classlist_read(n, toks);
            auto it = std::find(toks.begin(), toks.end(), s);
            if (it != toks.end()) { toks.erase(it); now_on = false; }
            else { toks.push_back(s); now_on = true; }
            JS_FreeCString(ctx, s);
            classlist_write(n, toks);
        }
    }
    return JS_NewBool(ctx, now_on);
}
static JSValue cl_contains(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* n = (DomNode*)JS_GetOpaque(this_v, kElementClass);
    bool has = false;
    if (n && argc >= 1) {
        const char* s = JS_ToCString(ctx, argv[0]);
        if (s) {
            std::vector<std::string> toks; classlist_read(n, toks);
            has = std::find(toks.begin(), toks.end(), s) != toks.end();
            JS_FreeCString(ctx, s);
        }
    }
    return JS_NewBool(ctx, has);
}
static JSValue cl_item(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* n = (DomNode*)JS_GetOpaque(this_v, kElementClass);
    if (n && argc >= 1) {
        int32_t i = 0; JS_ToInt32(ctx, &i, argv[0]);
        std::vector<std::string> toks; classlist_read(n, toks);
        if (i >= 0 && size_t(i) < toks.size()) return JS_NewString(ctx, toks[i].c_str());
    }
    return JS_NULL;
}
static JSValue el_get_class_list2(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    if (wv_trace()) std::cerr << "[WV-T] el.classList" << std::endl;
    auto* n = el_of(this_v);
    // kElementClass class id + opaque=n so the cl_* thunks can reach the node
    JSValue o = JS_NewObjectClass(ctx, kElementClass);
    JS_SetOpaque(o, n);
    JS_SetPropertyStr(ctx, o, "add", JS_NewCFunction(ctx, cl_add, "add", 1));
    JS_SetPropertyStr(ctx, o, "remove", JS_NewCFunction(ctx, cl_remove, "remove", 1));
    JS_SetPropertyStr(ctx, o, "toggle", JS_NewCFunction(ctx, cl_toggle, "toggle", 1));
    JS_SetPropertyStr(ctx, o, "contains", JS_NewCFunction(ctx, cl_contains, "contains", 1));
    JS_SetPropertyStr(ctx, o, "item", JS_NewCFunction(ctx, cl_item, "item", 1));
    (void)n;
    return o;
}
// style.setProperty / removeProperty
static JSValue st_setProperty(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* n = (DomNode*)JS_GetOpaque(this_v, kStyleClass);
    if (n && argc >= 2) {
        const char* k = JS_ToCString(ctx, argv[0]);
        const char* v = JS_ToCString(ctx, argv[1]);
        if (k && v) {
            std::string key = css_key(k);
            n->style[key] = v;
            n->inline_keys.insert(key);   // S114: JS writes outrank rules
            if (key == "display") n->display_none = (std::string(v) == "none");
        }
        if (k) JS_FreeCString(ctx, k);
        if (v) JS_FreeCString(ctx, v);
    }
    return JS_UNDEFINED;
}
static JSValue st_removeProperty(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* n = (DomNode*)JS_GetOpaque(this_v, kStyleClass);
    if (n && argc >= 1) {
        const char* k = JS_ToCString(ctx, argv[0]);
        if (k) { std::string kk = css_key(k); n->style.erase(kk); n->inline_keys.erase(kk); JS_FreeCString(ctx, k); }
    }
    return JS_UNDEFINED;
}

// canvas width/height accessors on the element
static JSValue el_get_canvas_w(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    return JS_NewInt32(ctx, n && n->canvas ? n->canvas->width() : (n ? 300 : 0));
}
static JSValue el_set_canvas_w(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* n = el_of(this_v);
    if (n) {
        int32_t w = 300; JS_ToInt32(ctx, &w, argv[0]);
        if (!n->canvas) n->canvas = std::make_unique<Canvas2D>();
        n->canvas->set_size(std::max(1, w), n->canvas->height());
    }
    return JS_UNDEFINED;
}
static JSValue el_get_canvas_h(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    return JS_NewInt32(ctx, n && n->canvas ? n->canvas->height() : (n ? 150 : 0));
}
static JSValue el_set_canvas_h(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* n = el_of(this_v);
    if (n) {
        int32_t h = 150; JS_ToInt32(ctx, &h, argv[0]);
        if (!n->canvas) n->canvas = std::make_unique<Canvas2D>();
        n->canvas->set_size(n->canvas->width(), std::max(1, h));
    }
    return JS_UNDEFINED;
}

// ── canvas 2D thunks ────────────────────────────────────────────────────
static Canvas2D* c2d_of(JSValueConst v) { return (Canvas2D*)JS_GetOpaque(v, kCtx2DClass); }
static double argf(JSContext* ctx, JSValueConst v, double dflt = 0) {
    double d = dflt;
    if (!JS_ToFloat64(ctx, &d, v)) return d;
    return dflt;
}

static JSValue c2d_get_fillStyle(JSContext* ctx, JSValueConst this_v) {
    auto* c = c2d_of(this_v);
    return JS_NewString(ctx, c ? c->fill_style.c_str() : "#000000");
}
static JSValue c2d_set_fillStyle(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* c = c2d_of(this_v);
    if (c && argc >= 1) {
        if (JS_IsObject(argv[0])) {
            auto* g = (Gradient*)JS_GetOpaque(argv[0], kGradientClass);
            if (g) { c->fill_gradient = g; return JS_UNDEFINED; }
        }
        c->fill_gradient = nullptr;
        const char* s = JS_ToCString(ctx, argv[0]);
        if (s) { c->fill_style = s; JS_FreeCString(ctx, s); }
    }
    return JS_UNDEFINED;
}
static JSValue c2d_get_strokeStyle(JSContext* ctx, JSValueConst this_v) {
    auto* c = c2d_of(this_v);
    return JS_NewString(ctx, c ? c->stroke_style.c_str() : "#000000");
}
static JSValue c2d_set_strokeStyle(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* c = c2d_of(this_v);
    if (c && argc >= 1) {
        const char* s = JS_ToCString(ctx, argv[0]);
        if (s) { c->stroke_style = s; JS_FreeCString(ctx, s); }
    }
    return JS_UNDEFINED;
}
static JSValue c2d_set_globalAlpha(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* c = c2d_of(this_v);
    if (c && argc >= 1) c->global_alpha = float(std::clamp(argf(ctx, argv[0], 1.0), 0.0, 1.0));
    return JS_UNDEFINED;
}
static JSValue c2d_get_globalAlpha(JSContext* ctx, JSValueConst this_v) {
    auto* c = c2d_of(this_v);
    return JS_NewFloat64(ctx, c ? c->global_alpha : 1.0);
}
static JSValue c2d_set_gco(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* c = c2d_of(this_v);
    if (c && argc >= 1) {
        const char* s = JS_ToCString(ctx, argv[0]);
        if (s) {
            std::string nv = lower_s(s);
            static const char* kValid[] = {"source-over", "lighter", "destination-out",
                                           "destination-over", "multiply", "screen",
                                           "overlay", "copy", "xor", "source-in",
                                           "destination-in", "source-out", "source-atop",
                                           "destination-atop", "darken", "lighten"};
            for (auto* k : kValid)
                if (nv == k) { c->global_composite_operation = nv; break; }
            // WHATWG: invalid value → assignment ignored
        }
        JS_FreeCString(ctx, s);
    }
    return JS_UNDEFINED;
}
static JSValue c2d_get_gco(JSContext* ctx, JSValueConst this_v) {
    auto* c = c2d_of(this_v);
    return JS_NewString(ctx, c ? c->global_composite_operation.c_str() : "source-over");
}
static JSValue c2d_set_lineWidth(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* c = c2d_of(this_v);
    if (c && argc >= 1) c->line_width = float(argf(ctx, argv[0], 1.0));
    return JS_UNDEFINED;
}
static JSValue c2d_get_lineWidth(JSContext* ctx, JSValueConst this_v) {
    auto* c = c2d_of(this_v);
    return JS_NewFloat64(ctx, c ? c->line_width : 1.0);
}
static JSValue c2d_set_font(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* c = c2d_of(this_v);
    if (c && argc >= 1) {
        const char* s = JS_ToCString(ctx, argv[0]);
        if (s) { c->font = s; JS_FreeCString(ctx, s); }
    }
    return JS_UNDEFINED;
}
static JSValue c2d_get_font(JSContext* ctx, JSValueConst this_v) {
    auto* c = c2d_of(this_v);
    return JS_NewString(ctx, c ? c->font.c_str() : "10px sans-serif");
}
static JSValue c2d_set_textAlign(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* c = c2d_of(this_v);
    if (c && argc >= 1) {
        const char* s = JS_ToCString(ctx, argv[0]);
        if (s) { c->text_align = s; JS_FreeCString(ctx, s); }
    }
    return JS_UNDEFINED;
}
static JSValue c2d_get_textAlign(JSContext* ctx, JSValueConst this_v) {
    auto* c = c2d_of(this_v);
    return JS_NewString(ctx, c ? c->text_align.c_str() : "start");
}
static JSValue c2d_set_textBaseline(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* c = c2d_of(this_v);
    if (c && argc >= 1) {
        const char* s = JS_ToCString(ctx, argv[0]);
        if (s) { c->text_baseline = s; JS_FreeCString(ctx, s); }
    }
    return JS_UNDEFINED;
}
static JSValue c2d_get_textBaseline(JSContext* ctx, JSValueConst this_v) {
    auto* c = c2d_of(this_v);
    return JS_NewString(ctx, c ? c->text_baseline.c_str() : "alphabetic");
}



#define C2D_METHOD(name, body)                                              \
    static JSValue c2d_##name(JSContext* ctx, JSValueConst this_v,          \
                              int argc, JSValueConst* argv) {               \
        (void)argc;                                                         \
        auto* c = c2d_of(this_v);                                           \
        if (wv_trace()) std::cerr << "[WV-T] ctx2d." << #name << std::endl; \
        if (c) { body }                                                     \
        return JS_UNDEFINED;                                                \
    }

C2D_METHOD(fill_rect, { c->fill_rect(float(argf(ctx, argv[0])), float(argf(ctx, argv[1])),
                                      float(argf(ctx, argv[2])), float(argf(ctx, argv[3]))); })
C2D_METHOD(stroke_rect, { c->stroke_rect(float(argf(ctx, argv[0])), float(argf(ctx, argv[1])),
                                         float(argf(ctx, argv[2])), float(argf(ctx, argv[3]))); })
C2D_METHOD(clear_rect, { c->clear_rect(float(argf(ctx, argv[0])), float(argf(ctx, argv[1])),
                                       float(argf(ctx, argv[2])), float(argf(ctx, argv[3]))); })
C2D_METHOD(begin_path, { c->begin_path(); })
C2D_METHOD(close_path, { c->close_path(); })
C2D_METHOD(move_to, { c->move_to(float(argf(ctx, argv[0])), float(argf(ctx, argv[1]))); })
C2D_METHOD(line_to, { c->line_to(float(argf(ctx, argv[0])), float(argf(ctx, argv[1]))); })
C2D_METHOD(arc, { c->arc(float(argf(ctx, argv[0])), float(argf(ctx, argv[1])),
                         float(argf(ctx, argv[2])), float(argf(ctx, argv[3])),
                         float(argf(ctx, argv[4])), JS_ToBool(ctx, argc > 5 ? argv[5] : JS_FALSE)); })
C2D_METHOD(quadratic_curve_to, { c->quadratic_curve_to(float(argf(ctx, argv[0])), float(argf(ctx, argv[1])),
                                                       float(argf(ctx, argv[2])), float(argf(ctx, argv[3]))); })
C2D_METHOD(bezier_curve_to, { c->bezier_curve_to(float(argf(ctx, argv[0])), float(argf(ctx, argv[1])),
                                                 float(argf(ctx, argv[2])), float(argf(ctx, argv[3])),
                                                 float(argf(ctx, argv[4])), float(argf(ctx, argv[5]))); })
C2D_METHOD(rect, { c->rect_path(float(argf(ctx, argv[0])), float(argf(ctx, argv[1])),
                                float(argf(ctx, argv[2])), float(argf(ctx, argv[3]))); })
C2D_METHOD(fill, { c->fill(); })
C2D_METHOD(stroke, { c->stroke(); })
C2D_METHOD(clip, { c->clip(); })
C2D_METHOD(save, { c->save(); })
C2D_METHOD(restore, { c->restore(); })
C2D_METHOD(translate, { c->translate(float(argf(ctx, argv[0])), float(argf(ctx, argv[1]))); })
C2D_METHOD(scale, { c->scale(float(argf(ctx, argv[0])), float(argf(ctx, argv[1]))); })
C2D_METHOD(rotate, { c->rotate(float(argf(ctx, argv[0]))); })
C2D_METHOD(set_transform, { c->set_transform(float(argf(ctx, argv[0])), float(argf(ctx, argv[1])),
                                             float(argf(ctx, argv[2])), float(argf(ctx, argv[3])),
                                             float(argf(ctx, argv[4])), float(argf(ctx, argv[5]))); })
C2D_METHOD(transform, { c->transform(float(argf(ctx, argv[0])), float(argf(ctx, argv[1])),
                                     float(argf(ctx, argv[2])), float(argf(ctx, argv[3])),
                                     float(argf(ctx, argv[4])), float(argf(ctx, argv[5]))); })
C2D_METHOD(reset_transform, { c->reset_transform(); })
#undef C2D_METHOD

static JSValue c2d_fill_text(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* c = c2d_of(this_v);
    if (c && argc >= 3) {
        const char* s = JS_ToCString(ctx, argv[0]);
        if (s) {
            c->fill_text(s, float(argf(ctx, argv[1])), float(argf(ctx, argv[2])));
            JS_FreeCString(ctx, s);
        }
    }
    return JS_UNDEFINED;
}
static JSValue c2d_stroke_text(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* c = c2d_of(this_v);
    if (c && argc >= 3) {
        const char* s = JS_ToCString(ctx, argv[0]);
        if (s) {
            c->stroke_text(s, float(argf(ctx, argv[1])), float(argf(ctx, argv[2])));
            JS_FreeCString(ctx, s);
        }
    }
    return JS_UNDEFINED;
}
static JSValue c2d_measure_text(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* c = c2d_of(this_v);
    float w = 0;
    if (c && argc >= 1) {
        const char* s = JS_ToCString(ctx, argv[0]);
        if (s) { w = c->measure_text(s); JS_FreeCString(ctx, s); }
    }
    JSValue o = JS_NewObject(ctx);
    JS_SetPropertyStr(ctx, o, "width", JS_NewFloat64(ctx, w));
    return o;
}
static JSValue c2d_draw_image(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* c = c2d_of(this_v);
    if (!c || argc < 1 || !JS_IsObject(argv[0])) return JS_UNDEFINED;
    const renderer::FrameBuffer* src = nullptr;
    // canvas element?
    auto* n = el_of(argv[0]);
    if (n && n->is_canvas && n->canvas) src = &n->canvas->bitmap();
    if (!src) {
        auto* im = (ImageObj*)JS_GetOpaque(argv[0], kImageClass);
        if (im && im->fb) src = im->fb.get();
    }
    if (!src) return JS_UNDEFINED;
    float dw = src->get_width(), dh = src->get_height();
    float dx = 0, dy = 0;
    if (argc >= 3) {
        dx = float(argf(ctx, argv[1])); dy = float(argf(ctx, argv[2]));
        if (argc >= 5) { dw = float(argf(ctx, argv[3])); dh = float(argf(ctx, argv[4])); }
    }
    c->draw_image(*src, dx, dy, dw, dh);
    return JS_UNDEFINED;
}
static JSValue c2d_create_pattern(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* c = c2d_of(this_v);
    if (!c || argc < 1 || !JS_IsObject(argv[0])) return JS_NULL;
    const renderer::FrameBuffer* src = nullptr;
    auto* n = el_of(argv[0]);
    if (n && n->is_canvas && n->canvas) src = &n->canvas->bitmap();
    if (!src) return JS_NULL;
    auto* p = c->make_pattern(*src);
    JSValue o = JS_NewObjectClass(ctx, kPatternClass);
    JS_SetOpaque(o, p);
    return o;
}

static JSValue c2d_create_linear_gradient(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv);
static JSValue c2d_create_radial_gradient(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv);

static void setup_style_class(JSRuntime* rt) {
    static JSClassExoticMethods exotic;
    exotic.get_own_property = style_get_own_property;
    exotic.define_own_property = style_define_own_property;
    if (!kStyleClass) {
        JSClassDef d = {"CSSStyleDeclaration", noop_finalizer};
        d.exotic = &exotic;
        JS_NewClassID(&kStyleClass);
    }
    JSClassDef d = {"CSSStyleDeclaration", noop_finalizer};
    d.exotic = &exotic;
    JS_NewClass(rt, kStyleClass, &d);
}

static void register_js_classes(JSRuntime* rt) {
    JSClassDef dElem = {"HTMLElement", noop_finalizer};
    if (!kElementClass) JS_NewClassID(&kElementClass);
    if (JS_NewClass(rt, kElementClass, &dElem)) std::cerr << "[WV-CLS] HTMLElement reg FAILED\n";
    JSClassDef dCtx = {"CanvasRenderingContext2D", ctx2d_finalizer};
    if (!kCtx2DClass) JS_NewClassID(&kCtx2DClass);
    if (JS_NewClass(rt, kCtx2DClass, &dCtx)) std::cerr << "[WV-CLS] Ctx2D reg FAILED\n";
    JSClassDef dStore = {"Storage", noop_finalizer};
    if (!kStorageClass) JS_NewClassID(&kStorageClass);
    if (JS_NewClass(rt, kStorageClass, &dStore)) std::cerr << "[WV-CLS] Storage reg FAILED\n";
    JSClassDef dPat = {"CanvasPattern", noop_finalizer};
    if (!kPatternClass) JS_NewClassID(&kPatternClass);
    if (JS_NewClass(rt, kPatternClass, &dPat)) std::cerr << "[WV-CLS] Pattern reg FAILED\n";
    JSClassDef dImg = {"HTMLImageElement", image_finalizer};
    if (!kImageClass) JS_NewClassID(&kImageClass);
    if (JS_NewClass(rt, kImageClass, &dImg)) std::cerr << "[WV-CLS] Image reg FAILED\n";
    JSClassDef dGrad = {"CanvasGradient", noop_finalizer};
    if (!kGradientClass) JS_NewClassID(&kGradientClass);
    if (JS_NewClass(rt, kGradientClass, &dGrad)) std::cerr << "[WV-CLS] Gradient reg FAILED\n";
    std::cerr << "[WV-CLS] registered elem=" << kElementClass << " ctx2d=" << kCtx2DClass
              << " grad=" << kGradientClass << " style=" << kStyleClass << std::endl;
}

// ── element thunks ──────────────────────────────────────────────────────
static DomNode* el_of(JSValueConst v) {
    return (DomNode*)JS_GetOpaque(v, kElementClass);
}
static WebViewEngine::Impl* impl_of(JSContext* ctx) {
    return (WebViewEngine::Impl*)JS_GetContextOpaque(ctx);
}

static bool wv_trace() { static bool t = getenv("WV_TRACE") != nullptr; return t; }

// ── base64 (WebHTML btoa/atob law: latin1 byte string <-> base64) ──────
static const char kB64[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
static JSValue js_btoa(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv) {
    if (argc < 1) return JS_ThrowTypeError(ctx, "btoa requires an argument");
    const char* s = JS_ToCString(ctx, argv[0]);
    if (!s) return JS_EXCEPTION;
    size_t len = strlen(s);
    std::string out;
    out.reserve((len + 2) / 3 * 4);
    for (size_t i = 0; i < len; i += 3) {
        unsigned b0 = (unsigned char)s[i];
        unsigned b1 = i + 1 < len ? (unsigned char)s[i + 1] : 0;
        unsigned b2 = i + 2 < len ? (unsigned char)s[i + 2] : 0;
        out += kB64[b0 >> 2];
        out += kB64[((b0 & 3) << 4) | (b1 >> 4)];
        out += i + 1 < len ? kB64[((b1 & 15) << 2) | (b2 >> 6)] : '=';
        out += i + 2 < len ? kB64[b2 & 63] : '=';
    }
    JS_FreeCString(ctx, s);
    return JS_NewStringLen(ctx, out.c_str(), out.size());
}
static int b64val(char c) {
    if (c >= 'A' && c <= 'Z') return c - 'A';
    if (c >= 'a' && c <= 'z') return c - 'a' + 26;
    if (c >= '0' && c <= '9') return c - '0' + 52;
    if (c == '+') return 62;
    if (c == '/') return 63;
    return -1;
}
static JSValue js_atob(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv) {
    if (argc < 1) return JS_ThrowTypeError(ctx, "atob requires an argument");
    const char* s = JS_ToCString(ctx, argv[0]);
    if (!s) return JS_EXCEPTION;
    std::string out;
    int v = 0, bits = 0;
    for (const char* p = s; *p; ++p) {
        if (*p == '=') break;
        int d = b64val(*p);
        if (d < 0) continue;
        v = (v << 6) | d;
        bits += 6;
        if (bits >= 8) {
            bits -= 8;
            out += char((v >> bits) & 0xFF);
        }
    }
    JS_FreeCString(ctx, s);
    return JS_NewStringLen(ctx, out.c_str(), out.size());
}
static JSValue js_console_log(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv) {
    std::ostringstream oss;
    for (int i = 0; i < argc; ++i) {
        const char* s = JS_ToCString(ctx, argv[i]);
        if (s) { if (i) oss << ' '; oss << s; JS_FreeCString(ctx, s); }
    }
    std::cerr << "[WV-CONSOLE] " << oss.str() << std::endl;
    return JS_UNDEFINED;
}

static JSValue el_get_id(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    return JS_NewString(ctx, n && n->attrs.count("id") ? n->attrs["id"].c_str() : "");
}
static JSValue el_set_id(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* n = el_of(this_v);
    if (n && argc >= 1) {
        const char* s = JS_ToCString(ctx, argv[0]);
        if (s) { n->attrs["id"] = s; JS_FreeCString(ctx, s); }
    }
    return JS_UNDEFINED;
}
static JSValue el_get_tag(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    return JS_NewString(ctx, n ? upper_s(n->tag).c_str() : "");
}
static JSValue el_get_text(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    return JS_NewString(ctx, n ? HtmlParser::text_content(n).c_str() : "");
}
static JSValue el_set_text(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    if (wv_trace()) std::cerr << "[WV-T] el.innerText=" << std::endl;
    auto* n = el_of(this_v);
    if (n && argc >= 1) {
        const char* s = JS_ToCString(ctx, argv[0]);
        if (s) {
            n->children.clear();
            auto t = std::make_unique<DomNode>();
            t->tag = "#text"; t->text = s; t->parent = n;
            n->children.push_back(std::move(t));
            JS_FreeCString(ctx, s);
        }
    }
    return JS_UNDEFINED;
}
static JSValue el_get_inner_html(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    return JS_NewString(ctx, n ? HtmlParser::inner_html(n).c_str() : "");
}
static JSValue el_set_inner_html(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    if (wv_trace()) std::cerr << "[WV-T] el.innerHTML=" << std::endl;
    auto* n = el_of(this_v);
    if (n && argc >= 1) {
        const char* s = JS_ToCString(ctx, argv[0]);
        if (s) {
            auto frag = HtmlParser::parse_fragment(s);
            // S113: injected subtrees get the active stylesheet applied
            // (innerHTML-created elements match class/id rules immediately —
            // the mykanji cat-swap law: .kanji-display-catN must style the
            // fresh node the same frame it appears).
            auto* imp = impl_of(ctx);
            auto& rules = !imp->active_rules.empty() ? imp->active_rules : imp->css_rules;
            // WHATWG innerHTML law: the setter REPLACES all children.
            // (The old append-only behavior was invisible while injected
            // nodes carried no styles; with full-GUI styling it produced
            // duplicate cats — the S113 cat-swap regression.)
            for (auto& old : n->children) imp->orphans.push_back({old.get(), std::move(old)});
            n->children.clear();
            // adopt fragment children (transfer ownership out of the fragment box)
            for (auto& c : frag->children) {
                DomNode* raw = c.get();
                imp->orphans.push_back({raw, std::move(c)});
                raw->parent = n;
                n->children.push_back(std::move(imp->orphans.back().second));
                // fix the orphan bridge to point at the new owner
                imp->orphans.pop_back();
                HtmlParser::apply_css_impl(raw, rules, &imp->custom_props, false);
            }
            JS_FreeCString(ctx, s);
        }
    }
    return JS_UNDEFINED;
}
static JSValue st_setProperty(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv);
static JSValue st_removeProperty(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv);
static JSValue el_get_style(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    if (wv_trace()) std::cerr << "[WV-T] el.style" << std::endl;
    JSValue cached = JS_GetPropertyStr(ctx, this_v, "__style__");
    if (!JS_IsUndefined(cached)) return cached;
    JS_FreeValue(ctx, cached);
    auto* n = el_of(this_v);
    if (!n) return JS_UNDEFINED;
    JSValue o = JS_NewObjectClass(ctx, kStyleClass);
    JS_SetOpaque(o, n);
    JS_SetPropertyStr(ctx, o, "setProperty", JS_NewCFunction(ctx, st_setProperty, "setProperty", 2));
    JS_SetPropertyStr(ctx, o, "removeProperty", JS_NewCFunction(ctx, st_removeProperty, "removeProperty", 1));
    JS_SetPropertyStr(ctx, this_v, "__style__", JS_DupValue(ctx, o));  // keep alive
    return o;
}
static JSValue el_get_class_list(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    JSValue arr = JS_NewArray(ctx);
    if (n && n->attrs.count("class")) {
        std::istringstream ss(n->attrs["class"]);
        std::string tok; uint32_t i = 0;
        while (ss >> tok) JS_SetPropertyUint32(ctx, arr, i++, JS_NewString(ctx, tok.c_str()));
    }
    return arr;
}
static JSValue el_get_children(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    JSValue arr = JS_NewArray(ctx);
    if (n) {
        uint32_t i = 0;
        for (auto& c : n->children) {
            if (c->tag == "#text") continue;
            JS_SetPropertyUint32(ctx, arr, i++, impl_of(ctx)->get_element_js(c.get()));
        }
    }
    return arr;
}
static JSValue el_get_parent(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    if (!n || !n->parent) return JS_NULL;
    return impl_of(ctx)->get_element_js(n->parent);
}
static JSValue el_get_first_child(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    if (!n || n->children.empty()) return JS_NULL;
    return impl_of(ctx)->get_element_js(n->children.front().get());
}
// S117 DOM traversal law (WHATWG DOM §4.4): the full sibling/child family.
// nextElementSibling/previousElementSibling return the adjacent ELEMENT
// (skipping #text); nextSibling/previousSibling return the adjacent NODE of
// any kind; firstElementChild/lastElementChild/lastChild/childElementCount
// mirror the children list. org.asafonov.weather's NavigationView
// (setMenuButtonVisibility) walks nextElementSibling to toggle its nav
// buttons — one missing property aborted the whole ControlView build. Core
// DOM family: every HTML5 app benefits, zero package checks.
static JSValue el_get_next_element_sibling(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    if (!n || !n->parent) return JS_NULL;
    auto& sibs = n->parent->children;
    for (size_t i = 0; i + 1 < sibs.size(); ++i)
        if (sibs[i].get() == n)
            for (size_t j = i + 1; j < sibs.size(); ++j)
                if (sibs[j]->tag != "#text")
                    return impl_of(ctx)->get_element_js(sibs[j].get());
    return JS_NULL;
}
static JSValue el_get_prev_element_sibling(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    if (!n || !n->parent) return JS_NULL;
    auto& sibs = n->parent->children;
    for (size_t i = sibs.size(); i-- > 1;)
        if (sibs[i].get() == n)
            for (size_t j = i; j-- > 0;)
                if (sibs[j]->tag != "#text")
                    return impl_of(ctx)->get_element_js(sibs[j].get());
    return JS_NULL;
}
static JSValue el_get_next_sibling(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    if (!n || !n->parent) return JS_NULL;
    auto& sibs = n->parent->children;
    for (size_t i = 0; i + 1 < sibs.size(); ++i)
        if (sibs[i].get() == n) {
            if (i + 1 < sibs.size())
                return impl_of(ctx)->get_element_js(sibs[i + 1].get());
            break;
        }
    return JS_NULL;
}
static JSValue el_get_prev_sibling(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    if (!n || !n->parent) return JS_NULL;
    auto& sibs = n->parent->children;
    for (size_t i = sibs.size(); i-- > 1;)
        if (sibs[i].get() == n)
            return impl_of(ctx)->get_element_js(sibs[i - 1].get());
    return JS_NULL;
}
static JSValue el_get_first_element_child(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    if (n)
        for (auto& c : n->children)
            if (c->tag != "#text")
                return impl_of(ctx)->get_element_js(c.get());
    return JS_NULL;
}
static JSValue el_get_last_element_child(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    if (n)
        for (auto it = n->children.rbegin(); it != n->children.rend(); ++it)
            if ((*it)->tag != "#text")
                return impl_of(ctx)->get_element_js(it->get());
    return JS_NULL;
}
static JSValue el_get_last_child(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    if (!n || n->children.empty()) return JS_NULL;
    return impl_of(ctx)->get_element_js(n->children.back().get());
}
static JSValue el_get_child_element_count(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    int32_t cnt = 0;
    if (n)
        for (auto& c : n->children)
            if (c->tag != "#text") ++cnt;
    return JS_NewInt32(ctx, cnt);
}
static JSValue el_get_offset_w(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    return JS_NewInt32(ctx, n ? n->w : 0);
}
// S114 form-element property getters: .value defaults to "" (HTML §4.10.2
// value IDL attribute), .checked is the checked- ATTRIBUTE presence law
// (`<input checked>` has checked === true with no value)
static JSValue el_get_value_prop(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    auto it = n ? n->attrs.find("value") : n->attrs.end();
    return JS_NewString(ctx, it != n->attrs.end() ? it->second.c_str() : "");
}
static JSValue el_get_checked_prop(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    if (n) {
        auto it = n->attrs.find("checked");
        if (it != n->attrs.end())
            return JS_NewBool(ctx, it->second.empty() || it->second == "checked" ||
                                       it->second == "true");
    }
    return JS_FALSE;
}
// S114 className property law (HTML §2.6.4 className === class attribute) —
// Block'Buster tags gameplay objects with `element.className = 'object …'`
static JSValue el_get_class_name(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    auto it = n ? n->attrs.find("class") : n->attrs.end();
    return JS_NewString(ctx, it != n->attrs.end() ? it->second.c_str() : "");
}
static JSValue el_set_class_name(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* n = el_of(this_v);
    if (n && argc >= 1) {
        const char* v = JS_ToCString(ctx, argv[0]);
        if (v) { n->attrs["class"] = v; JS_FreeCString(ctx, v); }
    }
    return JS_UNDEFINED;
}
static JSValue el_set_checked_prop(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* n = el_of(this_v);
    if (n && argc >= 1) {
        int truthy = JS_ToBool(ctx, argv[0]);
        if (truthy) n->attrs["checked"] = "";
        else n->attrs.erase("checked");
    }
    return JS_UNDEFINED;
}
static JSValue el_get_offset_h(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    return JS_NewInt32(ctx, n ? n->h : 0);
}
static JSValue el_append_child(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    if (wv_trace()) std::cerr << "[WV-T] el.appendChild" << std::endl;
    auto* impl = impl_of(ctx);
    auto* n = el_of(this_v);
    if (!n || argc < 1 || !JS_IsObject(argv[0])) return JS_UNDEFINED;
    auto* c = el_of(argv[0]);
    if (!c) return JS_DupValue(ctx, argv[0]);
    // detach from current parent (move semantics, DOM law)
    if (c->parent) {
        auto& pc = c->parent->children;
        for (size_t i = 0; i < pc.size(); ++i)
            if (pc[i].get() == c) { pc[i].release(); pc.erase(pc.begin() + i); break; }
    } else {
        // adopt from the orphan bridge
        for (size_t i = 0; i < impl->orphans.size(); ++i)
            if (impl->orphans[i].first == c) {
                impl->orphans[i].second.release();
                impl->orphans.erase(impl->orphans.begin() + i);
                break;
            }
    }
    c->parent = n;
    n->children.push_back(std::unique_ptr<DomNode>(c));
    // S114 appendChild stylesheet law: JS-created elements receive the
    // ACTIVE stylesheet rules when they enter the document — without this
    // the gameplay objects (createElement + appendChild, no innerHTML) had
    // NO class styles: no background, no position, invisible bricks.
    {
        auto& rules = !impl->active_rules.empty() ? impl->active_rules : impl->css_rules;
        std::function<void(DomNode*)> apply = [&](DomNode* g) {
            HtmlParser::apply_css_impl(g, rules, &impl->custom_props, false);
            for (auto& gc : g->children) apply(gc.get());
        };
        apply(c);
    }
    return JS_DupValue(ctx, argv[0]);
}
static JSValue el_remove_child(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* n = el_of(this_v);
    if (n && argc >= 1) {
        auto* c = el_of(argv[0]);
        if (c && c->parent == n) {
            auto& pc = n->children;
            for (size_t i = 0; i < pc.size(); ++i)
                if (pc[i].get() == c) { pc[i].release(); pc.erase(pc.begin() + i); break; }
            // hand ownership to the orphan bridge so the node stays alive
            impl_of(ctx)->orphans.push_back({c, std::unique_ptr<DomNode>(c)});
        }
    }
    return argc >= 1 ? JS_DupValue(ctx, argv[0]) : JS_UNDEFINED;
}
static JSValue el_insert_before(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* impl = impl_of(ctx);
    auto* n = el_of(this_v);
    if (!n || argc < 1 || !JS_IsObject(argv[0])) return JS_UNDEFINED;
    auto* c = el_of(argv[0]);
    DomNode* before = argc >= 2 && JS_IsObject(argv[1]) ? el_of(argv[1]) : nullptr;
    if (!c) return JS_DupValue(ctx, argv[0]);
    if (c->parent) {
        auto& pc = c->parent->children;
        for (size_t i = 0; i < pc.size(); ++i)
            if (pc[i].get() == c) { pc[i].release(); pc.erase(pc.begin() + i); break; }
    } else {
        for (size_t i = 0; i < impl->orphans.size(); ++i)
            if (impl->orphans[i].first == c) {
                impl->orphans[i].second.release();
                impl->orphans.erase(impl->orphans.begin() + i);
                break;
            }
    }
    c->parent = n;
    auto up = std::unique_ptr<DomNode>(c);
    size_t at = n->children.size();
    if (before) {
        for (size_t i = 0; i < n->children.size(); ++i)
            if (n->children[i].get() == before) { at = i; break; }
    }
    n->children.insert(n->children.begin() + at, std::move(up));
    return JS_DupValue(ctx, argv[0]);
}
static JSValue el_remove(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    if (n && n->parent) {
        auto& pc = n->parent->children;
        for (size_t i = 0; i < pc.size(); ++i)
            if (pc[i].get() == n) { pc[i].release(); pc.erase(pc.begin() + i); break; }
        n->parent = nullptr;
        impl_of(ctx)->orphans.push_back({n, std::unique_ptr<DomNode>(n)});
    }
    return JS_UNDEFINED;
}
static JSValue el_addEventListener(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    if (wv_trace()) std::cerr << "[WV-T] el.addEventListener" << std::endl;
    auto* impl = impl_of(ctx);
    if (argc >= 2) {
        const char* type = JS_ToCString(ctx, argv[0]);
        if (type) {
            impl->listeners[el_of(this_v)][lower_s(type)].push_back(JS_DupValue(ctx, argv[1]));
            impl->stats.events_registered++;
            JS_FreeCString(ctx, type);
        }
    }
    return JS_UNDEFINED;
}
static JSValue el_removeEventListener(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* impl = impl_of(ctx);
    if (argc >= 2) {
        const char* type = JS_ToCString(ctx, argv[0]);
        if (type) {
            auto lit = impl->listeners.find(el_of(this_v));
            if (lit != impl->listeners.end()) {
                auto vit = lit->second.find(lower_s(type));
                if (vit != lit->second.end() && !vit->second.empty()) {
                    JS_FreeValue(ctx, vit->second.back());
                    vit->second.pop_back();
                }
            }
            JS_FreeCString(ctx, type);
        }
    }
    return JS_UNDEFINED;
}
// S113 ROOT-060: HTMLMediaElement.play/pause — silent-resolution law.
// The app-facing contract is the RETURN VALUE (a promise with .catch —
// WHATWG HTML §4.8.11 play() returns a Promise); this runtime renders
// without an audio sink, so playback resolves silently. The element-tag
// check keeps non-media elements honest (undefined — "not a function"
// stays correct for divs).
static JSValue el_media_play(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    if (!n || (n->tag != "audio" && n->tag != "video")) return JS_UNDEFINED;
    // promise-like: { catch(fn), then(fn) } — fire-and-forget resolve
    JSValue o = JS_NewObject(ctx);
    JSValue catchfn = JS_NewCFunction(ctx, [](JSContext* c, JSValueConst, int,
                                              JSValueConst*) -> JSValue {
        return JS_UNDEFINED; }, "catch", 1);
    JS_SetPropertyStr(ctx, o, "catch", catchfn);
    JSValue thenfn = JS_NewCFunction(ctx, [](JSContext* c, JSValueConst, int,
                                             JSValueConst*) -> JSValue {
        return JS_UNDEFINED; }, "then", 1);
    JS_SetPropertyStr(ctx, o, "then", thenfn);
    return o;
}
static JSValue el_media_pause(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    return JS_UNDEFINED;
}
// S118 SVG geometry law (fwd): shape elements have no HTML box; browsers
// report the geometry bbox in viewport coordinates (SVG2 §3.2 +
// SVGGeometryElement.getBoundingClientRect). Defined after svg_flatten.
static bool svg_shape_rect(struct DomNode* n, float vpw, float vph,
                           double& rx, double& ry, double& rw, double& rh);

static JSValue el_getBoundingClientRect(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    if (auto* pi = impl_of(ctx)) pi->sync_layout_if_needed();
    JSValue o = JS_NewObject(ctx);
    double x = n ? n->x : 0, y = n ? n->y : 0, w = n ? n->w : 0, h = n ? n->h : 0;
    // S118: an SVG shape (path/rect/circle/…/use) never gets an HTML slot,
    // so its plain box reads (0,0,0,0). Browsers answer the geometry bbox —
    // every app that measures an inline SVG icon/figure through
    // getBoundingClientRect() (accelerace's car placement) needs this.
    if (n && w <= 0 && h <= 0) {
        double rx, ry, rw, rh;
        if (auto* pi = impl_of(ctx))
            if (svg_shape_rect(n, float(pi->viewport_w), float(pi->viewport_h),
                               rx, ry, rw, rh)) { x = rx; y = ry; w = rw; h = rh; }
    }
    JS_SetPropertyStr(ctx, o, "left", JS_NewFloat64(ctx, x));
    JS_SetPropertyStr(ctx, o, "top", JS_NewFloat64(ctx, y));
    JS_SetPropertyStr(ctx, o, "right", JS_NewFloat64(ctx, x + w));
    JS_SetPropertyStr(ctx, o, "bottom", JS_NewFloat64(ctx, y + h));
    JS_SetPropertyStr(ctx, o, "width", JS_NewFloat64(ctx, w));
    JS_SetPropertyStr(ctx, o, "height", JS_NewFloat64(ctx, h));
    return o;
}
static JSValue el_setAttribute(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* n = el_of(this_v);
    if (n && argc >= 2) {
        const char* k = JS_ToCString(ctx, argv[0]);
        const char* v = JS_ToCString(ctx, argv[1]);
        if (k && v) {
            std::string key = lower_s(k);
            n->attrs[key] = v;
            if (n->is_canvas && key == "width") {
                if (!n->canvas) n->canvas = std::make_unique<Canvas2D>();
                n->canvas->set_size(atoi(v), n->canvas->height());
            } else if (n->is_canvas && key == "height") {
                if (!n->canvas) n->canvas = std::make_unique<Canvas2D>();
                n->canvas->set_size(n->canvas->width(), atoi(v));
            }
        }
        if (k) JS_FreeCString(ctx, k);
        if (v) JS_FreeCString(ctx, v);
    }
    return JS_UNDEFINED;
}
static JSValue el_getAttribute(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* n = el_of(this_v);
    if (n && argc >= 1) {
        const char* k = JS_ToCString(ctx, argv[0]);
        if (k) {
            auto it = n->attrs.find(lower_s(k));
            JS_FreeCString(ctx, k);
            if (it != n->attrs.end()) return JS_NewString(ctx, it->second.c_str());
        }
    }
    return JS_NULL;
}
static JSValue el_hasAttribute(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* n = el_of(this_v);
    if (n && argc >= 1) {
        const char* k = JS_ToCString(ctx, argv[0]);
        if (k) {
            bool has = n->attrs.count(lower_s(k)) > 0;
            JS_FreeCString(ctx, k);
            return JS_NewBool(ctx, has);
        }
    }
    return JS_FALSE;
}
static JSValue el_removeAttribute(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* n = el_of(this_v);
    if (n && argc >= 1) {
        const char* k = JS_ToCString(ctx, argv[0]);
        if (k) { n->attrs.erase(lower_s(k)); JS_FreeCString(ctx, k); }
    }
    return JS_UNDEFINED;
}
static JSValue el_click(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    if (n) {
        // synthetic click: dispatch a click event at the element center
        auto* impl = impl_of(ctx);
        JSValue ev = JS_NewObject(ctx);
        JS_SetPropertyStr(ctx, ev, "type", JS_NewString(ctx, "click"));
        JSValue t = impl->get_element_js(n);
        JS_SetPropertyStr(ctx, ev, "target", t);
        JS_SetPropertyStr(ctx, ev, "clientX", JS_NewInt32(ctx, n->x + n->w / 2));
        JS_SetPropertyStr(ctx, ev, "clientY", JS_NewInt32(ctx, n->y + n->h / 2));
        impl->dispatch(n, "click", ev);
    }
    return JS_UNDEFINED;
}
static JSValue el_focus(JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }

// ── CanvasGradient (owned by the Canvas2D; JS object is a view) ─────────
static JSValue grad_addColorStop(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* g = (Gradient*)JS_GetOpaque(this_v, kGradientClass);
    if (g && argc >= 2) {
        double off = 0; JS_ToFloat64(ctx, &off, argv[0]);
        const char* col = JS_ToCString(ctx, argv[1]);
        if (col) {
            bool ok = false;
            uint32_t rgba = parse_css_color(col, ok);
            if (ok) g->stops.push_back({float(off), rgba});
            JS_FreeCString(ctx, col);
        }
        std::sort(g->stops.begin(), g->stops.end(),
                  [](const Gradient::Stop& a, const Gradient::Stop& b) { return a.pos < b.pos; });
    }
    return JS_UNDEFINED;
}

// ── canvas getContext (WHATWG: 2d context bound to the element bitmap) ──
// ROOT-049 accessor wrappers (defined after this function; forward-declared)
static JSValue c2d_fillStyle_get(JSContext*, JSValueConst, int, JSValueConst*);
static JSValue c2d_fillStyle_set(JSContext*, JSValueConst, int, JSValueConst*);
static JSValue c2d_strokeStyle_get(JSContext*, JSValueConst, int, JSValueConst*);
static JSValue c2d_strokeStyle_set(JSContext*, JSValueConst, int, JSValueConst*);
static JSValue c2d_globalAlpha_get(JSContext*, JSValueConst, int, JSValueConst*);
static JSValue c2d_globalAlpha_set(JSContext*, JSValueConst, int, JSValueConst*);
static JSValue c2d_gco_get(JSContext*, JSValueConst, int, JSValueConst*);
static JSValue c2d_gco_set(JSContext*, JSValueConst, int, JSValueConst*);
static JSValue c2d_lineWidth_get(JSContext*, JSValueConst, int, JSValueConst*);
static JSValue c2d_lineWidth_set(JSContext*, JSValueConst, int, JSValueConst*);
static JSValue c2d_font_get(JSContext*, JSValueConst, int, JSValueConst*);
static JSValue c2d_font_set(JSContext*, JSValueConst, int, JSValueConst*);
static JSValue c2d_textAlign_get(JSContext*, JSValueConst, int, JSValueConst*);
static JSValue c2d_textAlign_set(JSContext*, JSValueConst, int, JSValueConst*);
static JSValue c2d_textBaseline_get(JSContext*, JSValueConst, int, JSValueConst*);
static JSValue c2d_textBaseline_set(JSContext*, JSValueConst, int, JSValueConst*);
static JSValue el_getContext(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    if (wv_trace()) std::cerr << "[WV-T] el.getContext" << std::endl;
    auto* n = el_of(this_v);
    if (!n || !n->is_canvas) return JS_NULL;
    if (!n->canvas) {
        n->canvas = std::make_unique<Canvas2D>();
        // S133 REPLACED-ELEMENT law (WHATWG HTML §4.12.4): the canvas
        // bitmap is sized from the width=/height= ATTRIBUTES (300x150
        // default) when the context is FIRST acquired — parse-time
        // attributes never sized the bitmap, so every fill landed on a
        // 1x1 surface and the canvas stayed invisible (T09 fixture:
        // draw_calls=2, zero pixels).
        auto aw = n->attrs.find("width");
        auto ah = n->attrs.find("height");
        int bw = aw != n->attrs.end() ? atoi(aw->second.c_str()) : 300;
        int bh = ah != n->attrs.end() ? atoi(ah->second.c_str()) : 150;
        n->canvas->set_size(std::max(1, bw), std::max(1, bh));
    }
    JSValue o = JS_NewObjectClass(ctx, kCtx2DClass);
    if (JS_IsException(o)) return o;
    JS_SetOpaque(o, n->canvas.get());
    // ROOT-049 law: the WHATWG CanvasRenderingContext2D surface must be
    // COMPLETE — the S109 build had the full C++ raster (Canvas2D) and even
    // pre-written binding helpers, but el_getContext registered only 6 of
    // them, so every real web app died with "TypeError: not a function" on
    // its first beginPath/fillRect. A smoke test that only exercises
    // registered members cannot catch this — the surface itself is the law.
    auto m = [&](const char* name, JSCFunction f, int len) {
        JS_SetPropertyStr(ctx, o, name, JS_NewCFunction(ctx, f, name, len));
    };
    // path + rect ops (C2D_METHOD-generated helpers)
    m("beginPath", c2d_begin_path, 0);
    m("closePath", c2d_close_path, 0);
    m("moveTo", c2d_move_to, 2);
    m("lineTo", c2d_line_to, 2);
    m("arc", c2d_arc, 5);
    m("ellipse", [](JSContext* c, JSValueConst t, int argc, JSValueConst* argv) -> JSValue {
        // ellipse(cx,cy,rx,ry,rot,a0,a1,ccw) — exact geometry via a scaled
        // unit-circle arc under a temporary transform.
        auto* e = c2d_of(t);
        if (e && argc >= 7) {
            e->save();
            e->translate(float(argf(c, argv[0])), float(argf(c, argv[1])));
            e->rotate(float(argf(c, argv[4])));
            e->scale(float(argf(c, argv[2])), float(argf(c, argv[3])));
            e->arc(0, 0, 1, float(argf(c, argv[5])), float(argf(c, argv[6])),
                   argc > 7 && JS_ToBool(c, argv[7]));
            e->restore();
        }
        return JS_UNDEFINED;
    }, 7);
    m("quadraticCurveTo", c2d_quadratic_curve_to, 4);
    m("bezierCurveTo", c2d_bezier_curve_to, 6);
    m("rect", c2d_rect, 4);
    m("fill", c2d_fill, 0);
    m("stroke", c2d_stroke, 0);
    m("clip", c2d_clip, 0);
    m("fillRect", c2d_fill_rect, 4);
    m("strokeRect", c2d_stroke_rect, 4);
    m("clearRect", c2d_clear_rect, 4);
    // state stack + transforms
    m("save", c2d_save, 0);
    m("restore", c2d_restore, 0);
    m("translate", c2d_translate, 2);
    m("scale", c2d_scale, 2);
    m("rotate", c2d_rotate, 1);
    m("transform", c2d_transform, 6);
    m("setTransform", c2d_set_transform, 6);
    m("resetTransform", c2d_reset_transform, 0);
    // text
    m("fillText", c2d_fill_text, 3);
    m("strokeText", c2d_stroke_text, 3);
    m("measureText", c2d_measure_text, 1);
    // images + patterns
    m("drawImage", c2d_draw_image, 5);
    m("createPattern", c2d_create_pattern, 2);
    // gradients (already registered pre-ROOT-049; kept on the same object)
    m("createLinearGradient", c2d_create_linear_gradient, 4);
    m("createRadialGradient", c2d_create_radial_gradient, 6);
    m("addColorStop", grad_addColorStop, 2);  // also on the gradient objects
    // dash + hit-testing (documented approximations)
    m("setLineDash", [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, 1);
    m("getLineDash", [](JSContext* c, JSValueConst, int, JSValueConst*) { return JS_NewArray(c); }, 0);
    m("isPointInPath", [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_FALSE; }, 2);
    // pixel access — real FrameBuffer raster (WHATWG §4.12.5.4)
    m("getImageData", [](JSContext* c, JSValueConst t, int argc, JSValueConst* argv) -> JSValue {
        auto* e = c2d_of(t);
        if (!e || argc < 4) return JS_NULL;
        int sx = int(argf(c, argv[0])), sy = int(argf(c, argv[1]));
        int sw = int(argf(c, argv[2])), sh = int(argf(c, argv[3]));
        if (sw <= 0 || sh <= 0) {
            sw = e->width();   // WHATWG: non-positive dims → whole bitmap
            sh = e->height();
            sx = 0; sy = 0;
        }
        auto& bm = e->bitmap();
        const auto& px = bm.get_pixels();
        JSValue data = JS_NewArray(c);
        for (int y = 0; y < sh; ++y)
            for (int x = 0; x < sw; ++x) {
                int bx = sx + x, by = sy + y;
                renderer::RGBA p{0, 0, 0, 0};
                if (bx >= 0 && by >= 0 && bx < bm.get_width() && by < bm.get_height())
                    p = px[size_t(by) * bm.get_width() + bx];
                uint32_t i = (uint32_t(y) * uint32_t(sw) + uint32_t(x)) * 4;
                JS_SetPropertyUint32(c, data, i + 0, JS_NewInt32(c, p.r));
                JS_SetPropertyUint32(c, data, i + 1, JS_NewInt32(c, p.g));
                JS_SetPropertyUint32(c, data, i + 2, JS_NewInt32(c, p.b));
                JS_SetPropertyUint32(c, data, i + 3, JS_NewInt32(c, p.a));
            }
        JSValue img = JS_NewObject(c);
        JS_SetPropertyStr(c, img, "width", JS_NewInt32(c, sw));
        JS_SetPropertyStr(c, img, "height", JS_NewInt32(c, sh));
        JS_SetPropertyStr(c, img, "data", data);
        return img;
    }, 4);
    m("putImageData", [](JSContext* c, JSValueConst t, int argc, JSValueConst* argv) -> JSValue {
        auto* e = c2d_of(t);
        if (!e || argc < 1) return JS_UNDEFINED;
        double dx = argc > 1 ? argf(c, argv[1]) : 0, dy = argc > 2 ? argf(c, argv[2]) : 0;
        JSValue data = JS_GetPropertyStr(c, argv[0], "data");
        JSValue wv = JS_GetPropertyStr(c, argv[0], "width");
        JSValue hv = JS_GetPropertyStr(c, argv[0], "height");
        int iw = 0, ih = 0;
        JS_ToInt32(c, &iw, wv); JS_ToInt32(c, &ih, hv);
        JS_FreeValue(c, wv); JS_FreeValue(c, hv);
        if (iw <= 0 || ih <= 0) { JS_FreeValue(c, data); return JS_UNDEFINED; }
        auto& bm = e->bitmap();
        auto& px = bm.get_pixels_mut();
        for (int y = 0; y < ih; ++y)
            for (int x = 0; x < iw; ++x) {
                JSValue idx = JS_NewInt32(c, (y * iw + x) * 4);
                JSValue r0 = JS_GetPropertyUint32(c, data, uint32_t((y * iw + x) * 4 + 0));
                JSValue g0 = JS_GetPropertyUint32(c, data, uint32_t((y * iw + x) * 4 + 1));
                JSValue b0 = JS_GetPropertyUint32(c, data, uint32_t((y * iw + x) * 4 + 2));
                JSValue a0 = JS_GetPropertyUint32(c, data, uint32_t((y * iw + x) * 4 + 3));
                uint32_t r = 0, g = 0, b = 0, a = 255;
                JS_ToUint32(c, &r, r0); JS_ToUint32(c, &g, g0);
                JS_ToUint32(c, &b, b0); JS_ToUint32(c, &a, a0);
                JS_FreeValue(c, r0); JS_FreeValue(c, g0);
                JS_FreeValue(c, b0); JS_FreeValue(c, a0);
                JS_FreeValue(c, idx);
                int bx = int(dx) + x, by = int(dy) + y;
                if (bx >= 0 && by >= 0 && bx < bm.get_width() && by < bm.get_height())
                    px[size_t(by) * bm.get_width() + bx] =
                        renderer::RGBA{uint8_t(r), uint8_t(g), uint8_t(b), uint8_t(a)};
            }
        JS_FreeValue(c, data);
        return JS_UNDEFINED;
    }, 4);
    m("createImageData", [](JSContext* c, JSValueConst, int argc, JSValueConst* argv) -> JSValue {
        if (argc < 2) return JS_NULL;
        int w = int(argf(c, argv[0])), h = int(argf(c, argv[1]));
        JSValue data = JS_NewArray(c);
        for (int i = 0; i < w * h * 4; ++i)
            JS_SetPropertyUint32(c, data, uint32_t(i), JS_NewInt32(c, 0));
        JSValue img = JS_NewObject(c);
        JS_SetPropertyStr(c, img, "width", JS_NewInt32(c, w));
        JS_SetPropertyStr(c, img, "height", JS_NewInt32(c, h));
        JS_SetPropertyStr(c, img, "data", data);
        return img;
    }, 2);
    // style properties — the 8 WHATWG attributes (real Canvas2D fields).
    // Plain function-pointer wrappers (captureless lambdas cannot carry the
    // accessor pointers; the getters have the 2-arg shape).
    struct C2DAcc { const char* name; JSCFunction* get; JSCFunction* set; };
    static const C2DAcc kC2dAccs[] = {
        {"fillStyle", c2d_fillStyle_get, c2d_fillStyle_set},
        {"strokeStyle", c2d_strokeStyle_get, c2d_strokeStyle_set},
        {"globalAlpha", c2d_globalAlpha_get, c2d_globalAlpha_set},
        {"globalCompositeOperation", c2d_gco_get, c2d_gco_set},
        {"lineWidth", c2d_lineWidth_get, c2d_lineWidth_set},
        {"font", c2d_font_get, c2d_font_set},
        {"textAlign", c2d_textAlign_get, c2d_textAlign_set},
        {"textBaseline", c2d_textBaseline_get, c2d_textBaseline_set},
    };
    for (const auto& a : kC2dAccs) {
        JSAtom at = JS_NewAtom(ctx, a.name);
        JS_DefinePropertyGetSet(ctx, o, at, JS_NewCFunction(ctx, a.get, a.name, 0),
                                JS_NewCFunction(ctx, a.set, a.name, 1), JS_PROP_C_W_E);
        JS_FreeAtom(ctx, at);
    }
    return o;
}

// 2-arg getters / 4-arg setters wrapped into JSCFunction shape (ROOT-049)
static JSValue c2d_fillStyle_get(JSContext* c, JSValueConst t, int, JSValueConst*) { return c2d_get_fillStyle(c, t); }
static JSValue c2d_fillStyle_set(JSContext* c, JSValueConst t, int n, JSValueConst* a) { c2d_set_fillStyle(c, t, n, a); return JS_UNDEFINED; }
static JSValue c2d_strokeStyle_get(JSContext* c, JSValueConst t, int, JSValueConst*) { return c2d_get_strokeStyle(c, t); }
static JSValue c2d_strokeStyle_set(JSContext* c, JSValueConst t, int n, JSValueConst* a) { c2d_set_strokeStyle(c, t, n, a); return JS_UNDEFINED; }
static JSValue c2d_globalAlpha_get(JSContext* c, JSValueConst t, int, JSValueConst*) { return c2d_get_globalAlpha(c, t); }
static JSValue c2d_globalAlpha_set(JSContext* c, JSValueConst t, int n, JSValueConst* a) { c2d_set_globalAlpha(c, t, n, a); return JS_UNDEFINED; }
static JSValue c2d_gco_get(JSContext* c, JSValueConst t, int, JSValueConst*) { return c2d_get_gco(c, t); }
static JSValue c2d_gco_set(JSContext* c, JSValueConst t, int n, JSValueConst* a) { c2d_set_gco(c, t, n, a); return JS_UNDEFINED; }
static JSValue c2d_lineWidth_get(JSContext* c, JSValueConst t, int, JSValueConst*) { return c2d_get_lineWidth(c, t); }
static JSValue c2d_lineWidth_set(JSContext* c, JSValueConst t, int n, JSValueConst* a) { c2d_set_lineWidth(c, t, n, a); return JS_UNDEFINED; }
static JSValue c2d_font_get(JSContext* c, JSValueConst t, int, JSValueConst*) { return c2d_get_font(c, t); }
static JSValue c2d_font_set(JSContext* c, JSValueConst t, int n, JSValueConst* a) { c2d_set_font(c, t, n, a); return JS_UNDEFINED; }
static JSValue c2d_textAlign_get(JSContext* c, JSValueConst t, int, JSValueConst*) { return c2d_get_textAlign(c, t); }
static JSValue c2d_textAlign_set(JSContext* c, JSValueConst t, int n, JSValueConst* a) { c2d_set_textAlign(c, t, n, a); return JS_UNDEFINED; }
static JSValue c2d_textBaseline_get(JSContext* c, JSValueConst t, int, JSValueConst*) { return c2d_get_textBaseline(c, t); }
static JSValue c2d_textBaseline_set(JSContext* c, JSValueConst t, int n, JSValueConst* a) { c2d_set_textBaseline(c, t, n, a); return JS_UNDEFINED; }
static JSValue c2d_create_linear_gradient(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* c = c2d_of(this_v);
    if (!c || argc < 4) return JS_NULL;
    auto* g = new Gradient();
    g->type = 0;
    (void)g;
    g->x0 = float(argf(ctx, argv[0])); g->y0 = float(argf(ctx, argv[1]));
    g->x1 = float(argf(ctx, argv[2])); g->y1 = float(argf(ctx, argv[3]));
    JSValue o = JS_NewObjectClass(ctx, kGradientClass);
    JS_SetOpaque(o, g);
    JS_SetPropertyStr(ctx, o, "addColorStop", JS_NewCFunction(ctx, grad_addColorStop, "addColorStop", 2));
    return o;
}
static JSValue c2d_create_radial_gradient(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* c = c2d_of(this_v);
    if (!c || argc < 6) return JS_NULL;
    auto* g = new Gradient();
    g->type = 1;
    g->x0 = float(argf(ctx, argv[0])); g->y0 = float(argf(ctx, argv[1])); g->r0 = float(argf(ctx, argv[2]));
    g->x1 = float(argf(ctx, argv[3])); g->y1 = float(argf(ctx, argv[4])); g->r1 = float(argf(ctx, argv[5]));
    JSValue o = JS_NewObjectClass(ctx, kGradientClass);
    JS_SetOpaque(o, g);
    JS_SetPropertyStr(ctx, o, "addColorStop", JS_NewCFunction(ctx, grad_addColorStop, "addColorStop", 2));
    return o;
}

// ── timers / rAF / storage / window ─────────────────────────────────────
static JSValue win_setTimeout(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv) {
    auto* impl = impl_of(ctx);
    if (argc < 1 || !JS_IsFunction(ctx, argv[0])) return JS_NewInt32(ctx, 0);
    double ms = argc >= 2 ? argf(ctx, argv[1]) : 0;
    int id = impl->next_timer_id++;
    std::vector<JSValue> args;
    for (int i = 2; i < argc; ++i) args.push_back(JS_DupValue(ctx, argv[i]));
    impl->timers[id] = {impl->now() + ms, 0, JS_DupValue(ctx, argv[0]), false};
    impl->timer_args_[id] = std::move(args);
    return JS_NewInt32(ctx, id);
}
static JSValue win_setInterval(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv) {
    auto* impl = impl_of(ctx);
    if (argc < 1 || !JS_IsFunction(ctx, argv[0])) return JS_NewInt32(ctx, 0);
    double ms = argc >= 2 ? argf(ctx, argv[1]) : 0;
    if (ms <= 0) ms = 1;
    int id = impl->next_timer_id++;
    std::vector<JSValue> args;
    for (int i = 2; i < argc; ++i) args.push_back(JS_DupValue(ctx, argv[i]));
    impl->timers[id] = {impl->now() + ms, ms, JS_DupValue(ctx, argv[0]), true};
    impl->timer_args_[id] = std::move(args);
    return JS_NewInt32(ctx, id);
}
static JSValue win_clearTimer(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv) {
    auto* impl = impl_of(ctx);
    if (argc >= 1) {
        int32_t id = 0; JS_ToInt32(ctx, &id, argv[0]);
        auto it = impl->timers.find(id);
        if (it != impl->timers.end()) {
            JS_FreeValue(ctx, it->second.func);
            impl->timers.erase(it);
            impl->timer_args_.erase(id);
        }
    }
    return JS_UNDEFINED;
}
static JSValue win_requestAnimationFrame(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv) {
    auto* impl = impl_of(ctx);
    if (argc < 1 || !JS_IsFunction(ctx, argv[0])) return JS_NewInt32(ctx, 0);
    impl->raf_queue.push_back({JS_DupValue(ctx, argv[0]), impl->now()});
    return JS_NewInt32(ctx, int(impl->raf_queue.size()));
}
static JSValue storage_getItem(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* impl = impl_of(ctx);
    if (argc >= 1) {
        const char* k = JS_ToCString(ctx, argv[0]);
        if (k) {
            auto it = impl->kv.find(k);
            JS_FreeCString(ctx, k);
            if (it != impl->kv.end()) return JS_NewString(ctx, it->second.c_str());
        }
    }
    return JS_NULL;
}
static JSValue storage_setItem(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv) {
    auto* impl = impl_of(ctx);
    if (argc >= 2) {
        const char* k = JS_ToCString(ctx, argv[0]);
        const char* v = JS_ToCString(ctx, argv[1]);
        if (k && v) impl->kv[k] = v;
        if (k) JS_FreeCString(ctx, k);
        if (v) JS_FreeCString(ctx, v);
        impl->kv_dirty = true;
    }
    return JS_UNDEFINED;
}
static JSValue storage_removeItem(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv) {
    auto* impl = impl_of(ctx);
    if (argc >= 1) {
        const char* k = JS_ToCString(ctx, argv[0]);
        if (k) { impl->kv.erase(k); JS_FreeCString(ctx, k); }
        impl->kv_dirty = true;
    }
    return JS_UNDEFINED;
}
static JSValue storage_clear(JSContext* ctx, JSValueConst, int, JSValueConst*) {
    auto* impl = impl_of(ctx);
    impl->kv.clear();
    impl->kv_dirty = true;
    return JS_UNDEFINED;
}
static JSValue storage_key(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv) {
    auto* impl = impl_of(ctx);
    int32_t i = 0;
    if (argc >= 1) JS_ToInt32(ctx, &i, argv[0]);
    int idx = 0;
    for (auto& [k, v] : impl->kv) {
        if (idx++ == i) return JS_NewString(ctx, k.c_str());
    }
    return JS_NULL;
}
static JSValue win_get_innerWidth(JSContext* ctx, JSValueConst, int, JSValueConst*) {
    return JS_NewFloat64(ctx, impl_of(ctx)->viewport_w);
}
static JSValue win_get_innerHeight(JSContext* ctx, JSValueConst, int, JSValueConst*) {
    return JS_NewFloat64(ctx, impl_of(ctx)->viewport_h);
}
static JSValue win_get_devicePixelRatio(JSContext* ctx, JSValueConst, int, JSValueConst*) {
    return JS_NewFloat64(ctx, 1.0);
}
static JSValue win_addEventListener(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv) {
    auto* impl = impl_of(ctx);
    if (argc >= 2) {
        const char* type = JS_ToCString(ctx, argv[0]);
        if (type) {
            impl->listeners[nullptr][lower_s(type)].push_back(JS_DupValue(ctx, argv[1]));
            impl->stats.events_registered++;
            JS_FreeCString(ctx, type);
        }
    }
    return JS_UNDEFINED;
}
static JSValue win_matchMedia(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv) {
    JSValue o = JS_NewObject(ctx);
    JS_SetPropertyStr(ctx, o, "matches", JS_FALSE);
    JS_SetPropertyStr(ctx, o, "media", argc >= 1 ? JS_DupValue(ctx, argv[0]) : JS_NewString(ctx, ""));
    JS_SetPropertyStr(ctx, o, "onchange", JS_UNDEFINED);
    JSValue noop = JS_NewCFunction(ctx, [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "noop", 0);
    JS_SetPropertyStr(ctx, o, "addListener", JS_DupValue(ctx, noop));
    JS_SetPropertyStr(ctx, o, "removeListener", JS_DupValue(ctx, noop));
    JS_SetPropertyStr(ctx, o, "addEventListener", JS_DupValue(ctx, noop));
    JS_SetPropertyStr(ctx, o, "removeEventListener", JS_DupValue(ctx, noop));
    JS_SetPropertyStr(ctx, o, "dispatchEvent", JS_NewBool(ctx, false));
    return o;
}
static JSValue win_getComputedStyle(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv) {
    // approximation: the element's own resolved style as a plain object
    JSValue o = JS_NewObject(ctx);
    if (argc >= 1 && JS_IsObject(argv[0])) {
        auto* n = el_of(argv[0]);
        if (n)
            for (auto& kv : n->style)
                JS_SetPropertyStr(ctx, o, kv.first.c_str(), JS_NewString(ctx, kv.second.c_str()));
    }
    JS_SetPropertyStr(ctx, o, "getPropertyValue",
                      JS_NewCFunction(ctx, [](JSContext* ctx2, JSValueConst this_v, int argc2, JSValueConst* argv2) {
                          JSValue sv = JS_GetPropertyStr(ctx2, this_v, "__src__");
                          JSValue r = JS_UNDEFINED;
                          if (argc2 >= 1) {
                              const char* k = JS_ToCString(ctx2, argv2[0]);
                              if (k) {
                                  JSValue v = JS_GetPropertyStr(ctx2, sv, k);
                                  r = JS_IsUndefined(v) ? JS_NewString(ctx2, "") : v;
                                  JS_FreeCString(ctx2, k);
                              }
                          }
                          JS_FreeValue(ctx2, sv);
                          return r;
                      }, "getPropertyValue", 1));
    JS_SetPropertyStr(ctx, o, "__src__", argc >= 1 ? JS_DupValue(ctx, argv[0]) : JS_UNDEFINED);
    return o;
}
static JSValue doc_createElement(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv);
static JSValue doc_createTextNode(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv);
static JSValue doc_getElementById(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv);
static JSValue doc_querySelector(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv);
static JSValue doc_querySelectorAll(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv);
static JSValue doc_getBody(JSContext* ctx, JSValueConst, int, JSValueConst*);
static JSValue doc_getDocEl(JSContext* ctx, JSValueConst, int, JSValueConst*);
static JSValue image_new(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv);
static JSValue image_get_src(JSContext* ctx, JSValueConst this_v, int, JSValueConst*);
static JSValue image_set_src(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv);

// ── document thunks ─────────────────────────────────────────────────────
static JSValue doc_getBody(JSContext* ctx, JSValueConst, int, JSValueConst*) {
    auto* impl = impl_of(ctx);
    return impl->get_element_js(impl->body());
}
static JSValue doc_getDocEl(JSContext* ctx, JSValueConst, int, JSValueConst*) {
    auto* impl = impl_of(ctx);
    return impl->get_element_js(impl->doc.root.get());
}
static JSValue doc_createElement(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv) {
    auto* impl = impl_of(ctx);
    if (argc < 1) return JS_NULL;
    const char* t = JS_ToCString(ctx, argv[0]);
    if (!t) return JS_NULL;
    auto n = std::make_unique<DomNode>();
    n->tag = lower_s(t);
    n->is_canvas = (n->tag == "canvas");
    if (n->is_canvas) n->canvas = std::make_unique<Canvas2D>();
    DomNode* raw = n.get();
    impl->orphans.push_back({raw, std::move(n)});
    JS_FreeCString(ctx, t);
    return impl->get_element_js(raw);
}
static JSValue doc_createTextNode(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv) {
    auto* impl = impl_of(ctx);
    auto n = std::make_unique<DomNode>();
    n->tag = "#text";
    if (argc >= 1) {
        const char* t = JS_ToCString(ctx, argv[0]);
        if (t) { n->text = t; JS_FreeCString(ctx, t); }
    }
    DomNode* raw = n.get();
    impl->orphans.push_back({raw, std::move(n)});
    return impl->get_element_js(raw);
}
static DomNode* find_by_id(DomNode* n, const std::string& id) {
    if (n->attrs.count("id") && n->attrs["id"] == id) return n;
    for (auto& c : n->children) {
        DomNode* r = find_by_id(c.get(), id);
        if (r) return r;
    }
    return nullptr;
}
static void collect_tag(DomNode* n, const std::string& tag, std::vector<DomNode*>& out) {
    if (n->tag == tag) out.push_back(n);
    for (auto& c : n->children) collect_tag(c.get(), tag, out);
}
static JSValue doc_getElementById(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv) {
    auto* impl = impl_of(ctx);
    if (argc < 1) return JS_NULL;
    const char* id = JS_ToCString(ctx, argv[0]);
    if (!id) return JS_NULL;
    DomNode* r = find_by_id(impl->doc.root.get(), id);
    if (!r)
        std::cerr << "[WV-DOC] getElementById MISS: \"" << id << "\"" << std::endl;
    JS_FreeCString(ctx, id);
    return r ? impl->get_element_js(r) : JS_NULL;
}
static JSValue doc_querySelector(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* impl = impl_of(ctx);
    if (argc < 1) return JS_NULL;
    const char* sel = JS_ToCString(ctx, argv[0]);
    if (!sel) return JS_NULL;
    std::string s = sel;
    JS_FreeCString(ctx, sel);
    // S114: querySelector routes through the REAL selector matcher — the old
    // tag/#/.-only branch answered NULL for the attribute grammar
    // (`input[name=sfx]` — every Block'Buster menu read dies there)
    // S118 scope law: on an ELEMENT the search covers the element's subtree
    // (DOM §querySelector; document.querySelector keeps the root scope).
    // The old doc-scope call answered the FIRST doc match even when the app
    // asked `this.element.querySelector(...)` — the wrong node for any app
    // with repeated structures (accelerace's per-car svg path reads).
    DomNode* scope = el_of(this_v);
    if (scope) {
        std::function<DomNode*(DomNode*)> walk2 = [&](DomNode* n) -> DomNode* {
            for (auto& c : n->children) {
                if (c->tag != "#fragment" && HtmlParser::matches_selector(s, c.get())) return c.get();
                DomNode* r = walk2(c.get());
                if (r) return r;
            }
            return nullptr;
        };
        DomNode* hit2 = walk2(scope);
        return hit2 ? impl->get_element_js(hit2) : JS_NULL;
    }
    std::function<DomNode*(DomNode*)> walk = [&](DomNode* n) -> DomNode* {
        if (n->tag != "#fragment" && HtmlParser::matches_selector(s, n)) return n;
        for (auto& c : n->children) { DomNode* r = walk(c.get()); if (r) return r; }
        return nullptr;
    };
    DomNode* hit = walk(impl->doc.root.get());
    return hit ? impl->get_element_js(hit) : JS_NULL;
}
static JSValue doc_querySelectorAll(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv) {
    auto* impl = impl_of(ctx);
    JSValue arr = JS_NewArray(ctx);
    if (argc >= 1) {
        const char* sel = JS_ToCString(ctx, argv[0]);
        if (sel) {
            std::vector<DomNode*> out;
            // S113 selector law: the REAL matcher (tag/.class/#id/compound/
            // descendant) — the old tag-only collect_tag silently answered
            // EMPTY for class selectors, so game.js's
            // querySelectorAll(".choice-button").forEach(addEventListener)
            // registered zero listeners (buttons were tap-dead).
            std::function<void(DomNode*, const std::string&)> collect =
                [&](DomNode* n, const std::string& s) {
                if (n->tag != "#fragment" && HtmlParser::matches_selector(s, n))
                    out.push_back(n);
                for (auto& c : n->children) collect(c.get(), s);
            };
            collect(impl->doc.root.get(), lower_s(sel));
            JS_FreeCString(ctx, sel);
            uint32_t i = 0;
            for (auto* n : out) JS_SetPropertyUint32(ctx, arr, i++, impl->get_element_js(n));
        }
    }
    return arr;
}

// S113 ROOT-060b: getElementsByClassName — live-ish array snapshot law
// (WHATWG DOM §2.7). mykanji's fail dialog writes the correct answer via
// document.getElementsByClassName("correct-answer")[0].
static JSValue doc_getElementsByClassName(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv) {
    auto* impl = impl_of(ctx);
    JSValue arr = JS_NewArray(ctx);
    if (argc >= 1) {
        const char* cls = JS_ToCString(ctx, argv[0]);
        if (cls) {
            std::string want(cls);
            JS_FreeCString(ctx, cls);
            std::function<void(DomNode*)> walk = [&](DomNode* n) {
                auto it = n->attrs.find("class");
                if (it != n->attrs.end()) {
                    std::istringstream ss(it->second);
                    std::string tok;
                    while (ss >> tok)
                        if (tok == want) { impl->get_element_js(n); break; }
                }
                bool matched = false;
                {   // re-check for push (token loop above only probed)
                    auto it2 = n->attrs.find("class");
                    if (it2 != n->attrs.end()) {
                        std::istringstream ss2(it2->second);
                        std::string t2;
                        while (ss2 >> t2) if (t2 == want) { matched = true; break; }
                    }
                }
                if (matched) {
                    // push (index computed via array length below)
                }
                for (auto& c : n->children) walk(c.get());
            };
            // simpler: direct collect
            std::vector<DomNode*> out;
            std::function<void(DomNode*)> collect = [&](DomNode* n) {
                auto it = n->attrs.find("class");
                if (it != n->attrs.end()) {
                    std::istringstream ss(it->second);
                    std::string tok;
                    while (ss >> tok)
                        if (tok == want) { out.push_back(n); break; }
                }
                for (auto& c : n->children) collect(c.get());
            };
            collect(impl->doc.root.get());
            uint32_t i = 0;
            for (auto* n : out) JS_SetPropertyUint32(ctx, arr, i++, impl->get_element_js(n));
        }
    }
    return arr;
}

// ── S133 getElementsByTagName law (DOM §Live collections; array form) ───
// document.getElementsByTagName(tag) walks the live tree in document order
// matching the lowercased tag name ("*" matches all). Measured need: the
// z.ai GTM bootstrap calls d.getElementsByTagName(s)[0] — a missing method
// throws "not a function" and kills the whole analytics inline script.
static JSValue doc_getElementsByTagName(JSContext* ctx, JSValueConst, int argc,
                                        JSValueConst* argv) {
    auto* impl = impl_of(ctx);
    JSValue arr = JS_NewArray(ctx);
    if (argc >= 1) {
        const char* t = JS_ToCString(ctx, argv[0]);
        if (t) {
            std::string want = t;
            JS_FreeCString(ctx, t);
            std::transform(want.begin(), want.end(), want.begin(),
                           [](unsigned char c) { return char(::tolower(c)); });
            std::vector<DomNode*> out;
            std::function<void(DomNode*)> collect = [&](DomNode* n) {
                std::string tag = n->tag;
                std::transform(tag.begin(), tag.end(), tag.begin(),
                               [](unsigned char c) { return char(::tolower(c)); });
                if ((want == "*" && !tag.empty() && tag[0] != '#') || tag == want)
                    out.push_back(n);
                for (auto& c : n->children) collect(c.get());
            };
            collect(impl->doc.root.get());
            uint32_t i = 0;
            for (auto* n : out) JS_SetPropertyUint32(ctx, arr, i++, impl->get_element_js(n));
        }
    }
    return arr;
}

// ── image (new Image()) ─────────────────────────────────────────────────
static JSValue image_new(JSContext* ctx, JSValueConst, int, JSValueConst*) {
    auto* impl = impl_of(ctx);
    auto* im = new ImageObj();
    impl->owned_images.push_back(im);
    JSValue o = JS_NewObjectClass(ctx, kImageClass);
    JS_SetOpaque(o, im);
    JSAtom sa = JS_NewAtom(ctx, "src");
    JS_DefinePropertyGetSet(ctx, o, sa, JS_NewCFunction(ctx, image_get_src, "src", 0),
                            JS_NewCFunction(ctx, image_set_src, "src", 1), JS_PROP_C_W_E);
    JS_FreeAtom(ctx, sa);
    return o;
}
// S114 HTMLAudioElement constructor law (HTML §4.8.3): `new Audio(src)` —
// play() returns a promise-like that resolves silently (no audio sink; the
// el_media_play contract) — Block'Buster's start() gates on it.
static JSValue audio_new(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv) {
    JSValue o = JS_NewObject(ctx);
    if (argc >= 1 && JS_IsString(argv[0]))
        JS_SetPropertyStr(ctx, o, "src", JS_DupValue(ctx, argv[0]));
    JS_SetPropertyStr(ctx, o, "play", JS_NewCFunction(ctx, [](JSContext* c, JSValueConst, int, JSValueConst*) -> JSValue {
        JSValue p = JS_NewObject(c);
        JS_SetPropertyStr(c, p, "catch", JS_NewCFunction(c, [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "catch", 1));
        JS_SetPropertyStr(c, p, "then", JS_NewCFunction(c, [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "then", 1));
        return p;
    }, "play", 0));
    JS_SetPropertyStr(ctx, o, "pause", JS_NewCFunction(ctx, [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "pause", 0));
    JS_SetPropertyStr(ctx, o, "load", JS_NewCFunction(ctx, [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "load", 0));
    JS_SetPropertyStr(ctx, o, "volume", JS_NewFloat64(ctx, 1.0));
    JS_SetPropertyStr(ctx, o, "loop", JS_FALSE);
    return o;
}
static void image_decode(ImageObj* im, WebViewEngine::Impl* impl) {
    auto bytes = impl->fetch_resource(im->src, "img-src");
    if (bytes.empty()) {
        std::cerr << "[WV-IMAGE] asset missing: " << im->src << std::endl;
        return;
    }
    int w = 0, h = 0, ch = 0;
    stbi_uc* data = stbi_load_from_memory(bytes.data(), int(bytes.size()), &w, &h, &ch, 4);
    if (!data) {
        std::cerr << "[WV-IMAGE] decode failed: " << im->src << std::endl;
        return;
    }
    im->fb = std::make_unique<renderer::FrameBuffer>(w, h);
    im->fb->set_alpha_preserve(true);
    auto& px = im->fb->get_pixels_mut();
    for (int i = 0; i < w * h; ++i) {
        px[i] = renderer::RGBA{data[i * 4], data[i * 4 + 1], data[i * 4 + 2], data[i * 4 + 3]};
    }
    stbi_image_free(data);
    im->natural_w = w;
    im->natural_h = h;
    im->complete = true;
    std::cerr << "[WV-IMAGE] decoded " << im->src << " " << w << "x" << h << std::endl;
}
static JSValue image_get_src(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* im = (ImageObj*)JS_GetOpaque(this_v, kImageClass);
    return JS_NewString(ctx, im ? im->src.c_str() : "");
}
static JSValue image_set_src(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    auto* im = (ImageObj*)JS_GetOpaque(this_v, kImageClass);
    if (im && argc >= 1) {
        const char* s = JS_ToCString(ctx, argv[0]);
        if (s) {
            im->src = s;
            JS_FreeCString(ctx, s);
            image_decode(im, impl_of(ctx));
            // onload dispatch
            JSValue onload = JS_GetPropertyStr(ctx, this_v, "onload");
            if (JS_IsFunction(ctx, onload)) {
                JSValue ev = JS_NewObject(ctx);
                JSValue r = JS_Call(ctx, onload, this_v, 1, &ev);
                JS_FreeValue(ctx, r);
                JS_FreeValue(ctx, ev);
            }
            JS_FreeValue(ctx, onload);
        }
    }
    return JS_UNDEFINED;
}

// ── element materialization ─────────────────────────────────────────────
static void define_element_members(JSContext* ctx, JSValue o, DomNode* n);

JSValue WebViewEngine::Impl::get_element_js(DomNode* n) {
    auto it = el_objs.find(n);
    if (it != el_objs.end()) return JS_DupValue(ctx, it->second);
    JSValue o = JS_NewObjectClass(ctx, kElementClass);
    if (JS_IsException(o)) { report_exception("element alloc"); return o; }
    JS_SetOpaque(o, n);
    define_element_members(ctx, o, n);
    el_objs[n] = JS_DupValue(ctx, o);
    return o;
}

static void define_element_members(JSContext* ctx, JSValue o, DomNode* n) {
    (void)n;
    auto def_get = [&](const char* name, JSCFunction* g) {
        JS_SetPropertyStr(ctx, o, name,
                          JS_NewCFunction(ctx, g, name, 0));  // simplified: getter-as-function
        // actual accessor:
        (void)0;
    };
    (void)def_get;
    auto accessor = [&](const char* name, JSCFunction* g, JSCFunction* s) {
        JSAtom a = JS_NewAtom(ctx, name);
        JS_DefinePropertyGetSet(ctx, o, a, JS_NewCFunction(ctx, g, name, 0),
                                s ? JS_NewCFunction(ctx, s, name, 1) : JS_UNDEFINED,
                                JS_PROP_C_W_E);
        JS_FreeAtom(ctx, a);
    };
    auto method = [&](const char* name, JSCFunction* f, int len) {
        JS_SetPropertyStr(ctx, o, name, JS_NewCFunction(ctx, f, name, len));
    };
    accessor("id", el_get_id, el_set_id);
    accessor("tagName", el_get_tag, nullptr);
    accessor("nodeName", el_get_tag, nullptr);
    // S114 form-element property law: .value/.checked are ATTRIBUTE-backed
    // (HTML §4.10 — `input[name=size]:checked`.value drives game menus)
    accessor("value", el_get_value_prop, el_setAttribute);
    accessor("checked", el_get_checked_prop, el_set_checked_prop);
    accessor("className", el_get_class_name, el_set_class_name);
    accessor("name", el_getAttribute, nullptr);
    accessor("type", el_getAttribute, nullptr);
    accessor("innerHTML", el_get_inner_html, el_set_inner_html);
    accessor("innerText", el_get_text, el_set_text);
    accessor("textContent", el_get_text, el_set_text);
    accessor("style", el_get_style, nullptr);
    accessor("classList", el_get_class_list2, nullptr);
    accessor("children", el_get_children, nullptr);
    accessor("parentElement", el_get_parent, nullptr);
    accessor("parentNode", el_get_parent, nullptr);
    accessor("firstChild", el_get_first_child, nullptr);
    // S117 DOM traversal law: full WHATWG sibling/child family
    accessor("nextElementSibling", el_get_next_element_sibling, nullptr);
    accessor("previousElementSibling", el_get_prev_element_sibling, nullptr);
    accessor("nextSibling", el_get_next_sibling, nullptr);
    accessor("previousSibling", el_get_prev_sibling, nullptr);
    accessor("firstElementChild", el_get_first_element_child, nullptr);
    accessor("lastElementChild", el_get_last_element_child, nullptr);
    accessor("lastChild", el_get_last_child, nullptr);
    accessor("childElementCount", el_get_child_element_count, nullptr);
    accessor("offsetWidth", el_get_offset_w, nullptr);
    accessor("offsetHeight", el_get_offset_h, nullptr);
    method("setAttribute", el_setAttribute, 2);
    method("getAttribute", el_getAttribute, 1);
    method("hasAttribute", el_hasAttribute, 1);
    method("removeAttribute", el_removeAttribute, 1);
    method("appendChild", el_append_child, 1);
    method("removeChild", el_remove_child, 1);
    method("insertBefore", el_insert_before, 2);
    method("remove", el_remove, 0);
    method("addEventListener", el_addEventListener, 2);
    method("removeEventListener", el_removeEventListener, 2);
    method("getBoundingClientRect", el_getBoundingClientRect, 0);
    method("click", el_click, 0);
    method("focus", el_focus, 0);
    // S113 ROOT-060: HTMLMediaElement law — play()/pause() exist on media
    // elements; play() returns a promise (the app chains .catch on it).
    // This runtime renders without an audio device: play resolves silently
    // (honest degradation — the app's visual flow continues, which is what
    // mykanji's sound.play().catch(...) gates).
    method("play", el_media_play, 0);
    method("pause", el_media_pause, 0);
    method("querySelector", doc_querySelector, 1);
    method("querySelectorAll", doc_querySelectorAll, 1);
    // canvas props + getContext
    method("getContext", el_getContext, 1);
    accessor("width", el_get_canvas_w, el_set_canvas_w);
    accessor("height", el_get_canvas_h, el_set_canvas_h);
    // HTMLInputElement-ish value accessor: reads/writes the value attribute
    method("getValue", el_getAttribute, 1);
}

// ── event dispatch (capture skipped; bubble = target→root walk) ─────────
void WebViewEngine::Impl::dispatch(DomNode* target, const std::string& type0, JSValue ev) {
    stats.events_dispatched++;
    // event-type case law: listener maps are keyed by the lowercased type
    // (win_addEventListener lowercases at registration) — mixed-case
    // dispatches ("DOMContentLoaded") used to miss every listener
    std::string type = lower_s(type0);
    // S114 INLINE EVENT ATTRIBUTE law (HTML §6.1.6.1): onclick=, ontouchstart=
    // … are compiled and invoked as handlers through the capture chain —
    // Block'Buster's Start button (`<button onclick="start()">`) and most
    // HTML5 game menus wire through attributes, not addEventListener.
    std::string attr = "on" + lower_s(type);
    JSValue earg[1] = {ev};
    for (DomNode* n = target; n; n = n->parent) {
        auto ait = n->attrs.find(attr);
        if (ait != n->attrs.end() && !ait->second.empty()) {
            // compile-once cache: (node, attr) → function
            uint64_t ckey = (uint64_t)(uintptr_t)n * 2654435761u ^
                            (uint64_t)(uint32_t)std::hash<std::string>()(attr);
            auto fit = inline_handlers.find(ckey);
            JSValue fn;
            if (fit != inline_handlers.end()) {
                fn = fit->second;
            } else {
                std::string src = "(function(event){ with(document) { with(this) { "
                                  + ait->second + " } } })";
                fn = JS_Eval(ctx, src.c_str(), src.size(), "<inline-handler>",
                             JS_EVAL_TYPE_GLOBAL);
                if (JS_IsException(fn)) { report_exception("inline " + attr); continue; }
                inline_handlers[ckey] = fn;
            }
            set_deadline(5.0);
            JSValue r = JS_Call(ctx, fn, get_element_js(n), 1, earg);
            if (JS_IsException(r)) report_exception("inline " + attr);
            JS_FreeValue(ctx, r);
        }
    }
    std::vector<DomNode*> chain;
    for (DomNode* n = target; n; n = n->parent) chain.push_back(n);
    for (auto* n : chain) {
        auto lit = listeners.find(n);
        if (lit == listeners.end()) continue;
        auto vit = lit->second.find(type);
        if (vit == lit->second.end()) continue;
        JS_SetPropertyStr(ctx, ev, "currentTarget",
                          n == target ? JS_GetPropertyStr(ctx, ev, "target")
                                      : get_element_js(n));
        for (auto& f : vit->second) {
            set_deadline(5.0);
            JSValue r = JS_Call(ctx, f, JS_UNDEFINED, 1, &ev);
            if (JS_IsException(r)) report_exception("listener " + type);
            JS_FreeValue(ctx, r);
        }
    }
    // window/document-level listeners (nullptr key)
    auto lit = listeners.find(nullptr);
    if (lit != listeners.end()) {
        auto vit = lit->second.find(type);
        if (vit != lit->second.end()) {
            for (auto& f : vit->second) {
                set_deadline(5.0);
                JSValue r = JS_Call(ctx, f, JS_UNDEFINED, 1, &ev);
                if (JS_IsException(r)) report_exception("window listener " + type);
                JS_FreeValue(ctx, r);
            }
        }
    }
}

// ── bindings setup ──────────────────────────────────────────────────────
void WebViewEngine::Impl::setup_bindings() {
    setup_style_class(rt);
    ctx = JS_NewContext(rt);
    JS_SetContextOpaque(ctx, this);
    // Custom classes need REAL prototype objects: JS_NewObjectClass with an
    // unset class proto leaves proto = JS_NULL (OBJECT tag, NULL ptr) — any
    // property miss then walks into NULL and SEGVs. (S109 root cause.)
    {
        JSValue p;
        p = JS_NewObject(ctx); JS_SetClassProto(ctx, kElementClass, p);
        p = JS_NewObject(ctx); JS_SetClassProto(ctx, kCtx2DClass, p);
        p = JS_NewObject(ctx); JS_SetClassProto(ctx, kStyleClass, p);
        p = JS_NewObject(ctx); JS_SetClassProto(ctx, kStorageClass, p);
        p = JS_NewObject(ctx); JS_SetClassProto(ctx, kPatternClass, p);
        p = JS_NewObject(ctx); JS_SetClassProto(ctx, kImageClass, p);
        p = JS_NewObject(ctx); JS_SetClassProto(ctx, kGradientClass, p);
    }

    // S114 WINDOW===GLOBAL law (WHATWG HTML §8.1: the Window IS the global
    // object). The engine previously used a SEPARATE plain object for window,
    // so `window.asafonov = {}` was invisible to bare-identifier code —
    // Block'Buster's inline onclick start() died with "'asafonov' is not
    // defined". window now references the real global object.
    window_obj = JS_GetGlobalObject(ctx);
    JSValue global = JS_GetGlobalObject(ctx);
    {
        // console — full Chromium DevTools console contract (all members are
        // FUNCTIONS; missing members are a law violation that kills real web
        // apps: e.g. Breakout 71's migration runner calls console.debug after
        // every successful migration, and one missing member aborted all 8
        // migrations + the main inline script with "TypeError: not a function").
        // log-level family (debug/trace/dir/dirxml/table alias log output)
        JSValue con = JS_NewObject(ctx);
        JS_SetPropertyStr(ctx, con, "log", JS_NewCFunction(ctx, js_console_log, "log", 1));
        JS_SetPropertyStr(ctx, con, "info", JS_NewCFunction(ctx, js_console_log, "info", 1));
        JS_SetPropertyStr(ctx, con, "warn", JS_NewCFunction(ctx, js_console_log, "warn", 1));
        JS_SetPropertyStr(ctx, con, "error", JS_NewCFunction(ctx, js_console_log, "error", 1));
        JS_SetPropertyStr(ctx, con, "debug", JS_NewCFunction(ctx, js_console_log, "debug", 1));
        JS_SetPropertyStr(ctx, con, "trace", JS_NewCFunction(ctx, js_console_log, "trace", 1));
        JS_SetPropertyStr(ctx, con, "dir", JS_NewCFunction(ctx, js_console_log, "dir", 1));
        JS_SetPropertyStr(ctx, con, "dirxml", JS_NewCFunction(ctx, js_console_log, "dirxml", 1));
        JS_SetPropertyStr(ctx, con, "table", JS_NewCFunction(ctx, js_console_log, "table", 1));
        // no-op-but-lawful diagnostics family (must exist as functions)
        for (const char* m : {"time", "timeLog", "timeEnd", "timeStamp", "count", "countReset",
                              "group", "groupCollapsed", "groupEnd", "clear", "profile", "profileEnd"}) {
            JS_SetPropertyStr(ctx, con, m, JS_NewCFunction(ctx, [](JSContext*, JSValueConst, int, JSValueConst*) {
                return JS_UNDEFINED;
            }, m, 0));
        }
        // assert: no-op when the condition is truthy, logs "Assertion failed: ..." otherwise
        JS_SetPropertyStr(ctx, con, "assert", JS_NewCFunction(ctx, [](JSContext* c, JSValueConst, int argc, JSValueConst* argv) {
            bool truthy = argc > 0 && JS_ToBool(c, argv[0]);
            if (!truthy) {
                std::ostringstream oss;
                oss << "Assertion failed:";
                for (int i = 1; i < argc; ++i) {
                    const char* s = JS_ToCString(c, argv[i]);
                    if (s) { oss << ' ' << s; JS_FreeCString(c, s); }
                }
                std::cerr << "[WV-CONSOLE] " << oss.str() << std::endl;
            }
            return JS_UNDEFINED;
        }, "assert", 1));
        JS_SetPropertyStr(ctx, global, "console", con);
        // base64
        JS_SetPropertyStr(ctx, global, "btoa", JS_NewCFunction(ctx, js_btoa, "btoa", 1));
        JS_SetPropertyStr(ctx, global, "atob", JS_NewCFunction(ctx, js_atob, "atob", 1));
        // timers
        JS_SetPropertyStr(ctx, global, "setTimeout", JS_NewCFunction(ctx, win_setTimeout, "setTimeout", 1));
        JS_SetPropertyStr(ctx, global, "setInterval", JS_NewCFunction(ctx, win_setInterval, "setInterval", 1));
        JS_SetPropertyStr(ctx, global, "clearTimeout", JS_NewCFunction(ctx, win_clearTimer, "clearTimeout", 1));
        JS_SetPropertyStr(ctx, global, "clearInterval", JS_NewCFunction(ctx, win_clearTimer, "clearInterval", 1));
        JS_SetPropertyStr(ctx, global, "requestAnimationFrame",
                          JS_NewCFunction(ctx, win_requestAnimationFrame, "requestAnimationFrame", 1));
        // window alias on global
        JS_SetPropertyStr(ctx, global, "window", JS_DupValue(ctx, window_obj));
        JS_SetPropertyStr(ctx, global, "self", JS_DupValue(ctx, window_obj));
        // window members (also on global)
        for (JSValue* tgt : {&window_obj, &global}) {
            JS_SetPropertyStr(ctx, *tgt, "setTimeout", JS_NewCFunction(ctx, win_setTimeout, "setTimeout", 1));
            JS_SetPropertyStr(ctx, *tgt, "setInterval", JS_NewCFunction(ctx, win_setInterval, "setInterval", 1));
            JS_SetPropertyStr(ctx, *tgt, "clearTimeout", JS_NewCFunction(ctx, win_clearTimer, "clearTimeout", 1));
            JS_SetPropertyStr(ctx, *tgt, "clearInterval", JS_NewCFunction(ctx, win_clearTimer, "clearInterval", 1));
            JS_SetPropertyStr(ctx, *tgt, "requestAnimationFrame",
                              JS_NewCFunction(ctx, win_requestAnimationFrame, "requestAnimationFrame", 1));
            JS_SetPropertyStr(ctx, *tgt, "addEventListener",
                              JS_NewCFunction(ctx, win_addEventListener, "addEventListener", 2));
            JS_SetPropertyStr(ctx, *tgt, "removeEventListener",
                              JS_NewCFunction(ctx, el_removeEventListener, "removeEventListener", 2));
            JS_SetPropertyStr(ctx, *tgt, "matchMedia", JS_NewCFunction(ctx, win_matchMedia, "matchMedia", 1));
            JS_SetPropertyStr(ctx, *tgt, "getComputedStyle",
                              JS_NewCFunction(ctx, win_getComputedStyle, "getComputedStyle", 1));
            JS_SetPropertyStr(ctx, *tgt, "open", JS_NewCFunction(ctx, [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_NULL; }, "open", 1));
            JS_SetPropertyStr(ctx, *tgt, "close", JS_NewCFunction(ctx, [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "close", 0));
            JS_SetPropertyStr(ctx, *tgt, "scrollTo", JS_NewCFunction(ctx, [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "scrollTo", 2));
            JS_SetPropertyStr(ctx, *tgt, "Image", make_ctor(ctx, image_new, "Image", 0));
            JS_SetPropertyStr(ctx, *tgt, "Audio", make_ctor(ctx, audio_new, "Audio", 0));
            JS_SetPropertyStr(ctx, *tgt, "devicePixelRatio", JS_NewFloat64(ctx, 1.0));
        }
        // innerWidth/innerHeight accessors on global + window
        JSAtom wi = JS_NewAtom(ctx, "innerWidth");
        JS_DefinePropertyGetSet(ctx, global, wi, JS_NewCFunction(ctx, win_get_innerWidth, "innerWidth", 0), JS_UNDEFINED, JS_PROP_C_W_E);
        JS_DefinePropertyGetSet(ctx, window_obj, wi, JS_NewCFunction(ctx, win_get_innerWidth, "innerWidth", 0), JS_UNDEFINED, JS_PROP_C_W_E);
        JS_FreeAtom(ctx, wi);
        JSAtom hi = JS_NewAtom(ctx, "innerHeight");
        JS_DefinePropertyGetSet(ctx, global, hi, JS_NewCFunction(ctx, win_get_innerHeight, "innerHeight", 0), JS_UNDEFINED, JS_PROP_C_W_E);
        JS_DefinePropertyGetSet(ctx, window_obj, hi, JS_NewCFunction(ctx, win_get_innerHeight, "innerHeight", 0), JS_UNDEFINED, JS_PROP_C_W_E);
        JS_FreeAtom(ctx, hi);
        // document
        document_obj = JS_NewObject(ctx);
        JS_SetPropertyStr(ctx, document_obj, "getElementById", JS_NewCFunction(ctx, doc_getElementById, "getElementById", 1));
        JS_SetPropertyStr(ctx, document_obj, "querySelector", JS_NewCFunction(ctx, doc_querySelector, "querySelector", 1));
        JS_SetPropertyStr(ctx, document_obj, "querySelectorAll", JS_NewCFunction(ctx, doc_querySelectorAll, "querySelectorAll", 1));
        JS_SetPropertyStr(ctx, document_obj, "getElementsByClassName", JS_NewCFunction(ctx, doc_getElementsByClassName, "getElementsByClassName", 1));
        JS_SetPropertyStr(ctx, document_obj, "getElementsByTagName", JS_NewCFunction(ctx, doc_getElementsByTagName, "getElementsByTagName", 1));
        JS_SetPropertyStr(ctx, document_obj, "createElement", JS_NewCFunction(ctx, doc_createElement, "createElement", 1));
        JS_SetPropertyStr(ctx, document_obj, "createTextNode", JS_NewCFunction(ctx, doc_createTextNode, "createTextNode", 1));
        JS_SetPropertyStr(ctx, document_obj, "addEventListener", JS_NewCFunction(ctx, win_addEventListener, "addEventListener", 2));
        JS_SetPropertyStr(ctx, document_obj, "body", JS_UNDEFINED);  // accessor-ish below
        {
            // body/documentElement as getters (lazy materialization)
            JSAtom ba = JS_NewAtom(ctx, "body");
            JS_DefinePropertyGetSet(ctx, document_obj, ba,
                                    JS_NewCFunction(ctx, doc_getBody, "body", 0), JS_UNDEFINED, JS_PROP_C_W_E);
            JS_FreeAtom(ctx, ba);
            JSAtom ha = JS_NewAtom(ctx, "documentElement");
            JS_DefinePropertyGetSet(ctx, document_obj, ha,
                                    JS_NewCFunction(ctx, doc_getDocEl, "documentElement", 0), JS_UNDEFINED, JS_PROP_C_W_E);
            JS_FreeAtom(ctx, ha);
            JSAtom ta = JS_NewAtom(ctx, "title");
            JS_DefinePropertyGetSet(ctx, document_obj, ta,
                                    JS_NewCFunction(ctx, [](JSContext* c, JSValueConst, int, JSValueConst*) {
                                        return JS_NewString(c, impl_of(c)->doc.title.c_str());
                                    }, "title", 0), JS_UNDEFINED, JS_PROP_C_W_E);
            JS_FreeAtom(ctx, ta);
        }
        JS_SetPropertyStr(ctx, global, "document", JS_DupValue(ctx, document_obj));
        JS_SetPropertyStr(ctx, window_obj, "document", JS_DupValue(ctx, document_obj));
        // navigator
        JSValue nav = JS_NewObject(ctx);
        JS_SetPropertyStr(ctx, nav, "userAgent",
                          JS_NewString(ctx, "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 MiniAndroid-WebView S109"));
        JS_SetPropertyStr(ctx, nav, "language", JS_NewString(ctx, "en-US"));
        JS_SetPropertyStr(ctx, nav, "languages", JS_NewString(ctx, "en-US"));
        JS_SetPropertyStr(ctx, nav, "onLine", JS_NewBool(ctx, true));
        JS_SetPropertyStr(ctx, global, "navigator", nav);
        // location (full surface: the corpus reads hash/search/href/reload)
        JSValue loc = JS_NewObject(ctx);
        std::string doc_url = self->document_url();
        std::string hash_v, search_v;
        {
            size_t hq = doc_url.find('#');
            if (hq != std::string::npos) { hash_v = doc_url.substr(hq); doc_url = doc_url.substr(0, hq); }
            size_t q = doc_url.find('?');
            if (q != std::string::npos) { search_v = doc_url.substr(q); doc_url = doc_url.substr(0, q); }
        }
        JS_SetPropertyStr(ctx, loc, "href", JS_NewString(ctx, self->document_url().c_str()));
        // S133: reflect the real scheme (hardcoded "file:" misled http(s)
        // document scripts; jQuery's support checks branch on it)
        JS_SetPropertyStr(ctx, loc, "protocol", JS_NewString(
            ctx, (doc_url.rfind("https://", 0) == 0 ? "https:"
                  : doc_url.rfind("http://", 0) == 0 ? "http:" : "file:")));
        JS_SetPropertyStr(ctx, loc, "hash", JS_NewString(ctx, hash_v.c_str()));
        JS_SetPropertyStr(ctx, loc, "search", JS_NewString(ctx, search_v.c_str()));
        JS_SetPropertyStr(ctx, loc, "pathname", JS_NewString(ctx, doc_url.c_str()));
        JS_SetPropertyStr(ctx, loc, "host", JS_NewString(ctx, ""));
        JS_SetPropertyStr(ctx, loc, "hostname", JS_NewString(ctx, ""));
        JS_SetPropertyStr(ctx, loc, "origin", JS_NewString(ctx, "null"));
        JS_SetPropertyStr(ctx, loc, "port", JS_NewString(ctx, ""));
        JS_SetPropertyStr(ctx, loc, "reload", JS_NewCFunction(ctx, [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "reload", 0));
        JS_SetPropertyStr(ctx, loc, "replace", JS_NewCFunction(ctx, [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "replace", 1));
        JS_SetPropertyStr(ctx, global, "location", loc);
        // S133 DOCUMENT-LOCATION alias law (HTML §5.2): document.location
        // IS window.location (same object). jQuery reads
        // document.location.host — the missing alias broke its support
        // checks ("cannot read property 'host' of undefined").
        JS_SetPropertyStr(ctx, document_obj, "location", JS_DupValue(ctx, loc));
        // localStorage (file-backed, per-package)
        storage_obj = JS_NewObjectClass(ctx, kStorageClass);
        JS_SetPropertyStr(ctx, storage_obj, "getItem", JS_NewCFunction(ctx, storage_getItem, "getItem", 1));
        JS_SetPropertyStr(ctx, storage_obj, "setItem", JS_NewCFunction(ctx, storage_setItem, "setItem", 2));
        JS_SetPropertyStr(ctx, storage_obj, "removeItem", JS_NewCFunction(ctx, storage_removeItem, "removeItem", 1));
        JS_SetPropertyStr(ctx, storage_obj, "clear", JS_NewCFunction(ctx, storage_clear, "clear", 0));
        JS_SetPropertyStr(ctx, storage_obj, "key", JS_NewCFunction(ctx, storage_key, "key", 1));
        JS_SetPropertyStr(ctx, storage_obj, "getLength", JS_NewCFunction(ctx,
            [](JSContext* c, JSValueConst, int, JSValueConst*) {
                return JS_NewInt32(c, int(impl_of(c)->kv.size()));
            }, "getLength", 0));
        JS_SetPropertyStr(ctx, global, "localStorage", JS_DupValue(ctx, storage_obj));
        // Math.random → deterministic LCG (3-run evidence determinism; documented deviation)
        JSValue math = JS_GetPropertyStr(ctx, global, "Math");
        JS_SetPropertyStr(ctx, math, "random",
                          JS_NewCFunction(ctx, [](JSContext* c, JSValueConst, int, JSValueConst*) {
                              auto* impl = impl_of(c);
                              impl->rng_state = impl->rng_state * 1664525u + 1013904223u;
                              return JS_NewFloat64(c, double(impl->rng_state >> 8) / double(1 << 24));
                          }, "random", 0));
        JS_FreeValue(ctx, math);
        // performance.now (virtual clock)
        JSValue perf = JS_NewObject(ctx);
        JS_SetPropertyStr(ctx, perf, "now",
                          JS_NewCFunction(ctx, [](JSContext* c, JSValueConst, int, JSValueConst*) {
                              return JS_NewFloat64(c, impl_of(c)->now());
                          }, "now", 0));
        JS_SetPropertyStr(ctx, global, "performance", perf);
        // screen
        JSValue scr = JS_NewObject(ctx);
        JS_SetPropertyStr(ctx, scr, "width", JS_NewFloat64(ctx, viewport_w));
        JS_SetPropertyStr(ctx, scr, "height", JS_NewFloat64(ctx, viewport_h));
        JS_SetPropertyStr(ctx, global, "screen", scr);
        // crypto.getRandomValues (deterministic LCG — 3-run evidence law)
        JSValue crypto_o = JS_NewObject(ctx);
        JS_SetPropertyStr(ctx, crypto_o, "getRandomValues",
            JS_NewCFunction(ctx, [](JSContext* c, JSValueConst, int argc, JSValueConst* argv) {
                if (argc >= 1 && JS_IsObject(argv[0])) {
                    JSValue len_v = JS_GetPropertyStr(c, argv[0], "length");
                    int32_t len = 0; JS_ToInt32(c, &len, len_v);
                    JS_FreeValue(c, len_v);
                    auto* impl = impl_of(c);
                    for (int32_t i = 0; i < len && i < 65536; ++i) {
                        impl->rng_state = impl->rng_state * 1664525u + 1013904223u;
                        JSValue b = JS_NewInt32(c, int(impl->rng_state >> 24));
                        JS_SetPropertyUint32(c, argv[0], uint32_t(i), b);
                    }
                }
                return argc >= 1 ? JS_DupValue(c, argv[0]) : JS_UNDEFINED;
            }, "getRandomValues", 1));
        // S118 WebCrypto digest law: crypto.subtle.digest over the OpenSSL
        // EVP backend (SHA-1/256/384/512 — the corpus signs request URLs
        // through SHA-256 digests of TextEncoder bytes). Real crypto, real
        // semantics: input BufferSource, output ArrayBuffer.
        {
            JSValue subtle = JS_NewObject(ctx);
            JS_SetPropertyStr(ctx, subtle, "digest",
                JS_NewCFunction(ctx, [](JSContext* c, JSValueConst, int argc, JSValueConst* argv) -> JSValue {
                    if (argc < 2) return JS_ThrowTypeError(c, "digest: (algorithm, data)");
                    const char* alg = JS_ToCString(c, argv[0]);
                    if (!alg) return JS_EXCEPTION;
                    std::string a = lower_s(alg);
                    JS_FreeCString(c, alg);
                    const EVP_MD* md = nullptr;
                    if (a == "sha-1" || a == "sha1") md = EVP_sha1();
                    else if (a == "sha-256" || a == "sha256") md = EVP_sha256();
                    else if (a == "sha-384" || a == "sha384") md = EVP_sha384();
                    else if (a == "sha-512" || a == "sha512") md = EVP_sha512();
                    if (!md) return JS_ThrowTypeError(c, "digest: unsupported algorithm");
                    // data: ArrayBuffer | TypedArray (BufferSource)
                    size_t blen = 0;
                    uint8_t* p = JS_GetArrayBuffer(c, &blen, argv[1]);
                    if (!p) {
                        JSValue exc = JS_GetException(c);   // clear the probe error
                        JS_FreeValue(c, exc);
                        size_t off = 0, bl = 0, bpe = 0;
                        JSValue tab = JS_GetTypedArrayBuffer(c, argv[1], &off, &bl, &bpe);
                        if (JS_IsException(tab))
                            return JS_ThrowTypeError(c, "digest: data must be BufferSource");
                        p = JS_GetArrayBuffer(c, &blen, tab);
                        JS_FreeValue(c, tab);
                        if (!p) return JS_ThrowTypeError(c, "digest: detached buffer");
                        p += off; blen = bl;
                    }
                    unsigned char out[EVP_MAX_MD_SIZE];
                    unsigned int olen = 0;
                    if (!EVP_Digest(p, (size_t)blen, out, &olen, md, nullptr))
                        return JS_ThrowInternalError(c, "digest failed");
                    return JS_NewArrayBufferCopy(c, out, olen);
                }, "digest", 2));
            JS_SetPropertyStr(ctx, crypto_o, "subtle", subtle);
        }
        JS_SetPropertyStr(ctx, global, "crypto", crypto_o);
        // S118 TextEncoder/TextDecoder law (UTF-8 byte <-> string, WHATWG
        // Encoding): the corpus encodes digest inputs and decodes fetched
        // bytes through them. Implemented as JS over QuickJS primitives
        // (UTF-8 via escape/unescape Annex-B pair) — byte-exact semantics.
        {
            static const char te_src[] =
                "(function(){"
                "function TextEncoder(){}"
                "TextEncoder.prototype.encode=function(s){"
                " s=unescape(encodeURIComponent(String(s)));"
                " var a=new Uint8Array(s.length);"
                " for(var i=0;i<s.length;++i) a[i]=s.charCodeAt(i)&0xff;"
                " return a;};"
                "TextEncoder.prototype.encoding='utf-8';"
                "function TextDecoder(){"
                " this.decode=function(u8){"
                "  if(!u8) return '';"
                "  var s='';"
                "  if(typeof u8==='string') s=u8;"
                "  else {var n=(u8.byteLength!==undefined)?u8.byteLength:(u8.length||0);"
                "   for(var i=0;i<n;++i) s+=String.fromCharCode(u8[i]);}"
                "  return decodeURIComponent(escape(s));};}"
                "globalThis.TextEncoder=TextEncoder;"
                "globalThis.TextDecoder=TextDecoder;"
                "})()";
            JSValue te = JS_Eval(ctx, te_src, sizeof(te_src) - 1,
                                 "<text-encoding>", JS_EVAL_TYPE_GLOBAL);
            JS_FreeValue(ctx, te);
        }
        // S133 web-vitals/stubs law: telemetry-driven pages reference
        // PerformanceObserver at load; a missing global throws a
        // ReferenceError that kills the whole inline script (z.ai's first
        // inline bundle died here BEFORE its real payload ran). The stub
        // records nothing but keeps the calling script alive — the honest
        // semantic is "observer registered, no metrics available".
        {
            static const char po_src[] =
                "(function(){"
                "function PerformanceObserver(cb){"
                " this.observe=function(){(cb||function(){})({"
                "  getEntries:function(){return [];},"
                "  getEntriesByType:function(){return [];},"
                "  getEntriesByName:function(){return [];}});};"
                " this.disconnect=function(){};"
                " this.takeRecords=function(){return [];};}"
                "PerformanceObserver.supportedEntryTypes=[];"
                "globalThis.PerformanceObserver=PerformanceObserver;"
                "globalThis.IntersectionObserver=globalThis.IntersectionObserver||PerformanceObserver;"
                "globalThis.MutationObserver=globalThis.MutationObserver||PerformanceObserver;"
                "globalThis.ResizeObserver=globalThis.ResizeObserver||PerformanceObserver;"
                "globalThis.matchMedia=globalThis.matchMedia||function(q){"
                " return {matches:false, media:String(q||''), addListener:function(){},"
                "  removeListener:function(){}, addEventListener:function(){},"
                "  removeEventListener:function(){}, onchange:null, dispatchEvent:function(){return false;}};};"
                "globalThis.requestIdleCallback=globalThis.requestIdleCallback||function(f){"
                " return setTimeout(function(){f({didTimeout:false,timeRemaining:function(){return 0;}});},1);};"
                "globalThis.cancelIdleCallback=globalThis.cancelIdleCallback||clearTimeout;"
                "})()";
            JSValue po = JS_Eval(ctx, po_src, sizeof(po_src) - 1,
                                 "<web-stubs>", JS_EVAL_TYPE_GLOBAL);
            JS_FreeValue(ctx, po);
        }
        // S118 fetch law: WHATWG fetch subset over the S100 NET-001 HTTPS
        // client (mininet::http_get — OpenSSL TLS, redirects, chunked).
        // fetch() returns a Promise; the GET is performed synchronously and
        // the promise settles before return — the async/await continuation
        // is a QuickJS JOB, drained by the S118 job-pump law at every
        // engine quiescence point (run_scripts/tick). Response carries
        // status/ok/url + text()/json() over the fetched body.
        JSValue fetch_fn = JS_NewCFunction(ctx, [](JSContext* c, JSValueConst, int argc, JSValueConst* argv) -> JSValue {
            if (!impl_of(c)) return JS_EXCEPTION;
            std::string url;
            if (argc >= 1) {
                if (JS_IsString(argv[0])) {
                    const char* u = JS_ToCString(c, argv[0]);
                    if (u) { url = u; JS_FreeCString(c, u); }
                } else {
                    // Request-object form: read .url (feature-detected usage)
                    JSValue uv = JS_GetPropertyStr(c, argv[0], "url");
                    if (JS_IsString(uv)) {
                        const char* u = JS_ToCString(c, uv);
                        if (u) { url = u; JS_FreeCString(c, u); }
                    }
                    JS_FreeValue(c, uv);
                }
            }
            JSValue resolving[2];
            JSValue promise = JS_NewPromiseCapability(c, resolving);
            if (JS_IsException(promise)) return promise;
            if (url.empty()) {
                JSValue err = JS_ThrowTypeError(c, "fetch: url required");
                JSValue ignored = JS_Call(c, resolving[1], JS_UNDEFINED, 1, &err);
                JS_FreeValue(c, ignored);
                JS_FreeValue(c, err);
                JS_FreeValue(c, resolving[0]);
                JS_FreeValue(c, resolving[1]);
                return promise;
            }
            // S133 FETCH-URL law (WHATWG Fetch §"parse a URL"): the spec
            // string resolves against the DOCUMENT base when the caller is
            // a document/worker — fetch("/api/config") MUST hit the site's
            // origin, not throw "bad url". resolve_url merges relative,
            // root-relative and scheme-relative refs (absolute passes
            // through unchanged).
            auto* impl_fetch = impl_of(c);
            if (impl_fetch) url = impl_fetch->resolve_url(url);
            // S133 FETCH-INIT law (WHATWG Fetch §4.1): fetch(url, init) —
            // init.method selects the request method (GET supported; any
            // other method is an HONEST visible rejection, never a silent
            // GET), init.headers forwards request headers (Authorization
            // Bearer — measured need: chat.z.ai /api/models 403 without it,
            // 200 with it). Plain-object Headers form.
            std::map<std::string, std::string> req_headers;
            std::string method = "GET";
            if (argc >= 2 && JS_IsObject(argv[1])) {
                JSValue mv = JS_GetPropertyStr(c, argv[1], "method");
                if (JS_IsString(mv)) {
                    const char* m = JS_ToCString(c, mv);
                    if (m) {
                        method = m;
                        JS_FreeCString(c, m);
                    }
                    // WHATWG: normalize the method (case-insensitive)
                    for (auto& ch : method) ch = char(::toupper((unsigned char)ch));
                }
                JS_FreeValue(c, mv);
                JSValue hv = JS_GetPropertyStr(c, argv[1], "headers");
                if (JS_IsObject(hv)) {
                    JSPropertyEnum* props = nullptr;
                    uint32_t nprops = 0;
                    if (JS_GetOwnPropertyNames(c, &props, &nprops, hv,
                                               JS_GPN_STRING_MASK | JS_GPN_ENUM_ONLY) == 0) {
                        for (uint32_t i = 0; i < nprops; ++i) {
                            const char* k = JS_AtomToCString(c, props[i].atom);
                            JSValue val = JS_GetProperty(c, hv, props[i].atom);
                            const char* v = JS_IsString(val) ? JS_ToCString(c, val) : nullptr;
                            if (k && v) req_headers[k] = v;
                            if (k) JS_FreeCString(c, k);
                            if (v) JS_FreeCString(c, v);
                            JS_FreeValue(c, val);
                            JS_FreeAtom(c, props[i].atom);
                        }
                        js_free(c, props);
                    }
                }
                JS_FreeValue(c, hv);
            }
            if (method != "GET") {
                std::string msg = "fetch method " + method +
                                  " not supported by the runtime fetch substrate "
                                  "(GET only) — visible rejection, not a silent GET";
                std::cerr << "[WV-FETCH] REJECT " << method << " " << url << std::endl;
                JSValue err = JS_NewError(c);
                JS_SetPropertyStr(c, err, "message", JS_NewString(c, msg.c_str()));
                JS_SetPropertyStr(c, err, "name", JS_NewString(c, "TypeError"));
                JSValue ign = JS_Call(c, resolving[1], JS_UNDEFINED, 1, &err);
                JS_FreeValue(c, ign);
                JS_FreeValue(c, err);
                JS_FreeValue(c, resolving[0]);
                JS_FreeValue(c, resolving[1]);
                return promise;
            }
            std::string hdr_note;
            for (auto& [hk, hv2] : req_headers) hdr_note += " " + hk + "=" + hv2;
            std::cerr << "[WV-FETCH] GET " << url
                      << (hdr_note.empty() ? "" : (" headers:" + hdr_note))
                      << std::endl;
            // S133 FETCH-ASSET law: after base resolution a ref that is NOT
            // http(s) is a LOCAL document (AOSP WebView file:///android_asset
            // base → the APK asset tree serves fetch, matching Chromium's
            // file-protocol handling). Network refs go over mininet.
            if (url.rfind("http://", 0) != 0 && url.rfind("https://", 0) != 0) {
                auto* impl_f2 = impl_of(c);
                auto bytes = impl_f2 ? impl_f2->fetch_resource(url, "fetch")
                                     : std::vector<uint8_t>{};
                JSValue resp2 = JS_NewObject(c);
                JS_SetPropertyStr(c, resp2, "status",
                                  JS_NewInt32(c, bytes.empty() ? 404 : 200));
                JS_SetPropertyStr(c, resp2, "ok", JS_NewBool(c, !bytes.empty()));
                JS_SetPropertyStr(c, resp2, "url", JS_NewString(c, url.c_str()));
                JS_SetPropertyStr(c, resp2, "bodyUsed", JS_NewBool(c, false));
                JS_SetPropertyStr(c, resp2, "\x01body",
                                  JS_NewStringLen(c, (const char*)bytes.data(),
                                                  bytes.size()));
                JS_SetPropertyStr(c, resp2, "text", JS_NewCFunction(c,
                    [](JSContext* c2, JSValueConst this_v2, int, JSValueConst*) {
                        return JS_GetPropertyStr(c2, this_v2, "\x01body");
                    }, "text", 0));
                JS_SetPropertyStr(c, resp2, "json", JS_NewCFunction(c,
                    [](JSContext* c2, JSValueConst this_v2, int, JSValueConst*) {
                        JSValue b = JS_GetPropertyStr(c2, this_v2, "\x01body");
                        if (!JS_IsString(b)) return b;
                        size_t bl2 = 0;
                        const char* raw = JS_ToCStringLen(c2, &bl2, b);
                        if (!raw) { JS_FreeValue(c2, b); return JS_EXCEPTION; }
                        JSValue parsed = JS_ParseJSON(c2, raw, bl2, "<fetch-asset>");
                        JS_FreeCString(c2, raw);
                        JS_FreeValue(c2, b);
                        return parsed;   // non-JSON → honest SyntaxError
                    }, "json", 0));
                JSValue ign2 = JS_Call(c, resolving[0], JS_UNDEFINED, 1, &resp2);
                JS_FreeValue(c, ign2);
                JS_FreeValue(c, resp2);
                JS_FreeValue(c, resolving[0]);
                JS_FreeValue(c, resolving[1]);
                return promise;
            }
            mininet::HttpResponse hr = req_headers.empty()
                ? mininet::http_get(url, 5, 20000)
                : mininet::http_get_ex(url, req_headers, 5, 20000);
            if (!hr.ok()) {
                std::cerr << "[WV-FETCH] FAILED status=" << hr.status
                          << " err=" << hr.error << std::endl;
                std::string msg = hr.error.empty()
                    ? ("http status " + std::to_string(hr.status)) : hr.error;
                JSValue err = JS_NewError(c);
                JS_SetPropertyStr(c, err, "message", JS_NewString(c, msg.c_str()));
                JS_SetPropertyStr(c, err, "name", JS_NewString(c, "TypeError"));
                JS_SetPropertyStr(c, err, "status", JS_NewInt32(c, hr.status));
                JSValue ignored = JS_Call(c, resolving[1], JS_UNDEFINED, 1, &err);
                JS_FreeValue(c, ignored);
                JS_FreeValue(c, err);
                JS_FreeValue(c, resolving[0]);
                JS_FreeValue(c, resolving[1]);
                return promise;
            }
            std::cerr << "[WV-FETCH] ok status=" << hr.status
                      << " bytes=" << hr.body.size() << std::endl;
            JSValue resp = JS_NewObject(c);
            JS_SetPropertyStr(c, resp, "status", JS_NewInt32(c, hr.status));
            JS_SetPropertyStr(c, resp, "ok", JS_NewBool(c, hr.status >= 200 && hr.status < 300));
            JS_SetPropertyStr(c, resp, "url", JS_NewString(c, hr.final_url.c_str()));
            JS_SetPropertyStr(c, resp, "bodyUsed", JS_NewBool(c, false));
            // hidden body slot (read by text()/json())
            JS_SetPropertyStr(c, resp, "\x01body", JS_NewStringLen(c, hr.body.data(), hr.body.size()));
            JS_SetPropertyStr(c, resp, "text", JS_NewCFunction(c,
                [](JSContext* c2, JSValueConst this_v2, int, JSValueConst*) {
                    JSValue b = JS_GetPropertyStr(c2, this_v2, "\x01body");
                    return b;   // move: string out
                }, "text", 0));
            JS_SetPropertyStr(c, resp, "json", JS_NewCFunction(c,
                [](JSContext* c2, JSValueConst this_v2, int, JSValueConst*) {
                    JSValue b = JS_GetPropertyStr(c2, this_v2, "\x01body");
                    if (!JS_IsString(b)) return b;
                    size_t bl2 = 0;
                    const char* raw = JS_ToCStringLen(c2, &bl2, b);
                    if (!raw) { JS_FreeValue(c2, b); return JS_EXCEPTION; }
                    JSValue parsed = JS_ParseJSON(c2, raw, bl2, "<response>");
                    JS_FreeCString(c2, raw);
                    JS_FreeValue(c2, b);
                    if (JS_IsException(parsed)) {
                        // HTML/error pages are not JSON — throw the honest
                        // SyntaxError the spec prescribes
                        return parsed;
                    }
                    return parsed;
                }, "json", 0));
            JSValue ignored = JS_Call(c, resolving[0], JS_UNDEFINED, 1, &resp);
            JS_FreeValue(c, ignored);
            JS_FreeValue(c, resp);
            JS_FreeValue(c, resolving[0]);
            JS_FreeValue(c, resolving[1]);
            return promise;
        }, "fetch", 1);
        JS_SetPropertyStr(ctx, global, "fetch", fetch_fn);
        // Blob / URL.createObjectURL / FileReader / AudioContext / Worker:
        // feature-detected by the corpus bundles; safe minimal semantics.
        JS_SetPropertyStr(ctx, global, "Blob",
            make_ctor(ctx, [](JSContext* c, JSValueConst, int, JSValueConst*) {
                return JS_NewObject(c);  // empty blob object
            }, "Blob", 0));
        // URL: constructor (WHATWG URL law, file-scope subset) + statics
        JSValue url_ctor = make_ctor(ctx, [](JSContext* c, JSValueConst this_v, int argc, JSValueConst* argv) {
            JSValue o = JS_NewObject(c);
            std::string href = argc >= 1 ? "" : "";
            if (argc >= 1) {
                const char* h = JS_ToCString(c, argv[0]);
                if (h) { href = h; JS_FreeCString(c, h); }
            }
            std::string hash_v, search_v;
            size_t hq = href.find('#');
            if (hq != std::string::npos) { hash_v = href.substr(hq); href = href.substr(0, hq); }
            size_t q = href.find('?');
            if (q != std::string::npos) { search_v = href.substr(q); href = href.substr(0, q); }
            JS_SetPropertyStr(c, o, "href", JS_NewString(c, href.c_str()));
            JS_SetPropertyStr(c, o, "hash", JS_NewString(c, hash_v.c_str()));
            JS_SetPropertyStr(c, o, "search", JS_NewString(c, search_v.c_str()));
            JS_SetPropertyStr(c, o, "pathname", JS_NewString(c, href.c_str()));
            JS_SetPropertyStr(c, o, "origin", JS_NewString(c, "null"));
            JS_SetPropertyStr(c, o, "protocol", JS_NewString(c, "file:"));
            return o;
        }, "URL", 1);
        JS_SetPropertyStr(ctx, url_ctor, "createObjectURL",
            JS_NewCFunction(ctx, [](JSContext* c, JSValueConst, int, JSValueConst*) {
                return JS_NewString(c, "blob:miniandroid/unsupported");
            }, "createObjectURL", 1));
        JS_SetPropertyStr(ctx, url_ctor, "revokeObjectURL",
            JS_NewCFunction(ctx, [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "revokeObjectURL", 1));
        JS_SetPropertyStr(ctx, global, "URL", url_ctor);
        // ── S133 URLSearchParams law (WHATWG URL §urlencoded) ───────────
        // Measured need: 30+ call sites in the z.ai bundle (query building
        // for every API fetch). Implemented as a JS polyfill (same pattern
        // as the TextEncoder law): parse from string (leading '?' stripped,
        // '+' = space, percent-decode) | pair-array | record; append/set/
        // get/has/delete/toString/forEach + entries/keys/values iterators.
        {
            static const char usp_src[] =
                "(function(){"
                "function USP(init){"
                " this._p=[];"
                " if(init==null) return;"
                " if(typeof init==='string'){"
                "  if(init.charAt(0)==='?') init=init.slice(1);"
                "  var ps=init.split('&');"
                "  for(var i=0;i<ps.length;i++){"
                "   if(ps[i]==='') continue;"
                "   var eq=ps[i].indexOf('='),k,v;"
                "   if(eq<0){k=ps[i];v='';}else{k=ps[i].slice(0,eq);v=ps[i].slice(eq+1);}"
                "   k=k.replace(/\\+/g,' ').replace(/%([^0-9A-Fa-f]{2}|$)/g,function(m,g){return g?'%25'+g:'%25';});"
                "   v=v.replace(/\\+/g,' ');"
                "   try{k=decodeURIComponent(k);}catch(e){}"
                "   try{v=decodeURIComponent(v);}catch(e){}"
                "   this._p.push([k,v]);"
                "  }"
                " } else if(Array.isArray(init)){"
                "  for(var i=0;i<init.length;i++) this._p.push([String(init[i][0]),String(init[i][1])]);"
                " } else {"
                "  for(var k in init) if(Object.prototype.hasOwnProperty.call(init,k)) this._p.push([String(k),String(init[k])]);"
                " }"
                "}"
                "USP.prototype.append=function(k,v){this._p.push([String(k),String(v)]);};"
                "USP.prototype.set=function(k,v){k=String(k);v=String(v);var f=false,out=[];"
                " for(var i=0;i<this._p.length;i++){if(this._p[i][0]===k){if(!f){out.push([k,v]);f=true;}}else out.push(this._p[i]);}"
                " if(!f)out.push([k,v]); this._p=out;};"
                "USP.prototype.get=function(k){k=String(k);for(var i=0;i<this._p.length;i++)if(this._p[i][0]===k)return this._p[i][1];return null;};"
                "USP.prototype.has=function(k){k=String(k);for(var i=0;i<this._p.length;i++)if(this._p[i][0]===k)return true;return false;};"
                "USP.prototype.delete=function(k){k=String(k);var out=[];for(var i=0;i<this._p.length;i++)if(this._p[i][0]!==k)out.push(this._p[i]);this._p=out;};"
                "USP.prototype.toString=function(){var out=[];"
                " var e=function(x){return encodeURIComponent(x).replace(/%20/g,'+');};"
                " for(var i=0;i<this._p.length;i++)out.push(e(this._p[i][0])+'='+e(this._p[i][1]));"
                " return out.join('&');};"
                "USP.prototype.forEach=function(cb,ta){for(var i=0;i<this._p.length;i++)cb.call(ta,this._p[i][1],this._p[i][0],this);};"
                "USP.prototype.entries=function*(){for(var i=0;i<this._p.length;i++)yield [this._p[i][0],this._p[i][1]];"
                " if(typeof Symbol==='function'&&Symbol.iterator&&USP.prototype.entries&&!USP.prototype.entries.__tagged){Object.defineProperty(USP.prototype.entries,'__tagged',{value:1});}"
                " };"
                "USP.prototype.keys=function*(){for(var i=0;i<this._p.length;i++)yield this._p[i][0];};"
                "USP.prototype.values=function*(){for(var i=0;i<this._p.length;i++)yield this._p[i][1];};"
                "if(typeof Symbol==='function'&&Symbol.iterator) USP.prototype[Symbol.iterator]=USP.prototype.entries;"
                "globalThis.URLSearchParams=USP;"
                "})()";
            JSValue usp = JS_Eval(ctx, usp_src, sizeof(usp_src) - 1,
                                  "<urlsearch-params>", JS_EVAL_TYPE_GLOBAL);
            JS_FreeValue(ctx, usp);
        }
        JS_SetPropertyStr(ctx, global, "FileReader",
            make_ctor(ctx, [](JSContext* c, JSValueConst, int, JSValueConst*) {
                JSValue o = JS_NewObject(c);
                JS_SetPropertyStr(c, o, "readAsDataURL", JS_NewCFunction(c,
                    [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "readAsDataURL", 1));
                return o;
            }, "FileReader", 0));
        JS_SetPropertyStr(ctx, global, "Worker",
            make_ctor(ctx, [](JSContext* c, JSValueConst, int, JSValueConst*) {
                // Web Workers require a concurrent script host — honest
                // construction failure the bundle feature-detects.
                return JS_ThrowTypeError(c, "Workers unsupported in this WebView build");
            }, "Worker", 1));
        // Intl (QuickJS 2024 lacks it; the corpus formats scores/numbers
        // through Intl.NumberFormat — provide the honest minimal semantics:
        // grouping separators + digit options).
        JSValue intl = JS_NewObject(ctx);
        JS_SetPropertyStr(ctx, intl, "NumberFormat",
            make_ctor(ctx, [](JSContext* c, JSValueConst, int argc, JSValueConst* argv) {
                JSValue o = JS_NewObject(c);
                JSValue ctor = JS_GetPropertyStr(c, o, "constructor");
                (void)ctor;
                // format(n): group thousands, honor {maximumFractionDigits}
                JS_SetPropertyStr(c, o, "format", JS_NewCFunction(c,
                    [](JSContext* c2, JSValueConst this_v, int argc2, JSValueConst* argv2) {
                        double x = argc2 >= 1 ? 0 : 0;
                        if (argc2 >= 1) JS_ToFloat64(c2, &x, argv2[0]);
                        char buf[64];
                        snprintf(buf, sizeof(buf), "%.0f", x);
                        std::string s = buf;
                        // group by 3 from the left
                        int insert = int(s.size()) - 3;
                        while (insert > 0) { s.insert(size_t(insert), ","); insert -= 3; }
                        return JS_NewString(c2, s.c_str());
                    }, "format", 1));
                JSValue resolved = JS_NewObject(c);
                JS_SetPropertyStr(c, resolved, "locale", JS_NewString(c, "en-US"));
                JS_SetPropertyStr(c, o, "resolvedOptions", JS_NewCFunction(c,
                    [](JSContext* c2, JSValueConst this_v, int, JSValueConst*) {
                        JSValue ro = JS_NewObject(c2);
                        JS_SetPropertyStr(c2, ro, "locale", JS_NewString(c2, "en-US"));
                        return ro;
                    }, "resolvedOptions", 0));
                return o;
            }, "NumberFormat", 0));
        JS_SetPropertyStr(ctx, intl, "DateTimeFormat",
            make_ctor(ctx, [](JSContext* c, JSValueConst, int, JSValueConst*) {
                JSValue o = JS_NewObject(c);
                JS_SetPropertyStr(c, o, "format", JS_NewCFunction(c,
                    [](JSContext* c2, JSValueConst, int, JSValueConst*) {
                        return JS_NewString(c2, "");
                    }, "format", 1));
                return o;
            }, "DateTimeFormat", 0));
        JS_SetPropertyStr(ctx, intl, "Collator",
            make_ctor(ctx, [](JSContext* c, JSValueConst, int, JSValueConst*) {
                JSValue o = JS_NewObject(c);
                JS_SetPropertyStr(c, o, "compare", JS_NewCFunction(c,
                    [](JSContext* c2, JSValueConst, int argc2, JSValueConst* argv2) {
                        if (argc2 < 2) return JS_NewInt32(c2, 0);
                        const char* a = JS_ToCString(c2, argv2[0]);
                        const char* b = JS_ToCString(c2, argv2[1]);
                        int r = a && b ? strcmp(a, b) : 0;
                        if (a) JS_FreeCString(c2, a);
                        if (b) JS_FreeCString(c2, b);
                        return JS_NewInt32(c2, r < 0 ? -1 : (r > 0 ? 1 : 0));
                    }, "compare", 2));
                return o;
            }, "Collator", 0));
        JS_SetPropertyStr(ctx, global, "Intl", intl);
        // WebAudio: the corpus sound engine does new (AudioContext||webkitAudioContext)
        // unconditionally at sound init. Honest approximation: the surface
        // exists, nodes are inert (audio output is not wired in this build;
        // documented deviation — the game runs silent).
        JSValue audio_ctor = make_ctor(ctx, [](JSContext* c, JSValueConst, int, JSValueConst*) {
            std::cerr << "[WV-AUDIO] AudioContext ctor entered" << std::endl;
            JSValue ac = JS_NewObject(c);
            JS_SetPropertyStr(c, ac, "state", JS_NewString(c, "suspended"));
            JS_SetPropertyStr(c, ac, "currentTime", JS_NewFloat64(c, 0.0));
            JS_SetPropertyStr(c, ac, "sampleRate", JS_NewInt32(c, 44100));
            JS_SetPropertyStr(c, ac, "destination", JS_NewObject(c));
            auto node_fn = JS_NewCFunction(c, [](JSContext* c2, JSValueConst, int, JSValueConst*) {
                JSValue n = JS_NewObject(c2);
                JS_SetPropertyStr(c2, n, "connect", JS_NewCFunction(c2,
                    [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "connect", 1));
                JS_SetPropertyStr(c2, n, "start", JS_NewCFunction(c2,
                    [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "start", 0));
                JS_SetPropertyStr(c2, n, "stop", JS_NewCFunction(c2,
                    [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "stop", 0));
                JS_SetPropertyStr(c2, n, "gain", JS_NewObject(c2));
                JS_SetPropertyStr(c2, n, "frequency", JS_NewObject(c2));
                JS_SetPropertyStr(c2, n, "type", JS_UNDEFINED);
                JS_SetPropertyStr(c2, n, "buffer", JS_UNDEFINED);
                JS_SetPropertyStr(c2, n, "onended", JS_UNDEFINED);
                return n;
            }, "node", 0);
            for (const char* m : {"createMediaStreamDestination", "createOscillator",
                                  "createGain", "createBufferSource", "createBiquadFilter",
                                  "createAnalyser", "createScriptProcessor", "createDynamicsCompressor"}) {
                JS_SetPropertyStr(c, ac, m, JS_DupValue(c, node_fn));
            }
            JS_SetPropertyStr(c, ac, "resume", JS_NewCFunction(c,
                [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "resume", 0));
            JS_SetPropertyStr(c, ac, "suspend", JS_NewCFunction(c,
                [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "suspend", 0));
            JS_SetPropertyStr(c, ac, "close", JS_NewCFunction(c,
                [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "close", 0));
            return ac;
        }, "AudioContext", 0);
        JS_SetPropertyStr(ctx, global, "AudioContext", JS_DupValue(ctx, audio_ctor));
        JS_SetPropertyStr(ctx, global, "webkitAudioContext", audio_ctor);
        // screen.orientation / navigator.vibrate / navigator.wakeLock:
        // guarded feature-detects in the corpus; honest inert semantics.
        JSValue scr2 = JS_GetPropertyStr(ctx, global, "screen");
        JSValue orient = JS_NewObject(ctx);
        JS_SetPropertyStr(ctx, orient, "lock", JS_NewCFunction(ctx,
            [](JSContext* c, JSValueConst, int, JSValueConst*) {
                // return a resolved-promise-like thenable
                JSValue p = JS_NewObject(c);
                JS_SetPropertyStr(c, p, "then", JS_NewCFunction(c,
                    [](JSContext* c2, JSValueConst this_v, int argc2, JSValueConst* argv2) {
                        if (argc2 >= 1 && JS_IsFunction(c2, argv2[0])) {
                            JSValue r = JS_Call(c2, argv2[0], JS_UNDEFINED, 0, nullptr);
                            JS_FreeValue(c2, r);
                        }
                        return JS_UNDEFINED;
                    }, "then", 1));
                return p;
            }, "lock", 1));
        JS_SetPropertyStr(ctx, orient, "unlock", JS_NewCFunction(ctx,
            [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "unlock", 0));
        JS_SetPropertyStr(ctx, scr2, "orientation", orient);
        JSValue nav2 = JS_GetPropertyStr(ctx, global, "navigator");
        JS_SetPropertyStr(ctx, nav2, "vibrate", JS_NewCFunction(ctx,
            [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_TRUE; }, "vibrate", 1));
        JSValue wl = JS_NewObject(ctx);
        JS_SetPropertyStr(ctx, wl, "request", JS_NewCFunction(ctx,
            [](JSContext* c, JSValueConst, int, JSValueConst*) {
                return JS_ThrowTypeError(c, "wakeLock unsupported");
            }, "request", 1));
        JS_SetPropertyStr(ctx, nav2, "wakeLock", wl);
        // canvas.captureStream (frame-capture API used by the game loop)
        JSValue cap = JS_NewCFunction(ctx, [](JSContext* c, JSValueConst this_v, int, JSValueConst*) {
            JSValue stream = JS_NewObject(c);
            JSValue tracks = JS_NewArray(c);
            JSValue track = JS_NewObject(c);
            JS_SetPropertyStr(c, track, "requestFrame", JS_NewCFunction(c,
                [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "requestFrame", 0));
            JS_SetPropertyUint32(c, tracks, 0, track);
            JS_SetPropertyStr(c, stream, "getVideoTracks", JS_NewCFunction(c,
                [](JSContext* c2, JSValueConst, int, JSValueConst*) {
                    return JS_UNDEFINED;  // replaced below via closure-free stub
                }, "getVideoTracks", 0));
            JS_SetPropertyStr(c, stream, "getTracks", JS_NewCFunction(c,
                [](JSContext* c2, JSValueConst, int, JSValueConst*) {
                    return JS_UNDEFINED;
                }, "getTracks", 0));
            (void)tracks;
            return stream;
        }, "captureStream", 0);
        // history
        JSValue hist = JS_NewObject(ctx);
        JS_SetPropertyStr(ctx, hist, "pushState", JS_NewCFunction(ctx, [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "pushState", 3));
        JS_SetPropertyStr(ctx, hist, "replaceState", JS_NewCFunction(ctx, [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "replaceState", 3));
        JS_SetPropertyStr(ctx, hist, "back", JS_NewCFunction(ctx, [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "back", 0));
        JS_SetPropertyStr(ctx, global, "history", hist);
        // alert/confirm
        JS_SetPropertyStr(ctx, global, "alert",
                          JS_NewCFunction(ctx, [](JSContext* c, JSValueConst, int argc, JSValueConst* argv) {
                              if (argc >= 1) {
                                  const char* m = JS_ToCString(c, argv[0]);
                                  std::cerr << "[WV-ALERT] " << (m ? m : "") << std::endl;
                                  if (m) JS_FreeCString(c, m);
                              }
                              return JS_UNDEFINED;
                          }, "alert", 1));
        JS_SetPropertyStr(ctx, global, "confirm", JS_NewCFunction(ctx, [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_FALSE; }, "confirm", 1));
        // AOSP WebView law: `window` exposes the same globals. Mirror the
        // property set onto the window object (document.location.* etc. are
        // read through `window.` by bundlers).
        for (const char* name : {"console", "navigator", "location", "localStorage",
                                 "performance", "screen", "history", "document",
                                 "alert", "confirm", "matchMedia", "getComputedStyle",
                                 "open", "close", "scrollTo", "Image", "AudioContext",
                                 "webkitAudioContext", "Blob", "URL", "FileReader",
                                 "Worker", "Intl", "btoa", "atob", "crypto"}) {
            JSValue v = JS_GetPropertyStr(ctx, global, name);
            if (!JS_IsUndefined(v)) JS_SetPropertyStr(ctx, window_obj, name, v);
            else JS_FreeValue(ctx, v);
        }
    }
    JS_FreeValue(ctx, global);
    load_persisted_kv();

    // ── bindings smoke test (engine-parity proof; logs the first failure) ──
    const char* smoke =
        "(function(){"
        "var steps=[];"
        "function t(n,f){try{var r=f();console.warn('[SMOKE] '+n+' ok');return r;}catch(e){console.warn('[SMOKE] '+n+' FAIL '+(e&&e.message||e));throw new Error('SMOKE-STOP '+(e&&e.message||e));}}"
        "t('canvas',function(){return document.createElement('canvas');});"
        "t('ctx',function(){return document.createElement('canvas').getContext('2d');});"
        "t('grad',function(){return document.createElement('canvas').getContext('2d').createLinearGradient(0,0,1,1);});"
        "t('addColorStop',function(){var g=document.createElement('canvas').getContext('2d').createLinearGradient(0,0,1,1);g.addColorStop(0,'#fff');return g;});"
        "t('fillStyle',function(){var x=document.createElement('canvas').getContext('2d');x.fillStyle='#fff';x.fillStyle=x.createLinearGradient(0,0,1,1);return 1;});"
        "t('classList',function(){var d=document.createElement('div');d.classList.add('a');return d.classList.contains('a');});"
        "t('style',function(){document.createElement('div').style.display='none';return 1;});"
        "t('setTimeout',function(){return setTimeout(function(){},1);});"
        "t('rAF',function(){return requestAnimationFrame(function(){});});"
        "t('raf-typeof',function(){return typeof requestAnimationFrame;});"
        "t('raf-window-typeof',function(){return typeof window.requestAnimationFrame;});"
        "t('raf-direct',function(){window.requestAnimationFrame(function(){});return 1;});"
        "t('localStorage',function(){localStorage.setItem('s','1');return localStorage.getItem('s');});"
        "t('getElementById',function(){return document.getElementById('game');});"
        "t('body',function(){return document.body;});"
        "t('AudioContext',function(){return new (window.AudioContext||window.webkitAudioContext)();});"
        "t('Intl',function(){return new Intl.NumberFormat().format(1234);});"
        "t('URL',function(){return new URL('file:///x');});"
        "t('btoa',function(){return btoa('abc');});"
        "console.warn('[WV-SMOKE] all ok');"
        "})()";
    JSValue sr = JS_Eval(ctx, smoke, strlen(smoke), "<smoke>", JS_EVAL_TYPE_GLOBAL);
    if (JS_IsException(sr)) {
        report_exception("SMOKE");
    }
    JS_FreeValue(ctx, sr);
}

// ── script pipeline ─────────────────────────────────────────────────────
void WebViewEngine::Impl::run_scripts() {
    // external <script src> fetch (document order, inline scripts interleaved
    // by position — approximated: inline run first in document order, then
    // externals; documented deviation, corpus entry scripts are terminal).
    // S133: inline module scripts carry a synthetic module name anchored at
    // the document base so their relative imports resolve.
    int inline_module_n = 0;
    for (auto& [code, is_mod] : doc.inline_scripts) {
        if (is_mod) {
            std::string base = self->document_url();
            if (base.empty()) base = "module";
            exec_script(code, base + "#inline-" + std::to_string(++inline_module_n),
                        true);
        } else {
            // S133: per-script eval filename — minified stacks like
            // "inline:5" are unattributable when every inline script shares
            // one name; inline-<n>:<line> maps a failure to its script.
            exec_script(code, "inline-" + std::to_string(++inline_module_n));
        }
    }
    for (auto& [src, stype] : doc.external_scripts) {
        bool is_mod = stype == "module";
        auto bytes = fetch_resource(src, "script-exec");
        if (bytes.empty()) {
            std::cerr << "[WV-SCRIPT] external script missing: " << src
                      << " (resolved " << resolve_url(src) << ")" << std::endl;
            continue;
        }
        std::string code(bytes.begin(), bytes.end());
        // module name = RESOLVED absolute ref (the loader's base for its own
        // imports); classic scripts keep the raw src as the eval filename
        std::string name = is_mod ? resolve_url(src) : src;
        if (is_mod) {
            size_t q = name.find_first_of("?#");
            if (q != std::string::npos) name.erase(q);
        }
        exec_script(code, name, is_mod);
    }
    // S118 JOB-PUMP law: every script start (async fn kick-off, promise
    // chains, await continuations) lands on the QuickJS job queue — without
    // an explicit drain those continuations NEVER run (the embedder owns
    // the job loop; there is no implicit pump). Bounded for determinism.
    drain_pending_jobs(4096);
    // count DOM nodes for provenance
    std::function<void(DomNode*)> count = [&](DomNode* n) {
        stats.dom_nodes++;
        for (auto& c : n->children) count(c.get());
    };
    count(doc.root.get());
    // S114 DOMContentLoaded law (HTML §13.2.7): after the parser finishes
    // (all inline + external scripts executed) the event fires on the
    // document. Real games build their entire view layer in this callback
    // (Block'Buster's FieldView + window.view wiring).
    {
        JSValue ev = JS_NewObject(ctx);
        JS_SetPropertyStr(ctx, ev, "type", JS_NewString(ctx, "DOMContentLoaded"));
        dispatch(doc.root.get(), "DOMContentLoaded", ev);
        // the load event on the window follows (ordering law: DCL → load)
        JSValue lev = JS_NewObject(ctx);
        JS_SetPropertyStr(ctx, lev, "type", JS_NewString(ctx, "load"));
        dispatch(nullptr, "load", lev);
        // S118 job pump: DCL/load listeners kick off async init chains
        // (weather's ForecastView -> fetch -> await) — resume them here
        drain_pending_jobs(4096);
    }
}

// ── layout + compose ────────────────────────────────────────────────────
static std::string trim2(const std::string& s);

// ROOT-050 law (S111) + S114 GENERIC EVALUATOR: CSS <length> resolution
// must handle calc() (+ - * / with precedence and nesting), var() fallbacks,
// and the full unit family — px, vw, vh, vmin/vmax, % (axis-aware), em/rem,
// pt. Breakout 71 sizes its canvas with `height:calc(var(--vh,1vh)*100)`;
// Block'Buster drives EVERY size through var()+calc()+vw
// (`h1{font-size:calc(var(--size_4)*2 + var(--size_2))}`).
struct CssCtx {
    float vw = 0, vh = 0;        // viewport w/h (px)
    float pctw = 0, pcth = 0;    // containing-block w/h for % resolution
    float em = 0;                // element font-size for em/rem
};

static float css_eval(const std::string& v, const CssCtx& cx, float dflt, int pct_axis);

namespace css_eval_detail {
struct Term {
    float px = 0;
    bool is_len = false;   // false → unitless scalar (valid only in * and /)
};

// Recursive-descent calc grammar (CSS Values §8): expr = term (('+'|'-') term)*
// term = factor (('*'|'/') factor)*, factor = <length> | <number> | '(' expr ')'
struct Parser {
    const std::string& s;
    const CssCtx& cx;
    int pct_axis;            // 0 → % of pctw, 1 → % of pcth
    size_t i = 0;
    bool ok = true;

    Parser(const std::string& body, const CssCtx& c, int axis)
        : s(body), cx(c), pct_axis(axis) {}

    static bool dig(char ch) { return ch >= '0' && ch <= '9'; }
    void skip_ws() { while (i < s.size() && (s[i] == ' ' || s[i] == '\t' || s[i] == '\r' || s[i] == '\n')) ++i; }

    float resolve_unit(float num, const std::string& u) {
        if (u.empty() || u == "px") return num;
        if (u == "vw") return num * cx.vw / 100.f;
        if (u == "vh") return num * cx.vh / 100.f;
        if (u == "vmin") return num * std::min(cx.vw, cx.vh) / 100.f;
        if (u == "vmax") return num * std::max(cx.vw, cx.vh) / 100.f;
        if (u == "%") return num * (pct_axis == 1 ? cx.pcth : cx.pctw) / 100.f;
        if (u == "em" || u == "rem") return num * cx.em;
        if (u == "pt") return num * 96.f / 72.f;
        return num;   // unknown/unitless → px-lenient
    }

    Term parse_expr() {
        Term l = parse_term();
        for (;;) {
            skip_ws();
            if (i < s.size() && (s[i] == '+' || s[i] == '-')) {
                char op = s[i++];
                Term r = parse_term();
                if (r.is_len) l.is_len = true;
                l.px += (op == '+' ? 1.f : -1.f) * r.px;
            } else break;
        }
        return l;
    }
    Term parse_term() {
        Term l = parse_factor();
        for (;;) {
            skip_ws();
            if (i < s.size() && (s[i] == '*' || s[i] == '/')) {
                char op = s[i++];
                Term r = parse_factor();
                if (op == '*') {
                    if (l.is_len && r.is_len) { ok = false; return {0, false}; }  // length×length invalid
                    if (r.is_len && !l.is_len) l = r;   // scalar × length
                    else l.px *= r.px;
                } else {
                    if (r.is_len || r.px == 0.f) { ok = false; return {0, false}; }  // ÷ by length/zero invalid
                    l.px /= r.px;
                }
            } else break;
        }
        return l;
    }
    Term parse_factor() {
        skip_ws();
        if (i < s.size() && s[i] == '(') {
            ++i;
            Term t = parse_expr();
            skip_ws();
            if (i < s.size() && s[i] == ')') ++i; else ok = false;
            return t;
        }
        // S117 math-function nesting law: min()/max()/clamp() are legal
        // calc() FACTORS (CSS Values §8.2). Weather chains
        // --size4:max(0.6vw,0.6vh) into every size via
        // calc(var(--size4)*6) — the number scanner hit 'm' and the whole
        // calc() failed, collapsing every var-chained width/height to the
        // block-fill fallback (icons 1080px, pages unrenderable).
        if (s.compare(i, 4, "min(") == 0 || s.compare(i, 4, "max(") == 0 ||
            s.compare(i, 6, "clamp(") == 0) {
            size_t f0 = i;
            size_t j = s.find('(', i);
            if (j == std::string::npos) { ok = false; return {0, false}; }
            int depth = 0;
            for (; j < s.size(); ++j) {
                depth += s[j] == '(' ? 1 : 0;
                depth -= s[j] == ')' ? 1 : 0;
                if (depth == 0) break;
            }
            if (depth != 0) { ok = false; return {0, false}; }
            float r = css_eval(s.substr(f0, j - f0 + 1), cx, 0.f, pct_axis);
            i = j + 1;
            return {r, true};                  // a math function yields a length
        }
        size_t st = i;
        while (i < s.size() && (dig(s[i]) || s[i] == '.' || s[i] == '-' || s[i] == '+')) ++i;
        if (st == i) { ok = false; return {0, false}; }
        float num = ::strtof(s.c_str() + st, nullptr);
        size_t u0 = i;
        while (i < s.size() && ((s[i] >= 'a' && s[i] <= 'z') || s[i] == '%')) ++i;
        std::string unit = s.substr(u0, i - u0);
        // bare number → SCALAR (is_len=false): `4vw*2` is len×scalar, legal;
        // treating the scalar as a length made every such product "invalid".
        // px/vw/%/em… are lengths by definition.
        return {resolve_unit(num, unit), !unit.empty()};
    }
};
}  // namespace css_eval_detail

static float css_eval(const std::string& v, const CssCtx& cx, float dflt, int pct_axis) {
    if (v.empty()) return dflt;
    std::string s = trim2(v);
    // var(--x[, fallback]) substitution (custom props are var-resolved
    // upstream when defined; this catches JS-set inline styles + calc args)
    size_t vp;
    int guard = 0;
    while ((vp = s.find("var(")) != std::string::npos && guard++ < 8) {
        size_t open = vp + 4, depth = 1, i = open;
        while (i < s.size() && depth) {
            depth += s[i] == '(' ? 1 : 0;
            depth -= s[i] == ')' ? 1 : 0;
            ++i;
        }
        if (depth) return dflt;
        std::string inner = s.substr(open, i - open - 1);
        std::string repl;
        size_t comma = inner.find(',');
        if (comma != std::string::npos) repl = trim2(inner.substr(comma + 1));
        s = s.substr(0, vp) + repl + s.substr(i);
    }
    if (s.empty()) return dflt;
    // S114 CSS Values §3 math functions: min()/max()/clamp() — the same
    // family as calc(). accelerace sizes EVERYTHING through
    // `--height_car: max(15vw, 15vh)`; unhandled, the value fell through
    // to 0/negative and FT_Set_Pixel_Sizes(0) crashed hb_shape.
    if ((s.rfind("min(", 0) == 0 || s.rfind("max(", 0) == 0 ||
         s.rfind("clamp(", 0) == 0) && s.back() == ')') {
        bool is_min = s.rfind("min(", 0) == 0;
        bool is_clamp = s.rfind("clamp(", 0) == 0;
        size_t g0 = s.find('(') + 1, g1 = s.size() - 1;
        std::vector<std::string> args;
        int depth2 = 0; std::string cur2;
        for (size_t i = g0; i < g1; ++i) {
            char ch = s[i];
            if (ch == '(') ++depth2;
            if (ch == ')') --depth2;
            if (ch == ',' && depth2 == 0) { args.push_back(trim2(cur2)); cur2.clear(); }
            else cur2 += ch;
        }
        args.push_back(trim2(cur2));
        if (is_clamp) {
            if (args.size() != 3) return dflt;
            float mn = css_eval(args[0], cx, dflt, pct_axis);
            float val = css_eval(args[1], cx, dflt, pct_axis);
            float mx = css_eval(args[2], cx, dflt, pct_axis);
            return std::max(mn, std::min(val, mx));
        }
        if (args.empty()) return dflt;
        bool have = false; float best = 0;
        for (auto& a : args) {
            float r = css_eval(a, cx, dflt, pct_axis);
            if (!have) { best = r; have = true; }
            else best = is_min ? std::min(best, r) : std::max(best, r);
        }
        return have ? best : dflt;
    }
    if (s.rfind("calc(", 0) == 0 && s.back() == ')') {
        std::string body = s.substr(5, s.size() - 6);   // NAMED local — a temporary
        // here would dangle (Parser holds const std::string&)
        css_eval_detail::Parser ps(body, cx, pct_axis);
        css_eval_detail::Term t = ps.parse_expr();
        ps.skip_ws();
        if (wv_trace())
            std::cerr << "[WV-CALC] in='" << s << "' px=" << t.px
                      << " ok=" << ps.ok << " i=" << ps.i
                      << " want=" << body.size() << std::endl;
        if (!ps.ok || ps.i != body.size()) return dflt;   // full-consumption law
        return t.px;
    }
    css_eval_detail::Parser ps(s, cx, pct_axis);
    css_eval_detail::Term t = ps.parse_factor();
    if (!ps.ok) return dflt;
    return t.px;
}

// legacy 3-arg form — % and vw/vh all resolve against `viewport` (the
// pre-S114 behavior; kept for call sites without a containing block)
static float css_len_px(const std::string& v, float viewport, float dflt) {
    CssCtx cx;
    cx.vw = cx.vh = cx.pctw = cx.pcth = viewport;
    return css_eval(v, cx, dflt, 0);
}

void WebViewEngine::Impl::compute_layout() {
    // (layout happens inside render; kept as a seam for future passes)
}

static std::string trim2(const std::string& s) {
    size_t a = s.find_first_not_of(" \t\r\n");
    if (a == std::string::npos) return "";
    size_t b = s.find_last_not_of(" \t\r\n");
    return s.substr(a, b - a + 1);
}

static void style_element(DomNode* n, double vw, double vh,
                          const std::map<std::string, int>& font_map) {
    auto get = [&](const char* k) {
        auto it = n->style.find(k);
        return it != n->style.end() ? it->second : std::string();
    };
    n->display_none = get("display") == "none";
    // S114: visibility:hidden ≠ display:none — a hidden element keeps its
    // layout slot (CSS 2.1 §11.1.2); paint/text-gather consult the eff chain.
    n->vis_hidden_own = get("visibility") == "hidden";
    n->visible = !n->display_none;
    // S114 positional model: static / relative / absolute / fixed (CSS2.1 §9.3)
    std::string pos = get("position");
    n->pos_mode = pos == "fixed" ? 3 : pos == "absolute" ? 2 : pos == "relative" ? 1 : 0;
    n->positioned = (n->pos_mode == 2 || n->pos_mode == 3);
    // S114: the offset ladder treats `auto` as UNSPECIFIED (CSS 2.1 §9.3.2 —
    // `left:auto` falls back to the static position, it is not zero)
    auto off_of = [&](const char* k) -> std::string {
        std::string v = get(k);
        return (v.empty() || v == "auto") ? std::string() : v;
    };
    n->off_l = off_of("left"); n->off_t = off_of("top");
    n->off_r = off_of("right"); n->off_b = off_of("bottom");
    {
        std::string z = get("z-index");
        n->z_given = !z.empty() && z != "auto";
        n->z_index = n->z_given ? atoi(z.c_str()) : 0;
    }
    n->border_box = get("box-sizing").find("border-box") != std::string::npos;
    n->overflow_hidden = get("overflow") == "hidden";
    n->flex_row = get("flex-direction").find("row") != std::string::npos;
    bool ok = false;
    std::string bg = get("background-color");
    if (bg.empty()) bg = get("background");
    // only accept color forms (skip gradients/images — corpus bg is color)
    if (!bg.empty() && bg != "transparent") {
        uint32_t c = parse_css_color(bg, ok);
        if (ok) { n->bg = c; n->has_bg = true; }
    }
    std::string fg = get("color");
    if (!fg.empty()) {
        uint32_t c = parse_css_color(fg, ok);
        if (ok) { n->fg = c; n->has_fg = true; }
    }
    // S114: font-size resolves vw against the viewport WIDTH (the old call
    // passed vh — every vw-sized UI was 1.78× too large) and em against the
    // inherited size (fallback stays the legacy 28px document default).
    {
        float parent_em = 14.f * 2;
        for (DomNode* p = n->parent; p; p = p->parent)
            if (p->style.count("font-size")) { parent_em = p->font_size; break; }
        CssCtx fctx;
        fctx.vw = float(vw); fctx.vh = float(vh);
        fctx.pctw = float(vw); fctx.pcth = float(vh);
        fctx.em = parent_em;
        n->font_size = css_eval(get("font-size"), fctx, 14 * 2, 0);
    }
    // line-height: unitless factor or <length> (CSS 2.1 §10.8.1)
    {
        std::string lh = get("line-height");
        n->line_h_px = 0; n->line_h_num = -1.f;
        if (!lh.empty() && lh != "normal") {
            char* end = nullptr;
            float num = ::strtod(lh.c_str(), &end);
            if (end && *end == '\0' && lh.find_first_not_of("0123456789.-") == std::string::npos)
                n->line_h_num = num;                      // unitless factor law
            else {
                CssCtx lctx;
                lctx.vw = float(vw); lctx.vh = float(vh);
                lctx.pctw = float(vw); lctx.pcth = float(vh);
                lctx.em = n->font_size;
                n->line_h_px = int(css_eval(lh, lctx, 0, 0));
            }
        }
    }
    n->bold = get("font-weight") == "bold" || get("font-weight") == "700" ||
              get("font-weight") == "800" || get("font-weight") == "900";
    std::string ta = get("text-align");
    n->text_align = ta == "center" ? 1 : (ta == "right" ? 2 : 0);

    // ── S113/S114 CSS box model + paint properties ─────────────────────
    // S114: every length goes through css_eval — vw/vh/% units were silently
    // truncated by strtod before (Block'Buster: `padding: var(--size_5)`
    // = 5.6vw painted as 5px).
    auto len = [&](const std::string& v, float dflt, int axis) {
        CssCtx c;
        c.vw = float(vw); c.vh = float(vh);
        // margin/padding % resolve against the containing-block WIDTH
        // (CSS 2.1 §8.3/§8.4 — even top/bottom margins); CB approximated
        // by the viewport at style time, exact CB applied at layout.
        c.pctw = float(vw); c.pcth = float(vw);
        c.em = n->font_size;
        return css_eval(v, c, dflt, axis);
    };
    // padding: longhand-first cascade (apply_rule_to expanded single-value
    // shorthands into longhands, so a later longhand override wins per side);
    // multi-value shorthand path only when NO longhand exists
    {
        float v[4] = {0, 0, 0, 0};
        bool has_lh = n->style.count("padding-top") || n->style.count("padding-right") ||
                      n->style.count("padding-bottom") || n->style.count("padding-left");
        std::string pv = get("padding");
        if (has_lh) {
            v[0] = len(get("padding-top"), 0, 1);
            v[1] = len(get("padding-right"), 0, 0);
            v[2] = len(get("padding-bottom"), 0, 1);
            v[3] = len(get("padding-left"), 0, 0);
        } else if (!pv.empty()) {
            std::istringstream ss(pv); std::string tok; int k = 0;
            while (ss >> tok && k < 4) v[k++] = len(tok, 0, 0);
            if (k == 1) { v[1] = v[2] = v[3] = v[0]; }
            else if (k == 2) { v[2] = v[0]; v[3] = v[1]; }
            else if (k == 3) { v[3] = v[1]; }
        }
        n->pad_t = int(v[0]); n->pad_r = int(v[1]);
        n->pad_b = int(v[2]); n->pad_l = int(v[3]);
    }
    // margin: longhand-first cascade (same law as padding) + auto centering
    {
        float v[4] = {0, 0, 0, 0};
        bool has_lh = n->style.count("margin-top") || n->style.count("margin-right") ||
                      n->style.count("margin-bottom") || n->style.count("margin-left");
        std::string mv = get("margin");
        if (has_lh) {
            auto mside = [&](int idx, const char* k, int axis) {
                std::string s2 = get(k);
                if (s2 == "auto") { if (idx == 1 || idx == 3) n->mar_lr_auto = true; }
                else if (!s2.empty() && s2.find(' ') == std::string::npos)
                    v[idx] = len(s2, 0, axis);
            };
            mside(0, "margin-top", 1);
            mside(1, "margin-right", 0);
            mside(2, "margin-bottom", 1);
            mside(3, "margin-left", 0);
        } else if (!mv.empty()) {
            std::istringstream ss(mv); std::string tok; int k = 0;
            while (ss >> tok && k < 4) {
                if (tok == "auto") { if (k == 1 || k == 3) n->mar_lr_auto = true; v[k] = 0; }
                else v[k] = len(tok, 0, 0);
                ++k;
            }
            if (k == 1) { v[1] = v[2] = v[3] = v[0]; }
            else if (k == 2) { v[2] = v[0]; v[3] = v[1]; }
            else if (k == 3) { v[3] = v[1]; }
        }
        n->mar_t = int(v[0]); n->mar_r = int(v[1]);
        n->mar_b = int(v[2]); n->mar_l = int(v[3]);
        n->mar_t = std::max(-4096, std::min(4096, n->mar_t));
        n->mar_b = std::max(-4096, std::min(4096, n->mar_b));
    }
    // border shorthand: "4px solid #ffcde4" / "0.1vw solid rgba(...)"
    {
        std::string bs = get("border");
        if (!bs.empty()) {
            std::istringstream ss(bs);
            std::string wtok, styletok, coltok;
            ss >> wtok >> styletok >> coltok;
            int bw = int(len(wtok, 0, 0));
            bool okb = false;
            uint32_t col = coltok.empty() ? 0xff000000 : parse_css_color(coltok, okb);
            if (bw > 0 && styletok != "none") { n->border_w = bw; n->border_col = col; n->has_border = true; }
        }
        std::string bc = get("border-color");
        std::string bws = get("border-width");
        if (!bc.empty() && n->has_border) {
            bool okb = false; uint32_t col = parse_css_color(bc, okb);
            if (okb) n->border_col = col;
        }
        if (!bws.empty() && n->has_border)
            n->border_w = int(len(bws, 0, 0));
    }
    n->radius = int(len(get("border-radius"), 0, 0));
    // display law: flex / inline / inline-block / none (none handled above)
    {
        std::string disp = get("display");
        n->flex = disp == "flex";
        // S118 flex-direction default law (CSS Flexbox §4): the INITIAL
        // value of flex-direction is row. The engine read a missing
        // flex-direction as column — every `display:flex` container
        // without an explicit direction stacked on the wrong axis and
        // centered/stretched on the wrong one (accelerace's road).
        if (n->flex) {
            std::string fd = get("flex-direction");
            if (fd.find("column") != std::string::npos) n->flex_row = false;
            else n->flex_row = true;          // row / row-reverse / default
        }
        if (disp == "inline" || disp == "inline-block") n->inline_el = true;
        // S133 ATOMIC INLINE-BOX law: inline-block is an atomic box, not text
        if (disp == "inline-block") n->inline_block = true;
        if (n->tag == "span" || n->tag == "a" || n->tag == "b" || n->tag == "strong" ||
            n->tag == "em" || n->tag == "label" || n->tag == "small")
            if (disp.empty()) n->inline_el = true;
    }
    if (get("align-items") == "center") n->align_items = 1;
    if (get("justify-content") == "center") n->justify_content = 1;
    // width/height — S114 resolution ladder:
    //   plain "N%"            → w_pct/h_pct (resolved against the CB at layout)
    //   calc/%-bearing string → w_raw/h_raw (same, kept raw for calc forms)
    //   px/vw/vh/em           → has_w/has_h (immediate)
    // percentages must NOT set has_w (the 1126px-button double-resolution bug)
    {
        std::string ws = get("width"), hs = get("height");
        n->w_raw.clear(); n->h_raw.clear();
        n->w_pct = -1.f; n->h_pct = -1.f;
        n->has_w = false; n->has_h = false;   // stale-style law (JS property removal)
        if (!ws.empty() && ws != "auto") {
            if (ws.back() == '%') n->w_pct = float(::atof(ws.c_str()));
            else if (ws.find('%') != std::string::npos || ws.find("calc(") == 0)
                n->w_raw = ws;
            else { n->w = int(len(ws, 0, 0)); n->has_w = true; }
        }
        if (!hs.empty() && hs != "auto") {
            if (hs.back() == '%') n->h_pct = float(::atof(hs.c_str()));
            else if (hs.find('%') != std::string::npos || hs.find("calc(") == 0)
                n->h_raw = hs;
            else { n->h = int(len(hs, 0, 1)); n->has_h = true; }
        }
    }
    if (!get("max-width").empty())
        n->max_w = int(len(get("max-width"), -1, 0));
    // background-image / gradient / shorthand backgrounds
    {
        std::string bi = get("background-image");
        std::string bsh = get("background");
        std::string src = !bi.empty() ? bi : bsh;
        if (src.find("linear-gradient(") != std::string::npos) {
            size_t g0 = src.find("linear-gradient(") + 16;
            // S114: paren-DEPTH matching — rgba()/rgb() stops inside the
            // gradient body made the flat find(')') truncate the color list
            // (the Block'Buster title gradient silently failed to parse)
            size_t g1 = g0, gdepth = 1;
            for (; g1 < src.size() && gdepth; ++g1) {
                if (src[g1] == '(') ++gdepth;
                else if (src[g1] == ')') --gdepth;
            }
            if (gdepth == 0) --g1;
            if (g1 != std::string::npos) {
                std::string body = src.substr(g0, g1 - g0);
                // split top-level commas
                std::vector<std::string> parts;
                int depth = 0; std::string cur;
                for (char c : body) {
                    if (c == '(') ++depth;
                    if (c == ')') --depth;
                    if (c == ',' && depth == 0) { parts.push_back(trim2(cur)); cur.clear(); }
                    else cur += c;
                }
                parts.push_back(trim2(cur));
                size_t stop = 0;
                if (!parts.empty() && parts[0].find("#") == std::string::npos &&
                    parts[0].find("rgb") == std::string::npos)
                    stop = 1;  // direction part
                if (parts.size() >= stop + 2) {
                    bool ok1 = false, ok2 = false;
                    uint32_t c1 = parse_css_color(parts[stop], ok1);
                    uint32_t c2 = parse_css_color(parts[stop + 1], ok2);
                    if (ok1 && ok2) {
                        n->grad = true; n->grad_from = c1; n->grad_to = c2;
                        n->has_bg = false;  // gradient replaces the color
                        // S114 direction law (CSS Images §3.1): 0deg = to top,
                        // 90deg = to right, 180deg = to bottom; keywords too
                        std::string dir = lower_s(parts[0]);
                        if (dir.find("bottom") != std::string::npos &&
                            dir.find("right") != std::string::npos)
                            n->grad_diag = true;
                        else if (dir.find("top") != std::string::npos)
                            n->grad_dir = 1;      // to top
                        else if (dir.find("right") != std::string::npos)
                            n->grad_dir = 2;      // to right
                        else if (dir.find("left") != std::string::npos)
                            n->grad_dir = 3;
                        else if (!dir.empty() && dir.find("deg") != std::string::npos) {
                            float deg = ::atof(dir.c_str());
                            if (deg == 0) n->grad_dir = 1;
                            else if (deg == 90) n->grad_dir = 2;
                            else if (deg == 180) n->grad_dir = 0;
                            else if (deg == 270) n->grad_dir = 3;
                        }
                    }
                }
            }
        } else {
            size_t u0 = src.find("url(");
            if (u0 != std::string::npos) {
                size_t p0 = u0 + 4, pe = src.find(')', p0);
                if (pe != std::string::npos) {
                    std::string url = src.substr(p0, pe - p0);
                    url.erase(std::remove(url.begin(), url.end(), '"'), url.end());
                    url.erase(std::remove(url.begin(), url.end(), '\''), url.end());
                    n->bg_image = url;
                }
            }
        }
    }
    // S114 background-size: contain | N% (single-value = width, height auto)
    {
        std::string bsz = get("background-size");
        if (bsz.find("contain") != std::string::npos) n->bg_contain = true;
        else if (!bsz.empty() && bsz.back() == '%')
            n->bg_size_pct = float(::atof(bsz.c_str()));
    }
    if (get("transform").find("scaleX(-1)") != std::string::npos) n->bg_mirror = true;
    // S114 gradient-text law (-webkit-background-clip: text): the gradient
    // paints the GLYPHS, not the box (Block'Buster title, game logos).
    {
        std::string clip = get("-webkit-background-clip") + "," + get("background-clip");
        std::string fill = get("-webkit-text-fill-color");
        if (wv_trace() && n->grad)
            std::cerr << "[WV-GTXT] tag=" << n->tag << " grad=1 clip='" << clip
                      << "' fill='" << fill << "' => " << (clip.find("text") != std::string::npos || fill == "transparent" ? "GRADIENT-TEXT" : "box") << std::endl;
        if (n->grad && (clip.find("text") != std::string::npos || fill == "transparent")) {
            n->grad_text = true;
            n->grad = false;          // glyphs carry the gradient
            n->has_bg = false;
        }
    }
    // shadows
    {
        std::string ts = get("text-shadow");
        if (!ts.empty()) {
            size_t c0 = ts.find("rgba");
            if (c0 == std::string::npos) c0 = ts.find("#");
            if (c0 != std::string::npos) {
                bool oks = false;
                uint32_t col = parse_css_color(trim2(ts.substr(c0)), oks);
                if (oks) { n->text_shadow = true; n->text_shadow_col = col; }
            }
        }
        // S114 box-shadow parse: [inset] ox oy blur spread color — the spread
        // term is the dim-overlay idiom (`.info{box-shadow:0 0 1.4vw 150vw …}`)
        std::string bxs = get("box-shadow");
        if (!bxs.empty() && bxs.find("inset") == std::string::npos) {
            // split top-level tokens (color may be first or last)
            std::vector<std::string> toks;
            {
                std::istringstream ss(bxs); std::string tk;
                auto balanced = [](const std::string& t) {
                    int depth = 0;
                    for (char c : t) { if (c == '(') ++depth; else if (c == ')') --depth; }
                    return depth <= 0;
                };
                while (ss >> tk) {
                    if ((tk.rfind("rgba", 0) == 0 || tk.rfind("rgb", 0) == 0) &&
                        tk.back() != ')') {
                        std::string rest;
                        while (ss >> rest) { tk += " " + rest; if (rest.back() == ')') break; }
                    }
                    // S118 math-expression token law: calc()/var()/max()/min()
                    // fragments are ONE token (paren-balanced) — whitespace
                    // inside the expression split the old tokenizer and the
                    // blur/spread lengths parsed as 0 (every glow rendered
                    // as a hard-edged opaque slab)
                    else if ((tk.find("calc(") != std::string::npos ||
                              tk.find("var(") != std::string::npos ||
                              tk.find("max(") != std::string::npos ||
                              tk.find("min(") != std::string::npos) &&
                             !balanced(tk)) {
                        std::string rest;
                        while (ss >> rest) {
                            tk += " " + rest;
                            if (balanced(tk)) break;
                        }
                    }
                    toks.push_back(tk);
                }
            }
            float L[4] = {0, 0, 0, 0}; int li = 0;
            bool col_ok = false; uint32_t col = 0;
            for (auto& tk : toks) {
                bool okc = false;
                uint32_t c2 = parse_css_color(tk, okc);
                if (okc) { col = c2; col_ok = true; continue; }
                if (tk == "inset") continue;
                if (li < 4) L[li++] = len(tk, 0, 0);
            }
            n->box_shadow = true;
            n->sh_ox = int(L[0]); n->sh_oy = int(L[1]);
            n->sh_blur = int(L[2]); n->sh_spread = int(L[3]);
            if (col_ok) { n->sh_col = col; n->sh_col_valid = true; }
        } else {
            n->box_shadow = false;
            n->sh_col_valid = false; n->sh_spread = 0;
        }
    }
    // @font-face family resolution (Typeface.createFromAsset law)
    {
        auto fit = n->style.find("font-family");
        if (fit != n->style.end()) {
            std::string fams = lower_s(fit->second);
            size_t comma = fams.find(',');
            std::string first = comma == std::string::npos ? fams : fams.substr(0, comma);
            first.erase(std::remove(first.begin(), first.end(), '"'), first.end());
            first.erase(std::remove(first.begin(), first.end(), '\''), first.end());
            first = trim2(first);
            auto jit = font_map.find(first);
            if (jit != font_map.end()) n->font_face = jit->second;
        }
    }
    if (n->is_canvas && n->canvas) {
        // canvas CSS size: style width/height (px/vw forms — % forms stay in
        // w_pct/w_raw for the layout pass); bitmap = JS-set size
        std::string cw = get("width"), chh = get("height");
        if (!cw.empty() && cw != "auto" && cw.back() != '%' &&
            cw.find('%') == std::string::npos && cw.find("calc(") != 0)
            n->w = int(len(cw, float(n->canvas->width()), 0));
        if (!chh.empty() && chh != "auto" && chh.back() != '%' &&
            chh.find('%') == std::string::npos && chh.find("calc(") != 0)
            n->h = int(len(chh, float(n->canvas->height()), 1));
        // S133 REPLACED-ELEMENT INTRINSIC law (WHATWG HTML §4.12.4): the
        // canvas width=/height= ATTRIBUTES are the element's default box
        // (300x150 fallback) when CSS leaves it auto — attribute-only
        // canvases laid out 0x0 and never painted (T09 fixture).
        // The SAME attributes size the BITMAP (the attribute IS the bitmap
        // dimensions): a parsed canvas kept a 1x1 bitmap, so fillRect drew
        // into a degenerate surface (T09 draw_calls=2, zero pixels).
        if (n->canvas->width() <= 1 && n->canvas->height() <= 1) {
            auto aw = n->attrs.find("width");
            auto ah = n->attrs.find("height");
            int bw = aw != n->attrs.end() ? atoi(aw->second.c_str()) : 300;
            int bh = ah != n->attrs.end() ? atoi(ah->second.c_str()) : 150;
            n->canvas->set_size(std::max(1, bw), std::max(1, bh));
        }
        if (!n->has_w && cw.empty()) {
            auto aw = n->attrs.find("width");
            if (aw != n->attrs.end()) {
                n->w = std::max(1, atoi(aw->second.c_str()));
                n->has_w = true;
            } else {
                n->w = 300;
                n->has_w = true;
            }
        }
        if (!n->has_h && chh.empty()) {
            auto ah = n->attrs.find("height");
            if (ah != n->attrs.end()) {
                n->h = std::max(1, atoi(ah->second.c_str()));
                n->has_h = true;
            } else {
                n->h = 150;
                n->has_h = true;
            }
        }
        if (wv_trace())
            std::cerr << "[WV-CANVAS] id=" << (n->attrs.count("id") ? n->attrs.at("id") : "")
                      << " css_w=" << cw << " css_h=" << chh
                      << " -> box " << n->w << "x" << n->h
                      << " bitmap " << n->canvas->width() << "x" << n->canvas->height()
                      << " positioned=" << n->positioned << std::endl;
    }
    // ── S133 REPLACED-IMAGE law (WHATWG HTML §4.8.3 <img>) ──────────────
    // <img> is an atomic inline-level replaced element. Box: CSS width/
    // height (the resolution ladder) else the width=/height= attributes.
    // The source fetches through the SAME resource substrate (network or
    // asset) at paint; decode errors keep the honest empty box.
    if (n->tag == "img") {
        n->inline_el = true;
        n->inline_block = true;
        if (!n->has_w) {
            auto aw = n->attrs.find("width");
            if (aw != n->attrs.end()) {
                n->w = std::max(1, atoi(aw->second.c_str()));
                n->has_w = true;
            }
        }
        if (!n->has_h) {
            auto ah = n->attrs.find("height");
            if (ah != n->attrs.end()) {
                n->h = std::max(1, atoi(ah->second.c_str()));
                n->has_h = true;
            }
        }
    }
    // (the non-canvas duplicate width re-resolution was REMOVED — it
    // double-resolved % strings against the viewport and polluted n->w/h
    // behind the layout pass's back; the S114 ladder above is the single
    // resolution site)
}

// ── S117 inline-SVG law: generic SVG2 shape materialization ─────────────
// <svg> is a replaced leaf box; <path> paints through the page framebuffer
// (nonzero-winding scanline fill, SVG2 default); <use xlink:href="#id">
// resolves to <symbol>/<path> definitions (a <symbol> never renders in
// place — SVG2 §5.6); viewBox maps into the element box with the
// xMidYMid-meet law. Modern HTML5 UIs ship icons and figures as inline SVG
// — a document-engine capability, not an app-specific patch (weather icon
// sets, accelerace car figures, and the whole svg-icon idiom).
struct SvgPt { float x, y; };

static bool svg_viewbox(DomNode* n, float& vx, float& vy, float& vw, float& vh) {
    auto it = n->attrs.find("viewbox");        // HTML stream is lowercased
    if (it == n->attrs.end()) it = n->attrs.find("viewBox");
    if (it == n->attrs.end()) return false;
    if (sscanf(it->second.c_str(), "%f %f %f %f", &vx, &vy, &vw, &vh) != 4) return false;
    return vw > 0 && vh > 0;
}

static inline void svg_ws(const char*& p) {
    while (*p == ' ' || *p == ',' || *p == '\n' || *p == '\r' || *p == '\t') ++p;
}
static inline bool svg_num(const char*& p, float& out) {
    svg_ws(p);
    const char* q = p;
    if (*p == '+' || *p == '-') ++p;
    bool dig = false;
    while (*p >= '0' && *p <= '9') { ++p; dig = true; }
    if (*p == '.') { ++p; while (*p >= '0' && *p <= '9') { ++p; dig = true; } }
    if (!dig) { p = q; return false; }
    if (*p == 'e' || *p == 'E') {
        const char* r = p + 1;
        if (*r == '+' || *r == '-') ++r;
        if (*r >= '0' && *r <= '9') { p = r; while (*p >= '0' && *p <= '9') ++p; }
    }
    out = float(strtod(q, nullptr));
    return true;
}

// Flatten path data to device-space subpaths (a,b,c,d,e,f: user→device
// affine x' = a·x + c·y + e, y' = b·x + d·y + f). Cubics 12 seg, quads 10,
// arcs 14 (endpoint→center parameterization, SVG F.6).
static std::vector<std::vector<SvgPt>> svg_flatten(const std::string& dstr,
                                                   float a, float b, float c, float dd,
                                                   float e, float f) {
    std::vector<std::vector<SvgPt>> subs;
    size_t cur = SIZE_MAX;
    const char* p = dstr.c_str();
    float cx = 0, cy = 0, sx = 0, sy = 0;
    float lc1x = 0, lc1y = 0, lqx = 0, lqy = 0;
    bool has_lc = false, has_lq = false;
    char cmd = 0;
    auto xform = [&](float ux, float uy) -> SvgPt {
        return {a * ux + c * uy + e, b * ux + dd * uy + f};
    };
    auto ensure = [&](float ux, float uy) {
        if (cur == SIZE_MAX) {
            subs.emplace_back();
            cur = subs.size() - 1;
            subs[cur].push_back(xform(ux, uy));
        }
    };
    auto line_to = [&](float ux, float uy) {
        ensure(cx, cy);
        subs[cur].push_back(xform(ux, uy));
        cx = ux; cy = uy;
    };
    auto moveto = [&](float ux, float uy) {
        subs.emplace_back();
        cur = subs.size() - 1;
        subs[cur].push_back(xform(ux, uy));
        cx = ux; cy = uy; sx = ux; sy = uy;
    };
    while (true) {
        svg_ws(p);
        if (!*p) break;
        if (strchr("MmLlHhVvCcSsQqTtAaZz", *p)) { cmd = *p++; svg_ws(p); }
        float n1, n2, n3, n4, n5, n6, n7;
        switch (cmd) {
        case 'M': case 'm': {
            if (!svg_num(p, n1)) break;
            if (!svg_num(p, n2)) break;
            moveto(cmd == 'M' ? n1 : cx + n1, cmd == 'M' ? n2 : cy + n2);
            cmd = (cmd == 'M') ? 'L' : 'l';      // implicit repeats
            break; }
        case 'L': case 'l': {
            if (!svg_num(p, n1) || !svg_num(p, n2)) break;
            line_to(cmd == 'L' ? n1 : cx + n1, cmd == 'L' ? n2 : cy + n2);
            break; }
        case 'H': case 'h': {
            if (!svg_num(p, n1)) break;
            line_to(cmd == 'H' ? n1 : cx + n1, cy);
            break; }
        case 'V': case 'v': {
            if (!svg_num(p, n1)) break;
            line_to(cx, cmd == 'V' ? n1 : cy + n1);
            break; }
        case 'C': case 'c': {
            if (!svg_num(p, n1) || !svg_num(p, n2) || !svg_num(p, n3) ||
                !svg_num(p, n4) || !svg_num(p, n5) || !svg_num(p, n6)) break;
            float x0 = cx, y0 = cy;
            float x1 = cmd == 'C' ? n1 : cx + n1, y1 = cmd == 'C' ? n2 : cy + n2;
            float x2 = cmd == 'C' ? n3 : cx + n3, y2 = cmd == 'C' ? n4 : cy + n4;
            float x3 = cmd == 'C' ? n5 : cx + n5, y3 = cmd == 'C' ? n6 : cy + n6;
            ensure(x0, y0);
            for (int k = 1; k <= 12; ++k) {
                float t = k / 12.f, mt = 1 - t;
                float bx = mt*mt*mt*x0 + 3*mt*mt*t*x1 + 3*mt*t*t*x2 + t*t*t*x3;
                float by = mt*mt*mt*y0 + 3*mt*mt*t*y1 + 3*mt*t*t*y2 + t*t*t*y3;
                subs[cur].push_back(xform(bx, by));
            }
            cx = x3; cy = y3; lc1x = x2; lc1y = y2; has_lc = true; has_lq = false;
            break; }
        case 'S': case 's': {
            if (!svg_num(p, n1) || !svg_num(p, n2) || !svg_num(p, n3) ||
                !svg_num(p, n4)) break;
            float x0 = cx, y0 = cy;
            float x1 = has_lc ? 2 * cx - lc1x : cx, y1 = has_lc ? 2 * cy - lc1y : cy;
            float x2 = cmd == 'S' ? n1 : cx + n1, y2 = cmd == 'S' ? n2 : cy + n2;
            float x3 = cmd == 'S' ? n3 : cx + n3, y3 = cmd == 'S' ? n4 : cy + n4;
            ensure(x0, y0);
            for (int k = 1; k <= 12; ++k) {
                float t = k / 12.f, mt = 1 - t;
                float bx = mt*mt*mt*x0 + 3*mt*mt*t*x1 + 3*mt*t*t*x2 + t*t*t*x3;
                float by = mt*mt*mt*y0 + 3*mt*mt*t*y1 + 3*mt*t*t*y2 + t*t*t*y3;
                subs[cur].push_back(xform(bx, by));
            }
            cx = x3; cy = y3; lc1x = x2; lc1y = y2; has_lc = true; has_lq = false;
            break; }
        case 'Q': case 'q': {
            if (!svg_num(p, n1) || !svg_num(p, n2) || !svg_num(p, n3) ||
                !svg_num(p, n4)) break;
            float x0 = cx, y0 = cy;
            float x1 = cmd == 'Q' ? n1 : cx + n1, y1 = cmd == 'Q' ? n2 : cy + n2;
            float x2 = cmd == 'Q' ? n3 : cx + n3, y2 = cmd == 'Q' ? n4 : cy + n4;
            ensure(x0, y0);
            for (int k = 1; k <= 10; ++k) {
                float t = k / 10.f, mt = 1 - t;
                float bx = mt*mt*x0 + 2*mt*t*x1 + t*t*x2;
                float by = mt*mt*y0 + 2*mt*t*y1 + t*t*y2;
                subs[cur].push_back(xform(bx, by));
            }
            cx = x2; cy = y2; lqx = x1; lqy = y1; has_lq = true; has_lc = false;
            break; }
        case 'T': case 't': {
            if (!svg_num(p, n1) || !svg_num(p, n2)) break;
            float x0 = cx, y0 = cy;
            float x1 = has_lq ? 2 * cx - lqx : cx, y1 = has_lq ? 2 * cy - lqy : cy;
            float x2 = cmd == 'T' ? n1 : cx + n1, y2 = cmd == 'T' ? n2 : cy + n2;
            ensure(x0, y0);
            for (int k = 1; k <= 10; ++k) {
                float t = k / 10.f, mt = 1 - t;
                float bx = mt*mt*x0 + 2*mt*t*x1 + t*t*x2;
                float by = mt*mt*y0 + 2*mt*t*y1 + t*t*y2;
                subs[cur].push_back(xform(bx, by));
            }
            cx = x2; cy = y2; lqx = x1; lqy = y1; has_lq = true; has_lc = false;
            break; }
        case 'A': case 'a': {
            if (!svg_num(p, n1) || !svg_num(p, n2) || !svg_num(p, n3) ||
                !svg_num(p, n4) || !svg_num(p, n5) || !svg_num(p, n6) ||
                !svg_num(p, n7)) break;
            float rx = fabsf(n1), ry = fabsf(n2);
            float phi = n3 * float(M_PI) / 180.f;
            bool laf = n4 != 0, sf = n5 != 0;
            float x2 = cmd == 'a' ? cx + n6 : n6, y2 = cmd == 'a' ? cy + n7 : n7;
            float x1 = cx, y1 = cy;
            if (rx > 0 && ry > 0 && (x1 != x2 || y1 != y2)) {
                float cosp = cosf(phi), sinp = sinf(phi);
                float dx = (x1 - x2) / 2, dy = (y1 - y2) / 2;
                float x1p =  cosp * dx + sinp * dy;
                float y1p = -sinp * dx + cosp * dy;
                float l = x1p*x1p/(rx*rx) + y1p*y1p/(ry*ry);
                if (l > 1) { rx *= sqrtf(l); ry *= sqrtf(l); }
                float num = rx*rx*ry*ry - rx*rx*y1p*y1p - ry*ry*x1p*x1p;
                float den = rx*rx*y1p*y1p + ry*ry*x1p*x1p;
                float co = sqrtf(std::max(0.f, num / std::max(den, 1e-9f)));
                if (laf == sf) co = -co;
                float cxp =  co * rx * y1p / ry;
                float cyp = -co * ry * x1p / rx;
                float ccx = cosp * cxp - sinp * cyp + (x1 + x2) / 2;
                float ccy = sinp * cxp + cosp * cyp + (y1 + y2) / 2;
                float ux = (x1p - cxp) / rx, uy = (y1p - cyp) / ry;
                float vx2 = (-x1p - cxp) / rx, vy2 = (-y1p - cyp) / ry;
                float th1 = atan2f(uy, ux);
                float dth = acosf(std::max(-1.f, std::min(1.f,
                    (ux*vx2 + uy*vy2) /
                    std::max(sqrtf(ux*ux + uy*uy) * sqrtf(vx2*vx2 + vy2*vy2), 1e-9f))));
                if (ux * vy2 - uy * vx2 < 0) dth = -dth;
                if (!sf && dth > 0) dth -= float(2 * M_PI);
                if (sf && dth < 0) dth += float(2 * M_PI);
                for (int k = 1; k <= 14; ++k) {
                    float th = th1 + dth * k / 14;
                    float px2 = ccx + rx * cosf(th) * cosp - ry * sinf(th) * sinp;
                    float py2 = ccy + rx * cosf(th) * sinp + ry * sinf(th) * cosp;
                    line_to(px2, py2);
                }
            }
            cx = x2; cy = y2;
            break; }
        case 'Z': case 'z': {
            if (cur != SIZE_MAX) subs[cur].push_back(xform(sx, sy));
            cx = sx; cy = sy; cur = SIZE_MAX;
            break; }
        default:
            ++p;      // skip stray char (tolerant parse)
            break;
        }
    }
    return subs;
}

// ── S118 SVG shape geometry law ─────────────────────────────────────────
// getBoundingClientRect() on an SVG shape answers the geometry bbox in
// VIEWPORT coordinates (SVG2 SVGGeometryElement; browsers include the
// stroke). The affine mirrors the S117 paint law exactly (viewBox →
// element box, xMidYMid-meet), so what measures == what paints.
// <use> resolves symbol/path definitions through the same mapping the
// paint path uses (symbol viewBox fitted into the use-site box).
static bool svg_inherited_prop(DomNode* n, const char* prop, std::string& out) {
    auto st = n->style.find(prop);
    if (st != n->style.end()) { out = st->second; return true; }
    auto at = n->attrs.find(prop);
    if (at != n->attrs.end()) { out = at->second; return true; }
    for (DomNode* p = n->parent; p; p = p->parent) {
        auto st2 = p->style.find(prop);
        if (st2 != p->style.end()) { out = st2->second; return true; }
        auto at2 = p->attrs.find(prop);
        if (at2 != p->attrs.end()) { out = at2->second; return true; }
    }
    return false;
}

static bool svg_shape_rect(DomNode* n, float vpw, float vph,
                           double& rx, double& ry, double& rw, double& rh) {
    static const char* shapes[] = {"path", "rect", "circle", "ellipse",
                                   "line", "polygon", "polyline", "use"};
    bool is_shape = false;
    for (const char* s2 : shapes)
        if (n->tag == s2) { is_shape = true; break; }
    if (!is_shape) return false;
    // nearest laid-out <svg> ancestor
    DomNode* svg = nullptr;
    for (DomNode* p = n->parent; p; p = p->parent)
        if (p->tag == "svg" && p->w > 0 && p->h > 0) { svg = p; break; }
    if (!svg) return false;
    float vx = 0, vy = 0, vw2 = 0, vh2 = 0;
    float s, E, F;
    if (svg_viewbox(svg, vx, vy, vw2, vh2)) {
        s = std::min(float(svg->w) / vw2, float(svg->h) / vh2);
        E = float(svg->x) + (float(svg->w) - vw2 * s) / 2.f - vx * s;
        F = float(svg->y) + (float(svg->h) - vh2 * s) / 2.f - vy * s;
    } else { s = 1.f; E = float(svg->x); F = float(svg->y); }
    float minx = 1e30f, miny = 1e30f, maxx = -1e30f, maxy = -1e30f;
    bool any = false;
    auto acc = [&](float px, float py) {
        any = true;
        minx = std::min(minx, px); miny = std::min(miny, py);
        maxx = std::max(maxx, px); maxy = std::max(maxy, py);
    };
    auto num_attr = [&](DomNode* m, const char* k, float dflt) -> float {
        auto it = m->attrs.find(k);
        return it == m->attrs.end() ? dflt : strtof(it->second.c_str(), nullptr);
    };
    std::function<bool(DomNode*, float, float, float, float, float, float)>
        geo_of = [&](DomNode* m, float A, float B, float C, float D,
                     float E2, float F2) -> bool {
        auto pt = [&](float ux, float uy) {
            acc(A * ux + C * uy + E2, B * ux + D * uy + F2);
        };
        if (m->tag == "path") {
            auto dit = m->attrs.find("d");
            if (dit == m->attrs.end() || dit->second.empty()) return false;
            auto subs = svg_flatten(dit->second, A, B, C, D, E2, F2);
            for (auto& sp : subs) for (auto& p2 : sp) acc(p2.x, p2.y);
            return !subs.empty();
        }
        if (m->tag == "rect") {
            float x = num_attr(m, "x", 0), y = num_attr(m, "y", 0);
            float w2 = num_attr(m, "width", 0), h2 = num_attr(m, "height", 0);
            pt(x, y); pt(x + w2, y); pt(x, y + h2); pt(x + w2, y + h2);
            return true;
        }
        if (m->tag == "circle" || m->tag == "ellipse") {
            float cx = num_attr(m, "cx", 0), cy = num_attr(m, "cy", 0);
            float r2 = m->tag == "circle" ? num_attr(m, "r", 0) : num_attr(m, "rx", 0);
            float r3 = m->tag == "circle" ? r2 : num_attr(m, "ry", 0);
            pt(cx - r2, cy - r3); pt(cx + r2, cy - r3);
            pt(cx - r2, cy + r3); pt(cx + r2, cy + r3);
            return true;
        }
        if (m->tag == "line") {
            pt(num_attr(m, "x1", 0), num_attr(m, "y1", 0));
            pt(num_attr(m, "x2", 0), num_attr(m, "y2", 0));
            return true;
        }
        if (m->tag == "polygon" || m->tag == "polyline") {
            auto pit = m->attrs.find("points");
            if (pit != m->attrs.end()) {
                const char* p3 = pit->second.c_str();
                float nx, ny;
                while (svg_num(p3, nx) && svg_num(p3, ny)) pt(nx, ny);
                return true;
            }
            return false;
        }
        if (m->tag == "use") {
            std::string href;
            auto h1 = m->attrs.find("xlink:href");
            auto h2 = m->attrs.find("href");
            if (h1 != m->attrs.end()) href = h1->second;
            else if (h2 != m->attrs.end()) href = h2->second;
            if (href.size() < 2 || href[0] != '#') return false;
            DomNode* tgt = find_by_id(svg, href.substr(1));
            if (!tgt) return false;
            if (tgt->tag == "symbol") {
                float svx, svy, svw, svh;
                if (svg_viewbox(tgt, svx, svy, svw, svh)) {
                    // paint law: symbol viewBox fitted into the use-site box
                    float s2 = std::min(float(svg->w) / svw, float(svg->h) / svh);
                    float E3 = float(svg->x) + (float(svg->w) - svw * s2) / 2.f - svx * s2;
                    float F3 = float(svg->y) + (float(svg->h) - svh * s2) / 2.f - svy * s2;
                    bool got = false;
                    for (auto& ch : tgt->children)
                        got = geo_of(ch.get(), s2, 0, 0, s2, E3, F3) || got;
                    return got;
                }
            }
            bool got = false;
            for (auto& ch : tgt->children)
                got = geo_of(ch.get(), A, B, C, D, E2, F2) || got;
            if (tgt->tag == "path") got = geo_of(tgt, A, B, C, D, E2, F2) || got;
            return got;
        }
        if (m->tag == "g" || m->tag == "svg" || m->tag == "a") {
            bool got = false;
            for (auto& ch : m->children)
                got = geo_of(ch.get(), A, B, C, D, E2, F2) || got;
            return got;
        }
        return false;
    };
    geo_of(n, s, 0, 0, s, E, F);
    if (!any) return false;
    // stroke expansion (browsers include stroke in getBoundingClientRect)
    std::string sw;
    if (svg_inherited_prop(n, "stroke-width", sw)) {
        // S118 length law: stroke-width resolves through the CSS evaluator
        CssCtx gcx;
        gcx.vw = vpw; gcx.vh = vph;
        gcx.pctw = float(svg->w); gcx.pcth = float(svg->h);
        float swu = 0;
        {
            float r3 = css_eval(sw, gcx, -1.f, 0);
            swu = r3 > 0 ? r3 : strtof(sw.c_str(), nullptr);
        }
        if (swu > 0) {
            float half = swu * s / 2.f;
            minx -= half; miny -= half; maxx += half; maxy += half;
        }
    }
    rx = minx; ry = miny; rw = maxx - minx; rh = maxy - miny;
    return true;
}

// nonzero-winding scanline fill (SVG2 fill-rule default) across ALL
// subpaths — inter-subpath winding accumulates, so donut glyphs keep holes
static void svg_fill_paths(renderer::FrameBuffer* fb, int W, int H,
                           const std::vector<std::vector<SvgPt>>& subs,
                           renderer::RGBA col) {
    if (subs.empty() || W <= 0 || H <= 0) return;
    struct Edge { float x0, y0, x1, y1; };
    std::vector<Edge> edges;
    float miny = 1e9f, maxy = -1e9f;
    for (auto& s : subs) {
        if (s.size() < 3) continue;
        for (size_t i = 0; i < s.size(); ++i) {
            const SvgPt& p0 = s[i == 0 ? s.size() - 1 : i - 1];
            const SvgPt& p1 = s[i];
            if (p0.y == p1.y) continue;              // horizontal: no crossing
            edges.push_back({p0.x, p0.y, p1.x, p1.y});
            miny = std::min(miny, std::min(p0.y, p1.y));
            maxy = std::max(maxy, std::max(p0.y, p1.y));
        }
    }
    if (edges.empty()) return;
    int y0 = std::max(0, int(floorf(miny)) + 1);
    int y1 = std::min(H - 1, int(ceilf(maxy)));
    std::vector<std::pair<float, int>> xv;
    for (int yy = y0; yy <= y1; ++yy) {
        float sy = yy + 0.5f;
        xv.clear();
        for (auto& e2 : edges)
            if ((e2.y0 <= sy && e2.y1 > sy) || (e2.y1 <= sy && e2.y0 > sy)) {
                float t = (sy - e2.y0) / (e2.y1 - e2.y0);
                xv.push_back({e2.x0 + t * (e2.x1 - e2.x0), e2.y1 > e2.y0 ? 1 : -1});
            }
        if (xv.empty()) continue;
        std::sort(xv.begin(), xv.end());
        int wind = 0;
        float span0 = 0;
        for (auto& q : xv) {
            if (wind == 0) span0 = q.first;
            wind += q.second;
            if (wind == 0) {
                int xa = std::max(0, int(ceilf(span0 - 0.5f)));
                int xb = std::min(W - 1, int(ceilf(q.first - 0.5f)) - 1);
                for (int xx = xa; xx <= xb; ++xx) fb->set_pixel(xx, yy, col);
            }
        }
    }
}

// stroke law: polyline stroking via disc stamping along each segment —
// round caps/joins for free, device width = user stroke-width × scale
static void svg_stroke_paths(renderer::FrameBuffer* fb, int W, int H,
                             const std::vector<std::vector<SvgPt>>& subs,
                             renderer::RGBA col, float width) {
    int r = std::max(0, int(width / 2));
    if (r <= 0 && width <= 0) return;
    if (r < 1) r = 1;
    long stamped = 0;
    float mnx = 1e9f, mny = 1e9f, mxx = -1e9f, mxy = -1e9f;
    for (auto& s : subs) {
        if (s.size() < 2) continue;
        for (size_t i = 1; i < s.size(); ++i) {
            float x0 = s[i - 1].x, y0 = s[i - 1].y, x1 = s[i].x, y1 = s[i].y;
            float len = sqrtf((x1 - x0) * (x1 - x0) + (y1 - y0) * (y1 - y0));
            int steps = std::max(1, int(len));
            for (int k = 0; k <= steps; ++k) {
                float t = k / float(steps);
                int ccx = int(x0 + (x1 - x0) * t), ccy = int(y0 + (y1 - y0) * t);
                mnx = std::min(mnx, float(ccx)); mny = std::min(mny, float(ccy));
                mxx = std::max(mxx, float(ccx)); mxy = std::max(mxy, float(ccy));
                for (int yy = ccy - r; yy <= ccy + r; ++yy)
                    for (int xx = ccx - r; xx <= ccx + r; ++xx) {
                        if (xx < 0 || xx >= W || yy < 0 || yy >= H) continue;
                        if ((xx - ccx) * (xx - ccx) + (yy - ccy) * (yy - ccy) <= r * r) {
                            fb->set_pixel(xx, yy, col);
                            ++stamped;
                        }
                    }
            }
        }
    }
    if (wv_trace())
        std::cerr << "[WV-SVG-STROKE] w=" << width << " stamped=" << stamped
                  << " bbox=(" << mnx << "," << mny << ")-(" << mxx << "," << mxy
                  << ") col=(" << int(col.r) << "," << int(col.g) << "," << int(col.b) << ")"
                  << std::endl;
}

void WebViewEngine::render(uint8_t* dst, int w, int h) {
    auto* impl = impl_.get();
    if (!impl || !impl->ctx) return;
    impl->viewport_w = w;
    impl->viewport_h = h;
    auto* surface_fb = impl->surface.get();
    if (!surface_fb || surface_fb->get_width() != w || surface_fb->get_height() != h) {
        impl->surface = std::make_unique<renderer::FrameBuffer>(w, h);
        surface_fb = impl->surface.get();
    }
    // page background: white (browser default) then body bg
    surface_fb->clear(renderer::Colors::WHITE);

    // ══ S113 FULL-GUI RENDER LAW ═════════════════════════════════════════
    // The render criterion is the COMPLETE graphical interface — CSS box
    // layout (block + flex column), colors, borders, radii, gradients,
    // images, shadows, pseudo-elements, typography — not merely "content
    // present". Honest approximations: single-line text runs, px-only
    // shorthands, static paint (CSS animations skipped).

    // 0. @media evaluation — once per viewport width (constant per run).
    if (impl->css_viewport_w != w) {
        impl->active_rules.clear();
        for (auto& r : impl->css_rules) {
            if (r.media_min_w >= 0 && w < r.media_min_w) continue;
            if (r.media_max_w >= 0 && w > r.media_max_w) continue;
            impl->active_rules.push_back(r);
        }
        HtmlParser::apply_css(impl->doc.root.get(), impl->active_rules,
                              &impl->custom_props);
        impl->css_viewport_w = w;
        std::cerr << "[WV-CSS] viewport=" << w
                  << " active_rules=" << impl->active_rules.size() << std::endl;
    }

    // side tables (deterministic per render)
    std::map<const DomNode*, std::string> merged_text;
    std::map<const DomNode*, std::pair<int, int>> text_line;   // #text → (y_top, width)

    auto face_of = [&](DomNode* n) {
        return n->eff_face >= 0 ? n->eff_face : int(fonts::FACE_SYSTEM);
    };

    // 1. style walk: box-model resolution + inheritance + pseudo rules.
    // S114: ::before/::after MATERIALIZED as real boxes (the browser model —
    // CSS2.1 §12.1: pseudo-elements behave like real children). Box props
    // (position/size/background/border) apply through the ordinary
    // style_element path; the content string becomes a #text child.
    std::function<void(DomNode*, DomNode*, int)> style_walk =
        [&](DomNode* n, DomNode* parent, int sw_depth) {
        if (sw_depth > 300) {
            if (wv_trace())
                std::cerr << "[WV-DEPTH] style_walk overflow at tag=" << n->tag << std::endl;
            return;
        }
        if (n->tag == "script" || n->tag == "style" || n->tag == "head" ||
            n->tag == "title" || n->tag == "link" || n->tag == "meta")
            return;
        style_element(n, double(w), double(h), impl->font_family_map);
        if (wv_trace() && (n->tag == "h1" ||
                           (n->attrs.count("class") && n->attrs.at("class") == "wrap"))) {
            std::cerr << "[WV-STYLE] tag=" << n->tag;
            for (auto& kv : n->style) std::cerr << " | " << kv.first << "=" << kv.second;
            std::cerr << std::endl;
        }
        if (parent) {
            n->eff_fg = n->has_fg ? n->fg : parent->eff_fg;
            n->eff_fg_valid = n->has_fg || parent->eff_fg_valid;
            n->eff_face = n->font_face >= 0 ? n->font_face : parent->eff_face;
            n->eff_font_size = n->style.count("font-size")
                ? n->font_size : parent->eff_font_size;
            n->eff_bold = n->bold || parent->eff_bold;
            // text-align tri-state law: explicit prop wins (including
            // left!) — 0 must not mean "unset" or .choice-button's
            // text-align:left would inherit the container's center.
            n->eff_align = n->style.count("text-align")
                ? (n->style.at("text-align") == "center" ? 1
                  : n->style.at("text-align") == "right" ? 2 : 0)
                : parent->eff_align;
            // S114 visibility chain: inherits, but an own `visibility:
            // visible` RESETS it (the h1-span-hidden/icon-visible law)
            n->eff_vis_hidden = n->vis_hidden_own ? true : parent->eff_vis_hidden;
            if (n->style.count("visibility") &&
                n->style.at("visibility") == "visible")
                n->eff_vis_hidden = false;
        } else {
            n->eff_fg = n->fg; n->eff_fg_valid = n->has_fg;
            n->eff_face = n->font_face;
            n->eff_font_size = n->font_size;
            n->eff_bold = n->bold;
            n->eff_align = n->text_align;
            n->eff_vis_hidden = n->vis_hidden_own;
        }
        // S114 pseudo-box sync (reuse law): pseudo boxes are PERSISTENT —
        // matched by (slot, rule-index) and updated in place. Destroying and
        // recreating them every render dangled the JS wrapper cache
        // (el_objs keyed by raw node ptr) — the accelerace heap crash.
        if (false && n->tag != "#pseudo") {  // S114-PSEUDO-DISABLED-EXPERIMENT
            // gather the matching pseudo rules in order
            struct PseudoHit { const CssRule* rule; };
            std::vector<const CssRule*> before_rules, after_rules;
            for (auto& r : impl->active_rules) {
                if (!r.pseudo_before && !r.pseudo_after) continue;
                if (!HtmlParser::matches_selector(r.selector, n)) continue;
                (r.pseudo_before ? before_rules : after_rules).push_back(&r);
            }
            auto sync_slot = [&](const std::vector<const CssRule*>& rules,
                                 std::vector<DomNode*>& slot) {
                // slot = existing pseudo nodes for this side, in order
                for (size_t i = 0; i < rules.size(); ++i) {
                    const CssRule* r = rules[i];
                    DomNode* p = nullptr;
                    if (i < slot.size()) {
                        p = slot[i];
                    } else {
                        auto np = std::make_unique<DomNode>();
                        np->tag = "#pseudo";
                        np->parent = n;
                        np->attrs["pseudo"] = r->pseudo_before ? "before" : "after";
                        p = np.get();
                        n->children.insert(
                            r->pseudo_before ? n->children.begin() + i
                                             : n->children.end(),
                            std::move(np));
                        slot.push_back(p);
                    }
                    p->style.clear();
                    p->inline_keys.clear();
                    for (auto& kv : r->props) {
                        if (kv.first == "content") continue;
                        p->style[kv.first] =
                            HtmlParser::resolve_var_string(kv.second, impl->custom_props);
                    }
                    std::string content;
                    auto cit = r->props.find("content");
                    if (cit != r->props.end()) {
                        content = cit->second;
                        if (content.size() >= 2 &&
                            (content.front() == '"' || content.front() == '\''))
                            content = content.substr(1, content.size() - 2);
                    }
                    std::string disp = p->style.count("display") ? p->style.at("display") : "";
                    std::string ppos = p->style.count("position") ? p->style.at("position") : "";
                    p->inline_el = !(disp == "block" || ppos == "absolute" || ppos == "fixed");
                    p->children.clear();
                    if (!content.empty()) {
                        auto t = std::make_unique<DomNode>();
                        t->tag = "#text";
                        t->text = content;
                        t->parent = p;
                        p->children.push_back(std::move(t));
                    }
                    style_element(p, double(w), double(h), impl->font_family_map);
                    p->eff_fg = p->has_fg ? p->fg : n->eff_fg;
                    p->eff_fg_valid = p->has_fg || n->eff_fg_valid;
                    p->eff_face = p->font_face >= 0 ? p->font_face : n->eff_face;
                    p->eff_font_size = p->style.count("font-size")
                        ? p->font_size : n->eff_font_size;
                    p->eff_bold = p->bold || n->eff_bold;
                    p->eff_align = n->eff_align;
                    p->eff_vis_hidden = p->vis_hidden_own ? true : n->eff_vis_hidden;
                    if (p->style.count("visibility") &&
                        p->style.at("visibility") == "visible")
                        p->eff_vis_hidden = false;
                }
                // surplus pseudos (rules stopped matching) → detach
                for (size_t i = rules.size(); i < slot.size(); ++i) {
                    DomNode* dead = slot[i];
                    for (auto cit2 = n->children.begin(); cit2 != n->children.end(); ++cit2)
                        if (cit2->get() == dead) { n->children.erase(cit2); break; }
                }
                slot.resize(rules.size());
            };
            std::vector<DomNode*> before_slot, after_slot;
            for (auto& c : n->children) {
                if (c->tag != "#pseudo") continue;
                if (c->attrs.count("pseudo") && c->attrs.at("pseudo") == "before")
                    before_slot.push_back(c.get());
                else
                    after_slot.push_back(c.get());
            }
            sync_slot(before_rules, before_slot);
            sync_slot(after_rules, after_slot);
        }
        for (auto& c : n->children) style_walk(c.get(), n, sw_depth + 1);
    };
    style_walk(impl->doc.root.get(), nullptr, 0);

    // own merged inline text of a node (spans merge into the parent flow;
    // block children own their own lines — the S112 duplicate-text law fix).
    // S114: visibility:hidden subtrees contribute NO text (CSS §11.5 — the
    // h1 span keeps its slot but its "o" glyph vanishes behind the icon).
    std::function<void(DomNode*, std::string&)> gather_inline =
        [&](DomNode* c, std::string& out) {
        if (c->eff_vis_hidden) return;
        if (c->tag == "#text") { out += c->text; return; }
        // S133: inline-block is ATOMIC (CSS 2.1 §9.2.2) — its text belongs
        // to its own box, never to the parent's merged run
        if (c->inline_block) return;
        if (c->inline_el) for (auto& g : c->children) gather_inline(g.get(), out);
    };
    auto own_text_of = [&](DomNode* n) -> std::string {
        auto it = merged_text.find(n);
        if (it != merged_text.end()) return it->second;
        std::string out;
        for (auto& c : n->children) gather_inline(c.get(), out);
        // whitespace-only merged text renders nothing (CSS white-space
        // collapsing law — the newlines between block divs are HAM-less)
        if (out.find_first_not_of(" \t\r\n") == std::string::npos) out.clear();
        merged_text[n] = out;
        return out;
    };
    auto is_ws_text = [](const std::string& t) {
        return t.find_first_not_of(" \t\r\n") == std::string::npos;
    };

    // ROOT-051 law (CSS Backgrounds — the canvas background): the ROOT
    // element's (html, else body) background propagates to the viewport
    // canvas BEFORE any child paints. html/body are excluded from the flow
    // painter, so without this propagation the page stayed white even when
    // the document set a real theme color (--background1:#030c23).
    {
        DomNode* body = nullptr;
        std::function<DomNode*(DomNode*)> find_body = [&](DomNode* n) -> DomNode* {
            for (auto& c : n->children) {
                if (c->tag == "body") return c.get();
                if (auto* r = find_body(c.get())) return r;
            }
            return nullptr;
        };
        body = find_body(impl->doc.root.get());
        DomNode* bg_src = impl->doc.root->has_bg ? (DomNode*)impl->doc.root.get() : body;
        if (wv_trace())
            std::cerr << "[WV-BG] root_has_bg=" << impl->doc.root->has_bg
                      << " body=" << (body ? "yes" : "no")
                      << " body_has_bg=" << (body ? body->has_bg : -1)
                      << " body_style_bg=" << (body && body->style.count("background-color")
                                               ? body->style["background-color"] : "<none>")
                      << std::endl;
        if (bg_src && bg_src->has_bg) {
            renderer::RGBA c{uint8_t(bg_src->bg & 255), uint8_t((bg_src->bg >> 8) & 255),
                             uint8_t((bg_src->bg >> 16) & 255), 255};
            for (auto& px : surface_fb->get_pixels_mut()) px = c;
        }
    }

    // 2. raster helpers — rounded-rect laws (per-pixel, alpha blending)
    auto in_round = [&](int px, int py, int x, int y, int rw, int rh, int r) -> bool {
        if (rw <= 0 || rh <= 0) return false;
        if (px < x || px >= x + rw || py < y || py >= y + rh) return false;
        if (r <= 0) return true;
        if (r > rw / 2) r = rw / 2;
        if (r > rh / 2) r = rh / 2;
        int dx = 0, dy = 0;
        if (px < x + r) dx = x + r - px;
        else if (px >= x + rw - r) dx = px - (x + rw - r - 1);
        if (py < y + r) dy = y + r - py;
        else if (py >= y + rh - r) dy = py - (y + rh - r - 1);
        return dx * dx + dy * dy <= r * r;
    };
    auto fill_round = [&](int x, int y, int rw, int rh, int r, renderer::RGBA col) {
        for (int yy = std::max(0, y); yy < std::min(h, y + rh); ++yy)
            for (int xx = std::max(0, x); xx < std::min(w, x + rw); ++xx)
                if (in_round(xx, yy, x, y, rw, rh, r)) surface_fb->set_pixel(xx, yy, col);
    };
    auto fill_round_grad = [&](int x, int y, int rw, int rh, int r, bool diag,
                               uint32_t from, uint32_t to, int dir = 0) {
        renderer::RGBA c1{uint8_t(from & 255), uint8_t((from >> 8) & 255),
                          uint8_t((from >> 16) & 255), 255};
        renderer::RGBA c2{uint8_t(to & 255), uint8_t((to >> 8) & 255),
                          uint8_t((to >> 16) & 255), 255};
        float denom = diag && (rw + rh) > 0 ? float(rw + rh) : float(rh > 0 ? rh : 1);
        float denom_x = float(rw > 0 ? rw : 1);
        for (int yy = std::max(0, y); yy < std::min(h, y + rh); ++yy)
            for (int xx = std::max(0, x); xx < std::min(w, x + rw); ++xx) {
                if (!in_round(xx, yy, x, y, rw, rh, r)) continue;
                float t;
                if (diag) t = float((xx - x) + (yy - y)) / denom;
                else if (dir == 2) t = float(xx - x) / denom_x;       // to right
                else if (dir == 3) t = 1.f - float(xx - x) / denom_x; // to left
                else if (dir == 1) t = 1.f - float(yy - y) / denom;   // to top
                else t = float(yy - y) / denom;                        // to bottom
                t = std::max(0.f, std::min(1.f, t));
                renderer::RGBA c{uint8_t(c1.r + (c2.r - c1.r) * t),
                                 uint8_t(c1.g + (c2.g - c1.g) * t),
                                 uint8_t(c1.b + (c2.b - c1.b) * t), 255};
                surface_fb->set_pixel(xx, yy, c);
            }
    };
    auto stroke_round_ring = [&](int x, int y, int rw, int rh, int r, int bw,
                                 renderer::RGBA col) {
        if (bw <= 0) return;
        int ir = std::max(0, r - bw);
        for (int yy = std::max(0, y); yy < std::min(h, y + rh); ++yy)
            for (int xx = std::max(0, x); xx < std::min(w, x + rw); ++xx) {
                if (!in_round(xx, yy, x, y, rw, rh, r)) continue;
                if (in_round(xx, yy, x + bw, y + bw, std::max(0, rw - 2 * bw),
                             std::max(0, rh - 2 * bw), ir))
                    continue;
                surface_fb->set_pixel(xx, yy, col);
            }
    };
    // background-image (APK asset PNG law, contain fit, optional mirror)
    auto draw_bg_image = [&](DomNode* n) {
        auto it = impl->img_cache.find(n->bg_image);
        if (it == impl->img_cache.end()) {
            WebViewEngine::Impl::CachedImg img;
            auto bytes = impl->fetch_resource(n->bg_image, "img-src");
            if (!bytes.empty()) {
                renderer::DecodedImage dec;
                if (renderer::decode_image_bytes(bytes, &dec) && dec.ok) {
                    img.w = dec.width; img.h = dec.height; img.ok = true;
                    img.px.resize(size_t(dec.width) * dec.height);
                    for (size_t i = 0; i < img.px.size(); ++i)
                        img.px[i] = {dec.rgba[i * 4], dec.rgba[i * 4 + 1],
                                     dec.rgba[i * 4 + 2], dec.rgba[i * 4 + 3]};
                }
            }
            if (wv_trace())
                std::cerr << "[WV-IMG] " << n->bg_image << " ok=" << img.ok
                          << " " << img.w << "x" << img.h << std::endl;
            it = impl->img_cache.emplace(n->bg_image, std::move(img)).first;
        }
        if (!it->second.ok) return;
        int cx = n->x + n->border_w + n->pad_l, cy2 = n->y + n->border_w + n->pad_t;
        int cw = n->w - 2 * n->border_w - n->pad_l - n->pad_r;
        int ch = n->h - 2 * n->border_w - n->pad_t - n->pad_b;
        if (cw <= 0 || ch <= 0) return;
        int dw = cw, dh = ch, ox = 0, oy = 0;
        if (n->bg_contain) {
            float sc = std::min(float(cw) / it->second.w, float(ch) / it->second.h);
            dw = std::max(1, int(it->second.w * sc));
            dh = std::max(1, int(it->second.h * sc));
            ox = (cw - dw) / 2; oy = (ch - dh) / 2;
        } else if (n->bg_size_pct > 0) {
            // single-value % law: width scales, height proportional (top-left)
            dw = std::max(1, int(float(cw) * n->bg_size_pct / 100.f));
            dh = std::max(1, int(dw * float(it->second.h) / float(it->second.w)));
        }
        const auto& src = it->second.px;
        int sw = it->second.w, sh2 = it->second.h;
        // S114: backgrounds CLIP to the padding box (CSS Backgrounds §3 —
        // background-repeat:no-repeat never spills outside the box)
        for (int yy = 0; yy < dh; ++yy) {
            int dy = cy2 + oy + yy;
            if (dy < cy2 || dy >= cy2 + ch) continue;
            int sy = int((yy + .5f) / dh * sh2);
            if (sy >= sh2) sy = sh2 - 1;
            for (int xx = 0; xx < dw; ++xx) {
                int dx = cx + ox + xx;
                if (dx < cx || dx >= cx + cw) continue;
                int sx = int((xx + .5f) / dw * sw);
                if (sx >= sw) sx = sw - 1;
                if (n->bg_mirror) sx = sw - 1 - sx;
                auto c = src[size_t(sy) * sw + sx];
                if (c.a == 0) continue;
                surface_fb->set_pixel(cx + ox + xx, cy2 + oy + yy, c);
            }
        }
    };
    // own merged text at the stored line position (align law, face law,
    // text-shadow law)
    // row height law: line-height (px > factor > legacy 1.6) — CSS 2.1 §10.8
    // S114 INLINE-FRAGMENT law (CSS 2.1 §10.3.1 inline box model): a merged
    // line paints as styled RUNS — each inline element contributes its glyphs
    // with ITS OWN effective color/font-size/face/bold. The flat merge lost
    // the `.scores span` green value ("Score: <span>0</span>" painted the 0
    // in the div's white at the div's size — every styled inline fragment in
    // every HTML5 app died this way). The concatenation of the runs equals
    // own_text_of(n) exactly (same traversal, same visibility rules), so the
    // layout-measured line_w stays the width anchor.
    struct TxtRun {
        std::string t; uint32_t fg; bool fg_valid;
        float size; bool bold; int face;
    };
    std::map<DomNode*, std::vector<TxtRun>> run_cache;
    std::function<void(DomNode*, DomNode*, std::vector<TxtRun>&)> gather_runs =
        [&](DomNode* elem, DomNode* c, std::vector<TxtRun>& out) {
        if (!c || c->eff_vis_hidden) return;
        if (c->tag == "#text") {
            TxtRun r;
            r.t = c->text;
            r.fg = elem->eff_fg; r.fg_valid = elem->eff_fg_valid;
            r.size = elem->eff_font_size; r.bold = elem->eff_bold;
            r.face = elem->eff_face >= 0 ? elem->eff_face : int(fonts::FACE_SYSTEM);
            out.push_back(std::move(r));
            return;
        }
        if (c->inline_el)
            for (auto& g : c->children) gather_runs(c, g.get(), out);
    };
    auto runs_of = [&](DomNode* n) -> const std::vector<TxtRun>& {
        auto it = run_cache.find(n);
        if (it != run_cache.end()) return it->second;
        std::vector<TxtRun> out;
        for (auto& c : n->children) gather_runs(n, c.get(), out);
        return run_cache.emplace(n, std::move(out)).first->second;
    };
    auto line_h_of = [&](DomNode* n) -> int {
        if (n->line_h_px > 0) return n->line_h_px;
        if (n->line_h_num > 0) return int(n->line_h_num * n->eff_font_size);
        return int(n->eff_font_size * 1.6f) + 4;
    };
    auto draw_text_of = [&](DomNode* n, int line_y, int line_w) {
        std::string t = own_text_of(n);
        if (wv_trace() && !t.empty())
            std::cerr << "[WV-DRAWTXT] tag=" << n->tag
                      << " t='" << t.substr(0, 24) << "' runs=" << runs_of(n).size()
                      << std::endl;
        if (t.empty()) return;
        auto& sh = fonts::TextShaper::instance();
        if (!sh.available()) return;
        float size = n->eff_font_size;
        int cw = n->w - 2 * n->border_w - n->pad_l - n->pad_r;
        float tx = float(n->x + n->border_w + n->pad_l);
        if (n->eff_align == 1)
            tx = float(n->x + n->border_w + n->pad_l) +
                 std::max(0.f, float(cw - line_w) / 2.f);
        else if (n->eff_align == 2)
            tx = float(n->x + n->w - n->border_w - n->pad_r - line_w);
        renderer::RGBA col{0, 0, 0, 255};
        if (n->eff_fg_valid)
            col = renderer::RGBA{uint8_t(n->eff_fg & 255),
                                 uint8_t((n->eff_fg >> 8) & 255),
                                 uint8_t((n->eff_fg >> 16) & 255),
                                 uint8_t((n->eff_fg >> 24) & 255)};
        int face = face_of(n);
        int lh = line_h_of(n);
        float baseline = n->line_h_px > 0 || n->line_h_num > 0
            ? float(line_y) + float(lh) * 0.5f + size * 0.36f   // line-box law
            : float(line_y) + size * 1.1f;                      // legacy baseline law
        // S114 gradient-text law: glyphs filled with the rule's gradient
        // (rendered white into a scratch buffer, then gradient-mapped)
        if (n->grad_text) {
            int tw = std::max(1, line_w), th = std::max(1, lh);
            renderer::FrameBuffer tmp(tw, th);
            tmp.clear(renderer::RGBA{0, 0, 0, 0});   // transparent base — the
            // ctor leaves raw memory (garbage alpha read as glyph pixels)
            renderer::RGBA white{255, 255, 255, 255};
            sh.draw(tmp, t, 0, baseline - float(line_y), size, white, n->eff_bold, face);
            renderer::RGBA c1{uint8_t(n->grad_from & 255), uint8_t((n->grad_from >> 8) & 255),
                              uint8_t((n->grad_from >> 16) & 255), 255};
            renderer::RGBA c2{uint8_t(n->grad_to & 255), uint8_t((n->grad_to >> 8) & 255),
                              uint8_t((n->grad_to >> 16) & 255), 255};
            const auto& tp = tmp.get_pixels();
            for (int yy = 0; yy < th; ++yy) {
                for (int xx = 0; xx < tw; ++xx) {
                    const auto& sc = tp[size_t(yy) * tw + xx];
                    if (sc.a == 0) continue;
                    float tgrad;
                    if (n->grad_dir == 2) tgrad = float(xx) / float(tw - 1);
                    else if (n->grad_dir == 3) tgrad = 1.f - float(xx) / float(tw - 1);
                    else if (n->grad_dir == 1) tgrad = 1.f - float(yy) / float(th - 1);
                    else tgrad = float(yy) / float(th - 1);
                    tgrad = std::max(0.f, std::min(1.f, tgrad));
                    renderer::RGBA gc{uint8_t(c1.r + (c2.r - c1.r) * tgrad),
                                      uint8_t(c1.g + (c2.g - c1.g) * tgrad),
                                      uint8_t(c1.b + (c2.b - c1.b) * tgrad), 255};
                    int dx = int(tx) + xx, dy = line_y + yy;
                    if (dx < 0 || dy < 0 || dx >= w || dy >= h) continue;
                    surface_fb->set_pixel(dx, dy, gc);
                }
            }
            return;
        }
        // S114 INLINE-FRAGMENT law: mixed-style lines paint run-by-run
        // (each run carries its own effective color/size/face/bold)
        {
            const auto& runs = runs_of(n);
            if (runs.size() > 1) {
                float cur = tx;
                for (const auto& r : runs) {
                    if (r.t.empty()) continue;
                    renderer::RGBA rcol = col;
                    if (r.fg_valid)
                        rcol = renderer::RGBA{uint8_t(r.fg & 255),
                                              uint8_t((r.fg >> 8) & 255),
                                              uint8_t((r.fg >> 16) & 255), 255};
                    if (n->text_shadow) {
                        renderer::RGBA shc{uint8_t(n->text_shadow_col & 255),
                                           uint8_t((n->text_shadow_col >> 8) & 255),
                                           uint8_t((n->text_shadow_col >> 16) & 255),
                                           uint8_t((n->text_shadow_col >> 24) & 255)};
                        sh.draw(*surface_fb, r.t, cur + 2, baseline + 2, r.size, shc,
                                r.bold, r.face);
                    }
                    sh.draw(*surface_fb, r.t, cur, baseline, r.size, rcol, r.bold, r.face);
                    cur += sh.shape(r.t, r.size, r.bold, r.face).width;
                }
                return;
            }
        }
        if (n->text_shadow) {
            renderer::RGBA shc{uint8_t(n->text_shadow_col & 255),
                               uint8_t((n->text_shadow_col >> 8) & 255),
                               uint8_t((n->text_shadow_col >> 16) & 255),
                               uint8_t((n->text_shadow_col >> 24) & 255)};
            sh.draw(*surface_fb, t, tx + 2, baseline + 2, size, shc, n->eff_bold, face);
        }
        sh.draw(*surface_fb, t, tx, baseline, size, col, n->eff_bold, face);
    };

    // 3. S114 LAYOUT CORE — the containing-block model (CSS 2.1 §10):
    // one positional law for every element. Flow (block + flex column/row)
    // records STATIC positions for out-of-flow children; the positioned pass
    // then places absolute/fixed boxes against their nearest positioned
    // ancestor (or the initial containing block), with margins, shrink-to-
    // fit and offset-computed sizes. No package checks anywhere.
    std::function<int(DomNode*, int)> measure_w;
    measure_w = [&](DomNode* n, int mw_depth) -> int {
        if (mw_depth > 400) return 0;
        int extra = n->border_box ? 0 : 2 * n->border_w + n->pad_l + n->pad_r;
        int cw2 = 0;
        std::string t = own_text_of(n);
        if (!t.empty()) {
            auto& sh = fonts::TextShaper::instance();
            if (sh.available())
                cw2 = std::max(cw2, int(sh.shape(t, n->eff_font_size, n->eff_bold,
                                                 face_of(n)).width));
        }
        for (auto& c : n->children) {
            if (c->tag == "#text") continue;
            if (c->display_none || c->positioned) continue;   // hidden keeps slot (visibility law)
            // S133: an atomic inline-block contributes its OUTER width to a
            // shrink-to-fit parent (CSS 2.1 §10.3.9)
            if (c->inline_block && !c->has_w && c->w_pct < 0 && c->w_raw.empty()) {
                cw2 = std::max(cw2, measure_w(c.get(), mw_depth + 1) +
                                        2 * c->border_w + c->pad_l + c->pad_r +
                                        (c->border_box ? 0 : 0));
                continue;
            }
            if (c->inline_el) continue;
            if (c->has_w)
                cw2 = std::max(cw2, c->w + (c->border_box ? 0 : 2 * c->border_w + c->pad_l + c->pad_r));
            else if (c->w_pct >= 0 || !c->w_raw.empty()) continue;
            else cw2 = std::max(cw2, measure_w(c.get(), mw_depth + 1));
        }
        return cw2 + extra;
    };
    // row height law moved above draw_text_of (shared by text paint + layout)

    // forward decls (flow ⇄ positioned mutual recursion)
    std::function<int(DomNode*, int, int, int, int, int)> layout_inflow;   // (n,x,y,w,avail_h,depth)
    struct CBBox { int x = 0, y = 0, w = 0, h = 0; };
    std::function<void(DomNode*, const CBBox&, int)> layout_positioned_tree;

    // cb length resolver — % against the CB box on the requested axis
    auto cb_len = [](const std::string& v, float vw_, float vh_, float cbw, float cbh,
                     float em_, float dflt, int axis) -> float {
        if (v.empty()) return dflt;
        CssCtx c;
        c.vw = vw_; c.vh = vh_; c.pctw = cbw; c.pcth = cbh; c.em = em_;
        return css_eval(v, c, dflt, axis);
    };
    auto outer_w_of = [&](DomNode* c) -> int {
        // explicit width → OUTER width (border-box folds pad+border, the
        // content-box law adds them — CSS 2.1 §10.3)
        if (!c->has_w) return -1;
        return c->border_box ? c->w : c->w + 2 * c->border_w + c->pad_l + c->pad_r;
    };

    // in-flow stack: one pass placing block/flex children (used directly and
    // by the 2-pass justify-center law)
    auto layout_stack_once = [&](DomNode* n, int content_x, int content_y,
                                 int content_w, int cy_shift, int avail_h,
                                 int depth, int& extent_out) -> int {
        // S118 justify axis law: the shift is along the MAIN axis — X for a
        // flex-row, Y for a column/block stack. The old code only shifted
        // cy, so a row with justify-content:center never centered (the
        // accelerace road strip stayed pinned at x=0).
        bool row_axis = n->flex && n->flex_row;
        int cy = content_y + (row_axis ? 0 : cy_shift);
        int cx = content_x + (row_axis ? cy_shift : 0);
        int row_main = 0;   // Σ member widths of THIS pass (nest-safe: a local,
                            // the old captured global was wiped by nested rows)
        std::vector<int> widths(n->children.size(), -1);
        std::vector<int> heights(n->children.size(), 0);
        // S114 merged-run law: ALL inline content of the node paints as ONE
        // line box (own_text_of — the exact string draw_text_of paints), so
        // the layout must measure and advance ONE row, not one per #text
        // node (h1's split "Bl"+span+"ck'Buster" was two phantom rows).
        bool text_row_done = false;
        for (size_t i = 0; i < n->children.size(); ++i) {
            DomNode* c = n->children[i].get();
            if (c->tag == "#text") {
                if (text_row_done || is_ws_text(c->text)) continue;
                std::string merged = own_text_of(n);
                if (merged.empty()) { text_row_done = true; continue; }
                int tw = 0;
                auto& sh = fonts::TextShaper::instance();
                if (sh.available())
                    tw = int(sh.shape(merged, n->eff_font_size, n->eff_bold,
                                      face_of(n)).width);
                widths[i] = tw;
                heights[i] = line_h_of(n);
                text_line[c] = {cy, tw};
                text_row_done = true;
                if (!n->flex_row) cy += heights[i];
                continue;
            }
            if (c->tag == "script" || c->tag == "style" || c->tag == "head" ||
                c->tag == "title" || c->tag == "link" || c->tag == "meta" ||
                c->tag == "audio")
                continue;
            if (n->tag == "svg") continue;   // S117: SVG shapes take no HTML slots
            if (c->display_none) continue;        // visibility:hidden keeps its slot
            if (c->inline_block && !c->positioned) {
                // S133 ATOMIC INLINE-BOX law (CSS 2.1 §9.2.2/§10.3.9): the
                // box keeps its slot in the inline run — shrink-to-fit when
                // no explicit width, wrap on the second sweep.
                int ow2 = outer_w_of(c);
                if (ow2 >= 0) widths[i] = ow2;
                else if (c->w_pct >= 0)
                    widths[i] = int(float(content_w) * c->w_pct / 100.f);
                else if (!c->w_raw.empty()) {
                    float pv = cb_len(c->w_raw, float(w), float(h),
                                      float(content_w),
                                      float(avail_h > 0 ? avail_h : content_w),
                                      c->font_size, -1.f, 0);
                    widths[i] = pv >= 0 ? int(pv)
                                        : std::min(measure_w(c, 0), content_w);
                } else {
                    widths[i] = std::min(measure_w(c, 0), content_w);
                }
                widths[i] = std::max(widths[i], 2 * c->border_w);
                c->static_x = content_x;
                c->static_y = cy;
                c->static_pos_recorded = true;
                continue;
            }
            if (c->inline_el) {
                widths[i] = -2;                    // merged into parent text
                // S114: inline subtrees may still CONTAIN positioned
                // descendants — record the flow origin so the auto-offset
                // fallback lands here, not at the viewport corner
                c->static_x = content_x;
                c->static_y = cy;
                c->static_pos_recorded = true;
                continue;
            }
            // STATIC POSITION RECORD — where this box would sit if it were
            // in-flow (CSS 2.1 §10.3.7: auto offsets use the static position)
            c->static_x = n->flex_row ? cx + c->mar_l : content_x;
            c->static_y = n->flex_row ? content_y : cy;
            c->static_pos_recorded = true;
            if (c->positioned) continue;          // out of flow — placed later vs the CB
            int extra = c->border_box ? 0 : 2 * c->border_w + c->pad_l + c->pad_r;
            int ow = outer_w_of(c);
            if (ow >= 0) widths[i] = ow;
            else if (c->w_pct >= 0) widths[i] = int(float(content_w) * c->w_pct / 100.f);
            else if (!c->w_raw.empty()) {
                // S118 invalid-at-computed-value-time law (CSS Custom
                // Properties §3.1): an undefined var() with no fallback
                // invalidates the declaration — the property computes to its
                // INITIAL value (width:auto → shrink-to-fit), never the
                // containing-block size. `width: calc(var(--ligth))` in the
                // accelerace stylesheet (an app typo) used to read as
                // full-width and dragged the row shrink law onto the road.
                float pv = cb_len(c->w_raw, float(w), float(h),
                                  float(content_w),
                                  float(avail_h > 0 ? avail_h : content_w),
                                  c->font_size, -1.f, 0);
                if (pv >= 0) widths[i] = int(pv);
                else widths[i] = std::min(measure_w(c, 0), content_w);
            }
            else if (n->flex && n->align_items == 1) {
                widths[i] = std::min(measure_w(c, 0), content_w);  // flex center shrink
                if (wv_trace())
                    std::cerr << "[WV-MEASURE] tag=" << c->tag
                              << " class=" << (c->attrs.count("class") ? c->attrs.at("class") : "")
                              << " mw=" << measure_w(c, 0) << " cw=" << content_w << std::endl;
            }
            else widths[i] = content_w;                         // block fill law
            if (c->max_w >= 0 && widths[i] > c->max_w) widths[i] = c->max_w;
            widths[i] = std::max(widths[i], 2 * c->border_w);
        }
        // S117 flex-shrink law (CSS Flexbox §7.2: flex-shrink defaults to
        // 1): when a flex ROW's members overflow the container, every
        // member scales down proportionally to its base size — the weather
        // nav (list + pages(filling) + add) pushed its last icon to x=1149,
        // off-viewport, without this law.
        if (n->flex && n->flex_row) {
            int total = 0;
            for (size_t i = 0; i < n->children.size(); ++i)
                if (widths[i] > 0)
                    total += widths[i] + n->children[i]->mar_l + n->children[i]->mar_r;
            if (total > content_w && total > 0) {
                float factor = float(content_w) / float(total);
                for (size_t i = 0; i < n->children.size(); ++i) {
                    DomNode* c = n->children[i].get();
                    if (widths[i] <= 0) continue;
                    int m = c->mar_l + c->mar_r;
                    int shr = int((widths[i] + m) * factor) - m;
                    widths[i] = std::max(1, std::min(widths[i], shr));
                }
            }
        }
        // flex-ROW cross-size pass: tallest child governs the line height
        int row_h = 0;
        if (n->flex && n->flex_row)
            for (size_t i = 0; i < n->children.size(); ++i)
                if (widths[i] >= 0 && heights[i] == 0) heights[i] = -1;  // element child marker
        // S133 inline-run cursors (atomic inline-block line state)
        int ib_x = content_x, ib_y = cy, ib_run_h = 0;
        for (size_t i = 0; i < n->children.size(); ++i) {
            DomNode* c = n->children[i].get();
            if (c->tag == "#text") {
                // S114 line-record law: the MEASURE pass already recorded the
                // merged row ({y,width}); re-recording here reused the
                // ADVANCED cy — every merged line painted one line-height too
                // low (the .scores labels landed inside the brick field and
                // multi-row stacks double-advanced). Placement owns ELEMENT
                // boxes only.
                continue;
            }
            if (widths[i] < 0) continue;
            // ── S133 ATOMIC INLINE-BOX RUN law (CSS 2.1 §9.2.2) ──────────
            // inline-block boxes flow HORIZONTALLY in the parent's line,
            // wrapping to the next line when the run exceeds the container
            // width (T02 color chips, T14's 2000-cell grid). The block
            // stack's cursor (cy) follows the deepest wrapped line.
            if (c->inline_block && !c->positioned && !n->flex) {
                int iw = widths[i] + c->mar_l + c->mar_r;
                if (ib_x > content_x && ib_x + iw > content_x + content_w) {
                    ib_x = content_x;              // wrap: new line at run start
                    ib_y += ib_run_h;              // advance by the line's height
                    ib_run_h = 0;
                }
                int hb = layout_inflow(c, ib_x + c->mar_l, ib_y, widths[i],
                                       avail_h, depth + 1);
                ib_x += iw;
                ib_run_h = std::max(ib_run_h, hb + c->mar_t + c->mar_b);
                cy = std::max(cy, ib_y + ib_run_h);
                continue;
            }
            int x;
            if (n->flex_row) x = cx + c->mar_l;
            else x = content_x + c->mar_l;
            if (!n->flex_row && (n->align_items == 1 || c->mar_lr_auto))
                x = content_x + std::max(0, content_w - widths[i]) / 2;
            int hb;
            if (heights[i] == -1) heights[i] = 0;   // marker consumed
            hb = layout_inflow(c, x, cy, widths[i], avail_h, depth + 1);
            if (n->flex_row) {
                // S118 flex cross-axis STRETCH law (CSS Flexbox §9.4.4 —
                // align-items defaults to stretch): a row member with an
                // auto height fills the container's DEFINITE cross size
                // (child_avail = fixed_inner). The road_sides strip in
                // accelerace (no height, stretching road) stayed 0px tall
                // and never painted without this.
                if (avail_h > 0 && !c->has_h && c->h_pct < 0 && c->h_raw.empty()) {
                    int target = avail_h - c->mar_t - c->mar_b;
                    if (c->h < target) { c->h = target; hb = target; }
                }
                row_h = std::max(row_h, hb + c->mar_t + c->mar_b);
                cx += widths[i] + c->mar_l + c->mar_r;
                heights[i] = hb;
                row_main += widths[i] + c->mar_l + c->mar_r;
            } else {
                cy += hb + c->mar_b;
                // S133: a block sibling ends the inline run — the next
                // inline-block line starts BELOW the placed block
                ib_x = content_x; ib_y = cy; ib_run_h = 0;
            }
        }
        // second sweep for flex-row vertical centering (2-pass shift law)
        if (n->flex && n->flex_row && n->align_items == 1 && row_h > 0) {
            cx = content_x;
            for (size_t i = 0; i < n->children.size(); ++i) {
                DomNode* c = n->children[i].get();
                if (c->tag == "#text" || widths[i] < 0) {
                    if (c->tag == "#text" && !is_ws_text(c->text) && widths[i] >= 0) cx += widths[i];
                    continue;
                }
                if (c->positioned || c->display_none || c->inline_el) continue;
                int hb = heights[i];
                int dy = std::max(0, (row_h - (hb + c->mar_t + c->mar_b)) / 2);
                layout_inflow(c, cx + c->mar_l, content_y + dy, widths[i], avail_h, depth + 1);
                cx += widths[i] + c->mar_l + c->mar_r;
            }
        }
        if (n->flex && n->flex_row) { extent_out = row_main; return row_h; }
        extent_out = 0;
        return cy - content_y - cy_shift;
    };

    // in-flow layout: places n at (x,y) with outer width w_in, lays out its
    // in-flow children, applies height % and the relative-offset shift.
    layout_inflow = [&](DomNode* n, int x, int y, int w_in, int avail_h, int depth) -> int {
        if (depth > 400) {
            if (wv_trace())
                std::cerr << "[WV-DEPTH] layout_inflow overflow tag=" << n->tag
                          << " class=" << (n->attrs.count("class") ? n->attrs.at("class") : "") << std::endl;
            n->laid_out = true;
            return 0;
        }
        // relative offset shift (CSS 2.1 §9.4.3): the flow slot stays, the
        // box moves by left/top (or negative right/bottom)
        if (n->pos_mode == 1 && n->parent) {
            DomNode* cbn = nullptr;
            for (DomNode* p = n->parent; p; p = p->parent)
                if (p->pos_mode != 0 && p->laid_out) { cbn = p; break; }
            float cbw = cbn ? float(cbn->w) : float(w);
            float cbh = cbn ? float(cbn->h) : float(h);
            int dx = 0, dy = 0;
            if (!n->off_l.empty()) dx = int(cb_len(n->off_l, float(w), float(h), cbw, cbh, n->font_size, 0, 0));
            else if (!n->off_r.empty()) dx = -int(cb_len(n->off_r, float(w), float(h), cbw, cbh, n->font_size, 0, 0));
            if (!n->off_t.empty()) dy = int(cb_len(n->off_t, float(w), float(h), cbw, cbh, n->font_size, 0, 1));
            else if (!n->off_b.empty()) dy = -int(cb_len(n->off_b, float(w), float(h), cbw, cbh, n->font_size, 0, 1));
            x += dx; y += dy;
        }
        n->x = x; n->y = y; n->w = w_in; n->laid_out = true;
        if (n->tag == "svg") {
            // S117 SVG leaf-box law: an <svg> is a replaced element — its
            // shapes take no HTML layout slots; the box is CSS/attr-sized
            // (has_h path below stays authoritative), else viewBox aspect ×
            // width, else an icon square (capped). A definitions-only svg
            // (all <symbol>/<defs>) is zero-height — symbols render at their
            // <use> site, never in place (SVG2 §5.6).
            bool only_defs = true;
            for (auto& cc : n->children)
                if (cc->tag != "symbol" && cc->tag != "defs" && cc->tag != "#text") {
                    only_defs = false; break;
                }
            if (!n->has_h) {
                if (n->h_pct >= 0 && avail_h > 0) {
                    n->h = int(float(avail_h) * n->h_pct / 100.f);   // CSS 100% law
                } else if (!n->h_raw.empty() && avail_h > 0) {
                    float pv = cb_len(n->h_raw, float(w), float(h), float(w_in),
                                      float(avail_h), n->font_size, -1, 1);
                    if (pv >= 0) n->h = int(pv);
                } else {
                    float vx, vy, vw2, vh2;
                    if (only_defs) n->h = 0;
                    else if (svg_viewbox(n, vx, vy, vw2, vh2) && n->w > 0)
                        n->h = int(float(n->w) * vh2 / vw2 + 0.5f);
                    else
                        n->h = std::min(n->w, 128);
                }
                if (n->h > 4096) n->h = 4096;
            }
            return n->h;
        }
        if (wv_trace())
            std::cerr << "[WV-BOX] tag=" << n->tag
                      << " class=" << (n->attrs.count("class") ? n->attrs.at("class") : "")
                      << " box=" << x << "," << y << " " << w_in << "x" << n->h
                      << " pos=" << n->pos_mode << " flex=" << n->flex
                      << " row=" << n->flex_row << " ai=" << n->align_items
                      << " fs=" << n->eff_font_size << std::endl;
        // height % (border-box folds pad+border)
        if (!n->has_h && n->h_pct >= 0 && avail_h > 0) {
            n->h = int(float(avail_h) * n->h_pct / 100.f);
            if (!n->border_box) n->h += 2 * n->border_w + n->pad_t + n->pad_b;
            if (n->h_raw.empty()) n->has_h = true;
        }
        // calc/%-bearing height strings for FLOW boxes resolve against the
        // available height (else auto)
        if (!n->has_h && !n->h_raw.empty() && avail_h > 0) {
            float pv = cb_len(n->h_raw, float(w), float(h), float(w_in),
                              float(avail_h), n->font_size, -1, 1);
            if (pv >= 0) {
                n->h = int(pv);
                if (!n->border_box) n->h += 2 * n->border_w + n->pad_t + n->pad_b;
                n->has_h = true;
            }
        }
        int content_w = w_in - (n->border_box ? 0 : 0) - 2 * n->border_w - n->pad_l - n->pad_r;
        if (content_w < 0) content_w = 0;
        int fixed_inner = -1;
        if (n->has_h) fixed_inner = n->h - 2 * n->border_w - n->pad_t - n->pad_b;
        int child_avail = fixed_inner > 0 ? fixed_inner : 0;
        int justify_extent = 0;
        int used = layout_stack_once(n, x + n->border_w + n->pad_l,
                                     y + n->border_w + n->pad_t, content_w, 0, child_avail, depth,
                                     justify_extent);
        if (n->flex && n->justify_content == 1) {
            if (n->flex_row) {
                // S118 main-axis (X) centering law: shift = (content width −
                // Σ member widths)/2. The old branch compared the CROSS
                // extent against the container height and shifted Y — both
                // wrong-axis (accelerace road_sides pinned at x=0, y=9600).
                if (wv_trace())
                    std::cerr << "[WV-JUSTIFY] row tag=" << n->tag
                              << " class=" << (n->attrs.count("class") ? n->attrs.at("class") : "")
                              << " extent=" << justify_extent
                              << " content_w=" << content_w << std::endl;
                if (justify_extent > 0 && justify_extent < content_w) {
                    int shift = (content_w - justify_extent) / 2;
                    layout_stack_once(n, x + n->border_w + n->pad_l,
                                      y + n->border_w + n->pad_t, content_w, shift, child_avail, depth,
                                      justify_extent);
                }
            } else if (fixed_inner > 0 && used < fixed_inner) {
                int shift = (fixed_inner - used) / 2;
                layout_stack_once(n, x + n->border_w + n->pad_l,
                                  y + n->border_w + n->pad_t, content_w, shift, child_avail, depth,
                                  justify_extent);
                used = fixed_inner;
            }
        }
        // leaf min-height law (legacy flow parity for leaf rows)
        if (!n->has_h && n->h_pct < 0) {
            bool leaf = true;
            for (auto& c : n->children)
                if (c->tag != "#text" && !c->inline_el) { leaf = false; break; }
            if (leaf) {
                int min_h = line_h_of(n);
                if (used < min_h) used = min_h;
            }
        }
        if (!n->has_h)
            n->h = used + 2 * n->border_w + n->pad_t + n->pad_b;
        return n->h;
    };

    // positioned placement: absolute/fixed against the containing block
    layout_positioned_tree = [&](DomNode* n, const CBBox& cb_in, int depth) {
        if (depth > 400) {
            if (wv_trace())
                std::cerr << "[WV-DEPTH] pos_tree overflow tag=" << n->tag << std::endl;
            return;
        }
        for (auto& cc : n->children) {
            DomNode* c = cc.get();
            if (c->tag == "script" || c->tag == "style" || c->tag == "head" ||
                c->tag == "title" || c->tag == "link" || c->tag == "meta") continue;
            if (c->display_none) continue;
            if (c->pos_mode >= 2) {
                // fixed → the ICB, absolute → the passed CB (CSS 2.1 §10.1)
                CBBox box = c->pos_mode == 3 ? CBBox{0, 0, w, h} : cb_in;
                // S114: offsets are OPTIONAL booleans + values — negative
                // lengths are legal (`bottom:-40%` pins BELOW the box), so
                // the old `>= 0` sentinel misread them as unspecified
                bool hl = !c->off_l.empty(), ht = !c->off_t.empty();
                bool hr = !c->off_r.empty(), hb2 = !c->off_b.empty();
                float l = hl ? cb_len(c->off_l, float(w), float(h), float(box.w), float(box.h), c->font_size, 0, 0) : 0.f;
                float t = ht ? cb_len(c->off_t, float(w), float(h), float(box.w), float(box.h), c->font_size, 0, 1) : 0.f;
                float r_ = hr ? cb_len(c->off_r, float(w), float(h), float(box.w), float(box.h), c->font_size, 0, 0) : 0.f;
                float b_ = hb2 ? cb_len(c->off_b, float(w), float(h), float(box.w), float(box.h), c->font_size, 0, 1) : 0.f;
                // ── width (§10.3.7 ladder) ──
                int ow = outer_w_of(c);
                if (ow < 0 && c->w_pct >= 0) ow = int(float(box.w) * c->w_pct / 100.f);
                if (ow < 0 && !c->w_raw.empty())
                    ow = int(cb_len(c->w_raw, float(w), float(h), float(box.w), float(box.h),
                                    c->font_size, -1, 0));
                if (ow < 0 && hl && hr)
                    ow = int(float(box.w) - l - r_ - float(c->mar_l + c->mar_r));
                int avail_w = int(float(box.w) - std::max(0.f, l) - std::max(0.f, r_)
                                 - float(c->mar_l + c->mar_r));
                if (ow < 0 && c->tag == "svg") {
                    // S118 SVG intrinsic-ratio law (SVG2 §7.2 replaced
                    // element sizing): an <svg> with an auto width and a
                    // definite height takes width = height × viewBox ratio
                    // (else the box square). Zero-width svg boxes broke every
                    // getBoundingClientRect() measure of inline icons
                    // (accelerace car placement computed NaN/garbage).
                    float vx, vy, vw2, vh2;
                    bool only_defs2 = true;
                    for (auto& cc2 : c->children)
                        if (cc2->tag != "symbol" && cc2->tag != "defs" && cc2->tag != "#text") {
                            only_defs2 = false; break;
                        }
                    int rh = c->has_h ? c->h
                           : (c->h_pct >= 0 ? int(float(box.h) * c->h_pct / 100.f) : -1);
                    if (!only_defs2 && rh > 0) {
                        if (svg_viewbox(c, vx, vy, vw2, vh2))
                            ow = std::max(1, int(float(rh) * vw2 / vh2 + 0.5f));
                        else
                            ow = rh;
                    }
                }
                if (ow < 0) ow = std::min(measure_w(c, 0), std::max(0, avail_w));
                if (c->max_w >= 0 && ow > c->max_w) ow = c->max_w;
                ow = std::max(ow, 2 * c->border_w);
                // ── height ──
                int oh = -1;
                if (c->has_h) oh = c->border_box ? c->h : c->h + 2 * c->border_w + c->pad_t + c->pad_b;
                else if (c->h_pct >= 0) oh = int(float(box.h) * c->h_pct / 100.f);
                else if (!c->h_raw.empty())
                    oh = int(cb_len(c->h_raw, float(w), float(h), float(box.w), float(box.h),
                                    c->font_size, -1, 1));
                if (oh < 0 && ht && hb2) oh = int(float(box.h) - t - b_ - float(c->mar_t + c->mar_b));
                // ── placement (auto offsets → the static position) ──
                // S114 static-origin law: a node never placed in flow (the
                // inline-subtree span — `.sound_label span` etc.) has NO
                // static slot; (0,0) would pin its pseudo content to the
                // viewport corner (it overpainted the score row). Fall back
                // to the nearest laid-out ancestor's CONTENT origin.
                auto static_origin = [&](DomNode* d) -> std::pair<int, int> {
                    for (DomNode* p = d->parent; p; p = p->parent)
                        if (p->laid_out)
                            return {p->x + p->border_w + p->pad_l,
                                    p->y + p->border_w + p->pad_t};
                    return {0, 0};
                };
                int x2, y2;
                if (hl) x2 = box.x + int(l) + c->mar_l;
                else if (hr) x2 = box.x + box.w - int(r_) - c->mar_r - ow;
                else if (c->static_pos_recorded) x2 = c->static_x + c->mar_l;
                else x2 = static_origin(c).first + c->mar_l;
                if (ht) y2 = box.y + int(t) + c->mar_t;
                else if (hb2 && oh >= 0) y2 = box.y + box.h - int(b_) - c->mar_b - oh;
                else if (c->static_pos_recorded) y2 = c->static_y + c->mar_t;
                else y2 = static_origin(c).second + c->mar_t;
                // provisional height for auto boxes; layout_inflow refines it
                if (oh >= 0) { c->h = oh; c->has_h = true; }
                layout_inflow(c, x2, y2, ow, box.h, depth + 1);
                // bottom-offset law: height was auto → anchor via the measured h
                if (!ht && hb2 && c->pos_mode != 3)
                    layout_inflow(c, x2, box.y + box.h - int(b_) - c->mar_b - c->h, ow, box.h, depth + 1);
                // recurse: this box is the CB for ITS positioned descendants
                CBBox inner;
                inner.x = c->x + c->border_w + c->pad_l;
                inner.y = c->y + c->border_w + c->pad_t;
                inner.w = c->w - 2 * c->border_w - c->pad_l - c->pad_r;
                inner.h = c->h - 2 * c->border_w - c->pad_t - c->pad_b;
                if (inner.w < 0) inner.w = 0;
                if (inner.h < 0) inner.h = 0;
                layout_positioned_tree(c, inner, depth + 1);
            } else {
                // in-flow child — its own box becomes the CB when positioned-
                // relative; otherwise pass the CB through unchanged
                CBBox pass = cb_in;
                if (c->pos_mode == 1 && c->laid_out) {
                    pass.x = c->x + c->border_w + c->pad_l;
                    pass.y = c->y + c->border_w + c->pad_t;
                    pass.w = c->w - 2 * c->border_w - c->pad_l - c->pad_r;
                    pass.h = c->h - 2 * c->border_w - c->pad_t - c->pad_b;
                    if (pass.w < 0) pass.w = 0;
                    if (pass.h < 0) pass.h = 0;
                } else if (c->pos_mode == 1 && c->inline_el && c->parent) {
                    // S114 INLINE containing-block law (CSS 2.1 §10.1): a
                    // position:relative INLINE element is the containing
                    // block for its positioned descendants — its box is the
                    // glyph run it owns inside the parent's line box (the
                    // Block'Buster icon pins to the "o" span, not to the h1).
                    DomNode* p = c->parent;
                    // the parent's recorded text line (first #text entry)
                    int line_y = -1, line_w2 = 0;
                    for (auto& g : p->children) {
                        if (g->tag != "#text") continue;
                        auto it2 = text_line.find(g.get());
                        if (it2 != text_line.end()) {
                            line_y = it2->second.first;
                            line_w2 = it2->second.second;
                            break;
                        }
                    }
                    if (line_y >= 0) {
                        // split the merged run: text BEFORE c + c's own text
                        std::string before, own;
                        bool in_c = false;
                        std::function<void(DomNode*, std::string&)> collect =
                            [&](DomNode* g, std::string& out) {
                            if (g->eff_vis_hidden) return;
                            if (g->tag == "#text") { out += g->text; return; }
                            if (g->inline_el)
                                for (auto& gg : g->children) collect(gg.get(), out);
                        };
                        for (auto& g : p->children) {
                            if (g.get() == c) { in_c = true; continue; }
                            collect(g.get(), in_c ? own : before);
                        }
                        auto& sh = fonts::TextShaper::instance();
                        float prefix_w = 0, own_w = float(std::max(8, line_h_of(p) / 2));
                        if (sh.available()) {
                            if (!before.empty())
                                prefix_w = float(sh.shape(before, p->eff_font_size,
                                                          p->eff_bold, face_of(p)).width);
                            if (!own.empty())
                                own_w = float(sh.shape(own, p->eff_font_size,
                                                       p->eff_bold, face_of(p)).width);
                        }
                        // drawn-origin law (mirrors draw_text_of centering)
                        int cw2 = p->w - 2 * p->border_w - p->pad_l - p->pad_r;
                        float tx = float(p->x + p->border_w + p->pad_l);
                        if (p->eff_align == 1)
                            tx += std::max(0.f, float(cw2 - line_w2) / 2.f);
                        else if (p->eff_align == 2)
                            tx += float(cw2 - line_w2);
                        pass.x = int(tx + prefix_w);
                        pass.y = line_y;
                        pass.w = std::max(1, int(own_w));
                        pass.h = line_h_of(p);
                    }
                }
                layout_positioned_tree(c, pass, depth + 1);
            }
        }
    };

    // flow root: the body fills the ICB width; height % chains start there
    DomNode* body_n = impl->body();
    layout_inflow(body_n, 0, 0, w, h, 1);
    // body (position:relative per UA resets) is the first containing block
    CBBox body_cb;
    body_cb.x = body_n->x + body_n->border_w + body_n->pad_l;
    body_cb.y = body_n->y + body_n->border_w + body_n->pad_t;
    body_cb.w = body_n->w - 2 * body_n->border_w - body_n->pad_l - body_n->pad_r;
    body_cb.h = body_n->h - 2 * body_n->border_w - body_n->pad_t - body_n->pad_b;
    if (body_cb.w < 0) body_cb.w = 0;
    if (body_cb.h < 0) body_cb.h = 0;
    layout_positioned_tree(body_n, body_cb, 1);

    // S118 trace: positioned box dump (WV_TRACE=1) — absolute/relative
    // layout is the top diagnostic blind spot for positioned scene games
    if (wv_trace()) {
        std::function<void(DomNode*)> dump_pos = [&](DomNode* n) {
            if (true)
                std::cerr << "[WV-LAYOUT] tag=" << n->tag
                          << (n->attrs.count("class") ? (" ." + n->attrs.at("class")) : "")
                          << (n->attrs.count("id") ? (" #" + n->attrs.at("id")) : "")
                          << (n->display_none ? " DISPLAY:NONE" : "")
                          << " box=" << n->x << "," << n->y << " " << n->w << "x" << n->h
                          << " pos=" << (n->positioned ? (n->style.count("position") ? n->style.at("position") : "?") : (n->style.count("position") ? n->style.at("position") : "static"))
                          << " z=" << n->z_index << (n->z_given ? "g" : "")
                          << " pm=" << n->pos_mode << " lo=" << n->laid_out << " vis=" << n->visible
                          << std::endl;
            for (auto& c : n->children) dump_pos(c.get());
        };
        dump_pos(body_n);
    }


    // ── S117 inline-SVG paint law ───────────────────────────────────────
    // property resolution: style (CSS wins) → presentational attribute →
    // inherited (fill/stroke/stroke-width inherit down the tree) → default.
    auto svg_prop_of = [&](DomNode* c, const char* prop) -> std::string {
        auto st = c->style.find(prop);
        if (st != c->style.end()) return st->second;
        auto at = c->attrs.find(prop);
        if (at != c->attrs.end()) return at->second;
        for (DomNode* p = c->parent; p; p = p->parent) {
            auto st2 = p->style.find(prop);
            if (st2 != p->style.end()) return st2->second;
            auto at2 = p->attrs.find(prop);
            if (at2 != p->attrs.end()) return at2->second;
        }
        return "";
    };
    std::function<void(DomNode*, float, float, float, float, float, float,
                       int, int, int, int)> paint_svg_content;
    paint_svg_content = [&](DomNode* n, float A, float B, float C, float D,
                            float E, float F, int bx, int by, int bw, int bh) {
        for (auto& chp : n->children) {
            DomNode* c = chp.get();
            if (c->tag == "symbol" || c->tag == "defs") continue; // use-site only
            // ── S133 SVG2 BASIC-SHAPES law (§10.3/§10.4) ────────────────
            // rect/circle/ellipse paint through the SAME path raster as
            // <path>: synthesize equivalent path data (zero new raster
            // code). Measured: the fixture page's <circle>/<rect> (and any
            // icon set using basic shapes) painted nothing before.
            std::string shape_d;
            if (c->tag == "rect" || c->tag == "circle" || c->tag == "ellipse") {
                auto num = [&](const char* k) -> float {
                    auto it = c->attrs.find(k);
                    return it == c->attrs.end()
                               ? 0.f
                               : strtof(it->second.c_str(), nullptr);
                };
                char buf[64];
                if (c->tag == "rect") {
                    float x = num("x"), y = num("y");
                    float w2 = num("width"), h2 = num("height");
                    if (w2 <= 0 || h2 <= 0) continue;
                    snprintf(buf, sizeof buf, "M %g %g H %g V %g H %g Z",
                             x, y, x + w2, y + h2, x);
                    shape_d = buf;
                } else {
                    float cx2 = num("cx"), cy2 = num("cy");
                    float rx = c->tag == "circle" ? num("r") : num("rx");
                    float ry = c->tag == "circle" ? num("r") : num("ry");
                    if (rx <= 0 || ry <= 0) continue;
                    const int SEG = 48;
                    for (int k2 = 0; k2 <= SEG; ++k2) {
                        float th = float(k2) / SEG * 2.f * float(M_PI);
                        snprintf(buf, sizeof buf, "%s %g %g",
                                 k2 == 0 ? "M" : "L",
                                 cx2 + rx * cosf(th), cy2 + ry * sinf(th));
                        shape_d += buf;
                    }
                    shape_d += " Z";
                }
            }
            if (c->tag == "path" || !shape_d.empty()) {
                std::string dstr;
                if (c->tag == "path") {
                    auto dit = c->attrs.find("d");
                    if (dit == c->attrs.end() || dit->second.empty()) continue;
                    dstr = dit->second;
                } else {
                    dstr = shape_d;
                }
                auto subs = svg_flatten(dstr, A, B, C, D, E, F);
                // fill (SVG default fill = black; fill:none skips)
                std::string f = svg_prop_of(c, "fill");
                if (f.empty()) f = "#000";
                // S118 trace: which paint properties each path resolved —
                // inline-SVG styling gaps are invisible otherwise
                if (wv_trace())
                    std::cerr << "[WV-SVG-PATH] fill='" << f << "' stroke='"
                              << svg_prop_of(c, "stroke") << "' dlen=" << dstr.size()
                              << std::endl;
                if (f != "none" && f != "transparent") {
                    bool okc = false;
                    uint32_t col = parse_css_color(f, okc);
                    if (!okc) col = 0;
                    svg_fill_paths(surface_fb, w, h, subs,
                                   renderer::RGBA{uint8_t(col & 255),
                                                  uint8_t((col >> 8) & 255),
                                                  uint8_t((col >> 16) & 255), 255});
                }
                // stroke (SVG default = none; width default 1 user unit)
                std::string stv = svg_prop_of(c, "stroke");
                if (!stv.empty() && stv != "none" && stv != "transparent") {
                    bool okc = false;
                    uint32_t col = parse_css_color(stv, okc);
                    if (!okc) col = 0;
                    float swu = 1.f;
                    std::string sww = svg_prop_of(c, "stroke-width");
                    if (!sww.empty()) {
                        // S118 SVG length law: stroke-width computes through
                        // the CSS length evaluator (px/vw/vh/calc/max) —
                        // the raw string read 0 through strtof and every
                        // stroked icon painted hairline-thin.
                        CssCtx scx;
                        scx.vw = float(w); scx.vh = float(h);
                        scx.pctw = float(bw > 0 ? bw : 1);
                        scx.pcth = float(bh > 0 ? bh : 1);
                        scx.em = c->eff_font_size > 0 ? c->eff_font_size : 28.f;
                        float r2 = css_eval(sww, scx, -1.f, 0);
                        swu = r2 > 0 ? r2 : std::max(0.05f, strtof(sww.c_str(), nullptr));
                        if (wv_trace())
                            std::cerr << "[WV-SVG-SW] raw='" << sww << "' -> " << swu
                                      << " user units (scale " << sqrtf(fabsf(A * D - B * C))
                                      << ") subs=" << subs.size()
                                      << " pts=" << (subs.empty() ? 0 : int(subs[0].size())) << std::endl;
                    }
                    float scale = sqrtf(fabsf(A * D - B * C));
                    svg_stroke_paths(surface_fb, w, h, subs,
                                     renderer::RGBA{uint8_t(col & 255),
                                                    uint8_t((col >> 8) & 255),
                                                    uint8_t((col >> 16) & 255), 255},
                                     std::max(1.f, swu * scale));
                }
            } else if (c->tag == "use") {
                std::string href;
                auto h1 = c->attrs.find("xlink:href");
                auto h2 = c->attrs.find("href");
                if (h1 != c->attrs.end()) href = h1->second;
                else if (h2 != c->attrs.end()) href = h2->second;
                if (href.size() < 2 || href[0] != '#') continue;
                DomNode* tgt = find_by_id(impl->doc.root.get(), href.substr(1));
                if (!tgt) continue;
                if (tgt->tag == "symbol") {
                    float vx, vy, vw2, vh2;
                    int uw = bw > 0 ? bw : 48, uh = bh > 0 ? bh : 48;
                    if (svg_viewbox(tgt, vx, vy, vw2, vh2) && uw > 0 && uh > 0) {
                        float s = std::min(float(uw) / vw2, float(uh) / vh2);
                        paint_svg_content(tgt, s, 0, 0, s,
                                          float(bx) + (uw - vw2 * s) / 2.f - vx * s,
                                          float(by) + (uh - vh2 * s) / 2.f - vy * s,
                                          bx, by, uw, uh);
                    } else {
                        paint_svg_content(tgt, 1, 0, 0, 1, float(bx), float(by),
                                          bx, by, uw, uh);
                    }
                } else {
                    paint_svg_content(tgt, A, B, C, D, E, F, bx, by, bw, bh);
                }
            } else if (c->tag == "g" || c->tag == "svg") {
                if (c->tag == "svg") {
                    float vx, vy, vw2, vh2;
                    if (svg_viewbox(c, vx, vy, vw2, vh2) && c->w > 0 && c->h > 0) {
                        float s = std::min(float(c->w) / vw2, float(c->h) / vh2);
                        paint_svg_content(c, s, 0, 0, s,
                                          float(c->x) + (c->w - vw2 * s) / 2.f - vx * s,
                                          float(c->y) + (c->h - vh2 * s) / 2.f - vy * s,
                                          c->x, c->y, c->w, c->h);
                        continue;
                    }
                }
                paint_svg_content(c, A, B, C, D, E, F, bx, by, bw, bh);
            }
        }
    };
    auto paint_svg_node = [&](DomNode* n) {
        int bw = n->w - 2 * n->border_w - n->pad_l - n->pad_r;
        int bh = n->h - 2 * n->border_w - n->pad_t - n->pad_b;
        int bx = n->x + n->border_w + n->pad_l;
        int by = n->y + n->border_w + n->pad_t;
        if (wv_trace())
            std::cerr << "[WV-SVG] box=" << bx << "," << by << " " << bw << "x" << bh
                      << " kids=" << n->children.size() << std::endl;
        if (bw <= 0 || bh <= 0) return;
        float vx, vy, vw2, vh2;
        if (svg_viewbox(n, vx, vy, vw2, vh2)) {
            float s = std::min(float(bw) / vw2, float(bh) / vh2);
            paint_svg_content(n, s, 0, 0, s,
                              float(bx) + (bw - vw2 * s) / 2.f - vx * s,
                              float(by) + (bh - vh2 * s) / 2.f - vy * s,
                              bx, by, bw, bh);
        } else {
            paint_svg_content(n, 1, 0, 0, 1, float(bx), float(by), bx, by, bw, bh);
        }
    };

    // 4. paint — flow (document order), then positioned (z ascending).
    // S114: visibility chain (own hidden node skips its OWN box but children
    // may override back to visible — CSS 2.1 §11.1.2); box-shadow spread law.
    std::function<void(DomNode*)> paint_node = [&](DomNode* n) {
        if (n->display_none || !n->laid_out) return;
        if (n->tag == "script" || n->tag == "style" || n->tag == "head" ||
            n->tag == "title" || n->tag == "link" || n->tag == "meta") return;
        if (!n->eff_vis_hidden) {
            if (n->box_shadow) {
                // proper shadow: offset + spread + color (the 150vw dim
                // overlay idiom paints the whole-viewport dimmer)
                if (n->sh_col_valid &&
                    (n->sh_ox || n->sh_oy || n->sh_blur || n->sh_spread)) {
                    uint8_t a = uint8_t((n->sh_col >> 24) & 255);
                    renderer::RGBA scol{uint8_t(n->sh_col & 255),
                                        uint8_t((n->sh_col >> 8) & 255),
                                        uint8_t((n->sh_col >> 16) & 255), a};
                    int sx = n->x + n->sh_ox - n->sh_spread;
                    int sy = n->y + n->sh_oy - n->sh_spread;
                    int sw2 = n->w + 2 * n->sh_spread;
                    int sh2 = n->h + 2 * n->sh_spread;
                    int rad = n->radius + n->sh_spread;
                    // S118 blur-falloff law (CSS Backgrounds §6.1): the
                    // shadow edge fades from full alpha to transparent
                    // across the blur radius. The old paint ignored the
                    // blur and filled the spread rect SOLID — every glow
                    // (accelerace street lights) rendered as an opaque slab.
                    if (n->sh_blur > 0) {
                        // S118 Gaussian-ish falloff law (CSS Backgrounds §6.1):
                        // alpha ≈ 1 well inside the shape, ≈ 0.5 AT the shape
                        // edge, → 0 across the blur radius outside. Painted
                        // outside-in so the inner (more opaque) bands win.
                        int B = std::min(int(n->sh_blur), 512);
                        const int STEPS = 16;
                        for (int k = STEPS; k >= 0; --k) {
                            float d = (float(k) / STEPS) * B - B / 2.f;
                            float t = d / (B / 2.f);
                            float g = std::exp(-2.f * t * t);
                            uint8_t ba = uint8_t(a * g);
                            if (!ba) continue;
                            int infl = int(d);
                            fill_round(sx - infl, sy - infl, sw2 + 2 * infl,
                                       sh2 + 2 * infl, std::max(0, rad + infl),
                                       renderer::RGBA{scol.r, scol.g, scol.b, ba});
                        }
                    } else {
                        fill_round(sx, sy, sw2, sh2, rad, scol);
                    }
                } else {
                    // legacy +6 soft shadow (shadow with no parseable parts)
                    fill_round(n->x, n->y + 6, n->w, n->h, n->radius + 4,
                               renderer::RGBA{0, 0, 0, 36});
                }
            }
            if (n->grad)
                fill_round_grad(n->x, n->y, n->w, n->h, n->radius, n->grad_diag,
                                n->grad_from, n->grad_to, n->grad_dir);
            else if (n->has_bg) {
                renderer::RGBA c{uint8_t(n->bg & 255), uint8_t((n->bg >> 8) & 255),
                                 uint8_t((n->bg >> 16) & 255), uint8_t(n->bg_alpha)};
                fill_round(n->x, n->y, n->w, n->h, n->radius, c);
            }
            if (!n->bg_image.empty()) draw_bg_image(n);
            if (n->has_border) {
                renderer::RGBA bc{uint8_t(n->border_col & 255),
                                  uint8_t((n->border_col >> 8) & 255),
                                  uint8_t((n->border_col >> 16) & 255), 255};
                stroke_round_ring(n->x, n->y, n->w, n->h, n->radius, n->border_w, bc);
            }
            if (n->tag == "svg") {
                paint_svg_node(n);          // S117 inline-SVG paint law
            } else if (n->tag == "img" && n->w > 0 && n->h > 0) {
                // ── S133 REPLACED-IMAGE paint law ───────────────────────
                // src → fetch_resource (network OR asset, one resource
                // table) → decode (decode_image_bytes) → blit scaled into
                // the box (drawImage semantics; the same scaling law the
                // canvas blit uses). Missing/broken source = honest empty
                // box (no fabricated pixels).
                auto it2 = impl->img_cache.find(n->attrs.count("src")
                                                    ? n->attrs["src"]
                                                    : std::string());
                if (it2 == impl->img_cache.end()) {
                    auto sit = n->attrs.find("src");
                    if (sit != n->attrs.end()) {
                        auto bytes = impl->fetch_resource(sit->second, "img-src");
                        WebViewEngine::Impl::CachedImg img;
                        if (!bytes.empty()) {
                            renderer::DecodedImage dec;
                            if (renderer::decode_image_bytes(bytes, &dec) && dec.ok) {
                                img.w = dec.width; img.h = dec.height; img.ok = true;
                                img.px.resize(size_t(dec.width) * dec.height);
                                for (size_t pi = 0; pi < img.px.size(); ++pi)
                                    img.px[pi] = {dec.rgba[pi * 4], dec.rgba[pi * 4 + 1],
                                                  dec.rgba[pi * 4 + 2], dec.rgba[pi * 4 + 3]};
                            }
                        }
                        it2 = impl->img_cache.emplace(sit->second, std::move(img)).first;
                    }
                }
                if (it2 != impl->img_cache.end() && it2->second.ok &&
                    it2->second.w > 0 && it2->second.h > 0) {
                    int sw = it2->second.w, shh = it2->second.h;
                    for (int yy = 0; yy < n->h; ++yy) {
                        int sy = int((yy + .5f) / n->h * shh);
                        if (sy < 0 || sy >= shh) continue;
                        for (int xx = 0; xx < n->w; ++xx) {
                            int sx = int((xx + .5f) / n->w * sw);
                            if (sx < 0 || sx >= sw) continue;
                            int dx = n->x + xx, dy = n->y + yy;
                            if (dx < 0 || dy < 0 || dx >= w || dy >= h) continue;
                            auto c = it2->second.px[size_t(sy) * sw + sx];
                            surface_fb->set_pixel(dx, dy, c);
                        }
                    }
                }
            } else if (n->is_canvas && n->canvas && n->canvas->bitmap().get_pixel_count() > 0 &&
                n->w > 0 && n->h > 0) {
                // canvas bitmap → page (drawImage semantics through Canvas2D)
                const auto& src = n->canvas->bitmap().get_pixels();
                int sw = n->canvas->bitmap().get_width(), shh = n->canvas->bitmap().get_height();
                for (int yy = 0; yy < n->h; ++yy) {
                    int sy = int((yy + .5f) / n->h * shh);
                    if (sy < 0 || sy >= shh) continue;
                    for (int xx = 0; xx < n->w; ++xx) {
                        int sx = int((xx + .5f) / n->w * sw);
                        if (sx < 0 || sx >= sw) continue;
                        int dx = n->x + xx, dy = n->y + yy;
                        if (dx < 0 || dy < 0 || dx >= w || dy >= h) continue;
                        auto c = src[size_t(sy) * sw + sx];
                        if (c.a > 0) surface_fb->set_pixel(dx, dy, c);
                    }
                }
            } else {
                bool drawn = false;
                for (auto& c : n->children) {
                    if (c->tag != "#text") continue;
                    if (drawn) break;
                    auto it2 = text_line.find(c.get());
                    if (it2 == text_line.end()) continue;
                    drawn = true;
                    draw_text_of(n, it2->second.first, it2->second.second);
                }
            }
        }
        for (auto& c : n->children) {
            // S133: inline_block is atomic — it IS painted (unlike plain
            // inline elements, whose boxes merge into the parent flow)
            if (c->tag == "#text" || (c->inline_el && !c->inline_block) ||
                c->positioned)
                continue;
            paint_node(c.get());
        }
    };
    // paint from the BODY (the root holder element is never laid out — the
    // all-pink regression — and head-family children paint nothing anyway)
    paint_node(body_n);

    std::vector<DomNode*> pos_paint;
    std::function<void(DomNode*)> gather_pos = [&](DomNode* n) {
        if (n->tag == "script" || n->tag == "style" || n->tag == "head" ||
            n->tag == "title" || n->tag == "link" || n->tag == "meta") return;
        if (n->positioned && n->visible && n->laid_out) pos_paint.push_back(n);
        for (auto& c : n->children) gather_pos(c.get());
    };
    gather_pos(impl->doc.root.get());
    // S118 STACKING law (CSS 2.1 Appendix E.2 + §9.9.1): positioned
    // descendants include RELATIVE boxes — a relative element carrying a
    // z-index joins the z-ordered paint phase. The old flow-only paint
    // buried accelerace's car (position:relative, z-index:99) under the
    // absolutely-positioned road that follows it in paint order.
    // (relative boxes keep their flow paint; the z-phase repaint lands
    // identical pixels on top, matching the browser's stacking result)
    std::function<void(DomNode*)> gather_rel = [&](DomNode* n) {
        if (n->display_none) return;
        if (n->tag != "script" && n->tag != "style" && n->tag != "head" &&
            n->tag != "title" && n->tag != "link" && n->tag != "meta" &&
            n->pos_mode == 1 && n->z_given && n->visible && n->laid_out)
            pos_paint.push_back(n);
        for (auto& c : n->children) gather_rel(c.get());
    };
    gather_rel(impl->doc.root.get());
    std::stable_sort(pos_paint.begin(), pos_paint.end(),
                     [](const DomNode* a, const DomNode* b) { return a->z_index < b->z_index; });
    if (wv_trace()) {
        std::cerr << "[WV-POS] order:";
        for (auto* p : pos_paint)
            std::cerr << " " << p->tag
                      << (p->attrs.count("class") ? ("." + p->attrs.at("class")) : "")
                      << "(" << p->z_index << ")";
        std::cerr << std::endl;
    }
    for (auto* p : pos_paint) paint_node(p);

    // blit the page surface into the caller's buffer
    const auto& px = surface_fb->get_pixels();
    for (int i = 0; i < size_t(w) * h && i < int(px.size()); ++i) {
        dst[i * 4] = px[i].r;
        dst[i * 4 + 1] = px[i].g;
        dst[i * 4 + 2] = px[i].b;
        dst[i * 4 + 3] = px[i].a;
    }
    impl->painted_once = true;   // S118: boxes are established from here on
}

// ── frame pump ──────────────────────────────────────────────────────────
void WebViewEngine::tick(double frame_ms) {
    auto* impl = impl_.get();
    if (!impl || !impl->ctx) return;
    if (frame_ms <= impl->now_ms) frame_ms = impl->now_ms + 16.6;  // vsync law floor
    impl->now_ms = frame_ms;
    // 1) due timers (setInterval reschedules; setTimeout one-shot)
    std::vector<int> fired;
    for (auto& [id, t] : impl->timers)
        if (t.due_ms <= frame_ms) fired.push_back(id);
    for (int id : fired) {
        auto it = impl->timers.find(id);
        if (it == impl->timers.end()) continue;  // cleared by an earlier callback
        bool repeated = it->second.repeated;
        double interval = it->second.interval;
        JSValue func = JS_DupValue(impl->ctx, it->second.func);
        std::vector<JSValue> args;
        for (auto& a : impl->timer_args_[id]) args.push_back(JS_DupValue(impl->ctx, a));
        // DETACH from the maps before calling: the callback may legally call
        // clearTimeout(id) — writing through `it` after that erase was the
        // heap-corruption root cause (invalidated RB-tree iterator).
        JS_FreeValue(impl->ctx, it->second.func);
        impl->timers.erase(it);
        impl->timer_args_.erase(id);
        impl->set_deadline(5.0);
        JSValue r = JS_Call(impl->ctx, func, JS_UNDEFINED, int(args.size()), args.data());
        if (JS_IsException(r)) impl->report_exception("timer");
        JS_FreeValue(impl->ctx, r);
        impl->stats.timers_fired++;
        if (repeated) {
            // reinsert transferring our owned refs
            auto& t = impl->timers[id];
            t = {frame_ms + interval, interval, func, true};
            impl->timer_args_[id] = std::move(args);
        } else {
            for (auto& a : args) JS_FreeValue(impl->ctx, a);
            JS_FreeValue(impl->ctx, func);
        }
    }
    // S118 job pump: timer callbacks await promises (fetch chains) — the
    // continuations must resume before the next frame paints
    impl->drain_pending_jobs(4096);
    // 2) rAF: swap-queue law (callbacks registered now run NEXT frame)
    auto queue = std::move(impl->raf_queue);
    impl->raf_queue.clear();
    for (auto& [f, reg_ms] : queue) {
        impl->set_deadline(5.0);
        JSValue ts = JS_NewFloat64(impl->ctx, frame_ms);
        JSValue r = JS_Call(impl->ctx, f, JS_UNDEFINED, 1, &ts);
        if (JS_IsException(r)) impl->report_exception("rAF");
        JS_FreeValue(impl->ctx, r);
        JS_FreeValue(impl->ctx, ts);
        JS_FreeValue(impl->ctx, f);
        impl->stats.raf_frames++;
    }
    impl->stats.draw_calls = impl->sum_draw_calls();
}

bool WebViewEngine::needs_frames() const {
    auto* impl = impl_.get();
    return impl && (!impl->timers.empty() || !impl->raf_queue.empty());
}

// ── input ───────────────────────────────────────────────────────────────
bool WebViewEngine::pointer_event(int x, int y, const std::string& type) {
    auto* impl = impl_.get();
    if (!impl || !impl->ctx) return false;
    // S114 hit-test law: candidates gathered in PAINT order (flow tree, then
    // positioned z-ascending — mirroring paint_node exactly), the LAST
    // painted node containing the point wins. display:none and
    // visibility:hidden nodes never paint, so they never hit.
    DomNode* hit = nullptr;
    auto contains = [](DomNode* n, int px, int py) {
        return n->w > 0 && n->h > 0 &&
               px >= n->x && px < n->x + n->w && py >= n->y && py < n->y + n->h;
    };
    std::vector<DomNode*> paint_order;
    // S114 transparency law: a box with no background/border/image/text
    // paints NOTHING — it never receives pointer events (CSS hit-testing;
    // the full-screen transparent .wrap overlays used to swallow taps)
    auto paints_something = [&](DomNode* n) -> bool {
        if (n->has_bg || n->grad || n->has_border || n->box_shadow ||
            !n->bg_image.empty() || n->is_canvas)
            return true;
        // any non-whitespace text in the subtree paints glyphs
        std::function<bool(const DomNode*)> has_text = [&](const DomNode* g) -> bool {
            if (g->tag == "#text")
                return g->text.find_first_not_of(" \t\r\n") != std::string::npos;
            for (auto& c : g->children) if (has_text(c.get())) return true;
            return false;
        };
        return has_text(n);
    };
    std::function<void(DomNode*)> flow_walk = [&](DomNode* n) {
        if (n->display_none || n->eff_vis_hidden) return;
        if (n->tag != "html" && n->tag != "body" && paints_something(n))
            paint_order.push_back(n);
        for (auto& c : n->children) {
            if (c->positioned) continue;
            flow_walk(c.get());
        }
    };
    std::function<void(DomNode*)> pos_walk = [&](DomNode* n) {
        if (n->display_none || n->eff_vis_hidden) return;
        if (n->tag != "html" && n->tag != "body" && paints_something(n))
            paint_order.push_back(n);
        // flow children first (paint_node law), positioned z-ascending after
        std::vector<DomNode*> pos_kids;
        for (auto& c : n->children) {
            if (c->display_none) continue;
            if (c->positioned) pos_kids.push_back(c.get());
            else pos_walk(c.get());
        }
        std::stable_sort(pos_kids.begin(), pos_kids.end(),
                         [](const DomNode* a, const DomNode* b) { return a->z_index < b->z_index; });
        for (auto* p : pos_kids) pos_walk(p);
    };
    DomNode* body_n2 = impl->body();
    if (body_n2) flow_walk(body_n2);
    for (auto& c : impl->doc.root->children)
        if (c->tag == "body") { /* body's flow walk done above */ }
    // positioned pass from the body (matches the layout/paint root)
    {
        std::vector<DomNode*> pos_kids;
        std::function<void(DomNode*)> top_pos = [&](DomNode* n) {
            for (auto& c : n->children) {
                if (c->display_none) continue;
                if (c->positioned) pos_kids.push_back(c.get());
                else top_pos(c.get());
            }
        };
        top_pos(body_n2 ? body_n2 : impl->doc.root.get());
        std::stable_sort(pos_kids.begin(), pos_kids.end(),
                         [](const DomNode* a, const DomNode* b) { return a->z_index < b->z_index; });
        for (auto* p : pos_kids) pos_walk(p);
    }
    // S114 hit selection: the DEEPEST painted node containing the point wins
    // (browser hit-testing targets leaf boxes; ancestors only back it up),
    // ties broken by paint order (later paints on top)
    int best_depth = -1;
    size_t best_idx = 0;
    for (size_t pi = 0; pi < paint_order.size(); ++pi) {
        DomNode* n = paint_order[pi];
        if (!n->laid_out || !contains(n, x, y)) continue;
        int depth = 0;
        for (DomNode* p = n; p; p = p->parent) ++depth;
        if (depth >= best_depth) { best_depth = depth; best_idx = pi; }
    }
    hit = best_depth >= 0 ? paint_order[best_idx] : nullptr;
    if (wv_trace())
        std::cerr << "[WV-POINTER] " << type << " at (" << x << "," << y
                  << ") hit=" << (hit ? hit->tag : "none")
                  << (hit && hit->attrs.count("class")
                          ? "." + hit->attrs.at("class")
                          : "")
                  << " listeners="
                  << (hit && impl->listeners.count(hit)
                          ? impl->listeners.at(hit).count(lower_s(type))
                          : 0)
                  << std::endl;
    if (!hit) return false;
    JSValue ev = JS_NewObject(impl->ctx);
    JS_SetPropertyStr(impl->ctx, ev, "type", JS_NewString(impl->ctx, type.c_str()));
    JS_SetPropertyStr(impl->ctx, ev, "target", impl->get_element_js(hit));
    JS_SetPropertyStr(impl->ctx, ev, "button", JS_NewInt32(impl->ctx, 0));
    JS_SetPropertyStr(impl->ctx, ev, "pointerId", JS_NewInt32(impl->ctx, 1));
    JS_SetPropertyStr(impl->ctx, ev, "clientX", JS_NewInt32(impl->ctx, x));
    JS_SetPropertyStr(impl->ctx, ev, "clientY", JS_NewInt32(impl->ctx, y));
    JS_SetPropertyStr(impl->ctx, ev, "pageX", JS_NewInt32(impl->ctx, x));
    JS_SetPropertyStr(impl->ctx, ev, "pageY", JS_NewInt32(impl->ctx, y));
    // touches array (touch events law)
    JSValue touches = JS_NewArray(impl->ctx);
    JSValue t0 = JS_NewObject(impl->ctx);
    JS_SetPropertyStr(impl->ctx, t0, "clientX", JS_NewInt32(impl->ctx, x));
    JS_SetPropertyStr(impl->ctx, t0, "clientY", JS_NewInt32(impl->ctx, y));
    JS_SetPropertyStr(impl->ctx, t0, "pageX", JS_NewInt32(impl->ctx, x));
    JS_SetPropertyStr(impl->ctx, t0, "pageY", JS_NewInt32(impl->ctx, y));
    JS_SetPropertyUint32(impl->ctx, touches, 0, t0);
    JS_SetPropertyStr(impl->ctx, ev, "touches", touches);
    impl->dispatch(hit, lower_s(type), ev);
    return true;
}

bool WebViewEngine::key_event(const std::string& key, const std::string& type, const std::string&) {
    auto* impl = impl_.get();
    if (!impl || !impl->ctx) return false;
    JSValue ev = JS_NewObject(impl->ctx);
    JS_SetPropertyStr(impl->ctx, ev, "type", JS_NewString(impl->ctx, type.c_str()));
    JS_SetPropertyStr(impl->ctx, ev, "key", JS_NewString(impl->ctx, key.c_str()));
    JS_SetPropertyStr(impl->ctx, ev, "code", JS_NewString(impl->ctx, key.c_str()));
    // window-level key listeners
    auto lit = impl->listeners.find(nullptr);
    bool ran = false;
    if (lit != impl->listeners.end()) {
        auto vit = lit->second.find(lower_s(type));
        if (vit != lit->second.end()) {
            for (auto& f : vit->second) {
                impl->set_deadline(5.0);
                JSValue r = JS_Call(impl->ctx, f, JS_UNDEFINED, 1, &ev);
                if (JS_IsException(r)) impl->report_exception("key listener");
                JS_FreeValue(impl->ctx, r);
                ran = true;
            }
        }
    }
    impl->stats.events_dispatched++;
    return ran;
}

// ── S133 ES-MODULE loader law ───────────────────────────────────────────
// WHATWG HTML §4.12.21 + ES2020 modules: type=module scripts (and any
// import()/static import they trigger) resolve specifiers against the
// document base and fetch through the SAME resource substrate as every
// other external ref (S133 fetch_resource → mininet::http_get / APK
// assets). QuickJS owns the module map — one instance per resolved name.
struct WebViewEngine::Impl;   // fwd (defined below)

static char* s133_module_normalize(JSContext* ctx, const char* base_name,
                                   const char* name, void* opaque) {
    (void)opaque;
    std::string ref = name;
    // Bare module specifier ("react-dom/client"): NOT a path — hand it back
    // unchanged; the loader refuses it with an honest error (import maps are
    // a separate measured-need feature).
    if (!(ref.rfind("/", 0) == 0 || ref.rfind("./", 0) == 0 ||
          ref.rfind("../", 0) == 0 || ref.rfind("//", 0) == 0 ||
          ref.rfind("http://", 0) == 0 || ref.rfind("https://", 0) == 0 ||
          ref.rfind("assets/", 0) == 0 || ref.rfind("file:", 0) == 0 ||
          ref.rfind("data:", 0) == 0)) {
        char* out = (char*)js_malloc(ctx, ref.size() + 1);
        memcpy(out, ref.c_str(), ref.size() + 1);
        return out;
    }
    // already absolute (scheme'd or APK-asset form) — take as-is
    if (ref.rfind("http://", 0) == 0 || ref.rfind("https://", 0) == 0 ||
        ref.rfind("assets/", 0) == 0 || ref.rfind("file:", 0) == 0) {
        char* out = (char*)js_malloc(ctx, ref.size() + 1);
        memcpy(out, ref.c_str(), ref.size() + 1);
        return out;
    }
    // merge against the importing module's URL (RFC 3986 §5.2 transform).
    // base_name is the module's own resolved name (absolute or asset path).
    std::string base = base_name ? base_name : "";
    std::string dir;
    if (ref.rfind("//", 0) == 0) {
        ref = "https:" + ref;
        char* out = (char*)js_malloc(ctx, ref.size() + 1);
        memcpy(out, ref.c_str(), ref.size() + 1);
        return out;
    }
    size_t slash = base.rfind('/');
    if (slash == std::string::npos) dir = "";
    else {
        // keep scheme+host+directory (skip the "path0" root edge)
        size_t scheme_end = base.find("://");
        if (ref[0] == '/' && scheme_end != std::string::npos) {
            size_t host_slash = base.find('/', scheme_end + 3);
            dir = base.substr(0, host_slash == std::string::npos
                                      ? base.size() : host_slash);
        } else {
            dir = base.substr(0, slash + 1);
        }
    }
    std::string merged = ref[0] == '/' ? dir + ref : dir + ref;
    // RFC 3986 §5.2.4 remove_dot_segments over the path portion. Only a
    // "://" form carries a scheme+authority prefix; asset paths ("assets/…")
    // are ROOTED relative names — they must NOT gain a leading slash.
    {
        std::string prefix;
        std::string p = merged;
        size_t se = p.find("://");
        if (se != std::string::npos) {
            size_t hs = p.find('/', se + 3);
            if (hs != std::string::npos) {
                prefix = p.substr(0, hs);
                p = p.substr(hs);
            } else {
                prefix = p;
                p.clear();
            }
        }
        std::vector<std::string> out;
        size_t i = 0;
        while (i < p.size()) {
            size_t j = p.find('/', i);
            std::string seg = p.substr(i, (j == std::string::npos ? p.size() : j) - i);
            i = (j == std::string::npos) ? p.size() : j + 1;
            if (seg.empty() || seg == ".") continue;
            if (seg == "..") { if (!out.empty()) out.pop_back(); continue; }
            out.push_back(seg);
        }
        std::string r = prefix;
        for (size_t k = 0; k < out.size(); ++k) {
            if (!r.empty() && r.back() != '/') r += "/";
            r += out[k];
        }
        merged = r;
    }
    char* out = (char*)js_malloc(ctx, merged.size() + 1);
    memcpy(out, merged.c_str(), merged.size() + 1);
    return out;
}

static JSModuleDef* s133_module_loader(JSContext* ctx, const char* module_name,
                                       void* opaque) {
    auto* impl = (WebViewEngine::Impl*)opaque;
    if (!impl) {
        JS_ThrowInternalError(ctx, "module loader: no engine");
        return nullptr;
    }
    // Bare specifiers (react-dom/client) are NOT resolvable: honest error
    // (a bare-import map is a separate, measured-need feature).
    if (std::string(module_name).rfind("http", 0) != 0 &&
        std::string(module_name).rfind("assets/", 0) != 0 &&
        std::string(module_name).rfind("/assets/", 0) != 0) {
        std::string msg = std::string("could not resolve module specifier '") +
                          module_name + "' (no import map)";
        std::cerr << "[WV-MODULE] " << msg << std::endl;
        JS_ThrowReferenceError(ctx, msg.c_str());
        return nullptr;
    }
    auto bytes = impl->fetch_resource(module_name, "module-import");
    if (bytes.empty()) {
        std::string msg = std::string("could not load module '") + module_name + "'";
        std::cerr << "[WV-MODULE] " << msg << std::endl;
        JS_ThrowReferenceError(ctx, msg.c_str());
        return nullptr;
    }
    std::string code(bytes.begin(), bytes.end());
    JSValue func_val = JS_Eval(ctx, code.c_str(), code.size(), module_name,
                               JS_EVAL_TYPE_MODULE | JS_EVAL_FLAG_COMPILE_ONLY);
    if (JS_IsException(func_val)) return nullptr;
    // COMPILE_ONLY module eval returns JS_TAG_MODULE whose ptr IS the def.
    JSModuleDef* m = (JSModuleDef*)JS_VALUE_GET_PTR(func_val);
    JS_FreeValue(ctx, func_val);   // def stays registered in the module map
    std::cerr << "[WV-MODULE] loaded " << module_name << " ("
              << code.size() << " bytes)" << std::endl;
    return m;
}

// ── S133 UNHANDLED-REJECTION law ────────────────────────────────────────
// A real browser reports unhandled promise rejections on the console
// (WHATWG HTML §8.1.2.6 "unhandledrejection"). The engine swallowed them
// silently — a whole SPA boot chain can die invisibly (measured: z.ai's
// mount promise chain). The tracker makes every rejection VISIBLE.
static void s133_promise_rejection(JSContext* ctx, JSValueConst promise,
                                   JSValueConst reason, JS_BOOL is_handled,
                                   void* opaque) {
    (void)promise;
    (void)opaque;
    if (is_handled) return;
    const char* msg = JS_ToCString(ctx, reason);
    std::cerr << "[WV-REJECT] unhandled promise rejection: "
              << (msg ? msg : "(no reason)") << std::endl;
    if (msg) JS_FreeCString(ctx, msg);
    // S133: line/column when present — minified single-line bundles still
    // carry pc2line positions on the exception object
    for (const char* prop : {"lineNumber", "columnNumber"}) {
        JSValue v = JS_GetPropertyStr(ctx, reason, prop);
        if (JS_IsNumber(v)) {
            double d = -1; JS_ToFloat64(ctx, &d, v);
            std::cerr << "[WV-REJECT]   " << prop << "=" << long(d) << std::endl;
        }
        JS_FreeValue(ctx, v);
    }
    JSValue stack = JS_GetPropertyStr(ctx, reason, "stack");
    if (JS_IsString(stack)) {
        const char* st = JS_ToCString(ctx, stack);
        if (st && *st) std::cerr << "[WV-REJECT] stack: " << st << std::endl;
        if (st) JS_FreeCString(ctx, st);
    }
    JS_FreeValue(ctx, stack);
}

// ── engine lifecycle ────────────────────────────────────────────────────
WebViewEngine::WebViewEngine(uint32_t view_id) : view_id_(view_id) {
    impl_ = std::make_unique<Impl>();
    impl_->self = this;
    impl_->rt = JS_NewRuntime();
    JS_SetMemoryLimit(impl_->rt, 512ull * 1024 * 1024);
    // S133 ES-MODULE law: the runtime module system resolves specifiers
    // against the importing module's URL and fetches through the engine's
    // resource substrate (network + assets, one resource table).
    JS_SetModuleLoaderFunc(impl_->rt, s133_module_normalize, s133_module_loader,
                           impl_.get());
    JS_SetHostPromiseRejectionTracker(impl_->rt, s133_promise_rejection,
                                      impl_.get());
    register_js_classes(impl_->rt);
    impl_->rng_state ^= view_id * 2654435761u + 1;
}

WebViewEngine::~WebViewEngine() {
    if (impl_) {
        impl_->persist_kv();
        impl_.reset();
    }
}

bool WebViewEngine::load_document(const std::string& url, const std::string& html,
                                  const std::string& apk_path) {
    auto* impl = impl_.get();
    if (!impl || !impl->rt) return false;
    impl->apk_path = apk_path;
    url_ = url;
    impl->doc = HtmlParser::parse(html);
    impl->canvas_nodes.clear();
    std::function<void(DomNode*)> cc = [&](DomNode* n) {
        if (n->is_canvas) impl->canvas_nodes.push_back(n);
        for (auto& c : n->children) cc(c.get());
    };
    cc(impl->doc.root.get());
    std::cerr << "[WV-ENGINE] parsed: nodes(doc)=" << impl->doc.inline_scripts.size()
              << " inline scripts, " << impl->doc.external_scripts.size()
              << " external scripts, title=\"" << impl->doc.title << "\"" << std::endl;
    // collect <style> rules from the parsed tree
    std::function<void(DomNode*)> css = [&](DomNode* n) {
        if (n->tag == "style") {
            auto rules = HtmlParser::parse_stylesheet(n->text);
            for (auto& r : rules) impl->css_rules.push_back(std::move(r));
        }
        for (auto& c : n->children) css(c.get());
    };
    css(impl->doc.root.get());
    // S113+ external stylesheets — <link rel=stylesheet href> fetch + parse
    // (S133: APK-asset OR network tier through fetch_resource — one resource
    // table covers every consumer).
    for (auto& [href, _tag] : impl->doc.external_styles) {
        auto bytes = impl->fetch_resource(href, "stylesheet");
        if (bytes.empty()) {
            std::cerr << "[WV-CSS] external stylesheet fetch FAILED: " << href << std::endl;
            continue;
        }
        std::string css_text(bytes.begin(), bytes.end());
        auto rules = HtmlParser::parse_stylesheet(css_text);
        std::cerr << "[WV-CSS] external " << href << " rules=" << rules.size() << std::endl;
        for (auto& r : rules) impl->css_rules.push_back(std::move(r));
    }
    // S113: @font-face registration law (Typeface.createFromAsset equivalence)
    for (auto& r : impl->css_rules) {
        if (r.selector != "@font-face") continue;
        auto fam_it = r.props.find("font-family");
        auto src_it = r.props.find("src");
        if (fam_it == r.props.end() || src_it == r.props.end()) continue;
        std::string family = lower_s(fam_it->second);
        family.erase(std::remove(family.begin(), family.end(), '"'), family.end());
        family.erase(std::remove(family.begin(), family.end(), '\''), family.end());
        family = trim2(family);
        size_t u0 = src_it->second.find("url(");
        if (u0 == std::string::npos) continue;
        size_t p0 = u0 + 4, pe = src_it->second.find(')', p0);
        if (pe == std::string::npos) continue;
        std::string url = src_it->second.substr(p0, pe - p0);
        url.erase(std::remove(url.begin(), url.end(), '"'), url.end());
        url.erase(std::remove(url.begin(), url.end(), '\''), url.end());
        auto fbytes = impl->fetch_resource(url, "font-face");
        if (fbytes.empty()) {
            std::cerr << "[WV-FONT] fetch FAILED: " << url << std::endl;
            continue;
        }
        int idx = fonts::TextShaper::instance().register_app_font_memory(fbytes, family, false);
        if (idx >= 0) {
            impl->font_family_map[family] = idx;
            std::cerr << "[WV-FONT] registered '" << family << "' face=" << idx
                      << " (" << fbytes.size() << " bytes)" << std::endl;
        } else {
            std::cerr << "[WV-FONT] register FAILED for '" << family << "'" << std::endl;
        }
    }
    HtmlParser::apply_css_impl(impl->doc.root.get(), impl->css_rules,
                               &impl->custom_props, true);
    std::cerr << "[WV-ENGINE] css rules=" << impl->css_rules.size() << std::endl;
    impl->setup_bindings();
    impl->run_scripts();
    impl->stats.draw_calls = impl->sum_draw_calls();
    std::cerr << "[WV-ENGINE] scripts executed=" << impl->stats.scripts_executed
              << " js_errors=" << impl->stats.js_errors
              << " draw_calls=" << impl->stats.draw_calls
              << " raf_pending=" << impl->raf_queue.size()
              << " timers=" << impl->timers.size()
              << " script_ms=" << int(impl->stats.script_ms) << std::endl;
    return true;
}

// ── registry ────────────────────────────────────────────────────────────
WebViewRegistry& WebViewRegistry::instance() {
    static WebViewRegistry r;
    return r;
}
std::shared_ptr<WebViewEngine> WebViewRegistry::create(uint32_t view_id) {
    auto e = std::make_shared<WebViewEngine>(view_id);
    engines_[view_id] = e;
    return e;
}
std::shared_ptr<WebViewEngine> WebViewRegistry::find(uint32_t view_id) {
    auto it = engines_.find(view_id);
    return it == engines_.end() ? nullptr : it->second;
}
void WebViewRegistry::tick_all(double frame_ms) {
    for (auto& [id, e] : engines_) e->tick(frame_ms);
}
bool WebViewRegistry::any_needs_frames() const {
    for (auto& [id, e] : engines_)
        if (e->needs_frames()) return true;
    return false;
}
std::vector<std::shared_ptr<WebViewEngine>> WebViewRegistry::all() const {
    std::vector<std::shared_ptr<WebViewEngine>> out;
    for (auto& [id, e] : engines_) out.push_back(e);
    return out;
}

}} // namespace miniandroid::webview

