package com.probe.c7runtime;

import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.ContentProviderClient;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.database.Cursor;
import java.io.FileNotFoundException;
import android.net.Uri;
import android.content.ServiceConnection;
import android.os.Bundle;
import android.os.IBinder;
import android.widget.TextView;
import java.io.FileOutputStream;

/** CODER7 ordered-broadcast + service-contract probe — generic Android
 *  component semantics, no package-specific runtime branches. Every op
 *  records GATEA-style machine-readable lines to files/c7_results.jsonl
 *  and stdout; negative ops PASS only when the AOSP-contract behavior
 *  (exception or non-delivery) actually arrives. */
public class MainActivity extends Activity {

    private StringBuilder RES = new StringBuilder();

    private void ok(String op, Object detail) {
        RES.append("C7|").append(op).append("|PASS|").append(detail).append("\n");
    }
    private void fail(String op, Object detail) {
        RES.append("C7|").append(op).append("|FAIL|").append(detail).append("\n");
    }

    static final class Conn implements ServiceConnection {
        public int calls = 0;
        public IBinder binder = null;
        public void onServiceConnected(ComponentName n, IBinder b) {
            calls++; binder = b;
        }
        public void onServiceDisconnected(ComponentName n) {}
    }

    /** Dynamic ORDER receiver, priority 40 — sits between RHigh(50) and
     *  RMid(20); mutates the result chain (AOSP ordered propagation). */
    static class DynHigh extends BroadcastReceiver {
        static boolean chainSeen = false;
        static String detail = "";
        public void onReceive(Context c, Intent i) {
            Order.append("Dyn");
            int code = getResultCode();
            String data = getResultData();
            chainSeen = (code == 1 && "r1".equals(data));
            detail = "code=" + code + " data=" + data;
            setResultCode(2);
            setResultData("r2");
            getResultExtras(true).putInt("k", 7);
        }
    }

    /** Category-mismatch receiver (no categories declared). */
    static class DynNoCat extends BroadcastReceiver {
        static int deliveries = 0;
        public void onReceive(Context c, Intent i) { deliveries++; }
    }

    /** Category-match receiver (declares C7CAT1). */
    static class DynCat extends BroadcastReceiver {
        static int deliveries = 0;
        public void onReceive(Context c, Intent i) { deliveries++; }
    }

    /** goAsync law receiver. */
    static class GADyn extends BroadcastReceiver {
        static int prCode = Integer.MIN_VALUE;
        static String prData = "unread";
        static String recvDataAfterGoAsync = "unread";
        static int prExtrasE = -1;
        static boolean finished = false;
        public void onReceive(Context c, Intent i) {
            Order.append("GA");
            BroadcastReceiver.PendingResult pr = goAsync();
            prCode = pr.getResultCode();
            prData = pr.getResultData();
            prExtrasE = pr.getResultExtras(false).getInt("e", -1);
            recvDataAfterGoAsync = getResultData();
            pr.finish();
            finished = true;
        }
    }

    /** Final resultReceiver for the ORDER chain (AOSP: runs after every
     *  other receiver, carrying the final result state). */
    static class FinalOrder extends BroadcastReceiver {
        static boolean finalOk = false;
        static String detail = "";
        public void onReceive(Context c, Intent i) {
            Order.append("FINAL");
            int code = getResultCode();
            String data = getResultData();
            int k = getResultExtras(true).getInt("k", -1);
            finalOk = (code == 2 && "r2".equals(data) && k == 7);
            detail = "code=" + code + " data=" + data + " k=" + k;
        }
    }

    /** Final resultReceiver for the ABORT chain — AOSP: STILL runs after
     *  abortBroadcast(). */
    static class FinalAbort extends BroadcastReceiver {
        static boolean ranAfterAbort = false;
        static String data = "";
        public void onReceive(Context c, Intent i) {
            ranAfterAbort = true;
            data = getResultData();
        }
    }

    /** Ordered-broadcast hint check receiver. */
    static class OrderedHint extends BroadcastReceiver {
        static boolean orderedHint = false;
        static boolean setResultThrew = false;
        public void onReceive(Context c, Intent i) {
            orderedHint = isOrderedBroadcast();
            try {
                setResultData("hint-check");  // must NOT throw (AOSP
                                              // checkSynchronousHint logs)
            } catch (Throwable t) { setResultThrew = true; }
        }
    }

    // ═════════ WAVE-3 dynamic probe receivers ═════════
    static class MimeDynA extends BroadcastReceiver {
        static int deliveries = 0;
        public void onReceive(Context c, Intent i) { deliveries++; }
    }
    static class MimeDynB extends BroadcastReceiver {
        static int deliveries = 0;
        public void onReceive(Context c, Intent i) { deliveries++; }
    }
    static class SchemeDynA extends BroadcastReceiver {
        static int deliveries = 0;
        public void onReceive(Context c, Intent i) { deliveries++; }
    }
    static class SchemeDynB extends BroadcastReceiver {
        static int deliveries = 0;
        public void onReceive(Context c, Intent i) { deliveries++; }
    }
    static class OrdStickyFinal extends BroadcastReceiver {
        static boolean ran = false; static int code = 999; static String data = "?";
        public void onReceive(Context c, Intent i) {
            ran = true; code = getResultCode(); data = getResultData();
        }
    }
    static class ZeroFinal extends BroadcastReceiver {
        static boolean ran = false; static int code = 999; static String data = "?";
        public void onReceive(Context c, Intent i) {
            ran = true; code = getResultCode(); data = getResultData();
        }
    }
    static class StickyOrdB extends BroadcastReceiver {
        static int caught = 0; static boolean initial = false;
        public void onReceive(Context c, Intent i) {
            caught++; initial = isInitialStickyBroadcast();
        }
    }
    static class AllUnregR extends BroadcastReceiver {
        public int hits = 0;
        public void onReceive(Context c, Intent i) { hits++; }
    }
    static class CtrlRecv extends BroadcastReceiver {
        static int hits = 0;
        public void onReceive(Context c, Intent i) { hits++; }
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        RES = new StringBuilder();
        try { runProbe(); } catch (Throwable t) { fail("PROBE-FATAL", t); }
        try {
            FileOutputStream fos = openFileOutput("c7_results.jsonl",
                                                  Context.MODE_PRIVATE);
            fos.write(RES.toString().getBytes("UTF-8"));
            fos.flush(); fos.close();
        } catch (Throwable t) { fail("RESULTS-WRITE", t); }
        TextView tv = new TextView(this);
        tv.setTextSize(11f);
        tv.setText(RES.toString());
        setContentView(tv);
    }

