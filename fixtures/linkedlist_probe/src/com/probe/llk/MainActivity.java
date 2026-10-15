/* linkedlist_probe — CONT-69 semantic probe for the java.util collection
 * CONSTRUCTION law (F-NEW-369 root family).
 *
 * The root shape (memory, cold first launch):
 *   MemoGameDefaultImages.getResIDs:  LinkedList l = new LinkedList();
 *   ResIdAdapter.getResourceName:     for (X s : l) { ... }   ← l never
 *   added-to on this path, so the receiver object carried NO F-036 backing
 *   store (__array_length__), the iterator law's presence gate failed and
 *   the shadow answered a NULL iterator → hasNext NPE → onCreate unwind.
 *
 * Families (each writes a machine-readable jsonl row + TextView line):
 *   P1  zero-add LinkedList + immediate for-each  (THE root shape)
 *   P2  LinkedList add(a,b) + iterate             (order fidelity)
 *   P3  LinkedList(Collection) copy ctor + size   (cascade interplay)
 *   P4  zero-add ArrayList + for-each             (family-wide negative
 *                                                  control — same law must
 *                                                  hold for ArrayList)
 *   P5  fresh LinkedList size()==0 && isEmpty()
 *   P6  iterator() explicit on fresh list, hasNext()==false, no next()
 */
package com.probe.llk;

import android.app.Activity;
import android.content.Context;
import android.os.Bundle;
import android.widget.TextView;
import java.io.FileOutputStream;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.LinkedList;

public class MainActivity extends Activity {

    private StringBuilder RES = new StringBuilder();

    private void ok(String op, String d) {
        RES.append("LLK|").append(op).append("|PASS|").append(d).append("\n");
    }
    private void fail(String op, String d) {
        RES.append("LLK|").append(op).append("|FAIL|").append(d).append("\n");
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        try { runProbe(); } catch (Throwable t) { fail("PROBE-FATAL", String.valueOf(t)); }
        try {
            FileOutputStream fos = openFileOutput("linkedlist_results.jsonl",
                                                  Context.MODE_PRIVATE);
            fos.write(RES.toString().getBytes("UTF-8"));
            fos.flush();
            fos.close();
        } catch (Throwable t) { fail("RESULTS-WRITE", String.valueOf(t)); }
        TextView tv = new TextView(this);
        tv.setTextSize(12f);
        tv.setText(RES.toString());
        setContentView(tv);
    }

    private void runProbe() {
        // P1 — THE ROOT SHAPE: construct, never add, for-each immediately.
        // AOSP: the loop body must be skipped (empty iterator); NO exception.
        try {
            LinkedList<String> l = new LinkedList<String>();
            int n = 0;
            for (String s : l) n++;
            ok("P1", n == 0 ? "EMPTY_OK n=0" : "UNEXPECTED n=" + n);
        } catch (Throwable t) { fail("P1", String.valueOf(t)); }

        // P2 — add then iterate: element order + count fidelity.
        try {
            LinkedList<String> l = new LinkedList<String>();
            l.add("a");
            l.add("b");
            StringBuilder sb = new StringBuilder();
            for (String s : l) {
                if (sb.length() > 0) sb.append(',');
                sb.append(s);
            }
            ok("P2", "a,b".equals(sb.toString())
                     ? "ORDER_OK a,b" : "WRONG " + sb.toString());
        } catch (Throwable t) { fail("P2", String.valueOf(t)); }

        // P3 — LinkedList(Collection) copy ctor: size + element carry.
        try {
            ArrayList<String> src = new ArrayList<String>();
            src.add("x");
            LinkedList<String> l = new LinkedList<String>(src);
            StringBuilder sb = new StringBuilder();
            for (String s : l) sb.append(s);
            String srcGet, cpGet;
            try { srcGet = String.valueOf(src.get(0)); }
            catch (Throwable t) { srcGet = "get-threw:" + t.getClass().getSimpleName(); }
            try { cpGet = String.valueOf(l.get(0)); }
            catch (Throwable t) { cpGet = "get-threw:" + t.getClass().getSimpleName(); }
            boolean good = (l.size() == 1) && "x".equals(sb.toString());
            ok("P3", good ? "COPY_OK size=1 it=x"
                          : "WRONG size=" + l.size() + " it=" + sb.toString()
                            + " src.get0=" + srcGet + " cp.get0=" + cpGet);
        } catch (Throwable t) { fail("P3", String.valueOf(t)); }

        // P4 — FAMILY-WIDE CONTROL: zero-add ArrayList + for-each.
        try {
            ArrayList<String> l = new ArrayList<String>();
            int n = 0;
            for (String s : l) n++;
            ok("P4", n == 0 ? "EMPTY_OK n=0" : "UNEXPECTED n=" + n);
        } catch (Throwable t) { fail("P4", String.valueOf(t)); }

        // P5 — fresh LinkedList answers the AOSP empty-contract scalars.
        try {
            LinkedList<String> l = new LinkedList<String>();
            boolean e = l.isEmpty();
            int sz = l.size();
            ok("P5", (e && sz == 0) ? "TRUE"
                                    : "isEmpty=" + e + " size=" + sz);
        } catch (Throwable t) { fail("P5", String.valueOf(t)); }

        // P6 — explicit iterator() on a fresh list: hasNext()==false and
        // next() must throw NoSuchElementException (AOSP contract).
        try {
            LinkedList<String> l = new LinkedList<String>();
            Iterator<String> it = l.iterator();
            boolean hn = it.hasNext();
            try {
                it.next();
                fail("P6", "no-exception on next() over empty iterator");
            } catch (java.util.NoSuchElementException nsee) {
                ok("P6", hn ? "WRONG hasNext=true but next threw NSEE"
                            : "EMPTY_IT_OK hasNext=false next=NSEE");
            }
        } catch (Throwable t) { fail("P6", String.valueOf(t)); }

        // P7 — THE APP ROOT SHAPE: ArrayList.subList(1,3) view + iterate.
        // (memory cold path: reduce() returns list.subList(0, n), the
        // caller for-eaches it; a null subList = hasNext NPE = white face)
        try {
            ArrayList<String> l = new ArrayList<String>();
            l.add("a"); l.add("b"); l.add("c");
            java.util.List<String> sub = l.subList(1, 3);
            StringBuilder sb = new StringBuilder();
            for (String s : sub) {
                if (sb.length() > 0) sb.append(',');
                sb.append(s);
            }
            ok("P7", (sub.size() == 2 && "b,c".equals(sb.toString()))
                     ? "SUBLIST_OK b,c" : "WRONG size=" + sub.size()
                                          + " it=" + sb.toString());
        } catch (Throwable t) { fail("P7", String.valueOf(t)); }

        // P8 — LinkedList.subList + subList-of-subList chain (view law).
        try {
            LinkedList<String> l = new LinkedList<String>();
            for (int i = 0; i < 5; i++) l.add(String.valueOf(i));
            java.util.List<String> sub = l.subList(1, 4);
            java.util.List<String> sub2 = sub.subList(1, 2);
            StringBuilder sb = new StringBuilder();
            for (String s : sub2) sb.append(s);
            ok("P8", (sub.size() == 3 && "2".equals(sb.toString()))
                     ? "CHAIN_OK 3/2" : "WRONG sub=" + sub.size()
                                        + " sub2it=" + sb.toString());
        } catch (Throwable t) { fail("P8", String.valueOf(t)); }
    }
}
