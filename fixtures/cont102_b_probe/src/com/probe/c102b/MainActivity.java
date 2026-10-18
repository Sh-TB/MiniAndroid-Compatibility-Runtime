package com.probe.c102b;

import android.app.Activity;
import android.content.pm.ActivityInfo;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.os.Bundle;

/**
 * CONT-102 Batch B — #364 CONT-98 T2 (manifest parsing / component defaults)
 * + T7 (PackageManager/ApplicationInfo/PackageInfo truthfulness) +
 * T1 (package identity consistency at runtime; install-transaction
 * atomicity itself is gated by the F-NEW-376 reinstall battery 8/8).
 */
public class MainActivity extends Activity {

    void row(String tag, Object v) {
        System.err.println("[C102-" + tag + "] " + v);
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try {
            run();
            System.err.println("[C102-B-DONE] ok");
        } catch (Throwable t) {
            System.err.println("[C102-B-ERR] " + t);
        }
    }

    void run() throws Exception {
        PackageManager pm = getPackageManager();

        // ── T2: manifest → normalized package model ───────────────────
        row("M-PKG", getPackageName());                       // com.probe.c102b

        ApplicationInfo ai = getApplicationInfo();
        row("M-APP-PKG", ai.packageName);
        row("M-APP-ENABLED", ai.enabled);                     // default true
        row("M-TARGETSDK", ai.targetSdkVersion);              // 34
        row("M-MINSDK", ai.minSdkVersion);                    // 24 (if served)

        // component defaults: main = standard launchMode (0), exported true;
        // Second = singleTop (1), exported false.
        ActivityInfo main = pm.getActivityInfo(
                new android.content.ComponentName(this, MainActivity.class), 0);
        row("M-MAIN-EXPORTED", main.exported);                // true
        row("M-MAIN-LAUNCHMODE", main.launchMode);            // 0 standard
        ActivityInfo second = pm.getActivityInfo(
                new android.content.ComponentName(this, Second.class), 0);
        row("M-SECOND-EXPORTED", second.exported);            // false
        row("M-SECOND-LAUNCHMODE", second.launchMode);        // 1 singleTop

        // T1: identity — two lookups answer the SAME normalized model.
        ActivityInfo main2 = pm.getActivityInfo(
                new android.content.ComponentName(this, MainActivity.class), 0);
        row("I-IDENTITY", main2.exported == main.exported
                && main2.launchMode == main.launchMode);

        // ── T7: PackageInfo truthfulness ─────────────────────────────
        PackageInfo pi = pm.getPackageInfo(getPackageName(), 0);
        row("PM-VERSION-NAME", pi.versionName);               // 1.2.3
        row("PM-VERSION-CODE", pi.versionCode);               // 7
        row("PM-PKG-NAME", pi.packageName);

        PackageInfo pav = pm.getPackageInfo(getPackageName(),
                PackageManager.GET_ACTIVITIES);
        row("PM-ACTIVITY-COUNT",
                pav.activities == null ? -1 : pav.activities.length); // 2

        PackageInfo pperm = pm.getPackageInfo(getPackageName(),
                PackageManager.GET_PERMISSIONS);
        int found = 0;
        if (pperm.requestedPermissions != null) {
            for (String p : pperm.requestedPermissions) {
                if ("com.probe.c102b.DECLARED".equals(p)) found++;
            }
        }
        row("PM-REQUESTED-PERM", found);                      // 1

        // metadata round-trip
        Bundle md = getApplicationInfo().metaData;
        row("M-META", md == null ? "null" : Integer.valueOf(md.getInt("c102.meta", -1)));

        // declared permission checks (T8 share)
        int cpSelf = checkSelfPermission("com.probe.c102b.DECLARED");
        row("R-CHECKSELF-DECL", cpSelf);       // AOSP install-grant: 0 GRANTED
        int cpUndecl = checkSelfPermission("android.permission.CAMERA");
        row("R-CHECKSELF-UNDECL", cpUndecl);   // -1 DENIED

        // package-not-found law
        try {
            pm.getPackageInfo("no.such.pkg.c102b", 0);
            row("PM-NOTFOUND", "no-exception");
        } catch (PackageManager.NameNotFoundException e) {
            row("PM-NOTFOUND", "NameNotFoundException");
        }

        // T1: sourceDir identity — own staged APK readable (resolve law)
        row("I-SOURCEDIR", ai.sourceDir == null ? "null" : ai.sourceDir);
        java.io.File f = new java.io.File(ai.sourceDir);
        row("I-SOURCEDIR-PATH", f.getPath());
        row("I-SOURCEDIR-EXISTS", f.exists());
        row("I-SOURCEDIR-LEN", f.length());
    }
}
