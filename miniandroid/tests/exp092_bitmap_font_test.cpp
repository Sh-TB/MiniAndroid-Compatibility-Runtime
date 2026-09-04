// EXP-092: BitmapFont regression test.
//
// Verifies that the auto-generated bitmap font (from gen_bitmap_font.py)
// can render every ASCII printable char (32..126), the friend's
// micro-regression strings (HELLO, 0123456789, +/-.:-), and the actual
// runtime-resolved SMS strings.
//
// Build & run:
//   g++ -std=c++17 -Isrc -Isrc/renderer -Ithird_party/nlohmann_json/include \
//       tests/exp092_bitmap_font_test.cpp \
//       src/renderer/software_renderer.cpp \
//       -lz -o build/exp092_font_test
//   ./build/exp092_font_test

#include "../src/renderer/software_renderer.h"
#include <cassert>
#include <cstdio>
#include <set>
#include <string>
#include <vector>

using miniandroid::renderer::BitmapFont;
using miniandroid::renderer::FrameBuffer;
using miniandroid::renderer::SoftwareCanvas;
using miniandroid::renderer::RGBA;
namespace Colors = miniandroid::renderer::Colors;

static int total_tests = 0;
static int passed_tests = 0;

void check(bool cond, const std::string& desc) {
    total_tests++;
    if (cond) {
        passed_tests++;
        printf("  [PASS] %s\n", desc.c_str());
    } else {
        printf("  [FAIL] %s\n", desc.c_str());
    }
}

// Render text to a framebuffer and count the dark pixels rendered.
// Returns the count of dark (text) pixels.
static int render_text_and_count_dark_pixels(const std::string& text) {
    FrameBuffer fb(80, 24);  // small canvas
    fb.clear(Colors::WHITE);
    SoftwareCanvas canvas(&fb);
    BitmapFont font;

    // Background: white
    // Text: dark grey
    canvas.draw_text(text, 0, font.get_line_height(), Colors::GREY_800, &font);

    // Count non-white pixels in the framebuffer
    const auto& pixels = fb.get_pixels();
    int dark_count = 0;
    for (const auto& p : pixels) {
        if (p.r < 200 || p.g < 200 || p.b < 200) dark_count++;
    }
    return dark_count;
}

