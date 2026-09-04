/*
 * MiniAndroid execution-proof demo application.
 *
 * Purpose: a minimal, fully open-source Android app whose ONLY job is to make
 * an end-to-end execution of a real APK visible and verifiable:
 *
 *   APK install -> Activity.onCreate (DEX bytecode) -> programmatic View
 *   hierarchy -> setContentView -> rendered frame -> user click -> DEX
 *   onClick -> state change (counter, position, color, text) -> re-render.
 *
 * Every piece of state is encoded in VISIBLE UI so that a screenshot is
 * self-evidencing:
 *   - a title TextView            ("Hello MiniAndroid!")
 *   - a status TextView           ("count=N pos=(x,y) color=NAME")
 *   - a colored box View          (moves + changes color on every click)
 *   - a TAP ME Button             (the interaction that drives state)
 *
 * The UI is built programmatically in Java/DEX (no XML resources) on purpose:
 * it proves the deepest path (real bytecode driving the View API), and the
 * same app compiles with the standard Android toolchain (javac/d8 or
 * gradle) without any resource compilation step.
 *
 * License: MIT.
 */
package com.miniandroid.demo;

import android.app.Activity;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity implements View.OnClickListener {

    // mutable visible state
    private int count = 0;

    private TextView title;
    private TextView status;
    private View box;
    private FrameLayout stage;

    // Box palette (ARGB). Cycle order: red -> green -> blue -> yellow.
    private static final int[] COLORS = {
        0xFFE53935, // red
        0xFF43A047, // green
        0xFF1E88E5, // blue
        0xFFFDD835  // yellow
    };
    private static final String[] COLOR_NAMES = {
        "RED", "GREEN", "BLUE", "YELLOW"
    };

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        title = new TextView(this);
        title.setText("Hello MiniAndroid!");

        status = new TextView(this);
        status.setText(formatState(0, 40, 80, 0));

        box = new View(this);
        box.setBackgroundColor(COLORS[0]);

        stage = new FrameLayout(this);
        placeBox(40, 80);

        Button tap = new Button(this);
        tap.setText("TAP ME");
        tap.setOnClickListener(this);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.addView(title, linearParams(-1, -2));    // MATCH_PARENT x WRAP_CONTENT
        root.addView(status, linearParams(-1, -2));
        root.addView(tap, linearParams(-1, -2));
        root.addView(stage, linearParams(-1, 1300));  // fixed-height stage area

        setContentView(root);
    }

    /** Positions the box inside the stage via FrameLayout margins. */
    private void placeBox(int x, int y) {
        stage.removeView(box);
        FrameLayout.LayoutParams p =
                new FrameLayout.LayoutParams(160, 160, Gravity.TOP | Gravity.LEFT);
        p.width = 160;
        p.height = 160;
        p.gravity = Gravity.TOP | Gravity.LEFT;
        p.leftMargin = x;
        p.topMargin = y;
        stage.addView(box, p);
    }

    /** One interaction step: counter up, color cycles, box moves, text syncs. */
    private void step() {
        count++;
        int ci = count % COLOR_NAMES.length;
        int x = 40 + (count % 5) * 180;
        int y = 80 + (count % 4) * 290;
        box.setBackgroundColor(COLORS[ci]);
        placeBox(x, y);
        status.setText(formatState(count, x, y, ci));
    }

    private static String formatState(int c, int x, int y, int ci) {
        StringBuilder sb = new StringBuilder();
        sb.append("count=").append(c)
          .append(" pos=(").append(x).append(",").append(y).append(")")
          .append(" color=").append(COLOR_NAMES[ci]);
        return sb.toString();
    }

    private static LinearLayout.LayoutParams linearParams(int w, int h) {
        return new LinearLayout.LayoutParams(w, h);
    }

    @Override
    public void onClick(View v) {
        step();
    }
}
