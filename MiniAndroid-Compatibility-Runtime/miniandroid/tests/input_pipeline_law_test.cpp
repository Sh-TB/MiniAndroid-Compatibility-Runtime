// input_pipeline_law_test — G06 §4/§5 focused law battery.
//
// Law references (AOSP @android-14.0.0_r2, frameworks/base/core/java/):
//   * View.java L17044-17047  touchable = CLICKABLE || LONG_CLICKABLE
//   * View.java L17049-17057  disabled view consumes but does not respond
//   * View.java L17113-17125  DOWN → setPressed(true) + checkForLongClick(500ms)
//   * View.java L17133-17169  UP → removeLongPressCallback + post(PerformClick)
//                             + post(UnsetPressedState @ 64ms)
//   * View.java L17140-17143  focusable-in-touch-mode UP takes focus,
//                             focusTaken suppresses PerformClick
//   * View.java L17172-17184  CANCEL → unpress + remove callbacks
//   * View.java L17198-17208  MOVE outside touch slop → unpress + disarm
//   * View.java CheckForLongPress: performLongClick() consumed ⇒
//                             mHasPerformedLongPress ⇒ UP click suppressed
//   * ViewConfiguration.java L72 PRESSED_STATE_DURATION=64, L122 TAP_TIMEOUT=100,
//                             getLongPressTimeout()=500
//   * StateListDrawable.getStateDrawableIndex: first matching item in
//     document order wins; undeclared states are wildcards
//
// Each CHECK names the law it guards.

#include "../src/framework/touch_dispatcher.h"
#include "../src/framework/state_list.h"
#include "../src/framework/heap_adapter.h"
#include "../src/dex/dalvik_engine.h"

#include <cstdio>
#include <string>

using namespace miniandroid;

static int g_checks = 0, g_fail = 0;
static void check(bool ok, const std::string& what) {
    g_checks++;
    if (!ok) {
        g_fail++;
        printf("  FAIL: %s\n", what.c_str());
    }
}

namespace {

struct Rig {
    dalvik::DalvikHeap heap;
    framework::DalvikHeapAdapter heap_adapter{&heap};
    framework::ViewShadow views;
    framework::HandlerShadow handler;
    framework::TouchDispatcher dispatcher{&views, &handler};

    // stub callback observability
    int clicks = 0;
    uint32_t last_click_target = 0;
    int long_clicks = 0;
    bool long_click_consumes = true;
    uint32_t last_long_click_target = 0;

    Rig() {
        views.init(&heap_adapter);
        handler.init(&heap_adapter);
        dispatcher.set_click_dispatch([&](uint32_t id) {
            clicks++;
            last_click_target = id;
            return true;
        });
        dispatcher.set_long_click_dispatch([&](uint32_t id, bool& consumed) {
            long_clicks++;
            last_long_click_target = id;
            consumed = long_click_consumes;
            return true;
        });
    }

    uint32_t button(int x, int y, int w, int h, bool enabled = true,
                    bool clickable = true) {
        uint32_t id = views.create_view("Landroid/widget/Button;");
        auto* n = views.find_node(id);
        n->x = x; n->y = y; n->width = w; n->height = h;
        n->enabled = enabled;
        n->clickable = clickable;
        return id;
    }

    // Drain everything due at the CURRENT virtual instant.
    size_t drain() {
        size_t total = 0;
        for (int i = 0; i < 64; ++i) {
            std::vector<uint32_t> due;
            size_t n = handler.drain_ready(&due);
            total += n;
            if (n == 0) break;
            for (uint32_t id : due) dispatcher.fire_framework_callback(id, nullptr);
        }
        return total;
    }

    void advance(int64_t ms) { handler.advance_virtual(ms); }
};

// A minimal compiled <selector> AXML fixture is exercised through
// parse_state_list — but building a real AXML here would duplicate the
// AXML parser tests. The selector path is instead covered end-to-end by
// the G06-FIX external-fixture golden (real aapt2 output). The pick law is
// unit-tested directly below.

}  // namespace

