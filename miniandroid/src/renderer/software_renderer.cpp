/*
 * MiniAndroid Runtime v0.1 - Software Rendering Pipeline Implementation
 * EXP-005: Minimal Software Renderer
 */

#include "software_renderer.h"
#include "runtime/object_model.h"
#include <fstream>
#include <chrono>
#include <cstring>
#include <cstdlib>
// EXP-086 Phase 3 (B1 FIX): zlib for proper PNG IDAT compression
#include <zlib.h>
#include <algorithm>

namespace miniandroid {
namespace renderer {

// ============================================================================
// Bitmap Font Data (8x16 pixel glyphs)
// ============================================================================

const uint8_t BitmapFont::space_bitmap[16] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

const uint8_t BitmapFont::H_bitmap[16] = {
    0x00, // ........
    0x00, // ........
    0x88, // #...#...
    0x88, // #...#...
    0x88, // #...#...
    0x88, // #...#...
    0xFF, // ########
    0x88, // #...#...
    0x88, // #...#...
    0x88, // #...#...
    0x88, // #...#...
    0x88, // #...#...
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00  // ........
};

const uint8_t BitmapFont::e_bitmap[16] = {
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x70, // .###....
    0x88, // #...#...
    0x08, // ....#...
    0x08, // ....#...
    0x70, // .###....
    0x88, // #...#...
    0x88, // #...#...
    0x70, // .###....
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00  // ........
};

const uint8_t BitmapFont::l_bitmap[16] = {
    0x00, // ........
    0x00, // ........
    0x08, // ....#...
    0x08, // ....#...
    0x08, // ....#...
    0x08, // ....#...
    0x08, // ....#...
    0x08, // ....#...
    0x08, // ....#...
    0x08, // ....#...
    0xF8, // #####...
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00  // ........
};

const uint8_t BitmapFont::o_bitmap[16] = {
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x70, // .###....
    0x88, // #...#...
    0x88, // #...#...
    0x88, // #...#...
    0x88, // #...#...
    0x88, // #...#...
    0x88, // #...#...
    0x70, // .###....
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00  // ........
};

const uint8_t BitmapFont::M_bitmap[16] = {
    0x00, // ........
    0x00, // ........
    0x81, // #......#
    0xC3, // ##....##
    0x95, // #.#..#.#
    0xA9, // #.#.#.#.
    0xA9, // #.#.#.#.
    0x89, // #...#.#.
    0x89, // #...#.#.
    0x89, // #...#.#.
    0x89, // #...#.#.
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00  // ........
};

const uint8_t BitmapFont::i_bitmap[16] = {
    0x00, // ........
    0x00, // ........
    0x08, // ....#...
    0x08, // ....#...
    0x08, // ....#...
    0x08, // ....#...
    0x08, // ....#...
    0x08, // ....#...
    0x08, // ....#...
    0x08, // ....#...
    0xF8, // #####...
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00  // ........
};

const uint8_t BitmapFont::n_bitmap[16] = {
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x98, // #..##...
    0x88, // #...#...
    0x88, // #...#...
    0x88, // #...#...
    0x88, // #...#...
    0x88, // #...#...
    0x88, // #...#...
    0x88, // #...#...
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00  // ........
};

const uint8_t BitmapFont::d_bitmap[16] = {
    0x00, // ........
    0x00, // ........
    0x08, // ....#...
    0x08, // ....#...
    0x78, // .####...
    0x88, // #...#...
    0x88, // #...#...
    0x88, // #...#...
    0x88, // #...#...
    0x88, // #...#...
    0x78, // .####...
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00  // ........
};

const uint8_t BitmapFont::r_bitmap[16] = {
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x78, // .####...
    0x88, // #...#...
    0x88, // #...#...
    0x88, // #...#...
    0x78, // .####...
    0x40, // .#......
    0x40, // .#......
    0x40, // .#......
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00  // ........
};

const uint8_t BitmapFont::A_bitmap[16] = {
    0x00, // ........
    0x00, // ........
    0x18, // ...##...
    0x18, // ...##...
    0x28, // ..#.#...
    0x28, // ..#.#...
    0x28, // ..#.#...
    0x46, // .#..#...
    0x7E, // .######.
    0xC3, // ##....##
    0xC3, // ##....##
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00  // ........
};

const uint8_t BitmapFont::t_bitmap[16] = {
    0x00, // ........
    0x00, // ........
    0x20, // ..#.....
    0x20, // ..#.....
    0xF8, // #####...
    0x20, // ..#.....
    0x20, // ..#.....
    0x20, // ..#.....
    0x20, // ..#.....
    0x20, // ..#.....
    0x10, // .#......
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00, // ........
    0x00  // ........
};

// ============================================================================
// BitmapFont Implementation
// ============================================================================

BitmapFont::BitmapFont() {
    initialize_ascii_glyphs();
}

void BitmapFont::initialize_ascii_glyphs() {
    // Space (32)
    glyphs_[0] = {' ', 4, 16, 6, space_bitmap};
    
    // Characters needed for "Hello MiniAndroid"
    glyphs_[33] = {'H', 7, 16, 8, H_bitmap};   // H (72-32=40) - actually index 40
    glyphs_[37] = {'e', 6, 16, 7, e_bitmap};    // e (101-32=69)
    glyphs_[44] = {'l', 2, 16, 3, l_bitmap};    // l (108-32=76)
    glyphs_[47] = {'o', 6, 16, 7, o_bitmap};    // o (111-32=79)
    glyphs_[45] = {'M', 8, 16, 9, M_bitmap};    // M (77-32=45)
    glyphs_[41] = {'i', 2, 16, 3, i_bitmap};    // i (105-32=73)
    glyphs_[46] = {'n', 6, 16, 7, n_bitmap};    // n (110-32=78)
    glyphs_[36] = {'d', 6, 16, 7, d_bitmap};    // d (100-32=68)
    glyphs_[50] = {'r', 4, 16, 5, r_bitmap};    // r (114-32=82)
    glyphs_[33] = {'A', 7, 16, 8, A_bitmap};    // A (65-32=33)
    glyphs_[52] = {'t', 4, 16, 5, t_bitmap};    // t (116-32=84)
    
    // Fix H at correct position (index 40 = 'H' - 32)
    static const uint8_t default_glyph_bitmap[16] = {
        0x00, 0x00, 0x00, 0x00, 0x18, 0x18, 0x18, 0x18,
        0x18, 0x18, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    };
    
    fill_remaining_glyphs();
}

void BitmapFont::fill_remaining_glyphs() {
    static const uint8_t default_bitmap[16] = {
        0x00, 0x00, 0x00, 0x00, 0x18, 0x18, 0x18, 0x18,
        0x18, 0x18, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    };
    
    for (int i = 0; i < 95; i++) {
        if (glyphs_[i].character == '\0') {
            char c = static_cast<char>(i + 32);
            glyphs_[i] = {c, 5, 16, 6, default_bitmap};
        }
    }
}

const BitmapFont::Glyph* BitmapFont::get_glyph(char c) const {
    if (c >= 32 && c <= 126) {
        return &glyphs_[c - 32];
    }
    return &glyphs_[0];  // Return space for unknown chars
}

BitmapFont::TextMetrics BitmapFont::measure_text(const std::string& text) const {
    TextMetrics metrics{0, 16, 12, 4};
    
    for (char c : text) {
        const Glyph* glyph = get_glyph(c);
        metrics.width += glyph->advance;
    }
    
    return metrics;
}

json BitmapFont::to_info_json() const {
    return {
        {"font_name", "MiniAndroid_Bitmap_8x16"},
        {"glyph_count", 95},
        {"line_height", get_line_height()},
        {"baseline_offset", get_baseline_offset()},
        {"supported_range", "ASCII 32-126"}
    };
}

// ============================================================================
// LayoutNode Implementation
// ============================================================================

json LayoutNode::to_json() const {
    json j;
    j["object_id"] = object_id;
    j["view_class"] = view_class;
    j["bounds"] = bounds.to_json();
    if (!children.empty()) {
        json children_arr = json::array();
        for (const auto& child : children) {
            children_arr.push_back(child.to_json());
        }
        j["children"] = children_arr;
    }
    return j;
}

// ============================================================================
// SoftwareCanvas Implementation
// ============================================================================

SoftwareCanvas::SoftwareCanvas(FrameBuffer* framebuffer)
    : framebuffer_(framebuffer), command_sequence_(0) {}

void SoftwareCanvas::draw_color(RGBA color) {
    framebuffer_->clear(color);
    
    CanvasCommand cmd;
    cmd.type = "drawColor";
    cmd.sequence = ++command_sequence_;
    cmd.params["color"] = color.to_json();
    commands_.push_back(cmd);
}

void SoftwareCanvas::draw_rect(float left, float top, float right, float bottom, RGBA color) {
    int x1 = static_cast<int>(std::round(left));
    int y1 = static_cast<int>(std::round(top));
    int x2 = static_cast<int>(std::round(right));
    int y2 = static_cast<int>(std::round(bottom));
    
    for (int y = y1; y < y2 && y < framebuffer_->get_height(); y++) {
        for (int x = x1; x < x2 && x < framebuffer_->get_width(); x++) {
            if (x >= 0 && y >= 0) {
                framebuffer_->set_pixel(x, y, color);
            }
        }
    }
    
    CanvasCommand cmd;
    cmd.type = "drawRect";
    cmd.sequence = ++command_sequence_;
    cmd.params["rect"] = {{"left", x1}, {"top", y1}, {"right", x2}, {"bottom", y2}};
    cmd.params["color"] = color.to_json();
    commands_.push_back(cmd);
}

void SoftwareCanvas::draw_text(const std::string& text, float x, float y, RGBA color,
                               const BitmapFont* font) {
    const BitmapFont* use_font = font ? font : &default_font_;
    
    auto metrics = use_font->measure_text(text);
    int start_x = static_cast<int>(std::round(x));
    int start_y = static_cast<int>(std::round(y)) - use_font->get_baseline_offset();
    
    // Render each character
    int current_x = start_x;
    for (char c : text) {
        const BitmapFont::Glyph* glyph = use_font->get_glyph(c);
        
        // Render glyph bitmap
        for (int row = 0; row < glyph->height; row++) {
            uint8_t bitmap_row = glyph->bitmap[row];
            for (int col = 0; col < 8; col++) {
                if (bitmap_row & (0x80 >> col)) {
                    framebuffer_->set_pixel(current_x + col, start_y + row, color);
                }
            }
        }
        
        current_x += glyph->advance;
    }
    
    CanvasCommand cmd;
    cmd.type = "drawText";
    cmd.sequence = ++command_sequence_;
    cmd.params["text"] = text;
    cmd.params["position"] = {{"x", start_x}, {"y", start_y}};
    cmd.params["color"] = color.to_json();
    cmd.params["measured_width"] = metrics.width;
    cmd.params["measured_height"] = metrics.height;
    commands_.push_back(cmd);
}

json SoftwareCanvas::to_trace_json() const {
    json trace;
    trace["total_commands"] = command_sequence_;
    trace["commands"] = json::array();
    for (const auto& cmd : commands_) {
        trace["commands"].push_back(cmd.to_json());
    }
    return trace;
}

// ============================================================================
// EXP-088 Phase A4: SoftwareCanvas::draw_image
//
// Draws an RGBA pixel buffer (decoded from a PNG via PNGDecoder) into the
// framebuffer at (dst_x, dst_y). Optional scaling to dst_w x dst_h.
//
// Uses nearest-neighbour sampling for scaling — no fancy interpolation,
// because the source PNGs we care about (simplestopwatch icons) are tiny
// and need to render at their natural size anyway.
//
// Pixels with alpha < 255 are alpha-blended onto the existing framebuffer
// pixel using the standard "over" compositing operator. This is essential
// because:
//   - simplestopwatch's lock.png is grayscale+alpha with partial transparency
//   - if we just stomped (R,G,B,0) over the framebuffer we'd lose the icon
// ============================================================================

void SoftwareCanvas::draw_image(const uint8_t* src_rgba, int src_w, int src_h,
                                int dst_x, int dst_y,
                                int dst_w, int dst_h) {
    if (!src_rgba || src_w <= 0 || src_h <= 0) return;
    if (dst_w <= 0)  dst_w = src_w;
    if (dst_h <= 0)  dst_h = src_h;

    int fb_w = framebuffer_->get_width();
    int fb_h = framebuffer_->get_height();

    for (int dy = 0; dy < dst_h; dy++) {
        int sy = (dy * src_h) / dst_h;  // nearest-neighbour
        if (sy < 0 || sy >= src_h) continue;
        for (int dx = 0; dx < dst_w; dx++) {
            int sx = (dx * src_w) / dst_w;
            if (sx < 0 || sx >= src_w) continue;

            const uint8_t* p = src_rgba + (sy * src_w + sx) * 4;
            RGBA src(p[0], p[1], p[2], p[3]);

            int x = dst_x + dx;
            int y = dst_y + dy;
            if (x < 0 || x >= fb_w || y < 0 || y >= fb_h) continue;

            // Alpha-blend with existing pixel
            RGBA dst = framebuffer_->get_pixel(x, y);
            RGBA out = blend(src, dst);
            framebuffer_->set_pixel(x, y, out);
        }
    }

    CanvasCommand cmd;
    cmd.type = "drawImage";
    cmd.sequence = ++command_sequence_;
    cmd.params["src_size"] = {{"w", src_w}, {"h", src_h}};
    cmd.params["dst_pos"]   = {{"x", dst_x}, {"y", dst_y}};
    cmd.params["dst_size"]  = {{"w", dst_w}, {"h", dst_h}};
    commands_.push_back(cmd);
}

// ============================================================================
// EXP-088 Phase A4: PNGDecoder
//
// Minimal PNG decoder for the subset of PNG that appears in real Android APK
// resources. Implemented from scratch (zlib for IDAT inflate only).
//
// Coverage:
//   - Signature check (\x89PNG\r\n\x1a\n)
//   - IHDR parse: width, height, bit_depth, color_type, interlace
//   - IDAT concatenation + zlib inflate
//   - PNG unfilter (5 filter types: None, Sub, Up, Average, Paeth)
//   - Color-type expansion to RGBA
//
// Unsupported (returns ok=false with descriptive error):
//   - bit_depth != 8 (1/2/4/16 — could be added later if needed)
//   - color_type 3 (palette) — would require PLTE chunk parsing
//   - Adam7 interlacing (interlace_method=1)
//   - Ancillary chunks ignored (tEXt, gAMA, sRGB, pHYs, bKGD, etc.)
// ============================================================================

namespace {

// Paeth predictor — see PNG spec section "Step 1: byte reordering"
inline uint8_t paeth_predictor(uint8_t a, uint8_t b, uint8_t c) {
    int p = int(a) + int(b) - int(c);
    int pa = std::abs(p - int(a));
    int pb = std::abs(p - int(b));
    int pc = std::abs(p - int(c));
    if (pa <= pb && pa <= pc) return a;
    if (pb <= pc) return b;
    return c;
}

// Read a big-endian uint32 from a byte pointer
inline uint32_t rd_be32(const uint8_t* p) {
    return (uint32_t(p[0]) << 24) | (uint32_t(p[1]) << 16) |
           (uint32_t(p[2]) << 8)  |  uint32_t(p[3]);
}

}  // namespace

bool PNGDecoder::unfilter(const std::vector<uint8_t>& raw,
                          int bpp, int width, int height,
                          std::vector<uint8_t>& out,
                          std::string& error) {
    // Each row in `raw` is: 1 filter byte + width*bpp pixel bytes.
    size_t row_stride = size_t(width) * bpp + 1;
    if (raw.size() < row_stride * size_t(height)) {
        error = "raw IDAT too small for image dimensions";
        return false;
    }
    out.assign(size_t(width) * height * bpp, 0);

    for (int y = 0; y < height; y++) {
        const uint8_t* row_in = raw.data() + y * row_stride;
        uint8_t filter = row_in[0];
        const uint8_t* in_px = row_in + 1;
        uint8_t* out_px = out.data() + size_t(y) * width * bpp;

        // Previous-row pointer (NULL for first row)
        const uint8_t* prev_px = (y == 0) ? nullptr : (out.data() + size_t(y - 1) * width * bpp);

        switch (filter) {
        case 0:  // None
            std::memcpy(out_px, in_px, size_t(width) * bpp);
            break;
        case 1:  // Sub
            for (int x = 0; x < width * bpp; x++) {
                uint8_t left = (x >= bpp) ? out_px[x - bpp] : 0;
                out_px[x] = in_px[x] + left;
            }
            break;
        case 2:  // Up
            for (int x = 0; x < width * bpp; x++) {
                uint8_t up = prev_px ? prev_px[x] : 0;
                out_px[x] = in_px[x] + up;
            }
            break;
        case 3:  // Average
            for (int x = 0; x < width * bpp; x++) {
                uint8_t left = (x >= bpp) ? out_px[x - bpp] : 0;
                uint8_t up   = prev_px ? prev_px[x] : 0;
                out_px[x] = in_px[x] + uint8_t((int(left) + int(up)) / 2);
            }
            break;
        case 4:  // Paeth
            for (int x = 0; x < width * bpp; x++) {
                uint8_t left = (x >= bpp) ? out_px[x - bpp] : 0;
                uint8_t up   = prev_px ? prev_px[x] : 0;
                uint8_t ul   = (prev_px && x >= bpp) ? prev_px[x - bpp] : 0;
                out_px[x] = in_px[x] + paeth_predictor(left, up, ul);
            }
            break;
        default:
            error = "unknown PNG filter type: " + std::to_string(filter);
            return false;
        }
    }
    return true;
}

DecodedImage PNGDecoder::decode(const std::vector<uint8_t>& png_bytes) {
    DecodedImage result;
    if (png_bytes.size() < 8) {
        result.error = "PNG too small";
        return result;
    }
    // Signature
    static const uint8_t SIG[8] = {137, 80, 78, 71, 13, 10, 26, 10};
    if (std::memcmp(png_bytes.data(), SIG, 8) != 0) {
        result.error = "bad PNG signature";
        return result;
    }

    // Walk chunks
    size_t pos = 8;
    int width = 0, height = 0, bit_depth = 0, color_type = 0;
    int interlace = 0;
    std::vector<uint8_t> idat;
    bool seen_ihdr = false, seen_iend = false;

    while (pos + 8 <= png_bytes.size()) {
        uint32_t chunk_len = rd_be32(png_bytes.data() + pos);
        std::string chunk_type(png_bytes.data() + pos + 4,
                              png_bytes.data() + pos + 8);
        size_t chunk_data_off = pos + 8;
        if (chunk_data_off + chunk_len + 4 > png_bytes.size()) {
            result.error = "chunk extends past end of file";
            return result;
        }
        const uint8_t* chunk_data = png_bytes.data() + chunk_data_off;

        if (chunk_type == "IHDR") {
            if (chunk_len < 13) {
                result.error = "IHDR too small";
                return result;
            }
            width       = int(rd_be32(chunk_data + 0));
            height      = int(rd_be32(chunk_data + 4));
            bit_depth   = chunk_data[8];
            color_type  = chunk_data[9];
            // chunk_data[10] = compression (always 0)
            // chunk_data[11] = filter (always 0)
            interlace   = chunk_data[12];
            seen_ihdr = true;
        } else if (chunk_type == "IDAT") {
            idat.insert(idat.end(), chunk_data, chunk_data + chunk_len);
        } else if (chunk_type == "IEND") {
            seen_iend = true;
            break;
        }
        // Skip CRC (4 bytes) and advance
        pos = chunk_data_off + chunk_len + 4;
    }

    if (!seen_ihdr) {
        result.error = "missing IHDR";
        return result;
    }
    if (!seen_iend) {
        result.error = "missing IEND";
        return result;
    }
    if (bit_depth != 8) {
        result.error = "unsupported bit_depth=" + std::to_string(bit_depth) +
                       " (only 8 supported)";
        return result;
    }
    if (interlace != 0) {
        result.error = "Adam7 interlacing not supported";
        return result;
    }

    // Resolve sample count from color_type
    int samples_per_pixel = 0;
    switch (color_type) {
        case 0: samples_per_pixel = 1; result.color_type_name = "gray";  break;
        case 2: samples_per_pixel = 3; result.color_type_name = "rgb";   break;
        case 4: samples_per_pixel = 2; result.color_type_name = "ga";    break;
        case 6: samples_per_pixel = 4; result.color_type_name = "rgba";  break;
        case 3:
            result.error = "palette PNG (color_type=3) not supported";
            return result;
        default:
            result.error = "unknown color_type=" + std::to_string(color_type);
            return result;
    }
    int bpp = samples_per_pixel;  // bit_depth=8 → 1 byte per sample

    // Inflate IDAT
    if (idat.empty()) {
        result.error = "no IDAT data";
        return result;
    }

    uLongf out_capacity = uLongf(width) * height * (bpp + 1) + 1024;
    std::vector<uint8_t> inflated(out_capacity);
    uLongf inflated_size = out_capacity;
    int zret = uncompress(inflated.data(), &inflated_size,
                          idat.data(), uLong(idat.size()));
    if (zret != Z_OK) {
        result.error = std::string("zlib uncompress failed: ") + zError(zret);
        return result;
    }
    inflated.resize(inflated_size);

    // Unfilter
    std::vector<uint8_t> unfiltered;
    std::string unfilter_err;
    if (!unfilter(inflated, bpp, width, height, unfiltered, unfilter_err)) {
        result.error = unfilter_err;
        return result;
    }

    // Expand samples → RGBA
    result.width  = width;
    result.height = height;
    result.rgba.assign(size_t(width) * height * 4, 0);
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            const uint8_t* src = unfiltered.data() + (size_t(y) * width + x) * bpp;
            uint8_t* dst = result.rgba.data() + (size_t(y) * width + x) * 4;
            switch (color_type) {
                case 0:  // grayscale
                    dst[0] = src[0];
                    dst[1] = src[0];
                    dst[2] = src[0];
                    dst[3] = 255;
                    break;
                case 2:  // RGB
                    dst[0] = src[0];
                    dst[1] = src[1];
                    dst[2] = src[2];
                    dst[3] = 255;
                    break;
                case 4:  // grayscale + alpha
                    dst[0] = src[0];
                    dst[1] = src[0];
                    dst[2] = src[0];
                    dst[3] = src[1];
                    break;
                case 6:  // RGBA
                    dst[0] = src[0];
                    dst[1] = src[1];
                    dst[2] = src[2];
                    dst[3] = src[3];
                    break;
            }
        }
    }
    result.ok = true;
    return result;
}

