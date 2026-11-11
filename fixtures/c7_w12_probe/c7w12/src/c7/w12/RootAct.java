package c7.w12;

import android.app.Activity;
import android.os.Bundle;

/** CODER7 WAVE-12 — the parent-chain launch targets (RootAct → MidAct →
 *  ChildAct, the addParentStack walk's AOSP parentActivityName chain).
 *  Each is a plain no-op activity: the startActivities / PendingIntent
 *  launch pipelines drain through them without verdict rows. */
public class RootAct extends Activity {
    @Override public void onCreate(Bundle icicle) {
        super.onCreate(icicle);
    }
}
