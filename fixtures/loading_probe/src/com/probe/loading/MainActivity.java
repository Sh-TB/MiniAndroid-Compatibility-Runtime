package com.probe.loading;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.AssetFileDescriptor;
import android.content.res.AssetManager;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Bundle;
import android.os.Environment;
import android.widget.TextView;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.InputStream;

/** LOADING-CAMPAIGN synthetic probe — exercises every P0 loading API.
 *  Results render as TextView text (visible in dump-view-tree/screenshot)
 *  and the run counter proves write→read→RESTART persistence. */
public class MainActivity extends Activity {

    private static String LOG = "";
    private static void log(String k, Object v) { LOG += k + "=" + v + "\n"; }

    private byte[] readAll(InputStream in) throws Exception {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        byte[] buf = new byte[512];
        int n;
        while ((n = in.read(buf)) > 0) bos.write(buf, 0, n);
        in.close();
        return bos.toByteArray();
    }

    private String readAllText(InputStream in) throws Exception {
        return new String(readAll(in), "UTF-8");
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        LOG = "";
        try { runProbe(); } catch (Throwable t) { log("PROBE-THROW", String.valueOf(t)); }
        TextView tv = new TextView(this);
        tv.setTextSize(13f);
        tv.setText(LOG);
        setContentView(tv);
    }

