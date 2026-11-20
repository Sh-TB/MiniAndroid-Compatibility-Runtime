// s18_text_layout_laws_test — S18 family C (#632-N2/N3/N4 + NEW-23 partial):
// the SINGLE SOURCE OF TRUTH text geometry law — fonts::TextShaper::layout_text
// (real shaped advances; both the measure pass and the draw path call it, so
// geometry and pixels cannot disagree). Expectations are the AOSP
// TextView/StaticLayout laws documented at text_shaper.h:138-147 (G36/G47),
// cross-validated against the loaded face metrics — no speculative values.
// Laws:
//   C1  includeFontPadding law (N2): first-line box above baseline = |top|
//       with pad ON, |ascent| with pad OFF; the two runs differ by exactly
//       |top|-|ascent| of the SAME face at the SAME size (G47 law).
//   C2  descent law mirrors it below the baseline (|bottom| vs |descent|).
//   C3  metrics identity: font_metrics() and the shaped run agree (the layout
//       is built from the face the shaper resolves — no separate constants).
//   C4  lineSpacingAdd law (N3): baseline step between identical lines grows
//       by exactly spacing_add when mult=1 (extra_k = add).
//   C5  lineSpacingMultiplier law (N3): mult=1.5 grows the step by
//       (below-above)*(1.5-1) relative to the single-spaced step (G47 extra_k).
//   C6  ellipsize END (N4): over-wide last line truncated with U+2026 and
//       fits max_width; NONE keeps full text.
//   C7  maxLines law (N4): 3-line text capped at 2 lines; maxLines!=singleLine
//       (a 1-line cap truncates content but wraps at width — line count = 1).
//   C8  first-strong base direction (NEW-23 first-strong half): a pure-Arabic
//       run reports rtl_base=true; a pure-Latin run false (the AOSP
//       first-strong heuristic; locale/textDirection parity stays oracle-bound).
#include "../src/fonts/text_shaper.h"
#include <cstdio>
#include <cmath>
#include <iostream>
#include <string>

using namespace miniandroid;

static int g_pass = 0, g_fail = 0;
static void record(bool ok, const std::string& what) {
    std::cout << (ok ? "  PASS  " : "  FAIL  ") << what << "\n";
    if (ok) ++g_pass; else ++g_fail;
}