int main() {
    printf("── G06 §4: tap law (DOWN → press → UP → queued PerformClick) ──\n");
    {
        Rig r;
        uint32_t btn = r.button(100, 200, 300, 100);
        r.dispatcher.dispatch(btn, {framework::TouchAction::DOWN, 150, 250});
        auto* n = r.views.find_node(btn);
        check(n->pressed, "L17113-17125: DOWN sets pressed immediately");
        check(r.handler.queue_size() == 1,
              "DOWN arms exactly one callback (CheckForLongPress @500ms)");

        r.advance(50);
        r.dispatcher.dispatch(btn, {framework::TouchAction::UP, 150, 250});
        check(n->pressed,
              "UP does not unpress synchronously (UnsetPressedState posted)");
        check(r.clicks == 0,
              "L17163-17168: click is POSTED, not dispatched inline");
        size_t drained_now = r.drain();
        check(drained_now >= 1, "PerformClick due at UP instant drains");
        check(r.clicks == 1, "PerformClick fired exactly once");
        check(r.last_click_target == btn, "PerformClick targets the hit view");
        check(n->pressed, "pressed still set at t+64 not yet reached");
        r.advance(64);
        size_t drained_unpress = r.drain();
        check(drained_unpress >= 1, "UnsetPressedState due at +64ms drains");
        check(!n->pressed, "L17174-17179: UnsetPressedState clears pressed");
        check(r.long_clicks == 0, "no long-press fired for a fast tap");
    }

    printf("── G06 §4: disabled law ──────────────────────────────────────────\n");
    {
        Rig r;
        uint32_t btn = r.button(0, 0, 200, 100, /*enabled=*/false);
        auto down = r.dispatcher.dispatch(
            btn, {framework::TouchAction::DOWN, 50, 50});
        auto* n = r.views.find_node(btn);
        check(down["consumed"] == true,
              "L17049-17057: disabled touchable view CONSUMES the DOWN");
        check(!n->pressed, "disabled view never enters pressed state");
        r.advance(50);
        auto up = r.dispatcher.dispatch(btn, {framework::TouchAction::UP, 50, 50});
        check(up["consumed"] == true, "disabled view consumes the UP too");
        r.advance(64);
        r.drain();
        check(r.clicks == 0, "disabled view never fires PerformClick");
        check(r.long_clicks == 0, "disabled view never fires long-press");
        check(!n->pressed, "no pressed residue on disabled view");
    }

    printf("── G06 §4: long-press law (consumed ⇒ UP click suppressed) ──────\n");
    {
        Rig r;
        uint32_t btn = r.button(0, 0, 200, 100);
        auto* n = r.views.find_node(btn);
        r.dispatcher.dispatch(btn, {framework::TouchAction::DOWN, 100, 50});
        r.advance(500);
        size_t drained = r.drain();
        check(drained >= 1, "CheckForLongPress due at +500ms drains");
        check(r.long_clicks == 1, "performLongClick dispatched at 500ms law");
        check(r.long_click_consumes && r.dispatcher.has_performed_long_press(),
              "CheckForLongPress: consumed long press sets "
              "mHasPerformedLongPress");
        r.advance(30);
        r.dispatcher.dispatch(btn, {framework::TouchAction::UP, 100, 50});
        r.advance(64);
        r.drain();
        check(r.clicks == 0,
              "GOLDEN-02 law: consumed long press SUPPRESSES the UP click");
        check(!n->pressed, "UnsetPressedState still clears pressed after "
                           "long-press UP");
    }

    printf("── G06 §4: long-press NOT consumed ⇒ UP performs click ─────────\n");
    {
        Rig r;
        uint32_t btn = r.button(0, 0, 200, 100);
        r.long_click_consumes = false;  // onLongClick returns false
        r.dispatcher.dispatch(btn, {framework::TouchAction::DOWN, 100, 50});
        r.advance(500);
        r.drain();
        r.advance(30);
        r.dispatcher.dispatch(btn, {framework::TouchAction::UP, 100, 50});
        r.advance(64);
        r.drain();
        check(r.clicks == 1,
              "unconsumed long press → UP performs the click (View.java)");
    }

    printf("── G06 §4: CANCEL law ────────────────────────────────────────────\n");
    {
        Rig r;
        uint32_t btn = r.button(0, 0, 200, 100);
        auto* n = r.views.find_node(btn);
        r.dispatcher.dispatch(btn, {framework::TouchAction::DOWN, 100, 50});
        check(n->pressed, "precondition: pressed after DOWN");
        auto cancel = r.dispatcher.dispatch(
            btn, {framework::TouchAction::CANCEL, 100, 50});
        check(!n->pressed, "L17172-17184: CANCEL clears pressed");
        check(r.handler.queue_size() == 0,
              "CANCEL removes CheckForLongPress from the queue");
        auto up = r.dispatcher.dispatch(btn, {framework::TouchAction::UP, 100, 50});
        check(up["consumed"] == false,
              "UP after CANCEL starts no gesture (not consumed)");
        r.advance(64);
        r.drain();
        check(r.clicks == 0, "CANCEL kills the gesture: no click on later UP");
    }

    printf("── G06 §4: MOVE-outside law ──────────────────────────────────────\n");
    {
        Rig r;
        uint32_t btn = r.button(100, 100, 200, 100);
        auto* n = r.views.find_node(btn);
        r.dispatcher.dispatch(btn, {framework::TouchAction::DOWN, 150, 150});
        check(n->pressed, "precondition: pressed after DOWN");
        // 400px away — far beyond the 21px touch slop (8dp @420dpi).
        r.dispatcher.dispatch(btn, {framework::TouchAction::MOVE, 500, 500});
        check(!n->pressed,
              "L17198-17208: MOVE outside touch slop clears pressed");
        check(r.handler.queue_size() == 0,
              "MOVE outside removes the long-press callback");
        r.dispatcher.dispatch(btn, {framework::TouchAction::UP, 500, 500});
        r.advance(64);
        r.drain();
        check(r.clicks == 0,
              "pressed was cleared → UP performs no click (View.java: only "
              "pressed/prepressed UP clicks)");
    }

    printf("── G06 §4: target law (deepest touchable, visibility gating) ────\n");
    {
        Rig r;
        uint32_t parent = r.button(0, 0, 400, 400);
        uint32_t child = r.button(50, 50, 100, 100);
        r.views.add_child(parent, child);
        uint32_t invisible = r.button(300, 300, 80, 80);
        r.views.find_node(invisible)->visibility = 4;  // INVISIBLE
        r.views.add_child(parent, invisible);

        auto down = r.dispatcher.dispatch(
            parent, {framework::TouchAction::DOWN, 80, 80});
        check(down["target_view_id"] == child,
              "deepest touchable view under the point wins");
        r.dispatcher.dispatch(parent, {framework::TouchAction::CANCEL, 80, 80});

        auto down2 = r.dispatcher.dispatch(
            parent, {framework::TouchAction::DOWN, 330, 330});
        check(down2["target_view_id"] == parent,
              "INVISIBLE child is not a touch target (parent receives)");
        r.dispatcher.dispatch(parent, {framework::TouchAction::CANCEL, 330, 330});

        auto down3 = r.dispatcher.dispatch(
            parent, {framework::TouchAction::DOWN, 900, 900});
        check(down3["target_view_id"] == 0 && down3["consumed"] == false,
              "outside every target → not consumed, no dispatch");
    }

    printf("── G06 §5: focus law (focusable-in-touch-mode) ───────────────────\n");
    {
        Rig r;
        uint32_t field = r.button(0, 0, 300, 100);
        auto* n = r.views.find_node(field);
        n->focusable = true;
        n->focusable_in_touch_mode = true;
        r.dispatcher.dispatch(field, {framework::TouchAction::DOWN, 50, 50});
        r.advance(50);
        r.dispatcher.dispatch(field, {framework::TouchAction::UP, 50, 50});
        check(n->focused,
              "L17140-17143: UP takes focus for focusable-in-touch-mode");
        r.advance(64);
        r.drain();
        check(r.clicks == 0,
              "focusTaken SUPPRESSES PerformClick (EditText law: tap focuses, "
              "does not click)");
        // Second tap on already-focused view → normal click.
        r.dispatcher.dispatch(field, {framework::TouchAction::DOWN, 50, 50});
        r.advance(50);
        r.dispatcher.dispatch(field, {framework::TouchAction::UP, 50, 50});
        r.advance(64);
        r.drain();
        check(r.clicks == 1,
              "already-focused view clicks normally on the next tap");
    }

    printf("── G06 §5: state-list pick law (StateListDrawable) ───────────────\n");
    {
        std::vector<framework::ViewShadow::ViewNode::BgStateItem> items;
        using Item = framework::ViewShadow::ViewNode::BgStateItem;
        // Document order matters: pressed item FIRST (matches AOSP selector
        // convention where more specific states come first).
        Item pressed_item;
        pressed_item.state_pressed = 1;
        pressed_item.color = 0xFFFF5252u;
        pressed_item.has_color = true;
        Item disabled_item;
        disabled_item.state_enabled = 0;
        disabled_item.color = 0xFFBDBDBDu;
        disabled_item.has_color = true;
        Item default_item;
        default_item.color = 0xFF2196F3u;
        default_item.has_color = true;
        items = {pressed_item, disabled_item, default_item};

        uint32_t c = 0;
        std::string p;
        bool ok = framework::pick_state_list(items, /*pressed=*/true,
                                             /*enabled=*/true,
                                             /*selected=*/false, &c, &p);
        check(ok && c == 0xFFFF5252u,
              "getStateDrawableIndex law: pressed=true matches item 1");

        ok = framework::pick_state_list(items, false, false, false, &c, &p);
        check(ok && c == 0xFFBDBDBDu,
              "state_enabled=\"false\" item matches a disabled view");

        ok = framework::pick_state_list(items, false, true, false, &c, &p);
        check(ok && c == 0xFF2196F3u,
              "no match on items 1-2 → wildcard default item wins");

        // Reverse order proves document-order precedence: a matching item
        // earlier in the list beats the wildcard even if a later item also
        // matches.
        std::vector<Item> reversed{default_item, pressed_item};
        ok = framework::pick_state_list(reversed, true, true, false, &c, &p);
        check(ok && c == 0xFF2196F3u,
              "FIRST matching item in document order wins (not best match)");
    }

    printf("── G06 §4: hostile input (stray UP, repeated DOWN, no target) ───\n");
    {
        Rig r;
        // Stray UP with no gesture.
        auto up = r.dispatcher.dispatch(0, {framework::TouchAction::UP, 5, 5});
        check(up["consumed"] == false, "stray UP without DOWN is not consumed");
        // Repeated DOWN without UP: the second DOWN resets the gesture
        // defensively (no stale-callback leak).
        uint32_t btn = r.button(0, 0, 200, 100);
        r.dispatcher.dispatch(btn, {framework::TouchAction::DOWN, 10, 10});
        r.dispatcher.dispatch(btn, {framework::TouchAction::DOWN, 10, 10});
        check(r.handler.queue_size() == 1,
              "repeated DOWN: exactly one long-press check armed (no leak)");
        r.dispatcher.dispatch(btn, {framework::TouchAction::CANCEL, 10, 10});
        // Unknown framework token.
        bool ok = r.dispatcher.fire_framework_callback(0xF1234567, nullptr);
        check(!ok, "unknown framework token rejected (hostile-safe)");
    }

    printf("════════════════════════════════════════════════════\n");
    printf("RESULT: %d checks, %d failures\n", g_checks, g_fail);
    printf(g_fail == 0 ? "INPUT PIPELINE LAW: ALL PASS\n"
                       : "INPUT PIPELINE LAW: FAILURES PRESENT\n");
    return g_fail == 0 ? 0 : 1;
}
