package com.probe.f352;

import android.app.Activity;
import android.graphics.BlendMode;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.PorterDuff;
import android.graphics.PorterDuffColorFilter;
import android.os.Bundle;
import android.view.View;

/**
 * F-NEW-352 probe — the Paint color-filter (draw-time tint) law.
 *
 * Each patch isolates ONE law from the AOSP PorterDuffColorFilter contract:
 * the filter color = SRC, the drawn bitmap pixel = DST. The patches are
 * 120x120 at fixed slots; the verifier (scripts/cont64_verify_f352.py)
 * reads the screenshot pixels and asserts each row's expected color.
 *
 * Layout (x=80 left patch, x=300 right patch; y per row):
 *   R1 y=80   T1 SRC_IN over opaque WHITE   -> pure tint red
 *             T2 SRC_IN over TRANSPARENT    -> nothing (alpha 0)
 *   R2 y=230  T3 SRC_ATOP over HALF-ALPHA   -> tinted rgb, alpha kept
 *             T4 MULTIPLY red x BLUE        -> black-ish rgb
 *   R3 y=380  T5 no-filter control          -> bitmap colors UNCHANGED
 *             T6 BlendModeColorFilter SRC_IN-> pure tint green
 *   R4 y=530  T7 SRC_IN tint over WHITE x2 at DIFFERENT paints (filter
 *             per-paint state: paint A red, paint B blue)
 *             T8 getColorFilter != null round-trip drives a white->tint
 *             (the filter recorded on the paint is the SAME object)
 */
public class MainActivity extends Activity {

    static final int PATCH = 120;

    static Bitmap make(int w, int h, int argb, int halfSplitColor, boolean halfAlpha) {
        Bitmap b = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        int[] px = new int[w * h];
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++) {
                if (halfAlpha && x >= w / 2) px[y * w + x] = halfSplitColor & 0x80FFFFFF;
                else if (!halfAlpha && x >= w / 2) px[y * w + x] = halfSplitColor;
                else px[y * w + x] = argb;
            }
        b.setPixels(px, 0, w, 0, 0, w, h);
        return b;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(new ProbeView(this));
    }

    static class ProbeView extends View {
        Paint p = new Paint();
        Paint pRed = new Paint();
        Paint pBlue = new Paint();
        Paint pCtl = new Paint();

        ProbeView(Activity a) { super(a); }

        @Override
        protected void onDraw(Canvas c) {
            c.drawColor(Color.rgb(24, 24, 28));   // the probe background

            // R1 T1: SRC_IN over OPAQUE WHITE -> the tint's rgb, alpha kept.
            Bitmap white = make(PATCH, PATCH, 0xFFFFFFFF, 0xFFFFFFFF, false);
            pRed.setColorFilter(new PorterDuffColorFilter(0xFFFF0000, PorterDuff.Mode.SRC_IN));
            c.drawBitmap(white, 80f, 80f, pRed);

            // R1 T2: SRC_IN over TRANSPARENT -> out alpha = 0 (nothing shows).
            Bitmap clear = make(PATCH, PATCH, 0x00000000, 0x00000000, false);
            c.drawBitmap(clear, 300f, 80f, pRed);

            // R2 T3: SRC_ATOP over HALF-ALPHA (left half opaque white, right
            // half 50% white) -> tinted rgb weighted by dst alpha.
            Bitmap half = make(PATCH, PATCH, 0xFFFFFFFF, 0xFFFFFFFF, true);
            Paint pa = new Paint();
            pa.setColorFilter(new PorterDuffColorFilter(0xFF00FF00, PorterDuff.Mode.SRC_ATOP));
            c.drawBitmap(half, 80f, 230f, pa);

            // R2 T4: MULTIPLY red x BLUE -> rgb (0,0,0).
            Bitmap blue = make(PATCH, PATCH, 0xFF0000FF, 0xFF0000FF, false);
            Paint pm = new Paint();
            pm.setColorFilter(new PorterDuffColorFilter(0xFFFF0000, PorterDuff.Mode.MULTIPLY));
            c.drawBitmap(blue, 300f, 230f, pm);

            // R3 T5: NO filter (the negative control) -> bitmap unchanged.
            Bitmap solid = make(PATCH, PATCH, 0xFF004488, 0xFF004488, false);
            pCtl.setColor(0xFF004488);
            c.drawBitmap(solid, 80f, 380f, pCtl);

            // R3 T6: BlendModeColorFilter SRC_IN (the compose-era API).
            Bitmap white2 = make(PATCH, PATCH, 0xFFFFFFFF, 0xFFFFFFFF, false);
            Paint pg = new Paint();
            pg.setColorFilter(new android.graphics.BlendModeColorFilter(
                0xFF00CC44, BlendMode.SRC_IN));
            c.drawBitmap(white2, 300f, 380f, pg);

            // R4 T7: per-paint filter STATE — pRed keeps ITS red filter,
            // pBlue gets blue; both draw white bitmaps in the same wave.
            pBlue.setColorFilter(new PorterDuffColorFilter(0xFF0000FF, PorterDuff.Mode.SRC_IN));
            c.drawBitmap(make(PATCH, PATCH, 0xFFFFFFFF, 0xFFFFFFFF, false), 80f, 530f, pRed);
            c.drawBitmap(make(PATCH, PATCH, 0xFFFFFFFF, 0xFFFFFFFF, false), 300f, 530f, pBlue);

            // R4 T8: the getColorFilter round-trip — the SAME filter object
            // recorded on the paint drives this draw (white -> green tint).
            Paint p8 = new Paint();
            PorterDuffColorFilter f8 = new PorterDuffColorFilter(0xFF11AA66, PorterDuff.Mode.SRC_IN);
            p8.setColorFilter(f8);
            if (p8.getColorFilter() == f8)
                c.drawBitmap(make(PATCH, PATCH, 0xFFFFFFFF, 0xFFFFFFFF, false), 80f, 680f, p8);
            // (if the round-trip breaks, the patch stays background = the
            // verifier reads the miss as the honest FAIL face)
        }
    }
}