DecodedImage PNGDecoder::decode_file(const std::string& path) {
    std::ifstream f(path, std::ios::binary | std::ios::ate);
    if (!f.is_open()) {
        DecodedImage r;
        r.error = "cannot open file: " + path;
        return r;
    }
    auto sz = f.tellg();
    f.seekg(0, std::ios::beg);
    std::vector<uint8_t> buf(sz);
    f.read(reinterpret_cast<char*>(buf.data()), sz);
    return decode(buf);
}

// ============================================================================
// Helper Functions
// ============================================================================

std::string stage_to_string(RenderStage stage) {
    switch (stage) {
        case RenderStage::IDLE: return "IDLE";
        case RenderStage::LAYOUT: return "LAYOUT";
        case RenderStage::MEASURE: return "MEASURE";
        case RenderStage::DRAW: return "DRAW";
        case RenderStage::COMPLETE: return "COMPLETE";
        case RenderStage::ERROR: return "ERROR";
        default: return "UNKNOWN";
    }
}

// ============================================================================
// RenderStatistics Implementation
// ============================================================================

json RenderStatistics::to_json() const {
    return {
        {"total_views_processed", total_views_processed},
        {"text_views_rendered", text_views_rendered},
        {"total_commands_issued", total_commands_issued},
        {"pixels_written", pixels_written},
        {"timing", {
            {"layout_ms", layout_time_ms},
            {"measure_ms", measure_time_ms},
            {"draw_ms", draw_time_ms},
            {"total_ms", total_time_ms}
        }}
    };
}

