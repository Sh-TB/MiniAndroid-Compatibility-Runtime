/*
 * GOLDEN-03 §3/§7/§9 — CANONICAL RESOURCE-ID + TYPED-VALUE MODEL.
 *
 * The ONE source of truth for:
 *   • 0xPPTTEEEE decomposition / composition (ResId)            (§3)
 *   • Res_value dataType + complex-unit constants                (§7)
 *   • TypedValue complex→dimension / fraction / color laws       (§7/§9)
 *
 * Every resource consumer (ArscParser, AXML parser, LayoutInflater,
 * manifest reader, resource_trace) must use these helpers instead of
 * re-implementing bit manipulation or unit math.
 *
 * AOSP oracle (aosp-mirror/platform_frameworks_base @ 1cdfff555f4a):
 *   libs/androidfw/include/androidfw/ResourceTypes.h  — Res_value,
 *       ResTable_config, complex data layout (unit = low nibble,
 *       radix = bits 4-5, mantissa = bits 8-31).
 *   core/java/android/util/TypedValue.java — complexToFloat,
 *       applyDimension, complexToDimensionPixelSize (rounding +
 *       nonzero-floor tail), complexToFraction, coerceToString.
 *
 * GOLDEN DEBUG PROTOCOL: every law below cites its AOSP origin; nothing
 * is fitted to a fixture.
 */

#ifndef MINIANDROID_RES_ID_H
#define MINIANDROID_RES_ID_H

#include <cstdint>
#include <cstdio>
#include <string>
#include <optional>

namespace miniandroid {
namespace resources {

// ── Res_value dataType constants (ResourceTypes.h, Res_value.dataType) ────
enum ResValueType : uint8_t {
    RES_TYPE_NULL              = 0x00,  // TYPE_NULL
    RES_TYPE_REFERENCE         = 0x01,  // TYPE_REFERENCE      (data = ResTable_ref)
    RES_TYPE_ATTRIBUTE         = 0x02,  // TYPE_ATTRIBUTE      (data = attr id)
    RES_TYPE_STRING            = 0x03,  // TYPE_STRING         (data = pool index)
    RES_TYPE_FLOAT             = 0x04,  // TYPE_FLOAT          (data = IEEE-754 bits)
    RES_TYPE_DIMENSION         = 0x05,  // TYPE_DIMENSION      (complex)
    RES_TYPE_FRACTION          = 0x06,  // TYPE_FRACTION       (complex)
    RES_TYPE_DYNAMIC_REFERENCE = 0x07,  // TYPE_DYNAMIC_REFERENCE
    RES_TYPE_DYNAMIC_ATTRIBUTE = 0x08,  // TYPE_DYNAMIC_ATTRIBUTE
    RES_TYPE_FIRST_INT         = 0x10,
    RES_TYPE_INT_DEC           = 0x10,  // TYPE_INT_DEC
    RES_TYPE_INT_HEX           = 0x11,  // TYPE_INT_HEX
    RES_TYPE_INT_BOOLEAN       = 0x12,  // TYPE_INT_BOOLEAN    (0/1)
    RES_TYPE_FIRST_COLOR_INT   = 0x1C,
    RES_TYPE_INT_COLOR_ARGB8   = 0x1C,  // #AARRGGBB
    RES_TYPE_INT_COLOR_RGB8    = 0x1D,  // #RRGGBB (opaque)
    RES_TYPE_INT_COLOR_ARGB4   = 0x1E,  // #ARGB (4-bit)
    RES_TYPE_INT_COLOR_RGB4    = 0x1F,  // #RGB (4-bit)
};

// ── Complex data encoding (TypedValue.java) ────────────────────────────────
// data = mantissa(24b, signed, <<8) | radix(2b @4) | unit(4b @0)
static constexpr uint32_t COMPLEX_MANTISSA_MASK = 0x00FFFFFFu;
static constexpr uint32_t COMPLEX_MANTISSA_SHIFT = 8;
static constexpr uint32_t COMPLEX_RADIX_SHIFT    = 4;
static constexpr uint32_t COMPLEX_RADIX_MASK     = 0x3;
static constexpr uint32_t COMPLEX_UNIT_SHIFT     = 0;
static constexpr uint32_t COMPLEX_UNIT_MASK      = 0xF;

// Dimension units (low nibble when type == DIMENSION)
enum : uint8_t {
    COMPLEX_UNIT_PX   = 0,
    COMPLEX_UNIT_DIP  = 1,
    COMPLEX_UNIT_SP   = 2,
    COMPLEX_UNIT_PT   = 3,
    COMPLEX_UNIT_IN   = 4,
    COMPLEX_UNIT_MM   = 5,
};
// Fraction units (low nibble when type == FRACTION)
enum : uint8_t {
    COMPLEX_UNIT_FRACTION        = 0,  // % of base (item)
    COMPLEX_UNIT_FRACTION_PARENT = 1,  // % of parent
};

// ── Canonical resource id (§3) ─────────────────────────────────────────────
// 0xPPTTEEEE: package byte 3, type byte 2 (1-based into the package's type
// string pool), entry halfword 0. AOSP: Res_INTERNAL_ID / aapt2 PackageId.
struct ResId {
    uint8_t  package = 0;   // bits 24-31
    uint8_t  type    = 0;   // bits 16-23
    uint16_t entry   = 0;   // bits 0-15

