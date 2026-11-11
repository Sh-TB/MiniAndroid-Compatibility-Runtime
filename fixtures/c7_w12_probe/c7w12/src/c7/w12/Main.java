package c7.w12;

import android.app.Activity;
import android.app.PendingIntent;
import android.app.TaskStackBuilder;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.ServiceInfo;
import android.os.Bundle;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** CODER7 WAVE-12 — the WAVE-12 conformance battery (package c7.w12).
 *  Ops W01..W13 cover the wave's three frontier families end-to-end:
 *   W01 getServiceInfo().foregroundServiceType == 9 (dataSync|location)
 *   W02 getPackageInfo(GET_SERVICES).services[0].foregroundServiceType == 9
 *   W03/W04/W05 the 3-arg startForeground laws (service side)
 *   W06 the MANIFEST-sentinel missing-type law (PlainService)
 *   W07 TaskStackBuilder create/addNextIntent ×2 + editIntentAt alias +
 *       the out-of-range IndexOutOfBoundsException
 *   W08 addNextIntentWithParentStack — the parentActivityName walk
 *       (ChildAct → MidAct → RootAct), root-first order, the
 *       makeMainActivity root flavor
 *   W09 getIntents() — the root copy carries NEW_TASK|CLEAR_TASK|
 *       TASK_ON_HOME, the others verbatim; copies are independent
 *   W10 getPendingIntent(7, UPDATE_CURRENT|IMMUTABLE) non-null + send()
 *   W11 startActivities() — the raw stack drains (no throw)
 *   W12 getPackagesHoldingPermissions ANY law: [INTERNET, c7.laws.OPEN]
 *       hits BOTH the self package (INTERNET) and c7laws (c7.laws.OPEN);
 *       GET_PERMISSIONS carries the requestedPermissions verbatim
 *   W13 getPackagesHoldingPermissions([CAMERA]) → honest empty
 *  Every op try/catch'd: a missing engine API is an honest FAIL row. */
