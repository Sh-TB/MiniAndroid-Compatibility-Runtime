package com.probe.c99im;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.ImageView;

/**
 * CONT-99 T3 — ImageView/Drawable sizing, scaleType and image-bounds probe
 * (V1). Deterministic nodpi assets: red_land 200x100 (#FFCC2222),
 * blue_port 100x200 (#FF2222CC), green_sq 100x100 (#FF22CC22); window bg
 * #FFEEEEEE. Views are left-aligned boxes in a vertical LinearLayout:
 *
 *   iv1 200x200 red_land fitCenter  -> drawn (0,50,200,100)  letterbox
 *   iv2 200x200 red_land centerCrop -> crop x2: (-100..300, 200..400)
 *   iv3 200x200 blue_port fitCenter -> drawn (50,400,100,200)
 *   iv4 100x100 green_sq fitXY      -> fills (0,600,100,100)
 *   iv5 200x200 green_sq centerInside -> (50,750,100,100) no upscale
 *   iv6 100x100 green_sq center     -> natural, fills box exactly
 *   iv7 wrap_content green_sq       -> intrinsic 100x100 at (0,1000)
 *   iv8 100x100 NO src              -> nothing drawn (missing-image neg)
 *
 * PHASE1 rows: per-view scaleType/measured/drawable/intrinsic state right
 * after inflation+layout (the XML inflation + measurement contract).
 * PHASE2: programmatic iv1.setScaleType(FIT_XY) — the state must switch
 * and the FINAL RASTER must fill iv1's box (pixel rows below).
 *
 * Pixel oracle (scripts/cont99_img_run.sh, deterministic PPM samples):
 *   (100,100) red   (10,10)  RED after PHASE2 (FIT_XY fills the box)
 *   (100,300) red   (5,205)  red   (centerCrop reaches the box edge x=5)
 *   (100,500) blue  (10,410) bg    (fitCenter letterbox)
 *   (50,650)  green (1,601)  green (fitXY fills)
 *   (100,800) green (10,710) bg    (centerInside no upscale)
 *   (50,950)  green (1,901)  green (center natural == box)
 *   (50,1050) green (150,1050) bg  (wrap_content == intrinsic, nothing beyond)
 *   (50,1150) bg                   (missing image draws nothing)
 * The image must stay within its own view bounds and the letterbox/crop
 * pixels must match the AOSP matrix law — never stretch-to-fill by default.
 */
public class MainActivity extends Activity {
    ImageView iv1, iv2, iv3, iv4, iv5, iv6, iv7, iv8;

    void row(String tag, ImageView v) {
        android.graphics.drawable.Drawable d = v.getDrawable();
        String st = (v.getScaleType() == null) ? "null"
                : v.getScaleType().toString();
        System.err.println("[C99-IM] " + tag + " st=" + st
                + " mw=" + v.getMeasuredWidth()
                + " mh=" + v.getMeasuredHeight()
                + " drawable=" + (d != null)
                + " iw=" + (d != null ? d.getIntrinsicWidth() : -1)
                + " ih=" + (d != null ? d.getIntrinsicHeight() : -1));
    }

    void dump(String phase) {
        System.err.println("[C99-IMPHASE] " + phase);
        row("iv1", iv1);
        row("iv2", iv2);
        row("iv3", iv3);
        row("iv4", iv4);
        row("iv5", iv5);
        row("iv6", iv6);
        row("iv7", iv7);
        row("iv8", iv8);
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        setContentView(R.layout.main);
        iv1 = (ImageView) findViewById(R.id.iv1);
        iv2 = (ImageView) findViewById(R.id.iv2);
        iv3 = (ImageView) findViewById(R.id.iv3);
        iv4 = (ImageView) findViewById(R.id.iv4);
        iv5 = (ImageView) findViewById(R.id.iv5);
        iv6 = (ImageView) findViewById(R.id.iv6);
        iv7 = (ImageView) findViewById(R.id.iv7);
        iv8 = (ImageView) findViewById(R.id.iv8);
        System.err.println("[C99-IMVER] V1-C99IM");
        new Handler(Looper.getMainLooper()).postDelayed(new Runnable() {
            public void run() {
                try {
                    dump("PHASE1");
                    iv1.setScaleType(ImageView.ScaleType.FIT_XY);
                    System.err.println("[C99-IMSWITCH] iv1 -> FIT_XY st="
                            + iv1.getScaleType());
                    iv1.requestLayout();
                    System.err.println("[C99-IMDONE] printed");
                } catch (Throwable t) {
                    System.err.println("[C99-IMERR] " + t);
                }
            }
        }, 1200);
    }
}
