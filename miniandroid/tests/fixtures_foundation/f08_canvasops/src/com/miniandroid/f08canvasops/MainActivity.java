package com.miniandroid.f08canvasops;
import android.app.Activity; import android.content.Context; import android.os.Bundle;
import android.graphics.Canvas; import android.graphics.Color; import android.graphics.Paint;
import android.view.View;

public class MainActivity extends Activity {
    public static class ProbeView extends View {
        public ProbeView(Context c) { super(c); }
        @Override public void onDraw(Canvas canvas) {
            // Row 1 (y 0..179): drawColor full-view is replaced by rows below;
            // start by filling background via drawColor then overdraw.
            Paint p = new Paint();
            // R1: drawColor (white base) + drawRect fill
            canvas.drawColor(Color.WHITE);
            p.setColor(Color.RED);
            canvas.drawRect(40, 20, 400, 140, p);              // R1 red rect
            // R2: drawCircle fill + stroke
            p.setColor(Color.BLUE);
            p.setStyle(Paint.Style.FILL);
            canvas.drawCircle(140, 280, 80, p);                // R2 blue disc
            p.setColor(Color.rgb(0,150,0));
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(12);
            canvas.drawCircle(420, 280, 80, p);                // R2 stroke ring
            // R3: drawLine (2x) + drawText
            p.setColor(Color.BLACK);
            p.setStyle(Paint.Style.FILL);
            p.setStrokeWidth(6);
            canvas.drawLine(40, 500, 700, 500, p);
            canvas.drawLine(40, 560, 700, 560, p);
            p.setTextSize(40);
            canvas.drawText("OK", 760, 540, p);                // R3 text
            // R4: translate + restore
            canvas.save();
            canvas.translate(300, 620);
            p.setColor(Color.rgb(128,0,128));
            canvas.drawRect(40, 640, 240, 740, p);             // R4 purple at 340,1260 (translated)
            canvas.restore();
            // R5: scale probe — scale(2,2) then small rect; if scale applied,
            // the rect appears 4x area at doubled coords.
            canvas.save();
            canvas.scale(2.0f, 2.0f);
            p.setColor(Color.rgb(255,140,0));
            canvas.drawRect(40, 820, 90, 845, p);              // R5 orange probe
            canvas.restore();
            // R6: clipRect probe — clip then draw outside; if clip enforced,
            // the outside part must not appear.
            canvas.save();
            p.setColor(Color.rgb(0,180,180));
            canvas.clipRect(40, 980, 300, 1080);
            canvas.drawRect(40, 980, 800, 1080, p);            // R6 teal (clipped?)
            canvas.restore();
            // R7: rotate probe — rotate 45 then axis-aligned rect; if rotation
            // applied the raster is a diamond, else a plain rect.
            canvas.save();
            canvas.rotate(45);
            p.setColor(Color.rgb(90,90,90));
            canvas.drawRect(600, 1150, 800, 1200, p);          // R7 gray probe
            canvas.restore();
            // R8: setARGB probe — engine gap census (A5): currently unhandled.
            Paint p2 = new Paint();
            p2.setARGB(255, 0, 0, 200);
            canvas.drawRect(40, 1300, 400, 1400, p2);          // R8 expect blue
            // R9: drawRoundRect probe (radius 40 — corners rounded?)
            p.setColor(Color.rgb(180,120,60));
            canvas.drawRoundRect(460, 1300, 860, 1400, 40, 40, p); // R9 brown
            // R10: drawText non-ASCII probe (A6): Persian via Canvas
            canvas.drawText("سلام", 40, 1520, p);
        }
    }
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        setContentView(new ProbeView(this)); }
}
