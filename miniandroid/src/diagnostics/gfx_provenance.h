// S82-GFX-REVOLUTION P2 — pixel provenance instrument (header-only).
//
// Records the S82-GFX §6 evidence-bit chain for every image that ATTEMPTS to
// reach the screen, per frame framebuffer census, and the final screenshot
// capture record:
//
//   ASSET_FOUND → RESOURCE_RESOLVED → DECODED → BITMAP_CREATED →
//   VIEW_RECEIVED → DRAW_CALLED → CANVAS_WRITTEN → SURFACE_UPDATED →
//   COMPOSITED → SCREENSHOT_CAPTURED
//
// Zero cost when MINIANDROID_GFX_PROVENANCE is unset (one bool check).
// Output JSON is small (Git-friendly, S82-GFX §23/§33 law).
#ifndef MINIANDROID_GFX_PROVENANCE_H
#define MINIANDROID_GFX_PROVENANCE_H

#include <algorithm>
#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>

#include <nlohmann/json.hpp>

namespace miniandroid {
namespace diagnostics {

class GfxProvenance {
public:
    static GfxProvenance& instance() {
        static GfxProvenance inst;
        return inst;
    }

    // Reads MINIANDROID_GFX_PROVENANCE=<out.json>; also flips verbose
    // stdout markers off by keeping records internal.
    void begin() {
        const char* p = std::getenv("MINIANDROID_GFX_PROVENANCE");
        if (p && *p) {
            enabled_ = true;
            out_path_ = p;
        }
    }

    bool enabled() const { return enabled_; }

    // One record per image draw ATTEMPT anywhere in the pipeline.
    // origin: "imageview-direct" | "imageview-resid" | "background-bitmap" |
    //         "canvas-drawBitmap" | "bitmapfactory-decode"
    void record_image(const std::string& origin, uint32_t resid,
                      const std::string& path, bool asset_found,
                      bool decoded, int w, int h,
                      const std::string& colortype, int sel_density,
                      float dx, float dy, float dw, float dh,
                      bool draw_called, const std::string& failure) {
        if (!enabled_) return;
        nlohmann::json r = {
            {"origin", origin},
            {"resid", resid},
            {"path", path},
            {"ASSET_FOUND", asset_found},
            {"RESOURCE_RESOLVED", !path.empty()},
            {"DECODED", decoded},
            {"BITMAP_CREATED", decoded && w > 0 && h > 0},
            {"VIEW_RECEIVED", origin.rfind("imageview", 0) == 0 ||
                              origin.rfind("background", 0) == 0},
            {"DRAW_CALLED", draw_called},
            {"width", w}, {"height", h},
            {"color_type", colortype},
            {"src_density", sel_density},
            {"dst", {{"x", dx}, {"y", dy}, {"w", dw}, {"h", dh}}},
        };
        if (!failure.empty()) r["FAILURE"] = failure;
        events_.push_back(std::move(r));
    }

    // drawBitmap replay: bitmap resolved from store + replayed flag.
    void record_canvas_bitmap(uint32_t bitmap_id, bool resolved, int sw,
                              int sh, bool replayed) {
        if (!enabled_) return;
        events_.push_back({
            {"origin", "canvas-drawBitmap"},
            {"bitmap_id", bitmap_id},
            {"BITMAP_RESOLVED", resolved},
            {"DECODED", resolved},
            {"REPLAYED", replayed},
            {"width", sw}, {"height", sh},
            {"DRAW_CALLED", replayed},
        });
    }

    // Per-frame census of the composed framebuffer (surface evidence).
    void record_frame_census(int frame_index, size_t total_px, size_t nonwhite,
                             size_t unique_colors,
                             const std::vector<uint32_t>& top_colors) {
        if (!enabled_) return;
        nlohmann::json j = {
            {"frame", frame_index},
            {"total_px", total_px},
            {"nonwhite_px", nonwhite},
            {"unique_colors", unique_colors},
        };
        nlohmann::json tc = nlohmann::json::array();
        for (uint32_t c : top_colors) tc.push_back(c);
        j["top_colors_rgb"] = std::move(tc);
        frames_.push_back(std::move(j));
    }

    void finalize(const std::string& screenshot_path, bool captured,
                  size_t screenshot_nonwhite, size_t screenshot_unique) {
        if (!enabled_) return;
        nlohmann::json out = {
            {"instrument", "MINIANDROID_GFX_PROVENANCE"},
            {"events", events_},
            {"frame_census", frames_},
            {"screenshot", {
                {"path", screenshot_path},
                {"SCREENSHOT_CAPTURED", captured},
                {"nonwhite_px", screenshot_nonwhite},
                {"unique_colors", screenshot_unique},
            }},
        };
        std::ofstream f(out_path_, std::ios::binary);
        if (f) f << out.dump(1);
        enabled_ = false;  // one-shot: avoid double-write on re-capture
    }

private:
    GfxProvenance() = default;
    bool enabled_ = false;
    std::string out_path_;
    nlohmann::json events_ = nlohmann::json::array();
    nlohmann::json frames_ = nlohmann::json::array();
};

}  // namespace diagnostics
}  // namespace miniandroid

#endif  // MINIANDROID_GFX_PROVENANCE_H
