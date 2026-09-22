// gl_surface_shadow.h — S83-GFX-BASE §24/§25: GLSurfaceView + EGL model.
//
// ─────────────────────────────────────────────────────────────────────────
// LAW (AOSP android.opengl.GLSurfaceView + android.opengl.EGL14/GLSurfaceView
// EGL wiring; Anbox/emugl guest→host law and SwiftShader CPU law per S83
// §24: GPU is NOT a prerequisite — one deterministic software path must
// exist, and PortableGL IS that path for MiniAndroid).
//
// What this shadow owns:
//   * GLSurfaceView GL-specific methods: setRenderer + the EGL plumbing
//     setters (recorded state; the ENGINE drives the actual frame cycle:
//     onSurfaceCreated → onSurfaceChanged → onDrawFrame → present).
//     Everything else (hierarchy, measure/layout, visibility) falls through
//     to the ViewShadow catch-all — GLSurfaceView IS-A View.
//   * GL10/GL11/GLES10/GLES11 method routing into the PortableGL software
//     context (the SAME context the GLES20 bridge drives — one GL, one
//     framebuffer). ES1 fixed-function maps onto PGL 2.1 fixed-function.
//   * EGL object model: EGLDisplay/EGLConfig/EGLContext/EGLSurface as real
//     heap objects; egl* statics as state-honest operations. eglSwapBuffers
//     answers true (the engine performs the actual present into the
//     window framebuffer after onDrawFrame).
//
// F-NEW-157 (libGDX createGLSurfaceView NPE) root cause: GLSurfaceView had
// NO shadow at all — construction fell through every layer and the
// AndroidGraphics chain unwound. This shadow gives the class a real
// lifecycle surface.
// ─────────────────────────────────────────────────────────────────────────
#pragma once

#include "shadow_registry.h"

#include <string>

namespace miniandroid { namespace framework {

class GLSurfaceViewShadow : public Shadow {
public:
    std::string name() const override { return "GLSurfaceViewShadow"; }

    bool handles_class(const std::string& cls) const override {
        return cls.find("opengl/GLSurfaceView") != std::string::npos ||
               cls.find("opengles/GL10") != std::string::npos ||
               cls.find("opengles/GL11") != std::string::npos ||
               cls.find("opengl/GLES10") != std::string::npos ||
               cls.find("opengl/GLES11") != std::string::npos ||
               cls.find("khronos/egl/EGLConfig") != std::string::npos ||
               cls.find("khronos/egl/EGLContext") != std::string::npos ||
               cls.find("khronos/egl/EGLDisplay") != std::string::npos ||
               cls.find("khronos/egl/EGLSurface") != std::string::npos ||
               cls.find("khronos/egl/EGL10") != std::string::npos ||
               cls.find("opengl/EGL14") != std::string::npos ||
               cls.find("opengl/EGLExt") != std::string::npos;
    }

    void init(HeapAllocator* heap) override;
    CallResult dispatch(const CallContext& ctx) override;

    std::vector<std::string> implemented_methods() const override {
        return {"setRenderer", "setEGLContextClientVersion",
                "setEGLConfigChooser", "setEGLContextFactory",
                "setEGLWindowSurfaceFactory", "setGLWrapper", "setRenderMode",
                "getRenderMode", "setDebugFlags", "getDebugFlags",
                "setPreserveEGLContextOnPause", "requestRender", "queueEvent",
                "onPause", "onResume", "glClearColor", "glClear", "glViewport",
                "glEnable", "glDisable", "glBlendFunc", "glColor4f",
                "glColor4x", "glMatrixMode", "glLoadIdentity", "glTranslatef",
                "glRotatef", "glScalef", "glOrthof", "glFrustumf",
                "glEnableClientState", "glVertexPointer", "glColorPointer",
                "glDrawArrays", "glDrawElements", "glFlush", "glFinish",
                "eglGetDisplay", "eglInitialize", "eglChooseConfig",
                "eglCreateContext", "eglCreateWindowSurface", "eglMakeCurrent",
                "eglSwapBuffers", "eglDestroySurface", "eglGetError"};
    }

private:
    // GL method routing (shared by GL10/GL11/GLES10/GLES11 receivers).
    CallResult dispatch_gl(const CallContext& ctx, const std::string& m);
    // EGL statics/object methods (EGL10/EGL14 + object classes).
    CallResult dispatch_egl(const CallContext& ctx, const std::string& m);
};

} } // namespace miniandroid::framework
