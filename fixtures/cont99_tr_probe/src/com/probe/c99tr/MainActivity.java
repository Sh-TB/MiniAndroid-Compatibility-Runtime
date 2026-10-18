package com.probe.c99tr;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.DisplayMetrics;
import android.util.TypedValue;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;

/**
 * CONT-99 T2 — parent/child coordinate transforms, density and window
 * insets probe (V1).
 *
 * Deterministic px tree (window 1080x1920), all rows full-width, stacked:
 *   root LinearLayout VERTICAL match x match (no padding)
 *     rowA FrameLayout 1080x300  abs (0,0)
 *       childB View 100x50 margins (100,50,0,0)   parent-rel (100,50)
 *                                               abs (100,50)  [control row:
 *                                               parent at origin so the
 *                                               parent-relative law and the
 *                                               absolute accident agree]
 *     rowC FrameLayout 1080x300  abs (0,300)
 *       childD View 100x50 tx=30 ty=20, click -> D
 *                                   parent-rel (0,0)   abs (0,300)
 *                                   visual (30,320,100,50)
 *       AOSP getLeft/getTop are PARENT-RELATIVE: expected (0,0).
 *       An absolute-coordinate implementation prints (0,300) here —
 *       that is the local-vs-parent discriminator.
 *     rowE FrameLayout 1080x300  abs (0,600)
 *       childF View 100x50 scaleX=scaleY=2, click -> F
 *                                   abs (0,600); pivot lazy-center (50,25)
 *                                   visual (-50,575,200,100)  [F-NEW-359
 *                                   draw law: origin + pivot*(1-scale)]
 *     rowG LinearLayout 1080x300 scrollY=150  abs (0,900)
 *       childH Button 200x80 click -> H           abs (0,900)
 *                                   visual (draw): shifted -150 and
 *                                   clipped by rowG -> NOT visible.
 *       scroll law: a tap at y P maps to laid-out y P+scrollY; the tap
 *       pipeline must NOT hit childH at its stale laid-out region.
 *     rowI FrameLayout 1080x220  abs (0,1200)
 *       childI2 View 100x50 rotation=90   [STATE row only: rotation draw +
 *       hit matrix is the recorded F-NEW-359 frontier; hit must not exceed
 *       what the raster actually paints]
 *
 * Evidence rows:
 *   [C99-FRAME] laid-out skeleton (unshifted by transforms — AOSP law:
 *               translation/scale/rotation/scroll never change layout)
 *   [C99-LOC]   left/top (parent-relative law) + getLocationOnScreen/
 *               getLocationInWindow (parent-chain-sum law == the absolute
 *               window position)
 *   [C99-TX]    getTranslationX/Y + getX()/getY() (= left + translation)
 *   [C99-SC]    getScaleX/Y + lazy-center pivot law (F-NEW-359)
 *   [C99-ROT]   getRotation state
 *   [C99-SCRLL] scroll state + "scroll does not relayout" law
 *   [C99-DENS]  DisplayMetrics + TypedValue.applyDimension consistency
 *               (applyDimension(100dp) == 100*density — whatever density
 *               the runtime reports, it must be self-consistent)
 *   [C99-INSET] honest inset report (dispatched or unsupported)
 *   [C99-TAP]   per-view click rows; [C99-COUNT] settled counters
 *
 * Harness pairing (deterministic, one tap per run):
 *   --tap 150,75  -> B=1 only        (pure pipeline control, no transforms)
 *   --tap 110,340 -> D=1 by LAW      (inside the TRANSLATED rect (30..130,
 *                                     320..370), outside the untranslated
 *                                     (0..100, 300..350))
 *   --tap 120,650 -> F=1 by LAW      (inside the SCALED rect (-50..150,
 *                                     575..675), outside the untranslated
 *                                     (0..100, 600..650))
 *   --tap 100,930 -> H=0 by LAW      (930+scrollY(150)=1080 is outside H's
 *                                     laid-out (0..200, 900..980); the raw-
 *                                     bounds pipeline would fire H on the
 *                                     stale region of a scrolled-away,
 *                                     visually clipped control)
 * Hit-test coordinates must agree with the raster: what is painted is what
 * is tappable — nothing more, nothing less.
 */
