/*
 * MiniAndroid CYCLE-E proof fixture — Canvas Path strengthening.
 *
 * One custom View (a real INNER CLASS, so the APK exercises the
 * Outer$Inner class path through ECJ → D8 → the runtime class resolver)
 * draws four regions whose pixels DISCRIMINATE between correct and wrong
 * Path/Canvas implementations:
 *
 *   R1 top-left     CUBIC Bézier fill — if cubicTo were dropped or treated
 *                   as lineTo, the contour degenerates and the bulge probe
 *                   finds white instead of blue.
 *   R2 top-right    rMoveTo/rLineTo polyline, STROKED — center stays white
 *                   (fill/stroke honesty); then Path.offset(dx,dy) shifts a
 *                   copy — if offset is ignored the red square is missing.
 *   R3 bottom-left  drawOval (real curve, not a rect: bbox corner white)
 *                   + drawArc(useCenter=true) pie wedge (center + sweep
 *                   quadrant yellow; the opposite quadrant white).
 *   R4 bottom-right TWO overlapping same-direction squares per fill rule:
 *                   WINDING keeps the overlap filled; EVEN_ODD punches a
 *                   hole. If setFillType is ignored or the rasterizer has
 *                   only one rule, one of the two overlaps is wrong.
 *
 * The drawing runs through REAL DEX bytecode every frame:
 * onDraw(Canvas) → android.graphics.Path/Canvas/Paint shadows → renderer.
 * All geometry is static, so two runs must produce byte-identical frames
 * (determinism proof).
 *
 * License: MIT.
 */
package com.miniandroid.pathfix;

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
        setContentView(new PathView(this));
    }

    class PathView extends View {
        PathView(android.content.Context c) { super(c); }

        @Override
        public void onDraw(Canvas canvas) {
            // ── R1: cubic Bézier "wave" filled blue ─────────────────────
            Paint blue = new Paint();
            blue.setColor(0xFF1E40AF);
            Path wave = new Path();
            wave.moveTo(20, 30);
            // Control points pull the curve DOWN to depth ~105 at the middle
            // (0.25*30 + 0.75*130 = 105). The closing chord runs at y=30.
            wave.cubicTo(60, 130, 140, 130, 180, 30);
            wave.close();
            canvas.drawPath(wave, blue);

            // ── R2: rMoveTo/rLineTo open polyline, stroked ──────────────
            Paint greenStroke = new Paint();
            greenStroke.setColor(0xFF228B22);
            greenStroke.setStyle(Paint.Style.STROKE);
            greenStroke.setStrokeWidth(6);
            Path square = new Path();
            square.moveTo(250, 40);
            square.rLineTo(60, 0);     // → (310, 40)  top edge
            square.rLineTo(0, 50);     // → (310, 90)  right edge
            square.rMoveTo(-60, 0);    // new sub-path at (250, 90)
            square.rLineTo(0, -50);    // → (250, 40)  left edge
            canvas.drawPath(square, greenStroke);

            // offset() must shift REAL geometry: a second draw paints the
            // same square 100 right / 120 down, in red.
            square.offset(100, 120);
            Paint redStroke = new Paint();
            redStroke.setColor(0xFFC62828);
            redStroke.setStyle(Paint.Style.STROKE);
            redStroke.setStrokeWidth(6);
            canvas.drawPath(square, redStroke);

            // ── R3: drawOval + drawArc ──────────────────────────────────
            Paint red = new Paint();
            red.setColor(0xFFC62828);
            canvas.drawOval(40, 460, 200, 620, red);   // circle r=80 @ (120,540)

            Paint yellow = new Paint();
            yellow.setColor(0xFFF9A825);
            // Pie wedge: 0° (3 o'clock) sweeping 90° clockwise → 6 o'clock.
            canvas.drawArc(240, 460, 400, 620, 0, 90, true, yellow);

            // ── R4: WINDING vs EVEN_ODD on identical geometry ───────────
            Paint magenta = new Paint();
            magenta.setColor(0xFFAD1457);
            Path windingPair = new Path();
            windingPair.addRect(40, 660, 130, 750, Path.Direction.CW);
            windingPair.addRect(85, 705, 175, 795, Path.Direction.CW);
            // default fill type = WINDING → overlap stays filled
            canvas.drawPath(windingPair, magenta);

            Paint cyan = new Paint();
            cyan.setColor(0xFF00838F);
            Path evenOddPair = new Path();
            evenOddPair.setFillType(Path.FillType.EVEN_ODD);
            evenOddPair.addRect(250, 660, 340, 750, Path.Direction.CW);
            evenOddPair.addRect(295, 705, 385, 795, Path.Direction.CW);
            // EVEN_ODD → overlap becomes a hole
            canvas.drawPath(evenOddPair, cyan);
        }
    }
}
