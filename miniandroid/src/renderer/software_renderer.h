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
        if (alpha_preserve_) {
            // S83-GFX-BASE (Contract C6): offscreen LAYER targets composite
            // SRC-OVER onto a transparent buffer — the pixel's own alpha is
            // accumulated (out_a = sa + da·(1-sa), premultiplied math,
            // straight-RGBA storage). Opaque targets keep the legacy law.
            RGBA& dst = pixels_[idx];
            const float sa = color.a / 255.f, da = dst.a / 255.f;
            const float oa = sa + da * (1.f - sa);
            if (oa <= 0.f) {
                dst = Colors::TRANSPARENT;
            } else {
                const float k = da * (1.f - sa);
                dst.r = (uint8_t)std::min(255.f, std::round((color.r * sa + dst.r * k) / oa));
                dst.g = (uint8_t)std::min(255.f, std::round((color.g * sa + dst.g * k) / oa));
                dst.b = (uint8_t)std::min(255.f, std::round((color.b * sa + dst.b * k) / oa));
                dst.a = (uint8_t)std::min(255.f, std::round(oa * 255.f));
            }
        } else {
            pixels_[idx] = blend(color, pixels_[idx]);
        }
        draw_count_++;
    }
    
    // S83-GFX-BASE: layer mode — set_pixel accumulates alpha (see above).
    void set_alpha_preserve(bool on) { alpha_preserve_ = on; }
    bool alpha_preserve() const { return alpha_preserve_; }
    
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
    bool alpha_preserve_ = false;
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

    // ── S68 FOUNDATION (drawBitmap src/dst law, §12) ────────────────────
    // AOSP Canvas.drawBitmap(bitmap, srcRect, dstRect, paint) contract:
    // the SOURCE SUBSET (sx, sy, sw, sh in source pixels) is selected first
    // (crop), then scaled into the DESTINATION rect (dx, dy, dw, dh).
    // Nearest-neighbour sampling (Paint.FilterBitmap default = false law —
    // android.graphics.Paint: "FilterBitmap flag: use bilinear filtering
    // when false, nearest is the default"). Alpha "over" composited.
    // Honors the canvas clip rect set by set_clip().
    void draw_image_region(const uint8_t* src_rgba, int src_w, int src_h,
                           int sx, int sy, int sw, int sh,
                           int dx, int dy, int dw, int dh);

    // ── S68 FOUNDATION (Canvas clip law, §12) ───────────────────────────
    // AOSP Canvas: clipRect restricts drawing to the intersection with the
    // current clip. The clip is DEVICE space; every later draw intersects
    // with it. FrameBuffer itself is clip-free (one flat pixel array), so
    // the clip lives on the SoftwareCanvas that funnels every primitive.
    // Axis: framebuffer pixels (NOT view space) — replay maps into it.
    void set_clip(float left, float top, float right, float bottom);
    void clear_clip();
    bool has_clip() const { return clip_active_; }

    // ── S83-GFX-BASE (Contract C1 clipPath law) ─────────────────────
    // A path clip restricts drawing to the rasterized scanline spans of
    // the path (device space). Spans are per-row [x_start, x_end) pairs,
    // indexed relative to row y0. Every primitive consults them through
    // clip_allows(); clear_clip() drops both rect and path clip.
    void set_path_clip(int y0, int y1,
                       std::vector<std::vector<std::pair<float, float>>> spans);
    bool has_path_clip() const { return !path_spans_.empty(); }
    // Public device-space clip query (rect ∧ path) — used by the per-pixel
    // drawBitmap replay path which bypasses draw_rect.
    bool device_clip_allows(int x, int y) const { return clip_allows(x, y); }

    // S68: framebuffer accessor — the Canvas text path draws shaped glyphs
    // directly onto the framebuffer (TextShaper.draw(FrameBuffer&,...)).
    FrameBuffer& fb() { return *framebuffer_; }

    const std::vector<CanvasCommand>& get_commands() const { return commands_; }
    uint64_t get_command_count() const { return command_sequence_; }
    json to_trace_json() const;

