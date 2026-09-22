package org.miniandroid.gfx.l2_colortypes;

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
        ImageView a = new ImageView(this);
        a.setImageResource(R.drawable.pal);
        ImageView g = new ImageView(this);
        g.setImageResource(R.drawable.gray);
        ImageView r = new ImageView(this);
        r.setImageResource(R.drawable.rgb);
        ImageView ga = new ImageView(this);
        ga.setImageResource(R.drawable.ga);
        root.addView(a);
        root.addView(g);
        root.addView(r);
        root.addView(ga);
        setContentView(root);
    }
}
