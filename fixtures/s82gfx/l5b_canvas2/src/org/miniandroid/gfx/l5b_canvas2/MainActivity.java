package org.miniandroid.gfx.l5b_canvas2;

import android.app.Activity;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.Path;
import android.os.Bundle;
import android.view.View;
import android.widget.LinearLayout;

// S83-GFX-BASE: pins the NEW Canvas foundation laws pixel-wise:
//   1. saveLayerAlpha real isolation (layer alpha compositing at restore)
//   2. clipPath (path clip via scanline spans, fill honored)
//   3. drawLines / drawPoints (stroke law)
//   4. Matrix concat rotate (AOSP 3x3 layout through MatrixShadow)
//   5. drawPosText (positioned glyphs)
// Each block paints at a distinct screen region with distinct colors so a
// single frame evidence covers every law independently.
public class MainActivity extends Activity {
    static class DrawView extends View {
        DrawView(Context c) { super(c); }

        @Override
        protected void onDraw(Canvas canvas) {
            canvas.drawColor(Color.rgb(250, 248, 243));
            Paint p = new Paint();
            p.setStyle(Paint.Style.FILL);

            // 1) saveLayerAlpha(40,40,340,240, 128): red rect inside the
            //    layer blends to ~50% over the white bg (pink). The green
            //    rect AFTER restore must be fully opaque (isolation law).
            canvas.saveLayerAlpha(40f, 40f, 340f, 240f, 128);
            p.setColor(Color.rgb(255, 0, 0));
            canvas.drawRect(60, 60, 320, 220, p);
            canvas.restore();
            p.setColor(Color.rgb(0, 170, 60));
            canvas.drawRect(360, 60, 600, 220, p);

            // 2) clipPath: purple rect painted through a triangular clip —
            //    only the triangle region may receive pixels.
            Path tri = new Path();
            tri.moveTo(80, 300);
            tri.lineTo(360, 300);
            tri.lineTo(220, 480);
            tri.close();
            canvas.save();
            canvas.clipPath(tri);
            p.setColor(Color.rgb(150, 60, 200));
            canvas.drawRect(60, 280, 380, 500, p);
            canvas.restore();

            // 3) drawLines: two connected segments (an L shape); drawPoints:
            //    four orange 10px squares.
            Paint line = new Paint();
            line.setColor(Color.rgb(0, 120, 220));
            line.setStrokeWidth(6f);
            float[] seg = {420, 320, 640, 320, 640, 460};
            canvas.drawLines(seg, line);
            Paint dot = new Paint();
            dot.setColor(Color.rgb(230, 140, 0));
            dot.setStrokeWidth(10f);
            float[] dots = {80, 560, 130, 560, 180, 560, 230, 560};
            canvas.drawPoints(dots, dot);

            // 4) Matrix: rotate a dark square 45 deg around its center — the
            //    rendered square must extend OUTSIDE the axis-aligned
            //    bounds (rotation law through the real Matrix values).
            canvas.save();
            Matrix m = new Matrix();
            m.postRotate(45f, 520f, 560f);
            canvas.concat(m);
            p.setColor(Color.rgb(90, 90, 90));
            canvas.drawRect(470, 510, 570, 610, p);
            canvas.restore();

            // 5) drawPosText: 'A','B','C' at explicit positions.
            Paint tp = new Paint();
            tp.setColor(Color.BLACK);
            tp.setTextSize(40f);
            float[] pos = {80, 660, 130, 660, 180, 660};
            canvas.drawPosText("ABC", pos, tp);
        }
    }

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.addView(new DrawView(this));
        setContentView(root);
    }
}
