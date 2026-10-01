// velocity_tracker.h — S129 (R-NEW-425, CAP-INPUT-108): VelocityTracker law.
//
// AOSP android-14.0.0_r2 sources (committed under docs/upstream/aosp/input_laws/):
//   * VelocityTracker.java  — Java surface: obtain()/recycle()/clear()/
//     addMovement(MotionEvent)/computeCurrentVelocity(units[, max])/
//     getXVelocity()/getYVelocity()/getAxisVelocity(axis[, id]).
//     ACTIVE_POINTER_ID = -1. computeCurrentVelocity(int) == max Float.MAX_VALUE.
//   * VelocityTracker.h L179-227 — LSQ2 = LeastSquaresVelocityTrackerStrategy
//     (degree 2, Weighting::NONE); HORIZON = 100 ms; HISTORY_SIZE = 20.
//   * VelocityTracker.cpp (native) — the law this model ports 1:1:
//       - addMovement(MotionEvent): ACTION_DOWN → clear() then sample both
//         axes; ACTION_MOVE → sample; ACTION_UP / ACTION_POINTER_UP /
//         ACTION_CANCEL → EARLY RETURN (the UP position is never added —
//         "we want to preserve the last known velocity of the pointers");
//         other actions ignored.
//       - VelocityTracker::addMovement(eventTime, pointerId, axis, position):
//         when the same pointer re-fires after more than
//         ASSUME_POINTER_STOPPED_TIME (40 ms) the strategies are cleared
//         ("Assume that all pointers have stopped").
//       - LeastSquaresVelocityTrackerStrategy::getEstimator: iterate newest →
//         oldest; stop when age > HORIZON; per sample
//         time = -age (SECONDS), weight = 1 (Weighting::NONE);
//         degree = min(2, m-1); degree==2 → solveUnweightedLeastSquaresDeg2
//         (closed-form quadratic fit y = a·x² + b·x + c via
//         Sxx/Sxy/Sxx2/Sx2y/Sx2x2 sums); degree==1 → 2x2 normal equations
//         (AOSP solveLeastSquares with unit weights); velocity = coeff[1]
//         (d(position)/d(time) at the newest sample, t=0).
//       - VelocityTracker::getComputedVelocity(units, maxVelocity):
//         adjustedVelocity = clamp(velocity * units / 1000, ±maxVelocity).
//         A single sample (degree 0) yields NO velocity (value_or(0) → 0).
//
// The DEX bridge (VelocityTrackerShadow) claims Landroid/view/VelocityTracker;
// and binds obtain/recycle/clear/addMovement/computeCurrentVelocity/
// getXVelocity/getYVelocity/getAxisVelocity/isAxisSupported. Event times come
// from the materialized MotionEvent __time__ field (virtual-clock ms —
// deterministic under the one-queue law), so computed velocities are
// byte-stable across runs.

#ifndef MINIANDROID_VELOCITY_TRACKER_H
#define MINIANDROID_VELOCITY_TRACKER_H

#include "shadow_registry.h"

#include <cstdint>
#include <unordered_map>
#include <vector>

namespace miniandroid {
namespace framework {

// Pure algorithm — no engine dependencies (unit-testable per the campaign
// law-test gate).
class VelocityTrackerModel {
public:
    // AOSP MotionEvent action-masked values (MotionEvent.java table — the
    // same values the dispatcher and the engine constants table use).
    static constexpr int kActionDown = 0;
    static constexpr int kActionUp = 1;
    static constexpr int kActionMove = 2;
    static constexpr int kActionCancel = 3;

    // AOSP VelocityTracker.h L208: HORIZON = 100 ms.
    static constexpr int64_t kHorizonMs = 100;
    // AOSP VelocityTracker.h L210: HISTORY_SIZE = 20 samples per axis.
    static constexpr size_t kHistorySize = 20;
    // AOSP VelocityTracker.cpp L79: ASSUME_POINTER_STOPPED_TIME = 40 ms.
    static constexpr int64_t kAssumeStoppedMs = 40;

