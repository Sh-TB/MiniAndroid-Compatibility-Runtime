#!/usr/bin/env python3
"""W20-K: re-apply ALL knowledge-transfer integrations onto the restored
671d2577 split tree. Every replacement asserts exactly-once."""
import sys

def edit(path, old, new, count=1):
    s = open(path).read()
    n = s.count(old)
    assert n == count, f"{path}: pattern count {n} != {count}\n---\n{old[:120]}"
    open(path, 'w').write(s.replace(old, new))
    print(f"OK {path} ({old[:40].strip()}...)")

# ── WS8: take_result always delivers the AOSP default ──────────────────
edit('src/framework/android_shadows.h',
'''    bool take_result(int* result_code, uint32_t* data_intent_id) {
        if (!has_result_) return false;
        has_result_ = false;
        if (result_code) *result_code = result_code_;
        if (data_intent_id) *data_intent_id = result_data_intent_id_;
        return true;
    }''',
'''    bool take_result(int* result_code, uint32_t* data_intent_id) {
        // W20-K (S237-WS8, AOSP Activity.java @android-14 L953): mResultCode
        // is a DEFAULT (RESULT_CANCELED), not an "unset" sentinel. finish()
        // delivers (RESULT_CANCELED, null Intent) even when the child never
        // called setResult. The one-shot law is preserved (slot cleared).
        if (result_code)
            *result_code = has_result_ ? result_code_ : 0;
        if (data_intent_id)
            *data_intent_id = has_result_ ? result_data_intent_id_ : 0;
        has_result_ = false;
        return true;
    }
    // Evidence-only accessor: delivery no longer depends on has_result().
    bool has_result() const { return has_result_; }''')

# ── WS9: ViewNode activated/hovered flags ───────────────────────────────
edit('src/framework/android_shadows.h',
'''        bool selected = false;           // View.setSelected''',
'''        bool selected = false;           // View.setSelected
        bool activated = false;          // W20-K (S237-WS9): View.setActivated
        bool hovered = false;            // W20-K (S237-WS9): View.setHovered''')

# ── WS9: webview_node_at helper decl ────────────────────────────────────
edit('src/framework/android_shadows.h',
'''    ViewNode* find_node(uint32_t view_id);''',
'''    ViewNode* find_node(uint32_t view_id);
    // W20-K (S237-WS4): topmost WebView-family node containing the screen
    // point (browser hit-test law) — used by the env-gated swipe-to-browser
    // drag forward so an HTML5 touch game receives the REAL gesture.
    ViewNode* webview_node_at(int x, int y);''')

# ── WS7: engine decl ────────────────────────────────────────────────────
edit('src/dex/dalvik_engine.h',
'''
    // EXP-088+ Phase 1.2 (secondary-DEX injection): Inject ALL classes from''',
'''
    // W20-K (S237-WS7): AOSP Dialog lifecycle-callback delivery — drains the
    // DialogShadow exactly-once tokens (OnCancel -> OnDismiss -> OnShow) and
    // invokes the app's REAL overrides via try_recursive_invoke with the
    // DialogInterface receiver. No-op when nothing is armed; safe to call
    // from any dispatch/frame point (defined in runtime/execution_engine.cpp
    // so it exists in both DALVIK_SPLIT=1 and =0 link sets).
    void deliver_pending_dialog_callbacks();

    // EXP-088+ Phase 1.2 (secondary-DEX injection): Inject ALL classes from''')

# ── WS7: DialogWindow listener fields ───────────────────────────────────
edit('src/framework/dialog_shadow.h',
'''    // Window frame geometry (computed by layout_window() at show time;
    // the renderer draws the frame and the decor tree inside it).
    int frame_left = 0, frame_top = 0, frame_w = 0, frame_h = 0;
};''',
'''    // Window frame geometry (computed by layout_window() at show time;
    // the renderer draws the frame and the decor tree inside it).
    int frame_left = 0, frame_top = 0, frame_w = 0, frame_h = 0;

    // W20-K (S237-WS7, AOSP Dialog.java show/dismiss/cancel message laws):
    // the three lifecycle listeners MUST be stored (the old setters were a
    // shared no-op bucket) and delivered exactly once:
    //   show()    -> OnShow (after onStart)
    //   dismiss() -> OnDismiss
    //   cancel()  -> OnCancel THEN OnDismiss (two separate AOSP messages)
    uint32_t on_show_listener = 0;
    uint32_t on_dismiss_listener = 0;
    uint32_t on_cancel_listener = 0;
    bool pending_show_cb = false;
    bool pending_dismiss_cb = false;
    bool pending_cancel_cb = false;
};''')

# ── WS7: DialogShadow consume API decl ──────────────────────────────────
edit('src/framework/dialog_shadow.h',
'''    // Dismiss a window by its Dialog object id (used by the click router:
    // no-listener button clicks still dismiss, matching real Android).
    void dismiss_dialog(uint32_t dialog_obj_id);''',
'''    // Dismiss a window by its Dialog object id (used by the click router:
    // no-listener button clicks still dismiss, matching real Android).
    void dismiss_dialog(uint32_t dialog_obj_id);

    // W20-K (S237-WS7): exactly-once lifecycle-callback tokens — the ENGINE
    // drains these after a show/dismiss/cancel shadow dispatch and invokes
    // the app's real onShow/onDismiss/onCancel overrides (drain-style, the
    // same shape as ThreadShadow::consume_pending_start).
    bool consume_pending_show_cb(uint32_t& dialog_obj_id);
    bool consume_pending_dismiss_cb(uint32_t& dialog_obj_id);
    bool consume_pending_cancel_cb(uint32_t& dialog_obj_id);''')

