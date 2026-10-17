package com.probe.a2t;

import android.app.Activity;
import android.os.Bundle;
import java.util.Arrays;

// CONT-82 — the Arrays.toString overload-matrix acceptance fixture
// (CONT-80 Track 4 gate). Locks the CONT-366 ROOT-A law at the current
// HEAD: every AOSP shape answers "[...]" or the FOUR-CHAR "null" — never
// a null reference (the Asteroids Revenge Intrinsics NPE family).
public class MainActivity extends Activity {
    static void chk(String tag, boolean ok, String got) {
        System.out.println("[A2T-" + tag + "] " + (ok ? "PASS" : "FAIL")
                + " got=" + got);
    }

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        int[] ints = {1, 2, 3};
        chk("INTS", "[1, 2, 3]".equals(Arrays.toString(ints)),
                Arrays.toString(ints));
        boolean[] bools = {true, false};
        chk("BOOLS", "[true, false]".equals(Arrays.toString(bools)),
                Arrays.toString(bools));
        char[] chars = {'x', 'y'};
        chk("CHARS", "[x, y]".equals(Arrays.toString(chars)),
                Arrays.toString(chars));
        int[] empty = {};
        chk("EMPTY", "[]".equals(Arrays.toString(empty)),
                Arrays.toString(empty));
        String[] objs = {"a", null};
        chk("OBJS", "[a, null]".equals(Arrays.toString(objs)),
                Arrays.toString(objs));
        String nil = Arrays.toString((int[]) null);
        chk("NULL", "null".equals(nil) && nil != null, nil);
        String nilObj = Arrays.toString((Object[]) null);
        chk("NULLOBJ", "null".equals(nilObj) && nilObj != null, nilObj);
        long[] longs = {7L};
        chk("LONGS", "[7]".equals(Arrays.toString(longs)),
                Arrays.toString(longs));
        System.out.println("[A2T-DONE] rows complete");
    }
}
