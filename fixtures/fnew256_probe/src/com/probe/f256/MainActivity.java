package com.probe.f256;

import android.app.Activity;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.List;

/**
 * CONT-11 W7B synthetic probe — the compose PLACEMENT cascade engine-law faces
 * (F-NEW-256 W7A refinement: the tree materializes+attaches+measures, but the
 * placement cascade never lands → isPlaced stays false → drawBlock skips).
 *
 * Upstream contracts under test (generic platform laws — no app specifics):
 *
 *  F256-A (face β) measureResult backing-field law: private backing starts
 *          NULL; null-checking getter; the layout-block SAM held inside the
 *          result MUST run exactly once per placeChildren() invocation via
 *          interface dispatch on the runtime class; a never-measured holder
 *          must NOT crash the chain (upstream: DefaultMeasureResult no-op or
 *          UnmeasuredError) — the block counter proves which path ran.
 *  F256-B (face α) layoutChildren guard law: the exact 4-term short-circuit
 *          chain from upstream MeasurePassDelegate.layoutChildren():
 *            layoutPendingForAlignment || (!duringAlignmentLinesQuery &&
 *            !isPlacingForAlignment && layoutPending)
 *          must enter the block when layoutPending=true and skip when false,
 *          clearing layoutPending inside the block (upstream law).
 *  F256-C (face δ) inlined placeAt write-first law: a runnable whose FIRST
 *          statement writes delegate.isPlacedByParent=true, then branches;
 *          the flag must land in BOTH the early-return and the fallthrough
 *          branch (upstream placeAt sets isPlacedByParent=true before any
 *          layoutPending check) — invoked via a holder-held lambda field.
 *  F256-D markNodeAndSubtreeAsPlaced recursion law: set self flag then
 *          recurse children depth-first (the q0 shape) — all nodes flagged.
 *  F256-E packed-switch placement dispatch (the Placeable-place shape):
 *          int derived from Float.floatToRawIntBits must dispatch every arm
 *          of a packed-switch (R8 compiles the zIndex/layer dispatch this way).
 */
public class MainActivity extends Activity {

    private static String report = "";

    private static void row(String id, boolean pass, String detail) {
        report += id + "|" + (pass ? "PASS" : "FAIL") + "|" + detail + "\n";
    }

    // ── F256-A machinery ────────────────────────────────────────────────
    interface MResult { void placeChildren(); }

    static int noOpRuns = 0;
    static final MResult DEFAULT_NOOP = new MResult() {
        @Override public void placeChildren() { noOpRuns++; }
    };

    static class LayoutBlock implements MResult {
        int runs = 0;
        int placedFlagWrites = 0;
        @Override public void placeChildren() { runs++; placedFlagWrites++; }
    }

    static class Coordinator {
        private MResult _measureResult = null;   // upstream _measureResult null default
        boolean hasResult() { return _measureResult != null; }
        MResult result() { return _measureResult; }        // raw read (may be null)
        void setResult(MResult r) { _measureResult = r; }  // upstream internal set
        void placeChildrenViaGetter() {
            MResult r = _measureResult != null ? _measureResult : DEFAULT_NOOP;
            r.placeChildren();
        }
    }

    // ── F256-C machinery ────────────────────────────────────────────────
    static class Delegate {
        boolean isPlacedByParent = false;
        boolean needsCoordinatesUpdate = false;
    }

    interface PlaceAction { void place(); }

    static class PlaceAt implements PlaceAction {
        Delegate d;
        int position;
        PlaceAt(Delegate d, int position) { this.d = d; this.position = position; }
        @Override public void place() {
            d.isPlacedByParent = true;                 // FIRST STATEMENT — upstream law
            if (position != 0) {
                d.needsCoordinatesUpdate = true;
                return;                                // early return AFTER the write
            }
            d.needsCoordinatesUpdate = false;
        }
    }

    static class PlaceHolder {
        PlaceAction block;                             // holder-held lambda field
        void run() { block.place(); }                  // interface dispatch on field
    }

    // ── F256-D machinery ────────────────────────────────────────────────
    static class LNode {
        boolean isPlaced = false;
        final List<LNode> children = new ArrayList<>();
        void markNodeAndSubtreeAsPlaced() {
            isPlaced = true;
            for (int i = 0; i < children.size(); i++) {
                children.get(i).markNodeAndSubtreeAsPlaced();
            }
        }
    }

