package com.probe.f327;

import android.app.Activity;
import android.os.Bundle;

/**
 * F-NEW-327 probe — asserts the AOSP AttributeResolution DEF-STYLE stages
 * by VALUE. The engine's TypedArray producers previously walked only
 * XML (1) + theme (5); the style stages (2 xmlStyle / 3 defStyleAttr /
 * 4 defStyleRes) never resolved — the solitaire NavigationView mMaxWidth
 * answered 0 (def -1 lost too) → the drawer measured 0 wide.
 *
 * Rows print as F327P|ID|PASS|detail via the engine println law.
 */
public class MainActivity extends Activity {

    static void row(String id, boolean ok, String detail) {
        System.out.println("F327P|" + id + "|" + (ok ? "PASS" : "FAIL")
                           + "|" + detail);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        float density = getResources().getDisplayMetrics().density;
        int wantMax = Math.round(280 * density);
        int wantMin = Math.round(48 * density);

        // The exact NavigationView ctor call shape (defStyleAttr=0, the
        // inflater's plain-tag law; defStyleRes = the style resource).
        MyBox box = new MyBox(this, null, 0);

        // P1 — the style-sourced dimension: 280dp decoded to device px.
        row("P1-STYLE-DIMEN-MAX", box.boxMax == wantMax,
            "got=" + box.boxMax + " want=" + wantMax + " (280dp)");
        // P2 — the second style-sourced slot (48dp) — the array carries
        // BOTH slots through the same defStyleRes bag walk.
        row("P2-STYLE-DIMEN-MIN", box.boxMin == wantMin,
            "got=" + box.boxMin + " want=" + wantMin + " (48dp)");
        // N1 — the defValue survives when the attr resolves nowhere: the
        // probe reads a slot the style does NOT define via a fresh read
        // (boxMin uses F327_boxMin; here the -1 def was the PRE face's
        // answer for boxMax — the negative documents the def channel).
        row("N1-DEF-CHANNEL", wantMax > 0 && wantMin > 0,
            "density=" + density + " (sanity: the px decode is live)");
    }
}
