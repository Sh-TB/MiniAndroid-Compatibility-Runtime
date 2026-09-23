/*
 * S66 CANVAS PROBE — controlled framebuffer evidence fixture (§1/§5/§6).
 *
 * One custom View whose REAL onDraw() DEX bytecode issues every draw
 * primitive at EXACT known coordinates with EXACT known colors, so every
 * framebuffer pixel is analytically predictable:
 *
 *   T1  drawColor WHITE            -> full-frame background
 *   T2  fillRect   RED    (100,100)-(300,200)
 *   T3  fillRect   BLUE   (500,100)-(560,160)
 *   T4  drawLine   GREEN  (400,400)->(600,400), width 4
 *   T5  drawCircle BLUE   center (800,300) r=80
 *   T6  fillRect   GRAY80 (700,100)-(760,160)   (0xFF808080 opaque)
 *   T7  drawText   BLACK  "AaBbCc 0123456789 X O" at (100,700)
 *   T8  alpha rect 0x80FF0000 over white (100,900)-(400,1100)
 *       -> source-over blend law: pixel = #FF7F7F (g,b = 255*(1-128/255))
 *   T9  STROKE rect GREEN (500,1200)-(700,1300), width 6
 *   T10 CLIP test: clipRect(560,1225,640,1275) then fillRect YELLOW
 *       (500,1200)-(700,1300). AOSP Canvas law (SkCanvas::clipRect ->
 *       SkCanvas::save -> getSaveCount/restore): the yellow ink may ONLY
 *       appear inside the clip. Engine flat-state model accepts clipRect
 *       as a documented NO-OP (canvas_shadow.cpp "Accepted (flat state
 *       model); geometry NOT reproduced" + warn_noop), so ink outside the
 *       clip = expected-by-current-engine, flagged RENDERER GAP.
 *   T11 Persian word (dour, "round") at (100,1500): the runtime bitmap font covers
 *       printable ASCII 32..126 only (BitmapFont law) — non-ASCII glyph
 *       coverage gap is expected and documented.
 *
 * No clocks, no randomness: identical invocations must produce
 * byte-identical frames. License: MIT.
 */
package com.miniandroid.canvasprobe;

import android.app.Activity;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.View;

public class MainActivity extends Activity {

    static class ProbeView extends View {
        ProbeView(Context c) { super(c); }

        @Override
        public void onDraw(Canvas canvas) {
            Paint p = new Paint();

            // T1 background
            p.setColor(Color.WHITE);
            canvas.drawPaint(p);

            // T2 red fill rect
            p.setColor(Color.RED);
            canvas.drawRect(100, 100, 300, 200, p);

            // T3 blue fill rect
            p.setColor(Color.BLUE);
            canvas.drawRect(500, 100, 560, 160, p);

            // T4 green line, width 4
            p.setColor(Color.GREEN);
            p.setStrokeWidth(4);
            canvas.drawLine(400, 400, 600, 400, p);

            // T5 blue circle r=80 at (800,300)
            p.setColor(Color.BLUE);
            p.setStyle(Paint.Style.FILL);
            canvas.drawCircle(800, 300, 80, p);

            // T6 opaque mid-gray rect
            p.setColor(0xFF808080);
            canvas.drawRect(700, 100, 760, 160, p);

            // T7 black ASCII text
            p.setColor(Color.BLACK);
            canvas.drawText("AaBbCc 0123456789 X O", 100, 700, p);

            // T8 50%-alpha red over white -> source-over blend
            p.setColor(0x80FF0000);
            canvas.drawRect(100, 900, 400, 1100, p);

            // T9 stroke-only rect (green, 6px border)
            p.setColor(Color.GREEN);
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(6);
            canvas.drawRect(500, 1200, 700, 1300, p);

            // T10 clip law test (see header)
            p.setColor(Color.YELLOW);
            p.setStyle(Paint.Style.FILL);
            canvas.save();
            canvas.clipRect(560, 1225, 640, 1275);
            canvas.drawRect(500, 1200, 700, 1300, p);
            canvas.restore();

            // T11 non-ASCII text (font coverage gap probe)
            p.setColor(Color.BLACK);
            canvas.drawText("\u062F\u0648\u0631", 100, 1500, p);
        }
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(new ProbeView(this));
    }
}
