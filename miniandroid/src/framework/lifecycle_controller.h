// lifecycle_controller.h — G07 §7/§10 runtime lifecycle state machine.
//
// The Activity-lifecycle state machine of the runtime. Transitions are
// EFFECTS of runtime events (DEX callback completed, finish() requested,
// frame boundary reached) — never a scripted sequence.
//
// States (§10 canonical machine):
//   PROCESS_CREATED → ACTIVITY_CREATED → STARTED → RESUMED
//   RESUMED → PAUSED → STOPPED → DESTROYED
//   STOPPED → STARTED (restart)   PAUSED → RESUMED (re-resume)
//
// AOSP laws (android-14.0.0_r2, frameworks/base/core/java/android/app/):
//  * ActivityThread.performLaunchActivity L3653+: instantiate + onCreate
//    (via Instrumentation.callActivityOnCreate)
//  * ActivityThread.handleResumeActivity L4986+: performResume →
//    onStart (when restarting) then onResume
//  * ActivityThread.handlePauseActivity L5152 → performPauseActivity →
//    Instrumentation.callActivityOnPause → onPause
//  * ActivityThread.handleStopActivity L5408 → performStopActivityInner →
//    callActivityOnStop → onStop
//  * ActivityThread.performDestroyActivity: onDestroy
//  * finish() law: Activity.finish sets mFinished and asks
//    ActivityManager; the callbacks arrive as transactions — the runtime
//    applies them at the next frame boundary (request_finish law).
//  * TransactionExecutor law (launch order): A.onPause → B.onCreate →
//    B.onStart → B.onResume → A.onStop — pause of the old activity is the
//    FIRST callback of a switch, stop is the LAST (G08 uses this order).

#ifndef MINIANDROID_LIFECYCLE_CONTROLLER_H
#define MINIANDROID_LIFECYCLE_CONTROLLER_H

#include "../third_party/nlohmann_json/include/nlohmann/json.hpp"

#include <cstdint>
#include <string>
#include <vector>

namespace miniandroid {
namespace framework {

enum class LifecyclePhase {
    PROCESS_CREATED,
    ACTIVITY_CREATED,
    STARTED,
    RESUMED,
    PAUSED,
    STOPPED,
    DESTROYED,
    FAILED
};

const char* lifecycle_phase_name(LifecyclePhase s);

class LifecycleController {
public:
    struct Entry {
        LifecyclePhase from = LifecyclePhase::PROCESS_CREATED;
        LifecyclePhase to = LifecyclePhase::PROCESS_CREATED;
        std::string reason;
        int64_t virtual_ms = 0;
        bool success = true;
    };

    // Guarded transition (AOSP state law). Records every attempt — a
    // rejected transition is recorded with success=false (hostile-input
    // evidence), never silently ignored.
    bool transition_to(LifecyclePhase next, const std::string& reason,
                       int64_t virtual_ms);

    LifecyclePhase state() const { return state_; }

    // AOSP finish cascade: RESUMED/PAUSED/STOPPED → DESTROYED through the
    // canonical intermediate transitions (onPause/onStop/onDestroy are
    // dispatched by the engine between these transitions). Returns false
    // (with a recorded FAILED entry) where the cascade is not defined.
    bool finish_cascade(int64_t virtual_ms);

    const std::vector<Entry>& entries() const { return entries_; }

    nlohmann::json to_json(const std::string& apk,
                           const std::string& activity_class) const;

private:
    LifecyclePhase state_ = LifecyclePhase::PROCESS_CREATED;
    std::vector<Entry> entries_;
};

}  // namespace framework
}  // namespace miniandroid

#endif  // MINIANDROID_LIFECYCLE_CONTROLLER_H
