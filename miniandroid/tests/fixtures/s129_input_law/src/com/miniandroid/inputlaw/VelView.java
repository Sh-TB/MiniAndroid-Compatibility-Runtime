package com.miniandroid.inputlaw;

import android.view.MotionEvent;
import android.view.VelocityTracker;
import android.view.View;
import android.widget.TextView;
import android.content.Context;
import android.util.AttributeSet;

/**
 * S129 (CAP-INPUT-108) fixture custom view: feeds every received event into
 * a VelocityTracker (obtain → addMovement(DOWN/MOVEs) → computeCurrentVelocity
 * at UP) exactly per the AOSP VelocityTracker Javadoc usage pattern, then
 * publishes the computed velocities on a TextView so the run manifest carries
 * the REAL DEX-computed values.
 */
public class VelView extends View {
    private VelocityTracker tracker;
    public TextView out;

    public VelView(Context c) {
        super(c);
    }

    public VelView(Context c, AttributeSet attrs) {
        super(c, attrs);
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        if (tracker == null) {
            tracker = VelocityTracker.obtain();
        }
        tracker.addMovement(event);
        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_UP: {
                tracker.computeCurrentVelocity(1000);
                float vx = tracker.getXVelocity();
                float vy = tracker.getYVelocity();
                if (out != null) {
                    out.setText("VY=" + (int) vy + ";VX=" + (int) vx);
                }
                tracker.recycle();
                tracker = null;
                return true;
            }
            case MotionEvent.ACTION_CANCEL:
                tracker.recycle();
                tracker = null;
                return true;
        }
        return true;
    }
}
