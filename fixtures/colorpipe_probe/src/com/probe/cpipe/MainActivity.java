package com.probe.cpipe;

import android.app.Activity;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * CONT-38 Phase-2 discriminating probe — the Compose text-color pipeline's
 * ENGINE-VISIBLE semantics, replicated as real plain-Java DEX (no Compose
 * classes needed). Every row is a generic platform contract.
 *
 * TR rows: the identity-keyed HAMT (bit-masked trie) that carries the
 * composition-local provider scope map — the exact algorithm shapes decoded
 * from the target APK's Lch1;/Llu0;/Lju0; family: 5-bit segments per level
 * via SIGNED shift, key-mask a / sub-mask b, bitCount-indexed entry arrays,
 * and the collision merge. If the engine executes any primitive wrongly,
 * the put/get round-trip fails HERE first.
 *
 * SC rows: the provider-scope flow — a scope map gains an entry (put), a
 * reader inside the scope resolves through it, a reader outside falls back
 * to the default (the LocalContentColor black face is the DEFAULT, by
 * design, when no provider ran); identity-key discipline; packed-color
 * (argb << 32) and takeOrElse sentinel (16) laws.
 *
 * PC rows: paint-color state laws on the REAL render path (TextView colors
 * read back + the visible pixel verified runner-side like fnew298):
 * explicit non-black, explicit black (a VALID requested color), alpha
 * preservation, and a color CHANGE between two draws.
 */
public class MainActivity extends Activity {

    private static String report = "";

    private static void row(String id, boolean pass, String detail) {
        report += id + "|" + (pass ? "PASS" : "FAIL") + "|" + detail + "\n";
    }

    // ── A minimal identity-keyed HAMT — the decoded Lch1;/Llu0; shapes ──
    static final class Node {
        int keyMask;      // Lch1;.a — bits of DIRECT (key,value) pairs
        int subMask;      // Lch1;.b — bits of sub-node slots
        Object[] d;       // interleaved key/value pairs; sub-nodes appended
        Node(int keyMask, int subMask, Object[] d) {
            this.keyMask = keyMask; this.subMask = subMask; this.d = d;
        }
    }

    static final class hamt {
        static String frameTrace = "";
        Node root = new Node(0, 0, new Object[0]);
        int size = 0;

        private static int seg(int hash, int depth) {
            return (hash >> depth) & 31;              // the SIGNED shift the APK uses
        }
        private static int entryIndex(Node n, int bit) {
            return Integer.bitCount(n.keyMask & (bit - 1)) * 2;
        }
        private static int subIndex(Node n, int bit) {
            return n.d.length - 1 - Integer.bitCount(n.subMask & (bit - 1));
        }
        private static boolean hasKey(Node n, int bit) { return (n.keyMask & bit) != 0; }
        private static boolean hasSub(Node n, int bit) { return (n.subMask & bit) != 0; }

        Object get(Object key) {
            if (key == null) return null;
            return get(root, key.hashCode(), 0, key);
        }
        Object getAt(Node start, int hash, int depth, Object key) {
            return get(start, hash, depth, key);
        }
        private Object get(Node n, int hash, int depth, Object key) {
            frameTrace += "[" + depth + "|" + (n == null ? -1 : n.keyMask) + "]";
            if (n == null) return null;
            int bit = 1 << seg(hash, depth);
            if (hasKey(n, bit)) {
                int idx = entryIndex(n, bit);
                if (key == n.d[idx] || key.equals(n.d[idx]))
                    return n.d[idx + 1];
                return null;
            }
            if (hasSub(n, bit)) {
                Node sub = (Node) n.d[subIndex(n, bit)];
                if (depth >= 30) {
                    for (int i = 0; i + 1 < sub.d.length; i += 2)
                        if (key == sub.d[i] || key.equals(sub.d[i]))
                            return sub.d[i + 1];
                    return null;
                }
                return get(sub, hash, depth + 5, key);
            }
            return null;
        }

