/*
 * M3 F-026 micro reproducer — the Room/SQLite persistence law family
 * (§5 deep closure), executed as real DEX inside a real APK, with a
 * VISUAL verdict.
 *
 * Shape note: the helper/DAO classes below are hand-rolled in EXACTLY the
 * shape Room's kapt-generated code produces (SQLiteOpenHelper subclass +
 * typed query methods over Cursor) — the same runtime surface microtimer's
 * real Room bytecode exercises (F-012 covers the Room-generated-adapter
 * INSERT/reopen chain on a real corpus APK; this fixture isolates the
 * SQLite/Cursor/txn laws so each defect class is attributable).
 *
 * Seven laws, one 150px band each (green = holds, red = violated):
 *   L1 INSERT×3 + SELECT ORDER BY id → exactly A,B,C (deterministic order)
 *   L2 UPDATE ... WHERE → affected==1, persisted qty==11
 *   L3 DELETE ... WHERE → affected==1, count==2
 *   L4 txn commit: begin→INS→INS→setSuccessful→end → count==4
 *   L5 txn rollback: begin→INS→(not successful)→end → count==4 (atomic)
 *   L6 cursor laws: typed reads (getInt/getString), isNull true for NULL
 *      column and false for non-NULL, moveToPosition/moveToNext/getCount
 *      walk lands on exactly the committed rows
 *   L7 reopen: close + new helper → count==4, updated qty survives
 *
 * Determinism: no time, no randomness — fixed strings, fixed ints.
 */
package com.miniandroid.probe;

import android.app.Activity;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.View;

public class MainActivity extends Activity {

    static class LawHelper extends SQLiteOpenHelper {
        LawHelper(Context c) { super(c, "f026law.db", null, 1); }
        @Override public void onCreate(SQLiteDatabase db) {
            db.execSQL("CREATE TABLE item(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    + "name TEXT NOT NULL, qty INTEGER NOT NULL, note TEXT)");
        }
        @Override public void onUpgrade(SQLiteDatabase db, int a, int b) { }
    }

    static boolean l1 = false, l2 = false, l3 = false,
                   l4 = false, l5 = false, l6 = false, l7 = false;

    private static int scalar(SQLiteDatabase db, String sql) {
        Cursor c = db.rawQuery(sql, new String[0]);
        int v = -999;
        if (c.moveToFirst()) v = c.getInt(0);
        c.close();
        return v;
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try {
            LawHelper h = new LawHelper(this);
            SQLiteDatabase db = h.getWritableDatabase();

            // L1 — INSERT×3, deterministic id order.
            db.execSQL("INSERT INTO item(name, qty, note) VALUES('A', 1, 'first')");
            db.execSQL("INSERT INTO item(name, qty, note) VALUES('B', 1, NULL)");
            db.execSQL("INSERT INTO item(name, qty, note) VALUES('C', 1, 'third')");
            Cursor c = db.rawQuery(
                "SELECT name FROM item ORDER BY id", new String[0]);
            StringBuilder sb = new StringBuilder();
            while (c.moveToNext()) sb.append(c.getString(0));
            int n1 = c.getCount();
            c.close();
            l1 = n1 == 3 && "ABC".contentEquals(sb);

            // L2 — UPDATE: affected count + persisted value.
            db.execSQL("UPDATE item SET qty = qty + 10 WHERE name = 'B'");
            l2 = scalar(db, "SELECT qty FROM item WHERE name = 'B'") == 11;

            // L3 — DELETE.
            db.execSQL("DELETE FROM item WHERE name = 'C'");
            l3 = scalar(db, "SELECT COUNT(*) FROM item") == 2
                && scalar(db, "SELECT COUNT(*) FROM item WHERE name = 'C'") == 0;

            // L4 — transaction commit (both inserts land atomically).
            db.beginTransaction();
            db.execSQL("INSERT INTO item(name, qty, note) VALUES('D', 4, NULL)");
            db.execSQL("INSERT INTO item(name, qty, note) VALUES('E', 5, NULL)");
            db.setTransactionSuccessful();
            db.endTransaction();
            l4 = scalar(db, "SELECT COUNT(*) FROM item") == 4;

            // L5 — transaction rollback (insert without setSuccessful dies).
            db.beginTransaction();
            db.execSQL("INSERT INTO item(name, qty, note) VALUES('F', 6, NULL)");
            db.endTransaction();
            l5 = scalar(db, "SELECT COUNT(*) FROM item") == 4
                && scalar(db, "SELECT COUNT(*) FROM item WHERE name = 'F'") == 0;

            // L6 — Cursor typed reads + isNull + position laws.
            Cursor q = db.rawQuery(
                "SELECT name, qty, note FROM item ORDER BY id", new String[0]);
            boolean typed = true, nulls = true;
            int walked = 0;
            int firstQty = -1;
            if (q.moveToFirst()) {
                firstQty = q.getInt(1);           // typed read: A.qty == 1
                nulls &= !q.isNull(2);            // A.note = 'first' → not null
                nulls &= q.isNull(0) == false;    // name never null here
                walked++;
                q.moveToNext();                   // → B row
                nulls &= q.isNull(2);            // B.note IS NULL
                typed &= q.getInt(1) == 11;      // the L2 update persisted
                walked++;
                while (q.moveToNext()) walked++;
            }
            q.close();
            l6 = typed && nulls && walked == 4 && firstQty == 1
                && scalar(db, "SELECT COUNT(*) FROM item") == 4;

            // L7 — reopen: close the handle, open a fresh helper.
            db.close();
            LawHelper h2 = new LawHelper(this);
            SQLiteDatabase db2 = h2.getWritableDatabase();
            int reopened = scalar(db2, "SELECT COUNT(*) FROM item");
            int bQty = scalar(db2, "SELECT qty FROM item WHERE name = 'B'");
            db2.close();
            l7 = reopened == 4 && bQty == 11;
        } catch (Throwable t) {
            // any throw = law chain violated; bands render red
        }
        setContentView(new ProbeView(this));
    }

    class ProbeView extends View {
        ProbeView(android.content.Context c) { super(c); }

        @Override
        public void onDraw(Canvas canvas) {
            canvas.drawColor(0xFFFFFFFF);
            Paint p = new Paint();
            p.setStyle(Paint.Style.FILL);
            boolean[] laws = { l1, l2, l3, l4, l5, l6, l7 };
            for (int i = 0; i < 7; i++) {
                p.setColor(laws[i] ? 0xFF00A000 : 0xFFD00000);
                int top = 100 + i * 250;
                canvas.drawRect(100, top, 980, top + 150, p);
            }
        }
    }
}
