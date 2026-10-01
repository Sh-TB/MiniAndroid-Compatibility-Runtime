// touch_dispatcher.h — G06 §4/§5 canonical input pipeline.
//
//   external input → window/root → hit testing → View.onTouchEvent law
//   → listener callback (scheduled on the ONE main-thread queue)
//   → consumption → state mutation → invalidation → next frame
//
// Framework callbacks (PerformClick / UnsetPressedState / CheckForLongPress)
// are AOSP-internal Runnables, not DEX objects. They are scheduled on the
// SAME virtual-clock HandlerShadow queue as app Runnables through reserved
// framework tokens (>= kFrameworkTokenBase), so callback ORDERING obeys the
// one-queue law: (ready_at_ms, enqueue seq) — identical to AOSP MessageQueue.
//
// Laws (AOSP android-14.0.0_r2, frameworks/base/core/java/android/view/):
//  * View.java L17044-17047: touchable = CLICKABLE || LONG_CLICKABLE ||
//    CONTEXT_CLICKABLE. Target selection ignores enabled state
//    (ViewGroup.getTouchTarget → canViewReceivePointerEvents: visibility only).
//  * View.java L17049-17057: DISABLED law — a disabled (touchable) view
//    CONSUMES the sequence but does not respond (no press, no click); UP
//    clears any pressed state; onTouchEvent returns `clickable`.
//  * View.java L17113-17125: ACTION_DOWN (non-scrolling container) →
//    setPressed(true) IMMEDIATELY + checkForLongClick(500ms).
//  * View.java L17133-17169: ACTION_UP && pressed && !mHasPerformedLongPress
//    → removeLongPressCallback + post(PerformClick) — posted, so pending
//    visual state updates run before the click — + UnsetPressedState posted
//    at PRESSED_STATE_DURATION (ViewConfiguration.java L72 = 64ms).
//  * View.java L17140-17143: UP takes focus FIRST when isFocusable() &&
//    isFocusableInTouchMode() && !isFocused(); focusTaken SUPPRESSES the
//    PerformClick post (that is how EditText takes focus without clicking).
//  * View.java L17172-17184: ACTION_CANCEL → setPressed(false) +
//    removeTapCallback + removeLongPressCallback + flag reset.
//  * View.java L17198-17208: ACTION_MOVE outside touch slop → remove tap +
//    long-press callbacks + setPressed(false).
//  * View.java CheckForLongPress: if (performLongClick()) mHasPerformedLongPress
//    = true → the UP click is suppressed.
//  * ViewConfiguration.java L122 TAP_TIMEOUT=100, L645 getLongPressTimeout()
//    = 500 default, L72 PRESSED_STATE_DURATION=64. Touch slop =
//    getScaledTouchSlop = 8dp (densified: 8 * 420/160 = 21px on the
//    campaign's 420dpi device).

#ifndef MINIANDROID_TOUCH_DISPATCHER_H
#define MINIANDROID_TOUCH_DISPATCHER_H

#include "android_shadows.h"
#include "../third_party/nlohmann_json/include/nlohmann/json.hpp"

#include <functional>
#include <string>

namespace miniandroid {
namespace framework {

enum class TouchAction { DOWN = 0, MOVE = 1, UP = 2, CANCEL = 3 };

const char* touch_action_name(TouchAction a);

struct TouchEvent {
    TouchAction action;
    int x = 0;
    int y = 0;
};

struct TouchConfig {
    int touch_slop_px = 21;                  // 8dp @ 420dpi device law
    int64_t long_press_timeout_ms = 500;     // ViewConfiguration.getLongPressTimeout
    int64_t pressed_state_duration_ms = 64;  // ViewConfiguration PRESSED_STATE_DURATION
};

class TouchDispatcher {
public:
    using Config = TouchConfig;

    // DEX callback bridges (owned by the engine). click_fn returns whether a
    // listener consumed the click; long_click_fn sets `consumed` per
    // onLongClick's return value.
    using ClickFn = std::function<bool(uint32_t view_id, float x, float y)>;
    using LongClickFn = std::function<bool(uint32_t view_id, bool& consumed)>;
    // F-110e (S62+): touch-listener dispatch (View.OnTouchListener.onTouch).
    // `consumed` = the listener's boolean return (true = owns the gesture).
    using TouchFn = std::function<bool(uint32_t view_id, int action, float x,
                                       float y, bool& consumed)>;
    // S128 (R-NEW-424, CAP-INPUT-100): ViewGroup.onInterceptTouchEvent dispatch.
    // `intercepted` = the override's boolean return (true = this ViewGroup
    // steals the gesture from its children — AOSP ViewGroup law).
    using InterceptFn = std::function<bool(uint32_t view_id, int action,
                                           float x, float y, bool& intercepted)>;

    TouchDispatcher(ViewShadow* views, HandlerShadow* handler,
                    const Config& cfg = Config());

    void set_click_dispatch(ClickFn fn) { click_fn_ = std::move(fn); }
    void set_long_click_dispatch(LongClickFn fn) { long_click_fn_ = std::move(fn); }
    void set_touch_dispatch(TouchFn fn) { touch_fn_ = std::move(fn); }
    void set_intercept_dispatch(InterceptFn fn) {
        intercept_fn_ = std::move(fn);
    }

    // Dispatch one event through the AOSP onTouchEvent law. Returns the
    // dispatch record (also appended to the cumulative trace).
    nlohmann::json dispatch(uint32_t root_id, const TouchEvent& ev);

