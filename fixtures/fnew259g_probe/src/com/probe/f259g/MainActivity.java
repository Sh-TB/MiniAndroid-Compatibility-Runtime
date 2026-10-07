package com.probe.f259g;

import android.app.Activity;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.util.AbstractList;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

/**
 * CONT-11 W7 synthetic probe — F-NEW-259 / F-NEW-259b GENERICITY audit
 * (directive sections 9 and 10). Upstream contracts under test, all
 * generic platform laws — no app specifics:
 *
 *   F-NEW-259 descriptor-slot fallback dimensions:
 *   F259-H  multi-level DEX chain walk: size()/get(I) declared at the
 *           GRANDPARENT level; leaf + middle concrete → 2-hop walk.
 *   F259-I  covariant boxed override: get(I) returns Integer where the
 *           host slot declares Object (javac emits the bridge
 *           (I)Ljava/lang/Object; → covariant body). Values must survive.
 *   F259-J  array-element return: List<String[]> slot get(I) returns the
 *           SAME array object through the iterator round-trip (identity).
 *   F259-K  declaring-class state: the slot body reads a grandparent
 *           protected field (salt) with the LEAF as receiver — the slot
 *           executes on the real receiver, not a synthetic instance.
 *   F259-L  negative: a DEX list with NO size()/get(I) anywhere in its
 *           chain must NOT be driven by the slot law (falls to the
 *           shadow dispatch) — iteration yields 0, no crash.
 *
 *   F-NEW-259b addAll semantics matrix:
 *   F259-M  empty-source addAll → returns false, size unchanged.
 *   F259-N  duplicate values preserved (size counts dupes).
 *   F259-O  boxed Integer elements keep their VALUES (kind fidelity).
 *   F259-P  array elements keep IDENTITY through the copy.
 *   F259-Q  guest→shadow: receiver ArrayList, source DEX-defined
 *           subclass instance — elements delivered.
 *   F259-R  shadow→guest: receiver DEX-defined subclass, source
 *           ArrayList — elements delivered.
 *   F259-S  guest→guest: both DEX-defined subclasses — delivered.
 *   F259-T  object identity: after addAll, get(0) == the ORIGINAL object
 *           (same reference, not a copy).
 */
public class MainActivity extends Activity {

    private static String report = "";

    private static void row(String id, boolean pass, String detail) {
        report += id + "|" + (pass ? "PASS" : "FAIL") + "|" + detail + "\n";
    }

    // ── F259-H/K: three-level chain, grandparent declares the slots ────
    static class Base3 extends AbstractList<String> {
        protected final ArrayList<String> backing = new ArrayList<String>();
        protected final int salt;
        Base3(int s) { salt = s; }
        @Override public int size() { return backing.size() + salt; }
        @Override public String get(int i) { return backing.get(i); }
        void put(String s) { backing.add(s); }
    }
    static class Mid3 extends Base3 {
        Mid3(int s) { super(s); }
    }
    static class Leaf3 extends Mid3 {
        Leaf3(int s) { super(s); }
    }

    // ── F259-I: covariant boxed override (bridge (I)Ljava/lang/Object;) ─
    static class BoxList extends AbstractList<Integer> {
        private final ArrayList<Integer> backing = new ArrayList<Integer>();
        void put(Integer v) { backing.add(v); }
        @Override public Integer get(int i) { return backing.get(i); }
        @Override public int size() { return backing.size(); }
    }

    // ── F259-J: array elements ──────────────────────────────────────────
    static class ArrList extends AbstractList<String[]> {
        private final ArrayList<String[]> backing = new ArrayList<String[]>();
        void put(String[] a) { backing.add(a); }
        @Override public String[] get(int i) { return backing.get(i); }
        @Override public int size() { return backing.size(); }
    }

    // ── F259-L: DEX list with NO size/get in its chain ─────────────────
    static class NoSlots extends AbstractList<String> {
        @Override public Iterator<String> iterator() {
            return new java.util.Vector<String>().iterator();
        }
        // deliberately NO size()/get(I) → AbstractList's abstract stubs
        // stay abstract at the DEX level? javac cannot instantiate an
        // abstract class — so instead override them to THROW:
        @Override public int size() { throw new IllegalStateException("no-slots"); }
        @Override public String get(int i) { throw new IllegalStateException("no-slots"); }
    }

