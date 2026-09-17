/*
 * MiniAndroid CROSSWORD-GOLDEN fixture — S51 finalization "بازی جدول".
 *
 * A real fill-in crossword: 5x5 grid, three interlocked words sharing
 * letters — ACROSS BEAM (row 2), DOWN MAP (col 4, rows 2-4, shares the M),
 * ACROSS PROP (row 4, shares the final P). Nine letter cells start empty;
 * the clue band lists all three words. Tapping an empty cell fills the
 * clue-driven correct letter (study mode); a filled cell ignores further
 * taps. When every word's letters are all present the status flips to
 * SOLVED! and the game freezes (Android-correct early return).
 *
 * What it exercises through REAL DEX bytecode:
 *   Activity.onCreate → mixed view tree (Button + TextView cells in
 *   LinearLayout rows) → per-cell inner-class OnClickListener → click
 *   dispatch → 2D char[][] interlock verification (real control flow over
 *   both orientations) → setText mutation → re-render → NEXT FRAME.
 *
 * Determinism: no clocks, no randomness, no ambient state. Letters are
 * filled, never removed — identical click sequences produce byte-identical
 * frames.
 *
 * Harness mapping (S51-verified law): the CLICK-SEQ driver iterates
 * clickable views in DESCENDING view-id order (most recently created
 * first). Cell views are created row-major top-to-bottom (r0c0 … r4c4),
 * so the nine EMPTY-cell buttons are tapped in reverse row-major order:
 * (3,3) (3,2) (3,1) (3,0) (2,3) (1,3) (1,2) (1,1) (1,0) — per
 * scripts/build/design_s51_games.json (crossword.taps). Words complete
 * PROP@4, MAP@6, BEAM@9 → SOLVED! at click 9 (design solver proven).
 *
 * License: MIT.
 */
package com.miniandroid.crossword;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    // Solution letters at every word cell; ' ' = black (non-button) cell.
    // Words: BEAM across row1, MAP down col3 rows1-3, PROP across row3.
    // All 9 letter cells start EMPTY (tap-to-fill).
    private static final char[][] TARGET = {
        {' ', ' ', ' ', ' ', ' '},
        {'B', 'E', 'A', 'M', ' '},
        {' ', ' ', ' ', 'A', ' '},
        {'P', 'R', 'O', 'P', ' '},
        {' ', ' ', ' ', ' ', ' '},
    };
    private static final int WORDS_TOTAL = 3;
    private static final int FILLS_TOTAL = 9;

    private final char[][] grid = new char[5][5];
    private final boolean[][] filled = new boolean[5][5];
    private int fills = 0;
    private boolean solved = false;

    private TextView status;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);      // 1 = VERTICAL

        status = new TextView(this);
        status.setText("WORDS 0/" + WORDS_TOTAL + " FILLED 0/" + FILLS_TOTAL);
        root.addView(status, new LinearLayout.LayoutParams(-1, -2));

        TextView clues = new TextView(this);
        clues.setText("ACROSS: beam(r2) prop(r4) DOWN: map(c4)");
        root.addView(clues, new LinearLayout.LayoutParams(-1, -2));

        for (int r = 0; r < 5; r++) {
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);  // 0 = HORIZONTAL
            root.addView(row, new LinearLayout.LayoutParams(-1, 0, 1.0f));
            for (int c = 0; c < 5; c++) {
                final int rr = r, cc = c;
                if (TARGET[r][c] == ' ') {
                    TextView black = new TextView(this);
                    black.setText(".");
                    row.addView(black, new LinearLayout.LayoutParams(0, -1, 1.0f));
                } else {
                    Button cell = new Button(this);
                    cell.setText("");
                    cell.setOnClickListener(new CellListener(rr, cc));
                    row.addView(cell, new LinearLayout.LayoutParams(0, -1, 1.0f));
                }
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
            if (solved || filled[r][c]) {
                return;                                   // frozen or filled
            }
            grid[r][c] = TARGET[r][c];
            filled[r][c] = true;
            fills++;
            ((Button) v).setText(String.valueOf(TARGET[r][c]));

            if (fills == FILLS_TOTAL && allWordsComplete()) {
                status.setText("SOLVED!");
                solved = true;
            } else {
                int words = countCompleteWords();
                status.setText("WORDS " + words + "/" + WORDS_TOTAL
                    + " FILLED " + fills + "/" + FILLS_TOTAL);
            }
        }
    }

    /** Real interlock check: a word is complete when all its cells are. */
    private int countCompleteWords() {
        int n = 0;
        if (cellFilled(1, 0) && cellFilled(1, 1) && cellFilled(1, 2) && cellFilled(1, 3)) {
            n++;                                          // BEAM
        }
        if (cellFilled(1, 3) && cellFilled(2, 3) && cellFilled(3, 3)) {
            n++;                                          // MAP
        }
        if (cellFilled(3, 0) && cellFilled(3, 1) && cellFilled(3, 2) && cellFilled(3, 3)) {
            n++;                                          // PROP
        }
        return n;
    }

    private boolean cellFilled(int r, int c) {
        return filled[r][c];
    }

    private boolean allWordsComplete() {
        return countCompleteWords() == WORDS_TOTAL;
    }
}
