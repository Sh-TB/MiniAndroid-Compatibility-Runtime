// gesture_detector_shadow.h — S130 (R-NEW-429, CAP-GESTURE-131) GestureDetector law.
//
// SOURCE FIRST: docs/upstream/aosp/s130_laws/GestureDetector.java
// (aosp-mirror/platform_frameworks_base @ android-14.0.0_r2). Ported laws:
//  * L251-254 constants: LONGPRESS_TIMEOUT = ViewConfiguration.
//    getLongPressTimeout() = 500ms; TAP_TIMEOUT = getTapTimeout() = 100ms;
//    DOUBLE_TAP_TIMEOUT = getDoubleTapTimeout() = 300ms;
//    DOUBLE_TAP_MIN_TIME = 40ms.
//  * ViewConfiguration 8dp touch slop (densified 21px @420dpi), minimum
//    fling velocity 50dp/s (scaled 131.25 px/s), maximum 8000dp/s.
//  * onDown fires for EVERY DOWN (L~470: mIsDownstate... alwaysInTapRegion
//    reset); SHOW_PRESS scheduled at TAP_TIMEOUT; LONG_PRESS at
//    LONGPRESS_TIMEOUT (cancel on slop exit / UP / second event).
//  * MOVE beyond slop → onScroll(e1, e2, distanceX = prevFocus - focus,
//    distanceY) — L~610 cancels SHOW_PRESS/LONG_PRESS.
//  * UP in tap region → onSingleTapUp + (with a double-tap listener)
//    onSingleTapConfirmed after DOUBLE_TAP_TIMEOUT; velocity ≥ minFling →
//    onFling(e1, e2, vx, vy) via VelocityTracker LSQ2 law.
//  * DOUBLE_TAP: DOWN within DOUBLE_TAP_TIMEOUT of the previous DOWN's UP
//    and within double-tap slop → onDoubleTap(e).
//
// Determinism law: the detector is fed VIRTUAL-clock event times (one-queue
// law). Scheduled framework callbacks (SHOW_PRESS/LONG_PRESS/SINGLE_TAP_
// CONFIRMED) fire on the next feed()/poll(now) whose virtual time has passed
// — documented deviation from AOSP's real Handler posts (same bounded-pump
// family as the S129 40ms ASSUME_POINTER_STOPPED law).
#ifndef MINIANDROID_GESTURE_DETECTOR_SHADOW_H
#define MINIANDROID_GESTURE_DETECTOR_SHADOW_H

#include "shadow_registry.h"
#include "velocity_tracker.h"

#include <functional>
#include <string>
#include <unordered_map>
#include <vector>

namespace miniandroid { namespace framework {

// Pure GestureDetector model (deterministic; law-testable).
struct GdModel {
    static constexpr int64_t kTapTimeoutMs = 100;
    static constexpr int64_t kLongPressTimeoutMs = 500;
    static constexpr int64_t kDoubleTapTimeoutMs = 300;
    static constexpr int64_t kDoubleTapMinTimeMs = 40;
    static constexpr float kTouchSlopPx = 21.0f;         // 8dp @420dpi
    static constexpr float kDoubleTapSlopPx = 262.0f;    // 100dp @420dpi
    static constexpr float kMinFlingPxPerS = 131.25f;    // 50dp/s @420dpi
    static constexpr float kMaxFlingPxPerS = 21000.0f;   // 8000dp/s @420dpi

    struct Pending { std::string cb; int64_t due_ms = 0; };
    bool has_down = false;
    bool in_tap_region = true;
    bool is_double_tapping = false;
    float down_x = 0, down_y = 0;
    float prev_focus_x = 0, prev_focus_y = 0;
    float focus_x = 0, focus_y = 0;
    int64_t down_ms = 0, prev_up_ms = -100000;
    float prev_down_x = 0, prev_down_y = 0;
    bool long_press_fired = false, show_press_fired = false;
    VelocityTrackerModel tracker;
    std::vector<Pending> pending;

    // Callbacks: cb + up to 4 floats (x, y, distX/distVx, distY/distVy).
    using Cb = std::function<bool(const char*, float, float, float, float)>;
    Cb cb;
    void emit(const char* name, float a, float b, float c, float d) {
        if (cb) cb(name, a, b, c, d);
    }

    // Feed one event; returns true when a callback consumed the gesture.
    bool feed(int action, float x, float y, int64_t now);
    // Fire due scheduled callbacks (SHOW_PRESS/LONG_PRESS/SINGLE_TAP_CONFIRMED).
    void poll(int64_t now);
    void cancel_scheduled();
};

class GestureDetectorShadow : public Shadow {
public:
    std::string name() const override { return "GestureDetectorShadow"; }
    bool handles_class(const std::string& class_name) const override;
    CallResult dispatch(const CallContext& ctx) override;
    std::vector<std::string> implemented_methods() const override;
    std::vector<std::string> stubbed_methods() const override;

    // Engine wiring: clock + DEX callback dispatch (listener object id and
    // callback name are handed back; the engine materializes MotionEvents
    // and invokes the listener class method).
    using DexDispatch = std::function<void(uint32_t gd_obj, uint32_t listener_obj,
                                           const std::string& cb, float f1, float f2,
                                           float f3, float f4, bool& consumed)>;
    void set_now_fn(std::function<int64_t()> fn) { now_fn_ = std::move(fn); }
    void set_dex_dispatch(DexDispatch fn) { dex_dispatch_ = std::move(fn); }
    GdModel* model_for(uint32_t obj) {
        return states_.count(obj) ? &states_[obj].model : nullptr;
    }

    std::function<int64_t()> now_fn_;
    DexDispatch dex_dispatch_;
    // gd object id → (model, listener object id, listener class desc).
    struct GdState {
        GdModel model;
        uint32_t listener_obj = 0;
        std::string listener_class;
        bool longpress_enabled = true;
    };
    std::unordered_map<uint32_t, GdState> states_;
    void wire_(uint32_t gd_obj, GdState& st);
};

}}  // namespace miniandroid::framework

#endif  // MINIANDROID_GESTURE_DETECTOR_SHADOW_H
