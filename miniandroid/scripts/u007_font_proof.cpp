// UNIFIED_007 — Runtime-integrated font pipeline proof.
// Renders the master-request sample strings through THE SAME TextShaper
// module the runtime uses for every TextView, then writes PNG + metrics.
//
// Strings (exact per charter):
//   «سلام دنیا»   Persian (RTL)
//   «Hello دنیا»  mixed LTR+RTL bidi
//   «۱۲۳۴۵»       Extended Arabic-Indic digits
// plus Latin control: Hello World
//
// Build: see scripts/build_u007_font_proof.sh
#include "../src/fonts/text_shaper.h"
#include "../src/renderer/software_renderer.h"

#include <cstdio>
#include <string>
#include <vector>
#include <fstream>
#include <sstream>

using namespace miniandroid;

int main(int argc, char** argv) {
    const char* out_prefix = argc > 1 ? argv[1] : "run/u007_font_proof/proof";

    auto& shaper = fonts::TextShaper::instance();
    if (!shaper.available()) {
        std::fprintf(stderr, "TextShaper unavailable\n");
        return 1;
    }

    struct Sample { const char* name; const char* text; };
    std::vector<Sample> samples = {
        {"fa_salaam_donya", "سلام دنیا"},
        {"mixed_hello_donya", "Hello دنیا"},
        {"fa_digits_12345", "۱۲۳۴۵"},
        {"latin_hello_world", "Hello World"},
    };

    renderer::FrameBuffer fb(1080, 90 * (int)samples.size() + 40);
    fb.clear(renderer::Colors::WHITE);

    std::ostringstream mj;
    mj << "{\n  \"pipeline\": \"FriBidi->HarfBuzz->FreeType via runtime TextShaper\",\n";
    mj << "  \"font\": \"" << shaper.primary_font_path() << "\",\n  \"samples\": [\n";

    float pen_y = 60;
    bool all_ok = true;
    for (size_t si = 0; si < samples.size(); ++si) {
        const auto& s = samples[si];
        const auto& st = shaper.shape(s.text, 48.0f);
        float baseline = pen_y;
        float x = 40;
        if (st.rtl_base) x = 1040 - st.width;  // RTL right-align
        shaper.draw(fb, s.text, x, baseline, 48.0f,
                    renderer::RGBA{0x10, 0x10, 0x10, 0xFF});
        long nonwhite = 0;
        for (int y = (int)pen_y - 55; y < (int)pen_y + 15; ++y) {
            for (int xx = 0; xx < fb.get_width(); ++xx) {
                auto p = fb.get_pixel(xx, y);
                if (p.r < 250 || p.g < 250 || p.b < 250) nonwhite++;
            }
        }
        bool ok = st.glyphs.size() > 0 && nonwhite > 0;
        all_ok = all_ok && ok;
        mj << "  {\"sample\": \"" << s.name << "\", \"text_utf8\": \"" << s.text
           << "\", \"glyph_count\": " << st.glyphs.size()
           << ", \"notdef_count\": " << st.notdef_count
           << ", \"width_px\": " << (int)st.width
           << ", \"rtl_base\": " << (st.rtl_base ? "true" : "false")
           << ", \"strip_nonwhite_px\": " << nonwhite
           << ", \"shaped_ok\": " << (ok ? "true" : "false") << "}"
           << (si + 1 < samples.size() ? "," : "") << "\n";
        pen_y += 90;
    }
    mj << "],\n  \"all_ok\": " << (all_ok ? "true" : "false") << "\n}\n";

    std::string png_path = std::string(out_prefix) + ".png";
    if (!renderer::PNGWriter::write_png(png_path, fb)) {
        std::fprintf(stderr, "PNG write failed\n");
        return 1;
    }
    std::ofstream mjf(std::string(out_prefix) + "_metrics.json");
    mjf << mj.str();
    std::printf("proof written: %s\n", png_path.c_str());
    return all_ok ? 0 : 2;
}