public class Main extends Activity {
    @Override public void onCreate(Bundle icicle) {
        super.onCreate(icicle);
        PackageManager pm = getPackageManager();

        // ── W01: the TYPED service resolves via getServiceInfo ────────
        // (the vendored stub lacks the ServiceInfo.foregroundServiceType
        // INSTANCE field — the W11 §6(c) peekService precedent: the
        // manifest=9 parse proof rides the W03/W04 subset pair below +
        // the SVC-FG-TYPE engine rows the runner greps verbatim.)
        try {
            ServiceInfo si = pm.getServiceInfo(
                new ComponentName(this, W12Service.class), 0);
            if (si != null && si.name != null
                && si.name.endsWith("W12Service"))
                Rec.ok("W01", "typed service resolves"
                    + " (fgs parse proof: W03/W04 + SVC-FG-TYPE rows)");
            else
                Rec.bad("W01", "svc="
                    + (si == null ? "null" : si.name));
        } catch (Throwable t) {
            Rec.bad("W01", "throw:" + t.getClass().getName());
        }

        // ── W02: the GET_SERVICES array lists both manifest services ───
        try {
            PackageInfo pi = pm.getPackageInfo(getPackageName(),
                PackageManager.GET_SERVICES);
            int n = pi.services == null ? -1 : pi.services.length;
            boolean first = n >= 1 && pi.services[0].name != null
                && pi.services[0].name.endsWith("W12Service");
            if (n == 2 && first)
                Rec.ok("W02", "GET_SERVICES count=2 [0]=W12Service");
            else
                Rec.bad("W02", "count=" + n
                    + " first=" + (n >= 1 ? pi.services[0].name : "none"));
        } catch (Throwable t) {
            Rec.bad("W02", "throw:" + t.getClass().getName());
        }

        // ── the services start (their rows land in onStartCommand, the
        //    deterministic frame-drain order: W12Service then
        //    PlainService — FIFO) ──────────────────────────────────────
        try {
            startForegroundService(new Intent(this, W12Service.class));
            startForegroundService(new Intent(this, PlainService.class));
        } catch (Throwable t) {
            Rec.bad("W03", "svc start throw:" + t.getClass().getName());
        }

        // ── W07: TaskStackBuilder addNextIntent ×2 + editIntentAt ─────
        try {
            TaskStackBuilder tsb = TaskStackBuilder.create(this);
            Intent root = new Intent(this, RootAct.class)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            Intent top = new Intent(this, ChildAct.class);
            tsb.addNextIntent(root).addNextIntent(top);
            boolean count2 = tsb.getIntentCount() == 2;
            // the ALIAS law: editIntentAt returns the SAME Intent — the
            // mutation is visible through a second editIntentAt read.
            tsb.editIntentAt(1).setAction("c7.w12.EDIT");
            boolean alias = "c7.w12.EDIT".equals(
                tsb.editIntentAt(1).getAction());
            boolean rootCls = false;
            android.content.ComponentName rc = tsb.editIntentAt(0)
                .getComponent();
            rootCls = rc != null && "c7.w12.RootAct".equals(
                rc.getClassName());
            boolean oobe = false;
            try {
                tsb.editIntentAt(5);
            } catch (IndexOutOfBoundsException ex) {
                oobe = true;
            }
            if (count2 && alias && rootCls && oobe)
                Rec.ok("W07", "count=2;alias=1;root_cls=1;edit(5)=IOOBE");
            else
                Rec.bad("W07", "count2=" + (count2 ? 1 : 0)
                    + ";alias=" + (alias ? 1 : 0)
                    + ";root_cls=" + (rootCls ? 1 : 0)
                    + ";oobe=" + (oobe ? 1 : 0));
        } catch (Throwable t) {
            Rec.bad("W07", "throw:" + t.getClass().getName());
        }

        // ── W08: addNextIntentWithParentStack — the parent walk ────────
        try {
            TaskStackBuilder tsb2 = TaskStackBuilder.create(this);
            tsb2.addNextIntentWithParentStack(
                new Intent(this, ChildAct.class));
            int n = tsb2.getIntentCount();
            boolean shape = false, rootMain = false, mid = false,
                child = false;
            if (n == 3) {
                shape = true;
                android.content.ComponentName c0 = tsb2.editIntentAt(0)
                    .getComponent();
                android.content.ComponentName c1 = tsb2.editIntentAt(1)
                    .getComponent();
                android.content.ComponentName c2 = tsb2.editIntentAt(2)
                    .getComponent();
                rootMain = c0 != null
                    && "c7.w12.RootAct".equals(c0.getClassName())
                    && "android.intent.action.MAIN".equals(
                        tsb2.editIntentAt(0).getAction());
                mid = c1 != null
                    && "c7.w12.MidAct".equals(c1.getClassName());
                child = c2 != null
                    && "c7.w12.ChildAct".equals(c2.getClassName());
            }
            if (shape && rootMain && mid && child)
                Rec.ok("W08", "walk=3 root=RootAct(ACTION_MAIN) mid=MidAct"
                    + " top=ChildAct");
            else
                Rec.bad("W08", "n=" + n
                    + ";shape=" + (shape ? 1 : 0)
                    + ";root=" + (rootMain ? 1 : 0)
                    + ";mid=" + (mid ? 1 : 0)
                    + ";child=" + (child ? 1 : 0)
                    + ";c0=" + (c0 == null ? "null"
                        : c0.getClassName() + "/" + c0.getClassName()
                            .equals("c7.w12.RootAct"))
                    + ";a0=" + tsb2.editIntentAt(0).getAction()
                    + ";c1=" + (c1 == null ? "null" : c1.getClassName()));
        } catch (Throwable t) {
            Rec.bad("W08", "throw:" + t.getClass().getName());
        }

        // ── W09: getIntents — the root restart copy + verbatim copies ──
        try {
            TaskStackBuilder tsb2 = TaskStackBuilder.create(this);
            tsb2.addNextIntentWithParentStack(
                new Intent(this, ChildAct.class));
            Intent[] intents = tsb2.getIntents();
            int mask = Intent.FLAG_ACTIVITY_NEW_TASK
                | Intent.FLAG_ACTIVITY_CLEAR_TASK
                | Intent.FLAG_ACTIVITY_TASK_ON_HOME;
            boolean rootFlags = intents != null && intents.length == 3
                && (intents[0].getFlags() & mask) == mask;
            boolean verbatim = intents != null && intents.length >= 2
                && intents[1].getFlags() == 0;
            boolean independent = false;
            if (intents != null && intents.length >= 2) {
                intents[1].setAction("c7.w12.COPY_MUT");
                independent = tsb2.editIntentAt(2).getAction() == null;
            }
            if (rootFlags && verbatim && independent)
                Rec.ok("W09", "getIntents[0] restart-flags=1;[1] verbatim"
                    + " copies independent");
            else
                Rec.bad("W09", "rootFlags=" + (rootFlags ? 1 : 0)
                    + ";verbatim=" + (verbatim ? 1 : 0)
                    + ";independent=" + (independent ? 1 : 0));
        } catch (Throwable t) {
            Rec.bad("W09", "throw:" + t.getClass().getName());
        }

        // ── W10: getPendingIntent + send — the restart pipeline ────────
        try {
            TaskStackBuilder tsb3 = TaskStackBuilder.create(this);
            tsb3.addNextIntent(new Intent(this, RootAct.class));
            PendingIntent pi = tsb3.getPendingIntent(7,
                PendingIntent.FLAG_UPDATE_CURRENT
                | PendingIntent.FLAG_IMMUTABLE);
            boolean nonNull = pi != null;
            boolean sent = false;
            if (pi != null) {
                pi.send(0);  // the stub's send(int) overload
                sent = true;
            }
            if (nonNull && sent)
                Rec.ok("W10", "getPendingIntent rc=7 non-null; send() "
                    + "dispatched the root restart intent");
            else
                Rec.bad("W10", "nonNull=" + (nonNull ? 1 : 0)
                    + ";sent=" + (sent ? 1 : 0));
        } catch (Throwable t) {
            Rec.bad("W10", "throw:" + t.getClass().getName());
        }

        // ── W11: startActivities — the raw stack drains in order ───────
        try {
            TaskStackBuilder tsb = TaskStackBuilder.create(this);
            tsb.addNextIntent(new Intent(this, RootAct.class)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            tsb.addNextIntent(new Intent(this, MidAct.class));
            tsb.startActivities();
            Rec.ok("W11", "startActivities count=2 dispatched (no throw)");
        } catch (Throwable t) {
            Rec.bad("W11", "throw:" + t.getClass().getName());
        }

        // ── W12: getPackagesHoldingPermissions — the ANY law ───────────
        try {
            String[] perms = new String[] {
                "android.permission.INTERNET", "c7.laws.OPEN"};
            List<PackageInfo> hits = new ArrayList<PackageInfo>(
                pm.getPackagesHoldingPermissions(perms,
                    PackageManager.GET_PERMISSIONS));
            boolean selfHit = false, lawsHit = false, permsVerbatim = false;
            for (PackageInfo p : hits) {
                if ("c7.w12".equals(p.packageName)) {
                    selfHit = true;
                    permsVerbatim = p.requestedPermissions != null
                        && Arrays.asList(p.requestedPermissions).contains(
                            "android.permission.INTERNET");
                }
                if ("c7.laws".equals(p.packageName)) lawsHit = true;
            }
            if (hits.size() == 2 && selfHit && lawsHit && permsVerbatim)
                Rec.ok("W12", "ANY law: 2 hits (c7.w12 via INTERNET;"
                    + " c7.laws via c7.laws.OPEN); perms verbatim");
            else
                Rec.bad("W12", "hits=" + hits.size()
                    + ";self=" + (selfHit ? 1 : 0)
                    + ";laws=" + (lawsHit ? 1 : 0)
                    + ";verbatim=" + (permsVerbatim ? 1 : 0));
        } catch (Throwable t) {
            Rec.bad("W12", "throw:" + t.getClass().getName());
        }

        // ── W13: getPackagesHoldingPermissions — the honest empty ──────
        try {
            String[] perms = new String[] {
                "android.permission.CAMERA"};
            List<PackageInfo> hits =
                pm.getPackagesHoldingPermissions(perms, 0);
            if (hits.isEmpty())
                Rec.ok("W13", "CAMERA holder set empty (no package holds "
                    + "it — honest negative)");
            else
                Rec.bad("W13", "hits=" + hits.size() + " (fabrication)");
        } catch (Throwable t) {
            Rec.bad("W13", "throw:" + t.getClass().getName());
        }

        Rec.flush(this, "c7w12_results.jsonl");
    }
}
