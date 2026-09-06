package com.miniandroid.g07lifecycle;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

/**
 * G07 §7/§9/§10 lifecycle fixture. Every lifecycle callback APPENDS its
 * marker to tv_state through REAL DEX bytecode, so the visible text IS the
 * runtime's lifecycle record:
 *
 *   C = onCreate, S = onStart, R = onResume,
 *   P = onPause, H = onStop (stoP is P, so H = halt), D = onDestroy
 *
 * A self-limiting Handler chain (3 ticks @ 250ms) proves main-thread task
 * dispatch + callback ordering; btn_finish calls finish() so the runtime's
 * finish cascade (onPause → onStop → onDestroy) executes real DEX too.
 */
public class MainActivity extends Activity implements View.OnClickListener {

    private TextView tvState;
    private TextView tvTick;
    private String marks = "";
    private int ticks = 0;
    private Handler handler = new Handler();
    private Runnable tick = new Runnable() {
        public void run() {
            ticks = ticks + 1;
            tvTick.setText("Ticks: " + ticks);
            if (ticks < 3) {
                handler.postDelayed(this, 250);
            }
        }
    };

    private void mark(String m) {
        marks = marks + m;
        tvState.setText(marks);
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_lifecycle);
        tvState = (TextView) findViewById(R.id.tv_state);
        tvTick = (TextView) findViewById(R.id.tv_tick);
        Button finish = (Button) findViewById(R.id.btn_finish);
        finish.setOnClickListener(this);
        mark("C");
        handler.postDelayed(tick, 250);
    }

    @Override
    public void onStart() {
        super.onStart();
        mark("S");
    }

    @Override
    public void onResume() {
        super.onResume();
        mark("R");
    }

    @Override
    public void onPause() {
        super.onPause();
        mark("P");
    }

    @Override
    public void onStop() {
        super.onStop();
        mark("H");
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        mark("D");
    }

    @Override
    public void onClick(View v) {
        finish();
    }
}
