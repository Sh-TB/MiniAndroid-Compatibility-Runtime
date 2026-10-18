package com.probe.c99btn;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;

/**
 * CONT-99 T4 — Button/control bounds, state and click-target probe (V1).
 *
 * Deterministic px tree (window 1080x1920):
 *   root LinearLayout VERTICAL match x match
 *     row1 LinearLayout HORIZONTAL 1080x120  (no padding)
 *       btnA Button 300x100 bg #FFCC2222  onClick -> [C99-BTN] A
 *       btnB Button 200x80  bg #FF22CC22  onClick -> [C99-BTN] B
 *         (adjacent, DIFFERENT sizes; btnA x=0..300, btnB x=300..500,
 *          btnB height 80 < row 120 -> top-aligned cross-axis; the point
 *          (700,60) is inside row1 but inside NEITHER button)
 *     btnC Button 200x80 bg #FF2222CC  setEnabled(false) -> tap must NOT fire
 *
 * Evidence rows:
 *   [C99-LAY]  laid-out bounds of each control (extends the T1 contract to
 *              a row with two children of different heights)
 *   [C99-BTN]  per-button onClick rows (one per real dispatch) + a settled
 *              state dump (isEnabled/isPressed/isClickable)
 *
 * Harness pairing (deterministic, one tap per run):
 *   run --click-test        -> A row + B row + NO C row (disabled law)
 *   run --tap 150,50        -> A row only (btnA center)
 *   run --tap 700,60        -> NO rows (between-buttons negative)
 *   run --tap 100,190       -> NO C row (disabled control at its center)
 * A correctly drawn button with a wrong hitbox is not a pass: the tap
 * pipeline MUST hit-test the real laid-out bounds.
 */
public class MainActivity extends Activity {
    LinearLayout root, row1;
    Button btnA, btnB, btnC;
    int aClicks = 0, bClicks = 0, cClicks = 0;

    void bounds(String tag, View v, int el, int et, int ew, int eh) {
        int l = v.getLeft(), t = v.getTop();
        int w = v.getWidth(), h = v.getHeight();
        String verdict = (l == el && t == et && w == ew && h == eh)
                ? "OK" : "DIVERGE";
        System.err.println("[C99-LAY] " + tag
                + " l=" + l + " t=" + t + " w=" + w + " h=" + h
                + " exp=" + el + "/" + et + "/" + ew + "/" + eh
                + " v=" + verdict);
    }

    void dump(String phase) {
        System.err.println("[C99-PHASE] " + phase);
        bounds("btnA", btnA, 0, 0, 300, 100);
        bounds("btnB", btnB, 300, 0, 200, 80);
        bounds("btnC", btnC, 0, 120, 200, 80);
        System.err.println("[C99-STATE] A enabled=" + btnA.isEnabled()
                + " clickable=" + btnA.isClickable()
                + " pressed=" + btnA.isPressed()
                + " | B enabled=" + btnB.isEnabled()
                + " pressed=" + btnB.isPressed()
                + " | C enabled=" + btnC.isEnabled()
                + " clickable=" + btnC.isClickable());
        System.err.println("[C99-COUNT] A=" + aClicks + " B=" + bClicks
                + " C=" + cClicks);
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        setContentView(root);

        row1 = new LinearLayout(this);
        row1.setOrientation(LinearLayout.HORIZONTAL);
        root.addView(row1, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 120));

        btnA = new Button(this);
        btnA.setText("A");
        btnA.setBackgroundColor(0xFFCC2222);
        btnA.setOnClickListener(v -> {
            aClicks++;
            System.err.println("[C99-BTN] A onClick count=" + aClicks);
        });
        row1.addView(btnA, new LinearLayout.LayoutParams(300, 100));

        btnB = new Button(this);
        btnB.setText("B");
        btnB.setBackgroundColor(0xFF22CC22);
        btnB.setOnClickListener(v -> {
            bClicks++;
            System.err.println("[C99-BTN] B onClick count=" + bClicks);
        });
        row1.addView(btnB, new LinearLayout.LayoutParams(200, 80));

        btnC = new Button(this);
        btnC.setText("C-disabled");
        btnC.setBackgroundColor(0xFF2222CC);
        btnC.setEnabled(false);
        btnC.setOnClickListener(v -> {
            cClicks++;
            System.err.println("[C99-BTN] C onClick count=" + cClicks
                    + " (DISABLED-LAW-VIOLATION)");
        });
        root.addView(btnC, new LinearLayout.LayoutParams(200, 80));

        System.err.println("[C99-VER] V1-C99BTN");
        new Handler(Looper.getMainLooper()).postDelayed(
                new Runnable() { public void run() {
                    try { dump("SETTLED"); System.err.println("[C99-DONE] printed"); }
                    catch (Throwable t) { System.err.println("[C99-ERR] " + t); }
                }}, 1200);
    }
}
