/*
 * MiniAndroid HELLOWORLD-GOLDEN fixture — §27/§28 "simplest permanent
 * boot/render regression test". RESOURCE-BACKED variant (§36.E).
 *
 * Chain exercised, end to end, through REAL toolchain output
 * (aapt2 → ECJ → D8) and REAL DEX bytecode:
 *   APK load → binary manifest → Application → Activity.onCreate →
 *   class load → DEX execution →
 *     setContentView(R.layout.activity_main) →
 *     AXML inflation + resources.arsc @string/@id resolution →
 *     View tree (LinearLayout + 2 TextView + Button) →
 *     measure → layout → fonts (FreeType/HarfBuzz/FriBidi) →
 *     Canvas draw → software renderer → visible PNG frame.
 *
 * The display strings live in resources.arsc (res/values/strings.xml),
 * NOT in the DEX string pool — the validation gate proves this by
 * asserting the literals are present in resources.arsc and absent from
 * classes.dex (§36.E resource-backed discriminator).
 *
 * The findViewById + setGravity/setTextSize/setText(int) calls below
 * intentionally KEEP the DEX-dispatch coverage of EXT-AOSP-001/002
 * (gravity law + sp law) that the golden validation asserts from the
 * runtime log.
 *
 * No clocks, no randomness, no ambient state: identical invocations must
 * produce byte-identical frames (§28 deterministic-replay requirement).
 *
 * License: MIT.
 */
package com.miniandroid.helloworldgolden;

import android.app.Activity;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // REAL resource chain: R.layout constant → binary AXML →
        // LayoutInflater → resources.arsc (@string, @id, 28sp/14sp,
        // colors #141414/#606060).
        setContentView(R.layout.activity_main);

        // DEX-dispatch coverage on the inflated tree (same values as the
        // AXML attrs — no visual change, only API-path coverage).
        LinearLayout root = (LinearLayout) findViewById(R.id.root);
        root.setGravity(0x11);                       // Gravity.CENTER (EXT-AOSP-001)

        TextView hello = (TextView) findViewById(R.id.hello_headline);
        hello.setTextSize(28.0f);                    // sp law (EXT-AOSP-002)
        hello.setText(R.string.hello_headline);      // resource-id text dispatch

        TextView sub = (TextView) findViewById(R.id.hello_sub);
        sub.setTextSize(14.0f);                      // sp law (EXT-AOSP-002, 14sp)
        sub.setText(R.string.hello_subtitle);

        Button ok = (Button) findViewById(R.id.ok_button);
        ok.setText(R.string.ok_label);
    }
}
