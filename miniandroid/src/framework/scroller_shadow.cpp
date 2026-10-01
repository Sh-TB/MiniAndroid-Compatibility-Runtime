// scroller_shadow.cpp — S130 (R-NEW-427, CAP-SCROLLING-126) Scroller/OverScroller.
// Laws quoted in scroller_shadow.h (Scroller.java, android-14.0.0_r2).
#include "scroller_shadow.h"

#include <iostream>

namespace miniandroid { namespace framework {

bool ScrollerShadow::handles_class(const std::string& class_name) const {
    return class_name.find("Landroid/widget/Scroller;") == 0 ||
           class_name.find("Landroid/widget/OverScroller;") == 0;
}

CallResult ScrollerShadow::dispatch(const CallContext& ctx) {
    const std::string& m = ctx.method;
    // Constructors — allocate the model onto the heap object (ctor capture,
    // TouchDelegateShadow precedent).
    if (m == "<init>") {
        uint32_t id = ctx.receiver_id;
        if (id == 0) return CallResult::handled_void();
        models_[id] = ScrollerModel{};
        return CallResult::handled_void();
    }
    auto it = models_.find(ctx.receiver_id);
    if (it == models_.end()) {
        // Methods invoked on a not-yet-modeled object: allocate lazily so the
        // law never NPEs (AOSP: a Scroller is always usable after ctor).
        if (!ctx.has_receiver || ctx.receiver_id == 0) return CallResult::not_handled();
        it = models_.emplace(ctx.receiver_id, ScrollerModel{}).first;
    }
    ScrollerModel& mdl = it->second;
    const int64_t now_ms = now();

    if (m == "startScroll") {
        // startScroll(startX,startY,dx,dy[,duration]) — L376/394.
        const int sx = ctx.arg_as_int(0, 0), sy = ctx.arg_as_int(1, 0);
        const int dx = ctx.arg_as_int(2, 0), dy = ctx.arg_as_int(3, 0);
        const int dur = ctx.args.size() >= 5
                            ? ctx.arg_as_int(4, ScrollerModel::kDefaultDurationMs)
                            : ScrollerModel::kDefaultDurationMs;
        mdl.start_scroll(sx, sy, dx, dy, dur, now_ms);
        std::cerr << "[SCROLLER] startScroll obj=" << ctx.receiver_id
                  << " start=(" << sx << "," << sy << ") delta=(" << dx << "," << dy
                  << ") dur=" << mdl.duration_ms << "ms" << std::endl;
        return CallResult::handled_void();
    }
    if (m == "fling") {
        // fling(startX,startY,vx,vy,minX,maxX,minY,maxY[,overX,overY]).
        const int sx = ctx.arg_as_int(0, 0), sy = ctx.arg_as_int(1, 0);
        const float vx = ctx.arg_as_float(2, 0.0f), vy = ctx.arg_as_float(3, 0.0f);
        const int min_x = ctx.arg_as_int(4, 0), max_x = ctx.arg_as_int(5, 0);
        const int min_y = ctx.arg_as_int(6, 0), max_y = ctx.arg_as_int(7, 0);
        mdl.fling(sx, sy, vx, vy, min_x, max_x, min_y, max_y, now_ms);
        std::cerr << "[SCROLLER] fling obj=" << ctx.receiver_id
                  << " start=(" << sx << "," << sy << ") v=(" << vx << "," << vy
                  << ") final=(" << mdl.final_x << "," << mdl.final_y
                  << ") dur=" << mdl.duration_ms << "ms" << std::endl;
        return CallResult::handled_void();
    }
    if (m == "computeScrollOffset") {
        return CallResult::handled_bool(mdl.compute_scroll_offset(now_ms));
    }
    if (m == "getCurrX") return CallResult::handled_int(mdl.curr_x);
    if (m == "getCurrY") return CallResult::handled_int(mdl.curr_y);
    if (m == "getStartX") return CallResult::handled_int(mdl.start_x);
    if (m == "getStartY") return CallResult::handled_int(mdl.start_y);
    if (m == "getFinalX") return CallResult::handled_int(mdl.final_x);
    if (m == "getFinalY") return CallResult::handled_int(mdl.final_y);
    if (m == "getDuration") return CallResult::handled_int(mdl.duration_ms);
    if (m == "isFinished") return CallResult::handled_bool(mdl.finished);
    if (m == "forceFinished") {
        mdl.force_finished(ctx.arg_as_bool(0, true));
        return CallResult::handled_void();
    }
    if (m == "abortAnimation") {
        mdl.abort(now_ms);
        return CallResult::handled_void();
    }
    if (m == "timePassed") {
        return CallResult::handled_int(int(mdl.finished ? mdl.duration_ms
                                                        : now_ms - mdl.start_ms));
    }
    if (m == "isScrollingInDirection") return CallResult::handled_bool(false);
    if (m == "setInterpolator" || m == "setFriction" || m == "setFinalX" ||
        m == "setFinalY") {
        return CallResult::handled_void();
    }
    (void)now_ms;
    (void)mdl;
    return CallResult::not_handled();
}

std::vector<std::string> ScrollerShadow::implemented_methods() const {
    return {"<init>", "startScroll", "fling", "computeScrollOffset", "getCurrX",
            "getCurrY", "getStartX", "getStartY", "getFinalX", "getFinalY",
            "getDuration", "isFinished", "forceFinished", "abortAnimation",
            "timePassed", "setInterpolator"};
}

std::vector<std::string> ScrollerShadow::stubbed_methods() const {
    // Documented boundaries (not observed by the corpus; honest record).
    return {"extendDuration", "setFinalX", "setFinalY", "setFriction",
            "isScrollingInDirection"};
}

}}  // namespace miniandroid::framework
