package com.probe.c99cv;

import android.app.Activity;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.View;
import android.widget.LinearLayout;

/**
 * CONT-99 T7 — canvas save/restore, clipping, saveLayer isolation and
 * invalidation probe (V1-C99CV). One custom 300x300 view drawn with a fully
 * deterministic sequence, then a BLUE 300x100 sibling BELOW it:
 *
 *   sequence inside onDraw:
 *     s0 = getSaveCount()            (AOSP baseline == 1)
 *     save() -> clipRect(0,0,150,300) -> drawRect RED 300x300
 *     s1 = getSaveCount()            (== 2)
 *     restore() -> s2 = getSaveCount() (back to 1)
 *     drawRect GREEN right half (150,0,300,300)   [restore MUST have
 *       cleared the clip, else right half stays white]
 *     save() -> clipRect(0,0,0,10) [empty clip]
 *       quickReject(0,0,100,100) MUST be true; getClipBounds() null
 *     restore()
 *     restore() with saveCount==1 [underflow: must be a safe no-op,
 *       saveCount stays 1, no crash]
 *     saveLayer(0,0,100,100) -> drawRect YELLOW 300x300 -> restore()
 *       [layer composite: yellow ONLY in (0..100,0..100); the rest of
 *       the canvas must keep its previous content]
 *     final saveCount == 1 (balanced)
 *
 *   raster laws:
 *     P1 (75,150)  RED    (clip confined the first rect)
 *     P2 (225,150) GREEN  (restore cleared the clip)
 *     P3 (50,50)   YELLOW (saveLayer composite region)
 *     P4 (225,50)  GREEN  (outside layer keeps previous content)
 *     P5 (150,350) BLUE   (sibling below — no clip/layer leak into
 *                          later siblings)
 */
public class MainActivity extends Activity {

    static class CV extends View {
        Paint red = new Paint(); Paint green = new Paint();
        Paint yellow = new Paint();
        String trace = "";
        CV(Context ctx) {
            super(ctx);
            red.setColor(0xFFCC2222);
            green.setColor(0xFF22CC22);
            yellow.setColor(0xFFCCCC22);
        }
        @Override protected void onDraw(Canvas c) {
            c.drawColor(0xFFFFFFFF);
            int s0 = c.getSaveCount();
            c.save();
            c.clipRect(0f, 0f, 150f, 300f);
            c.drawRect(0f, 0f, 300f, 300f, red);
            int s1 = c.getSaveCount();
            c.restore();
            int s2 = c.getSaveCount();
            c.drawRect(150f, 0f, 300f, 300f, green);
            c.save();
            c.clipRect(0f, 0f, 0f, 10f);
            boolean qr = c.quickReject(0f, 0f, 100f, 100f);
            android.graphics.Rect cb = c.getClipBounds();
            System.err.println("[C99-CV] emptyclip quickReject=" + qr
                    + " clipBoundsNull=" + (cb == null)
                    + " sc=" + c.getSaveCount());
            c.restore();
            int before = c.getSaveCount();
            c.restore();
            int after = c.getSaveCount();
            System.err.println("[C99-CV] underflow before=" + before
                    + " after=" + after);
            c.saveLayer(0f, 0f, 100f, 100f, null);
            c.drawRect(0f, 0f, 300f, 300f, yellow);
            c.restore();
            int sf = c.getSaveCount();
            trace = "s0=" + s0 + " s1=" + s1 + " s2=" + s2 + " sf=" + sf;
            System.err.println("[C99-CV] trace " + trace);
            System.err.println("[C99-CVDONE] printed");
        }
    }

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFFEEEEEE);

        CV cv = new CV(this);
        LinearLayout.LayoutParams lp1 =
                new LinearLayout.LayoutParams(300, 300);
        lp1.topMargin = 20;
        cv.setLayoutParams(lp1);

        View sib = new View(this);
        sib.setBackgroundColor(0xFF2222CC);
        LinearLayout.LayoutParams lp2 =
                new LinearLayout.LayoutParams(300, 100);
        lp2.topMargin = 20;
        sib.setLayoutParams(lp2);

        root.addView(cv); root.addView(sib);
        setContentView(root);
        System.err.println("[C99-CVVER] V1-C99CV");
    }
}
