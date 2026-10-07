package com.probe.fcol;

import android.app.Activity;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.ListIterator;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * CONT-11 W7 — Kotlin/COLLECTION SEMANTIC-LAW AUDIT (directive §8).
 * One probe = the JDK semantic contract per operation family; the engine
 * must answer each row from GENERIC law, not per-class roots. Rows:
 *
 *   K1  ArrayList set/remove/indexOf/contains/isEmpty
 *   K2  ArrayList listIterator set/add/index laws
 *   K3  ArrayList.subList is a VIEW (backing change reflects)
 *   K4  LinkedList head/tail laws + iteration order
 *   K5  ArrayDeque FIFO order + poll/peek/size
 *   K6  HashMap put/get/remove/containsKey/getOrDefault
 *   K7  HashMap keySet/entrySet iteration
 *   K8  LinkedHashMap INSERTION-ORDER iteration
 *   K9  HashSet duplicate rejection + contains
 *   K10 LinkedHashSet insertion-order iteration
 *   K11 Iterator.remove law (last returned; double-remove throws ISE)
 *   K12 ListIterator previous/add/set index laws
 *   K13 Collection.removeIf (Iterable default method)
 *   K14 List.sort (List interface default → merged sort)
 *   K15 Stream.of.filter.collect (java.util.stream family)
 *   K16 removeAll/retainAll/clear bulk laws
 *   K17 Map.merge / computeIfAbsent (Map default methods)
 *   K18 Iterable.forEach on List and Map (default methods)
 */
public class MainActivity extends Activity {

    private static String report = "";

