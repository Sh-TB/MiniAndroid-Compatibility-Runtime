// s250_dialog_lifecycle_contract_test — W20-K (S237-WS7, independent coder
// cODER-ohc): AOSP Dialog lifecycle listener law (@android-14 Dialog.java):
//   setOnShowListener/setOnDismissListener/setOnCancelListener must STORE
//   the listener; show() → onShow exactly once; dismiss() → onDismiss once;
//   cancel() → onCancel THEN onDismiss (each exactly once).
// Shadow-level contract (tokens) + the engine drain API exists; real DEX
// delivery exercised by the APK regression runs.
#include "../src/framework/dialog_shadow.h"
#include "../src/dex/dalvik_engine_impl.h"
// W20-K test adapter: DalvikHeap behind the shadow HeapAllocator face.
class TestHeapAdapter : public miniandroid::framework::HeapAllocator {
public:
    explicit TestHeapAdapter(miniandroid::dalvik::DalvikHeap& h) : h_(h) {}
    uint32_t allocate(const std::string& c) override {
        return h_.allocate(c, 0, 0);
    }
    uint32_t get_singleton(const std::string&) override { return 0; }
    uint32_t get_or_create(const std::string& c) override {
        return h_.allocate(c, 0, 0);
    }
    bool has_object(uint32_t) override { return true; }
private:
    miniandroid::dalvik::DalvikHeap& h_;
};


#include <iostream>
#include <string>

using miniandroid::framework::CallContext;
using miniandroid::framework::CallResult;
using miniandroid::framework::DialogShadow;
using miniandroid::framework::DialogWindow;

static int g_pass = 0, g_fail = 0;
static void record(const std::string& name, bool passed,
                   const std::string& detail) {
    std::cout << (passed ? "  PASS  " : "  FAIL  ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << "\n";
    if (passed) ++g_pass; else ++g_fail;
}

static CallContext dctx(uint32_t recv, const std::string& m,
                        uint32_t listener = 0,
                        const std::string& cls = "Landroid/app/Dialog;") {
    CallContext c;
    c.has_receiver = recv != 0;
    c.receiver_id = recv;
    c.receiver_class = cls;
    c.class_name = cls;
    c.method = m;
    if (listener != 0) {
        CallContext::Arg a;
        a.kind = CallContext::Arg::Kind::OBJECT;
        a.object_id = listener;
        c.args.push_back(a);
    }
    return c;
}

int main() {
    std::cout << "== s250_dialog_lifecycle_contract ==\n";
    DialogShadow ds;
    miniandroid::dalvik::DalvikHeap heap;   // the create() face allocates
    TestHeapAdapter heap_adapter(heap);      // the dialog object on the heap
    ds.init(&heap_adapter);

    uint32_t builder = 10000, on_show = 20001, on_dismiss = 20002,
             on_cancel = 20003;
    // AOSP Builder.create() allocates the DialogWindow bound to the returned
    // Dialog object; drive it through the SAME dispatch the DEX call reaches
    // (the shadow mints the dialog object id — the app keeps the identity).
    auto cr = ds.dispatch(dctx(builder, "create", 0,
                               "Landroid/app/AlertDialog$Builder;"));
    uint32_t dlg = cr.handled ? cr.object_id : 0;
    record("ws7_create_yields_dialog", cr.handled && dlg != 0,
           "create() → dialog obj#" + std::to_string(dlg));

    record("ws7_setters_store_listeners",
           ds.dispatch(dctx(dlg, "setOnShowListener", on_show)).handled &&
               ds.dispatch(dctx(dlg, "setOnDismissListener", on_dismiss))
                   .handled &&
               ds.dispatch(dctx(dlg, "setOnCancelListener", on_cancel))
                   .handled,
           "all three setters dispatch");
    DialogWindow* w = ds.window_by_obj(dlg);
    record("ws7_listener_ids_stored",
           w && w->on_show_listener == on_show &&
               w->on_dismiss_listener == on_dismiss &&
               w->on_cancel_listener == on_cancel,
           "listener ids kept on DialogWindow (was: discarded)");

    if (dlg != 0) ds.dispatch(dctx(dlg, "show"));
    record("ws7_show_arms_onshow_once", w && w->pending_show_cb,
           "show() armed OnShow");
    uint32_t got = 0;
    bool first = ds.consume_pending_show_cb(got);
    bool second = ds.consume_pending_show_cb(got);
    record("ws7_onshow_exactly_once",
           first && got == dlg && !second, "drained once, then empty");

    ds.dispatch(dctx(dlg, "dismiss"));
    record("ws7_dismiss_arms_ondismiss", w && w->pending_dismiss_cb,
           "dismiss() armed OnDismiss");
    bool d1 = ds.consume_pending_dismiss_cb(got);
    record("ws7_ondismiss_once", d1 && got == dlg &&
               !ds.consume_pending_dismiss_cb(got), "drained once");

    // fresh dialog for the cancel ordering law
    auto cr2 = ds.dispatch(dctx(10005, "create", 0,
                                "Landroid/app/AlertDialog$Builder;"));
    uint32_t dlg2 = cr2.handled ? cr2.object_id : 0;
    ds.dispatch(dctx(dlg2, "create"));
    ds.dispatch(dctx(dlg2, "setOnCancelListener", on_cancel));
    ds.dispatch(dctx(dlg2, "setOnDismissListener", on_dismiss));
    ds.dispatch(dctx(dlg2, "cancel"));
    uint32_t c1 = 0, c2 = 0;
    bool cancel_first = ds.consume_pending_cancel_cb(c1);
    bool dismiss_next = ds.consume_pending_dismiss_cb(c2);
    record("ws7_cancel_oncancel_then_ondismiss",
           cancel_first && c1 == dlg2 && dismiss_next && c2 == dlg2 &&
               !ds.consume_pending_cancel_cb(c1),
           "cancel() → onCancel THEN onDismiss, each once (AOSP two-message "
           "law)");

    std::cout << "== " << g_pass << " passed / " << g_fail << " failed ==\n";
    return g_fail == 0 ? 0 : 1;
}
