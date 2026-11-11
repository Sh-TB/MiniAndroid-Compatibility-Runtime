// task_stack_builder_shadow.cpp — CODER7 WAVE-12 implementation.
// Every law cites the AOSP android-14 source it mirrors (see the header
// block for the mIntents ordering + getIntents() flag laws).
#include "task_stack_builder_shadow.h"
#include "pending_intent_shadow.h"

#include "../dex/dalvik_engine.h"  // DalvikValue/DalvikType (the array-element law)

#include <iostream>

namespace miniandroid {
namespace framework {

namespace {
// AOSP Intent.java (source-verified): FLAG_ACTIVITY_NEW_TASK 0x10000000,
// FLAG_ACTIVITY_CLEAR_TASK 0x00008000, FLAG_ACTIVITY_TASK_ON_HOME 0x00004000.
constexpr int32_t kFlagNewTask = 0x10000000;
constexpr int32_t kFlagClearTask = 0x00008000;
constexpr int32_t kFlagTaskOnHome = 0x00004000;
constexpr const char* kActionMain = "android.intent.action.MAIN";
constexpr const char* kCategoryLauncher = "android.intent.category.LAUNCHER";
}  // namespace

uint32_t TaskStackBuilderShadow::make_main_intent(const std::string& pkg,
                                                  const std::string& cls) {
    // AOSP Intent.makeMainActivity(ComponentName): new Intent(ACTION_MAIN)
    // + setComponent + addCategory(CATEGORY_LAUNCHER).
    uint32_t oid = heap_->allocate("Landroid/content/Intent;");
    auto* ish = registry_ ? registry_->find_as<IntentShadow>() : nullptr;
    if (ish) {
        auto pi = ish->get_or_create_intent(oid);
        if (pi) {
            pi->action = kActionMain;
            if (!pkg.empty()) pi->component_package = pkg;
            if (!cls.empty()) pi->component_class = cls;
            pi->categories.push_back(kCategoryLauncher);
        }
    }
    return oid;
}

uint32_t TaskStackBuilderShadow::copy_intent(uint32_t src_oid,
                                             bool with_restart_flags) {
    // The getIntents() element law: a verbatim Intent copy (element 0
    // additionally carries the restart flags). The IntentShadow record is
    // the canonical intent state every instance-side law reads.
    uint32_t oid = heap_->allocate("Landroid/content/Intent;");
    auto* ish = registry_ ? registry_->find_as<IntentShadow>() : nullptr;
    if (!ish) return oid;
    auto src = ish->get_or_create_intent(src_oid);
    auto dst = ish->get_or_create_intent(oid);
    if (src && dst) {
        *dst = *src;
        dst->intent_object_id = oid;
        if (with_restart_flags)
            dst->flags |= (kFlagNewTask | kFlagClearTask | kFlagTaskOnHome);
    }
    return oid;
}

namespace {
// CODER7 WAVE-12: descriptor ("Lc7/w12/RootAct;") → dotted binary name
// ("c7.w12.RootAct") — the manifest parent table stores the dotted
// absolute form (the same normalization the engine info laws run).
std::string c7_tsb_norm_cls(std::string c) {
    if (c.size() >= 2 && c.front() == 'L' && c.back() == ';')
        c = c.substr(1, c.size() - 2);
    for (auto& ch : c)
        if (ch == '/') ch = '.';
    return c;
}
}  // namespace

bool TaskStackBuilderShadow::add_parent_stack(uint32_t builder_oid,
                                              const std::string& pkg,
                                              const std::string& cls,
                                              std::string& err) {
    // AOSP addParentStack(ComponentName): walk parentActivityName upward,
    // inserting each ancestor at `insertAt` (the LAST inserted — the
    // root-most parent — ends up FIRST = the task root). The root-most
    // parent (no parent of its own) at insertAt == 0 becomes
    // Intent.makeMainActivity(target); every other step is a plain
    // component intent. An unresolvable component is LOUD: AOSP wraps the
    // NameNotFoundException in IllegalArgumentException — the engine's
    // exception channel carries the same law.
    if (!parent_resolver_) {
        err = "parent resolver unwired (engine boot incomplete)";
        return false;
    }
    const size_t insert_at = stacks_[builder_oid].size();
    std::string cur_pkg = pkg;
    std::string cur_cls = c7_tsb_norm_cls(cls);
    std::string parent = parent_resolver_(cur_pkg, cur_cls);
    size_t c7_steps = 0;
    while (!parent.empty()) {
        const std::string target_cls = parent;
        const std::string next_parent =
            parent_resolver_(cur_pkg, target_cls);
        uint32_t intent_oid =
            (next_parent.empty() && insert_at == 0)
                ? make_main_intent(cur_pkg, target_cls)
                : [&] {
                      uint32_t oid =
                          heap_->allocate("Landroid/content/Intent;");
                      if (auto* ish = registry_
                                          ? registry_->find_as<IntentShadow>()
                                          : nullptr) {
                          if (auto pi = ish->get_or_create_intent(oid)) {
                              if (!cur_pkg.empty())
                                  pi->component_package = cur_pkg;
                              pi->component_class = target_cls;
                          }
                      }
                      return oid;
                  }();
        auto& st = stacks_[builder_oid];
        st.insert(st.begin() + static_cast<long>(insert_at), intent_oid);
        cur_cls = target_cls;
        parent = next_parent;
        c7_steps++;
        if (c7_steps > 64) {  // manifest cycle guard (AOSP loops forever on
                              // a cyclic parentActivityName chain — the
                              // engine answers loudly instead)
            err = "parentActivityName cycle detected (over 64 steps)";
            return false;
        }
    }
    (void)c7_steps;
    return true;
}

CallResult TaskStackBuilderShadow::dispatch(const CallContext& ctx) {
    const auto& m = ctx.method;
    const std::string& cls = ctx.class_name;
    if (cls != "Landroid/app/TaskStackBuilder;") return CallResult::not_handled();

    // ── static factory ────────────────────────────────────────────────────
    if (m == "create") {
        // AOSP TaskStackBuilder.create(Context): a fresh builder.
        if (!heap_) return CallResult::not_handled();
        // allocate (NOT get_or_create): builders are NOT singletons —
        // each create() must own a fresh stack (the HeapAdapter
        // get_or_create returns the FIRST registered instance).
        uint32_t oid = heap_->allocate("Landroid/app/TaskStackBuilder;");
        stacks_[oid] = {};
        std::cerr << "[C7-TSB] create -> obj=" << oid << std::endl;
        return CallResult::handled_object(oid,
                                          "Landroid/app/TaskStackBuilder;");
    }

    // ── instance methods ──────────────────────────────────────────────────
    auto& st = stacks_[ctx.receiver_id];

    if (m == "addNextIntent") {
        // AOSP addNextIntent(Intent): appended — becomes the TOP of the
        // synthesized stack. Returns `this` (chainable).
        if (ctx.args.empty() ||
            ctx.args[0].kind != CallContext::Arg::Kind::OBJECT ||
            ctx.args[0].object_id == 0) {
            return CallResult::handled_exception(
                "Ljava/lang/IllegalArgumentException;",
                "addNextIntent requires an Intent");
        }
        st.push_back(ctx.args[0].object_id);
        return CallResult::handled_object(
            ctx.receiver_id, "Landroid/app/TaskStackBuilder;");
    }

    if (m == "addNextIntentWithParentStack") {
        // AOSP addNextIntentWithParentStack(Intent): resolve the target
        // component (the intent's recorded component; a component-less
        // intent would resolveActivity — the engine's implicit-resolution
        // law lives in the startActivities pipeline, the walk below
        // records the parent chain only when a component is present),
        // addParentStack(target), then addNextIntent(nextIntent).
        if (ctx.args.empty() ||
            ctx.args[0].kind != CallContext::Arg::Kind::OBJECT ||
            ctx.args[0].object_id == 0) {
            return CallResult::handled_exception(
                "Ljava/lang/IllegalArgumentException;",
                "addNextIntentWithParentStack requires an Intent");
        }
        uint32_t next_oid = ctx.args[0].object_id;
        std::string pkg, clsname;
        if (auto* ish = registry_ ? registry_->find_as<IntentShadow>()
                                  : nullptr) {
            if (auto pi = ish->get_or_create_intent(next_oid)) {
                pkg = pi->component_package;
                clsname = pi->component_class;
            }
        }
        clsname = c7_tsb_norm_cls(clsname);
        if (!clsname.empty()) {
            std::string err;
            if (!add_parent_stack(ctx.receiver_id, pkg, clsname, err)) {
                // AOSP: NameNotFoundException wrapped in
                // IllegalArgumentException (the loud bad-component law).
                return CallResult::handled_exception(
                    "Ljava/lang/IllegalArgumentException;",
                    "Bad ComponentName while traversing activity parent "
                    "metadata: " + err);
            }
        }
        st.push_back(next_oid);
        return CallResult::handled_object(
            ctx.receiver_id, "Landroid/app/TaskStackBuilder;");
    }

    if (m == "addParentStack") {
        // AOSP addParentStack(ComponentName) — the walk alone (the
        // overloads taking Activity/Class normalize to the ComponentName
        // form upstream).
        if (ctx.args.empty() ||
            ctx.args[0].kind != CallContext::Arg::Kind::OBJECT ||
            ctx.args[0].object_id == 0) {
            return CallResult::handled_exception(
                "Ljava/lang/IllegalArgumentException;",
                "addParentStack requires a ComponentName");
        }
        std::string pkg, clsname;
        if (heap_) {
            heap_->get_object_string_field(ctx.args[0].object_id, "mPackage",
                                           pkg);
            heap_->get_object_string_field(ctx.args[0].object_id, "mClass",
                                           clsname);
        }
        std::string err;
        if (!add_parent_stack(ctx.receiver_id, pkg,
                              c7_tsb_norm_cls(clsname), err)) {
            return CallResult::handled_exception(
                "Ljava/lang/IllegalArgumentException;",
                "Bad ComponentName while traversing activity parent "
                "metadata: " + err);
        }
        return CallResult::handled_object(
            ctx.receiver_id, "Landroid/app/TaskStackBuilder;");
    }

    if (m == "getIntentCount") {
        // AOSP getIntentCount(): mIntents.size().
        return CallResult::handled_int(static_cast<int32_t>(st.size()));
    }

    if (m == "editIntentAt") {
        // AOSP editIntentAt(index): mIntents.get(index) — the SAME Intent
        // object (alias: mutations land in the stack), out-of-range is the
        // ArrayList.get IndexOutOfBoundsException (android-14 source).
        int32_t idx = ctx.arg_as_int(0, -1);
        if (idx < 0 || idx >= static_cast<int32_t>(st.size())) {
            return CallResult::handled_exception(
                "Ljava/lang/IndexOutOfBoundsException;",
                "editIntentAt: index " + std::to_string(idx) +
                    " out of bounds for length " +
                    std::to_string(st.size()));
        }
        return CallResult::handled_object(st[static_cast<size_t>(idx)],
                                          "Landroid/content/Intent;");
    }

    if (m == "getIntents") {
        // AOSP getIntents(): element 0 (the ROOT) is a COPY carrying
        // FLAG_ACTIVITY_NEW_TASK | FLAG_ACTIVITY_CLEAR_TASK |
        // FLAG_ACTIVITY_TASK_ON_HOME; the rest are verbatim copies.
        // Returns Intent[] (the engine array shape: __array_length__ +
        // array[i] fields).
        if (!heap_) return CallResult::not_handled();
        uint32_t arr = heap_->get_or_create("[Landroid/content/Intent;");
        heap_->set_object_int_field(arr, "__array_length__",
                                    static_cast<int32_t>(st.size()));
        for (size_t i = 0; i < st.size(); ++i) {
            uint32_t ci = copy_intent(st[i], /*with_restart_flags=*/i == 0);
            // The engine array shape: array[i] OBJECT_REF elements (the
            // M4 F-028d set_object_ref_field law — the same channel the
            // String[] element materializations ride).
            heap_->set_object_ref_field(
                arr, "array[" + std::to_string(i) + "]", ci,
                "Landroid/content/Intent;", "", false);
        }
        std::cerr << "[C7-TSB] getIntents count=" << st.size()
                  << " (root copy carries the restart flags)" << std::endl;
        return CallResult::handled_object(arr, "[Landroid/content/Intent;");
    }

    if (m == "getPendingIntent") {
        // AOSP getPendingIntent(requestCode, flags) = PendingIntent
        // .getActivity(context, requestCode, getIntents(), flags). The
        // PendingIntentShadow record law owns the identity/caching
        // (AMS IntentSenderRecord); the base intent is the ROOT COPY
        // (element 0 with the restart flags — the AOSP array's base
        // element; the single-runtime model carries the array by its
        // base — the W11 §6(f) documented-simplification precedent).
        int32_t rc = ctx.arg_as_int(0, 0);
        int32_t flags = ctx.arg_as_int(1, 0);
        auto* pish =
            registry_ ? registry_->find_as<PendingIntentShadow>() : nullptr;
        if (!pish || !heap_) return CallResult::not_handled();
        uint32_t root = st.empty() ? 0 : copy_intent(st[0], true);
        if (root == 0) {
            return CallResult::handled_exception(
                "Ljava/lang/IllegalStateException;",
                "getPendingIntent on an empty TaskStackBuilder");
        }
        return pish->record_from("ACTIVITY", rc, root, flags);
    }

    if (m == "startActivities") {
        // AOSP startActivities() = Context.startActivities(mIntents):
        // the RAW intents (NO flag copies), drained in order by the
        // engine's W3 startActivities law (resolution + synchronous
        // gate + FIFO queue). The engine-wired dispatcher bridges it.
        if (!start_dispatcher_) {
            return CallResult::handled_exception(
                "Ljava/lang/IllegalStateException;",
                "startActivities dispatcher unwired (engine boot "
                "incomplete)");
        }
        std::string err;
        if (!start_dispatcher_(st, err)) {
            return CallResult::handled_exception(
                "Ljava/lang/IllegalArgumentException;",
                "startActivities: " + err);
        }
        return CallResult::handled_void();
    }

    // Unknown method — honest unhandled (the registry's view path answers
    // loudly; never a fabricated return).
    return CallResult::not_handled();
}

}  // namespace framework
}  // namespace miniandroid