        void put(Object key, Object val) {
            if (key == null) return;
            root = insert(root, key.hashCode(), 0, key, val);
            size++;
        }
        private Node insert(Node n, int hash, int depth, Object key, Object val) {
            int bit = 1 << seg(hash, depth);
            if (hasSub(n, bit)) {
                // descend into the EXISTING sub-node (the APK l/m shape)
                int sidx = n.d.length - 1 - Integer.bitCount(n.subMask & (bit - 1));
                Node sub = (Node) n.d[sidx];
                Node newSub = insert(sub, hash, depth + 5, key, val);
                Object[] d = n.d.clone();
                d[sidx] = newSub;
                return new Node(n.keyMask, n.subMask, d);
            }
            if (hasKey(n, bit)) {
                int idx = entryIndex(n, bit);
                Object oldKey = n.d[idx];
                if (oldKey == key || oldKey.equals(key)) {
                    Object[] d = n.d.clone(); d[idx + 1] = val;
                    return new Node(n.keyMask, n.subMask, d);
                }
                return merge(n, hash, depth, key, val, oldKey, n.d[idx + 1], bit);
            }
            Object[] d = new Object[n.d.length + 2];
            int idx = entryIndex(n, bit);
            System.arraycopy(n.d, 0, d, 0, idx);
            d[idx] = key; d[idx + 1] = val;
            System.arraycopy(n.d, idx, d, idx + 2, n.d.length - idx);
            return new Node(n.keyMask | bit, n.subMask, d);
        }
        private Node merge(Node n, int hash, int depth, Object k1, Object v1,
                           Object k2, Object v2, int bit) {
            if (depth >= 30) {
                Object[] d = new Object[] { k2, v2, k1, v1 };
                return new Node(0, bit, d);
            }
            int h2 = k2.hashCode();
            int s1 = seg(hash, depth + 5), s2 = seg(h2, depth + 5);
            Node deep;
            if (s1 == s2) {
                Node empty = new Node(0, 0, new Object[0]);
                deep = insert(empty, hash, depth + 5, k1, v1);
                deep = insert(deep, h2, depth + 5, k2, v2);
            } else {
                deep = new Node(0, 0, new Object[0]);
                deep = insert(deep, hash, depth + 5, k1, v1);
                deep = insert(deep, h2, depth + 5, k2, v2);
            }
            // the APK layout: pairs front (bit order), sub-nodes at the
            // TAIL of the grown array (reverse-bit order via len-1-count)
            Object[] d = new Object[n.d.length + 1];
            System.arraycopy(n.d, 0, d, 0, n.d.length);
            int newSubMask = n.subMask | bit;
            int si = d.length - 1 - Integer.bitCount(newSubMask & (bit - 1));
            d[si] = deep;
            // the relocated key's bit LEAVES the key mask (it moved down)
            return new Node(n.keyMask & ~bit, newSubMask, d);
        }
    }

    /** A plain holder WITHOUT hashCode/equals overrides — identity key. */
    static final class Local {
        final String name;
        Local(String name) { this.name = name; }
        public String toString() { return "Local(" + name + ")"; }
    }

    static final Local CONTENT_COLOR = new Local("contentColor");
    static final Local DENSITY       = new Local("density");
    static final Local TEXT_STYLE    = new Local("textStyle");
    static final Local COLOR_SCHEME  = new Local("colorScheme");

    /** The provider-scope resolve: scope map get, else the default. */
    static Object resolve(hamt scope, Local l, Object def) {
        Object v = scope.get(l);
        return v != null ? v : def;
    }

    private static int currentText = 0xFF000000;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // ── TR-01: two keys, distinct segments — basic round trip ──
        try {
            hamt m = new hamt();
            m.put(CONTENT_COLOR, "cc");
            m.put(DENSITY, "dn");
            boolean ok = "cc".equals(m.get(CONTENT_COLOR))
                && "dn".equals(m.get(DENSITY))
                && m.get(TEXT_STYLE) == null;
            row("TR-01", ok, "2-key distinct-segment put/get ok=" + ok);
        } catch (Throwable t) { row("TR-01", false, "threw " + t); }

