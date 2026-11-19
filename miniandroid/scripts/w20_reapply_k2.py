#!/usr/bin/env python3
"""W20-K re-apply PART 2: WS9 arms + state_list + WS5 + WS6 + engine drain +
frame pump + bridge entry + WS4."""
def edit(path, old, new, count=1):
    s = open(path).read()
    n = s.count(old)
    assert n == count, f"{path}: pattern count {n} != {count}\n---\n{old[:120]}"
    open(path, 'w').write(s.replace(old, new))
    print(f"OK {path} ({old[:40].strip()}...)")

# ── WS9: the 10 dispatch arms (after the setEnabled arm) ────────────────
edit('src/framework/android_shadows.cpp',
'''    if (m == "setEnabled") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        n->enabled = ctx.arg_as_bool(0, true);
        return CallResult::handled_void();
    }''',
'''    if (m == "setEnabled") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        n->enabled = ctx.arg_as_bool(0, true);
        return CallResult::handled_void();
    }
    // ── W20-K (S237-WS9): AOSP View state-flag family (View.java setFlags
    // law @android-14: PFLAG_SELECTED/ACTIVATED/PRESSED/LONG_CLICKABLE/
    // HOVERED) — the whole family previously fell through to not_handled()
    // (REC-MISS silent no-op). Corpus DEX call-site demand: openlauncher 17,
    // stopwatch 3, tictactoe 2, opensudoku 2, dooz/a2048 1 each. The
    // state-list background re-picks EVERY frame, so the flag change reaches
    // rendering without an extra dirty pass.
    if (m == "setSelected") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        n->selected = ctx.arg_as_bool(0, false);
        return CallResult::handled_void();
    }
    if (m == "isSelected") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        return CallResult::handled_bool(n->selected);
    }
    if (m == "setPressed") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        n->pressed = ctx.arg_as_bool(0, false);
        return CallResult::handled_void();
    }
    if (m == "isPressed") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        return CallResult::handled_bool(n->pressed);
    }
    if (m == "setActivated") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        n->activated = ctx.arg_as_bool(0, false);
        return CallResult::handled_void();
    }
    if (m == "isActivated") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        return CallResult::handled_bool(n->activated);
    }
    if (m == "setHovered") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        n->hovered = ctx.arg_as_bool(0, false);
        return CallResult::handled_void();
    }
    if (m == "isHovered") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        return CallResult::handled_bool(n->hovered);
    }
    if (m == "setLongClickable") {
        // AOSP: setLongClickable(true) is implicit when an
        // OnLongClickListener is attached; the stored listener wins.
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        bool v = ctx.arg_as_bool(0, false);
        n->long_clickable = v || n->long_click_listener_id != 0;
        return CallResult::handled_void();
    }
    if (m == "isLongClickable") {
        auto* n = get_or_create_node(ctx.receiver_id, ctx.receiver_class.empty() ? ctx.class_name : ctx.receiver_class);
        return CallResult::handled_bool(n->long_clickable);
    }''')

# ── WS9: webview_node_at impl (before find_node impl) ───────────────────
edit('src/framework/android_shadows.cpp',
'''const ViewShadow::ViewNode* ViewShadow::find_node(uint32_t view_id) const {''',
'''ViewShadow::ViewNode* ViewShadow::webview_node_at(int x, int y) {
    ViewNode* best = nullptr;
    int best_area = -1;
    for (auto& kv : nodes_) {
        ViewNode* n = kv.second.get();
        if (!n || n->class_desc.find("WebView;") == std::string::npos)
            continue;
        if (n->visibility != 0) continue;  // VISIBLE=0 law
        if (x < n->x || y < n->y ||
            x >= n->x + n->measured_width ||
            y >= n->y + n->measured_height)
            continue;
        int area = n->measured_width * n->measured_height;
        if (area < best_area || best_area < 0) {
            best_area = area;
            best = n;
        }
    }
    return best;
}

const ViewShadow::ViewNode* ViewShadow::find_node(uint32_t view_id) const {''')