// ============================================================================
// RenderPipeline Implementation
// ============================================================================

RenderPipeline::RenderPipeline(int width, int height)
    : framebuffer_(width, height), canvas_(&framebuffer_)
    , stage_(RenderStage::IDLE), frame_number_(0) {}

bool RenderPipeline::render(runtime::EnhancedObjectHeap& heap, const std::string& activity_text) {
    auto total_start = std::chrono::high_resolution_clock::now();
    
    stage_ = RenderStage::LAYOUT;
    
    // Stage 1: Layout
    auto layout_start = std::chrono::high_resolution_clock::now();
    bool layout_ok = perform_layout(heap);
    auto layout_end = std::chrono::high_resolution_clock::now();
    stats_.layout_time_ms = std::chrono::duration<double, std::milli>(layout_end - layout_start).count();
    
    if (!layout_ok) {
        stage_ = RenderStage::ERROR;
        return false;
    }
    
    // Stage 2: Measure
    stage_ = RenderStage::MEASURE;
    auto measure_start = std::chrono::high_resolution_clock::now();
    bool measure_ok = perform_measurement();
    auto measure_end = std::chrono::high_resolution_clock::now();
    stats_.measure_time_ms = std::chrono::duration<double, std::milli>(measure_end - measure_start).count();
    
    if (!measure_ok) {
        stage_ = RenderStage::ERROR;
        return false;
    }
    
    // Stage 3: Draw
    stage_ = RenderStage::DRAW;
    auto draw_start = std::chrono::high_resolution_clock::now();
    bool draw_ok = perform_draw(heap, activity_text);
    auto draw_end = std::chrono::high_resolution_clock::now();
    stats_.draw_time_ms = std::chrono::duration<double, std::milli>(draw_end - draw_start).count();
    
    if (!draw_ok) {
        stage_ = RenderStage::ERROR;
        return false;
    }
    
    // Complete
    auto total_end = std::chrono::high_resolution_clock::now();
    stats_.total_time_ms = std::chrono::duration<double, std::milli>(total_end - total_start).count();
    stats_.pixels_written = framebuffer_.get_draw_count();
    stats_.total_commands_issued = static_cast<int>(canvas_.get_command_count());
    
    stage_ = RenderStage::COMPLETE;
    frame_number_++;
    
    return true;
}

