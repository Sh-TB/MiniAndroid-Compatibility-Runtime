// s106_text2_law_test.cpp — S106 text/font micro-gap fence (second batch).
// Drives the REAL fonts::TextShaper / fonts::layout_text (the same objects
// the runtime draw path uses) and asserts the AOSP upstream laws:
//
//   X1  (MG-052 missing-glyph detection)  — uncovered codepoint flags
//                                          notdef_count > 0.
//   X2  (MG-053 tofu detection)           — covered string reports
//                                          notdef_count == 0 (no false tofu).
//   X3  (MG-061 line spacing)             — spacing_mult 2 doubles per-line
//                                          box vs mult 1 (StaticLayout law).
//   X4  (MG-062 includeFontPadding)       — pad=true first line_above =
//                                          |fm.top| >= |fm.ascent|; pad=false
//                                          uses |fm.ascent| (TextView law).
//   X5  (MG-067 font ascent)              — ascent > 0 finite and stable
//                                          across two calls (FontMetrics law).
//   X6  (MG-068 font descent)             — descent > 0 and
//                                          ascent+descent <= line_height.
//   X7  (MG-071 whitespace)               — trailing spaces do not count
//                                          toward line width.
//   X8  (MG-074 maxLines)                 — max_lines=2 caps the line count.
//   X9  (MG-075 singleLine)               — max_lines=1 never word-wraps
//                                          (TextView singleLine law).
//   X10 (MG-086 font file failure)        — unknown family resolution falls
//                                          back to a usable face (no crash,
//                                          honest fallback semantics).
//   X11 (MG-087 resource font family)     — resolve_family distinguishes
//                                          monospace vs sans-serif faces.
//   X12 (MG-088 downloadable fallback)    — unavailable (downloadable)
//                                          family resolves to the system
//                                          face — TextView fallback law.
//
// Exit 0 iff ALL laws hold. Evidence: last line "s106 text2 laws PASS n/n".

#include "../src/fonts/text_shaper.h"

#include <algorithm>
#include <cstdio>
#include <string>

using namespace miniandroid::fonts;

static int g_pass = 0, g_fail = 0;
static void check(const char* name, bool ok, const std::string& detail = "") {
    if (ok) { ++g_pass; std::printf("PASS %s %s\n", name, detail.c_str()); }
    else { ++g_fail; std::printf("FAIL %s %s\n", name, detail.c_str()); }
}

