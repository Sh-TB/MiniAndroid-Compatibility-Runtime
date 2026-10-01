// scroller_shadow.h — S130 (R-NEW-427, CAP-SCROLLING-126) Scroller/OverScroller law.
//
// SOURCE FIRST: docs/upstream/aosp/s130_laws/Scroller.java
// (aosp-mirror/platform_frameworks_base @ android-14.0.0_r2), committed
// before this implementation. Ported laws (Scroller.java line anchors):
//  * L96 DEFAULT_DURATION=250, L97 SCROLL_MODE=0, L98 FLING_MODE=1.
//  * L101 DECELERATION_RATE = log(0.78)/log(0.9).
//  * L187 mPhysicalCoeff = computeDeceleration(0.84f) — L203: GRAVITY_EARTH
//    (9.80665) * 39.37 (inch/meter) * ppi * friction. ppi = density*160
//    (420dpi device → 420).
//  * L394-376 startScroll: mode=SCROLL, final=start+delta, duration default 250.
//  * L454-494 fling: getSplineDeceleration = log(INFLEXION(0.35) * |v| /
//    (mFlingFriction(0.015) * physCoeff)); duration = 1000*exp(l/(rate-1));
//    distance = friction*physCoeff*exp(rate/(rate-1)*l); final clamped to
//    [min,max] bounds (clampedFlingDistance, L505-512).
//  * L315 computeScrollOffset: timePassed=(now-start); SCROLL_MODE →
//    x=duration==0?1:timePassed/duration → ViscousFluidInterpolator
//    (L570-600: SCALE 8.0, viscousFluid(x) = x<1 ? x-(1-exp(-x)) :
//    0.36787944117 + (1-exp(1-x))*(1-0.36787944117), NORMALIZE=1/vf(1),
//    OFFSET=1-NORMALIZE*vf(1)); curr = start + round(delta*interp(t)).
//    FLING_MODE → curr = start + round(distance * viscous(t)) toward final.
//  * isFinished / forceFinished / abortAnimation lifecycle.
//
// The model is PURE (every method takes now_ms) so law tests are
// deterministic without a clock. The Shadow dispatch feeds the virtual
// Handler clock (one-queue law) through now_fn_.
#ifndef MINIANDROID_SCROLLER_SHADOW_H
#define MINIANDROID_SCROLLER_SHADOW_H

#include "shadow_registry.h"

#include <cmath>
#include <functional>
#include <unordered_map>

namespace miniandroid { namespace framework {

// Pure Scroller model (1:1 with Scroller.java laws above).
struct ScrollerModel {
    static constexpr float kFriction = 0.015f;              // ViewConfiguration.getScrollFriction
    static constexpr float kGravityEarth = 9.80665f;        // SensorManager.GRAVITY_EARTH
    static constexpr float kInchPerMeter = 39.37f;
    static constexpr float kFrictionTune = 0.84f;           // Scroller.java L187
    static constexpr float kInflexion = 0.35f;              // OverScroller INFLEXION
    static constexpr int   kDefaultDurationMs = 250;        // Scroller.java L96
    static constexpr int   kScrollMode = 0;                 // SCROLL_MODE
    static constexpr int   kFlingMode = 1;                  // FLING_MODE
    // Scroller.java L101: DECELERATION_RATE = log(0.78)/log(0.9)
    static constexpr double kDecelerationRate =
        std::log(0.78) / std::log(0.9);

    int mode = -1;              // -1 idle, SCROLL_MODE, FLING_MODE
    int start_x = 0, start_y = 0;
    int final_x = 0, final_y = 0;
    int curr_x = 0, curr_y = 0;
    int64_t start_ms = 0;
    int duration_ms = 0;
    double fling_distance_x = 0, fling_distance_y = 0;
    bool finished = true;
    float ppi = 420.0f;         // density 2.625 * 160 (campaign device law)