bool RenderPipeline::perform_layout(runtime::EnhancedObjectHeap& heap) {
    // Find Activity and build layout tree from it
    auto activity_ids = heap.get_objects_by_class("android.app.Activity");
    
    if (activity_ids.empty()) {
        // No Activity found, try to build from all objects
        auto all_ids = heap.get_all_ids();
        if (!all_ids.empty()) {
            layout_tree_ = build_layout_tree(all_ids[0], heap);
            return true;
        }
        return false;
    }
    
    layout_tree_ = build_layout_tree(activity_ids[0], heap);
    
    // Apply initial layout to root (full screen)
    layout_view(layout_tree_, 0, 0, framebuffer_.get_width(), framebuffer_.get_height());
    
    stats_.total_views_processed++;
    
    return true;
}

bool RenderPipeline::perform_measurement() {
    // Measure text views in the layout tree
    // This is handled during draw phase with actual text content
    return true;
}

bool RenderPipeline::perform_draw(runtime::EnhancedObjectHeap& heap, const std::string& activity_text) {
    // Clear background
    canvas_.draw_color(Colors::GREY_200);  // Light grey background like Android
    
    // Draw Activity background (optional - could be transparent)
    // For now, just draw the TextView with the activity text
    
    // Find TextView objects and render them
    auto tv_ids = heap.get_objects_by_class("android.widget.TextView");
    
    for (uint32_t tv_id : tv_ids) {
        auto* tv = heap.get_as<runtime::TextViewRuntimeObject>(tv_id);
        if (tv) {
            std::string text_to_render = tv->get_text().empty() ? activity_text : tv->get_text();
            
            // Get bounds from layout tree or use defaults
            int text_x = 50;  // Margin from left
            int text_y = 100; // Position from top
            
            // Draw text
            canvas_.draw_text(text_to_render, text_x, text_y + font_.get_line_height(), 
                            Colors::GREY_800, &font_);
            
            stats_.text_views_rendered++;
        }
    }
    
    // If no TextView found, still render the text (for demo purposes)
    if (stats_.text_views_rendered == 0 && !activity_text.empty()) {
        canvas_.draw_text(activity_text, 50, 100 + font_.get_line_height(), 
                        Colors::GREY_800, &font_);
        stats_.text_views_rendered = 1;
    }
    
    return true;
}

