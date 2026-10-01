package com.miniandroid.inputlaw;

import android.app.Activity;
import android.graphics.Rect;
import android.os.Bundle;
import android.view.TouchDelegate;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

/**
 * S129 input-law fixture (CAP-INPUT-108 + CAP-INPUT-110), driven by REAL DEX
 * bytecode (compiled by ECJ, dexed by D8; the runtime contains no
 * fixture-specific code):
 *
 *  1. CAP-INPUT-110 TouchDelegate — the classic AOSP pattern: the parent
 *     FrameLayout gets a TouchDelegate mapping a large rect (parent-local
 *     (300,300)-(1000,800)) onto the 48dp btn_delegate that sits at the
 *     top-left corner. A tap at (900,700) hits NO touchable child, so the
 *     AOSP fallback arm runs the parent's onTouchEvent → the delegate
 *     forwards the gesture to btn_delegate → its onClick fires. Proves:
 *     TouchDelegate ctor + setTouchDelegate + View.onTouchEvent consult
 *     (View.java L17060-17064) + delegate retarget + PerformClick.
 *  2. CAP-INPUT-108 VelocityTracker — VelView (custom view) feeds every
 *     dispatched event into VelocityTracker.obtain()/addMovement and calls
 *     computeCurrentVelocity(1000) at UP; the computed VY/VX land on
 *     tv_velocity. Driven with --swipe 100,1400,100,1592 (12 MOVEs @16ms =
 *     1000 px/s downward) through the canonical dispatcher law pipeline.
 */
public class MainActivity extends Activity {
    private TextView tvDelegate;
    private VelView vel;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        tvDelegate = (TextView) findViewById(R.id.tv_delegate);
        TextView tvVelocity = (TextView) findViewById(R.id.tv_velocity);
        Button btnDelegate = (Button) findViewById(R.id.btn_delegate);
        vel = (VelView) findViewById(R.id.vel);
        vel.out = tvVelocity;

        View parent = findViewById(R.id.parent);
        // Bounds in the OWNING view's local coordinates (AOSP ctor doc).
        // Direct call (no post): the rect constants are layout-independent.
        parent.setTouchDelegate(new TouchDelegate(new Rect(300, 300, 1000, 800),
                btnDelegate));

        btnDelegate.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                tvDelegate.setText("DELEGATE-CLICK");
            }
        });
    }
}
