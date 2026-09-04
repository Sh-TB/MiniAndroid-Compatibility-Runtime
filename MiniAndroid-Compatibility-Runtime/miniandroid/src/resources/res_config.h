/*
 * CAMPAIGN 009 — §6 ARSC CONFIGURATION BUCKET MATCHING
 *
 * AOSP-faithful ResTable_config semantics, ported from:
 *   aosp-mirror/platform_frameworks_base @ 1cdfff555f4a
 *     libs/androidfw/include/androidfw/ResourceTypes.h  (struct ResTable_config)
 *     libs/androidfw/ResourceTypes.cpp                   (match/isBetterThan)
 *
 * Implements:
 *   ResTableConfig::from_bytes()   — parse raw config chunk bytes (big-endian fields)
 *   ResTableConfig::match()        — settings-compatible filter (exact AOSP order)
 *   ResTableConfig::isBetterThan() — best-config selection (exact AOSP order)
 *   device_config()                — the runtime's requested settings (env-overridable)
 *
 * GOLDEN DEBUG PROTOCOL: no fake data; unsupported fields documented below.
 */

#ifndef MINIANDROID_RES_CONFIG_H
#define MINIANDROID_RES_CONFIG_H

#include <cstdint>
#include <cstring>
#include <string>

namespace miniandroid {
namespace resources {

// AOSP ResTable_config constants
static constexpr uint16_t MASK_LAYOUTDIR       = 0xC0;
static constexpr uint16_t MASK_SCREENSIZE      = 0x0F;
static constexpr uint16_t MASK_SCREENLONG      = 0x30;
static constexpr uint16_t MASK_UI_MODE_TYPE    = 0x0F;
static constexpr uint16_t MASK_UI_MODE_NIGHT   = 0x30;
static constexpr uint16_t MASK_KEYSHIDDEN      = 0x03;
static constexpr uint16_t MASK_NAVHIDDEN       = 0x0C;
static constexpr uint16_t MASK_SCREENROUND     = 0x03;
static constexpr uint16_t MASK_HDR             = 0x0C;
static constexpr uint16_t MASK_WIDE_COLOR_GAMUT= 0x03;

static constexpr uint16_t DENSITY_DEFAULT      = 0;
static constexpr uint16_t DENSITY_LOW          = 120;
static constexpr uint16_t DENSITY_MEDIUM       = 160;
static constexpr uint16_t DENSITY_TV           = 213;
static constexpr uint16_t DENSITY_HIGH         = 240;
static constexpr uint16_t DENSITY_XHIGH        = 320;
static constexpr uint16_t DENSITY_XXHIGH       = 480;
static constexpr uint16_t DENSITY_XXXHIGH      = 640;
static constexpr uint16_t DENSITY_ANY          = 0xFFFE;
static constexpr uint16_t DENSITY_NONE         = 0xFFFF;

static constexpr uint8_t  ORIENTATION_PORTRAIT  = 1;
static constexpr uint8_t  ORIENTATION_LANDSCAPE = 2;

// AOSP ResTable_config binary layout (ResourceTypes.h @ 1cdfff555f4a).
// All multi-byte fields are little-endian ON DISK in the ARSC; language/country
// are packed big-endian 2-char pairs (packLanguage).
struct ResTableConfig {
    uint32_t size = 0;               // bytes actually present in the chunk
    // imsi
    uint32_t mcc = 0, mnc = 0;
    // locale
    uint8_t  language[2] = {0, 0};   // packed (see unpack_language)
    uint8_t  country[2]  = {0, 0};
    char     localeScript[4] = {0,0,0,0};
    char     localeVariant[8] = {0,0,0,0,0,0,0,0};
    uint8_t  localeNumberingSystem[8] = {0,0,0,0,0,0,0,0};
    // screenType
    uint8_t  orientation = 0, touchscreen = 0;
    uint16_t density = 0;
    // input
    uint8_t  keyboard = 0, navigation = 0, inputFlags = 0, inputPad0 = 0;
    // screenSize
    uint16_t screenWidth = 0, screenHeight = 0;
    // version
    uint16_t sdkVersion = 0, minorVersion = 0;
    // screenConfig
    uint8_t  screenLayout = 0, uiMode = 0;
    uint16_t smallestScreenWidthDp = 0;
    // screenConfig2
    uint8_t  screenLayout2 = 0, colorMode = 0;
    // screenSizeDp
    uint16_t screenWidthDp = 0, screenHeightDp = 0;
    // grammaticalInflection (newer tables)
    uint8_t  grammaticalInflection = 0;

