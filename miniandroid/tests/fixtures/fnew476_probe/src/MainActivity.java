package com.probe.fnew476;

import android.app.Activity;
import android.os.Bundle;

public class MainActivity extends Activity {
    static class R {
        // receiver+long+float+Object = 5 regs -> 35c count=5 (G nibble = Object)
        int mixed(long j, float f, Object o) {
            return (o == null ? -1 : 100) + (int)(j % 10) + (int)f;
        }
        // receiver+Object = 2 regs -> 35c count=2 (control)
        int simple(Object o) { return (o == null ? -2 : 300); }
        // receiver+long+double+Object+int+Object = 8 regs -> 3rc
        int wide(long j, double d, Object a, int i, Object b) {
            return (a == null || b == null ? -3 : 400) + (int)(j % 10) + (int)d + i;
        }
        // receiver+long+long+Object = 6 regs -> 3rc
        int twoLongs(long a, long b, Object o) {
            return (o == null ? -4 : 500) + (int)(a % 10) + (int)(b % 10);
        }
    }
    static StringBuilder log = new StringBuilder();
    static void probe(String name, int got, int want) {
        log.append(name).append("=").append(got)
           .append(got == want ? " PASS" : " FAIL(want " + want + ")").append(";");
    }
    @Override protected void onCreate(Bundle s) {
        super.onCreate(s);
        R r = new R();
        Object self = this;
        int a1 = r.simple(self);                 // count=2
        int a2 = r.mixed(21L, 2.0f, self);       // count=5, Object in G
        int a3 = r.mixed(21L, 2.0f, null);       // count=5, null control
        int a4 = r.wide(21L, 1.5, self, 7, r);   // 3rc
        int a5 = r.twoLongs(21L, 32L, self);     // 3rc
        probe("simple", a1, 300);
        probe("mixed_G", a2, 103);
        probe("mixed_null", a3, 2);
        probe("wide_3rc", a4, 409);
        probe("twoLongs_3rc", a5, 503);
        android.util.Log.i("F476", log.toString());
        System.out.println("PROBE-F476 " + log);
    }
}
