#!/usr/bin/env python3
"""FONT-PIPE-002 (#605) cpp patch part 2: load_face_first implementation +
the verification API implementations + the destructor leak fix.
Idempotent: skips when the marker is already present."""
import sys

P = sys.argv[1] if len(sys.argv) > 1 else \
    "/home/z/my-project/miniandroid/src/fonts/text_shaper.cpp"
s = open(P).read()

IMPL = r'''
// ---------------------------------------------------------------------------
// FONT-PIPE-002 (#605) — portable font resolution. Per-face ordered
// candidate tables: the canonical Debian path FIRST (reproducibility),
// then the other common distro layouts (Fedora TTF/, Arch flat, Noto's
// real Debian directory truetype/noto/ for the emoji face — the old
// single pinned path /usr/share/fonts/truetype/emoji/ never existed on
// Debian, so the color-emoji face could not load on this host at all).
// A genuine miss is REPORTED (loud stderr + FileIoTrace row) and never
// silently aliased; the constructor's optional-face aliases carry the
// honest Face::aliased flag instead.
// ---------------------------------------------------------------------------
namespace {
struct FaceCandidateTable {
    int idx;
    const char* name;
    const char* const* paths;
    size_t count;
};
const char* const kCandRegular[] = {
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",      // Debian/Ubuntu
    "/usr/share/fonts/TTF/dejavu/DejaVuSans.ttf",           // Fedora layout
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",               // flat layout
};
const char* const kCandBold[] = {
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
};
const char* const kCandFallback[] = {
    "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",     // Debian/Ubuntu
    "/usr/share/fonts/TTF/freefont/FreeSerif.ttf",          // Fedora layout
    "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf", // Noto fallback
};
const char* const kCandEmoji[] = {
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",    // Debian REAL dir
    "/usr/share/fonts/truetype/emoji/NotoColorEmoji.ttf",   // legacy pinned
    "/usr/share/fonts/noto/NotoColorEmoji.ttf",             // flat layout
};
const char* const kCandCJK[] = {
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",         // Debian/Ubuntu
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",    // Arch layout
};
const FaceCandidateTable kFaceTables[] = {
    {0, "regular",  kCandRegular,  3},
    {1, "bold",     kCandBold,     3},
    {2, "fallback", kCandFallback, 3},
    {3, "emoji",    kCandEmoji,    3},
    {5, "cjk",      kCandCJK,      4},
};
}  // namespace

bool TextShaper::load_face_first(int idx) {
    const FaceCandidateTable* t = nullptr;
    for (const auto& tab : kFaceTables)
        if (tab.idx == idx) { t = &tab; break; }
    if (!t) return false;  // monospace keeps its own exe-relative search
    size_t tried = 0;
    for (size_t i = 0; i < t->count; ++i) {
        const char* c = t->paths[i];
        std::FILE* fp = std::fopen(c, "rb");
        if (!fp) continue;                    // absent candidate: silent probe
        std::fclose(fp);
        ++tried;                              // exists on disk: really tried
        if (load_face(idx, c)) {
            font_paths_[idx] = c;             // record the winner
            return true;
        }
        // present but rejected by FreeType (corrupt/unparsed): try next
    }
    std::fprintf(stderr,
        "[TEXTSHAPER] %s face not found (searched %zu candidate paths) — "
        "REPORTED, never silently aliased\n", t->name, tried);
    miniandroid::diagnostics::FileIoTrace::instance().record(
        "FONT-FACE", t->name, false,
        "FONT-PIPE-002: all " + std::to_string(tried) +
            " candidates failed", "TextShaper");
    return false;
}

// ---------------------------------------------------------------------------
// FONT-PIPE-002 (#605) — the font-load verification API. The consumer-
// visible answer to "did this font REALLY load and render?"
// ---------------------------------------------------------------------------
TextShaper::FaceInfo TextShaper::face_info(int idx) const {
    FaceInfo fi;
    fi.index = idx;
    if (idx >= 0 && idx < kBaseFaceCount) {
        const Face& f = faces_[idx];
        if (!f.ft_face) { fi.state = FaceState::MISSING; return fi; }
        fi.state = f.aliased ? FaceState::ALIASED : FaceState::LOADED;
        fi.units_per_em = f.units_per_em;
        fi.path = f.path;
        fi.glyph_count =
            reinterpret_cast<FT_Face>(f.ft_face)->num_glyphs;
    } else if (idx >= kBaseFaceCount &&
               idx - kBaseFaceCount < (int)app_faces_.size()) {
        const Face& f = app_faces_[idx - kBaseFaceCount];
        if (!f.ft_face) { fi.state = FaceState::MISSING; return fi; }
        fi.state = FaceState::LOADED;         // app faces are never aliased
        fi.units_per_em = f.units_per_em;
        fi.path = f.path;
        fi.glyph_count =
            reinterpret_cast<FT_Face>(f.ft_face)->num_glyphs;
    }
    return fi;
}

int TextShaper::loaded_face_count() const {
    int n = 0;
    for (int i = 0; i < kBaseFaceCount; ++i)
        if (faces_[i].ft_face && !faces_[i].aliased) ++n;
    return n;
}

uint32_t TextShaper::loaded_face_mask() const {
    uint32_t m = 0;
    for (int i = 0; i < kBaseFaceCount; ++i)
        if (faces_[i].ft_face && !faces_[i].aliased) m |= (1u << i);
    return m;
}

std::string TextShaper::font_diagnostic_report() const {
    static const char* kNames[6] = {
        "regular", "bold", "fallback", "emoji", "monospace", "cjk" };
    std::string out = "FONT_DIAGNOSTIC v1 (FONT-PIPE-002)\n";
    for (int i = 0; i < kBaseFaceCount; ++i) {
        FaceInfo fi = face_info(i);
        const char* st = fi.state == FaceState::LOADED ? "LOADED"
                       : fi.state == FaceState::ALIASED ? "ALIASED"
                       : "MISSING";
        out += std::string("  face=") + kNames[i] + " state=" + st +
               " glyphs=" + std::to_string(fi.glyph_count) +
               " path=" + (fi.path.empty() ? "<none>" : fi.path) + "\n";
    }
    out += "FONT_DIAGNOSTIC SUMMARY loaded_faces=" +
           std::to_string(loaded_face_count()) + "/6 available=" +
           (available_ ? "1" : "0") + "\n";
    return out;
}

TextShaper::RenderProof TextShaper::verify_text_renders(
    int idx, const std::string& utf8, float size_px) const {
    RenderProof p;
    // The probe runs on a FRESH FT_Face loaded from the same backing data
    // so the shaper's cached hb_ft fonts (which reference the shared
    // faces' current size) can never be disturbed by a size change.
    FT_Face ft = nullptr;
    std::shared_ptr<std::vector<uint8_t>> keep_bytes;
    if (idx >= 0 && idx < kBaseFaceCount) {
        const Face& f = faces_[idx];
        if (f.aliased || !f.ft_face) {
            // aliased faces have no real file of their own: prove the
            // ALIAS SOURCE (the regular face's file) — that is the truth.
            const Face& src = faces_[kFaceRegular];
            if (src.ft_face &&
                FT_New_Face(reinterpret_cast<FT_Library>(ft_lib_),
                            src.path.c_str(), 0, &ft)) {
                p.detail = "probe face open failed"; return p;
            }
        } else if (f.ft_face) {
            if (f.path.empty() || f.path[0] == '/') {
                if (FT_New_Face(reinterpret_cast<FT_Library>(ft_lib_),
                                f.path.c_str(), 0, &ft)) {
                    p.detail = "probe face open failed"; return p;
                }
            } else if (f.bytes) {              // memory-backed base face
                keep_bytes = f.bytes;
                if (FT_New_Memory_Face(
                        reinterpret_cast<FT_Library>(ft_lib_),
                        f.bytes->data(), (FT_Long)f.bytes->size(), 0,
                        &ft)) {
                    p.detail = "probe memory face failed"; return p;
                }
            } else { p.detail = "no backing data"; return p; }
        }
    } else if (idx >= kBaseFaceCount &&
               idx - kBaseFaceCount < (int)app_faces_.size()) {
        const Face& f = app_faces_[idx - kBaseFaceCount];
        if (f.bytes) {
            keep_bytes = f.bytes;
            if (FT_New_Memory_Face(reinterpret_cast<FT_Library>(ft_lib_),
                                   f.bytes->data(),
                                   (FT_Long)f.bytes->size(), 0, &ft)) {
                p.detail = "probe memory face failed"; return p;
            }
        } else if (!f.path.empty()) {
            if (FT_New_Face(reinterpret_cast<FT_Library>(ft_lib_),
                            f.path.c_str(), 0, &ft)) {
                p.detail = "probe face open failed"; return p;
            }
        } else { p.detail = "no backing data"; return p; }
    } else { p.detail = "unknown face index"; return p; }
    if (!ft) { p.detail = "no probe face"; return p; }

    // Size: fixed-strike fonts (CBDT color emoji) select a strike;
    // outline fonts set the nominal pixel size.
    if (ft->num_fixed_sizes > 0) {
        int best = 0, bestd = 1 << 30;
        for (int i = 0; i < ft->num_fixed_sizes; ++i) {
            int sz = ft->available_sizes[i].size >> 6;
            int d = std::abs(sz - (int)std::lround(size_px));
            if (d < bestd) { bestd = d; best = i; }
        }
        FT_Select_Size(ft, best);
    } else if (FT_Set_Char_Size(ft, 0,
                                (FT_F26Dot6)std::lround(size_px * 64.0f),
                                72, 72)) {
        p.detail = "set size failed";
        FT_Done_Face(ft);
        return p;
    }

    std::u32string u32 = utf8_to_u32(utf8);
    for (uint32_t cp : u32) {
        FT_UInt g = FT_Get_Char_Index(ft, cp);
        if (!g) { ++p.notdef_count; continue; }
        ++p.glyph_count;
        if (FT_Load_Glyph(ft, g, FT_LOAD_RENDER)) continue;
        const FT_Bitmap& bm = ft->glyph->bitmap;
        if (bm.pixel_mode == FT_PIXEL_MODE_GRAY) {
            for (unsigned r = 0; r < bm.rows; ++r)
                for (unsigned c2 = 0; c2 < bm.width; ++c2)
                    if (bm.buffer[r * bm.pitch + c2] > 8) ++p.ink_pixels;
        } else if (bm.pixel_mode == FT_PIXEL_MODE_BGRA) {
            for (unsigned r = 0; r < bm.rows; ++r)
                for (unsigned c2 = 0; c2 < bm.width; ++c2)
                    if (bm.buffer[r * bm.pitch + c2 * 4 + 3] > 8)
                        ++p.ink_pixels;
        } else {
            for (unsigned r = 0; r < bm.rows; ++r)
                for (unsigned c2 = 0; c2 < bm.pitch; ++c2)
                    if (bm.buffer[r * bm.pitch + c2]) ++p.ink_pixels;
        }
    }
    FT_Done_Face(ft);
    p.ok = p.glyph_count > 0 && p.ink_pixels > 0;
    p.detail = "glyphs=" + std::to_string(p.glyph_count) +
               " ink=" + std::to_string(p.ink_pixels) +
               " notdef=" + std::to_string(p.notdef_count);
    return p;
}
'''

