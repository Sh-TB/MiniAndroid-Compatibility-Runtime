// window_insets_shadow.cpp — S113 ROOT-059 implementation. See the header
// for the platform law; this file is deliberately small: the whole failure
// chain was "platform object materialization returned null".
#include "window_insets_shadow.h"

#include <iostream>

namespace miniandroid { namespace framework {

void WindowInsetsShadow::init(HeapAllocator* heap) { heap_ = heap; }

uint32_t WindowInsetsShadow::materialize() {
    if (!heap_) return 0;
    return heap_->allocate("Landroid/view/WindowInsets;");
}

CallResult WindowInsetsShadow::dispatch(const CallContext& ctx) {
    const std::string& m = ctx.method;
    if (!heap_) return CallResult{};

    // Builder <init> — ()V and (WindowInsets)V: the receiver object is
    // already heap-allocated by new-instance; recording the constructor as
    // a no-op keeps the copy-source object intact (fields default zero).
    if (m == "<init>") return CallResult::handled_void();

    // Builder.build() — non-null WindowInsets law (ROOT-059 entry point).
    if (m == "build") {
        uint32_t obj = materialize();
        if (obj == 0) return CallResult{};
        std::cerr << "[ROOT-059] WindowInsets$Builder.build -> o" << obj << std::endl;
        return CallResult::handled_object(obj, "Landroid/view/WindowInsets;");
    }

    // Instance methods on WindowInsets — receiver non-null chain law.
    uint32_t recv = ctx.has_receiver ? ctx.receiver_id : 0;
    if (recv == 0) recv = materialize();
    if (recv == 0) return CallResult{};

    if (m == "consumeDisplayCutout" || m == "consumeStableInsets" ||
        m == "consumeSystemWindowInsets" || m == "replaceSystemWindowInsets") {
        // AOSP: consumed copies; with zero insets the copy equals self.
        // Returning the receiver keeps the androidx Impl.<clinit> CONSUMED
        // chain fully non-null (ROOT-059).
        return CallResult::handled_object(recv, "Landroid/view/WindowInsets;");
    }
    if (m == "getDisplayCutout") {
        // No cutout on this runtime — AOSP null law for cutout-free devices.
        return CallResult::handled_null();
    }
    if (m == "getInsets") {
        // API 29 Insets law: zero-insets object (no system bars recorded).
        uint32_t ins = heap_->allocate("Landroid/graphics/Insets;");
        return CallResult::handled_object(ins, "Landroid/graphics/Insets;");
    }
    if (m.rfind("getSystemWindowInset", 0) == 0) {
        return CallResult::handled_int(0);
    }
    return CallResult{};   // unclaimed → honest REC-MISS
}

}} // namespace miniandroid::framework
