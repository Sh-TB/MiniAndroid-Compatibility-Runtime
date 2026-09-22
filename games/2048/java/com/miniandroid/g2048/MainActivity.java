package com.miniandroid.g2048;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;

/** 2048 — real Android app for the MiniAndroid runtime (S80).
 *  Classic Gabriele Cirulli mechanics (MIT), board rendered by a custom
 *  View. Static state (runtime object-identity law); advances purely on
 *  button taps — no timer needed. */
public class MainActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        findViewById(R.id.btn_left).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { Board2048View.move(0); }
        });
        findViewById(R.id.btn_up).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { Board2048View.move(1); }
        });
        findViewById(R.id.btn_right).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { Board2048View.move(2); }
        });
        findViewById(R.id.btn_down).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { Board2048View.move(3); }
        });
    }
}
