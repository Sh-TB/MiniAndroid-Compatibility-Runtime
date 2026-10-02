package com.probe.loading;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.net.Uri;

/** S-1 provider-install-stage probe: onCreate flips a static flag the
 *  Activity reads — proves the provider ran BEFORE Application/Activity. */
public class ProbeProvider extends ContentProvider {
    public static boolean ran = false;
    @Override
    public boolean onCreate() { ran = true; return true; }
    @Override public Cursor query(Uri uri, String[] p, String s, String[] a, String o) { return null; }
    @Override public String getType(Uri uri) { return null; }
    @Override public Uri insert(Uri uri, ContentValues v) { return null; }
    @Override public int delete(Uri uri, String s, String[] a) { return 0; }
    @Override public int update(Uri uri, ContentValues v, String s, String[] a) { return 0; }
}