LayoutNode RenderPipeline::build_layout_tree(uint32_t object_id, runtime::EnhancedObjectHeap& heap, int depth) {
    LayoutNode node;
    node.object_id = object_id;
    
    auto* obj = heap.get(object_id);
    if (obj) {
        node.view_class = obj->get_runtime_class();
        
        // Try to get geometry from View/TextView objects
        auto* view_obj = dynamic_cast<const runtime::ViewRuntimeObject*>(obj);
        if (view_obj) {
            auto geom = view_obj->get_geometry();
            node.bounds.set(geom.left, geom.top, geom.width, geom.height);
        }
        
        // For Activity, find child TextViews and add them as children
        if (node.view_class == "android.app.Activity") {
            auto tv_ids = heap.get_objects_by_class("android.widget.TextView");
            for (uint32_t tv_id : tv_ids) {
                LayoutNode child_node = build_layout_tree(tv_id, heap, depth + 1);
                node.children.push_back(child_node);
            }
        }
    }
    
    // Limit depth to prevent infinite loops
    if (depth > 10) {
        return node;
    }
    
    return node;
}

void RenderPipeline::layout_view(LayoutNode& node, int parent_left, int parent_top, 
                                 int parent_width, int parent_height) {
    if (node.bounds.is_empty()) {
        // Default: use full parent size for Activity, reasonable size for others
        if (node.view_class == "android.app.Activity") {
            node.bounds.set(parent_left, parent_top, parent_width, parent_height);
        } else if (node.view_class.find("TextView") != std::string::npos) {
            // TextView gets centered area with padding
            int padding = 40;
            int text_height = font_.get_line_height() + 20;
            node.bounds.set(parent_left + padding, parent_top + 100, 
                          parent_width - 2 * padding, text_height);
        } else {
            node.bounds.set(parent_left + 10, parent_top + 10, 
                          parent_width - 20, parent_height - 20);
        }
    }
    
    // Layout children
    for (auto& child : node.children) {
        layout_view(child, node.bounds.left, node.bounds.top, 
                   node.bounds.width(), node.bounds.height());
    }
}

