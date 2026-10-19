package com.probe.c106b;

import android.app.Activity;
import android.os.Bundle;

import java.lang.reflect.Field;
import java.util.Arrays;

/**
 * CONT-107 / F-NEW-449 probe: the reflection count-agreement law, minimized.
 *
 * Telegram play_billing face (CONT-104/106): protobuf-lite MessageSchema walk
 * (n2.r) reads a Field[]/String[] entries array of length 11 but the loop
 * bound derives from a second count source -> rotated-loop boundary read
 * aget-object v29,v24,v10 with v10 == v24.length @0x568.
 *
 * Upstream both counts come from the SAME class metadata; on MiniAndroid the
 * engine serves reflection metadata through its own laws. This probe pins the
 * engine's count sources against each other over one class:
 *   C449-COUNT    getDeclaredFields().length == 11
 *   C449-NAMES    exact name set, statics and instances mixed
 *   C449-UNSAFE   sun.misc.Unsafe theUnsafe acquisition (n2.<clinit> law)
 *   C449-OFFSET   objectFieldOffset per instance field, zero throws
 *   C449-SOFFSET  staticFieldOffset per static field, zero throws
 *   C449-ORDER    two getDeclaredFields() calls agree on order (stable walk)
 *   C449-MODS     modifiers answered for static vs instance (count split law)
 * AOSP: count 11, all offsets resolvable, order stable.
 */
public class MainActivity extends Activity {

    public static class Schema {
        private static int sA;
        private static String sB;
        private static Object sC;
        private int f0;
        private String f1;
        private Object f2;
        private long f3;
        private int f4;
        private String f5;
        private Object f6;
        private long f7;
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);

        Field[] fs = Schema.class.getDeclaredFields();
        int count = fs.length;
        String[] names = new String[count];
        for (int i = 0; i < count; i++) names[i] = fs[i].getName();
        Arrays.sort(names);

        System.err.println("[C449-COUNT] count=" + count + " expected=11");

        StringBuilder sb = new StringBuilder();
        for (String n : names) sb.append(n).append(',');
        System.err.println("[C449-NAMES] " + sb);

        sun.misc.Unsafe u = null;
        String unsafeFace = "NO-EXC";
        try {
            Field uf = sun.misc.Unsafe.class.getDeclaredField("theUnsafe");
            uf.setAccessible(true);
            u = (sun.misc.Unsafe) uf.get(null);
        } catch (Throwable t) {
            unsafeFace = t.getClass().getSimpleName();
        }
        System.err.println("[C449-UNSAFE] face=" + unsafeFace
                + " unsafe=" + (u != null));

        if (u != null) {
            int offs = 0, throws_ = 0;
            for (Field f : fs) {
                try {
                    if (java.lang.reflect.Modifier.isStatic(f.getModifiers())) {
                        u.staticFieldOffset(f);
                    } else {
                        u.objectFieldOffset(f);
                    }
                    offs++;
                } catch (Throwable t) {
                    throws_++;
                    System.err.println("[C449-OFFTHROW] " + f.getName() + " -> "
                            + t.getClass().getSimpleName());
                }
            }
            System.err.println("[C449-OFFSET] resolved=" + offs + " of " + count
                    + " throws=" + throws_);
        }

        try {
            int statics = 0, instances = 0;
            for (Field f : fs) {
                if (java.lang.reflect.Modifier.isStatic(f.getModifiers())) statics++;
                else instances++;
            }
            System.err.println("[C449-MODS] statics=" + statics
                    + " instances=" + instances);
        } catch (Throwable t) {
            System.err.println("[C449-MODS] face=" + t.getClass().getSimpleName());
        }

        try {
            Field[] fs2 = Schema.class.getDeclaredFields();
            boolean stable = fs2.length == fs.length;
            if (stable) {
                for (int i = 0; i < fs.length; i++) {
                    if (!fs2[i].getName().equals(fs[i].getName())) { stable = false; break; }
                }
            }
            System.err.println("[C449-ORDER] stable=" + stable);
        } catch (Throwable t) {
            System.err.println("[C449-ORDER] face=" + t.getClass().getSimpleName());
        }
    }
}
