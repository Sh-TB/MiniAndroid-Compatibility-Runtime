package com.miniandroid.f52nanlaw;
import android.app.Activity; import android.os.Bundle;
import android.widget.LinearLayout; import android.view.View;
import android.view.ViewGroup;
import android.graphics.Color;

// S69 F-135: Double/Float NaN / infinite / compare family — OpenJDK law.
// Each row renders GREEN (0xFF1B8A44) only when the called API answers per
// the OpenJDK contract; RED (0xFFD13438) otherwise. The independent verifier
// (verify_foundation.py) asserts each row's EXACT color, so a stub-false
// isNaN or a wrong compare ordering breaks a specific, named row.
//
// NaN / ±Inf are PRODUCED, not hard-coded: IEEE div semantics (0.0/0.0,
// 1.0/0.0, -1.0/0.0) — the same values real APK arithmetic (dooz Compose
// layout math, Vector-Pinball physics) feeds into these guards.
public class MainActivity extends Activity {
    static final int OK  = 0xFF1B8A44;
    static final int BAD = 0xFFD13438;

    View row(int color) {
        View v = new View(this);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 100);
        v.setLayoutParams(lp);
        v.setBackgroundColor(color);
        return v;
    }

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);

        double nan  = 0.0d / 0.0d;
        double inf  = 1.0d / 0.0d;
        double ninf = -1.0d / 0.0d;
        float  fnan = 0.0f / 0.0f;

        // 1. Double.isNaN(NaN) == true          (OpenJDK Double.java:1031 v!=v)
        root.addView(row(Double.isNaN(nan) ? OK : BAD));
        // 2. Double.isNaN(1.5) == false         (a plain double is not NaN)
        root.addView(row(!Double.isNaN(1.5d) ? OK : BAD));
        // 3. Double.isInfinite(+Inf) == true    (Double.java:1048 abs>MAX)
        root.addView(row(Double.isInfinite(inf) ? OK : BAD));
        // 4. Double.isInfinite(-Inf) == true    (sign-independent law)
        root.addView(row(Double.isInfinite(ninf) ? OK : BAD));
        // 5. Float.isNaN(NaN) == true           (OpenJDK Float.java:631 f!=f)
        root.addView(row(Float.isNaN(fnan) ? OK : BAD));
        // 6. Double.compare(1.0, 2.0) == -1     (numeric ordering)
        root.addView(row(Double.compare(1.0d, 2.0d) == -1 ? OK : BAD));
        // 7. Double.compare(NaN, 1.0) == +1     (Double.java:1538 NaN sorts
        //    above every value incl. +Inf — bits ordering law)
        root.addView(row(Double.compare(nan, 1.0d) == 1 ? OK : BAD));
        // 8. Float.compare(+0.0, -0.0) == +1    (bits law distinguishes ±0.0)
        root.addView(row(Float.compare(0.0f, -0.0f) == 1 ? OK : BAD));
        // 9. Float.compare(2.0f, 2.0f) == 0
        root.addView(row(Float.compare(2.0f, 2.0f) == 0 ? OK : BAD));

        setContentView(root);
    }
}
