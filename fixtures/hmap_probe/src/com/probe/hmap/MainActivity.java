package com.probe.hmap;

import android.app.Activity;
import java.io.File;
import java.io.FileOutputStream;
import android.os.Bundle;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;

public class MainActivity extends Activity {
    static String out = "";

    void ok(String id, String detail) { out += id + "|PASS|" + detail + "\n"; }
    void fail(String id, String detail) { out += id + "|FAIL|" + detail + "\n"; }

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        // HMAP-01 — real heap map: put then entrySet().iterator() (the
        // androidx lifecycle d.a pc=0x74/0x7c shape).
        try {
            HashMap<String, String> m = new HashMap<>();
            m.put("k1", "v1");
            m.put("k2", "v2");
            Set<Map.Entry<String, String>> s = m.entrySet();
            if (s == null) { fail("HMAP-01", "entrySet()=null"); }
            else {
                int n = 0;
                StringBuilder kv = new StringBuilder();
                Iterator<Map.Entry<String, String>> it = s.iterator();
                while (it.hasNext()) {
                    Map.Entry<String, String> e = it.next();
                    kv.append(e.getKey()).append("=").append(e.getValue()).append(";");
                    n++;
                }
                if (n == 2) ok("HMAP-01", "entrySet iterate " + kv);
                else fail("HMAP-01", "entrySet iterate n=" + n + " " + kv);
            }
        } catch (Throwable t) { fail("HMAP-01", String.valueOf(t)); }

        // HMAP-02 — keySet view.
        try {
            HashMap<String, Integer> m = new HashMap<>();
            m.put("a", 1);
            m.put("b", 2);
            Set<String> ks = m.keySet();
            int n = 0;
            if (ks != null) { Iterator<String> it = ks.iterator(); while (it.hasNext()) { it.next(); n++; } }
            if (n == 2) ok("HMAP-02", "keySet iterate n=" + n);
            else fail("HMAP-02", "keySet n=" + n + (ks == null ? " (null)" : ""));
        } catch (Throwable t) { fail("HMAP-02", String.valueOf(t)); }

        // HMAP-03 — empty map entrySet iterate (R-NEW-397 shape).
        try {
            HashMap<String, String> m = new HashMap<>();
            Set<Map.Entry<String, String>> s = m.entrySet();
            int n = 0;
            if (s != null) { Iterator<Map.Entry<String, String>> it = s.iterator(); while (it.hasNext()) { it.next(); n++; } }
            if (n == 0) ok("HMAP-03", "empty entrySet iterate n=0");
            else fail("HMAP-03", "n=" + n);
        } catch (Throwable t) { fail("HMAP-03", String.valueOf(t)); }

        // HMAP-04 — static map field (the y.b classToAdapters shape: sget
        // HashMap, put, then a DIFFERENT method entrySet()s it).
        try {
            S.put("x", new V());
            HashMap<String, V> m = S.map;
            int n = 0;
            if (m != null) { for (Map.Entry<String, V> e : m.entrySet()) { n++; } }
            if (n == 1) ok("HMAP-04", "static-map entrySet n=" + n);
            else fail("HMAP-04", "n=" + n + (m == null ? " map-null" : ""));
        } catch (Throwable t) { fail("HMAP-04", String.valueOf(t)); }

        // Persist results where the harness reads them.
        try {
            File f = new File(getFilesDir(), "hmap_results.jsonl");
            FileOutputStream fos = new FileOutputStream(f);
            fos.write(out.getBytes());
            fos.close();
        } catch (Throwable t) { /* record-free honest failure */ }
    }
}

class S {
    static HashMap<String, V> map = new HashMap<>();
    static void put(String k, V v) { map.put(k, v); }
}

class V { }
