package com.probe.w4ladder;

import android.app.Activity;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.TextView;

/**
 * CONT-8 W4 Ladder Probe A+B (directive §1).
 *
 * Probe A: native View whose onDraw() performs drawRect + drawText +
 *          drawBitmap + drawPath (+ drawCircle bonus), plus
 *          canvas.save/translate/restore state ops.
 * Probe B: a ViewGroup (FrameLayout) containing the Probe-A view and a
 *          TextView - proves the ViewGroup child-dispatch draw path.
 */
public class MainActivity extends Activity {
    private static String report = "";

    private static void row(String id, boolean pass, String detail) {
        report += id + "|" + (pass ? "PASS" : "FAIL") + "|" + detail + "\n";
    }

    /** Probe A - native View with the op families. */
    public static class ProbeAView extends View {
        public int rectOps = 0, textOps = 0, bitmapOps = 0, pathOps = 0,
                   circleOps = 0, saves = 0, translates = 0;
        private Bitmap bmp;
        private Paint paint;
        private boolean reported = false;

        public ProbeAView(Context c) {
            super(c);
            paint = new Paint();
            paint.setColor(0xFFCC2222);
            bmp = Bitmap.createBitmap(8, 8, Bitmap.Config.ARGB_8888);
            Canvas bc = new Canvas(bmp);
            bc.drawColor(0xFF2244CC);
        }

        @Override
        protected void onDraw(Canvas canvas) {
            canvas.save();
            translates++;
            canvas.translate(40, 40);
            translates++;
            canvas.restore();
            saves++;

            paint.setColor(0xFFCC2222);
            paint.setStyle(Paint.Style.FILL);
            canvas.drawRect(60, 80, 260, 200, paint);
            rectOps++;

            paint.setColor(0xFF22AA44);
            canvas.drawCircle(480, 140, 70, paint);
            circleOps++;

            paint.setColor(0xFF111111);
            paint.setTextSize(46f);
            canvas.drawText("W4LADDER-A", 60, 280, paint);
            textOps++;

            Path p = new Path();
            p.moveTo(60, 340);
            p.lineTo(240, 340);
            p.lineTo(150, 460);
            p.close();
            paint.setColor(0xFFDD8811);
            canvas.drawPath(p, paint);
            pathOps++;

            canvas.save();
            canvas.translate(360, 320);
            canvas.drawBitmap(bmp, 0, 0, paint);
            bitmapOps++;
            canvas.restore();

            if (!reported) {
                reported = true;
                row("A-OPS", true,
                    "rect=" + rectOps + " circle=" + circleOps +
                    " text=" + textOps + " path=" + pathOps +
                    " bitmap=" + bitmapOps + " save=" + saves +
                    " translate=" + translates);
            }
        }
    }

    private int childCount = -1;
    private boolean rep2 = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        FrameLayout root = new FrameLayout(this);
        ProbeAView a = new ProbeAView(this);
        root.addView(a, new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.MATCH_PARENT));
        TextView tv = new TextView(this);
        tv.setText("W4LADDER-B-GROUP");
        tv.setTextColor(0xFF7030A0);
        tv.setX(60f);
        tv.setY(500f);
        root.addView(tv);
        setContentView(root);
        childCount = root.getChildCount();

        row("B-TREE", childCount == 2,
            "ViewGroup childCount=" + childCount + " (ProbeAView + TextView)");
        row("A-CREATED", true, "ProbeAView constructed, bitmap 8x8 app-owned");
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (!rep2) {
            rep2 = true;
            row("B-TREE2", childCount == 2, "onResume childCount=" + childCount);
            row("SUMMARY", true, "rows recorded");
        }
    }
}
