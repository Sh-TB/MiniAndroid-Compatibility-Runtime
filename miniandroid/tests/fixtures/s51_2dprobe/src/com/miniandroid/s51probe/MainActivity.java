/*
 * S51 2D-ARRAY PROBE — isolates the Connect Four aput-null failure.
 *
 * Law under test (real Dalvik/ART): `new char[R][C]` allocates the outer
 * array AND every inner array immediately (JVMS multianewarray semantics;
 * d8 lowers it to new-array outer + { new-array inner; aput-object } loop).
 *
 * Three bands rendered from REAL DEX state:
 *   band1: outer-null=…   (field-allocated board == null?)
 *   band2: inner-null=…   (board[1] == null after creation loop?)
 *   band3: value=…        (board[1][2] after store — must print X)
 */
package com.miniandroid.s51probe;

import android.app.Activity;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    private final char[][] board = new char[6][7];

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);

        boolean outerNull = (board == null);
        TextView t1 = new TextView(this);
        t1.setText("outer-null=" + outerNull);
        root.addView(t1);

        boolean innerNull;
        try {
            innerNull = (board[1] == null);
        } catch (NullPointerException e) {
            innerNull = true;
        }
        TextView t2 = new TextView(this);
        t2.setText("inner-null=" + innerNull);
        root.addView(t2);

        String value;
        try {
            board[1][2] = 'X';
            value = "v=" + board[1][2];
        } catch (NullPointerException e) {
            value = "aput-null-thrown";
        }
        TextView t3 = new TextView(this);
        t3.setText(value);
        root.addView(t3);

        setContentView(root);
    }
}
