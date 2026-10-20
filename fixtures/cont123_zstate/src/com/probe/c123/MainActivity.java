package com.probe.c123;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.LinearLayout;

/** CONT-123 W-01: F-NEW-192 elevation Z-state family probe (AOSP View.java
 * Z = elevation + translationZ; setZ keeps elevation and adjusts
 * translationZ). Live faces printed as C123- lines. */
public class MainActivity extends Activity {
    static int pass = 0, fail = 0;
    static void v(boolean ok, String id, String detail) {
        if (ok) { pass++; System.out.println("C123- " + id + " PASS " + detail); }
        else    { fail++; System.out.println("C123- " + id + " FAIL " + detail); }
    }
    @Override public void onCreate(Bundle icicle) {
        super.onCreate(icicle);
        LinearLayout root = new LinearLayout(this);
        View a = new View(this);
        root.addView(a);
        setContentView(root);
        a.setElevation(4.0f);
        float z0 = a.getZ();
        v(z0 == 4.0f, "Z01", "setElevation(4) -> getZ()=" + z0);
        a.setTranslationZ(3.0f);
        float z1 = a.getZ();
        float tz = a.getTranslationZ();
        v(z1 == 7.0f && tz == 3.0f, "Z02", "elevation+translationZ -> getZ()=" + z1 + " tZ=" + tz);
        a.setZ(10.0f);
        float tz2 = a.getTranslationZ();
        float el = a.getElevation();
        float z2 = a.getZ();
        v(Math.abs(tz2 - 6.0f) < 1e-4f && el == 4.0f && Math.abs(z2 - 10.0f) < 1e-4f,
          "Z03", "setZ(10): tZ=" + tz2 + " el=" + el + " z=" + z2);
        float el2 = a.getElevation();
        v(el2 == 4.0f, "Z04", "getElevation round-trip=" + el2);
        System.out.println("C123- VERDICT pass=" + pass + " fail=" + fail);
    }
}
