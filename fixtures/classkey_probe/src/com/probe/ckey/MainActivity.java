package com.probe.ckey;

import android.app.Activity;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.ListIterator;
import java.util.Map;

/**
 * CONT-38v independent-verification probe — generic platform contracts for
 * the two friend-reported findings, verified against the ALREADY-REGISTERED
 * roots (no duplicate registry entries):
 *
 *   Friend "F-NEW-257" (Class objects as stable map keys) == the registered
 *   F-069/R-NEW-293 const-class STABLE IDENTITY law + F-103 heap-backed
 *   tokens + F-NEW-249 getClass stable token + F-NEW-282 boundary
 *   materialization + F-NEW-248 String-content map keys. ART law: one
 *   java.lang.Class instance per runtime class — identity is observable
 *   through == and through Map<Class,V> put/get keyed at DIFFERENT
 *   production sites. Ordinary object keys keep IDENTITY semantics
 *   (no equals override -> distinct instances never merge); String keys
 *   keep CONTENT semantics.
 *
 *   Friend "F-NEW-258" (non-null ArrayList.listIterator) == the registered
 *   F-NEW-255 listIterator law + LAW-B write-back law (CONT-18). OpenJDK
 *   AbstractList.ListItr: listIterator() never null; the full cursor
 *   contract (hasNext/hasPrevious/next/previous/nextIndex/previousIndex)
 *   plus the write faces set/remove/add with lastReturned semantics and
 *   the double-remove IllegalStateException.
 *
 * Every row is a generic platform contract — no app-specific conditions.
 */
public class MainActivity extends Activity {

    private static String report = "";

    private static void row(String id, boolean pass, String detail) {
        report += id + "|" + (pass ? "PASS" : "FAIL") + "|" + detail + "\n";
    }

    /** A plain app class WITHOUT equals() — identity-key law witness. */
    private static class Token {
        final String tag;
        Token(String tag) { this.tag = tag; }
        public String toString() { return "Token(" + tag + ")"; }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // ── CK-01: two const-class evaluations of the SAME descriptor are
        // reference-equal (F-069 stable identity). The friend's claimed
        // root cause ("different runtime reference IDs for the same
        // logical Class") must NOT reproduce.
        try {
            boolean eq = (String.class == String.class)
                && (java.util.List.class == java.util.List.class);
            row("CK-01", eq, "const-class identity same descriptor eq=" + eq);
        } catch (Throwable t) { row("CK-01", false, "threw " + t); }

        // ── CK-02: const-class token == getClass() token (F-103/F-NEW-249
        // cross-production identity — the separately-produced-reference
        // round trip the verification directive requires).
        try {
            String s = "prod-getclass";
            boolean eq = (s.getClass() == String.class)
                && (((Object) new Integer(7)).getClass() == Integer.class);
            row("CK-02", eq, "getClass token == const-class token eq=" + eq);
        } catch (Throwable t) { row("CK-02", false, "threw " + t); }

        // ── CK-03: THE FRIEND'S EXACT SCENARIO — put with a Class key at
        // one production site, get with a SEPARATELY produced reference to
        // the same logical Class. HashMap must return the stored value.
        try {
            Map<Class<?>, String> reg = new HashMap<Class<?>, String>();
            reg.put(String.class, "S-VAL");
            reg.put(Integer.class, "I-VAL");
            Class<?> lookup = "separate production".getClass(); // not String.class literal
            String got = reg.get(lookup);
            boolean ok = "S-VAL".equals(got) && "I-VAL".equals(reg.get(Integer.class));
            row("CK-03", ok, "HashMap<Class,V> cross-site get=" + got);
        } catch (Throwable t) { row("CK-03", false, "threw " + t); }

