package org.miniandroid.gfx.l4d_ninepatch;

import android.app.Activity;
import android.os.Bundle;
import android.widget.LinearLayout;

// S83-GFX-BASE: NinePatchDrawable fixture — a 24x12 .9.png (teal content,
// red stripe at src x=4..5, blue stripe at src x=18..19) stretched to a
// full-screen background. The stretch law keeps the red/blue stripes at
// their marker-driven positions and expands only the marker zones.
public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout root = new LinearLayout(this);
        root.setBackgroundResource(org.miniandroid.gfx.l4d_ninepatch.R.drawable.btn);
        setContentView(root);
    }
}
