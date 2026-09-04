/*
 * Cycle E pre-probe: how do android.graphics enum constants behave when
 * referenced from real DEX? Discriminates via pixels:
 *   - STROKE honored  -> center of the rect stays white, border green
 *   - STROKE ignored  -> whole rect green (fill fallback)
 *   - setFillType honored -> overlap of the two squares is a hole (white)
 *   - setFillType ignored -> overlap filled (default rule wins)
 */
package com.miniandroid.probe;

import android.app.Activity;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.os.Bundle;
import android.view.View;

public class MainActivity extends Activity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(new ProbeView(this));
    }

    class ProbeView extends View {
        ProbeView(android.content.Context c) { super(c); }

        @Override
        public void onDraw(Canvas canvas) {
            Paint stroke = new Paint();
            stroke.setColor(0xFF228B22);   // forest green
            stroke.setStyle(Paint.Style.STROKE);   // enum object arg!
            stroke.setStrokeWidth(8);

            canvas.drawRect(60, 60, 300, 260, stroke);

            // Path fill-type probe: two same-direction overlapping squares
            // with EVEN_ODD -> overlap must be a hole if setFillType works.
            Path p = new Path();
            p.setFillType(Path.FillType.EVEN_ODD);  // enum object arg!
            p.addRect(340, 60, 440, 160, Path.Direction.CW);
            p.addRect(390, 110, 490, 210, Path.Direction.CW);
            Paint fill = new Paint();
            fill.setColor(0xFFB22222);   // firebrick
            canvas.drawPath(p, fill);
        }
    }
}