    // ── F256-E machinery ────────────────────────────────────────────────
    static int switchArm = -1;
    static void dispatchByFloatBits(float z) {
        int bits = Float.floatToRawIntBits(z);
        int key = (bits >>> 24) & 0x03;                // packed-switch payload path
        switch (key) {
            case 0: switchArm = 0; break;
            case 1: switchArm = 1; break;
            case 2: switchArm = 2; break;
            case 3: switchArm = 3; break;
            default: switchArm = 99; break;
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // ── F256-A: measureResult backing field + SAM block dispatch ────
        try {
            Coordinator c = new Coordinator();
            // never-measured path must fall to the no-op, not crash
            c.placeChildrenViaGetter();
            boolean noopPath = (noOpRuns == 1);
            // measured path: the real result's block runs via interface dispatch
            LayoutBlock lb = new LayoutBlock();
            c.setResult(lb);
            c.placeChildrenViaGetter();
            boolean realPath = (lb.runs == 1) && c.hasResult();
            // the SAME object persists across methods (field law)
            MResult again = c.result();
            boolean identity = (again == lb);
            row("F256-A", noopPath && realPath && identity,
                "noop=" + noOpRuns + " blockRuns=" + lb.runs
                + " identity=" + identity + " hasResult=" + c.hasResult());
        } catch (Throwable t) { row("F256-A", false, "threw " + t); }

        // ── F256-B: the layoutChildren 4-term guard ─────────────────────
        try {
            boolean layoutPendingForAlignment = false;
            boolean duringAlignmentLinesQuery = false;
            boolean isPlacingForAlignment = false;
            boolean layoutPending = true;
            boolean ran = false;
            if (layoutPendingForAlignment ||
                    (!duringAlignmentLinesQuery && !isPlacingForAlignment && layoutPending)) {
                ran = true;
                layoutPending = false;                 // cleared inside the block
            }
            boolean positive = ran && !layoutPending;
            // negative: pending=false → skip
            boolean ran2 = false;
            boolean layoutPending2 = false;
            if (layoutPendingForAlignment ||
                    (!duringAlignmentLinesQuery && !isPlacingForAlignment && layoutPending2)) {
                ran2 = true;
            }
            row("F256-B", positive && !ran2,
                "ran=" + ran + " cleared=" + !layoutPending + " negativeRan=" + ran2);
        } catch (Throwable t) { row("F256-B", false, "threw " + t); }

        // ── F256-C: inlined placeAt write-first via holder-held lambda ──
        try {
            Delegate d1 = new Delegate();
            PlaceHolder h = new PlaceHolder();
            h.block = new PlaceAt(d1, 0);
            h.run();                                   // fallthrough branch
            boolean fallthrough = d1.isPlacedByParent;
            Delegate d2 = new Delegate();
            PlaceHolder h2 = new PlaceHolder();
            h2.block = new PlaceAt(d2, 7);
            h2.run();                                  // early-return branch
            boolean early = d2.isPlacedByParent && d2.needsCoordinatesUpdate;
            row("F256-C", fallthrough && early,
                "fallthrough=" + fallthrough + " early=" + early);
        } catch (Throwable t) { row("F256-C", false, "threw " + t); }

        // ── F256-D: markNodeAndSubtreeAsPlaced recursion ────────────────
        try {
            LNode root = new LNode();
            LNode a = new LNode(); LNode b = new LNode();
            LNode a1 = new LNode(); LNode a2 = new LNode();
            root.children.add(a); root.children.add(b);
            a.children.add(a1); a.children.add(a2);
            root.markNodeAndSubtreeAsPlaced();
            boolean all = root.isPlaced && a.isPlaced && b.isPlaced
                && a1.isPlaced && a2.isPlaced;
            row("F256-D", all, "placedAll=" + all + " depth=3 breadth=2");
        } catch (Throwable t) { row("F256-D", false, "threw " + t); }

        // ── F256-E: packed-switch over float bits ───────────────────────
        try {
            boolean ok = true;
            // top byte of the float bits is 0x00,0x41,0x42,0x43 → keys 0..3
            float[] inputs = {0.0f, 8.5f, 32.0f, 128.0f};
            for (int i = 0; i < inputs.length; i++) {
                dispatchByFloatBits(inputs[i]);
                if (switchArm != i) ok = false;
            }
            row("F256-E", ok, "arms=0,1,2,3 ok=" + ok);
        } catch (Throwable t) { row("F256-E", false, "threw " + t); }

        TextView tv = new TextView(this);
        tv.setText(report.isEmpty() ? "NO ROWS" : report);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.addView(tv);
        setContentView(root);
    }
}
