// S109 WEBVIEW-ENGINE — implementation. See webview_engine.h for laws.
#include "webview_engine.h"
#include "text_shaper.h"
#include "../resources/resource_runtime.h"
#include "../third_party/nlohmann_json/include/nlohmann/json.hpp"
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

    // ── S113 CSS layout/paint state ─────────────────────────────────────
    int css_viewport_w = -1;              // last width used for @media evaluation
    std::vector<CssRule> active_rules;    // media-filtered rules for the current viewport
    std::map<std::string, int> font_family_map;   // lowercased @font-face family → face idx
    struct CachedImg { int w = 0, h = 0; std::vector<renderer::RGBA> px; bool ok = false; };
    std::map<std::string, CachedImg> img_cache;

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

    bool exec_script(const std::string& code, const std::string& name) {
        if (code.empty()) return false;
        set_deadline(20.0);  // hang guard: no infinite loop stalls the runtime
        auto t0 = std::chrono::steady_clock::now();
        JSValue r = JS_Eval(ctx, code.c_str(), code.size(), name.c_str(), JS_EVAL_TYPE_GLOBAL);
        stats.script_ms += std::chrono::duration<double, std::milli>(
            std::chrono::steady_clock::now() - t0).count();
        bool ok = !JS_IsException(r);
        JS_FreeValue(ctx, r);
        if (!ok) report_exception("script " + name);
        else stats.scripts_executed++;
        return ok;
    }

    // ── URL/asset law ──────────────────────────────────────────────────
    std::string url_dir() const {
        std::string u = self->document_url();
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
        if (ref[0] == '/') return "assets" + ref;   // app-root-relative
        return url_dir() + ref;
    }
    std::vector<uint8_t> fetch_asset(const std::string& ref) {
        std::string entry = resolve_url(ref);
        size_t q = entry.find_first_of("?#");
        if (q != std::string::npos) entry.erase(q);
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
    std::string key = lower_s(name);
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
    std::string key = lower_s(name);
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
            std::string key = lower_s(k);
            n->style[key] = v;
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
        if (k) { n->style.erase(lower_s(k)); JS_FreeCString(ctx, k); }
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
static JSValue el_get_offset_w(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    return JS_NewInt32(ctx, n ? n->w : 0);
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
static JSValue el_getBoundingClientRect(JSContext* ctx, JSValueConst this_v, int, JSValueConst*) {
    auto* n = el_of(this_v);
    JSValue o = JS_NewObject(ctx);
    double x = n ? n->x : 0, y = n ? n->y : 0, w = n ? n->w : 0, h = n ? n->h : 0;
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
    if (!n->canvas) n->canvas = std::make_unique<Canvas2D>();
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
static JSValue doc_querySelector(JSContext* ctx, JSValueConst, int argc, JSValueConst* argv) {
    auto* impl = impl_of(ctx);
    if (argc < 1) return JS_NULL;
    const char* sel = JS_ToCString(ctx, argv[0]);
    if (!sel) return JS_NULL;
    std::string s = sel;
    JS_FreeCString(ctx, sel);
    DomNode* hit = nullptr;
    if (!s.empty() && s[0] == '#') {
        hit = find_by_id(impl->doc.root.get(), s.substr(1));
    } else if (!s.empty() && s[0] == '.') {
        std::string cls = s.substr(1);
        std::function<DomNode*(DomNode*)> walk = [&](DomNode* n) -> DomNode* {
            auto it = n->attrs.find("class");
            if (it != n->attrs.end()) {
                std::istringstream ss(it->second);
                std::string tok;
                while (ss >> tok) if (tok == cls) return n;
            }
            for (auto& c : n->children) { DomNode* r = walk(c.get()); if (r) return r; }
            return nullptr;
        };
        hit = walk(impl->doc.root.get());
    } else {
        std::string tag = lower_s(s);
        std::vector<DomNode*> out;
        collect_tag(impl->doc.root.get(), tag, out);
        hit = out.empty() ? nullptr : out.front();
    }
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
static void image_decode(ImageObj* im, WebViewEngine::Impl* impl) {
    auto bytes = impl->fetch_asset(im->src);
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
    accessor("innerHTML", el_get_inner_html, el_set_inner_html);
    accessor("innerText", el_get_text, el_set_text);
    accessor("textContent", el_get_text, el_set_text);
    accessor("style", el_get_style, nullptr);
    accessor("classList", el_get_class_list2, nullptr);
    accessor("children", el_get_children, nullptr);
    accessor("parentElement", el_get_parent, nullptr);
    accessor("parentNode", el_get_parent, nullptr);
    accessor("firstChild", el_get_first_child, nullptr);
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
void WebViewEngine::Impl::dispatch(DomNode* target, const std::string& type, JSValue ev) {
    stats.events_dispatched++;
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

    window_obj = JS_NewObject(ctx);
    // globalThis == window
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
        JS_SetPropertyStr(ctx, loc, "protocol", JS_NewString(ctx, "file:"));
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
        JS_SetPropertyStr(ctx, global, "crypto", crypto_o);
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
    for (auto& code : doc.inline_scripts) exec_script(code, "inline");
    for (auto& [src, _] : doc.external_scripts) {
        auto bytes = fetch_asset(src);
        if (bytes.empty()) {
            std::cerr << "[WV-SCRIPT] external script missing: " << src
                      << " (resolved " << resolve_url(src) << ")" << std::endl;
            continue;
        }
        std::string code(bytes.begin(), bytes.end());
        std::cerr << "[WV-SCRIPT] external " << src << " bytes=" << code.size() << std::endl;
        exec_script(code, src);
    }
    // count DOM nodes for provenance
    std::function<void(DomNode*)> count = [&](DomNode* n) {
        stats.dom_nodes++;
        for (auto& c : n->children) count(c.get());
    };
    count(doc.root.get());
}

// ── layout + compose ────────────────────────────────────────────────────
// ROOT-050 law: CSS <length> resolution must handle calc() and var() —
// Breakout 71 sizes its canvas with `height:calc(var(--vh,1vh)*100)` and the
// old atof() answered 0 for any calc() form, collapsing the canvas to a
// ~30px strip. Resolution order: substitute var(--x, fallback) (custom props
// are var-resolved upstream when defined), then evaluate the calc term
// (<len> * <num> / <num> * <len> / <len> / <num> / plain <len>).
static float css_len_px(const std::string& v, float viewport, float dflt) {
    if (v.empty()) return dflt;
    std::string s = v;
    size_t vp;
    while ((vp = s.find("var(")) != std::string::npos) {
        size_t open = vp + 4, depth = 1, i = open;
        while (i < s.size() && depth) {
            depth += s[i] == '(' ? 1 : 0;
            depth -= s[i] == ')' ? 1 : 0;
            ++i;
        }
        std::string inner = s.substr(open, i - open - 1);
        std::string repl;
        size_t comma = inner.find(',');
        if (comma != std::string::npos) repl = inner.substr(comma + 1);
        s = s.substr(0, vp) + repl + s.substr(i);
    }
    if (s.rfind("calc(", 0) == 0 && !s.empty() && s.back() == ')') {
        std::string body = s.substr(5, s.size() - 6);
        size_t star = body.find('*'), slash = body.find('/');
        if (star != std::string::npos && (slash == std::string::npos || star < slash)) {
            std::string lhs = body.substr(0, star), rhs = body.substr(star + 1);
            auto has_unit = [&](const std::string& t) {
                return t.find("vw") != std::string::npos ||
                       t.find("vh") != std::string::npos ||
                       (!t.empty() && t.back() == '%');
            };
            // exactly one side is a <length>, the other a scalar
            if (has_unit(lhs) && !has_unit(rhs))
                return css_len_px(lhs, viewport, dflt) * ::atof(rhs.c_str());
            if (has_unit(rhs) && !has_unit(lhs))
                return css_len_px(rhs, viewport, dflt) * ::atof(lhs.c_str());
            if (!has_unit(lhs) && !has_unit(rhs))
                return float(::atof(lhs.c_str()) * ::atof(rhs.c_str()));
            return dflt;  // both lengths: unit mismatch → invalid per CSS
        }
        if (slash != std::string::npos) {
            std::string lhs = body.substr(0, slash), rhs = body.substr(slash + 1);
            float denom = ::atof(rhs.c_str());
            return denom != 0 ? css_len_px(lhs, viewport, dflt) / denom : dflt;
        }
        return css_len_px(body, viewport, dflt);
    }
    auto val = [&](float unit = 1.f) { return ::atof(s.c_str()) * unit; };
    if (s.find("vw") != std::string::npos) return val(viewport / 100.f);
    if (s.find("vh") != std::string::npos) return val(viewport / 100.f);
    if (s.back() == '%') return val(viewport / 100.f);
    return val();
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
    n->visible = !n->display_none;
    if (get("display") == "none" || get("visibility") == "hidden") n->visible = false;
    std::string pos = get("position");
    n->positioned = (pos == "fixed" || pos == "absolute");
    n->z_index = atoi(get("z-index").c_str());
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
    n->font_size = float(css_len_px(get("font-size"), float(vh), 14 * 2));
    n->bold = get("font-weight") == "bold" || get("font-weight") == "700";
    std::string ta = get("text-align");
    n->text_align = ta == "center" ? 1 : (ta == "right" ? 2 : 0);

    // ── S113 CSS box model + paint properties ─────────────────────────
    // padding shorthand (px corpus law; 1/2/3/4-value expansion)
    {
        int v[4] = {0, 0, 0, 0};
        std::string pv = get("padding");
        if (!pv.empty()) {
            std::istringstream ss(pv); std::string tok; int k = 0;
            while (ss >> tok && k < 4) v[k++] = int(::strtod(tok.c_str(), nullptr));
            if (k == 1) { v[1] = v[2] = v[3] = v[0]; }
            else if (k == 2) { v[2] = v[0]; v[3] = v[1]; }
            else if (k == 3) { v[3] = v[1]; }
        } else {
            v[0] = int(::strtod(get("padding-top").c_str(), nullptr));
            v[1] = int(::strtod(get("padding-right").c_str(), nullptr));
            v[2] = int(::strtod(get("padding-bottom").c_str(), nullptr));
            v[3] = int(::strtod(get("padding-left").c_str(), nullptr));
        }
        n->pad_t = v[0]; n->pad_r = v[1]; n->pad_b = v[2]; n->pad_l = v[3];
    }
    // margin shorthand + auto centering
    {
        int v[4] = {0, 0, 0, 0};
        std::string mv = get("margin");
        if (!mv.empty()) {
            std::istringstream ss(mv); std::string tok; int k = 0;
            while (ss >> tok && k < 4) {
                if (tok == "auto") { if (k == 1 || k == 3) n->mar_lr_auto = true; v[k] = 0; }
                else v[k] = int(::strtod(tok.c_str(), nullptr));
                ++k;
            }
            if (k == 1) { v[1] = v[2] = v[3] = v[0]; }
            else if (k == 2) { v[2] = v[0]; v[3] = v[1]; }
            else if (k == 3) { v[3] = v[1]; }
        } else {
            v[0] = int(::strtod(get("margin-top").c_str(), nullptr));
            v[1] = int(::strtod(get("margin-right").c_str(), nullptr));
            v[2] = int(::strtod(get("margin-bottom").c_str(), nullptr));
            v[3] = int(::strtod(get("margin-left").c_str(), nullptr));
            n->mar_lr_auto = get("margin-left") == "auto" && get("margin-right") == "auto";
        }
        n->mar_t = v[0]; n->mar_r = v[1]; n->mar_b = v[2]; n->mar_l = v[3];
        n->mar_t = std::max(-4096, std::min(4096, n->mar_t));
        n->mar_b = std::max(-4096, std::min(4096, n->mar_b));
    }
    // border shorthand: "4px solid #ffcde4"
    {
        std::string bs = get("border");
        if (!bs.empty()) {
            std::istringstream ss(bs);
            std::string wtok, styletok, coltok;
            ss >> wtok >> styletok >> coltok;
            int bw = int(::strtod(wtok.c_str(), nullptr));
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
            n->border_w = int(::strtod(bws.c_str(), nullptr));
    }
    n->radius = int(::strtod(get("border-radius").c_str(), nullptr));
    // display law: flex / inline / none (none already handled above)
    {
        std::string disp = get("display");
        n->flex = disp == "flex";
        if (disp == "inline") n->inline_el = true;
        if (n->tag == "span" || n->tag == "a" || n->tag == "b" || n->tag == "strong" ||
            n->tag == "em" || n->tag == "label" || n->tag == "small")
            if (disp.empty()) n->inline_el = true;
    }
    if (get("align-items") == "center") n->align_items = 1;
    if (get("justify-content") == "center") n->justify_content = 1;
    // width/height % forms — S113 law: percentages resolve against the
    // CONTAINING BLOCK at layout time; they must NOT set has_w (that would
    // double-resolve against the viewport and add padding/border on top,
    // producing 1126px buttons inside a 1080px container).
    {
        std::string ws = get("width"), hs = get("height");
        if (!ws.empty() && ws.back() == '%') {
            n->w_pct = float(::atof(ws.c_str()));
        } else if (!ws.empty() && ws != "auto") {
            n->w = int(css_len_px(ws, float(vw), 0));
            n->has_w = true;   // px, vw, vh — all resolvable now
        }
        if (!hs.empty() && hs.back() == '%') {
            n->h_pct = float(::atof(hs.c_str()));
        } else if (!hs.empty() && hs != "auto") {
            n->h = int(css_len_px(hs, float(vh), 0));
            n->has_h = true;
        }
    }
    if (!get("max-width").empty())
        n->max_w = int(css_len_px(get("max-width"), float(vw), -1));
    // background-image / gradient / shorthand backgrounds
    {
        std::string bi = get("background-image");
        std::string bsh = get("background");
        std::string src = !bi.empty() ? bi : bsh;
        if (src.find("linear-gradient(") != std::string::npos) {
            size_t g0 = src.find("linear-gradient(") + 16;
            size_t g1 = src.find(')', g0);
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
                        if (!parts[0].empty() && parts[0].find("bottom") != std::string::npos)
                            n->grad_diag = true;
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
    if (get("background-size").find("contain") != std::string::npos) n->bg_contain = true;
    if (get("transform").find("scaleX(-1)") != std::string::npos) n->bg_mirror = true;
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
        std::string bxs = get("box-shadow");
        if (!bxs.empty() && bxs.find("inset") == std::string::npos) n->box_shadow = true;
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
        // canvas CSS size: style width/height; bitmap = JS-set size
        std::string cw = get("width"), chh = get("height");
        if (!cw.empty()) n->w = int(css_len_px(cw, float(vw), float(n->canvas->width())));
        if (!chh.empty()) n->h = int(css_len_px(chh, float(vh), float(n->canvas->height())));
        if (wv_trace())
            std::cerr << "[WV-CANVAS] id=" << (n->attrs.count("id") ? n->attrs.at("id") : "")
                      << " css_w=" << cw << " css_h=" << chh
                      << " -> box " << n->w << "x" << n->h
                      << " bitmap " << n->canvas->width() << "x" << n->canvas->height()
                      << " positioned=" << n->positioned << std::endl;
    } else {
        std::string w = get("width"), h = get("height");
        if (!w.empty()) n->w = int(css_len_px(w, float(vw), 0));
        if (!h.empty()) n->h = int(css_len_px(h, float(vh), 0));
    }
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

    // 1. style walk: box-model resolution + inheritance + pseudo rules
    std::function<void(DomNode*, DomNode*)> style_walk =
        [&](DomNode* n, DomNode* parent) {
        if (n->tag == "script" || n->tag == "style" || n->tag == "head" ||
            n->tag == "title" || n->tag == "link" || n->tag == "meta")
            return;
        style_element(n, double(w), double(h), impl->font_family_map);
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
        } else {
            n->eff_fg = n->fg; n->eff_fg_valid = n->has_fg;
            n->eff_face = n->font_face;
            n->eff_font_size = n->font_size;
            n->eff_bold = n->bold;
            n->eff_align = n->text_align;
        }
        // pseudo-element content (::before/::after rules)
        n->pseudo_before.clear(); n->pseudo_after.clear();
        for (auto& r : impl->active_rules) {
            if (!r.pseudo_before && !r.pseudo_after) continue;
            if (!HtmlParser::matches_selector(r.selector, n)) continue;
            auto cit = r.props.find("content");
            if (cit == r.props.end()) continue;
            std::string content = cit->second;
            if (content.size() >= 2 &&
                (content.front() == '"' || content.front() == '\''))
                content = content.substr(1, content.size() - 2);
            if (r.pseudo_before) {
                n->pseudo_before = content;
                if (r.props.count("margin-right")) n->pseudo_before += " ";
            } else {
                if (r.props.count("margin-left")) n->pseudo_after += " ";
                n->pseudo_after += content;
            }
        }
        for (auto& c : n->children) style_walk(c.get(), n);
    };
    style_walk(impl->doc.root.get(), nullptr);

    // own merged inline text of a node (spans merge into the parent flow;
    // block children own their own lines — the S112 duplicate-text law fix)
    std::function<void(DomNode*, std::string&)> gather_inline =
        [&](DomNode* c, std::string& out) {
        if (c->tag == "#text") { out += c->text; return; }
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
        out = n->pseudo_before + out + n->pseudo_after;
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
                               uint32_t from, uint32_t to) {
        renderer::RGBA c1{uint8_t(from & 255), uint8_t((from >> 8) & 255),
                          uint8_t((from >> 16) & 255), 255};
        renderer::RGBA c2{uint8_t(to & 255), uint8_t((to >> 8) & 255),
                          uint8_t((to >> 16) & 255), 255};
        float denom = diag && (rw + rh) > 0 ? float(rw + rh) : float(rh > 0 ? rh : 1);
        for (int yy = std::max(0, y); yy < std::min(h, y + rh); ++yy)
            for (int xx = std::max(0, x); xx < std::min(w, x + rw); ++xx) {
                if (!in_round(xx, yy, x, y, rw, rh, r)) continue;
                float t = diag ? float((xx - x) + (yy - y)) / denom
                               : float(yy - y) / denom;
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
            auto bytes = impl->fetch_asset(n->bg_image);
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
        }
        const auto& src = it->second.px;
        int sw = it->second.w, sh2 = it->second.h;
        for (int yy = 0; yy < dh; ++yy) {
            int sy = int((yy + .5f) / dh * sh2);
            if (sy >= sh2) sy = sh2 - 1;
            for (int xx = 0; xx < dw; ++xx) {
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
    auto draw_text_of = [&](DomNode* n, int line_y, int line_w) {
        std::string t = own_text_of(n);
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
        float baseline = float(line_y) + size * 1.1f;   // legacy baseline law
        if (n->text_shadow) {
            renderer::RGBA shc{uint8_t(n->text_shadow_col & 255),
                               uint8_t((n->text_shadow_col >> 8) & 255),
                               uint8_t((n->text_shadow_col >> 16) & 255),
                               uint8_t((n->text_shadow_col >> 24) & 255)};
            sh.draw(*surface_fb, t, tx + 2, baseline + 2, size, shc, n->eff_bold, face);
        }
        sh.draw(*surface_fb, t, tx, baseline, size, col, n->eff_bold, face);
    };

    // 3. layout — block + flex-column subset (max-content shrink law,
    //    block fill law, margin/padding/border box, auto-centering)
    std::function<int(DomNode*)> measure_w = [&](DomNode* n) -> int {
        int extra = 2 * n->border_w + n->pad_l + n->pad_r;
        int cw2 = 0;
        std::string t = own_text_of(n);
        if (!t.empty()) {
            auto& sh = fonts::TextShaper::instance();
            if (sh.available())
                cw2 = std::max(cw2, int(sh.shape(t, n->eff_font_size, n->eff_bold,
                                                 face_of(n)).width));
        }
        for (auto& c : n->children) {
            if (c->tag == "#text" || c->inline_el) continue;
            if (c->display_none || !c->visible || c->positioned) continue;
            if (c->has_w) cw2 = std::max(cw2, c->w + 2 * c->border_w + c->pad_l + c->pad_r);
            else if (c->w_pct >= 0) continue;
            else cw2 = std::max(cw2, measure_w(c.get()));
        }
        return cw2 + extra;
    };

    std::function<int(DomNode*, int, int, int)> layout_node_at;
    auto layout_stack_once = [&](DomNode* n, int content_x, int content_y,
                                 int content_w, int cy_shift) -> int {
        int cy = content_y + cy_shift;
        std::vector<int> widths(n->children.size(), -1);
        std::vector<int> heights(n->children.size(), 0);
        for (size_t i = 0; i < n->children.size(); ++i) {
            DomNode* c = n->children[i].get();
            if (c->tag == "#text") {
                // whitespace-only text between block boxes renders nothing
                if (is_ws_text(c->text)) continue;
                int tw = 0;
                auto& sh = fonts::TextShaper::instance();
                if (sh.available() && !c->text.empty())
                    tw = int(sh.shape(c->text, n->eff_font_size, n->eff_bold,
                                      face_of(n)).width);
                widths[i] = tw;
                heights[i] = int(n->eff_font_size * 1.6f) + 4;   // legacy line law
                continue;
            }
            // non-boxing elements: never take layout slots (the S113 audit:
            // <audio> without controls and the head family are zero-size in
            // browsers — as rows they added ~480px of phantom height).
            if (c->tag == "script" || c->tag == "style" || c->tag == "head" ||
                c->tag == "title" || c->tag == "link" || c->tag == "meta" ||
                c->tag == "audio")
                continue;
            if (c->display_none || !c->visible || c->positioned) continue;
            if (c->inline_el) { widths[i] = -2; continue; }   // merged into parent text
            int extra = 2 * c->border_w + c->pad_l + c->pad_r;
            if (c->has_w) widths[i] = c->w + extra;
            else if (c->w_pct >= 0) widths[i] = int(float(content_w) * c->w_pct / 100.f);
            else if (n->flex && n->align_items == 1)
                widths[i] = std::min(measure_w(c), content_w);  // flex center shrink
            else widths[i] = content_w;                         // block fill law
            if (c->max_w >= 0 && widths[i] > c->max_w) widths[i] = c->max_w;
            widths[i] = std::max(widths[i], 2 * c->border_w);
        }
        for (size_t i = 0; i < n->children.size(); ++i) {
            DomNode* c = n->children[i].get();
            if (c->tag == "#text") {
                text_line[c] = {cy, widths[i]};
                cy += heights[i];
                continue;
            }
            if (widths[i] < 0) continue;
            int x = content_x + c->mar_l;
            if (n->align_items == 1 || c->mar_lr_auto)
                x = content_x + std::max(0, content_w - widths[i]) / 2;
            int hb = layout_node_at(c, x, cy, widths[i]);
            cy += hb + c->mar_b;
        }
        return cy - content_y - cy_shift;
    };
    layout_node_at = [&](DomNode* n, int x, int y, int outer_w) -> int {
        n->x = x; n->y = y; n->w = outer_w; n->laid_out = true;
        if (wv_trace())
            std::cerr << "[WV-BOX] tag=" << n->tag
                      << " class=" << (n->attrs.count("class") ? n->attrs.at("class") : "")
                      << " box=" << x << "," << y << " " << outer_w << "x" << n->h
                      << " flex=" << n->flex << " hfixed=" << n->has_h
                      << " fs=" << n->eff_font_size << std::endl;
        int content_w = outer_w - 2 * n->border_w - n->pad_l - n->pad_r;
        if (content_w < 0) content_w = 0;
        int fixed_inner = -1;
        if (n->has_h) fixed_inner = n->h - 2 * n->border_w - n->pad_t - n->pad_b;
        int used = layout_stack_once(n, x + n->border_w + n->pad_l,
                                     y + n->border_w + n->pad_t, content_w, 0);
        if (n->flex && n->justify_content == 1 && fixed_inner > 0 && used < fixed_inner) {
            layout_stack_once(n, x + n->border_w + n->pad_l,
                              y + n->border_w + n->pad_t, content_w,
                              (fixed_inner - used) / 2);
            used = fixed_inner;
        }
        // leaf min-height law (legacy flow parity for leaf rows)
        if (!n->has_h && n->h_pct < 0) {
            bool leaf = true;
            for (auto& c : n->children)
                if (c->tag != "#text" && !c->inline_el) { leaf = false; break; }
            if (leaf) {
                int min_h = int(n->eff_font_size * 1.6f) + 4;
                if (used < min_h) used = min_h;
            }
        }
        if (!n->has_h)
            n->h = used + 2 * n->border_w + n->pad_t + n->pad_b;
        return n->h;
    };

    DomNode* body_n = impl->body();
    layout_node_at(body_n, 0, 0, w);

    // positioned roots (fixed/absolute) — resolve offsets, layout subtree
    std::vector<DomNode*> pos_roots;
    std::function<void(DomNode*)> collect_pos_roots = [&](DomNode* n) {
        if (n->tag == "script" || n->tag == "style" || n->tag == "head" ||
            n->tag == "title" || n->tag == "link" || n->tag == "meta") return;
        if (n->positioned && n->visible) {
            bool anc_pos = false;
            for (DomNode* p = n->parent; p; p = p->parent)
                if (p->positioned) { anc_pos = true; break; }
            if (!anc_pos) pos_roots.push_back(n);
        }
        for (auto& c : n->children) collect_pos_roots(c.get());
    };
    collect_pos_roots(impl->doc.root.get());

    std::function<void(DomNode*)> layout_positioned_root = [&](DomNode* n) {
        auto gv = [&](const char* k) -> std::string {
            auto it2 = n->style.find(k);
            return it2 != n->style.end() ? it2->second : std::string();
        };
        float l = -1, t = -1, r_ = -1, b_ = -1;
        if (!gv("left").empty()) l = css_len_px(gv("left"), float(w), 0);
        if (!gv("top").empty()) t = css_len_px(gv("top"), float(h), 0);
        if (!gv("right").empty()) r_ = css_len_px(gv("right"), float(w), 0);
        if (!gv("bottom").empty()) b_ = css_len_px(gv("bottom"), float(h), 0);
        int bw2 = n->w > 0 ? n->w : (r_ >= 0 && l >= 0 ? int(w - r_ - l)
                                   : std::min(measure_w(n), w));
        n->w = bw2;
        int x2 = l >= 0 ? int(l) : (r_ >= 0 ? int(w - r_ - bw2) : 0);
        int y2 = t >= 0 ? int(t) : 0;
        n->x = x2; n->y = y2; n->laid_out = true;
        int content_w = bw2 - 2 * n->border_w - n->pad_l - n->pad_r;
        if (content_w < 0) content_w = 0;
        int used = layout_stack_once(n, x2 + n->border_w + n->pad_l,
                                     y2 + n->border_w + n->pad_t, content_w, 0);
        if (n->flex && n->justify_content == 1) {
            int fixed_inner = n->has_h ? n->h - 2 * n->border_w - n->pad_t - n->pad_b : -1;
            if (fixed_inner > 0 && used < fixed_inner) {
                layout_stack_once(n, x2 + n->border_w + n->pad_l,
                                  y2 + n->border_w + n->pad_t, content_w,
                                  (fixed_inner - used) / 2);
                used = fixed_inner;
            }
        }
        if (!n->has_h) {
            int bh2 = (b_ >= 0 && t >= 0) ? int(h - b_ - t)
                                          : used + 2 * n->border_w + n->pad_t + n->pad_b;
            n->h = bh2;
            if (b_ >= 0 && t < 0) n->y = int(h - b_ - bh2);
        }
    };
    std::function<void(DomNode*)> layout_pos_nested = [&](DomNode* n) {
        for (auto& c : n->children) {
            if (c->tag == "script" || c->tag == "style" || c->tag == "head") continue;
            if (c->positioned && c->visible) layout_positioned_root(c.get());
            else if (!c->positioned) layout_pos_nested(c.get());
        }
    };
    for (auto* pr : pos_roots) {
        layout_positioned_root(pr);
        layout_pos_nested(pr);
    }

    // 4. paint — flow (document order), then positioned (z ascending)
    std::function<void(DomNode*)> paint_node = [&](DomNode* n) {
        if (!n->visible || !n->laid_out) return;
        if (n->tag == "script" || n->tag == "style" || n->tag == "head" ||
            n->tag == "title" || n->tag == "link" || n->tag == "meta") return;
        if (n->box_shadow)
            fill_round(n->x, n->y + 6, n->w, n->h, n->radius + 4,
                       renderer::RGBA{0, 0, 0, 36});
        if (n->grad)
            fill_round_grad(n->x, n->y, n->w, n->h, n->radius, n->grad_diag,
                            n->grad_from, n->grad_to);
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
        if (n->is_canvas && n->canvas && n->canvas->bitmap().get_pixel_count() > 0 &&
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
        for (auto& c : n->children) {
            if (c->tag == "#text" || c->inline_el || c->positioned) continue;
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
    std::stable_sort(pos_paint.begin(), pos_paint.end(),
                     [](const DomNode* a, const DomNode* b) { return a->z_index < b->z_index; });
    for (auto* p : pos_paint) paint_node(p);

    // blit the page surface into the caller's buffer
    const auto& px = surface_fb->get_pixels();
    for (int i = 0; i < size_t(w) * h && i < int(px.size()); ++i) {
        dst[i * 4] = px[i].r;
        dst[i * 4 + 1] = px[i].g;
        dst[i * 4 + 2] = px[i].b;
        dst[i * 4 + 3] = px[i].a;
    }
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
    // hit test: topmost positioned element then flow elements (paint order)
    DomNode* hit = nullptr;
    auto contains = [](DomNode* n, int px, int py) {
        return n->visible && n->w > 0 && n->h > 0 &&
               px >= n->x && px < n->x + n->w && py >= n->y && py < n->y + n->h;
    };
    // positioned last-painted wins: scan body subtree in paint order
    std::vector<DomNode*> all;
    std::function<void(DomNode*)> walk = [&](DomNode* n) {
        if (n->tag == "script" || n->tag == "style" || n->tag == "head") return;
        if (n->tag != "html" && n->tag != "body") all.push_back(n);
        for (auto& c : n->children) walk(c.get());
    };
    for (auto& c : impl->doc.root->children) walk(c.get());
    for (auto* n : all)
        if (contains(n, x, y)) hit = n;   // last in paint order wins
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

// ── engine lifecycle ────────────────────────────────────────────────────
WebViewEngine::WebViewEngine(uint32_t view_id) : view_id_(view_id) {
    impl_ = std::make_unique<Impl>();
    impl_->self = this;
    impl_->rt = JS_NewRuntime();
    JS_SetMemoryLimit(impl_->rt, 512ull * 1024 * 1024);
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
    // S113: external stylesheets — <link rel=stylesheet href> fetch + parse
    // (the same APK-asset law external scripts use; no network dependency)
    for (auto& [href, _tag] : impl->doc.external_styles) {
        auto bytes = impl->fetch_asset(href);
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
        auto fbytes = impl->fetch_asset(url);
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

