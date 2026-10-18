package com.probe.clinit1;

import android.app.Activity;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.View;

// CONT-87 Track 1 fixture (F-NEW-395): the smallest deterministic DEX-level
// reproduction set for the deferred-exception-inside-<clinit> laws.
//
// Rows (stderr) are the evidence surface; the canvas band only mirrors them:
//   [C87-CC-*]  ClinitCatch: forName("probe.does.not.Exist") wrapped in an
//               in-clinit catch-all — deferred CNFE raised at an invoke that
//               IS covered by the clinit frame's own try range. Expected law
//               (JVMS 5.5 / AOSP): the catch observes ClassNotFoundException,
//               clinit completes, class initializes.
//   [C87-AC-*]  ClinitArithCatch: deferred ArithmeticException (ARITH-LIT8
//               raise site) inside an in-clinit catch-all — same law, second
//               raise origin.
//   [C87-UT-*]  ClinitThrow: UNCAUGHT clinit throw — honesty law: [CLASS_INIT]
//               FAILED + F-NEW-215 erroneous state; first active use observed
//               by the caller (recorded verbatim), second use per JVMS 5.5
//               (NoClassDefFoundError family).
//   [C87-OK]    sanity static-init row.
public class MainActivity extends Activity {
    private static int rows = 0;
    private static String ccState = "PENDING";
    private static String acState = "PENDING";
    private static String utState = "PENDING";
    private static String ut2State = "PENDING";

    static class ClinitCatch {
        static String result;
        static {
            System.out.println("[C87-CC-BEGIN]");
            try {
                Class.forName("probe.does.not.Exist");
                System.out.println("[C87-CC-NOTHROW]");
            } catch (Throwable t) {
                result = "caught:" + t.getClass().getName();
                System.out.println("[C87-CC-CAUGHT] " + result);
            }
            System.out.println("[C87-CC-END]");
        }
    }

    static class ClinitArithCatch {
        static int v = 7;
        static {
            System.out.println("[C87-AC-BEGIN]");
            try {
                int ten = 10;
                v = ten / 0;
                System.out.println("[C87-AC-NOTHROW]");
            } catch (Throwable t) {
                System.out.println("[C87-AC-CAUGHT] " + t.getClass().getName());
            }
            System.out.println("[C87-AC-END]");
        }
    }

    static class ClinitThrow {
        static int s = 42;
        static {
            System.out.println("[C87-UT-BEGIN]");
            int ten = 10;
            int z = ten / 0;
            System.out.println("[C87-UT-END] z=" + z);
        }
    }

    static class ClinitOk {
        static final String S = "ok";
    }

    @Override public void onCreate(Bundle b) {
        super.onCreate(b);
        System.out.println("[C87-VERSION] pkg=com.probe.clinit1 wave=CONT-87");
        System.out.println("[C87-OK] " + ClinitOk.S);
        rows++;
        try {
            ccState = String.valueOf(ClinitCatch.result);
            System.out.println("[C87-CC-STATE] " + ccState);
        } catch (Throwable t) {
            ccState = "main-caught:" + t.getClass().getName();
            System.out.println("[C87-CC-STATE] " + ccState);
        }
        rows++;
        try {
            System.out.println("[C87-AC-STATE] v=" + ClinitArithCatch.v);
            acState = "clinit-ok";
        } catch (Throwable t) {
            acState = "main-caught:" + t.getClass().getName();
            System.out.println("[C87-AC-STATE] " + acState);
        }
        rows++;
        try {
            System.out.println("[C87-UT-STATE] s=" + ClinitThrow.s);
            utState = "clinit-ok";
        } catch (Throwable t) {
            utState = "main-caught:" + t.getClass().getName();
            System.out.println("[C87-UT-STATE] " + utState);
        }
        rows++;
        try {
            System.out.println("[C87-UT2-STATE] s=" + ClinitThrow.s);
            ut2State = "clinit-ok";
        } catch (Throwable t) {
            ut2State = "main-caught:" + t.getClass().getName();
            System.out.println("[C87-UT2-STATE] " + ut2State);
        }
        rows++;
        System.out.println("[C87-DONE] rows=" + rows + " cc=" + ccState
            + " ac=" + acState + " ut=" + utState + " ut2=" + ut2State);
        setContentView(new ProbeView(this));
    }

    private class ProbeView extends View {
        ProbeView(android.content.Context c) { super(c); }
        @Override public void draw(Canvas canvas) {
            super.draw(canvas);
            canvas.drawColor(Color.rgb(12, 16, 24));
            Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
            p.setColor(Color.WHITE);
            p.setTextSize(34f);
            canvas.drawText("C87 clinit probe", 40f, 120f, p);
            p.setTextSize(26f);
            p.setColor(ccState.startsWith("caught:") ? Color.rgb(80, 220, 120)
                                                     : Color.rgb(230, 90, 90));
            canvas.drawText("CC  " + ccState, 40f, 220f, p);
            p.setColor(acState.equals("clinit-ok") ? Color.rgb(80, 220, 120)
                                                   : Color.rgb(230, 90, 90));
            canvas.drawText("AC  " + acState, 40f, 300f, p);
            p.setColor(utState.startsWith("main-caught") ? Color.rgb(80, 220, 120)
                                                         : Color.rgb(230, 90, 90));
            canvas.drawText("UT  " + utState, 40f, 380f, p);
            p.setColor(ut2State.startsWith("main-caught") ? Color.rgb(80, 220, 120)
                                                          : Color.rgb(230, 90, 90));
            canvas.drawText("UT2 " + ut2State, 40f, 460f, p);
        }
        @Override protected void onDraw(Canvas canvas) { draw(canvas); }
    }
}