    private void runProbe() throws Exception {
        final String FILES = "/data/user/0/com.probe.loading/files";
        final String FILES_ALIAS = "/data/data/com.probe.loading/files";

        // 0. provider install stage (runs BEFORE this Activity per AOSP order)
        log("provider-ran", ProbeProvider.ran);

        // 1. ST-1 getAbsolutePath unhijacked (must NOT be /tmp/miniandroid)
        String abs = new File(FILES + "/probe.txt").getAbsolutePath();
        log("abs-path", abs);
        log("abs-ok", String.valueOf(abs.equals(FILES + "/probe.txt")));

        // 2. ST-2 write path: openFileOutput → close → exists → length
        FileOutputStream fos = openFileOutput("probe.txt", Context.MODE_PRIVATE);
        byte[] payload = "hello-probe-42".getBytes("UTF-8");
        fos.write(payload);
        fos.flush();
        fos.close();
        File pf = new File(FILES + "/probe.txt");
        log("write-exists", pf.exists());
        log("write-length", pf.length());

        // 3. read back via FileInputStream (absolute logical path)
        FileInputStream fis = new FileInputStream(pf);
        String back = readAllText(fis);
        log("read-back", back);
        log("read-ok", String.valueOf("hello-probe-42".equals(back)));

        // 4. openFileInput contract + missing → FileNotFoundException
        try {
            FileInputStream fis2 = openFileInput("probe.txt");
            log("ofi-read", readAllText(fis2));
        } catch (Throwable t) { log("ofi-throw", t.getClass().getSimpleName()); }
        try {
            FileInputStream miss = openFileInput("no-such-file.txt");
            miss.read();
            log("ofi-missing", "FAKE-SUCCESS");
        } catch (FileNotFoundException e) {
            log("ofi-missing", "FNFE-HONEST");
        } catch (Throwable t) { log("ofi-missing", t.getClass().getSimpleName()); }

        // 5. /data/user/0 ↔ /data/data alias law
        log("alias-exists", new File(FILES_ALIAS + "/probe.txt").exists());
        log("alias-read", readAllText(new FileInputStream(new File(FILES_ALIAS + "/probe.txt"))));

        // 6. fileList + deleteFile
        String[] fl = fileList();
        boolean listed = false;
        for (String s : fl) if ("probe.txt".equals(s)) listed = true;
        log("fileList-has-probe", listed);
        FileOutputStream fos2 = openFileOutput("del-me.txt", Context.MODE_PRIVATE);
        fos2.write("x".getBytes("UTF-8"));
        fos2.close();
        log("deleteFile", deleteFile("del-me.txt"));
        log("deleteFile-again", deleteFile("del-me.txt"));

        // 7. File.renameTo / length / isFile
        FileOutputStream fos3 = openFileOutput("ren-src.txt", Context.MODE_PRIVATE);
        fos3.write("renamed-bytes".getBytes("UTF-8"));
        fos3.close();
        File src = new File(FILES + "/ren-src.txt");
        File dst = new File(FILES + "/ren-dst.txt");
        log("renameTo", src.renameTo(dst));
        log("ren-dst-length", dst.length());
        log("ren-dst-isFile", dst.isFile());
        log("ren-src-gone", !src.exists());

        // 8. assets: existing / missing (FNFE) / nested / list
        AssetManager am = getAssets();
        String atxt = readAllText(am.open("a_text.txt"));
        log("asset-open", atxt);
        try {
            am.open("no_such_asset.bin");
            log("asset-missing", "FAKE-SUCCESS");
        } catch (FileNotFoundException e) {
            log("asset-missing", "FNFE-HONEST");
        }
        String nested = readAllText(am.open("nested/sub.txt"));
        log("asset-nested", nested);
        String[] names = am.list("");
        boolean hasAsset = false;
        for (String s : names) if ("a_text.txt".equals(s)) hasAsset = true;
        log("asset-list-has-text", hasAsset);
        String[] nestedNames = am.list("nested");
        log("asset-list-nested-len", nestedNames.length);

        // 9. openFd on STORED png asset → AFD → createInputStream → bytes
        try {
            AssetFileDescriptor afd = am.openFd("img.png");
            log("openFd-offset", afd.getStartOffset());
            log("openFd-length", afd.getLength());
            byte[] img = readAll(afd.createInputStream());
            log("afd-bytes", img.length);
            log("afd-png-magic", String.format("%02x%02x", img[0], img[1]));
        } catch (FileNotFoundException e) {
            log("openFd", "FNFE-HONEST-COMPRESSED");
        }

        // 10. decodeStream over the asset stream (asset → bytes → bitmap)
        InputStream ais = am.open("img.png");
        Bitmap bm = BitmapFactory.decodeStream(ais);
        log("decodeStream", bm != null ? (bm.getWidth() + "x" + bm.getHeight()) : "NULL");
        ais.close();

        // 11. decodeFile over a written sandbox file (write → decode → pixels)
        FileOutputStream imgOut = openFileOutput("img_copy.png", Context.MODE_PRIVATE);
        imgOut.write(readAll(am.open("img.png")));
        imgOut.close();
        Bitmap df = BitmapFactory.decodeFile(FILES + "/img_copy.png");
        log("decodeFile", df != null ? (df.getWidth() + "x" + df.getHeight()) : "NULL");

        // 12. SharedPreferences: escape round-trip + restart counter
        SharedPreferences sp = getSharedPreferences("probe", Context.MODE_PRIVATE);
        int runs = sp.getInt("runs", 0) + 1;
        sp.edit().putInt("runs", runs)
                 .putString("esc", "a<b>&c\"d'e")
                 .putBoolean("flag", true)
                 .putLong("big", 9876543210L)
                 .putFloat("f", 1.5f)
                 .commit();
        SharedPreferences sp2 = getSharedPreferences("probe", Context.MODE_PRIVATE);
        log("prefs-runs", runs);
        log("prefs-esc", sp2.getString("esc", "MISS"));
        log("prefs-flag", sp2.getBoolean("flag", false));
        log("prefs-long", sp2.getLong("big", 0L));
        log("prefs-float", String.valueOf(sp2.getFloat("f", 0f)));
        SharedPreferences.Editor e3 = sp2.edit();
        e3.remove("flag");
        e3.clear();   // then rewrite the counter so next run still increments
        e3.putInt("runs", runs).putString("post-clear", "survived").commit();
        SharedPreferences sp3 = getSharedPreferences("probe", Context.MODE_PRIVATE);
        log("prefs-clear-killed-esc", String.valueOf(!"a<b>&c\"d'e".equals(sp3.getString("esc", ""))));
        log("prefs-post-clear", sp3.getString("post-clear", "MISS"));

        // 13. SQLite: helper write → same-run read (restart proof via runs)
        Db db = new Db(this);
        SQLiteDatabase w = db.getWritableDatabase();
        w.execSQL("CREATE TABLE IF NOT EXISTS t(id INTEGER PRIMARY KEY, v TEXT)");
        w.execSQL("INSERT INTO t(v) VALUES('sql-row-" + runs + "')");
        log("sql-opened", w.getPath() != null && w.getPath().length() > 0);
        db.close();

        // 14. external storage (virtual volume) write → read
        File ext = new File(Environment.getExternalStorageDirectory(), "probe_ext.txt");
        FileOutputStream efos = new FileOutputStream(ext);
        efos.write("external-bytes-77".getBytes("UTF-8"));
        efos.close();
        log("ext-read", readAllText(new FileInputStream(ext)));
        log("ext-file-exists", ext.exists());
        File extApp = getExternalFilesDir(null);
        log("extApp-dir", extApp != null && extApp.getAbsolutePath().length() > 0);

        // 15. HOST ESCAPE closed: /etc, /home DENIED (Android-failure contract)
        try {
            FileInputStream h = new FileInputStream("/etc/hostname");
            h.read();
            log("host-deny", "FAKE-SUCCESS");
        } catch (FileNotFoundException ex) {
            log("host-deny", "FNFE-HONEST");
        }
        log("host-etc-exists", new File("/etc/passwd").exists());
        log("host-etc-mkdirs", new File("/etc/probe_escape").mkdirs());
        log("host-home-list", new File("/home").list() != null ? "LISTED" : "NULL-HONEST");

        // 16. /dev/urandom ALLOWED (Android-legal device node)
        try {
            FileInputStream u = new FileInputStream("/dev/urandom");
            int first = u.read();
            log("urandom-read", first >= 0 ? "OK" : "EOF");
            u.close();
        } catch (Throwable t) { log("urandom-read", "THROW:" + t.getClass().getSimpleName()); }

        // 17. isolation: another package's namespace invisible
        log("isolation-other-pkg", new File("/data/data/com.other.app/files/x").exists());

        // 18. raw resource + openRawResourceFd
        String raw = readAllText(getResources().openRawResource(R.raw.probe_raw));
        log("raw-contains", raw);
    }

    private static class Db extends SQLiteOpenHelper {
        Db(Context c) { super(c, "probe_db.sqlite", null, 1); }
        @Override public void onCreate(SQLiteDatabase d) {
            d.execSQL("CREATE TABLE IF NOT EXISTS t(id INTEGER PRIMARY KEY, v TEXT)");
        }
        @Override public void onUpgrade(SQLiteDatabase d, int o, int n) { }
    }
}
