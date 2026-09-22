package org.miniandroid.gfx.l5_canvas;

import android.app.Activity;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.os.Bundle;
import android.view.View;
import android.widget.LinearLayout;

public class MainActivity extends Activity {
    static class DrawView extends View {
        Paint fill = new Paint();
        Paint thin = new Paint();
        DrawView(Context c) {
            super(c);
            fill.setColor(Color.rgb(200, 30, 30));
            fill.setStyle(Paint.Style.FILL);
            thin.setColor(Color.rgb(0, 90, 200));
            thin.setStyle(Paint.Style.STROKE);
            thin.setStrokeWidth(4f);
        }
        @Override
        protected void onDraw(Canvas canvas) {
            canvas.drawColor(Color.rgb(245, 240, 220));
            canvas.drawRect(40, 40, 400, 200, fill);
            Path tri = new Path();
            tri.moveTo(60, 480);
            tri.lineTo(300, 480);
            tri.lineTo(180, 260);
            tri.close();
            Paint green = new Paint();
            green.setColor(Color.rgb(0, 160, 60));
            green.setStyle(Paint.Style.FILL);
            canvas.drawPath(tri, green);
            Paint text = new Paint();
            text.setColor(Color.BLACK);
            text.setTextSize(48f);
            canvas.drawText("GFX-CANVAS", 40, 560, text);
            canvas.save();
            canvas.clipRect(420, 40, 700, 300);
            canvas.drawRect(430, 50, 690, 290, thin);
            canvas.restore();
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