        // ── CK-04: LinkedHashMap variant (the dooz NavigatorProvider /
        // ViewModelStore shape — registration via reflection-produced
        // Class, lookup via KClass round-trip).
        try {
            Map<Class<?>, String> reg = new LinkedHashMap<Class<?>, String>();
            reg.put(java.util.ArrayList.class, "ARR");
            reg.put(java.util.HashMap.class, "HM");
            Class<?> probe = new ArrayList<String>().getClass();
            boolean ok = "ARR".equals(reg.get(probe))
                && reg.containsKey(java.util.HashMap.class)
                && reg.get(Long.class) == null;
            row("CK-04", ok, "LinkedHashMap<Class,V> cross-site ok=" + ok);
        } catch (Throwable t) { row("CK-04", false, "threw " + t); }

        // ── CK-05: DISTINCT descriptors never share a key (discrimination).
        try {
            Map<Class<?>, String> reg = new HashMap<Class<?>, String>();
            reg.put(String.class, "S");
            boolean distinct = reg.get(Integer.class) == null
                && reg.get(CharSequence.class) == null
                && "S".equals(reg.get(String.class));
            row("CK-05", distinct, "distinct Class keys stay distinct");
        } catch (Throwable t) { row("CK-05", false, "threw " + t); }

        // ── CK-06: ordinary object keys keep IDENTITY semantics — two
        // Tokens with equal tags are NOT the same key (no equals override),
        // and the SAME instance round-trips.
        try {
            Map<Token, String> m = new HashMap<Token, String>();
            Token t1 = new Token("a");
            m.put(t1, "V1");
            Token t2 = new Token("a");
            boolean ok = "V1".equals(m.get(t1)) && (m.get(t2) == null);
            row("CK-06", ok, "object keys identity-preserved t2get="
                + m.get(t2));
        } catch (Throwable t) { row("CK-06", false, "threw " + t); }

        // ── CK-07: String keys keep CONTENT semantics (F-NEW-248 guard —
        // the exact dooz getNavigator("composable") law the friend cites).
        try {
            Map<String, String> m = new HashMap<String, String>();
            m.put(new String("composable"), "NAV");
            boolean ok = "NAV".equals(m.get("composable"));
            row("CK-07", ok, "String keys content-equal ok=" + ok);
        } catch (Throwable t) { row("CK-07", false, "threw " + t); }

        // ── LI-01: populated ArrayList listIterator full cursor walk
        // (F-NEW-255 law; the friend's NPE face must not reproduce).
        try {
            List<String> l = new ArrayList<String>();
            l.add("a"); l.add("b"); l.add("c");
            ListIterator<String> it = l.listIterator();
            boolean ok = (it != null)
                && it.nextIndex() == 0 && it.previousIndex() == -1
                && it.hasNext() && "a".equals(it.next())
                && "b".equals(it.next()) && "c".equals(it.next())
                && !it.hasNext() && it.hasPrevious()
                && "c".equals(it.previous()) && "b".equals(it.previous())
                && it.nextIndex() == 1 && it.previousIndex() == 0
                && "a".equals(it.previous())
                && it.previousIndex() == -1 && !it.hasPrevious();
            row("LI-01", ok, "full cursor walk fwd+back ok=" + ok);
        } catch (Throwable t) { row("LI-01", false, "threw " + t); }

        // ── LI-02: empty list — non-null iterator, both probes false.
        try {
            List<String> l = new ArrayList<String>();
            ListIterator<String> it = l.listIterator();
            boolean ok = (it != null) && !it.hasNext() && !it.hasPrevious()
                && it.nextIndex() == 0 && it.previousIndex() == -1;
            row("LI-02", ok, "empty list: non-null, no crash, cursor at 0");
        } catch (Throwable t) { row("LI-02", false, "threw " + t); }

        // ── LI-03: listIterator(index) start law (mid-list start).
        try {
            List<String> l = new ArrayList<String>();
            l.add("a"); l.add("b"); l.add("c");
            ListIterator<String> it = l.listIterator(1);
            boolean ok = it.hasNext() && it.hasPrevious()
                && "b".equals(it.next()) && "c".equals(it.next())
                && it.hasPrevious();
            row("LI-03", ok, "listIterator(1) starts mid-list ok=" + ok);
        } catch (Throwable t) { row("LI-03", false, "threw " + t); }

