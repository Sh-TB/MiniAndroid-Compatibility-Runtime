package com.probe.c106b2;

import android.app.Activity;
import android.content.Context;
import android.content.res.TypedArray;
import android.graphics.Canvas;
import android.os.Bundle;
import android.util.AttributeSet;
import android.util.TypedValue;
import android.view.View;

/**
 * CONT-107 / F-NEW-448 probe: the Toolbar height-0 chain, minimized.
 *
 * Chess face (CONT-106): appcompat Toolbar.onMeasure reads static I Ll/m3;.a
 * twice and gets 0 -> Toolbar measured 1080x0 -> unrendered. Upstream, that
 * static carries the theme-derived action-bar default height resolved during
 * appcompat init.
 *
 * This probe exercises each link of the chain generically:
 *   C448-RESOLVE  theme.resolveAttribute(dimension attr)      (TypedValue law)
 *   C448-TYPE     the resolved TypedValue type/coercion
 *   C448-DIM      TypedArray.getDimensionPixelSize            (dimension law)
 *   C448-STATIC   static int round-trip (the m3.a slot law)
 *   C448-MEASURE  onMeasure reads the static -> measured height (measure law)
 * AOSP: resolve ok=true, type=DIMENSION, dim=56dp-in-px>0, static==dim,
 * measured==static.
 */
public class MainActivity extends Activity {

    /** the Ll/m3;.a analog: theme-derived static read from onMeasure */
    public static int sBarHeight = 0;
    public static boolean sResolveOk = false;
    public static int sDimVal = 0;
    public static int sTvType = -1;
    public static int sMeasuredH = -1;

    public static class BarView extends View {
        public BarView(Context c) { super(c); }

        @Override protected void onMeasure(int wspec, int hspec) {
            // the Toolbar law: height comes from the static, not the spec
            int h = sBarHeight;
            sMeasuredH = h;
            setMeasuredDimension(MeasureSpec.getSize(wspec), h);
        }

        @Override protected void onDraw(Canvas c) { }
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);

        TypedValue tv = new TypedValue();
        sResolveOk = getTheme().resolveAttribute(R.attr.probeBarSize, tv, true);
        sTvType = tv.type;

        TypedArray ta = obtainStyledAttributes(new int[]{R.attr.probeBarSize});
        sDimVal = ta.getDimensionPixelSize(0, 0);
        ta.recycle();

        // upstream appcompat init writes the static from the resolved value
        sBarHeight = sDimVal;

        BarView bar = new BarView(this);
        int wspec = View.MeasureSpec.makeMeasureSpec(1080, View.MeasureSpec.EXACTLY);
        int hspec = View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED);
        bar.measure(wspec, hspec);

        System.err.println("[C448-RESOLVE] ok=" + sResolveOk);
        System.err.println("[C448-TYPE] type=" + sTvType + " val=" + tv.coerceToString());
        System.err.println("[C448-DIM] dim=" + sDimVal);
        System.err.println("[C448-STATIC] static=" + sBarHeight);
        System.err.println("[C448-MEASURE] measured=" + sMeasuredH
                + " expected=" + sBarHeight);
    }
}