public class MainActivity extends Activity {
    LinearLayout root, rowG;
    FrameLayout rowA, rowC, rowE, rowI;
    View childB, childD, childF, childI2;
    Button childH;
    int bClicks = 0, dClicks = 0, fClicks = 0, hClicks = 0;

    void bounds(String tag, View v, int el, int et, int ew, int eh) {
        int l = v.getLeft(), t = v.getTop();
        int w = v.getWidth(), h = v.getHeight();
        String verdict = (l == el && t == et && w == ew && h == eh)
                ? "OK" : "DIVERGE";
        System.err.println("[C99-FRAME] " + tag
                + " l=" + l + " t=" + t + " w=" + w + " h=" + h
                + " exp=" + el + "/" + et + "/" + ew + "/" + eh
                + " v=" + verdict);
    }

    void loc(String tag, View v, int el, int et, int esx, int esy) {
        int l = v.getLeft(), t = v.getTop();
        String v1 = (l == el && t == et) ? "OK" : "DIVERGE";
        String scr, win, v2, v3;
        try {
            int[] a = new int[2];
            v.getLocationOnScreen(a);
            scr = a[0] + "/" + a[1];
            v2 = (a[0] == esx && a[1] == esy) ? "OK" : "DIVERGE";
        } catch (Throwable e) {
            scr = "ERR:" + e.getClass().getSimpleName();
            v2 = "DIVERGE";
        }
        try {
            int[] a = new int[2];
            v.getLocationInWindow(a);
            win = a[0] + "/" + a[1];
            v3 = (a[0] == esx && a[1] == esy) ? "OK" : "DIVERGE";
        } catch (Throwable e) {
            win = "ERR:" + e.getClass().getSimpleName();
            v3 = "DIVERGE";
        }
        System.err.println("[C99-LOC] " + tag
                + " left=" + l + " top=" + t + " exp=" + el + "/" + et
                + " v=" + v1
                + " | onScreen=" + scr + " exp=" + esx + "/" + esy + " v=" + v2
                + " | inWindow=" + win + " v=" + v3);
    }

    void dump() {
        System.err.println("[C99-PHASE] settled");
        // 1. layout skeleton — transforms/scroll must NOT shift layout
        bounds("rowA", rowA, 0, 0, 1080, 300);
        bounds("rowC", rowC, 0, 300, 1080, 300);
        bounds("rowE", rowE, 0, 600, 1080, 300);
        bounds("rowG", rowG, 0, 900, 1080, 300);
        bounds("rowI", rowI, 0, 1200, 1080, 220);
        // 2. local vs parent vs screen frames
        //    childB: parent at origin -> parent-relative == absolute
        loc("childB", childB, 100, 50, 100, 50);
        //    childD: rowC at y=300 -> AOSP parent-relative (0,0);
        //    screen (0,300). An absolute impl prints left/top (0,300).
        loc("childD", childD, 0, 0, 0, 300);
        //    childH: rowG at y=900 -> parent-relative (0,0), screen (0,900)
        loc("childH", childH, 0, 0, 0, 900);
        // 3. translation state + getX/getY law (left + translation)
        System.err.println("[C99-TX] childD tx=" + childD.getTranslationX()
                + " ty=" + childD.getTranslationY()
                + " getX=" + childD.getX() + " expX=30.0"
                + " getY=" + childD.getY() + " expY=20.0");
        // 4. scale state + lazy-center pivot law
        System.err.println("[C99-SC] childF scaleX=" + childF.getScaleX()
                + " scaleY=" + childF.getScaleY()
                + " pivotX=" + childF.getPivotX() + " expPivotX=50.0"
                + " pivotY=" + childF.getPivotY() + " expPivotY=25.0");
        // 5. rotation state (draw/hit matrix = recorded frontier)
        System.err.println("[C99-ROT] childI2 rotation=" + childI2.getRotation()
                + " exp=90.0");
        // 6. scroll law: state stored, layout untouched
        System.err.println("[C99-SCRLL] rowG scrollY=" + rowG.getScrollY()
                + " exp=150 childH left=" + childH.getLeft()
                + " top=" + childH.getTop()
                + " exp=0/0 (scroll never relayouts)");
        // 7. density consistency (applyDimension(100dp) == 100*density)
        try {
            DisplayMetrics dm = getResources().getDisplayMetrics();
            float d = dm.density;
            float applied = TypedValue.applyDimension(
                    TypedValue.COMPLEX_UNIT_DIP, 100, dm);
            boolean ok = Math.abs(applied - 100f * d) < 0.01f;
            System.err.println("[C99-DENS] density=" + d + " dpi=" + dm.densityDpi
                    + " px=" + dm.widthPixels + "x" + dm.heightPixels
                    + " applyDim100dp=" + applied
                    + " exp=" + (100f * d) + " v=" + (ok ? "OK" : "DIVERGE"));
        } catch (Throwable e) {
            System.err.println("[C99-DENS] ERR:" + e.getClass().getSimpleName());
        }
        // 8. insets — honest report (dispatched / null / unsupported)
        try {
            View dv = getWindow().getDecorView();
            Object wi = dv.getRootWindowInsets();
            System.err.println("[C99-INSET] rootWindowInsets="
                    + ((wi == null) ? "null" : wi.toString()));
        } catch (Throwable e) {
            System.err.println("[C99-INSET] rootWindowInsets ERR:"
                    + e.getClass().getSimpleName());
        }
        // 9. settled counters (tap runs print their rows before this)
        System.err.println("[C99-COUNT] B=" + bClicks + " D=" + dClicks
                + " F=" + fClicks + " H=" + hClicks);
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        setContentView(root);

        // rowA — control row (parent at origin)
        rowA = new FrameLayout(this);
        rowA.setBackgroundColor(0xFF2244CC);
        root.addView(rowA, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 300));
        childB = new View(this);
        childB.setBackgroundColor(0xFFCC2222);
        childB.setOnClickListener(v -> {
            bClicks++;
            System.err.println("[C99-TAP] B count=" + bClicks);
        });
        FrameLayout.LayoutParams lb = new FrameLayout.LayoutParams(100, 50);
        lb.setMargins(100, 50, 0, 0);
        rowA.addView(childB, lb);

