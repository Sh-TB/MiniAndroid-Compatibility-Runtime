// touch_delegate_law_test — S129 (R-NEW-426, CAP-INPUT-110) law battery.
//
// Law references (AOSP android-14.0.0_r2, committed under
// docs/upstream/aosp/input_laws/):
//   * View.java L17060-17064: View.onTouchEvent consults mTouchDelegate
//     BEFORE the clickable switch — a hit forwards the event to the
//     delegate view's dispatchTouchEvent.
//   * TouchDelegate.java ctor: mBounds = bounds (OWNER-LOCAL coordinates);
//     mSlop = scaledTouchSlop; mSlopBounds = mBounds inset(-mSlop, -mSlop).
//   * TouchDelegate.onTouchEvent DOWN: mDelegateTargeted = mBounds.contains
//     (EXACT bounds); MOVE/UP: sendToDelegate = mDelegateTargeted, hit =
//     mSlopBounds.contains; hit → setLocation(delegate w/2, h/2),
//     !hit → setLocation(-2*slop, -2*slop); CANCEL: clear mDelegateTargeted.
//   * AOSP ViewGroup.dispatchTouchEvent: the owner's onTouchEvent (and thus
//     the delegate) runs when NO child claims the DOWN (fallback arm).
//
// Each CHECK names the law it guards.

#include "../src/framework/touch_dispatcher.h"
#include "../src/framework/heap_adapter.h"
#include "../src/dex/dalvik_engine.h"

#include <cstdio>

using namespace miniandroid;

static int g_checks = 0, g_fail = 0;
static void check(bool ok, const char* what) {
    g_checks++;
    if (!ok) {
        g_fail++;
        printf("  FAIL: %s\n", what);
    }
}

namespace {

struct Rig {
    dalvik::DalvikHeap heap;
    framework::DalvikHeapAdapter heap_adapter{&heap};
    framework::ViewShadow views;
    framework::HandlerShadow handler;
    framework::TouchDispatcher dispatcher{&views, &handler};

    int clicks = 0;
    uint32_t last_click_target = 0;

    Rig() {
        views.init(&heap_adapter);
        handler.init(&heap_adapter);
        dispatcher.set_click_dispatch([&](uint32_t id, float, float) {
            clicks++;
            last_click_target = id;
            return true;
        });
    }

    uint32_t button(int x, int y, int w, int h, bool enabled = true) {
        uint32_t id = views.create_view("Landroid/widget/Button;");
        auto* n = views.find_node(id);
        n->x = x; n->y = y; n->width = w; n->height = h;
        n->enabled = enabled;
        n->clickable = true;
        return id;
    }

    // A non-touchable container (FrameLayout law: not clickable).
    uint32_t container(int x, int y, int w, int h) {
        uint32_t id = views.create_view("Landroid/widget/FrameLayout;");
        auto* n = views.find_node(id);
        n->x = x; n->y = y; n->width = w; n->height = h;
        return id;
    }

    void set_delegate(uint32_t owner, uint32_t delegate, int l, int t, int r,
                      int b) {
        auto* n = views.find_node(owner);
        n->delegate_bounds_left = l;
        n->delegate_bounds_top = t;
        n->delegate_bounds_right = r;
        n->delegate_bounds_bottom = b;
        n->touch_delegate_view = delegate;
    }

    size_t drain() {
        size_t total = 0;
        for (int i = 0; i < 64; ++i) {
            std::vector<uint32_t> due;
            size_t n = handler.drain_ready(&due);
            total += n;
            if (n == 0) break;
            for (uint32_t id : due)
                dispatcher.fire_framework_callback(id, nullptr);
        }
        return total;
    }

    void advance(int64_t ms) { handler.advance_virtual(ms); }
};

}  // namespace

