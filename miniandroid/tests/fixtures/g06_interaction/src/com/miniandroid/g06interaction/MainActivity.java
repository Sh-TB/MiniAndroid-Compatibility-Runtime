package com.miniandroid.g06interaction;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

/**
 * G06 §6 interaction fixture: the three touch laws on one screen, driven by
 * REAL DEX bytecode (this class is compiled by ECJ and dexed by D8; the
 * runtime contains no fixture-specific code):
 *
 *  1. btn_tap     — Button with a state-list background (pressed = red).
 *                   onClick increments a counter and updates tv_counter.
 *                   Proves: input → pressed state → click callback → state
 *                   mutation → render (visual: red mid-press, counter +1).
 *  2. btn_disabled — setEnabled(false) in onCreate. Per the AOSP disabled
 *                   law it consumes touches but never responds: no pressed
 *                   visual, no onClick. Proves: disabled gating.
 *  3. btn_long    — OnLongClickListener returning true (consumed).
 *                   Proves: 500ms long-press → onLongClick → text change.
 */
public class MainActivity extends Activity implements View.OnClickListener,
        View.OnLongClickListener {

    private Button btnTap;
    private Button btnDisabled;
    private Button btnLong;
    private TextView tvCounter;
    private TextView tvLong;
    private int taps = 0;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        btnTap = (Button) findViewById(R.id.btn_tap);
        btnDisabled = (Button) findViewById(R.id.btn_disabled);
        btnLong = (Button) findViewById(R.id.btn_long);
        tvCounter = (TextView) findViewById(R.id.tv_counter);
        tvLong = (TextView) findViewById(R.id.tv_long);

        btnTap.setOnClickListener(this);
        btnDisabled.setOnClickListener(this);
        btnDisabled.setEnabled(false);
        btnLong.setOnLongClickListener(this);
    }

    @Override
    public void onClick(View v) {
        if (v == btnTap) {
            taps = taps + 1;
            tvCounter.setText("Taps: " + taps);
        }
        // btn_disabled is disabled: reaching here would violate the law —
        // the counter never moves for it (guarded by the golden).
    }

    @Override
    public boolean onLongClick(View v) {
        if (v == btnLong) {
            tvLong.setText("LONG-CLICKED");
            return true;
        }
        return false;
    }
}
