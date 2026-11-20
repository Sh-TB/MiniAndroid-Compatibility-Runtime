// s18_dimension_rounding_laws_test — S18 family A (#632-M3): the ONE canonical
// dimension-conversion law at res_id.cpp (complex_unit_to_dimension_pixel_size
// — "The ONE rounding + nonzero-floor implementation", public in res_id.h).
// Expected values computed arithmetically BEFORE the test was written (see
// RAW_LOGS/s18_methodology_2026-11-20.md §A): C-style trunc-toward-zero of
// px±0.5, then the nonzero-floor tail (res==0 && px!=0 -> ±1).
// Laws:
//   A1  20dp @2.625 -> 53   (52.5 -> round-half-away, matches S17 R2.a)
//   A2  fractional positives hit the nonzero floor: 0.2dp->1, 0.1dp->1, 0.04dp->1
//   A3  negatives: -20dp->-53, -0.1dp->-1 (floor mirrors the sign)
//   A4  physical units off xdpi=420: 1in->420, 1mm->17, 1pt->6
//   A5  sp via scaled_density 3.4125: 10sp -> 34
//   A6  typed complex WORD path (mantissa<<8|unit) agrees with the float path
//   A7  zero is zero: 0.0 -> 0; magnitude law holds at 1e6dp (no overflow)
#include "../src/resources/res_id.h"
#include "../src/resources/arsc_parser.h"
#include <cstdio>
#include <iostream>
#include <string>

using namespace miniandroid;

static int g_pass = 0, g_fail = 0;
static void record(bool ok, const std::string& what) {
    std::cout << (ok ? "  PASS  " : "  FAIL  ") << what << "\n";
    if (ok) ++g_pass; else ++g_fail;
}
static resources::DensityContext ctx() {
    resources::DensityContext c;
    c.density = 2.625f;
    c.scaled_density = 3.4125f;  // 2.625 * 1.3
    c.xdpi = 420.0f;
    return c;
}
using CU = resources::DimUnit;  // DIM_DIP=1, DIM_SP=2, DIM_PT=3, DIM_IN=4, DIM_MM=5

int main() {
    std::cout << "== s18 dimension rounding laws (M3) ==\n";
    auto c = ctx();
    auto px = [&](float v, uint8_t unit) {
        return resources::complex_unit_to_dimension_pixel_size(unit, v, c);
    };

    record(px(20.0f, CU::DIM_DIP) == 53, "A1 20dp @2.625 -> 53 (round-half-away)");
    record(px(0.2f, CU::DIM_DIP) == 1 && px(0.1f, CU::DIM_DIP) == 1 &&
           px(0.04f, CU::DIM_DIP) == 1,
           "A2 nonzero floor: 0.2dp/0.1dp/0.04dp -> 1 (never 0 for nonzero)");
    record(px(-20.0f, CU::DIM_DIP) == -53 && px(-0.1f, CU::DIM_DIP) == -1,
           "A3 negatives: -20dp -> -53, -0.1dp -> -1 (sign-mirrored floor)");
    record(px(1.0f, CU::DIM_IN) == 420 && px(1.0f, CU::DIM_MM) == 17 &&
           px(1.0f, CU::DIM_PT) == 6,
           "A4 physical units off xdpi=420: 1in->420, 1mm->17, 1pt->6");
    record(px(10.0f, CU::DIM_SP) == 34,
           "A5 10sp @scaled_density 3.4125 -> 34 (matches S17 R3)");

    // A6: the typed complex WORD path (GOLDEN-03 §9 canonical form) must agree
    // with the float path. word = (mantissa << 8) | unit for radix 0.
    uint32_t word20dp = (20u << 8) | CU::DIM_DIP;
    uint32_t word1in  = (1u << 8) | CU::DIM_IN;
    record(resources::complex_to_dimension_pixel_size(word20dp, c) == 53 &&
           resources::complex_to_dimension_pixel_size(word1in, c) == 420,
           "A6 typed word path agrees: (20<<8)|DIP -> 53, (1<<8)|IN -> 420");

    record(px(0.0f, CU::DIM_DIP) == 0 &&
           px(1000000.0f, CU::DIM_DIP) == 2625000,
           "A7 zero stays zero; 1e6dp -> 2625000 (no overflow/tail)");

    std::cout << "== s18 dimension rounding laws: " << g_pass << " pass / "
              << g_fail << " fail ==\n";
    return g_fail == 0 ? 0 : 1;
}
