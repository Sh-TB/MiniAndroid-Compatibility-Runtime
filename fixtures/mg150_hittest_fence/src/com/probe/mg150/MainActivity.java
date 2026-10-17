package com.probe.mg150;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;

/**
 * MG-150 dedicated transform hit-test fence (issue #364 FOUNDATION
 * addendum MG-150 — translated view hit testing).
 *
 * Laws under test:
 *   AOSP View.java: translationX/Y offsets the view's visual AND touchable
 *   geometry (mRenderNode offsets apply to both draw and hit testing —
 *   input maps through the inverse of the render transform).
 *
 * Recorded MiniAndroid semantics (this fence LOCKS them):
 *   - translation get/set properties implemented (MG-150 original note);
 *   - hit-test consumes LAYOUT bounds only (axis-aligned), translation is
 *     NOT consumed by hit-test NOR by the render walk (F-NEW-359 records
 *     rotation-about-pivot as the frontier; the translation delta is the
 *     named sibling frontier).
 *
 * Rows:
 *   MG150-GEOM  layout bounds + translation readbacks
 *   MG150-CLICK fires from the button's OnClickListener (AOSP PerformClick)
 *   MG150-VERSION identity
 *
 * Harness contract (scripts/cont76_fence_mg150.sh):
 *   tap A 150,150  -> inside LAYOUT bounds  (100..300 x 100..200): the
 *                     engine's hit walk targets the button; MG150-CLICK
 *                     MUST appear (current law, GREEN).
 *   tap B 450,350  -> inside TRANSLATED visual bounds only (400..600 x
 *                     300..400): AOSP would target the button; the engine
 *                     records "no touch target" (the documented deviation —
 *                     MG150-CLICK MUST NOT appear; the deviation row is the
 *                     named frontier, NOT a silent gap).
 */
public class MainActivity extends Activity {

    public static final String VERSION = "V1-MG150";
    private static int clicks = 0;

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        System.err.println("[MG150-VERSION] code=" + VERSION);

        FrameLayout root = new FrameLayout(this);
        Button btn = new Button(this);
        btn.setText("T");
        btn.setClickable(true);
        FrameLayout.LayoutParams lp =
                new FrameLayout.LayoutParams(200, 100);
        // layout margins place the button at (100,100) size 200x100
        lp.leftMargin = 100;
        lp.topMargin = 100;
        root.addView(btn, lp);

        btn.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                clicks++;
                System.err.println("[MG150-CLICK] count=" + clicks
                        + " view=" + v.getClass().getSimpleName());
            }
        });

        // transform properties (MG-150's implemented half)
        btn.setTranslationX(300.0f);
        btn.setTranslationY(200.0f);
        System.err.println("[MG150-GEOM] layout=(100,100) size=(200,100)"
                + " tx=" + btn.getTranslationX() + " ty=" + btn.getTranslationY());

        setContentView(root);
    }
}
