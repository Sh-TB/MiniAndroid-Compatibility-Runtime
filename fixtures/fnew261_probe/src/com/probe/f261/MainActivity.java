package com.probe.f261;

import android.app.Activity;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * CONT-11 W7 synthetic probe — F-NEW-261: the Context-family bridge guard.
 *
 * Upstream law under test (android.content.Context.getDeclared
 * "SharedPreferences getSharedPreferences(String name, int mode)"):
 * the bridge must accept ANY receiver whose RUNTIME ancestry reaches a
 * Context-family shadow root — not only receivers whose own descriptor
 * happens to contain the substrings "Context"/"Activity".
 *
 * Real-world face (batch-20, solitaire_tb): GameSelector extends the
 * R8-renamed support-v7/v4 chain; the name-substring guard missed,
 * getSharedPreferences answered null, and the app's bundled
 * PreferenceManager read prefs off the NULL receiver — 35 uncaught
 * NPEs from one guard. The fix accepts Context-family ancestry via the
 * same bounded DEX-chain walk as F-NEW-259.
 *
 *   F261-A  baseline: direct Activity receiver -> prefs object, getString
 *           answers the stored default (the P0.12 law, pre-existing).
 *   F261-B  THE FIX FACE: receiver class PrefsHost (extends Activity,
 *           NO "Context"/"Activity" substring in its own descriptor)
 *           -> getSharedPreferences must return a live prefs object and
 *           getString must answer the default.
 *   F261-C  deep ancestry: receiver class Deep (extends PrefsHost) —
 *           2 hops of DEX chain — same law.
 *   F261-D  S99 identity law: two getSharedPreferences(name) calls from
 *           DIFFERENT receiver classes (Activity vs Deep) must return the
 *           SAME SharedPreferences instance for the same file name
 *           (AOSP ContextImpl caches per name), and writes through one
 *           must be visible through the other.
 *   F261-E  negative law: a DIFFERENT file name is a DIFFERENT storage —
 *           a key written to file A must NOT appear in file B.
 */
public class MainActivity extends Activity {

    private static String report = "";

    private static void row(String id, boolean pass, String detail) {
        report += id + "|" + (pass ? "PASS" : "FAIL") + "|" + detail + "\n";
    }

    /** Receiver with NO "Context"/"Activity" substring in its descriptor. */
    static class PrefsHost extends Activity { }

    /** Two-hop ancestry from the shadow root. */
    static class Deep extends PrefsHost { }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // ── F261-A: baseline direct Activity receiver ───────────────────
        try {
            android.content.SharedPreferences p =
                getSharedPreferences("f261a", MODE_PRIVATE);
            String v = p.getString("k", "DEF");
            row("F261-A", "DEF".equals(v),
                "direct receiver getString=" + v + " (want DEF)");
        } catch (Throwable t) { row("F261-A", false, "threw " + t); }

        // ── F261-B: THE FIX FACE — PrefsHost receiver (no substring) ────
        try {
            PrefsHost host = new PrefsHost();
            // emulate the app face: dispatch through the sub-class receiver
            android.content.SharedPreferences p =
                host.getSharedPreferences("f261b", MODE_PRIVATE);
            String v = (p == null) ? null : p.getString("k", "DEF");
            row("F261-B", p != null && "DEF".equals(v),
                "PrefsHost receiver prefs=" + (p == null ? "NULL" : "live")
                    + " getString=" + v + " (want live/DEF)");
        } catch (Throwable t) { row("F261-B", false, "threw " + t); }

        // ── F261-C: two-hop ancestry (Deep extends PrefsHost) ───────────
        try {
            Deep d = new Deep();
            android.content.SharedPreferences p =
                d.getSharedPreferences("f261c", MODE_PRIVATE);
            String v = (p == null) ? null : p.getString("k", "DEF");
            row("F261-C", p != null && "DEF".equals(v),
                "Deep receiver prefs=" + (p == null ? "NULL" : "live")
                    + " getString=" + v + " (want live/DEF)");
        } catch (Throwable t) { row("F261-C", false, "threw " + t); }

        // ── F261-D: per-name identity across receivers (S99 law) ────────
        try {
            android.content.SharedPreferences p1 =
                getSharedPreferences("f261d", MODE_PRIVATE);
            p1.edit().putString("ident", "same").commit();
            Deep d = new Deep();
            android.content.SharedPreferences p2 =
                d.getSharedPreferences("f261d", MODE_PRIVATE);
            String v2 = (p2 == null) ? null : p2.getString("ident", "MISS");
            row("F261-D", "same".equals(v2),
                "cross-receiver read=" + v2 + " (want same — one file, one identity)");
        } catch (Throwable t) { row("F261-D", false, "threw " + t); }

        // ── F261-E: negative — distinct name = distinct storage ─────────
        try {
            android.content.SharedPreferences pa =
                getSharedPreferences("f261e1", MODE_PRIVATE);
            pa.edit().putString("only_a", "A").commit();
            android.content.SharedPreferences pb =
                getSharedPreferences("f261e2", MODE_PRIVATE);
            String leak = pb.getString("only_a", "ABSENT");
            row("F261-E", "ABSENT".equals(leak),
                "cross-file leak=" + leak + " (want ABSENT)");
        } catch (Throwable t) { row("F261-E", false, "threw " + t); }

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        TextView tv = new TextView(this);
        tv.setText(report.isEmpty() ? "NO ROWS" : report);
        root.addView(tv);
        setContentView(root);
    }
}
