package com.probe.c7act;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.os.Bundle;

/** W3-A1/A5: the for-result target. Records the caller identity law
 *  (getCallingActivity/getCallingPackage) and the isFinishing law
 *  (true in onDestroy after finish(), the AOSP mFinished shape). */
public class ResAct extends Activity {
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        ComponentName cn = getCallingActivity();
        String cnCls = cn != null ? cn.getClassName() : null;
        String pkg = getCallingPackage();
        if ("com.probe.c7act.Main".equals(cnCls)
                && "com.probe.c7act".equals(pkg))
            Rec.ok("W3-A1a", "getCallingActivity=Main pkg=com.probe.c7act "
                    + "(AOSP caller identity law)");
        else
            Rec.fail("W3-A1a", "getCallingActivity="
                    + (cnCls != null ? cnCls : "null") + " pkg="
                    + (pkg != null ? pkg : "null"));
        Main.postFinish(this);
    }
    @Override protected void onDestroy() {
        super.onDestroy();
        // W3-A5: mFinished persists through the teardown.
        Rec.fail("W3-A5", "isFinishing-in-onDestroy=" + isFinishing());
    }
    @Override protected void onResume() {
        super.onResume();
        setResult(7, new Intent("com.probe.c7act.RESULT"));
        finish();
    }
}
