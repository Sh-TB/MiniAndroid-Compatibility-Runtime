package com.probe.f293;

import android.app.Activity;
import android.content.Context;
import android.os.Bundle;
import android.widget.TextView;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.util.ArrayList;
import java.util.List;

/**
 * F-NEW-293 probe — GATE A APP-VISIBLE PATH LAW (dir-getter family).
 *
 * AOSP law (frameworks/base ContextImpl + the engine's own data_root.h
 * GATE A header): an application NEVER sees a host path. Context.getFilesDir()
 * answers /data/user/0/<pkg>/files (alias /data/data/<pkg>/files — the user-0
 * alias), and every Context-anchored dir getter mints its File with that
 * ANDROID-LOGICAL spelling; the physical mapping happens inside
 * resolve_android_path at open time.
 *
 * Pre-fix face (CONT-33 §9 decode, reproduced on composeStopwatch): the
 * default app-data root is the RELATIVE literal "runtime/data", so the GATE A
 * reverse mapping (logical_android_path) compared an ABSOLUTE host path
 * against a RELATIVE prefix table and silently no-oped — getFilesDir minted
 * its File with the host spelling "runtime/data/data/data/<pkg>/files". The
 * app then joined child names onto it; every open re-anchored the (relative)
 * host spelling under package_data_dir() AGAIN, multiplying the prefix
 * (runtime/data/data/data/<pkg>/runtime/data/… ENOENT face).
 *
 * Contract rows (the app-visible namespace contract, not the physical store):
 *
 *   DIR-FILES-LOGICAL  getFilesDir().getAbsolutePath() starts with "/data/"
 *                      and ends with "/files"        (THE law row)
 *   DIR-CACHE-LOGICAL  getCacheDir().getAbsolutePath() same family guard
 *   FILE-JOIN-LOGICAL  new File(filesDir, "datastore/preference.preferences_pb")
 *                      .getPath() starts with "/data/data/" and carries no
 *                      host prefix (the exact DataStore join shape)
 *   RT-CREATE-EXISTS   f.delete(); f.createNewFile()==true then
 *                      f.exists()==true (delete makes it deterministic
 *                      across runs — createNewFile answers false when the
 *                      file already exists, AOSP-legal)
 *   RT-WRITE-READ      write "F293-PAYLOAD" through FileOutputStream →
 *                      read back through a FRESH File minted from
 *                      getFilesDir() → same bytes (same-file law)
 *   DS-DIR-MKDIRS      after File(filesDir,"datastore").mkdirs(), a fresh
 *                      File(filesDir,"datastore").isDirectory()==true
 *   NO-HOST-LEAK       none of the three app-visible strings contains
 *                      "runtime/" (explicit leak guard)
 *   SUMMARY            PASS iff all rows pass
 *
 * Hygiene: activity class "Main" carries no substring that any name-gated
 * engine arm matches (CONT-32 probe-hygiene law).
 */
public class Main extends Activity {
    static List<String> out = new ArrayList<String>();
    static int pass = 0, fail = 0;

