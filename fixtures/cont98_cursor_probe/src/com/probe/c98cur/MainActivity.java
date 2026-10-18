package com.probe.c98cur;

import android.app.Activity;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;

/**
 * CONT-98 T6 (issue #364) — Cursor / database CONTRACT probe.
 *
 * Law under test (AOSP AbstractCursor / CursorWindow / SQLite column
 * conversion): a Cursor is a typed window over a dynamically-typed SQLite
 * store. Concrete laws:
 *   * getString on an INTEGER/REAL cell converts to decimal text; on NULL
 *     it returns null (not "").
 *   * getInt/getLong on a TEXT cell parse the leading numeric prefix
 *     (sqlite3Atoi64 semantics: optional ws/sign, digit prefix, junk
 *     stops); on REAL they truncate toward zero; on NULL they are 0.
 *   * getDouble/getFloat preserve REAL cells EXACTLY (no int64 collapse).
 *   * getType reports FIELD_TYPE_{NULL,INTEGER,FLOAT,TEXT,BLOB}.
 *   * moveToPosition(<0) parks at -1 (beforeFirst) and returns false;
 *     moveToPosition(>=count) parks at count (afterLast) and returns
 *     false (AbstractCursor.moveToPosition).
 *   * Accessing a column while pos==-1 throws
 *     CursorIndexOutOfBoundsException("Before first row."); at
 *     pos==count throws CursorIndexOutOfBoundsException("After last
 *     row.") (AbstractCursor.checkPosition).
 *   * getColumnIndexOrThrow throws IllegalArgumentException on unknown
 *     column; getColumnIndex returns -1.
 *   * Transaction law: commit only when setTransactionSuccessful was
 *     called; otherwise endTransaction ROLLS BACK.
 *
 * Self-contained: one private database, literal SQL, deterministic
 * ordering (rowid). Rows print PASS/FAIL to stderr; the harness log is
 * the evidence.
 */
public class MainActivity extends Activity {

    public static final String VERSION = "V2-C98";
    private int pass = 0, fail = 0;

    private void log(String row, boolean ok, String detail) {
        if (ok) pass++; else fail++;
        System.err.println("[C98-" + row + "] " + (ok ? "PASS" : "FAIL") + " " + detail);
    }

    private SQLiteDatabase db;

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        System.err.println("[C98-VERSION] code=" + VERSION + " pkg=" + getPackageName());

