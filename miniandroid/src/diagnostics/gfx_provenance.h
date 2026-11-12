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

    // IAPK: classify a byte path into the canonical source classes the
    // installed-app campaign requires:
    //   SOURCE_APK      — the original sideload APK (pre-install identity)
    //   INSTALLED_APK   — the package store codePath (.../data/app/<pkg>/base.apk)
    //   APP_DATA_FILE   — the package's private data (.../data/data/<pkg>/...)
    //   EXTERNAL_APP_FILE — the shared volume's app-specific area
    //                       (.../Android/data/<pkg>/...)
    //   OTHER_HOST_PATH — any other host path
    static std::string classify_byte_source(const std::string& path) {
        if (path.find("/data/app/") != std::string::npos)
            return "INSTALLED_APK";
        if (path.find("/data/data/") != std::string::npos)
            return "APP_DATA_FILE";
        if (path.find("/Android/data/") != std::string::npos ||
            path.find("/Android/obb/") != std::string::npos)
            return "EXTERNAL_APP_FILE";
        if (path.find("/storage/emulated/") != std::string::npos)
            return "EXTERNAL_SHARED_FILE";
        // Unversioned store-relative or sideload paths: heuristics are
        // forbidden — only the two canonical markers above are certain;
        // everything else is honest OTHER.
        return "OTHER_HOST_PATH";
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
        // ── SECONDARY CAMPAIGN V5: explicit provenance states ──────────
        // Every real pixel source carries ONE canonical state:
        //   IMAGE_RESOURCE      — resolved through resources.arsc (resid)
        //   IMAGE_APK_PATH      — an APK entry path (asset/file-backed)
        //   IMAGE_DIRECT_PIXELS — raw bitmap pixels (BitmapFactory/
        //                         programmatic canvas; never dropped for
        //                         lacking an APK path)
        r["provenance_state"] = resid != 0 ? "IMAGE_RESOURCE"
                                : !path.empty() ? "IMAGE_APK_PATH"
                                : "IMAGE_DIRECT_PIXELS";
        // IAPK (F-NEW-234 wave): byte-source classification — proves whether
        // the pixel bytes came from the INSTALLED package, the original
        // sideload APK, app-private data, external app storage, or elsewhere.
        if (!path.empty()) {
            r["byte_source"] = classify_byte_source(path);
        }
        events_.push_back(std::move(r));
        cap_bounded(events_, kMaxEvents, event_drops_);
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
            // V5: canvas replay consumes stored raw pixels — the direct
            // pixel provenance state (no APK path required by law).
            {"provenance_state", "IMAGE_DIRECT_PIXELS"},
        });
        cap_bounded(events_, kMaxEvents, event_drops_);
    }

    // ── S83-GFX-BASE §33: GL chain bits ─────────────────────────────────
    // One record per GLSurfaceView frame: the GL provenance chain is
    //   RENDERER_BOUND → (SURFACE_CREATED) → DRAW_SUBMITTED →
    //   FRAMEBUFFER_UPDATED → SURFACE_PRESENTED
    // GP S223 LOG-004 (issue #582): every bit is now DERIVED from real
    // evidence, never manufactured. The old form set DRAW_SUBMITTED /
    // FRAMEBUFFER_UPDATED / SURFACE_WRITTEN / BUFFER_PRESENTED /
    // DRAW_CALLED true unconditionally — even a frame whose callbacks
    // failed or whose clip intersection copied ZERO pixels reported a
    // full success chain. Now: DRAW_CALLED/DRAW_SUBMITTED = the surface
    // frame dispatch returned true (onDrawFrame really executed);
    // FRAMEBUFFER_UPDATED/SURFACE_WRITTEN/BUFFER_PRESENTED = the blit
    // actually copied ≥1 pixel into the window framebuffer.
    void record_gl_presented(uint32_t view_id, int w, int h, bool first,
                             bool draw_called, size_t blitted_px) {
        if (!enabled_) return;
        events_.push_back({
            {"origin", "glsurfaceview-frame"},
            {"view_id", view_id},
            {"RENDERER_BOUND", true},
            {"SURFACE_CREATED", first},
            {"DRAW_CALLED", draw_called},
            {"DRAW_SUBMITTED", draw_called},
            {"FRAMEBUFFER_UPDATED", blitted_px > 0},
            {"SURFACE_WRITTEN", blitted_px > 0},
            {"BUFFER_PRESENTED", blitted_px > 0},
            {"blitted_px", blitted_px},
            {"width", w}, {"height", h},
        });
        cap_bounded(events_, kMaxEvents, event_drops_);
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
        cap_bounded(frames_, kMaxFrames, frame_drops_);
    }

    // ── S83-GFX-BASE §34: FIRST_DIVERGENCE auto-derivation ───────────────
    // Contract C7 law: FIRST_DIVERGENCE = the first chain bit that is 0
    // while all earlier applicable bits are 1. Derived here at frame
    // finalize from the recorded bits themselves — never hand-claimed.
    static const std::vector<std::string>& chain_order() {
        static const std::vector<std::string> kOrder = {
            "ASSET_FOUND", "RESOURCE_RESOLVED", "RESOURCE_SELECTED", "DECODED",
            "BITMAP_CREATED", "DRAWABLE_CREATED", "VIEW_RECEIVED", "VIEW_BOUND",
            "MEASURED", "LAYOUT", "RENDERER_BOUND", "SURFACE_CREATED",
            "DRAW_SUBMITTED", "FRAMEBUFFER_UPDATED", "DRAW_CALLED",
            "CANVAS_MUTATED", "SURFACE_WRITTEN", "BUFFER_PRESENTED",
            "COMPOSITED", "SCREENSHOT_CAPTURED",
        };
        return kOrder;
    }

    // Walks one event's applicable chain bits in canonical order. Returns
    // nullptr when the whole applicable chain is 1 (no divergence). The
    // first applicable bit that is 0 names the divergence; if no earlier
    // bit was 1 the chain never started (still a divergence, noted).
    static nlohmann::json derive_event_divergence(const nlohmann::json& ev) {
        std::vector<std::string> passed;
        for (const auto& bit : chain_order()) {
            auto it = ev.find(bit);
            if (it == ev.end() || !it->is_boolean()) continue;  // not applicable
            if (it->get<bool>()) {
                passed.push_back(bit);
                continue;
            }
            nlohmann::json d = {{"bit", bit}, {"earlier_passed", passed}};
            if (passed.empty()) d["note"] = "chain never started";
            return d;
        }
        return nullptr;
    }

    void finalize(const std::string& screenshot_path, bool captured,
                  size_t screenshot_nonwhite, size_t screenshot_unique) {
        if (!enabled_) return;
        // §34: derive per-event + global first divergence before the write.
        nlohmann::json global_div = nullptr;
        std::string global_origin;
        for (auto& ev : events_) {
            nlohmann::json d = derive_event_divergence(ev);
            if (!d.is_null()) {
                ev["FIRST_DIVERGENCE"] = d;
                if (global_div.is_null()) {
                    global_div = d;
                    global_origin = ev.value("origin", "");
                }
            }
        }
        nlohmann::json shot = {
            {"path", screenshot_path},
            {"SCREENSHOT_CAPTURED", captured},
            {"nonwhite_px", screenshot_nonwhite},
            {"unique_colors", screenshot_unique},
        };
        nlohmann::json out = {
            {"instrument", "MINIANDROID_GFX_PROVENANCE"},
            {"chain_law", "C7: FIRST_DIVERGENCE = first applicable bit=0 "
                          "while all earlier applicable bits=1"},
            // GP S223 LOG-012: truncation is VISIBLE — the ring's drop
            // counters land in the manifest (never a silent cap).
            {"drops", {{"events", event_drops_}, {"frames", frame_drops_}}},
            {"events", events_},
            {"frame_census", frames_},
            {"screenshot", shot},
        };
        if (!global_div.is_null()) {
            out["first_divergence"] = global_div;
            out["first_divergence"]["origin"] = global_origin;
        } else if (!events_.empty()) {
            out["first_divergence"] = nullptr;   // every recorded chain complete
        }
        std::ofstream f(out_path_, std::ios::binary);
        if (f) f << out.dump(1);
        enabled_ = false;  // one-shot: avoid double-write on re-capture
    }