int main() {
    printf("── CAP-INPUT-110: fallback delegate retargets the DOWN ──────\n");
    {
        Rig r;
        uint32_t parent = r.container(0, 0, 400, 400);
        uint32_t btn = r.button(100, 100, 50, 50);
        uint32_t other = r.button(0, 0, 40, 40);
        r.views.add_child(parent, btn);
        r.views.add_child(parent, other);
        // Bounds in OWNER-LOCAL coords (AOSP ctor doc) — covers (80,80)
        // but NOT the button bounds and NOT `other`.
        r.set_delegate(parent, btn, 50, 50, 300, 300);

        auto down = r.dispatcher.dispatch(
            parent, {framework::TouchAction::DOWN, 80, 80});
        check(down["delegate_law"] == true,
              "no touchable child under the point → parent's delegate runs");
        check(down["target_view_id"] == btn,
              "gesture retargets to the DELEGATE view (mDelegateView)");
        check(down["consumed"] == true,
              "delegate claimed the DOWN (delegateView.dispatchTouchEvent)");
        auto* bn = r.views.find_node(btn);
        check(bn->pressed,
              "delegate receives the DOWN law: pressed feedback at center");
        r.advance(50);
        auto up = r.dispatcher.dispatch(
            parent, {framework::TouchAction::UP, 80, 80});
        check(up["delegate_up_forwarded"] == true,
              "UP forwards while mDelegateTargeted (TouchDelegate UP arm)");
        r.advance(64);
        r.drain();
        check(r.clicks == 1 && r.last_click_target == btn,
              "UP performs the DELEGATE's click (setLocation(w/2, h/2) law)");
    }

    printf("── CAP-INPUT-110: a real child under the point still wins ───\n");
    {
        Rig r;
        uint32_t parent = r.container(0, 0, 400, 400);
        uint32_t btn = r.button(100, 100, 50, 50);
        uint32_t other = r.button(0, 0, 40, 40);
        r.views.add_child(parent, btn);
        r.views.add_child(parent, other);
        r.set_delegate(parent, btn, 50, 50, 300, 300);

        // (20,20) hits `other` — a touchable child → the target path wins
        // and the delegate is never consulted (AOSP dispatch order).
        auto down = r.dispatcher.dispatch(
            parent, {framework::TouchAction::DOWN, 20, 20});
        check(down["target_view_id"] == other,
              "touchable child under the point beats the delegate");
        r.advance(50);
        r.dispatcher.dispatch(parent, {framework::TouchAction::UP, 20, 20});
        r.advance(64);
        r.drain();
        check(r.clicks == 1 && r.last_click_target == other,
              "click lands on the real target, not the delegate");
    }

    printf("── CAP-INPUT-110: DOWN uses EXACT mBounds (no slop) ─────────\n");
    {
        Rig r;
        uint32_t parent = r.container(0, 0, 400, 400);
        uint32_t btn = r.button(100, 100, 50, 50);
        r.views.add_child(parent, btn);
        r.set_delegate(parent, btn, 50, 50, 300, 300);
        // 21px slop would make (30,30) hit the slop bounds — but the DOWN
        // law tests the EXACT bounds: (30,30) is outside (50,50,300,300).
        auto down = r.dispatcher.dispatch(
            parent, {framework::TouchAction::DOWN, 30, 30});
        check(down["delegate_law"].is_null() &&
                  down["target_view_id"] == 0 &&
                  down["consumed"] == false,
              "DOWN outside mBounds (inside slop) does NOT delegate "
              "(mBounds.contains law)");
    }

    printf("── CAP-INPUT-110: MOVE outside slopBounds cancels ───────────\n");
    {
        Rig r;
        uint32_t parent = r.container(0, 0, 400, 400);
        uint32_t btn = r.button(100, 100, 50, 50);
        r.views.add_child(parent, btn);
        r.set_delegate(parent, btn, 50, 50, 300, 300);
        r.dispatcher.dispatch(parent, {framework::TouchAction::DOWN, 80, 80});
        auto* bn = r.views.find_node(btn);
        check(bn->pressed, "precondition: delegate pressed after DOWN");
        // (390,390) is outside mSlopBounds (300+21=321).
        r.advance(10);
        auto mv = r.dispatcher.dispatch(
            parent, {framework::TouchAction::MOVE, 390, 390});
        check(!bn->pressed,
              "MOVE outside mSlopBounds → delegate unpressed "
              "(setLocation(-2*slop) law)");
        r.dispatcher.dispatch(parent, {framework::TouchAction::UP, 390, 390});
        r.advance(64);
        r.drain();
        check(r.clicks == 0,
              "UP after leaving the slop bounds performs no click");
        (void)mv;
    }

    printf("── CAP-INPUT-110: MOVE within slopBounds keeps the tap ──────\n");
    {
        Rig r;
        uint32_t parent = r.container(0, 0, 400, 400);
        uint32_t btn = r.button(100, 100, 50, 50);
        r.views.add_child(parent, btn);
        r.set_delegate(parent, btn, 50, 50, 300, 300);
        r.dispatcher.dispatch(parent, {framework::TouchAction::DOWN, 80, 80});
        auto* bn = r.views.find_node(btn);
        r.advance(10);
        // (95,95) stays inside mSlopBounds (29..321) → forwarded at center.
        r.dispatcher.dispatch(parent, {framework::TouchAction::MOVE, 95, 95});
        check(bn->pressed,
              "MOVE within mSlopBounds keeps the delegate pressed");
        r.dispatcher.dispatch(parent, {framework::TouchAction::UP, 95, 95});
        r.advance(64);
        r.drain();
        check(r.clicks == 1 && r.last_click_target == btn,
              "in-bounds drift still performs the delegate's click");
    }

    printf("── CAP-INPUT-110: disabled delegate consumes without click ──\n");
    {
        Rig r;
        uint32_t parent = r.container(0, 0, 400, 400);
        uint32_t btn = r.button(100, 100, 50, 50, /*enabled=*/false);
        r.views.add_child(parent, btn);
        r.set_delegate(parent, btn, 50, 50, 300, 300);
        auto down = r.dispatcher.dispatch(
            parent, {framework::TouchAction::DOWN, 80, 80});
        check(down["target_view_id"] == btn && down["disabled_law"] == true,
              "disabled delegate consumes the DOWN without response");
        auto* bn = r.views.find_node(btn);
        check(!bn->pressed, "disabled delegate never presses");
        r.advance(50);
        r.dispatcher.dispatch(parent, {framework::TouchAction::UP, 80, 80});
        r.advance(64);
        r.drain();
        check(r.clicks == 0, "disabled delegate never clicks");
    }

    printf("── CAP-INPUT-110: CANCEL clears mDelegateTargeted ───────────\n");
    {
        Rig r;
        uint32_t parent = r.container(0, 0, 400, 400);
        uint32_t btn = r.button(100, 100, 50, 50);
        r.views.add_child(parent, btn);
        r.set_delegate(parent, btn, 50, 50, 300, 300);
        r.dispatcher.dispatch(parent, {framework::TouchAction::DOWN, 80, 80});
        auto* bn = r.views.find_node(btn);
        check(bn->pressed, "precondition: delegate pressed");
        r.dispatcher.dispatch(parent, {framework::TouchAction::CANCEL, 80, 80});
        check(!bn->pressed, "CANCEL unpresses the delegate");
        auto up = r.dispatcher.dispatch(
            parent, {framework::TouchAction::UP, 80, 80});
        check(up["consumed"] == false,
              "UP after CANCEL starts no gesture (target cleared)");
        r.advance(64);
        r.drain();
        check(r.clicks == 0, "no click after CANCEL");
    }

    printf("── CAP-INPUT-110: ancestor-chain delegate (recursion unwind) \n");
    {
        Rig r;
        uint32_t grand = r.container(0, 0, 600, 600);
        uint32_t parent = r.container(0, 0, 400, 400);
        uint32_t btn = r.button(100, 100, 50, 50);
        r.views.add_child(grand, parent);
        r.views.add_child(parent, btn);
        // The DELEGATE lives on the grandparent; the deepest visible view
        // containing (80,80) is `parent`, whose delegate is unset — the
        // AOSP recursion unwinds to the grandparent's onTouchEvent.
        r.set_delegate(grand, btn, 50, 50, 300, 300);
        auto down = r.dispatcher.dispatch(
            grand, {framework::TouchAction::DOWN, 80, 80});
        check(down["target_view_id"] == btn && down["delegate_law"] == true,
              "delegate on an ANCESTOR is consulted when the deeper view "
              "has none (fallback unwind law)");
        r.advance(50);
        r.dispatcher.dispatch(grand, {framework::TouchAction::UP, 80, 80});
        r.advance(64);
        r.drain();
        check(r.clicks == 1 && r.last_click_target == btn,
              "ancestor delegate completes the click");
    }

    printf("════════════════════════════════════════════════════\n");
    printf("RESULT: %d checks, %d failures\n", g_checks, g_fail);
    printf(g_fail == 0 ? "TOUCH DELEGATE LAW: ALL PASS\n"
                       : "TOUCH DELEGATE LAW: FAILURES PRESENT\n");
    return g_fail == 0 ? 0 : 1;
}
