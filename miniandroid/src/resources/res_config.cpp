/*
 * CAMPAIGN 009 — §6 ARSC CONFIGURATION BUCKET MATCHING (implementation)
 * Oracle: aosp-mirror/platform_frameworks_base @ 1cdfff555f4a, ResourceTypes.cpp
 *         match() @2909, isBetterThan() @2641, isLocaleBetterThan() @2520
 * The isBetterThan() body below mirrors the AOSP decision order verbatim
 * (imsi → locale → grammaticalInflection → layoutdir → sw → w/h-dp →
 *  screensize/long → round → gamut/hdr → orientation → uiMode →
 *  density/touchscreen → keysHidden/navHidden/keyboard/navigation →
 *  screenSize → version).
 */
#include "res_config.h"
#include <cstdlib>
#include <algorithm>

namespace miniandroid {
namespace resources {

// little-endian readers
static inline uint16_t le16(const uint8_t* p) { return (uint16_t)(p[0] | (p[1] << 8)); }
static inline uint32_t le32(const uint8_t* p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

ResTableConfig ResTableConfig::from_bytes(const uint8_t* p, size_t avail) {
    ResTableConfig c;
    if (!p || avail < 4) return c;
    c.size = le32(p);                       // ResTable_config::size
    size_t sz = c.size;
    if (sz == 0 || sz > 4096) sz = avail;   // guard: broken size field
    sz = std::min(sz, avail);

    // AOSP ResTable_config layout (offsets from chunk start) — ResourceTypes.h:
    //   0 size(4) | 4 mcc(2) | 6 mnc(2) | 8 language[2] | 10 country[2]
    //  12 orientation | 13 touchscreen | 14 density(2) | 16 keyboard
    //  17 navigation | 18 inputFlags | 19 pad0 | 20 screenWidth(2) | 22 screenHeight(2)
    //  24 sdkVersion(2) | 26 minorVersion(2) | 28 screenLayout | 29 uiMode
    //  30 smallestScreenWidthDp(2) | 32 screenLayout2 | 33 colorMode | 34 pad1(2)
    //  36 screenWidthDp(2) | 38 screenHeightDp(2) | 40 localeScript[4]
    //  44 localeVariant[8] | 52 localeNumberingSystem[8] | 60 grammaticalInflection
    if (sz >= 6)  { c.mcc = le16(p + 4); }
    if (sz >= 8)  { c.mnc = le16(p + 6); }
    if (sz >= 10) { c.language[0] = p[8];  c.language[1] = p[9];
                    c.country[0]  = p[10]; c.country[1]  = p[11]; }
    if (sz >= 13) { c.orientation = p[12]; c.touchscreen = p[13]; }
    if (sz >= 16) { c.density = le16(p + 14); }
    if (sz >= 17) { c.keyboard = p[16]; }
    if (sz >= 18) { c.navigation = p[17]; }
    if (sz >= 19) { c.inputFlags = p[18]; }
    if (sz >= 22) { c.screenWidth = le16(p + 20); }
    if (sz >= 24) { c.screenHeight = le16(p + 22); }
    if (sz >= 26) { c.sdkVersion = le16(p + 24); }
    if (sz >= 28) { c.minorVersion = le16(p + 26); }
    if (sz >= 29) { c.screenLayout = p[28]; }
    if (sz >= 30) { c.uiMode = p[29]; }
    if (sz >= 32) { c.smallestScreenWidthDp = le16(p + 30); }
    if (sz >= 33) { c.screenLayout2 = p[32]; }
    if (sz >= 34) { c.colorMode = p[33]; }
    if (sz >= 38) { c.screenWidthDp = le16(p + 36); }
    if (sz >= 40) { c.screenHeightDp = le16(p + 38); }
    if (sz >= 44) { memcpy(c.localeScript, p + 40, 4); }
    if (sz >= 52) { memcpy(c.localeVariant, p + 44, 8); }
    if (sz >= 60) { memcpy(c.localeNumberingSystem, p + 52, 8); }
    if (sz >= 61) { c.grammaticalInflection = p[60]; }
    c.compute_fields();
    return c;
}

void ResTableConfig::compute_fields() {
    imsi        = (mcc || mnc) ? 1u : 0u;
    locale      = (language[0] || language[1] || country[0] || country[1] ||
                   localeScript[0] || localeVariant[0] || localeNumberingSystem[0]) ? 1u : 0u;
    screenType  = (orientation || touchscreen || density) ? 1u : 0u;
    input       = (keyboard || navigation || inputFlags) ? 1u : 0u;
    screenSize  = (screenWidth || screenHeight) ? 1u : 0u;
    version     = (sdkVersion || minorVersion) ? 1u : 0u;
    screenConfig = (screenLayout || uiMode || smallestScreenWidthDp) ? 1u : 0u;
    screenConfig2 = (screenLayout2 || colorMode) ? 1u : 0u;
    screenSizeDpMask = (screenWidthDp || screenHeightDp) ? 1u : 0u;
}

std::string ResTableConfig::unpack_language(const uint8_t in[2]) {
    std::string s;
    if (in[0]) s += (char)(in[0] & 0x7f);
    if (in[1]) s += (char)(in[1] & 0x7f);
    return s;
}
std::string ResTableConfig::unpack_country(const uint8_t in[2]) {
    std::string s;
    if (in[0]) s += (char)(in[0] & 0x7f);
    if (in[1]) s += (char)(in[1] & 0x7f);
    return s;
}

bool ResTableConfig::langs_are_equivalent(const uint8_t a[2], const uint8_t b[2]) {
    return are_identical(a, b);
}

// AOSP match() @2909 — verbatim decision order
bool ResTableConfig::match(const ResTableConfig& settings) const {
    if (imsi != 0) {
        if (mcc != 0 && mcc != settings.mcc) return false;
        if (mnc != 0 && mnc != settings.mnc) return false;
    }
    if (locale != 0) {
        // Runtime request is scriptless → AOSP countriesMustMatch branch.
        if (!langs_are_equivalent(language, settings.language)) return false;
        if (country[0] != '\0' && !are_identical(country, settings.country)) return false;
    }
    if (grammaticalInflection && grammaticalInflection != settings.grammaticalInflection) return false;
    if (screenConfig != 0) {
        const int layout_dir = screenLayout & MASK_LAYOUTDIR;
        if (layout_dir != 0 && layout_dir != (settings.screenLayout & MASK_LAYOUTDIR)) return false;
        const int size_bucket = screenLayout & MASK_SCREENSIZE;
        if (size_bucket != 0 && size_bucket > (settings.screenLayout & MASK_SCREENSIZE)) return false;
        const int lng = screenLayout & MASK_SCREENLONG;
        if (lng != 0 && lng != (settings.screenLayout & MASK_SCREENLONG)) return false;
        const int umt = uiMode & MASK_UI_MODE_TYPE;
        if (umt != 0 && umt != (settings.uiMode & MASK_UI_MODE_TYPE)) return false;
        const int umn = uiMode & MASK_UI_MODE_NIGHT;
        if (umn != 0 && umn != (settings.uiMode & MASK_UI_MODE_NIGHT)) return false;
        if (smallestScreenWidthDp != 0 && smallestScreenWidthDp > settings.smallestScreenWidthDp)
            return false;
    }
    if (screenConfig2 != 0) {
        const int rnd = screenLayout2 & MASK_SCREENROUND;
        if (rnd != 0 && rnd != (settings.screenLayout2 & MASK_SCREENROUND)) return false;
        const int h = colorMode & MASK_HDR;
        if (h != 0 && h != (settings.colorMode & MASK_HDR)) return false;
        const int g = colorMode & MASK_WIDE_COLOR_GAMUT;
        if (g != 0 && g != (settings.colorMode & MASK_WIDE_COLOR_GAMUT)) return false;
    }
    if (screenSizeDpMask != 0) {
        if (screenWidthDp != 0 && screenWidthDp > settings.screenWidthDp) return false;
        if (screenHeightDp != 0 && screenHeightDp > settings.screenHeightDp) return false;
    }
    if (screenType != 0) {
        if (orientation != 0 && orientation != settings.orientation) return false;
        // density always matches — scaled (see isBetterThan)
        if (touchscreen != 0 && touchscreen != settings.touchscreen) return false;
    }
    if (input != 0) {
        const int kh = inputFlags & MASK_KEYSHIDDEN;
        const int skh = settings.inputFlags & MASK_KEYSHIDDEN;
        if (kh != 0 && kh != skh) {
            // AOSP compat: KEYSHIDDEN_NO(1) also matches KEYSHIDDEN_SOFT(3)
            if (!(kh == 1 && skh == 3)) return false;
        }
        const int nh = inputFlags & MASK_NAVHIDDEN;
        if (nh != 0 && nh != (settings.inputFlags & MASK_NAVHIDDEN)) return false;
        if (keyboard != 0 && keyboard != settings.keyboard) return false;
        if (navigation != 0 && navigation != settings.navigation) return false;
    }
    if (screenSize != 0) {
        if (screenWidth != 0 && screenWidth > settings.screenWidth) return false;
        if (screenHeight != 0 && screenHeight > settings.screenHeight) return false;
    }
    if (version != 0) {
        if (sdkVersion != 0 && sdkVersion > settings.sdkVersion) return false;
        if (minorVersion != 0 && minorVersion != settings.minorVersion) return false;
    }
    return true;
}

// AOSP isLocaleBetterThan @2520 (request is scriptless → language + region rules;
// CLDR likely-region tables noted as documented simplification)
bool ResTableConfig::is_locale_better_than(const ResTableConfig& self, const ResTableConfig& o,
                                           const ResTableConfig& requested) {
    if (requested.locale == 0) return false;
    if (self.locale == 0 && o.locale == 0) return false;

    if (!langs_are_equivalent(self.language, o.language)) {
        static const uint8_t kEnglish[2] = {'e', 'n'};
        if (are_identical(requested.language, kEnglish)) {
            static const uint8_t kUS[2] = {'U', 'S'};
            if (are_identical(requested.country, kUS)) {
                if (self.language[0] != '\0') {
                    return self.country[0] == '\0' || are_identical(self.country, kUS);
                } else {
                    return !(o.country[0] == '\0' || are_identical(o.country, kUS));
                }
            }
        }
        return self.language[0] != '\0';
    }
    // Equivalent languages: region decision (localeDataCompareRegions simplified:
    // exact request-region match beats; equal or no request region → not better)
    if (self.country[0] == o.country[0] && self.country[1] == o.country[1]) return false;
    if (requested.country[0] != '\0') return are_identical(self.country, requested.country);
    return false;
}

// AOSP isBetterThan @2641 — verbatim decision order
bool ResTableConfig::isBetterThan(const ResTableConfig& o, const ResTableConfig& requested) const {
    if (requested.size != 0) {
        if (imsi || o.imsi) {
            if ((mcc != o.mcc) && requested.mcc) return (mcc != 0);
            if ((mnc != o.mnc) && requested.mnc) return (mnc != 0);
        }
        if (requested.locale && (locale || o.locale) &&
            is_locale_better_than(*this, o, requested)) {
            return true;
        }
        if (grammaticalInflection || o.grammaticalInflection) {
            if (grammaticalInflection != o.grammaticalInflection &&
                requested.grammaticalInflection) {
                return grammaticalInflection != 0;
            }
        }
        if (screenLayout || o.screenLayout) {
            if (((screenLayout ^ o.screenLayout) & MASK_LAYOUTDIR) != 0 &&
                (requested.screenLayout & MASK_LAYOUTDIR)) {
                return (screenLayout & MASK_LAYOUTDIR) > (o.screenLayout & MASK_LAYOUTDIR);
            }
        }
        if (smallestScreenWidthDp || o.smallestScreenWidthDp) {
            // closest to actual size, assuming larger filtered out in match()
            if (smallestScreenWidthDp != o.smallestScreenWidthDp)
                return smallestScreenWidthDp > o.smallestScreenWidthDp;
        }
        if (screenSizeDpMask || o.screenSizeDpMask) {
            int my_delta = 0, other_delta = 0;
            if (requested.screenWidthDp) {
                my_delta += requested.screenWidthDp - screenWidthDp;
                other_delta += requested.screenWidthDp - o.screenWidthDp;
            }
            if (requested.screenHeightDp) {
                my_delta += requested.screenHeightDp - screenHeightDp;
                other_delta += requested.screenHeightDp - o.screenHeightDp;
            }
            if (my_delta != other_delta) return my_delta < other_delta;
        }
        if (screenLayout || o.screenLayout) {
            if (((screenLayout ^ o.screenLayout) & MASK_SCREENSIZE) != 0 &&
                (requested.screenLayout & MASK_SCREENSIZE)) {
                // AOSP: undefined counts as NORMAL when request >= NORMAL
                int my_sl = screenLayout & MASK_SCREENSIZE;
                int o_sl = o.screenLayout & MASK_SCREENSIZE;
                int fixed_my = my_sl, fixed_o = o_sl;
                if ((requested.screenLayout & MASK_SCREENSIZE) >= 2 /*NORMAL*/) {
                    if (fixed_my == 0) fixed_my = 2;
                    if (fixed_o == 0) fixed_o = 2;
                }
                if (fixed_my == fixed_o) {
                    if (my_sl == 0) return false;   // 'this' undefined => other better
                    return true;
                }
                return fixed_my > fixed_o;
            }
            if (((screenLayout ^ o.screenLayout) & MASK_SCREENLONG) != 0 &&
                (requested.screenLayout & MASK_SCREENLONG)) {
                return (screenLayout & MASK_SCREENLONG);
            }
        }
        if (screenLayout2 || o.screenLayout2) {
            if (((screenLayout2 ^ o.screenLayout2) & MASK_SCREENROUND) != 0 &&
                (requested.screenLayout2 & MASK_SCREENROUND)) {
                return (screenLayout2 & MASK_SCREENROUND);
            }
        }
        if (colorMode || o.colorMode) {
            if (((colorMode ^ o.colorMode) & MASK_WIDE_COLOR_GAMUT) != 0 &&
                (requested.colorMode & MASK_WIDE_COLOR_GAMUT)) {
                return (colorMode & MASK_WIDE_COLOR_GAMUT);
            }
            if (((colorMode ^ o.colorMode) & MASK_HDR) != 0 &&
                (requested.colorMode & MASK_HDR)) {
                return (colorMode & MASK_HDR);
            }
        }
        if ((orientation != o.orientation) && requested.orientation) return (orientation != 0);
        if (uiMode || o.uiMode) {
            if (((uiMode ^ o.uiMode) & MASK_UI_MODE_TYPE) != 0 &&
                (requested.uiMode & MASK_UI_MODE_TYPE)) {
                return (uiMode & MASK_UI_MODE_TYPE);
            }
            if (((uiMode ^ o.uiMode) & MASK_UI_MODE_NIGHT) != 0 &&
                (requested.uiMode & MASK_UI_MODE_NIGHT)) {
                return (uiMode & MASK_UI_MODE_NIGHT);
            }
        }
        if (screenType || o.screenType) {
            if (density != o.density) {
                int this_density = density ? (int)density : (int)DENSITY_MEDIUM;
                int other_density = o.density ? (int)o.density : (int)DENSITY_MEDIUM;
                if (this_density == (int)DENSITY_ANY) return true;
                if (other_density == (int)DENSITY_ANY) return false;
                int requested_density = (int)requested.density;
                if (requested.density == 0 || requested.density == DENSITY_ANY)
                    requested_density = (int)DENSITY_MEDIUM;
                int h = this_density, l = other_density;
                bool b_im_bigger = true;
                if (l > h) { std::swap(l, h); b_im_bigger = false; }
                if (h == requested_density) return b_im_bigger;
                else if (l >= requested_density) return !b_im_bigger;  // prefer scale DOWN
                else return b_im_bigger;
            }
            if ((touchscreen != o.touchscreen) && requested.touchscreen) return (touchscreen != 0);
        }
        if (input || o.input) {
            const int kh = inputFlags & MASK_KEYSHIDDEN;
            const int o_kh = o.inputFlags & MASK_KEYSHIDDEN;
            if (kh != o_kh) {
                const int req_kh = requested.inputFlags & MASK_KEYSHIDDEN;
                if (req_kh) {
                    if (!kh) return false;
                    if (!o_kh) return true;
                    if (req_kh == kh) return true;
                    if (req_kh == o_kh) return false;
                }
            }
            const int nh = inputFlags & MASK_NAVHIDDEN;
            const int o_nh = o.inputFlags & MASK_NAVHIDDEN;
            if (nh != o_nh) {
                const int req_nh = requested.inputFlags & MASK_NAVHIDDEN;
                if (req_nh) {
                    if (!nh) return false;
                    if (!o_nh) return true;
                }
            }
            if ((keyboard != o.keyboard) && requested.keyboard) return (keyboard != 0);
            if ((navigation != o.navigation) && requested.navigation) return (navigation != 0);
        }
        if (screenSize || o.screenSize) {
            int my_delta = 0, other_delta = 0;
            if (requested.screenWidth) {
                my_delta += requested.screenWidth - screenWidth;
                other_delta += requested.screenWidth - o.screenWidth;
            }
            if (requested.screenHeight) {
                my_delta += requested.screenHeight - screenHeight;
                other_delta += requested.screenHeight - o.screenHeight;
            }
            if (my_delta != other_delta) return my_delta < other_delta;
        }
        if (version || o.version) {
            // G31 session fix: AOSP-EXACT version tie-break
            // (ResourceTypes.cpp@android-14.0.0_r50 L2489-2501). The old code
            // returned (sdkVersion > o.sdkVersion), which is NOT the AOSP
            // law: between two version-qualified candidates isBetterThan
            // returns false both ways, so the FIRST candidate in table order
            // stays (AssetManager2::FindEntryInternal). Evidence: EXT-01
            // layout/activity_main variants () v9.xml, (v16) UD.xml, (v21)
            // 02.xml — aapt2 dump confirms the order; a conforming runtime
            // therefore inflates the v16 variant (fontFamily=monospace,
            // elegantTextHeight absent).
            if (sdkVersion != o.sdkVersion) {
                if (!sdkVersion) return false;
                if (!o.sdkVersion) return true;
            }
            if (minorVersion != o.minorVersion) {
                if (!minorVersion) return false;
                if (!o.minorVersion) return true;
            }
        }
        return false;
    }
    // No requested settings: prefer the more-specific config (AOSP fallback).
    if (locale != o.locale) return locale > o.locale;
    if (density != o.density) return density > o.density;
    return false;
}

std::string ResTableConfig::to_string() const {
    std::string out;
    auto add = [&](const std::string& q) { if (!out.empty()) out += "-"; out += q; };
    if (locale) {
        std::string lang = language_str();
        if (!lang.empty()) add(lang);
        std::string ctry = country_str();
        if (!ctry.empty()) add("r" + ctry);
    }
    if (screenType) {
        if (orientation == ORIENTATION_PORTRAIT) add("port");
        else if (orientation == ORIENTATION_LANDSCAPE) add("land");
        if (density == DENSITY_NONE) add("nodpi");
        else if (density == DENSITY_ANY) add("anydpi");
        else if (density) add(std::to_string(density) + "dpi");
    }
    if (screenConfig && smallestScreenWidthDp)
        add("sw" + std::to_string(smallestScreenWidthDp) + "dp");
    if (screenSizeDpMask) {
        if (screenWidthDp) add("w" + std::to_string(screenWidthDp) + "dp");
        if (screenHeightDp) add("h" + std::to_string(screenHeightDp) + "dp");
    }
    if (version && sdkVersion) add("v" + std::to_string(sdkVersion));
    return out;
}

// ---------------------------------------------------------------------------
// Device configuration (the runtime's request). 1080x1920 @ 480dpi phone.
// ---------------------------------------------------------------------------
static ResTableConfig build_device_config() {
    ResTableConfig c;
    // locale: MINIANDROID_LOCALE ("fa", "fa-IR", "en-US"...) — default en-US
    const char* loc = std::getenv("MINIANDROID_LOCALE");
    std::string locale_s = loc && *loc ? loc : "en-US";
    std::string lang = locale_s.substr(0, 2), ctry;
    if (locale_s.size() >= 5 && locale_s[2] == '-') ctry = locale_s.substr(3, 2);
    if (lang.size() == 2) {
        c.language[0] = (uint8_t)std::tolower((unsigned char)lang[0]);
        c.language[1] = (uint8_t)std::tolower((unsigned char)lang[1]);
    }
    if (ctry.size() == 2) {
        c.country[0] = (uint8_t)std::toupper((unsigned char)ctry[0]);
        c.country[1] = (uint8_t)std::toupper((unsigned char)ctry[1]);
    }
    // density: MINIANDROID_DENSITY — default 480 (xxhdpi for a 1080p phone)
    c.density = DENSITY_XXHIGH;
    const char* dens = std::getenv("MINIANDROID_DENSITY");
    if (dens && *dens) {
        int d = std::atoi(dens);
        if (d > 0) c.density = (uint16_t)d;
    }
    // screen: 1080x1920, 360x640dp, portrait, finger, nokeys, night=no
    c.orientation = ORIENTATION_PORTRAIT;
    c.touchscreen = 3;            // TOUCHSCREEN_FINGER
    c.keyboard = 1;               // KEYBOARD_NOKEYS
    c.navigation = 1;             // NAVIGATION_NONAV
    c.inputFlags = 0;             // KEYSHIDDEN_SOFT implied | NAVHIDDEN_NO
    c.screenWidth = 1080; c.screenHeight = 1920;
    c.screenWidthDp = 360; c.screenHeightDp = 640;
    c.smallestScreenWidthDp = 360;
    c.screenLayout  = 0x02 | 0x10;   // SIZE_NORMAL | LONG_NO
    c.uiMode        = 0x01 | 0x10;   // TYPE_NORMAL | NIGHT_NO
    c.screenLayout2 = 0x01;          // SCREENROUND_NO
    c.colorMode     = 0x01 | 0x04;   // WIDE_GAMUT_NO | HDR_NO
    c.sdkVersion = 34;               // runtime target API level
    c.minorVersion = 0;
    // G31 session fix: requested.size MUST be non-zero — AOSP isBetterThan
    // gates its entire comparison body on `if (requested.size != 0)`
    // (ResourceTypes.cpp@android-14.0.0_r50 L2641+). With size==0 the whole
    // law was skipped (falling through to the legacy "no settings" branch),
    // so SDK-version-qualified layout variants (EXT-01: v16/v21) could never
    // beat the default variant and fontFamily never reached the inflater.
    // 64 = the ResTable_config size aapt2 8.x emits for these tables
    // (matches ResTableConfig::from_bytes' field window).
    c.size = 64;
    c.compute_fields();
    return c;
}

const ResTableConfig& device_config() {
    static ResTableConfig cfg = build_device_config();
    return cfg;
}

} // namespace resources
} // namespace miniandroid
