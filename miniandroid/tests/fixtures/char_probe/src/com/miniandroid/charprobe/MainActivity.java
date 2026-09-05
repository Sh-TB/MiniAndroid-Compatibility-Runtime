/*
 * MiniAndroid CHAR-PROBE fixture — discriminates char semantics end to end.
 *
 * Each line renders ONE construct's result. Expected values (Android/JVM):
 *   P1 f=X          — char field initial read, concat
 *   P2 branch=TX    — ternary on char == 'X' (true branch)
 *   P3 f2=O         — flip assignment  f = (f=='X') ? 'O' : 'X'
 *   P4 branch=CO    — ternary on flipped char (false branch)
 *   P5 b0=O         — char[] store/load (aput-char/aget-char)
 *   P6 eq=false     — char[] element vs flipped field compare
 *   P7 w=false      — the exact wins() pattern from tictactoe_golden
 *   P8 w2=true      — same pattern with a real row
 * License: MIT.
 */
package com.miniandroid.charprobe;

import android.app.Activity;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    private char f = 'X';

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);

        TextView t1 = new TextView(this);
        t1.setText("P1 f=" + f);
        root.addView(t1);

        TextView t2 = new TextView(this);
        t2.setText("P2 branch=" + (f == 'X' ? "TX" : "TO"));
        root.addView(t2);

        f = (f == 'X') ? 'O' : 'X';

        TextView t3 = new TextView(this);
        t3.setText("P3 f2=" + f);
        root.addView(t3);

        TextView t4 = new TextView(this);
        t4.setText("P4 branch=" + (f == 'X' ? "TX" : "TO"));
        root.addView(t4);

        char[] b = new char[3];
        b[0] = 'O';
        b[1] = 'X';
        TextView t5 = new TextView(this);
        t5.setText("P5 b0=" + b[0]);
        root.addView(t5);

        TextView t6 = new TextView(this);
        t6.setText("P6 eq=" + (b[0] == f));
        root.addView(t6);

        // Exact tictactoe_golden wins() pattern: O at cells 8,5,2 (a column)
        // after the fixture's first three clicks. Expected: no win → false.
        char[] bd = new char[9];
        bd[8] = 'X';
        bd[5] = 'O';
        bd[2] = 'O';
        TextView t7 = new TextView(this);
        t7.setText("P7 w=" + wins(bd, 'O'));
        root.addView(t7);

        // Real row win: X at cells 0,1,2 → true.
        char[] bd2 = new char[9];
        bd2[0] = 'X';
        bd2[1] = 'X';
        bd2[2] = 'X';
        TextView t8 = new TextView(this);
        t8.setText("P8 w2=" + wins(bd2, 'X'));
        root.addView(t8);

        setContentView(root);
    }

    private boolean wins(char[] board, char p) {
        for (int i = 0; i < 3; i++) {
            if (board[i * 3] == p && board[i * 3 + 1] == p && board[i * 3 + 2] == p) {
                return true;
            }
            if (board[i] == p && board[i + 3] == p && board[i + 6] == p) {
                return true;
            }
        }
        return (board[0] == p && board[4] == p && board[8] == p)
            || (board[2] == p && board[4] == p && board[6] == p);
    }
}
