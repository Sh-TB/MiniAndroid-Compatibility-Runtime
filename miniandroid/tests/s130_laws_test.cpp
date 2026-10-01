// s130_laws_test.cpp — S130 MASS BATCH law tests (pure models, deterministic).
// Covers: R-NEW-427 Scroller laws, R-NEW-429 GestureDetector laws,
// R-NEW-431/432 KeyEvent/FocusFinder laws. Exit 0 = ALL PASS.
#include "../src/framework/scroller_shadow.h"
#include "../src/framework/gesture_detector_shadow.h"
#include "../src/framework/key_event_shadow.h"

#include <cmath>
#include <cstdio>

using namespace miniandroid::framework;

static int g_checks = 0, g_pass = 0;
#define CHECK(cond)                                                            \
    do {                                                                       \
        ++g_checks;                                                            \
        if (cond) {                                                            \
            ++g_pass;                                                          \
        } else {                                                               \
            std::printf("FAIL line %d: %s\n", __LINE__, #cond);                \
        }                                                                      \
    } while (0)

static void test_scroller_laws() {
    // Viscous fluid interpolation anchors (Scroller.java L570-600).
    const float v0 = ScrollerModel::viscous_interpolation(0.0f);
    const float v1 = ScrollerModel::viscous_interpolation(1.0f);
    CHECK(std::fabs(v0) < 0.02f);           // f(0) ~= 0
    CHECK(std::fabs(v1 - 1.0f) < 0.02f);    // normalized f(1) = 1
    CHECK(ScrollerModel::viscous_interpolation(0.5f) > 0.3f);

    // startScroll: final = start + delta; duration default 250 (L96).
    ScrollerModel m;
    m.start_scroll(100, 200, -300, 50, 0, /*now=*/1000);
    CHECK(m.mode == ScrollerModel::kScrollMode);
    CHECK(m.final_x == -200 && m.final_y == 250);
    CHECK(m.duration_ms == ScrollerModel::kDefaultDurationMs);
    CHECK(!m.finished);
    // Mid-flight: t=0.5 → viscous(0.5) between 0 and 1, monotone toward final.
    m.compute_scroll_offset(1000 + 125);
    CHECK(m.curr_x < 100 && m.curr_x > -200);
    CHECK(m.compute_scroll_offset(1000 + 250) == false);  // done → false
    CHECK(m.curr_x == m.final_x);  // settle at final (AOSP end law)

    // Fling physics: distance/duration follow the spline laws (L481-494) and
    // the final position clamps to bounds.
    ScrollerModel f;
    const float ppc = f.physical_coeff();
    CHECK(ppc > 0);
    f.fling(0, 0, /*vx=*/0, /*vy=*/-3000, 0, 0, -2400, 0, /*now=*/0);
    CHECK(f.mode == ScrollerModel::kFlingMode);
    CHECK(f.duration_ms > 0);
    CHECK(f.final_y <= 0);           // negative velocity → upward (−y)
    CHECK(f.final_y >= -2400);       // clamped to the min bound
    CHECK(f.compute_scroll_offset(f.duration_ms - 1));
    CHECK(f.compute_scroll_offset(f.duration_ms + 1) == false);
    CHECK(f.final_y == f.curr_y);    // fling settles at the clamped final
    CHECK(!f.finished_law(0) || f.duration_ms == 0);
    // Higher velocity → longer duration (spline deceleration law).
    ScrollerModel f2;
    f2.fling(0, 0, 0, -6000, 0, 0, -4800, 0, 0);
    CHECK(f2.duration_ms > f.duration_ms);
}

static void test_gesture_laws() {
    // Constants (GestureDetector.java L251-254 + ViewConfiguration scaling).
    CHECK(GdModel::kTapTimeoutMs == 100);
    CHECK(GdModel::kLongPressTimeoutMs == 500);
    CHECK(GdModel::kDoubleTapTimeoutMs == 300);
    CHECK(GdModel::kDoubleTapMinTimeMs == 40);
    CHECK(GdModel::kTouchSlopPx == 21.0f);

    struct Log {
        std::string seq;
        float fling_vy = 0;
    } log;
    GdModel gd;
    gd.cb = [&](const char* cb, float a, float b, float c, float d) {
        log.seq += cb;
        log.seq += ";";
        if (std::string(cb) == "onFling") { log.fling_vy = c; (void)a; (void)b; (void)d; }
        return true;
    };
    // Tap: DOWN at 0ms, UP at 60ms → onDown + onSingleTapUp; confirmed at +300.
    CHECK(gd.feed(0, 100, 100, 0));    // DOWN
    CHECK(gd.feed(1, 100, 100, 60));   // UP
    gd.poll(60 + 299);                 // inside the double-tap window
    CHECK(log.seq.find("onSingleTapConfirmed") == std::string::npos);
    gd.poll(60 + 301);
    CHECK(log.seq.find("onSingleTapUp;") != std::string::npos);
    CHECK(log.seq.find("onSingleTapConfirmed;") != std::string::npos);

    // Long press: DOWN then poll at 500ms → onLongPress fires.
    GdModel gd2;
    bool long_fired = false;
    gd2.cb = [&](const char* cb, float, float, float, float) {
        if (std::string(cb) == "onLongPress") long_fired = true;
        return true;
    };
    gd2.feed(0, 50, 50, 0);
    gd2.poll(499);
    CHECK(!long_fired);
    gd2.poll(501);
    CHECK(long_fired);

    // Scroll + fling: DOWN, MOVE beyond slop → onScroll; fast UP → onFling.
    GdModel gd3;
    int scrolls = 0;
    float fling_vy = 0;
    gd3.cb = [&](const char* cb, float, float, float c, float d) {
        const std::string s(cb);
        if (s == "onScroll") ++scrolls;
        if (s == "onFling") fling_vy = d;
        return true;
    };
    CHECK(gd3.feed(0, 100, 1000, 0));
    CHECK(gd3.feed(2, 100, 1100, 16));   // 100px > 21px slop → scroll
    CHECK(scrolls >= 1);
    CHECK(gd3.feed(2, 100, 1150, 32));
    CHECK(gd3.feed(2, 100, 1200, 48));
    CHECK(gd3.feed(1, 100, 1250, 64));   // fast UP → fling (LSQ2 velocity)
    CHECK(fling_vy > 0.0f);              // downward drag → positive vy
}

static void test_key_focus_laws() {
    using KM = KeyEventModel;
    // Keycode↔char law (KeyCharacterMap VIRTUAL_KEYBOARD, uppercase).
    CHECK(KM::keycode_to_char(KM::kKeycodeA) == 'A');
    CHECK(KM::keycode_to_char(KM::kKeycodeZ) == 'Z');
    CHECK(KM::keycode_to_char(KM::kKeycode0 + 5) == '5');
    CHECK(KM::keycode_to_char(KM::kKeycodeSpace) == ' ');
    CHECK(KM::keycode_to_char(KM::kKeycodeBack) == 0);
    // Token parsing (driver law).
    CHECK(KM::keycode_from_token("BACK") == 4);
    CHECK(KM::keycode_from_token("DPAD_DOWN") == 20);
    CHECK(KM::keycode_from_token("A") == 29);

    // FocusFinder law: rightward search picks the nearest right neighbor.
    std::vector<KM::FocusCandidate> cands = {
        {10, 0, 0, 100, 100},     // src
        {11, 200, 10, 300, 90},   // right, close
        {12, 700, 10, 800, 90},   // right, far
        {13, 20, 400, 80, 500},   // below, beam-overlapping (DOWN candidate)
    };
    const KM::FocusCandidate src{10, 0, 0, 100, 100, true};
    CHECK(KM::focus_search(cands, KM::kKeycodeDpadRight, src) == 11);
    CHECK(KM::focus_search(cands, KM::kKeycodeDpadDown, src) == 13);
    CHECK(KM::focus_search(cands, KM::kKeycodeDpadUp, src) == 0);
    // Non-focusable candidates are skipped (focusable law).
    cands[1].focusable = false;
    CHECK(KM::focus_search(cands, KM::kKeycodeDpadRight, src) == 12);
}

int main() {
    test_scroller_laws();
    test_gesture_laws();
    test_key_focus_laws();
    std::printf("s130_laws_test: %d/%d checks PASS\n", g_pass, g_checks);
    return g_pass == g_checks ? 0 : 1;
}
