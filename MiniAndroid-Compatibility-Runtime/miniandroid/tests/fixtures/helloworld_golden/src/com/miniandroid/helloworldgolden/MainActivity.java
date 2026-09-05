/*
 * MiniAndroid HELLOWORLD-GOLDEN fixture — §27/§28 "simplest permanent
 * boot/render regression test".
 *
 * Chain exercised, end to end, through REAL toolchain output (ECJ → D8)
 * and REAL DEX bytecode:
 *   APK load → manifest parse → Application → Activity.onCreate →
 *   class load → DEX execution → View construction (LinearLayout +
 *   TextView + Button) → measure → layout → fonts (real shaping via
 *   FreeType/HarfBuzz/FriBidi) → Canvas draw → software renderer →
 *   visible PNG frame.
 *
 * No clocks, no randomness, no ambient state: identical invocations must
 * produce byte-identical frames (§28 deterministic-replay requirement).
 *
 * License: MIT.
 */
package com.miniandroid.helloworldgolden;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);          // 1 = VERTICAL
        root.setGravity(0x11);                               // Gravity.CENTER

        TextView hello = new TextView(this);
        hello.setText("Hello, MiniAndroid!");
        hello.setTextSize(28.0f);
        hello.setTextColor(Color.rgb(20, 20, 20));

        TextView sub = new TextView(this);
        sub.setText("real APK - real DEX - real render");
        sub.setTextSize(14.0f);
        sub.setTextColor(Color.rgb(96, 96, 96));

        Button ok = new Button(this);
        ok.setText("OK");

        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-2, -2);
        root.addView(hello, lp);
        root.addView(sub, lp);
        root.addView(ok, lp);

        setContentView(root);
    }
}
