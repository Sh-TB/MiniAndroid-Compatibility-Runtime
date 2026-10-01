// S135 — VISUAL RUNTIME BOOT/TRACE LOGGER — on-screen trace overlay.
//
// Renders the runtime boot/trace panel ONTO A COPY of the authoritative
// framebuffer (S135 §9 architecture law):
//
//   APP RENDERING → AUTHORITATIVE FRAME → VISUAL TRACE COMPOSITION →
//   SCREENSHOT / DISPLAY
//
// The overlay NEVER:
//   - touches the app ViewShadow tree / app view tree (§8 hard rule)
//   - writes into the app framebuffer used as evidence
//   - participates in measure/layout/draw of the app
//   - acts as an app pixel owner (S135 §27: never a placeholder renderer)
//
// It is composed in stage_capture_output AFTER the authoritative PNG is
// written, into a separate diagnostic file (trace_overlay.png).
//
// Semantic colors (S135 §4):
//   GREEN  = confirmed      YELLOW = started/pending/incomplete
//   RED    = failure/divergence    BLUE  = informational
//   PURPLE = renderer/provenance   GRAY  = not reached
#ifndef MINIANDROID_TRACE_OVERLAY_H
#define MINIANDROID_TRACE_OVERLAY_H

#include <string>
#include <vector>

#include "trace_engine.h"
#include "../renderer/software_renderer.h"

namespace miniandroid {
namespace diagnostics {

class TraceOverlay {
public:
    struct Options {
        bool expanded = false;      // full forensic panel (MINIANDROID_TRACE_UI=expanded)
        bool header_only = false;   // tiny always-visible status strip
        int  margin = 12;           // px from the screen edge
        int  max_tail_events = 10;  // tail rows in the expanded panel
    };

    // Compose the diagnostic frame: a COPY of `authoritative` with the
    // trace panel drawn on top of the copy. The authoritative frame buffer
    // passed in is read-only here — the caller owns the original.
    // Returns a new FrameBuffer containing authoritative pixels + overlay.
    static renderer::FrameBuffer compose(const renderer::FrameBuffer& authoritative,
                                         const TraceEngine& trace,
                                         const Options& opts);

    // Convenience: decide expanded mode from env (MINIANDROID_TRACE_UI).
    static Options options_from_env();
};

} // namespace diagnostics
} // namespace miniandroid

#endif // MINIANDROID_TRACE_OVERLAY_H
