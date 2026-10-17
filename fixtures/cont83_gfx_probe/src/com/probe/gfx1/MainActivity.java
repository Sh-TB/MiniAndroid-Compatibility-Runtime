package com.probe.gfx1;

import android.app.Activity;
import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.os.Bundle;
import javax.microedition.khronos.opengles.GL10;
import javax.microedition.khronos.egl.EGLConfig;

// CONT-83 graphics-boundary probe. Asserts, through the REAL pipeline:
//   1. framework-constant materialization (F-NEW-386 pre/post evidence —
//      the hand table's long-tail gaps sget 0 pre-fix),
//   2. the GLSurfaceView frame pump (created/changed/draw stages),
//   3. the GLES20 static bridge wiring (F-NEW-388): shader/program
//      plumbing + REAL array materialization through glUniformMatrix4fv,
//   4. the GL10 ES1 subset + the honest ES1-FFP REC-MISS frontier,
//   5. GLSL-not-compiled honesty (glCompileShader recorded, frontier row).
// Evidence lives in the [GFX1-*] rows + the MINIANDROID_GFX_TRACE JSONL,
// NOT in the screenshot (the GLSL frontier means no app pixels yet).
public class MainActivity extends Activity {
    private GLSurfaceView glView;
    private static int frames = 0;   // static: no outer-this dependency

    private static void c(String name, int v) {
        System.out.println("[GFX1-CONST] " + name + "=" + (v & 0xffffffffL));
    }

    @Override public void onCreate(Bundle b) {
        super.onCreate(b);
        System.out.println("[GFX1-VERSION] pkg=com.probe.gfx1 wave=CONT-83");
        c("GL10.GL_COLOR_BUFFER_BIT", GL10.GL_COLOR_BUFFER_BIT);
        c("GL10.GL_NEAREST", GL10.GL_NEAREST);
        c("GL10.GL_LINEAR", GL10.GL_LINEAR);
        c("GL10.GL_REPEAT", GL10.GL_REPEAT);
        c("GL10.GL_CLAMP_TO_EDGE", GL10.GL_CLAMP_TO_EDGE);
        c("GL10.GL_LIGHT0", GL10.GL_LIGHT0);
        c("GLES20.GL_VERTEX_SHADER", GLES20.GL_VERTEX_SHADER);
        c("GLES20.GL_FRAMEBUFFER", GLES20.GL_FRAMEBUFFER);
        c("GLES20.GL_COLOR_ATTACHMENT0", GLES20.GL_COLOR_ATTACHMENT0);
        c("GLES20.GL_COMPILE_STATUS", GLES20.GL_COMPILE_STATUS);
        glView = new GLSurfaceView(this);
        glView.setEGLContextClientVersion(2);
        glView.setRenderer(new Renderer());
        setContentView(glView);
        System.out.println("[GFX1-DONE] setup complete");
    }

    private class Renderer implements GLSurfaceView.Renderer {
        @Override public void onSurfaceCreated(GL10 gl, EGLConfig cfg) {
            System.out.println("[GFX1-SURFACE-CREATED]");
            int vs = GLES20.glCreateShader(GLES20.GL_VERTEX_SHADER);
            GLES20.glShaderSource(vs,
                "attribute vec4 aPos; void main(){ gl_Position = aPos; }");
            GLES20.glCompileShader(vs);
            int fs = GLES20.glCreateShader(GLES20.GL_FRAGMENT_SHADER);
            GLES20.glShaderSource(fs,
                "precision mediump float; void main(){ gl_FragColor = vec4(1.0); }");
            GLES20.glCompileShader(fs);
            int prog = GLES20.glCreateProgram();
            GLES20.glAttachShader(prog, vs);
            GLES20.glAttachShader(prog, fs);
            GLES20.glLinkProgram(prog);
            GLES20.glUseProgram(prog);
            int loc = GLES20.glGetUniformLocation(prog, "uM");
            float[] m = new float[]{1, 0, 0, 0,  0, 1, 0, 0,
                                    0, 0, 1, 0,  0, 0, 0, 1};
            GLES20.glUniformMatrix4fv(loc, 1, false, m, 0);
            int err = GLES20.glGetError();
            System.out.println("[GFX1-GLES20-SEQ] vs=" + vs + " fs=" + fs
                + " prog=" + prog + " loc=" + loc + " err=" + err);
        }

        @Override public void onSurfaceChanged(GL10 gl, int w, int h) {
            System.out.println("[GFX1-SURFACE-CHANGED] " + w + "x" + h);
        }

        @Override public void onDrawFrame(GL10 gl) {
            frames++;
            gl.glClearColor(0.2f, 0.4f, 0.8f, 1.0f);
            gl.glClear(GL10.GL_COLOR_BUFFER_BIT);
            gl.glViewport(0, 0, 1080, 1920);
            gl.glEnable(GL10.GL_BLEND);
            gl.glBlendFunc(GL10.GL_SRC_ALPHA, GL10.GL_ONE_MINUS_SRC_ALPHA);
            // ES1 fixed-function frontier: falls through to the honest
            // REC-MISS row (no invented color-clear substitution).
            gl.glColor4f(1f, 0f, 0f, 1f);
            System.out.println("[GFX1-FRAME] " + frames);
        }
    }
}
