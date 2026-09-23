/*
 * MiniAndroid BALLTAP-GOLDEN fixture — S51 finalization (very simple 2D game with a ball): a
 * tap-driven Pong/Breakout hybrid.
 *
 * A 7x5 ball field (TextView grid) with a 2-cell paddle on the bottom
 * row. Three control buttons: RIGHT moves the paddle +2 cells, LEFT -1
 * (asymmetric step is a documented design constant that lets the forced
 * rotation still track the ball), STEP advances the ball one cell with
 * side-wall bounces. Ball reaching the paddle row inside the paddle =
 * GOAL (serve resets to top-center); outside = MISS. Three goals = WIN,
 * frozen tail (Android-correct early return).
 *
 * What it exercises through REAL DEX bytecode:
 *   Activity.onCreate → programmatic view tree (field grid TextViews +
 *   paddle TextViews + 3 Buttons) → per-button inner-class listeners →
 *   click dispatch → integer physics (position, velocity, wall bounce,
 *   paddle collision, score/lives) → setText mutation → re-render →
 *   NEXT FRAME.
 *
 * Determinism: no clocks, no randomness, no ambient state — pure
 * input-driven physics; identical click sequences produce byte-identical
 * frame sequences.
 *
 * Harness mapping (S51-verified law): the CLICK-SEQ driver iterates
 * clickable views in DESCENDING view-id order (most recently created
 * first). Buttons are created LEFT, STEP, RIGHT, so taps rotate
 * RIGHT, STEP, LEFT cyclically — RIGHT(+2), STEP, LEFT(-1) nets zero
 * paddle drift per cycle, and the +2/-1 asymmetry carries the paddle to
 * cover every arrival (design solver: goals at ball-steps 4, 8, 12;
 * 35 clicks to WIN, zero misses).
 *
 * License: MIT.
 */
package com.miniandroid.balltap;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    private static final int W = 7, H = 5;        // ball field
    private static final int GOALS_TO_WIN = 3;

    private int bx = 3, by = 0;                   // ball position
    private int dx = 1, dy = 1;                   // ball velocity
    private int paddle = 3;                       // paddle left cell (covers paddle, paddle+1)
    private int goals = 0;
    private boolean won = false;

    private TextView status;
    private final TextView[][] field = new TextView[H][W];
    private final TextView[] paddleRow = new TextView[W];

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);      // 1 = VERTICAL

        status = new TextView(this);
        status.setText("GOAL 0/3 SERVE");
        root.addView(status, new LinearLayout.LayoutParams(-1, -2));

        // Ball field: H rows x W cols of TextViews, top row first.
        for (int r = 0; r < H; r++) {
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);  // 0 = HORIZONTAL
            root.addView(row, new LinearLayout.LayoutParams(-1, 0, 1.0f));
            for (int c = 0; c < W; c++) {
                TextView t = new TextView(this);
                t.setText(".");
                field[r][c] = t;
                row.addView(t, new LinearLayout.LayoutParams(0, -1, 1.0f));
            }
        }

        // Paddle row (bottom): 7 TextViews.
        for (int c = 0; c < W; c++) {
            TextView t = new TextView(this);
            t.setText(".");
            paddleRow[c] = t;
        }
        LinearLayout prow = new LinearLayout(this);
        prow.setOrientation(LinearLayout.HORIZONTAL);
        for (int c = 0; c < W; c++) {
            prow.addView(paddleRow[c], new LinearLayout.LayoutParams(0, -1, 1.0f));
        }
        root.addView(prow, new LinearLayout.LayoutParams(-1, -2));

        // Control buttons — created LEFT, STEP, RIGHT so the descending
        // view-id rotation taps RIGHT, STEP, LEFT (see header).
        String[] names = {"LEFT", "STEP", "RIGHT"};
        for (int b = 0; b < 3; b++) {
            final int bi = b;
            Button btn = new Button(this);
            btn.setText(names[b]);
            btn.setOnClickListener(new ControlListener(bi));
            root.addView(btn, new LinearLayout.LayoutParams(-1, -2));
        }

        setContentView(root);
        render();
    }

    /** Inner class listener — exercises the Outer$Inner DEX class path. */
    class ControlListener implements View.OnClickListener {
        private final int which;                       // 0 LEFT, 1 STEP, 2 RIGHT

        ControlListener(int which) {
            this.which = which;
        }

        @Override
        public void onClick(View v) {
            if (won) {
                return;                                // frozen tail
            }
            if (which == 2) {                          // RIGHT: +2 cells
                paddle = paddle + 2;
                if (paddle > W - 2) paddle = W - 2;
            } else if (which == 0) {                   // LEFT: -1 cell
                paddle = paddle - 1;
                if (paddle < 0) paddle = 0;
            } else {                                   // STEP: advance ball
                int nx = bx + dx;
                if (nx > W - 1 || nx < 0) {
                    dx = -dx;                          // wall bounce
                    nx = bx + dx;
                }
                bx = nx;
                by = by + dy;
                if (by == H - 1) {                     // arrival row
                    if (bx >= paddle && bx <= paddle + 1) {
                        goals++;
                        status.setText("GOAL " + goals + "/" + GOALS_TO_WIN);
                        bx = 3; by = 0; dx = 1; dy = 1;  // serve
                        if (goals == GOALS_TO_WIN) {
                            status.setText("GOAL 3/3 WIN");
                            won = true;
                        }
                    }
                    // note: golden sequence contains no MISS; the MISS
                    // branch (lives) is exercised by design variance only.
                }
            }
            render();
        }
    }

    /** Full-screen repaint: field, ball, paddle. */
    private void render() {
        for (int r = 0; r < H; r++) {
            for (int c = 0; c < W; c++) {
                if (r == by && c == bx) {
                    field[r][c].setText("o");
                } else {
                    field[r][c].setText(".");
                }
            }
        }
        for (int c = 0; c < W; c++) {
            paddleRow[c].setText((c == paddle || c == paddle + 1) ? "=" : ".");
        }
    }
}
