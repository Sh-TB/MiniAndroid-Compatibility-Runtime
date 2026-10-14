package com.probe.f351;

import android.app.Activity;
import android.content.Context;
import android.graphics.BlendMode;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.os.Bundle;
import android.view.View;

/**
 * F-NEW-351 probe — vector-icon path rasterization laws (the compose
 * material-icon face: 4 two-tone icons render as SOLID BLACK SQUARES on
 * dooz v23 at binary 5112377f).
 *
 * Each row isolates ONE law from the live dooz draw-window trace
 * (run/cont63/drawwin180): save -> translate -> scale(2.75) -> Path
 * rewind/build (moveTo + rCubicTo/rLineTo + close, 2 contour groups) ->
 * drawPath with a reused Paint (0x4d000000 tone / 0xff000000 main).
 *
 * The anti-square assertion: a circular path drawn into its bounding box
 * MUST leave the box CORNERS empty. dooz's icons fill the whole 63x63 box
 * with hard edges — either the contours or the rasterizer are wrong.
 */
public class MainActivity extends Activity {

    static final float K = 0.552284749831f; // circle kappa

    static void circle(Path p, float cx, float cy, float r) {
        p.moveTo(cx, cy - r);
        p.rCubicTo(r * K, 0, r, r * (1 - K), r, r);
        p.rCubicTo(0, r * K, -r * (1 - K), r, -r, r);
        p.rCubicTo(-r * K, 0, -r, -r * (1 - K), -r, -r);
        p.rCubicTo(0, -r * K, r * (1 - K), -r, r, -r);
        p.close();
    }

    static void quadCircle(Path p, float cx, float cy, float r) {
        p.moveTo(cx, cy - r);
        p.rQuadTo(r, 0, r, r);
        p.rQuadTo(0, r, -r, r);
        p.rQuadTo(-r, 0, -r, -r);
        p.rQuadTo(0, -r, r, -r);
        p.close();
    }

    static void square(Path p, float x, float y, float s) {
        p.moveTo(x, y);
        p.rLineTo(s, 0);
        p.rLineTo(0, s);
        p.rLineTo(-s, 0);
        p.close();
    }


    interface ScaleI { void sc(float a, float b); }

    static class Wrapper implements ScaleI {
        final Canvas c;
        Wrapper(Canvas c) { this.c = c; }
        public void sc(float a, float b) { c.scale(a, b); }
    }

    static void scaleThrough(Canvas c, float a, float b) {
        ScaleI w = new Wrapper(c);
        w.sc(a, b);
    }

    static Paint rp2() {
        Paint p = new Paint();
        p.setColor(0xFF2244AA);
        return p;
    }

    static class ProbeView extends View {
        ProbeView(Context c) { super(c); }