        // ── TR-02: hash-collision pair (shared first segment → merge) ──
        try {
            Local a = null, b = null;
            for (int i = 1; i < 400 && a == null; i++) {
                Local x = new Local("k" + i);
                for (int j = i + 1; j < 900; j++) {
                    Local y = new Local("k" + j);
                    if (((x.hashCode() >> 0) & 31) == ((y.hashCode() >> 0) & 31)) {
                        a = x; b = y; break;
                    }
                }
            }
            hamt m = new hamt();
            m.put(a, "A");
            m.put(b, "B");
            Object ga = m.get(a), gb = m.get(b);
            boolean ok = "A".equals(ga) && "B".equals(gb)
                && m.get(CONTENT_COLOR) == null;
            row("TR-02", ok && a != null, "collision merge put/get ok=" + ok
                + " (ha=" + (a == null ? "?" : a.hashCode())
                + " hb=" + (b == null ? "?" : b.hashCode())
                + " ga=" + ga + " gb=" + gb + ")");
        } catch (Throwable t) { row("TR-02", false, "threw " + t); }

        // ── TR-03: three keys in the SAME first segment — chain ──
        try {
            Local[] ks = new Local[3];
            int found = 0;
            for (int i = 1; i < 3000 && found < 3; i++) {
                Local x = new Local("d" + i);
                if (((x.hashCode() >> 0) & 31) == 7) ks[found++] = x;
            }
            hamt m = new hamt();
            for (int i = 0; i < found; i++) m.put(ks[i], "V" + i);
            boolean ok = found == 3;
            StringBuilder got = new StringBuilder();
            for (int i = 0; i < found && ok; i++) {
                Object g = m.get(ks[i]);
                got.append(" g").append(i).append('=').append(g);
                ok = ("V" + i).equals(g);
            }
            row("TR-03", ok, "3-key same-segment chain ok=" + ok + got);
        } catch (Throwable t) { row("TR-03", false, "threw " + t); }

        // ── TR-06: structural introspection of the TR-02 merge shape ──
        try {
            Local a = new Local("kx1");
            Local b = new Local("ky1");
            // force the same first segment
            for (int i = 1; i < 2000 && ((a.hashCode() >> 0) & 31) != 3; i++) a = new Local("kx" + i);
            for (int i = 1; i < 4000 && (b == null || ((b.hashCode() >> 0) & 31) != 3
                    || b.hashCode() == a.hashCode()); i++) b = new Local("ky" + i);
            hamt m = new hamt();
            m.put(a, "A");
            Node r1 = m.root;
            boolean step1 = r1.keyMask == (1 << ((a.hashCode() >> 0) & 31))
                && r1.subMask == 0 && r1.d.length == 2
                && r1.d[0] == a && "A".equals(r1.d[1]);
            m.put(b, "B");
            Node r2 = m.root;
            int bit = 1 << ((a.hashCode() >> 0) & 31);
            boolean subThere = (r2.subMask & bit) != 0;
            Node sub = null;
            if (subThere) {
                int sidx = r2.d.length - 1 - Integer.bitCount(r2.subMask & (bit - 1));
                Object o = r2.d[sidx];
                sub = (Node) o;
            }
            String subShape = sub == null ? "no-sub" :
                ("km=" + sub.keyMask + " sm=" + sub.subMask + " len=" + sub.d.length
                 + " d0isB=" + (sub.d[0] == b) + " d1=" + sub.d[1]
                 + " d2=" + (sub.d.length > 2 ? sub.d[2] : "-")
                 + " d3=" + (sub.d.length > 3 ? sub.d[3] : "-"));
            Object direct = null;
            if (sub != null) {
                int bbit = 1 << ((b.hashCode() >> 5) & 31);
                int idx = Integer.bitCount(sub.keyMask & (bbit - 1)) * 2;
                direct = (sub.keyMask & bbit) != 0 && idx + 1 < sub.d.length
                    ? sub.d[idx + 1] : "NO-KEY-ROW";
            }
            boolean ok = step1 && subThere && "B".equals(direct) && "B".equals(m.get(b));
            row("TR-06", ok, "structure step1=" + step1 + " subThere=" + subThere
                + " [" + subShape + "] direct=" + direct + " get=" + m.get(b));
        } catch (Throwable t) { row("TR-06", false, "threw " + t); }

