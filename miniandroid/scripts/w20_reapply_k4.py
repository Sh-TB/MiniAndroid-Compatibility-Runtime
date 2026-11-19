#!/usr/bin/env python3
"""W20-K re-apply PART 4: Frozen Options seeds (both copies), WS4 webview
changedTouches, WS4 drag forward, Makefile battery line."""
def edit(path, old, new, count=1):
    s = open(path).read()
    n = s.count(old)
    assert n == count, f"{path}: {n} != {count}"
    open(path,'w').write(s.replace(old,new))
    print(f"OK {path} ({old[:36].strip()}...)")

SEEDS = '''
    // W20-K (S237-PLAY, Frozen Bubble): AOSP BitmapFactory.Options PUBLIC
    // fields (BitmapFactory.java Options @android-14) — Class.getField on
    // Options must SUCCEED (real Android answers from framework metadata).
    // Defaults per AOSP: inScaled=true, inPremultiplied=true, rest 0/false.
    seed("Landroid/graphics/BitmapFactory$Options;.inScaled",
         DalvikValue::make_bool(true));
    seed("Landroid/graphics/BitmapFactory$Options;.inPremultiplied",
         DalvikValue::make_bool(true));
    seed("Landroid/graphics/BitmapFactory$Options;.inDither",
         DalvikValue::make_bool(false));
    seed("Landroid/graphics/BitmapFactory$Options;.inMutable",
         DalvikValue::make_bool(false));
    seed("Landroid/graphics/BitmapFactory$Options;.inJustDecodeBounds",
         DalvikValue::make_bool(false));
    seed("Landroid/graphics/BitmapFactory$Options;.inSampleSize",
         DalvikValue::make_int(0));
    seed("Landroid/graphics/BitmapFactory$Options;.inDensity",
         DalvikValue::make_int(0));
    seed("Landroid/graphics/BitmapFactory$Options;.inTargetDensity",
         DalvikValue::make_int(0));
    seed("Landroid/graphics/BitmapFactory$Options;.inScreenDensity",
         DalvikValue::make_int(0));
    seed("Landroid/graphics/BitmapFactory$Options;.inPreferredDensity",
         DalvikValue::make_int(0));
    seed("Landroid/graphics/BitmapFactory$Options;.outWidth",
         DalvikValue::make_int(-1));
    seed("Landroid/graphics/BitmapFactory$Options;.outHeight",
         DalvikValue::make_int(-1));'''

for p, anchor in [
    ('src/dex/dalvik_opcodes_invoke.cpp', 'seed("Landroid/os/Build;.SERIAL"'),
    ('src/dex/dalvik_engine.cpp', 'seed("Landroid/os/Build;.SERIAL"'),
]:
    s = open(p).read()
    i = s.find(anchor)
    assert i >= 0, p
    le = s.find('\n', i)
    if 'BitmapFactory$Options;.inScaled' in s:
        print(f"SKIP {p} (already seeded)")
        continue
    s = s[:le] + SEEDS + s[le:]
    open(p,'w').write(s)
    print(f"OK {p} seeded")