int main() {
    printf("=== EXP-092 BitmapFont regression test ===\n\n");

    BitmapFont font;

    // --- Test 1: All 95 printable ASCII chars have a non-space bitmap.
    printf("[1] Verify all 95 printable ASCII chars have a real glyph\n");
    int empty_glyphs = 0;
    int total_glyphs = 0;
    std::vector<char> missing_glyphs;
    for (int c = 32; c <= 126; c++) {
        total_glyphs++;
        const auto* g = font.get_glyph(static_cast<char>(c));
        if (!g) {
            missing_glyphs.push_back(static_cast<char>(c));
            continue;
        }
        // Count dark bits in the bitmap — for space this is 0, for everything
        // else there must be at least 1 dark pixel.
        bool has_dark = false;
        if (c != ' ') {  // space is expected to be all-zero
            for (int i = 0; i < g->height; i++) {
                if (g->bitmap[i] != 0) { has_dark = true; break; }
            }
        }
        if (!has_dark && c != ' ') {
            empty_glyphs++;
            missing_glyphs.push_back(static_cast<char>(c));
        }
    }
    printf("  total glyphs: %d\n", total_glyphs);
    printf("  empty glyphs: %d\n", empty_glyphs);
    check(empty_glyphs == 0,
          "All non-space chars have at least 1 dark pixel in their bitmap");

    // --- Test 2: Specific glyph indices are correctly placed.
    printf("\n[2] Verify specific glyph indices\n");
    {
        // ASCII 32 → space
        const auto* sp = font.get_glyph(' ');
        check(sp && sp->character == ' ', "get_glyph(' ').character == ' '");

        // ASCII 65 → 'A'
        const auto* A = font.get_glyph('A');
        check(A && A->character == 'A', "get_glyph('A').character == 'A'");

        // ASCII 72 → 'H' (this was the buggy one in the old font)
        const auto* H = font.get_glyph('H');
        check(H && H->character == 'H', "get_glyph('H').character == 'H'");

        // ASCII 97 → 'a' (lowercase)
        const auto* a = font.get_glyph('a');
        check(a && a->character == 'a', "get_glyph('a').character == 'a'");

        // ASCII 48 → '0' (digit)
        const auto* zero = font.get_glyph('0');
        check(zero && zero->character == '0', "get_glyph('0').character == '0'");

        // ASCII 43 → '+' (the multi-DEX string bug case)
        const auto* plus = font.get_glyph('+');
        check(plus && plus->character == '+', "get_glyph('+').character == '+'");

        // ASCII 46 → '.' (the dot)
        const auto* dot = font.get_glyph('.');
        check(dot && dot->character == '.', "get_glyph('.').character == '.'");

        // ASCII 58 → ':' (colon)
        const auto* colon = font.get_glyph(':');
        check(colon && colon->character == ':', "get_glyph(':').character == ':'");

        // ASCII 45 → '-' (minus/hyphen)
        const auto* minus = font.get_glyph('-');
        check(minus && minus->character == '-', "get_glyph('-').character == '-'");

        // ASCII 47 → '/' (slash)
        const auto* slash = font.get_glyph('/');
        check(slash && slash->character == '/', "get_glyph('/').character == '/'");
    }

    // --- Test 3: Friend's micro-regression strings render visibly.
    printf("\n[3] Friend's micro-regression: HELLO, 0123456789, +/-.:-\n");
    struct TestCase { std::string name; std::string text; int min_dark; };
    std::vector<TestCase> cases = {
        {"HELLO",            "HELLO",        20},
        {"0123456789",       "0123456789",   30},
        {"+/-.:-",           "+/-.:-",       10},
        {"Hello MiniAndroid","Hello MiniAndroid", 40},
    };
    for (const auto& tc : cases) {
        int dark = render_text_and_count_dark_pixels(tc.text);
        printf("  render(\"%s\") = %d dark pixels (min required: %d)\n",
               tc.text.c_str(), dark, tc.min_dark);
        check(dark >= tc.min_dark,
              "render(\"" + tc.text + "\") renders enough dark pixels");
    }

    // --- Test 4: Runtime-resolved SMS strings render visibly.
    // These are the actual strings returned by LocaleController.getString()
    // after the EXP-092 resource_values.json loading fix.
    printf("\n[4] Runtime SMS strings (post-EXP-092 fix)\n");
    std::vector<TestCase> sms_cases = {
        {"Enter code",                  "Enter code",                  30},
        {"Phone verification",          "Phone verification",          60},
        {"Check your Telegram messages","Check your Telegram messages",100},
        {"Resend code",                 "Resend code",                 30},
        {"Enter phrase from SMS",       "Enter phrase from SMS",       80},
        {"Enter word from SMS",         "Enter word from SMS",         60},
        {"Phone number",               "Phone number",                40},
        {"Please confirm your country code and enter your phone number.",
         "Please confirm your country code and enter your phone number.", 100},
    };
    for (const auto& tc : sms_cases) {
        int dark = render_text_and_count_dark_pixels(tc.text);
        printf("  render(\"%s\") = %d dark pixels (min: %d)\n",
               tc.text.c_str(), dark, tc.min_dark);
        check(dark >= tc.min_dark,
              "SMS string renders: \"" + tc.text + "\"");
    }

    // --- Test 5: Empty string produces 0 dark pixels.
    printf("\n[5] Edge cases\n");
    check(render_text_and_count_dark_pixels("") == 0,
          "Empty string produces 0 dark pixels");
    // All-spaces produces 0 dark pixels
    check(render_text_and_count_dark_pixels("    ") == 0,
          "All-spaces string produces 0 dark pixels");

    // --- Test 6: measure_text returns reasonable widths.
    printf("\n[6] measure_text returns reasonable widths\n");
    {
        auto m1 = font.measure_text("HELLO");
        check(m1.width > 0 && m1.width <= 80, "measure_text(\"HELLO\") width > 0");
        auto m2 = font.measure_text("0123456789");
        check(m2.width > m1.width, "10-char string is wider than 5-char string");
        auto m3 = font.measure_text("");
        check(m3.width == 0, "measure_text(\"\") width == 0");
    }

    printf("\n=== SUMMARY ===\n");
    printf("Passed: %d / %d\n", passed_tests, total_tests);
    return (passed_tests == total_tests) ? 0 : 1;
}