    // ── F259-Q/R/S: guest (DEX-defined) collection subclasses ──────────
    static class GuestA extends ArrayList<String> { }
    static class GuestB extends ArrayList<String> { }

    // ── F259-T: identity element type ───────────────────────────────────
    static class Token {
        final String v;
        Token(String v) { this.v = v; }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // ── F259-H: grandparent-declared slots, 2-hop chain walk ────────
        try {
            Leaf3 l = new Leaf3(0);
            l.put("h1"); l.put("h2"); l.put("h3");
            int n = 0;
            StringBuilder seen = new StringBuilder();
            for (Iterator<String> it = l.iterator(); it.hasNext(); ) {
                seen.append(it.next()).append(',');
                n++;
            }
            row("F259-H", n == 3, "grandparent slots n=" + n + " [" + seen
                + "] (want 3)");
        } catch (Throwable t) { row("F259-H", false, "threw " + t); }

        // ── F259-I: covariant boxed get — values survive the bridge ─────
        try {
            BoxList b = new BoxList();
            b.put(Integer.valueOf(10)); b.put(Integer.valueOf(20));
            b.put(Integer.valueOf(30));
            int sum = 0; int n = 0;
            for (Iterator<Integer> it = b.iterator(); it.hasNext(); ) {
                sum += it.next().intValue();
                n++;
            }
            row("F259-I", n == 3 && sum == 60, "boxed n=" + n + " sum="
                + sum + " (want 3/60)");
        } catch (Throwable t) { row("F259-I", false, "threw " + t); }

        // ── F259-J: array elements keep identity ────────────────────────
        try {
            ArrList a = new ArrList();
            String[] a0 = new String[] { "x", "y" };
            String[] a1 = new String[] { "z" };
            a.put(a0); a.put(a1);
            boolean identity = true; int n = 0;
            String secondLen = "";
            for (Iterator<String[]> it = a.iterator(); it.hasNext(); ) {
                String[] got = it.next();
                if (got != (n == 0 ? a0 : a1)) identity = false;
                if (n == 1) secondLen = String.valueOf(got.length);
                n++;
            }
            row("F259-J", identity && n == 2, "arrays identity="
                + identity + " n=" + n + " a1.len=" + secondLen
                + " (want true/2/1)");
        } catch (Throwable t) { row("F259-J", false, "threw " + t); }

        // ── F259-K: grandparent salt field with leaf receiver ───────────
        try {
            Leaf3 l = new Leaf3(2);  // salt=2 → size() = backing + 2
            l.put("k1"); l.put("k2");
            // size() must observe the INHERITED field: 2 + 2 = 4.
            // The iterator protocol reads size() → hasNext must reflect it
            // (the slot executed on the real receiver). get() only covers
            // the 2 real elements, so a faithful protocol yields k1 then
            // k2 — an extra next() would throw (caught below as failure).
            String first = null, second = null;
            int n = 0;
            try {
                for (Iterator<String> it = l.iterator(); it.hasNext(); ) {
                    String s = it.next();
                    if (n == 0) first = s; else if (n == 1) second = s;
                    n++;
                    if (n > 4) break;  // bound a runaway loop
                }
            } catch (Throwable inner) { /* bounded: record state */ }
            row("F259-K", n == 2 && "k1".equals(first) && "k2".equals(second),
                "salt field law: first=" + first + " second=" + second
                    + " n=" + n + " (want k1,k2,2)");
        } catch (Throwable t) { row("F259-K", false, "threw " + t); }

        // ── F259-L: negative — throwing slots must propagate, not fake ──
        try {
            NoSlots ns = new NoSlots();
            boolean threw = false;
            try {
                for (Iterator<String> it = ns.iterator(); it.hasNext(); ) {
                    it.next();
                }
            } catch (IllegalStateException ise) {
                threw = true;
            }
            row("F259-L", threw, "throwing slot propagated=" + threw
                + " (want true — no silent empty iteration)");
        } catch (Throwable t) { row("F259-L", false, "threw " + t); }

