// GOLDEN-03 — canonical resource-id / resolution / TypedValue law test.
//
// Proves, against synthetic in-memory ARSC tables (no fixture dependency):
//   §3  ResId canonical pack/unpack/validity — one decomposition model
//   §7  Res_value semantic boundaries: FRACTION decode, FLOAT passthrough,
//       color decode law (ARGB8/RGB8/ARGB4/RGB4 → 0xAARRGGBB)
//   §9  TypedValue laws: complexToFloat, applyDimension (PX/DIP/SP/PT/IN/MM),
//       complexToDimensionPixelSize (rounding + nonzero-floor tail),
//       complexToFraction
//   §4  resolve(resourceId, deviceConfig) → structured ResolutionResult:
//       reference chain recorded, selected configuration reported per step
//   §6  bounded/cycle-safe reference resolution with NAMED deterministic
//       failures: MISSING_ENTRY, INVALID_ID, MISSING_REFERENCE_TARGET,
//       CYCLE (self + mutual), DEPTH_EXCEEDED
//   §8  attribute-key style-bag query with ResTable_map_entry parent
//       inheritance, parent-cycle safety
//
// AOSP oracle: aosp-mirror/platform_frameworks_base @ 1cdfff555f4a —
// ResourceTypes.h Res_value/ResTable_map, TypedValue.java
// (complexToFloat @1054, applyDimension @917, complexToDimensionPixelSize,
// complexToFraction @961), AssetManager2 resolveReference chain semantics.
#include "synthetic_arsc.h"

#include <cmath>
#include <cstdio>
#include <iostream>
#include <string>

using namespace miniandroid::resources;
using synthetic_arsc::append32;
using synthetic_arsc::append16;
using synthetic_arsc::put32;

static int g_pass = 0, g_fail = 0;
static void check(bool ok, const std::string& what) {
    if (ok) { g_pass++; std::cout << "  PASS: " << what << "\n"; }
    else    { g_fail++; std::cout << "  FAIL: " << what << "\n"; }
}
static bool near_f(float a, float b, float eps = 1e-4f) { return std::fabs(a - b) < eps; }

// ── the shared synthetic table (see file comment for the layout) ──────────
static std::vector<uint8_t> build_law_table() {
    std::vector<std::string> strings = {
        "hello %1$s",     // 0
        "black",          // 1 (unused, pool filler proving STRING is pool-indexed)
    };
    std::vector<synthetic_arsc::TypeVariant> variants;

    // type 1 "string" → 0x7f01xxxx
    variants.push_back({1, "string", 0, {
        {"hello_message", false, 0, /*type*/ 0x03, 0, /*stridx*/ 0, {}},
    }});
    // type 2 "color" → 0x7f02xxxx
    variants.push_back({2, "color", 0, {
        {"alias",   false, 0, 0x01, 0x7f020001, -1, {}},   // REFERENCE → primary
        {"primary", false, 0, 0x1C, 0xFF000000, -1, {}},   // COLOR_ARGB8 black
        {"selfref", false, 0, 0x01, 0x7f020002, -1, {}},   // REFERENCE → itself
        {"r1",      false, 0, 0x01, 0x7f020004, -1, {}},   // mutual cycle
        {"r2",      false, 0, 0x01, 0x7f020003, -1, {}},
    }});
    // type 3 "style" → 0x7f03xxxx (bags with ResTable_map keys + parent)
    variants.push_back({3, "style", 0, {
        {"Parent", true, 0, 0, 0, -1,
            {{0x01010054, 0x01, 0x7f020001}}},             // windowBackground → @color/primary
        {"Child",  true, 0x7f030000, 0, 0, -1, {}},        // inherits via parent
        {"CycA",   true, 0x7f030003, 0, 0, -1, {}},
        {"CycB",   true, 0x7f030002, 0, 0, -1, {}},
    }});
    // type 4 "chain" → 0x7f04xxxx: 30-hop reference chain (depth law)
    {
        std::vector<synthetic_arsc::EntrySpec> chain;
        for (int i = 0; i < 30; i++) {
            char nm[16]; snprintf(nm, sizeof nm, "c%02d", i);
            uint32_t next = (i == 29) ? 0x7f020001 : (0x7f040000u + (uint32_t)i + 1);
            chain.push_back({nm, false, 0, 0x01, next, -1, {}});
        }
        variants.push_back({4, "chain", 0, chain});
    }
    // type 5 "fraction" → 0x7f05xxxx: 50% encoded (mantissa 64 @ radix 1 = 0.5)
    variants.push_back({5, "fraction", 0, {
        {"half", false, 0, 0x06, 0x00004010, -1, {}},
    }});
    return synthetic_arsc::build(strings, variants);
}

