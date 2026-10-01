// velocity_tracker_law_test — S129 (R-NEW-425, CAP-INPUT-108) law battery.
//
// Law references (AOSP android-14.0.0_r2, committed under
// docs/upstream/aosp/input_laws/):
//   * VelocityTracker.h L179-227: LSQ2 = LeastSquaresVelocityTrackerStrategy
//     (degree 2, Weighting::NONE), HORIZON = 100 ms, HISTORY_SIZE = 20.
//   * VelocityTracker.cpp addMovement(MotionEvent): DOWN → clear + sample;
//     MOVE → sample; UP/POINTER_UP/CANCEL → EARLY RETURN (no sample);
//     >40 ms gap (ASSUME_POINTER_STOPPED_TIME) clears the strategies.
//   * VelocityTracker.cpp getEstimator: newest → oldest within HORIZON,
//     time = -age (seconds); degree 2 → solveUnweightedLeastSquaresDeg2;
//     velocity = coeff[1]; degree 0 → no velocity.
//   * VelocityTracker.cpp getComputedVelocity: clamp(v * units / 1000,
//     ±maxVelocity).
//
// Each CHECK names the law it guards.

#include "../src/framework/velocity_tracker.h"

#include <cmath>
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

// Constant-velocity drag at the canonical 60Hz touch cadence: DOWN at t0
// (0 px), one MOVE every 16 ms. Samples must stay closer together than the
// 40 ms ASSUME_POINTER_STOPPED_TIME — exactly like a real finger.
// The LSQ2 fit of collinear samples answers the EXACT constant velocity.
void feed_constant_drag(framework::VelocityTrackerModel& vt, int64_t t0_ms,
                        float px_per_step, int steps) {
    vt.add_movement(t0_ms, 0 /*DOWN*/, 0.0f, 0.0f);
    for (int i = 1; i <= steps; ++i) {
        vt.add_movement(t0_ms + 16 * i, 2 /*MOVE*/, i * px_per_step,
                        i * px_per_step);
    }
}

}  // namespace