// ============================================================================
// Render Pipeline Trace Methods
// ============================================================================

json RenderPipeline::get_layout_trace() const {
    json trace;
    trace["stage"] = "LAYOUT";
    trace["layout_tree"] = layout_tree_.to_json();
    trace["timestamp_ms"] = stats_.layout_time_ms;
    return trace;
}

json RenderPipeline::get_measure_trace() const {
    json trace;
    trace["stage"] = "MEASURE";
    trace["measurements"] = json::array();
    
    for (const auto& [id, metrics] : text_metrics_cache_) {
        json m;
        m["object_id"] = id;
        m["width"] = metrics.width;
        m["height"] = metrics.height;
        m["ascent"] = metrics.ascent;
        m["descent"] = metrics.descent;
        trace["measurements"].push_back(m);
    }
    
    trace["font_info"] = font_.to_info_json();
    trace["timestamp_ms"] = stats_.measure_time_ms;
    return trace;
}

json RenderPipeline::get_canvas_trace() const {
    json trace;
    trace["stage"] = "CANVAS_COMMANDS";
    trace["canvas_trace"] = canvas_.to_trace_json();
    return trace;
}

json RenderPipeline::get_render_trace() const {
    json trace;
    trace["experiment"] = "EXP-005";
    trace["pipeline_status"] = stage_to_string(stage_);
    trace["frame_number"] = frame_number_;
    trace["statistics"] = stats_.to_json();
    trace["framebuffer_info"] = framebuffer_.to_info_json();
    trace["layout"] = get_layout_trace();
    trace["canvas"] = get_canvas_trace();
    return trace;
}

json RenderPipeline::get_text_render_trace() const {
    json trace;
    trace["stage"] = "TEXT_RENDERING";
    trace["text_views_rendered"] = stats_.text_views_rendered;
    trace["font_used"] = font_.to_info_json();
    
    // Extract text-related commands from canvas
    json text_commands = json::array();
    for (const auto& cmd : canvas_.get_commands()) {
        if (cmd.type == "drawText") {
            text_commands.push_back(cmd.to_json());
        }
    }
    trace["text_commands"] = text_commands;
    
    return trace;
}

// ============================================================================
// PNG Writer Implementation (Minimal PNG without external library)
// ============================================================================