        // ── TR-07/08: recursion-boundary bisection ──
        try {
            Local a = new Local("kx1");
            Local b = new Local("ky1");
            for (int i = 1; i < 2000 && ((a.hashCode() >> 0) & 31) != 3; i++) a = new Local("kx" + i);
            for (int i = 1; i < 4000 && (b == null || ((b.hashCode() >> 0) & 31) != 3
                    || b.hashCode() == a.hashCode()); i++) b = new Local("ky" + i);
            hamt m = new hamt();
            m.put(a, "A");
            m.put(b, "B");
            Node r2 = m.root;
            int bit = 1 << ((a.hashCode() >> 0) & 31);
            Node sub = (Node) r2.d[r2.d.length - 1 - Integer.bitCount(r2.subMask & (bit - 1))];
            int hb = b.hashCode();
            Object directDepth5 = m.getAt(sub, hb, 5, b);      // explicit depth 5
            Object exprDepth = m.getAt(sub, hb, 0 + 5, b);     // 0+5 expression
            Object fromRootExpr = m.getAt(r2, hb, 0, b);       // the full walk, explicit
            boolean ok = "B".equals(directDepth5) && "B".equals(exprDepth)
                && "B".equals(fromRootExpr);
            row("TR-07", ok, "explicit-depth walks d5=" + directDepth5
                + " expr=" + exprDepth + " root=" + fromRootExpr);
        } catch (Throwable t) { row("TR-07", false, "threw " + t); }

        // ── TR-08: recursion frame trace ──
        try {
            Local a = new Local("kx1");
            Local b = new Local("ky1");
            for (int i = 1; i < 2000 && ((a.hashCode() >> 0) & 31) != 3; i++) a = new Local("kx" + i);
            for (int i = 1; i < 4000 && (b == null || ((b.hashCode() >> 0) & 31) != 3
                    || b.hashCode() == a.hashCode()); i++) b = new Local("ky" + i);
            hamt m = new hamt();
            m.put(a, "A");
            m.put(b, "B");
            hamt.frameTrace = "";
            Object g = m.get(b);
            row("TR-08", "B".equals(g), "frames=" + hamt.frameTrace + " get=" + g);
        } catch (Throwable t) { row("TR-08", false, "threw " + t); }

        // ── TR-04: negative — missing key answers null ──
        try {
            hamt m = new hamt();
            m.put(CONTENT_COLOR, "cc");
            row("TR-04", m.get(TEXT_STYLE) == null && m.get(new Local("zz")) == null,
                "missing keys answer null");
        } catch (Throwable t) { row("TR-04", false, "threw " + t); }

        // ── TR-05: replace existing key ──
        try {
            hamt m = new hamt();
            m.put(CONTENT_COLOR, "old");
            m.put(CONTENT_COLOR, "new");
            row("TR-05", "new".equals(m.get(CONTENT_COLOR)) && m.size == 2,
                "replace ok size=" + m.size);
        } catch (Throwable t) { row("TR-05", false, "threw " + t); }

        // ── SC-01: the provider-scope flow ──
        try {
            hamt outer = new hamt();
            outer.put(DENSITY, "1.0");
            hamt inner = new hamt();
            inner.put(DENSITY, "1.0");
            inner.put(CONTENT_COLOR, "theme-onSurface");
            boolean inside = "theme-onSurface".equals(resolve(inner, CONTENT_COLOR, "BLACK-DEFAULT"));
            boolean outside = "BLACK-DEFAULT".equals(resolve(outer, CONTENT_COLOR, "BLACK-DEFAULT"));
            row("SC-01", inside && outside, "scope resolve in=" + inside + " out=" + outside);
        } catch (Throwable t) { row("SC-01", false, "threw " + t); }

