package com.probe.acts2;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;

/** F-145 probe leg B: the TOP-OF-STACK activity (green + marker text). */
public class SecondActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout v = new LinearLayout(this);
        v.setOrientation(LinearLayout.VERTICAL);
        v.setBackgroundColor(Color.rgb(0, 128, 0));
        TextView t = new TextView(this);
        t.setText("F145-TOP-OF-STACK");
        v.addView(t);
        setContentView(v);
        System.out.println("[F145] second-activity onCreate done");
    }
}
