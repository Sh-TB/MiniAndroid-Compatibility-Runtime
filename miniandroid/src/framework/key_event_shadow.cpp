// key_event_shadow.cpp — S130 KeyEvent constants + FocusFinder law port.
// See key_event_shadow.h for the source anchors.
#include "key_event_shadow.h"

#include <algorithm>
#include <cmath>

namespace miniandroid { namespace framework {

int KeyEventModel::keycode_from_token(const std::string& token) {
    if (token == "BACK") return kKeycodeBack;
    if (token == "DPAD_UP") return kKeycodeDpadUp;
    if (token == "DPAD_DOWN") return kKeycodeDpadDown;
    if (token == "DPAD_LEFT") return kKeycodeDpadLeft;
    if (token == "DPAD_RIGHT") return kKeycodeDpadRight;
    if (token == "ENTER") return kKeycodeEnter;
    if (token == "DEL") return kKeycodeDel;
    if (token == "SPACE") return kKeycodeSpace;
    if (token.size() == 1) {
        const char c = token[0];
        if (c >= '0' && c <= '9') return kKeycode0 + (c - '0');
        if (c >= 'A' && c <= 'Z') return kKeycodeA + (c - 'A');
        if (c == ',') return kKeycodeComma;
        if (c == '.') return kKeycodePeriod;
        if (c == ' ') return kKeycodeSpace;
    }
    return -1;  // unknown token — driver rejects
}

const char* KeyEventModel::keycode_name(int keycode) {
    switch (keycode) {
    case kKeycodeBack: return "BACK";
    case kKeycodeDpadUp: return "DPAD_UP";
    case kKeycodeDpadDown: return "DPAD_DOWN";
    case kKeycodeDpadLeft: return "DPAD_LEFT";
    case kKeycodeDpadRight: return "DPAD_RIGHT";
    case kKeycodeDpadCenter: return "DPAD_CENTER";
    case kKeycodeEnter: return "ENTER";
    case kKeycodeDel: return "DEL";
    case kKeycodeSpace: return "SPACE";
    default: return "KEYCODE";
    }
}

uint32_t KeyEventModel::focus_search(const std::vector<FocusCandidate>& cands,
                                     int direction,
                                     const FocusCandidate& src) {
    // FocusFinder law: candidates must lie IN the direction (their near edge
    // must not be behind the source's far edge along the axis); score =
    // major-axis offset + 0.4 * minor-axis center offset. Documented
    // simplification of the AOSP beam algorithm (FocusFinder.java L620-700).
    const int scx = src.l + (src.r - src.l) / 2;
    const int scy = src.t + (src.b - src.t) / 2;
    uint32_t best = 0;
    double best_score = 1e18;
    for (const auto& c : cands) {
        if (!c.focusable || c.id == src.id) continue;
        const int ccx = c.l + (c.r - c.l) / 2;
        const int ccy = c.t + (c.b - c.t) / 2;
        double major = 0, minor = 0;
        bool in_dir = false;
        switch (direction) {
        case kKeycodeDpadUp:
            // Beam law (FocusFinder L620-700): UP/DOWN candidates must
            // horizontally BEAM-overlap the source.
            in_dir = (c.l < src.r && c.r > src.l) && (c.b <= src.t || ccy < scy);
            major = double(src.t - c.b);
            if (major < 0) major = 0;
            minor = double(std::abs(ccx - scx));
            break;
        case kKeycodeDpadDown:
            in_dir = (c.l < src.r && c.r > src.l) && (c.t >= src.b || ccy > scy);
            major = double(c.t - src.b);
            if (major < 0) major = 0;
            minor = double(std::abs(ccx - scx));
            break;
        case kKeycodeDpadLeft:
            // LEFT/RIGHT candidates must vertically BEAM-overlap.
            in_dir = (c.t < src.b && c.b > src.t) && (c.r <= src.l || ccx < scx);
            major = double(src.l - c.r);
            if (major < 0) major = 0;
            minor = double(std::abs(ccy - scy));
            break;
        case kKeycodeDpadRight:
            in_dir = (c.t < src.b && c.b > src.t) && (c.l >= src.r || ccx > scx);
            major = double(c.l - src.r);
            if (major < 0) major = 0;
            minor = double(std::abs(ccy - scy));
            break;
        default:
            return 0;
        }
        if (!in_dir) continue;
        const double score = major + 0.4 * minor;
        if (score < best_score) {
            best_score = score;
            best = c.id;
        }
    }
    return best;
}

}}  // namespace miniandroid::framework