    float physical_coeff() const {
        // Scroller.java L203: gravity * inch/meter * ppi * friction.
        return kGravityEarth * kInchPerMeter * ppi * kFrictionTune;
    }
    // AOSP ViscousFluidInterpolator (Scroller.java L570-600).
    static float viscous_fluid(float x) {
        x *= 8.0f;  // VISCOUS_FLUID_SCALE
        if (x < 1.0f) {
            x -= (1.0f - std::exp(-x));
        } else {
            const float start = 0.36787944117f;  // 1/e
            x = 1.0f - std::exp(1.0f - x);
            x = start + x * (1.0f - start);
        }
        return x;
    }
    static float viscous_interpolation(float input) {
        const float normalize = 1.0f / viscous_fluid(1.0f);
        const float offset = 1.0f - normalize * viscous_fluid(1.0f);
        const float interpolated = normalize * viscous_fluid(input);
        return interpolated > 0 ? interpolated + offset : interpolated;
    }
    double spline_deceleration(float velocity) const {
        // Scroller.java L481-482.
        return std::log(kInflexion * std::fabs(velocity) /
                        (kFriction * double(physical_coeff())));
    }
    int spline_fling_duration(float velocity) const {
        // L485-489: 1000 * exp(l / (rate - 1)).
        const double l = spline_deceleration(velocity);
        const double decel_minus_one = kDecelerationRate - 1.0;
        return int(1000.0 * std::exp(l / decel_minus_one));
    }
    double spline_fling_distance(float velocity) const {
        // L491-494: friction * physCoeff * exp(rate/(rate-1) * l).
        const double l = spline_deceleration(velocity);
        const double decel_minus_one = kDecelerationRate - 1.0;
        return double(kFriction * physical_coeff()) *
               std::exp(kDecelerationRate / decel_minus_one * l);
    }
    void start_scroll(int sx, int sy, int dx, int dy, int duration, int64_t now) {
        mode = kScrollMode;
        start_x = curr_x = sx; start_y = curr_y = sy;
        final_x = sx + dx; final_y = sy + dy;
        duration_ms = duration > 0 ? duration : kDefaultDurationMs;
        start_ms = now;
        finished = false;
    }
    void fling(int sx, int sy, float vx, float vy,
               int min_x, int max_x, int min_y, int max_y, int64_t now) {
        mode = kFlingMode;
        start_x = curr_x = sx; start_y = curr_y = sy;
        start_ms = now;
        finished = false;
        // Distance per axis = total spline distance, sign-preserving, then
        // clamped to the scroll bounds (Scroller.java fling + clamp law).
        const double dist = spline_fling_distance(std::sqrt(vx * vx + vy * vy));
        int fx = sx, fy = sy;
        if (vx != 0) {
            double d = (vx > 0 ? dist : -dist);
            fx = int(sx + d);
            if (max_x > min_x) fx = std::min(std::max(fx, min_x), max_x);
        }
        if (vy != 0) {
            double d = (vy > 0 ? dist : -dist);
            fy = int(sy + d);
            if (max_y > min_y) fy = std::min(std::max(fy, min_y), max_y);
        }
        final_x = fx; final_y = fy;
        duration_ms = spline_fling_duration(std::sqrt(vx * vx + vy * vy));
        fling_distance_x = std::fabs(double(final_x - start_x));
        fling_distance_y = std::fabs(double(final_y - start_y));
    }
    // Scroller.java L315 computeScrollOffset.
    bool compute_scroll_offset(int64_t now) {
        if (finished) return false;
        if (finished_law(now)) {
            // AOSP end law: the final compute settles mCurr at mFinal.
            finished = true;
            curr_x = final_x;
            curr_y = final_y;
            return false;
        }
        const double t = duration_ms > 0
                             ? double(now - start_ms) / double(duration_ms)
                             : 1.0;
        const float interp = viscous_interpolation(float(std::min(1.0, std::max(0.0, t))));
        if (mode == kScrollMode) {
            curr_x = start_x + int(std::lround(double(final_x - start_x) * interp));
            curr_y = start_y + int(std::lround(double(final_y - start_y) * interp));
        } else {
            // FLING: progress along the remaining distance toward final.
            const double rem_x = std::fabs(double(final_x - start_x));
            const double rem_y = std::fabs(double(final_y - start_y));
            const double done_x = rem_x * double(interp);
            const double done_y = rem_y * double(interp);
            curr_x = start_x + int(std::lround((final_x >= start_x ? done_x : -done_x)));
            curr_y = start_y + int(std::lround((final_y >= start_y ? done_y : -done_y)));
        }
        return true;
    }
    bool finished_law(int64_t now) const {
        return duration_ms > 0 ? (now - start_ms) >= duration_ms : true;
    }
    void force_finished(bool f) { finished = f; }
    void abort(int64_t now) { compute_scroll_offset(now); finished = true; }
};

class ScrollerShadow : public Shadow {
public:
    std::string name() const override { return "ScrollerShadow"; }
    bool handles_class(const std::string& class_name) const override;
    CallResult dispatch(const CallContext& ctx) override;
    std::vector<std::string> implemented_methods() const override;
    std::vector<std::string> stubbed_methods() const override;
    // Virtual-clock source (HandlerShadow::virtual_now_ms) — wired by engine.
    void set_now_fn(std::function<int64_t()> fn) { now_fn_ = std::move(fn); }
    ScrollerModel* model_for(uint32_t obj) {
        return models_.count(obj) ? &models_[obj] : nullptr;
    }
    std::function<int64_t()> now_fn_;

private:
    int64_t now() const {
        return now_fn_ ? now_fn_() : 0;
    }
    std::unordered_map<uint32_t, ScrollerModel> models_;
};

}}  // namespace miniandroid::framework

#endif  // MINIANDROID_SCROLLER_SHADOW_H