        // ── SC-02: same-instance key round trip (sget static semantics) ──
        try {
            hamt m = new hamt();
            m.put(COLOR_SCHEME, "scheme");
            Local same = COLOR_SCHEME;
            row("SC-02", "scheme".equals(m.get(same)), "same-instance key round trip");
        } catch (Throwable t) { row("SC-02", false, "threw " + t); }

        // ── SC-03: identity hashCode stability across many calls ──
        try {
            int h0 = CONTENT_COLOR.hashCode();
            boolean stable = true;
            for (int i = 0; i < 50; i++) stable &= CONTENT_COLOR.hashCode() == h0;
            row("SC-03", stable, "identity hashCode stable h=" + h0);
        } catch (Throwable t) { row("SC-03", false, "threw " + t); }

        // ── SC-04: packed-color law — (argb << 32) / toArgb (>>> 32) / the
        // 16 sentinel ──
        try {
            long black = 0xFF000000L << 32;
            long white = 0xFFFFFFFFL << 32;
            int argbBlack = (int) (black >>> 32);
            int argbWhite = (int) (white >>> 32);
            long unspec = 16L;
            boolean ok = argbBlack == 0xFF000000 && argbWhite == 0xFFFFFFFF
                && unspec != black && unspec == 16L;
            row("SC-04", ok, "pack/unpack laws ok black=" + Integer.toHexString(argbBlack));
        } catch (Throwable t) { row("SC-04", false, "threw " + t); }

        // ── SC-05: takeOrElse shape — specified wins, sentinel falls to Black ──
        try {
            long color = 0xFF335577L << 32;
            long resolved = (color != 16L) ? color : 0xFF000000L << 32;
            boolean ok = resolved == (0xFF335577L << 32);
            long unspec = 16L;
            long resolved2 = (unspec != 16L) ? unspec : 0xFF000000L << 32;
            ok &= resolved2 == (0xFF000000L << 32);
            row("SC-05", ok, "takeOrElse specified-wins/sentinel-falls ok");
        } catch (Throwable t) { row("SC-05", false, "threw " + t); }

        // ── PC-01: explicit non-black color on a REAL TextView ──
        TextView pc1 = new TextView(this);
        pc1.setTextColor(0xFF3366CC);
        row("PC-01", pc1.getCurrentTextColor() == 0xFF3366CC,
            "explicit non-black getCurrentTextColor=" + Integer.toHexString(pc1.getCurrentTextColor()));

        // ── PC-02: explicit black is a VALID requested color ──
        TextView pc2 = new TextView(this);
        pc2.setTextColor(0xFF000000);
        row("PC-02", pc2.getCurrentTextColor() == 0xFF000000, "explicit black preserved");

        // ── PC-03: alpha color preserved (no truncation to opaque) ──
        TextView pc3 = new TextView(this);
        pc3.setTextColor(0x80FF8800);
        row("PC-03", pc3.getCurrentTextColor() == 0x80FF8800,
            "alpha preserved=" + Integer.toHexString(pc3.getCurrentTextColor()));

        // ── PC-04: color CHANGE between two draws on the SAME widget ──
        TextView pc4 = new TextView(this);
        pc4.setTextColor(0xFFFF0000);
        boolean changed = pc4.getCurrentTextColor() == 0xFFFF0000;
        currentText = 0xFF00FF00;
        pc4.setTextColor(currentText);
        changed &= pc4.getCurrentTextColor() == 0xFF00FF00;
        row("PC-04", changed, "color change between draws ok");

        // ── visible render: runner-side pixel gate reads the final frame —
        // a WHITE 'COLORPROBE' text on a BLACK background. The text paints
        // through the REAL pipeline; the pixel row proves visibility. ──
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF000000);
        TextView tv = new TextView(this);
        tv.setText("CKPROBE " + countPass() + "/" + countTotal() + "\n" + report);
        tv.setTextColor(0xFFFFFFFF);
        tv.setTextSize(28f);
        root.addView(tv);
        TextView marker = new TextView(this);
        marker.setText("COLORPROBE");
        marker.setTextColor(0xFFFFFFFF);
        marker.setTextSize(28f);
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
