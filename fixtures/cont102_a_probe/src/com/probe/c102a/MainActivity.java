package com.probe.c102a;

import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.ContentUris;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;

/**
 * CONT-102 Batch A — #364 CONT-98 T5 (ContentProvider URI contract) +
 * T3 (broadcast delivery) + T4 (service start/stop lifecycle).
 * All rows are deterministic; verdicts ride stderr [C102-*] rows.
 */
public class MainActivity extends Activity {
    static final Uri ITEMS =
            Uri.parse("content://com.probe.c102a.bookdb/items");
    static final String ACT = "com.probe.c102a.DYN_ACTION";
    static final String ACT_OTHER = "com.probe.c102a.OTHER_ACTION";

    static int dynFired = 0;
    static String dynExtra = null;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try {
            run();
            System.err.println("[C102-A-DONE] ok");
        } catch (Throwable t) {
            System.err.println("[C102-A-ERR] " + t);
        }
    }

    void row(String tag, Object v) {
        System.err.println("[C102-" + tag + "] " + v);
    }

    void run() {
        // ── T5: provider lifecycle + CRUD ─────────────────────────────
        row("P-ONCREATE", BookProvider.onCreateCalled);

        // P-QUERY-BASE: seeded rows readable through the resolver
        Cursor c = getContentResolver().query(ITEMS, null, null, null, null);
        int n0 = 0;
        String firstTitle = null;
        if (c != null) {
            while (c.moveToNext()) {
                if (firstTitle == null) firstTitle = c.getString(1);
                n0++;
            }
            c.close();
        }
        row("P-QUERY-COUNT", n0);            // exp 2
        row("P-QUERY-FIRST", firstTitle);    // exp rowA

        // P-TYPE: declared MIME from the provider class
        row("P-TYPE", getContentResolver().getType(ITEMS));

        // P-INSERT: returns a content Uri, table grows to 3
        ContentValues cv = new ContentValues();
        cv.put("title", "rowC");
        Uri ret = getContentResolver().insert(ITEMS, cv);
        row("P-INSERT-URI", ret == null ? "null" : ret.toString());
        Cursor c2 = getContentResolver().query(ITEMS, null, null, null, null);
        int n1 = 0;
        String lastTitle = null;
        if (c2 != null) {
            while (c2.moveToNext()) { n1++; lastTitle = c2.getString(1); }
            c2.close();
        }
        row("P-AFTER-INSERT", n1);           // exp 3
        row("P-INSERT-LAST", lastTitle);     // exp rowC

        // P-UPDATE: rewrite _id=1 title to rowA2, count 1
        ContentValues uv = new ContentValues();
        uv.put("title", "rowA2");
        int un = getContentResolver().update(ITEMS, uv, "_id=1", null);
        row("P-UPDATE-COUNT", un);           // exp 1
        Cursor c3 = getContentResolver().query(ITEMS, null, null, null, null);
        String a1 = null;
        if (c3 != null) {
            if (c3.moveToFirst()) a1 = c3.getString(1);
            c3.close();
        }
        row("P-UPDATE-FIRST", a1);           // exp rowA2

        // P-DELETE: removes rowB, count 1, then 2 rows remain
        int dn = getContentResolver().delete(ITEMS, "title=rowB", null);
        Cursor c4 = getContentResolver().query(ITEMS, null, null, null, null);
        int n2 = 0;
        if (c4 != null) { while (c4.moveToNext()) n2++; c4.close(); }
        row("P-DELETE-COUNT", dn);           // exp 1
        row("P-AFTER-DELETE", n2);           // exp 2

        // P-UNKNOWN: unregistered authority — MODERN AOSP law (API 26+
        // ActivityThread.acquireProvider throws
        // IllegalArgumentException("Unknown authority …") which
        // ContentResolver.query surfaces; the engine's N-18 decision
        // implements exactly this — V1 probe's null expectation was the
        // pre-N legacy contract, recoded honestly in V2).
        try {
            Cursor cu = getContentResolver().query(
                    Uri.parse("content://no.such.authority/x"),
                    null, null, null, null);
            row("P-UNKNOWN", cu == null ? "null-cursor" : "non-null");
        } catch (IllegalArgumentException e) {
            row("P-UNKNOWN", "EXC:IllegalArgumentException");  // exp (N-18)
        } catch (Throwable t) {
            row("P-UNKNOWN", "EXC:" + t.getClass().getSimpleName());
        }

        // ── T3: broadcast delivery ────────────────────────────────────
        BroadcastReceiver dyn = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                dynFired++;
                dynExtra = intent.getStringExtra("k");
                System.err.println("[C102-DRX] fired=" + dynFired
                        + " k=" + dynExtra);
            }
        };
        IntentFilter f = new IntentFilter(ACT);
        Intent reg = registerReceiver(dyn, f);
        row("B-REG", reg == null ? "null" : "non-null");

        Intent bi = new Intent(ACT);
        bi.putExtra("k", "v1");
        sendBroadcast(bi);
        row("B-DYN-FIRED", dynFired);        // exp 1
        row("B-DYN-EXTRA", dynExtra);        // exp v1

        sendBroadcast(new Intent(ACT_OTHER));
        row("B-NEG-FIRED", dynFired);        // exp 1 (unchanged)

        unregisterReceiver(dyn);
        sendBroadcast(new Intent(ACT));
        row("B-UNREG-FIRED", dynFired);      // exp 1 (unchanged)

        sendBroadcast(new Intent("com.probe.c102a.MANIFEST_ACTION")
                .putExtra("k", "m1"));
        row("B-MANIFEST-FIRED", ManifestRx.fired);   // exp 1
        row("B-MANIFEST-ACTION", ManifestRx.lastAction);
        row("B-MANIFEST-EXTRA", ManifestRx.lastExtra); // exp m1

        // ── T4: service lifecycle ─────────────────────────────────────
        Intent si = new Intent(this, Svc.class);
        Object o = startService(si);
        row("S-START1", o == null ? "null" : "non-null");
        row("S-LOG1", Svc.log.toString());   // onCreate;onStartCommand:1;
        startService(si);
        row("S-START2-LOG", Svc.log.toString()); // +onStartCommand:2;
        row("S-LAST-STARTID", Svc.lastStartId);  // exp 2
        boolean st = stopService(si);
        row("S-STOP-RET", st);
        row("S-DESTROYED", Svc.destroyed);   // exp true
        row("S-LOG-FINAL", Svc.log.toString());
    }
}
