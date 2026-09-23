/*
 * MiniAndroid MINESWEEP-GOLDEN fixture — S51 finalization (mine-finding game in the Windows XP style).
 *
 * Classic 9x9 beginner board with 10 fixed mines (no randomness — the
 * mine layout is a design constant). Tapping a hidden safe cell reveals
 * it; a zero cell reveals its neighborhood by real flood fill (iterative
 * DFS over an int stack — heavy DEX exercise: 2D arrays, nested loops,
 * adjacency counting). First tap is mine-safe by construction (XP
 * first-click law; the forced rotation's first target (8,8) is safe).
 * Tapping all safe cells — directly or via flood — wins:
 * MINES 10 SAFE 71/71 WIN. Tapping a mine would end the game BOOM (code
 * path present; the golden sequence never hits it).
 *
 * What it exercises through REAL DEX bytecode:
 *   Activity.onCreate → 81-Button grid in LinearLayout rows → per-cell
 *   inner-class OnClickListener → click dispatch → boolean[][] mine
 *   lookup → iterative flood-fill (int[] stack, array bounds, nested
 *   loops) → adjacency digit rendering → setText mutation → re-render →
 *   NEXT FRAME.
 *
 * Determinism: fixed mine layout, no clocks, no randomness.
 *
 * Harness mapping (S51-verified law): the CLICK-SEQ driver iterates
 * clickable views in DESCENDING view-id order (most recently created
 * first). Cells are created row-major top-to-bottom (r0c0 … r8c8), so
 * taps rotate (8,8) (8,7) … (0,0) cyclically. The mine layout is placed
 * ONLY in cells the rotation does not reach before the win completes
 * (design solver: win at click 64, zero booms — see
 * scripts/build/design_s51_games.json minesweep.mines).
 *
 * License: MIT.
 */
package com.miniandroid.minesweep;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    private static final int N = 9;
    private static final int MINES = 10;
    private static final int SAFE = 71;            // 81 - 10

    // Fixed mine layout (design constant — XP-style beginner board).
    private static final int[] MINE_R = {0, 0, 0, 0, 0, 0, 1, 1, 1, 1};
    private static final int[] MINE_C = {0, 1, 2, 6, 7, 8, 0, 1, 6, 7};

    private final boolean[][] mine = new boolean[N][N];
    private final boolean[][] revealed = new boolean[N][N];
    private int revealedCount = 0;
    private boolean over = false;

    private TextView status;
    private final Button[][] cells = new Button[N][N];
    // Flood stack capacity law: a cell can be pushed by each of its up to 8
    // neighbors before it is popped (still unrevealed at push time), so the
    // worst-case live stack is 8 per cell (S51 finding: capacity N*N
    // overflowed at pc=122 and the F-016 exception-honesty law correctly
    // flagged it — capacity must be N*N*8).
    private final int[] stack = new int[N * N * 8];    // flood-fill stack

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        for (int i = 0; i < MINES; i++) {
            mine[MINE_R[i]][MINE_C[i]] = true;
        }

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);      // 1 = VERTICAL

        status = new TextView(this);
        status.setText("MINES 10 SAFE 0/71");
        root.addView(status, new LinearLayout.LayoutParams(-1, -2));

        // 9x9 grid of buttons, row-major top-to-bottom (id law, see header).
        for (int r = 0; r < N; r++) {
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);  // 0 = HORIZONTAL
            root.addView(row, new LinearLayout.LayoutParams(-1, 0, 1.0f));
            for (int c = 0; c < N; c++) {
                final int rr = r, cc = c;
                Button b = new Button(this);
                b.setText("");
                b.setOnClickListener(new CellListener(rr, cc));
                cells[r][c] = b;
                row.addView(b, new LinearLayout.LayoutParams(0, -1, 1.0f));
            }
        }

        setContentView(root);
    }

    /** Inner class listener — exercises the Outer$Inner DEX class path. */
    class CellListener implements View.OnClickListener {
        private final int r, c;

        CellListener(int r, int c) {
            this.r = r;
            this.c = c;
        }

        @Override
        public void onClick(View v) {
            if (over || revealed[r][c]) {
                return;                                   // frozen / revealed
            }
            if (mine[r][c]) {
                cells[r][c].setText("*");
                status.setText("BOOM - GAME OVER");
                over = true;
                return;
            }
            flood(r, c);
            if (revealedCount == SAFE) {
                status.setText("MINES 10 SAFE 71/71 WIN");
                over = true;
            } else {
                status.setText("MINES 10 SAFE " + revealedCount + "/71");
            }
        }
    }

    /** Iterative DFS flood fill — reveals this cell and, for zero cells,
     *  the whole connected zero region with its digit border. */
    private void flood(int r, int c) {
        int sp = 0;
        stack[sp++] = r * N + c;
        while (sp > 0) {
            int cur = stack[--sp];
            int cr = cur / N, cc = cur % N;
            if (revealed[cr][cc] || mine[cr][cc]) {
                continue;
            }
            revealed[cr][cc] = true;
            revealedCount++;
            int adj = adjacency(cr, cc);
            cells[cr][cc].setText(adj == 0 ? "" : String.valueOf(adj));
            if (adj == 0) {
                for (int dr = -1; dr <= 1; dr++) {
                    for (int dc = -1; dc <= 1; dc++) {
                        int nr = cr + dr, nc = cc + dc;
                        if ((dr != 0 || dc != 0) && nr >= 0 && nr < N
                                && nc >= 0 && nc < N
                                && !revealed[nr][nc] && !mine[nr][nc]) {
                            stack[sp++] = nr * N + nc;
                        }
                    }
                }
            }
        }
    }

    /** Real adjacency count over the 8-neighborhood. */
    private int adjacency(int r, int c) {
        int n = 0;
        for (int dr = -1; dr <= 1; dr++) {
            for (int dc = -1; dc <= 1; dc++) {
                if (dr == 0 && dc == 0) {
                    continue;
                }
                int nr = r + dr, nc = c + dc;
                if (nr >= 0 && nr < N && nc >= 0 && nc < N && mine[nr][nc]) {
                    n++;
                }
            }
        }
        return n;
    }
}
