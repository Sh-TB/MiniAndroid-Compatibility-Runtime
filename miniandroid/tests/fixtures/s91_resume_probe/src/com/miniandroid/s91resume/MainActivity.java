package com.miniandroid.s91resume;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.View;

/**
 * S91 RESUME PROBE — sandbox state save/restore law, minimal face.
 *
 * Run N (fresh --data-root):  reads runs=0  -> RED   screen, "runs=0 first"
 * Run N (same --data-root):   reads runs>=1 -> GREEN screen, "runs=<n> restored"
 *
 * Single semantic law under test:
 *   SharedPreferences.putInt/commit persists to <data-root>/<pkg>/shared_prefs
 *   and a LATER PROCESS reading getInt through the SAME interface path
 *   observes the persisted value (AOSP SharedPreferencesImpl contract).
 */
public class MainActivity extends Activity {

    static int observedRuns = -1;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        SharedPreferences sp = getSharedPreferences("resume", Context.MODE_PRIVATE);
        observedRuns = sp.getInt("runs", 0);
        SharedPreferences.Editor ed = sp.edit();
        ed.putInt("runs", observedRuns + 1);
        ed.commit();
        setContentView(new ProbeView(this));
    }

    static class ProbeView extends View {
        ProbeView(android.content.Context c) { super(c); }

        @Override
        protected void onDraw(Canvas canvas) {
            canvas.drawColor(observedRuns > 0 ? Color.rgb(0, 160, 0)
                                              : Color.rgb(200, 40, 40));
            Paint p = new Paint();
            p.setColor(Color.WHITE);
            p.setTextSize(60);
            canvas.drawText("runs=" + observedRuns
                            + (observedRuns > 0 ? " RESTORED" : " FIRST"),
                            80, 300, p);
        }
    }
}
