package com.probe.t563;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;

/** T16 F-NEW-563 guard-absorbability probe.
 *  OP1: System.loadLibrary("t563_missing") GUARDED by catch (UnsatisfiedLinkError).
 *       PASS = the engine raises the error through the normal exception
 *       machinery so app-side guards can absorb it (guarded paths continue).
 *  OP2: same load UNGUARDED, last op — if onCreate dies here, the ABSENCE
 *       of the UNGUARDED-THREW marker is itself the observation. */
public class MainActivity extends Activity {
    private StringBuilder R = new StringBuilder();
    private void paint() {
        TextView tv = new TextView(this);
        tv.setTextSize(13f);
        tv.setText(R.toString());
        setContentView(tv);
    }
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        R.append("T563-START\n");
        try {
            System.loadLibrary("t563_missing");
            R.append("OP1|UNEXPECTED-LOADED\n");
        } catch (UnsatisfiedLinkError e) {
            R.append("OP1|GUARD-ABSORBED|").append(e.getClass().getName()).append("\n");
        } catch (Throwable t) {
            R.append("OP1|WRONG-TYPE|").append(t.getClass().getName()).append("\n");
        }
        paint();
        System.loadLibrary("t563_missing");
        R.append("OP2|UNGUARDED-RETURNED\n");
        paint();
    }
}