    // Reset the tracker back to its initial state (VelocityTracker.clear()).
    void clear();

    // addMovement(MotionEvent) — one call per received event. Law:
    // DOWN → clear + sample; MOVE → sample; UP/CANCEL/others → early return;
    // a MOVE arriving > 40 ms after the previous event resets the samples.
    void add_movement(int64_t event_time_ms, int action_masked, float x,
                      float y);

    // computeCurrentVelocity(units, maxVelocity) — fits both axes.
    void compute_current_velocity(int units, float max_velocity);
    // computeCurrentVelocity(units) — max = Float.MAX_VALUE.
    void compute_current_velocity(int units);

    // getXVelocity()/getYVelocity() — the LAST COMPUTED velocity
    // (0 before the first computeCurrentVelocity, AOSP value_or(0) law).
    float x_velocity() const { return x_velocity_; }
    float y_velocity() const { return y_velocity_; }

    // Test/diagnostic introspection: samples currently retained per axis.
    size_t x_sample_count() const { return x_samples_.size(); }
    size_t y_sample_count() const { return y_samples_.size(); }

private:
    struct Sample {
        int64_t t_ms = 0;  // virtual event time (ms)
        float pos = 0.0f;  // position along one axis (px)
    };

    // Per-axis LSQ2 estimator — returns coeff[1] (px per SECOND) or false
    // when no velocity exists (fewer than 2 samples in the horizon).
    bool axis_velocity_(const std::vector<Sample>& samples, float& out) const;

    // AOSP addMovement(eventTime, pointerId, axis, position) per axis.
    void add_axis_sample_(std::vector<Sample>& axis, int64_t t_ms, float pos);

    std::vector<Sample> x_samples_;
    std::vector<Sample> y_samples_;
    int64_t last_event_time_ms_ = 0;
    bool has_last_event_time_ = false;
    float x_velocity_ = 0.0f;
    float y_velocity_ = 0.0f;
};

// ─────────────────────────────────────────────────────────────────────────
// VelocityTrackerShadow — DEX bridge for Landroid/view/VelocityTracker;.
//
// Methods (AOSP VelocityTracker.java surface):
//   static VelocityTracker obtain()      → new tracked heap object
//   void recycle()                       → clear + return to pool (we clear)
//   void clear()
//   void addMovement(MotionEvent)        → reads __action__/__x__/__y__/
//                                          __time__ fields (the engine
//                                          materializes them for every
//                                          dispatched touch event)
//   void computeCurrentVelocity(int units)
//   void computeCurrentVelocity(int units, float maxVelocity)
//   float getXVelocity() / getXVelocity(int id)
//   float getYVelocity() / getYVelocity(int id)
//   float getAxisVelocity(int axis) / getAxisVelocity(int axis, int id)
//   boolean isAxisSupported(int axis)    → AXIS_X(0)/AXIS_Y(1) true
// Pointer-id overloads answer the active-pointer value (single-pointer
// model — the documented runtime boundary, same as the dispatcher).
// ─────────────────────────────────────────────────────────────────────────
class VelocityTrackerShadow : public Shadow {
public:
    std::string name() const override { return "VelocityTrackerShadow"; }
    bool handles_class(const std::string& class_name) const override {
        return class_name == "Landroid/view/VelocityTracker;";
    }
    CallResult dispatch(const CallContext& ctx) override;
    std::vector<std::string> implemented_methods() const override {
        return {"obtain",        "recycle",      "clear",     "addMovement",
                "computeCurrentVelocity",        "getXVelocity",
                "getYVelocity",          "getAxisVelocity",
                "isAxisSupported"};
    }

private:
    VelocityTrackerModel* model_for_(uint32_t object_id);
    VelocityTrackerModel* require_model_(uint32_t object_id);

    std::unordered_map<uint32_t, VelocityTrackerModel> trackers_;
};

}  // namespace framework
}  // namespace miniandroid

#endif  // MINIANDROID_VELOCITY_TRACKER_H
