package com.probe.c103a;

import android.app.Activity;
import android.content.ComponentName;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.ServiceInfo;
import android.os.Bundle;

/**
 * CONT-103 Batch A — the component-resolution law surface that telegram's
 * Lkg/i;.P died on: getServiceInfo(ComponentName, flags) across EVERY AOSP
 * ComponentName construction path (Class, (String,String), createRelative),
 * the GET_META_DATA seeding law, the NameNotFoundException negative contract,
 * the PackageInfo.services arm, and the sibling getActivityInfo/getProviderInfo
 * laws (F-NEW-425 / F-273) as regression rows.
 */
public class MainActivity extends Activity {

    void row(String tag, Object v) {
        System.err.println("[C103A-" + tag + "] " + v);
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try {
            run();
            System.err.println("[C103A-DONE] ok");
        } catch (Throwable t) {
            System.err.println("[C103A-ERR] " + t);
        }
    }

    void run() throws Exception {
        PackageManager pm = getPackageManager();
        String pkg = getPackageName();
        row("PKG", pkg);

        // R1 — ComponentName(Context, Class) path (telegram/Firebase uses this).
        ServiceInfo s1 = pm.getServiceInfo(new ComponentName(this, MyService.class), 0);
        row("S-CLS", s1 != null ? s1.name : "NULL");

        // R2 — ComponentName(String pkg, String cls) path.
        ServiceInfo s2 = pm.getServiceInfo(new ComponentName(pkg, "com.probe.c103a.MyService"), 0);
        row("S-STR", s2 != null ? s2.name : "NULL");

        // R3 — ComponentName.createRelative (API 26+) with leading-dot class.
        ServiceInfo s3 = pm.getServiceInfo(
                ComponentName.createRelative(pkg, ".MyService"), 0);
        row("S-REL", s3 != null ? s3.name : "NULL");

        // R4 — GET_META_DATA seeding law on <service><meta-data>.
        ServiceInfo s4 = pm.getServiceInfo(new ComponentName(this, MyService.class),
                PackageManager.GET_META_DATA);
        row("S-META", s4 != null && s4.metaData != null
                ? String.valueOf(s4.metaData.getString("c103.svcmeta")) : "NO-META");

        // R5 — negative contract: undeclared component → NameNotFoundException.
        boolean negCaught = false;
        try {
            pm.getServiceInfo(new ComponentName(this, Ghost.class), 0);
            row("S-NEG", "NO-THROW");
        } catch (PackageManager.NameNotFoundException e) {
            negCaught = true;
            row("S-NEG", "CAUGHT");
        }
        row("S-NEG-CHECK", negCaught);

        // R6 — PackageInfo.services arm (GET_SERVICES into getPackageInfo).
        PackageInfo pi = pm.getPackageInfo(pkg, PackageManager.GET_SERVICES);
        row("PI-SVC-COUNT", pi.services != null ? pi.services.length : -1);

        // R7 — getActivityInfo regression row (F-NEW-425 law intact).
        row("A-CLS", pm.getActivityInfo(new ComponentName(this, MainActivity.class), 0).name);

        // R8 — getProviderInfo regression row (F-273 law intact).
        try {
            Object pi2 = pm.getProviderInfo(
                    new ComponentName(pkg, "com.probe.c103a.DummyProvider"), 0);
            row("P-OK", pi2 != null ? "NONNULL" : "NULL");
        } catch (Throwable t) {
            row("P-OK", "ERR:" + t.getClass().getSimpleName());
        }

        // R9 — flattenToString/flattenAsString identity (recorded, both paths).
        ComponentName cn = new ComponentName(this, MyService.class);
        row("CN-FLAT", cn.flattenToString());

        // R10 — repeated query identity (telegram calls it twice).
        row("S-REPEAT",
                pm.getServiceInfo(new ComponentName(this, MyService.class), 128).name);
    }
}
