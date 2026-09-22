package org.miniandroid.gfx.l6_glsurface;

import android.app.Activity;
import android.opengl.GLSurfaceView;
import android.os.Bundle;
import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

public class MainActivity extends Activity {
    static class ClearRenderer implements GLSurfaceView.Renderer {
        public void onSurfaceCreated(GL10 gl, EGLConfig config) {}
        public void onSurfaceChanged(GL10 gl, int w, int h) {}
        public void onDrawFrame(GL10 gl) {
            gl.glClearColor(0.1f, 0.6f, 0.9f, 1f);
            gl.glClear(GL10.GL_COLOR_BUFFER_BIT);
        }
    }
    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        GLSurfaceView v = new GLSurfaceView(this);
        v.setRenderer(new ClearRenderer());
        setContentView(v);
    }
}
