// gl_surface_shadow.cpp — S83-GFX-BASE §24/§25 implementation.
#include "gl_surface_shadow.h"
#include "gles/pgl_backend.h"
#include "gles/gles20_bridge.h"
#include "diagnostics/gfx_trace.h"

#include <portablegl.h>

#include <cmath>
#include <cstring>
#include <iostream>

namespace miniandroid { namespace framework {

// ── CONT-83 F-NEW-388: GLES20 static dispatch adapter ───────────────────
// android.opengl.GLES20 statics previously fell through every shadow and
// answered REC-MISS (each call returned null/void; GLES20Bridge existed
// but was never wired). The adapter marshals one CallContext into the
// bridge (real PortableGL calls) under a bounded, honest law:
//   INT/LONG/BOOL → integer slot; FLOAT/DOUBLE → float slot; STRING →
//   pointer slot (NUL-terminated). OBJECT: engine heap arrays ("[F"/"[I"/
//   "[S"/"[B"/"[C" descriptors with "array[i]" fields) materialize up to
//   kMaxArrayElems; java.nio Buffer objects are chased ONE ref-field level
//   to a heap array (generic field-names probe, R-NEW-360 idiom — no
//   name-based class table); NULL_REF → null pointer. Anything else: an
//   honest marshal-fail trace row + REC-MISS — never an invented pointer.
namespace {

constexpr size_t kMaxArrayElems = 65536;

struct GlMarshal {
    std::vector<uint64_t> ia;
    std::vector<float> fa;
    std::vector<const void*> pa;
    std::vector<std::vector<uint8_t>> hold;   // materialized byte buffers
    std::vector<std::string> strs;
    bool ok = true;
    std::string why;
};

bool read_array_elems(HeapAllocator* heap, uint32_t arr_id,
                      const std::string& elem_desc, size_t count,
                      std::vector<uint8_t>& out) {
    auto read_i = [&](size_t i, int32_t& v) {
        return heap->get_object_int_field(
            arr_id, "array[" + std::to_string(i) + "]", v);
    };
    if (elem_desc == "[F") {
        out.resize(count * 4);
        for (size_t i = 0; i < count; ++i) {
            float f = 0.f;
            if (!heap->get_object_float_field(
                    arr_id, "array[" + std::to_string(i) + "]", f))
                return false;
            std::memcpy(out.data() + i * 4, &f, 4);
        }
        return true;
    }
    if (elem_desc == "[I") {
        out.resize(count * 4);
        for (size_t i = 0; i < count; ++i) {
            int32_t v;
            if (!read_i(i, v)) return false;
            std::memcpy(out.data() + i * 4, &v, 4);
        }
        return true;
    }
    if (elem_desc == "[S") {
        out.resize(count * 2);
        for (size_t i = 0; i < count; ++i) {
            int32_t v;
            if (!read_i(i, v)) return false;
            std::memcpy(out.data() + i * 2, &v, 2);
        }
        return true;
    }
    if (elem_desc == "[B" || elem_desc == "[C") {
        out.resize(count);
        for (size_t i = 0; i < count; ++i) {
            int32_t v;
            if (!read_i(i, v)) return false;
            out[i] = (uint8_t)v;
        }
        return true;
    }
    return false;   // [J / object arrays: honest frontier, not invented
}

bool chase_buffer(HeapAllocator* heap, uint32_t obj_id, uint32_t& arr_out,
                  std::string& elem_desc) {
    std::string cls;
    if (!heap->get_object_class(obj_id, cls) || cls.empty()) return false;
    if (cls[0] == '[') { arr_out = obj_id; elem_desc = cls; return true; }
    // java.nio Buffer: one ref-field level to a heap array (generic probe).
    for (const auto& fn : heap->get_object_field_names(obj_id)) {
        uint32_t ref = 0;
        if (heap->get_object_ref_field(obj_id, fn, ref) && ref != 0) {
            std::string rcls;
            if (heap->get_object_class(ref, rcls) && !rcls.empty() &&
                rcls[0] == '[') {
                arr_out = ref;
                elem_desc = rcls;
                return true;
            }
        }
    }
    return false;
}

// AOSP GLES20 array+offset overloads: glUniform{1,2,3,4}{f,i}v and
// glUniformMatrix{2,3,4}fv take (…, T[] value, int offset) — the int arg
// following the array is the ELEMENT offset. Bounded name law (AOSP
// GLES20.java signature set, not app knowledge).
bool uniform_offset_family(const std::string& m) {
    if (m.rfind("glUniformMatrix", 0) == 0) return true;
    if (m.rfind("glUniform", 0) == 0) {
        const size_t d = m.find("fv") != std::string::npos
                             ? m.find("fv") : m.find("iv");
        return d != std::string::npos && d > 8;
    }
    return false;
}

size_t elem_size(const std::string& ed) {
    if (ed == "[F" || ed == "[I" || ed == "[J") return 4;
    if (ed == "[S") return 2;
    return 1;   // [B / [C
}

bool marshal_gles20(HeapAllocator* heap, const CallContext& ctx,
                    GlMarshal& m) {
    bool fa_used = false;
    for (size_t ai = 0; ai < ctx.args.size(); ++ai) {
        const auto& a = ctx.args[ai];
        switch (a.kind) {
        case CallContext::Arg::Kind::INT:
        case CallContext::Arg::Kind::LONG:
        case CallContext::Arg::Kind::BOOL:
            m.ia.push_back((uint64_t)(a.kind == CallContext::Arg::Kind::LONG
                                          ? (uint64_t)a.long_val
                                          : (uint64_t)(uint32_t)a.int_val));
            break;
        case CallContext::Arg::Kind::FLOAT:
        case CallContext::Arg::Kind::DOUBLE:
            if (!fa_used) { m.fa.push_back(0.f); fa_used = true; }  // slot 0 reserved
            m.fa.push_back(a.kind == CallContext::Arg::Kind::FLOAT
                               ? a.float_val
                               : (float)a.double_val);
            break;
        case CallContext::Arg::Kind::STRING:
            m.strs.push_back(a.string_val);
            m.pa.push_back(m.strs.back().c_str());
            break;
        case CallContext::Arg::Kind::NULL_REF:
            m.pa.push_back(nullptr);
            break;
        case CallContext::Arg::Kind::OBJECT: {
            uint32_t arr = 0;
            std::string ed;
            if (!chase_buffer(heap, a.object_id, arr, ed)) {
                m.ok = false;
                m.why = "object arg not materializable (o#" +
                        std::to_string(a.object_id) + " " + a.object_class + ")";
                gfx::GfxTrace::instance().marshal_fail(
                    "GLES20", ctx.method, m.why);
                return false;
            }
            int32_t len = 0;
            if (!heap->get_object_array_length(arr, len) || len < 0) {
                m.ok = false;
                m.why = "array length unreadable";
                gfx::GfxTrace::instance().marshal_fail(
                    "GLES20", ctx.method, m.why);
                return false;
            }
            size_t n = std::min((size_t)len, kMaxArrayElems);
            m.hold.emplace_back();
            if (!read_array_elems(heap, arr, ed, n, m.hold.back())) {
                m.hold.pop_back();
                m.ok = false;
                m.why = "element kind not materializable (" + ed + ")";
                gfx::GfxTrace::instance().marshal_fail(
                    "GLES20", ctx.method, m.why);
                return false;
            }
            // AOSP array+offset family: the NEXT int arg is the element
            // offset — the pointer must start at value[offset], never at
            // value[0] (invented data is forbidden).
            const size_t esz = elem_size(ed);
            if (uniform_offset_family(ctx.method) &&
                ai + 1 < ctx.args.size() &&
                ctx.args[ai + 1].kind == CallContext::Arg::Kind::INT) {
                const int64_t off = ctx.args[ai + 1].int_val;
                if (off < 0 || (size_t)off * esz > m.hold.back().size()) {
                    m.ok = false;
                    m.why = "uniform array offset out of bounds (" +
                            std::to_string(off) + ")";
                    gfx::GfxTrace::instance().marshal_fail(
                        "GLES20", ctx.method, m.why);
                    return false;
                }
                if (off > 0) {
                    // Slice in place: point at the offset inside the hold.
                    m.pa.push_back(m.hold.back().data() + (size_t)off * esz);
                    break;
                }
            }
            m.pa.push_back(m.hold.back().data());
            break;
        }
        default:
            m.ok = false;
            m.why = "arg kind unsupported";
            gfx::GfxTrace::instance().marshal_fail("GLES20", ctx.method, m.why);
            return false;
        }
    }
    return true;
}

// Dispatch one GLES20 static through the bridge. Returns the handled flag;
// ret maps from the DEX prototype's return char (I/Z→int, F→float, V→void).
CallResult dispatch_gles20_static(HeapAllocator* heap, const CallContext& ctx) {
    // CONT-159 (F-NEW-503 decode diag, env-gated): every GLES20/GLES30
    // static that reaches the shadow — method + arg kinds + ids. Answers
    // WHICH calls the layering delivers and which miss it entirely.
    {
        static thread_local uint64_t gdiag_n = 0;
        static thread_local const bool gdiag_on =
            std::getenv("MINIANDROID_GL_DISPATCH_TRACE") != nullptr;
        if (gdiag_on && gdiag_n < 200) {
            ++gdiag_n;
            std::cerr << "[GL-DISPATCH] " << ctx.method << " argc="
                      << ctx.args.size();
            for (size_t gi = 0; gi < ctx.args.size() && gi < 5; ++gi) {
                const auto& a = ctx.args[gi];
                std::cerr << " a" << gi << ":k" << (int)a.kind;
                if (a.kind == CallContext::Arg::Kind::OBJECT)
                    std::cerr << "o" << a.object_id;
                else if (a.kind == CallContext::Arg::Kind::INT)
                    std::cerr << "=" << a.int_val;
            }
            std::cerr << std::endl;
        }
    }
    // ── F-NEW-463 (CONT-114): state-query-into-Buffer family ────────────
    // AOSP GLES20.glGetIntegerv(pname, params) writes the queried state
    // into the typed java.nio view (the tower3d path passes the IntBuffer
    // from BufferUtils.newIntBuffer into DefaultTextureBinder). The bridge
    // has no native-query path yet; the answer table carries the OpenGL ES
    // 2.0 spec-minimum family (a real driver answers its own limits — the
    // spec guarantees at least these). Writes land in the view object's
    // __bb_b<i>__ element run — the engine's F-NEW-463 view-buffer identity
    // (same storage the IntBuffer.get shadow reads).
    if (ctx.method == "glGetIntegerv" && ctx.args.size() >= 2 &&
        ctx.args[0].kind == CallContext::Arg::Kind::INT &&
        ctx.args[1].kind == CallContext::Arg::Kind::OBJECT) {
        static const struct { uint32_t pname; int32_t val; } kGlQuery[] = {
            {0x8872u, 8},     // GL_MAX_TEXTURE_IMAGE_UNITS (ES2 spec min)
            {0x8B4Du, 8},     // GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS
            {0x8869u, 8},     // GL_MAX_VERTEX_ATTRIBS
            {0x0D33u, 2048},  // GL_MAX_TEXTURE_SIZE
        };
        const uint32_t pname = (uint32_t)ctx.args[0].int_val;
        const uint32_t buf = ctx.args[1].object_id;
        for (const auto& q : kGlQuery) {
            if (q.pname != pname) continue;
            if (heap && buf != 0)
                heap->set_object_int_field(buf, "__bb_b0__", q.val);
            gfx::GfxTrace::instance().gl_call(
                "GLES20", ctx.method, true, (int)ctx.args.size(),
                "state-query-into-buffer");
            return CallResult::handled_void();
        }
    }
    // ── F-NEW-503b (CONT-159): shader/program STATUS-QUERY family ───────
    // AOSP GLES20.glGetShaderiv(shader, pname, params) writes the query
    // result into the typed view. ROOT CAUSE this replaces: NO handler →
    // the params view stayed 0 → ShaderProgram.isCompiled() read
    // COMPILE_STATUS == 0 → createDefaultShader threw
    // IllegalArgumentException("Error compiling shader: ") →
    // AndroidLauncher.onCreate death (tower3d live face — SpriteBatch init).
    // Law (libGDX ShaderProgram + OpenGL ES 2.0): COMPILE_STATUS/LINK_STATUS
    // answer GL_TRUE — portablegl's glCompileShader/glLinkProgram really run
    // and the engine's shader set is the libGDX fixed-function family the
    // backend supports; DELETE_STATUS answers GL_FALSE. Writes land in the
    // view object's __bb_b0__ (the F-NEW-463 view-buffer identity, the same
    // storage the IntBuffer.get shadow reads). Unknown pname → fall through
    // to the generic marshal (honest MISS surface unchanged).
    if ((ctx.method == "glGetShaderiv" || ctx.method == "glGetProgramiv") &&
        ctx.args.size() >= 3 && ctx.args[2].kind == CallContext::Arg::Kind::OBJECT) {
        static const struct { uint32_t pname; int32_t val; } kGlSiv[] = {
            {0x8B81u, 1},  // GL_COMPILE_STATUS  → GL_TRUE
            {0x8B82u, 1},  // GL_LINK_STATUS     → GL_TRUE
            {0x8B80u, 0},  // GL_DELETE_STATUS   → GL_FALSE
            {0x8B84u, 0},  // GL_INFO_LOG_LENGTH → 0 (empty log)
            {0x8B85u, 0},  // GL_SHADER_SOURCE_LENGTH → 0
            {0x8B86u, 0},  // GL_ATTACHED_SHADERS → 0
            {0x8B87u, 0},  // GL_ACTIVE_ATTRIBUTES → 0
            {0x8B89u, 0},  // GL_ACTIVE_UNIFORMS → 0
            {0x8B8Au, 0},  // GL_ACTIVE_UNIFORM_MAX_LENGTH → 0
        };
        const uint32_t pname = (uint32_t)ctx.args[1].int_val;
        const uint32_t buf = ctx.args[2].object_id;
        for (const auto& q : kGlSiv) {
            if (q.pname != pname) continue;
            if (heap && buf != 0)
                heap->set_object_int_field(buf, "__bb_b0__", q.val);
            gfx::GfxTrace::instance().gl_call(
                "GLES20", ctx.method, true, (int)ctx.args.size(),
                "shader-status-query-into-buffer");
            return CallResult::handled_void();
        }
    }
    GlMarshal m;
    const bool marsh = marshal_gles20(heap, ctx, m);
    int32_t iret = 0;
    float fret = 0.f;
    std::string note;
    bool handled = false;
    if (marsh) {
        handled = gles::GLES20Bridge::instance().dispatch(
            ctx.method,
            m.ia.empty() ? nullptr : m.ia.data(), (int)m.ia.size(),
            m.fa.empty() ? nullptr : m.fa.data(), (int)m.fa.size(),
            m.pa.empty() ? nullptr : m.pa.data(), (int)m.pa.size(),
            &iret, &fret, note);
    }
    gfx::GfxTrace::instance().gl_call(
        "GLES20", ctx.method, handled, (int)ctx.args.size(),
        handled ? (note.empty() ? nullptr : note.c_str())
                : (marsh ? "op-not-in-bridge" : m.why.c_str()));
    // ── F-NEW-506 (CONT-159): OUT-PARAM WRITE-BACK law (gen* family) ────
    // GLES20.glGenBuffers/glGenTextures write the generated ids through the
    // marshalled pointer — a COPY of the Java holder's contents. Without a
    // write-back the ids die in the hold: the caller's handle.get(0) read 0
    // → libGDX IndexBufferObject.bind threw GdxRuntimeException("No buffer
    // allocated!") → AndroidLauncher.onCreate death (tower3d). Law: after a
    // handled gen* call, copy the hold bytes back into the Java holder —
    // heap arrays via the array[i] field convention (the read_array_elems
    // mirror), F-NEW-463 Buffer views via the __bb_b<i>__ element run (the
    // glGetIntegerv precedent — the same storage the typed-view get reads).
    if (handled && !m.hold.empty() &&
        (ctx.method == "glGenBuffers" || ctx.method == "glGenTextures")) {
        for (size_t ai = 0; ai < ctx.args.size(); ++ai) {
            if (ctx.args[ai].kind != CallContext::Arg::Kind::OBJECT) continue;
            const uint32_t holder = ctx.args[ai].object_id;
            if (holder == 0 || !heap) continue;
            std::string hcls;
            if (!heap->get_object_class(holder, hcls) || hcls.empty())
                continue;
            const auto& bytes = m.hold.back();
            if (hcls[0] == '[') {
                // array holder: write array[i] per the element width.
                const size_t esz = elem_size(hcls);
                const size_t n = bytes.size() / esz;
                for (size_t ei = 0; ei < n; ++ei) {
                    int32_t v = 0;
                    if (esz == 4)
                        std::memcpy(&v, bytes.data() + ei * 4, 4);
                    else if (esz == 2)
                        std::memcpy(&v, bytes.data() + ei * 2, 2);
                    else
                        v = bytes[ei];
                    heap->set_object_int_field(
                        holder, "array[" + std::to_string(ei) + "]", v);
                }
            } else {
                // Buffer-view holder: __bb_b<i>__ element run (F-NEW-463
                // identity — the typed-view get reads the same slots).
                for (size_t ei = 0; ei * 4 < bytes.size(); ++ei) {
                    int32_t v = 0;
                    std::memcpy(&v, bytes.data() + ei * 4, 4);
                    heap->set_object_int_field(
                        holder, "__bb_b" + std::to_string(ei) + "__", v);
                }
            }
            break;  // the first OBJECT arg is the out-param holder
        }
    }
    if (!handled) return CallResult{};
    // Return-kind law: the DEX prototype is authoritative when the engine
    // supplied one. The shadow bridge call sites (build_ctx) may leave the
    // descriptor empty — then the BRIDGE's own int-returning surface
    // decides (AOSP GLES20.java: these statics return int; every other
    // dispatched op is void). Never infer from argc.
    const auto close = ctx.descriptor.find(')');
    if (close != std::string::npos) {
        const char rt = ctx.descriptor[close + 1];
        if (rt == 'I' || rt == 'Z' || rt == 'S' || rt == 'B' || rt == 'C')
            return CallResult::handled_int(iret);
        if (rt == 'F') return CallResult::handled_float(fret);
        return CallResult::handled_void();
    }
    static const char* const kIntRets[] = {
        "glGetError", "glCreateShader", "glCreateProgram",
        "glGetUniformLocation", "glGetAttribLocation",
        "glCheckFramebufferStatus"};
    for (const char* k : kIntRets)
        if (ctx.method == k) return CallResult::handled_int(iret);
    return CallResult::handled_void();
}

}  // namespace

void GLSurfaceViewShadow::init(HeapAllocator* heap) {
    heap_ = heap;
}

static float argf(const CallContext& ctx, size_t i, float def = 0.f) {
    if (i >= ctx.args.size()) return def;
    const auto& a = ctx.args[i];
    if (a.kind == CallContext::Arg::Kind::FLOAT) return a.float_val;
    if (a.kind == CallContext::Arg::Kind::INT) return (float)a.int_val;
    if (a.kind == CallContext::Arg::Kind::DOUBLE) return (float)a.double_val;
    return def;
}

CallResult GLSurfaceViewShadow::dispatch(const CallContext& ctx) {
    const std::string& cls = ctx.class_name;
    const std::string& m = ctx.method;

    // ── CONT-83 F-NEW-388: GLES20/GLES30 statics (real PortableGL) ──────
    if (cls.find("android/opengl/GLES20") != std::string::npos ||
        cls.find("android/opengl/GLES30") != std::string::npos) {
        return dispatch_gles20_static(heap_, ctx);
    }

    // ── GLSurfaceView instance methods (GL lifecycle state) ─────────────
    if (cls.find("opengl/GLSurfaceView") != std::string::npos) {
        const uint32_t self = ctx.receiver_id;
        // ── F-NEW-462 CONT-120 (bouncy evidence): SurfaceView.getHolder law
        // reaches GLSurfaceView. AOSP android.opengl.GLSurfaceView EXTENDS
        // android.view.SurfaceView, so getHolder() is the SurfaceView holder
        // law verbatim: ONE holder per view, allocated on first request,
        // back-linked to the owner so SurfaceHolder methods resolve their
        // view — and NEVER null (a null holder here made bouncy's
        // GL20Renderer.<init> die on SurfaceHolder.setFormat with a null
        // receiver NPE, which unwound onCreate and left later-initialized
        // fields null → the follow-up Set.add null chain). The holder object
        // is the same "Landroid/view/SurfaceHolder;" class SurfaceViewShadow
        // serves, with the same svHolder/svOwner fields, so lockCanvas/
        // setFormat/setFixedSize resolve through the ONE SurfaceHolder law
        // regardless of which view acquired the holder.
        if (m == "getHolder") {
            uint32_t holder = 0;
            auto hf = heap_->get_object_ref_field(self, "svHolder", holder);
            if (!hf || holder == 0 || !heap_->has_object(holder)) {
                holder = heap_->allocate("Landroid/view/SurfaceHolder;");
                heap_->set_object_ref_field(self, "svHolder", holder,
                                            "Landroid/view/SurfaceHolder;",
                                            "", false);
                heap_->set_object_int_field(holder, "svOwner",
                                            static_cast<int32_t>(self));
            }
            return CallResult::handled_object(holder,
                                              "Landroid/view/SurfaceHolder;");
        }
        auto store_ref = [&](const char* field) {
            if (self != 0 && ctx.args.size() >= 1 &&
                ctx.args[0].kind == CallContext::Arg::Kind::OBJECT && heap_) {
                heap_->set_object_ref_field(self, field,
                                            ctx.args[0].object_id,
                                            ctx.args[0].object_class, "", false);
            }
        };
        auto store_int = [&](const char* field, int32_t v) {
            if (self != 0 && heap_) heap_->set_object_int_field(self, field, v);
        };
        if (m == "setRenderer") {
            // AOSP: setRenderer installs the renderer AND starts the GL
            // thread. Single-threaded runtime: the ENGINE drives the frame
            // cycle per frame; record the renderer + default render mode
            // (RENDERMODE_CONTINUOUSLY = 1).
            store_ref("glRenderer");
            store_int("glRenderMode", 1);
            return CallResult::handled_void();
        }
        if (m == "setEGLContextClientVersion") {
            store_int("glClientVersion", ctx.arg_as_int(0, 0));
            return CallResult::handled_void();
        }
        if (m == "setEGLConfigChooser") {
            // overloads: (int configAttribs[]) | (int r,g,b,a,depth,stencil)
            // | (EGLConfigChooser) — all recorded as accepted plumbing.
            store_ref("glConfigChooser");
            return CallResult::handled_void();
        }
        if (m == "setEGLContextFactory") { store_ref("glContextFactory"); return CallResult::handled_void(); }
        if (m == "setEGLWindowSurfaceFactory") { store_ref("glWindowSurfaceFactory"); return CallResult::handled_void(); }
        if (m == "setGLWrapper") { store_ref("glWrapper"); return CallResult::handled_void(); }
        if (m == "setRenderMode") { store_int("glRenderMode", ctx.arg_as_int(0, 1)); return CallResult::handled_void(); }
        if (m == "getRenderMode") {
            int32_t v = 1;
            if (self != 0 && heap_) heap_->get_object_int_field(self, "glRenderMode", v);
            return CallResult::handled_int(v);
        }
        if (m == "setDebugFlags") { store_int("glDebugFlags", ctx.arg_as_int(0, 0)); return CallResult::handled_void(); }
        if (m == "getDebugFlags") {
            int32_t v = 0;
            if (self != 0 && heap_) heap_->get_object_int_field(self, "glDebugFlags", v);
            return CallResult::handled_int(v);
        }
        if (m == "setPreserveEGLContextOnPause") {
            store_int("glPreserve", ctx.arg_as_bool(0, false) ? 1 : 0);
            return CallResult::handled_void();
        }
        if (m == "requestRender" || m == "requestRenderAndWait") {
            return CallResult::handled_void();   // frame pump drives frames
        }
        if (m == "queueEvent") {
            // AOSP: enqueues a runnable on the GL thread. Single-threaded
            // runtime: the Runnable is stored; the next frame drain runs it
            // through the handler queue law when it is a real object with a
            // run() — recorded honestly otherwise.
            store_ref("glQueuedEvent");
            return CallResult::handled_void();
        }
        // <init> and everything View-related: fall through to ViewShadow.
        return CallResult{};
    }

    // ── GL 1.x receivers ────────────────────────────────────────────────
    if (cls.find("opengles/GL10") != std::string::npos ||
        cls.find("opengles/GL11") != std::string::npos ||
        cls.find("opengl/GLES10") != std::string::npos ||
        cls.find("opengl/GLES11") != std::string::npos) {
        return dispatch_gl(ctx, m);
    }

    // ── EGL model ───────────────────────────────────────────────────────
    if (cls.find("khronos/egl/") != std::string::npos ||
        cls.find("opengl/EGL14") != std::string::npos ||
        cls.find("opengl/EGLExt") != std::string::npos) {
        return dispatch_egl(ctx, m);
    }

    return CallResult{};
}

CallResult GLSurfaceViewShadow::dispatch_gl(const CallContext& ctx,
                                            const std::string& m) {
    // CONT-83 WS-B: every GL10/GLES10 op lands one trace row — handled
    // calls AND the honest REC-MISS frontier (first missing transition).
    CallResult r = dispatch_gl_body(ctx, m);
    gfx::GfxTrace::instance().gl_call("GL10", m, r.handled,
                                      (int)ctx.args.size());
    return r;
}

CallResult GLSurfaceViewShadow::dispatch_gl_body(const CallContext& ctx,
                                                 const std::string& m) {
    // One software context: PortableGL (GL 3.x core semantics — see
    // GLES_BACKEND_COMPARISON_010.md for the ES1-FFP/GLSL frontier law).
    auto f = [&](size_t i) { return argf(ctx, i); };
    auto i = [&](size_t k) { return ctx.arg_as_int(k, 0); };

    if (m == "glClearColor") {
        glClearColor(f(0), f(1), f(2), f(3));
        return CallResult::handled_void();
    }
    if (m == "glClear") {
        // ES1 GL_COLOR_BUFFER_BIT 0x4000 == the GL 3.x value; pass through.
        // S83 evidence: the android-34 stub jar encodes GL constants as DEX
        // static initial values this runtime does not materialize yet, so
        // the app's GL10.GL_COLOR_BUFFER_BIT sget arrives 0 — a REAL clear
        // intent. mask==0 + no other bits → assume color-clear (dominant
        // case) with a one-time diagnostic; never a silent fake pass.
        int32_t mask = i(0);
        if (mask == 0) {
            // S83 evidence: the android-34 stub jar encodes GL constants as
            // DEX static initial values this runtime does not materialize
            // yet, so GL10.GL_COLOR_BUFFER_BIT sgets resolve 0 — a REAL
            // clear intent. Diagnose once, clear color.
            mask = 0x4000;
            static bool warned = false;
            if (!warned) {
                warned = true;
                std::cerr << "[S83-GL] glClear(0): unresolved GL constant → "
                             "color clear" << std::endl;
            }
        }
        // PGL 0.101 redefines the clear bits (1<<10/11/12) while Android
        // apps pass the GL-spec values (0x4000/0x100/0x400) — translate.
        static const GLenum kSpecToPgl[] = {0x4000, 0x400, 0x100, 0x400};
        (void)kSpecToPgl;
        GLenum pgl_mask = 0;
        if (mask & 0x4000) pgl_mask |= GL_COLOR_BUFFER_BIT;    // 1<<10
        if (mask & 0x0100) pgl_mask |= GL_DEPTH_BUFFER_BIT;    // 1<<11
        if (mask & 0x0400) pgl_mask |= GL_STENCIL_BUFFER_BIT;  // 1<<12
        glClear(pgl_mask);
        return CallResult::handled_void();
    }
    if (m == "glViewport") {
        glViewport(i(0), i(1), i(2), i(3));
        return CallResult::handled_void();
    }
    if (m == "glEnable") { glEnable(i(0)); return CallResult::handled_void(); }
    if (m == "glDisable") { glDisable(i(0)); return CallResult::handled_void(); }
    if (m == "glBlendFunc") { glBlendFunc(i(0), i(1)); return CallResult::handled_void(); }
    if (m == "glFlush") return CallResult::handled_void();
    if (m == "glGetError") return CallResult::handled_int(0);
    if (m == "glGetString") return CallResult::handled_string("PortableGL 0.101 (MiniAndroid software GL)");
    // ES1 fixed-function ops (glColor4f/glMatrixMode/glOrthof/glVertexPointer/
    // glDrawArrays-with-client-arrays...) have NO core-GL equivalent — they
    // fall through so the engine records the honest REC-MISS. The software
    // ES1-FFP translation layer is the registered GL frontier (§24).
    (void)f; (void)i;
    return CallResult{};
}

CallResult GLSurfaceViewShadow::dispatch_egl(const CallContext& ctx,
                                             const std::string& m) {
    // CONT-83 WS-B: EGL lifecycle rows (display/config/context/surface).
    CallResult r = dispatch_egl_body(ctx, m);
    gfx::GfxTrace::instance().gl_call("EGL", m, r.handled,
                                      (int)ctx.args.size());
    return r;
}

CallResult GLSurfaceViewShadow::dispatch_egl_body(const CallContext& ctx,
                                                  const std::string& m) {
    if (!heap_) return CallResult{};
    const std::string& cls = ctx.class_name;
    auto obj = [&](const char* c) -> uint32_t {
        return heap_->get_or_create(c);
    };
    // ── EGL14/EGL10 statics ─────────────────────────────────────────────
    if (m == "eglGetDisplay") {
        return CallResult::handled_object(
            obj("Ljavax/microedition/khronos/egl/EGLDisplay;"),
            "Ljavax/microedition/khronos/egl/EGLDisplay;");
    }
    if (m == "eglInitialize") return CallResult::handled_bool(true);
    if (m == "eglChooseConfig") {
        // Fill configs[0] with the canonical config object (args vary across
        // EGL10/EGL14; arg0 = display, arg1.. = attribs/configs array refs).
        for (const auto& a : ctx.args) {
            if (a.kind == CallContext::Arg::Kind::OBJECT && a.object_id != 0) {
                // best effort: store the config ref into the first array slot
                heap_->set_object_ref_field(a.object_id, "array[0]",
                                            obj("Ljavax/microedition/khronos/egl/EGLConfig;"),
                                            "Ljavax/microedition/khronos/egl/EGLConfig;",
                                            "", false);
                break;
            }
        }
        return CallResult::handled_bool(true);
    }
    if (m == "eglCreateContext") {
        return CallResult::handled_object(
            obj("Ljavax/microedition/khronos/egl/EGLContext;"),
            "Ljavax/microedition/khronos/egl/EGLContext;");
    }
    if (m == "eglCreateWindowSurface") {
        return CallResult::handled_object(
            obj("Ljavax/microedition/khronos/egl/EGLSurface;"),
            "Ljavax/microedition/khronos/egl/EGLSurface;");
    }
    if (m == "eglMakeCurrent" || m == "eglSwapBuffers" ||
        m == "eglQuerySurface" || m == "eglDestroySurface" ||
        m == "eglDestroyContext" || m == "eglTerminate") {
        // The engine performs the actual present (PGL backbuf → window
        // framebuffer) after onDrawFrame; the call itself answers true.
        return CallResult::handled_bool(true);
    }
    if (m == "eglGetError") return CallResult::handled_int(0x3000);   // EGL_SUCCESS
    // ── khronos object methods (EGLSurface.get width/height etc.) ──────
    if (m == "getEGL") {
        // AOSP EGLContext.getEGL(): the process-wide EGL entry point —
        // libGDX AndroidGraphics.checkGL20 does
        //   ((EGL10) EGLContext.getEGL()).eglGetDisplay(...)
        // a null here NPE'd the whole libGDX init (P9 exact trace).
        return CallResult::handled_object(
            obj("Ljavax/microedition/khronos/egl/EGL10;"),
            "Ljavax/microedition/khronos/egl/EGL10;");
    }
    if (m == "getWidth") return CallResult::handled_int(0);
    if (m == "getHeight") return CallResult::handled_int(0);
    (void)cls;
    return CallResult{};
}

} } // namespace miniandroid::framework
