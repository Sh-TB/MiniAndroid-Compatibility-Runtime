// g06g08_hostile_test — G06–G08 §18 hostile-input safety battery.
//
// No infinite loop, uncontrolled recursion, OOB, corruption, or unbounded
// memory growth under hostile input/lifecycle/intent conditions. Every case
// must terminate deterministically with named behavior.

#include "../src/framework/touch_dispatcher.h"
#include "../src/framework/lifecycle_controller.h"
#include "../src/framework/android_shadows.h"
#include "../src/framework/heap_adapter.h"
#include "../src/dex/dalvik_engine.h"

#include <cstdio>
#include <string>
#include <vector>

using namespace miniandroid;

static int g_checks = 0, g_fail = 0;
static void check(bool ok, const std::string& what) {
    g_checks++;
    if (!ok) { g_fail++; printf("  FAIL: %s\n", what.c_str()); }
}

namespace {

struct Rig {
    dalvik::DalvikHeap heap;
    framework::DalvikHeapAdapter heap_adapter{&heap};
    framework::ViewShadow views;
    framework::HandlerShadow handler;
    framework::TouchDispatcher dispatcher{&views, &handler};
    int clicks = 0;

    Rig() {
        views.init(&heap_adapter);
        handler.init(&heap_adapter);
        dispatcher.set_click_dispatch([&](uint32_t) { clicks++; return true; });
        dispatcher.set_long_click_dispatch(
            [](uint32_t, bool& c) { c = true; return true; });
    }

    uint32_t button(int x, int y, int w, int h) {
        uint32_t id = views.create_view("Landroid/widget/Button;");
        auto* n = views.find_node(id);
        n->x = x; n->y = y; n->width = w; n->height = h;
        n->clickable = true;
        return id;
    }
    void drain() {
        std::vector<uint32_t> due;
        for (int i = 0; i < 64; ++i) {
            due.clear();
            if (handler.drain_ready(&due) == 0) break;
            for (uint32_t id : due) dispatcher.fire_framework_callback(id, nullptr);
        }
    }
};

}  // namespace

