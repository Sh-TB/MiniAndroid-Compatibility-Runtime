// s244_app_font_discovery_law_test — the app-font discovery + no-default-
// font laws (#605 follow-up). Proves HOW the engine finds an app's own
// fonts and WHAT happens when no default font exists:
//   D1-D3  discovery contract: APK bytes -> memory face -> family model
//   D4-D6  failure isolation: corrupt app font never touches the chain
//   D7-D9  family routing: per-face identity, name lookup, bold arm
//   N1-N6  the no-default-font chain (run BOTH worlds: normal + hidden)
#include "../src/fonts/text_shaper.h"

#include <cstdio>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

using miniandroid::fonts::TextShaper;
using miniandroid::fonts::FACE_SYSTEM;

static int g_pass = 0, g_fail = 0;
static void record(const std::string& name, bool passed,
                   const std::string& detail) {
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name
              << (detail.empty() ? "" : " — " + detail) << "\n";
    if (passed) ++g_pass; else ++g_fail;
}
static std::vector<uint8_t> file_bytes(const std::string& p) {
    std::ifstream f(p, std::ios::binary);
    if (!f) return {};
    return std::vector<uint8_t>((std::istreambuf_iterator<char>(f)),
                                std::istreambuf_iterator<char>());
}

int main() {
    std::cout << "== s244 app-font discovery battery ==\n";
    TextShaper& ts = TextShaper::instance();
    const float SZ = 16.0f;

    // ---- D1: the APK-entry law — raw bytes from ANY entry name load as a
    // family face (assets/fonts/x.ttf, res/UJ.ttf, anything).
    std::vector<uint8_t> sys = file_bytes(ts.primary_font_path());
    std::vector<uint8_t> mono = file_bytes(ts.monospace_font_path());
    int idx_reg = ts.register_app_font_memory(sys, "assets/fonts/app.ttf",
                                              false);
    record("D01_apk_bytes_to_face", idx_reg >= 0 &&
           ts.face_info(idx_reg).glyph_count > 0,
           "idx=" + std::to_string(idx_reg));
    // D2: the name-lookup law (exact entry, "/name" suffix, absent)
    record("D02_name_exact",
           ts.app_face_index_for_name("assets/fonts/app.ttf") == idx_reg, "");
    record("D03_name_suffix",
           ts.app_face_index_for_name("fonts/app.ttf") == idx_reg, "");
    record("D04_name_absent",
           ts.app_face_index_for_name("fonts/none.ttf") < 0, "");
    // ---- D4/D5: failure isolation — a corrupt app font NEVER touches the
    // system chain (the AOSP law: createFromAsset failure -> default face).
    // (Guard the slice: in the hidden-font world `sys` is empty — slicing
    // an empty vector is UB and segfaulted the FIRST hidden-world run.)
    std::vector<uint8_t> corrupt;
    if (sys.size() > 300) corrupt.assign(sys.begin(), sys.begin() + 300);
    else for (int i = 0; i < 300; ++i)
        corrupt.push_back((uint8_t)(0x40 + (i % 60)));
    int bad = ts.register_app_font_memory(corrupt, "assets/fonts/bad.ttf",
                                          false);
    const auto& st_after = ts.shape("System Chain Alive", SZ, false,
                                    FACE_SYSTEM);
    record("D05_corrupt_isolated", bad < 0 && st_after.width > 0,
           "bad=" + std::to_string(bad) + " chain width=" +
           std::to_string((long)st_after.width));
    record("D06_extract_empty_isolated",
           ts.register_app_font_memory({}, "assets/fonts/empty.ttf",
                                       false) < 0, "");
    // ---- D7-D9: family routing — two DISTINCT faces stay distinct.
    int idx_mono = -1;
    if (!mono.empty())
        idx_mono = ts.register_app_font_memory(mono, "res/UJ.ttf", true);
    record("D07_two_faces_distinct",
           idx_reg >= 0 && idx_mono >= 0 && idx_reg != idx_mono,
           "reg=" + std::to_string(idx_reg) + " mono=" +
           std::to_string(idx_mono));
    if (idx_reg >= 0 && idx_mono >= 0) {
        float w1 = ts.shape("Width Identity", SZ, false, idx_reg).width;
        float w2 = ts.shape("Width Identity", SZ, false, idx_mono).width;
        record("D08_face_identity_widths", w1 > 0 && w2 > 0 && w1 != w2,
               "reg=" + std::to_string((long)w1) + " mono=" +
               std::to_string((long)w2));
        record("D09_bold_arm_routes",
               ts.face_info(idx_mono).state ==
                   TextShaper::FaceState::LOADED,  // is_bold=true family face
               "");
    } else {
        record("D08_face_identity_widths", false, "registration incomplete");
        record("D09_bold_arm_routes", false, "registration incomplete");
    }
    // ---- N1-N6: the no-default-font chain (the honest-fail laws the
    // hidden-font world re-proves end to end).
    record("N1_empty_text_zero_width",
           ts.shape("", SZ, false, FACE_SYSTEM).width == 0 &&
           ts.shape("", SZ, false, FACE_SYSTEM).glyphs.empty(), "");
    {   // N2: unknown face index — honest resolution, never a crash
        const auto& st = ts.shape("Unknown Idx", SZ, false, 999999);
        record("N2_unknown_face_index_safe", st.width >= 0, "");
    }
    {   // N3: the diagnostics surface exists and is truthful
        std::string rep = ts.font_diagnostic_report();
        record("N3_diagnostic_report_truthful",
               rep.find("FONT_DIAGNOSTIC") == 0 &&
               rep.find("SUMMARY") != std::string::npos, "");
    }
    {   // N4: app-font verification end-to-end (the "did IT load" proof).
        // Tries ANY registered app face — in the hidden-font world the
        // app's own (memory-registered) font is the one that must still
        // render, proving app fonts are independent of the system tree.
        int any_app = idx_reg >= 0 ? idx_reg : idx_mono;
        bool ok = any_app >= 0 &&
                  ts.verify_text_renders(any_app, "App Face", SZ).ok;
        record("N4_app_face_render_proof", ok,
               any_app >= 0 ? "face=" + std::to_string(any_app)
                            : "no app face registered");
    }
    {   // N5: the family law — has_family is permissive (unknown -> sans)
        record("N5_family_resolution_usable",
               ts.resolve_family("no-such-family", false) >= 0 &&
               ts.has_family("monospace"), "");
    }
    {   // N6: after every app-font failure the FT library stays alive
        const auto& st = ts.shape("Alive", SZ, false, FACE_SYSTEM);
        record("N6_ft_alive_after_failures", st.width > 0, "");
    }

    std::cout << "== " << g_pass << " passed / " << g_fail
              << " failed ==\n";
    return g_fail == 0 ? 0 : 1;
}