int main() {
    std::cout << "== s18 text layout laws (N2/N3/N4) ==\n";
    auto& ts = fonts::TextShaper::instance();
    const float SZ = 16.0f;
    const std::string BODY = "the quick brown fox jumps over the lazy dog";

    // C1/C2 — includeFontPadding (N2): the G47 law lives in line_above[]
    // ("|fm.top| for the first line with includeFontPadding, else
    // |fm.ascent|", text_shaper.h:141-143). TextLayout.ascent/descent stay
    // the raw face box (text_shaper.cpp:1369, unconditional) — the pad law
    // is the FIRST-LINE line_above value.
    auto fm = ts.font_metrics(SZ, false, fonts::FACE_SYSTEM);
    auto pad = fonts::layout_text(BODY, SZ, false, 100.0f, 0, fonts::FACE_SYSTEM,
                              1.0f, 0.0f, true);
    auto nopad = fonts::layout_text(BODY, SZ, false, 100.0f, 0, fonts::FACE_SYSTEM,
                                1.0f, 0.0f, false);
    {
        std::cout << "        [C1 actual: |top|=" << -fm.top << " |ascent|="
                  << -fm.ascent << " pad.line_above[0]=" << pad.line_above[0]
                  << " nopad.line_above[0]=" << nopad.line_above[0] << "]\n";
        bool c1 = !pad.line_above.empty() && !nopad.line_above.empty() &&
                  pad.line_above[0] == -fm.top &&
                  nopad.line_above[0] == -fm.ascent;
        record(c1, "C1 includeFontPadding: first-line line_above = |top| vs "
                   "|ascent| (N2, G47 field law)");
        bool c2 = pad.line_boxes.size() >= 1 &&
                  pad.line_boxes.back() >= nopad.line_boxes.back();
        record(c2, "C2 last-line box with pad uses |bottom| (>= no-pad box) "
                   "(N2)");
    }

    // C3 — metrics identity: shaped run of the face is the geometry source
    {
        auto run = ts.shape("abc", SZ, false, fonts::FACE_SYSTEM);
        bool ok = run.ascent > 0 && run.descent > 0 &&
                  run.ascent == -fm.ascent && run.descent == fm.descent;
        record(ok, "C3 shaped run ascent/descent == face metrics (no drift)");
    }

    // C4/C5 — line spacing (N3): the G47 per-line law lives in line_boxes
    // (line_height stays the RAW single-spaced box — text_shaper.cpp:1369).
    // With include_pad=true: line 0 above = fm.top (negative), line 1 (last)
    // below = fm.bottom; extra applies to NON-last lines only (default
    // addLastLineLineSpacing=false, text_shaper.cpp:1032).
    {
        auto fm = ts.font_metrics(SZ, false, fonts::FACE_SYSTEM);
        const float RAW = fm.descent - fm.ascent;   // no-pad single box
        auto two = fonts::layout_text("aa\naa", SZ, false, 1000.0f, 0,
                                  fonts::FACE_SYSTEM, 1.0f, 8.0f, true);
        bool two_lines = two.line_boxes.size() == 2;
        bool c4 = two_lines &&
                  std::fabs(two.line_boxes[0] - ((fm.descent + 8.0f) - fm.top)) < 0.51f &&
                  std::fabs(two.line_boxes[1] - (fm.bottom - fm.top)) < 0.51f;
        record(c4,
               "C4 lineSpacingAdd: box0 = descent+add-top, box1 = bottom-top "
               "(extra on non-last lines only) (N3)");
        auto mult = fonts::layout_text("aa\naa", SZ, false, 1000.0f, 0,
                                   fonts::FACE_SYSTEM, 1.5f, 0.0f, true);
        bool c5 = mult.line_boxes.size() == 2 &&
                  std::fabs(mult.line_boxes[0] - 1.5f * (fm.descent - fm.top)) < 0.51f &&
                  std::fabs(mult.line_boxes[1] - (fm.bottom - fm.top)) < 0.51f;
        record(c5,
               "C5 lineSpacingMultiplier: box0 = m*(below-above), last box "
               "unmultiplied (N3)");
        (void)RAW;
    }

    // C6 — ellipsize END (N4): the truncation targets an OVER-WIDE last
    // drawn line. A wrap that already fits (all lines under max_width) has
    // nothing to truncate — the trigger is an unbreakable run wider than
    // max_width (or a maxLines cap mid-line).
    {
        const std::string WIDE = "extraordinarily lengthening throughout";
        auto none = fonts::layout_text(WIDE, SZ, false, 60.0f, 0,
                                   fonts::FACE_SYSTEM, 1.0f, 0.0f, true, false, 0);
        auto endt = fonts::layout_text(WIDE, SZ, false, 60.0f, 0,
                                   fonts::FACE_SYSTEM, 1.0f, 0.0f, true, false, 3);
        std::string last = endt.lines.empty() ? "" : endt.lines.back().text;
        std::cout << "        [C6 actual: lines(none)=" << none.lines.size()
                  << " lines(end)=" << endt.lines.size()
                  << " last='" << last
                  << "' w=" << (endt.lines.empty() ? -1.0f
                              : endt.lines.back().width) << "]\n";
        // U+2026 in UTF-8 is e2 80 a6 — match the full sequence (back()
        // alone would only see the 0xa6 trail byte).
        bool ell = last.find("\xe2\x80\xa6") != std::string::npos;
        bool fits = endt.lines.empty() ||
                    endt.lines.back().width <= 60.0f + 0.51f;
        bool none_keeps = !none.lines.empty() &&
                          none.lines.back().text.find("\xe2\x80\xa6") ==
                              std::string::npos;
        record(ell && fits && none_keeps,
               "C6 ellipsize END: over-wide last line truncated with U+2026 "
               "and fits width; NONE keeps content (N4)");
    }

    // C7 — maxLines (N4)
    {
        auto capped = fonts::layout_text(BODY, SZ, false, 60.0f, 2,
                                     fonts::FACE_SYSTEM, 1.0f, 0.0f, true);
        auto one = fonts::layout_text(BODY, SZ, false, 60.0f, 1,
                                  fonts::FACE_SYSTEM, 1.0f, 0.0f, true);
        record(capped.lines.size() == 2 && one.lines.size() == 1,
               "C7 maxLines caps the block: 2 and 1 lines (N4; != singleLine)");
    }

    // C8 — first-strong base direction (NEW-23: first-strong half)
    {
        auto ar = ts.shape("\xD9\x85\xD8\xB1\xD8\xAD\xD8\xA8\xD8\xA7", SZ,
                           false, fonts::FACE_SYSTEM);  // مرحبا
        auto la = ts.shape("hello", SZ, false, fonts::FACE_SYSTEM);
        record(ar.rtl_base && !la.rtl_base,
               "C8 first-strong: Arabic run rtl_base=true, Latin false");
    }

    std::cout << "== s18 text layout laws: " << g_pass << " pass / " << g_fail
              << " fail ==\n";
    return g_fail == 0 ? 0 : 1;
}
