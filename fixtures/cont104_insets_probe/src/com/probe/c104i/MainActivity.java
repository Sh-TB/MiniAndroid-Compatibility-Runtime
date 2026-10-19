package com.probe.c104i;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.view.WindowInsets;
import android.widget.LinearLayout;

/**
 * CONT-104 F-NEW-442 probe — AOSP View.getRootWindowInsets attach law.
 *
 * Rows (all deterministic):
 *  [C104-PREATTACH] attached=false null=true   — AOSP law: unattached view
 *      (mAttachInfo == null) answers null root insets (View.java law).
 *  [C104-ATTACHED] attached=true nonnull=true  — AOSP law: an ATTACHED view
 *      answers NON-NULL root insets (mAttachInfo.mViewRootImpl.getWindowInsets).
 *      Real-APK oracle: chess androidx RecyclerView.onAttachedToWindow →
 *      ViewCompat.getRootWindowInsets → WindowInsetsCompat.toWindowInsetsCompat
 *      (Ln0/k1;.c, R8-inlined requireNonNull getClass()) NPE x8 → APP BOUNDARY.
 *  [C104-CLS] cls=class android.view.WindowInsets — identity of the answer.
 */
public class MainActivity extends Activity {

    public static class MyView extends View {
        public MyView(android.content.Context c) { super(c); }

        @Override
        protected void onAttachedToWindow() {
            super.onAttachedToWindow();
            WindowInsets wi = getRootWindowInsets();
            System.err.println("[C104-ATTACHED] attached=" + isAttachedToWindow()
                    + " nonnull=" + (wi != null));
            if (wi != null) {
                System.err.println("[C104-CLS] cls=" + wi.getClass().toString());
                // F-NEW-442b face — AOSP View.computeSystemWindowInsets law:
                // non-null insets input → NON-NULL result + emptied local rect.
                android.graphics.Rect local = new android.graphics.Rect(7, 8, 9, 10);
                WindowInsets result = computeSystemWindowInsets(wi, local);
                System.err.println("[C104-CSWI] same=" + (result == wi)
                        + " emptyLocal=" + local.isEmpty());
            }
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        View detached = new View(this);
        WindowInsets pre = detached.getRootWindowInsets();
        System.err.println("[C104-PREATTACH] attached=" + detached.isAttachedToWindow()
                + " null=" + (pre == null));
        LinearLayout root = new LinearLayout(this);
        root.addView(new MyView(this));
        setContentView(root);
    }
}
