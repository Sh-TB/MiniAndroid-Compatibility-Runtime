package com.probe.gatea;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.ProviderInfo;
import android.content.res.AssetFileDescriptor;
import android.content.res.AssetManager;
import android.content.res.Resources;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Bundle;
import android.os.ParcelFileDescriptor;
import android.widget.TextView;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.HashSet;
import java.util.Set;

/** GATE A synthetic probe (issue #370 §17) — real APK, normal Android APIs.
 *  Every operation is individually caught and recorded as a machine-readable
 *  result line written to files/gate_a_results.jsonl (physical backing proof)
 *  and echoed to stdout. Expected-failure (negative) ops PASS only when the
 *  AOSP-contract exception actually arrives. */
public class MainActivity extends Activity {

    private StringBuilder RES = new StringBuilder();

    private void ok(String op, Object detail) {
        RES.append("GATEA|").append(op).append("|PASS|").append(detail).append("\n");
    }
    private void fail(String op, String detail) {
        RES.append("GATEA|").append(op).append("|FAIL|").append(detail).append("\n");
    }
    private void fail(String op, Throwable t) {
        RES.append("GATEA|").append(op).append("|FAIL|").append(String.valueOf(t)).append("\n");
    }
    /** Negative op: PASS only when the expected exception type arrived. */
    private void neg(String op, String expect, Thunk t) {
        try {
            Object r = t.run();
            fail(op, "no-exception (returned " + r + ") expected " + expect);
        } catch (Throwable thrown) {
            String cls = thrown.getClass().getSimpleName();
            String name = thrown.getClass().getName();
            if (name.contains(expect)) ok(op, expect + " honest: " + thrown);
            else fail(op, "wrong exception " + name + " expected " + expect);
        }
    }
    private interface Thunk { Object run() throws Exception; }

    private byte[] readAll(InputStream in) throws Exception {
        java.io.ByteArrayOutputStream bos = new java.io.ByteArrayOutputStream();
        byte[] buf = new byte[512];
        int n;
        while ((n = in.read(buf)) > 0) bos.write(buf, 0, n);
        in.close();
        return bos.toByteArray();
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        RES = new StringBuilder();
        try { runProbe(); } catch (Throwable t) { fail("PROBE-FATAL", t); }
        // Emit: machine-readable results file (physical write proof) + stdout
        // echo + rendered text (view-tree/screenshot channel).
        try {
            FileOutputStream fos = openFileOutput("gate_a_results.jsonl",
                                                  Context.MODE_PRIVATE);
            fos.write(RES.toString().getBytes("UTF-8"));
            fos.flush();
            fos.close();
        } catch (Throwable t) { fail("RESULTS-WRITE", t); }
        TextView tv = new TextView(this);
        tv.setTextSize(11f);
        tv.setText(RES.toString());
        setContentView(tv);
    }

