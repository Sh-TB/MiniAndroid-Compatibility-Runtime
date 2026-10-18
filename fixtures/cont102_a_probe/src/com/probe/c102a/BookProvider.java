package com.probe.c102a;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;

/**
 * CONT-98 T5 — in-memory ContentProvider (AOSP deterministic contract).
 * Table "items": columns _id INTEGER, title TEXT.
 */
public class BookProvider extends ContentProvider {
    static final Object[] ROW_A = {1L, "rowA"};
    static final Object[] ROW_B = {2L, "rowB"};
    static java.util.List<Object[]> table = new java.util.ArrayList<Object[]>();
    static boolean onCreateCalled = false;

    @Override
    public boolean onCreate() {
        onCreateCalled = true;
        table.clear();
        table.add(ROW_A);
        table.add(ROW_B);
        return true;
    }

    @Override
    public Cursor query(Uri uri, String[] projection, String selection,
                        String[] selectionArgs, String sortOrder) {
        MatrixCursor c = new MatrixCursor(
                new String[]{"_id", "title"});
        for (Object[] row : table) c.addRow(row);
        return c;
    }

    @Override
    public String getType(Uri uri) {
        return "vnd.android.cursor.item/vnd.probe.book";
    }

    @Override
    public Uri insert(Uri uri, ContentValues values) {
        long id = table.size() + 100L;
        Object[] row = new Object[2];
        row[0] = id;
        row[1] = values == null ? null : values.getAsString("title");
        table.add(row);
        return Uri.parse("content://com.probe.c102a.bookdb/items/" + id);
    }

    @Override
    public int update(Uri uri, ContentValues values, String selection,
                      String[] selectionArgs) {
        int n = 0;
        String t = values == null ? null : values.getAsString("title");
        for (Object[] row : table) {
            if (((Long) row[0]) == 1L) {
                row[1] = t;
                n++;
            }
        }
        return n;
    }

    @Override
    public int delete(Uri uri, String selection, String[] selectionArgs) {
        // delete the row with title "rowB"
        int before = table.size();
        java.util.List<Object[]> keep = new java.util.ArrayList<Object[]>();
        for (Object[] row : table) {
            if (!"rowB".equals(row[1])) keep.add(row);
        }
        table = keep;
        return before - keep.size();
    }
}
