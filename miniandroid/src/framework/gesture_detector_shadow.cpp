// gesture_detector_shadow.cpp — S130 (R-NEW-429) GestureDetector law port.
// Constants and callback order quoted from GestureDetector.java
// (android-14.0.0_r2) — see gesture_detector_shadow.h.
#include "gesture_detector_shadow.h"

#include <cmath>
#include <iostream>

namespace miniandroid { namespace framework {

static float sq_dist(float ax, float ay, float bx, float by) {
    const float dx = ax - bx, dy = ay - by;
    return dx * dx + dy * dy;
}

void GdModel::cancel_scheduled() {
    pending.clear();
}

void GdModel::poll(int64_t now) {
    // Fire due framework callbacks in schedule order (deterministic law).
    for (auto it = pending.begin(); it != pending.end();) {
        if (now >= it->due_ms) {
            const std::string name = it->cb;
            it = pending.erase(it);
            if (name == "onShowPress") {
                if (!show_press_fired) {
                    show_press_fired = true;
                    emit("onShowPress", 0, 0, 0, 0);
                }
            } else if (name == "onLongPress") {
                if (!long_press_fired) {
                    long_press_fired = true;
                    cancel_scheduled();
                    emit("onLongPress", focus_x, focus_y, 0, 0);
                }
            } else if (name == "onSingleTapConfirmed") {
                if (!has_down) emit("onSingleTapConfirmed", focus_x, focus_y, 0, 0);
            }
        } else {
            ++it;
        }
    }
}

bool GdModel::feed(int action, float x, float y, int64_t now) {
    // AOSP actions: DOWN=0, MOVE=2, UP=1, CANCEL=3.
    bool consumed = false;
    tracker.add_movement(now, action, x, y);
    switch (action) {
    case 0: {  // ACTION_DOWN
        // Double-tap law: second DOWN within DOUBLE_TAP_TIMEOUT of the
        // previous tap and inside the double-tap slop square.
        if (!is_double_tapping && now - prev_up_ms >= kDoubleTapMinTimeMs &&
            now - prev_up_ms <= kDoubleTapTimeoutMs &&
            sq_dist(x, y, prev_down_x, prev_down_y) <
                kDoubleTapSlopPx * kDoubleTapSlopPx) {
            is_double_tapping = true;
            emit("onDoubleTap", x, y, 0, 0);
            consumed = true;
        }
        has_down = true;
        in_tap_region = true;
        long_press_fired = false;
        show_press_fired = false;
        down_x = prev_focus_x = focus_x = x;
        down_y = prev_focus_y = focus_y = y;
        down_ms = now;
        emit("onDown", x, y, 0, 0);
        consumed = true;
        // SHOW_PRESS at TAP_TIMEOUT; LONG_PRESS at LONGPRESS_TIMEOUT
        // (GestureDetector.java L251-252 + handler posts).
        pending.push_back({"onShowPress", now + kTapTimeoutMs});
        pending.push_back({"onLongPress", now + kLongPressTimeoutMs});
        break;
    }
    case 2: {  // ACTION_MOVE
        focus_x = x; focus_y = y;
        poll(now);
        if (long_press_fired) return true;
        if (in_tap_region &&
            sq_dist(x, y, down_x, down_y) > kTouchSlopPx * kTouchSlopPx) {
            // Left the tap region: cancel press callbacks, start scrolling.
            in_tap_region = false;
            cancel_scheduled();
        }
        if (!in_tap_region) {
            const float dx = prev_focus_x - focus_x;   // AOSP distanceX law
            const float dy = prev_focus_y - focus_y;
            emit("onScroll", down_x, down_y, dx, dy);
            consumed = true;
        }
        prev_focus_x = x; prev_focus_y = y;
        break;
    }
    case 1: {  // ACTION_UP
        poll(now);
        prev_up_ms = now;
        prev_down_x = down_x; prev_down_y = down_y;
        const bool was_in_tap_region = in_tap_region;
        cancel_scheduled();
        has_down = false;
        if (long_press_fired) { is_double_tapping = false; return true; }
        if (was_in_tap_region) {
            emit("onSingleTapUp", x, y, 0, 0);
            consumed = true;
            // SINGLE_TAP_CONFIRMED after the double-tap window.
            pending.push_back({"onSingleTapConfirmed", now + kDoubleTapTimeoutMs});
        }
        // Fling law: velocity from the LSQ2 tracker; |v| >= minFling.
        tracker.compute_current_velocity(1000, kMaxFlingPxPerS);
        const float vx = tracker.x_velocity(), vy = tracker.y_velocity();
        if (!was_in_tap_region &&
            std::fabs(vx) > kMinFlingPxPerS || std::fabs(vy) > kMinFlingPxPerS) {
            emit("onFling", down_x, down_y, vx, vy);
            consumed = true;
        }
        is_double_tapping = false;
        break;
    }
    case 3: {  // ACTION_CANCEL
        cancel_scheduled();
        has_down = false;
        is_double_tapping = false;
        break;
    }
    default: break;
    }
    return consumed;
}

bool GestureDetectorShadow::handles_class(const std::string& class_name) const {
    return class_name.find("Landroid/view/GestureDetector;") == 0;
}

void GestureDetectorShadow::wire_(uint32_t gd_obj, GdState& st) {
    (void)st;  // the callback resolves the listener at CALL time (map may
               // rehash; per-call lookup keeps the listener fresh after
               // setOnDoubleTapListener swaps it).
    st.model.cb = [this, gd_obj](const char* cb, float f1, float f2,
                                 float f3, float f4) -> bool {
        bool consumed = false;
        auto it = states_.find(gd_obj);
        if (dex_dispatch_ && it != states_.end())
            dex_dispatch_(gd_obj, it->second.listener_obj, cb, f1, f2, f3,
                          f4, consumed);
        return consumed;
    };
}

CallResult GestureDetectorShadow::dispatch(const CallContext& ctx) {
    const std::string& m = ctx.method;
    if (m == "<init>") {
        // GestureDetector(context, listener[, handler]) — capture listener.
        const uint32_t id = ctx.receiver_id;
        if (id == 0) return CallResult::handled_void();
        GdState& st = states_[id];
        st.model = GdModel{};
        st.listener_obj = ctx.arg_as_object(1, 0);
        st.listener_class.clear();
        if (st.listener_obj && heap_)
            heap_->get_object_class(st.listener_obj, st.listener_class);
        wire_(id, st);
        std::cerr << "[GESTURE] ctor obj=" << id << " listener=o"
                  << st.listener_obj << " class=" << st.listener_class << std::endl;
        return CallResult::handled_void();
    }
    auto it = states_.find(ctx.receiver_id);
    if (it == states_.end()) {
        if (!ctx.has_receiver || ctx.receiver_id == 0) return CallResult::not_handled();
        it = states_.emplace(ctx.receiver_id, GdState{}).first;
        wire_(ctx.receiver_id, it->second);
    }
    GdState& st = it->second;
    const int64_t now = now_fn_ ? now_fn_() : 0;

    if (m == "onTouchEvent") {
        // Read the materialized MotionEvent fields (engine event law; the
        // HeapAllocator field adapters are out-param style).
        const uint32_t ev = ctx.arg_as_object(0, 0);
        int action = 0;
        float x = 0.0f, y = 0.0f, tf = 0.0f;
        if (heap_) {
            int32_t a32 = 0;
            if (heap_->get_object_int_field(ev, "__action__", a32)) action = a32;
            heap_->get_object_float_field(ev, "__x__", x);
            heap_->get_object_float_field(ev, "__y__", y);
            heap_->get_object_float_field(ev, "__time__", tf);
        }
        long long t = now;
        if (tf > 0) t = (long long)tf;
        const bool consumed = st.model.feed(action, x, y, t);
        return CallResult::handled_bool(consumed);
    }
    if (m == "setOnDoubleTapListener") {
        st.listener_obj = ctx.arg_as_object(0, st.listener_obj);
        st.listener_class.clear();
        if (st.listener_obj && heap_)
            heap_->get_object_class(st.listener_obj, st.listener_class);
        return CallResult::handled_void();
    }
    if (m == "isLongpressEnabled") return CallResult::handled_bool(st.longpress_enabled);
    if (m == "setIsLongpressEnabled") {
        st.longpress_enabled = ctx.arg_as_bool(0, true);
        return CallResult::handled_void();
    }
    if (m == "onGenericMotionEvent") return CallResult::handled_bool(false);
    return CallResult::not_handled();
}

std::vector<std::string> GestureDetectorShadow::implemented_methods() const {
    return {"<init>", "onTouchEvent", "setOnDoubleTapListener",
            "isLongpressEnabled", "setIsLongpressEnabled"};
}

std::vector<std::string> GestureDetectorShadow::stubbed_methods() const {
    // Documented boundary: the double-tap listener family is captured but
    // onDoubleTapEvent/onContextClick are not modeled beyond onDoubleTap.
    return {"onDoubleTapEvent", "onGenericMotionEvent"};
}

}}  // namespace miniandroid::framework
