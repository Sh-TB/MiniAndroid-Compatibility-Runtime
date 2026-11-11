// task_stack_builder_shadow.h — CODER7 WAVE-12: android.app.TaskStackBuilder
//
// ─────────────────────────────────────────────────────────────────────────────
// LAW (AOSP frameworks/base core/java/android/app/TaskStackBuilder.java,
// android-14 source-verified):
//
// TaskStackBuilder synthesizes a cross-task activity stack: mIntents holds
// the intents ROOT-FIRST (index 0 = the task root, the LAST added is the
// top). addParentStack(ComponentName) walks ActivityInfo.parentActivityName
// upward through PackageManager.getActivityInfo, inserting each parent at
// `insertAt` so the LAST inserted (the root-most parent) ends up FIRST;
// the root-most parent's intent is Intent.makeMainActivity(target) when
// insertAt == 0 (ACTION_MAIN + component + CATEGORY_LAUNCHER), others are
// plain component intents. getIntents() COPIES the stack: element 0 gets
// FLAG_ACTIVITY_NEW_TASK | FLAG_ACTIVITY_CLEAR_TASK |
// FLAG_ACTIVITY_TASK_ON_HOME, the rest are verbatim copies.
// makeRestartActivityTask is NOT on TaskStackBuilder in android-34 (the
// vendored stub declares none) — the restart law lives on
// Intent.makeRestartActivityTask (IntentShadow). getPendingIntent(requestCode,
// flags) = PendingIntent.getActivity(context, requestCode, getIntents(),
// flags): the shadow delegates to the PendingIntentShadow record law with
// the ROOT copy as the base intent (the AOSP array form carried by its
// element-0 base for the single-runtime model — the W11 §6(f)
// documented-simplification precedent). startActivities() = AOSP
// Context.startActivities(mIntents): the RAW intents (no flag copies),
// drained in order by the engine's W3 startActivities law via the
// engine-wired dispatcher.
// ─────────────────────────────────────────────────────────────────────────────
#ifndef MINIANDROID_FRAMEWORK_TASK_STACK_BUILDER_SHADOW_H
#define MINIANDROID_FRAMEWORK_TASK_STACK_BUILDER_SHADOW_H

#include "../framework/shadow_registry.h"
#include "../framework/android_shadows.h"  // IntentShadow record access

#include <cstdint>
#include <functional>
#include <map>
#include <string>
#include <vector>

namespace miniandroid {
namespace framework {

class PendingIntentShadow;

class TaskStackBuilderShadow : public Shadow {
public:
    std::string name() const override { return "TaskStackBuilderShadow"; }

    bool handles_class(const std::string& cls) const override {
        // Exact family claim only (the PendingIntentShadow registration
        // law — the catch-all view path must never see this descriptor).
        return cls == "Landroid/app/TaskStackBuilder;";
    }

    CallResult dispatch(const CallContext& ctx) override;

    // ── engine-wired callbacks (the set_send_dispatcher precedent) ──────
    // The parent resolver: (package, dotted class) → dotted parent class
    // ("" = none / unknown). The engine answers from the manifest
    // transfer (own package) and the C7 package index (store packages).
    using ParentResolver =
        std::function<std::string(const std::string& pkg,
                                  const std::string& cls)>;
    void set_parent_resolver(ParentResolver fn) {
        parent_resolver_ = std::move(fn);
    }
    // The startActivities dispatcher: the engine bridges the RAW intent
    // stack through its W3 Context.startActivities law (resolution +
    // synchronous gate + FIFO queue). Returns dispatch ok.
    using StartDispatcher = std::function<bool(
        const std::vector<uint32_t>& intent_oids, std::string& err)>;
    void set_start_dispatcher(StartDispatcher fn) {
        start_dispatcher_ = std::move(fn);
    }

    // ── evidence accessors ────────────────────────────────────────────────
    size_t builder_count() const { return stacks_.size(); }
    size_t stack_depth(uint32_t builder_oid) const {
        auto it = stacks_.find(builder_oid);
        return it == stacks_.end() ? 0 : it->second.size();
    }

private:
    // builder oid → intent oids (ROOT-FIRST, the AOSP mIntents law).
    std::map<uint32_t, std::vector<uint32_t>> stacks_;
    ParentResolver parent_resolver_;
    StartDispatcher start_dispatcher_;

    // AOSP addParentStack(ComponentName): the parentActivityName walk.
    // Returns false (and sets err) when the walk hits an unresolvable
    // component (AOSP NameNotFoundException → IllegalArgumentException).
    bool add_parent_stack(uint32_t builder_oid, const std::string& pkg,
                          const std::string& cls, std::string& err);
    // The Intent.makeMainActivity law (ACTION_MAIN + component +
    // CATEGORY_LAUNCHER) — used for the root-most parent at insertAt 0
    // and shared with the makeRestartActivityTask family (IntentShadow).
    uint32_t make_main_intent(const std::string& pkg, const std::string& cls);
    // A verbatim Intent copy (the getIntents() element law); with_flags
    // ORs the restart flags onto element 0 (NEW_TASK|CLEAR_TASK|
    // TASK_ON_HOME — AOSP getIntents).
    uint32_t copy_intent(uint32_t src_oid, bool with_restart_flags);
};

}  // namespace framework
}  // namespace miniandroid

#endif  // MINIANDROID_FRAMEWORK_TASK_STACK_BUILDER_SHADOW_H
