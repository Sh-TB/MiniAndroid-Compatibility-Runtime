/*
 * MiniAndroid TICTACTOE-GOLDEN fixture — the §9/§10/§11 "ONE COMPLETE APK"
 * proof for a View/DEX-based interactive app.
 *
 * What it exercises, end to end, through REAL DEX bytecode:
 *   Activity.onCreate → programmatic View tree (nested LinearLayouts +
 *   9 Buttons + status TextView) → per-cell INNER-CLASS OnClickListener
 *   (Outer$Inner DEX path) → click dispatch → state mutation (board[],
 *   turn switch) → setText → invalidate → re-render → SECOND FRAME.
 *   Win/draw detection runs real Java control flow over the board array.
 *
 * Determinism: no clocks, no randomness, no ambient state — identical
 * click sequences must produce byte-identical frame sequences.
 *
 * License: MIT.
 */
package com.miniandroid.tictactoegolden;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    // Board cell marks: 0 = empty, 'X' or 'O'.
    private final char[] board = new char[9];
    private char turn = 'X';
    private int moves = 0;
    private boolean gameOver = false;

    private TextView status;
    private final Button[] cells = new Button[9];

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);      // 1 = VERTICAL

        status = new TextView(this);
        status.setText("X to move");
        LinearLayout.LayoutParams statusLp =
            new LinearLayout.LayoutParams(-1, -2);       // MATCH_PARENT, WRAP_CONTENT
        root.addView(status, statusLp);

        for (int r = 0; r < 3; r++) {
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL); // 0 = HORIZONTAL
            // Each row takes exactly one third of the column height.
            LinearLayout.LayoutParams rowLp =
                new LinearLayout.LayoutParams(-1, 0, 1.0f);
            root.addView(row, rowLp);

            for (int c = 0; c < 3; c++) {
                final int idx = r * 3 + c;
                Button b = new Button(this);
                b.setText("");
                // Every cell fills one third of the row width, full height.
                LinearLayout.LayoutParams cellLp =
                    new LinearLayout.LayoutParams(0, -1, 1.0f);
                b.setOnClickListener(new CellListener(idx));
                cells[idx] = b;
                row.addView(b, cellLp);
            }
        }

        setContentView(root);
    }

    /** Inner class listener — exercises the Outer$Inner DEX class path. */
    class CellListener implements View.OnClickListener {
        private final int idx;

        CellListener(int idx) {
            this.idx = idx;
        }

        @Override
        public void onClick(View v) {
            if (gameOver || board[idx] != 0) {
                return;
            }
            board[idx] = turn;
            cells[idx].setText(turn == 'X' ? "X" : "O");
            moves++;

            if (wins(turn)) {
                status.setText(turn + " WINS");
                gameOver = true;
            } else if (moves == 9) {
                status.setText("DRAW");
                gameOver = true;
            } else {
                turn = (turn == 'X') ? 'O' : 'X';
                status.setText(turn + " to move");
            }
        }
    }

    /** Real win detection over the board array (rows, columns, diagonals). */
    private boolean wins(char p) {
        for (int i = 0; i < 3; i++) {
            if (board[i * 3] == p && board[i * 3 + 1] == p && board[i * 3 + 2] == p) {
                return true;   // row i
            }
            if (board[i] == p && board[i + 3] == p && board[i + 6] == p) {
                return true;   // column i
            }
        }
        return (board[0] == p && board[4] == p && board[8] == p)
            || (board[2] == p && board[4] == p && board[6] == p);
    }
}