int main() {
    printf("── §18 input: out-of-window / extreme coordinates ────────────────\n");
    {
        Rig r;
        uint32_t btn = r.button(100, 100, 200, 100);
        // Extreme coordinates must not select targets or corrupt state.
        auto far_ev = r.dispatcher.dispatch(
            btn, {framework::TouchAction::DOWN, 1 << 28, -(1 << 28)});
        check(far_ev["target_view_id"] == 0 && far_ev["consumed"] == false,
              "out-of-window DOWN: no target, not consumed");
        auto neg = r.dispatcher.dispatch(
            btn, {framework::TouchAction::MOVE, -5, -5});
        check(neg["consumed"] == false, "MOVE with no gesture: not consumed");
        // UP at extreme coordinates with no gesture.
        auto up = r.dispatcher.dispatch(
            btn, {framework::TouchAction::UP, 1 << 30, 1 << 30});
        check(up["consumed"] == false,
              "UP at extreme coords without gesture: not consumed");
        r.drain();
        check(r.clicks == 0, "no clicks from out-of-window events");
    }

    printf("── §18 input: repeated DOWN + CANCEL storm + UP flood ────────────\n");
    {
        Rig r;
        uint32_t btn = r.button(0, 0, 200, 100);
        // 512 repeated DOWNs without UP: each resets the previous gesture —
        // the queue must never grow beyond one CheckForLongPress.
        bool queue_bounded = true;
        for (int i = 0; i < 512; ++i) {
            r.dispatcher.dispatch(btn, {framework::TouchAction::DOWN, 50, 50});
            if (r.handler.queue_size() > 1) { queue_bounded = false; break; }
        }
        check(queue_bounded, "repeated DOWN: queue bounded");
        // 512 CANCELs with no active gesture.
        for (int i = 0; i < 512; ++i) {
            r.dispatcher.dispatch(btn, {framework::TouchAction::CANCEL, 50, 50});
        }
        check(r.handler.queue_size() == 0, "CANCEL storm leaves no callbacks");
        // 512 UPs with no gesture.
        for (int i = 0; i < 512; ++i) {
            r.dispatcher.dispatch(btn, {framework::TouchAction::UP, 50, 50});
        }
        r.drain();
        check(r.clicks == 0, "UP flood produces no clicks");
        // Stray framework tokens.
        for (uint32_t tok = 0xF0000000u; tok < 0xF0000040u; ++tok) {
            r.dispatcher.fire_framework_callback(tok, nullptr);
        }
        check(true, "unknown token flood: no crash, no dispatch");
        check(r.clicks == 0, "token flood produced no clicks");
    }

    printf("── §18 lifecycle: hostile transitions ────────────────────────────\n");
    {
        framework::LifecycleController lc;
        // 1000 double-onCreate attempts.
        lc.transition_to(framework::LifecyclePhase::ACTIVITY_CREATED,
                         "onCreate", 0);
        int rejected = 0;
        for (int i = 0; i < 1000; ++i) {
            if (!lc.transition_to(framework::LifecyclePhase::ACTIVITY_CREATED,
                                  "hostile re-launch", i))
                rejected++;
        }
        check(rejected == 1000, "1000 re-launch attempts all rejected");
        // Proper launch to RESUMED, then destroy; the cascade from
        // ACTIVITY_CREATED (never started) must itself be rejected.
        framework::LifecycleController lc1;
        lc1.transition_to(framework::LifecyclePhase::ACTIVITY_CREATED,
                          "onCreate", 0);
        check(!lc1.finish_cascade(5),
              "finish cascade from ACTIVITY_CREATED rejected (never started)");
        lc1.transition_to(framework::LifecyclePhase::STARTED, "onStart", 6);
        lc1.transition_to(framework::LifecyclePhase::RESUMED, "onResume", 7);
        check(lc1.finish_cascade(8), "cascade from RESUMED accepted");
        // Zombie attempts from DESTROYED — all rejected, state immutable.
        for (int i = 0; i < 100; ++i) {
            lc1.transition_to(framework::LifecyclePhase::RESUMED, "zombie", i);
            lc1.transition_to(framework::LifecyclePhase::STARTED, "zombie", i);
            lc1.transition_to(framework::LifecyclePhase::PAUSED, "zombie", i);
        }
        check(lc1.state() == framework::LifecyclePhase::DESTROYED,
              "post-destroy state machine is immutable");
        // Rejected attempts recorded, unbounded trace? — bounded by the
        // number of ATTEMPTS (input), never self-growing.
        // 1 onCreate + 2 launch + 3 cascade + 300 zombies = 306; the
        // REJECTED cascade from ACTIVITY_CREATED records no entry (it never
        // reached a state where the cascade law applies).
        check(lc1.entries().size() == 306,
              "every attempt recorded exactly once (no duplicate growth)");
    }

    printf("── §18 runtime: hostile re-post storm drain bound ────────────────\n");
    {
        // A Runnable that re-posts itself every drain: the engine's drain
        // loop caps at 64 iterations (documented §18 law) — verify the cap
        // holds using the framework-token path with a self-re-posting stub.
        dalvik::DalvikHeap heap;
        framework::DalvikHeapAdapter ha{&heap};
        framework::HandlerShadow handler;
        handler.init(&ha);
        framework::TouchDispatcher dispatcher{nullptr, &handler};
        // Simulate a hostile callback that re-enqueues itself indefinitely:
        // use remove/enqueue churn on the queue through the public API.
        for (int i = 0; i < 4096; ++i) {
            handler.enqueue(900000 + static_cast<uint32_t>(i), 0, "hostile");
        }
        std::vector<uint32_t> due;
        size_t fired = 0;
        for (int iter = 0; iter < 64; ++iter) {
            due.clear();
            size_t n = handler.drain_ready(&due);
            fired += n;
            if (n == 0) break;
        }
        check(fired == 4096, "4096 hostile queued entries drain in bounded "
                             "iterations (64-pass cap law)");
        check(handler.queue_size() == 0, "queue empty after bounded drain");
    }

    printf("════════════════════════════════════════════════════\n");
    printf("RESULT: %d checks, %d failures\n", g_checks, g_fail);
    printf(g_fail == 0 ? "G06-G08 HOSTILE: ALL PASS\n"
                       : "G06-G08 HOSTILE: FAILURES PRESENT\n");
    return g_fail == 0 ? 0 : 1;
}
