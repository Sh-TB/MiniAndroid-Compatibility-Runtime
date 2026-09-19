package com.miniandroid.f32dimen;
import android.app.Activity; import android.os.Bundle; import android.view.View;
import android.widget.TextView; import android.widget.LinearLayout;
public class MainActivity extends Activity {
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        setContentView(R.layout.activity_main);
        // AOSP law: 100dp at density 2.625 (420dpi bucket) = 262px (262.5 floored).
        int px = getResources().getDimensionPixelSize(R.dimen.probe);
        TextView tv = new TextView(this);
        tv.setText("PX=" + px);
        ((LinearLayout) findViewById(R.id.dimroot)).addView(tv);
    }
}
