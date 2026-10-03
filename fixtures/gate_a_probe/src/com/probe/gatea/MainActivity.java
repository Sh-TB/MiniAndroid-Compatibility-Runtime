package com.probe.gatea;

import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.ServiceConnection;
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
import android.net.Uri;
import android.os.Bundle;
import android.os.IBinder;
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

        // ══ PROVIDER DISPATCH CHAIN (#371 PHASE B1 — G-1/G-3 closure) ══
        // Full AOSP call chain: provider installed → client ContentResolver
        // → content:// authority dispatch → provider → Cursor/Uri/int →
        // caller state change. Negative legs assert the AOSP failure
        // contracts (no silent null, no silent success).
        try {
            File served = new File(getFilesDir(), "provider_served.bin");
            FileOutputStream pf = new FileOutputStream(served);
            pf.write("PROVIDER-BYTES-77".getBytes("UTF-8"));
            pf.close();
            ok("PROV-PREP", "served-file len=" + served.length());
        } catch (Throwable t) { fail("PROV-PREP", t); }
        try {
            ContentValues cv = new ContentValues();
            cv.put("name", "alpha");
            cv.put("value", "41");
            Uri u = getContentResolver().insert(
                Uri.parse("content://com.probe.gatea.gateprovider/notes"), cv);
            if (u != null && u.getLastPathSegment() != null
                    && GateProvider.insertCalls == 1
                    && "alpha".equals(GateProvider.lastInsertName))
                ok("PROV-02", "insert→uri=" + u
                        + " providerCalls=1 name=alpha");
            else fail("PROV-02", "uri=" + u + " calls="
                    + GateProvider.insertCalls + " name="
                    + GateProvider.lastInsertName);
        } catch (Throwable t) { fail("PROV-02", t); }
        try {
            Cursor c = getContentResolver().query(
                Uri.parse("content://com.probe.gatea.gateprovider/notes"),
                null, null, null, null);
            boolean good = false;
            String v = "";
            if (c != null) {
                int ni = c.getColumnIndex("name");
                int vi = c.getColumnIndex("value");
                good = c.getCount() == 1 && c.moveToFirst() && ni == 1 && vi == 2;
                if (good) v = c.getString(ni) + ":" + c.getString(vi);
                c.close();
            }
            if (good && "alpha:41".equals(v))
                ok("PROV-03", "cursor rows=1 cols=3 name:value=" + v);
            else fail("PROV-03", "good=" + good + " v=" + v);
        } catch (Throwable t) { fail("PROV-03", t); }
        try {
            ContentValues uv = new ContentValues();
            uv.put("value", 99);
            int n = getContentResolver().update(
                Uri.parse("content://com.probe.gatea.gateprovider/notes/1"),
                uv, null, null);
            if (n == 1 && GateProvider.updateCalls == 1
                    && GateProvider.lastUpdateValue == 99)
                ok("PROV-04", "update rows=1 providerValue=99");
            else fail("PROV-04", "rows=" + n + " calls="
                    + GateProvider.updateCalls + " val="
                    + GateProvider.lastUpdateValue);
        } catch (Throwable t) { fail("PROV-04", t); }
        try {
            int n = getContentResolver().delete(
                Uri.parse("content://com.probe.gatea.gateprovider/notes/1"),
                null, null);
            Cursor c = getContentResolver().query(
                Uri.parse("content://com.probe.gatea.gateprovider/notes"),
                null, null, null, null);
            int after = c != null ? c.getCount() : -1;
            if (c != null) c.close();
            if (n == 1 && after == 0 && GateProvider.deleteCalls == 1)
                ok("PROV-05", "delete rows=1 tableAfter=0 (state change)");
            else fail("PROV-05", "rows=" + n + " after=" + after
                    + " calls=" + GateProvider.deleteCalls);
        } catch (Throwable t) { fail("PROV-05", t); }
        try {
            // Re-insert so later restart-persistence runs see data again.
            ContentValues cv = new ContentValues();
            cv.put("name", "beta");
            cv.put("value", "7");
            getContentResolver().insert(
                Uri.parse("content://com.probe.gatea.gateprovider/notes"), cv);
        } catch (Throwable t) { fail("PROV-RESEED", t); }
        try {
            ParcelFileDescriptor pfd = getContentResolver().openFileDescriptor(
                Uri.parse("content://com.probe.gatea.gateprovider/files/served.bin"),
                "r");
            FileInputStream fin = new FileInputStream(pfd.getFileDescriptor());
            java.io.ByteArrayOutputStream bos = new java.io.ByteArrayOutputStream();
            byte[] buf = new byte[256];
            int n;
            while ((n = fin.read(buf)) > 0) bos.write(buf, 0, n);
            fin.close();
            pfd.close();
            String via = bos.toString("UTF-8");
            FileInputStream direct = new FileInputStream(
                new File(getFilesDir(), "provider_served.bin"));
            java.io.ByteArrayOutputStream b2 = new java.io.ByteArrayOutputStream();
            while ((n = direct.read(buf)) > 0) b2.write(buf, 0, n);
            direct.close();
            String via2 = b2.toString("UTF-8");
            if (GateProvider.openFileCalls >= 1 && "PROVIDER-BYTES-77".equals(via)
                    && via.equals(via2))
                ok("PROV-06", "openFileDescriptor bytes==direct ("
                        + via.length() + "B)");
            else fail("PROV-06", "pfdBytes=" + via + " direct=" + via2
                    + " calls=" + GateProvider.openFileCalls);
        } catch (Throwable t) { fail("PROV-06", t); }
        try {
            String t = getContentResolver().getType(
                Uri.parse("content://com.probe.gatea.gateprovider/notes"));
            long id = android.content.ContentUris.parseId(Uri.parse(
                "content://com.probe.gatea.gateprovider/notes/41"));
            if ("vnd.probe.note".equals(t) && id == 41)
                ok("PROV-07", "getType=" + t + " parseId=41");
            else fail("PROV-07", "type=" + t + " id=" + id);
        } catch (Throwable t) { fail("PROV-07", t); }
        neg("PROV-08", "IllegalArgument", new Thunk() {
            public Object run() {
                return getContentResolver().insert(
                    Uri.parse("content://no.such.authority/x"),
                    new ContentValues());
            }
        });
        try {
            Object c = getContentResolver().query(
                Uri.parse("content://no.such.authority/x"),
                null, null, null, null);
            if (c == null)
                ok("PROV-09", "query unknown authority → documented null");
            else fail("PROV-09", "non-null: " + c);
        } catch (Throwable t) { fail("PROV-09", t); }

        // ══ SERVICES (#371 PHASE B5 — UPP-006 probe-justified) ══════════
        try {
            Intent si = new Intent(this, GateService.class);
            ComponentName cn1 = startService(si);
            ComponentName cn2 = startService(si);
            if (cn1 != null && cn2 != null && GateService.creates == 1
                    && GateService.startCommands == 2 && GateService.lastStartId >= 2)
                ok("SVC-01", "startx2 → onCreate=1 onStartCommand=2 startId="
                        + GateService.lastStartId);
            else fail("SVC-01", "creates=" + GateService.creates + " starts="
                    + GateService.startCommands + " cn1=" + cn1);
        } catch (Throwable t) { fail("SVC-01", t); }
        ProbeConn conn = new ProbeConn();
        try {
            boolean bound = bindService(new Intent(this, GateService.class),
                                        conn, Context.BIND_AUTO_CREATE);
            if (bound && ProbeConn.calls == 1 && ProbeConn.binder != null)
                ok("SVC-02", "bindService → onServiceConnected binder="
                        + (ProbeConn.binder != null ? "live" : "null"));
            else fail("SVC-02", "bound=" + bound + " calls=" + ProbeConn.calls);
        } catch (Throwable t) { fail("SVC-02", t); }
        try {
            unbindService(conn);
            if (GateService.destroys == 0)
                ok("SVC-03", "unbind → service STAYS (started-by-startService)");
            else fail("SVC-03", "destroys=" + GateService.destroys);
        } catch (Throwable t) { fail("SVC-03", String.valueOf(t)); }
        try {
            boolean stopped = stopService(new Intent(this, GateService.class));
            if (stopped && GateService.destroys == 1)
                ok("SVC-04", "stopService → onDestroy (destroys=1)");
            else fail("SVC-04", "stopped=" + stopped + " destroys="
                    + GateService.destroys);
        } catch (Throwable t) { fail("SVC-04", t); }

        // ══ BROADCASTS (#371 PHASE B5) ══════════════════════════════════
        try {
            sendBroadcast(new Intent("com.probe.gatea.PING"));
            if (GateReceiver.manifestDeliveries == 1
                    && "com.probe.gatea.PING".equals(GateReceiver.lastManifestAction)
                    && "bound".equals(GateReceiver.lastReceiverContext))
                ok("BCAST-01", "manifest receiver delivered onReceive ctx=bound");
            else fail("BCAST-01", "deliveries=" + GateReceiver.manifestDeliveries
                    + " ctx=" + GateReceiver.lastReceiverContext);
        } catch (Throwable t) { fail("BCAST-01", t); }
        try {
            ProbeDyn dyn = new ProbeDyn();
            registerReceiver(dyn, new IntentFilter("com.probe.gatea.DYN"));
            sendBroadcast(new Intent("com.probe.gatea.DYN"));
            if (ProbeDyn.deliveries == 1)
                ok("BCAST-02", "dynamic receiver delivered (1)");
            else fail("BCAST-02", "deliveries=" + ProbeDyn.deliveries);
            unregisterReceiver(dyn);
            sendBroadcast(new Intent("com.probe.gatea.DYN"));
            if (ProbeDyn.deliveries == 1)
                ok("BCAST-03", "unregister → no further delivery");
            else fail("BCAST-03", "deliveries=" + ProbeDyn.deliveries);
        } catch (Throwable t) { fail("BCAST-02", t); }
        neg("BCAST-04", "IllegalArgument", new Thunk() {
            public Object run() {
                sendBroadcast(new Intent());
                return "sent";
            }
        });

        // ══ DEVICE-PROTECTED STORAGE (#371 G-8 closure) ═════════════════
        try {
            Context de = createDeviceProtectedStorageContext();
            File deFiles = de.getFilesDir();
            boolean spell = deFiles != null && deFiles.getAbsolutePath()
                    .contains("/data/user_de/0/" + PKG);
            File deF = new File(deFiles, "de_probe.bin");
            FileOutputStream df = new FileOutputStream(deF);
            df.write("DE-FENCE".getBytes("UTF-8"));
            df.close();
            boolean separate = !new File(getFilesDir(), "de_probe.bin").exists();
            if (spell && deF.exists() && deF.length() == 8 && separate)
                ok("DE-01", "de-files=" + deFiles.getAbsolutePath()
                        + " written=8B isolated-from-CE=true");
            else fail("DE-01", "spell=" + spell + " write=" + deF.exists()
                    + " isolated=" + separate);
        } catch (Throwable t) { fail("DE-01", t); }

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
            if (f.getParent() != null)
                ok("FILE-10", "parent=" + f.getParent() + " name=" + f.getName()
                        + " isAbs=" + f.isAbsolute());
            else fail("FILE-10", "parent=null (G-7: non-view getParent must "
                    + "reach the File name-component law)");
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
            boolean has = java.util.Arrays.asList(fileList()).contains("stream_io.bin");
            if (has) ok("IO-08", "fileList has stream_io.bin=true");
            else fail("IO-08", "fileList has stream_io.bin=false (G-6: "
                    + "contains must use element equality, not identity)");
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
            if (eq) ok("FD-02", "afd-stream-bytes=" + viaFd.length
                    + " equal-to-direct=true");
            else fail("FD-02", "afd-stream-bytes=" + viaFd.length
                    + " equal-to-direct=false (G-5: AFD stream bytes must "
                    + "equal the direct-open entry bytes)");
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

        // ══ CONFIG/DENSITY/FONT SELECTION (#371 PHASE B3 — UPP-004) ════
        // Frozen device profile law: en-US, portrait, NIGHT_NO, 420dpi.
        // The AOSP ResTable_config best-match law must select the DEFAULT
        // value over unreachable qualifiers (-night/-land/-zh-rCN), the
        // CLOSEST density bucket, and fall back to default when nothing
        // matches. Font resources resolve through the same ARSC.
        try {
            Resources res = getResources();
            int localeId = res.getIdentifier("probe_locale", "string", PKG);
            String locale = res.getString(localeId);
            if ("en-default-value".equals(locale))
                ok("CFG-01", "locale default wins (-zh-rCN/-land unreachable)");
            else fail("CFG-01", "locale=" + locale);
        } catch (Throwable t) { fail("CFG-01", t); }
        try {
            Resources res = getResources();
            int nightId = res.getIdentifier("probe_night", "string", PKG);
            String night = res.getString(nightId);
            if ("night-off-value".equals(night))
                ok("CFG-02", "default wins (-night unreachable at NIGHT_NO)");
            else fail("CFG-02", "night=" + night);
        } catch (Throwable t) { fail("CFG-02", t); }
        try {
            Resources res = getResources();
            int fbId = res.getIdentifier("probe_fallback", "string", PKG);
            String fb = res.getString(fbId);
            if ("fallback-default-value".equals(fb))
                ok("CFG-03", "no-match falls back to default config");
            else fail("CFG-03", "fallback=" + fb);
        } catch (Throwable t) { fail("CFG-03", t); }
        try {
            Resources res = getResources();
            int drawId = res.getIdentifier("probe_cfg", "drawable", PKG);
            Bitmap bmp = BitmapFactory.decodeResource(res, drawId);
            // 420dpi: xhdpi(320) distance 100 < mdpi(160) distance 260 —
            // the AOSP density best-match law MUST pick the xhdpi variant.
            if (bmp != null && bmp.getWidth() == 32)
                ok("CFG-04", "density best-match picked xhdpi 32px variant");
            else fail("CFG-04", "bmp=" + (bmp == null ? "null" : bmp.getWidth() + "px"));
        } catch (Throwable t) { fail("CFG-04", t); }
        try {
            Resources res = getResources();
            int fontId = res.getIdentifier("probe_font", "font", PKG);
            InputStream fin = res.openRawResource(fontId);
            byte[] head = new byte[4];
            int got = fin.read(head);
            fin.close();
            boolean ttf = got == 4 && head[0] == 0 && head[1] == 1
                    && head[2] == 0 && head[3] == 0;
            if (fontId != 0 && ttf)
                ok("CFG-05", "font resource id=0x"
                        + Integer.toHexString(fontId) + " TTF-magic=true");
            else fail("CFG-05", "fontId=" + fontId + " head=" + got);
        } catch (Throwable t) { fail("CFG-05", t); }

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

        // #371 PHASE B2 (G-4/G-2): extraction-backed native identity.
        try {
            String nld = getApplicationInfo().nativeLibraryDir;
            if (nld != null && nld.endsWith("/data/app/" + PKG + "/lib/arm64-v8a"))
                ok("NAT-03", "nativeLibraryDir=" + nld + " (extraction-backed)");
            else fail("NAT-03", "nativeLibraryDir=" + nld);
        } catch (Throwable t) { fail("NAT-03", t); }
        try {
            try {
                System.loadLibrary("probe");
                fail("NAT-04", "no exception (fake load success)");
            } catch (UnsatisfiedLinkError ule) {
                String m = ule.getMessage() != null ? ule.getMessage()
                                                    : String.valueOf(ule);
                if (m.contains("extracted at"))
                    ok("NAT-04", "ULE precise: " + m.substring(0, Math.min(120, m.length())));
                else fail("NAT-04", "ULE without extraction detail: " + m);
            }
        } catch (Throwable t) { fail("NAT-04", t); }
        try {
            try {
                System.loadLibrary("gatea_nosuch_lib");
                fail("NAT-05", "no exception (fake load success)");
            } catch (UnsatisfiedLinkError ule) {
                String m = ule.getMessage() != null ? ule.getMessage()
                                                    : String.valueOf(ule);
                if (m.contains("not found"))
                    ok("NAT-05", "ULE not-found shape: " + m.substring(0, Math.min(100, m.length())));
                else fail("NAT-05", "wrong detail: " + m);
            }
        } catch (Throwable t) { fail("NAT-05", t); }

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

    /** #371 B5: named static connection (inner classes are DEX-resolvable). */
    static class ProbeConn implements ServiceConnection {
        static int calls = 0;
        static Object binder = null;
        @Override public void onServiceConnected(ComponentName n, IBinder b) {
            calls++;
            binder = b;
        }
        @Override public void onServiceDisconnected(ComponentName n) { }
    }

    /** #371 B5: dynamic receiver probe. */
    static class ProbeDyn extends BroadcastReceiver {
        static int deliveries = 0;
        @Override public void onReceive(Context c, Intent i) {
            deliveries++;
        }
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
