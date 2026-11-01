package com.miniandroid.sqltasks;

import android.app.Activity;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.Color;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/**
 * SQL Tasks — canonical FULL-CRUD SQLite proof app (S144 TRAIN-59).
 * Real android.database.sqlite.SQLiteDatabase over the engine's real
 * sqlite3 backend, ALL FOUR arms exercised by real view taps:
 *   INSERT  — ADD TASK button (compileStatement.executeInsert)
 *   SELECT  — refresh() rawQuery renders every row after each op
 *   UPDATE  — row TOGGLE button (db.update with ContentValues) — the arm
 *             no earlier canonical app used
 *   DELETE  — row DEL button (db.delete) + CLEAR ALL (delete where "1")
 * Deterministic: no clocks, no randomness. Persistence: the DB file
 * survives the process (reopen reads the rows the previous run wrote).
 */
public class MainActivity extends Activity {

    private SQLiteDatabase db;
    private LinearLayout listHost;
    private TextView status;
    private TextView lastSql;
    private int nextTask = 1;

    private static final String[] SEED_TITLES = {
        "buy coffee beans", "ship the release", "water the plants"
    };

    private static final String SQL_CREATE =
        "CREATE TABLE IF NOT EXISTS tasks ("
        + "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        + "title TEXT NOT NULL, "
        + "done INTEGER NOT NULL DEFAULT 0)";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        db = openOrCreateDatabase("tasks.db", MODE_PRIVATE, null);
        db.execSQL(SQL_CREATE);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(22, 28, 34));

        status = new TextView(this);
        status.setTextColor(Color.rgb(126, 200, 226));
        status.setTextSize(20f);
        status.setPadding(24, 24, 24, 8);
        root.addView(status);

        lastSql = new TextView(this);
        lastSql.setTextColor(Color.rgb(150, 158, 176));
        lastSql.setTextSize(12f);
        lastSql.setPadding(24, 0, 24, 12);
        root.addView(lastSql);

        Button add = new Button(this);
        add.setText("ADD TASK");
        add.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { addTask(); }
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
        refresh("onCreate CREATE TABLE IF NOT EXISTS tasks");
    }

    private void addTask() {
        String title = "Task #" + nextTask + " " + SEED_TITLES[(nextTask - 1) % 3];
        android.database.sqlite.SQLiteStatement st = db.compileStatement(
            "INSERT INTO tasks (title, done) VALUES (?, 0)");
        st.bindString(1, title);
        long rowId = st.executeInsert();
        nextTask++;
        refresh("INSERT rowId=" + rowId + " (" + title + ")");
    }

    /** The UPDATE arm: db.update with ContentValues toggles done. */
    private void toggleTask(final long id, final int cur) {
        ContentValues cv = new ContentValues();
        cv.put("done", cur == 0 ? 1 : 0);
        int n = db.update("tasks", cv, "id = ?",
            new String[]{String.valueOf(id)});
        refresh("UPDATE id=" + id + " done=" + (cur == 0 ? 1 : 0)
            + " (rows=" + n + ")");
    }

    private void deleteTask(final long id) {
        db.delete("tasks", "id = ?", new String[]{String.valueOf(id)});
        refresh("DELETE id=" + id);
    }

    private void clearAll() {
        db.delete("tasks", "1", null);
        nextTask = 1;
        refresh("DELETE all");
    }

    private void refresh(String what) {
        lastSql.setText(what);
        Cursor c = db.rawQuery(
            "SELECT id, title, done FROM tasks ORDER BY id", null);
        int n = c.getCount();
        int done = 0;
        while (c.moveToNext()) if (c.getInt(2) != 0) done++;
        status.setText("Tasks: " + n + " (done " + done + ")");
        listHost.removeAllViews();
        c.moveToPosition(-1);
        while (c.moveToNext()) {
            final long id = c.getLong(0);
            final String title = c.getString(1);
            final int doneFlag = c.getInt(2);
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);
            Button tgl = new Button(this);
            tgl.setText("[" + id + "] " + (doneFlag != 0 ? "[x] " : "[ ] ")
                + title);
            tgl.setOnClickListener(new View.OnClickListener() {
                public void onClick(View v) { toggleTask(id, doneFlag); }
            });
            LinearLayout.LayoutParams tp = new LinearLayout.LayoutParams(
                0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
            row.addView(tgl, tp);
            Button del = new Button(this);
            del.setText("DEL");
            del.setOnClickListener(new View.OnClickListener() {
                public void onClick(View v) { deleteTask(id); }
            });
            row.addView(del, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));
            listHost.addView(row, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));
        }
        c.close();
    }
}
