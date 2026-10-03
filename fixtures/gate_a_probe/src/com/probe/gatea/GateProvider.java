package com.probe.gatea;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.Context;
import android.content.UriMatcher;
import android.content.pm.ProviderInfo;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import java.io.File;
import java.util.ArrayList;
import java.util.List;

/** GATE A probe provider (issue #370 §10): proves the S-1 provider install
 *  stage ran BEFORE Application/Activity onCreate (AOSP ActivityThread
 *  order) and that attachInfo carries a live context + authority.
 *  #371 PHASE B1: the provider now holds REAL state — query answers a
 *  MatrixCursor, insert/update/delete mutate the table, openFile serves a
 *  real file via ParcelFileDescriptor, UriMatcher routes paths — so the
 *  full resolver chain (installed provider → client ContentResolver → URI
 *  dispatch → provider → Cursor → caller state change) is probe-asserted. */
public class GateProvider extends ContentProvider {

    public static boolean ran = false;
    public static boolean attachInfoContextNonNull = false;
    public static String attachAuthority = "";
    // #371 B1: provider-side dispatch observability (caller-independent).
    public static int queryCalls = 0;
    public static int insertCalls = 0;
    public static int updateCalls = 0;
    public static int deleteCalls = 0;
    public static int openFileCalls = 0;
    public static String lastInsertName = "";
    public static int lastUpdateValue = -1;

    // In-memory table: rows of [id, name, value] as strings.
    public static final List<String[]> TABLE = new ArrayList<>();
    public static final String[] COLUMNS = {"_id", "name", "value"};
    private static long nextId = 1;

    private static final int MATCH_DIR = 1;
    private static final int MATCH_ITEM = 2;
    private UriMatcher matcher;

    @Override public boolean onCreate() {
        ran = true;
        attachInfoContextNonNull = getContext() != null;
        matcher = new UriMatcher(UriMatcher.NO_MATCH);
        if (getContext() != null) {
            String a = attachAuthority.isEmpty()
                ? "com.probe.gatea.gateprovider" : attachAuthority;
            matcher.addURI(a, "notes", MATCH_DIR);
            matcher.addURI(a, "notes/#", MATCH_ITEM);
        }
        return true;
    }

    @Override public void attachInfo(Context context, ProviderInfo info) {
        super.attachInfo(context, info);
        if (info != null && info.authority != null) attachAuthority = info.authority;
        if (context != null) attachInfoContextNonNull = true;
    }

    @Override public Cursor query(Uri uri, String[] projection, String selection,
                                  String[] selectionArgs, String sortOrder) {
        queryCalls++;
        int code = matcher != null ? matcher.match(uri) : MATCH_DIR;
        MatrixCursor c = new MatrixCursor(COLUMNS);
        if (code == MATCH_DIR || code == MATCH_ITEM) {
            for (String[] row : TABLE) c.addRow(new Object[]{row[0], row[1], row[2]});
        }
        return c;
    }
    @Override public String getType(Uri uri) { return "vnd.probe.note"; }
    @Override public Uri insert(Uri uri, ContentValues values) {
        insertCalls++;
        String name = values != null && values.getAsString("name") != null
            ? values.getAsString("name") : "";
        lastInsertName = name;
        String[] row = new String[]{String.valueOf(nextId++), name,
            values != null && values.getAsString("value") != null
                ? values.getAsString("value") : ""};
        TABLE.add(row);
        return Uri.parse(uri.toString() + "/" + row[0]);
    }
    @Override public int delete(Uri uri, String selection, String[] selectionArgs) {
        deleteCalls++;
        if (TABLE.isEmpty()) return 0;
        TABLE.remove(TABLE.size() - 1);
        return 1;
    }
    @Override public int update(Uri uri, ContentValues values, String selection,
                                String[] selectionArgs) {
        updateCalls++;
        int v = values != null && values.getAsInteger("value") != null
            ? values.getAsInteger("value") : -1;
        lastUpdateValue = v;
        return TABLE.size();
    }

    /** #371 B1: FileProvider-style openFile — serves a REAL sandbox file the
     *  activity wrote, through a real ParcelFileDescriptor. */
    @Override public ParcelFileDescriptor openFile(Uri uri, String mode)
            throws java.io.FileNotFoundException {
        openFileCalls++;
        File f = new File(getContext().getFilesDir(), "provider_served.bin");
        if (!f.exists()) throw new java.io.FileNotFoundException(f.getPath());
        int m = "w".equals(mode)
            ? ParcelFileDescriptor.MODE_WRITE_ONLY
              | ParcelFileDescriptor.MODE_CREATE
              | ParcelFileDescriptor.MODE_TRUNCATE
            : ParcelFileDescriptor.MODE_READ_ONLY;
        return ParcelFileDescriptor.open(f, m);
    }
}