        @Override protected void onDraw(Canvas canvas) {
            canvas.drawColor(0xFFFFFFFF);
            Paint tp = new Paint();
            tp.setColor(0xFF000000);
            tp.setTextSize(30);

            // R1: triangle via moveTo + rLineTo + close (baseline rasterizer).
            Path t = new Path();
            t.moveTo(150, 70);
            t.rLineTo(80, 160);
            t.rLineTo(-160, 0);
            t.close();
            Paint black = new Paint();
            black.setColor(0xFF000000);
            canvas.drawPath(t, black);
            canvas.drawText("R1", 130, 265, tp);

            // R2: THE ANTI-SQUARE — 4xCubicTo circle, solid black.
            Path c2 = new Path();
            circle(c2, 390, 150, 85);
            canvas.drawPath(c2, black);
            canvas.drawText("R2", 370, 265, tp);

            // R3: alpha law — the two-tone tone layer (0x4d000000 over white).
            Path c3 = new Path();
            circle(c3, 630, 150, 85);
            Paint tone = new Paint();
            tone.setColor(0x4D000000);
            canvas.drawPath(c3, tone);
            canvas.drawText("R3", 610, 265, tp);

            // R4: BlendMode.SRC_OVER paint (the dooz SGET-MISS face) must not
            // corrupt the fill.
            Path c4 = new Path();
            circle(c4, 870, 150, 85);
            Paint bm = new Paint();
            bm.setColor(0xFF000000);
            bm.setBlendMode(BlendMode.SRC_OVER);
            canvas.drawPath(c4, bm);
            canvas.drawText("R4", 850, 265, tp);

            // R5: TWO contour groups in ONE path (the dooz build pattern:
            // moveTo..close, moveTo..close) drawn with a single drawPath.
            Path two = new Path();
            circle(two, 150, 390, 85);      // outer disc
            two.moveTo(120, 360);           // inner square contour
            two.rLineTo(60, 0);
            two.rLineTo(0, 60);
            two.rLineTo(-60, 0);
            two.close();
            canvas.drawPath(two, black);
            canvas.drawText("R5", 130, 505, tp);

            // R6: PATH REUSE (rewind between draws) with a second Paint color.
            Path reuse = new Path();
            circle(reuse, 390, 390, 85);
            canvas.drawPath(reuse, black);
            reuse.rewind();
            square(reuse, 330, 330, 120);
            Paint blue = new Paint();
            blue.setColor(0xFF2244AA);
            canvas.drawPath(reuse, blue);
            canvas.drawText("R6", 370, 505, tp);

            // R7: THE COMPOSE TRANSFORM PATTERN — save/translate/scale(2.75)/
            // build a 24-unit-space circle/draw/restore (the live dooz
            // draw-window sequence at Canvas.save->scale->drawPath).
            canvas.save();
            canvas.translate(540, 300);
            canvas.scale(2.75f, 2.75f);
            Path v = new Path();
            circle(v, 32.7f, 32.7f, 32.7f);  // 24-unit viewport circle scaled up
            canvas.drawPath(v, black);
            canvas.restore();
            canvas.drawText("R7", 610, 505, tp);

            // R8: PAINT REUSE with color switch (paint 14815 cycles in dooz).
            Paint sw = new Paint();
            Path c8a = new Path();
            circle(c8a, 870, 390, 60);
            sw.setColor(0x4D000000);
            canvas.drawPath(c8a, sw);
            Path c8b = new Path();
            circle(c8b, 870, 390, 85);
            sw.setColor(0xFF000000);
            canvas.drawPath(c8b, sw);
            canvas.drawText("R8", 850, 505, tp);

            // R9: rQuadTo circle (quadratic variant).
            Path c9 = new Path();
            quadCircle(c9, 150, 630, 85);
            canvas.drawPath(c9, black);
            canvas.drawText("R9", 130, 745, tp);

            // R10: nested-box law — small circle INSIDE a big circle path,
            // opposite winding (the two-tone cutout law): nonzero winding
            // fills the ring, the inner disc punches OUT only when reversed;
            // same-direction stays filled (AOSP WINDING default).
            Path ring = new Path();
            circle(ring, 390, 630, 85);       // outer, CW
            Path inner = new Path();
            circle(inner, 390, 630, 40);      // inner, also CW (same direction)
            ring.addPath(inner, 0, 0);
            canvas.drawPath(ring, black);
            canvas.drawText("RA", 370, 745, tp);

        // R11 (dooz-shape replica): interface-dispatched wrapper + asymmetric
        // scale — isolates the invoke-shape difference (interface vs virtual)
        // that the live dooz trace suspected (a=0 after scale).
        canvas.save();
        canvas.translate(300, 540);
        scaleThrough(canvas, 3.0f, 2.0f);
        Paint rp = new Paint();
        rp.setColor(0xFF2244AA);
        canvas.drawRect(10, 10, 30, 20, rp);
        canvas.restore();
        canvas.drawText("RB", 370, 745, tp);

        // R12: direct asymmetric scale (no wrapper) — the control row.
        canvas.save();
        canvas.translate(540, 540);
        canvas.scale(3.0f, 2.0f);
        canvas.drawRect(10, 10, 30, 20, rp2());
        canvas.restore();
        canvas.drawText("RC", 610, 745, tp);

        // RD: BlendMode.CLEAR = destination ERASE (Skia kClear law — the
        // DrawCache.clear face). Red rect; a CLEAR-paint rect over the left
        // half must make it TRANSPARENT, not black.
        Paint red = new Paint();
        red.setColor(0xFFCC2222);
        canvas.drawRect(540, 540, 720, 700, red);
        Paint clear = new Paint();
        clear.setColor(0xFF000000);
        clear.setBlendMode(BlendMode.CLEAR);
        canvas.drawRect(540, 540, 630, 700, clear);
        canvas.drawText("RD", 610, 745, tp);

        // RE: CLEAR into a BITMAP TARGET (Canvas(Bitmap) + flush + getPixel):
        // bitmap filled red, left half cleared through a bitmap-target
        // canvas, composited at (780,540) — left = transparent(white bg),
        // right = red; getPixel prints the truth as text.
        Bitmap wbm = Bitmap.createBitmap(64, 64, Bitmap.Config.ARGB_8888);
        wbm.eraseColor(0xFFCC2222);
        Canvas bc = new Canvas(wbm);
        Paint clr2 = new Paint();
        clr2.setColor(0xFF000000);
        clr2.setBlendMode(BlendMode.CLEAR);
        bc.drawRect(0, 0, 32, 64, clr2);
        int gp1 = wbm.getPixel(8, 32);    // cleared half -> 0x00000000
        int gp2 = wbm.getPixel(56, 32);   // kept half   -> ffcc2222
        canvas.drawBitmap(wbm, 780, 540, null);
        Paint tp2 = new Paint();
        tp2.setColor(0xFF000000);
        tp2.setTextSize(26);
        canvas.drawText("RE" + Integer.toHexString(gp1), 780, 640, tp2);
        canvas.drawText("RF" + Integer.toHexString(gp2), 780, 680, tp2);

        }
    }

    @Override protected void onCreate(Bundle s) {
        super.onCreate(s);
        setContentView(new ProbeView(this));
    }
}
