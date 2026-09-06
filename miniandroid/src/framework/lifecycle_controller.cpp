// lifecycle_controller.cpp — G07 lifecycle state machine implementation.
// Transition law table mirrors ActivityThread's transaction handlers.

#include "lifecycle_controller.h"

namespace miniandroid {
namespace framework {

const char* lifecycle_phase_name(LifecyclePhase s) {
    switch (s) {
        case LifecyclePhase::PROCESS_CREATED: return "PROCESS_CREATED";
        case LifecyclePhase::ACTIVITY_CREATED: return "ACTIVITY_CREATED";
        case LifecyclePhase::STARTED: return "STARTED";
        case LifecyclePhase::RESUMED: return "RESUMED";
        case LifecyclePhase::PAUSED: return "PAUSED";
        case LifecyclePhase::STOPPED: return "STOPPED";
        case LifecyclePhase::DESTROYED: return "DESTROYED";
        case LifecyclePhase::FAILED: return "FAILED";
    }
    return "?";
}

namespace {
// AOSP-valid transitions (ActivityThread transaction laws):
//   onCreate → ACTIVITY_CREATED (performLaunchActivity)
//   onStart   → STARTED          (handleResumeActivity / restart)
//   onResume  → RESUMED          (handleResumeActivity)
//   onPause   → PAUSED           (handlePauseActivity — FIRST callback of
//                               an activity switch, TransactionExecutor law)
//   onStop    → STOPPED          (handleStopActivity — LAST callback of a
//                               switch)
//   restart   → STARTED          (handleResumeActivity from STOPPED)
//   onDestroy → DESTROYED        (performDestroyActivity)
bool valid_from(LifecyclePhase from, LifecyclePhase to) {
    switch (to) {
        case LifecyclePhase::ACTIVITY_CREATED:
            return from == LifecyclePhase::PROCESS_CREATED;
        case LifecyclePhase::STARTED:
            return from == LifecyclePhase::ACTIVITY_CREATED ||
                   from == LifecyclePhase::STOPPED;  // restart law
        case LifecyclePhase::RESUMED:
            return from == LifecyclePhase::STARTED ||
                   from == LifecyclePhase::PAUSED;   // re-resume law
        case LifecyclePhase::PAUSED:
            return from == LifecyclePhase::RESUMED;
        case LifecyclePhase::STOPPED:
            return from == LifecyclePhase::PAUSED;
        case LifecyclePhase::DESTROYED:
            // performDestroyActivity applies after pause/stop of the
            // finishing activity (finish cascade intermediate steps).
            return from == LifecyclePhase::STOPPED ||
                   from == LifecyclePhase::PAUSED ||
                   from == LifecyclePhase::RESUMED;  // finish() shortcut
        default:
            return false;
    }
}
}  // namespace

bool LifecycleController::transition_to(LifecyclePhase next,
                                        const std::string& reason,
                                        int64_t virtual_ms) {
    Entry e;
    e.from = state_;
    e.to = next;
    e.reason = reason;
    e.virtual_ms = virtual_ms;
    e.success = valid_from(state_, next);
    if (e.success) state_ = next;
    entries_.push_back(e);
    return e.success;
}

bool LifecycleController::finish_cascade(int64_t virtual_ms) {
    // Canonical finish order (ActivityThread): onPause → onStop →
    // onDestroy for the finishing activity. The engine dispatches each
    // callback between these transitions.
    if (state_ == LifecyclePhase::RESUMED) {
        if (!transition_to(LifecyclePhase::PAUSED, "finish cascade: onPause",
                           virtual_ms))
            return false;
    }
    if (state_ == LifecyclePhase::PAUSED) {
        if (!transition_to(LifecyclePhase::STOPPED, "finish cascade: onStop",
                           virtual_ms))
            return false;
    }
    if (state_ == LifecyclePhase::STOPPED) {
        return transition_to(LifecyclePhase::DESTROYED,
                             "finish cascade: onDestroy", virtual_ms);
    }
    return false;
}

nlohmann::json LifecycleController::to_json(const std::string& apk,
                                            const std::string& activity_class)
    const {
    nlohmann::json j;
    j["apk"] = apk;
    j["activity"] = activity_class;
    j["final_state"] = lifecycle_phase_name(state_);
    j["transitions"] = nlohmann::json::array();
    for (const auto& e : entries_) {
        j["transitions"].push_back({
            {"from", lifecycle_phase_name(e.from)},
            {"to", lifecycle_phase_name(e.to)},
            {"reason", e.reason},
            {"virtual_ms", e.virtual_ms},
            {"success", e.success},
        });
    }
    return j;
}

}  // namespace framework
}  // namespace miniandroid
