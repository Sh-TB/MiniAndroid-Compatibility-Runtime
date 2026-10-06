package com.probe.w3;

import android.app.Activity;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.io.Serializable;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;
import java.util.ListIterator;
import java.util.concurrent.CancellationException;

/**
 * CONT-7 W3 synthetic probe — source->law->positive/negative rows for the
 * three generic laws fixed this wave:
 *
 *   F-NEW-253  platform hierarchy fallback in Class.isInstance /
 *              isAssignableFrom (Parcelable.isInstance(Bundle) must be TRUE
 *              — AOSP: Bundle extends BaseBundle implements Parcelable).
 *   F-NEW-254  libcore exception-chain extends edges (CancellationException
 *              extends IllegalStateException extends RuntimeException ...
 *              Throwable) reachable from an app subclass.
 *   F-NEW-255  ListIterator shadow law: List.listIterator() never null;
 *              hasPrevious/previous/nextIndex/previousIndex cursor contract
 *              (OpenJDK AbstractList.ListItr).
 *
 * Every row is a generic platform contract — no app-specific conditions.
 * Visual verdict bands render through the view tree (pixel-gate reads it).
 */
public class MainActivity extends Activity {

    private static String report = "";

    private static void row(String id, boolean pass, String detail) {
        report += id + "|" + (pass ? "PASS" : "FAIL") + "|" + detail + "\n";
    }

    /** A plain app Exception subclass — must still be-a Throwable. */
    private static class AppException extends CancellationException { }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // ── F-NEW-253 positives ────────────────────────────────────────
        try {
            Bundle b = new Bundle();
            boolean r = android.os.Parcelable.class.isInstance(b);
            row("W3-01", r, "Parcelable.isInstance(Bundle)=" + r + " (AOSP: TRUE)");
        } catch (Throwable t) { row("W3-01", false, "threw " + t); }

        try {
            // The exact dooz face: isInstance via reflection on the class
            // array walk (saveable platform check shape).
            Class<?>[] accept = { Serializable.class, android.os.Parcelable.class,
                                  String.class, Bundle.class };
            boolean any = false;
            Bundle b = new Bundle();
            for (Class<?> c : accept) if (c.isInstance(b)) { any = true; break; }
            row("W3-02", any, "acceptable-classes walk Bundle accepted=" + any);
        } catch (Throwable t) { row("W3-02", false, "threw " + t); }

        try {
            // isAssignableFrom arm of the same law.
            boolean r = android.os.Parcelable.class.isAssignableFrom(Bundle.class);
            row("W3-03", r, "Parcelable.isAssignableFrom(Bundle)=" + r);
        } catch (Throwable t) { row("W3-03", false, "threw " + t); }

        // ── F-NEW-253 negatives (honest false answers preserved) ──────
        try {
            boolean r = android.os.Parcelable.class.isInstance("plain string");
            row("W3-04", !r, "Parcelable.isInstance(String)=" + r + " (must be FALSE)");
        } catch (Throwable t) { row("W3-04", false, "threw " + t); }

        try {
            boolean r = android.os.Parcelable.class.isInstance(null);
            row("W3-05", !r, "Parcelable.isInstance(null)=" + r + " (OpenJDK: FALSE)");
        } catch (Throwable t) { row("W3-05", false, "threw " + t); }

        // ── F-NEW-254 positives (platform exception chain) ─────────────
        try {
            CancellationException ce = new CancellationException("probe");
            row("W3-06", ce instanceof Throwable,
                "CancellationException instanceof Throwable (extends chain)");
        } catch (Throwable t) { row("W3-06", false, "threw " + t); }

        try {
            AppException ae = new AppException();
            boolean r = Throwable.class.isInstance(ae);
            row("W3-07", r, "Throwable.isInstance(app CancellationException subclass)=" + r);
        } catch (Throwable t) { row("W3-07", false, "threw " + t); }

        try {
            boolean r = IllegalStateException.class.isAssignableFrom(AppException.class);
            row("W3-08", r, "IllegalStateException.isAssignableFrom(app subclass chain)");
        } catch (Throwable t) { row("W3-08", false, "threw " + t); }

        // ── F-NEW-254 negative ─────────────────────────────────────────
        try {
            boolean r = Throwable.class.isInstance(null);
            row("W3-09", !r, "Throwable.isInstance(null)=" + r + " (must be FALSE)");
        } catch (Throwable t) { row("W3-09", false, "threw " + t); }

        // ── F-NEW-255 positives (ListIterator shadow law) ──────────────
        try {
            List<String> list = new ArrayList<String>();
            list.add("a"); list.add("b"); list.add("c");
            ListIterator<String> it = list.listIterator();
            boolean ok = (it != null) && it.hasNext() && "a".equals(it.next())
                && "b".equals(it.next()) && "c".equals(it.next())
                && !it.hasNext() && it.hasPrevious()
                && "c".equals(it.previous()) && "b".equals(it.previous())
                && it.nextIndex() == 1 && it.previousIndex() == 0;
            row("W3-10", ok, "ArrayList listIterator forward+backward cursor walk ok=" + ok);
        } catch (Throwable t) { row("W3-10", false, "threw " + t); }

        try {
            List<String> list = new ArrayList<String>();
            list.add("x");
            ListIterator<String> it = list.listIterator(1);
            boolean ok = (it != null) && !it.hasNext() && it.hasPrevious()
                && "x".equals(it.previous());
            row("W3-11", ok, "listIterator(index=size) starts at end, previous works");
        } catch (Throwable t) { row("W3-11", false, "threw " + t); }

        // ── F-NEW-255 negative ─────────────────────────────────────────
        try {
            List<String> list = new ArrayList<String>();
            ListIterator<String> it = list.listIterator();
            boolean ok = (it != null) && !it.hasNext() && !it.hasPrevious();
            row("W3-12", ok, "empty list: hasNext=false AND hasPrevious=false (no crash)");
        } catch (Throwable t) { row("W3-12", false, "threw " + t); }

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        TextView tv = new TextView(this);
        int pass = 0, total = 0;
        for (String line : report.split("\n")) {
            if (line.isEmpty()) continue;
            total++;
            if (line.contains("|PASS|")) pass++;
        }
        tv.setText("W3PROBE " + pass + "/" + total + "\n" + report);
        root.addView(tv);
        setContentView(root);
    }
}
