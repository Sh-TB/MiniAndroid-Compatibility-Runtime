/*
 * MiniAndroid Runtime v0.1 - Software Rendering Pipeline
 * EXP-005: Minimal Software Renderer
 * 
 * Converts View/Object state into real framebuffer and generates screenshots.
 * 
 * Golden Debug Protocol Compliant:
 * - No fake screenshot
 * - Generated image must come from runtime state
 * - Trace every rendering step
 */

#ifndef MINIANDROID_SOFTWARE_RENDERER_H
#define MINIANDROID_SOFTWARE_RENDERER_H

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <cstdint>
#include <cmath>
#include <algorithm>
#include <chrono>
#include <sstream>
#include <iomanip>
#include <array>

#include "../../third_party/nlohmann_json/include/nlohmann/json.hpp"

// Forward declarations from object model
namespace miniandroid {
namespace runtime {
    class TextViewRuntimeObject;
    class ViewRuntimeObject;
    class ActivityRuntimeObject;
    class EnhancedObjectHeap;
}
}

namespace miniandroid {
namespace renderer {

using json = nlohmann::json;

// ============================================================================
// Color Types (Task #1)
// ============================================================================

struct RGBA {
    uint8_t r = 0;
    uint8_t g = 0;
    uint8_t b = 0;
    uint8_t a = 255;
    
    RGBA() = default;
    constexpr RGBA(uint8_t r, uint8_t g, uint8_t b, uint8_t a = 255) : r(r), g(g), b(b), a(a) {}
    
    static RGBA from_hex(uint32_t hex) {
        return RGBA(
            (hex >> 16) & 0xFF,
            (hex >> 8) & 0xFF,
            hex & 0xFF,
            (hex >> 24) & 0xFF
        );
    }
    
    uint32_t to_hex() const {
        return (uint32_t(a) << 24) | (uint32_t(r) << 16) | (uint32_t(g) << 8) | uint32_t(b);
    }
    
    json to_json() const {
        json j;
        j["r"] = r;
        j["g"] = g;
        j["b"] = b;
        j["a"] = a;
        j["hex"] = "#" + [&]() {
            std::ostringstream oss;
            oss << std::hex << std::setw(2) << std::setfill('0') << (int)r
                << std::setw(2) << (int)g 
                << std::setw(2) << (int)b;
            return oss.str();
        }();
        return j;
    }
};

inline RGBA blend(const RGBA& src, const RGBA& dst) {
    if (src.a == 255) return src;
    if (src.a == 0) return dst;
    
    float alpha = src.a / 255.0f;
    float inv_alpha = 1.0f - alpha;
    
    return RGBA(
        static_cast<uint8_t>(src.r * alpha + dst.r * inv_alpha),
        static_cast<uint8_t>(src.g * alpha + dst.g * inv_alpha),
        static_cast<uint8_t>(src.b * alpha + dst.b * inv_alpha),
        255
    );
}

// Predefined colors
namespace Colors {
    constexpr RGBA BLACK{0, 0, 0, 255};
    constexpr RGBA WHITE{255, 255, 255, 255};
    constexpr RGBA TRANSPARENT{0, 0, 0, 0};
    constexpr RGBA GREY_200{225, 225, 225, 255};   // Background
    constexpr RGBA GREY_800{33, 33, 33, 255};      // Text
    constexpr RGBA DEEP_ORANGE{255, 87, 34, 255};  // Accent
}

// ============================================================================
// FrameBuffer Class (Task #1)
// ============================================================================

class FrameBuffer {
public:
    FrameBuffer(int width = 480, int height = 800)
        : width_(width), height_(height)
    {
        pixels_.resize(width * height, Colors::WHITE);
        clear_count_ = 0;
        draw_count_ = 0;
    }
    
    int get_width() const { return width_; }
    int get_height() const { return height_; }
    size_t get_pixel_count() const { return pixels_.size(); }
    
    void clear(RGBA color = Colors::WHITE) {
        std::fill(pixels_.begin(), pixels_.end(), color);
        clear_count_++;
        
        json op;
        op["type"] = "CLEAR";
        op["color"] = color.to_json();
        op["sequence"] = clear_count_;
        operations_.push_back(op);
    }
    
    void set_pixel(int x, int y, RGBA color) {
        if (x < 0 || x >= width_ || y < 0 || y >= height_) return;
        
        size_t idx = y * width_ + x;
        pixels_[idx] = blend(color, pixels_[idx]);
        draw_count_++;
    }
    
    RGBA get_pixel(int x, int y) const {
        if (x < 0 || x >= width_ || y < 0 || y >= height_) {
            return Colors::TRANSPARENT;
        }
        return pixels_[y * width_ + x];
    }
    
    const std::vector<RGBA>& get_pixels() const { return pixels_; }
    
