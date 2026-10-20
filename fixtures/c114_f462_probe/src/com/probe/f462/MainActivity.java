package com.probe.f462;

import android.app.Activity;
import android.os.Bundle;

public class MainActivity extends Activity {
    static class Cfg {
        int width = 1080;
        int useGL30 = 1;
    }

    // libGDX-shaped: DEX class extending a FRAMEWORK class; its ctor calls
    // the framework super ctor, then does framework-ish calls.
    static class ViewLike extends android.opengl.GLSurfaceView {
        ViewLike(android.content.Context ctx) {
            super(ctx);
            setEGLContextClientVersion(2);
        }
    }

    // AndroidGraphics-shaped: NOT a view; its ctor creates the ViewLike
    // internally, THEN stores its own fields (the F-NEW-462 sequence).
    static class Gfx {
        Cfg cfg;
        Object app;
        ViewLike view;
        long lastFrameTime;

        Gfx(Object application, Cfg config) {
            this.app = application;
            this.cfg = config;
            this.view = new ViewLike((android.content.Context) application);
            // field stores AFTER the nested view construction (the law under test)
            this.lastFrameTime = 77L;
        }
    }

    // ── V2: the frame-pump receiver law (F-NEW-462 refined) ──────────────
    // Renderer whose fields are stored in ITS ctor; onDrawFrame reads them
    // back. Pre-fix the runtime dispatched renderer callbacks with the VIEW
    // as receiver -> this.frameSeq missed (answered 0) + this neverSeen
    // NPE'd family. Class name contains "GLSurfaceView" (frame-pump gate).
    static class GLSurfaceViewProbe extends android.opengl.GLSurfaceView {
        GLSurfaceViewProbe(android.content.Context ctx) {
            super(ctx);
        }
    }

    static class RendererImpl implements android.opengl.GLSurfaceView.Renderer {
        int frameSeq;
        int ctorStamp;

        RendererImpl() {
            this.frameSeq = 4242;
            this.ctorStamp = 777;
        }

        public void onSurfaceCreated(javax.microedition.khronos.opengles.GL10 gl,
                                     javax.microedition.khronos.egl.EGLConfig config) {
            System.err.println("[C462-SURF] ctorStamp=" + ctorStamp);
        }

        public void onSurfaceChanged(javax.microedition.khronos.opengles.GL10 gl,
                                     int width, int height) {
            System.err.println("[C462-CHG] ctorStamp=" + ctorStamp + " w=" + width);
        }

        public void onDrawFrame(javax.microedition.khronos.opengles.GL10 gl) {
            System.err.println("[C462-FRAME] seq=" + frameSeq
                    + " stamp=" + ctorStamp);
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Cfg config = new Cfg();
        Gfx g = new Gfx(this, config);
        // V1 readbacks: ctor-calls-ctor receiver binding (REFUTED sub-hypothesis
        // — simple shape stores correctly; retained as negative control).
        System.err.println("[C462-SELF] app_null=" + (g.app == null)
                + " cfg_null=" + (g.cfg == null)
                + " view_null=" + (g.view == null)
                + " lft=" + g.lastFrameTime);
        if (g.cfg != null) {
            System.err.println("[C462-CFG] width=" + g.cfg.width
                    + " useGL30=" + g.cfg.useGL30);
        } else {
            System.err.println("[C462-CFG] width=MISS useGL30=MISS");
        }
        // V2: attach a GLSurfaceView + renderer -> the frame pump drives
        // onSurfaceCreated/onSurfaceChanged/onDrawFrame per frame.
        GLSurfaceViewProbe vp = new GLSurfaceViewProbe(this);
        vp.setRenderer(new RendererImpl());
        setContentView(vp);
        System.err.println("[C462-VERSION] F462-V2");
    }
}