    private void runProbe() {
        // ══ ORD-01: priority ordering (manifest 50 > dyn 40 > 20 > 10) ══
        Order.reset(); RLow.called = false;
        DynHigh.chainSeen = false; DynHigh.detail = "";
        RMid.chainSeen = false; RMid.detail = "";
        FinalOrder.finalOk = false; FinalOrder.detail = "";
        try {
            DynHigh dyn = new DynHigh();
            IntentFilter df = new IntentFilter("com.probe.c7runtime.ORDER");
            df.setPriority(40);
            registerReceiver(dyn, df);
            sendOrderedBroadcast(
                new Intent("com.probe.c7runtime.ORDER"), null,
                new FinalOrder(), null, -1, null, null);
            String expect = "High,Dyn,Mid,Low,FINAL";
            if (expect.equals(Order.seq.toString())
                    && RHigh.sawInitialResultOk && DynHigh.chainSeen
                    && RMid.chainSeen && FinalOrder.finalOk)
                ok("ORD-01", "order=" + Order.seq + " seed(-1)✓ chain✓"
                        + " final(" + FinalOrder.detail + ")");
            else
                fail("ORD-01", "order=" + Order.seq
                        + " seed=" + RHigh.sawInitialResultOk
                        + " dyn=" + DynHigh.detail
                        + " mid=" + RMid.detail
                        + " final=" + FinalOrder.detail);
            unregisterReceiver(dyn);
        } catch (Throwable t) { fail("ORD-01", t); }

        // ══ ORD-02: abortBroadcast stops lower priority; final still runs ══
        Order.reset(); RLow.called = false; RAbort.called = false;
        FinalAbort.ranAfterAbort = false; FinalAbort.data = "";
        try {
            sendOrderedBroadcast(new Intent("com.probe.c7runtime.ABORT"),
                    null, new FinalAbort(), null, -1, null, null);
            if (RAbort.called && !RLow.called && FinalAbort.ranAfterAbort
                    && "aborted-here".equals(FinalAbort.data))
                ok("ORD-02", "abort: Low skipped, final ran with data="
                        + FinalAbort.data);
            else
                fail("ORD-02", "abort=" + RAbort.called + " lowCalled="
                        + RLow.called + " finalRan=" + FinalAbort.ranAfterAbort
                        + " finalData=" + FinalAbort.data);
        } catch (Throwable t) { fail("ORD-02", t); }

        // ══ ORD-03: abort is a LOG-ONLY no-op on a NON-ordered send ══
        Order.reset(); RLow.called = false; RAbort.called = false;
        try {
            sendBroadcast(new Intent("com.probe.c7runtime.ABORT"));
            if (RAbort.called && RLow.called)
                ok("ORD-03", "non-ordered: abort no-op → both delivered");
            else
                fail("ORD-03", "abort=" + RAbort.called + " low=" + RLow.called);
        } catch (Throwable t) { fail("ORD-03", t); }

        // ══ ORD-04: category law (IntentFilter.matchCategories) ══
        DynNoCat.deliveries = 0; DynCat.deliveries = 0;
        try {
            DynNoCat noCat = new DynNoCat();
            DynCat withCat = new DynCat();
            IntentFilter f1 = new IntentFilter("com.probe.c7runtime.CAT");
            IntentFilter f2 = new IntentFilter("com.probe.c7runtime.CAT");
            f2.addCategory("com.probe.c7runtime.C7CAT1");
            registerReceiver(noCat, f1);
            registerReceiver(withCat, f2);
            Intent ci = new Intent("com.probe.c7runtime.CAT");
            ci.addCategory("com.probe.c7runtime.C7CAT1");
            sendOrderedBroadcast(ci, null);
            if (DynNoCat.deliveries == 0 && DynCat.deliveries == 1)
                ok("ORD-04", "category: mismatch skipped, match delivered");
            else
                fail("ORD-04", "noCat=" + DynNoCat.deliveries + " cat="
                        + DynCat.deliveries);
            unregisterReceiver(noCat);
            unregisterReceiver(withCat);
        } catch (Throwable t) { fail("ORD-04", t); }

        // ══ ORD-05: ordered hint + log-only setResult on non-ordered ══
        OrderedHint.orderedHint = false;
        OrderedHint.setResultThrew = false;
        try {
            OrderedHint oh = new OrderedHint();
            registerReceiver(oh, new IntentFilter("com.probe.c7runtime.HINT"));
            sendOrderedBroadcast(new Intent("com.probe.c7runtime.HINT"), null);
            boolean ordOk = OrderedHint.orderedHint;
            unregisterReceiver(oh);
            registerReceiver(oh, new IntentFilter("com.probe.c7runtime.HINT2"));
            sendBroadcast(new Intent("com.probe.c7runtime.HINT2"));
            unregisterReceiver(oh);
            boolean plainOk = !OrderedHint.setResultThrew;
            if (ordOk && plainOk)
                ok("ORD-05", "isOrderedBroadcast=true; plain setResult no-throw");
            else
                fail("ORD-05", "orderedHint=" + ordOk + " plainNoThrow="
                        + plainOk);
        } catch (Throwable t) { fail("ORD-05", t); }

        // ══ ORD-06: receiver permission law (held vs missing) ══
        RPerm.delivered = false; RPermMissing.delivered = false;
        try {
            sendOrderedBroadcast(new Intent("com.probe.c7runtime.PERM"), null);
            sendOrderedBroadcast(new Intent("com.probe.c7runtime.PERM2"), null);
            if (RPerm.delivered && !RPermMissing.delivered)
                ok("ORD-06", "perm held → delivered; perm missing → denied");
            else
                fail("ORD-06", "held=" + RPerm.delivered + " missing="
                        + RPermMissing.delivered);
        } catch (Throwable t) { fail("ORD-06", t); }

        // ══ ORD-07: 7-arg overload seeds + goAsync detach law ══
        Order.reset();
        GADyn.prCode = Integer.MIN_VALUE; GADyn.prData = "unread";
        GADyn.recvDataAfterGoAsync = "unread"; GADyn.prExtrasE = -1;
        try {
            GADyn ga = new GADyn();
            registerReceiver(ga, new IntentFilter("com.probe.c7runtime.GA"));
            Bundle seed = new Bundle();
            seed.putInt("e", 9);
            sendOrderedBroadcast(new Intent("com.probe.c7runtime.GA"), null,
                    new FinalOrder(), null, 5, "seed", seed);
            unregisterReceiver(ga);
            if (GADyn.prCode == 5 && "seed".equals(GADyn.prData)
                    && GADyn.prExtrasE == 9 && GADyn.recvDataAfterGoAsync == null
                    && GADyn.finished)
                ok("ORD-07", "goAsync: pr(code=5,data=seed,e=9) detached,"
                        + " receiver-level null, finish ok");
            else
                fail("ORD-07", "prCode=" + GADyn.prCode + " prData="
                        + GADyn.prData + " prE=" + GADyn.prExtrasE
                        + " recvAfter=" + GADyn.recvDataAfterGoAsync);
        } catch (Throwable t) { fail("ORD-07", t); }

        // ══ SVC-05: stopSelfResult(startId) law ══
        SvcA.creates = 0; SvcA.starts = 0; SvcA.destroys = 0;
        SvcA.lastStartId = -1; SvcA.lastStopAnswer = false;
        try {
            Intent ia = new Intent(this, SvcA.class);
            startService(ia); startService(ia);          // startIds 1, 2
            int startsAfterPlain = SvcA.starts;
            Intent iOld = new Intent(this, SvcA.class);
            iOld.setAction("com.probe.c7runtime.STOP_OLD");
            startService(iOld);                          // startId 3; calls
                                                         // stopSelfResult(1)
            boolean oldIdAnswer = SvcA.lastStopAnswer;
            int destroysAfterOld = SvcA.destroys;
            Intent iLast = new Intent(this, SvcA.class);
            iLast.setAction("com.probe.c7runtime.STOP_LAST");
            startService(iLast);                         // startId 4; calls
                                                         // stopSelfResult(4)
            boolean lastIdAnswer = SvcA.lastStopAnswer;
            if (startsAfterPlain == 2 && !oldIdAnswer && destroysAfterOld == 0
                    && lastIdAnswer && SvcA.destroys == 1)
                ok("SVC-05", "startx2 + stopSelfResult(old)=false (service"
                        + " stays), stopSelfResult(last)=true → onDestroy");
            else
                fail("SVC-05", "starts=" + SvcA.starts + " oldAns="
                        + oldIdAnswer + " dOld=" + destroysAfterOld
                        + " lastAns=" + lastIdAnswer + " destroys="
                        + SvcA.destroys);
        } catch (Throwable t) { fail("SVC-05", t); }

        // ══ SVC-06: onUnbind default(false) → onDestroy (pure-bound) ══
        SvcB.binds = 0; SvcB.unbinds = 0; SvcB.destroys = 0;
        try {
            Conn cb = new Conn();
            bindService(new Intent(this, SvcB.class), cb,
                        Context.BIND_AUTO_CREATE);
            unbindService(cb);
            if (SvcB.binds == 1 && SvcB.unbinds == 1 && SvcB.destroys == 1)
                ok("SVC-06", "pure-bound unbind → onUnbind(false) → onDestroy");
            else
                fail("SVC-06", "binds=" + SvcB.binds + " unbinds=" + SvcB.unbinds
                        + " destroys=" + SvcB.destroys);
        } catch (Throwable t) { fail("SVC-06", t); }

        // ══ SVC-07: onUnbind(true) → onRebind on next bind ══
        SvcC.binds = 0; SvcC.rebinds = 0; SvcC.unbinds = 0; SvcC.destroys = 0;
        try {
            Conn c1 = new Conn(); Conn c2 = new Conn();
            bindService(new Intent(this, SvcC.class), c1,
                        Context.BIND_AUTO_CREATE);
            unbindService(c1);
            boolean aliveAfterUnbind = (SvcC.destroys == 0);
            bindService(new Intent(this, SvcC.class), c2,
                        Context.BIND_AUTO_CREATE);
            boolean rebindFired = (SvcC.rebinds == 1 && SvcC.binds == 1);
            boolean reconnected = (c2.calls == 1 && c2.binder != null);
            stopService(new Intent(this, SvcC.class));
            if (aliveAfterUnbind && rebindFired && reconnected
                    && SvcC.destroys == 1)
                ok("SVC-07", "unbind→onUnbind(true) stays; rebind→onRebind;"
                        + " retained binder reconnected; stop→onDestroy");
            else
                fail("SVC-07", "alive=" + aliveAfterUnbind + " rebinds="
                        + SvcC.rebinds + " binds=" + SvcC.binds
                        + " conn2calls=" + c2.calls + " destroys="
                        + SvcC.destroys);
        } catch (Throwable t) { fail("SVC-07", t); }

        // ══ SVC-08: unbindService(conn) targets ITS service only ══
        SvcD.destroys = 0; SvcE.destroys = 0;
        try {
            Conn cd = new Conn(); Conn ce = new Conn();
            bindService(new Intent(this, SvcD.class), cd,
                        Context.BIND_AUTO_CREATE);
            bindService(new Intent(this, SvcE.class), ce,
                        Context.BIND_AUTO_CREATE);
            unbindService(ce);
            if (SvcE.destroys == 1 && SvcD.destroys == 0)
                ok("SVC-08", "unbind(connE) destroyed only SvcE");
            else
                fail("SVC-08", "svcD=" + SvcD.destroys + " svcE="
                        + SvcE.destroys);
            // ══ SVC-09: double unbind → IAE (AOSP ContextImpl law) ══
            try {
                unbindService(ce);
                fail("SVC-09", "no-exception (double unbind silent)");
            } catch (IllegalArgumentException okIae) {
                ok("SVC-09", "double unbind → IllegalArgumentException: "
                        + okIae.getMessage());
            } catch (Throwable t) {
                fail("SVC-09", "wrong exception: " + t);
            }
            stopService(new Intent(this, SvcD.class));
        } catch (Throwable t) { fail("SVC-08", t); }

        // ══ SVC-10: bring-down path delivers onUnbind before onDestroy ══
        // (AOSP ActiveServices bringDownServiceLocked: a stopService /
        // stopSelf on a service with LIVE bindings delivers onUnbind
        // FIRST; wave-1 left the stop paths without onUnbind — PENDING §7.)
        SvcF.creates = 0; SvcF.binds = 0; SvcF.unbinds = 0; SvcF.destroys = 0;
        try {
            Conn cf = new Conn();
            startService(new Intent(this, SvcF.class));
            bindService(new Intent(this, SvcF.class), cf,
                        Context.BIND_AUTO_CREATE);
            stopService(new Intent(this, SvcF.class));
            if (SvcF.creates == 1 && SvcF.binds == 1 && SvcF.unbinds == 1
                    && SvcF.destroys == 1)
                ok("SVC-10", "bring-down: onUnbind delivered before onDestroy"
                        + " (unbinds=1 destroys=1)");
            else
                fail("SVC-10", "creates=" + SvcF.creates + " binds="
                        + SvcF.binds + " unbinds=" + SvcF.unbinds
                        + " destroys=" + SvcF.destroys);
        } catch (Throwable t) { fail("SVC-10", t); }

        // ══ ORD-08: per-filter double delivery (same action, two filters) ══
        // AOSP resolves per (receiver, filter): MultiFilter delivers TWICE
        // (MFA@60, MFB@15) interleaved with MFH@30 / MFL@5; the wave-1
        // MAX-fold delivered ONCE at the receiver-level max priority.
        Order.reset();
        MultiFilter.deliveries = 0;
        try {
            sendOrderedBroadcast(new Intent("com.probe.c7runtime.MF"), null,
                    new FinalOrder(), null, -1, null, null);
            if ("MFA,MFH,MFB,MFL,FINAL".equals(Order.seq.toString())
                    && MultiFilter.deliveries == 2)
                ok("ORD-08", "per-filter: " + Order.seq
                        + " deliveries=" + MultiFilter.deliveries);
            else
                fail("ORD-08", "order=" + Order.seq + " deliveries="
                        + MultiFilter.deliveries);
        } catch (Throwable t) { fail("ORD-08", t); }

        // ══ ORD-09: per-filter category law (second filter is selective) ══
        // intent MFCAT + category MFCC matches ONLY filter B → exactly one
        // more delivery; intent MFCAT + undeclared category matches NOTHING.
        int mfBefore = MultiFilter.deliveries;
        try {
            Intent ci = new Intent("com.probe.c7runtime.MFCAT");
            ci.addCategory("com.probe.c7runtime.MFCC");
            sendOrderedBroadcast(ci, null);
            int afterCat = MultiFilter.deliveries;
            Intent xi = new Intent("com.probe.c7runtime.MFCAT");
            xi.addCategory("com.probe.c7runtime.OTHERCAT");
            sendOrderedBroadcast(xi, null);
            int afterOther = MultiFilter.deliveries;
            if (mfBefore >= 2 && afterCat == mfBefore + 1
                    && afterOther == afterCat)
                ok("ORD-09", "category filter law: +" + (afterCat - mfBefore)
                        + " via filter B, +0 for undeclared category");
            else
                fail("ORD-09", "before=" + mfBefore + " afterCat=" + afterCat
                        + " afterOther=" + afterOther);
        } catch (Throwable t) { fail("ORD-09", t); }

        // ══ ORD-10: dynamic registration-permission law ══
        // DynPerm is registered WITH broadcastPermission DYNPERM (not held
        // by this app) → its send is DENIED; DynNoPerm (same action, no
        // permission) is the delivered CONTROL.
        DynPerm.deliveries = 0; DynNoPerm.deliveries = 0;
        try {
            DynPerm dp = new DynPerm();
            DynNoPerm dnp = new DynNoPerm();
            registerReceiver(dp, new IntentFilter("com.probe.c7runtime.DYNP"),
                    "com.probe.c7runtime.DYNPERM", null);
            registerReceiver(dnp, new IntentFilter("com.probe.c7runtime.DYNP"));
            sendOrderedBroadcast(new Intent("com.probe.c7runtime.DYNP"), null);
            unregisterReceiver(dp);
            unregisterReceiver(dnp);
            if (DynPerm.deliveries == 0 && DynNoPerm.deliveries == 1)
                ok("ORD-10", "registration permission: denied without it,"
                        + " control delivered (perm=0, ctrl=1)");
            else
                fail("ORD-10", "perm=" + DynPerm.deliveries + " ctrl="
                        + DynNoPerm.deliveries);
        } catch (Throwable t) { fail("ORD-10", t); }

        // ══ STK-01: sticky cache + initial catch-up delivery ══
        StickyCatch.caught = 0; StickyCatch.initial = false;
        StickyCatch.val = "";
        try {
            Intent s1 = new Intent("com.probe.c7runtime.STK");
            s1.putExtra("v", "v1");
            sendStickyBroadcast(s1);
            StickyCatch sc = new StickyCatch();
            registerReceiver(sc, new IntentFilter("com.probe.c7runtime.STK"));
            unregisterReceiver(sc);
            if (StickyCatch.caught == 1 && StickyCatch.initial
                    && "v1".equals(StickyCatch.val))
                ok("STK-01", "sticky catch-up: caught=1 initial=true v=v1");
            else
                fail("STK-01", "caught=" + StickyCatch.caught + " initial="
                        + StickyCatch.initial + " val=" + StickyCatch.val);
        } catch (Throwable t) { fail("STK-01", t); }

        // ══ STK-02: removeStickyBroadcast ends the catch-up ══
        StickyCatch2.caught = 0;
        try {
            removeStickyBroadcast(new Intent("com.probe.c7runtime.STK"));
            StickyCatch2 sc2 = new StickyCatch2();
            registerReceiver(sc2, new IntentFilter("com.probe.c7runtime.STK"));
            unregisterReceiver(sc2);
            if (StickyCatch2.caught == 0)
                ok("STK-02", "removeStickyBroadcast: late register gets 0");
            else
                fail("STK-02", "caught=" + StickyCatch2.caught);
        } catch (Throwable t) { fail("STK-02", t); }

        // ══ STK-04: re-cached sticky (fresh send after removal) ══
        StickyCatch3.caught = 0; StickyCatch3.val = "";
        try {
            Intent s2 = new Intent("com.probe.c7runtime.STK");
            s2.putExtra("v", "v2");
            sendStickyBroadcast(s2);
            StickyCatch3 sc3 = new StickyCatch3();
            registerReceiver(sc3, new IntentFilter("com.probe.c7runtime.STK"));
            unregisterReceiver(sc3);
            if (StickyCatch3.caught == 1 && "v2".equals(StickyCatch3.val))
                ok("STK-04", "re-cache: fresh sticky v2 delivered on register");
            else
                fail("STK-04", "caught=" + StickyCatch3.caught + " val="
                        + StickyCatch3.val);
        } catch (Throwable t) { fail("STK-04", t); }

        // ══ EXP-01..03: exported law observations (mode-dependent) ══
        // The sender identity is chosen by the RUN MODE (no env → the
        // running package; MINIANDROID_C7_SENDER_PKG → a modeled foreign
        // sender; MINIANDROID_C7_SENDER_PERMS → its held permissions).
        // Expected: R0 (same-pkg) all delivered; R1 (foreign, no perms)
        // EXP1/EXP2 denied, EXP3 delivered; R2 (foreign + PERMISSION)
        // EXP2 delivered too. Recorded as OBS rows — the harness asserts
        // per mode.
        ExpLocked.delivered = false; ExpOpen.delivered = false;
        ExpDefault.delivered = false;
        try {
            sendOrderedBroadcast(new Intent("com.probe.c7runtime.EXP1"), null);
            sendOrderedBroadcast(new Intent("com.probe.c7runtime.EXP2"), null);
            sendOrderedBroadcast(new Intent("com.probe.c7runtime.EXP3"), null);
            RES.append("C7|EXP-01|OBS|ExpLocked exported=false delivered=")
               .append(ExpLocked.delivered).append("\n");
            RES.append("C7|EXP-02|OBS|ExpOpen exported=true+perm delivered=")
               .append(ExpOpen.delivered).append("\n");
            RES.append("C7|EXP-03|OBS|ExpDefault no-attr+filter delivered=")
               .append(ExpDefault.delivered).append("\n");
        } catch (Throwable t) { fail("EXP-OBS", t); }

        runProbeW3();
    }

