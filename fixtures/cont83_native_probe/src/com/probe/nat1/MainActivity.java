package com.probe.nat1;

import android.app.Activity;
import android.os.Bundle;

// CONT-83 F-NEW-387 probe. Rows:
//   [NAT1-VERSION]   identity
//   [NAT1-ADD]       add3(2,3,4) via the real dlopen'd lib (expect 9)
//   [NAT1-MATH]      mathCheck(9) via the REAL libm dependency (expect 9)
//   [NAT1-NEG]       loading the unresolvable lib must fail LOUDLY
//                    (UnsatisfiedLinkError) — honest block, never silence
public class MainActivity extends Activity {
    @Override public void onCreate(Bundle b) {
        super.onCreate(b);
        System.out.println("[NAT1-VERSION] pkg=com.probe.nat1 wave=CONT-83");
        try {
            int r = NativeProbe.add3(2, 3, 4);
            int m = NativeProbe.mathCheck(9);
            System.out.println("[NAT1-ADD] add3=" + r);
            System.out.println("[NAT1-MATH] mathCheck=" + m);
        } catch (Throwable t) {
            System.out.println("[NAT1-ADD] FAILED " + t.getClass().getSimpleName());
        }
        try {
            Class.forName("com.probe.nat1.NativeShadow", true,
                          NativeProbe.class.getClassLoader());
            System.out.println("[NAT1-NEG] unexpectedly loaded");
        } catch (Throwable t) {
            System.out.println("[NAT1-NEG] " + t.getClass().getSimpleName());
        }
        System.out.println("[NAT1-DONE] complete");
    }
}
