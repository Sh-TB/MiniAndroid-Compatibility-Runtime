package com.probe.f259;

import android.app.Activity;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.util.AbstractList;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

/**
 * CONT-10 W6 synthetic probe — F-NEW-259 (R8-rename-safe DEX list iterator
 * slot resolution) + the navigation-compose visibleEntries filter chain
 * semantics that gate the NavHost destination content.
 *
 * Upstream contracts under test (generic platform laws — no app specifics):
 *
 *   F259-A  AbstractList.iterator() over a DEX-defined List subclass
 *           (host-inherited iterator) yields the receiver's REAL elements
 *           (JDK AbstractList.Itr drives size()/get(I)).
 *   F259-B  Enum.compareTo == ordinal difference (R8 may permute constant
 *           declaration order; compareTo must follow the constructor
 *           ordinal the dex carries).
 *   F259-C  instanceof against a sibling subclass is FALSE
 *           (screen instanceof Graph must be false; graph instanceof Graph
 *           true) — the nav "destination !is NavGraph" filter.
 *   F259-D  FULL NavHost visibleEntries filter chain reproduction:
 *           backQueue = [graphEntry(CREATED, Graph), gameEntry(STARTED,
 *           Screen)]; filter = !result.contains(e) &&
 *           e.max.compareTo(STARTED) >= 0 && !(e.dest instanceof Graph)
 *           → exactly [gameEntry].
 *   F259-E  negative: an empty queue yields an empty result.
 */
public class MainActivity extends Activity {

    private static String report = "";

    private static void row(String id, boolean pass, String detail) {
        report += id + "|" + (pass ? "PASS" : "FAIL") + "|" + detail + "\n";
    }

    /** Lifecycle.State shape with the R8-permuted declaration order. */
    enum St { DESTROYED, INITIALIZED, CREATED, STARTED, RESUMED }

    static class Dest { }
    static class Graph extends Dest { }
    static class Screen extends Dest { }

    static class Entry {
        final Dest dest;
        final St max;
        Entry(Dest d, St m) { dest = d; max = m; }
    }

    /** Plain app List over the shadow AbstractList (host-inherited iterator). */
    static class HostList extends AbstractList<String> {
        private final ArrayList<String> backing = new ArrayList<String>();
        void addItem(String s) { backing.add(s); }
        @Override public int size() { return backing.size(); }
        @Override public String get(int i) { return backing.get(i); }
    }

    private static int filterVisible(List<Entry> queue) {
        List<Entry> result = new ArrayList<Entry>();
        for (Entry e : queue) {
            if (!result.contains(e)
                    && e.max.compareTo(St.STARTED) >= 0
                    && !(e.dest instanceof Graph)) {
                result.add(e);
            }
        }
        return result.size();
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // ── F259-A: host-inherited iterator over a DEX List subclass ────
        try {
            HostList hl = new HostList();
            hl.addItem("alpha"); hl.addItem("beta"); hl.addItem("gamma");
            int n = 0;
            StringBuilder seen = new StringBuilder();
            for (Iterator<String> it = hl.iterator(); it.hasNext(); ) {
                seen.append(it.next()).append(',');
                n++;
            }
            row("F259-A", n == 3,
                "hostList iterator n=" + n + " [" + seen + "] (want 3)");
        } catch (Throwable t) { row("F259-A", false, "threw " + t); }

        // ── F259-B: enum compareTo ordinal law ──────────────────────────
        try {
            int same = St.STARTED.compareTo(St.STARTED);
            int below = St.CREATED.compareTo(St.STARTED);
            int above = St.RESUMED.compareTo(St.STARTED);
            row("F259-B", same == 0 && below < 0 && above > 0,
                "STARTED vs STARTED=" + same + " CREATED=" + below
                    + " RESUMED=" + above);
        } catch (Throwable t) { row("F259-B", false, "threw " + t); }

        // ── F259-C: sibling-subclass instanceof law ─────────────────────
        try {
            Dest screen = new Screen();
            Dest graph = new Graph();
            boolean screenIsGraph = screen instanceof Graph;
            boolean graphIsGraph = graph instanceof Graph;
            row("F259-C", !screenIsGraph && graphIsGraph,
                "screen instanceof Graph=" + screenIsGraph
                    + " graph=" + graphIsGraph);
        } catch (Throwable t) { row("F259-C", false, "threw " + t); }

        // ── F259-D: the NavHost visibleEntries filter chain ─────────────
        try {
            List<Entry> queue = new ArrayList<Entry>();
            queue.add(new Entry(new Graph(), St.CREATED));
            queue.add(new Entry(new Screen(), St.STARTED));
            int n = filterVisible(queue);
            row("F259-D", n == 1,
                "visibleEntries n=" + n + " (want exactly 1: the game entry)");
        } catch (Throwable t) { row("F259-D", false, "threw " + t); }

        // ── F259-E: negative — empty queue yields empty result ──────────
        try {
            List<Entry> queue = new ArrayList<Entry>();
            int n = filterVisible(queue);
            row("F259-E", n == 0, "empty queue n=" + n + " (want 0)");
        } catch (Throwable t) { row("F259-E", false, "threw " + t); }

        // ── F259-F: ArrayList.addAll(Collection) APPEND law ─────────────
        // OpenJDK: addAll appends c's elements after the receiver's current
        // end and returns true when changed. The dooz populateVisibleEntries
        // face: entries.addAll(backQueue.filter{...}) must deliver the
        // filtered element.
        try {
            List<Entry> entries = new ArrayList<Entry>();
            List<Entry> filtered = new ArrayList<Entry>();
            filtered.add(new Entry(new Screen(), St.STARTED));
            boolean changed = entries.addAll(filtered);
            row("F259-F", changed && entries.size() == 1,
                "addAll changed=" + changed + " size=" + entries.size()
                    + " (want true/1)");
        } catch (Throwable t) { row("F259-F", false, "threw " + t); }

        // ── F259-G: addAll append-after-existing (two-round append) ─────
        try {
            List<String> acc = new ArrayList<String>();
            acc.add("x");
            List<String> more = new ArrayList<String>();
            more.add("y"); more.add("z");
            acc.addAll(more);
            boolean order = acc.size() == 3 && "x".equals(acc.get(0))
                && "y".equals(acc.get(1)) && "z".equals(acc.get(2));
            row("F259-G", order, "append size=" + acc.size()
                + " [0]=" + acc.get(0) + " [1]=" + acc.get(1)
                + " [2]=" + acc.get(2) + " (want x,y,z)");
        } catch (Throwable t) { row("F259-G", false, "threw " + t); }

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        TextView tv = new TextView(this);
        tv.setText(report.isEmpty() ? "NO ROWS" : report);
        root.addView(tv);
        setContentView(root);
    }
}
