package org.miniandroid.gfx.l4c_vector;

import android.app.Activity;
import android.os.Bundle;
import android.widget.LinearLayout;

// S83-GFX-BASE §14: VectorDrawable pixel fixture.
//   path1: green rect (viewport 24x24 → bounds)
//   path2: even-odd red ring (outer rect minus inner rect = hole)
//   path3: white circle via ARC commands (endpoint parameterization)
// The vector is the window background of a full-screen view.
public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout root = new LinearLayout(this);
        root.setBackgroundResource(org.miniandroid.gfx.l4c_vector.R.drawable.ic_vector);
        setContentView(root);
    }
}