        // rowC — translation row
        rowC = new FrameLayout(this);
        rowC.setBackgroundColor(0xFF22CC44);
        root.addView(rowC, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 300));
        childD = new View(this);
        childD.setBackgroundColor(0xFFCCCC22);
        childD.setOnClickListener(v -> {
            dClicks++;
            System.err.println("[C99-TAP] D count=" + dClicks);
        });
        rowC.addView(childD, new FrameLayout.LayoutParams(100, 50));
        childD.setTranslationX(30);
        childD.setTranslationY(20);

        // rowE — scale row
        rowE = new FrameLayout(this);
        rowE.setBackgroundColor(0xFF4422CC);
        root.addView(rowE, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 300));
        childF = new View(this);
        childF.setBackgroundColor(0xFF22CCCC);
        childF.setOnClickListener(v -> {
            fClicks++;
            System.err.println("[C99-TAP] F count=" + fClicks);
        });
        rowE.addView(childF, new FrameLayout.LayoutParams(100, 50));
        childF.setScaleX(2.0f);
        childF.setScaleY(2.0f);

        // rowG — scroll row (content scrolled away; H visually clipped)
        rowG = new LinearLayout(this);
        rowG.setBackgroundColor(0xFF884422);
        root.addView(rowG, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 300));
        childH = new Button(this);
        childH.setText("H");
        childH.setBackgroundColor(0xFFEEEEEE);
        childH.setOnClickListener(v -> {
            hClicks++;
            System.err.println("[C99-TAP] H count=" + hClicks
                    + " (STALE-REGION-LAW-VIOLATION if scrolled away)");
        });
        rowG.addView(childH, new LinearLayout.LayoutParams(200, 80));
        rowG.setScrollY(150);

        // rowI — rotation state row
        rowI = new FrameLayout(this);
        rowI.setBackgroundColor(0xFF225577);
        root.addView(rowI, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 220));
        childI2 = new View(this);
        childI2.setBackgroundColor(0xFFCC22CC);
        rowI.addView(childI2, new FrameLayout.LayoutParams(100, 50));
        childI2.setRotation(90.0f);

        System.err.println("[C99-VER] V1-C99TR");
        new Handler(Looper.getMainLooper()).postDelayed(
                new Runnable() { public void run() {
                    try { dump(); System.err.println("[C99-DONE] printed"); }
                    catch (Throwable t) { System.err.println("[C99-ERR] " + t); }
                }}, 1200);
    }
}
