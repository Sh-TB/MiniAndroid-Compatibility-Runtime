// vector_raster.h — S27-W1 (#633/#634) the VectorDrawable rasterization law.
//
// AOSP VectorDrawable.inflate+draw: the <vector> root maps its
// viewportWidth/Height onto the drawable bounds (aspect-preserving,
// centered); every <path> child carries an SVG-syntax android:pathData
// plus android:fillColor/fillAlpha and is filled in document order
// (later paths paint over earlier ones). The engine's C9-3 intrinsic law
// already resolved the vector XML + its dims; this module turns the SAME
// parsed AXML into REAL pixels so the decoded bitmap flows the existing
// g04 fit-rect + draw_image pipeline — no second render path, no
// renderer changes.
//
// v1 documented subset (honest stats for everything outside it):
//   * fill paths only (fillColor/fillAlpha); stroke-only paths are
//     counted as skipped (flip's vectors are fill-only).
//   * pathData commands M m L l H h V v C c S s Q q T t A a Z z.
//   * fillType: even-odd scanline (AOSP default nonZero — identical for
//     non-self-intersecting contours, which is every recorded fixture;
//     the deviation is named here, not hidden).
//   * cubic/quad flattening: 16 fixed segments per curve; arcs: endpoint
//     parameterization → ≤4 cubics per ≤90° arc (12 max/arc). All
//     deterministic — no RNG, no timing anywhere.
#pragma once

#include <cstdint>
#include <string>
#include <vector>

#include "resources/axml_parser.h"

namespace miniandroid {
namespace framework {

struct VectorRasterStats {
    int paths = 0;            // <path> children seen
    int painted_paths = 0;    // actually rasterized
    int skipped_paths = 0;    // no pathData / stroke-only / unparseable
    int contours = 0;         // total subpaths emitted
    std::string first_skip;   // honest reason of the first skip
};

/// Rasterize the <vector> root into w×h straight-alpha RGBA
/// (StoredBitmap contract: premultiplied OFF). Returns true when at
/// least one path painted; stats carry the honest per-path accounting.
bool vector_rasterize(const resources::AxmlElement& root, int w, int h,
                      std::vector<uint8_t>& rgba, VectorRasterStats& stats);

}  // namespace framework
}  // namespace miniandroid
