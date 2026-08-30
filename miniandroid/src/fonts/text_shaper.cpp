/*
 * UNIFIED_007 — TextShaper implementation.
 * FriBidi → HarfBuzz → FreeType → framebuffer alpha blit.
 * See text_shaper.h for the design contract.
 */

#include "text_shaper.h"

#include <ft2build.h>
#include FT_FREETYPE_H
#include FT_GLYPH_H
#include <harfbuzz/hb.h>
#include <harfbuzz/hb-ft.h>
#include <fribidi/fribidi.h>

#include <cmath>
#include <cstring>
#include <cstdio>
#include <functional>

namespace miniandroid {
namespace fonts {

// ---------------------------------------------------------------------------
// UTF-8 → UTF-32 (permissive but correct for well-formed input)
// ---------------------------------------------------------------------------
static std::u32string utf8_to_u32(const std::string& s) {
    std::u32string out;
    out.reserve(s.size());
    size_t i = 0;
    while (i < s.size()) {
        uint32_t cp = (unsigned char)s[i];
        int extra = (cp < 0x80) ? 0 : (cp < 0xE0 ? 1 : (cp < 0xF0 ? 2 : 3));
        if (cp >= 0x80) {
            if (cp < 0xE0)      cp &= 0x1F;
            else if (cp < 0xF0) cp &= 0x0F;
            else                cp &= 0x07;
        }
        bool bad = false;
        for (int k = 0; k < extra; ++k) {
            if (i + 1 >= s.size() || ((unsigned char)s[i + 1] & 0xC0) != 0x80) {
                bad = true; break;
            }
            cp = (cp << 6) | ((unsigned char)s[++i] & 0x3F);
        }
        if (bad) { ++i; continue; }
        out.push_back(cp);
        ++i;
    }
    return out;
}

TextShaper& TextShaper::instance() {
    static TextShaper inst;
    return inst;
}

TextShaper::TextShaper() {
    if (FT_Init_FreeType(reinterpret_cast<FT_Library*>(&ft_lib_))) {
        std::fprintf(stderr, "[TEXTSHAPER] FT_Init_FreeType FAILED\n");
        return;
    }
    available_ = true;
    if (!load_face(kFaceRegular,  font_paths_[kFaceRegular].c_str()))  available_ = false;
    if (!load_face(kFaceBold,    font_paths_[kFaceBold].c_str())) {
        // Bold missing is not fatal — fall back to regular metrics.
        faces_[kFaceBold].ft_face = faces_[kFaceRegular].ft_face;
        faces_[kFaceBold].path = font_paths_[kFaceRegular];
        faces_[kFaceBold].units_per_em = faces_[kFaceRegular].units_per_em;
    }
    if (!load_face(kFaceFallback, font_paths_[kFaceFallback].c_str())) {
        faces_[kFaceFallback].ft_face = faces_[kFaceRegular].ft_face;
        faces_[kFaceFallback].path = font_paths_[kFaceRegular];
        faces_[kFaceFallback].units_per_em = faces_[kFaceRegular].units_per_em;
    }
    // Emoji face (optional): NotoColorEmoji is a CBDT bitmap font with fixed
    // strikes. Pick the closest strike to typical UI text sizes.
    if (load_face(kFaceEmoji, font_paths_[kFaceEmoji].c_str())) {
        FT_Face ef = reinterpret_cast<FT_Face>(faces_[kFaceEmoji].ft_face);
        if (ef->num_fixed_sizes > 0) {
            int best = 0, bestd = 1 << 30;
            for (int i = 0; i < ef->num_fixed_sizes; ++i) {
                // FT_Bitmap_Size.size is 26.6 fixed point → convert to px.
                int sz = ef->available_sizes[i].size >> 6;
                int d = std::abs(sz - 64);
                if (d < bestd) { bestd = d; best = i; }
            }
            FT_Select_Size(ef, best);
            emoji_strike_px_ = ef->available_sizes[best].size >> 6;
            emoji_available_ = true;
        }
    }
    if (available_) {
        std::fprintf(stderr,
            "[TEXTSHAPER] READY primary=%s bold=%s fallback=%s emoji=%s(strike=%d)\n",
            faces_[kFaceRegular].path.c_str(),
            faces_[kFaceBold].path.c_str(),
            faces_[kFaceFallback].path.c_str(),
            emoji_available_ ? faces_[kFaceEmoji].path.c_str() : "none",
            emoji_strike_px_);
    }
}

TextShaper::~TextShaper() {
    for (auto& kv : hb_fonts_) {
        if (kv.second) hb_font_destroy(reinterpret_cast<hb_font_t*>(kv.second));
    }
    for (int i = 0; i < 3; ++i) {
        // Only destroy faces we own (distinguish by path equality is fine here;
        // duplicates were aliased, FT_Done_Face on aliased face would double-free,
        // so we track ownership by comparing pointers).
    }
    // Collect unique faces and destroy each once.
    FT_Face r = reinterpret_cast<FT_Face>(faces_[kFaceRegular].ft_face);
    FT_Face b = reinterpret_cast<FT_Face>(faces_[kFaceBold].ft_face);
    FT_Face f = reinterpret_cast<FT_Face>(faces_[kFaceFallback].ft_face);
    FT_Face e = reinterpret_cast<FT_Face>(faces_[kFaceEmoji].ft_face);
    if (e && e != r && e != b && e != f) FT_Done_Face(e);
    if (f && f != r && f != b) FT_Done_Face(f);
    if (b && b != r) FT_Done_Face(b);
    if (r) FT_Done_Face(r);
    if (ft_lib_) FT_Done_FreeType(reinterpret_cast<FT_Library>(ft_lib_));
}

bool TextShaper::load_face(int idx, const char* path) {
    FT_Face face = nullptr;
    if (FT_New_Face(reinterpret_cast<FT_Library>(ft_lib_), path, 0, &face)) {
        std::fprintf(stderr, "[TEXTSHAPER] FT_New_Face FAILED path=%s\n", path);
        return false;
    }
    faces_[idx].ft_face = face;
    faces_[idx].units_per_em = face->units_per_EM;
    faces_[idx].path = path;
    return true;
}

uint64_t TextShaper::hash_string(const std::string& s, float size_px, bool bold) const {
    uint64_t h = 1469598103934665603ull;
    auto mix = [&h](uint8_t byte) {
        h ^= byte; h *= 1099511628211ull;
    };
    for (char c : s) mix((uint8_t)c);
    mix(0xFF);
    uint32_t sz = (uint32_t)std::lround(size_px * 4.0f);
    for (int k = 0; k < 4; ++k) mix((uint8_t)(sz >> (8 * k)));
    mix(bold ? 1 : 0);
    return h;
}

// ---------------------------------------------------------------------------
// shape(): bidi + shaping + metrics (glyph rasters NOT generated here)
// ---------------------------------------------------------------------------
const ShapedText& TextShaper::shape(const std::string& utf8, float size_px,
                                    bool bold) {
    std::lock_guard<std::mutex> lock(mtx_);
    uint64_t key = hash_string(utf8, size_px, bold);
    auto it = shape_cache_.find(key);
    if (it != shape_cache_.end()) return it->second;

    ShapedText result;
    if (!available_ || utf8.empty()) {
        auto res = shape_cache_.emplace(key, std::move(result));
        return res.first->second;
    }

    int face_idx = bold ? kFaceBold : kFaceRegular;
    FT_Face face = reinterpret_cast<FT_Face>(faces_[face_idx].ft_face);
    if (!face) face = reinterpret_cast<FT_Face>(faces_[kFaceRegular].ft_face);

    // Fixed pixel size — size_px is exactly the em size in px (26.6 fixed).
    FT_Set_Pixel_Sizes(face, 0, (FT_UInt)std::lround(size_px));

    // Font metrics at this size.
    result.ascent  = (float)(face->size->metrics.ascender  >> 6);
    result.descent = (float)(-(face->size->metrics.descender >> 6));
    if (result.ascent <= 0)  result.ascent  = size_px * 0.9f;
    if (result.descent <= 0) result.descent = size_px * 0.25f;

    // hb_font for this face+size.
    uint32_t sz26 = (uint32_t)std::lround(size_px * 64.0f);
    uint64_t hfkey = ((uint64_t)face_idx << 48) ^ sz26;
    hb_font_t* hb_font = nullptr;
    auto hfit = hb_fonts_.find(hfkey);
    if (hfit != hb_fonts_.end()) {
        hb_font = reinterpret_cast<hb_font_t*>(hfit->second);
    } else {
        hb_font = hb_ft_font_create(face, nullptr);
        hb_fonts_[hfkey] = hb_font;
    }
    if (!hb_font) {
        std::fprintf(stderr, "[TEXTSHAPER] hb_ft_font_create FAILED size=%.1f\n", size_px);
        auto res = shape_cache_.emplace(key, std::move(result));
        return res.first->second;
    }
    // NOTE: hb_ft_font_create adopts the face's current scale — no explicit
    // hb_ft_font_set_scale call (API removed in newer HarfBuzz).

    // UTF-8 → UTF-32.
    std::u32string u32 = utf8_to_u32(utf8);
    std::vector<FriBidiChar> src(u32.begin(), u32.end());

    // FriBidi: first-strong base direction.
    FriBidiParType base = FRIBIDI_PAR_LTR;
    for (FriBidiChar ch : src) {
        FriBidiCharType t = fribidi_get_bidi_type(ch);
        if (t == FRIBIDI_TYPE_R || t == FRIBIDI_TYPE_AL) { base = FRIBIDI_PAR_RTL; break; }
        if (t == FRIBIDI_TYPE_L) break;
    }
    result.rtl_base = (base == FRIBIDI_PAR_RTL);

    // Visual reorder (handles embedded opposite-direction segments).
    std::vector<FriBidiChar> vis(src.size() + 1);
    FriBidiLevel lvl = fribidi_log2vis(src.data(), (FriBidiStrIndex)src.size(),
                                       &base, vis.data(), nullptr, nullptr, nullptr);
    if (lvl < 0) {
        // Reorder failed — use logical order as-is (degraded but functional).
        vis.assign(src.begin(), src.end());
    }

    // HarfBuzz shaping of the VISUAL sequence.
    hb_buffer_t* buf = hb_buffer_create();
    hb_buffer_add_utf32(buf, vis.data(), (int)vis.size(), 0, -1);
    hb_buffer_guess_segment_properties(buf);
    hb_shape(hb_font, buf, nullptr, 0);

    unsigned gn = 0;
    hb_glyph_info_t* gi = hb_buffer_get_glyph_infos(buf, &gn);
    hb_glyph_position_t* gp = hb_buffer_get_glyph_positions(buf, nullptr);

    result.glyphs.reserve(gn);
    for (unsigned k = 0; k < gn; ++k) {
        ShapedGlyph g;
        g.glyph_id  = gi[k].codepoint;
        g.cluster   = gi[k].cluster;
        g.x_advance = (float)(gp[k].x_advance >> 6);
        g.x_offset  = (float)(gp[k].x_offset >> 6);
        g.y_offset  = (float)(gp[k].y_offset >> 6);
        if (g.glyph_id == 0) result.notdef_count++;
        result.glyphs.push_back(g);
        result.width += g.x_advance;
    }
    hb_buffer_destroy(buf);

    // ------------------------------------------------------------------
    // Emoji fallback (Android font-chain behavior): for every primary
    // .notdef, try NotoColorEmoji at the same cluster. Advances come from
    // the emoji shaping scaled to the requested size.
    // ------------------------------------------------------------------
    if (result.notdef_count > 0 && emoji_available_ && emoji_strike_px_ > 0) {
        FT_Face eface = reinterpret_cast<FT_Face>(faces_[kFaceEmoji].ft_face);
        uint32_t esz26 = (uint32_t)emoji_strike_px_ * 64;
        uint64_t ehkey = ((uint64_t)kFaceEmoji << 48) ^ esz26;
        hb_font_t* ehb = nullptr;
        auto eit = hb_fonts_.find(ehkey);
        if (eit != hb_fonts_.end()) ehb = reinterpret_cast<hb_font_t*>(eit->second);
        else { ehb = hb_ft_font_create(eface, nullptr); hb_fonts_[ehkey] = ehb; }
        if (ehb) {
            hb_buffer_t* ebuf = hb_buffer_create();
            hb_buffer_add_utf32(ebuf, vis.data(), (int)vis.size(), 0, -1);
            hb_buffer_guess_segment_properties(ebuf);
            hb_shape(ehb, ebuf, nullptr, 0);
            unsigned en = 0;
            hb_glyph_info_t* egi = hb_buffer_get_glyph_infos(ebuf, &en);
            hb_glyph_position_t* egp = hb_buffer_get_glyph_positions(ebuf, nullptr);
            float scale = size_px / (float)emoji_strike_px_;
            std::unordered_map<uint32_t, uint32_t> cluster_to_emoji_gid;
            std::unordered_map<uint32_t, float> cluster_to_emoji_adv;
            for (unsigned k = 0; k < en; ++k) {
                if (egi[k].codepoint != 0) {
                    cluster_to_emoji_gid[egi[k].cluster] = egi[k].codepoint;
                    cluster_to_emoji_adv[egi[k].cluster] = (float)(egp[k].x_advance >> 6) * scale;
                }
            }
            hb_buffer_destroy(ebuf);
            for (auto& g : result.glyphs) {
                if (g.glyph_id == 0) {
                    auto fit = cluster_to_emoji_gid.find(g.cluster);
                    if (fit != cluster_to_emoji_gid.end()) {
                        g.use_emoji = true;
                        g.emoji_gid = fit->second;
                        g.emoji_scale = scale;
                        auto ait = cluster_to_emoji_adv.find(g.cluster);
                        if (ait != cluster_to_emoji_adv.end()) {
                            result.width += ait->second - g.x_advance;
                            g.x_advance = ait->second;
                        }
                        result.notdef_count--;
                    }
                }
            }
        }
    }

    auto res = shape_cache_.emplace(key, std::move(result));
    return res.first->second;
}

float TextShaper::line_height(float size_px, bool bold) const {
    (void)bold;
    // Android-style leading: ascent + descent plus a small gap.
    return size_px * 1.2f;
}

// ---------------------------------------------------------------------------
// glyph raster cache: (face, size, gid) → 8-bit coverage bitmap
// ---------------------------------------------------------------------------
static uint64_t raster_key(int face_idx, float size_px, uint32_t gid) {
    uint32_t szq = (uint32_t)std::lround(size_px * 4.0f);
    return ((uint64_t)(uint32_t)face_idx << 56)
         ^ ((uint64_t)(szq & 0xFFFFFF) << 24)
         ^ (uint64_t)(gid & 0xFFFFFF);
}

static bool raster_glyph(FT_Face face, uint32_t gid, float size_px,
                         RasterPub* out, bool want_color = false) {
    if (want_color) {
        // CBDT/CBLC color bitmap path (NotoColorEmoji). The face is already
        // FT_Select_Size'd to the chosen strike; do NOT call Set_Pixel_Sizes.
        if (FT_Load_Glyph(face, gid, FT_LOAD_COLOR)) return false;
        FT_GlyphSlot g = face->glyph;
        FT_Bitmap& bm = g->bitmap;
        if (bm.pixel_mode != FT_PIXEL_MODE_BGRA) {
            // No color bitmap at this gid — signal caller to try grayscale.
            return false;
        }
        out->color = true;
        out->w = (int)bm.width;
        out->h = (int)bm.rows;
        out->left = g->bitmap_left;
        out->top = g->bitmap_top;
        out->bgra.assign((size_t)bm.width * bm.rows * 4, 0);
        for (unsigned ry = 0; ry < bm.rows; ++ry) {
            memcpy(&out->bgra[(size_t)ry * bm.width * 4],
                   bm.buffer + (size_t)ry * bm.pitch,
                   (size_t)bm.width * 4);
        }
        return true;
    }
    if (FT_Set_Pixel_Sizes(face, 0, (FT_UInt)std::lround(size_px))) return false;
    if (FT_Load_Glyph(face, gid, FT_LOAD_DEFAULT)) return false;
    if (FT_Render_Glyph(face->glyph, FT_RENDER_MODE_NORMAL)) return false;
    FT_GlyphSlot g = face->glyph;
    FT_Bitmap& bm = g->bitmap;
    out->w = (int)bm.width;
    out->h = (int)bm.rows;
    out->left = g->bitmap_left;
    out->top = g->bitmap_top;
    out->color = false;
    out->alpha.assign((size_t)out->w * out->h, 0);
    if (bm.buffer) {
        for (int ry = 0; ry < out->h; ++ry) {
            for (int rx = 0; rx < out->w; ++rx) {
                uint8_t a;
                if (bm.pixel_mode == FT_PIXEL_MODE_GRAY) {
                    a = bm.buffer[(size_t)ry * bm.pitch + rx];
                } else if (bm.pixel_mode == FT_PIXEL_MODE_MONO) {
                    const uint8_t* row = bm.buffer + (size_t)ry * bm.pitch;
                    a = ((row[rx >> 3] >> (7 - (rx & 7))) & 1) ? 255 : 0;
                } else {
                    a = bm.buffer[(size_t)ry * bm.pitch + rx];
                }
                out->alpha[(size_t)ry * out->w + rx] = a;
            }
        }
    }
    return true;
}

// ---------------------------------------------------------------------------
// draw(): shape + raster + alpha-blend blit
// ---------------------------------------------------------------------------
void TextShaper::draw(renderer::FrameBuffer& fb, const std::string& utf8,
                      float x, float y_baseline, float size_px,
                      const renderer::RGBA& color, bool bold) {
    const ShapedText& st = shape(utf8, size_px, bold);
    if (!available_ || st.glyphs.empty()) return;

    int face_idx = bold ? kFaceBold : kFaceRegular;
    FT_Face face = reinterpret_cast<FT_Face>(faces_[face_idx].ft_face);
    if (!face) face = reinterpret_cast<FT_Face>(faces_[kFaceRegular].ft_face);
    FT_Face eface = reinterpret_cast<FT_Face>(faces_[kFaceEmoji].ft_face);

    std::lock_guard<std::mutex> lock(mtx_);
    float pen_x = x;
    for (const auto& g : st.glyphs) {
        if (g.use_emoji && emoji_available_ && eface) {
            // ----- color emoji (CBDT) path -----
            uint64_t rk = raster_key(kFaceEmoji, (float)emoji_strike_px_, g.emoji_gid);
            auto rit = rasters_.find(rk);
            if (rit == rasters_.end()) {
                RasterPub pub;
                if (raster_glyph(eface, g.emoji_gid, (float)emoji_strike_px_, &pub,
                                 /*want_color=*/true)) {
                    rit = rasters_.emplace(rk, std::move(pub)).first;
                }
            }
            if (rit != rasters_.end()) {
                const auto& r = rit->second;
                // Scale strike bitmap down to requested size (nearest).
                int dw = std::max(1, (int)std::lround(r.w * g.emoji_scale));
                int dh = std::max(1, (int)std::lround(r.h * g.emoji_scale));
                int gx = (int)std::lround(pen_x + g.x_offset);
                int gy = (int)std::lround(y_baseline - g.y_offset)
                       - (int)std::lround(r.top * g.emoji_scale) - dh / 4;
                for (int dy = 0; dy < dh; ++dy) {
                    int sy = (dy * r.h) / dh;
                    for (int dx = 0; dx < dw; ++dx) {
                        int sx = (dx * r.w) / dw;
                        const uint8_t* p = &r.bgra[(sy * r.w + sx) * 4];
                        // FreeType CBDT: premultiplied BGRA.
                        uint8_t a = p[3];
                        if (!a) continue;
                        uint8_t b = std::min(255, (int)p[0] * 255 / a);
                        uint8_t gr = std::min(255, (int)p[1] * 255 / a);
                        uint8_t rr = std::min(255, (int)p[2] * 255 / a);
                        fb.set_pixel(gx + dx, gy + dy,
                                     renderer::RGBA{rr, gr, b, a});
                    }
                }
            }
            pen_x += g.x_advance;
            continue;
        }
        // ----- grayscale path -----
        uint64_t rk = raster_key(face_idx, size_px, g.glyph_id);
        auto rit = rasters_.find(rk);
        if (rit == rasters_.end()) {
            RasterPub pub;
            if (raster_glyph(face, g.glyph_id, size_px, &pub)) {
                rit = rasters_.emplace(rk, std::move(pub)).first;
            }
        }
        if (rit != rasters_.end()) {
            const auto& r = rit->second;
            if (r.color) {
                // Color raster reached via grayscale key — blit as color.
                int gx = (int)std::lround(pen_x + g.x_offset);
                int gy = (int)std::lround(y_baseline - g.y_offset) - r.top;
                for (int ry = 0; ry < r.h; ++ry) {
                    for (int rx = 0; rx < r.w; ++rx) {
                        const uint8_t* p = &r.bgra[(ry * r.w + rx) * 4];
                        uint8_t a = p[3];
                        if (!a) continue;
                        uint8_t b = std::min(255, (int)p[0] * 255 / a);
                        uint8_t gr = std::min(255, (int)p[1] * 255 / a);
                        uint8_t rr = std::min(255, (int)p[2] * 255 / a);
                        fb.set_pixel(gx + rx, gy + ry, renderer::RGBA{rr, gr, b, a});
                    }
                }
            } else {
                int gx = (int)std::lround(pen_x + g.x_offset) + r.left;
                int gy = (int)std::lround(y_baseline - g.y_offset) - r.top;
                for (int ry = 0; ry < r.h; ++ry) {
                    for (int rx = 0; rx < r.w; ++rx) {
                        uint8_t a = r.alpha[(size_t)ry * r.w + rx];
                        if (!a) continue;
                        renderer::RGBA px = color;
                        px.a = (uint8_t)((px.a * a) / 255);
                        fb.set_pixel(gx + rx, gy + ry, px);
                    }
                }
            }
        }
        pen_x += g.x_advance;
    }
}

}  // namespace fonts
}  // namespace miniandroid
