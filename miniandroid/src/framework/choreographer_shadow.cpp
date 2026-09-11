// F-050 — Choreographer shadow implementation. See choreographer_shadow.h
// for the root-gap evidence chain and the transferred AOSP/AndroidX laws.

#include "choreographer_shadow.h"

#include <algorithm>
#include <iostream>

namespace miniandroid { namespace framework {

CallResult ChoreographerShadow::dispatch(const CallContext& ctx) {
    if (!heap_) return CallResult::not_handled();
    const std::string& m = ctx.method;

    if (m == "getInstance") {
        // AOSP: thread-local instance for the current Looper. The runtime
        // has exactly one main Looper (LooperShadow law), so the instance
        // is a singleton heap object — identity preserved across calls
        // (AndroidUiDispatcher caches it, K.u compares J.k vs K.i by
        // reference equality: LM1/i;.a(Object,Object) == law).
        if (choreographer_obj_id_ == 0) {
            choreographer_obj_id_ = heap_->get_or_create("Landroid/view/Choreographer;");
        }
        return CallResult::handled_object(choreographer_obj_id_,
                                          "Landroid/view/Choreographer;");
    }

    if (m == "postFrameCallback" || m == "postFrameCallbackDelayed") {
        // args[0] = FrameCallback; postFrameCallbackDelayed adds args[1] = delay (J ms).
        uint32_t cb_id = ctx.arg_as_object(0, 0);
        if (cb_id == 0) return CallResult::handled_void();  // no-op on null cb (fail-soft)
        int64_t delay_ms = 0;
        if (m == "postFrameCallbackDelayed") {
            const auto& a = (ctx.args.size() > 1) ? ctx.args[1] : CallContext::Arg{};
            if (a.kind == CallContext::Arg::Kind::LONG) delay_ms = a.long_val;
            else if (a.kind == CallContext::Arg::Kind::INT) delay_ms = a.int_val;
        }
        std::string cb_cls = "Landroid/view/Choreographer$FrameCallback;";
        if (!ctx.args.empty() && !ctx.args[0].object_class.empty())
            cb_cls = ctx.args[0].object_class;
        PendingCallback pc;
        pc.callback_id = cb_id;
        pc.callback_class = cb_cls;
        pc.ready_at_nanos = frame_time_nanos_ + delay_ms * 1000000LL;
        pc.enqueue_seq = next_seq_++;
        pending_.push_back(std::move(pc));
        std::cerr << "[CHOREO] postFrameCallback cb=" << cb_id
                  << " class=" << cb_cls << " delay=" << delay_ms
                  << "ms ready_at=" << (frame_time_nanos_ + delay_ms * 1000000LL)
                  << "ns pending=" << pending_.size() << std::endl;
        return CallResult::handled_void();
    }

    if (m == "removeFrameCallback") {
        uint32_t cb_id = ctx.arg_as_object(0, 0);
        size_t before = pending_.size();
        pending_.erase(
            std::remove_if(pending_.begin(), pending_.end(),
                           [&](const PendingCallback& p) { return p.callback_id == cb_id; }),
            pending_.end());
        std::cerr << "[CHOREO] removeFrameCallback cb=" << cb_id
                  << " removed=" << (before - pending_.size()) << std::endl;
        return CallResult::handled_void();
    }

    if (m == "getFrameTimeNanos" || m == "getFrameTime") {
        // AOSP: only legal inside a doFrame callback (ISE otherwise).
        // Documented deviation: fail-soft to the last frame time; the
        // strict ISE law is recorded in the ROOT_LAW ledger as a queued
        // strictness item. Deterministic either way.
        return CallResult::handled_long(frame_time_nanos_);
    }

    return CallResult::not_handled();
}

std::vector<ChoreographerShadow::DueFrame> ChoreographerShadow::take_due_callbacks() {
    std::vector<DueFrame> out;
    if (pending_.empty()) return out;
    // ONE vsync tick: advance the deterministic frame clock, deliver ONE
    // shared timestamp to every callback ready at this tick (AOSP doFrame
    // law: all CALLBACK_ANIMATION records run with the same frameTimeNanos).
    frame_time_nanos_ += kFrameIntervalNanos;
    std::vector<size_t> due_idx;
    for (size_t i = 0; i < pending_.size(); ++i)
        if (pending_[i].ready_at_nanos <= frame_time_nanos_) due_idx.push_back(i);
    std::stable_sort(due_idx.begin(), due_idx.end(), [&](size_t a, size_t b) {
        if (pending_[a].ready_at_nanos != pending_[b].ready_at_nanos)
            return pending_[a].ready_at_nanos < pending_[b].ready_at_nanos;
        return pending_[a].enqueue_seq < pending_[b].enqueue_seq;
    });
    for (size_t i : due_idx) {
        DueFrame d;
        d.callback_id = pending_[i].callback_id;
        d.callback_class = pending_[i].callback_class;
        d.frame_time_nanos = frame_time_nanos_;
        out.push_back(std::move(d));
    }
    // Remove consumed records (descending order keeps offsets valid).
    std::sort(due_idx.begin(), due_idx.end(), std::greater<size_t>());
    for (size_t i : due_idx) pending_.erase(pending_.begin() + static_cast<long>(i));
    std::cerr << "[CHOREO] doFrame tick t=" << frame_time_nanos_
              << "ns fired=" << out.size()
              << " still_pending=" << pending_.size() << std::endl;
    return out;
}

}} // namespace miniandroid::framework
