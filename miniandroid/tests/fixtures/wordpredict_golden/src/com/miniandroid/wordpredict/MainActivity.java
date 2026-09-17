/*
 * MiniAndroid WORDPREDICT-GOLDEN fixture — S51 finalization
 * "پیش‌بینی کلمات" (word prediction): a simple quiz app class.
 *
 * Five questions; each shows a sentence with a blank and four candidate
 * word buttons (candidates re-labeled per question). A correct tap scores
 * and advances; a wrong tap shows WRONG — try again and keeps the
 * question. Question 2 deliberately has its correct answer on a button
 * the forced tap rotation reaches SECOND, proving the wrong-answer path
 * (status flash + retry) through real DEX bytecode. After question 5 the
 * app freezes at SCORE 5/5 DONE (Android-correct early return).
 *
 * What it exercises through REAL DEX bytecode:
 *   Activity.onCreate → programmatic view tree (status TextView + 4
 *   candidate Buttons) → per-button inner-class OnClickListener → click
 *   dispatch → String[] question table mutation (re-labeling per
 *   question) → conditional scoring → setText → re-render → NEXT FRAME.
 *
 * Determinism: no clocks, no randomness, no ambient state.
 *
 * Harness mapping (S51-verified law): the CLICK-SEQ driver iterates
 * clickable views in DESCENDING view-id order (most recently created
 * first). Buttons are created b0,b1,b2,b3 left-to-right, so taps rotate
 * b3,b2,b1,b0 cyclically. Engineered mapping (design solver):
 *   q1 correct=b3 (click1), q2 correct=b2 (click2),
 *   q3 correct=b0 (click3 WRONG on b1, click4 correct on b0),
 *   q4 correct=b3 (click5), q5 correct=b2 (click6) → SCORE 5/5 DONE.
 *
 * License: MIT.
 */
package com.miniandroid.wordpredict;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    // Question table: prefix, correct answer, 4 candidates (b0..b3).
    private static final String[] PREFIX = {
        "The sky on a clear day is",
        "Water boils when it is",
        "A baby cat is called a",
        "Two plus two equals",
        "The opposite of night is",
    };
    private static final String[][] CANDS = {
        {"red", "big", "run", "blue"},
        {"cold", "hot", "wet", "ice"},
        {"puppy", "calf", "kitten", "cub"},
        {"five", "ten", "two", "four"},
        {"dark", "day", "noon", "star"},
    };
    private static final int[] CORRECT = {3, 2, 0, 3, 2}; // button index

    private int q = 0;          // current question index
    private int score = 0;
    private boolean done = false;

    private TextView status;
    private TextView question;
    private final Button[] btns = new Button[4];

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);      // 1 = VERTICAL

        status = new TextView(this);
        status.setText("Q1/5 SCORE 0");
        root.addView(status, new LinearLayout.LayoutParams(-1, -2));

        question = new TextView(this);
        question.setText(PREFIX[0] + " ___");
        root.addView(question, new LinearLayout.LayoutParams(-1, -2));

        for (int b = 0; b < 4; b++) {
            final int bi = b;
            Button btn = new Button(this);
            btn.setText(CANDS[0][b]);
            btn.setOnClickListener(new AnswerListener(bi));
            btns[b] = btn;
            root.addView(btn, new LinearLayout.LayoutParams(-1, -2));
        }

        setContentView(root);
    }

    /** Inner class listener — exercises the Outer$Inner DEX class path. */
    class AnswerListener implements View.OnClickListener {
        private final int idx;

        AnswerListener(int idx) {
            this.idx = idx;
        }

        @Override
        public void onClick(View v) {
            if (done) {
                return;                                   // frozen
            }
            if (idx == CORRECT[q]) {
                score++;
                q++;
                if (q == PREFIX.length) {
                    status.setText("SCORE " + score + "/5 DONE");
                    done = true;
                } else {
                    status.setText("Q" + (q + 1) + "/5 SCORE " + score);
                    question.setText(PREFIX[q] + " ___");
                    for (int b = 0; b < 4; b++) {
                        btns[b].setText(CANDS[q][b]);
                    }
                }
            } else {
                status.setText("WRONG - try again. Q" + (q + 1)
                    + "/5 SCORE " + score);
            }
        }
    }
}