private:
    FrameBuffer* framebuffer_;
    uint64_t command_sequence_ = 0;
    std::vector<CanvasCommand> commands_;
    BitmapFont default_font_;
    // S68 clip state (device space, inclusive-exclusive like draw spans):
    bool clip_active_ = false;
    float clip_l_ = 0, clip_t_ = 0, clip_r_ = 0, clip_b_ = 0;
    // S83 path clip (device-space scanline spans):
    int path_y0_ = 0, path_y1_ = 0;
    std::vector<std::vector<std::pair<float, float>>> path_spans_;
    // Returns false when (x, y) is clipped out (rect ∧ path).
    bool clip_allows(int x, int y) const {
        if (clip_active_) {
            if (!(x >= (int)clip_l_ && x < (int)clip_r_ &&
                  y >= (int)clip_t_ && y < (int)clip_b_)) return false;
        }
        if (!path_spans_.empty()) {
            if (y < path_y0_ || y >= path_y1_) return false;
            const auto& row = path_spans_[(size_t)(y - path_y0_)];
            for (const auto& sp : row)
                if (x >= (int)sp.first && x < (int)sp.second) return true;
            return false;
        }
        return true;
    }

public:
    // S83-GFX-BASE: retarget the canvas at a different framebuffer (layer
    // replay). All primitives funnel through framebuffer_; switching the
    // pointer redirects them without touching clip/command state.
    void set_target(FrameBuffer* fb) { framebuffer_ = fb; }
    FrameBuffer* target() const { return framebuffer_; }

private:
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

// ============================================================================
// PNG Writer — CAMPAIGN 010 R1: libpng-backed encoder.
// ============================================================================

class PNGWriter {
public:
    static bool write_png(const std::string& filename, const FrameBuffer& fb);
    static json generate_screenshot_info(const FrameBuffer& fb,
                                        const RenderPipeline& pipeline,
                                        const std::string& text_content);
};

// ============================================================================
// PNG Decoder — CAMPAIGN 010 R1: libpng-backed.
//
// Decodes an in-memory PNG file of ANY color type (0/2/3/4/6), bit depth
// (1/2/4/8/16, 16 stripped to 8) and interlace method (including Adam7)
// into a flat RGBA pixel buffer, per the Android Bitmap ARGB_8888 contract.
// tRNS transparency is applied. This replaced the EXP-088 Phase A4
// hand-written decoder after a 7,036-image real-APK differential benchmark
// (custom: 97.07% success, 3 tRNS misdecodes; libpng: 100%, byte-identical
// to stb_image v2.30, 1.65x faster). The PIL byte-identity test fixture
// (tools/exp088_a4_png_decoder_test.cpp) still guards the interface.
// ============================================================================

struct DecodedImage {
    int width = 0;
    int height = 0;
    std::vector<uint8_t> rgba;  // width * height * 4 bytes
    std::string color_type_name;  // "gray", "rgb", "ga", "rgba"
    bool ok = false;
    std::string error;
};

// S95 L-S95-ADAPTIVE-1: app-resource resolver handed DOWN to the vector /
// adaptive-icon decoder. The renderer has no ResTable; the engine (which
// owns ARSC + APK zip access) resolves references on demand. A color ref
// fills argb; a drawable ref fills bytes/path/density.
struct VectorImageRef {
    bool resolved = false;
    bool is_color = false;
    uint32_t argb = 0;
    std::vector<uint8_t> bytes;
    std::string path;
    uint16_t density = 0;
};
using VectorRefResolver = std::function<bool(uint32_t resid, VectorImageRef* out)>;

// ── G04 §4/§8: header-only image dimension probe ───────────────────────────
// AOSP law: Drawable.getIntrinsicWidth/Height must be answerable BEFORE a
// full decode (ImageView.onMeasure runs pre-draw; decoding every bitmap
// during measure would be the wrong complexity class). We parse the encoded
// headers only:
//   PNG  → IHDR width/height (big-endian u32 at byte 16/20 after the 8-byte
//          signature + 4 len + 4 type)
//   WebP → VP8X canvas size (24-bit-1) / VP8 frame header / VP8L 14-bit dims
//   JPEG → SOF0/SOF2 frame header dimensions
// Returns true with w/h filled on success. NEVER decodes pixel data — safe
// on hostile input beyond the header window (bounds-checked, no allocation).
struct ImageSizeProbe {
    int width = 0, height = 0;
};
bool probe_image_size(const std::vector<uint8_t>& bytes, ImageSizeProbe* out);

