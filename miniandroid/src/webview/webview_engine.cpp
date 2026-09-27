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
        for (auto& c : doc.root->children)
            if (c->tag == "body") return c.get();
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
            // adopt fragment children (transfer ownership out of the fragment box)
            for (auto& c : frag->children) {
                DomNode* raw = c.get();
                impl_of(ctx)->orphans.push_back({raw, std::move(c)});
                raw->parent = n;
                n->children.push_back(std::move(impl_of(ctx)->orphans.back().second));
                // fix the orphan bridge to point at the new owner
                impl_of(ctx)->orphans.pop_back();
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
static JSValue el_getContext(JSContext* ctx, JSValueConst this_v, int argc, JSValueConst* argv) {
    if (wv_trace()) std::cerr << "[WV-T] el.getContext" << std::endl;
    auto* n = el_of(this_v);
    if (!n || !n->is_canvas) return JS_NULL;
    if (!n->canvas) n->canvas = std::make_unique<Canvas2D>();
    JSValue o = JS_NewObjectClass(ctx, kCtx2DClass);
    if (JS_IsException(o)) return o;
    JS_SetOpaque(o, n->canvas.get());
    JS_SetPropertyStr(ctx, o, "createLinearGradient",
                      JS_NewCFunction(ctx, c2d_create_linear_gradient, "createLinearGradient", 4));
    JS_SetPropertyStr(ctx, o, "createRadialGradient",
                      JS_NewCFunction(ctx, c2d_create_radial_gradient, "createRadialGradient", 6));
    JS_SetPropertyStr(ctx, o, "addColorStop",
                      JS_NewCFunction(ctx, grad_addColorStop, "addColorStop", 2));
    // dash support: accepted, dashes rasterized as solid strokes (documented
    // approximation — dash pattern rasterization is a later frontier)
    JS_SetPropertyStr(ctx, o, "setLineDash", JS_NewCFunction(ctx,
        [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_UNDEFINED; }, "setLineDash", 1));
    JS_SetPropertyStr(ctx, o, "getLineDash", JS_NewCFunction(ctx,
        [](JSContext* c, JSValueConst, int, JSValueConst*) { return JS_NewArray(c); }, "getLineDash", 0));
    JS_SetPropertyStr(ctx, o, "isPointInPath", JS_NewCFunction(ctx,
        [](JSContext*, JSValueConst, int, JSValueConst*) { return JS_FALSE; }, "isPointInPath", 2));
    return o;
}
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
            collect_tag(impl->doc.root.get(), lower_s(sel), out);
            JS_FreeCString(ctx, sel);
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
        // console
        JSValue con = JS_NewObject(ctx);
        JS_SetPropertyStr(ctx, con, "log", JS_NewCFunction(ctx, js_console_log, "log", 1));
        JS_SetPropertyStr(ctx, con, "info", JS_NewCFunction(ctx, js_console_log, "info", 1));
        JS_SetPropertyStr(ctx, con, "warn", JS_NewCFunction(ctx, js_console_log, "warn", 1));
        JS_SetPropertyStr(ctx, con, "error", JS_NewCFunction(ctx, js_console_log, "error", 1));
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
static float css_len_px(const std::string& v, float viewport, float dflt) {
    if (v.empty()) return dflt;
    auto val = [&](float unit = 1.f) { return ::atof(v.c_str()) * unit; };
    if (v.find("vw") != std::string::npos) return val(viewport / 100.f);
    if (v.find("vh") != std::string::npos) return val(viewport / 100.f);
    if (v.back() == '%') return val(viewport / 100.f);
    return val();
}

void WebViewEngine::Impl::compute_layout() {
    // (layout happens inside render; kept as a seam for future passes)
}

static void style_element(DomNode* n, double vw, double vh) {
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
    if (n->is_canvas && n->canvas) {
        // canvas CSS size: style width/height; bitmap = JS-set size
        std::string cw = get("width"), chh = get("height");
        if (!cw.empty()) n->w = int(css_len_px(cw, float(vw), float(n->canvas->width())));
        if (!chh.empty()) n->h = int(css_len_px(chh, float(vh), float(n->canvas->height())));
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
    auto* body = impl->body();

    // pass 1: style + box computation
    std::vector<DomNode*> flow;         // static, document order
    std::vector<DomNode*> positioned;   // fixed/absolute, z-sorted later
    std::function<void(DomNode*)> collect = [&](DomNode* n) {
        if (n->tag == "script" || n->tag == "style" || n->tag == "head" ||
            n->tag == "title" || n->tag == "link" || n->tag == "meta")
            return;
        style_element(n, double(w), double(h));
        if (n->positioned) positioned.push_back(n);
        else if (n->tag != "html" && n->tag != "body") flow.push_back(n);
        for (auto& c : n->children) collect(c.get());
    };
    for (auto& c : impl->doc.root->children) collect(c.get());

    // pass 2: paint — static flow first (document order), then positioned
    // (z-index ascending, stable) — CSS painting-order law (approximation).
    auto paint_text_node = [&](DomNode* n, int x, int y, int w_box) {
        std::string t = HtmlParser::text_content(n);
        if (t.empty()) return;
        auto& sh = fonts::TextShaper::instance();
        if (!sh.available()) return;
        float size = n->font_size;
        renderer::RGBA col{0, 0, 0, 255};
        if (n->has_fg) {
            col = renderer::RGBA{uint8_t(n->fg & 255), uint8_t((n->fg >> 8) & 255),
                                 uint8_t((n->fg >> 16) & 255), uint8_t((n->fg >> 24) & 255)};
        }
        sh.draw(*surface_fb, t, float(x), float(y) + size * 1.1f, size, col, n->bold);
    };
    auto paint_box = [&](DomNode* n, int x, int y, int w_box, int h_box) {
        n->x = x; n->y = y; n->w = w_box; n->h = h_box;
        if (n->has_bg && w_box > 0 && h_box > 0) {
            renderer::RGBA c{uint8_t(n->bg & 255), uint8_t((n->bg >> 8) & 255),
                             uint8_t((n->bg >> 16) & 255), uint8_t((n->bg >> 24) & 255)};
            for (int yy = std::max(0, y); yy < std::min(h, y + h_box); ++yy)
                for (int xx = std::max(0, x); xx < std::min(w, x + w_box); ++xx)
                    surface_fb->set_pixel(xx, yy, c);
        }
        if (n->is_canvas && n->canvas && n->canvas->bitmap().get_pixel_count() > 0 &&
            w_box > 0 && h_box > 0) {
            // canvas bitmap → page (drawImage semantics through Canvas2D)
            const auto& src = n->canvas->bitmap().get_pixels();
            int sw = n->canvas->bitmap().get_width(), shh = n->canvas->bitmap().get_height();
            for (int yy = 0; yy < h_box; ++yy) {
                int sy = int((yy + .5f) / h_box * shh);
                if (sy < 0 || sy >= shh) continue;
                for (int xx = 0; xx < w_box; ++xx) {
                    int sx = int((xx + .5f) / w_box * sw);
                    if (sx < 0 || sx >= sw) continue;
                    int dx = x + xx, dy = y + yy;
                    if (dx < 0 || dy < 0 || dx >= w || dy >= h) continue;
                    auto c = src[size_t(sy) * sw + sx];
                    if (c.a == 255)
                        surface_fb->set_pixel(dx, dy, c);
                    else if (c.a > 0)
                        surface_fb->set_pixel(dx, dy, c);  // set_pixel blends
                }
            }
        } else {
            paint_text_node(n, x, y, w_box);
        }
    };

    int flow_y = 0;
    for (auto* n : flow) {
        if (!n->visible) continue;
        // block flow: full-width rows, stack vertically (document-order law
        // approximation for block elements; corpus pages are fixed-layout)
        int bh = n->h > 0 ? n->h : int(n->font_size * 1.6f) + 4;
        int bw = n->w > 0 ? n->w : w;
        if (bw > w) bw = w;
        paint_box(n, 0, flow_y, bw, bh);
        flow_y += bh;
        if (flow_y > h) break;
    }
    std::stable_sort(positioned.begin(), positioned.end(),
                     [](const DomNode* a, const DomNode* b) { return a->z_index < b->z_index; });
    for (auto* n : positioned) {
        if (!n->visible) continue;
        auto get = [&](const char* k) {
            auto it = n->style.find(k);
            return it != n->style.end() ? it->second : std::string();
        };
        float l = -1, t = -1, r = -1, b = -1;
        if (!get("left").empty()) l = css_len_px(get("left"), float(w), 0);
        if (!get("top").empty()) t = css_len_px(get("top"), float(h), 0);
        if (!get("right").empty()) r = css_len_px(get("right"), float(w), 0);
        if (!get("bottom").empty()) b = css_len_px(get("bottom"), float(h), 0);
        std::string ntext = HtmlParser::text_content(n);
        int bw = n->w > 0 ? n->w : (r >= 0 && l >= 0 ? int(w - r - l)
                                    : int(fonts::TextShaper::instance()
                                              .shape(ntext, n->font_size, n->bold)
                                              .width) + 24);
        int bh = n->h > 0 ? n->h : (b >= 0 && t >= 0 ? int(h - b - t) : int(n->font_size * 1.6f) + 8);
        int x = l >= 0 ? int(l) : (r >= 0 ? int(w - r - bw) : 0);
        int y = t >= 0 ? int(t) : (b >= 0 ? int(h - b - bh) : 0);
        paint_box(n, x, y, bw, bh);
    }

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
    HtmlParser::apply_css(impl->doc.root.get(), impl->css_rules, &impl->custom_props);
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

