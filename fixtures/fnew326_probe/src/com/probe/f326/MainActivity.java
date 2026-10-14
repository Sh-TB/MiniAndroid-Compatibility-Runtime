package com.probe.f326;

import android.app.Activity;
import android.os.Bundle;
import android.view.ViewGroup;

/**
 * F-NEW-326 probe — asserts the AOSP ViewGroup.getChildMeasureSpec(III)I
 * law AND the framework-boundary static resolution by VALUE.
 *
 * ART truth: invoke-static resolution walks the FULL superclass chain —
 * past the DEX boundary into the framework — to the class that declares
 * the method. The support-lib R8 artifacts reference child-class-owned
 * method_ids that no DEX class declares; the engine's DEX-side resolver
 * stops at the framework boundary and the bridge keyed on the app class
 * answered the STUBBED typed default (0) — the solitaire drawer child
 * spec chain broke (spec 0x0 face).
 *
 * Rows print as F326|ID|PASS|detail via the engine println law.
 * The build produces TWO variants: unpatched (owner=ViewGroup direct)
 * and patched (the method_id owner byte-rewritten to MyBox — the R8
 * artifact shape; every row then exercises the full re-dispatch chain).
 */
public class MainActivity extends Activity {

    static final int EX = 1 << 30;   // 0x40000000 — in-place EXACTLY
    static final int AM = 2 << 30;   // 0x80000000 — in-place AT_MOST
    static final int UN = 0;         //            — in-place UNSPECIFIED

    static void row(String id, int got, int want) {
        System.out.println("F326|" + id + "|" + (got == want ? "PASS" : "FAIL")
                           + "|got=0x" + Integer.toHexString(got)
                           + " want=0x" + Integer.toHexString(want));
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // The AOSP law matrix (ViewGroup.java, stable since API 1):
        // EXACTLY parent: dim>=0 → EXACTLY|dim; MATCH → EXACTLY|size;
        //                 WRAP → AT_MOST|size; size = max(0, specSize-pad)
        row("P1-EX-WRAP",
            ViewGroup.getChildMeasureSpec(EX | 1080, 0, -2),
            (1080 & 0x3FFFFFFF) | AM);
        row("P2-EX-WRAP-PAD",
            ViewGroup.getChildMeasureSpec(EX | 1080, 100, -2),
            (980 & 0x3FFFFFFF) | AM);
        row("P3-EX-MATCH",
            ViewGroup.getChildMeasureSpec(EX | 1080, 0, -1),
            (1080 & 0x3FFFFFFF) | EX);
        row("P4-EX-DIM",
            ViewGroup.getChildMeasureSpec(EX | 1080, 0, 300),
            (300 & 0x3FFFFFFF) | EX);
        // AT_MOST parent: dim>=0 → EXACTLY|dim; MATCH/WRAP → AT_MOST|size
        row("P5-AM-WRAP",
            ViewGroup.getChildMeasureSpec(AM | 500, 0, -2),
            (500 & 0x3FFFFFFF) | AM);
        row("P6-AM-MATCH",
            ViewGroup.getChildMeasureSpec(AM | 500, 0, -1),
            (500 & 0x3FFFFFFF) | AM);
        row("P7-AM-DIM",
            ViewGroup.getChildMeasureSpec(AM | 500, 0, 200),
            (200 & 0x3FFFFFFF) | EX);
        // UNSPECIFIED parent: dim>=0 → EXACTLY|dim; MATCH/WRAP → UNSPEC|size
        row("P8-UN-WRAP",
            ViewGroup.getChildMeasureSpec(UN | 100, 0, -2),
            (100 & 0x3FFFFFFF) | UN);
        row("P9-UN-MATCH",
            ViewGroup.getChildMeasureSpec(UN | 100, 0, -1),
            (100 & 0x3FFFFFFF) | UN);
        row("P10-UN-DIM",
            ViewGroup.getChildMeasureSpec(UN | 100, 0, 50),
            (50 & 0x3FFFFFFF) | EX);
        // AOSP negative: a child dimension < WRAP_CONTENT (-7) matches NO
        // branch on an EXACTLY parent → resultSize=0, resultMode=UNSPEC → 0.
        row("N1-EX-NEG-DIM",
            ViewGroup.getChildMeasureSpec(EX | 1080, 0, -7),
            0);

        // The R8-artifact face (subclass-owned method_id, no declaration):
        // goes through owner=MyBox → DEX resolver miss → framework-boundary
        // retry (LinearLayout STUBBED → ViewGroup law).
        MyBox box = new MyBox(this);
        row("P11-SUBCLASS-OWNER",
            box.probeSpec(EX | 1080, 0, -2),
            (1080 & 0x3FFFFFFF) | AM);
        row("P12-SUBCLASS-MATCH",
            box.probeSpec(EX | 1080, 0, -1),
            (1080 & 0x3FFFFFFF) | EX);
    }
}