    // ═══════════════════════════════════════════════════════════════════
    // CODER7 WAVE-3 ops — broadcast matchData/unregister/sticky-ordered,
    // service AUTO_CREATE/missing/stopSelf(int), provider client laws,
    // PackageManager resolution laws. Same verdict discipline as wave-1/2.
    // ═══════════════════════════════════════════════════════════════════
    private void runProbeW3() {
        // ══ W3-B11: unregisterReceiver of an unknown receiver → IAE ══
        try {
            try {
                unregisterReceiver(new AllUnregR());
                fail("W3-B11", "no exception for unknown receiver");
            } catch (IllegalArgumentException iae) {
                ok("W3-B11", "unknown receiver → IllegalArgumentException: "
                        + iae.getMessage());
            }
        } catch (Throwable t) { fail("W3-B11", t); }

        // ══ W3-B12: ONE unregister kills EVERY registration of the receiver ══
        try {
            AllUnregR r2 = new AllUnregR();
            registerReceiver(r2, new IntentFilter("com.probe.c7runtime.DUAL1"));
            registerReceiver(r2, new IntentFilter("com.probe.c7runtime.DUAL2"));
            sendBroadcast(new Intent("com.probe.c7runtime.DUAL1"));
            sendBroadcast(new Intent("com.probe.c7runtime.DUAL2"));
            int before = r2.hits;
            unregisterReceiver(r2);
            sendBroadcast(new Intent("com.probe.c7runtime.DUAL1"));
            sendBroadcast(new Intent("com.probe.c7runtime.DUAL2"));
            if (before == 2 && r2.hits == before)
                ok("W3-B12", "dual registration delivered 2; one unregister → 0 more");
            else
                fail("W3-B12", "before=" + before + " after=" + r2.hits);
        } catch (Throwable t) { fail("W3-B12", t); }

        // ══ W3-B14: IntentFilter.matchData TYPE half (manifest + dynamic) ══
        try {
            MimeRecv.deliveries = 0;
            MimeDynA.deliveries = 0; MimeDynB.deliveries = 0;
            IntentFilter fa = new IntentFilter("com.probe.c7runtime.MIME2");
            fa.addDataType("text/plain");
            MimeDynA a = new MimeDynA(); registerReceiver(a, fa);
            IntentFilter fb = new IntentFilter("com.probe.c7runtime.MIME2");
            fb.addDataType("image/*");
            MimeDynB b = new MimeDynB(); registerReceiver(b, fb);
            sendBroadcast(new Intent("com.probe.c7runtime.MIME").setType("text/plain"));
            sendBroadcast(new Intent("com.probe.c7runtime.MIME2").setType("text/plain"));
            int mrText = MimeRecv.deliveries, aText = MimeDynA.deliveries;
            MimeRecv.deliveries = 0; MimeDynA.deliveries = 0;
            sendBroadcast(new Intent("com.probe.c7runtime.MIME").setType("image/png"));
            sendBroadcast(new Intent("com.probe.c7runtime.MIME2").setType("image/png"));
            int mrImg = MimeRecv.deliveries, aImg = MimeDynA.deliveries,
                bImg = MimeDynB.deliveries;
            unregisterReceiver(a); unregisterReceiver(b);
            if (mrText == 1 && aText == 1 && mrImg == 0 && aImg == 0 && bImg == 1)
                ok("W3-B14", "MIME: text/plain→manifest+" + aText
                        + "dyn; image/png→wildcard-dyn only (" + bImg
                        + "); mismatch silent (" + mrImg + "/" + aImg + ")");
            else
                fail("W3-B14", "mr=" + mrText + "/" + mrImg + " a=" + aText
                        + "/" + aImg + " bImg=" + bImg);
        } catch (Throwable t) { fail("W3-B14", t); }

        // ══ W3-B15: matchData DATA half (scheme) ══
        try {
            SchemeRecv.deliveries = 0;
            SchemeDynA.deliveries = 0; SchemeDynB.deliveries = 0;
            IntentFilter fa = new IntentFilter("com.probe.c7runtime.SCHEME2");
            fa.addDataScheme("content");
            SchemeDynA a = new SchemeDynA(); registerReceiver(a, fa);
            IntentFilter fb = new IntentFilter("com.probe.c7runtime.SCHEME2");
            fb.addDataScheme("https");
            SchemeDynB b = new SchemeDynB(); registerReceiver(b, fb);
            sendBroadcast(new Intent("com.probe.c7runtime.SCHEME")
                    .setData(Uri.parse("content://probe/x")));
            sendBroadcast(new Intent("com.probe.c7runtime.SCHEME2")
                    .setData(Uri.parse("content://probe/y")));
            int mc = SchemeRecv.deliveries, ac = SchemeDynA.deliveries;
            SchemeRecv.deliveries = 0; SchemeDynA.deliveries = 0;
            sendBroadcast(new Intent("com.probe.c7runtime.SCHEME")
                    .setData(Uri.parse("https://probe/z")));
            sendBroadcast(new Intent("com.probe.c7runtime.SCHEME2")
                    .setData(Uri.parse("https://probe/w")));
            int mh = SchemeRecv.deliveries, ah = SchemeDynA.deliveries,
                bh = SchemeDynB.deliveries;
            unregisterReceiver(a); unregisterReceiver(b);
            if (mc == 1 && ac == 1 && mh == 0 && ah == 0 && bh == 1)
                ok("W3-B15", "scheme: content→manifest+content-dyn; "
                        + "https→https-dyn only; mismatch silent");
            else
                fail("W3-B15", "mc=" + mc + " ac=" + ac + " mh=" + mh
                        + " ah=" + ah + " bh=" + bh);
        } catch (Throwable t) { fail("W3-B15", t); }

        // ══ W3-B16: sendStickyOrderedBroadcast = ordered + sticky cache ══
        try {
            StickyCatch.caught = 0; StickyCatch.initial = false;
            OrdStickyFinal.ran = false; OrdStickyFinal.code = 999;
            OrdStickyFinal.data = "?";
            StickyOrdB.caught = 0; StickyOrdB.initial = false;
            sendStickyOrderedBroadcast(
                new Intent("com.probe.c7runtime.STKYORD").putExtra("v", "vo"),
                new OrdStickyFinal(), null, 5, "seed", null);
            boolean chainRan = StickyCatch.caught >= 1;
            boolean finalRan = OrdStickyFinal.ran
                    && OrdStickyFinal.code == 5
                    && "seed".equals(OrdStickyFinal.data);
            registerReceiver(new StickyOrdB(),
                    new IntentFilter("com.probe.c7runtime.STKYORD"));
            boolean caughtUp = StickyOrdB.caught == 1
                    && StickyOrdB.initial;
            removeStickyBroadcast(
                    new Intent("com.probe.c7runtime.STKYORD"));
            if (chainRan && finalRan && caughtUp)
                ok("W3-B16", "sticky-ordered: chain delivered, final(code=5,"
                        + "data=seed), fresh receiver caught the sticky "
                        + "with isInitialStickyBroadcast=true, then removed");
            else
                fail("W3-B16", "chain=" + chainRan + " final=" + finalRan
                        + " caughtUp=" + caughtUp);
        } catch (Throwable t) { fail("W3-B16", t); }

        // ══ W3-B3ev: zero matching receivers — final still runs (evidence) ══
        try {
            ZeroFinal.ran = false; ZeroFinal.code = 999; ZeroFinal.data = "?";
            sendOrderedBroadcast(
                new Intent("com.probe.c7runtime.NOSUCHRECV"), null,
                new ZeroFinal(), null, 9, "zseed", null);
            if (ZeroFinal.ran && ZeroFinal.code == 9
                    && "zseed".equals(ZeroFinal.data))
                ok("W3-B3ev", "zero matching receivers → final resultReceiver "
                        + "still ran with the seed (code=9 data=zseed)");
            else
                fail("W3-B3ev", "ran=" + ZeroFinal.ran + " code="
                        + ZeroFinal.code + " data=" + ZeroFinal.data);
        } catch (Throwable t) { fail("W3-B3ev", t); }

        // ══ W3-S11: bind WITHOUT BIND_AUTO_CREATE queues the connection ══
        try {
            SvcG.creates = 0; SvcG.binds = 0; SvcG.destroys = 0;
            Conn cg = new Conn();
            Intent gi = new Intent(this, SvcG.class);
            boolean bound = bindService(gi, cg, 0);
            boolean createdEarly = SvcG.creates > 0;
            boolean connectedEarly = cg.calls > 0;
            startService(new Intent(this, SvcG.class));
            boolean createdThen = SvcG.creates == 1;
            boolean connectedThen = cg.calls == 1;
            unbindService(cg);
            boolean aliveAfterUnbind = SvcG.destroys == 0;
            stopService(new Intent(this, SvcG.class));
            if (bound && !createdEarly && !connectedEarly && createdThen
                    && connectedThen && aliveAfterUnbind && SvcG.destroys == 1)
                ok("W3-S11", "flags=0 bind: no onCreate/no connect; "
                        + "startService → create + queued connect; unbind "
                        + "keeps the started svc; stop destroys");
            else
                fail("W3-S11", "bound=" + bound + " earlyC=" + createdEarly
                        + " earlyConn=" + connectedEarly + " creates="
                        + SvcG.creates + " conn=" + cg.calls + " stops="
                        + SvcG.destroys);
        } catch (Throwable t) { fail("W3-S11", t); }

        // ══ W3-S12: startService/bindService of a NOT-INSTALLED service ══
        try {
            Intent miss = new Intent();
            miss.setComponent(new ComponentName(getPackageName(),
                    "com.probe.c7runtime.NotInstalledService"));
            ComponentName cn = startService(miss);
            boolean bindAns = true;
            try {
                bindAns = bindService(miss, new Conn(), 0);
            } catch (Throwable t2) {
                bindAns = true;
            }
            if (cn == null && bindAns == false)
                ok("W3-S12", "not-installed: startService → null "
                        + "ComponentName; bindService → false (AOSP law)");
            else
                fail("W3-S12", "cn=" + cn + " bind=" + bindAns);
        } catch (Throwable t) { fail("W3-S12", t); }

        // ══ W3-S13: stopSelf(int) obeys the getLastStartId guard ══
        try {
            SvcH.destroys = 0; SvcH.staleGuardWorked = false;
            startService(new Intent(this, SvcH.class));
            startService(new Intent(this, SvcH.class));
            boolean aliveAfterStale =
                    SvcH.destroys == 0 && SvcH.staleGuardWorked;
            startService(new Intent(this, SvcH.class));
            if (aliveAfterStale && SvcH.destroys == 1)
                ok("W3-S13", "stale stopSelf(1) → service stayed; "
                        + "stopSelf(last) → onDestroy (destroys=1)");
            else
                fail("W3-S13", "staleOk=" + aliveAfterStale + " destroys="
                        + SvcH.destroys);
        } catch (Throwable t) { fail("W3-S13", t); }

        // ══ W3-P10: acquireContentProviderClient — real client object ══
        try {
            Uri pu = Uri.parse("content://com.probe.c7runtime.prov/tbl");
            ContentProviderClient cl =
                    getContentResolver().acquireContentProviderClient(pu);
            boolean clientReal = cl != null;
            int beforeCalls = W3Provider.queryCalls;
            Cursor qc = cl != null ? cl.query(pu, null, null, null, null)
                                   : null;
            int rows = qc != null ? qc.getCount() : -1;
            if (qc != null) qc.close();
            String mt = cl != null ? cl.getType(pu) : "?";
            boolean rel1 = false, rel2Threw = false;
            if (cl != null) {
                rel1 = cl.release();
                try {
                    cl.release();
                    rel2Threw = false;
                } catch (IllegalStateException ise) {
                    rel2Threw = true;
                }
            }
            if (clientReal && rows == 2
                    && W3Provider.queryCalls == beforeCalls + 1
                    && "vnd.android.cursor.dir/vnd.probe.w3".equals(mt)
                    && rel1 && rel2Threw)
                ok("W3-P10", "client acquired (real object); client.query "
                        + "routed (rows=2); getType routed; release=true; "
                        + "2nd release → IllegalStateException");
            else
                fail("W3-P10", "real=" + clientReal + " rows=" + rows
                        + " calls=" + beforeCalls + "+"
                        + (W3Provider.queryCalls - beforeCalls) + " type="
                        + mt + " rel1=" + rel1 + " rel2Threw=" + rel2Threw);
        } catch (Throwable t) { fail("W3-P10", t); }

        // ══ W3-P11: openTypedAssetFileDescriptor error propagation ══
        try {
            Uri pu2 = Uri.parse("content://com.probe.c7runtime.prov/none");
            boolean threw = false;
            try {
                getContentResolver().openTypedAssetFileDescriptor(pu2,
                        "text/plain", null);
            } catch (FileNotFoundException fnf) {
                threw = true;
            }
            if (threw)
                ok("W3-P11", "openTypedAssetFileDescriptor → provider "
                        + "openFile FileNotFoundException propagated");
            else
                fail("W3-P11", "no exception");
        } catch (Throwable t) { fail("W3-P11", t); }

        // ══ W3-R01: MATCH_DEFAULT_ONLY resolution (CATEGORY_DEFAULT law) ══
        try {
            PackageManager pm = getPackageManager();
            Intent ai = new Intent("com.probe.c7runtime.ACTDEF");
            android.content.pm.ResolveInfo strict =
                    pm.resolveActivity(ai, PackageManager.MATCH_DEFAULT_ONLY);
            android.content.pm.ResolveInfo lax = pm.resolveActivity(ai, 0);
            java.util.List all = pm.queryIntentActivities(ai, 0);
            int n = all != null ? all.size() : -1;
            String sCls = strict != null && strict.activityInfo != null
                    ? strict.activityInfo.name : "?";
            String lCls = lax != null && lax.activityInfo != null
                    ? lax.activityInfo.name : "?";
            if ("com.probe.c7runtime.ResDefA".equals(sCls)
                    && "com.probe.c7runtime.ResDefA".equals(lCls) && n == 2)
                ok("W3-R01", "MATCH_DEFAULT_ONLY → ResDefA (filter has "
                        + "CATEGORY_DEFAULT); resolveActivity(0) → first "
                        + "match; query → " + n + " candidates");
            else
                fail("W3-R01", "strict=" + sCls + " lax=" + lCls + " n=" + n);
        } catch (Throwable t) { fail("W3-R01", t); }

        // ══ W3-R02: resolveService + queryIntentServices ══
        try {
            PackageManager pm = getPackageManager();
            android.content.pm.ResolveInfo svc = pm.resolveService(
                    new Intent("com.probe.c7runtime.ACTSVC"), 0);
            java.util.List svcs = pm.queryIntentServices(
                    new Intent("com.probe.c7runtime.ACTSVC"), 0);
            String sCls = svc != null && svc.serviceInfo != null
                    ? svc.serviceInfo.name : "?";
            int n = svcs != null ? svcs.size() : -1;
            if ("com.probe.c7runtime.SvcFilter".equals(sCls) && n == 1)
                ok("W3-R02", "resolveService → SvcFilter; "
                        + "queryIntentServices → 1 (real manifest filters)");
            else
                fail("W3-R02", "svc=" + sCls + " n=" + n);
        } catch (Throwable t) { fail("W3-R02", t); }

        // ══ W3-R03: disabled components invisible everywhere ══
        try {
            DisRecv.deliveries = 0;
            CtrlRecv.hits = 0;
            registerReceiver(new CtrlRecv(),
                    new IntentFilter("com.probe.c7runtime.DISCTRL"));
            sendBroadcast(new Intent("com.probe.c7runtime.DIS"));
            sendBroadcast(new Intent("com.probe.c7runtime.DISCTRL"));
            Intent dsvc = new Intent();
            dsvc.setComponent(new ComponentName(getPackageName(),
                    "com.probe.c7runtime.DisSvc"));
            ComponentName dcn = startService(dsvc);
            Object dprov = null;
            try {
                dprov = getPackageManager().resolveContentProvider(
                        "com.probe.c7runtime.disprov", 0);
            } catch (Throwable t2) {
                dprov = null;
            }
            boolean disSilent = DisRecv.deliveries == 0;
            boolean ctrlDelivered = CtrlRecv.hits == 1;
            if (disSilent && ctrlDelivered && dcn == null && dprov == null)
                ok("W3-R03", "enabled=false: receiver silent (0 deliveries; "
                        + "enabled control delivered), startService → null, "
                        + "resolveContentProvider → null");
            else
                fail("W3-R03", "dis=" + DisRecv.deliveries + " ctrl="
                        + CtrlRecv.hits + " dcn=" + dcn + " dprov=" + dprov);
        } catch (Throwable t) { fail("W3-R03", t); }

        // ══ W3-IT1: Intent.setType/getType + setData/getData round-trip ══
        try {
            Intent it = new Intent("com.probe.c7runtime.RT");
            it.setType("text/plain");
            String t = it.getType();
            it.setData(Uri.parse("content://rt/host/p1"));
            Uri d = it.getData();
            boolean dataOk = d != null;
            if ("text/plain".equals(t) && dataOk)
                ok("W3-IT1", "setType/getType round-trip exact; setData/getData "
                        + "non-null (matchData dimensions recorded)");
            else
                fail("W3-IT1", "type=" + t + " dataNonNull=" + dataOk);
        } catch (Throwable t) { fail("W3-IT1", t); }
    }

    @Override protected void onDestroy() { super.onDestroy(); }
}
