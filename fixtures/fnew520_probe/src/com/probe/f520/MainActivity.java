package com.probe.f520;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import java.util.Iterator;
import java.util.PriorityQueue;

/**
 * CONT-29 W1 synthetic probe — F-NEW-520 (PriorityQueue claim + heap-family
 * laws). The class was claimed by NO shadow: iterator() answered null and
 * Iterator.hasNext NPE'd (decoded face: wocheneinkauf Ly7;.a — the
 * BreakIterator line-breaking worklist never ran).
 *
 * Upstream contracts under test (generic platform laws — no app specifics):
 *
 *   F520-A  add + iterator: the iteration walks the internal ARRAY in
 *           insertion order (OpenJDK PriorityQueue.iterator(): "The
 *           Iterator does not traverse the elements in any particular
 *           order" — array order IS the faithful law, not sorted order).
 *   F520-B  poll() x5 on Integer elements drains in ASCENDING order
 *           (the natural-ordering least-element law).
 *   F520-C  poll() on an EMPTY queue returns null (never throws).
 *   F520-D  String elements: poll() returns the lexicographically least.
 *   F520-E  peek() returns the least WITHOUT removing (size unchanged);
 *           poll() removes (size decrements).
 *   F520-F  offer() == add() return-true contract (unbounded queue);
 *           size/isEmpty/contains/clear contracts.
 */
public class MainActivity extends Activity {

    private static String report = "";

    private static void row(String id, boolean pass, String detail) {
        report += id + "|" + (pass ? "PASS" : "FAIL") + "|" + detail + "\n";
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        TextView tv = new TextView(this);
        run();
        tv.setText(report);
        setContentView(tv);
    }

    private static void run() {
        // ── F520-A: iterator order = insertion order (array law) ──
        PriorityQueue<Integer> q = new PriorityQueue<Integer>();
        q.add(30); q.add(10); q.add(20);
        StringBuilder it = new StringBuilder();
        Iterator<Integer> ix = q.iterator();
        while (ix.hasNext()) { it.append(ix.next()).append(","); }
        row("F520-A", it.toString().equals("30,10,20,"),
            "iterator=" + it);

        // ── F520-B: poll drains ascending (least-element law) ──
        boolean drainOk = true;
        StringBuilder drained = new StringBuilder();
        int want = 10;
        while (!q.isEmpty()) {
            Integer v = q.poll();
            drained.append(v).append(",");
            if (v == null || v.intValue() != want) drainOk = false;
            want += 10;
        }
        row("F520-B", drainOk, "drain=" + drained);

        // ── F520-C: poll on empty → null, no exception ──
        Integer n = null;
        boolean nullOk = true;
        try { n = q.poll(); } catch (Throwable t) { nullOk = false; }
        row("F520-C", nullOk && n == null, "pollEmpty=" + n);

        // ── F520-D: String poll = lexicographic min ──
        PriorityQueue<String> sq = new PriorityQueue<String>();
        sq.offer("pear"); sq.offer("apple"); sq.offer("fig");
        String first = sq.poll();
        String second = sq.poll();
        row("F520-D", "apple".equals(first) && "fig".equals(second),
            "polls=" + first + "/" + second);

        // ── F520-E: peek non-removing, poll removing ──
        PriorityQueue<Integer> eq = new PriorityQueue<Integer>();
        eq.add(7); eq.add(3);
        Integer p1 = eq.peek();
        int afterPeek = eq.size();
        Integer p2 = eq.poll();
        int afterPoll = eq.size();
        row("F520-E", p1 != null && p1.intValue() == 3 && afterPeek == 2
                      && p2 != null && p2.intValue() == 3 && afterPoll == 1,
            "peek=" + p1 + " sizeAfterPeek=" + afterPeek
            + " poll=" + p2 + " sizeAfterPoll=" + afterPoll);

        // ── F520-F: offer/contains/clear contracts ──
        PriorityQueue<Integer> fq = new PriorityQueue<Integer>();
        boolean offerTrue = fq.offer(42);
        boolean contains = fq.contains(42);
        boolean containsMissing = fq.contains(99);
        fq.clear();
        row("F520-F", offerTrue && contains && !containsMissing
                      && fq.isEmpty() && fq.size() == 0,
            "offer=" + offerTrue + " contains=" + contains
            + " missing=" + containsMissing
            + " emptyAfterClear=" + fq.isEmpty());
    }
}
