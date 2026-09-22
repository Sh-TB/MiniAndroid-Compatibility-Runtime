package org.miniandroid.gfx.l4_xmldrawables;

import android.app.Activity;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        Button a = new Button(this);
        a.setText("SHAPE");
        a.setBackgroundResource(R.drawable.shape_round);
        Button g = new Button(this);
        g.setText("GRADIENT");
        g.setBackgroundResource(R.drawable.gradient_bar);
        Button l = new Button(this);
        l.setText("LAYER");
        l.setBackgroundResource(R.drawable.layer_card);
        Button s = new Button(this);
        s.setText("SELECTOR");
        s.setBackgroundResource(R.drawable.btn_state);
        root.addView(a);
        root.addView(g);
        root.addView(l);
        root.addView(s);
        setContentView(root);
    }
}
