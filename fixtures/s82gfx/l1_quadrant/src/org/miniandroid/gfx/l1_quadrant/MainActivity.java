package org.miniandroid.gfx.l1_quadrant;

import android.app.Activity;
import android.os.Bundle;
import android.widget.ImageView;
import android.widget.LinearLayout;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        ImageView iv = new ImageView(this);
        iv.setImageResource(R.drawable.quadrant);
        root.addView(iv);
        setContentView(root);
    }
}
