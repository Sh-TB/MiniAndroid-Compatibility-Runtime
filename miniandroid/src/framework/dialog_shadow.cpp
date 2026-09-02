// CAMPAIGN 013 B1 — Dialog / Toast / ArrayAdapter shadow implementation.
// See dialog_shadow.h for the architecture rationale.

#include "dialog_shadow.h"
#include "android_shadows.h"
#include "../renderer/software_renderer.h"

#include <algorithm>
#include <iostream>

namespace miniandroid { namespace framework {

// ─────────────────────────────────────────────────────────────────────────
// DialogShadow
// ─────────────────────────────────────────────────────────────────────────

ViewShadow* DialogShadow::views() {
    if (!view_shadow_ && registry_) {
        view_shadow_ = registry_->find_as<ViewShadow>();
    }
    return view_shadow_;
}

DialogWindow* DialogShadow::window_by_obj(uint32_t obj_id) {
    auto it = owner_index_.find(obj_id);
    if (it == owner_index_.end()) return nullptr;
    if (it->second >= windows_.size()) return nullptr;
    return &windows_[it->second];
}

DialogWindow* DialogShadow::window_by_view_root(uint32_t view_id) {
    for (auto& w : windows_) {
        if (w.decor_root_id == view_id) return &w;
    }
    return nullptr;
}

uint32_t DialogShadow::listener_for_click(uint32_t dialog_obj_id, int which,
                                          int* which_out) {
    DialogWindow* win = window_by_obj(dialog_obj_id);
    if (!win) return 0;
    *which_out = which;
    if (which >= 0) return win->item_listener;      // list row
    if (which == -1) return win->positive.listener; // BUTTON_POSITIVE
    if (which == -2) return win->negative.listener; // BUTTON_NEGATIVE
    if (which == -3) return win->neutral.listener;  // BUTTON_NEUTRAL
    return 0;
}

void DialogShadow::resolve_strings(
        const std::function<std::string(int32_t)>& resolver) {
    for (auto& w : windows_) {
        if (w.title.empty() && w.title_resid != 0) w.title = resolver(w.title_resid);
        if (w.message.empty() && w.message_resid != 0) w.message = resolver(w.message_resid);
        for (auto* b : {&w.positive, &w.negative, &w.neutral}) {
            if (b->label.empty() && b->label_resid != 0) b->label = resolver(b->label_resid);
        }
    }
    if (toast_.text.empty() && toast_.text_resid != 0) {
        toast_.text = resolver(toast_.text_resid);
    }
}

void DialogShadow::layout_window(DialogWindow& win, int screen_w, int screen_h) {
    // Empirical Material-ish proportions: ~86% width, centered, content-
    // sized height. Density factor 1 (the runtime's pixel density).
    const int pad = 24;          // window inner padding
    const int lh = 16;           // BitmapFont line height
    const int item_h = 88;       // list row height
    int w = std::max(480, std::min(screen_w * 86 / 100, 920));
    int content_h = pad * 2;
    if (!win.title.empty() || win.title_resid != 0) content_h += lh * 3;
    int lines = 1;
    for (char c : win.message) if (c == '\n') lines++;
    if (!win.message.empty() || win.message_resid != 0) content_h += lines * (lh + 8) + 24;
    if (!win.items.empty()) content_h += std::min((int)win.items.size(), 6) * item_h;
    if (win.custom_view_id != 0) content_h += 320;  // custom content allowance
    bool has_buttons = win.positive.listener != 0 || win.negative.listener != 0 ||
                       win.neutral.listener != 0 || !win.positive.label.empty() ||
                       !win.negative.label.empty() || !win.neutral.label.empty();
    if (has_buttons) content_h += 128;
    int h = std::min(content_h, screen_h - 120);
    int left = (screen_w - w) / 2;
    int top = (screen_h - h) / 2;
    win.frame_left = left; win.frame_top = top;
    win.frame_w = w; win.frame_h = h;
    std::cerr << "[DIALOG-LAYOUT] frame=(" << left << "," << top << " "
              << w << "x" << h << ") items=" << win.items.size()
              << " title=\"" << win.title << "\" msg_lines=" << lines
              << std::endl;
}

void DialogShadow::build_decor_tree(DialogWindow& win, ViewShadow* vs) {
    if (win.decor_root_id != 0 || vs == nullptr) return;

    // Decor root: vertical LinearLayout filling the window frame.
    auto* root = vs->get_or_create_node(next_decor_id_, "Landroid/widget/LinearLayout;");
    root->orientation = 1;  // VERTICAL
    root->clickable = false;
    win.decor_root_id = next_decor_id_++;

    auto add_text_row = [&](const std::string& text, const char* cls, bool bold) {
        auto* n = vs->get_or_create_node(next_decor_id_, cls);
        n->parent_id = win.decor_root_id;
        n->text = text;
        n->lp_width = -1;   // MATCH_PARENT
        n->lp_height = -2;  // WRAP_CONTENT
        (void)bold;         // BitmapFont has a single face; weight via color below
        root->children.push_back(next_decor_id_);
        return next_decor_id_++;
    };

    if (!win.title.empty()) {
        add_text_row(win.title, "Landroid/widget/TextView;", true);
    }
    if (!win.message.empty()) {
        add_text_row(win.message, "Landroid/widget/TextView;", false);
    }
    if (win.custom_view_id != 0) {
        // Re-parent the app's own view subtree under the dialog decor root.
        if (auto* cv = vs->find_node(win.custom_view_id)) {
            cv->parent_id = win.decor_root_id;
            cv->lp_width = -1;
            root->children.push_back(win.custom_view_id);
        }
    }
    // Item rows: REAL clickable ViewNodes owned by this dialog window.
    const int item_h = 88;  // Material list row height (px, density=1)
    for (size_t i = 0; i < win.items.size(); i++) {
        auto* n = vs->get_or_create_node(next_decor_id_, "Landroid/widget/TextView;");
        n->parent_id = win.decor_root_id;
        n->text = win.items[i];
        n->clickable = true;
        n->enabled = true;
        n->lp_width = -1;
        n->lp_height = item_h;
        n->dialog_owner_obj = win.dialog_obj_id;
        n->dialog_which = static_cast<int>(i);
        n->click_listener_id = win.item_listener;  // for probe candidate discovery
        n->text_gravity = 0x10;                    // CENTER_VERTICAL
        if (win.single_choice && win.checked_item == static_cast<int>(i)) {
            n->text = "> " + n->text;              // ASCII single-choice marker
        }
        root->children.push_back(next_decor_id_);
        next_decor_id_++;
    }
    // Button row: horizontal LinearLayout with REAL DialogInterface buttons.
    bool has_buttons = !win.positive.label.empty() || !win.negative.label.empty() ||
                       !win.neutral.label.empty();
    if (has_buttons) {
        auto* row = vs->get_or_create_node(next_decor_id_, "Landroid/widget/LinearLayout;");
        row->parent_id = win.decor_root_id;
        row->orientation = 0;  // HORIZONTAL
        row->lp_width = -1;
        row->lp_height = 128;
        row->text_gravity = 0x11;  // CENTER
        root->children.push_back(next_decor_id_);
        uint32_t row_id = next_decor_id_++;

        auto add_button = [&](const DialogWindow::Btn& b) {
            if (b.label.empty() && b.label_resid == 0) return;
            auto* n = vs->get_or_create_node(next_decor_id_, "Landroid/widget/Button;");
            n->parent_id = row_id;
            n->text = b.label;
            n->clickable = true;
            n->enabled = true;
            n->lp_width = 0;   // weight-like: row layout gives equal thirds
            n->lp_height = -1;
            n->dialog_owner_obj = win.dialog_obj_id;
            n->dialog_which = b.which;
            n->click_listener_id = b.listener;
            n->text_gravity = 0x11;
            vs->find_node(row_id)->children.push_back(next_decor_id_);
            next_decor_id_++;
        };
        add_button(win.neutral);
        add_button(win.negative);
        add_button(win.positive);
    }
    std::cerr << "[DIALOG-DECOR] built decor tree root_id=" << win.decor_root_id
              << " rows=" << root->children.size() << std::endl;
}

CallResult DialogShadow::dispatch(const CallContext& ctx) {
    const std::string& cls = ctx.class_name;
    const std::string& m = ctx.method;

    // ── Toast ──────────────────────────────────────────────────────────
    if (cls.find("Toast;") != std::string::npos) {
        return dispatch_toast(ctx);
    }

    // ── AlertDialog$Builder / AlertDialog / Dialog ─────────────────────
    DialogWindow* win = window_by_obj(ctx.receiver_id);
    if (!win) {
        // <init> on a new Builder object → create a window bound to it.
        if (m == "<init>" || m == "<clinit>") {
            windows_.emplace_back();
            DialogWindow& nw = windows_.back();
            nw.builder_obj_id = ctx.receiver_id;
            nw.positive.which = -1;
            nw.negative.which = -2;
            nw.neutral.which = -3;
            owner_index_[ctx.receiver_id] = windows_.size() - 1;
            std::cerr << "[DIALOG] new Builder window obj=" << ctx.receiver_id
                      << " idx=" << (windows_.size() - 1) << std::endl;
            return CallResult::handled_void();
        }
        // show() called on a Builder that was never dispatched through us
        // (e.g. constructed before this shadow was registered — defensive).
        if (m == "show" || m == "create") {
            windows_.emplace_back();
            DialogWindow& nw = windows_.back();
            nw.builder_obj_id = ctx.receiver_id;
            nw.dialog_obj_id = ctx.receiver_id;
            nw.positive.which = -1;
            nw.negative.which = -2;
            nw.neutral.which = -3;
            owner_index_[ctx.receiver_id] = windows_.size() - 1;
            return dispatch_builder(ctx, nw);
        }
        return CallResult::not_handled();
    }
    if (cls.find("AlertDialog$Builder") != std::string::npos) {
        return dispatch_builder(ctx, *win);
    }
    return dispatch_dialog(ctx, *win);
}

CallResult DialogShadow::dispatch_builder(const CallContext& ctx, DialogWindow& win) {
    const std::string& m = ctx.method;

    if (m == "setTitle" || m == "setCustomTitle") {
        if (!ctx.args.empty() && ctx.args[0].kind == CallContext::Arg::Kind::INT) {
            win.title_resid = ctx.args[0].int_val;
        } else {
            win.title = ctx.arg_as_string(0);
        }
        return CallResult::handled_object(ctx.receiver_id, ctx.class_name);
    }
    if (m == "setMessage") {
        if (!ctx.args.empty() && ctx.args[0].kind == CallContext::Arg::Kind::INT) {
            win.message_resid = ctx.args[0].int_val;
        } else {
            win.message = ctx.arg_as_string(0);
        }
        return CallResult::handled_object(ctx.receiver_id, ctx.class_name);
    }
    if (m == "setItems") {
        win.single_choice = false;
        // setItems(int itemsResid, listener) or setItems(List, listener)
        if (ctx.args.size() >= 2) {
            win.item_listener = ctx.arg_as_object(1);
        }
        // Items arrive as a CharSequence[] / List object — the engine's
        // arg_as_string on OBJECT args gives "[obj:N]"; ArrayAdapter-backed
        // lists are pulled at show() time. Character sequence arrays are
        // recorded as placeholders resolved from the adapter when possible.
        return CallResult::handled_object(ctx.receiver_id, ctx.class_name);
    }
    if (m == "setSingleChoiceItems") {
        win.single_choice = true;
        if (ctx.args.size() >= 1 && ctx.args[0].kind == CallContext::Arg::Kind::INT) {
            win.checked_item = 0;  // resid-array form: checked state resolved lazily
            if (ctx.args.size() >= 2) win.checked_item = ctx.arg_as_int(1);
            if (ctx.args.size() >= 3) win.item_listener = ctx.arg_as_object(2);
        } else {
            if (ctx.args.size() >= 2) win.checked_item = ctx.arg_as_int(1);
            if (ctx.args.size() >= 3) win.item_listener = ctx.arg_as_object(2);
            else if (ctx.args.size() >= 2) win.item_listener = ctx.arg_as_object(1);
        }
        return CallResult::handled_object(ctx.receiver_id, ctx.class_name);
    }
    if (m == "setAdapter" || m == "setCursor") {
        if (!ctx.args.empty()) win.adapter_obj_id = ctx.arg_as_object(0);
        if (ctx.args.size() >= 2) win.item_listener = ctx.arg_as_object(1);
        return CallResult::handled_object(ctx.receiver_id, ctx.class_name);
    }
    if (m == "setPositiveButton"  ||
        m == "setNegativeButton" || m == "setNeutralButton") {
        DialogWindow::Btn b;
        b.which = m == "setPositiveButton" ? -1
                : m == "setNegativeButton" ? -2 : -3;
        if (!ctx.args.empty() && ctx.args[0].kind == CallContext::Arg::Kind::INT) {
            b.label_resid = ctx.args[0].int_val;
        } else {
            b.label = ctx.arg_as_string(0);
        }
        if (ctx.args.size() >= 2) b.listener = ctx.arg_as_object(1);
        if (b.which == -1) win.positive = b;
        else if (b.which == -2) win.negative = b;
        else win.neutral = b;
        return CallResult::handled_object(ctx.receiver_id, ctx.class_name);
    }
    if (m == "setView") {
        win.custom_view_id = ctx.arg_as_object(0);
        return CallResult::handled_object(ctx.receiver_id, ctx.class_name);
    }
    if (m == "setCancelable" || m == "setCanceledOnTouchOutside") {
        return CallResult::handled_object(ctx.receiver_id, ctx.class_name);
    }
    if (m == "setOnItemClickListener" || m == "setOnItemSelectedListener") {
        return CallResult::handled_object(ctx.receiver_id, ctx.class_name);
    }
    if (m == "create") {
        // Allocate the Dialog object bound to this same window.
        uint32_t dlg = heap_ ? heap_->allocate("Landroid/app/AlertDialog;") : 0;
        win.dialog_obj_id = dlg;
        if (dlg != 0) owner_index_[dlg] = owner_index_[ctx.receiver_id];
        std::cerr << "[DIALOG] create() -> dialog obj=" << dlg
                  << " title=\"" << win.title << "\"" << std::endl;
        return CallResult::handled_object(dlg, "Landroid/app/AlertDialog;");
    }
    if (m == "show") {
        // Builder.show() == create().show()
        uint32_t dlg = heap_ ? heap_->allocate("Landroid/app/AlertDialog;") : 0;
        win.dialog_obj_id = dlg;
        if (dlg != 0) owner_index_[dlg] = owner_index_[ctx.receiver_id];
        return dispatch_dialog(ctx, win);
    }
    return CallResult::not_handled();
}

CallResult DialogShadow::dispatch_dialog(const CallContext& ctx, DialogWindow& win) {
    const std::string& m = ctx.method;

    if (m == "show" || m == "onStart") {
        if (!win.showing) {
            win.showing = true;
            win.ever_shown = true;
            win.dismissed = false;
            // Pull adapter items NOW (adapter fully populated by app code).
            if (win.items.empty() && win.adapter_obj_id != 0 && registry_) {
                auto* adapter_shadow = registry_->find_as<ArrayAdapterShadow>();
                if (adapter_shadow) {
                    win.items = adapter_shadow->items_for(win.adapter_obj_id);
                }
            }
            // setItems(CharSequence[]) arrays recorded via engine heap are
            // handled by the engine bridge storing string arrays; when the
            // window has a single_choice resid list the rows are created
            // from the message as a fallback (rare in real corpus apps).
            build_decor_tree(win, views());
            layout_window(win, 1080, 1920);
            std::cerr << "[DIALOG] show() obj=" << win.dialog_obj_id
                      << " decor_root=" << win.decor_root_id
                      << " items=" << win.items.size() << std::endl;
        }
        return CallResult::handled_void();
    }
    if (m == "dismiss" || m == "cancel" || m == "hide") {
        win.showing = false;
        win.dismissed = true;
        std::cerr << "[DIALOG] dismiss() obj=" << win.dialog_obj_id << std::endl;
        return CallResult::handled_void();
    }
    if (m == "isShowing") {
        return CallResult::handled_bool(win.showing);
    }
    if (m == "setOnShowListener" || m == "setOnDismissListener" ||
        m == "setOnCancelListener" || m == "setCanceledOnTouchOutside" ||
        m == "setCancelable") {
        return CallResult::handled_void();
    }
    if (m == "setTitle") {
        if (!ctx.args.empty() && ctx.args[0].kind == CallContext::Arg::Kind::INT) {
            win.title_resid = ctx.args[0].int_val;
        } else {
            win.title = ctx.arg_as_string(0);
        }
        return CallResult::handled_void();
    }
    if (m == "findViewById") {
        return CallResult::not_handled();  // ViewShadow handles its own ids
    }
    return CallResult::not_handled();
}

CallResult DialogShadow::dispatch_toast(const CallContext& ctx) {
    const std::string& m = ctx.method;
    if (m == "makeText") {
        uint32_t obj = heap_ ? heap_->allocate("Landroid/widget/Toast;") : 0;
        ToastState t;
        t.toast_obj_id = obj;
        // makeText(Context, int resId, int duration) or (Context, CharSequence, int)
        if (ctx.args.size() >= 2 && ctx.args[1].kind == CallContext::Arg::Kind::INT) {
            t.text_resid = ctx.args[1].int_val;
        } else if (ctx.args.size() >= 2) {
            t.text = ctx.arg_as_string(1);
        }
        toast_ = t;
        std::cerr << "[TOAST] makeText obj=" << obj << " text=\"" << t.text
                  << "\" resid=" << t.text_resid << std::endl;
        return CallResult::handled_object(obj, "Landroid/widget/Toast;");
    }
    if (m == "show") {
        toast_.showing = true;
        std::cerr << "[TOAST] show() text=\"" << toast_.text << "\"" << std::endl;
        return CallResult::handled_void();
    }
    if (m == "cancel" || m == "hide") {
        toast_.showing = false;
        return CallResult::handled_void();
    }
    if (m == "setText") {
        toast_.text = ctx.arg_as_string(0);
        toast_.text_resid = 0;
        return CallResult::handled_void();
    }
    if (m == "setDuration") {
        return CallResult::handled_void();
    }
    return CallResult::not_handled();
}

void DialogShadow::dismiss_dialog(uint32_t dialog_obj_id) {
    if (DialogWindow* win = window_by_obj(dialog_obj_id)) {
        win->showing = false;
        win->dismissed = true;
        std::cerr << "[DIALOG] dismiss_dialog(obj=" << dialog_obj_id << ")" << std::endl;
    }
}

// CAMPAIGN 013 B1: paint showing dialog windows from REAL recorded state.
// Dim overlay is a manual framebuffer blend (the walk's draw_rect writes
// opaque colors; real dialogs dim the host content behind the window).
void DialogShadow::render_dialogs(
        miniandroid::renderer::SoftwareCanvas& canvas,
        miniandroid::renderer::FrameBuffer& fb,
        int screen_w, int screen_h,
        const std::function<std::string(int32_t)>& resolver) {
    using namespace miniandroid::renderer;

    resolve_strings(resolver);
    const int W = fb.get_width(), H = fb.get_height();
    if (W != screen_w || H != screen_h) {
        screen_w = W; screen_h = H;
    }

    // ── Toast (bottom transient window) ────────────────────────────────
    if (toast_.showing && (!toast_.text.empty() || toast_.text_resid != 0)) {
        const int lh = 16;
        int tw = 0;
        for (const auto& ln : {toast_.text}) {
            BitmapFont probe;
            tw = std::max(tw, probe.measure_text(ln).width);
        }
        int box_w = std::min(screen_w - 80, tw + 96);
        int box_h = lh + 40;
        int bx = (screen_w - box_w) / 2, by = screen_h - box_h - 96;
        canvas.draw_rect(bx, by, bx + box_w, by + box_h, RGBA{0x2A, 0x2A, 0x2A, 0xE6});
        canvas.draw_text(toast_.text, bx + 48, by + 28, Colors::WHITE);
        std::cerr << "[DIALOG-RENDER] toast box " << box_w << "x" << box_h
                  << " text=\"" << toast_.text << "\"" << std::endl;
    }

    for (auto& win : windows_) {
        if (!win.showing) continue;
        layout_window(win, screen_w, screen_h);

        // 1. Dim overlay — 40% black over the whole screen.
        {
            const uint8_t alpha = 102;  // 0.4 * 255
            // FrameBuffer stores RGBA structs; blend via set_pixel is slow in
            // debug but the framebuffer is only 2M pixels — acceptable.
            for (int y = 0; y < screen_h; ++y) {
                for (int x = 0; x < screen_w; ++x) {
                    RGBA c = fb.get_pixel(x, y);
                    c.r = static_cast<uint8_t>((c.r * (255 - alpha)) / 255);
                    c.g = static_cast<uint8_t>((c.g * (255 - alpha)) / 255);
                    c.b = static_cast<uint8_t>((c.b * (255 - alpha)) / 255);
                    fb.set_pixel(x, y, c);
                }
            }
        }

        // 2. Window chrome: white panel + grey border + subtle shadow edge.
        const int l = win.frame_left, t = win.frame_top;
        const int r = l + win.frame_w, b = t + win.frame_h;
        canvas.draw_rect(l - 2, t - 2, r + 2, b + 2, RGBA{0xB0, 0xB0, 0xB0, 0xFF});  // border
        canvas.draw_rect(l, t, r, b, Colors::WHITE);                                  // panel

        BitmapFont font;
        const int lh = font.get_line_height();
        const int pad = 24;
        int y = t + pad;

        // 3. Title
        if (!win.title.empty()) {
            canvas.draw_text(win.title, l + pad, y + lh - 4, Colors::GREY_800, &font);
            y += lh + 14;
            canvas.draw_rect(l + pad, y, r - pad, y + 1, RGBA{0xE0, 0xE0, 0xE0, 0xFF});
            y += 12;
        }

        // 4. Message (word-wrapped)
        if (!win.message.empty()) {
            const int avail = win.frame_w - pad * 2;
            std::string line, word;
            for (size_t i = 0; i <= win.message.size(); i++) {
                char c = (i < win.message.size()) ? win.message[i] : '\n';
                if (c == '\n' || c == ' ') {
                    if (!word.empty()) {
                        std::string probe = line.empty() ? word : line + " " + word;
                        if (!line.empty() && font.measure_text(probe).width > avail) {
                            canvas.draw_text(line, l + pad, y, Colors::GREY_800, &font);
                            y += lh + 6;
                            line = word;
                        } else {
                            line = probe;
                        }
                        word.clear();
                    }
                    if (c == '\n' && !line.empty()) {
                        canvas.draw_text(line, l + pad, y, Colors::GREY_800, &font);
                        y += lh + 6;
                        line.clear();
                    }
                    continue;
                }
                word += c;
            }
            if (!line.empty()) {
                canvas.draw_text(line, l + pad, y, Colors::GREY_800, &font);
                y += lh + 6;
            }
            y += 12;
        }

        // 5. Item rows (clickable ViewNodes exist for these — the painter
        // mirrors their content; input comes from dispatch_click).
        const int item_h = 88;
        int items_shown = std::min<size_t>(win.items.size(), 6);
        int rows_top = y;
        for (int i = 0; i < static_cast<int>(items_shown); i++) {
            int ry = rows_top + i * item_h;
            if (ry + item_h > b - 128) break;  // keep the button row visible
            canvas.draw_text(win.items[i], l + pad, ry + item_h / 2 - lh / 2,
                             Colors::GREY_800, &font);
            canvas.draw_rect(l + 8, ry + item_h - 1, r - 8, ry + item_h,
                             RGBA{0xEE, 0xEE, 0xEE, 0xFF});
        }

        // 6. Button row (top separator + labels in thirds)
        bool any_btn = !win.positive.label.empty() || !win.negative.label.empty() ||
                       !win.neutral.label.empty();
        if (any_btn) {
            canvas.draw_rect(l, b - 112, r, b - 111, RGBA{0xE0, 0xE0, 0xE0, 0xFF});
            int thirds = 0;
            for (const auto* btn : {&win.neutral, &win.negative, &win.positive}) {
                if (!btn->label.empty()) thirds++;
            }
            int seg_w = (win.frame_w - 2 * pad) / std::max(thirds, 1);
            int bx = l + pad;
            for (const auto* btn : {&win.neutral, &win.negative, &win.positive}) {
                if (btn->label.empty()) continue;
                auto m = font.measure_text(btn->label);
                int tx = bx + (seg_w - m.width) / 2;
                canvas.draw_text(btn->label, tx, b - 112 + 62 - lh / 2,
                                 RGBA{0x00, 0x62, 0xCC, 0xFF}, &font);
                bx += seg_w;
            }
        }
        std::cerr << "[DIALOG-RENDER] window obj=" << win.dialog_obj_id
                  << " frame=(" << l << "," << t << " " << win.frame_w
                  << "x" << win.frame_h << ") items=" << win.items.size()
                  << " painted" << std::endl;
    }
}

// ─────────────────────────────────────────────────────────────────────────
// ArrayAdapterShadow
// ─────────────────────────────────────────────────────────────────────────

CallResult ArrayAdapterShadow::dispatch(const CallContext& ctx) {
    const std::string& m = ctx.method;
    const uint32_t recv = ctx.receiver_id;

    if (m == "<init>") {
        items_[recv].clear();
        // ctor variants that take a List/Object[] as last argument
        for (auto& a : ctx.args) {
            if (a.kind == CallContext::Arg::Kind::OBJECT &&
                    !a.string_val.empty()) {
                // string_val is only populated for String objects
            }
        }
        return CallResult::handled_void();
    }
    if (m == "add" || m == "insert" || m == "addLast") {
        std::string s = ctx.arg_as_string(0);
        if (!s.empty() && s.rfind("[obj:", 0) != 0) {
            items_[recv].push_back(s);
            std::cerr << "[ARRAY-ADAPTER] obj=" << recv << " add \"" << s
                      << "\" size=" << items_[recv].size() << std::endl;
            return CallResult::handled_void();
        }
        // Object arg: try toString via the registry (CollectionShadow etc.)
        items_[recv].push_back(s);
        return CallResult::handled_void();
    }
    if (m == "addAll") {
        for (auto& a : ctx.args) {
            std::string s = a.kind == CallContext::Arg::Kind::STRING ? a.string_val : "";
            if (!s.empty()) items_[recv].push_back(s);
        }
        return CallResult::handled_void();
    }
    if (m == "clear") {
        items_[recv].clear();
        return CallResult::handled_void();
    }
    if (m == "getCount" || m == "size") {
        return CallResult::handled_int(static_cast<int32_t>(items_[recv].size()));
    }
    if (m == "getItem") {
        int i = ctx.arg_as_int(0);
        auto it = items_.find(recv);
        if (it != items_.end() && i >= 0 && i < (int)it->second.size()) {
            return CallResult::handled_string(it->second[i]);
        }
        return CallResult::handled_null();
    }
    if (m == "getContext") {
        return CallResult::handled_int(0);  // caller expects the Activity — rare in dialogs
    }
    if (m == "notifyDataSetChanged" || m == "notifyDataSetInvalidated" ||
        m == "setNotifyOnChange" || m == "setDropDownViewResource") {
        return CallResult::handled_void();
    }
    if (m == "getView" || m == "getDropDownView") {
        return CallResult::handled_null();  // dialog rows render from items_ directly
    }
    return CallResult::not_handled();
}

std::vector<std::string> ArrayAdapterShadow::items_for(uint32_t adapter_obj_id) const {
    auto it = items_.find(adapter_obj_id);
    return it != items_.end() ? it->second : std::vector<std::string>{};
}

}} // namespace miniandroid::framework
