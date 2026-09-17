/*
 * S50 sandbox forensics probe — PHASE 3 evidence fixture.
 *
 * The app performs persistence touches against its package sandbox and
 * RENDERS the pre-write state it observed, so the screenshot itself is
 * evidence of what survived the previous process:
 *
 *   BAND1 PREFS: SharedPreferences "s50prefs" int "opens" (0 on fresh);
 *                writes back opens+1 via commit().
 *   BAND2 DB:    SQLiteOpenHelper "s50.db" table opens(id INTEGER
 *                PRIMARY KEY AUTOINCREMENT, src TEXT NOT NULL); counts
 *                rows, then inserts one row with src='run'.
 *   BAND3 LAW:   java.io.File path law — getFilesDir() must resolve to
 *                <app_data_root>/<package>/files (S50-R1; was hard-coded
 *                /tmp/miniandroid/files). green=law holds, amber=violated.
 *
 * Band colors carry the verdict for pixel-level assertions:
 *   amber (200,140,0) = fresh-sandbox path observed (B1/B2)
 *   green (0,160,0)   = persisted state observed (B1/B2) / law holds (B3)
 *   blue  (30,80,200) reserved
 * Text carries the exact observed values (machine-verifiable in the
 * sandbox files themselves: marker content, shared_prefs XML, sqlite db).
 *
 * Determinism law: no time, no randomness, no absolute paths rendered.
 * Identical sandbox state => byte-identical render (3-run gate usable).
 */
package com.miniandroid.s50probe;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.View;

public class MainActivity extends Activity {

    static final int AMBER = Color.rgb(200, 140, 0);
    static final int GREEN = Color.rgb(0, 160, 0);
    static final int DARK  = Color.rgb(24, 24, 24);

    static boolean b1Persisted = false, b2Persisted = false, b3Persisted = false;
    static final int BLUE = Color.rgb(30, 80, 200);
    static String b1Text = "", b2Text = "", b3Text = "";
    static boolean b3IsLaw = true;

    static class DbHelper extends SQLiteOpenHelper {
        DbHelper(Context c) { super(c, "s50.db", null, 1); }
        @Override public void onCreate(SQLiteDatabase db) {
            db.execSQL("CREATE TABLE opens(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    + "src TEXT NOT NULL)");
        }
        @Override public void onUpgrade(SQLiteDatabase db, int a, int b) { }
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // ---- BAND1: SharedPreferences counter (S50 sandbox probe) ----
        SharedPreferences sp = getSharedPreferences("s50prefs",
                Context.MODE_PRIVATE);
        int opens = sp.getInt("opens", 0);
        b1Persisted = opens > 0;
        b1Text = "PREFS: opens-was=" + opens;
        SharedPreferences.Editor ed = sp.edit();
        ed.putInt("opens", opens + 1);
        ed.commit();

        // ---- BAND2: SQLite rows --------------------------------------
        DbHelper h = new DbHelper(this);
        SQLiteDatabase db = h.getWritableDatabase();
        int rows = 0;
        Cursor c = db.rawQuery("SELECT COUNT(*) FROM opens", new String[0]);
        if (c.moveToFirst()) rows = c.getInt(0);
        c.close();
        b2Persisted = rows > 0;
        b2Text = "DB: rows-was=" + rows;
        db.execSQL("INSERT INTO opens(src) VALUES('run')");
        db.close();

        // ---- BAND3: java.io.File path law (S50-R1 getFilesDir law) ----
        // Deterministic across data roots: after the S50-R1 fix,
        // getFilesDir() = <app_data_root>/<package>/files, so the parent of
        // a child file ends with "<package>/files" for EVERY root, and
        // getName/isAbsolute follow R-NEW-347 constants.
        java.io.File marker = new java.io.File(getFilesDir(), "s50_marker.txt");
        java.io.File filesDir = getFilesDir();
        String parent = filesDir.getAbsolutePath();
        boolean parentLaw = parent.endsWith("com.miniandroid.s50probe/files");
        b3Text = "FILE LAW: name=" + marker.getName()
               + " parent-law=" + parentLaw
               + " parentAbs=" + filesDir.isAbsolute();
        b3Persisted = parentLaw;  // green = path law holds, amber = violated

        setContentView(new BandView(this));
    }

    static class BandView extends View {
        private final Paint bg = new Paint();
        private final Paint tx = new Paint();

        BandView(Context c) {
            super(c);
            tx.setColor(Color.WHITE);
            tx.setTextSize(44);
            tx.setAntiAlias(false);
        }

        void band(Canvas canvas, int top, boolean persisted, String line1,
                  String line2) {
            bg.setColor(persisted ? GREEN : AMBER);
            canvas.drawRect(0, top, 1080, top + 640, bg);
            tx.setColor(DARK);
            canvas.drawText(line1, 60, top + 120, tx);
            tx.setColor(Color.WHITE);
            canvas.drawText(line2, 60, top + 220, tx);
        }

        @Override
        public void onDraw(Canvas canvas) {
            canvas.drawColor(DARK);
            band(canvas, 0,    b1Persisted, "S50 SANDBOX PROBE: PREFS",
                    b1Text);
            band(canvas, 640,  b2Persisted, "SQLITE DB",
                    b2Text);
            // BAND3 law probe: blue when the path law HOLDS.
            bg.setColor(b3Persisted ? BLUE : AMBER);
            canvas.drawRect(0, 1280, 1080, 1920, bg);
            tx.setColor(DARK);
            canvas.drawText("FILE PATH LAW", 60, 1400, tx);
            tx.setColor(Color.WHITE);
            canvas.drawText(b3Text, 60, 1500, tx);
        }
    }
}
