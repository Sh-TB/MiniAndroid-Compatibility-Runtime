package com.probe.c99lay;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * CONT-99 T1 — View measurement and layout contract probe (V2).
 *
 * Deterministic px tree (window 1080x1920, all lp values in px so the
 * expectations are density-independent). Every row prints ACTUAL laid-out
 * bounds (getWidth/getHeight/getLeft/getTop), measured dims, the AOSP-law
 * expectation computed from the container's OWN observed origin
 * (self-anchoring), and an OK/DIVERGE verdict.
 *
 * Phases (Handler on the main looper):
 *   PHASE1 (post)      — runs BEFORE the first traversal by design
 *                        (AOSP: the first traversal is a Choreographer
 *                        callback; a plain Handler.post from onCreate
 *                        drains first). Rows print root bounds only —
 *                        all-zero views here are the CORRECT pre-layout
 *                        semantic (S103 W1 law), not a divergence.
 *   PHASE2 (post 1500) — settled tree after the first layout pass(es).
 *   PHASE3 (post 3000) — after btn.setLayoutParams(300,80) +
 *                        root.requestLayout() issued at PHASE2: the
 *                        relayout must have APPLIED by now (AOSP
 *                        requestLayout is deferred to the next
 *                        performTraversals, i.e. a later frame).
 *
 * Tree (V2 — the V1 colD expectations were fixture-error: in AOSP a
 * match_parent child with NO weight consumes the full row via its
 * EXACTLY(parent) measure, so the 0px+weight siblings collapse to 0 —
 * the engine answered exactly the AOSP law; the fixture now encodes it
 * and adds weightRow2, a clean two-weight row with NO match-parent
 * sibling, to prove the positive-space weight share):
 *   root LinearLayout VERTICAL match x match
 *     bar   LinearLayout HORIZONTAL match x 100  pad-l=20 pad-t=20  bg RED
 *       chip1 View 50x50 bg GREEN  leftMargin=10 (post-addView field store)
 *       chip2 View 50x50 bg BLUE   leftMargin=20 (post-addView field store)
 *     weightRow LinearLayout HORIZONTAL match x 150 bg #FF444444
 *       colA View lp_w=0 weight=1 h=match bg #FF00AA00
 *       colB View lp_w=0 weight=3 h=match bg #FF0000AA
 *       colC View lp_w=0 weight=1 h=100  bg #FFAAAA00
 *       colD View lp_w=match (NO weight) h=50 bg #FF333333
 *     frame FrameLayout match x 200 pad=30 (setPadding) bg WHITE
 *       inner LinearLayout HORIZONTAL 120x80 bg #FFFF8800
 *           (FrameLayout.LayoutParams(120, 80, Gravity.CENTER) ctor)
 *         leaf View 40x40 bg #FF800080 (centered by inner's container
 *            gravity CENTER: (120-40)/2, (80-40)/2)
 *     weightRow2 LinearLayout HORIZONTAL match x 150 bg #FF222222
 *       colE View lp_w=0 weight=1 h=match bg #FF008888
 *       colF View lp_w=0 weight=3 h=match bg #FF880088
 *     btn   Button 200x80 → PHASE3 expects 300x80
 *     img   ImageView 120x90 (bg #FF00FFFF — T1 verifies BOUNDS not content)
 *     mpChild View match x 60 bg #FF00AAAA
 *     wrapTv TextView wrap x wrap "Hello C99" (soft row: w>0, 20<=h<=300)
 */
public class MainActivity extends Activity {
    LinearLayout root, bar, weightRow, inner, weightRow2;
    FrameLayout frame;
    View chip1, chip2, colA, colB, colC, colD, colE, colF, leaf, mpChild;
    Button btn;
    ImageView img;
    TextView wrapTv;
    boolean phase2done = false;

    void row(String tag, View v, int el, int et, int ew, int eh) {
        int l = v.getLeft(), t = v.getTop();
        int w = v.getWidth(), h = v.getHeight();
        String verdict;
        if (eh < 0) { // soft row: range assertion on h, w>0
            verdict = (w > 0 && h >= 20 && h <= 300) ? "OK" : "DIVERGE";
        } else {
            verdict = (l == el && t == et && w == ew && h == eh) ? "OK" : "DIVERGE";
        }
        System.err.println("[C99-LAY] " + tag
                + " l=" + l + " t=" + t + " w=" + w + " h=" + h
                + " mw=" + v.getMeasuredWidth() + " mh=" + v.getMeasuredHeight()
                + " exp=" + el + "/" + et + "/" + ew + "/" + eh
                + " v=" + verdict);
    }

    void dump(String phase) {
        int rl = root.getLeft(), rt = root.getTop();
        System.err.println("[C99-PHASE] " + phase
                + " root=" + rl + "/" + rt + "/"
                + root.getWidth() + "/" + root.getHeight()
                + " padL=" + root.getPaddingLeft());
        // children of bar (self-anchored to bar's own observed origin)
        int blx = bar.getLeft(), bty = bar.getTop();
        row("chip1", chip1, blx + 20 + 10, bty + 20, 50, 50);
        row("chip2", chip2, blx + 20 + 10 + 50 + 20, bty + 20, 50, 50);
        row("bar", bar, rl, rt, 1080, 100);
        int wx = weightRow.getLeft(), wy = weightRow.getTop();
        row("weightRow", weightRow, rl, rt + 100, 1080, 150);
        // AOSP mixed row: colD (match_parent, no weight) measures
        // EXACTLY(1080) and consumes the row; the 0px+weight siblings
        // collapse to 0 width and stack at the origin.
        row("colA", colA, wx, wy, 0, 150);
        row("colB", colB, wx, wy, 0, 150);
        row("colC", colC, wx, wy, 0, 100);
        row("colD", colD, wx, wy, 1080, 50);
        int fl = frame.getLeft(), ft = frame.getTop();
        row("frame", frame, rl, rt + 250, 1080, 200);
        // inner centered in the padded content of the FrameLayout
        int cw = frame.getWidth() - 60, ch = frame.getHeight() - 60;
        row("inner", inner, fl + 30 + (cw - 120) / 2, ft + 30 + (ch - 80) / 2, 120, 80);
        // leaf centered inside inner by the CONTAINER gravity law
        row("leaf", leaf, inner.getLeft() + 40, inner.getTop() + 20, 40, 40);
        int w2x = weightRow2.getLeft(), w2y = weightRow2.getTop();
        row("weightRow2", weightRow2, rl, rt + 450, 1080, 150);
        // AOSP clean weight row: free = 1080; shares 1:3
        row("colE", colE, w2x, w2y, 1080 * 1 / 4, 150);
        row("colF", colF, w2x + 1080 * 1 / 4, w2y, 1080 * 3 / 4, 150);
        row("btn", btn, rl, rt + 600, phase2done ? 200 : 200, 80);
        row("img", img, rl, rt + 680, 120, 90);
        row("mpChild", mpChild, rl, rt + 770, 1080, 60);
        row("wrapTv", wrapTv, rl, rt + 830, 0, -1);
    }

    void dumpPhase3() {
        int rl = root.getLeft(), rt = root.getTop();
        // AOSP: the requestLayout relayout has applied by a LATER frame
        row("btn-P3", btn, rl, rt + 600, 300, 80);
        row("img-P3", img, rl, rt + 680, 120, 90);
        row("mpChild-P3", mpChild, rl, rt + 770, 1080, 60);
    }

    void buildTree() {
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        setContentView(root);

        bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setPadding(20, 20, 0, 0);
        bar.setBackgroundColor(0xFFFF0000);
        root.addView(bar, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 100));

        chip1 = new View(this);
        chip1.setBackgroundColor(0xFF00FF00);
        bar.addView(chip1, new LinearLayout.LayoutParams(50, 50));
        ((LinearLayout.LayoutParams) chip1.getLayoutParams()).leftMargin = 10;

        chip2 = new View(this);
        chip2.setBackgroundColor(0xFF0000FF);
        bar.addView(chip2, new LinearLayout.LayoutParams(50, 50));
        ((LinearLayout.LayoutParams) chip2.getLayoutParams()).leftMargin = 20;

        weightRow = new LinearLayout(this);
        weightRow.setOrientation(LinearLayout.HORIZONTAL);
        weightRow.setBackgroundColor(0xFF444444);
        root.addView(weightRow, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 150));

        LinearLayout.LayoutParams la = new LinearLayout.LayoutParams(0,
                LinearLayout.LayoutParams.MATCH_PARENT);
        la.weight = 1f;
        colA = new View(this);
        colA.setBackgroundColor(0xFF00AA00);
        weightRow.addView(colA, la);

        LinearLayout.LayoutParams lb = new LinearLayout.LayoutParams(0,
                LinearLayout.LayoutParams.MATCH_PARENT);
        lb.weight = 3f;
        colB = new View(this);
        colB.setBackgroundColor(0xFF0000AA);
        weightRow.addView(colB, lb);

        LinearLayout.LayoutParams lc = new LinearLayout.LayoutParams(0, 100);
        lc.weight = 1f;
        colC = new View(this);
        colC.setBackgroundColor(0xFFAAAA00);
        weightRow.addView(colC, lc);

        colD = new View(this);
        colD.setBackgroundColor(0xFF333333);
        weightRow.addView(colD, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 50));

        frame = new FrameLayout(this);
        frame.setPadding(30, 30, 30, 30);
        frame.setBackgroundColor(0xFFFFFFFF);
        root.addView(frame, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 200));

        inner = new LinearLayout(this);
        inner.setOrientation(LinearLayout.HORIZONTAL);
        inner.setGravity(Gravity.CENTER);
        inner.setBackgroundColor(0xFFFF8800);
        frame.addView(inner, new FrameLayout.LayoutParams(120, 80, Gravity.CENTER));

        leaf = new View(this);
        leaf.setBackgroundColor(0xFF800080);
        inner.addView(leaf, new LinearLayout.LayoutParams(40, 40));

        weightRow2 = new LinearLayout(this);
        weightRow2.setOrientation(LinearLayout.HORIZONTAL);
        weightRow2.setBackgroundColor(0xFF222222);
        root.addView(weightRow2, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 150));

        LinearLayout.LayoutParams le = new LinearLayout.LayoutParams(0,
                LinearLayout.LayoutParams.MATCH_PARENT);
        le.weight = 1f;
        colE = new View(this);
        colE.setBackgroundColor(0xFF008888);
        weightRow2.addView(colE, le);

        LinearLayout.LayoutParams lf = new LinearLayout.LayoutParams(0,
                LinearLayout.LayoutParams.MATCH_PARENT);
        lf.weight = 3f;
        colF = new View(this);
        colF.setBackgroundColor(0xFF880088);
        weightRow2.addView(colF, lf);

        btn = new Button(this);
        btn.setText("OK");
        root.addView(btn, new LinearLayout.LayoutParams(200, 80));

        img = new ImageView(this);
        img.setBackgroundColor(0xFF00FFFF);
        root.addView(img, new LinearLayout.LayoutParams(120, 90));

        mpChild = new View(this);
        mpChild.setBackgroundColor(0xFF00AAAA);
        root.addView(mpChild, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 60));

        wrapTv = new TextView(this);
        wrapTv.setText("Hello C99");
        root.addView(wrapTv, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT));
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        buildTree();
        System.err.println("[C99-VER] V2-C99LAY");
        Handler h = new Handler(Looper.getMainLooper());
        h.post(new Runnable() { public void run() {
            // Pre-traversal by design: root bounds only (S103 law: a
            // measure-less view answers 0 — the CORRECT pre-layout state).
            System.err.println("[C99-PHASE] PHASE1 root=" + root.getLeft()
                    + "/" + root.getTop() + "/" + root.getWidth()
                    + "/" + root.getHeight());
        }});
        h.postDelayed(new Runnable() { public void run() {
            try {
                if (!phase2done) {
                    phase2done = true;
                    dump("PHASE2");
                    btn.setLayoutParams(new LinearLayout.LayoutParams(300, 80));
                    root.requestLayout();
                    System.err.println("[C99-MUT] setLayoutParams(300,80)+requestLayout");
                }
            } catch (Throwable t) { System.err.println("[C99-ERR] P2 " + t); }
        }}, 1500);
        h.postDelayed(new Runnable() { public void run() {
            try { dumpPhase3(); System.err.println("[C99-DONE] PHASE3-PRINTED"); }
            catch (Throwable t) { System.err.println("[C99-ERR] P3 " + t); }
        }}, 3000);
    }
}