MARK = "FONT-PIPE-002-IMPL-APPLIED"
if MARK in s:
    print("already applied — skip")
else:
    ANCHOR = "uint64_t TextShaper::hash_string("
    assert ANCHOR in s, "hash_string anchor missing"
    s = s.replace(ANCHOR, IMPL + "\n" + ANCHOR, 1)

    # Destructor leak fix: the CJK face + the app-registered faces were
    # loaded but never freed (the uniqueness chain covered r/b/f/e/m only).
    OLD_DT = """    FT_Face m = reinterpret_cast<FT_Face>(faces_[kFaceMonospace].ft_face);
    if (m && m != r && m != b && m != f && m != e) FT_Done_Face(m);"""
    NEW_DT = """    FT_Face m = reinterpret_cast<FT_Face>(faces_[kFaceMonospace].ft_face);
    FT_Face k = reinterpret_cast<FT_Face>(faces_[kFaceCJK].ft_face);
    if (k && k != r && k != b && k != f && k != e && k != m) FT_Done_Face(k);
    // FONT-PIPE-002 (#605) leak fix: the app-registered faces were never
    // freed either — release every distinct FT_Face they hold.
    for (const Face& af : app_faces_) {
        FT_Face a = reinterpret_cast<FT_Face>(af.ft_face);
        if (a && a != r && a != b && a != f && a != e && a != m && a != k)
            FT_Done_Face(a);
    }
    if (m && m != r && m != b && m != f && m != e) FT_Done_Face(m);"""
    assert OLD_DT in s, "destructor anchor missing"
    s = s.replace(OLD_DT, NEW_DT, 1)
    open(P, "w").write(s)
    print("IMPL + destructor fix applied:", P)
