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
    // R-NEW-398 (S78, F-153): CJK fallback — same font-chain pattern as the
    // emoji fields: when the primary face has no glyph for the cluster, the
    // glyph id from the CJK fallback face (single-codepoint ideographs, no
    // complex shaping) is drawn from kFaceCJK instead.
    bool use_cjk = false;
    uint32_t cjk_gid = 0;
    // F-NEW-422 (CONT-101 T5): general script fallback (AOSP fonts.xml
    // chain tail). When the emoji and CJK arms did not claim a .notdef
    // cluster and the wide-coverage fallback face (FreeSerif — Arabic,
    // Hebrew, extended Cyrillic/Greek, …) shapes a REAL glyph for it, the
    // glyph is drawn from kFaceFallback. Arabic joining forms come from
    // the fallback's GSUB via the hb re-shape (not a plain charmap swap).
    bool use_fallback = false;
    uint32_t fallback_gid = 0;
};

struct ShapedText {
    std::vector<ShapedGlyph> glyphs;  // VISUAL order (left→right pen flow)
    float width = 0.0f;               // total advance in px
    float ascent = 0.0f;              // px above baseline
    float descent = 0.0f;             // px below baseline (positive)
    bool rtl_base = false;            // first-strong base direction
    size_t notdef_count = 0;
};

// ---------------------------------------------------------------------------
// TextLayout — word-wrapped line layout computed from REAL shaped advances.
//
// This is the SINGLE SOURCE OF TRUTH for text geometry: both the layout
// measure pass (LayoutInflater::measure_layout) and the render draw path
// (ExecutionEngine view walk) call layout_text() so measured geometry and
// painted pixels can never disagree. No fixed character-width estimates.
//
// Android semantics mirrored (TextView / StaticLayout, simplified but
// honest): explicit '\n' always breaks; greedy word wrap on spaces against
// max_width_px; trailing spaces do not count toward line width; max_lines
// caps the block (0/negative = unlimited).
// ---------------------------------------------------------------------------
struct TextLayoutLine {
    std::string text;    // logical-order UTF-8 of the line (trimmed of the
                         // wrapping space)
    float width = 0.0f;  // shaped advance width in px
};

struct TextLayout {
    std::vector<TextLayoutLine> lines;
    float line_height = 0.0f;     // ascent + descent + leading (single-line box)
    float ascent = 0.0f;          // px above baseline (POSITIVE magnitude)
    float descent = 0.0f;         // px below baseline (positive)
    float max_line_width = 0.0f;  // longest line advance (desired width)
    // G36/G47 — AOSP StaticLayout per-line law (staticlayout_line_boxes):
    //   baseline_k = v_k + line_above[k];  v_{k+1} = v_k + line_boxes[k].
    //   line_above is the POSITIVE px from the line-box top to the baseline
    //   (|fm.top| for the first line with includeFontPadding, else |fm.ascent|).
    //   line_boxes[k] = the full box height of line k (multiplier applied).
    std::vector<float> line_above;
    std::vector<float> line_boxes;
    float block_height() const {
        float h = 0;
        for (float b : line_boxes) h += b;
        return h;
    }
};

// Face tokens shared by shape()/draw()/layout_text().
//   FACE_REGULAR / FACE_BOLD / FACE_APP (app-provided family from APK
//   assets, registered via register_app_font) — see TextShaper below.
constexpr int FACE_SYSTEM = -1;  // legacy: system family (regular/bold by flag)
constexpr int FACE_APP = -2;     // app-provided family (APK assets/fonts)

// -----------------------------------------------------------------------
// G36 — Android Paint.FontMetrics equivalent, from the resolved face at a
// pixel size. AOSP semantics (Paint.java / StaticLayout.java at
// android-14.0.0_r50, StaticLayout.out()):
//   ascent/descent — the single-spaced line box of the run's fonts
//                    (hhea-scaled; FreeType size metrics, which honor the
//                    OS/2 USE_TYPO_METRICS flag exactly like hb/AOSP).
//   top/bottom     — the maximum extents: with includeFontPadding=true
//                    (the TextView default) the FIRST line box uses top
//                    and the LAST line box uses bottom instead of
//                    ascent/descent. For faces where the full extents
//                    equal the single-spaced extents (e.g. DroidSansMono:
//                    hhea lineGap=0, win≈hhea) top==ascent and
//                    bottom==descent.
//   leading        — bottom - descent + top - ascent (0 for gap-less fonts).
// All values in px, ascent/top NEGATIVE, descent/bottom/leading POSITIVE.
// -----------------------------------------------------------------------
struct FontMetrics {
    float ascent = 0, descent = 0, top = 0, bottom = 0, leading = 0;
};