        try {
            db = openOrCreateDatabase("c98.db", MODE_PRIVATE, null);
            db.execSQL("DROP TABLE IF EXISTS t");
            db.execSQL("CREATE TABLE t(id INTEGER, name TEXT, score REAL, note TEXT)");
            db.execSQL("INSERT INTO t VALUES (1, 'alpha', 2.5, NULL)");
            db.execSQL("INSERT INTO t VALUES (2, '42abc', 3.5, 'x')");
            db.execSQL("INSERT INTO t VALUES (NULL, '  -7xyz', 0.5, 'y')");

            Cursor c = db.rawQuery(
                    "SELECT id, name, score, note FROM t ORDER BY rowid", null);

            // C98-COUNT / C98-COLS — shape laws (pre-existing, prove current)
            log("COUNT", c.getCount() == 3, "getCount=" + c.getCount());
            log("COLS", c.getColumnCount() == 4, "getColumnCount=" + c.getColumnCount());
            log("IDX", c.getColumnIndex("name") == 1 && c.getColumnIndex("nope") == -1,
                    "name=" + c.getColumnIndex("name") + " nope=" + c.getColumnIndex("nope"));

            // C98-MOVEFIRST + getPosition (new law)
            boolean mf = c.moveToFirst();
            log("MOVEFIRST", mf && c.getPosition() == 0,
                    "moveToFirst=" + mf + " pos=" + c.getPosition());

            // C98-STR-INT: getString(0) on INTEGER cell 1 == "1" (conversion law)
            String s0 = c.getString(0);
            log("STR-INT", "1".equals(s0), "getString(0)='" + s0 + "'");

            // C98-NULLSTR: getString(3) on NULL == null (not "")
            Object s3 = c.getString(3);
            log("NULLSTR", s3 == null, "getString(3)=" + (s3 == null ? "null" : "'" + s3 + "'"));

            // C98-GETTYPE: FIELD_TYPE laws on row0 (id=1 INT, name TEXT, score REAL, note NULL)
            int t0 = c.getType(0), t1 = c.getType(1), t2 = c.getType(2), t3 = c.getType(3);
            log("GETTYPE", t0 == 1 && t1 == 3 && t2 == 2 && t3 == 0,
                    "getType=[int=" + t0 + " text=" + t1 + " float=" + t2 + " null=" + t3 + "]");

            // C98-DOUBLE: REAL preserved exactly (no int64 collapse)
            double d0 = c.getDouble(2);
            log("DOUBLE", d0 == 2.5, "getDouble(2)=" + d0);

            // C98-INT-TEXT: TEXT prefix conversion on rows 1 and 2
            c.moveToPosition(1);
            int i42 = c.getInt(1);
            c.moveToPosition(2);
            int ineg = c.getInt(1);
            log("INT-TEXT", i42 == 42 && ineg == -7,
                    "getInt('42abc')=" + i42 + " getInt('  -7xyz')=" + ineg);

            // C98-NULLINT: getInt on NULL cell == 0, isNull true
            int iN = c.getInt(0);
            boolean isN = c.isNull(0);
            log("NULLINT", iN == 0 && isN, "getInt(NULL)=" + iN + " isNull=" + isN);

            // C98-POSITIONS: moveToLast/moveToPrevious/moveToNext + predicate laws
            boolean ml = c.moveToLast();
            boolean last2 = c.isLast() && c.getPosition() == 2;
            boolean mp = c.moveToPrevious();
            boolean mid = c.getPosition() == 1 && !c.isFirst() && !c.isLast() && !c.isBeforeFirst();
            boolean mn = c.moveToNext();
            boolean atLast = c.getPosition() == 2 && c.isLast();
            boolean mnEnd = !c.moveToNext();
            boolean after = c.isAfterLast() && !c.isClosed();
            log("POSITIONS", ml && last2 && mp && mid && mn && atLast && mnEnd && after,
                    "last=" + ml + " prev=" + mp + " afterEnd=" + after + " closed=" + c.isClosed());

            // C98-MOVEPOS: moveToPosition laws (AOSP parking)
            boolean m1 = c.moveToPosition(1);
            boolean mNeg = c.moveToPosition(-1);
            boolean beforeAfterNeg = mNeg == false && c.isBeforeFirst();
            boolean mBig = c.moveToPosition(99);
            boolean afterBig = mBig == false && c.isAfterLast();
            log("MOVEPOS", m1 && beforeAfterNeg && afterBig,
                    "pos(1)=" + m1 + " pos(-1) parked beforeFirst=" + beforeAfterNeg
                            + " pos(99) parked afterLast=" + afterBig);

            // C98-OOB-BEFORE: access at pos==-1 throws CursorIndexOutOfBoundsException
            // (explicit moveToPosition(-1) first: the MOVEPOS block legitimately
            // parked the cursor at afterLast — AOSP moveToPosition law.)
            c.moveToPosition(-1);
            try {
                c.getInt(0);
                log("OOB-BEFORE", false, "no exception at pos=-1");
            } catch (Throwable t) {
                log("OOB-BEFORE",
                        t.getClass().getName().endsWith("CursorIndexOutOfBoundsException")
                                && String.valueOf(t.getMessage()).contains("Before first row."),
                        "throw=" + t.getClass().getName() + " msg=" + t.getMessage());
            }

            // C98-OOB-AFTER: access at pos==count throws "After last row."
            c.moveToLast();
            c.moveToNext();
            try {
                c.getString(1);
                log("OOB-AFTER", false, "no exception at pos=count");
            } catch (Throwable t) {
                log("OOB-AFTER",
                        t.getClass().getName().endsWith("CursorIndexOutOfBoundsException")
                                && String.valueOf(t.getMessage()).contains("After last row."),
                        "throw=" + t.getClass().getName() + " msg=" + t.getMessage());
            }

            // C98-IDXORTHROW: getColumnIndexOrThrow laws
            try {
                int ok = c.getColumnIndexOrThrow("name");
                try {
                    c.getColumnIndexOrThrow("nope");
                    log("IDXORTHROW", false, "no exception for unknown column");
                } catch (Throwable t) {
                    log("IDXORTHROW",
                            ok == 1 && t instanceof IllegalArgumentException
                                    && String.valueOf(t.getMessage()).contains("nope"),
                            "idx=" + ok + " throw=" + t.getClass().getSimpleName()
                                    + " msg=" + t.getMessage());
                }
            } catch (Throwable t) {
                log("IDXORTHROW", false, "known column threw " + t);
            }

            c.close();
            log("CLOSE", c.isClosed(), "isClosed=" + c.isClosed());

            // C98-TRX-COMMIT: successful transaction persists
            db.beginTransaction();
            db.execSQL("INSERT INTO t VALUES (5, 'zeta', 1.5, 'w')");
            db.setTransactionSuccessful();
            db.endTransaction();
            Cursor c2 = db.rawQuery("SELECT count(*) FROM t", null);
            boolean commitOk = c2.moveToFirst() && c2.getInt(0) == 4
                    && "4".equals(c2.getString(0));
            c2.close();
            log("TRX-COMMIT", commitOk, "count after commit=" + (commitOk ? 4 : "?"));

            // C98-TRX-ROLLBACK: no setTransactionSuccessful -> ROLLBACK
            db.beginTransaction();
            db.execSQL("INSERT INTO t VALUES (6, 'ghost', 9.9, 'gone')");
            db.endTransaction();
            Cursor c3 = db.rawQuery("SELECT count(*) FROM t", null);
            boolean rbOk = c3.moveToFirst() && c3.getInt(0) == 4;
            c3.close();
            log("TRX-ROLLBACK", rbOk, "count after rollback=" + (rbOk ? 4 : "?"));

            db.close();
        } catch (Throwable t) {
            System.err.println("[C98-FATAL] " + t);
            fail++;
        }
        System.err.println("[C98-SUMMARY] pass=" + pass + " fail=" + fail);
    }
}