# ── WS9: state_list.h signature ─────────────────────────────────────────
edit('src/framework/state_list.h',
'''    bool checked = false,  // S106 MG-022: android:state_checked law
    bool focused = false,  // C9-18: android:state_focused law
    bool hovered = false,  // C9-18: android:state_hovered law''',
'''    bool checked = false,  // S106 MG-022: android:state_checked law
    bool focused = false,  // C9-18: android:state_focused law
    bool hovered = false,  // C9-18: android:state_hovered law
    // W20-K (S237-WS9): AOSP first-match law covers state_activated and
    // state_window_focused too (window_focused defaults TRUE — the plain
    // default view state of a focused window).
    bool activated = false,  // android:state_activated law
    bool window_focused = true,  // android:state_window_focused law''')

# ── WS9: state_list.cpp enforcement ─────────────────────────────────────
edit('src/framework/state_list.cpp',
'''    const ViewShadow::ViewNode::BgStateItem** winner_out) {''',
'''    bool activated, bool window_focused,
    const ViewShadow::ViewNode::BgStateItem** winner_out) {''')
edit('src/framework/state_list.cpp',
'''        if (it.state_hovered >= 0 &&
            it.state_hovered != (hovered ? 1 : 0))
            continue;''',
'''        if (it.state_hovered >= 0 &&
            it.state_hovered != (hovered ? 1 : 0))
            continue;
        // W20-K (S237-WS9): state_activated / state_window_focused were
        // parsed since S127 but NEVER consulted — a declared
        // state_activated="true" item matched as a wildcard and could win
        // the first-match slot for a view that was NOT activated.
        if (it.state_activated >= 0 &&
            it.state_activated != (activated ? 1 : 0))
            continue;
        if (it.state_window_focused >= 0 &&
            it.state_window_focused != (window_focused ? 1 : 0))
            continue;''')

# ── WS9: render caller forwards real flags ──────────────────────────────
edit('src/runtime/execution_engine.cpp',
'''                                        node->checked, node->focused, false,
                                        &win)) {''',
'''                                        node->checked, node->focused,
                                        node->hovered, node->activated,
                                        true, &win)) {''')

# ── WS7: frame-pump drain ───────────────────────────────────────────────
edit('src/runtime/execution_engine.cpp',
'''    trace_engine_.info("ExecutionEngine", "stage_render_frame", "Rendering frame");''',
'''    trace_engine_.info("ExecutionEngine", "stage_render_frame", "Rendering frame");
    // W20-K (S237-WS7): AOSP Dialog lifecycle delivery — drain armed
    // onShow/onDismiss/onCancel tokens BEFORE this frame paints (a dialog
    // shown late in onCreate must fire onShow before first paint, and a
    // cancel/dismiss that was the last framework call still delivers).
    dalvik_engine_.deliver_pending_dialog_callbacks();''')

# ── WS7: engine drain definition (append inside namespaces at EOF) ──────
edit('src/runtime/execution_engine.cpp',
'''}  // namespace runtime
}  // namespace miniandroid''',
'''namespace miniandroid {
namespace dalvik {

// W20-K (S237-WS7): AOSP Dialog lifecycle-callback delivery — the
// DialogShadow stores listener ids and arms exactly-once tokens; this drain
// invokes the app's REAL overrides. Order per AOSP Dialog.java: cancel()
// sends the CANCEL message then the DISMISS message; show() sends the SHOW
// message after onStart. Defined in this always-linked TU.
void DalvikExecutionEngine::deliver_pending_dialog_callbacks() {
    if (!shadow_registry_) return;
    auto* dsh = shadow_registry_->find_as<framework::DialogShadow>();
    if (!dsh) return;

    auto deliver = [&](uint32_t dlg, const char* method) {
        if (dlg == 0) return;
        std::string cls = "Landroid/app/Dialog;";
        if (auto* obj = get_heap_public().get(dlg))
            if (!obj->class_descriptor.empty())
                cls = obj->class_descriptor;
        DalvikValue ret;
        DalvikExecutionResult res;
        std::vector<DalvikValue> args;
        args.push_back(DalvikValue::make_object(
            dlg, "Landroid/app/Dialog;"));
        try_recursive_invoke(cls, method, args, ret, res);
    };

    uint32_t dlg = 0;
    while (dsh->consume_pending_cancel_cb(dlg))
        deliver(dlg, "onCancel");
    while (dsh->consume_pending_dismiss_cb(dlg))
        deliver(dlg, "onDismiss");
    while (dsh->consume_pending_show_cb(dlg))
        deliver(dlg, "onShow");
}

}  // namespace dalvik
}  // namespace miniandroid''')
print("PART 2 done")
