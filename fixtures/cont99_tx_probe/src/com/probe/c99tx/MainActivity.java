package com.probe.c99tx;

import android.app.Activity;
import android.graphics.Paint;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.TextUtils;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * CONT-99 T5 — text baseline, line wrapping, ellipsize and paint-bounds
 * probe (V2-C99TX). Deterministic programmatic layout on bg #FFEEEEEE;
 * every text box has a FIXED height and its own top margin, so the ink-band
 * geometry is known a priori:
 *
 * V2: EVERY child carries topMargin=20 — the AOSP LinearLayout stacking
 * law makes each box start 20px below the previous one's bottom (V1
 * fixture error: the margins were written as absolute offsets, so V1
 * boxes landed at 20/260/580/1040/1620/2280 — honest fixture correction,
 * same lesson as the CONT-99 T1 V1 fixture-error). Stacked geometry:
 *
 *   tv1 "AaBbGg123" 48px 300x100  y=20..120    (metrics/baseline band)
 *   tv3 48x'E'      32px 320x80   y=140..220  (maxLines=1 + ellipsize END:
 *                                               ink must NOT cross x=320)
 *   tv4 long sentence 28px 300x100 y=240..340 (must wrap INSIDE the box)
 *   tv5 "AaBbGg123" 48px 300x100  y=360..460  (includeFontPadding=false:
 *                                               with the primary face
 *                                               fm.top==fm.ascent, AOSP
 *                                               predicts ink top EQUAL
 *                                               to tv1 — font-dependent,
 *                                               judged at metrics level)
 *   tv6 "\u0633\u0644\u0627\u0645 \u062f\u0646\u06cc\u0627" 36px 300x80 y=480..560 (RTL shaping: real ink)
 *   tv2 "wrap measurement row" 32px wrap x wrap y=580.. (single line)
 *
 * Laws under test (AOSP):
 *   L1  ink stays within its own measured box (no paint-outside-bounds);
 *   L2  the gap bands stay pure background (no neighbor bleed);
 *   L3  ellipsize caps ink at the box right edge;
 *   L4  wrapping stays inside the fixed-height box;
 *   L5  includeFontPadding=false raises the ink top vs the default twin;
 *   L6  RTL text shapes to real glyphs (ink exists, no crash);
 *   L7  Paint metrics answer the G36 law (ascent<0<descent, lh=d-a,
 *       leading>=0, measureText>0, proportional to textSize).
 */
public class MainActivity extends Activity {
    TextView tv1, tv2, tv3, tv4, tv5, tv6;

    TextView mk(String text, float sizePx, int color, int w, int h, int y) {
        TextView tv = new TextView(this);
        tv.setText(text);
        tv.setTextSize(android.util.TypedValue.COMPLEX_UNIT_PX, sizePx);
        tv.setTextColor(color);
        tv.setIncludeFontPadding(true);
        LinearLayout.LayoutParams lp =
                new LinearLayout.LayoutParams(w, h);
        lp.topMargin = y;
        tv.setLayoutParams(lp);
        return tv;
    }

    void row(String tag, TextView v) {
        System.err.println("[C99-TX] " + tag
                + " mw=" + v.getMeasuredWidth()
                + " mh=" + v.getMeasuredHeight()
                + " w=" + v.getWidth() + " h=" + v.getHeight()
                + " padT=" + v.getPaddingTop()
                + " padB=" + v.getPaddingBottom()
                + " lineH=" + v.getLineHeight()
                + " maxLines=" + v.getMaxLines()
                + " ell=" + v.getEllipsize()
                + " ifp=" + v.getIncludeFontPadding());
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFFEEEEEE);

        tv1 = mk("AaBbGg123", 48, 0xFF222222, 300, 100, 20);
        tv3 = mk("EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE",
                 32, 0xFF228822, 320, 80, 20);
        tv3.setMaxLines(1);
        tv3.setEllipsize(TextUtils.TruncateAt.END);
        tv4 = mk("the quick brown fox jumps over the lazy dog again",
                 28, 0xFF882222, 300, 100, 20);
        tv5 = mk("AaBbGg123", 48, 0xFF222222, 300, 100, 20);
        tv5.setIncludeFontPadding(false);
        tv6 = mk("\u0633\u0644\u0627\u0645 \u062f\u0646\u06cc\u0627",
                 36, 0xFF442288, 300, 80, 20);
        tv2 = mk("wrap measurement row", 32, 0xFF222288,
                 ViewGroup.LayoutParams.WRAP_CONTENT,
                 ViewGroup.LayoutParams.WRAP_CONTENT, 20);

        root.addView(tv1); root.addView(tv3); root.addView(tv4);
        root.addView(tv5); root.addView(tv6); root.addView(tv2);
        setContentView(root);

        System.err.println("[C99-TXVER] V2-C99TX");
        Paint p = new Paint();
        p.setTextSize(48);
        Paint.FontMetrics fm = p.getFontMetrics();
        System.err.println("[C99-TXPAINT] size=48"
                + " ascent=" + p.ascent()
                + " descent=" + p.descent()
                + " top=" + fm.top + " bottom=" + fm.bottom
                + " leading=" + fm.leading
                + " meas48=" + p.measureText("AaBbGg123"));
        p.setTextSize(24);
        System.err.println("[C99-TXPAINT] size=24"
                + " ascent=" + p.ascent()
                + " descent=" + p.descent()
                + " meas24=" + p.measureText("AaBbGg123"));

        new Handler(Looper.getMainLooper()).postDelayed(new Runnable() {
            public void run() {
                try {
                    row("tv1", tv1); row("tv3", tv3); row("tv4", tv4);
                    row("tv5", tv5); row("tv6", tv6); row("tv2", tv2);
                    Paint tp = tv1.getPaint();
                    if (tp != null) {
                        System.err.println("[C99-TXVPAINT] tv1 size="
                                + tp.getTextSize()
                                + " ascent=" + tp.ascent()
                                + " descent=" + tp.descent());
                    }
                    System.err.println("[C99-TXDONE] printed");
                } catch (Throwable t) {
                    System.err.println("[C99-TXERR] " + t);
                }
            }
        }, 1200);
    }
}
