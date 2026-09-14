package com.miniandroid.scrollmin;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

/** R-NEW-336 minimal repro: ScrollView root, one TextView + one Button, nothing else. */
public class MainActivity extends Activity implements View.OnClickListener {
    private TextView target;
    private int n = 0;

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        target = (TextView) findViewById(R.id.s_target);
        Button btn = (Button) findViewById(R.id.s_btn);
        btn.setOnClickListener(this);
    }

    @Override public void onClick(View v) {
        n++;
        target.setText("clicked " + n);
    }
}