    // Fire one framework callback drained from the HandlerShadow queue.
    // Returns false when the token is unknown (hostile input).
    bool fire_framework_callback(uint32_t token, nlohmann::json* record);

    // Cumulative per-run dispatch trace (deterministic order).
    const nlohmann::json& trace() const { return trace_; }
    void reset_trace() { trace_ = nlohmann::json::array(); }

    // The view that owns the active gesture (0 when idle).
    uint32_t gesture_target() const { return gesture_target_; }
    bool gesture_pressed() const { return pressed_; }
    bool has_performed_long_press() const { return has_performed_long_press_; }
    // S128 (CAP-INPUT-102): the TouchTarget dispatch chain — target first,
    // then each ancestor ViewGroup up to the root (AOSP: every ViewGroup in
    // the chain holds its own mFirstTouchTarget pointing down the chain).
    const std::vector<uint32_t>& gesture_chain() const {
        return gesture_chain_;
    }

    // Drop the active gesture without CANCEL semantics (new DOWN resets).
    void reset_gesture();

private:
    struct TokenState {
        uint32_t id = 0;   // 0 = not scheduled
        std::string label;
    };

    // S129 (R-NEW-426, CAP-INPUT-110): per-gesture TouchDelegate state.
    // AOSP TouchDelegate.java: mDelegateTargeted (DOWN inside mBounds),
    // mSlopBounds (mBounds inset by -touchSlop) gate MOVE/UP forwarding.
    struct DelegateState {
        bool targeted = false;      // mDelegateTargeted
        uint32_t owner = 0;         // view carrying the TouchDelegate
        uint32_t delegate = 0;      // mDelegateView
        int bl = 0, bt = 0, br = 0, bb = 0;  // absolute mBounds
        int slop = 0;               // mSlop (px)
        bool in_slop_bounds(int x, int y) const {
            return targeted && x >= bl - slop && x < br + slop &&
                   y >= bt - slop && y < bb + slop;
        }
    };

    uint32_t schedule(TokenState& slot, const char* label, int64_t delay_ms);
    void unschedule(TokenState& slot);
    void press(uint32_t view_id, int x, int y, nlohmann::json* rec);
    void unpress(uint32_t view_id, nlohmann::json* rec);
    bool view_touchable(const ViewShadow::ViewNode& n) const;
    // S128 (R-NEW-424, CAP-INPUT-100): intercept pass along the TouchTarget
    // chain; returns the intercepting view id (0 = none).
    uint32_t run_intercept_chain(int action, int x, int y, nlohmann::json* rec);
    // S129 (R-NEW-426, CAP-INPUT-110): consult `owner`'s TouchDelegate for a
    // DOWN at (x,y) — AOSP TouchDelegate.onTouchEvent DOWN arm:
    // mDelegateTargeted = mBounds.contains(x, y) (EXACT bounds, no slop).
    // On a hit the gesture retargets to the delegate view and the normal
    // DOWN response law runs ON THE DELEGATE (event translated to the
    // delegate's center — AOSP setLocation(w/2, h/2)). Returns true when
    // the delegate claimed the gesture.
    bool consult_delegate_down_(uint32_t owner, int x, int y,
                                uint32_t root_id, nlohmann::json* rec);
    // S129: AOSP ViewGroup.dispatchTouchEvent fallback arm — when no child
    // claims the DOWN, the deepest visible ViewGroup containing the point
    // runs its View.onTouchEvent (delegate consult, L17060-17064), then the
    // recursion unwinds through its ancestors. Returns true when claimed.
    bool consult_fallback_delegates_(uint32_t root_id, int x, int y,
                                     nlohmann::json* rec);
    // S129: the DOWN response law (View.onTouchEvent DOWN processing):
    // disabled law → OnTouchListener/onTouchEvent override arm →
    // pressed feedback + long-press arming. Shared by the normal target
    // path and the delegate-retarget path (same law, different view).
    void apply_down_response_(uint32_t target, int x, int y,
                              nlohmann::json* rec, bool& consumed);

    ViewShadow* views_;
    HandlerShadow* handler_;
    Config cfg_;
    ClickFn click_fn_;
    LongClickFn long_click_fn_;
    TouchFn touch_fn_;               // F-110e
    InterceptFn intercept_fn_;       // S128 CAP-INPUT-100
    bool touch_listener_owns_ = false;  // F-110e: listener consumed DOWN

    // Single active gesture (single-pointer model — multi-touch is an
    // explicit documented boundary).
    uint32_t gesture_target_ = 0;
    std::vector<uint32_t> gesture_chain_;  // S128 CAP-INPUT-102 TouchTarget chain
    int down_x_ = 0, down_y_ = 0;
    bool pressed_ = false;
    bool has_performed_long_press_ = false;
    // S129 (R-NEW-426, CAP-INPUT-110): TouchDelegate per-gesture state.
    DelegateState delegate_;

    TokenState tok_check_long_press_{{0}, "CheckForLongPress"};
    TokenState tok_perform_click_{{0}, "PerformClick"};
    TokenState tok_unset_pressed_{{0}, "UnsetPressedState"};

    nlohmann::json trace_ = nlohmann::json::array();
};

}  // namespace framework
}  // namespace miniandroid

#endif  // MINIANDROID_TOUCH_DISPATCHER_H
