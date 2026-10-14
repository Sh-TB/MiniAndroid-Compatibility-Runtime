package com.probe.f309;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;

/**
 * F-NEW-309 probe — asserts the layout_gravity inflation law by VALUE and
 * CLASS IDENTITY (not absence of exceptions):
 *   P4  the child of a DEX-defined container answers the container's OWN
 *       LayoutParams subclass (AOSP generateLayoutParams law)
 *   P1/P2  android:layout_gravity="start" resolves to the raw AXML int
 *          8388611 (0x00800003) — the value solitaire's NavigationView
 *          carries and the value the drawer checks read
 *   P3  "end" resolves to 8388613 (0x00800005)
 *   P5  isDrawerView(left) == true — the drawer check the v7 toggle runs
 *   N1  a child with NO layout_gravity keeps gravity 0 (AOSP getInt
 *       default — the honest AppBarLayout face, not a defect)
 *   N2  isDrawerView(plain) == false — the "not a drawer" condition is
 *       still reachable for gravity-0 children
 *   N3  EVERY child carries the container's LayoutParams class (AOSP
 *       generateLayoutParams applies to all children)
 * Rows print as F309|ID|PASS|detail via the engine println law.
 */
public class MainActivity extends Activity {

    static void row(String id, boolean ok, String detail) {
        System.out.println("F309|" + id + "|" + (ok ? "PASS" : "FAIL")
                           + "|" + detail);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.main);

        ImageView left = (ImageView) findViewById(R.id.drawer_left);
        ImageView right = (ImageView) findViewById(R.id.drawer_right);
        ImageView plain = (ImageView) findViewById(R.id.plain_child);

        ViewGroup.LayoutParams plp = left.getLayoutParams();
        row("P4-LPCLASS", plp instanceof DrawerBox.LayoutParams,
            "left lp class=" + plp.getClass().getName());

        if (plp instanceof DrawerBox.LayoutParams) {
            DrawerBox.LayoutParams lp = (DrawerBox.LayoutParams) plp;
            row("P1-START",
                (lp.gravity & 0x800007) == 0x800003,
                "left gravity=0x" + Integer.toHexString(lp.gravity));
            row("P2-EXACT", lp.gravity == 8388611,
                "left gravity==" + lp.gravity + " want 8388611 (start)");
            row("P5-ISDRAWER-LEFT", DrawerBox.isDrawerView(left),
                "isDrawerView(left) want true");

            DrawerBox.LayoutParams rp =
                (DrawerBox.LayoutParams) right.getLayoutParams();
            row("P3-END", rp.gravity == 8388613,
                "right gravity=" + rp.gravity + " want 8388613 (end)");

            ViewGroup.LayoutParams ppp = plain.getLayoutParams();
            boolean plainClass = ppp instanceof DrawerBox.LayoutParams;
            row("N3-PLAIN-CLASS", plainClass,
                "plain lp class=" + ppp.getClass().getName());
            if (plainClass) {
                DrawerBox.LayoutParams pp = (DrawerBox.LayoutParams) ppp;
                row("N1-ABSENT-DEFAULT", pp.gravity == 0,
                    "plain gravity=" + pp.gravity + " want 0");
                row("N2-ISDRAWER-PLAIN", !DrawerBox.isDrawerView(plain),
                    "isDrawerView(plain) want false");
            } else {
                row("N1-ABSENT-DEFAULT", false,
                    "skipped: plain lp not a DrawerBox.LayoutParams");
                row("N2-ISDRAWER-PLAIN", false,
                    "skipped: plain lp not a DrawerBox.LayoutParams");
            }
        } else {
            row("P1-START", false,
                "skipped: left lp=" + plp.getClass().getName());
            row("P2-EXACT", false,
                "skipped: left lp not a DrawerBox.LayoutParams");
            row("P3-END", false,
                "skipped: right lp not a DrawerBox.LayoutParams");
            row("P5-ISDRAWER-LEFT", false,
                "skipped: isDrawerView cannot see the gravity");
            row("N1-ABSENT-DEFAULT", false,
                "skipped: plain lp not a DrawerBox.LayoutParams");
            row("N2-ISDRAWER-PLAIN", false,
                "skipped: plain lp not a DrawerBox.LayoutParams");
        }
    }
}
