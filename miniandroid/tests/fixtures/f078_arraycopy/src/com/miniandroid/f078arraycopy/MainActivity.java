/*
 * MiniAndroid F-078 ARRAYCOPY-PROBE fixture — pins System.arraycopy semantics
 * end to end (OpenJDK javadoc contract; the JVM lowers it to an intrinsic).
 *
 * Each line renders ONE construct's result. Expected values (Android/JVM):
 *   C1 plain=1,2,3,4        — distinct-array copy, element order preserved
 *   C2 shift=1,2,1,2,3,4,5  — SAME-array right-shift by 2 with overlapping
 *                             range (kotlin copyInto / TrieNode
 *                             mutableInsertEntryAt law): temp-copy semantics,
 *                             NOT naive forward propagation
 *   C3 lshift=2,3,4,5,5     — SAME-array left-shift by 1 (ArrayList remove)
 *   C4 mid=1,2,7,8,9,5,8,9  — ArrayList-style mid-insert: shift [2,5) right
 *                             into [3,6) (idx5 becomes "5"), then store 7,8,9
 *                             into the hole at idx 2,3,4
 *   C5 grow=k0,v0,k2,v2,k1,v1 — the EXACT kotlinx TrieNode insert sequence:
 *                             Arrays.copyOf grow, then same-array shift,
 *                             then key/value store — buffer must carry NO
 *                             nulls (bitmaps/buffer invariant, F-077 root)
 *   C6 npe=CAUGHT           — null dst → NullPointerException
 *   C7 oob=CAUGHT           — srcPos+length > src.length →
 *                             ArrayIndexOutOfBoundsException
 *   C8 ints=9,2,3           — int[] primitive copy
 *
 * License: MIT.
 */
package com.miniandroid.f078arraycopy;

import android.app.Activity;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.Arrays;

public class MainActivity extends Activity {

    private static String join(Object[] a) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < a.length; i++) {
            if (i > 0) sb.append(',');
            sb.append(a[i]);
        }
        return sb.toString();
    }

    private static String joinInts(int[] a) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < a.length; i++) {
            if (i > 0) sb.append(',');
            sb.append(a[i]);
        }
        return sb.toString();
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);

        // C1 — distinct-array copy.
        String[] src = {"1", "2", "3", "4"};
        String[] dst = new String[4];
        System.arraycopy(src, 0, dst, 0, 4);
        TextView t1 = new TextView(this);
        t1.setText("C1 plain=" + join(dst));
        root.addView(t1);

        // C2 — same-array right-shift by 2, range [0,5) → [2,7).
        // Temp-copy law: every dst slot equals the ORIGINAL src value.
        // Naive forward loop would propagate [1,2,1,2,1,2,1].
        String[] sh = {"1", "2", "3", "4", "5", "", ""};
        System.arraycopy(sh, 0, sh, 2, 5);
        TextView t2 = new TextView(this);
        t2.setText("C2 shift=" + join(sh));
        root.addView(t2);

        // C3 — same-array left-shift by 1, range [1,5) → [0,4).
        String[] ls = {"1", "2", "3", "4", "5"};
        System.arraycopy(ls, 1, ls, 0, 4);
        TextView t3 = new TextView(this);
        t3.setText("C3 lshift=" + join(ls));
        root.addView(t3);

        // C4 — ArrayList-style mid-insert: shift [2,5) right into [3,6),
        // then store 7,8,9 into the hole. Expected: idx5="5" (shifted),
        // idx6/7 untouched ("8","9").
        String[] mid = {"1", "2", "3", "4", "5", "7", "8", "9"};
        System.arraycopy(mid, 2, mid, 3, 3);
        mid[2] = "7"; mid[3] = "8"; mid[4] = "9";
        TextView t4 = new TextView(this);
        t4.setText("C4 mid=" + join(mid));
        root.addView(t4);

        // C5 — the EXACT kotlinx.collections.immutable TrieNode
        // mutableInsertEntryAt sequence (F-077 root): grow via Arrays.copyOf,
        // same-array shift, key/value store. Buffer invariant: no nulls.
        Object[] buf = new Object[]{"k0", "v0", "k1", "v1", null, null};
        Object[] grown = Arrays.copyOf(buf, 6);
        System.arraycopy(grown, 2, grown, 4, 2);
        grown[2] = "k2";
        grown[3] = "v2";
        TextView t5 = new TextView(this);
        t5.setText("C5 grow=" + join(grown));
        root.addView(t5);

        // C6 — null destination → NPE, caught.
        String npe = "UNCAUGHT";
        try {
            System.arraycopy(src, 0, null, 0, 1);
        } catch (NullPointerException e) {
            npe = "CAUGHT";
        }
        TextView t6 = new TextView(this);
        t6.setText("C6 npe=" + npe);
        root.addView(t6);

        // C7 — srcPos+length > src.length → AIOOBE, caught.
        String oob = "UNCAUGHT";
        try {
            System.arraycopy(src, 2, dst, 0, 3);
        } catch (ArrayIndexOutOfBoundsException e) {
            oob = "CAUGHT";
        }
        TextView t7 = new TextView(this);
        t7.setText("C7 oob=" + oob);
        root.addView(t7);

        // C8 — primitive int[] copy.
        int[] is = {9, 2, 3};
        int[] id = new int[3];
        System.arraycopy(is, 0, id, 0, 3);
        TextView t8 = new TextView(this);
        t8.setText("C8 ints=" + joinInts(id));
        root.addView(t8);

        setContentView(root);
    }
}
