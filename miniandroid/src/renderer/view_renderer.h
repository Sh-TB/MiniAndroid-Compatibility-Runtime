/*
 * MiniAndroid Runtime - UNIFIED_007 EXP-122
 * ViewRenderer: real measure → layout → draw over the ViewShadow tree.
 *
 * - Writes computed geometry back into ViewNode x/y/w/h (hit-testing source).
 * - Draws backgrounds (color / shape solid+gradient+corners+stroke / bitmap
 *   decoded from the APK), images (PNG/WebP/JPEG via the existing codecs),
 *   and text via TextShaper (HarfBuzz+FreeType) with bitmap-font fallback.
 * - hit_test(x,y) → topmost clickable view (MotionEvent target).
 */

#ifndef MINIANDROID_VIEW_RENDERER_H
#define MINIANDROID_VIEW_RENDERER_H

#include "../framework/android_shadows.h"
#include "software_renderer.h"
#include "../third_party/nlohmann_json/include/nlohmann/json.hpp"
#include <string>
#include <vector>
#include <map>

namespace miniandroid {

namespace apk { class ApkParser; }

namespace renderer {

class ViewRenderer {
public:
    ViewRenderer(framework::ViewShadow* views, int screen_w, int screen_h);

    int layout(uint32_t root_id);
    bool render_png(uint32_t root_id, const std::string& path,
                    const RGBA& window_bg = {0, 0, 0, 255});
    uint32_t hit_test(uint32_t root_id, int x, int y) const;
    nlohmann::json layout_dump(uint32_t root_id) const;
    // decode + cache image bitmaps referenced by the tree (PNG/WebP/JPEG)
    void preload_bitmaps(uint32_t root_id, apk::ApkParser& apk);

    struct Stats {
        int laid_out = 0;
        int drawn = 0;
        int images_drawn = 0, bg_bitmaps_drawn = 0, bg_shapes_drawn = 0;
        int texts_shaped = 0, texts_bitmap_fallback = 0;
        int nonwhite_pixels = 0;
    };
    const Stats& stats() const { return stats_; }

private:
    struct Box {
        int x, y, w, h;
    };
    Box measure_view(framework::ViewShadow::ViewNode& n, int avail_w, int avail_h);
    void layout_children_linear(framework::ViewShadow::ViewNode& n, const Box& b);
    void layout_children_relative(framework::ViewShadow::ViewNode& n, const Box& b);
    void layout_children_frame(framework::ViewShadow::ViewNode& n, const Box& b);
    void draw_view(framework::ViewShadow::ViewNode& n, FrameBuffer& fb,
                   const RGBA& window_bg);
    void draw_text_into(framework::ViewShadow::ViewNode& n, FrameBuffer& fb,
                        int left, int top, int w, int h);
    bool decode_into(const std::string& zip_path, apk::ApkParser& apk);
    bool is_linear(const framework::ViewShadow::ViewNode& n) const;
    bool is_relative(const framework::ViewShadow::ViewNode& n) const;
    bool is_frame(const framework::ViewShadow::ViewNode& n) const;
    bool is_scroll(const framework::ViewShadow::ViewNode& n) const;
    bool is_image(const framework::ViewShadow::ViewNode& n) const;
    bool is_edit_text(const framework::ViewShadow::ViewNode& n) const;

    framework::ViewShadow* views_;
    int screen_w_, screen_h_;
    Stats stats_;
    std::map<std::string, DecodedImage> bitmap_cache_;
};

}  // namespace renderer
}  // namespace miniandroid

#endif  // MINIANDROID_VIEW_RENDERER_H