// ── G04 §12: ImageView FIT_CENTER placement law (ImageView.java L255:
// mScaleType = ScaleType.FIT_CENTER default). Matrix law: scale =
// min(dW/srcW, dH/srcH); centered within the destination box. Shared by the
// ViewRenderer paint path and the ExecutionEngine frame path so the two
// render outputs cannot drift (§12: one renderer, one law).
struct FitRect {
    int x = 0, y = 0, w = 0, h = 0;
};
FitRect fit_center_rect(int src_w, int src_h, int box_x, int box_y,
                        int box_w, int box_h);

// ── S83-GFX-BASE (§19 ImageView scale-type law, one function) ───────────
// AOSP ImageView.onDraw / configureBounds (ImageView.java): the scale type
// picks the matrix that maps the source drawable into the view box.
//   MATRIX 0        identity matrix → natural size at box origin
//   FIT_XY 1        stretch independently to fill the box
//   FIT_START 2     fit-scale, aligned to box top-left
//   FIT_CENTER 3    fit-scale, centered (the historical fit_center_rect)
//   FIT_END 4       fit-scale, aligned to box bottom-right
//   CENTER 5        natural size, centered
//   CENTER_CROP 6   crop-scale = max(boxW/srcW, boxH/srcH), centered
//                   (destination overflows the box; clipped at draw)
//   CENTER_INSIDE 7 scale = min(1, fit-scale), centered (never upscales)
FitRect scale_image_rect(int scale_type, int src_w, int src_h,
                         int box_x, int box_y, int box_w, int box_h);

// ── S68 FOUNDATION (A3 image pipeline law, §13) ──────────────────────────
// ONE format-detecting decode entry point for EVERY image consumer
// (ImageView resource path, BitmapFactory shadow, drawable loading).
// AOSP BitmapFactory.java maps an encoded byte stream to a Bitmap via the
// format-specific decoder chosen by the container signature — the choice
// is made ON THE BYTES (magic numbers), never on the file extension.
//
// Detected formats (magic):
//   PNG  89 50 4E 47        → PNGDecoder (libpng)
//   JPEG FF D8 FF           → JPEGDecoder (libjpeg)
//   WebP RIFF....WEBP       → WebPDecoder (libwebp)
//   GIF  GIF87a / GIF89a    → EXPLICIT UNSUPPORTED: ok=false with error
//     "GIF format not supported (no decoder wired)" — Android apps get a
//     failed decode + Drawable failure, NEVER a silently-dropped view.
//   XML  '<'                → not a bitmap: ok=false "not a bitmap format".
//       (state-list XML drawables are the inflater's domain.)
//   AXML 0x03 0x00          → S95 L-S95-VECTOR-1: binary-AXML VectorDrawable
//       is RASTERIZED (see vector_decode.{h,cpp}); unsupported vector
//       features (gradient/clip-path/app color refs) are named errors.
// density_dpi: AOSP getIntrinsicWidth law raster scale (declared dp ×
//       dpi/160); 0 = viewport × clamped 4× fallback.
// resolver: optional app-resource resolver (L-S95-ADAPTIVE-1) — required
//       for <adaptive-icon> layers and app-color fillColor references.
// Returns true iff out->ok (decoded pixels available).
bool decode_image_bytes(const std::vector<uint8_t>& bytes, DecodedImage* out,
                        int density_dpi = 0,
                        const VectorRefResolver* resolver = nullptr);
// Format label for traces: "png" | "jpeg" | "webp" | "gif" | "axml" | "xml" | "unknown".
std::string image_format_name(const std::vector<uint8_t>& bytes);

class PNGDecoder {
public:
    // Decode a PNG file from a raw byte buffer.
    // Returns DecodedImage with .ok=true on success.
    static DecodedImage decode(const std::vector<uint8_t>& png_bytes);
    static DecodedImage decode_file(const std::string& path);
};

