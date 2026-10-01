// key_event_shadow.h — S130 (R-NEW-431/432, CAP-KEY-134/135, CAP-FOCUS-139).
//
// SOURCE FIRST: docs/upstream/aosp/s130_laws/KeyEvent.java constants +
// FocusFinder.java (aosp-mirror/platform_frameworks_base @ android-14.0.0_r2).
//  * KeyEvent action law: ACTION_DOWN=0, ACTION_UP=1; KEYCODE_BACK=4,
//    DPAD_UP=19, DPAD_DOWN=20, DPAD_LEFT=21, DPAD_RIGHT=22, DPAD_CENTER=23,
//    KEYCODE_0..9=7..16, KEYCODE_A..Z=29..54, COMMA=55, PERIOD=56, SPACE=62,
//    ENTER=66, DEL=67 (forward delete = backspace for EditText typing law).
//  * KeyCharacterMap VIRTUAL_KEYBOARD law: letter keys produce the letter
//    char; SHIFT state is a documented boundary (chars are uppercase).
//  * FocusFinder.java: focusSearch → candidates "in" the direction, scored
//    along the MAJOR axis then the MINOR axis; the ported law scores
//    major_offset + 0.4*minor_offset for rects fully traversable in the
//    direction (documented simplification of the beam algorithm, FocusFinder
//    L620-700 original quoted in docs/upstream).
//  * Back law: Activity.onKeyUp(KEYCODE_BACK) → onBackPressed (Activity.java
//    L~3400: mDefaultBackKeyPressed handling).
#ifndef MINIANDROID_KEY_EVENT_SHADOW_H
#define MINIANDROID_KEY_EVENT_SHADOW_H

#include <cstdint>
#include <string>
#include <vector>

namespace miniandroid { namespace framework {

// Pure KeyEvent model + FocusFinder law (deterministic, law-testable).
struct KeyEventModel {
    // Action constants (KeyEvent.java).
    static constexpr int kActionDown = 0;
    static constexpr int kActionUp = 1;
    // Keycode constants (KeyEvent.java public finals).
    static constexpr int kKeycodeBack = 4;
    static constexpr int kKeycodeDpadUp = 19, kKeycodeDpadDown = 20;
    static constexpr int kKeycodeDpadLeft = 21, kKeycodeDpadRight = 22;
    static constexpr int kKeycodeDpadCenter = 23;
    static constexpr int kKeycode0 = 7, kKeycode9 = 16;
    static constexpr int kKeycodeA = 29, kKeycodeZ = 54;
    static constexpr int kKeycodeComma = 55, kKeycodePeriod = 56;
    static constexpr int kKeycodeSpace = 62;
    static constexpr int kKeycodeEnter = 66;
    static constexpr int kKeycodeDel = 67;

    // KeyCharacterMap law: keycode → display char (0 = none).
    static char keycode_to_char(int keycode) {
        if (keycode >= kKeycode0 && keycode <= kKeycode9)
            return char('0' + (keycode - kKeycode0));
        if (keycode >= kKeycodeA && keycode <= kKeycodeZ)
            return char('A' + (keycode - kKeycodeA));
        switch (keycode) {
        case kKeycodeSpace: return ' ';
        case kKeycodeComma: return ',';
        case kKeycodePeriod: return '.';
        default: return 0;
        }
    }
    // Parse a decimal keycode token (also accepts names for drivers).
    static int keycode_from_token(const std::string& token);
    static const char* keycode_name(int keycode);

    // FocusFinder law — direction: 19 up / 20 down / 21 left / 22 right.
    // root_rect = candidate container; candidates carry (id, l, t, r, b).
    struct FocusCandidate {
        uint32_t id;
        int l, t, r, b;
        bool focusable = true;  // AOSP: focus search considers focusable views
    };
    static uint32_t focus_search(const std::vector<FocusCandidate>& cands,
                                 int direction,
                                 const FocusCandidate& src);
};

}}  // namespace miniandroid::framework

#endif  // MINIANDROID_KEY_EVENT_SHADOW_H