        // ── F259-M: empty-source addAll → false, unchanged ──────────────
        try {
            List<String> dst = new ArrayList<String>();
            dst.add("keep");
            boolean changed = dst.addAll(new ArrayList<String>());
            row("F259-M", !changed && dst.size() == 1
                && "keep".equals(dst.get(0)),
                "empty addAll changed=" + changed + " size=" + dst.size()
                    + " (want false/1/keep)");
        } catch (Throwable t) { row("F259-M", false, "threw " + t); }

        // ── F259-N: duplicate values preserved ──────────────────────────
        try {
            List<String> dst = new ArrayList<String>();
            List<String> src = new ArrayList<String>();
            src.add("d"); src.add("d"); src.add("e");
            dst.addAll(src);
            row("F259-N", dst.size() == 3 && "d".equals(dst.get(0))
                && "d".equals(dst.get(1)) && "e".equals(dst.get(2)),
                "dupes size=" + dst.size() + " [d,d,e] (want 3)");
        } catch (Throwable t) { row("F259-N", false, "threw " + t); }

        // ── F259-O: boxed Integer values survive the copy ───────────────
        try {
            List<Integer> dst = new ArrayList<Integer>();
            List<Integer> src = new ArrayList<Integer>();
            src.add(Integer.valueOf(7)); src.add(Integer.valueOf(9));
            dst.addAll(src);
            int sum = dst.get(0).intValue() + dst.get(1).intValue();
            row("F259-O", dst.size() == 2 && sum == 16,
                "ints size=" + dst.size() + " sum=" + sum + " (want 2/16)");
        } catch (Throwable t) { row("F259-O", false, "threw " + t); }

        // ── F259-P: array elements keep identity through addAll ─────────
        try {
            List<String[]> dst = new ArrayList<String[]>();
            List<String[]> src = new ArrayList<String[]>();
            String[] arr = new String[] { "a", "b" };
            src.add(arr);
            dst.addAll(src);
            row("F259-P", dst.get(0) == arr && dst.get(0).length == 2,
                "array identity=" + (dst.get(0) == arr) + " (want true)");
        } catch (Throwable t) { row("F259-P", false, "threw " + t); }

        // ── F259-Q: guest → shadow (ArrayList receiver) ─────────────────
        try {
            ArrayList<String> dst = new ArrayList<String>();
            GuestA src = new GuestA();
            src.add("q1"); src.add("q2");
            dst.addAll(src);
            row("F259-Q", dst.size() == 2 && "q1".equals(dst.get(0))
                && "q2".equals(dst.get(1)),
                "guest→shadow size=" + dst.size() + " (want 2/q1,q2)");
        } catch (Throwable t) { row("F259-Q", false, "threw " + t); }

        // ── F259-R: shadow → guest (DEX subclass receiver) ──────────────
        try {
            GuestB dst = new GuestB();
            List<String> src = new ArrayList<String>();
            src.add("r1"); src.add("r2");
            dst.addAll(src);
            row("F259-R", dst.size() == 2 && "r1".equals(dst.get(0))
                && "r2".equals(dst.get(1)),
                "shadow→guest size=" + dst.size() + " (want 2/r1,r2)");
        } catch (Throwable t) { row("F259-R", false, "threw " + t); }

        // ── F259-S: guest → guest ───────────────────────────────────────
        try {
            GuestA dst = new GuestA();
            GuestB src = new GuestB();
            src.add("s1"); src.add("s2"); src.add("s3");
            dst.addAll(src);
            row("F259-S", dst.size() == 3 && "s3".equals(dst.get(2)),
                "guest→guest size=" + dst.size() + " (want 3/s3)");
        } catch (Throwable t) { row("F259-S", false, "threw " + t); }

        // ── F259-T: object identity after addAll (no hidden copy) ───────
        try {
            List<Token> dst = new ArrayList<Token>();
            List<Token> src = new ArrayList<Token>();
            Token t1 = new Token("orig");
            src.add(t1);
            dst.addAll(src);
            Token back = dst.get(0);
            row("F259-T", back == t1 && "orig".equals(back.v),
                "identity=" + (back == t1) + " (want true)");
        } catch (Throwable t) { row("F259-T", false, "threw " + t); }

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        TextView tv = new TextView(this);
        tv.setText(report.isEmpty() ? "NO ROWS" : report);
        root.addView(tv);
        setContentView(root);
    }
}
