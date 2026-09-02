// CAMPAIGN 013 B1 — Dialog / Toast / ArrayAdapter shadow objects (§4/§5).
//
// Prior behavior (v0.11.3): AlertDialog$Builder / AlertDialog / Dialog /
// Toast / ArrayAdapter calls fell through to the API bridge as invisible
// no-ops. Real app code executed (callback → dialog.show()) but NOTHING
// became pixels — gmdice's dice-selection dialog produced an honest 0-px
// second frame (see 011.3 FRAME-2 evidence).
//
// This shadow implements the smallest reusable dialog OBJECT MODEL:
//   Builder state → create() → Dialog object → Window state → DecorView
//   tree (REAL ViewNodes in the ViewShadow namespace) → show()/dismiss()
//   → visible in the next rendered frame → dialog views receive REAL
//   clicks routed as DialogInterface$OnClickListener(dialog, which).
//
// The dialog participates in measure/layout/draw/input through the SAME
// ViewShadow node machinery as Activity content — no special-case pixels,
// no hard-coded rectangles.

#pragma once

#include "shadow_registry.h"

#include <cstdint>
#include <functional>
#include <map>
#include <string>
#include <vector>

// renderer types live at miniandroid::renderer (software_renderer.h)
namespace miniandroid { namespace renderer {
class SoftwareCanvas; class FrameBuffer; } }

namespace miniandroid { namespace framework {

class ViewShadow;

// One logical dialog window (Builder → create() → Dialog share one window).
struct DialogWindow {
    // Owner object ids: the Builder that created it and/or the Dialog
    // returned by create(). Both map to this window.
    uint32_t builder_obj_id = 0;
    uint32_t dialog_obj_id = 0;

    // Content recorded from Builder calls.
    std::string title;
    int32_t title_resid = 0;         // setTitle(int) — resolved at render time
    std::string message;
    int32_t message_resid = 0;       // setMessage(int)
    std::vector<std::string> items;  // setItems / setSingleChoiceItems / setAdapter
    int checked_item = -1;           // setSingleChoiceItems checked index
    bool single_choice = false;

    // Buttons: which = DialogInterface.BUTTON_POSITIVE(-1)/NEGATIVE(-2)/NEUTRAL(-3)
    struct Btn {
        int which = 0;
        std::string label;
        int32_t label_resid = 0;
        uint32_t listener = 0;       // DialogInterface$OnClickListener heap object
    };
    Btn positive, negative, neutral;

    uint32_t item_listener = 0;      // listener for setItems/setSingleChoiceItems
    uint32_t adapter_obj_id = 0;     // ListAdapter backed by ArrayAdapterShadow
    uint32_t custom_view_id = 0;     // setView(View)

    bool showing = false;
    bool ever_shown = false;
    bool dismissed = false;

    // Synthesized DecorView content root (ViewShadow node id). Created by
    // build_decor_tree() on first show().
    uint32_t decor_root_id = 0;

    // Window frame geometry (computed by layout_window() at show time;
    // the renderer draws the frame and the decor tree inside it).
    int frame_left = 0, frame_top = 0, frame_w = 0, frame_h = 0;
};

// Toast state (makeText → show → visible transient window).
struct ToastState {
    uint32_t toast_obj_id = 0;
    std::string text;
    int32_t text_resid = 0;
    bool showing = false;
};

// ─────────────────────────────────────────────────────────────────────────
// DialogShadow — owns ALL dialog windows + toast state for the run.
//
// Render integration (ExecutionEngine::stage_render_frame):
//   1. resolve_strings(resolver) — resid → string via the engine's
//      resource maps (shadows cannot reach the engine directly).
//   2. for each showing window: draw dim overlay + window frame, then the
//      engine renders the window's decor ViewNode tree with the standard
//      node walk (render_node_tree).
//
// Input integration (DalvikExecutionEngine::dispatch_click):
//   Dialog item/button ViewNodes carry (dialog_owner_obj, dialog_which);
//   the engine routes those clicks to the window's
//   DialogInterface$OnClickListener with REAL (dialog, which) arguments.
// ─────────────────────────────────────────────────────────────────────────
class DialogShadow : public Shadow {
public:
    std::string name() const override { return "DialogShadow"; }