// -----------------------------------------------------------------------
// G47 — AOSP StaticLayout line-box law (StaticLayout.java out(),
// android-14.0.0_r50), verbatim semantics for a run of N identical-metric
// lines:
//   line box above/below = font metrics ascent/descent,
//   with includePad: first line above = top, last line below = bottom,
//   extra_k = (below_k - above_k) * (spacingMult - 1) + spacingAdd for
//             every line EXCEPT the last (the last line gets NO extra),
//   next v += (below + extra) - above.
// Returns the per-line box heights (px). boxes.size() == line_count.
// -----------------------------------------------------------------------
std::vector<float> staticlayout_line_boxes(int line_count,
                                           const FontMetrics& fm,
                                           float spacing_mult, float spacing_add,
                                           bool include_pad);
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
    // face_idx: FACE_SYSTEM (default system family, bold selects the bold
    // face) or an index returned by register_app_font().
    const ShapedText& shape(const std::string& utf8, float size_px,
                            bool bold = false, int face_idx = FACE_SYSTEM);

    float line_height(float size_px, bool bold = false) const;

    // Vertical metrics for the resolved face at size_px.
    void metrics(float size_px, bool bold, int face_idx,
                 float* ascent, float* descent, float* line_height) const;

    // G32/G36 — FULL Android-style FontMetrics for the resolved face.
    FontMetrics font_metrics(float size_px, bool bold, int face_idx) const;

    // G32 — family resolution (AOSP fonts.xml law, system families):
    //   "monospace" / "sans-serif-monospace" / "monaco" -> DroidSansMono face
    //   "serif"                                          -> serif fallback face
    //   "sans-serif"/"sans"/""/unknown                   -> default sans face
    // Unknown names are reported on stderr (no silent substitution).
    int resolve_family(const std::string& family, bool bold) const;
    bool has_family(const std::string& family) const;
    std::string monospace_font_path() const { return font_paths_[kFaceMonospace]; }

    // Draw shaped text. (x, y_baseline) = pen origin. Alpha-blends onto fb.
    void draw(renderer::FrameBuffer& fb, const std::string& utf8,
              float x, float y_baseline, float size_px,
              const renderer::RGBA& color, bool bold = false,
              int face_idx = FACE_SYSTEM);

    // -----------------------------------------------------------------
    // App-provided font family (generic APK asset path — AOSP
    // Typeface.createFromAsset equivalence, no app special-casing).
    // register_app_font_memory() loads the face directly from APK-extracted
    // bytes; register_app_font() is the file-path convenience wrapper.
    // is_bold selects which face of the registered family answers bold
    // requests. Returns the face index (negative on failure — callers fall
    // back to the system family).
    // -----------------------------------------------------------------
    int register_app_font_memory(const std::vector<uint8_t>& bytes,
                                 const std::string& debug_name, bool is_bold);
    int register_app_font(const std::string& font_path, bool is_bold);
    // cont70 ANT-6: resolve a registered app face by its APK-entry name.
    // AOSP Typeface.createFromAsset needs the face for an asset path; the
    // startup scan (FIX-4 + F-NEW-315) registers under the full entry name
    // ("assets/fonts/x.ttf", "res/UJ.ttf") — match exact first, then by
    // "/<name>" suffix (callers pass "fonts/x.ttf"). Deterministic: first
    // registration-order match. Returns -1 when absent.
    int app_face_index_for_name(const std::string& name) const;
    bool has_app_font() const { return app_regular_idx_ >= 0 || app_bold_idx_ >= 0; }
    int app_regular_idx() const { return app_regular_idx_; }
    int app_bold_idx() const { return app_bold_idx_; }
    size_t app_font_count() const { return app_faces_.size(); }

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
    static constexpr int kFaceMonospace = 4; // G32: DroidSansMono (AOSP fonts.xml)
    static constexpr int kFaceCJK = 5;       // R-NEW-398: CJK ideograph fallback
    static constexpr int kBaseFaceCount = 6;

    bool load_face(int idx, const char* path);
    public:
    // -----------------------------------------------------------------
    // FONT-PIPE-002 (#605) — font-load verification API. "How do you KNOW
    // a font really loaded?" has exactly one consumer-visible answer:
    // per-face truth + an ink-pixel render proof. No diagnostic may claim
    // a load it cannot demonstrate. (PUBLIC: the batteries and any
    // consumer verify through this surface.)
    // -----------------------------------------------------------------
    enum class FaceState { MISSING, LOADED, ALIASED };
    struct FaceInfo {
        int index = -1;
        FaceState state = FaceState::MISSING;
        int glyph_count = 0;      // FT num_glyphs of the backing face
        int units_per_em = 0;
        std::string path;         // real file path, or the alias source
    };
    FaceInfo face_info(int idx) const;
    int loaded_face_count() const;        // real (non-aliased) loaded faces
    uint32_t loaded_face_mask() const;    // bit i set = base face i LOADED
    std::string font_diagnostic_report() const;  // one line per face + verdict
    struct RenderProof {
        bool ok = false;          // glyph_count>0 && ink_pixels>0
        long ink_pixels = 0;      // blitted alpha coverage (honest ink)
        long glyph_count = 0;     // codepoints this face actually covered
        long notdef_count = 0;    // codepoints with no glyph in this face
        std::string detail;
    };
    // Shapes the string THROUGH THE NAMED FACE ONLY (bypasses the fallback
    // routing on purpose — this proves the face itself), rasterizes every
    // covered glyph via FreeType and counts the alpha ink actually written.
    RenderProof verify_text_renders(int idx, const std::string& utf8,
                                    float size_px) const;
    private:
    // FONT-PIPE-002 (#605): ordered per-face candidate search across the
    // common distro font-tree layouts (Debian truetype/, Fedora TTF/,
    // Arch, Noto's noto/ dir — the emoji face's old single pinned path
    // /usr/share/fonts/truetype/emoji/ does not exist on Debian, which
    // ships truetype/noto/). The canonical candidate stays FIRST so a
    // reproducible environment resolves identically everywhere. A genuine
    // miss is REPORTED (loud stderr + FileIoTrace row), never silently
    // aliased; aliased faces carry the honest flag below.
    bool load_face_first(int idx);

    struct Face {
        void* ft_face = nullptr;   // FT_Face
        int units_per_em = 0;
        std::string path;
        // FONT-PIPE-002 (#605): TRUE when this face is backed by ANOTHER
        // face's FT_Face (the optional-face missing-file alias — bold/
        // fallback/monospace fall back to the regular face so bold text
        // still renders). The flag makes the alias CONSUMER-VISIBLE
        // (face_info/loaded_face_count/font_diagnostic_report) instead of
        // the silent constructor substitution that used to mask real
        // shaping bugs as bare notdef counts.
        bool aliased = false;
        // For memory-loaded app faces: the byte buffer must outlive the face.
        std::shared_ptr<std::vector<uint8_t>> bytes;
    };
    Face faces_[kBaseFaceCount];
    // App-registered faces (APK assets/fonts) — dynamic.
    std::vector<Face> app_faces_;
    int app_regular_idx_ = -1;
    int app_bold_idx_ = -1;
    // §7 structured diagnostics: FONT_RESOLUTION emitted once per process.
    mutable bool font_resolved_logged_ = false;
    // Resolve FACE_SYSTEM / FACE_APP / concrete index → concrete face index.
    int resolve_face(bool bold, int face_idx) const;
    bool available_ = false;
    bool emoji_available_ = false;
    bool cjk_available_ = false;  // R-NEW-398
    // F-NEW-422 (CONT-101 T5): TRUE when kFaceFallback loaded a REAL face
    // (not the regular-face alias the ctor installs when the file is
    // missing) — the script-fallback reshaping arm then participates.
    bool fallback_available_ = false;
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

    std::string font_paths_[6] = {
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
        "/usr/share/fonts/truetype/emoji/NotoColorEmoji.ttf",
        // G32: AOSP system monospace (fonts.xml law). Loaded lazily from
        // the candidate dirs below; a missing file is reported, never
        // silently substituted.
        "runtime/data/fonts/DroidSansMono.ttf",
        // R-NEW-398 (S78, F-153): CJK ideograph fallback face (AOSP
        // fonts.xml fallback-chain law — missing CJK glyphs resolve through
        // a CJK-capable face, never tofu). Optional: absent file = loud
        // diagnostic, CJK strings then honestly report notdef.
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    };
};

// ---------------------------------------------------------------------------
// layout_text — word-wrapped block layout from REAL shaped advances.
// Shared by the layout measure pass and the render draw path so measured
// geometry and painted pixels always agree. face_idx as in shape().
// spacing_mult/add/include_pad follow the AOSP TextView/StaticLayout law
// (defaults = the TextView defaults: multiplier 1, extra 0, font padding ON).
// ellipsize: AOSP TextUtils.TruncateAt ordinal (0 NONE, 1 START, 2 MIDDLE,
// 3 END, 4 MARQUEE). NONE keeps the legacy over-wrap behavior; START/
// MIDDLE/END truncate the over-wide LAST drawn line with the U+2026
// ellipsis glyph per TextUtils.ellipsize (MG-073, S98).
// ---------------------------------------------------------------------------
TextLayout layout_text(const std::string& utf8, float size_px, bool bold,
                       float max_width_px, int max_lines = 0,
                       int face_idx = FACE_SYSTEM,
                       float spacing_mult = 1.0f, float spacing_add_px = 0.0f,
                       bool include_pad = true, bool elegant_height = false,
                       int ellipsize = 0);

}  // namespace fonts
}  // namespace miniandroid

#endif  // MINIANDROID_TEXT_SHAPER_H