int main() {
    std::cout << "── resource core law regression (GOLDEN-03 §3/§4/§6/§7/§8/§9) ──\n";
    const DensityContext dev = DensityContext::from_density(2.625f);

    // ── §3 ResId canonical model ───────────────────────────────────────────
    {
        const uint32_t id = 0x7f020001u;
        ResId r = ResId::unpack(id);
        check(r.package == 0x7f && r.type == 0x02 && r.entry == 0x0001,
              "ResId::unpack 0x7f020001 → pkg=0x7f type=0x02 entry=0x0001");
        check(r.pack() == id, "ResId::pack roundtrip == original");
        check(ResId::unpack(0x00020001u).package == 0 && ResId::unpack(0x00020001u).valid() == false,
              "ResId: package 0 is invalid");
        check(ResId::unpack(0x7f000001u).valid() == false,
              "ResId: type 0 is invalid (1-based law)");
        check(r.to_string() == "0x7f020001", "ResId::to_string canonical form");
    }

    // ── §9 TypedValue laws ─────────────────────────────────────────────────
    {
        const uint32_t SP22 = (22u << 8) | 0x02;   // mantissa 22, radix 0, unit SP
        check(near_f(complex_to_float(SP22), 22.0f), "complexToFloat(22sp encoding) == 22.0");
        check(near_f(complex_unit_to_dimension_px(1, 1.0f, dev), 2.625f),
              "applyDimension DIP × density");
        check(near_f(complex_unit_to_dimension_px(2, 22.0f, dev), 57.75f),
              "applyDimension SP × scaledDensity (22sp → 57.75px)");
        check(near_f(complex_unit_to_dimension_px(3, 72.0f, dev), 420.0f),
              "applyDimension PT × xdpi/72 (72pt == 420px @420dpi)");
        check(near_f(complex_unit_to_dimension_px(4, 1.0f, dev), 420.0f),
              "applyDimension IN × xdpi");
        check(near_f(complex_unit_to_dimension_px(5, 25.4f, dev), 420.0f),
              "applyDimension MM × xdpi/25.4");
        check(complex_to_dimension_pixel_size(SP22, dev) == 58,
              "complexToDimensionPixelSize(22sp) == 58 (G46 rounding law)");
        // 0.3dp: mantissa 38 @ radix 1 (38 × 2^-15 = 0.296875), unit DIP — mantissa
        // lives at bits 8-31 per createComplex law (mantissa << COMPLEX_MANTISSA_SHIFT).
        const uint32_t DP03 = (38u << 8) | (1u << 4) | 0x01;
        check(complex_to_dimension_pixel_size(DP03, dev) == 1,
              "complexToDimensionPixelSize nonzero-floor tail (0.79px → 1, never silent 0)");
        // 50%: mantissa 64 @ radix 1 (64 × 2^-15 = 0.5), unit FRACTION.
        const uint32_t PCT50 = (64u << 8) | (1u << 4) | 0x00;
        check(near_f(complex_to_fraction(PCT50, 100.0f, 200.0f), 50.0f),
              "complexToFraction 50% of base");
        check(near_f(complex_to_fraction(PCT50 | 0x01u, 100.0f, 200.0f), 100.0f),
              "complexToFraction FRACTION_PARENT uses pbase");
    }

    // ── §7 color decode law ────────────────────────────────────────────────
    {
        check(color_data_to_argb(0x1C, 0x8000FF00u) == 0x8000FF00u,
              "color ARGB8 passthrough");
        check(color_data_to_argb(0x1D, 0x00332211u) == 0xFF332211u,
              "color RGB8 → opaque");
        check(color_data_to_argb(0x1E, 0xF00Fu) == 0xFF0000FFu,
              "color ARGB4 nibble expansion");
        check(color_data_to_argb(0x1F, 0x0F00u) == 0xFFFF0000u,
              "color RGB4 nibble expansion");
        check(!color_data_to_argb(0x03, 0).has_value(),
              "color law rejects non-color dataType");
    }

    // ── §4/§6 resolve_full + named failures ────────────────────────────────
    std::vector<uint8_t> blob = build_law_table();
    ArscParser arsc;
    check(arsc.parse(blob), "synthetic law table parses");
    if (!arsc.valid()) { std::cout << "RESULT: " << g_pass << " passed, " << g_fail << " failed\n"; return 1; }
    const ResTableConfig& device = device_config();

    {
        ResolutionResult r = arsc.resolve_full(0x7f020000, device);
        check(r.ok, "resolve_full(@color/alias) ok");
        check(r.chain.size() == 2 && r.reference_hops() == 1,
              "chain records the reference hop (alias → primary)");
        check(r.chain[0].raw_value.is_reference() && r.chain[0].raw_value.ref_id == 0x7f020001,
              "step[0] raw value is the pre-resolution REFERENCE (raw/resolved distinction)");
        check(r.chain[1].entry_name == "primary" &&
              r.chain[1].raw_value.type == DataType::COLOR_ARGB8 &&
              r.chain[1].raw_value.data == 0xFF000000u,
              "terminal step resolves to COLOR_ARGB8 #FF000000");
        check(r.chain[0].type_name == "color" && r.chain[1].type_name == "color",
              "type name reported on every step");
        check(!r.chain[0].selected_config_desc.empty() || r.chain[0].selected_config.size == 28,
              "selected configuration reported per step (parsed ResTableConfig present)");
        check(r.requested_id == 0x7f020000 && r.decomposed.type == 0x02,
              "result carries requested id + canonical decomposition");
        auto v = arsc.resolve_value(0x7f020000);
        check(v && v->data == 0xFF000000u, "resolve_value is the canonical chain projection");
        auto s = arsc.resolve_string(0x7f010000);
        check(s && *s == "hello %1$s", "resolve_string returns pool string");
    }
    {
        ResolutionResult r = arsc.resolve_full(0x7f020099, device);
        check(!r.ok && r.error == ResolutionError::MISSING_ENTRY,
              "missing id → named MISSING_ENTRY (deterministic)");
        check(arsc.resolve_full(0x00020000, device).error == ResolutionError::INVALID_ID,
              "package-0 id → INVALID_ID");
        check(arsc.resolve_full(0x7f000001, device).error == ResolutionError::INVALID_ID,
              "type-0 id → INVALID_ID");
        check(arsc.resolve_full(0x7f020003, device).error == ResolutionError::CYCLE,
              "mutual reference cycle → named CYCLE");
        check(arsc.resolve_full(0x7f020002, device).error == ResolutionError::CYCLE,
              "self reference cycle → named CYCLE");
        check(arsc.resolve_full(0x7f040000, device).error == ResolutionError::DEPTH_EXCEEDED,
              "30-hop chain → bounded DEPTH_EXCEEDED (no hang, no unbounded recursion)");
        // determinism: identical input → identical named error
        check(arsc.resolve_full(0x7f040000, device).error ==
              arsc.resolve_full(0x7f040000, device).error,
              "named failure is deterministic across calls");
    }
    {
        ResolutionResult r = arsc.resolve_full(0x7f050000, device);
        check(r.ok && r.terminal() && r.terminal()->raw_value.is_fraction() &&
              near_f(r.terminal()->raw_value.dim_value, 0.5f) &&
              r.terminal()->raw_value.dim_unit == COMPLEX_UNIT_FRACTION,
              "FRACTION decoded: 0x80 → 0.5 multiplier, unit % (§7)");
    }

    // ── §8 bag attribute query + parent inheritance ────────────────────────
    {
        auto direct = arsc.bag_value(0x7f030000, 0x01010054, device);
        check(direct && direct->is_reference() && direct->ref_id == 0x7f020001,
              "bag_value: windowBackground key found in own bag");
        auto inherited = arsc.bag_value(0x7f030001, 0x01010054, device);
        check(inherited && inherited->is_reference() && inherited->ref_id == 0x7f020001,
              "bag_value: key resolved through ResTable_map_entry parent (style inheritance)");
        check(!arsc.bag_value(0x7f030002, 0x01010054, device).has_value(),
              "bag_value: parent cycle fails safely (nullopt, no hang)");
        check(!arsc.bag_value(0x7f030000, 0x01010101, device).has_value(),
              "bag_value: absent key with no parent → deterministic nullopt");
    }

    std::cout << "RESULT: " << g_pass << " passed, " << g_fail << " failed\n";
    return g_fail == 0 ? 0 : 1;
}