    int get_clear_count() const { return clear_count_; }
    int get_draw_count() const { return draw_count_; }
    const std::vector<json>& get_operations() const { return operations_; }
    
    json to_info_json() const {
        json info;
        info["width"] = width_;
        info["height"] = height_;
        info["pixel_count"] = get_pixel_count();
        info["clear_count"] = clear_count_;
        info["draw_count"] = draw_count_;
        info["operations"] = operations_;
        return info;
    }

private:
    int width_, height_;
    std::vector<RGBA> pixels_;
    int clear_count_;
    int draw_count_;
    std::vector<json> operations_;
};

// ============================================================================
// Bitmap Font for Text Rendering (Task #6)
// ============================================================================

class BitmapFont {
public:
    struct Glyph {
        char character;
        int width;
        int height;
        int advance;
        const uint8_t* bitmap;
    };
    
    struct TextMetrics {
        int width;
        int height;
        int ascent;
        int descent;
    };
    
    BitmapFont();
    
    const Glyph* get_glyph(char c) const;
    TextMetrics measure_text(const std::string& text) const;
    int get_line_height() const { return 16; }
    int get_baseline_offset() const { return 12; }
    
    json to_info_json() const;

private:
    // EXP-092 FIX: Use the auto-generated bitmap_font_table from
    // bitmap_font_data.h (generated by scripts/gen_bitmap_font.py).
    // The previous hand-coded table only had 13 glyphs (space, H, e, l, o,
    // M, i, n, d, r, A, t) AND was mis-indexed — 'H' was written to slot 33
    // instead of slot 40, then overwritten by 'A'. All other ASCII chars
    // fell through to `fill_remaining_glyphs()`'s default "dot in the middle"
    // bitmap, which produced essentially unreadable text on screen.
    // The new font covers ALL 95 printable ASCII characters (32..126)
    // generated from DejaVuSansMono at 12pt, scaled to 8x16 with nearest-
    // neighbor sampling and thresholded at luminance < 128.
    std::array<Glyph, 95> glyphs_{};
    void initialize_ascii_glyphs();
    void fill_remaining_glyphs();
};

// ============================================================================
// Layout Structures (Task #2)
// ============================================================================

struct LayoutBounds {
    int left = 0, top = 0, right = 0, bottom = 0;
    
    int width() const { return right - left; }
    int height() const { return bottom - top; }
    bool is_empty() const { return width() <= 0 || height() <= 0; }
    void set(int l, int t, int w, int h) { left = l; top = t; right = l + w; bottom = t + h; }
    
    json to_json() const {
        return {{"left", left}, {"top", top}, {"right", right}, {"bottom", bottom},
                {"width", width()}, {"height", height()}};
    }
};

struct LayoutNode {
    uint32_t object_id = 0;
    std::string view_class;
    LayoutBounds bounds;
    std::vector<LayoutNode> children;
    
    json to_json() const;
};

// ============================================================================
// Software Canvas (Task #4)
// ============================================================================

struct CanvasCommand {
    std::string type;
    uint64_t sequence = 0;
    json params;
    
    json to_json() const {
        return {{"type", type}, {"sequence", sequence}, {"params", params}};
    }
};

class SoftwareCanvas {
public:
    explicit SoftwareCanvas(FrameBuffer* framebuffer);
    
    void draw_color(RGBA color);
    void draw_rect(float left, float top, float right, float bottom, RGBA color);
    void draw_text(const std::string& text, float x, float y, RGBA color, const BitmapFont* font = nullptr);

    // EXP-088 Phase A4: Draw decoded image pixels at (x, y) with optional
    // scaling to (dst_w, dst_h). If dst_w/dst_h are 0, use the source size.
    // The src_rgba buffer must be src_w * src_h * 4 bytes.
    // Pixels with alpha < 255 are alpha-blended onto the framebuffer.
    void draw_image(const uint8_t* src_rgba, int src_w, int src_h,
                    int dst_x, int dst_y,
                    int dst_w = 0, int dst_h = 0);

    const std::vector<CanvasCommand>& get_commands() const { return commands_; }
    uint64_t get_command_count() const { return command_sequence_; }
    json to_trace_json() const;

private:
    FrameBuffer* framebuffer_;
    uint64_t command_sequence_ = 0;
    std::vector<CanvasCommand> commands_;
    BitmapFont default_font_;
};

// ============================================================================
// Render Pipeline (Task #5)
// ============================================================================

enum class RenderStage { IDLE, LAYOUT, MEASURE, DRAW, COMPLETE, ERROR };

std::string stage_to_string(RenderStage stage);

struct RenderStatistics {
    int total_views_processed = 0;
    int text_views_rendered = 0;
    int total_commands_issued = 0;
    int pixels_written = 0;
    double layout_time_ms = 0;
    double measure_time_ms = 0;
    double draw_time_ms = 0;
    double total_time_ms = 0;
    
