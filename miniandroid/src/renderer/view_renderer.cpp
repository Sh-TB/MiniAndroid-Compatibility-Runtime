/* UNIFIED_007 EXP-122 — ViewRenderer implementation. */

#include "view_renderer.h"
#include "text_shaper.h"
#include "../apk/apk_parser.h"
#include <algorithm>
#include <cmath>
#include <functional>

namespace miniandroid {
namespace renderer {

using framework::ViewShadow;

static const int kGravityCenterV = 0x10;
static const int kGravityCenterH = 0x01;
static const int kGravityBottom = 0x50;
static const int kGravityRight = 0x05;

static RGBA argb(uint32_t c) {
    return RGBA{uint8_t((c >> 16) & 0xff), uint8_t((c >> 8) & 0xff),
                uint8_t(c & 0xff), uint8_t((c >> 24) & 0xff)};
}

ViewRenderer::ViewRenderer(ViewShadow* views, int screen_w, int screen_h)
    : views_(views), screen_w_(screen_w), screen_h_(screen_h) {}

bool ViewRenderer::is_linear(const ViewShadow::ViewNode& n) const {
    return n.class_desc.find("LinearLayout;") != std::string::npos ||
           n.class_desc.find("RadioGroup;") != std::string::npos ||
           n.class_desc.find("TableRow;") != std::string::npos;
}
bool ViewRenderer::is_relative(const ViewShadow::ViewNode& n) const {
    return n.class_desc.find("RelativeLayout;") != std::string::npos;
}
bool ViewRenderer::is_scroll(const ViewShadow::ViewNode& n) const {
    return n.class_desc.find("ScrollView;") != std::string::npos ||
           n.class_desc.find("HorizontalScrollView;") != std::string::npos;
}
bool ViewRenderer::is_frame(const ViewShadow::ViewNode& n) const {
    return n.class_desc.find("FrameLayout;") != std::string::npos ||
           n.class_desc.find("CoordinatorLayout;") != std::string::npos ||
           n.class_desc.find("AppBarLayout;") != std::string::npos ||
           n.class_desc.find("ConstraintLayout;") != std::string::npos;
}
bool ViewRenderer::is_image(const ViewShadow::ViewNode& n) const {
    return n.class_desc.find("ImageView;") != std::string::npos ||
           n.class_desc.find("ImageButton;") != std::string::npos;
}
bool ViewRenderer::is_edit_text(const ViewShadow::ViewNode& n) const {
    return n.class_desc.find("EditText;") != std::string::npos;
}

static bool is_text_like(const ViewShadow::ViewNode& n) {
    return n.class_desc.find("TextView;") != std::string::npos ||
           n.class_desc.find("Button;") != std::string::npos ||
           n.class_desc.find("EditText;") != std::string::npos ||
           n.class_desc.find("CheckBox;") != std::string::npos ||
           n.class_desc.find("RadioButton;") != std::string::npos ||
           n.class_desc.find("Switch;") != std::string::npos;
}

// ---------------------------------------------------------------------------
// Measure
// ---------------------------------------------------------------------------
ViewRenderer::Box ViewRenderer::measure_view(ViewShadow::ViewNode& n,
                                             int avail_w, int avail_h) {
    stats_.laid_out++;
    Box b{0, 0, 0, 0};
    b.w = (n.lp_width == -1) ? avail_w
          : (n.lp_width >= 0) ? n.lp_width
                              : avail_w;  // WRAP/INT_MIN refined below
    b.h = (n.lp_height == -1) ? avail_h
          : (n.lp_height >= 0) ? n.lp_height
                               : avail_h;
    bool wrap_w = n.lp_width == -2;
    bool wrap_h = n.lp_height == -2;

    if (wrap_w || wrap_h) {
        if (is_image(n) && !n.image_drawable_path.empty()) {
            auto it = bitmap_cache_.find(n.image_drawable_path);
            if (it != bitmap_cache_.end() && !it->second.rgba.empty()) {
                float bucket = 1.f;
                const std::string& p = n.image_drawable_path;
                if (p.find("-xxxhdpi") != std::string::npos) bucket = 4.f;
                else if (p.find("-xxhdpi") != std::string::npos) bucket = 3.f;
                else if (p.find("-xhdpi") != std::string::npos) bucket = 2.f;
                else if (p.find("-hdpi") != std::string::npos) bucket = 1.5f;
                float scale = 2.f / bucket;  // runtime density / asset bucket
                b.w = int(std::lround(it->second.width * scale)) + n.padding_l + n.padding_r;
                b.h = int(std::lround(it->second.height * scale)) + n.padding_t + n.padding_b;
            }
        } else if (is_text_like(n) || is_image(n)) {
            float ts = n.text_size_px > 0 ? n.text_size_px : 14.f * 2;
            std::string t = !n.text.empty() ? n.text : n.hint;
            if (wrap_w) {
                float tw = 0;
                if (!t.empty()) {
                    TextShaper::Options o;
                    o.size_px = ts;
                    o.bold = n.text_style_bold;
                    tw = TextShaper::instance().measure(t, o);
                }
                b.w = int(std::lround(tw)) + n.padding_l + n.padding_r + 2;
            }
            if (wrap_h) {
                TextShaper::Metrics m =
                    TextShaper::instance().metrics(ts, n.text_style_bold);
                b.h = int(std::lround(m.line_height)) + n.padding_t + n.padding_b + 8;
            }
        } else {
            // container wrap: sum children (single pass)
            int cw = 0, ch = 0;
            bool horiz = is_linear(n) && n.orientation == 0;
            for (uint32_t cid : n.children) {
                ViewShadow::ViewNode* c = views_->find_node(cid);
                if (!c || c->visibility == 8) continue;
                // Android: match_parent children inside a wrap_content
                // parent do not grow the parent (they resolve against its
                // final size afterwards). Treat them as 0 along the main
                // axis during the wrap measurement.
                int cmain = horiz ? c->lp_width : c->lp_height;
                if (cmain == -1 || c->layout_weight > 0) {
                    if (horiz) cw += 0;
                    else ch += 0;
                    continue;
                }
                Box cb = measure_view(*c, b.w, b.h);
                if (horiz) {
                    cw += cb.w + c->lp_margin_left + c->lp_margin_right;
                    ch = std::max(ch, cb.h + c->lp_margin_top + c->lp_margin_bottom);
                } else {
                    ch += cb.h + c->lp_margin_top + c->lp_margin_bottom;
                    cw = std::max(cw, cb.w + c->lp_margin_left + c->lp_margin_right);
                }
            }
            if (wrap_w) b.w = cw + n.padding_l + n.padding_r;
            if (wrap_h) b.h = ch + n.padding_t + n.padding_b;
        }
    }
    if (avail_w > 0 && b.w > avail_w) b.w = avail_w;
    if (avail_h > 0 && b.h > avail_h && n.lp_height != -1) b.h = avail_h;
    return b;
}

// ---------------------------------------------------------------------------
// Layout children
// ---------------------------------------------------------------------------
void ViewRenderer::layout_children_linear(ViewShadow::ViewNode& n, const Box& b) {
    bool horiz = n.orientation == 0;
    int content_w = b.w - n.padding_l - n.padding_r;
    int content_h = b.h - n.padding_t - n.padding_b;

    struct Entry {
        ViewShadow::ViewNode* v;
        Box box;
    };
    std::vector<Entry> entries;
    for (uint32_t cid : n.children) {
        ViewShadow::ViewNode* c = views_->find_node(cid);
        if (!c || c->visibility == 8) continue;
        entries.push_back({c, Box{0, 0, 0, 0}});
    }

    // Pass 1: fixed sizes
    int fixed_size = 0;
    for (auto& e : entries) {
        ViewShadow::ViewNode& c = *e.v;
        if (horiz) {
            if (c.lp_width >= 0) e.box.w = c.lp_width;
            else if (c.lp_width == -2 || c.lp_width == INT_MIN) {
                e.box.w = measure_view(c, content_w, content_h).w;
            } else e.box.w = 0;  // weighted
            if (c.lp_height == -1) e.box.h = content_h;
            else if (c.lp_height >= 0) e.box.h = c.lp_height;
            else e.box.h = measure_view(c, e.box.w > 0 ? e.box.w : content_w, content_h).h;
            if (e.box.w > 0) fixed_size += e.box.w + c.lp_margin_left + c.lp_margin_right;
        } else {
            if (c.lp_height >= 0) e.box.h = c.lp_height;
            else if (c.lp_height == -2 || c.lp_height == INT_MIN) {
                e.box.h = measure_view(c, content_w, content_h).h;
            } else e.box.h = 0;
            if (c.lp_width == -1) e.box.w = content_w;
            else if (c.lp_width >= 0) e.box.w = c.lp_width;
            else e.box.w = measure_view(c, content_w, e.box.h > 0 ? e.box.h : content_h).w;
            if (e.box.h > 0) fixed_size += e.box.h + c.lp_margin_top + c.lp_margin_bottom;
        }
    }

    // Pass 2: weighted children share the remaining free space
    // proportionally to layout_weight (Android: width/height=0dp + weight).
    float weight_sum = 0;
    for (auto& e : entries) {
        ViewShadow::ViewNode& c = *e.v;
        if ((horiz && c.lp_width == -1) || (!horiz && c.lp_height == -1))
            weight_sum += c.layout_weight > 0 ? c.layout_weight : 1;
        else if ((horiz && c.lp_width == 0 && c.layout_weight > 0) ||
                 (!horiz && c.lp_height == 0 && c.layout_weight > 0))
            weight_sum += c.layout_weight;
    }
    int free_space = (horiz ? content_w : content_h) - fixed_size;
    free_space = std::max(0, free_space);
    float unit = weight_sum > 0 ? float(free_space) / weight_sum : 0;

    int cursor = horiz ? n.padding_l : n.padding_t;
    int cursor_pre = horiz ? n.padding_l : n.padding_t;
    (void)cursor_pre;
    for (auto& e : entries) {
        ViewShadow::ViewNode& c = *e.v;
        int ml = c.lp_margin_left, mr = c.lp_margin_right;
        int mt = c.lp_margin_top, mb = c.lp_margin_bottom;
        // weighted share for this child
        float my_weight = 0;
        if (horiz && ((c.lp_width == -1) || (c.lp_width == 0 && c.layout_weight > 0)))
            my_weight = c.layout_weight > 0 ? c.layout_weight : 1;
        if (!horiz && ((c.lp_height == -1) || (c.lp_height == 0 && c.layout_weight > 0)))
            my_weight = c.layout_weight > 0 ? c.layout_weight : 1;
        if (horiz) {
            if (my_weight > 0 && weight_sum > 0)
                e.box.w = int(std::lround(float(free_space) * my_weight / weight_sum)) - ml - mr;
            e.box.w = std::max(0, e.box.w);
            e.box.h = std::min(e.box.h, std::max(0, content_h));
            e.box.x = cursor + ml;
            int y = n.padding_t + mt;
            int g = c.layout_gravity >= 0 ? c.layout_gravity : n.gravity;
            if (g & kGravityCenterV) y = n.padding_t + (content_h - e.box.h) / 2;
            else if (g & kGravityBottom) y = n.padding_t + content_h - e.box.h - mb;
            e.box.y = y;
            cursor += e.box.w + ml + mr;
        } else {
            if (my_weight > 0 && weight_sum > 0)
                e.box.h = int(std::lround(float(free_space) * my_weight / weight_sum)) - mt - mb;
            e.box.h = std::max(0, e.box.h);
            e.box.w = std::min(e.box.w, std::max(0, content_w));
            e.box.y = cursor + mt;
            int x = n.padding_l + ml;
            int g = c.layout_gravity >= 0 ? c.layout_gravity : n.gravity;
            if (g & kGravityCenterH) x = n.padding_l + (content_w - e.box.w) / 2;
            else if (g & kGravityRight) x = n.padding_l + content_w - e.box.w - mr;
            e.box.x = x;
            cursor += e.box.h + mt + mb;
        }
        c.x = b.x + e.box.x;
        c.y = b.y + e.box.y;
        c.width = e.box.w;
        c.height = e.box.h;
        Box cb{c.x, c.y, c.width, c.height};
        if (is_linear(c)) layout_children_linear(c, cb);
        else if (is_relative(c)) layout_children_relative(c, cb);
        else layout_children_frame(c, cb);
    }
}

void ViewRenderer::layout_children_relative(ViewShadow::ViewNode& n, const Box& b) {
    int content_w = b.w - n.padding_l - n.padding_r;
    int content_h = b.h - n.padding_t - n.padding_b;
    for (uint32_t cid : n.children) {
        ViewShadow::ViewNode* c = views_->find_node(cid);
        if (!c || c->visibility == 8) continue;
        Box cb = measure_view(*c, content_w, content_h);
        int x = n.padding_l, y = n.padding_t;
        int g = c->layout_gravity >= 0 ? c->layout_gravity : n.gravity;
        if (c->rel_parent_right && c->rel_parent_bottom) {
            x = n.padding_l + content_w - cb.w - c->lp_margin_right;
            y = n.padding_t + content_h - cb.h - c->lp_margin_bottom;
        } else if (c->rel_parent_bottom) {
            y = n.padding_t + content_h - cb.h - c->lp_margin_bottom;
            if (g & kGravityCenterH) x = n.padding_l + (content_w - cb.w) / 2;
        } else if (c->rel_parent_top) {
            y = n.padding_t + c->lp_margin_top;
            if (g & kGravityCenterH) x = n.padding_l + (content_w - cb.w) / 2;
        } else if (c->rel_center) {
            x = n.padding_l + (content_w - cb.w) / 2;
            y = n.padding_t + (content_h - cb.h) / 2;
        } else if (c->rel_center_h) {
            x = n.padding_l + (content_w - cb.w) / 2;
        } else if (c->rel_center_v) {
            y = n.padding_t + (content_h - cb.h) / 2;
        } else {
            y = n.padding_t + c->lp_margin_top;
        }
        c->x = b.x + x;
        c->y = b.y + y;
        c->width = cb.w;
        c->height = cb.h;
        Box nb{c->x, c->y, c->width, c->height};
        if (is_linear(*c)) layout_children_linear(*c, nb);
        else if (is_relative(*c)) layout_children_relative(*c, nb);
        else layout_children_frame(*c, nb);
    }
}

void ViewRenderer::layout_children_frame(ViewShadow::ViewNode& n, const Box& b) {
    int content_w = b.w - n.padding_l - n.padding_r;
    int content_h = b.h - n.padding_t - n.padding_b;
    for (uint32_t cid : n.children) {
        ViewShadow::ViewNode* c = views_->find_node(cid);
        if (!c || c->visibility == 8) continue;
        Box cb = measure_view(*c, content_w, content_h);
        int x = n.padding_l + c->lp_margin_left;
        int y = n.padding_t + c->lp_margin_top;
        int g = c->layout_gravity >= 0 ? c->layout_gravity
                : c->gravity >= 0 ? c->gravity : n.gravity;
        if (g & kGravityCenterH) x = n.padding_l + (content_w - cb.w) / 2;
        else if (g & kGravityRight) x = n.padding_l + content_w - cb.w - c->lp_margin_right;
        if (g & kGravityCenterV) y = n.padding_t + (content_h - cb.h) / 2;
        else if (g & kGravityBottom) y = n.padding_t + content_h - cb.h - c->lp_margin_bottom;
        c->x = b.x + x;
        c->y = b.y + y;
        c->width = cb.w;
        c->height = cb.h;
        Box nb{c->x, c->y, c->width, c->height};
        if (is_linear(*c)) layout_children_linear(*c, nb);
        else if (is_relative(*c)) layout_children_relative(*c, nb);
        else layout_children_frame(*c, nb);
    }
}

int ViewRenderer::layout(uint32_t root_id) {
    stats_ = Stats{};
    ViewShadow::ViewNode* root = views_->find_node(root_id);
    if (!root) return 0;
    root->x = 0;
    root->y = 0;
    root->width = root->lp_width >= 0 ? root->lp_width : screen_w_;
    root->height = root->lp_height >= 0 ? root->lp_height : screen_h_;
    Box b{0, 0, root->width, root->height};
    if (is_linear(*root)) layout_children_linear(*root, b);
    else if (is_relative(*root)) layout_children_relative(*root, b);
    else layout_children_frame(*root, b);
    return stats_.laid_out;
}

// ---------------------------------------------------------------------------
// Draw
// ---------------------------------------------------------------------------
static void fill_rect(FrameBuffer& fb, int x, int y, int w, int h, RGBA c) {
    for (int row = std::max(0, y); row < std::min(int(fb.get_height()), y + h); ++row)
        for (int col = std::max(0, x); col < std::min(int(fb.get_width()), x + w); ++col)
            fb.set_pixel(col, row, c);
}

static void fill_round_rect(FrameBuffer& fb, int x, int y, int w, int h,
                            float r, RGBA c) {
    int ri = int(std::lround(r));
    if (ri <= 0) { fill_rect(fb, x, y, w, h, c); return; }
    ri = std::min(ri, std::min(w, h) / 2);
    for (int row = 0; row < h; ++row)
        for (int col = 0; col < w; ++col) {
            int dx = col < ri ? ri - col : (col >= w - ri ? col - (w - ri - 1) : 0);
            int dy = row < ri ? ri - row : (row >= h - ri ? row - (h - ri - 1) : 0);
            if (dx > 0 && dy > 0) {
                int d2 = (ri - dx) * (ri - dx) + (ri - dy) * (ri - dy);
                if (d2 > ri * ri) continue;
            }
            fb.set_pixel(x + col, y + row, c);
        }
}

static void blit_image(FrameBuffer& fb, const DecodedImage& img, int dx, int dy,
                       int dw, int dh, int& images_drawn) {
    if (img.rgba.empty() || img.width <= 0 || img.height <= 0 || dw <= 0 || dh <= 0)
        return;
    float sx = float(img.width) / dw;
    float sy = float(img.height) / dh;
    for (int row = 0; row < dh; ++row)
        for (int col = 0; col < dw; ++col) {
            int ix = std::min(img.width - 1, int(col * sx));
            int iy = std::min(img.height - 1, int(row * sy));
            size_t o = (size_t(iy) * img.width + ix) * 4;
            RGBA c{img.rgba[o], img.rgba[o + 1], img.rgba[o + 2], img.rgba[o + 3]};
            fb.set_pixel(dx + col, dy + row, c);
        }
    images_drawn++;
}

bool ViewRenderer::decode_into(const std::string& zip_path, apk::ApkParser& apk) {
    auto& entry = bitmap_cache_[zip_path];
    if (!entry.rgba.empty()) return true;
    auto bytes = apk.extract_entry_cached(zip_path);
    if (bytes.empty()) return false;
    DecodedImage d;
    if (bytes.size() >= 8 && bytes[0] == 0x89 && bytes[1] == 'P') {
        d = PNGDecoder::decode(bytes);
    } else if (bytes.size() >= 12 && bytes[0] == 'R' && bytes[1] == 'I') {
        d = WebPDecoder::decode(bytes);
    } else if (bytes.size() >= 2 && bytes[0] == 0xFF && bytes[1] == 0xD8) {
        d = JPEGDecoder::decode(bytes);
    }
    if (d.rgba.empty()) return false;
    entry = std::move(d);
    return true;
}

void ViewRenderer::preload_bitmaps(uint32_t root_id, apk::ApkParser& apk) {
    std::function<void(uint32_t)> walk = [&](uint32_t id) {
        ViewShadow::ViewNode* n = views_->find_node(id);
        if (!n) return;
        if (!n->image_drawable_path.empty())
            decode_into(n->image_drawable_path, apk);
        if (!n->bg_drawable_path.empty())
            decode_into(n->bg_drawable_path, apk);
        for (uint32_t cid : n->children) walk(cid);
    };
    walk(root_id);
}

void ViewRenderer::draw_text_into(ViewShadow::ViewNode& n, FrameBuffer& fb,
                                  int left, int top, int w, int h) {
    std::string t = !n.text.empty() ? n.text : n.hint;
    if (t.empty()) return;
    float ts = n.text_size_px > 0 ? n.text_size_px : 28.f;
    RGBA col{0, 0, 0, 255};
    if (n.text_color) {
        col = argb(n.text_color);
    } else if (n.class_desc.find("Button;") != std::string::npos &&
               n.class_desc.find("ImageButton;") == std::string::npos) {
        col = RGBA{0xff, 0xff, 0xff, 0xff};  // button label default
    }
    TextShaper::Options o;
    o.size_px = ts;
    o.bold = n.text_style_bold;
    TextShaper::Metrics m = TextShaper::instance().metrics(ts, n.text_style_bold);
    int pen_y = top + int(std::lround(m.ascent)) + n.padding_t;
    float tw = TextShaper::instance().measure(t, o);
    int pen_x = left + n.padding_l;
    int g = n.text_gravity ? n.text_gravity : (n.gravity >= 0 ? n.gravity : 0);
    bool is_btn = n.class_desc.find("Button;") != std::string::npos &&
                  n.class_desc.find("ImageButton;") == std::string::npos;
    if (is_btn && !n.text_gravity && n.gravity < 0)
        g = kGravityCenterH | 0x10;  // Android Button default: center both
    if (g & kGravityCenterH) pen_x = left + (w - int(tw)) / 2;
    else if (g & kGravityRight) pen_x = left + w - int(tw) - n.padding_r;
    if (g & kGravityCenterV || (is_btn && !n.text_gravity && n.gravity < 0))
        pen_y = top + (h - int(m.line_height)) / 2 + int(m.ascent);

    auto& sh = TextShaper::instance();
    auto runs = sh.shape(t, o);
    if (runs.empty()) {
        stats_.texts_bitmap_fallback++;
        SoftwareCanvas cv(&fb);
        cv.draw_text(t, float(pen_x), float(pen_y), col, nullptr);
        return;
    }
    stats_.texts_shaped++;
    float pen = float(pen_x);
    for (const auto& gr : runs) {
        if (!gr.coverage.empty()) {
            for (unsigned r = 0; r < gr.bmp_h; ++r)
                for (unsigned c = 0; c < gr.bmp_w; ++c) {
                    uint8_t a = gr.coverage[size_t(r) * gr.bmp_w + c];
                    if (!a) continue;
                    RGBA px = col;
                    px.a = a;
                    fb.set_pixel(pen + gr.x_offset + gr.bmp_left + int(c),
                                 pen_y - gr.bmp_top + int(r), px);
                }
        }
        pen += gr.x_advance;
    }
}

void ViewRenderer::draw_view(ViewShadow::ViewNode& n, FrameBuffer& fb,
                             const RGBA& window_bg) {
    if (n.visibility != 0) return;  // INVISIBLE(4)/GONE(8) skipped
    int w = std::max(0, n.width), h = std::max(0, n.height);

    bool have_bg = false;
    RGBA bg{0, 0, 0, 255};
    if (n.bg_color) { bg = argb(n.bg_color); have_bg = bg.a > 0; }
    else if (n.bg_shape_has_solid) {
        bg = argb(n.bg_shape_solid);
        have_bg = bg.a > 0;  // fully-transparent shape = no visible background
    } else if (n.parent_id == 0) { bg = window_bg; have_bg = true; }

    if (n.bg_shape_has_gradient && w > 0 && h > 0) {
        RGBA g0 = argb(n.bg_shape_grad_start), g1 = argb(n.bg_shape_grad_end);
        double ang = (n.bg_shape_grad_angle % 360) * 3.14159265 / 180.0;
        float cx = w / 2.f, cy = h / 2.f;
        float denom = std::max(1.f, std::abs(w * float(std::cos(ang))) +
                                        std::abs(h * float(std::sin(ang))));
        for (int row = 0; row < h; ++row)
            for (int col = 0; col < w; ++col) {
                float t = 0.5f + 0.5f * ((col - cx) * float(std::cos(ang)) +
                                         (row - cy) * float(std::sin(ang))) / denom;
                t = std::min(1.f, std::max(0.f, t));
                RGBA c{uint8_t(g0.r * (1 - t) + g1.r * t),
                       uint8_t(g0.g * (1 - t) + g1.g * t),
                       uint8_t(g0.b * (1 - t) + g1.b * t),
                       uint8_t(g0.a * (1 - t) + g1.a * t)};
                fb.set_pixel(n.x + col, n.y + row, c);
            }
        stats_.bg_shapes_drawn++;
    } else if (have_bg && n.bg_shape_corner_radius > 0) {
        fill_round_rect(fb, n.x, n.y, w, h, n.bg_shape_corner_radius, bg);
        stats_.bg_shapes_drawn++;
    } else if (have_bg && w > 0 && h > 0) {
        fill_rect(fb, n.x, n.y, w, h, bg);
    }
    if (n.bg_shape_has_stroke && w > 0 && h > 0) {
        RGBA sc = argb(n.bg_shape_stroke_color);
        int sw = std::max(1, int(std::lround(n.bg_shape_stroke_width)));
        fill_rect(fb, n.x, n.y, w, sw, sc);
        fill_rect(fb, n.x, n.y + h - sw, w, sw, sc);
        fill_rect(fb, n.x, n.y, sw, h, sc);
        fill_rect(fb, n.x + w - sw, n.y, sw, h, sc);
    }

    // Button theme fallback: real Android draws a theme-provided button
    // background (framework resources are not shipped inside APKs). When the
    // APK defines none explicitly, approximate the Holo/Material default so
    // buttons remain visible (documented approximation, UNIFIED_007).
    bool is_button = n.class_desc.find("Button;") != std::string::npos &&
                     n.class_desc.find("ImageButton;") == std::string::npos;
    if (is_button && !have_bg && !n.bg_shape_has_solid &&
        !n.bg_shape_has_gradient && n.bg_drawable_path.empty() && w > 0 && h > 0) {
        fill_round_rect(fb, n.x, n.y, w, h, 6.f, RGBA{0x3a, 0x3f, 0x44, 0xff});
        RGBA rim{0x5a, 0x60, 0x66, 0xff};
        for (int i = 0; i < 2 && i < h; ++i)
            fill_rect(fb, n.x, n.y + i, w, 1, rim);
        stats_.bg_shapes_drawn++;
    }
    if (!n.bg_drawable_path.empty()) {
        auto& entry = bitmap_cache_[n.bg_drawable_path];
        if (!entry.rgba.empty()) {
            blit_image(fb, entry, n.x, n.y, w, h, stats_.images_drawn);
            stats_.bg_bitmaps_drawn++;
        }
    }

    stats_.drawn++;

    if (is_image(n) && !n.image_drawable_path.empty()) {
        auto& entry = bitmap_cache_[n.image_drawable_path];
        if (!entry.rgba.empty()) {
            blit_image(fb, entry, n.x + n.padding_l, n.y + n.padding_t,
                       std::max(1, w - n.padding_l - n.padding_r),
                       std::max(1, h - n.padding_t - n.padding_b), stats_.images_drawn);
        }
    }

    if (is_edit_text(n) && w > 0 && h > 0) {
        RGBA line{128, 128, 128, 255};
        fill_rect(fb, n.x + n.padding_l, n.y + h - 2,
                  std::max(1, w - n.padding_l - n.padding_r), 2, line);
    }

    if (!n.anim_frame_rgba.empty() && n.anim_w > 0 && n.anim_h > 0) {
        DecodedImage di;
        di.width = n.anim_w;
        di.height = n.anim_h;
        di.rgba = n.anim_frame_rgba;
        blit_image(fb, di, n.x, n.y, std::min(n.anim_w, std::max(1, w)),
                   std::min(n.anim_h, std::max(1, h)), stats_.images_drawn);
    } else {
        draw_text_into(n, fb, n.x, n.y, w, h);
    }

    for (uint32_t cid : n.children) {
        ViewShadow::ViewNode* c = views_->find_node(cid);
        if (c) draw_view(*c, fb, window_bg);
    }
}

bool ViewRenderer::render_png(uint32_t root_id, const std::string& path,
                              const RGBA& window_bg) {
    ViewShadow::ViewNode* root = views_->find_node(root_id);
    if (!root) return false;
    if (root->width <= 0) layout(root_id);
    FrameBuffer fb(screen_w_, screen_h_);
    fb.clear(RGBA{255, 255, 255, 255});
    draw_view(*root, fb, window_bg);
    int nonwhite = 0;
    for (int y = 0; y < screen_h_; y += 4)
        for (int x = 0; x < screen_w_; x += 4) {
            RGBA c = fb.get_pixel(x, y);
            if (!(c.r == 255 && c.g == 255 && c.b == 255)) nonwhite++;
        }
    stats_.nonwhite_pixels = nonwhite * 16;
    return PNGWriter::write_png(path, fb);
}

uint32_t ViewRenderer::hit_test(uint32_t root_id, int x, int y) const {
    uint32_t best_clickable = 0, best_any = 0;
    std::function<void(uint32_t)> walk = [&](uint32_t id) {
        ViewShadow::ViewNode* n = views_->find_node(id);
        if (!n || n->visibility != 0) return;
        if (x >= n->x && x < n->x + std::max(1, n->width) && y >= n->y &&
            y < n->y + std::max(1, n->height)) {
            if (!best_any) best_any = id;
            // GOLDEN-02: AOSP View touchability law — a view is a touch
            // target when it is CLICKABLE or LONG_CLICKABLE
            // (View.java: setOnLongClickListener sets LONG_CLICKABLE;
            // onTouchEvent handles press sequences for either flag).
            // The legacy predicate only covered clickable, so a view with
            // ONLY a long-click listener (the AOSP-legal pattern in the
            // EXT-01 fixture) was invisible to hit testing.
            bool clickable = n->clickable || !n->on_click_method.empty() ||
                             n->click_listener_id != 0 ||
                             !n->click_listener_class.empty() ||
                             n->long_click_listener_id != 0;
            if (clickable) best_clickable = id;
            for (uint32_t cid : n->children) walk(cid);
        }
    };
    walk(root_id);
    return best_clickable ? best_clickable : best_any;
}

nlohmann::json ViewRenderer::layout_dump(uint32_t root_id) const {
    std::function<void(uint32_t, nlohmann::json&)> walk = [&](uint32_t id,
                                                              nlohmann::json& out) {
        ViewShadow::ViewNode* n = views_->find_node(id);
        if (!n) {
            out = nullptr;
            return;
        }
        out = {
            {"id", id},
            {"class", n->class_desc},
            {"android_id", n->android_view_id},
            {"x", n->x}, {"y", n->y}, {"w", n->width}, {"h", n->height},
            {"text", n->text},
            {"text_size_px", n->text_size_px},
            {"text_color", n->text_color},
            {"bg_color", n->bg_color},
            {"bg_drawable", n->bg_drawable_path},
            {"image", n->image_drawable_path},
            {"onClick", n->on_click_method},
            {"clickable", n->clickable || !n->on_click_method.empty()},
            {"visibility", n->visibility},
        };
        out["children"] = nlohmann::json::array();
        for (uint32_t cid : n->children) {
            nlohmann::json cj;
            walk(cid, cj);
            out["children"].push_back(cj);
        }
    };
    nlohmann::json out;
    walk(root_id, out);
    return out;
}

}  // namespace renderer
}  // namespace miniandroid
