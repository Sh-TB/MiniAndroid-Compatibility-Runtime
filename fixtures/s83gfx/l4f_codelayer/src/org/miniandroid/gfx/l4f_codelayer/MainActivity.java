package org.miniandroid.gfx.l4f_codelayer;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.LayerDrawable;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackground(new ColorDrawable(Color.rgb(18, 18, 18)));

        // code-level LayerDrawable: indigo pad + inset orange RING
        GradientDrawable pad = new GradientDrawable();
        pad.setColor(Color.rgb(48, 63, 159));
        GradientDrawable ring = new GradientDrawable();
        ring.setShape(GradientDrawable.RING);
        ring.setColor(Color.rgb(255, 112, 67));
        ring.setInnerRadius(50);
        ring.setThickness(25);
        LayerDrawable ld = new LayerDrawable(new Drawable[]{pad, ring});
        ld.setLayerInset(1, 100, 50, 100, 50);
        View v1 = new View(this);
        v1.setBackground(ld);
        root.addView(v1, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 300));

        // code-level GradientDrawable: rounded green rect + red stroke
        GradientDrawable rr = new GradientDrawable();
        rr.setColor(Color.rgb(0, 200, 83));
        rr.setCornerRadius(30f);
        rr.setStroke(10, Color.rgb(229, 57, 53));
        View v2 = new View(this);
        v2.setBackground(rr);
        root.addView(v2, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 300));

        setContentView(root);
    }
}
