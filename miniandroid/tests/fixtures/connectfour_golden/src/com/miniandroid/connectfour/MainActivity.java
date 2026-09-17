/*
 * MiniAndroid CONNECT-FOUR-GOLDEN fixture — S51 "third board game"
 * generalization proof: a SECOND complete interactive board game proves
 * the runtime's game capability generalizes beyond TicTacToe.
 *
 * What it exercises, end to end, through REAL DEX bytecode:
 *   Activity.onCreate → programmatic View tree (status TextView +
 *   7 column Buttons + 6×7 board TextView grid) → per-column INNER-CLASS
 *   OnClickListener (Outer$Inner DEX path) → click dispatch → gravity
 *   drop (lowest empty row per column) → state mutation (board[][],
 *   turn switch, per-column fill counts) → setText → invalidate →
 *   re-render → NEXT FRAME. Win detection runs real Java control flow
 *   over all 4 directions (rows, columns, both diagonals).
 *
 * Determinism: no clocks, no randomness, no ambient state — identical
 * click sequences must produce byte-identical frame sequences.
 *
 * Harness mapping (S51-verified law): the CLICK-SEQ driver iterates
 * clickable views in DESCENDING view-id order (most recently created
 * first — ViewShadow::find_all_with_click_listener sort law). Column
 * buttons are created left-to-right (col 0..6), so click k targets
 * column (6 - ((k-1) % 7)). Under that mapping the deterministic game
 * ends: Y WINS at click 22 — the r+1,c+1 diagonal (0,3),(1,4),(2,5),
 * (3,6) completes when Y lands at (3,6) (col6's 4th drop; col6 receives
 * clicks 1,8,15,22). Verified against runtime frames + [CLICK-SEQ]
 * dispatch logs at S51 head; clicks 23+ are frozen by gameOver
 * (AOSP-correct early return).
 *
 * License: MIT.
 */
package com.miniandroid.connectfour;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    // board[row][col]; row 0 = BOTTOM (gravity drop law), col 0 = left.
    // Cell value: 0 = empty, 'R' (red) or 'Y' (yellow).
    private final char[][] board = new char[6][7];
    private final int[] colFill = new int[7];
    private char turn = 'R';
    private int drops = 0;
    private boolean gameOver = false;

    private TextView status;
    private final TextView[][] cells = new TextView[6][7];

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);      // 1 = VERTICAL

        status = new TextView(this);
        status.setText("R to move");
        root.addView(status,
            new LinearLayout.LayoutParams(-1, -2));      // MATCH_PARENT, WRAP_CONTENT

        // Column drop buttons — created LEFT to RIGHT so descending
        // view-id discovery maps click k to column 6-((k-1)%7) (see header).
        LinearLayout cols = new LinearLayout(this);
        cols.setOrientation(LinearLayout.HORIZONTAL);    // 0 = HORIZONTAL
        for (int c = 0; c < 7; c++) {
            final int col = c;
            Button b = new Button(this);
            b.setText("C" + c);
            b.setOnClickListener(new ColumnListener(col));
            cols.addView(b, new LinearLayout.LayoutParams(0, -2, 1.0f));
        }
        root.addView(cols, new LinearLayout.LayoutParams(-1, -2));

        // Board grid: 6 display rows, TOP (row 5) first — gravity view.
        for (int dr = 5; dr >= 0; dr--) {
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);
            LinearLayout.LayoutParams rowLp =
                new LinearLayout.LayoutParams(-1, 0, 1.0f);
            root.addView(row, rowLp);
            for (int c = 0; c < 7; c++) {
                final int rr = dr;
                TextView t = new TextView(this);
                t.setText("");
                cells[dr][c] = t;
                row.addView(t, new LinearLayout.LayoutParams(0, -1, 1.0f));
            }
        }

        setContentView(root);
    }

    /** Inner class listener — exercises the Outer$Inner DEX class path. */
    class ColumnListener implements View.OnClickListener {
        private final int col;

        ColumnListener(int col) {
            this.col = col;
        }

        @Override
        public void onClick(View v) {
            if (gameOver || colFill[col] >= 6) {
                return;                                   // frozen or full column
            }
            int row = colFill[col];
            board[row][col] = turn;
            cells[row][col].setText(turn == 'R' ? "R" : "Y");
            colFill[col] = row + 1;
            drops++;

            if (wins(turn)) {
                status.setText(turn + " WINS");
                gameOver = true;
            } else if (drops == 42) {
                status.setText("DRAW");
                gameOver = true;
            } else {
                turn = (turn == 'R') ? 'Y' : 'R';
                status.setText(turn + " to move");
            }
        }
    }

    /** Real win detection: 4-in-a-row, all four directions. */
    private boolean wins(char p) {
        for (int r = 0; r < 6; r++) {
            for (int c = 0; c < 7; c++) {
                if (board[r][c] != p) continue;
                if (c + 3 < 7 && board[r][c + 1] == p && board[r][c + 2] == p && board[r][c + 3] == p) return true;
                if (r + 3 < 6 && board[r + 1][c] == p && board[r + 2][c] == p && board[r + 3][c] == p) return true;
                if (r + 3 < 6 && c + 3 < 7 && board[r + 1][c + 1] == p && board[r + 2][c + 2] == p && board[r + 3][c + 3] == p) return true;
                if (r + 3 < 6 && c - 3 >= 0 && board[r + 1][c - 1] == p && board[r + 2][c - 2] == p && board[r + 3][c - 3] == p) return true;
            }
        }
        return false;
    }
}
