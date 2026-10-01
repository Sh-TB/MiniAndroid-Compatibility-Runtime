// velocity_tracker.cpp — S129 (R-NEW-425, CAP-INPUT-108) implementation.
// Every branch cites its AOSP android-14.0.0_r2 law anchor (see .h).

#include "velocity_tracker.h"

#include <algorithm>
#include <cmath>
#include <limits>

namespace miniandroid {
namespace framework {

void VelocityTrackerModel::clear() {
    x_samples_.clear();
    y_samples_.clear();
    last_event_time_ms_ = 0;
    has_last_event_time_ = false;
    // AOSP clear() does NOT reset the last computed velocities (the Java
    // getters keep answering the last computed value); only the samples go.
}

void VelocityTrackerModel::add_axis_sample_(std::vector<Sample>& axis,
                                            int64_t t_ms, float pos) {
    // AOSP LeastSquaresVelocityTrackerStrategy::addMovement — the newest
    // sample occupies the moving index; a sample with the SAME event time
    // updates the newest slot in place (AOSP: "If the eventtimes for both
    // events are identical, just update the data for this time").
    if (!axis.empty() && axis.back().t_ms == t_ms) {
        axis.back().pos = pos;
        return;
    }
    if (axis.size() == kHistorySize) axis.erase(axis.begin());
    axis.push_back(Sample{t_ms, pos});
}

void VelocityTrackerModel::add_movement(int64_t event_time_ms, int action,
                                        float x, float y) {
    // AOSP VelocityTracker.cpp addMovement(MotionEvent) action law.
    if (action == kActionDown) {
        // "Clear all pointers on down before adding the new movement."
        clear();
    } else if (action != kActionMove) {
        // ACTION_UP / ACTION_POINTER_UP: early return (preserve the last
        // known velocity; the UP position is never added). ACTION_CANCEL
        // and every other action: "Ignore all other actions."
        return;
    }
    // VelocityTracker::addMovement(eventTime, ...) stopped-pointer law:
    // a movement arriving > ASSUME_POINTER_STOPPED_TIME (40 ms) after the
    // previous one clears the strategies ("Assume that all pointers have
    // stopped") — the stale samples must not bleed into the new burst.
    if (has_last_event_time_ &&
        event_time_ms - last_event_time_ms_ > kAssumeStoppedMs) {
        x_samples_.clear();
        y_samples_.clear();
    }
    last_event_time_ms_ = event_time_ms;
    has_last_event_time_ = true;

    add_axis_sample_(x_samples_, event_time_ms, x);
    add_axis_sample_(y_samples_, event_time_ms, y);
}

// AOSP solveUnweightedLeastSquaresDeg2 (VelocityTracker.cpp L599+): solve
// y = a·x² + b·x + c with the closed-form Sxx/Sxy/Sxx2/Sx2y/Sx2x2 sums.
// Returns {c, b, a}; velocity = b (d/dx at x = 0 — the newest sample).
static bool solve_unweighted_lsq_deg2(const std::vector<float>& x,
                                      const std::vector<float>& y,
                                      float& out_b) {
    const size_t count = x.size();
    float sxi = 0, sxiyi = 0, syi = 0, sxi2 = 0, sxi3 = 0, sxi2yi = 0,
          sxi4 = 0;
    for (size_t i = 0; i < count; i++) {
        const float xi = x[i];
        const float yi = y[i];
        const float xi2 = xi * xi;
        const float xi3 = xi2 * xi;
        const float xi4 = xi3 * xi;
        sxi += xi;
        sxi2 += xi2;
        sxiyi += xi * yi;
        sxi2yi += xi2 * yi;
        syi += yi;
        sxi3 += xi3;
        sxi4 += xi4;
    }
    const float Sxx = sxi2 - sxi * sxi / count;
    const float Sxy = sxiyi - sxi * syi / count;
    const float Sxx2 = sxi3 - sxi * sxi2 / count;
    const float Sx2y = sxi2yi - sxi2 * syi / count;
    const float Sx2x2 = sxi4 - sxi2 * sxi2 / count;
    const float denominator = Sxx * Sx2x2 - Sxx2 * Sxx2;
    if (denominator == 0) return false;  // AOSP: division-by-0 guard
    // b (the linear coefficient) per AOSP: numerator = Sxy*Sx2x2 - Sx2y*Sxx2.
    out_b = (Sxy * Sx2x2 - Sx2y * Sxx2) / denominator;
    return true;
}

// AOSP solveLeastSquares degenerated to the degree-1 weighted normal
// equations (weights are 1 under Weighting::NONE): minimize
// Σ(yᵢ - (b·xᵢ + c))² → 2x2 symmetric system; velocity = slope b.
static bool solve_linear_lsq_slope(const std::vector<float>& x,
                                   const std::vector<float>& y,
                                   float& out_b) {
    const size_t count = x.size();
    float sx = 0, sy = 0, sxx = 0, sxy = 0;
    for (size_t i = 0; i < count; i++) {
        sx += x[i];
        sy += y[i];
        sxx += x[i] * x[i];
        sxy += x[i] * y[i];
    }
    const float n = static_cast<float>(count);
    const float det = n * sxx - sx * sx;
    if (det == 0) return false;
    out_b = (n * sxy - sx * sy) / det;
    return true;
}

bool VelocityTrackerModel::axis_velocity_(const std::vector<Sample>& samples,
                                          float& out) const {
    if (samples.empty()) return false;
    const int64_t newest_t = samples.back().t_ms;
    // AOSP getEstimator: newest → oldest; stop when age > HORIZON (100 ms);
    // time axis = -age in SECONDS (AOSP: time.push_back(-age * 0.000000001f)
    // from nanoseconds — ms/1000 here), weight 1 (Weighting::NONE).
    std::vector<float> positions, times;
    for (auto it = samples.rbegin(); it != samples.rend(); ++it) {
        const int64_t age = newest_t - it->t_ms;
        if (age > kHorizonMs) break;
        positions.push_back(it->pos);
        times.push_back(-age / 1000.0f);
    }
    const size_t m = positions.size();
    if (m == 0) return false;
    // degree = min(2, m-1).
    if (m >= 3) {
        if (solve_unweighted_lsq_deg2(times, positions, out)) return true;
    } else if (m == 2) {
        if (solve_linear_lsq_slope(times, positions, out)) return true;
    }
    // m == 1 → degree 0 → no velocity (AOSP getVelocity answers {} for
    // degree < 1; the Java getter resolves value_or(0)).
    return false;
}

void VelocityTrackerModel::compute_current_velocity(int units,
                                                    float max_velocity) {
    float vx = 0, vy = 0;
    const bool has_x = axis_velocity_(x_samples_, vx);
    const bool has_y = axis_velocity_(y_samples_, vy);
    // AOSP getComputedVelocity: adjusted = clamp(v * units / 1000, ±max).
    // The native fit yields px per SECOND (the time axis is seconds).
    const float scale = static_cast<float>(units) / 1000.0f;
    x_velocity_ = has_x ? std::clamp(vx * scale, -max_velocity, max_velocity)
                        : 0.0f;
    y_velocity_ = has_y ? std::clamp(vy * scale, -max_velocity, max_velocity)
                        : 0.0f;
}

void VelocityTrackerModel::compute_current_velocity(int units) {
    // AOSP computeCurrentVelocity(int) == max Float.MAX_VALUE.
    compute_current_velocity(units, std::numeric_limits<float>::max());
}

// ─────────────────────────────────────────────────────────────────────────
// VelocityTrackerShadow — DEX bridge.
// ─────────────────────────────────────────────────────────────────────────

VelocityTrackerModel* VelocityTrackerShadow::model_for_(uint32_t object_id) {
    auto it = trackers_.find(object_id);
    return it == trackers_.end() ? nullptr : &it->second;
}

VelocityTrackerModel* VelocityTrackerShadow::require_model_(
    uint32_t object_id) {
    // AOSP trackers are obtained via obtain(); a method arriving on an
    // unknown object (hostile stream / lost alloc) materializes a model so
    // the call is never a silent no-op.
    auto it = trackers_.find(object_id);
    if (it == trackers_.end())
        it = trackers_.emplace(object_id, VelocityTrackerModel{}).first;
    return &it->second;
}

CallResult VelocityTrackerShadow::dispatch(const CallContext& ctx) {
    const std::string& m = ctx.method;

    if (m == "obtain") {
        if (!heap_) return CallResult::handled_null();
        const uint32_t obj =
            heap_->allocate("Landroid/view/VelocityTracker;");
        if (obj == 0) return CallResult::handled_null();
        trackers_.emplace(obj, VelocityTrackerModel{});
        return CallResult::handled_object(obj, "Landroid/view/VelocityTracker;");
    }

    const uint32_t recv =
        ctx.has_receiver ? ctx.receiver_id
                         : (ctx.args.empty() ? 0 : ctx.args[0].object_id);
    if (m == "recycle") {
        // AOSP recycle(): clear() then return to the pool. The model is
        // dropped with the object mapping (pool of 2 is not modeled —
        // documented boundary; obtain() always allocates fresh state).
        trackers_.erase(recv);
        return CallResult::handled_void();
    }
    VelocityTrackerModel* model = require_model_(recv);

    if (m == "clear") {
        model->clear();
        return CallResult::handled_void();
    }
    if (m == "addMovement") {
        const uint32_t ev = ctx.arg_as_object(0, 0);
        if (ev == 0) {
            // AOSP addMovement(null) → IllegalArgumentException; the DEX
            // engine models the exception unwind upstream — a null event
            // reaching the shadow is hostile input: acknowledge, no sample.
            return CallResult::handled_void();
        }
        int32_t action = 0;
        float x = 0, y = 0;
        int64_t t_ms = 0;
        heap_->get_object_int_field(ev, "__action__", action);
        heap_->get_object_float_field(ev, "__x__", x);
        heap_->get_object_float_field(ev, "__y__", y);
        heap_->get_object_long_field(ev, "__time__", t_ms);
        model->add_movement(t_ms, action, x, y);
        return CallResult::handled_void();
    }
    if (m == "computeCurrentVelocity") {
        const int units = ctx.arg_as_int(0, 1000);
        if (ctx.args.size() >= 2) {
            model->compute_current_velocity(units, ctx.arg_as_float(1, 0.0f));
        } else {
            model->compute_current_velocity(units);
        }
        return CallResult::handled_void();
    }
    if (m == "getXVelocity" || m == "getYVelocity" ||
        m == "getAxisVelocity") {
        float v = 0;
        if (m == "getAxisVelocity") {
            const int axis = ctx.arg_as_int(0, 0);
            v = axis == 0 ? model->x_velocity() : model->y_velocity();
        } else {
            v = m == "getXVelocity" ? model->x_velocity()
                                    : model->y_velocity();
        }
        return CallResult::handled_float(v);
    }
    if (m == "isAxisSupported") {
        // AXIS_X (0) and AXIS_Y (1) are the velocity-trackable planar axes.
        const int axis = ctx.arg_as_int(0, -1);
        return CallResult::handled_bool(axis == 0 || axis == 1);
    }
    return CallResult::not_handled();
}

}  // namespace framework
}  // namespace miniandroid
