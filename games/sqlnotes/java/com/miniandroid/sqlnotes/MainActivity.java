package com.miniandroid.sqlnotes;

import android.app.Activity;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/**
 * SQL Notes — canonical SQLite CRUD proof app (S142 TRAIN-53).
 * Real android.database.sqlite.SQLiteDatabase over the engine's real
 * sqlite3 backend: CREATE TABLE / INSERT / SELECT / DELETE, each
 * interaction a real view click that changes the REAL database and the
 * rendered list. Deterministic: no clocks, no randomness.
 */
public class MainActivity extends Activity {

    private SQLiteDatabase db;
    private LinearLayout listHost;
    private TextView status;
    private TextView lastSql;
    private int nextNote = 1;

    private static final String SQL_CREATE =
        "CREATE TABLE IF NOT EXISTS notes ("
        + "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        + "title TEXT NOT NULL, "
        + "created TEXT NOT NULL)";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        db = openOrCreateDatabase("notes.db", MODE_PRIVATE, null);
        db.execSQL(SQL_CREATE);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(24, 26, 33));

        status = new TextView(this);
        status.setTextColor(Color.rgb(126, 226, 172));
        status.setTextSize(20f);
        status.setPadding(24, 24, 24, 12);
        root.addView(status);

        lastSql = new TextView(this);
        lastSql.setTextColor(Color.rgb(150, 158, 176));
        lastSql.setTextSize(12f);
        lastSql.setPadding(24, 0, 24, 12);
        root.addView(lastSql);

        Button add = new Button(this);
        add.setText("ADD NOTE");
        add.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { addNote(); }
        });
        LinearLayout.LayoutParams bp = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT);
        root.addView(add, bp);

        Button clear = new Button(this);
        clear.setText("CLEAR ALL");
        clear.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { clearAll(); }
        });
        root.addView(clear, bp);

        ScrollView scroll = new ScrollView(this);
        listHost = new LinearLayout(this);
        listHost.setOrientation(LinearLayout.VERTICAL);
        scroll.addView(listHost, new ViewGroup.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT));
        root.addView(scroll, new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.MATCH_PARENT, 1f));

        setContentView(root);
        refresh("onCreate CREATE TABLE IF NOT EXISTS notes");
    }

    private void addNote() {
        String title = "Note #" + nextNote;
        android.database.sqlite.SQLiteStatement st = db.compileStatement(
            "INSERT INTO notes (title, created) VALUES (?, ?)");
        st.bindString(1, title);
        st.bindString(2, "t" + nextNote);
        long rowId = st.executeInsert();
        nextNote++;
        refresh("INSERT rowId=" + rowId + " (" + title + ")");
    }

    private void deleteNote(final long id) {
        db.delete("notes", "id = ?", new String[]{String.valueOf(id)});
        refresh("DELETE id=" + id);
    }

    private void clearAll() {
        db.delete("notes", "1", null);
        nextNote = 1;
        refresh("DELETE all");
    }

    private void refresh(String what) {
        lastSql.setText(what);
        Cursor c = db.rawQuery(
            "SELECT id, title, created FROM notes ORDER BY id", null);
        int n = c.getCount();
        status.setText("Notes: " + n);
        listHost.removeAllViews();
        while (c.moveToNext()) {
            final long id = c.getLong(0);
            String title = c.getString(1);
            Button row = new Button(this);
            row.setText("[" + id + "] " + title + "  (tap = DELETE)");
            row.setOnClickListener(new View.OnClickListener() {
                public void onClick(View v) { deleteNote(id); }
            });
            listHost.addView(row, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));
        }
        c.close();
    }
}
