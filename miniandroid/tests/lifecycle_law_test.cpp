// lifecycle_law_test — G07 §7/§10 focused law battery.
//
// Laws (AOSP @android-14.0.0_r2, frameworks/base/core/java/android/app/):
//   * ActivityThread.performLaunchActivity L3653: instantiate + onCreate
//   * handleResumeActivity L4986: onStart (restart) → onResume
//   * handlePauseActivity L5152: onPause — FIRST callback of a switch
//   * handleStopActivity L5408: onStop — LAST callback of a switch
//   * performDestroyActivity: onDestroy
//   * finish() = REQUEST; cascade applied at a frame boundary
//   * MessageQueue (android/os/MessageQueue.java): dispatch in (when, seq)
//     order — a due message behind a not-due entry MUST still fire
//
// Each CHECK names the law it guards.

#include "../src/framework/lifecycle_controller.h"
#include "../src/framework/android_shadows.h"
#include "../src/framework/heap_adapter.h"
#include "../src/dex/dalvik_engine.h"

#include <algorithm>
#include <cstdio>
#include <string>

using namespace miniandroid;

static int g_checks = 0, g_fail = 0;
static void check(bool ok, const std::string& what) {
    g_checks++;
    if (!ok) { g_fail++; printf("  FAIL: %s\n", what.c_str()); }
}

using framework::LifecycleController;
using framework::LifecyclePhase;

