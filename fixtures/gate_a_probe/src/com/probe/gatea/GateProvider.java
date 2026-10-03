package com.probe.gatea;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.Context;
import android.content.pm.ProviderInfo;
import android.database.Cursor;
import android.net.Uri;

/** GATE A probe provider (issue #370 §10): proves the S-1 provider install
 *  stage ran BEFORE Application/Activity onCreate (AOSP ActivityThread
 *  order) and that attachInfo carries a live context + authority. */
public class GateProvider extends ContentProvider {

    public static boolean ran = false;
    public static boolean attachInfoContextNonNull = false;
    public static String attachAuthority = "";

    @Override public boolean onCreate() {
        ran = true;
        attachInfoContextNonNull = getContext() != null;
        return true;
    }

    @Override public void attachInfo(Context context, ProviderInfo info) {
        super.attachInfo(context, info);
        if (info != null && info.authority != null) attachAuthority = info.authority;
        if (context != null) attachInfoContextNonNull = true;
    }

    @Override public Cursor query(Uri uri, String[] projection, String selection,
                                  String[] selectionArgs, String sortOrder) {
        return null; // honest: no rows; the probe records the call happened
    }
    @Override public String getType(Uri uri) { return "text/plain"; }
    @Override public Uri insert(Uri uri, ContentValues values) { return uri; }
    @Override public int delete(Uri uri, String selection, String[] selectionArgs) { return 0; }
    @Override public int update(Uri uri, ContentValues values, String selection,
                                String[] selectionArgs) { return 0; }
}
