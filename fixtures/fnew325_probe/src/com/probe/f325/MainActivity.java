package com.probe.f325;

import android.app.Activity;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.LinearLayout;

/**
 * F-NEW-325 probe — asserts the S134 field-key law's framework-owned leg
 * by VALUE. ART: field resolution walks the receiver's class chain; a
 * field NOT declared by any DEX class lives in the framework superclass
 * — ONE bare slot, whoever references it. The runtime keyed the
 * interpreter's iget/iput with the REF class (MyLP, DEX) → a fabricated
 * qualified identity ("LMyLP;->width") split from the bare slot every
 * non-interpreter writer uses → reads answered the fabricated default.
 * Runtime face: F-NEW-309 wrote NavigationView's LP width=-2 (wrap), the
 * real DEX DrawerLayout.onMeasure read 0 → the drawer measured 0x0.
 *
 * Rows print as F325|ID|PASS|detail via the engine println law.
 */
public class MainActivity extends Activity {

    static void row(String id, boolean ok, String detail) {
        System.out.println("F325|" + id + "|" + (ok ? "PASS" : "FAIL")
                           + "|" + detail);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        MyBox box = new MyBox(this);
        MyLP lp = new MyLP(77, 88);
        lp.tag = "held";
        box.setLayoutParams(lp);

        // P1 — the framework field read through the DEX ref class: the
        // written 77 must come back (ONE bare slot; the fabricated
        // qualified key answered 0 in PRE).
        row("P1-FRAMEWORK-WIDTH", box.readWidth() == 77,
            "readWidth=" + box.readWidth() + " want 77");

        // P2 — the height leg (the written 88 through the same shape).
        row("P2-FRAMEWORK-HEIGHT", box.readHeight() == 88,
            "readHeight=" + box.readHeight() + " want 88");

        // N1 — a REAL DEX-declared field keeps its qualified slot: the
        // tag written by the app DEX (iput, ref MyLP) round-trips.
        row("N1-DEX-DECLARED-TAG", "held".equals(box.readTag()),
            "readTag=" + box.readTag() + " want held");

        // N2 — the framework-typed ref (LinearLayout.LayoutParams, non-DEX
        // ref class) reads the same bare slot — unchanged face.
        ViewGroup.LayoutParams plain = box.getLayoutParams();
        row("N2-FRAMEWORK-REF", plain != null && plain.width == 77,
            "plain.width=" + (plain == null ? -999 : plain.width) + " want 77");
    }
}
