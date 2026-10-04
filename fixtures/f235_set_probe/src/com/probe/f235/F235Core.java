package com.probe.f235;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * F-NEW-235 probe core — replicates the fairymahjong BoardShape dedup chain
 * exactly as R8/Kotlin compiled it (Lm;.&lt;init&gt; -> Ls;.D toSet -> Ls;.z
 * addAll -> Lj0; EmptySet), with per-stage PASS/FAIL rows so the first
 * diverging stage is directly observable on any engine.
 *
 * Semantics under test (OpenJDK/libcore source law):
 *   1. every java.util collection class IS-A java.util.Collection /
 *      java.util.List / java.util.Set / java.util.Map / java.lang.Iterable
 *      (JLS instanceof through interface closure);
 *   2. Collections.unmodifiableList(x) — a List view: still a Collection,
 *      same size, same iteration (OpenJDK Collections.UnmodifiableList);
 *   3. Kotlin toSet() shape: size==0 -> EmptySet; size==1 -> singleton;
 *      else LinkedHashSet(mapCapacity(size)) + addAll(iterate + add);
 *   4. Set element identity = equals/hashCode (data-class 31-mix law);
 *   5. dedup gate: positions.toSet().size() != positions.size() <=> a real
 *      duplicate exists.
 */
public final class F235Core {
    // ── Lq5; TilePosition replica: 3 ints, Kotlin data-class semantics ──
    public static final class TilePos {
        public final int x, y, layer;
        public TilePos(int x, int y, int layer) {
            this.x = x; this.y = y; this.layer = layer;
        }
        @Override public boolean equals(Object o) {
            if (this == o) return true;
            if (!(o instanceof TilePos)) return false;
            TilePos t = (TilePos) o;
            return x == t.x && y == t.y && layer == t.layer;
        }
        @Override public int hashCode() {
            // Kotlin data class: Integer.hashCode(field) mixed by 31 per component
            int r = java.lang.Integer.hashCode(x);
            r = r * 31 + java.lang.Integer.hashCode(y);
            r = r * 31 + java.lang.Integer.hashCode(layer);
            return r;
        }
        @Override public String toString() {
            return "TilePos(x=" + x + ", y=" + y + ", layer=" + layer + ")";
        }
    }

    public interface Row { void row(String id, boolean pass, String detail); }

    /** 50 distinct positions mirroring the game's layer-0 geometry. */
    public static List<TilePos> buildTiles() {
        List<TilePos> tiles = new ArrayList<TilePos>();
        for (int layer = 0; layer < 1; layer++) {
            int n = 0;
            for (int y = 0; n < 50 && y < 16; y++) {
                for (int x = (y % 2 == 0 ? 1 : 2); n < 50 && x < 16; x += 2) {
                    tiles.add(new TilePos(x, y, layer));
                    n++;
                }
            }
        }
        return tiles;
    }

    /** Ls;.z addAll replica: iterate + Collection.add, return count. */
    @SuppressWarnings({"unchecked", "rawtypes"})
    public static int addAllLike(Collection dst, Iterable src) {
        int n = 0;
        Iterator it = src.iterator();
        while (it.hasNext()) {
            dst.add(it.next());
            n++;
        }
        return n;
    }

    /** Kotlin mapCapacity (Li4;.p) replica. */
    public static int mapCapacity(int n) {
        if (n < 0) return n;
        if (n < 3) return n + 1;
        if (n < 1 << 30) return (int) ((n / 0.75f) + 1.0f);
        return Integer.MAX_VALUE;
    }

    /** Ls;.D toSet replica with the exact Kotlin branch shape. */
    @SuppressWarnings({"unchecked", "rawtypes"})
    public static Set<?> toSetLike(Object receiver) {
        if (receiver instanceof Collection) {
            Collection c = (Collection) receiver;
            int size = c.size();
            if (size == 0) return new LinkedHashSet();   // EmptySet stand-in
            if (size == 1) {
                Iterator it = c.iterator();
                return Collections.singleton(it.next());
            }
            LinkedHashSet set = new LinkedHashSet(mapCapacity(size));
            addAllLike(set, c);
            return set;
        }
        LinkedHashSet set2 = new LinkedHashSet();
        addAllLike(set2, (Iterable) receiver);
        if (set2.size() == 0) return new LinkedHashSet();
        if (set2.size() == 1) return Collections.singleton(set2.iterator().next());
        return set2;
    }