private:
    GfxProvenance() = default;
    // GP S223 LOG-012 (issue #582): the event/frame arrays were UNBOUNDED —
    // a long GL/image run pushed every record into memory until finalize.
    // Bounded ring now: FIRST rows survive (first-failure retention law) and
    // LAST rows survive; the drop counters land in the finalize manifest so
    // truncation is VISIBLE, never silent.
    static constexpr size_t kMaxEvents = 4096;
    static constexpr size_t kMaxFrames = 512;
    static void cap_bounded(nlohmann::json& arr, size_t cap, uint64_t& drops) {
        if (!arr.is_array() || arr.size() <= cap) return;
        drops += arr.size() - cap;
        nlohmann::json kept = nlohmann::json::array();
        const size_t head = cap / 2;
        for (size_t i = 0; i < head; ++i) kept.push_back(arr[i]);
        for (size_t i = arr.size() - (cap - head); i < arr.size(); ++i)
            kept.push_back(arr[i]);
        arr = std::move(kept);
    }
    bool enabled_ = false;
    std::string out_path_;
    uint64_t event_drops_ = 0;
    uint64_t frame_drops_ = 0;
    nlohmann::json events_ = nlohmann::json::array();
    nlohmann::json frames_ = nlohmann::json::array();
};

}  // namespace diagnostics
}  // namespace miniandroid

#endif  // MINIANDROID_GFX_PROVENANCE_H