    static synchronized void row(String id, boolean ok, String detail) {
        out.add("F293|" + id + "|" + (ok ? "PASS" : "FAIL") + "|" + detail);
        if (ok) pass++; else fail++;
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        out.clear(); pass = 0; fail = 0;
        TextView tv = new TextView(this);
        setContentView(tv);

        String pkg = getPackageName();
        String hostMark = "runtime/";

        // DIR-FILES-LOGICAL — THE law row: the app-visible files dir must be
        // the AOSP logical spelling (either /data/data or /data/user alias),
        // never the host store spelling.
        String filesAbs;
        String filesAbsDetail;
        try {
            File fd = getFilesDir();
            filesAbs = fd.getAbsolutePath();
            filesAbsDetail = filesAbs;
        } catch (Throwable t) {
            filesAbs = null;
            filesAbsDetail = "threw " + t.getClass().getName();
        }
        boolean filesOk = filesAbs != null
            && filesAbs.startsWith("/data/")
            && filesAbs.endsWith("/files");
        row("DIR-FILES-LOGICAL", filesOk,
            "got=\"" + filesAbsDetail + "\" want=/data/<" + pkg + ">/files");

        // DIR-CACHE-LOGICAL — same family, cache fence.
        String cacheAbs;
        String cacheAbsDetail;
        try {
            cacheAbs = getCacheDir().getAbsolutePath();
            cacheAbsDetail = cacheAbs;
        } catch (Throwable t) {
            cacheAbs = null;
            cacheAbsDetail = "threw " + t.getClass().getName();
        }
        boolean cacheOk = cacheAbs != null
            && cacheAbs.startsWith("/data/")
            && cacheAbs.endsWith("/cache");
        row("DIR-CACHE-LOGICAL", cacheOk,
            "got=\"" + cacheAbsDetail + "\" want=/data/<" + pkg + ">/cache");

        // FILE-JOIN-LOGICAL — the exact DataStore join shape (parent File +
        // relative child), inspected on getPath (app-visible spelling).
        String joinPath = null;
        String joinDetail;
        try {
            File fd = getFilesDir();
            File pb = new File(fd, "datastore/preference.preferences_pb");
            joinPath = pb.getPath();
            joinDetail = joinPath;
        } catch (Throwable t) {
            joinDetail = "threw " + t.getClass().getName();
        }
        boolean joinOk = joinPath != null
            && joinPath.startsWith("/data/data/")
            && !joinPath.contains(hostMark);
        row("FILE-JOIN-LOGICAL", joinOk,
            "got=\"" + joinDetail + "\" want=/data/data/…/files/datastore/…");

        // RT-CREATE-EXISTS — the create half of the round-trip.
        // delete() first: the data root persists across runs, and AOSP
        // createNewFile() answers false (not an error) when the file already
        // exists — the delete makes the row deterministic across runs.
        boolean created = false, exists = false;
        String rtDetail;
        try {
            File probeFile = new File(getFilesDir(), "probe293.txt");
            probeFile.delete();
            created = probeFile.createNewFile();
            exists = probeFile.exists();
            rtDetail = "created=" + created + " exists=" + exists
                + " path=\"" + probeFile.getPath() + "\"";
        } catch (Throwable t) {
            rtDetail = "threw " + t.getClass().getName()
                + " (" + t.getMessage() + ")";
        }
        row("RT-CREATE-EXISTS", created && exists, rtDetail);

        // RT-WRITE-READ — the same-file law: write through one File handle,
        // read back through a FRESH File minted from getFilesDir().
        String payload = "F293-PAYLOAD";
        String readBack = null;
        String wrDetail;
        try {
            File w = new File(getFilesDir(), "probe293.txt");
            FileOutputStream fos = new FileOutputStream(w);
            fos.write(payload.getBytes("UTF-8"));
            fos.close();
            File r = new File(getFilesDir(), "probe293.txt");
            FileInputStream fis = new FileInputStream(r);
            byte[] buf = new byte[64];
            int n = fis.read(buf);
            fis.close();
            readBack = n > 0 ? new String(buf, 0, n, "UTF-8") : "";
            wrDetail = "wrote=\"" + payload + "\" read=\"" + readBack + "\"";
        } catch (Throwable t) {
            wrDetail = "threw " + t.getClass().getName()
                + " (" + t.getMessage() + ")";
        }
        row("RT-WRITE-READ", payload.equals(readBack), wrDetail);

        // DS-DIR-MKDIRS — the DataStore datastore/ dir law across two
        // independently minted File objects. The law: after the mkdirs()
        // attempt (true = created; false = already existed — also legal),
        // a FRESH File for the same dir MUST answer isDirectory()==true
        // (deterministic across runs; the mkdirs return value is detail).
        boolean isDir = false;
        String dsDetail;
        try {
            File d1 = new File(getFilesDir(), "datastore");
            boolean mkdirs = d1.mkdirs();
            File d2 = new File(getFilesDir(), "datastore");
            isDir = d2.isDirectory();
            dsDetail = "mkdirs=" + mkdirs + " freshIsDirectory=" + isDir
                + " path=\"" + d2.getPath() + "\"";
        } catch (Throwable t) {
            dsDetail = "threw " + t.getClass().getName();
        }
        row("DS-DIR-MKDIRS", isDir, dsDetail);

        // NO-HOST-LEAK — explicit guard: no app-visible string carries the
        // host store spelling. Negatives must be honestly false.
        String sweep = String.valueOf(filesAbs) + "|" + String.valueOf(cacheAbs)
            + "|" + String.valueOf(joinPath);
        row("NO-HOST-LEAK", !sweep.contains(hostMark),
            "leak=" + sweep.contains(hostMark));

        StringBuilder sb = new StringBuilder();
        for (String s : out) sb.append(s).append('\n');
        String summary = "F293|SUMMARY|"
                + (fail == 0 && pass >= 7 ? "PASS" : "FAIL")
                + "| " + pass + " pass, " + fail + " fail";
        sb.append(summary);
        tv.setText(sb.toString());
        try {
            FileOutputStream fos = openFileOutput("f293_results.txt", MODE_PRIVATE);
            fos.write(sb.toString().getBytes("UTF-8"));
            fos.close();
        } catch (Throwable t2) { }
    }
}