# ── WS4: webview changedTouches (env-gated) ─────────────────────────────
edit('src/webview/webview_engine.cpp',
'''    JS_SetPropertyUint32(impl->ctx, touches, 0, t0);
    JS_SetPropertyStr(impl->ctx, ev, "touches", touches);
    impl->dispatch(hit, lower_s(type), ev);
    return true;
}''',
'''    JS_SetPropertyUint32(impl->ctx, touches, 0, t0);
    JS_SetPropertyStr(impl->ctx, ev, "touches", touches);
    // W20-K (S237-WS4, env-gated MINIANDROID_WV_CHANGED_TOUCHES, default
    // OFF): W3C TouchEvent completeness for real HTML5 games. 2048's
    // touchend reads event.changedTouches[0].clientX, guards on
    // event.touches.length, and calls preventDefault() — all three threw
    // TypeError before this gate. Gate unset => byte-identical pristine
    // behavior (S237 evidence: sha f3d5b860... both on and off).
    static const bool wv_changed_touches =
        std::getenv("MINIANDROID_WV_CHANGED_TOUCHES") != nullptr;
    if (wv_changed_touches) {
        bool is_touch = lower_s(type).rfind("touch", 0) == 0;
        bool is_end = lower_s(type) == "touchend";
        JSValue changed = JS_NewArray(impl->ctx);
        JSValue c0 = JS_NewObject(impl->ctx);
        JS_SetPropertyStr(impl->ctx, c0, "clientX", JS_NewInt32(impl->ctx, x));
        JS_SetPropertyStr(impl->ctx, c0, "clientY", JS_NewInt32(impl->ctx, y));
        JS_SetPropertyStr(impl->ctx, c0, "pageX", JS_NewInt32(impl->ctx, x));
        JS_SetPropertyStr(impl->ctx, c0, "pageY", JS_NewInt32(impl->ctx, y));
        JS_SetPropertyUint32(impl->ctx, changed, 0, c0);
        JS_SetPropertyStr(impl->ctx, ev, "changedTouches", changed);
        if (is_touch) {
            JSValue tgt = JS_NewArray(impl->ctx);
            if (!is_end) {
                JSValue g0 = JS_NewObject(impl->ctx);
                JS_SetPropertyStr(impl->ctx, g0, "clientX",
                                  JS_NewInt32(impl->ctx, x));
                JS_SetPropertyStr(impl->ctx, g0, "clientY",
                                  JS_NewInt32(impl->ctx, y));
                JS_SetPropertyUint32(impl->ctx, tgt, 0, g0);
            }
            JS_SetPropertyStr(impl->ctx, ev, "targetTouches", tgt);
            // W3C: touches/targetTouches are EMPTY on touchend.
            if (is_end)
                JS_SetPropertyStr(impl->ctx, ev, "touches",
                                  JS_NewArray(impl->ctx));
            auto noop_method =
                [](JSContext*, JSValueConst, int,
                   JSValueConst*) -> JSValue { return JS_UNDEFINED; };
            for (const char* mth : {"preventDefault", "stopPropagation",
                                    "stopImmediatePropagation"}) {
                JSValue fn = JS_NewCFunction(impl->ctx, noop_method, mth, 0);
                JS_SetPropertyStr(impl->ctx, ev, mth, fn);
            }
        }
    }
    impl->dispatch(hit, lower_s(type), ev);
    return true;
}''')

# ── WS4: swipe → browser drag forward (env-gated) ───────────────────────
edit('src/runtime/execution_engine.cpp',
'''                auto up_rec = touch_dispatcher_->dispatch(
                    swipe_root, {framework::TouchAction::UP, x2, y2});
                // Drain the gesture's posted callbacks (PerformClick chain).''',
'''                auto up_rec = touch_dispatcher_->dispatch(
                    swipe_root, {framework::TouchAction::UP, x2, y2});
                // W20-K (S237-WS4, env-gated MINIANDROID_WV_DRAG_FORWARD,
                // default OFF): forward the REAL multi-point gesture into
                // the WebView browser path (touchstart -> N x touchmove ->
                // touchend at view-local coordinates). Before this gate the
                // DEX-layer MOVE stream reached the app's Java onTouchEvent
                // but the browser engine only ever saw the single-point
                // click burst — an HTML5 touch game (2048) never received
                // touchmove. Gate unset => byte-identical pristine behavior.
                static const bool wv_drag_forward =
                    std::getenv("MINIANDROID_WV_DRAG_FORWARD") != nullptr;
                if (wv_drag_forward && shadow_registry_) {
                    if (auto* vs = shadow_registry_->find_as<
                            framework::ViewShadow>()) {
                        if (auto* wv = vs->webview_node_at(x1, y1)) {
                            if (auto eng =
                                    webview::WebViewRegistry::instance().find(
                                        wv->view_id)) {
                                const int lx1 = x1 - wv->x;
                                const int ly1 = y1 - wv->y;
                                const int lx2 = x2 - wv->x;
                                const int ly2 = y2 - wv->y;
                                std::cerr << "[WV-INPUT] swipe -> browser"
                                          << " gesture local (" << lx1 << ","
                                          << ly1 << ") -> (" << lx2 << ","
                                          << ly2 << ") view=o" << wv->view_id
                                          << std::endl;
                                eng->pointer_event(lx1, ly1, "touchstart");
                                for (int i = 1; i <= steps; ++i) {
                                    eng->pointer_event(
                                        lx1 + (lx2 - lx1) * i / steps,
                                        ly1 + (ly2 - ly1) * i / steps,
                                        "touchmove");
                                }
                                eng->pointer_event(lx2, ly2, "touchend");
                            }
                        }
                    }
                }
                // Drain the gesture's posted callbacks (PerformClick chain).''')

# ── Makefile battery line ───────────────────────────────────────────────
edit('Makefile',
'''s246_layout_closure_law_test s247_grid_rtl_law_test''',
'''s246_layout_closure_law_test s247_grid_rtl_law_test \\
	s248_sqlite_cursor_contract_test s249_adapter_position_contract_test s250_dialog_lifecycle_contract_test s251_activity_result_contract_test s252_view_state_flags_contract_test''')
print("PART 4 done")