    public static void run(Row row) {
        // P01 — instanceof Collection on ArrayList (interface-closure law)
        List<TilePos> tiles = buildTiles();
        boolean isColl = tiles instanceof Collection;
        row.row("P01-ARRAYLIST-IS-COLLECTION", isColl,
                "ArrayList instanceof Collection=" + isColl);

        // P02 — instanceof List on ArrayList
        boolean isList = tiles instanceof List;
        row.row("P02-ARRAYLIST-IS-LIST", isList, "instanceof List=" + isList);

        // P03 — the unmodifiable view chain (Lm;.b backing via
        // Collections.unmodifiableList): view is a Collection, size 50.
        List<TilePos> view = Collections.unmodifiableList(tiles);
        boolean viewIsColl = view instanceof Collection;
        int viewSize = viewIsColl ? ((Collection<TilePos>) view).size() : -1;
        row.row("P03-UNMODIFIABLE-VIEW", viewIsColl && viewSize == 50,
                "instanceof=" + viewIsColl + " size=" + viewSize);

        // P04 — iteration of the view yields every element (z's loop fuel)
        int counted = 0;
        Iterator<TilePos> it = view.iterator();
        while (it.hasNext()) { it.next(); counted++; }
        row.row("P04-ITERATE-COUNT", counted == 50, "iterated=" + counted);

        // P05 — the exact toSet chain: toSetLike(view).size() == 50
        Set<?> built = toSetLike(view);
        int bsize = built.size();
        row.row("P05-TOSET-SIZE", bsize == 50, "toSet(view).size()=" + bsize);

        // P06 — the game's dedup gate must NOT fire on distinct positions
        boolean gate = built.size() != view.size();
        row.row("P06-DEDUP-GATE", !gate,
                "set!=" + built.size() + " list=" + view.size()
                + " gate=" + gate);

        // P07 — Set.add equality law: 3 adds of 2 equal-valued positions
        Set<TilePos> s = new LinkedHashSet<TilePos>();
        boolean a1 = s.add(new TilePos(3, 0, 0));
        boolean a2 = s.add(new TilePos(5, 0, 0));
        boolean a3 = s.add(new TilePos(3, 0, 0));  // equal value → false
        row.row("P07-SET-ADD-EQUALS", a1 && a2 && !a3 && s.size() == 2,
                "adds=" + a1 + "/" + a2 + "/" + a3 + " size=" + s.size());

        // P08 — Set.contains with an equal-but-distinct key
        boolean c1 = s.contains(new TilePos(5, 0, 0));
        boolean c2 = s.contains(new TilePos(7, 0, 0));
        row.row("P08-SET-CONTAINS-EQUAL", c1 && !c2,
                "contains(5,0,0)=" + c1 + " contains(7,0,0)=" + c2);

        // P09 — Set/Map/Iterable closures on the other framework families
        Set<String> hs = new HashSet<String>();
        hs.add("a");
        Map<String, String> hm = new HashMap<String, String>();
        hm.put("k", "v");
        boolean setOk = hs instanceof Set && hs instanceof Collection
                        && hm instanceof Map;
        row.row("P09-SET-MAP-CLOSURE", setOk,
                "HashSet is Set/Collection, HashMap is Map: " + setOk);

        // N01 — negative: EmptySet shape for a size==0 receiver (0x0f branch)
        Set<?> empty = toSetLike(new ArrayList<TilePos>());
        row.row("N01-EMPTY-TARGET", empty.size() == 0,
                "toSet(empty).size()=" + empty.size());

        // N02 — negative: singleton shape for a size==1 receiver (0x11 branch)
        List<TilePos> one = new ArrayList<TilePos>();
        one.add(new TilePos(1, 1, 0));
        Set<?> single = toSetLike(one);
        row.row("N02-SINGLETON-TARGET", single.size() == 1,
                "toSet(one).size()=" + single.size());

        // P10 — the Lo;.<clinit> board-registry shape: new-array + aput
        // layers + listOf(vararg) + first().length — the exact chain whose
        // first() threw "List is empty." on a valid butterfly board.
        List<String> layerA = new ArrayList<String>();
        layerA.add(".......");
        layerA.add(".#...#.");
        List<String> layerB = new ArrayList<String>();
        layerB.add("..###..");
        List<String> layerC = new ArrayList<String>();
        layerC.add("...#...");
        Object[] layers = new Object[3];
        layers[0] = layerA;
        layers[1] = layerB;
        layers[2] = layerC;
        List<Object> layerList = new ArrayList<Object>();
        for (Object o : layers) layerList.add(o);   // listOf(vararg) copy
        Object first0 = layerList.isEmpty() ? null : layerList.get(0);
        boolean p10 = first0 instanceof List
                      && ((List<?>) first0).size() == 2;
        row.row("P10-LAYER-REGISTRY", p10,
                "first=" + first0 + " layers=" + layerList.size());

        // P11 — filled-array via asList + aget round-trip (array[i] store)
        String[] rows = new String[3];
        rows[0] = ".......";
        rows[1] = ".#...#.";
        rows[2] = "..###..";
        java.util.List<String> asList = java.util.Arrays.asList(rows);
        boolean p11 = asList.size() == 3
                      && ".......".equals(asList.get(0));
        row.row("P11-ASLIST-ROUNDTRIP", p11,
                "size=" + asList.size() + " first=" +
                (asList.isEmpty() ? "<empty>" : asList.get(0)));

        // N03 — negative: toSetLike on a NON-Collection Iterable keeps the
        // Iterable branch honest (0x40 path) — 50 via iterator as well.
        final List<TilePos> src = tiles;
        Iterable<TilePos> itOnly = new Iterable<TilePos>() {
            public Iterator<TilePos> iterator() { return src.iterator(); }
        };
        Set<?> viaIterable = toSetLike(itOnly);
        row.row("N03-ITERABLE-PATH", viaIterable.size() == 50,
                "toSet(iterable).size()=" + viaIterable.size());
    }

    private F235Core() {}
}