int main() {
    printf("── CAP-INPUT-108: constant-velocity fit (LSQ2 exactness) ──\n");
    {
        framework::VelocityTrackerModel vt;
        // 16px per 16ms = 1000 px/s on BOTH axes.
        feed_constant_drag(vt, 1000, 16.0f, 12);
        vt.compute_current_velocity(1000);
        check(std::fabs(vt.x_velocity() - 1000.0f) < 0.01f,
              "LSQ2 deg-2 fit of collinear samples: VX = 1000 px/s exact");
        check(std::fabs(vt.y_velocity() - 1000.0f) < 0.01f,
              "LSQ2 deg-2 fit of collinear samples: VY = 1000 px/s exact");
        // units=1 → per-millisecond (getComputedVelocity scaling law).
        vt.compute_current_velocity(1);
        check(std::fabs(vt.x_velocity() - 1.0f) < 0.001f,
              "units=1 scales v*units/1000 → 1.0 px/ms");
    }

    printf("── CAP-INPUT-108: maxVelocity clamp ─────────────────────────\n");
    {
        framework::VelocityTrackerModel vt;
        feed_constant_drag(vt, 0, 16.0f, 12);
        vt.compute_current_velocity(1000, 500.0f);
        check(std::fabs(vt.x_velocity() - 500.0f) < 0.01f,
              "computeCurrentVelocity(units, 500) clamps to ±500");
        vt.compute_current_velocity(1000, 5000.0f);
        check(std::fabs(vt.x_velocity() - 1000.0f) < 0.01f,
              "clamp above the true velocity is a no-op");
    }

    printf("── CAP-INPUT-108: UP never adds a sample ────────────────────\n");
    {
        framework::VelocityTrackerModel vt;
        feed_constant_drag(vt, 0, 16.0f, 6);
        const size_t before_x = vt.x_sample_count();
        vt.add_movement(97, 1 /*UP*/, 97.0f, 97.0f);
        vt.add_movement(98, 3 /*CANCEL*/, 98.0f, 98.0f);
        check(vt.x_sample_count() == before_x,
              "addMovement(UP/CANCEL) returns early — no sample (native law)");
        vt.compute_current_velocity(1000);
        check(std::fabs(vt.x_velocity() - 1000.0f) < 0.01f,
              "UP/CANCEL preserve the last known velocity");
    }

    printf("── CAP-INPUT-108: DOWN clears (new gesture) ─────────────────\n");
    {
        framework::VelocityTrackerModel vt;
        feed_constant_drag(vt, 0, 16.0f, 12);
        vt.add_movement(10000, 0 /*DOWN*/, 5.0f, 5.0f);
        check(vt.x_sample_count() == 1,
              "addMovement(DOWN) clears all pointers before sampling");
        vt.add_movement(10016, 2 /*MOVE*/, 21.0f, 21.0f);
        vt.compute_current_velocity(1000);
        // 16px over 16ms = 1000 px/s from the new burst only.
        check(std::fabs(vt.x_velocity() - 1000.0f) < 0.01f,
              "post-DOWN velocity computed from the NEW gesture alone");
    }

    printf("── CAP-INPUT-108: horizon (100 ms) ──────────────────────────\n");
    {
        framework::VelocityTrackerModel vt;
        // Decelerating drag: fast early, stop at the end. Samples outside
        // the 100 ms horizon must not dilute the newest estimate.
        vt.add_movement(0, 0 /*DOWN*/, 0.0f, 0.0f);
        for (int i = 1; i <= 10; ++i)
            vt.add_movement(16 * i, 2 /*MOVE*/, 60.0f * i, 0.0f);
        check(vt.x_sample_count() == 11,
              "HISTORY_SIZE=20 circular buffer keeps every sample fed "
              "(1 DOWN + 10 MOVEs)");
        // Slow final burst: 1px per 16ms = 62.5 px/s for the newest samples
        // (within the 100ms horizon), while the older 3750 px/s burst ages
        // out of the horizon.
        vt.add_movement(600, 2 /*MOVE*/, 610.0f, 0.0f);
        vt.add_movement(616, 2 /*MOVE*/, 611.0f, 0.0f);
        vt.add_movement(632, 2 /*MOVE*/, 612.0f, 0.0f);
        vt.add_movement(648, 2 /*MOVE*/, 613.0f, 0.0f);
        vt.compute_current_velocity(1000);
        check(std::fabs(vt.x_velocity() - 62.5f) < 0.6f,
              "HORIZON=100ms: stale fast samples excluded from the fit");
    }

    printf("── CAP-INPUT-108: 40 ms stopped-pointer reset ───────────────\n");
    {
        framework::VelocityTrackerModel vt;
        feed_constant_drag(vt, 0, 16.0f, 12);
        // One MOVE arriving 500 ms later: strategies cleared, then the
        // single fresh sample (degree 0 → no velocity).
        vt.add_movement(1000, 2 /*MOVE*/, 0.0f, 0.0f);
        vt.compute_current_velocity(1000);
        check(vt.x_sample_count() == 1,
              ">40ms gap clears the samples (ASSUME_POINTER_STOPPED_TIME)");
        check(std::fabs(vt.x_velocity()) < 0.0001f,
              "single sample after reset → degree 0 → velocity 0");
    }

    printf("── CAP-INPUT-108: degenerate inputs ─────────────────────────\n");
    {
        framework::VelocityTrackerModel vt;
        vt.compute_current_velocity(1000);
        check(vt.x_velocity() == 0.0f && vt.y_velocity() == 0.0f,
              "compute with no samples answers 0 (value_or(0) law)");
        vt.add_movement(0, 0 /*DOWN*/, 10.0f, 10.0f);
        vt.compute_current_velocity(1000);
        check(vt.x_velocity() == 0.0f,
              "single-sample tracker (degree 0) yields no velocity");
        // Identical timestamps update the newest slot (AOSP addMovement
        // same-eventTime law) instead of growing the buffer.
        vt.add_movement(100, 2 /*MOVE*/, 20.0f, 20.0f);
        vt.add_movement(100, 2 /*MOVE*/, 30.0f, 30.0f);
        check(vt.x_sample_count() == 1,
              "same-eventTime movement updates the newest sample");
    }

    printf("── CAP-INPUT-108: negative direction (fling up) ─────────────\n");
    {
        framework::VelocityTrackerModel vt;
        vt.add_movement(0, 0 /*DOWN*/, 0.0f, 0.0f);
        for (int i = 1; i <= 4; ++i)
            vt.add_movement(16 * i, 2 /*MOVE*/, 0.0f, -16.0f * i);
        vt.compute_current_velocity(1000);
        check(std::fabs(vt.y_velocity() + 1000.0f) < 0.01f,
              "upward drag → negative VY (sign law, ScrollView fling)");
    }

    printf("════════════════════════════════════════════════════\n");
    printf("RESULT: %d checks, %d failures\n", g_checks, g_fail);
    printf(g_fail == 0 ? "VELOCITY TRACKER LAW: ALL PASS\n"
                       : "VELOCITY TRACKER LAW: FAILURES PRESENT\n");
    return g_fail == 0 ? 0 : 1;
}
