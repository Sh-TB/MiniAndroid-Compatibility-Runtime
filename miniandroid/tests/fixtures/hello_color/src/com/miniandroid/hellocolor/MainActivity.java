/*
 * MiniAndroid HELLO-COLOR fixture — M9 deliverable probe:
 * colorful Hello World + bitmap image + stroke-border boxes.
 *
 * Resource chain: real aapt2 binary AXML + resources.arsc; art is a
 * real PNG decoded from the APK zip. DEX dispatch coverage below:
 * setTextColor / setBackgroundColor / setText(int) on the inflated
 * tree (same values as AXML — API-path coverage, no visual change).
 *
 * No clocks, no randomness: identical invocations must produce
 * byte-identical frames. License: MIT.
 */
package com.miniandroid.hellocolor;

import android.app.Activity;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        setContentView(R.layout.activity_main);

        // DEX-dispatch coverage on the inflated tree (mirrors AXML values).
        LinearLayout root = (LinearLayout) findViewById(R.id.root);
        root.setBackgroundColor(0xFF0D47A1);   // deep blue (ARGB int path)

        TextView headline = (TextView) findViewById(R.id.hc_headline);
        headline.setTextColor(0xFF1565C0);     // blue

        TextView subtitle = (TextView) findViewById(R.id.hc_subtitle);
        subtitle.setTextColor(0xFF2E7D32);     // green

        TextView footer = (TextView) findViewById(R.id.hc_footer);
        footer.setTextColor(0xFFD84315);       // deep orange
    }
}
