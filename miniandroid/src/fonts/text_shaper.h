/*
 * UNIFIED_007 — Real text shaping backend (Priority: FONT pipeline).
 *
 * Replaces the 8x16 BitmapFont (known advance bug, ASCII-only, no RTL)
 * with the FULL production pipeline used by Android:
 *
 *     UTF-8 → UTF-32 → FriBidi (bidi levels + visual reorder)
 *           → HarfBuzz (shaping, ligatures, Arabic joining)
 *           → FreeType (glyph rasterization, hinting)
 *           → alpha-blended blit into the software framebuffer
 *
 * Everything is cached:
 *   - FT faces loaded once (DejaVuSans, DejaVuSans-Bold, FreeSerif fallback)
 *   - hb_font_t per (face, pixel size)
 *   - glyph alpha rasters per (face, size, glyph id)
 *
 * NO fake data: missing font files or zero glyphs are reported via
 * available()/shape() results and stderr diagnostics.
 */

#ifndef MINIANDROID_TEXT_SHAPER_H
#define MINIANDROID_TEXT_SHAPER_H

#include "../renderer/software_renderer.h"
#include <cstdint>
#include <string>
#include <vector>
#include <unordered_map>
#include <mutex>

namespace miniandroid {
namespace fonts {

struct ShapedGlyph {
    uint32_t glyph_id = 0;
    uint32_t cluster = 0;       // index into logical u32 sequence
    float x_advance = 0.0f;     // px
    float x_offset = 0.0f;      // px
    float y_offset = 0.0f;      // px
    // Emoji fallback (Android font-chain behavior): when the primary face
    // produced .notdef and the emoji face covers the cluster, this glyph is
    // drawn from NotoColorEmoji (CBDT color bitmap) instead.
    bool use_emoji = false;
    uint32_t emoji_gid = 0;
    float emoji_scale = 1.0f;   // requested_px / emoji_strike_px
};

struct ShapedText {
    std::vector<ShapedGlyph> glyphs;  // VISUAL order (left→right pen flow)
    float width = 0.0f;               // total advance in px
    float ascent = 0.0f;              // px above baseline
    float descent = 0.0f;             // px below baseline (positive)
    bool rtl_base = false;            // first-strong base direction
    size_t notdef_count = 0;
};

// Public raster struct (used internally by the cache; exposed for tests).
struct RasterPub {
    std::vector<uint8_t> alpha;      // 8-bit coverage (grayscale path)
    std::vector<uint8_t> bgra;       // 4-byte premultiplied BGRA (color path)
    bool color = false;
    int w = 0, h = 0, left = 0, top = 0;
};

class TextShaper {
public:
    static TextShaper& instance();

    // true when at least one font face loaded successfully.
    bool available() const { return available_; }

    // Shape a single line of UTF-8 text at a pixel size. Returns metrics.
    const ShapedText& shape(const std::string& utf8, float size_px,
                            bool bold = false);

    float line_height(float size_px, bool bold = false) const;

    // Draw shaped text. (x, y_baseline) = pen origin. Alpha-blends onto fb.
    void draw(renderer::FrameBuffer& fb, const std::string& utf8,
              float x, float y_baseline, float size_px,
              const renderer::RGBA& color, bool bold = false);

    std::string primary_font_path() const { return font_paths_[0]; }
    size_t raster_cache_size() const { return rasters_.size(); }

private:
    TextShaper();
    ~TextShaper();
    TextShaper(const TextShaper&) = delete;
    TextShaper& operator=(const TextShaper&) = delete;

    static constexpr int kFaceRegular = 0;
    static constexpr int kFaceBold = 1;
    static constexpr int kFaceFallback = 2;  // FreeSerif (wide coverage)
    static constexpr int kFaceEmoji = 3;     // NotoColorEmoji (CBDT)

    bool load_face(int idx, const char* path);

    struct Face {
        void* ft_face = nullptr;   // FT_Face
        int units_per_em = 0;
        std::string path;
    };
    Face faces_[4];
    bool available_ = false;
    bool emoji_available_ = false;
    int emoji_strike_px_ = 0;   // CBDT fixed strike size (e.g. 128)

    void* ft_lib_ = nullptr;      // FT_Library

    // hb_font_t cache: key = face_idx * 0x1000000 + size26_6
    std::unordered_map<uint64_t, void*> hb_fonts_;

    // glyph raster cache: key = (face_idx<<56) ^ (size_q6<<24) ^ gid
    std::unordered_map<uint64_t, RasterPub> rasters_;

    std::mutex mtx_;
    // memoized shape results: hash(utf8, size, bold) → ShapedText
    std::unordered_map<uint64_t, ShapedText> shape_cache_;
    uint64_t hash_string(const std::string& s, float size_px, bool bold) const;

    std::string font_paths_[4] = {
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
        "/usr/share/fonts/truetype/emoji/NotoColorEmoji.ttf",
    };
};

}  // namespace fonts
}  // namespace miniandroid

#endif  // MINIANDROID_TEXT_SHAPER_H
