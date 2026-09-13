#!/usr/bin/env python3
"""F-100 (R-NEW-333): idle message-queue drain law in pump_compose_frames.

ROOT (evidence, dooz v18 S34 run): AndroidUiDispatcher.dispatch() posts BOTH
handler.post(dispatchCallback) AND choreographer.postFrameCallback(dispatchCallback)
(upstream AndroidUiDispatcher.android.kt:136-146). The handler-side J$c.run()
drains the trampolined queue and LEGALLY removes the choreographer-side
callback when toRunOnFrame is empty (upstream run() law). The old pump gated
its whole body on has_pending_callbacks() and broke out BEFORE the queue
drain once that legal remove landed — leaving runRecomposeAndApplyChanges'
withContext(broadcastFrameClock) continuation queued forever: no runner
resumption, no recomposition, NavHost start-destination LaunchedEffect never
ran, tree stayed root+1, 0 canvas ops, placeholder frame.

UPSTREAM LAWS (AOSP frameworks/base MessageQueue/Looper + AndroidX
AndroidUiDispatcher.android.kt):
  * Looper/MessageQueue dispatches messages when idle INDEPENDENT of vsync;
    the Choreographer frame is just another wake source ("dispatch during a
    handler callback or choreographer's animation frame stage, whichever
    comes first" — AndroidUiDispatcher class doc).
  * dispatchCallback.run(): performTrampolineDispatch() ALWAYS; then remove
    the choreographer callback ONLY if toRunOnFrame is empty.
Therefore the pump must drain the handler queue EVERY tick (before/after any
frame fire) and keep ticking while EITHER source has work, bounded.

No app/class special-casing: Choreographer + Handler are platform primitives.
Idempotent patch; keeps the same function signature.
"""
import sys

P = '/tmp/my-project/miniandroid/src/runtime/execution_engine.cpp'
src = open(P).read()

start_marker = "int ExecutionEngine::pump_compose_frames(int max_frames) {"
end_marker = "\n    return fired_frames;\n}"

i0 = src.find(start_marker)
if i0 < 0:
    print('PUMP NOT FOUND')
    sys.exit(1)
if '[F100-IDLEDRAIN]' in src[i0:i0+4000]:
    print('already present')
    sys.exit(0)
i1 = src.find(end_marker, i0)
assert i1 > i0

new_body = """int ExecutionEngine::pump_compose_frames(int max_frames) {
    auto* registry = dalvik_engine_.get_shadow_registry();
    auto* cs = registry ? registry->find_as<framework::ChoreographerShadow>() : nullptr;
    if (!cs) return 0;
    auto* hs = registry->find_as<framework::HandlerShadow>();
    int fired_frames = 0;
    // [F100-IDLEDRAIN] AOSP MessageQueue idle law: messages dispatch on idle
    // INDEPENDENT of vsync (the Choreographer frame is only one wake source;
    // AndroidUiDispatcher.dispatch posts BOTH a handler message and a frame
    // callback — "whichever comes first"). The handler-side dispatchCallback
    // drains the trampoline queue and may legally remove the choreographer
    // callback while dispatcher continuations are still queued; the pump
    // must therefore drain the queue EVERY tick and keep ticking while
    // either source has work. Bounded ticks keep reruns byte-deterministic.
    for (int tick = 0; tick < max_frames; ++tick) {
        bool did_work = false;
        if (cs->has_pending_callbacks()) {
            auto due = cs->take_due_callbacks();
            if (!due.empty()) {
                ++fired_frames;
                did_work = true;
                for (auto& d : due)
                    invoke_choreographer_do_frame(d.callback_id, d.callback_class,
                                                  d.frame_time_nanos);
            }
        }
        // Drain the resumption work the callbacks/dispatch posted — ALWAYS,
        // vsync-independent (one MessageQueue law; the same 64-round bound
        // the UC009-WIRE composition drain uses).
        if (hs) {
            for (int round = 0; round < 64; ++round) {
                std::vector<uint32_t> drained;
                size_t n = hs->drain_ready(&drained);
                if (n == 0) break;
                did_work = true;
                std::cerr << "[F100-PUMP] frame=" << fired_frames
                          << " drain round=" << round << " runnable(s)=" << n
                          << std::endl;
                for (uint32_t rid : drained) invoke_handler_runnable(rid);
            }
        }
        if (!did_work) break;  // quiescence: no vsync, no messages
    }
    if (fired_frames > 0) {
        std::cerr << "[CHOREO-PUMP] " << fired_frames
                  << " frame(s) fired (bound=" << max_frames << ")" << std::endl;
    }
    return fired_frames;
}"""

src = src[:i0] + new_body + src[i1 + len(end_marker):]
open(P, 'w').write(src)
print('F-100 pump law applied')
