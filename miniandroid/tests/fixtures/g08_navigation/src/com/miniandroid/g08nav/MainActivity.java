package com.miniandroid.g08nav;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

/**
 * G08 §11-14: the LAUNCHER activity of a two-Activity app. REAL DEX:
 * btn_launch sends an explicit Intent (setClassName) carrying a String
 * extra and an int extra; btn_launch_result starts SecondActivity
 * for-result with requestCode 42; onActivityResult records the delivery.
 */
public class MainActivity extends Activity implements View.OnClickListener {

    private TextView tvMsg;
    private String received = "";

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main_g08);
        tvMsg = (TextView) findViewById(R.id.tv_msg);
        Button launch = (Button) findViewById(R.id.btn_launch);
        Button launchResult = (Button) findViewById(R.id.btn_launch_result);
        launch.setOnClickListener(this);
        launchResult.setOnClickListener(this);
    }

    @Override
    public void onClick(View v) {
        if (v.getId() == R.id.btn_launch) {
            Intent i = new Intent();
            i.setClassName("com.miniandroid.g08nav",
                           "com.miniandroid.g08nav.SecondActivity");
            i.putExtra("greet", "hello");
            i.putExtra("num", 7);
            startActivity(i);
        } else if (v.getId() == R.id.btn_launch_result) {
            Intent i = new Intent();
            i.setClassName("com.miniandroid.g08nav",
                           "com.miniandroid.g08nav.SecondActivity");
            startActivityForResult(i, 42);
        }
    }

    @Override
    public void onActivityResult(int requestCode, int resultCode, Intent data) {
        received = received + "R" + requestCode + ":" + resultCode;
        tvMsg.setText(received);
    }
}
