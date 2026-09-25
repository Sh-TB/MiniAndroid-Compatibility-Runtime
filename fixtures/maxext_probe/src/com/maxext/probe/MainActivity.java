package com.maxext.probe;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.lang.reflect.Field;

public class MainActivity extends Activity {
    LinearLayout root;
    String postedRan = "not-run";
    String frontRan = "not-run";
    StringBuilder order = new StringBuilder("-");

    void line(String s) {
        TextView tv = new TextView(this);
        tv.setText(s);
        root.addView(tv);
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        setContentView(root);
        line("P0 fixture-start");
        probeWidth();
        probeReflection();
        probeHandler();
        line("PEND fixture-end");
    }

    // U-004: View.getWidth lifecycle (AOSP law: getWidth() = mRight - mLeft)
    void probeWidth() {
        View v = new View(this);
        line("W1 new w=" + v.getWidth() + " mw=" + v.getMeasuredWidth());
        v.measure(View.MeasureSpec.makeMeasureSpec(200, View.MeasureSpec.EXACTLY),
                  View.MeasureSpec.makeMeasureSpec(100, View.MeasureSpec.EXACTLY));
        line("W2 measured w=" + v.getWidth() + " mw=" + v.getMeasuredWidth());
        v.layout(10, 20, 210, 120);
        line("W3 laid-out w=" + v.getWidth() + " h=" + v.getHeight());
        View g = new View(this);
        g.setVisibility(View.GONE);
        g.layout(0, 0, 50, 30);
        line("W4 gone-layout w=" + g.getWidth() + " vis=" + g.getVisibility());
        View z = new View(this);
        z.layout(5, 5, 5, 5);
        line("W5 zero-frame w=" + z.getWidth());
    }

    // U-005: reflection Field.get static/instance semantics
    void probeReflection() {
        try {
            Field f = Host.class.getDeclaredField("primStatic");
            line("R1 static-prim=" + f.get(null));
        } catch (Throwable t) { line("R1 threw=" + t.getClass().getSimpleName()); }
        try {
            Field f = Host.class.getDeclaredField("objStatic");
            line("R2 static-obj=" + (f.get(null) != null ? "nonnull" : "null"));
        } catch (Throwable t) { line("R2 threw=" + t.getClass().getSimpleName()); }
        try {
            Field f = Host.class.getDeclaredField("FINAL_STATIC");
            line("R3 static-final=" + f.get(null));
        } catch (Throwable t) { line("R3 threw=" + t.getClass().getSimpleName()); }
        try {
            Field f = Host.class.getDeclaredField("primInst");
            line("R4 instance=" + f.get(this));
        } catch (Throwable t) { line("R4 threw=" + t.getClass().getSimpleName()); }
        try {
            Field f = Host.class.getDeclaredField("primInst");
            f.get(null);
            line("R5 null-recv=NO-THROW");
        } catch (NullPointerException e) { line("R5 null-recv=NPE(correct)"); }
          catch (Throwable t) { line("R5 threw=" + t.getClass().getSimpleName()); }
        try {
            Host.class.getDeclaredField("no_such_field");
            line("R6 missing=NO-THROW(divergence)");
        } catch (NoSuchFieldException e) { line("R6 missing=NSFE(correct)"); }
          catch (Throwable t) { line("R6 threw=" + t.getClass().getSimpleName()); }
        try {
            Field f = Host.class.getField("inheritedStatic");
            line("R7 inherited=" + f.get(null));
        } catch (Throwable t) { line("R7 threw=" + t.getClass().getSimpleName()); }
        try {
            Field f = Host.class.getDeclaredField("primStatic");
            f.set(null, 43);
            line("R8 after-set=" + Host.primStatic);
        } catch (Throwable t) { line("R8 threw=" + t.getClass().getSimpleName()); }
        try {
            Field f = Host.class.getDeclaredField("primInst");
            line("R9 mods=" + f.getModifiers());
        } catch (Throwable t) { line("R9 threw=" + t.getClass().getSimpleName()); }
        try {
            Field f = Host.class.getField("no_such_field");
            line("R10 getField=" + (f == null ? "NULL" : "nonnull"));
        } catch (NoSuchFieldException e) { line("R10 getField=NSFE(correct)"); }
          catch (Throwable t) { line("R10 threw=" + t.getClass().getSimpleName()); }
        try {
            Field f = Host.class.getDeclaredField("boxedStatic");
            Object o = f.get(null);
            line("R11 boxed=" + (o == null ? "NULL" : o.toString()));
        } catch (Throwable t) { line("R11 threw=" + t.getClass().getSimpleName()); }
        line("R12 direct=" + Host.boxedStatic + " prim=" + Host.primStatic);
    }

    // U-003: Handler / Looper materialization
    void probeHandler() {
        Looper ml = Looper.getMainLooper();
        line("H1 mainLooper=" + (ml == null ? "NULL" : "nonnull"));
        try {
            Handler h = new Handler(ml == null ? Looper.myLooper() : ml);
            line("H2 handler=OK");
            h.post(new Runnable() { public void run() { postedRan = "RAN"; order.append("P"); } });
            h.postAtFrontOfQueue(new Runnable() { public void run() { frontRan = "RAN"; order.append("F"); } });
            line("H5 order-so-far=" + order);
        } catch (Throwable t) { line("H2 threw=" + t.getClass().getSimpleName()); }
    }

    @Override protected void onResume() {
        super.onResume();
        line("H3 posted=" + postedRan);
        line("H4 front=" + frontRan);
        line("H6 order-final=" + order);
    }
}
