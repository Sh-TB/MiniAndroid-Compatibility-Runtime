package com.probe.f290;

import android.app.Activity;
import android.app.Dialog;
import android.content.Context;
import android.os.Bundle;
import android.view.ContextThemeWrapper;
import android.view.Window;
import android.view.WindowManager;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.List;

/**
 * F-NEW-290 probe — DIALOG OBJECT LAW (getWindow / getContext / Window attrs).
 *
 * AOSP android.app.Dialog.<init>: mWindow = new PhoneWindow(context) and
 * mContext are bound BEFORE any subclass ctor body runs — getWindow() and
 * getContext() NEVER answer null afterwards, for ANY Dialog receiver,
 * renamed or not (the receiver-identity principle of S134-F134A applied to
 * the Dialog family). The Window always carries its OWN
 * WindowManager.LayoutParams (getAttributes() never answers null) and
 * requestFeature() answers true while no content is installed.
 *
 * Discriminating scenario = the androidx compose DialogWrapper ctor shape
 * (composeStopwatch ground truth): a Dialog subclass whose ctor IMMEDIATELY
 * consumes getWindow(), iputs LayoutParams.type through it, configures the
 * window, and reads getContext(). On the pre-fix engine the virtual
 * getWindow() on the renamed subclass reached the bridge with the runtime
 * class, missed DialogShadow's platform-class gate, and the S71 ancestry
 * re-dispatch (Dialog→Context) stubbed NULL — the exact
 * "Dialog has no window" ISE face.
 *
 * Rows:
 *   DLG-WINDOW   getWindow() != null right after super(ctx)  (THE law)
 *   DLG-ATTRS    getWindow().getAttributes() != null
 *   DLG-SETATTRS lp.type write + setAttributes absorbed
 *   DLG-REQFEAT  requestFeature(FEATURE_NO_TITLE) == true
 *   DLG-CTX      getContext() != null (mContext ctor law)
 *   DLG-WSET     setBackgroundDrawableResource/setGravity/addFlags absorbed
 *   DLG-STABLE   second getWindow() answers the SAME Window (identity)
 *   SUMMARY      PASS iff all rows pass
 */
public class Main extends Activity {
    static List<String> out = new ArrayList<String>();
    static int pass = 0, fail = 0;

    static synchronized void row(String id, boolean ok, String detail) {
        out.add("F290|" + id + "|" + (ok ? "PASS" : "FAIL") + "|" + detail);
        if (ok) pass++; else fail++;
    }

    /** The androidx DialogWrapper ctor shape (compose ui window.Dialog). */
    static class WrapperDialog extends Dialog {
        WrapperDialog(Context c) {
            super(new ContextThemeWrapper(c, 16973840 /*Theme_Material_Dialog*/));
            Window w = getWindow();                       // AOSP: never null
            row("DLG-WINDOW", w != null, "getWindow!=null: " + (w != null));
            if (w != null) {
                WindowManager.LayoutParams lp = w.getAttributes();
                row("DLG-ATTRS", lp != null,
                    "getAttributes!=null: " + (lp != null));
                if (lp != null) {
                    try {
                        lp.type = WindowManager.LayoutParams.TYPE_APPLICATION;
                        w.setAttributes(lp);
                        row("DLG-SETATTRS", true, "type-write + setAttributes ok");
                    } catch (Throwable t) {
                        row("DLG-SETATTRS", false, t.getClass().getName());
                    }
                }
                try {
                    boolean rf = w.requestFeature(Window.FEATURE_NO_TITLE);
                    row("DLG-REQFEAT", rf, "requestFeature(NO_TITLE)=" + rf);
                } catch (Throwable t) {
                    row("DLG-REQFEAT", false, t.getClass().getName());
                }
                Context wc = getContext();                // AOSP: ctor arg
                row("DLG-CTX", wc != null, "getContext!=null: " + (wc != null));
                try {
                    w.setBackgroundDrawableResource(17170445);
                    w.setGravity(17 /*CENTER*/);
                    w.addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);
                    row("DLG-WSET", true, "bg/gravity/flags absorbed");
                } catch (Throwable t) {
                    row("DLG-WSET", false, t.getClass().getName());
                }
                row("DLG-STABLE", getWindow() == w,
                    "getWindow identity stable: " + (getWindow() == w));
            }
        }
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        out.clear(); pass = 0; fail = 0;
        TextView tv = new TextView(this);
        setContentView(tv);
        try {
            new WrapperDialog(this);
        } catch (Throwable t) {
            row("CTOR-EXC", false,
                t.getClass().getName() + ": " + t.getMessage());
        }
        StringBuilder sb = new StringBuilder();
        for (String s : out) sb.append(s).append('\n');
        String summary = "F290|SUMMARY|"
                + (fail == 0 && pass >= 7 ? "PASS" : "FAIL")
                + "| " + pass + " pass, " + fail + " fail";
        sb.append(summary);
        tv.setText(sb.toString());
        try {
            java.io.FileOutputStream fos =
                openFileOutput("f290_results.txt", MODE_PRIVATE);
            fos.write(sb.toString().getBytes("UTF-8"));
            fos.close();
        } catch (Throwable t2) { }
    }
}