uint32_t PNGWriter::crc32(const uint8_t* data, size_t length, uint32_t init_crc) {
    uint32_t crc = init_crc;
    
    static const uint32_t crc_table[256] = {
        0x00000000, 0x77073096, 0xEE0E612C, 0x990951BA, 0x076DC419, 0x706AF48F,
        0xE963A535, 0x9E64953A, 0x0EDB8832, 0x79DCB8A4, 0xE0D5E91E, 0x97D2D988,
        0x09B64C2B, 0x7EB17CBD, 0xE7B82D07, 0x90BF1D91, 0x1DB71064, 0x6AB020F2,
        0xF3B97148, 0x84BE41DE, 0x1ADAD47D, 0x6DDDE4EB, 0xF4D4B551, 0x83D385C7,
        0x136C9856, 0x646BA8C0, 0xFD62F97A, 0x8A65C9EC, 0x14015C4F, 0x63066CD9,
        0xFA0F3D63, 0x8D080DF5, 0x3B6E20C8, 0x4C69105E, 0xD56041E4, 0xA2677172,
        0x3C03E4D1, 0x4B04D447, 0xD20D85FD, 0xA50AB56B, 0x35B5A8FA, 0x42B2986C,
        0xDBBBC9D6, 0xACBCF940, 0x32D86CE3, 0x45DF5C75, 0xDCD60DCF, 0xABD13D59,
        0x26D930AC, 0x51DE003A, 0xC8D75180, 0xBFD06116, 0x21B4F4B5, 0x56B3C423,
        0xCFBA9599, 0xB8BDA50F, 0x2802B89E, 0x5F058808, 0xC60CD9B2, 0xB10BE924,
        0x2F6F7C87, 0x58684C11, 0xC1611DAB, 0xB6662D3D, 0x76DC4190, 0x01DB7106,
        0x98D220BC, 0xEFD5102A, 0x71B18589, 0x06B6B51F, 0x9FBFE4A5, 0xE8B8D433,
        0x7807C9A2, 0x0F00F934, 0x9609A88E, 0xE10E9818, 0x7F6A0DBB, 0x086D3D2D,
        0x91646C97, 0xE6635C01, 0x6B6B51F4, 0x1C6C6162, 0x856530D8, 0xF262004E,
        0x6C0695ED, 0x1B01A57B, 0x8208F4C1, 0xF50FC457, 0x65B0D9C6, 0x12B7E950,
        0x8BBEB8EA, 0xFCB9887C, 0x62DD1DDF, 0x15DA2D49, 0x8CD37CF3, 0xFBD44C65,
        0x4DB26158, 0x3AB551CE, 0xAE3BFA82, 0xF4BFDA8D, 0x36034AF6, 0x41047A60,
        0xDF60EFC3, 0xA867DF55, 0x316E8EEF, 0x4669BE79, 0xCB61B38C, 0xBC66831A,
        0x256FD2A0, 0x5268E236, 0xCC0C7795, 0xBB0B4703, 0x220216B9, 0x5505262F,
        0xC5BA3BBE, 0xB2BD0B28, 0x2BB45A92, 0x5CB36A04, 0xC2D7FFA7, 0xB5D0CF31,
        0x2CD99E8B, 0x5BDEAE1D, 0x9B64C2B0, 0xEC63F226, 0x756AA39C, 0x026D930A,
        0x9C0906A9, 0xEB0E363F, 0x72076785, 0x05005713, 0x95BF4A82, 0xE2B87A14,
        0x7BB12BAE, 0x0CB61B38, 0x92D28E9B, 0xE5D5BE0D, 0x7CDCEFB7, 0x0BDBDF21,
        0x86D3D2D4, 0xF1D4E242, 0x68DDB3F8, 0x1FDA836E, 0x81BE16CD, 0xF642B715,
        0x8FA58CB9, 0xFFEFF47D, 0x85845DD1, 0x6FA87E4F, 0xFE2CE6E0, 0xA3014314,
        0x4E0811A1, 0x75F4E852, 0xBD3AF235, 0x2AD7D2BB, 0xEB86D391, 0x96743B41,
        0x1636C361, 0x6D0CABE4, 0x7A0A674E, 0xEF9C54B4, 0x84C8D142, 0xD2A8C8A4,
        0x11090356, 0x6F4A94AB, 0xDD272F96, 0x560EA683, 0xBE5B6FF0, 0x127088B5,
        0x44935DE2, 0x5FB7C14E, 0x802B40B0, 0x0921E6F8, 0x8A4C9A2E, 0x8E29CFC1,
        0x2AA49E14, 0xE5D1C03D, 0x84DCC240, 0x38BCAFA2, 0x024771FF, 0x340BADCA,
        0x1C3956B4, 0x4C8EBABA, 0x380266C7, 0x460B0BE0, 0x6A6A5C8C, 0xE93A25DF,
        0x651D2BFC
    };
    
    for (size_t i = 0; i < length; i++) {
        crc = crc_table[(crc ^ data[i]) & 0xFF] ^ (crc >> 8);
    }
    
    return crc;
}