# ── WS7: dialog_shadow.cpp — show arm ───────────────────────────────────
edit('src/framework/dialog_shadow.cpp',
'''    if (m == "show" || m == "onStart") {
        if (!win.showing) {
            win.showing = true;
            win.ever_shown = true;
            win.dismissed = false;''',
'''    if (m == "show" || m == "onStart") {
        if (!win.showing) {
            win.showing = true;
            win.ever_shown = true;
            win.dismissed = false;
            // W20-K (S237-WS7): arm the OnShow callback token (delivered
            // exactly once by the engine drain after this dispatch).
            if (win.on_show_listener != 0)
                win.pending_show_cb = true;''')

# ── WS7: dialog_shadow.cpp — dismiss/cancel/hide arm ────────────────────
edit('src/framework/dialog_shadow.cpp',
'''    if (m == "dismiss" || m == "cancel" || m == "hide") {
        win.showing = false;
        win.dismissed = true;
        std::cerr << "[DIALOG] dismiss() obj=" << win.dialog_obj_id << std::endl;
        return CallResult::handled_void();
    }''',
'''    if (m == "dismiss" || m == "cancel" || m == "hide") {
        win.showing = false;
        win.dismissed = true;
        // W20-K (S237-WS7): AOSP cancel() sends the CANCEL message then the
        // DISMISS message (two deliveries); plain dismiss sends DISMISS only.
        if (m == "cancel") {
            if (win.on_cancel_listener != 0) win.pending_cancel_cb = true;
            if (win.on_dismiss_listener != 0) win.pending_dismiss_cb = true;
        } else if (m == "dismiss") {
            if (win.on_dismiss_listener != 0) win.pending_dismiss_cb = true;
        }
        std::cerr << "[DIALOG] dismiss() obj=" << win.dialog_obj_id << std::endl;
        return CallResult::handled_void();
    }''')

# ── WS7: dialog_shadow.cpp — setters store ──────────────────────────────
edit('src/framework/dialog_shadow.cpp',
'''    if (m == "setOnShowListener" || m == "setOnDismissListener" ||
        m == "setOnCancelListener" || m == "setCanceledOnTouchOutside" ||
        m == "setCancelable") {
        return CallResult::handled_void();
    }''',
'''    if (m == "setOnShowListener" || m == "setOnDismissListener" ||
        m == "setOnCancelListener") {
        // W20-K (S237-WS7): AOSP Dialog.java — the listener object is STORED
        // on the dialog (mShowMessage/mDismissMessage/mCancelMessage chain);
        // discarding it silently killed first-paint setup, resource release
        // and cancel hooks in every wiring app.
        uint32_t l = 0;
        if (!ctx.args.empty() && ctx.args[0].kind ==
                framework::CallContext::Arg::Kind::OBJECT)
            l = ctx.args[0].object_id;
        if (m == "setOnShowListener") win.on_show_listener = l;
        else if (m == "setOnDismissListener") win.on_dismiss_listener = l;
        else win.on_cancel_listener = l;
        return CallResult::handled_void();
    }
    if (m == "setCanceledOnTouchOutside" || m == "setCancelable") {
        return CallResult::handled_void();
    }''')

# ── WS7: dialog_shadow.cpp — dismiss_dialog arms + consume impls ────────
edit('src/framework/dialog_shadow.cpp',
'''void DialogShadow::dismiss_dialog(uint32_t dialog_obj_id) {
    if (DialogWindow* win = window_by_obj(dialog_obj_id)) {
        win->showing = false;
        win->dismissed = true;
        std::cerr << "[DIALOG] dismiss_dialog(obj=" << dialog_obj_id << ")" << std::endl;
    }
}''',
'''void DialogShadow::dismiss_dialog(uint32_t dialog_obj_id) {
    if (DialogWindow* win = window_by_obj(dialog_obj_id)) {
        win->showing = false;
        win->dismissed = true;
        // W20-K (S237-WS7): the click-router dismiss path also delivers
        // OnDismiss (AOSP Dialog.dismiss message).
        if (win->on_dismiss_listener != 0) win->pending_dismiss_cb = true;
        std::cerr << "[DIALOG] dismiss_dialog(obj=" << dialog_obj_id << ")" << std::endl;
    }
}

// W20-K (S237-WS7): exactly-once token drains (AOSP Dialog message laws).
bool DialogShadow::consume_pending_show_cb(uint32_t& dialog_obj_id) {
    for (auto& w : windows_) {
        if (w.pending_show_cb) {
            w.pending_show_cb = false;
            dialog_obj_id = w.dialog_obj_id;
            return true;
        }
    }
    return false;
}

bool DialogShadow::consume_pending_dismiss_cb(uint32_t& dialog_obj_id) {
    for (auto& w : windows_) {
        if (w.pending_dismiss_cb) {
            w.pending_dismiss_cb = false;
            dialog_obj_id = w.dialog_obj_id;
            return true;
        }
    }
    return false;
}

bool DialogShadow::consume_pending_cancel_cb(uint32_t& dialog_obj_id) {
    // AOSP ordering: cancel() -> OnCancel first, then OnDismiss — so the
    // cancel drain takes priority over a same-window dismiss token.
    for (auto& w : windows_) {
        if (w.pending_cancel_cb) {
            w.pending_cancel_cb = false;
            dialog_obj_id = w.dialog_obj_id;
            return true;
        }
    }
    return false;
}''')
print("PART 1 done")
