package com.probe.c7act;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.os.Bundle;
import android.os.Handler;
import java.io.FileOutputStream;

/** CODER7 WAVE-3 activity/task-chain probe: launchMode singleTop,
 *  FLAG_ACTIVITY_CLEAR_TOP, FLAG_ACTIVITY_NEW_TASK context law,
 *  startActivities, startActivityForResult caller identity, isFinishing,
 *  and the disabled-component launch gate. Each step posts the next so
 *  the frame pump drains the pending launch between steps. */
public class Main extends Activity {
    private static Handler H;
    private static Main SELF;

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        H = new Handler();
        SELF = this;
        Rec.out = "";
        H.post(new Runnable() { public void run() { step1(); } });
    }

    static void postFinish(Activity a) {
        H.post(new Runnable() { public void run() { } });
    }
    static void postTopRelaunch(Activity a) {
        H.post(new Runnable() { public void run() {
            a.startActivity(new Intent(a, STTop.class));
        } });
    }
    static void postCtChain(Activity a) {
        H.post(new Runnable() { public void run() {
            a.startActivity(new Intent(a, CTBase.class));
        } });
    }
    static void postCtMid(Activity a) {
        H.post(new Runnable() { public void run() {
            a.startActivity(new Intent(a, CTMid.class));
        } });
    }
    static void postClearTop(Activity a) {
        H.post(new Runnable() { public void run() {
            Intent i = new Intent(a, CTBase.class);
            i.addFlags(0x04000000);  // FLAG_ACTIVITY_CLEAR_TOP
            a.startActivity(i);
        } });
    }
    static void postDisabledTry(Activity a) {
        H.post(new Runnable() { public void run() {
            a.startActivity(new Intent(a, DisAct.class));
            H.post(new Runnable() { public void run() { flush(); } });
        } });
    }
    static void postTop(Activity a) {
        H.post(new Runnable() { public void run() {
            a.startActivity(new Intent(a, STTop.class));
        } });
    }
    static void postMulti(Activity a) {
        H.post(new Runnable() { public void run() {
            // W3-A6: the multi-launch law (FIFO queue).
            a.startActivities(new Intent[] {
                    new Intent(a, B1.class), new Intent(a, B2.class)});
        } });
    }

    private void step1() {
        // W3-A1: the for-result launch (caller identity round-trip).
        startActivityForResult(new Intent(this, ResAct.class), 77);
    }

    private static void step2() {
        // onActivityResult delivered → the caller identity + result code
        // verdict is recorded in onActivityResult below; drive W3-A2 here.
        Intent bad = new Intent(SELF, SvcNT.class);
        bad.setAction("NEWTASK_BAD");
        try {
            SELF.startService(bad);   // the IAE/AndroidRuntimeException
        } catch (Throwable t) {
            Rec.fail("W3-A2a", "no-flag service launch: "
                    + t.getClass().getSimpleName());
        }
        if (SvcNT.lastError.startsWith("AndroidRuntimeException")
                || SvcNT.lastError.startsWith("IllegalArgument")) {
            Rec.ok("W3-A2a", "no-flag service startActivity rejected: "
                    + SvcNT.lastError);
        }
        Intent okI = new Intent(SELF, SvcNT.class);
        okI.setAction("NEWTASK_OK");
        SELF.startService(okI);   // NEW_TASK held → pending launch
    }

    @Override protected void onActivityResult(int req, int rc, Intent d) {
        super.onActivityResult(req, rc, d);
        if (req == 77 && rc == 7) {
            Rec.ok("W3-A1b", "onActivityResult(77, 7) delivered; "
                    + "(caller identity recorded by ResAct)");
        } else {
            Rec.fail("W3-A1b", "req=" + req + " rc=" + rc);
        }
        H.post(new Runnable() { public void run() { step2(); } });
    }

    private static void flush() {
        // W3-A3/A4/A6/R04 verdicts + A5 verdict repair (isFinishing law).
        if (STTop.instances == 1 && STTop.newIntents == 1)
            Rec.ok("W3-A3", "singleTop: 1 instance, onNewIntent=1 "
                    + "(top re-launch did NOT create a new instance)");
        else
            Rec.fail("W3-A3", "instances=" + STTop.instances
                    + " newIntents=" + STTop.newIntents);
        if (CTBase.instances == 2 && CTBase.firstUp && CTMid.destroyed)
            Rec.ok("W3-A4", "CLEAR_TOP: above destroyed (CTMid onDestroy), "
                    + "target destroyed+recreated (instances=2)");
        else
            Rec.fail("W3-A4", "base=" + CTBase.instances + " firstUp="
                    + CTBase.firstUp + " midDestroyed=" + CTMid.destroyed
                    + " midInstances=" + CTMid.instances);
        if (B1.instances == 1 && B2.instances == 1)
            Rec.ok("W3-A6", "startActivities: both intents launched "
                    + "(FIFO queue drained)");
        else
            Rec.fail("W3-A6", "b1=" + B1.instances + " b2=" + B2.instances);
        if (DisAct.instances == 0)
            Rec.ok("W3-R04", "disabled activity: launch attempt refused "
                    + "(0 instances)");
        else
            Rec.fail("W3-R04", "disabled instances=" + DisAct.instances);
        // W3-A5 verdict rewrite: ResAct.onDestroy recorded the raw value.
        String a5 = Rec.out;
        boolean finTrue = a5.contains("isFinishing-in-onDestroy=true");
        if (finTrue) {
            Rec.out = replace(a5, "C7|W3-A5|FAIL|isFinishing-in-onDestroy=true",
                               "C7|W3-A5|PASS|mFinished persists: "
                                   + "isFinishing()==true in onDestroy");
        } else {
            Rec.out = replace(a5, "C7|W3-A5|FAIL|isFinishing-in-onDestroy=false",
                               "C7|W3-A5|FAIL|isFinishing()==false in "
                                   + "onDestroy (mFinished law absent)");
        }
        if (NewTaskAct.instances >= 1) {
            Rec.out = replace(Rec.out,
                    "C7|W3-A2a|PASS|no-flag service startActivity rejected",
                    "C7|W3-A2a|PASS|no-flag service startActivity rejected; "
                        + "NEW_TASK launch delivered (instances="
                        + NewTaskAct.instances + ")");
        }
        try {
            FileOutputStream fos = SELF.openFileOutput("act_results.jsonl",
                    MODE_PRIVATE);
            fos.write(Rec.out.getBytes("UTF-8"));
            fos.flush();
            fos.close();
        } catch (Throwable t) {
            Rec.fail("FLUSH", t.toString());
        }
    }

    private static String replace(String s, String from, String to) {
        int i = s.indexOf(from);
        if (i < 0) return s;
        return s.substring(0, i).concat(to)
                .concat(s.substring(i + from.length()));
    }
}