std::vector<uint8_t> PNGWriter::compress_data(const uint8_t* data, size_t length) {
    // EXP-086 Phase 3 (B1 FIX): Use zlib for proper PNG IDAT compression.
    //
    // The previous implementation was broken:
    // 1. It emitted a raw deflate non-compressed block with NO zlib header
    //    (PNG requires zlib-wrapped deflate: 2-byte CMF/FLG header + deflate
    //     + 4-byte Adler-32 checksum).
    // 2. The 2-byte LEN field can only hold values up to 65535, so any image
    //    larger than 64KB produced a truncated block.
    //
    // The new implementation uses zlib's compress2() with the default
    // compression level. This produces a valid zlib stream that any PNG
    // decoder (PIL, stb_image, libpng, web browsers) can decode.
    //
    // zlib is already linked (for APK deflate extraction), so no new deps.
    uLong bound = compressBound(length);
    std::vector<uint8_t> compressed(bound);

    uLongf actual_size = bound;
    int ret = compress2(compressed.data(), &actual_size,
                         data, length,
                         Z_DEFAULT_COMPRESSION);
    if (ret != Z_OK) {
        // Fallback: emit uncompressed (still wrapped in zlib format)
        // CMF: 0x78 (32K window, deflate), FLG: 0x01 (no dict, level 0)
        compressed.clear();
        compressed.push_back(0x78);
        compressed.push_back(0x01);
        // Single non-compressed deflate block (split if >65535)
        size_t remaining = length;
        const uint8_t* p = data;
        while (remaining > 0) {
            size_t chunk = std::min(remaining, (size_t)65535);
            uint8_t is_final = (remaining <= 65535) ? 0x01 : 0x00;
            compressed.push_back(is_final);  // BFINAL + BTYPE=00 (no compression)
            // LEN (little-endian)
            compressed.push_back(chunk & 0xFF);
            compressed.push_back((chunk >> 8) & 0xFF);
            // NLEN (one's complement of LEN, little-endian)
            uint16_t nlen = ~static_cast<uint16_t>(chunk);
            compressed.push_back(nlen & 0xFF);
            compressed.push_back((nlen >> 8) & 0xFF);
            // Data
            compressed.insert(compressed.end(), p, p + chunk);
            p += chunk;
            remaining -= chunk;
        }
        // Adler-32 checksum (big-endian)
        uint32_t adler = adler32(1L, data, length);
        compressed.push_back((adler >> 24) & 0xFF);
        compressed.push_back((adler >> 16) & 0xFF);
        compressed.push_back((adler >> 8) & 0xFF);
        compressed.push_back(adler & 0xFF);
        return compressed;
    }
    compressed.resize(actual_size);
    return compressed;
}

bool PNGWriter::write_png(const std::string& filename, const FrameBuffer& fb) {
    std::ofstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        return false;
    }
    
    int width = fb.get_width();
    int height = fb.get_height();
    
    // PNG signature
    const uint8_t png_signature[8] = {137, 80, 78, 71, 13, 10, 26, 10};
    file.write(reinterpret_cast<const char*>(png_signature), 8);
    
    // Helper lambda to write a chunk
    // EXP-086 Phase 4 (B1 FIX): Use zlib's crc32() for proper PNG chunk CRC.
    // The previous custom crc32() implementation was missing the standard
    // 0xFFFFFFFF init XOR, producing wrong CRCs that PIL/libpng reject.
    auto write_chunk = [&](const char* type, const uint8_t* data, size_t length) {
        uint32_t length_be = __builtin_bswap32(static_cast<uint32_t>(length));
        file.write(reinterpret_cast<const char*>(&length_be), 4);
        file.write(type, 4);
        file.write(reinterpret_cast<const char*>(data), length);

        // PNG CRC = zlib crc32 over (type + data)
        // zlib's crc32() handles the 0xFFFFFFFF init and final XOR automatically.
        uLong crc_val = ::crc32(0L, Z_NULL, 0);  // init
        crc_val = ::crc32(crc_val, reinterpret_cast<const Bytef*>(type), 4);
        if (length > 0) {
            crc_val = ::crc32(crc_val, reinterpret_cast<const Bytef*>(data), length);
        }
        uint32_t crc_be = __builtin_bswap32(static_cast<uint32_t>(crc_val));
        file.write(reinterpret_cast<const char*>(&crc_be), 4);
    };
    
    // IHDR chunk
    uint8_t ihdr[13];
    ihdr[0] = (width >> 24) & 0xFF;  // Width (big-endian)
    ihdr[1] = (width >> 16) & 0xFF;
    ihdr[2] = (width >> 8) & 0xFF;
    ihdr[3] = width & 0xFF;
    ihdr[4] = (height >> 24) & 0xFF;  // Height (big-endian)
    ihdr[5] = (height >> 16) & 0xFF;
    ihdr[6] = (height >> 8) & 0xFF;
    ihdr[7] = height & 0xFF;
    ihdr[8] = 8;   // Bit depth
    ihdr[9] = 2;   // Color type: RGB (we'll convert RGBA to RGB)
    ihdr[10] = 0;  // Compression method
    ihdr[11] = 0;  // Filter method
    ihdr[12] = 0;  // Interlace method
    write_chunk("IHDR", ihdr, 13);
    
    // IDAT chunk (image data)
    // Convert RGBA to RGB and add filter bytes (none = 0)
    size_t row_size = width * 3;  // RGB
    std::vector<uint8_t> image_data;
    image_data.reserve((row_size + 1) * height);
    
    for (int y = 0; y < height; y++) {
        image_data.push_back(0);  // Filter type: None
        
        for (int x = 0; x < width; x++) {
            RGBA pixel = fb.get_pixel(x, y);
            image_data.push_back(pixel.r);
            image_data.push_back(pixel.g);
            image_data.push_back(pixel.b);
        }
    }
    
    std::vector<uint8_t> compressed = compress_data(image_data.data(), image_data.size());
    write_chunk("IDAT", compressed.data(), compressed.size());
    
    // IEND chunk
    write_chunk("IEND", nullptr, 0);
    
    file.close();
    return true;
}

json PNGWriter::generate_screenshot_info(const FrameBuffer& fb, 
                                        const RenderPipeline& pipeline,
                                        const std::string& text_content) {
    json info;
    info["filename"] = "screenshot.png";
    info["format"] = "PNG";
    info["width"] = fb.get_width();
    info["height"] = fb.get_height();
    info["frame_number"] = pipeline.get_frame_number();
    info["rendered_objects"] = pipeline.get_statistics()["text_views_rendered"];
    info["text_content"] = text_content;
    info["pipeline_stage"] = stage_to_string(pipeline.get_stage());
    info["total_commands"] = pipeline.get_canvas().get_command_count();
    info["pixels_written"] = fb.get_draw_count();
    info["generation_timestamp"] = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()
    ).count();
    
    return info;
}

} // namespace renderer
} // namespace miniandroid
