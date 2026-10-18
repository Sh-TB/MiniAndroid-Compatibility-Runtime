package com.probe.c94p;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import android.graphics.Color;

/**
 * CONT-94 F-NEW-396 fixture: getParentActivity() live-identity law.
 *
 * Reproduces the identity break that killed the official Telegram login UI:
 * the runtime's getParentActivity law answered a FABRICATED object of a
 * hard-coded class (right class descriptor, wrong instance, uninitialized
 * fields) instead of THE LIVE ACTIVITY. The app-visible face:
 * instanceof passes, every field read on the result is null/default.
 *
 * Rows (stderr + on-screen):
 *   [C94-PROBE] identity=THIS marker=C94-MARKER-V1  — live identity (AOSP law)
 *   [C94-PROBE] identity=OTHER-SAME-CLASS marker=.. — fabricated same-class
 *   [C94-PROBE] identity=OTHER-CLASS cls=..          — fabricated other-class
 *   [C94-PROBE] parent=NULL                          — not-attached contract
 */
public class MainActivity extends Activity {
    public String marker;
    private String verdict;

    private void record(String s) { verdict = s; }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        this.marker = "C94-MARKER-V1";
        Activity a = getParentActivity();
        if (a == null) {
            record("[C94-PROBE] parent=NULL (not-attached contract)");
        } else if (a == this) {
            record("[C94-PROBE] identity=THIS marker=" + ((MainActivity) a).marker);
        } else {
            try {
                MainActivity m = (MainActivity) a;
                record("[C94-PROBE] identity=OTHER-SAME-CLASS marker=" + m.marker);
            } catch (ClassCastException cce) {
                record("[C94-PROBE] identity=OTHER-CLASS cls=" + a.getClass().getName());
            }
        }
        System.err.println(verdict);
        TextView tv = new TextView(this);
        tv.setText(verdict == null ? "[C94-PROBE] (no verdict)" : verdict);
        tv.setTextSize(28f);
        tv.setTextColor(Color.BLACK);
        setContentView(tv);
    }

    public Activity getParentActivity() {
        // DEX body must never run: the runtime's getParentActivity law serves
        // this call at the bridge layer (same name-keyed intercept Telegram's
        // BaseFragment.getParentActivity hits). Returns null defensively.
        return null;
    }
}
