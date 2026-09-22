package org.miniandroid.gfx.l0_solid;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundDrawable(new ColorDrawable(Color.rgb(20, 40, 60)));
        TextView tv = new TextView(this);
        tv.setText("L0 SOLID BASELINE");
        tv.setTextColor(Color.WHITE);
        Button btn = new Button(this);
        btn.setText("TAP");
        root.addView(tv);
        root.addView(btn);
        setContentView(root);
    }
}
