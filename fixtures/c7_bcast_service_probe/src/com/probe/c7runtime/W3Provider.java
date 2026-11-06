package com.probe.c7runtime;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.Context;
import android.content.pm.ProviderInfo;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import java.io.File;
import java.io.FileNotFoundException;

/** CODER7 WAVE-3: the provider behind the ContentProviderClient law
 *  (acquireContentProviderClient → client.query/release) and the
 *  openTypedAssetFileDescriptor/openFile error-propagation contract. Real
 *  in-memory table; openFile answers FileNotFoundException for the
 *  documented missing-file shape (AOSP ContentProvider.openFile base). */
public class W3Provider extends ContentProvider {
    public static int queryCalls = 0;
    public static String attachAuthority = "";
    public static final String[] COLS = {"_id", "name"};

    @Override public boolean onCreate() { return true; }

    @Override public void attachInfo(Context context, ProviderInfo info) {
        super.attachInfo(context, info);
        if (info != null && info.authority != null)
            attachAuthority = info.authority;
    }

    @Override public Cursor query(Uri uri, String[] p, String sel,
                                  String[] sargs, String sort) {
        queryCalls++;
        MatrixCursor c = new MatrixCursor(COLS);
        c.addRow(new Object[]{"1", "alpha"});
        c.addRow(new Object[]{"2", "beta"});
        return c;
    }
    @Override public String getType(Uri uri) {
        return "vnd.android.cursor.dir/vnd.probe.w3";
    }
    @Override public Uri insert(Uri uri, ContentValues v) { return null; }
    @Override public int delete(Uri uri, String s, String[] a) { return 0; }
    @Override public int update(Uri uri, ContentValues v, String s,
                                String[] a) { return 0; }
    @Override public ParcelFileDescriptor openFile(Uri uri, String mode)
            throws FileNotFoundException {
        throw new FileNotFoundException("No files supported by the provider "
                                            + "at " + uri);
    }
}
