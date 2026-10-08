/*
 * MiniAndroid Runtime — CONT-24 EXPERIMENT (TEST BRANCH ONLY)
 * skeleton_light: ONE generic "skeleton" frame painter.
 *
 * HYPOTHESIS UNDER TEST (user directive, 2026-10-09):
 *   Instead of the ~10K-line per-op graphics emulation chain
 *   (engine draw walk + CanvasShadow ops + TextShaper/HarfBuzz +
 *   bitmap/vector decode + drawable machinery), ONE compact generic
 *   component that paints the laid-out ViewShadow tree as a SKELETON
 *   (background fills + 5x7 ASCII text + depth-cycled outlines +
 *   image/clickable markers) may deliver most of the *informative*
 *   frame value at a fraction of the machinery.
 *
 * LAWS (identical to the authoritative render):
 *   - Same authoritative root (effective_content_root_()), same window
 *     background resolution, same frame-truth census contract.
 *   - Only REAL tree state is painted: bg_color, text, visibility,
 *     clickable, image_drawable_path provenance. No fabricated UI.
 *   - Geometry from ViewRenderer::layout (the existing S132 measure
 *     pass — reuse, not port).
 *   - Env-gated: MINIANDROID_SKELETON_LIGHT=1 (default OFF = the
 *     unmodified main-line pipeline byte-for-byte).
 *
 * This file exists ONLY on the cont24/skeleton-light-experiment branch.
 * It is a measurement instrument for the impact assessment, NOT a
 * proposal to ship; see evidence/cont24/SKEL_LIGHT_EXPERIMENT.md.
 */

#ifndef MINIANDROID_SKELETON_LIGHT_H
#define MINIANDROID_SKELETON_LIGHT_H

#include "software_renderer.h"
#include "../framework/android_shadows.h"
#include <cstdint>

namespace miniandroid {
namespace renderer {

bool skeleton_light_enabled();  // env MINIANDROID_SKELETON_LIGHT=1

struct SkeletonLightStats {
    int  nodes_total    = 0;  // visited tree nodes (pre-visibility filter)
    int  boxes_painted  = 0;  // background fills / outlines drawn
    int  texts_painted  = 0;  // ASCII text runs drawn with the 5x7 font
    int  texts_skipped_non_ascii = 0;  // non-ASCII content → marker line only
    int  images_marked  = 0;  // image-carrying views painted as placeholders
    int  clickables     = 0;  // clickable views marked (corner ticks)
    int  gone_skipped   = 0;  // GONE subtrees skipped
    int  invisible      = 0;  // INVISIBLE nodes counted, not painted
    int  depth_max      = 0;
    uint64_t pixels_touched = 0;  // non-window-background pixels written
};

// Measure (reuse ViewRenderer::layout) + paint the skeleton of the
// ViewShadow tree rooted at root_id into fb. Returns false only when the
// tree is unusable (caller falls back to the main-line path).
bool skeleton_light_render(framework::ViewShadow* views, uint32_t root_id,
                           int screen_w, int screen_h, const RGBA& win_bg,
                           FrameBuffer& fb, SkeletonLightStats& stats);

}  // namespace renderer
}  // namespace miniandroid

#endif  // MINIANDROID_SKELETON_LIGHT_H
