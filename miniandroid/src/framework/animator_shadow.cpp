// S99-MG-223 — Animator platform shadow implementation.
//
// WHY (S99 full-load evidence, run/s99/full_load/com.serwylo.babydots):
// babydots' AnimatedDots.<init> calls ValueAnimator.ofInt(...)/ofFloat(...)
// then setRepeatCount on the result. The runtime had NO ValueAnimator
// handling: the static factory fell through to the engine default (null
// object) and the very next instance invoke hit the F-141 null-receiver law
// → NPE "ValueAnimator.setRepeatCount on a null object reference" → APP
// BOUNDARY unwind → onCreate dead → zero frames (FAIL).
//
// AOSP law (ValueAnimator.java): ofInt/ofFloat/ofArgb/ofObject/ofProperty-
// ValuesHolder are static factories that return a non-null animator;
// setDuration(long) is FLUENT (returns the animator itself); setStartDelay/
// setRepeatCount/setRepeatMode/setInterpolator/addUpdateListener/addListener
// mutate state; start()/cancel()/end() lifecycle; isRunning/isStarted reflect
// the started flag; getAnimatedValue is null before start.
#include "animator_shadow.h"

#include <iostream>

namespace miniandroid { namespace framework {

bool AnimatorShadow::handles_class(const std::string& class_name) const {
    // The whole android.animation animator family this shadow models.
    return class_name.find("Landroid/animation/ValueAnimator;") == 0 ||
           class_name.find("Landroid/animation/ObjectAnimator;") == 0 ||
           class_name.find("Landroid/animation/Animator;") == 0 ||
           class_name.find("Landroid/animation/AnimatorSet;") == 0;
}

static bool is_animator_object_kind(const CallContext& ctx, size_t i) {
    return i < ctx.args.size() &&
           (ctx.args[i].kind == CallContext::Arg::Kind::OBJECT ||
            ctx.args[i].kind == CallContext::Arg::Kind::NULL_REF);
}

CallResult AnimatorShadow::dispatch(const CallContext& ctx) {
    const std::string& cls = ctx.class_name;
    const std::string& m = ctx.method;
    const bool is_value = cls.find("ValueAnimator;") != std::string::npos;
    const bool is_object_anim = cls.find("ObjectAnimator;") != std::string::npos;
    const bool is_set = cls.find("AnimatorSet;") != std::string::npos;

    // ── static factories ────────────────────────────────────────────────
    if (m == "ofInt" || m == "ofFloat" || m == "ofArgb" || m == "ofObject" ||
        m == "ofPropertyValuesHolder") {
        // ObjectAnimator overloads take (Object target, String prop, T...).
        // ValueAnimator overloads take (T...). The receiver-less static
        // call allocates the concrete animator class.
        const char* alloc_cls = is_object_anim ? "Landroid/animation/ObjectAnimator;"
                                               : "Landroid/animation/ValueAnimator;";
        uint32_t obj = heap_ ? heap_->allocate(alloc_cls) : 0;
        if (obj == 0) return CallResult::not_handled();
        {
            std::cerr << "[ANIM] " << (is_object_anim ? "ObjectAnimator" : "ValueAnimator")
                      << "." << m << " -> animator obj=" << obj << std::endl;
        }
        return CallResult::handled_object(obj, alloc_cls);
    }

    // ── fluent setDuration(long) → returns the animator itself ─────────
    if (m == "setDuration") {
        // AOSP: @NonNull ValueAnimator setDuration(long). Receiver is
        // carried in has_receiver/receiver_id for instance invokes.
        if (ctx.has_receiver && ctx.receiver_id != 0) {
            return CallResult::handled_object(ctx.receiver_id, cls);
        }
        return CallResult::handled_void();
    }

    // ── lifecycle ──────────────────────────────────────────────────────
    if (m == "start" || m == "cancel" || m == "end") {
        if (ctx.has_receiver) {
            if (m == "start") {
                started_[ctx.receiver_id] = true;
            } else {
                started_[ctx.receiver_id] = false;
            }
            std::cerr << "[ANIM] " << m << " animator=" << ctx.receiver_id
                      << " (state " << (started_[ctx.receiver_id] ? "running" : "idle")
                      << ")" << std::endl;
        }
        return CallResult::handled_void();
    }

    // ── state queries ──────────────────────────────────────────────────
    if (m == "isRunning" || m == "isStarted") {
        bool running = ctx.has_receiver && started_.count(ctx.receiver_id) &&
                       started_[ctx.receiver_id];
        return CallResult::handled_bool(running);
    }
    if (m == "isPaused") return CallResult::handled_bool(false);
    if (m == "getDuration") return CallResult::handled_long(0);
    if (m == "getStartDelay") return CallResult::handled_long(0);
    if (m == "getRepeatCount") {
        // AOSP default 0; INFINITE (-1) is stored by setRepeatCount below
        // only in the running-app state map (not observed by corpus yet).
        return CallResult::handled_int(repeat_count_.count(ctx.receiver_id)
                                           ? repeat_count_[ctx.receiver_id]
                                           : 0);
    }
    if (m == "getAnimatedFraction") return CallResult::handled_float(0.0f);
    if (m == "getAnimatedValue" || m == "getAnimatedValue(String)" ||
        m == "getValues" || m == "clone") {
        // getAnimatedValue: AOSP returns null before start. getValues/clone
        // are cold paths for the corpus; null is the honest pre-start law.
        return CallResult::handled_null();
    }
    if (m == "getInterpolator") return CallResult::handled_null();

    // ── void mutators (AOSP signatures verified per ValueAnimator.java) ─
    if (m == "setStartDelay" || m == "setRepeatCount" || m == "setRepeatMode" ||
        m == "setInterpolator" || m == "setEvaluator" || m == "setFloatValues" ||
        m == "setIntValues" || m == "setPropertyValuesHolder" ||
        m == "addUpdateListener" || m == "addListener" || m == "addPauseListener" ||
        m == "removeAllUpdateListeners" || m == "removeAllListeners" ||
        m == "removeUpdateListener" || m == "removeListener" ||
        m == "setCurrentPlayTime" || m == "setCurrentFraction" ||
        m == "setAllowRunningAsynchronously" || m == "setupStartValues" ||
        m == "setupEndValues" || m == "skipToEndValue" ||
        m == "setChildAnimator" || m == "play" || m == "playTogether" ||
        m == "playSequentially" || m == "setTarget" || m == "setPropertyName") {
        if (m == "setRepeatCount" && ctx.has_receiver) {
            repeat_count_[ctx.receiver_id] = ctx.arg_as_int(0, 0);
        }
        return CallResult::handled_void();
    }

    // AnimatorInflater.loadAnimator / loadStateListAnimator — return a
    // fresh animator object (resource XML animation inflation frontier).
    if (cls.find("AnimatorInflater;") != std::string::npos &&
        (m == "loadAnimator" || m == "loadStateListAnimator")) {
        uint32_t obj = heap_ ? heap_->allocate("Landroid/animation/ValueAnimator;") : 0;
        if (obj != 0) return CallResult::handled_object(obj, "Landroid/animation/ValueAnimator;");
    }

    (void)is_value; (void)is_set;
    return CallResult::not_handled();
}

std::vector<std::string> AnimatorShadow::implemented_methods() const {
    return {"ofInt", "ofFloat", "ofArgb", "ofObject", "ofPropertyValuesHolder",
            "setDuration", "start", "cancel", "end", "isRunning", "isStarted",
            "setRepeatCount", "setStartDelay", "setRepeatMode", "setInterpolator",
            "addUpdateListener", "addListener"};
}

std::vector<std::string> AnimatorShadow::stubbed_methods() const {
    return {"getAnimatedValue", "getAnimatedFraction", "getValues", "clone",
            "getInterpolator", "setCurrentPlayTime"};
}

}}  // namespace miniandroid::framework
