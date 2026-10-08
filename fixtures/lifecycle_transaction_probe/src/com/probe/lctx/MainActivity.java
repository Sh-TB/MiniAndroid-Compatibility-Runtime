package com.probe.lctx;

import android.app.Activity;
import android.app.Application;
import android.os.Bundle;

/**
 * CONT-23 — F-NEW-277 LIFECYCLE-TRANSACTION PROBE (issue #384).
 *
 * Law under test (AOSP ActivityThread, API 29 pre/post pairing): a launched
 * activity record must receive, in order, the CREATED phase (PreCreated ->
 * onCreate -> Created -> PostCreated), the START phase (PreStarted -> onStart
 * -> Started -> PostStarted) and the RESUME phase (PreResumed -> onResume ->
 * Resumed -> PostResumed). The androidx ReportFragment$LifecycleCallbacks
 * drives LifecycleRegistry ON_START/ON_RESUME from the Post hooks — before
 * F-NEW-277 the engine dispatched ONLY the created phase, so every
 * lifecycle-aware primitive stayed suspended forever.
 *
 * The probe registers an ActivityLifecycleCallbacks ON THE ACTIVITY (the
 * API 29+ ReportFragment.injectIfNeededIn path). Each row prints from the
 * code whose contract it asserts:
 *
 *   LCTX-STARTED    : the app's onStart ran AFTER PreStarted (and before
 *                     Started/PostStarted) — pre/post pairing order
 *   LCTX-POSTSTART  : onActivityPostStarted dispatched after onStart
 *   LCTX-RESUMED    : the app's onResume ran AFTER PreResumed and AFTER the
 *                     start phase completed
 *   LCTX-POSTRESUME : onActivityPostResumed dispatched (engine fan-out
 *                     completes the AOSP transaction)
 *   LCTX-TRACE      : the full ordered mark trace
 */
public class MainActivity extends Activity {

    private static final StringBuilder marks = new StringBuilder();
    private static boolean sawPreStarted, sawStarted, sawPostStarted;
    private static boolean sawPreResumed, sawResumed, sawPostResumed;
    private static boolean startOrderOk, resumeOrderOk;

    private static void mark(String s) {
        if (marks.length() > 0) marks.append(',');
        marks.append(s);
    }

    private static void row(String id, boolean pass, String detail) {
        System.out.println(id + "|" + (pass ? "PASS" : "FAIL") + "|" + detail);
    }

    private final Application.ActivityLifecycleCallbacks cb =
            new Application.ActivityLifecycleCallbacks() {
                @Override public void onActivityCreated(Activity a, Bundle b) {
                    mark("created-cb");
                }
                @Override public void onActivityPreStarted(Activity a) {
                    if (a == MainActivity.this) { sawPreStarted = true; mark("preStarted"); }
                }
                @Override public void onActivityStarted(Activity a) {
                    if (a == MainActivity.this) { sawStarted = true; mark("started"); }
                }
                @Override public void onActivityPostStarted(Activity a) {
                    if (a == MainActivity.this) {
                        sawPostStarted = true; mark("postStarted");
                        row("LCTX-POSTSTART", true, "postStarted dispatched; marks=" + marks);
                    }
                }
                @Override public void onActivityPreResumed(Activity a) {
                    if (a == MainActivity.this) { sawPreResumed = true; mark("preResumed"); }
                }
                @Override public void onActivityResumed(Activity a) {
                    if (a == MainActivity.this) { sawResumed = true; mark("resumed"); }
                }
                @Override public void onActivityPostResumed(Activity a) {
                    if (a == MainActivity.this) {
                        sawPostResumed = true; mark("postResumed");
                        row("LCTX-POSTRESUME", true,
                                "postResumed dispatched; marks=" + marks);
                        row("LCTX-TRACE", true, marks.toString());
                    }
                }
                @Override public void onActivityPaused(Activity a) {}
                @Override public void onActivityStopped(Activity a) {}
                @Override public void onActivitySaveInstanceState(Activity a, Bundle b) {}
                @Override public void onActivityDestroyed(Activity a) {}
            };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // API 29+ activity-scoped registration — the exact
        // ReportFragment$LifecycleCallbacks.registerIn(activity) path.
        registerActivityLifecycleCallbacks(cb);
        mark("created");
    }

    @Override
    protected void onStart() {
        super.onStart();
        // AOSP order: PreStarted -> onStart -> Started -> PostStarted.
        startOrderOk = sawPreStarted && !sawStarted && !sawPostStarted;
        mark("onStart");
        row("LCTX-STARTED", startOrderOk,
                "onStart ran after preStarted=" + sawPreStarted
                        + " (started=" + sawStarted + " postStarted=" + sawPostStarted
                        + " orderOk=" + startOrderOk + ")");
    }

    @Override
    protected void onResume() {
        super.onResume();
        // AOSP order: PreResumed -> onResume -> Resumed -> PostResumed, and
        // the START phase (PostStarted) completed before the RESUME phase.
        resumeOrderOk = sawPreResumed && !sawResumed && !sawPostResumed
                && sawPostStarted;
        mark("onResume");
        row("LCTX-RESUMED", resumeOrderOk,
                "onResume ran after preResumed=" + sawPreResumed
                        + " postStarted=" + sawPostStarted
                        + " orderOk=" + resumeOrderOk);
    }
}
