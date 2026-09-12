/*
 * MiniAndroid HELLO-SMOKE fixture — the Advanced HelloWorld /
 * Compatibility Smoke App (S23 Priority 2).
 *
 * One app, one screen, one DEX file exercising the compatibility chain
 * end to end. After ANY runtime change, running this fixture answers:
 * "DEX → framework → resources → layout → render → input → state" —
 * alive or broken?
 *
 * Coverage map (each line = one mission requirement):
 *   Activity lifecycle      onCreate + onResume update smoke_lifecycle
 *   Multiple views          TextView / Button / LinearLayout / FrameLayout
 *   Layout + measurement    inflated AXML tree, wrap/match + fixed sizes
 *   margins/padding/gravity @dimen padding, box margin + layout_gravity
 *   resource lookup         @string / @color / @dimen via aapt2 arsc,
 *                           plus the getString(R.string) API path
 *   click + state change    Button onClick: counter++ → setText
 *   invalidate/requestLayout the click handler calls both on the box
 *   visible state change    counter line changes between the two frames
 *   storage/state path      SharedPreferences write+read round-trip
 *
 * Deterministic: no clocks, no randomness. License: MIT.
 */
package com.miniandroid.hellosmoke;

import android.app.Activity;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity
        implements View.OnClickListener {

    private TextView counter;
    private TextView storageEcho;
    private TextView box;
    private FrameLayout boxHost;
    private SharedPreferences prefs;
    private int count = 0;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // findViewById on the inflated tree (AXML + arsc chain).
        LinearLayout root = (LinearLayout) findViewById(R.id.root);
        TextView title = (TextView) findViewById(R.id.smoke_title);
        TextView echo = (TextView) findViewById(R.id.smoke_echo);
        boxHost = (FrameLayout) findViewById(R.id.smoke_box_host);
        box = (TextView) findViewById(R.id.smoke_box);
        counter = (TextView) findViewById(R.id.smoke_counter);
        storageEcho = (TextView) findViewById(R.id.smoke_storage);
        TextView lifecycleLine = (TextView) findViewById(R.id.smoke_lifecycle);
        Button button = (Button) findViewById(R.id.smoke_button);

        // API-path resource lookup (mirrors the AXML @string chain).
        echo.setText(getString(R.string.smoke_api_string));

        // API-path color/dimension constants (ARGB int + pixel conversions
        // are the runtime's contract — same values as the AXML attributes).
        title.setTextColor(0xFF0B7A46);
        root.setPadding(20, 20, 20, 20);

        // Storage/state path: read whatever an earlier state wrote.
        prefs = getSharedPreferences("smoke_state", 0);
        int saved = prefs.getInt("count", -1);
        storageEcho.setText("pref_at_launch=" + (saved < 0 ? "none" : saved));

        // Input → state: the click handler is the smoke trigger.
        button.setOnClickListener(this);

        // Deterministic initial render: count=0, lifecycle=onCreate.
        counter.setText("count=0");
        lifecycleLine.setText("lifecycle=onCreate");
    }

    @Override
    public void onResume() {
        super.onResume();
        // Lifecycle ordering evidence: onResume runs AFTER onCreate.
        TextView lifecycleLine = (TextView) findViewById(R.id.smoke_lifecycle);
        lifecycleLine.setText("lifecycle=onResume");
    }

    @Override
    public void onClick(View v) {
        count = count + 1;

        // State mutation → visible render change.
        counter.setText("count=" + count);

        // The box shifts on the declared margin/gravity law and the
        // re-measure gate (R-NEW-302): invalidate + requestLayout.
        box.setText("box#" + count);
        box.requestLayout();
        box.invalidate();

        // Storage round-trip within the run: write then read back.
        // Editor chaining is the real AOSP usage pattern.
        prefs.edit()
                .putInt("count", count)
                .putString("last", "clicked")
                .apply();
        int roundTrip = prefs.getInt("count", -1);
        storageEcho.setText("pref_now=" + roundTrip);
    }
}