        // ── LI-04: set() overwrites lastReturned in the BACKING list
        // (LAW-B; OpenJDK ListItr.set).
        try {
            List<String> l = new ArrayList<String>();
            l.add("x"); l.add("y");
            ListIterator<String> it = l.listIterator();
            it.next();                       // "x", lastRet=0
            it.set("X");
            boolean ok = "X".equals(l.get(0)) && "y".equals(l.get(1))
                && "X".equals(it.previous());
            row("LI-04", ok, "set overwrites backing l0=" + l.get(0));
        } catch (Throwable t) { row("LI-04", false, "threw " + t); }

        // ── LI-05: add() inserts at the cursor and advances past it
        // (LAW-B; OpenJDK ListItr.add — a following previous() serves the
        // added element, and the next() re-serves it too per JDK docs).
        try {
            List<String> l = new ArrayList<String>();
            l.add("a"); l.add("b");
            ListIterator<String> it = l.listIterator();
            it.next();                       // cursor 1
            it.add("NEW");
            boolean ok = l.size() == 3 && "NEW".equals(l.get(1))
                && it.hasPrevious() && "NEW".equals(it.previous())
                && "a".equals(l.get(0)) && "b".equals(l.get(2));
            row("LI-05", ok, "add at cursor size=" + l.size() + " l1=" + l.get(1));
        } catch (Throwable t) { row("LI-05", false, "threw " + t); }

        // ── LI-06: remove() removes lastReturned; double remove → ISE
        // (LAW-B; OpenJDK Itr.remove contract).
        try {
            List<String> l = new ArrayList<String>();
            l.add("a"); l.add("b"); l.add("c");
            ListIterator<String> it = l.listIterator();
            it.next();                       // "a"
            it.remove();
            boolean ok0 = l.size() == 2 && "b".equals(l.get(0));
            boolean threw = false;
            try { it.remove(); } catch (IllegalStateException e) { threw = true; }
            row("LI-06", ok0 && threw, "remove + double-remove-ISE ok=" + ok0
                + " ise=" + threw);
        } catch (Throwable t) { row("LI-06", false, "threw " + t); }

        // ── LI-07: set/remove before any next() → ISE (lastReturned=-1).
        try {
            List<String> l = new ArrayList<String>();
            l.add("a");
            ListIterator<String> it = l.listIterator();
            boolean sThrew = false, rThrew = false;
            try { it.set("Z"); } catch (IllegalStateException e) { sThrew = true; }
            try { it.remove(); } catch (IllegalStateException e) { rThrew = true; }
            row("LI-07", sThrew && rThrew, "pre-next set/remove ISE s=" + sThrew
                + " r=" + rThrew);
        } catch (Throwable t) { row("LI-07", false, "threw " + t); }

        // ── LI-08: repeated iteration — a fresh listIterator re-walks.
        try {
            List<String> l = new ArrayList<String>();
            l.add("p"); l.add("q");
            ListIterator<String> i1 = l.listIterator();
            String s1 = i1.next() + i1.next();
            ListIterator<String> i2 = l.listIterator();
            String s2 = i2.next() + i2.next();
            row("LI-08", "pq".equals(s1) && "pq".equals(s2),
                "repeated iteration s1=" + s1 + " s2=" + s2);
        } catch (Throwable t) { row("LI-08", false, "threw " + t); }

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        TextView tv = new TextView(this);
        int pass = 0, total = 0;
        for (String line : report.split("\n")) {
            if (line.isEmpty()) continue;
            total++;
            if (line.contains("|PASS|")) pass++;
        }
        tv.setText("CKPROBE " + pass + "/" + total + "\n" + report);
        root.addView(tv);
        setContentView(root);
    }
}
