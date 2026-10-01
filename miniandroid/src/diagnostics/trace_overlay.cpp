// S135 — VISUAL RUNTIME BOOT/TRACE LOGGER — overlay composer implementation.
// See trace_overlay.h for the architecture law. Pure diagnostics sink:
// reads TraceEngine state, composes a COPY of the authoritative frame.
#include "trace_overlay.h"

#include <cstdlib>
#include <algorithm>
#include <cmath>
#include <sstream>
#include <iomanip>

namespace miniandroid {
namespace diagnostics {

using renderer::FrameBuffer;
using renderer::RGBA;
using renderer::BitmapFont;

namespace {

// ── Semantic palette (S135 §4) ───────────────────────────────────────────
constexpr struct { uint8_t r, g, b; } kGreen   = { 70, 205, 90 };
constexpr struct { uint8_t r, g, b; } kYellow  = { 235, 195, 40 };
constexpr struct { uint8_t r, g, b; } kRed     = { 238, 70, 70 };
constexpr struct { uint8_t r, g, b; } kBlue    = { 90, 150, 245 };
constexpr struct { uint8_t r, g, b; } kPurple  = { 190, 110, 235 };
constexpr struct { uint8_t r, g, b; } kGray    = { 145, 145, 145 };
constexpr struct { uint8_t r, g, b; } kPanel   = { 16, 20, 28 };
constexpr struct { uint8_t r, g, b; } kText    = { 225, 228, 235 };

RGBA sev_color(EventSev s) {
    switch (s) {
        case EventSev::CONFIRMED:  return { kGreen.r, kGreen.g, kGreen.b, 255 };
        case EventSev::PENDING:    return { kYellow.r, kYellow.g, kYellow.b, 255 };
        case EventSev::FAILURE:    return { kRed.r, kRed.g, kRed.b, 255 };
        case EventSev::RENDERER:   return { kPurple.r, kPurple.g, kPurple.b, 255 };
        case EventSev::NOT_REACHED:return { kGray.r, kGray.g, kGray.b, 255 };
        case EventSev::INFO:
        default:                   return { kBlue.r, kBlue.g, kBlue.b, 255 };
    }
}

// ── Status mini-glyphs (hand-drawn 8x9, MSB-first) ───────────────────────
// ASCII-only font cannot draw ✓ ✗ — the overlay draws its own semantic
// marks. Colors carry the meaning; the shapes disambiguate for colorblind
// readers (S135 §4: color is semantic, not decoration).
constexpr int kGlyphW = 8, kGlyphH = 9;
constexpr uint8_t kCheck[9]  = {0x00,0x01,0x03,0x06,0x6C,0x78,0x30,0x00,0x00};
constexpr uint8_t kCross[9]  = {0x00,0x41,0x23,0x14,0x08,0x14,0x23,0x41,0x00};
constexpr uint8_t kOpenSq[9] = {0x3C,0x42,0x42,0x42,0x42,0x42,0x3C,0x00,0x00};
constexpr uint8_t kDash[9]   = {0x00,0x00,0x00,0x1C,0x1C,0x00,0x00,0x00,0x00};
constexpr uint8_t kQuest[9]  = {0x3C,0x42,0x04,0x18,0x10,0x00,0x10,0x00,0x00};
constexpr uint8_t kTilde[9]  = {0x00,0x00,0x00,0x22,0x44,0x00,0x00,0x00,0x00};

void draw_status_glyph(FrameBuffer& fb, int x, int y, EventSev sev) {
    const uint8_t* rows = nullptr;
    switch (sev) {
        case EventSev::CONFIRMED:  rows = kCheck; break;
        case EventSev::FAILURE:    rows = kCross; break;
        case EventSev::PENDING:    rows = kTilde; break;
        case EventSev::NOT_REACHED:rows = kDash;  break;
        case EventSev::INFO:       rows = kOpenSq;break;
        case EventSev::RENDERER:   rows = kTilde; break;
    }
    const RGBA c = sev_color(sev);
    for (int r = 0; r < kGlyphH; ++r) {
        for (int col = 0; col < kGlyphW; ++col) {
            if (rows[r] & (0x80 >> col))
                fb.set_pixel(x + col, y + r, c);
        }
    }
}

// ASCII text via the existing 8x16 BitmapFont (REUSE — EXP-092 font data).
const BitmapFont& overlay_font() {
    static BitmapFont f;   // identical glyph data the renderer uses
    return f;
}

void draw_text(FrameBuffer& fb, const std::string& text, int x, int y,
               const RGBA& color) {
    const BitmapFont& font = overlay_font();
    int cx = x;
    for (char ch : text) {
        const BitmapFont::Glyph* g = font.get_glyph(ch);
        if (!g) { cx += 8; continue; }
        const int top = y;   // glyph top
        for (int row = 0; row < g->height; ++row) {
            const uint8_t bits = g->bitmap[row];
            for (int col = 0; col < 8; ++col) {
                if (bits & (0x80 >> col))
                    fb.set_pixel(cx + col, top + row, color);
            }
        }
        cx += g->advance;
    }
}

int text_width(const std::string& text) {
    int w = 0;
    for (char ch : text) {
        const BitmapFont::Glyph* g = overlay_font().get_glyph(ch);
        w += g ? g->advance : 8;
    }
    return w;
}
[[maybe_unused]] static int text_width_unused_ref = text_width("x");

// Alpha-blended panel backing (semi-transparent — the app frame stays
// readable under the diagnostics panel).
void blend_rect(FrameBuffer& fb, int x0, int y0, int w, int h,
                uint8_t rr, uint8_t gg, uint8_t bb, uint8_t alpha) {
    const int W = fb.get_width(), H = fb.get_height();
    for (int y = y0; y < y0 + h; ++y) {
        if (y < 0 || y >= H) continue;
        for (int x = x0; x < x0 + w; ++x) {
            if (x < 0 || x >= W) continue;
            const RGBA src = fb.get_pixels()[static_cast<size_t>(y) * W + x];
            const uint32_t a = alpha, ia = 255 - alpha;
            RGBA out;
            out.r = static_cast<uint8_t>((rr * a + src.r * ia) / 255);
            out.g = static_cast<uint8_t>((gg * a + src.g * ia) / 255);
            out.b = static_cast<uint8_t>((bb * a + src.b * ia) / 255);
            out.a = 255;
            fb.set_pixel(x, y, out);
        }
    }
}

std::string trunc(const std::string& s, size_t max_chars) {
    if (s.size() <= max_chars) return s;
    if (max_chars <= 3) return s.substr(0, max_chars);
    return s.substr(0, max_chars - 3) + "..";
}

} // anonymous namespace

TraceOverlay::Options TraceOverlay::options_from_env() {
    Options o;
    const char* v = std::getenv("MINIANDROID_TRACE_UI");
    if (v) {
        const std::string mode = v;
        o.expanded = (mode != "1" && mode != "header" && mode != "compact");
        o.header_only = (mode == "header");
    }
    return o;
}

FrameBuffer TraceOverlay::compose(const FrameBuffer& authoritative,
                                  const TraceEngine& trace,
                                  const Options& opts) {
    // COPY of the authoritative frame — the original evidence is untouched.
    FrameBuffer fb(authoritative.get_width(), authoritative.get_height());
    fb.get_pixels_mut() = authoritative.get_pixels();

    const int W = fb.get_width(), H = fb.get_height();
    const int margin = opts.margin;
    const int row_pitch = 18;
    const int panel_pad = 10;

    const auto& stages = trace.stage_states();
    const auto& order = stage::canonical_order();

    auto stage_sev = [&](const std::string& s) {
        auto it = stages.find(s);
        return it != stages.end() ? it->second : EventSev::NOT_REACHED;
    };

    // ── Compact status header (§20: MA | RUN | LIFECYCLE | VIEW DRAW FRAME)
    const std::string run_disp = trace.run_id().size() > 10
        ? trace.run_id().substr(trace.run_id().size() - 10) : trace.run_id();
    std::string life = trace.lifecycle_label().empty()
        ? std::string("(none)") : trace.lifecycle_label();

    if (opts.header_only) {
        const int hh = 22;
        const int hw = std::min(W - 2 * margin, 620);
        blend_rect(fb, margin, margin, hw, hh, kPanel.r, kPanel.g, kPanel.b, 205);
        std::string header = "MA | RUN " + run_disp + " | " + life;
        draw_text(fb, header, margin + 6, margin + 4,
                  { kText.r, kText.g, kText.b, 255 });
        // status glyphs right-to-left: FRAME, DRAW, VIEW (§20 header law)
        int rx = margin + hw - 8;
        draw_status_glyph(fb, rx - 8, margin + 6, stage_sev(stage::FRAME)); rx -= 8 + 8 + 44;
        draw_status_glyph(fb, rx - 8, margin + 6, stage_sev(stage::DRAW));   rx -= 8 + 8 + 42;
        draw_status_glyph(fb, rx - 8, margin + 6, stage_sev(stage::VIEWTREE));
        return fb;
    }

    // ── Full panel (§21 expanded forensic panel) ──────────────────────────
    struct Row { std::string label; std::string detail; EventSev sev; bool glyph; };
    std::vector<Row> rows;
    rows.push_back({"MINIANDROID RUNTIME TRACE", "", EventSev::INFO, false});
    rows.push_back({"RUN " + run_disp, "APK " + trunc(trace.package_label(), 30),
                    EventSev::INFO, false});
    rows.push_back({"ACTIVITY", trunc(trace.activity_label(), 34),
                    EventSev::INFO, false});
    rows.push_back({"LIFECYCLE", life,
                    life == "RESUMED" ? EventSev::CONFIRMED :
                    (life.empty() || life == "(none)" ? EventSev::NOT_REACHED
                                                      : EventSev::PENDING),
                    true});
    rows.push_back({"---", "", EventSev::NOT_REACHED, false});
    for (const auto& s : order) {
        std::string detail = trace.stage_detail(s);
        rows.push_back({s, trunc(detail, 52), stage_sev(s), true});
    }
    rows.push_back({"---", "", EventSev::NOT_REACHED, false});
    rows.push_back({"RENDERER",
                    trace.current_renderer_family().empty()
                        ? std::string(rf::UNKNOWN)
                        : trace.current_renderer_family(),
                    EventSev::RENDERER, false});

    const nlohmann::json& div = trace.first_divergence();
    std::string div_stage = "(none - full chain confirmed)";
    RGBA div_color = { kGreen.r, kGreen.g, kGreen.b, 255 };
    if (!div.is_null() && div.contains("stage") && !div["stage"].is_null()) {
        div_stage = div.value("stage", "?");
        div_color = { kRed.r, kRed.g, kRed.b, 255 };
    } else if (!div.is_null() && div.contains("event")) {
        // explicit-evidence divergence without a stage label
        div_stage = div.value("event", "?");
        div_color = { kRed.r, kRed.g, kRed.b, 255 };
    } else if (div.is_null()) {
        div_stage = "(pending finalize)";
        div_color = { kGray.r, kGray.g, kGray.b, 255 };
    }
    rows.push_back({"FIRST DIVERGENCE", trunc(div_stage, 30), EventSev::INFO, false});
    rows.push_back({"LAST EVENT", trunc(trace.last_event_name(), 30),
                    EventSev::INFO, false});

    const nlohmann::json& fa = trace.frame_analysis();
    if (!fa.is_null()) {
        rows.push_back({"FRAME", fa.value("verdict", std::string("?")),
                        fa.value("verdict", "") == "REAL_APP_CONTENT"
                            ? EventSev::CONFIRMED : EventSev::FAILURE, true});
        rows.push_back({"PIXELS",
                        "non-default " + std::to_string(
                            fa.value("non_default_pixels", size_t(0))) +
                        "  colors " + std::to_string(
                            fa.value("unique_colors", size_t(0))),
                        EventSev::INFO, false});
    }

    // Expanded: last events tail (§11) + first-divergence details
    const bool expanded = opts.expanded;
    if (expanded && !div.is_null()) {
        rows.push_back({"---", "", EventSev::NOT_REACHED, false});
        if (div.contains("expected"))
            rows.push_back({"EXPECTED", trunc(div.value("expected", ""), 52),
                            EventSev::INFO, false});
        if (div.contains("actual"))
            rows.push_back({"ACTUAL", trunc(div.value("actual", ""), 52),
                            EventSev::FAILURE, false});
        if (div.contains("last_successful_stage"))
            rows.push_back({"LAST OK", div.value("last_successful_stage", ""),
                            EventSev::CONFIRMED, false});
        if (div.contains("next_required_stage"))
            rows.push_back({"NEXT REQUIRED", div.value("next_required_stage", ""),
                            EventSev::PENDING, false});
        if (div.contains("first_failure_event") &&
            div["first_failure_event"].is_object()) {
            const auto& ffe = div["first_failure_event"];
            std::string exc = ffe.value("exception", "");
            std::string cls = ffe.value("cls", "");
            std::string mth = ffe.value("method", "");
            if (!exc.empty())
                rows.push_back({"EXCEPTION", trunc(exc, 52), EventSev::FAILURE, false});
            if (!cls.empty())
                rows.push_back({"LAST CLASS", trunc(cls, 52), EventSev::INFO, false});
            if (!mth.empty())
                rows.push_back({"LAST METHOD", trunc(mth, 52), EventSev::INFO, false});
        }
        size_t tail_n = std::min(trace.runtime_events().size(),
                                 static_cast<size_t>(opts.max_tail_events));
        if (tail_n > 0) {
            rows.push_back({"---", "", EventSev::NOT_REACHED, false});
            rows.push_back({"LAST EVENTS", "", EventSev::INFO, false});
            for (size_t i = trace.runtime_events().size() - tail_n;
                 i < trace.runtime_events().size(); ++i) {
                const RuntimeEvent& e = trace.runtime_events()[i];
                std::string line = std::to_string(e.seq) + " " + e.event;
                if (!e.state.empty()) line += " " + e.state;
                rows.push_back({"", trunc(line, 62), e.sev, false});
            }
        }
    }

    // panel geometry
    const int label_col = 8;                  // glyph col width
    const int text_col = label_col + 150;     // detail text column x offset
    int panel_w = text_col + 60 * 8 + panel_pad * 2;
    panel_w = std::min(panel_w, W - 2 * margin);
    const int panel_h = rows.size() * row_pitch + panel_pad * 2 + 6;
    const int px = margin, py = margin;

    blend_rect(fb, px, py, panel_w, std::min(panel_h, H - 2 * margin),
               kPanel.r, kPanel.g, kPanel.b, 210);
    // 2px accent border — semantic: red when diverged, green when complete
    const bool diverged = !div.is_null();
    const RGBA border = diverged
        ? RGBA{ kRed.r, kRed.g, kRed.b, 255 }
        : RGBA{ kGreen.r, kGreen.g, kGreen.b, 255 };
    const int bh = std::min(panel_h, H - 2 * margin);
    for (int i = 0; i < 2; ++i) {
        for (int x = px; x < px + panel_w; ++x) {
            fb.set_pixel(x, py + i, border);
            fb.set_pixel(x, py + bh - 1 - i, border);
        }
        for (int y = py; y < py + bh; ++y) {
            fb.set_pixel(px + i, y, border);
            fb.set_pixel(px + panel_w - 1 - i, y, border);
        }
    }

    // rows
    int y = py + panel_pad;
    for (const auto& r : rows) {
        if (r.label == "---") {
            const RGBA c{90, 96, 110, 255};
            for (int x = px + panel_pad; x < px + panel_w - panel_pad; x += 2)
                fb.set_pixel(x, y + 8, c);
            y += row_pitch;
            continue;
        }
        int tx = px + panel_pad;
        if (r.glyph) {
            draw_status_glyph(fb, tx, y + 4, r.sev);
            tx += label_col + 4;
        } else {
            tx += 4;
        }
        RGBA text_color = { kText.r, kText.g, kText.b, 255 };
        if (r.label == "MINIANDROID RUNTIME TRACE")
            text_color = { kBlue.r, kBlue.g, kBlue.b, 255 };
        else if (r.label == "FIRST DIVERGENCE")
            text_color = div_color;
        else if (r.label == "RENDERER")
            text_color = { kPurple.r, kPurple.g, kPurple.b, 255 };
        draw_text(fb, r.label, tx, y, text_color);
        if (!r.detail.empty()) {
            // detail color follows the row semantics when semantic,
            // otherwise neutral text
            RGBA dc = text_color;
            if (r.label == "FIRST DIVERGENCE") dc = div_color;
            else if (r.sev == EventSev::FAILURE) dc = { kRed.r, kRed.g, kRed.b, 255 };
            else if (r.sev == EventSev::CONFIRMED) dc = { kGreen.r, kGreen.g, kGreen.b, 255 };
            else if (r.sev == EventSev::PENDING) dc = { kYellow.r, kYellow.g, kYellow.b, 255 };
            draw_text(fb, r.detail, px + panel_pad + text_col, y, dc);
        }
        y += row_pitch;
        if (y + row_pitch > py + bh) break;   // honest clipping
    }

    // TRACE ID footer (§5: "TRACE ID: 1042:000184")
    std::ostringstream tid;
    tid << "TRACE ID: " << run_disp << ":" << std::setw(6) << std::setfill('0')
        << trace.rt_total();
    draw_text(fb, tid.str(), px + panel_pad, py + bh - 20,
              { kGray.r, kGray.g, kGray.b, 255 });

    return fb;
}

} // namespace diagnostics
} // namespace miniandroid
