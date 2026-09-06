package com.miniandroid.g08nav;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

/**
 * G08: the SECOND Activity. REAL DEX class — launched through the Activity
 * system (Intent → component resolution → instantiation → onCreate). Reads
 * the launch Intent's extras through getIntent() and shows them; its back
 * button sets a result and finishes, returning to MainActivity.
 */
public class SecondActivity extends Activity implements View.OnClickListener {

    private TextView tvExtra;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_second);
        tvExtra = (TextView) findViewById(R.id.tv_extra);
        Button back = (Button) findViewById(R.id.btn_back);
        back.setOnClickListener(this);
        Intent launch = getIntent();
        String greet = launch.getStringExtra("greet");
        int num = launch.getIntExtra("num", 0);
        tvExtra.setText(greet + ":" + num);
    }

    @Override
    public void onClick(View v) {
        setResult(-1, new Intent());
        finish();
    }
}
