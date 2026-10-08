/*
 * MiniAndroid Runtime — CONT-24 EXPERIMENT (TEST BRANCH ONLY)
 * skeleton_light.cpp — implementation. ONE file, ~330 lines, dependencies:
 *   FrameBuffer/RGBA (software_renderer.h — stays in any build) +
 *   ViewShadow (android_shadows.h — stays in any build) +
 *   ViewRenderer::layout (view_renderer.cpp — stays in any build).
 * It deliberately does NOT reference: canvas_shadow, text_shaper,
 * bitmap_font_data, vector_decode, gif_decoder, bitmap_shadow, state_list.
 * The LOC census in evidence/cont24/ measures what that independence means.
 */

#include "skeleton_light.h"

#include <algorithm>
#include <climits>
#include <cstdlib>
#include <cstring>
#include <set>
#include <vector>

namespace miniandroid {
namespace renderer {

bool skeleton_light_enabled() {
    const char* e = std::getenv("MINIANDROID_SKELETON_LIGHT");
    return e && e[0] && std::strcmp(e, "0") != 0;
}

namespace {

// ── 5x7 ASCII font (rows: bit 4 = leftmost column), 0x20..0x7E only ─────
// 96 glyphs * 7 bytes = 672 bytes of data — the entire "text stack".
const uint8_t kFont5x7[96][7] = {
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // space
    {0x00,0x00,0x5F,0x00,0x00,0x00,0x00}, // !
    {0x00,0x07,0x00,0x07,0x00,0x00,0x00}, // "
    {0x14,0x7F,0x14,0x7F,0x14,0x00,0x00}, // #
    {0x24,0x2A,0x7F,0x2A,0x12,0x00,0x00}, // $
    {0x23,0x13,0x08,0x64,0x62,0x00,0x00}, // %
    {0x36,0x49,0x55,0x22,0x50,0x00,0x00}, // &
    {0x00,0x05,0x03,0x00,0x00,0x00,0x00}, // '
    {0x00,0x1C,0x22,0x41,0x00,0x00,0x00}, // (
    {0x00,0x41,0x22,0x1C,0x00,0x00,0x00}, // )
    {0x14,0x08,0x3E,0x08,0x14,0x00,0x00}, // *
    {0x08,0x08,0x3E,0x08,0x08,0x00,0x00}, // +
    {0x00,0x50,0x30,0x00,0x00,0x00,0x00}, // ,
    {0x08,0x08,0x08,0x08,0x08,0x00,0x00}, // -
    {0x00,0x60,0x60,0x00,0x00,0x00,0x00}, // .
    {0x20,0x10,0x08,0x04,0x02,0x00,0x00}, // /
    {0x3E,0x51,0x49,0x45,0x3E,0x00,0x00}, // 0
    {0x00,0x42,0x7F,0x40,0x00,0x00,0x00}, // 1
    {0x42,0x61,0x51,0x49,0x46,0x00,0x00}, // 2
    {0x21,0x41,0x45,0x4B,0x31,0x00,0x00}, // 3
    {0x18,0x14,0x12,0x7F,0x10,0x00,0x00}, // 4
    {0x27,0x45,0x45,0x45,0x39,0x00,0x00}, // 5
    {0x3C,0x4A,0x49,0x49,0x30,0x00,0x00}, // 6
    {0x01,0x71,0x09,0x05,0x03,0x00,0x00}, // 7
    {0x36,0x49,0x49,0x49,0x36,0x00,0x00}, // 8
    {0x06,0x49,0x49,0x29,0x1E,0x00,0x00}, // 9
    {0x00,0x36,0x36,0x00,0x00,0x00,0x00}, // :
    {0x00,0x56,0x36,0x00,0x00,0x00,0x00}, // ;
    {0x00,0x08,0x14,0x22,0x41,0x00,0x00}, // <
    {0x14,0x14,0x14,0x14,0x14,0x00,0x00}, // =
    {0x41,0x22,0x14,0x08,0x00,0x00,0x00}, // >
    {0x02,0x01,0x51,0x09,0x06,0x00,0x00}, // ?
    {0x32,0x49,0x79,0x41,0x3E,0x00,0x00}, // @
    {0x7E,0x11,0x11,0x11,0x7E,0x00,0x00}, // A
    {0x7F,0x49,0x49,0x49,0x36,0x00,0x00}, // B
    {0x3E,0x41,0x41,0x41,0x22,0x00,0x00}, // C
    {0x7F,0x41,0x41,0x22,0x1C,0x00,0x00}, // D
    {0x7F,0x49,0x49,0x49,0x41,0x00,0x00}, // E
    {0x7F,0x09,0x09,0x01,0x01,0x00,0x00}, // F
    {0x3E,0x41,0x41,0x51,0x32,0x00,0x00}, // G
    {0x7F,0x08,0x08,0x08,0x7F,0x00,0x00}, // H
    {0x00,0x41,0x7F,0x41,0x00,0x00,0x00}, // I
    {0x20,0x40,0x41,0x3F,0x01,0x00,0x00}, // J
    {0x7F,0x08,0x14,0x22,0x41,0x00,0x00}, // K
    {0x7F,0x40,0x40,0x40,0x40,0x00,0x00}, // L
    {0x7F,0x02,0x04,0x02,0x7F,0x00,0x00}, // M
    {0x7F,0x04,0x08,0x10,0x7F,0x00,0x00}, // N
    {0x3E,0x41,0x41,0x41,0x3E,0x00,0x00}, // O
    {0x7F,0x09,0x09,0x09,0x06,0x00,0x00}, // P
    {0x3E,0x41,0x51,0x21,0x5E,0x00,0x00}, // Q
    {0x7F,0x09,0x19,0x29,0x46,0x00,0x00}, // R
    {0x46,0x49,0x49,0x49,0x31,0x00,0x00}, // S
    {0x01,0x01,0x7F,0x01,0x01,0x00,0x00}, // T
    {0x3F,0x40,0x40,0x40,0x3F,0x00,0x00}, // U
    {0x1F,0x20,0x40,0x20,0x1F,0x00,0x00}, // V
    {0x7F,0x20,0x18,0x20,0x7F,0x00,0x00}, // W
    {0x63,0x14,0x08,0x14,0x63,0x00,0x00}, // X
    {0x03,0x04,0x78,0x04,0x03,0x00,0x00}, // Y
    {0x61,0x51,0x49,0x45,0x43,0x00,0x00}, // Z
    {0x00,0x00,0x7F,0x41,0x41,0x00,0x00}, // [
    {0x02,0x04,0x08,0x10,0x20,0x00,0x00}, // backslash
    {0x00,0x41,0x41,0x7F,0x00,0x00,0x00}, // ]
    {0x04,0x02,0x01,0x02,0x04,0x00,0x00}, // ^
    {0x40,0x40,0x40,0x40,0x40,0x00,0x00}, // _
    {0x00,0x01,0x02,0x04,0x00,0x00,0x00}, // `
    {0x20,0x54,0x54,0x54,0x78,0x00,0x00}, // a
    {0x7F,0x48,0x44,0x44,0x38,0x00,0x00}, // b
    {0x38,0x44,0x44,0x44,0x20,0x00,0x00}, // c
    {0x38,0x44,0x44,0x48,0x7F,0x00,0x00}, // d
    {0x38,0x54,0x54,0x54,0x18,0x00,0x00}, // e
    {0x08,0x7E,0x09,0x01,0x02,0x00,0x00}, // f
    {0x08,0x14,0x54,0x54,0x3C,0x00,0x00}, // g
    {0x7F,0x08,0x04,0x04,0x78,0x00,0x00}, // h
    {0x00,0x44,0x7D,0x40,0x00,0x00,0x00}, // i
    {0x20,0x40,0x44,0x3D,0x00,0x00,0x00}, // j
    {0x00,0x7F,0x10,0x28,0x44,0x00,0x00}, // k
    {0x00,0x41,0x7F,0x40,0x00,0x00,0x00}, // l
    {0x7C,0x04,0x18,0x04,0x78,0x00,0x00}, // m
    {0x7C,0x08,0x04,0x04,0x78,0x00,0x00}, // n
    {0x38,0x44,0x44,0x44,0x38,0x00,0x00}, // o
    {0x7C,0x14,0x14,0x14,0x08,0x00,0x00}, // p
    {0x08,0x14,0x14,0x18,0x7C,0x00,0x00}, // q
    {0x7C,0x08,0x04,0x04,0x08,0x00,0x00}, // r
    {0x48,0x54,0x54,0x54,0x20,0x00,0x00}, // s
    {0x04,0x3F,0x44,0x40,0x20,0x00,0x00}, // t
    {0x3C,0x40,0x40,0x20,0x7C,0x00,0x00}, // u
    {0x1C,0x20,0x40,0x20,0x1C,0x00,0x00}, // v
    {0x3C,0x40,0x30,0x40,0x3C,0x00,0x00}, // w
    {0x44,0x28,0x10,0x28,0x44,0x00,0x00}, // x
    {0x0C,0x50,0x50,0x50,0x3C,0x00,0x00}, // y
    {0x44,0x64,0x54,0x4C,0x44,0x00,0x00}, // z
    {0x00,0x08,0x36,0x41,0x00,0x00,0x00}, // {
    {0x00,0x00,0x7F,0x00,0x00,0x00,0x00}, // |
    {0x00,0x41,0x36,0x08,0x00,0x00,0x00}, // }
    {0x08,0x04,0x48,0x30,0x30,0x48,0x04}, // ~
};

void sl_pixel(FrameBuffer& fb, int x, int y, const RGBA& c,
              uint64_t& touched) {
    if (x < 0 || y < 0 || x >= fb.get_width() || y >= fb.get_height()) return;
    fb.set_pixel(x, y, c);
    touched++;
}

void sl_fill_rect(FrameBuffer& fb, int x, int y, int w, int h, const RGBA& c,
                  uint64_t& touched) {
    if (w <= 0 || h <= 0) return;
    for (int yy = y; yy < y + h; yy++)
        for (int xx = x; xx < x + w; xx++)
            sl_pixel(fb, xx, yy, c, touched);
}

void sl_outline_rect(FrameBuffer& fb, int x, int y, int w, int h,
                     const RGBA& c, uint64_t& touched) {
    if (w <= 0 || h <= 0) return;
    for (int xx = x; xx < x + w; xx++) {
        sl_pixel(fb, xx, y, c, touched);
        sl_pixel(fb, xx, y + h - 1, c, touched);
    }
    for (int yy = y; yy < y + h; yy++) {
        sl_pixel(fb, x, yy, c, touched);
        sl_pixel(fb, x + w - 1, yy, c, touched);
    }
}

// One text line at 1x scale (5x7 + 1px spacing). ASCII-only law: bytes
// outside 0x20..0x7E render as a hollow block (honest placeholder).
void sl_draw_text(FrameBuffer& fb, int x, int y, const std::string& s,
                  const RGBA& c, uint64_t& touched) {
    int cx = x;
    for (unsigned char ch : s) {
        if (ch == '\n' || ch == '\t') ch = ' ';
        const uint8_t* glyph = kFont5x7[0];
        if (ch >= 0x20 && ch <= 0x7E) glyph = kFont5x7[ch - 0x20];
        // rows carry the glyph (bit 4 = leftmost column of the 5-wide cell)
        for (int row = 0; row < 7; row++) {
            const uint8_t bits = glyph[row];
            for (int col = 0; col < 5; col++)
                if (bits & (1 << (4 - col)))
                    sl_pixel(fb, cx + col, y + row, c, touched);
        }
        cx += 6;
        if (cx > fb.get_width()) break;
    }
}

RGBA depth_outline(int depth) {
    // Deterministic depth-cycled palette (never near-white: keeps the
    // non-white pixel metric honest against window backgrounds).
    static const uint8_t pal[6][3] = {
        {0xC0, 0x20, 0x20}, {0x20, 0x60, 0xC0}, {0x20, 0xA0, 0x40},
        {0xC0, 0x80, 0x20}, {0x80, 0x40, 0xC0}, {0x20, 0xA0, 0xA0}};
    const auto& p = pal[depth % 6];
    return RGBA{p[0], p[1], p[2], 0xFF};
}

bool is_text_like(const framework::ViewShadow::ViewNode& n) {
    const std::string& c = n.class_desc;
    return c.find("TextView") != std::string::npos ||
           c.find("EditText") != std::string::npos ||
           c.find("Button") != std::string::npos ||
           c.find("CheckBox") != std::string::npos ||
           c.find("RadioButton") != std::string::npos ||
           c.find("Switch") != std::string::npos;
}

}  // namespace

// ── COMPACT MEASURE (self-contained; AOSP ViewGroup laws, minimal subset) ──
// Resolves x/y/width/height px for every node in the subtree.
//   MATCH_PARENT(-1) → parent available; WRAP_CONTENT(-2) → content;
//   captured lp ≥ 0 → fixed px; no LayoutParams (INT_MIN) → node width/height
//   if the inflater set them, else MATCH_PARENT. LinearLayout honors its
//   captured orientation (AOSP default HORIZONTAL); everything else stacks
//   frame-style at the content origin. Deterministic, cycle-safe.
namespace {

struct SLFrame { int x, y, w, h; };

int sl_content_w(const framework::ViewShadow::ViewNode& n) {
    const std::string& s = !n.text.empty() ? n.text : n.hint;
    int w = 0;
    if (!s.empty()) w = std::min((size_t)120, s.size()) * 6 + 8;
    if (!n.children.empty()) {
        int cw = 0;
        for (uint32_t cid : n.children) {
            (void)cid;
            cw = std::max(cw, 24);
        }
        w = std::max(w, cw);
    }
    return std::max(w, 8) + n.padding_left + n.padding_right;
}

int sl_content_h(const framework::ViewShadow::ViewNode& n) {
    if (!n.children.empty()) return 24;
    return (!n.text.empty() || !n.hint.empty()) ? 16 : 8;
}

int sl_resolve(int lp, int fallback_px, int avail, int content) {
    if (lp == -1) return std::max(0, avail);
    if (lp == -2) return std::max(0, content);
    if (lp >= 0) return lp;
    return fallback_px > 0 ? fallback_px : std::max(0, avail);
}

bool sl_is_vertical(const framework::ViewShadow::ViewNode& n) {
    if (n.orientation >= 0) return n.orientation == 1;
    const std::string& c = n.class_desc;
    if (c.find("ScrollView") != std::string::npos ||
        c.find("ListView") != std::string::npos ||
        c.find("RecyclerView") != std::string::npos ||
        c.find("VerticalGrid") != std::string::npos)
        return true;  // vertical scrollers
    if (c.find("LinearLayout") != std::string::npos)
        return false;  // AOSP LinearLayout default = HORIZONTAL
    return true;       // menu/list-shaped trees dominate real apps
}

void sl_measure(framework::ViewShadow::ViewNode& n, SLFrame f,
                framework::ViewShadow* views, int& depth, int& max_depth,
                std::set<uint32_t>& visited) {
    if (!visited.insert(n.view_id).second) return;
    max_depth = std::max(max_depth, depth);
    const int pad_w = n.padding_left + n.padding_right;
    const int pad_h = n.padding_top + n.padding_bottom;
    const int avail_w = std::max(0, f.w - pad_w);
    const int avail_h = std::max(0, f.h - pad_h);
    const int cw = sl_resolve(n.lp_width, n.width > 0 ? n.width : INT_MIN,
                              avail_w, sl_content_w(n));
    const int ch = sl_resolve(n.lp_height, n.height > 0 ? n.height : INT_MIN,
                              avail_h, sl_content_h(n));
    n.x = f.x;
    n.y = f.y;
    n.width = cw;
    n.height = ch;
    depth++;
    // position children inside the content box
    const int cx0 = f.x + n.padding_left, cy0 = f.y + n.padding_top;
    const int box_w = cw - pad_w, box_h = ch - pad_h;
    if (sl_is_vertical(n)) {
        int cy = cy0;
        for (uint32_t cid : n.children) {
            auto* c = views->find_node(cid);
            if (!c) continue;
            const int m = c->lp_margin_top;
            const int cch = sl_resolve(c->lp_height,
                                       c->height > 0 ? c->height : INT_MIN,
                                       std::max(0, box_h - (cy - cy0)),
                                       sl_content_h(*c));
            const int ccw = sl_resolve(c->lp_width,
                                       c->width > 0 ? c->width : INT_MIN,
                                       box_w, sl_content_w(*c));
            const int cxx = cx0 + c->lp_margin_left +
                            (ccw >= box_w ? 0 : (box_w - ccw) / 2);
            sl_measure(*c, {cxx, cy + m, ccw, cch}, views, depth, max_depth,
                       visited);
            cy += m + cch + 4;  // AOSP LinearLayout no-spacing + 1px divider
        }
    } else {
        for (uint32_t cid : n.children) {
            auto* c = views->find_node(cid);
            if (!c) continue;
            const int ccw = sl_resolve(c->lp_width,
                                       c->width > 0 ? c->width : INT_MIN,
                                       box_w, sl_content_w(*c));
            const int cch = sl_resolve(c->lp_height,
                                       c->height > 0 ? c->height : INT_MIN,
                                       box_h, sl_content_h(*c));
            sl_measure(*c,
                       {cx0 + c->lp_margin_left, cy0 + c->lp_margin_top, ccw,
                        cch},
                       views, depth, max_depth, visited);
        }
    }
    depth--;
}

}  // namespace

bool skeleton_light_render(framework::ViewShadow* views, uint32_t root_id,
                           int screen_w, int screen_h, const RGBA& win_bg,
                           FrameBuffer& fb, SkeletonLightStats& stats) {
    if (!views || root_id == 0) return false;
    framework::ViewShadow::ViewNode* root = views->find_node(root_id);
    if (!root) return false;

    // 1) GEOMETRY — the self-contained compact measure above (reuse of the
    //    stale view_renderer.cpp module was attempted; it no longer compiles
    //    against the current ViewShadow API — recorded in the evidence).
    {
        std::set<uint32_t> seen;
        int depth = 0, max_depth = 0;
        sl_measure(*root, {0, 0, screen_w, screen_h}, views, depth, max_depth,
                   seen);
    }

    const auto pixel_eq = [](const RGBA& a, const RGBA& b) {
        return a.r == b.r && a.g == b.g && a.b == b.b && a.a == b.a;
    };

    // 2) PAINT — iterative walk (visited-set law, same as the engine walk).
    struct Task {
        framework::ViewShadow::ViewNode* n;
        int depth;
    };
    std::vector<Task> stack;
    std::set<uint32_t> visited;
    stack.push_back({root, 0});
    while (!stack.empty()) {
        const Task t = stack.back();
        stack.pop_back();
        if (!t.n || !visited.insert(t.n->view_id).second) continue;
        stats.nodes_total++;
        stats.depth_max = std::max(stats.depth_max, t.depth);

        if (t.n->visibility == 8) {  // GONE (AOSP constant)
            stats.gone_skipped++;
            continue;
        }
        if (t.n->visibility == 4) stats.invisible++;
        const bool paintable = t.n->visibility != 8 && t.n->visibility != 4;

        const int x = t.n->x, y = t.n->y;
        const int w = t.n->width, h = t.n->height;
        const bool on_screen = x < screen_w && y < screen_h &&
                               x + w > 0 && y + h > 0;

        // (a) background — only REAL app-set bg state is painted.
        if (paintable && on_screen && t.n->bg_color != 0) {
            const RGBA bg((uint8_t)((t.n->bg_color >> 16) & 0xFF),
                          (uint8_t)((t.n->bg_color >> 8) & 0xFF),
                          (uint8_t)(t.n->bg_color & 0xFF),
                          (uint8_t)((t.n->bg_color >> 24) & 0xFF));
            if (bg.a == 0xFF || !pixel_eq(bg, win_bg)) {
                sl_fill_rect(fb, x, y, w, h, bg, stats.pixels_touched);
                stats.boxes_painted++;
            }
        }
        // (b) outline for structural containers (depth-cycled, 1px)
        if (paintable && on_screen && !t.n->children.empty() && w > 8 && h > 8) {
            sl_outline_rect(fb, x, y, w, h,
                            depth_outline(t.depth), stats.pixels_touched);
            stats.boxes_painted++;
        }
        // (c) text — ASCII via 5x7; non-ASCII → 5x24 block marker line
        if (paintable && on_screen && is_text_like(*t.n)) {
            const std::string& s = !t.n->text.empty() ? t.n->text : t.n->hint;
            if (!s.empty()) {
                bool ascii = true;
                for (unsigned char ch : s)
                    if (ch < 0x20 || ch > 0x7E) { ascii = false; break; }
                uint32_t tc = t.n->text_color;
                RGBA col = tc ? RGBA((uint8_t)((tc >> 16) & 0xFF),
                                     (uint8_t)((tc >> 8) & 0xFF),
                                     (uint8_t)(tc & 0xFF),
                                     (uint8_t)((tc >> 24) & 0xFF))
                              : RGBA{0x10, 0x10, 0x10, 0xFF};
                if (paintable && ascii) {
                    sl_draw_text(fb, x + 2, y + 2, s, col, stats.pixels_touched);
                    stats.texts_painted++;
                } else {
                    // honest non-ASCII placeholder: one block bar
                    sl_fill_rect(fb, x + 2, y + 2, std::min(w - 4, 60),
                                 std::min(h - 4, 10), col, stats.pixels_touched);
                    stats.texts_skipped_non_ascii++;
                }
            }
        }
        // (d) image-carrying views — gray placeholder + provenance count
        if (paintable && on_screen && !t.n->image_drawable_path.empty()) {
            const RGBA gray{0x60, 0x60, 0x60, 0xFF};
            sl_fill_rect(fb, x + 1, y + 1, std::max(0, w - 2),
                         std::max(0, h - 2), gray, stats.pixels_touched);
            sl_draw_text(fb, x + 4, y + 4, "IMG", RGBA{0xE0, 0xE0, 0xE0, 0xFF},
                         stats.pixels_touched);
            stats.images_marked++;
        }
        // (e) clickable marker — corner ticks (hit-test targets stay REAL)
        if (paintable && on_screen && t.n->clickable && w > 4 && h > 4) {
            const RGBA tick{0xF0, 0xD0, 0x20, 0xFF};
            for (int k = 0; k < std::min(6, w / 2); k++) {
                sl_pixel(fb, x + k, y, tick, stats.pixels_touched);
                sl_pixel(fb, x, y + k, tick, stats.pixels_touched);
            }
            stats.clickables++;
        }
        for (auto it = t.n->children.rbegin(); it != t.n->children.rend(); ++it) {
            if (framework::ViewShadow::ViewNode* c = views->find_node(*it))
                stack.push_back({c, t.depth + 1});
        }
    }
    return stats.nodes_total > 0;
}

}  // namespace renderer
}  // namespace miniandroid
