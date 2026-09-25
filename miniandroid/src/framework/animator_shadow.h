// S99-MG-223 — Animator platform shadow (ValueAnimator / ObjectAnimator).
//
// Root cause fixed: ValueAnimator.ofInt/ofFloat fell through to the engine
// default (null object) → the app's very next setRepeatCount(start) hit the
// F-141 null-receiver NPE law → APP BOUNDARY unwind (babydots FAIL, S99
// full-load run). AOSP law: the static factories return a NON-NULL animator;
// setDuration is fluent; lifecycle/state queries follow ValueAnimator.java.
#pragma once

#include "shadow_registry.h"

#include <unordered_map>
#include <vector>

namespace miniandroid { namespace framework {

class AnimatorShadow : public Shadow {
public:
    std::string name() const override { return "AnimatorShadow"; }
    bool handles_class(const std::string& class_name) const override;
    CallResult dispatch(const CallContext& ctx) override;
    std::vector<std::string> implemented_methods() const override;
    std::vector<std::string> stubbed_methods() const override;

private:
    // Per-object runtime state (heap object id → flag), small corpus scale.
    std::unordered_map<uint32_t, bool> started_;
    std::unordered_map<uint32_t, int32_t> repeat_count_;
};

}}  // namespace miniandroid::framework
