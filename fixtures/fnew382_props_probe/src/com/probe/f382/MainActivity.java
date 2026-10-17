package com.probe.f382;

import android.app.Activity;
import android.os.Bundle;

/** F-NEW-382 regression lock (CONT-81): the ART identity properties.
 *  AOSP/ART truth: java.vm.name="Dalvik",
 *  java.specification.name="Dalvik Specification",
 *  java.runtime.name="Android Runtime". The libGDX SharedLibraryLoader
 *  platform law reads java.runtime.name.contains("Android Runtime").
 *  Negative: an unknown key answers null (no invented defaults). */
public class MainActivity extends Activity {
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        String vm = System.getProperty("java.vm.name");
        String spec = System.getProperty("java.specification.name");
        String rt = System.getProperty("java.runtime.name");
        String missing = System.getProperty("f382.absent.key");
        System.out.println("[F382-VM] " + vm);
        System.out.println("[F382-SPEC] " + spec);
        System.out.println("[F382-RT] " + rt
                + " android-law=" + String.valueOf(rt != null
                        && rt.contains("Android Runtime")));
        System.out.println("[F382-NEG] absent=" + missing);
    }
}
