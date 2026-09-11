// F-050 ROOT FIX — android.view.Choreographer shadow family + frame pump.
//
// ROOT GAP (discovered via the dooz v18 Compose first-frame battle at
// HEAD 6ff11eb2): Compose's AndroidUiDispatcher (R8 class J) and
// AndroidUiFrameClock (R8 class K) park the first composition at
// `withFrameNanos` by posting a Choreographer.FrameCallback:
//
//   J$a;.c (CurrentThread lazy):
//     Choreographer.getInstance()                        -> REC-MISS -> null
//     O0/b.a(Looper.getMainLooper())                     (F-029a Handler)
//     AndroidUiDispatcher.<init>(choreographer, handler)
//   K;.u (AndroidUiFrameClock.withFrameNanos):
//     dispatcher-choreographer identity check (J.k vs K.i)
//     synchronized(J.m) { J.o += K$c; if (!J.r) { J.r=true;
//       J.k.postFrameCallback(J.s) } }                   -> REC-MISS -> drop
//
// The runtime had NO Choreographer shadow, so postFrameCallback silently
// no-opped and NOTHING ever called FrameCallback.doFrame(frameTimeNanos).
// The suspended continuation was never resumed: Recomposer.applyChanges
// never ran, AndroidComposeView stayed children=0 size=0x105, and the
// framebuffer stayed 0/2073600 non-white (deterministic blank). Trace:
//   Choreographer.postFrameCallback depth=8  (posted, dropped)
//   ... no doFrame dispatch in the entire 14.6 MB run log ...
//   Choreographer.removeFrameCallback depth=1 (cancellation cleanup)
//
// AOSP laws transferred (frameworks/base Choreographer.java + AndroidX
// compose/ui/platform/AndroidUiDispatcher.android.kt):
//   * Choreographer.getInstance() returns the thread-local instance bound
//     to the current thread's Looper. The runtime is a deterministic
//     single-thread interpreter with ONE main Looper (LooperShadow law),
//     so the instance is a process-wide singleton object in the heap.
//   * postFrameCallback(cb) / postFrameCallbackDelayed(cb, delayMs)
//     schedule cb to run at the NEXT frame time (now + delay); duplicate
//     posts while a callback is already scheduled are legal upstream but
//     the frame clock posts once per batch (J.r guard), so FIFO with
//     duplicates allowed matches both.
//   * removeFrameCallback(cb) cancels every still-pending entry for cb
//     (AOSP removeCallbacks on the FRAME_CALLBACK_TOKEN).
//   * doFrame(frameTimeNanos) delivers ONE shared vsync timestamp to all
//     callbacks of a frame; timestamps are STRICTLY MONOTONIC with a
//     fixed nominal interval (60 Hz -> 16666667 ns). Determinism law:
//     the frame clock is VIRTUAL (base 1e9 ns, fixed quantum) — zero
//     wall-clock input, byte-identical reruns.
//   * getFrameTimeNanos()/getFrameTime() are only meaningful during a
//     doFrame dispatch; upstream throws IllegalStateException outside one.
//     The shadow fail-softs to the last frame time (documented deviation,
//     recorded in the ROOT_LAW ledger; no corpus APK reaches that path).
//   * The frame pump is the DISPLAY's vsync source in MiniAndroid: when
//     the main queue is idle and frame callbacks are pending, the engine
//     advances one frame, fires the callbacks (real DEX doFrame), drains
//     the Handler queue the resumptions post (one MessageQueue law), and
//     re-renders. The engine owns invocation (invoke_choreographer_doFrame);
//     the shadow only owns the schedule + virtual clock (HandlerShadow
//     layering law: queues live in shadows, engines invoke).
//
// No app special-casing: Choreographer is a platform primitive used by
// Compose, animations, and choreographed drawing on every real APK.
//
// Fixture: tests/fixtures/f050_choreographer_law (micro-proof, F-050 band set).

#ifndef MINIANDROID_FRAMEWORK_CHOREOGRAPHER_SHADOW_H_
#define MINIANDROID_FRAMEWORK_CHOREOGRAPHER_SHADOW_H_

#include "shadow_registry.h"

#include <cstdint>
#include <string>
#include <vector>

namespace miniandroid { namespace framework {

// ── ChoreographerShadow: exact-class claim on android.view.Choreographer ──
class ChoreographerShadow : public Shadow {
public:
    // Deterministic virtual frame clock (AOSP 60 Hz nominal vsync period).
    static constexpr int64_t kFrameBaseNanos = 1000000000LL;  // first frame @ 1e9 ns
    static constexpr int64_t kFrameIntervalNanos = 16666667LL;  // 1/60 s in ns

    std::string name() const override { return "ChoreographerShadow"; }

    // Exact-class claim only. Choreographer$FrameCallback implementations
    // are REAL APK classes — their doFrame(J)V must be dispatched through
    // the DEX engine (interface law), never shadowed.
    bool handles_class(const std::string& class_name) const override {
        return class_name == "Landroid/view/Choreographer;";
    }

    CallResult dispatch(const CallContext& ctx) override;
    std::vector<std::string> implemented_methods() const override {
        return {"getInstance", "postFrameCallback", "postFrameCallbackDelayed",
                "removeFrameCallback", "getFrameTimeNanos", "getFrameTime"};
    }

    // ── Frame-pump API (engine side; mirrors HandlerShadow layering) ──

    // True when at least one callback is scheduled (any delay).
    bool has_pending_callbacks() const { return !pending_.empty(); }

    // Take every callback whose ready time <= frame deadline. The taken
    // entries are REMOVED from the schedule (AOSP: CallbackRecord consumed
    // by runCallbacks); each carries the exact frame time of this vsync.
    struct DueFrame {
        uint32_t callback_id = 0;
        std::string callback_class;
        int64_t frame_time_nanos = 0;
    };
    std::vector<DueFrame> take_due_callbacks();

    // Last delivered frame time (deterministic virtual clock).
    int64_t last_frame_time_nanos() const { return frame_time_nanos_; }

    // True when the engine is inside a doFrame dispatch (getFrameTime law).
    bool in_do_frame() const { return in_do_frame_; }
    void set_in_do_frame(bool v) { in_do_frame_ = v; }

protected:
    struct PendingCallback {
        uint32_t callback_id = 0;
        std::string callback_class;
        int64_t ready_at_nanos = 0;   // schedule time + delay (ns)
        uint64_t enqueue_seq = 0;     // FIFO tiebreak
    };

    uint32_t choreographer_obj_id_ = 0;
    int64_t frame_time_nanos_ = kFrameBaseNanos;  // last delivered vsync
    bool in_do_frame_ = false;
    std::vector<PendingCallback> pending_;
    uint64_t next_seq_ = 1;
};

}} // namespace miniandroid::framework

#endif // MINIANDROID_FRAMEWORK_CHOREOGRAPHER_SHADOW_H_
