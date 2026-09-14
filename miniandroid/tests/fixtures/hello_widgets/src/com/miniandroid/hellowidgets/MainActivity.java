package com.miniandroid.hellowidgets;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ScrollView;
import android.widget.TextView;

/**
 * Hello Widgets — Advanced Hello World #3 (S38).
 *
 * Beyond plain text: an ImageView with a real APK drawable (EXP-067
 * setImageResource chain), an EditText the user can type into, a Button
 * whose click reads that text and mutates an echo TextView, a real
 * TableLayout grid (3 rows), and RelativeLayout children wired with
 * layout_below — all inflated from binary AXML + resources.arsc via
 * aapt2, all executed as real DEX bytecode.
 *
 * Known engine gap (R-NEW-336): post-click setText on the echo line
 * under a ScrollView root renders empty — registered honestly.
 *
 * Deterministic: no clocks, no randomness. License: MIT.
 */
public class MainActivity extends Activity implements View.OnClickListener {

    private EditText input;
    private TextView echo;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        input = (EditText) findViewById(R.id.w_input);
        echo = (TextView) findViewById(R.id.w_echo);
        Button btn = (Button) findViewById(R.id.w_btn_echo);
        btn.setOnClickListener(this);

        // Also prove the programmatic color path on the title.
        TextView title = (TextView) findViewById(R.id.w_title);
        title.setTextColor(0xFF4FC3F7);
    }

    @Override
    public void onClick(View v) {
        String typed = input.getText().toString();
        if (typed == null || typed.length() == 0) {
            typed = "(empty)";
        }
        echo.setText("echo: " + typed);
        echo.invalidate();
    }
}
