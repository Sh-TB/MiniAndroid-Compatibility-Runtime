// m3_arsc_style_law_test.cpp — MASTER CAMPAIGN 3 §13 resource-law battery.
//
// Laws under test (against a REAL aapt2-built fixture ARSC — no synthetic
// bytes, no fixture-specific parser branches):
//   [1..3] FIX-M3-003 (ResTable_map stride law): every key of a multi-key
//          style bag decodes EXACTLY; the 20-byte stride bug corrupted all
//          but coincidentally-aligned keys.
//   [4..5] FIX-M3-003b (bag_parent law): the style parent reference survives
//          the complex_items[0] value overwrite; bag_value walks it.
//   [6..8] FIX-M3-002 semantics at the ARSC layer: the parent chain delivers
//          layout_width=0dp / layout_weight=1 to a CHILD style that does not
//          carry them itself (style inheritance), and the child's OWN key
//          beats the parent's.
//   [9]    hostile: unknown style id → nullopt (no crash, no garbage).
//
// Usage: m3_arsc_style_law_test <resources.arsc path>
#include "../src/resources/arsc_parser.h"

#include <cstdio>
#include <cstdint>
#include <string>
#include <fstream>
#include <vector>

using miniandroid::resources::ArscParser;
using miniandroid::resources::ResTableConfig;
using miniandroid::resources::ResValue;

static int g_fail = 0, g_n = 0;
static void check(bool ok, const std::string& what) {
    g_n++;
    if (!ok) { g_fail++; printf("  FAIL: %s\n", what.c_str()); }
    else      printf("  PASS: %s\n", what.c_str());
}

static constexpr uint32_t ATTR_TEXT_SIZE    = 0x01010095;
static constexpr uint32_t ATTR_TEXT_COLOR   = 0x01010098;
static constexpr uint32_t ATTR_LAYOUT_WIDTH  = 0x010100f4;
static constexpr uint32_t ATTR_LAYOUT_HEIGHT = 0x010100f5;
static constexpr uint32_t ATTR_LAYOUT_MARGIN = 0x010100f6;
static constexpr uint32_t ATTR_LAYOUT_WEIGHT = 0x01010181;

int main(int argc, char** argv) {
    if (argc < 2) { printf("usage: %s <resources.arsc>\n", argv[0]); return 2; }
    std::ifstream f(argv[1], std::ios::binary);
    std::vector<uint8_t> data((std::istreambuf_iterator<char>(f)),
                              std::istreambuf_iterator<char>());
    check(data.size() > 8, "fixture arsc bytes read");

    ArscParser arsc;
    check(arsc.parse(data), "arsc parses: " + arsc.last_error());
    if (!arsc.valid()) return 1;

    auto digit = arsc.find_id("", "style", "M3KeypadDigit");
    auto parent = arsc.find_id("", "style", "M3KeypadButton");
    check(digit.has_value(), "style/M3KeypadDigit resolves");
    check(parent.has_value(), "style/M3KeypadButton resolves");
    if (!digit || !parent) return 1;

    ResTableConfig dev;
    const auto dctx =
        miniandroid::resources::DensityContext::from_density(2.625f);

    // [1..3] stride law: the PARENT bag carries 5 keys (textSize is NOT in
    // it — it lives in the child). All five must decode with exact ids.
    {
        auto r = arsc.resolve(*parent);
        check(r.has_value(), "parent style resolves to entry");
        const auto* e = r->best();
        check(e && e->is_complex, "parent style is a complex bag");
        check(e->complex_keys.size() == 5,
              "parent bag has exactly 5 keys (got " +
              std::to_string(e->complex_keys.size()) + ")");
        bool keys_exact = e->complex_keys.size() == 5 &&
            e->complex_keys[0] == ATTR_TEXT_COLOR &&
            e->complex_keys[1] == ATTR_LAYOUT_WIDTH &&
            e->complex_keys[2] == ATTR_LAYOUT_HEIGHT &&
            e->complex_keys[3] == ATTR_LAYOUT_MARGIN &&
            e->complex_keys[4] == ATTR_LAYOUT_WEIGHT;
        check(keys_exact, "every parent-bag key decodes exactly (stride law)");
    }

    // [4..5] bag_parent law.
    {
        auto r = arsc.resolve(*digit);
        const auto* e = r->best();
        check(e->bag_parent == *parent,
              "child style bag_parent == parent style id");
        // bag_value walks the chain: textSize lives in the CHILD bag.
        auto ts = arsc.bag_value(*digit, ATTR_TEXT_SIZE, dev);
        check(ts.has_value(), "bag_value finds child-own textSize");
    }

    // [6..8] style inheritance through the parent chain.
    {
        auto w = arsc.bag_value(*digit, ATTR_LAYOUT_WIDTH, dev);
        check(w.has_value(),
              "layout_width inherited from parent bag (chain walk)");
        check(w && w->is_dimension() &&
              miniandroid::resources::complex_to_dimension_pixel_size(
                  w->data, dctx) == 0,
              "inherited layout_width == 0dp");
        auto h = arsc.bag_value(*digit, ATTR_LAYOUT_HEIGHT, dev);
        check(h && h->is_int() && (int)h->data == -1,
              "inherited layout_height == match_parent (-1)");
        auto wt = arsc.bag_value(*digit, ATTR_LAYOUT_WEIGHT, dev);
        check(wt.has_value(), "layout_weight inherited from parent bag");
        if (wt) {
            float f = 0;
            if (wt->type == miniandroid::resources::DataType::FLOAT)
                memcpy(&f, &wt->data, 4);
            else f = (float)wt->data;
            check(f == 1.0f, "inherited layout_weight == 1.0");
        }
        // Child's OWN key beats the parent's: textColor lives only in the
        // parent; textSize only in the child. Direct-override precedence is
        // exercised at the inflate layer (battery U007 check).
        auto tc = arsc.bag_value(*digit, ATTR_TEXT_COLOR, dev);
        check(tc.has_value(), "textColor inherited through chain");
    }

    // [9] hostile: unknown style id.
    {
        auto v = arsc.bag_value(0x7fff0001u, ATTR_LAYOUT_WIDTH, dev);
        check(!v.has_value(), "unknown style id -> nullopt (no crash)");
    }

    printf("m3_arsc_style_law: %d/%d PASS\n", g_n - g_fail, g_n);
    return g_fail == 0 ? 0 : 1;
}