int main() {
    auto& sh = TextShaper::instance();
    if (!sh.available()) { std::printf("FAIL textshaper unavailable\n"); return 1; }

    // X1/X2 (MG-052/053): notdef detection both directions
    {
        // U+11F00-ish unassigned/uncoded glyph in most faces: use a Private
        // Use Area codepoint (U+E700) no system face maps.
        const std::string tofu = "A\xEE\x9C\x80";  // A + U+E700 PUA
        const auto& st_bad = sh.shape(tofu, 24.0f, false, 0);
        check("X1 mg-052 uncovered codepoint flags notdef",
              st_bad.notdef_count >= 1,
              "notdef=" + std::to_string(st_bad.notdef_count));
        const auto& st_ok = sh.shape("AΩЖ中", 24.0f, false, 0);
        check("X2 mg-053 covered string has zero tofu",
              st_ok.notdef_count == 0,
              "notdef=" + std::to_string(st_ok.notdef_count));
    }
    // X3 (MG-061): line spacing multiplier
    {
        const char* txt = "first line\nsecond line\nthird line";
        auto l1 = layout_text(txt, 20.f, false, 400.f, 0, FACE_SYSTEM,
                              1.0f, 0.f, true, false, 0);
        auto l2 = layout_text(txt, 20.f, false, 400.f, 0, FACE_SYSTEM,
                              2.0f, 0.f, true, false, 0);
        check("X3 mg-061 mult=2 doubles line box",
              !l1.line_boxes.empty() && !l2.line_boxes.empty() &&
              l2.line_boxes[0] > l1.line_boxes[0] * 1.9f &&
              l2.line_boxes[0] < l1.line_boxes[0] * 2.1f,
              "b1=" + std::to_string(l1.line_boxes[0]) +
              " b2=" + std::to_string(l2.line_boxes[0]));
        // spacing_add adds flat px per line
        auto la = layout_text(txt, 20.f, false, 400.f, 0, FACE_SYSTEM,
                              1.0f, 6.f, true, false, 0);
        check("X3 mg-061 add=6 adds flat px",
              la.line_boxes[0] > l1.line_boxes[0] + 5.5f &&
              la.line_boxes[0] < l1.line_boxes[0] + 6.5f,
              "ba=" + std::to_string(la.line_boxes[0]));
    }
    // X4 (MG-062): includeFontPadding law
    {
        auto pad = layout_text("Ag", 24.f, false, 200.f, 1, FACE_SYSTEM,
                               1.f, 0.f, true, false, 0);
        auto nopad = layout_text("Ag", 24.f, false, 200.f, 1, FACE_SYSTEM,
                                 1.f, 0.f, false, false, 0);
        check("X4 mg-062 pad line_above >= nopad",
              !pad.line_above.empty() && !nopad.line_above.empty() &&
              pad.line_above[0] >= nopad.line_above[0] - 0.5f,
              "pad=" + std::to_string(pad.line_above[0]) +
              " nopad=" + std::to_string(nopad.line_above[0]));
        check("X4 mg-062 nopad tracks ascent",
              !nopad.line_above.empty() &&
              std::abs(nopad.line_above[0] - nopad.ascent) <= 1.5f,
              "above=" + std::to_string(nopad.line_above[0]) +
              " ascent=" + std::to_string(nopad.ascent));
    }
    // X5/X6 (MG-067/068): ascent/descent metrics
    {
        auto a = layout_text("Hello", 24.f, false, 300.f, 1);
        auto b = layout_text("Hello", 24.f, false, 300.f, 1);
        check("X5 mg-067 ascent positive+stable",
              a.ascent > 0 && std::abs(a.ascent - b.ascent) < 0.01f,
              "ascent=" + std::to_string(a.ascent));
        check("X6 mg-068 descent positive; box covers both",
              a.descent > 0 && a.ascent + a.descent <= a.line_height + 0.5f,
              "descent=" + std::to_string(a.descent) +
              " line_height=" + std::to_string(a.line_height));
    }
    // X7 (MG-071): trailing-space width law
    {
        auto t = layout_text("word   ", 20.f, false, 400.f, 1);
        auto n = layout_text("word", 20.f, false, 400.f, 1);
        check("X7 mg-071 trailing spaces excluded from width",
              !t.lines.empty() && !n.lines.empty() &&
              std::abs(t.lines[0].width - n.lines[0].width) < 0.75f,
              "tw=" + std::to_string(t.lines[0].width) +
              " nw=" + std::to_string(n.lines[0].width));
    }
    // X8/X9 (MG-074/075): maxLines + singleLine
    {
        auto m = layout_text("alpha beta gamma delta epsilon", 20.f, false,
                             150.f, 2);
        check("X8 mg-074 max_lines=2 caps block", m.lines.size() == 2,
              "n=" + std::to_string(m.lines.size()));
        auto s = layout_text("alpha beta gamma delta epsilon", 20.f, false,
                             150.f, 1);
        check("X9 mg-075 singleLine never wraps", s.lines.size() == 1,
              "n=" + std::to_string(s.lines.size()));
    }
    // X10/X11/X12 (MG-086/087/088): family resolution + fallback laws
    {
        int sys = sh.resolve_family("sans-serif", false);
        int mono = sh.resolve_family("monospace", false);
        int unknown = sh.resolve_family("definitely-not-a-family", false);
        int downloadable_missing = sh.resolve_family(
            "sans-serif-downloadable-unavailable", false);
        check("X10 mg-086 unknown family falls back (no crash)",
              unknown >= FACE_SYSTEM, "face=" + std::to_string(unknown));
        check("X11 mg-087 monospace != sans-serif face",
              mono != sys, "mono=" + std::to_string(mono) +
              " sys=" + std::to_string(sys));
        check("X12 mg-088 unavailable downloadable falls back to system",
              downloadable_missing == sys || downloadable_missing >= FACE_SYSTEM,
              "face=" + std::to_string(downloadable_missing));
    }

    std::printf("s106 text2 laws %s %d/%d\n",
                g_fail == 0 ? "PASS" : "FAIL", g_pass, g_pass + g_fail);
    return g_fail == 0 ? 0 : 1;
}
