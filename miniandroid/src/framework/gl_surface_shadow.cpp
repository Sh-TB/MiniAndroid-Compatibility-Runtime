// gl_surface_shadow.cpp — S83-GFX-BASE §24/§25 implementation.
#include "gl_surface_shadow.h"
#include "gles/pgl_backend.h"

#include <portablegl.h>

#include <cmath>
#include <cstring>
#include <iostream>

namespace miniandroid { namespace framework {

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

    // ── GLSurfaceView instance methods (GL lifecycle state) ─────────────
    if (cls.find("opengl/GLSurfaceView") != std::string::npos) {
        const uint32_t self = ctx.receiver_id;
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