    private static void row(String id, boolean pass, String detail) {
        report += id + "|" + (pass ? "PASS" : "FAIL") + "|" + detail + "\n";
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // ── K1: ArrayList core readers ──────────────────────────────────
        try {
            List<String> l = new ArrayList<String>();
            l.add("a"); l.add("b"); l.add("c");
            l.set(1, "B");
            // CONT-18 T-03: self-decomposing detail — each conjunct is its
            // own fact so a compound ok=false is never opaque again.
            boolean g1 = "B".equals(l.get(1));
            int ix = l.indexOf("B");
            boolean cx = l.contains("c");
            boolean nemp = !l.isEmpty();
            int sz = l.size();
            l.remove(1);
            boolean g2 = "c".equals(l.get(1));
            int sz2 = l.size();
            boolean ok = g1 && ix == 1 && cx && nemp && sz == 3 && g2 && sz2 == 2;
            row("K1", ok, "g1=" + g1 + " ix=" + ix + " cx=" + cx
                + " nemp=" + nemp + " sz=" + sz + " g2=" + g2 + " sz2=" + sz2);
        } catch (Throwable t) { row("K1", false, "threw " + t); }

        // ── K2: listIterator set/add/previous ───────────────────────────
        try {
            List<String> l = new ArrayList<String>();
            l.add("x"); l.add("y");
            ListIterator<String> it = l.listIterator(1);
            String cur = it.previous();          // "x", index 0
            boolean prevOk = "x".equals(cur);
            int nix = it.nextIndex();
            it.set("X");
            String g0 = l.get(0);
            // OpenJDK ListItr law: previous() sets cursor = lastRet = 0, so
            // nextIndex() == cursor == 0 (a following next() re-serves "x").
            // The old ==1 expectation contradicted ListItr.previous() —
            // probe artifact fixed (CONT-18 T-03).
            row("K2", prevOk && nix == 0 && "X".equals(g0),
                "prev=" + cur + " nix=" + nix + " g0=" + g0);
        } catch (Throwable t) { row("K2", false, "threw " + t); }

        // ── K3: subList is a VIEW ───────────────────────────────────────
        try {
            List<String> l = new ArrayList<String>();
            l.add("a"); l.add("b"); l.add("c"); l.add("d");
            List<String> sub = l.subList(1, 3);   // [b, c]
            sub.set(0, "B");
            boolean ok = "B".equals(l.get(1));    // write THROUGH the view
            l.set(2, "C");
            ok &= "C".equals(sub.get(1));         // read-back reflects backing
            row("K3", ok, "subList view ok=" + ok);
        } catch (Throwable t) { row("K3", false, "threw " + t); }

        // ── K4: LinkedList head/tail laws ───────────────────────────────
        try {
            LinkedList<String> l = new LinkedList<String>();
            l.add("m");
            l.addFirst("f"); l.addLast("z");
            boolean ok = "f".equals(l.getFirst()) && "z".equals(l.getLast())
                && l.size() == 3;
            String r = l.removeFirst();
            ok &= "f".equals(r) && "m".equals(l.getFirst());
            StringBuilder order = new StringBuilder();
            for (Iterator<String> it = l.iterator(); it.hasNext(); )
                order.append(it.next());
            ok &= "mz".contentEquals(order);
            row("K4", ok, "deque ops ok=" + ok + " order=" + order);
        } catch (Throwable t) { row("K4", false, "threw " + t); }

        // ── K5: ArrayDeque FIFO ─────────────────────────────────────────
        try {
            ArrayDeque<String> d = new ArrayDeque<String>();
            d.add("1"); d.add("2"); d.add("3");
            boolean ok = "1".equals(d.peek()) && d.size() == 3;
            String p = d.poll();
            ok &= "1".equals(p) && "2".equals(d.peek()) && d.size() == 2;
            row("K5", ok, "arraydeque peek=" + d.peek() + " ok=" + ok);
        } catch (Throwable t) { row("K5", false, "threw " + t); }

        // ── K6: HashMap core ────────────────────────────────────────────
        try {
            Map<String, Integer> m = new HashMap<String, Integer>();
            m.put("a", 1); m.put("b", 2);
            boolean g = Integer.valueOf(1).equals(m.get("a"));
            boolean ck = m.containsKey("b");
            int sz = m.size();
            m.remove("a");
            String got = String.valueOf(m.get("a"));
            int sz2 = m.size();
            boolean remOk = m.get("a") == null && m.size() == 1;
            Integer def = m.getOrDefault("zz", 42);
            boolean defOk = def != null && def.intValue() == 42;
            boolean ok = g && ck && sz == 2 && remOk && defOk;
            row("K6", ok, "g=" + g + " ck=" + ck + " sz=" + sz
                + " remOk=" + remOk + " defOk=" + defOk
                + (def != null ? " def=" + def : " def=null")
                + " got=" + got + " sz2=" + sz2);
        } catch (Throwable t) { row("K6", false, "threw " + t); }

        // ── K7: HashMap keySet/entrySet iteration ───────────────────────
        try {
            Map<String, Integer> m = new HashMap<String, Integer>();
            m.put("k1", 10); m.put("k2", 20);
            int sum = 0; int seen = 0;
            for (Map.Entry<String, Integer> e : m.entrySet()) {
                sum += e.getValue().intValue();
                seen++;
            }
            int kcount = 0;
            for (Iterator<String> it = m.keySet().iterator(); it.hasNext(); ) {
                it.next(); kcount++;
            }
            row("K7", seen == 2 && sum == 30 && kcount == 2,
                "entries=" + seen + " sum=" + sum + " keys=" + kcount);
        } catch (Throwable t) { row("K7", false, "threw " + t); }

        // ── K8: LinkedHashMap insertion order ───────────────────────────
        try {
            Map<String, Integer> m = new LinkedHashMap<String, Integer>();
            m.put("first", 1); m.put("second", 2); m.put("third", 3);
            StringBuilder keys = new StringBuilder();
            for (Iterator<String> it = m.keySet().iterator(); it.hasNext(); )
                keys.append(it.next()).append(',');
            row("K8", "first,second,third,".contentEquals(keys),
                "order=" + keys);
        } catch (Throwable t) { row("K8", false, "threw " + t); }

        // ── K9: HashSet duplicate rejection ─────────────────────────────
        try {
            Set<String> s = new HashSet<String>();
            boolean added1 = s.add("u");
            boolean added2 = s.add("u");
            row("K9", added1 && !added2 && s.size() == 1 && s.contains("u"),
                "add1=" + added1 + " add2=" + added2 + " size=" + s.size());
        } catch (Throwable t) { row("K9", false, "threw " + t); }

        // ── K10: LinkedHashSet insertion order ──────────────────────────
        try {
            Set<String> s = new LinkedHashSet<String>();
            s.add("o1"); s.add("o2"); s.add("o3");
            StringBuilder order = new StringBuilder();
            for (Iterator<String> it = s.iterator(); it.hasNext(); )
                order.append(it.next()).append(',');
            row("K10", "o1,o2,o3,".contentEquals(order), "order=" + order);
        } catch (Throwable t) { row("K10", false, "threw " + t); }

        // ── K11: Iterator.remove law ────────────────────────────────────
        try {
            List<String> l = new ArrayList<String>();
            l.add("r1"); l.add("r2"); l.add("r3");
            Iterator<String> it = l.iterator();
            it.next(); it.remove();               // removes r1
            boolean threw = false;
            try { it.remove(); } catch (IllegalStateException ise) {
                threw = true;
            }
            boolean ok = l.size() == 2 && "r2".equals(l.get(0)) && threw;
            row("K11", ok, "remove law ok=" + ok + " threw2nd=" + threw);
        } catch (Throwable t) { row("K11", false, "threw " + t); }

        // ── K12: ListIterator add/set index law ─────────────────────────
        try {
            List<String> l = new ArrayList<String>();
            l.add("a"); l.add("c");
            ListIterator<String> it = l.listIterator();
            it.next();               // cursor 1
            it.add("b");             // insert at 1, cursor 2
            // OpenJDK ListItr law: add() does cursor++ -> after the insert
            // cursor=2, so previousIndex()=cursor-1=1 (the CONT-18 T-03
            // audit found the old ==2 expectation contradicted the very
            // contract the row claims to test — probe artifact, fixed).
            boolean ok = l.size() == 3 && "b".equals(l.get(1))
                && it.previousIndex() == 1 && it.nextIndex() == 2;
            row("K12", ok, "add law ok=" + ok + " size=" + l.size()
                + " g1=" + l.get(1) + " pidx=" + it.previousIndex());
        } catch (Throwable t) { row("K12", false, "threw " + t); }

        // ── K13: removeIf (Iterable/Collection default) ─────────────────
        try {
            List<Integer> l = new ArrayList<Integer>();
            l.add(1); l.add(2); l.add(3); l.add(4);
            boolean changed = l.removeIf(v -> v % 2 == 0);
            row("K13", changed && l.size() == 2
                && Integer.valueOf(1).equals(l.get(0))
                && Integer.valueOf(3).equals(l.get(1)),
                "removeIf ok=" + changed + " size=" + l.size());
        } catch (Throwable t) { row("K13", false, "threw " + t); }

        // ── K14: List.sort (List default method) ────────────────────────
        try {
            List<Integer> l = new ArrayList<Integer>();
            l.add(3); l.add(1); l.add(2);
            l.sort(Integer::compareTo);
            row("K14", l.size() == 3 && Integer.valueOf(1).equals(l.get(0))
                && Integer.valueOf(2).equals(l.get(1))
                && Integer.valueOf(3).equals(l.get(2)),
                "sorted [1,2,3] got " + l);
        } catch (Throwable t) { row("K14", false, "threw " + t); }

        // ── K15: Stream.of.filter.collect ───────────────────────────────
        try {
            List<String> out = Stream.of("s1", "s2", "x3")
                .filter(s -> s.startsWith("s"))
                .collect(Collectors.toList());
            row("K15", out != null && out.size() == 2
                && "s1".equals(out.get(0)) && "s2".equals(out.get(1)),
                "stream size=" + (out == null ? -1 : out.size()));
        } catch (Throwable t) { row("K15", false, "threw " + t); }

        // ── K16: removeAll/retainAll/clear ──────────────────────────────
        try {
            List<String> l = new ArrayList<String>();
            l.add("a"); l.add("b"); l.add("c");
            List<String> drop = new ArrayList<String>();
            drop.add("b");
            boolean ch = l.removeAll(drop);
            boolean ok = ch && l.size() == 2;
            List<String> keep = new ArrayList<String>();
            keep.add("c");
            ch = l.retainAll(keep);
            ok &= ch && l.size() == 1 && "c".equals(l.get(0));
            l.clear();
            ok &= l.isEmpty();
            row("K16", ok, "bulk ok=" + ok);
        } catch (Throwable t) { row("K16", false, "threw " + t); }

        // ── K17: Map.merge/computeIfAbsent ──────────────────────────────
        try {
            Map<String, Integer> m = new HashMap<String, Integer>();
            m.merge("n", 1, Integer::sum);
            m.merge("n", 2, Integer::sum);
            Integer nn = m.get("n");
            List<String> created = new ArrayList<String>();
            m.computeIfAbsent("c", k -> { created.add(k); return 9; });
            Integer cc = m.get("c");
            row("K17", nn != null && nn.intValue() == 3 && cc != null
                && cc.intValue() == 9 && created.size() == 1,
                "merge n=" + (nn == null ? -1 : nn.intValue())
                    + " compute c=" + (cc == null ? -1 : cc.intValue()));
        } catch (Throwable t) { row("K17", false, "threw " + t); }

        // ── K18: Iterable.forEach ───────────────────────────────────────
        try {
            List<String> l = new ArrayList<String>();
            l.add("f1"); l.add("f2");
            StringBuilder seen = new StringBuilder();
            l.forEach(s -> seen.append(s).append(';'));
            Map<String, Integer> m = new HashMap<String, Integer>();
            m.put("mf", 1);
            StringBuilder mkeys = new StringBuilder();
            m.forEach((k, v) -> mkeys.append(k));
            row("K18", "f1;f2;".contentEquals(seen)
                && "mf".contentEquals(mkeys),
                "forEach list=" + seen + " map=" + mkeys);
        } catch (Throwable t) { row("K18", false, "threw " + t); }

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        TextView tv = new TextView(this);
        tv.setText(report.isEmpty() ? "NO ROWS" : report);
        root.addView(tv);
        setContentView(root);
    }
}
