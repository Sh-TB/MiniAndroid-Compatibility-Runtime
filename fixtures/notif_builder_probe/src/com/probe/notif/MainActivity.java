package com.probe.notif;

import android.app.Activity;
import android.app.Notification;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * CONT-41 probe — AOSP Notification$Builder fluent-chain object law
 * (the CONT-38v recorded frontier: androidx NotificationCompat$Builder
 * wraps a framework Notification.Builder; with no law the fluent setter
 * answered the STUBBED void and the chained call NPE'd on a null
 * receiver).
 *
 * Every row is a generic platform contract — no app-specific conditions:
 *
 *   NB-01  both builder constructors produce a non-null builder
 *   NB-02  chained fluent setters return THIS (reference identity)
 *   NB-03  build() returns a non-null Notification, distinct per call
 *   NB-04  the builder stays fluent AFTER build() (AOSP builders are
 *          stateful objects, not one-shot)
 *   NB-05  the NotificationCompat-style WRAPPER face: an app class stores
 *          the framework builder in a field, calls fluent setters on the
 *          FIELD across methods, and builds — the exact mechanism that
 *          killed NotificationCompat$Builder.<init> pc=64 on the real APK
 *   NB-06  setters called in void context (result unconsumed) are honest
 *          no-crash calls
 *   NB-07  distinct builders stay distinct (identity law, no shared
 *          singleton)
 *   NB-08  the deprecated direct `new Notification()` ctor yields a
 *          non-null Notification
 */
public class MainActivity extends Activity {

    private static String report = "";

    private static void row(String id, boolean pass, String detail) {
        report += id + "|" + (pass ? "PASS" : "FAIL") + "|" + detail + "\n";
    }

    /** The NotificationCompatBuilder wrap face (app-side wrapper). */
    private static class CompatStyleWrapper {
        final Notification.Builder fb;
        CompatStyleWrapper(android.content.Context c) {
            fb = new Notification.Builder(c);
        }
        CompatStyleWrapper icon(int smallIcon) {
            fb.setSmallIcon(smallIcon);
            return this;
        }
        CompatStyleWrapper title(CharSequence t) {
            fb.setContentTitle(t);
            return this;
        }
        Notification go() {
            return fb.build();
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // ── NB-01: both constructors produce a non-null builder.
        try {
            Notification.Builder b1 = new Notification.Builder(this);
            Notification.Builder b2 = new Notification.Builder(this, "chan");
            row("NB-01", b1 != null && b2 != null,
                "ctors b1=" + (b1 != null) + " b2=" + (b2 != null));
        } catch (Throwable t) { row("NB-01", false, "threw " + t); }

        // ── NB-02: chained fluent setters return THIS (AOSP fluent law).
        try {
            Notification.Builder b = new Notification.Builder(this);
            Notification.Builder r = b.setSmallIcon(1)
                                       .setContentTitle("t")
                                       .setContentText("x")
                                       .setOngoing(true)
                                       .setWhen(42L);
            row("NB-02", r == b, "fluent identity same-ref=" + (r == b));
        } catch (Throwable t) { row("NB-02", false, "threw " + t); }

        // ── NB-03: build() non-null; distinct per call (fresh object).
        try {
            Notification.Builder b = new Notification.Builder(this);
            Notification n1 = b.build();
            Notification n2 = b.build();
            row("NB-03", n1 != null && n2 != null && n1 != n2,
                "build n1=" + (n1 != null) + " n2=" + (n2 != null)
                + " distinct=" + (n1 != n2));
        } catch (Throwable t) { row("NB-03", false, "threw " + t); }

        // ── NB-04: builder stays fluent after build().
        try {
            Notification.Builder b = new Notification.Builder(this);
            Notification n1 = b.build();
            Notification.Builder r = b.setContentTitle("post");
            Notification n2 = r.build();
            row("NB-04", n1 != null && r == b && n2 != null && n1 != n2,
                "post-build reuse fluent=" + (r == b) + " n2=" + (n2 != null));
        } catch (Throwable t) { row("NB-04", false, "threw " + t); }

        // ── NB-05: the NotificationCompat-style wrapper face — the exact
        // mechanism recorded on the real APK (field-stored builder, fluent
        // setters across methods, build at the end).
        try {
            CompatStyleWrapper w = new CompatStyleWrapper(this);
            Notification n = w.icon(0x0108007e).title("Wrapper").go();
            row("NB-05", n != null,
                "wrapper build non-null=" + (n != null));
        } catch (Throwable t) { row("NB-05", false, "threw " + t); }

        // ── NB-06: void-context setter calls (result unconsumed).
        try {
            Notification.Builder b = new Notification.Builder(this);
            b.setOnlyAlertOnce(true);
            b.setProgress(10, 1, false);
            row("NB-06", true, "void-context setters no-crash");
        } catch (Throwable t) { row("NB-06", false, "threw " + t); }

        // ── NB-07: distinct builders stay distinct (identity law).
        try {
            Notification.Builder b1 = new Notification.Builder(this);
            Notification.Builder b2 = new Notification.Builder(this);
            row("NB-07", b1 != b2, "distinct builders=" + (b1 != b2));
        } catch (Throwable t) { row("NB-07", false, "threw " + t); }

        // ── NB-08: the deprecated direct ctor yields a non-null
        // Notification (the Notification; <init> contract).
        try {
            Notification n = new Notification();
            row("NB-08", n != null, "direct ctor non-null=" + (n != null));
        } catch (Throwable t) { row("NB-08", false, "threw " + t); }

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        TextView tv = new TextView(this);
        int pass = 0, total = 0;
        for (String line : report.split("\n")) {
            if (line.isEmpty()) continue;
            total++;
            if (line.contains("|PASS|")) pass++;
        }
        tv.setText("NBPROBE " + pass + "/" + total + "\n" + report);
        root.addView(tv);
        setContentView(root);
    }
}