int main() {
    printf("── G07 §10: canonical launch sequence ───────────────────────────\n");
    {
        LifecycleController lc;
        check(lc.state() == LifecyclePhase::PROCESS_CREATED,
              "initial state = PROCESS_CREATED");
        check(lc.transition_to(LifecyclePhase::ACTIVITY_CREATED,
                               "onCreate via DEX", 1000),
              "PROCESS_CREATED → ACTIVITY_CREATED (performLaunchActivity)");
        check(lc.transition_to(LifecyclePhase::STARTED, "onStart via DEX",
                               1000),
              "ACTIVITY_CREATED → STARTED");
        check(lc.transition_to(LifecyclePhase::RESUMED, "onResume via DEX",
                               1000),
              "STARTED → RESUMED (handleResumeActivity)");
        check(lc.entries().size() == 3, "all transitions recorded");
        check(lc.entries()[0].success && lc.entries()[1].success &&
                  lc.entries()[2].success,
              "all launch transitions valid");
    }

    printf("── G07 §10: finish cascade order ─────────────────────────────────\n");
    {
        LifecycleController lc;
        lc.transition_to(LifecyclePhase::ACTIVITY_CREATED, "onCreate", 0);
        lc.transition_to(LifecyclePhase::STARTED, "onStart", 0);
        lc.transition_to(LifecyclePhase::RESUMED, "onResume", 0);
        check(lc.finish_cascade(5000), "finish cascade from RESUMED accepted");
        check(lc.state() == LifecyclePhase::DESTROYED,
              "RESUMED → PAUSED → STOPPED → DESTROYED (ActivityThread law)");
        const auto& es = lc.entries();
        check(es.size() == 6, "cascade recorded 3 intermediate transitions");
        check(es[3].to == LifecyclePhase::PAUSED &&
                  es[4].to == LifecyclePhase::STOPPED &&
                  es[5].to == LifecyclePhase::DESTROYED,
              "cascade order: onPause → onStop → onDestroy (§10 machine)");
        check(es[3].virtual_ms == 5000 && es[4].virtual_ms == 5000 &&
                  es[5].virtual_ms == 5000,
              "cascade transitions carry the frame-boundary timestamp");
    }

    printf("── G07 §10: hostile transitions rejected + recorded ─────────────\n");
    {
        LifecycleController lc;
        // onCreate twice — no double-launch.
        lc.transition_to(LifecyclePhase::ACTIVITY_CREATED, "onCreate", 10);
        check(!lc.transition_to(LifecyclePhase::ACTIVITY_CREATED, "onCreate #2",
                                20),
              "double onCreate rejected (performLaunchActivity runs once)");
        // resume before start.
        check(!lc.transition_to(LifecyclePhase::RESUMED, "hostile resume", 30),
              "ACTIVITY_CREATED → RESUMED rejected (no onStart shortcut)");
        // destroy from PROCESS_CREATED.
        LifecycleController lc2;
        check(!lc2.finish_cascade(40),
              "finish cascade from PROCESS_CREATED rejected (never launched)");
        // post-destroy everything rejected.
        LifecycleController lc3;
        lc3.transition_to(LifecyclePhase::ACTIVITY_CREATED, "onCreate", 0);
        lc3.transition_to(LifecyclePhase::STARTED, "onStart", 0);
        lc3.transition_to(LifecyclePhase::RESUMED, "onResume", 0);
        lc3.finish_cascade(50);
        check(!lc3.transition_to(LifecyclePhase::RESUMED, "zombie resume", 60),
              "RESUME after DESTROY rejected (no zombie activities)");
        check(!lc3.transition_to(LifecyclePhase::ACTIVITY_CREATED,
                                 "zombie onCreate", 70),
              "re-create after DESTROY rejected");
        // rejected attempts recorded as evidence.
        int failed = 0;
        for (const auto& e : lc3.entries())
            if (!e.success) failed++;
        check(failed >= 2,
              "rejected transitions RECORDED (success=false evidence)");
    }

    printf("── G07 §10: restart law (STOPPED → STARTED) ──────────────────────\n");
    {
        LifecycleController lc;
        lc.transition_to(LifecyclePhase::ACTIVITY_CREATED, "onCreate", 0);
        lc.transition_to(LifecyclePhase::STARTED, "onStart", 0);
        lc.transition_to(LifecyclePhase::RESUMED, "onResume", 0);
        lc.transition_to(LifecyclePhase::PAUSED, "onPause", 0);
        lc.transition_to(LifecyclePhase::STOPPED, "onStop", 0);
        // A comes back to foreground (e.g. B finished): onRestart → onStart
        check(lc.transition_to(LifecyclePhase::STARTED, "onRestart+onStart",
                               100),
              "STOPPED → STARTED restart law (handleResumeActivity from "
              "stopped)");
        check(lc.transition_to(LifecyclePhase::RESUMED, "onResume", 110),
              "restart → RESUMED completes the return transition");
    }

    printf("── G07 §8: MessageQueue (when, seq) ordering law ─────────────────\n");
    {
        // FIND-G07-003 regression: a due message behind a NOT-due entry
        // must still fire. postDelayed(A, 1000) then post(B, 0): at t=100
        // B fires even though A sits at the queue head.
        dalvik::DalvikHeap heap;
        framework::DalvikHeapAdapter heap_adapter{&heap};
        framework::HandlerShadow handler;
        handler.init(&heap_adapter);
        handler.enqueue(101, 1000, "A");
        handler.enqueue(102, 0, "B");
        handler.advance_virtual(100);
        std::vector<uint32_t> due;
        size_t n = handler.drain_ready(&due);
        check(n == 1 && due[0] == 102,
              "due message behind a not-due head fires FIRST "
              "(MessageQueue when-order law — FIND-G07-003)");
        handler.advance_virtual(900);
        due.clear();  // drain_ready APPENDS to the out vector (contract)
        n = handler.drain_ready(&due);
        check(n == 1 && due[0] == 101,
              "not-due entry fires when its when arrives");

        // FIFO tie-break at the same `when` (EXP-088 acceptance law).
        framework::HandlerShadow h2;
        h2.init(&heap_adapter);
        h2.enqueue(201, 0, "A");
        h2.enqueue(202, 0, "B");
        h2.enqueue(203, 400, "C");
        h2.settle();
        due.clear();
        n = h2.drain_ready(&due);
        check(n == 3 && due[0] == 201 && due[1] == 202 && due[2] == 203,
              "same-when entries keep FIFO (EXP-088 law preserved)");
    }

    printf("════════════════════════════════════════════════════\n");
    printf("RESULT: %d checks, %d failures\n", g_checks, g_fail);
    printf(g_fail == 0 ? "LIFECYCLE LAW: ALL PASS\n"
                       : "LIFECYCLE LAW: FAILURES PRESENT\n");
    return g_fail == 0 ? 0 : 1;
}