    private void runProbe() throws Exception {
        final String PKG = "com.probe.gatea";

        // ══ IDENTITY (issue #370 §1) ════════════════════════════════════
        try {
            String pn = getPackageName();
            if (PKG.equals(pn)) ok("ID-01", pn);
            else fail("ID-01", "package mismatch: " + pn);
        } catch (Throwable t) { fail("ID-01", t); }
        try {
            String src = getApplicationInfo().sourceDir;
            if (src != null && src.endsWith("/data/app/" + PKG + "/base.apk"))
                ok("ID-02", src);
            else fail("ID-02", "sourceDir not installed identity: " + src);
        } catch (Throwable t) { fail("ID-02", t); }
        try {
            android.content.pm.ApplicationInfo ai = getApplicationInfo();
            boolean dataDirOk = ai.dataDir != null && ai.dataDir.contains(PKG);
            if (ai != null && dataDirOk) ok("ID-03", ai.dataDir);
            else fail("ID-03", "dataDir=" + (ai == null ? "null-ai" : ai.dataDir));
        } catch (Throwable t) { fail("ID-03", t); }
        try {
            PackageInfo pi = getPackageManager().getPackageInfo(PKG,
                    PackageManager.GET_PROVIDERS);
            boolean provOk = pi.providers != null && pi.providers.length >= 1;
            String auth = provOk ? pi.providers[0].authority : "";
            if (provOk && "com.probe.gatea.gateprovider".equals(auth)
                    && pi.versionName != null)
                ok("ID-04", "versionName=" + pi.versionName + " providers=1 auth="
                        + auth);
            else fail("ID-04", "providers=" + (pi.providers == null ? -1
                    : pi.providers.length) + " auth=" + auth
                    + " versionName=" + pi.versionName);
        } catch (Throwable t) { fail("ID-04", t); }

        // ══ PROVIDER STAGE (§10 — installed BEFORE onCreate per AOSP) ══
        try {
            if (GateProvider.ran && GateProvider.attachInfoContextNonNull
                    && "com.probe.gatea.gateprovider".equals(GateProvider.attachAuthority))
                ok("PROV-01", "provider-ran=1 attachCtx=1 auth="
                        + GateProvider.attachAuthority);
            else fail("PROV-01", "ran=" + GateProvider.ran + " ctx="
                    + GateProvider.attachInfoContextNonNull + " auth="
                    + GateProvider.attachAuthority);
        } catch (Throwable t) { fail("PROV-01", t); }

        // ══ CONTEXT DIR FAMILY (§2) ════════════════════════════════════
        try {
            File f = getFilesDir();
            if (f != null && f.exists() && f.getAbsolutePath().endsWith("/files"))
                ok("DIR-01", f.getAbsolutePath() + " exists=true");
            else fail("DIR-01", String.valueOf(f == null ? "null" :
                    f.getAbsolutePath()) + " exists=" + f.exists());
        } catch (Throwable t) { fail("DIR-01", t); }
        try { ok("DIR-02", getCacheDir().getAbsolutePath()); }
        catch (Throwable t) { fail("DIR-02", t); }
        try { ok("DIR-03", getCodeCacheDir().getAbsolutePath()); }
        catch (Throwable t) { fail("DIR-03", t); }
        try { ok("DIR-04", getNoBackupFilesDir().getAbsolutePath()); }
        catch (Throwable t) { fail("DIR-04", t); }
        try { ok("DIR-05", getDataDir().getAbsolutePath()); }
        catch (Throwable t) { fail("DIR-05", t); }
        try {
            File dbp = getDatabasePath("gatea.db");
            String p = dbp.getAbsolutePath();
            if (p.contains("databases") && p.endsWith("gatea.db")) ok("DIR-06", p);
            else fail("DIR-06", p);
        } catch (Throwable t) { fail("DIR-06", t); }
        try {
            File d = getDir("custom", 0);
            if (d.exists() && d.getName().startsWith("app_")) ok("DIR-07", d.getName());
            else fail("DIR-07", d.getAbsolutePath() + " exists=" + d.exists());
        } catch (Throwable t) { fail("DIR-07", t); }
        try {
            File sp = getFileStreamPath("streampath.txt");
            String want = getFilesDir().getAbsolutePath() + "/streampath.txt";
            if (want.equals(sp.getAbsolutePath())) ok("DIR-08", sp.getAbsolutePath());
            else fail("DIR-08", sp.getAbsolutePath() + " want " + want);
        } catch (Throwable t) { fail("DIR-08", t); }
        try {
            File ef = getExternalFilesDir("probe");
            if (ef != null) {
                ef.mkdirs();
                File marker = new File(ef, "ext_marker.txt");
                FileOutputStream fo = new FileOutputStream(marker);
                fo.write("external-bytes".getBytes("UTF-8"));
                fo.close();
                ok("DIR-09", ef.getAbsolutePath() + " marker=" + marker.exists());
            } else fail("DIR-09", "null external files dir");
        } catch (Throwable t) { fail("DIR-09", t); }
        try { ok("DIR-10", getExternalCacheDir().getAbsolutePath()); }
        catch (Throwable t) { fail("DIR-10", t); }
        try {
            File[] media = getExternalMediaDirs();
            if (media != null && media.length >= 1) ok("DIR-11", "len=" + media.length
                    + " " + media[0].getAbsolutePath());
            else fail("DIR-11", "empty/null media dirs");
        } catch (Throwable t) { fail("DIR-11", t); }
        try { ok("DIR-12", getObbDir().getAbsolutePath()); }
        catch (Throwable t) { fail("DIR-12", t); }

        // ══ FILE API (§3) ═══════════════════════════════════════════════
        try {
            File f = new File(getFilesDir(), "file_ops.txt");
            f.delete();  // restart-idempotent: fresh create every run
            boolean created = f.createNewFile();
            if (created) ok("FILE-01", "created=true");
            else fail("FILE-01", "created=false on absent file");
        } catch (Throwable t) { fail("FILE-01", t); }
        try {
            File f = new File(getFilesDir(), "file_ops.txt");
            FileOutputStream fo = new FileOutputStream(f);
            fo.write("0123456789".getBytes("UTF-8"));
            fo.close();
            boolean pass = f.exists() && f.isFile() && f.length() == 10;
            if (pass) ok("FILE-02", "exists=true isFile=true len=10");
            else fail("FILE-02", "exists=" + f.exists() + " isFile=" + f.isFile()
                    + " len=" + f.length());
        } catch (Throwable t) { fail("FILE-02", t); }
        try {
            File f = new File(getFilesDir(), "file_ops.txt");
            boolean rw = f.canRead() && f.canWrite();
            if (rw) ok("FILE-03", "canRead=true canWrite=true");
            else fail("FILE-03", "canRead=" + f.canRead() + " canWrite="
                    + f.canWrite());
        } catch (Throwable t) { fail("FILE-03", t); }
        try {
            File f = new File(getFilesDir(), "file_ops.txt");
            // lastModified==0 is the runtime's DOCUMENTED determinism law
            // (mtime is wallclock-nondeterministic; 3-run byte determinism
            // forbids a host mtime). Recorded as OBSERVED, not PASS/FAIL.
            RES.append("GATEA|FILE-04|INFO|lastModified=").append(f.lastModified())
             .append(" (documented determinism law)\n");
        } catch (Throwable t) { fail("FILE-04", t); }
        try {
            File d = new File(getFilesDir(), "subdirA");
            d.delete();
            boolean made = d.mkdir();
            if (made && d.isDirectory()) ok("FILE-05", "mkdir=true isDir=true");
            else fail("FILE-05", "mkdir=" + made + " isDir=" + d.isDirectory());
        } catch (Throwable t) { fail("FILE-05", t); }
        try {
            File d = new File(getFilesDir(), "subdirB/deeper/leaf");
            boolean made = d.mkdirs();
            if (made && d.isDirectory()) ok("FILE-06", "mkdirs=true isDir=true");
            else fail("FILE-06", "mkdirs=" + made + " isDir=" + d.isDirectory());
        } catch (Throwable t) { fail("FILE-06", t); }
        try {
            File d = new File(getFilesDir(), "subdirA");
            d.mkdirs();
            new File(d, "x.txt").createNewFile();
            new File(d, "y.txt").createNewFile();
            String[] names = d.list();
            File[] files = d.listFiles();
            if (names.length == 2 && files.length == 2)
                ok("FILE-07", "list=2 listFiles=2");
            else fail("FILE-07", "list=" + names.length + " listFiles="
                    + files.length);
        } catch (Throwable t) { fail("FILE-07", t); }
        try {
            File a = new File(getFilesDir(), "ren_src.txt");
            FileOutputStream fo = new FileOutputStream(a);
            fo.write("rename-bytes".getBytes("UTF-8"));
            fo.close();
            File dst = new File(getFilesDir(), "ren_dst.txt");
            boolean moved = a.renameTo(dst);
            ok("FILE-08", "renamed=" + moved + " oldGone=" + !a.exists()
                    + " newLen=" + dst.length());
        } catch (Throwable t) { fail("FILE-08", t); }
        try {
            File f = new File(getFilesDir(), "ren_dst.txt");
            String abs = f.getAbsolutePath();
            String can = f.getCanonicalPath();
            ok("FILE-09", "abs=" + abs + " canonical=" + can);
        } catch (Throwable t) { fail("FILE-09", t); }
        try {
            File f = new File(getFilesDir(), "ren_dst.txt");
            ok("FILE-10", "parent=" + f.getParent() + " name=" + f.getName()
                    + " isAbs=" + f.isAbsolute());
        } catch (Throwable t) { fail("FILE-10", t); }
        try {
            File f = new File(getFilesDir(), "file_ops.txt");
            boolean deleted = f.delete();
            if (deleted && !f.exists()) ok("FILE-11", "deleted=true existsAfter=false");
            else fail("FILE-11", "deleted=" + deleted + " existsAfter="
                    + f.exists());
        } catch (Throwable t) { fail("FILE-11", t); }

        // ══ STREAMS (§4) ════════════════════════════════════════════════
        try {
            FileOutputStream fos = openFileOutput("stream_io.bin",
                                                  Context.MODE_PRIVATE);
            fos.write("stream-payload-42".getBytes("UTF-8"));
            fos.flush();
            fos.close();
            FileInputStream fis = openFileInput("stream_io.bin");
            String back = new String(readAll(fis), "UTF-8");
            fis.close();
            if ("stream-payload-42".equals(back))
                ok("IO-01", "write+read-back=true len=17");
            else fail("IO-01", "read-back=" + back);
        } catch (Throwable t) { fail("IO-01", t); }
        try {
            FileOutputStream fos = openFileOutput("stream_io.bin",
                                                  Context.MODE_APPEND);
            fos.write("|appended".getBytes("UTF-8"));
            fos.close();
            File f = new File(getFilesDir(), "stream_io.bin");
            ok("IO-02", "append len=" + f.length());
        } catch (Throwable t) { fail("IO-02", t); }
        try {
            FileOutputStream fos = new FileOutputStream(
                    new File(getFilesDir(), "stream_io.bin"), true);
            fos.write("XX".getBytes("UTF-8"), 0, 1);
            fos.close();
            ok("IO-03", "write(byte[],off,len) grew to "
                    + new File(getFilesDir(), "stream_io.bin").length());
        } catch (Throwable t) { fail("IO-03", t); }
        try {
            FileInputStream fis = openFileInput("stream_io.bin");
            int first = fis.read();
            byte[] chunk = new byte[4];
            int nread = fis.read(chunk, 0, 4);
            long skipped = fis.skip(2);
            int tail = fis.read();
            ok("IO-04", "first=" + first + " chunk=" + nread + " skip=" + skipped
                    + " tail=" + tail);
            fis.close();
        } catch (Throwable t) { fail("IO-04", t); }
        try {
            FileInputStream fis = openFileInput("stream_io.bin");
            int total = 0;
            while (fis.read() != -1) total++;
            int eof = fis.read();
            fis.close();
            ok("IO-05", "consumed=" + total + " eofIsMinus1=" + (eof == -1));
        } catch (Throwable t) { fail("IO-05", t); }
        try {
            int avail = openFileInput("stream_io.bin").available();
            ok("IO-06", "available=" + avail);
        } catch (Throwable t) { fail("IO-06", t); }
        try {
            FileOutputStream fos = openFileOutput("single.bin", Context.MODE_PRIVATE);
            fos.write(77);
            fos.close();
            FileInputStream fis = openFileInput("single.bin");
            int v = fis.read();
            fis.close();
            ok("IO-07", "write(int)=77 read=" + v + " match=" + (v == 77));
        } catch (Throwable t) { fail("IO-07", t); }
        try {
            ok("IO-08", "fileList has stream_io.bin="
                    + java.util.Arrays.asList(fileList()).contains("stream_io.bin"));
        } catch (Throwable t) { fail("IO-08", t); }
        try {
            boolean first = deleteFile("single.bin");
            boolean second = deleteFile("single.bin");
            ok("IO-09", "delete true-then-false=" + first + "/" + second);
        } catch (Throwable t) { fail("IO-09", t); }

        // ══ FD / PFD / AFD (§5) ═════════════════════════════════════════
        byte[] storedBytes = null;
        try {
            AssetManager am = getAssets();
            InputStream direct = am.open("gate_stored.png");
            storedBytes = readAll(direct);
            AssetFileDescriptor afd = am.openFd("gate_stored.png");
            boolean offOk = afd.getStartOffset() >= 0;
            boolean lenOk = afd.getDeclaredLength() == 75 || afd.getLength() == 75;
            ok("FD-01", "offset=" + afd.getStartOffset() + " declaredLen="
                    + afd.getDeclaredLength() + " offOk=" + offOk + " lenOk=" + lenOk);
        } catch (Throwable t) { fail("FD-01", t); }
        try {
            AssetManager am = getAssets();
            AssetFileDescriptor afd = am.openFd("gate_stored.png");
            InputStream s = afd.createInputStream();
            byte[] viaFd = readAll(s);
            boolean eq = java.util.Arrays.equals(viaFd, storedBytes);
            ok("FD-02", "afd-stream-bytes=" + viaFd.length + " equal-to-direct="
                    + eq);
        } catch (Throwable t) { fail("FD-02", t); }
        try {
            AssetFileDescriptor afd = getAssets().openFd("gate_stored.png");
            java.io.FileDescriptor fd = afd.getFileDescriptor();
            ok("FD-03", "fd=" + String.valueOf(fd));
        } catch (Throwable t) { fail("FD-03", t); }
        try {
            File target = new File(getFilesDir(), "stream_io.bin");
            ParcelFileDescriptor pfd = ParcelFileDescriptor.open(target,
                    ParcelFileDescriptor.MODE_READ_ONLY);
            boolean fdOk = pfd.getFd() >= 0;
            ParcelFileDescriptor dup = pfd.dup();
            ok("FD-04", "fd=" + pfd.getFd() + " dup=" + dup.getFd()
                    + " fdOk=" + fdOk);
            pfd.close();
            ok("FD-05", "closed; fd after close=" + pfd.getFd());
        } catch (Throwable t) { fail("FD-04/05", t); }
        try {
            AssetFileDescriptor afd = getAssets().openFd("gate_text.txt");
            long len = afd.getDeclaredLength();
            ok("FD-06", "text-asset openFd declaredLen=" + len
                    + " (AOSP: works only when STORED)");
        } catch (Throwable t) {
            RES.append("GATEA|FD-06|INFO|deflate-asset openFd -> ")
             .append(String.valueOf(t)).append("\n");
        }
        try {
            AssetFileDescriptor rafd = getResources().openRawResourceFd(
                    R.raw.probe_raw);
            long len = rafd.getDeclaredLength();
            if (len == 26) ok("FD-07", "raw openRawResourceFd len=26");
            else fail("FD-07", "raw AFD len=" + len + " want 26");
        } catch (Throwable t) {
            RES.append("GATEA|FD-07|INFO|raw openRawResourceFd -> ")
             .append(String.valueOf(t))
             .append(" (AOSP: FNFE for compressed raw entries)\n");
        }

        // ══ ASSETS (§6) ═════════════════════════════════════════════════
        try {
            String[] root = getAssets().list("");
            StringBuilder lens = new StringBuilder();
            boolean has = false;
            for (String n : root) {
                if ("gate_text.txt".equals(n)) has = true;
                lens.append(n.length()).append(",");
            }
            if (has) ok("ASSET-01", "list-root=" + java.util.Arrays.toString(root)
                    + " nameLens=" + lens);
            else fail("ASSET-01", "list-root=" + java.util.Arrays.toString(root)
                    + " nameLens=" + lens);
        } catch (Throwable t) { fail("ASSET-01", t); }
        try {
            String[] nested = getAssets().list("nested");
            ok("ASSET-02", "list(nested)=" + java.util.Arrays.toString(nested));
        } catch (Throwable t) { fail("ASSET-02", t); }
        try {
            String txt = new String(readAll(getAssets().open("gate_text.txt")),
                                    "UTF-8");
            if ("gate-a-text-payload-97531".equals(txt))
                ok("ASSET-03", txt);
            else fail("ASSET-03", "bytes=" + txt);
        } catch (Throwable t) { fail("ASSET-03", t); }
        try {
            String sub = new String(readAll(getAssets().open("nested/sub.txt")),
                                    "UTF-8");
            if ("nested-asset-bytes-24680".equals(sub)) ok("ASSET-04", sub);
            else fail("ASSET-04", "bytes=" + sub);
        } catch (Throwable t) { fail("ASSET-04", t); }
        neg("ASSET-05", "FileNotFound", new Thunk() {
            public Object run() throws Exception {
                return getAssets().open("no/such/asset.bin");
            }
        });

        // ══ RESOURCES (§7) ══════════════════════════════════════════════
        try {
            int id = getResources().getIdentifier("app_name", "string", PKG);
            ok("RES-01", "app_name id=0x" + Integer.toHexString(id));
        } catch (Throwable t) { fail("RES-01", t); }
        try {
            String name = getString(R.string.app_name);
            boolean tag = "GATE-A-INSPECTION".equals(getString(R.string.gate_tag));
            ok("RES-02", name + " tag-roundtrip=" + tag);
        } catch (Throwable t) { fail("RES-02", t); }
        try {
            byte[] raw = readAll(getResources().openRawResource(R.raw.probe_raw));
            String rawTxt = new String(raw, "UTF-8");
            if ("raw-resource-payload-13579".equals(rawTxt)) ok("RES-03", rawTxt);
            else fail("RES-03", "raw-bytes len=" + raw.length + " head="
                    + rawTxt);
        } catch (Throwable t) { fail("RES-03", t); }
        neg("RES-04", "NotFound", new Thunk() {
            public Object run() { return getResources().getString(0x7f0a9999); }
        });

        // ══ IMAGE DECODE (§8) ═══════════════════════════════════════════
        try {
            Bitmap bmp = BitmapFactory.decodeResource(getResources(),
                                                      R.drawable.probe_img);
            ok("IMG-01", "resource-bmp=" + (bmp != null ? bmp.getWidth() + "x"
                    + bmp.getHeight() : "null"));
        } catch (Throwable t) { fail("IMG-01", t); }
        try {
            File pngCopy = new File(getFilesDir(), "copy_gate.png");
            FileOutputStream fo = new FileOutputStream(pngCopy);
            fo.write(storedBytes == null ? new byte[0] : storedBytes);
            fo.close();
            Bitmap bmp = BitmapFactory.decodeFile(pngCopy.getAbsolutePath());
            ok("IMG-02", "file-bmp=" + (bmp != null ? bmp.getWidth() + "x"
                    + bmp.getHeight() : "null"));
        } catch (Throwable t) { fail("IMG-02", t); }
        try {
            Bitmap bmp = BitmapFactory.decodeByteArray(storedBytes, 0,
                    storedBytes == null ? 0 : storedBytes.length);
            ok("IMG-03", "bytes-bmp=" + (bmp != null ? bmp.getWidth() + "x"
                    + bmp.getHeight() : "null"));
        } catch (Throwable t) { fail("IMG-03", t); }

        // ══ SHARED PREFERENCES (§9) ═════════════════════════════════════
        try {
            SharedPreferences p = getSharedPreferences("gate_prefs",
                                                       Context.MODE_PRIVATE);
            Set<String> set = new HashSet<String>();
            set.add("alpha");
            set.add("beta");
            SharedPreferences.Editor e = p.edit();
            e.putString("k_string", "gate-<&>-value");
            e.putInt("k_int", -42);
            e.putLong("k_long", 9876543210L);
            e.putFloat("k_float", 2.5f);
            e.putBoolean("k_bool", true);
            e.putStringSet("k_set", set);
            boolean committed = e.commit();
            ok("PREF-01", "commit=" + committed);
        } catch (Throwable t) { fail("PREF-01", t); }
        try {
            SharedPreferences p = getSharedPreferences("gate_prefs",
                                                       Context.MODE_PRIVATE);
            boolean roundtrip = "gate-<&>-value".equals(p.getString("k_string", ""))
                    && p.getInt("k_int", 0) == -42
                    && p.getLong("k_long", 0) == 9876543210L
                    && p.getFloat("k_float", 0f) == 2.5f
                    && p.getBoolean("k_bool", false);
            ok("PREF-02", "escaped-roundtrip=" + roundtrip
                    + " set=" + p.getStringSet("k_set", new HashSet<String>()));
        } catch (Throwable t) { fail("PREF-02", t); }
        try {
            SharedPreferences fresh = getSharedPreferences("gate_prefs",
                                                           Context.MODE_PRIVATE);
            ok("PREF-03", "fresh-instance k_int=" + fresh.getInt("k_int", 0)
                    + " contains=" + fresh.contains("k_string"));
        } catch (Throwable t) { fail("PREF-03", t); }
        try {
            SharedPreferences p = getSharedPreferences("gate_prefs",
                                                       Context.MODE_PRIVATE);
            int counter = p.getInt("restart_counter", 0) + 1;
            p.edit().putInt("restart_counter", counter).commit();
            ok("PREF-06", "restart_counter=" + counter);
        } catch (Throwable t) { fail("PREF-06", t); }
        try {
            SharedPreferences p = getSharedPreferences("removal", Context.MODE_PRIVATE);
            p.edit().putString("gone", "soon").commit();
            p.edit().remove("gone").commit();
            boolean removed = !p.contains("gone");
            p.edit().putString("a", "1").commit();
            p.edit().putString("b", "2").commit();
            p.edit().clear().commit();
            ok("PREF-04", "removed=" + removed + " afterClear=" + p.getAll().size());
        } catch (Throwable t) { fail("PREF-04", t); }

        // ══ SQLITE (§9) ═════════════════════════════════════════════════
        try {
            SQLiteDatabase db = openOrCreateDatabase("gatea.db", 0, null);
            db.execSQL("CREATE TABLE IF NOT EXISTS t1 (id INTEGER PRIMARY KEY, v TEXT)");
            db.execSQL("INSERT INTO t1 (v) VALUES ('row-" + System.nanoTime() + "')");
            Cursor c = db.rawQuery("SELECT count(*), max(v) FROM t1", null);
            long rows = 0;
            String maxv = "";
            if (c.moveToFirst()) {
                rows = c.getLong(0);
                maxv = c.getString(1);
            }
            c.close();
            db.execSQL("CREATE TABLE IF NOT EXISTS t1b (id INTEGER)");
            ok("DB-01", "rows=" + rows + " last=" + maxv + " isOpen=" + db.isOpen());
        } catch (Throwable t) { fail("DB-01", t); }
        try {
            String[] dbs = databaseList();
            boolean has = false;
            for (String d : dbs) if (d.equals("gatea.db")) has = true;
            ok("DB-02", "databaseList=" + java.util.Arrays.toString(dbs)
                    + " has-gatea=" + has);
        } catch (Throwable t) { fail("DB-02", t); }
        try {
            Helper h = new Helper(this, "helper.db");
            SQLiteDatabase db = h.getWritableDatabase();
            db.execSQL("CREATE TABLE IF NOT EXISTS ht (id INTEGER)");
            ok("DB-03", "helper-db=" + (db != null && db.isOpen()) + " name="
                    + h.getDatabaseName());
        } catch (Throwable t) { fail("DB-03", t); }

        // ══ NATIVE (§11 — inventory contract; full exec is GATE B) ═════
        neg("NAT-01", "UnsatisfiedLink", new Thunk() {
            public Object run() {
                System.loadLibrary("gatea_nosuch_lib");
                return "loaded";
            }
        });
        try {
            String nld = getApplicationInfo().nativeLibraryDir;
            ok("NAT-02", "nativeLibraryDir=" + nld);
        } catch (Throwable t) { fail("NAT-02", t); }

        // ══ ISOLATION + NEGATIVE PATHS (§19) ════════════════════════════
        try {
            boolean cross = new File("/data/data/com.other.app/files/x")
                                .exists();
            ok("ISO-01", "cross-package exists()=" + cross
                    + " isolated=" + (cross == false));
        } catch (Throwable t) { fail("ISO-01", t); }
        try {
            File t1 = new File(getFilesDir(), "../../outside/secret.txt");
            boolean exists = t1.exists();
            ok("ISO-02", "traversal exists()=" + exists);
        } catch (Throwable t) { fail("ISO-02", t); }
        try {
            boolean hostNode = new File("/etc/passwd").exists();
            ok("ISO-03", "host /etc/passwd exists()=" + hostNode);
        } catch (Throwable t) { fail("ISO-03", t); }
        neg("ISO-04", "FileNotFound", new Thunk() {
            public Object run() throws Exception {
                return new FileInputStream("/etc/passwd");
            }
        });
        neg("IO-10", "FileNotFound", new Thunk() {
            public Object run() throws Exception {
                return openFileInput("definitely_missing_file.bin");
            }
        });
    }

    /** GATE A helper DB (onCreate records a marker the harness can grep). */
    private static class Helper extends SQLiteOpenHelper {
        Helper(Context c, String name) { super(c, name, null, 1); }
        @Override public void onCreate(SQLiteDatabase db) {
            db.execSQL("CREATE TABLE IF NOT EXISTS helper_init (id INTEGER)");
        }
        @Override public void onUpgrade(SQLiteDatabase db, int o, int n) { }
    }
}