    bool handles_class(const std::string& cls) const override {
        return cls.find("AlertDialog$Builder") != std::string::npos ||
               cls == "Landroid/app/AlertDialog;" ||
               cls == "Landroid/app/Dialog;" ||
               cls.find("AlertDialog;") != std::string::npos ||
               cls == "Landroid/app/DialogFragment;" ||
               cls == "Landroid/widget/Toast;" ||
               cls.find("Toast;") != std::string::npos;
    }

    CallResult dispatch(const CallContext& ctx) override;

    // ── accessors for renderer / engine ────────────────────────────────
    std::vector<DialogWindow>& windows() { return windows_; }
    const std::vector<DialogWindow>& windows() const { return windows_; }
    DialogWindow* window_by_obj(uint32_t obj_id);
    DialogWindow* window_by_view_root(uint32_t view_id);

    ToastState& toast() { return toast_; }

    // Resolve pending resid strings (called by the renderer each frame).
    void resolve_strings(const std::function<std::string(int32_t)>& resolver);

    // Build the DecorView content tree in the ViewShadow namespace for a
    // window that is about to be shown. Creates REAL ViewNodes:
    //   DecorLayout(vertical LinearLayout)
    //     ├─ Title TextView
    //     ├─ Message TextView        (if message)
    //     ├─ ItemList container      (one clickable TextView per item)
    //     ├─ custom content subtree  (already in ViewShadow; re-parented)
    //     └─ ButtonRow (horizontal LinearLayout of Buttons)
    void build_decor_tree(DialogWindow& win, ViewShadow* view_shadow);

    // Compute window frame geometry from content (called at show time).
    void layout_window(DialogWindow& win, int screen_w, int screen_h);

    // Click routing support: returns the listener object id for a dialog
    // item/button click and fills `which`. 0 = no listener (dismiss only).
    uint32_t listener_for_click(uint32_t dialog_obj_id, int which, int* which_out);

    // Dismiss a window by its Dialog object id (used by the click router:
    // no-listener button clicks still dismiss, matching real Android).
    void dismiss_dialog(uint32_t dialog_obj_id);

    // CAMPAIGN 013 B1: paint every showing dialog window onto the current
    // frame: dim overlay + window frame + REAL recorded content
    // (title/message/items/buttons). Called by ExecutionEngine after the
    // activity tree pass, BEFORE the fb→framebuffer_ copy. The decor
    // ViewNode tree (build_decor_tree) owns input/hierarchy; this painter
    // owns the window chrome pixels from the SAME recorded state.
    void render_dialogs(miniandroid::renderer::SoftwareCanvas& canvas,
                        miniandroid::renderer::FrameBuffer& fb,
                        int screen_w, int screen_h,
                        const std::function<std::string(int32_t)>& resolver);

private:
    ViewShadow* views();  // lazy cross-shadow lookup

    CallResult dispatch_builder(const CallContext& ctx, DialogWindow& win);
    CallResult dispatch_dialog(const CallContext& ctx, DialogWindow& win);
    CallResult dispatch_toast(const CallContext& ctx);

    std::vector<DialogWindow> windows_;
    std::map<uint32_t, size_t> owner_index_;   // builder/dialog obj → window idx
    ToastState toast_;
    ViewShadow* view_shadow_ = nullptr;
    int next_decor_id_ = 700000;  // synthetic view id space for dialog trees
};

// ─────────────────────────────────────────────────────────────────────────
// ArrayAdapterShadow — minimal ListAdapter backing for setAdapter dialogs
// and (later) ListView content. Records per-object item lists so dialog
// windows can materialize their item rows.
// ─────────────────────────────────────────────────────────────────────────
class ArrayAdapterShadow : public Shadow {
public:
    std::string name() const override { return "ArrayAdapterShadow"; }

    bool handles_class(const std::string& cls) const override {
        return cls.find("ArrayAdapter") != std::string::npos ||
               cls.find("ListAdapter") != std::string::npos;
    }

    CallResult dispatch(const CallContext& ctx) override;

    std::vector<std::string> items_for(uint32_t adapter_obj_id) const;

private:
    std::map<uint32_t, std::vector<std::string>> items_;
};

}} // namespace miniandroid::framework