    uint32_t locale = 0;   // computed: 1 if any locale field set
    uint32_t imsi = 0, screenType = 0, input = 0, screenSize = 0, version = 0;
    uint32_t screenConfig = 0, screenConfig2 = 0, screenSizeDpMask = 0;

    bool localeScriptWasComputed = false;

    // ---- parse from raw ARSC config bytes (little-endian fields) ----
    // Layout: 0 size | 4 mcc | 6 mnc | 8 language[2] | 10 country[2] | 12 orientation
    //   13 touchscreen | 14 density | 16 keyboard | 17 navigation | 18 inputFlags
    //   20 screenWidth | 22 screenHeight | 24 sdkVersion | 26 minorVersion
    //   28 screenLayout | 29 uiMode | 30 smallestScreenWidthDp | 32 screenLayout2
    //   33 colorMode | 36 screenWidthDp | 38 screenHeightDp | 40 localeScript[4]
    //   44 localeVariant[8] | 52 localeNumberingSystem[8] | 60 grammaticalInflection
    static ResTableConfig from_bytes(const uint8_t* p, size_t avail);

    // ---- AOSP semantics ----
    bool match(const ResTableConfig& settings) const;
    bool isBetterThan(const ResTableConfig& o, const ResTableConfig& requested) const;

    // ---- helpers ----
    uint16_t screen_layout_dir() const { return screenLayout & MASK_LAYOUTDIR; }
    uint16_t screen_size_bucket() const { return screenLayout & MASK_SCREENSIZE; }
    uint16_t screen_long() const { return screenLayout & MASK_SCREENLONG; }
    uint16_t ui_mode_type() const { return uiMode & MASK_UI_MODE_TYPE; }
    uint16_t ui_mode_night() const { return uiMode & MASK_UI_MODE_NIGHT; }
    uint16_t keys_hidden() const { return inputFlags & MASK_KEYSHIDDEN; }
    uint16_t nav_hidden() const { return inputFlags & MASK_NAVHIDDEN; }
    uint16_t screen_round() const { return screenLayout2 & MASK_SCREENROUND; }
    uint16_t hdr() const { return colorMode & MASK_HDR; }
    uint16_t wide_gamut() const { return colorMode & MASK_WIDE_COLOR_GAMUT; }

    // unpack packed 2-char language/country (AOSP packLanguage: 7-bit ASCII packing)
    std::string language_str() const { return unpack_language(language); }
    std::string country_str() const { return unpack_country(country); }

    void compute_fields();   // derive the union-key fields (locale, screenConfig, ...)

    // human-readable qualifier string ("b+en+US", "480dpi", "sw360dp"...)
    std::string to_string() const;

private:
    static std::string unpack_language(const uint8_t in[2]);
    static std::string unpack_country(const uint8_t in[2]);
    static bool langs_are_equivalent(const uint8_t lang_a[2], const uint8_t lang_b[2]);
    static bool are_identical(const uint8_t a[2], const uint8_t b[2]) {
        return a[0] == b[0] && a[1] == b[1];
    }
    static bool is_locale_better_than(const ResTableConfig& self, const ResTableConfig& o,
                                      const ResTableConfig& requested);
};

// The runtime's requested configuration (device model). Env-overridable:
//   MINIANDROID_LOCALE   ("fa", "fa-IR", "en-US", "zh-CN"...)   default "en-US"
//   MINIANDROID_DENSITY  (dpi int)                              default 480 (xxhdpi)
const ResTableConfig& device_config();

} // namespace resources
} // namespace miniandroid

#endif // MINIANDROID_RES_CONFIG_H
