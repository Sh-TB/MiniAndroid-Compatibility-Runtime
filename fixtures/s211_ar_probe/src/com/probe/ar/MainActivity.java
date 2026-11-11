package com.probe.ar;

import android.app.Activity;
import android.os.Bundle;
import android.view.accessibility.AccessibilityManager;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * S211 A-R probe — the #576 findings R2/R3/R4/R5 as executable rows.
 * Every row is a generic platform contract (OpenJDK / AOSP), no
 * app-specific code. Runner-side gate reads the report rows.
 *
 * R2 rows — Math.random(): OpenJDK Math.java random() = one private
 * shared Random, nextDouble ∈ [0,1). Pre-fix the engine had NO law
 * (typed default 0.0 constant — #576 R2).
 * R3 rows — Random(long)/setSeed: OpenJDK Random.java:97 "two Random
 * objects created with the same seed generate identical sequences";
 * setSeed resets to that sequence. Pre-fix both were absent (one shared
 * stream for every Random — #576 R3).
 * R4 rows — PackageManager.checkPermission vs Context.checkSelfPermission:
 * AOSP ContextImpl.checkSelfPermission DELEGATES to checkPermission —
 * the two can never disagree. Pre-fix they disagreed for manifest-declared
 * normal permissions (#576 R4).
 * R5 rows — AccessibilityManager.isEnabled real-device default true
 * (typed default false pre-law); contentDescription round-trip (ZERO
 * hits in the runtime pre-capture — #576 R5).
 */
public class MainActivity extends Activity {

    private static String report = "";

    private static void row(String id, boolean pass, String detail) {
        report += id + "|" + (pass ? "PASS" : "FAIL") + "|" + detail + "\n";
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // ── R2 — Math.random() ──────────────────────────────────────
        double r1 = Math.random();
        row("R2-01", r1 >= 0.0 && r1 < 1.0, "Math.random() in [0,1): " + r1);
        double r2 = Math.random();
        row("R2-02", r2 != r1, "stream advances (two draws differ): "
                + r1 + " vs " + r2);

        // ── R3 — seeded Random laws ─────────────────────────────────
        java.util.Random a = new java.util.Random(42L);
        java.util.Random b = new java.util.Random(42L);
        int ia = a.nextInt(1000);
        int ib = b.nextInt(1000);
        row("R3-01", ia == ib,
                "same seed → identical first nextInt(1000): "
                        + ia + " vs " + ib);
        int ia2 = a.nextInt(1000);
        int ib2 = b.nextInt(1000);
        row("R3-02", ia2 == ib2 && ia2 != ia,
                "second draws identical and advance: "
                        + ia2 + " vs " + ib2);
        java.util.Random c = new java.util.Random(7L);
        int ic7 = c.nextInt(1000);
        c.setSeed(7L);
        int ic7b = c.nextInt(1000);
        row("R3-03", ic7 == ic7b,
                "setSeed resets the sequence: " + ic7 + " vs " + ic7b);
        java.util.Random d = new java.util.Random(-1L);
        row("R3-04", d.nextInt(1000) >= 0 && d.nextInt(1000) < 1000,
                "negative seed answers in [0,bound)");
        java.util.Random u = new java.util.Random();
        int iu = u.nextInt(500);
        row("R3-05", iu >= 0 && iu < 500,
                "unseeded Random keeps the standing lane: " + iu);
        double da = a.nextDouble();
        row("R3-06", da >= 0.0 && da < 1.0,
                "seeded nextDouble in [0,1): " + da);

        // ── R4 — permission classifier agreement ────────────────────
        String pkg = getPackageName();
        int selfNet = checkSelfPermission("android.permission.INTERNET");
        int pmNet = -2;
        try {
            pmNet = getPackageManager().checkPermission(
                    "android.permission.INTERNET", pkg);
        } catch (Throwable t) {
            pmNet = -3;
        }
        row("R4-01", selfNet == 0,
                "checkSelfPermission(INTERNET) GRANTED: " + selfNet);
        row("R4-02", pmNet == 0,
                "checkPermission(INTERNET) GRANTED (was DENIED pre-R4): "
                        + pmNet);
        row("R4-03", selfNet == pmNet,
                "AOSP delegate agreement: " + selfNet + " vs " + pmNet);
        int selfCam = checkSelfPermission("android.permission.CAMERA");
        int pmCam = -2;
        try {
            pmCam = getPackageManager().checkPermission(
                    "android.permission.CAMERA", pkg);
        } catch (Throwable t) {
            pmCam = -3;
        }
        row("R4-04", selfCam == -1 && pmCam == -1,
                "dangerous stays runtime-grant DENIED in both: "
                        + selfCam + " / " + pmCam);

        // ── R5 — accessibility laws ─────────────────────────────────
        boolean amOk = false;
        boolean amEnabled = false;
        boolean amTouch = true;
        try {
            Object am = getSystemService(ACCESSIBILITY_SERVICE);
            AccessibilityManager m = (AccessibilityManager) am;
            amEnabled = m.isEnabled();
            amTouch = m.isTouchExplorationEnabled();
            amOk = true;
        } catch (Throwable t) {
            amOk = false;
        }
        row("R5-01", amOk && !amEnabled,
                "isEnabled() = typed-default false (the #576 R5 → true law is"
                        + " RECORDED, NOT SHIPPED — the S211 dooz A/B proved"
                        + " it alone regresses the Compose golden; lands with"
                        + " the Compose delegate family): " + amEnabled);
        row("R5-02", amOk && !amTouch,
                "isTouchExplorationEnabled() false: " + amTouch);
        TextView dtv = new TextView(this);
        dtv.setContentDescription("s211-desc");
        CharSequence cd = dtv.getContentDescription();
        row("R5-03", cd != null && "s211-desc".contentEquals(cd),
                "contentDescription round-trip: " + cd);

        // ── visible render: runner-side pixel gate reads the frame ──
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF000000);
        TextView tv = new TextView(this);
        int total = countTotal();
        int pass = countPass();
        tv.setText("ARPROBE " + pass + "/" + total + "\n" + report);
        tv.setTextColor(0xFFFFFFFF);
        tv.setTextSize(24f);
        root.addView(tv);
        TextView marker = new TextView(this);
        marker.setText("S211ARPROBE");
        marker.setTextColor(0xFFFFFFFF);
        marker.setTextSize(24f);
        root.addView(marker);
        setContentView(root);
    }

    private static int countPass() {
        int p = 0;
        for (String line : report.split("\n"))
            if (line.contains("|PASS|")) p++;
        return p;
    }

    private static int countTotal() {
        int t = 0;
        for (String line : report.split("\n"))
            if (line.contains("|PASS|") || line.contains("|FAIL|")) t++;
        return t;
    }
}
