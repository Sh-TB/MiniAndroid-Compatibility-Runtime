/*
 * GOLDEN-03 §7/§9 — TypedValue law implementations.
 * Laws and AOSP citations: see res_id.h.
 */
#include "res_id.h"

namespace miniandroid {
namespace resources {

float complex_to_float(uint32_t data) {
    // AOSP TypedValue.complexToFloat — kept here as the single definition
    // (moved from arsc_parser.cpp; same math, now one source of truth).
    static const float MANTISSA_MULT = 1.0f / (1 << COMPLEX_MANTISSA_SHIFT);
    static const float RADIX_MULTS[] = {
        1.0f * MANTISSA_MULT,
        1.0f / (1 << 7)  * MANTISSA_MULT,   // radix 23p7  (2^-7)
        1.0f / (1 << 15) * MANTISSA_MULT,   // radix 23p15 (2^-15)
        1.0f / (1 << 23) * MANTISSA_MULT,   // radix 23p23 (2^-23)
    };
    uint32_t mantissa = data & (COMPLEX_MANTISSA_MASK << COMPLEX_MANTISSA_SHIFT);
    int32_t signed_m = (int32_t)mantissa;   // mantissa is signed 24-bit at bits 8..31
    return signed_m * RADIX_MULTS[(data >> COMPLEX_RADIX_SHIFT) & COMPLEX_RADIX_MASK];
}

float complex_unit_to_dimension_px(uint8_t unit, float value, const DensityContext& metrics) {
    // TypedValue.applyDimension — exact AOSP switch.
    switch (unit) {
        case COMPLEX_UNIT_PX:  return value;
        case COMPLEX_UNIT_DIP: return value * metrics.density;
        case COMPLEX_UNIT_SP:  return value * metrics.scaled_density;
        case COMPLEX_UNIT_PT:  return value * metrics.xdpi * (1.0f / 72.0f);
        case COMPLEX_UNIT_IN:  return value * metrics.xdpi;
        case COMPLEX_UNIT_MM:  return value * metrics.xdpi * (1.0f / 25.4f);
        default:               return value;   // unknown unit: AOSP returns value
    }
}

float complex_to_dimension_px(uint32_t complex_data, const DensityContext& metrics) {
    // TypedValue.complexToDimension: unit decode + applyDimension.
    const uint8_t unit = (uint8_t)((complex_data >> COMPLEX_UNIT_SHIFT) & COMPLEX_UNIT_MASK);
    return complex_unit_to_dimension_px(unit, complex_to_float(complex_data), metrics);
}

int complex_to_dimension_pixel_size(uint32_t complex_data, const DensityContext& metrics) {
    // TypedValue.complexToDimensionPixelSize — exact law including the
    // nonzero-floor tail (a 0.3px dimension does NOT silently become 0px).
    const float value = complex_to_dimension_px(complex_data, metrics);
    const int res = (int)(value >= 0 ? (value + 0.5f) : (value - 0.5f));
    if (res != 0) return res;
    if (value == 0.0f) return 0;
    return (value > 0.0f) ? 1 : -1;
}

float complex_to_fraction(uint32_t complex_data, float base, float pbase) {
    // TypedValue.complexToFraction.
    const uint8_t unit = (uint8_t)((complex_data >> COMPLEX_UNIT_SHIFT) & COMPLEX_UNIT_MASK);
    const float f = complex_to_float(complex_data);
    switch (unit) {
        case COMPLEX_UNIT_FRACTION:        return f * base;
        case COMPLEX_UNIT_FRACTION_PARENT: return f * pbase;
        default:                           return f;
    }
}

std::optional<uint32_t> color_data_to_argb(uint8_t data_type, uint32_t data) {
    // ResourceTypes.h color types → 0xAARRGGBB.
    switch (data_type) {
        case RES_TYPE_INT_COLOR_ARGB8: return data;                        // #AARRGGBB
        case RES_TYPE_INT_COLOR_RGB8:  return 0xFF000000u | data;          // #RRGGBB → opaque
        case RES_TYPE_INT_COLOR_ARGB4: {                                   // #ARGB
            uint32_t a = (data >> 12) & 0xF, r = (data >> 8) & 0xF,
                     g = (data >> 4) & 0xF, b = data & 0xF;
            return (a * 0x11) << 24 | (r * 0x11) << 16 | (g * 0x11) << 8 | (b * 0x11);
        }
        case RES_TYPE_INT_COLOR_RGB4: {                                    // #RGB
            uint32_t r = (data >> 8) & 0xF, g = (data >> 4) & 0xF, b = data & 0xF;
            return 0xFF000000u | (r * 0x11) << 16 | (g * 0x11) << 8 | (b * 0x11);
        }
        default: return std::nullopt;
    }
}

} // namespace resources
} // namespace miniandroid
