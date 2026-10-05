package com.probe.armonly;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;

/**
 * LAW-001 ARM-only scope probe (ABI FIRST TEST LAW fixture).
 *
 * Purpose: this APK ships ONLY ARM native trees (lib/armeabi-v7a +
 * lib/arm64-v8a) and no x86/x86_64 tree. Under LAW-001 — the FIRST test
 * law — the unknown-APK preflight gate must classify it
 * ABI_OUT_OF_SCOPE (SKIP) from the real lib/<abi>/ entries BEFORE any
 * install/launch attempt, and the case must land in the SKIP statistics
 * bucket, never in the could-not-run (failure) bucket.
 *
 * The Activity itself is intentionally ordinary: if the scope gate were
 * ever removed, this app would install, launch, and then honestly fail on
 * its native path (the .so payloads are deterministic fixture stubs, not
 * host-executable code) — which is exactly the pre-LAW-001 behavior the
 * law exists to avoid wasting time on.
 */
public class MainActivity extends Activity {
    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        TextView tv = new TextView(this);
        tv.setText("LAW-001 ARM-only scope probe\n"
                + "native trees: armeabi-v7a, arm64-v8a\n"
                + "expected gate verdict: ABI_OUT_OF_SCOPE (SKIP)");
        setContentView(tv);
    }
}