    static constexpr ResId unpack(uint32_t id) {
        return ResId{(uint8_t)((id >> 24) & 0xFFu),
                     (uint8_t)((id >> 16) & 0xFFu),
                     (uint16_t)(id & 0xFFFFu)};
    }
    static constexpr uint32_t pack(uint8_t p, uint8_t t, uint16_t e) {
        return ((uint32_t)(p & 0xFFu) << 24) | ((uint32_t)(t & 0xFFu) << 16) |
               (uint32_t)(e & 0xFFFFu);
    }
    constexpr uint32_t pack() const { return pack(package, type, entry); }

    // AOSP validity: the type index is 1-based (0 = invalid); package 0 is
    // reserved ("null package"); entry is a full halfword.
    constexpr bool valid() const { return package != 0 && type != 0; }

    std::string to_string() const {
        char b[32];
        snprintf(b, sizeof b, "0x%08x", pack());
        return std::string(b);
    }
    std::string to_parts_string() const {
        char b[64];
        snprintf(b, sizeof b, "pkg=0x%02x type=0x%02x entry=0x%04x", package, type, entry);
        return std::string(b);
    }
};

// ── TypedValue laws (§9) — the ONE conversion path ─────────────────────────

// TypedValue.complexToFloat: mantissa × radix multiplier.
float complex_to_float(uint32_t data);   // defined in arsc_parser.cpp (existing)

// Device density model fed to the dimension laws. Mirrors the subset of
// android.util.DisplayMetrics the laws consume: density, scaledDensity
// (= density × fontScale), xdpi.
struct DensityContext {
    float density        = 2.625f;   // DisplayMetrics.density
    float scaled_density = 2.625f;   // DisplayMetrics.scaledDensity
    float xdpi           = 420.0f;   // DisplayMetrics.xdpi (physical dpi)

    static DensityContext from_density(float density, float font_scale = 1.0f) {
        DensityContext c;
        c.density = density;
        c.scaled_density = density * font_scale;
        c.xdpi = density * 160.0f;   // density = dpi/160 (AOSP DisplayMetrics law)
        return c;
    }
};

// TypedValue.applyDimension(unit, value, metrics) — AOSP law verbatim:
//   PX  → value
//   DIP → value × density
//   SP  → value × scaledDensity
//   PT  → value × xdpi × (1/72)
//   IN  → value × xdpi
//   MM  → value × xdpi × (1/25.4)
float complex_unit_to_dimension_px(uint8_t unit, float value, const DensityContext& metrics);

// TypedValue.complexToDimension(data, metrics): unit+nibble decode then
// applyDimension.
float complex_to_dimension_px(uint32_t complex_data, const DensityContext& metrics);

// TypedValue.complexToDimensionPixelSize(data, metrics) — full law:
//   value = complexToDimension(...)
//   res = (int)(value >= 0 ? value + 0.5f : value - 0.5f)   // round-toward-zero
//   if res != 0 → res;  if value == 0 → 0;  else ±1          // nonzero floor
int complex_to_dimension_pixel_size(uint32_t complex_data, const DensityContext& metrics);

// TypedValue.complexToFraction(data, base, pbase):
//   FRACTION        → complexToFloat(data) × base
//   FRACTION_PARENT → complexToFloat(data) × pbase
float complex_to_fraction(uint32_t complex_data, float base, float pbase);

// Color decode law (ResourceTypes.h TYPE_INT_COLOR_*): every color dataType
// → 0xAARRGGBB. Returns nullopt for non-color types.
std::optional<uint32_t> color_data_to_argb(uint8_t data_type, uint32_t data);

} // namespace resources
} // namespace miniandroid

#endif // MINIANDROID_RES_ID_H