    json to_json() const;
    
    // Allow access by key for convenience
    int operator[](const std::string& key) const {
        if (key == "text_views_rendered") return text_views_rendered;
        if (key == "total_views_processed") return total_views_processed;
        if (key == "total_commands_issued") return total_commands_issued;
        if (key == "pixels_written") return pixels_written;
        return 0;
    }
};

class RenderPipeline {
public:
    explicit RenderPipeline(int width = 480, int height = 800);
    
    bool render(runtime::EnhancedObjectHeap& heap, const std::string& activity_text = "Hello MiniAndroid");
    
    RenderStage get_stage() const { return stage_; }
    const FrameBuffer& get_framebuffer() const { return framebuffer_; }
    const SoftwareCanvas& get_canvas() const { return canvas_; }
    const LayoutNode& get_layout_tree() const { return layout_tree_; }
    const RenderStatistics& get_statistics() const { return stats_; }
    
    json get_layout_trace() const;
    json get_measure_trace() const;
    json get_canvas_trace() const;
    json get_render_trace() const;
    json get_text_render_trace() const;
    
    uint64_t get_frame_number() const { return frame_number_; }
    void next_frame() { frame_number_++; }

private:
    bool perform_layout(runtime::EnhancedObjectHeap& heap);
    bool perform_measurement();
    bool perform_draw(runtime::EnhancedObjectHeap& heap, const std::string& activity_text);
    
    LayoutNode build_layout_tree(uint32_t object_id, runtime::EnhancedObjectHeap& heap, int depth = 0);
    void layout_view(LayoutNode& node, int parent_left, int parent_top, int parent_width, int parent_height);
    
    FrameBuffer framebuffer_;
    SoftwareCanvas canvas_;
    LayoutNode layout_tree_;
    RenderStatistics stats_;
    RenderStage stage_;
    uint64_t frame_number_ = 0;
    BitmapFont font_;
    std::map<uint32_t, BitmapFont::TextMetrics> text_metrics_cache_;
};

// ============================================================================
// PNG Writer (Task #7)
// ============================================================================

class PNGWriter {
public:
    static bool write_png(const std::string& filename, const FrameBuffer& fb);
    static json generate_screenshot_info(const FrameBuffer& fb, 
                                        const RenderPipeline& pipeline,
                                        const std::string& text_content);

private:
    static uint32_t crc32(const uint8_t* data, size_t length, uint32_t init_crc = 0xFFFFFFFF);
    static std::vector<uint8_t> compress_data(const uint8_t* data, size_t length);
};

// ============================================================================
// PNG Decoder (EXP-088 Phase A4)
//
// Decodes an in-memory PNG file (any of color types 0/2/4/6, bit depth 8,
// non-interlaced) into a flat RGBA pixel buffer.
//
// This is the C++ counterpart of the Python "expected RGBA" reproducer in
// scripts/a4_01_create_known_png.py. The C++ decoder MUST produce byte-identical
// RGBA bytes to PIL.Image.convert("RGBA").tobytes() for every PNG written by
// that script. The test is exercised by tools/exp088_a4_png_decoder_test.cpp.
//
// Supports:
//   - color_type 0 (grayscale, 1 sample)
//   - color_type 2 (RGB, 3 samples)
//   - color_type 4 (grayscale + alpha, 2 samples)  <- simplestopwatch uses this
//   - color_type 6 (RGBA, 4 samples)
//   - bit depth 8
//   - non-interlaced (Adam7 NOT supported; will return false)
//   - All 5 PNG filter types (None, Sub, Up, Average, Paeth)
// ============================================================================

struct DecodedImage {
    int width = 0;
    int height = 0;
    std::vector<uint8_t> rgba;  // width * height * 4 bytes
    std::string color_type_name;  // "gray", "rgb", "ga", "rgba"
    bool ok = false;
    std::string error;
};

class PNGDecoder {
public:
    // Decode a PNG file from a raw byte buffer.
    // Returns DecodedImage with .ok=true on success.
    static DecodedImage decode(const std::vector<uint8_t>& png_bytes);
    static DecodedImage decode_file(const std::string& path);

private:
    // Apply a PNG unfilter pass on a single scanline.
    //  raw:  input bytes including the leading filter byte per row
    //  bpp:  bytes per pixel (1..4)
    //  width, height: image dimensions
    //  out:  output buffer (width * height * bpp bytes, no filter bytes)
    static bool unfilter(const std::vector<uint8_t>& raw,
                         int bpp, int width, int height,
                         std::vector<uint8_t>& out,
                         std::string& error);
};

} // namespace renderer
} // namespace miniandroid

#endif // MINIANDROID_SOFTWARE_RENDERER_H