// EXP-097 §5: WebPDecoder — wraps libwebp (Google's reference decoder).
//
// Per AOSP `BitmapFactory` source: a Bitmap can be created from a WebP
// encoded byte array; the framework delegates to its native WebP code
// (which is libwebp-derived — Google maintains both). We mirror that
// architecture: this class accepts the raw WebP bytes and returns a
// DecodedImage with .rgba populated in RGBA scan order.
//
// Supports (per libwebp capabilities):
//   * Lossy (VP8) WebP
//   * Lossless (VP8L) WebP
//   * Extended (VP8X) WebP — alpha, animation, ICC, etc. For animated
//     WebPs we decode the FIRST frame only (frame animation is the
//     RLottie/AnimatedDrawable domain — see §7).
//   * Alpha transparency
//   * Truncated input → ok=false with descriptive error
//
// libwebp is a mature, BSD-licensed reference implementation (per §13
// "do not re-research already-proven POCs"); we use it as-is.
class WebPDecoder {
public:
    static DecodedImage decode(const std::vector<uint8_t>& webp_bytes);
    static DecodedImage decode_file(const std::string& path);
};

// EXP-097 §6: JPEGDecoder — wraps libjpeg (the IJG reference decoder).
//
// Per AOSP `BitmapFactory`: JPEG decoding is delegated to libjpeg
// (Android's libjpeg-turbo fork). We use the system libjpeg (standard
// IJG reference); the API surface is identical for decode.
//
// Supports:
//   * Baseline JPEG (sequential, JFIF 1.01)
//   * Progressive JPEG (multiple scans — auto-handled by libjpeg)
//   * Grayscale and color (YCbCr) JPEG
//   * CMYK/Adobe APP14 (auto-converted to RGB by libjpeg)
//   * Truncated input → ok=false with descriptive error (libjpeg's
//     error manager longjmps out on fatal errors; we set up the
//     jmp_buf so a fatal error returns control rather than crashing)
class JPEGDecoder {
public:
    static DecodedImage decode(const std::vector<uint8_t>& jpeg_bytes);
    static DecodedImage decode_file(const std::string& path);
};

// EXP-097 §7: RLottieDecoder — rlottie-backed Lottie JSON → RGBA decoder.
//
// Per AOSP `BitmapFactory` and Telegram's RLottieDrawable: animated vector
// graphics (Lottie) are rendered to a Bitmap on each frame. rlottie is
// Samsung's reference C++ implementation (MIT-licensed) — Telegram and
// many other Android apps use it directly.
//
// This class wraps rlottie's C API:
//   1. lottie_animation_from_data(json_str, key, "") — parse the Lottie JSON
//   2. lottie_animation_get_size/totalframe/framerate — query animation props
//   3. lottie_animation_render(anim, frame, buffer, w, h, stride) — render
//      ONE frame to an RGBA buffer
//
// For a static render pass (the runtime's current model), we render frame 0
// of the FIRST animation encountered. For animated WebPs/GIFs the future
// AnimatedDrawable infrastructure will request successive frames.
class RLottieDecoder {
public:
    struct DecodedAnim {
        int width = 0;
        int height = 0;
        int total_frames = 0;
        double frame_rate = 0.0;
        std::vector<uint32_t> frames_rgba;  // width*height*4 per frame, concatenated
        bool ok = false;
        std::string error;
        std::string name;  // animation name (Lottie "nm" field, for diagnostics)
    };

    // Decode the first N frames of a Lottie animation.
    //   json_str:   raw Lottie JSON (Telegram stores it as `res/*.json`)
    //   max_frames: cap (e.g. 3 for frame_000/001/002 evidence; -1 for all)
    //   target_w/h: render size in pixels (Telegram uses dp(64), etc.)
    static DecodedAnim decode(const std::string& json_str,
                              int target_w, int target_h,
                              int max_frames = 3);
    static DecodedAnim decode_file(const std::string& path,
                                   int target_w, int target_h,
                                   int max_frames = 3);
};

} // namespace renderer
} // namespace miniandroid

#endif // MINIANDROID_SOFTWARE_RENDERER_H
