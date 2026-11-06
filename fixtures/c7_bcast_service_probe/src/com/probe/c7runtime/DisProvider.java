package com.probe.c7runtime;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;

/** CODER7 WAVE-3: android:enabled="false" provider — not published
 *  (resolveContentProvider answers null; authority dispatch → the
 *  unknown-authority law). */
public class DisProvider extends ContentProvider {
    @Override public boolean onCreate() { return true; }
    @Override public Cursor query(Uri u, String[] p, String s, String[] sa,
                                  String so) {
        return new MatrixCursor(new String[]{"x"});
    }
    @Override public String getType(Uri u) { return null; }
    @Override public Uri insert(Uri u, ContentValues v) { return null; }
    @Override public int delete(Uri u, String s, String[] a) { return 0; }
    @Override public int update(Uri u, ContentValues v, String s,
                                String[] a) { return 0; }
}
